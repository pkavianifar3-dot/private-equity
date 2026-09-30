"""Research associations refer to canonical Entities, apart from text mentions."""

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "validate_atlas_stage4", ROOT / "atlas/tools/validate-atlas.py"
)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class ResearchEntityReferenceTests(unittest.TestCase):
    def test_article_and_section_associations_are_independent_of_mentions(self):
        data = {
            "id": "research:sample",
            "entityRefs": ["concept:known"],
            "sections": [{
                "id": "opening",
                "entityRefs": ["person:known"],
                "mentions": [{"entityRef": "concept:other", "resolutionStatus": "RESOLVED"}],
            }],
        }
        errors = []
        validator.validate_research_entity_refs(
            data, {"concept:known", "person:known"}, errors,
            "research/content/sample.json",
        )
        self.assertEqual(errors, [])

    def test_unknown_article_and_section_refs_report_location_and_id(self):
        data = {
            "id": "research:sample",
            "entityRefs": ["concept:missing"],
            "sections": [{"id": "opening", "entityRefs": ["person:missing"]}],
        }
        errors = []
        validator.validate_research_entity_refs(
            data, set(), errors, "research/content/sample.json"
        )
        self.assertEqual(errors, [
            "research/content/sample.json:research:sample: unknown entityRef concept:missing",
            "research/content/sample.json:research:sample:opening: unknown entityRef person:missing",
        ])

    def test_schema_already_rejects_duplicate_article_refs(self):
        schema = json.loads(
            (ROOT / "research/schemas/research-schema-v2.json").read_text(encoding="utf-8")
        )
        article = json.loads(
            (ROOT / "research/content/private-capital.json").read_text(encoding="utf-8")
        )
        article["entityRefs"].append(article["entityRefs"][0])
        errors = list(Draft202012Validator(schema).iter_errors(article))
        self.assertTrue(any(list(error.path) == ["entityRefs"] and "non-unique" in error.message for error in errors))

    def test_document_validation_rejects_unknown_article_ref(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            research = Path(temp_dir) / "research"
            (research / "content").mkdir(parents=True)
            (research / "schemas").mkdir()
            shutil.copyfile(
                ROOT / "research/schemas/research-schema-v2.json",
                research / "schemas/research-schema-v2.json",
            )
            (research / "content/sample.json").write_text(
                json.dumps({
                    "id": "research:sample", "type": "Research", "schemaVersion": "2.0",
                    "url": "/articles/sample.html", "status": "PUBLISHED",
                    "title": {"fa": "نمونه"}, "summary": {"fa": "خلاصه"},
                    "publication": {}, "candidateClaimRefs": [], "sections": [],
                    "entityRefs": ["concept:missing"],
                }, ensure_ascii=False),
                encoding="utf-8",
            )
            original_root = validator.ROOT
            validator.ROOT = Path(temp_dir) / "atlas"
            try:
                errors = []
                validator.validate_research_documents(errors, set())
            finally:
                validator.ROOT = original_root
            self.assertIn(
                "research/content/sample.json:research:sample: unknown entityRef concept:missing",
                errors,
            )


if __name__ == "__main__":
    unittest.main()
