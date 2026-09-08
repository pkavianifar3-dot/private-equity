import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


SPEC = importlib.util.spec_from_file_location(
    "validate_atlas",
    "atlas/tools/validate-atlas.py",
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ResearchReferenceIntegrityTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self.research_root = self.root / "research"
        self.content_root = self.research_root / "content"
        self.content_root.mkdir(parents=True)

        self.original_root = VALIDATOR.ROOT
        VALIDATOR.ROOT = self.root / "atlas"

    def tearDown(self):
        VALIDATOR.ROOT = self.original_root
        self.temp_dir.cleanup()

    def write_research_document(self, section):
        path = self.content_root / "test-research.json"

        data = {
            "id": "research:test",
            "type": "article",
            "schemaVersion": "2.0",
            "url": "/research/test",
            "status": "PUBLISHED",
            "title": "Test Research",
            "summary": "Test summary",
            "publication": {},
            "candidateClaimRefs": [],
            "sections": [section],
        }

        path.write_text(
            json.dumps(data, ensure_ascii=False),
            encoding="utf-8",
        )

    def validate(self):
        errors = []

        entity_by_id = {"concept:subject": {"type": "Concept"}, "concept:object": {"type": "Concept"}}
        entity_ids = set(entity_by_id)

        VALIDATOR.validate_research_integrity(
            entity_by_id=entity_by_id,
            entity_ids=entity_ids,
            claim_ids={
                "claim:known-claim",
            },
            source_ids={
                "source:known-source",
            },
            relation_types={"INCLUDES"},
            relation_rules={"INCLUDES": {"subject_types": ["Concept"], "object_types": ["Concept"]}},
            errors=errors,
        )

        return errors

    def test_known_section_references_pass(self):
        self.write_research_document({
            "id": "section-one",
            "title": {
                "fa": "بخش اول",
            },
            "content": [],
            "claimRefs": [
                "claim:known-claim",
            ],
            "sourceRefs": [
                "source:known-source",
            ],
        })

        errors = self.validate()

        self.assertEqual(errors, [])

    def test_unknown_canonical_claim_fails(self):
        self.write_research_document({
            "id": "section-one",
            "title": {
                "fa": "بخش اول",
            },
            "content": [],
            "claimRefs": [
                "claim:unknown-claim",
            ],
        })

        errors = self.validate()

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "unknown canonical claim claim:unknown-claim",
            errors[0],
        )
        self.assertIn(
            "research/content/test-research.json:section-one",
            errors[0],
        )

    def test_unknown_canonical_source_fails(self):
        self.write_research_document({
            "id": "section-one",
            "title": {
                "fa": "بخش اول",
            },
            "content": [],
            "sourceRefs": [
                "source:unknown-source",
            ],
        })

        errors = self.validate()

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "unknown canonical source source:unknown-source",
            errors[0],
        )
        self.assertIn(
            "research/content/test-research.json:section-one",
            errors[0],
        )


    def test_unknown_research_predicate_fails(self):
        errors = []
        VALIDATOR.validate_research_claim_integrity(
            [{"id": "research-claim:test", "subject": "concept:subject", "predicate": "UNKNOWN", "object": "concept:object"}],
            {"concept:subject": {"type": "Concept"}, "concept:object": {"type": "Concept"}},
            {"concept:subject", "concept:object"},
            {"INCLUDES"},
            {"INCLUDES": {"subject_types": ["Concept"], "object_types": ["Concept"]}},
            errors,
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("unknown research predicate UNKNOWN", errors[0])


    def test_research_object_type_mismatch_fails(self):
        errors = []
        VALIDATOR.validate_research_claim_integrity(
            [{"id": "research-claim:test", "subject": "concept:subject", "predicate": "INCLUDES", "object": "organization:object"}],
            {"concept:subject": {"type": "Concept"}, "organization:object": {"type": "Organization"}},
            {"concept:subject", "organization:object"},
            {"INCLUDES"},
            {"INCLUDES": {"subject_types": ["Concept"], "object_types": ["Concept"]}},
            errors,
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("research object type Organization is not allowed for INCLUDES", errors[0])


    def test_research_predicate_taxonomy_is_enforced(self):
        errors = []
        VALIDATOR.validate_research_claim_integrity(
            [{"id": "research-claim:test", "subject": "concept:subject", "predicate": "INCLUDES", "object": "concept:object"}],
            {"concept:subject": {"type": "Concept"}, "concept:object": {"type": "Concept"}},
            {"concept:subject", "concept:object"},
            {"INCLUDES"},
            {"INCLUDES": {"subject_types": ["Concept"], "object_types": ["Concept"]}},
            errors,
            {"BROADER_THAN"},
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("is not allowed in Research", errors[0])


if __name__ == "__main__":
    unittest.main()
