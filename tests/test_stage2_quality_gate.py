"""Mutation checks against the real canonical records and current validator."""

import contextlib
import copy
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "stage2_validate_atlas", REPO / "atlas/tools/validate-atlas.py"
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class Stage2QualityGateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "atlas"
        for directory in (
            "entities", "claims", "evidence", "sources",
            "schemas", "taxonomies", "content",
        ):
            shutil.copytree(REPO / "atlas" / directory, self.root / directory)
        shutil.copytree(REPO / "research", self.root.parent / "research")

        for name, value in (
            ("ROOT", self.root),
            ("SCHEMAS_DIR", self.root / "schemas"),
        ):
            patched = patch.object(VALIDATOR, name, value)
            patched.start()
            self.addCleanup(patched.stop)

    def change(self, relative_path, edit):
        path = self.root / relative_path
        data = json.loads(path.read_text(encoding="utf-8"))
        edit(data)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def output(self, expected_exit):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            if expected_exit:
                with self.assertRaises(SystemExit) as caught:
                    VALIDATOR.main()
                self.assertEqual(caught.exception.code, 1)
            else:
                VALIDATOR.main()
        return stream.getvalue()

    def assert_rejected(self, *details):
        output = self.output(expected_exit=True)
        for detail in details:
            self.assertIn(detail, output)

    def test_unmodified_real_records_pass(self):
        self.assertIn("Atlas validation PASSED", self.output(expected_exit=False))

    def test_missing_entity_reference_reports_claim_file_and_id(self):
        self.change("claims/private-capital.json", lambda data: data["claims"][0].update(
            subject="concept:missing-entity", object="concept:missing-object"
        ))
        self.assert_rejected(
            "claims/private-capital.json:claim:private-capital-includes-private-equity",
            "unknown subject entity concept:missing-entity",
            "unknown object entity concept:missing-object",
        )

    def test_missing_evidence_reference_reports_claim_file_and_id(self):
        self.change("claims/private-capital.json", lambda data: data["claims"][0][
            "evidenceRefs"
        ].append("evidence:missing"))
        self.assert_rejected(
            "claims/private-capital.json:claim:private-capital-includes-private-equity",
            "unknown evidenceRefs ['evidence:missing']",
        )

    def test_missing_source_reference_reports_evidence_file_and_id(self):
        self.change("evidence/private-capital-research.json", lambda data: data[
            "evidence"
        ][0].update(sourceRef="source:missing"))
        self.assert_rejected(
            "evidence/private-capital-research.json:evidence:private-capital-includes-private-equity-01",
            "unknown source source:missing",
        )

    def test_malformed_id_and_unknown_entity_type_report_record_location(self):
        self.change("claims/private-capital.json", lambda data: data["claims"][0].update(
            id="claim:invalid id"
        ))
        self.change("entities/concepts/private-capital.json", lambda data: data.update(
            type="UnknownType"
        ))
        self.assert_rejected(
            "claims/private-capital.json:claim:invalid id: schema error",
            "entities/concepts/private-capital.json:concept:private-capital: schema error at type",
        )

    def test_object_and_value_together_fail_xor(self):
        value_file = self.root / "claims/investment-kayson-achareh-amount.json"
        value = json.loads(value_file.read_text(encoding="utf-8"))["claims"][0]["value"]
        self.change("claims/private-capital.json", lambda data: data["claims"][0].update(
            value=copy.deepcopy(value)
        ))
        self.assert_rejected(
            "claims/private-capital.json:claim:private-capital-includes-private-equity",
            "exactly one of object/value is required",
        )

    def test_missing_object_and_value_fails_xor(self):
        self.change("claims/private-capital.json", lambda data: data["claims"][0].pop(
            "object"
        ))
        self.assert_rejected(
            "claims/private-capital.json:claim:private-capital-includes-private-equity",
            "exactly one of object/value is required",
        )

    def test_status_and_confidence_are_separate_enums(self):
        self.change("claims/private-capital.json", lambda data: data["claims"][0].update(
            status="HIGH", confidence="SUPPORTED"
        ))
        self.assert_rejected(
            "claims/private-capital.json:claim:private-capital-includes-private-equity",
            "schema error at claims.0.status",
            "schema error at claims.0.confidence",
        )

    def test_valid_status_confidence_pair_is_not_artificially_coupled(self):
        data = json.loads((self.root / "claims/private-capital.json").read_text(encoding="utf-8"))
        claim = data["claims"][0]
        claim["status"] = "REPORTED"
        claim["confidence"] = "HIGH"
        errors = []
        VALIDATOR.add_schema_errors(
            claim, self.root / "schemas/claim-schema-v1.json", "claim fixture", errors
        )
        self.assertEqual(errors, [])

    def test_revision_without_predecessor_fails(self):
        self.change("claims/private-capital.json", lambda data: data["claims"][0].update(
            revision=2
        ))
        self.assert_rejected(
            "claims/private-capital.json:claim:private-capital-includes-private-equity",
            "must supersede a previous claim",
        )

    def test_supersedes_cycle_fails_on_real_claim_fixture(self):
        def cycle(data):
            original = data["claims"][0]
            successor = copy.deepcopy(original)
            successor.update(
                id="claim:private-capital-includes-private-equity-revision-two",
                revision=2,
                supersedes=original["id"],
            )
            original["supersedes"] = successor["id"]
            data["claims"].append(successor)

        self.change("claims/private-capital.json", cycle)
        self.assert_rejected(
            "claims/private-capital.json:claim:private-capital-includes-private-equity",
            "supersedes chain contains a cycle",
        )

    def test_used_predicate_without_render_contract_fails(self):
        self.change("taxonomies/relation-rendering.json", lambda data: data[
            "relations"
        ].pop("INCLUDES"))
        self.assert_rejected(
            "taxonomies/relation-rendering.json: missing rendering contract for predicate INCLUDES"
        )

    def test_render_contract_subject_type_mismatch_fails(self):
        self.change("taxonomies/relation-rendering.json", lambda data: data[
            "relations"
        ]["INCLUDES"].update(subject_types=["Person"]))
        self.assert_rejected(
            "taxonomies/relation-rendering.json: INCLUDES: subject_types does not match",
        )


class StaticPageInventoryTests(unittest.TestCase):
    def test_routed_entities_and_static_page_paths_match(self):
        spec = importlib.util.spec_from_file_location(
            "stage2_build_static_pages", REPO / "atlas/tools/build-static-pages.py"
        )
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        entities = builder.load_entities()
        expected = {
            REPO / "atlas" / builder.ROUTES[entity["type"]]
            / entity_id.split(":", 1)[1] / "index.html"
            for entity_id, entity in entities.items()
            if entity["type"] in builder.ROUTES
        }
        actual = {
            path
            for route in builder.ROUTES.values()
            for path in (REPO / "atlas" / route).glob("*/index.html")
        }
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
