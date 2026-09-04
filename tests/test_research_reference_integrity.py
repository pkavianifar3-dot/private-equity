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

        VALIDATOR.validate_research_integrity(
            entity_ids=set(),
            claim_ids={
                "claim:known-claim",
            },
            source_ids={
                "source:known-source",
            },
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


if __name__ == "__main__":
    unittest.main()
