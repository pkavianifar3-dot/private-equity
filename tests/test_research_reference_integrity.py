import importlib.util
import json
import shutil
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
        self.schema_root = self.research_root / "schemas"
        self.content_root.mkdir(parents=True)
        self.schema_root.mkdir(parents=True)

        shutil.copyfile(
            Path("research/schemas/research-schema-v2.json"),
            self.schema_root / "research-schema-v2.json",
        )

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


    def test_unknown_citation_source_fails(self):
        data = {"sections": [], "citations": [{"id": "citation:test", "sourceRef": "source:unknown-source"}]}
        errors = []
        VALIDATOR.validate_research_citation_integrity(data, {"source:known-source"}, [], errors)
        self.assertEqual(len(errors), 1)
        self.assertIn("unknown citation source source:unknown-source", errors[0])

    def test_unknown_citation_content_block_fails(self):
        data = {"sections": [], "citations": [{"id": "citation:test", "sourceRef": "source:known-source", "contentBlockId": "missing-block"}]}
        errors = []
        VALIDATOR.validate_research_citation_integrity(data, {"source:known-source"}, [], errors)
        self.assertEqual(len(errors), 1)
        self.assertIn("unknown citation content block missing-block", errors[0])

    def test_unknown_citation_evidence_fails(self):
        data = {"sections": [], "citations": [{"id": "citation:test", "sourceRef": "source:known-source", "evidenceRef": "evidence:unknown"}]}
        errors = []
        VALIDATOR.validate_research_citation_integrity(data, {"source:known-source"}, [], errors)
        self.assertEqual(len(errors), 1)
        self.assertIn("unknown citation evidence evidence:unknown", errors[0])

    def test_citation_evidence_source_mismatch_fails(self):
        data = {"sections": [], "citations": [{"id": "citation:test", "sourceRef": "source:other-source", "evidenceRef": "evidence:known"}]}
        evidence = [{"id": "evidence:known", "source": "source:known-source"}]
        errors = []
        VALIDATOR.validate_research_citation_integrity(data, {"source:known-source", "source:other-source"}, evidence, errors)
        self.assertEqual(len(errors), 1)
        self.assertIn("citation evidence source mismatch", errors[0])


    def test_citation_end_exceeding_block_text_fails(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "content": [
                        {
                            "id": "block-one",
                            "type": "paragraph",
                            "text": "متن کوتاه",
                        }
                    ],
                }
            ],
            "citations": [
                {
                    "id": "citation:test",
                    "sourceRef": "source:known-source",
                    "contentBlockId": "block-one",
                    "start": 0,
                    "end": 100,
                }
            ],
        }

        errors = []
        VALIDATOR.validate_research_citation_integrity(
            data,
            {"source:known-source"},
            [],
            errors,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "citation end exceeds content block text length",
            errors[0],
        )


    def test_unknown_mention_content_block_fails(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "title": {"fa": "بخش اول"},
                    "content": [
                        {
                            "id": "block-one",
                            "type": "paragraph",
                            "text": "متن پژوهش",
                        }
                    ],
                    "mentions": [
                        {
                            "id": "mention:test",
                            "text": "پژوهش",
                            "entityRef": "concept:subject",
                            "contentBlockId": "missing-block",
                            "start": 0,
                            "end": 7,
                            "resolutionStatus": "RESOLVED",
                        }
                    ],
                }
            ]
        }

        errors = []
        VALIDATOR.validate_research_mention_integrity(
            data,
            {"concept:subject"},
            errors,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "unknown mention content block missing-block",
            errors[0],
        )


    def test_mention_content_block_must_belong_to_same_section(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "title": {"fa": "بخش اول"},
                    "content": [],
                    "mentions": [
                        {
                            "id": "mention:test",
                            "text": "پژوهش",
                            "entityRef": "concept:subject",
                            "contentBlockId": "block-two",
                            "start": 0,
                            "end": 2,
                            "resolutionStatus": "RESOLVED",
                        }
                    ],
                },
                {
                    "id": "section-two",
                    "title": {"fa": "بخش دوم"},
                    "content": [
                        {
                            "id": "block-two",
                            "type": "paragraph",
                            "text": "متن پژوهش",
                        }
                    ],
                    "mentions": [],
                },
            ]
        }

        errors = []
        VALIDATOR.validate_research_mention_integrity(
            data,
            {"concept:subject"},
            errors,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "unknown mention content block block-two",
            errors[0],
        )


    def test_mention_start_and_end_must_be_provided_together(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "title": {"fa": "بخش اول"},
                    "content": [
                        {
                            "id": "block-one",
                            "type": "paragraph",
                            "text": "متن پژوهش",
                        }
                    ],
                    "mentions": [
                        {
                            "id": "mention:test",
                            "text": "پژوهش",
                            "entityRef": "concept:subject",
                            "contentBlockId": "block-one",
                            "start": 0,
                            "resolutionStatus": "RESOLVED",
                        }
                    ],
                }
            ]
        }

        errors = []
        VALIDATOR.validate_research_mention_integrity(
            data,
            {"concept:subject"},
            errors,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "mention start and end must be provided together",
            errors[0],
        )


    def test_mention_offsets_require_content_block(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "title": {"fa": "بخش اول"},
                    "content": [],
                    "mentions": [
                        {
                            "id": "mention:test",
                            "text": "پژوهش",
                            "entityRef": "concept:subject",
                            "start": 0,
                            "end": 7,
                            "resolutionStatus": "RESOLVED",
                        }
                    ],
                }
            ]
        }

        errors = []
        VALIDATOR.validate_research_mention_integrity(
            data,
            {"concept:subject"},
            errors,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "mention offsets require contentBlockId",
            errors[0],
        )


    def test_mention_offsets_require_textual_content_block(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "title": {"fa": "بخش اول"},
                    "content": [
                        {
                            "id": "figure-one",
                            "type": "figure",
                            "src": "figure.png",
                            "alt": "Figure",
                        }
                    ],
                    "mentions": [
                        {
                            "id": "mention:test",
                            "text": "پژوهش",
                            "entityRef": "concept:subject",
                            "contentBlockId": "figure-one",
                            "start": 0,
                            "end": 7,
                            "resolutionStatus": "RESOLVED",
                        }
                    ],
                }
            ]
        }

        errors = []
        VALIDATOR.validate_research_mention_integrity(
            data,
            {"concept:subject"},
            errors,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "mention offsets require a textual content block",
            errors[0],
        )


    def test_mention_end_exceeding_block_text_fails(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "title": {"fa": "بخش اول"},
                    "content": [
                        {
                            "id": "block-one",
                            "type": "paragraph",
                            "text": "متن کوتاه",
                        }
                    ],
                    "mentions": [
                        {
                            "id": "mention:test",
                            "text": "کوتاه",
                            "entityRef": "concept:subject",
                            "contentBlockId": "block-one",
                            "start": 0,
                            "end": 100,
                            "resolutionStatus": "RESOLVED",
                        }
                    ],
                }
            ]
        }

        errors = []
        VALIDATOR.validate_research_mention_integrity(
            data,
            {"concept:subject"},
            errors,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "mention end exceeds content block text length",
            errors[0],
        )


    def test_mention_start_must_not_be_negative(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "title": {"fa": "بخش اول"},
                    "content": [
                        {
                            "id": "block-one",
                            "type": "paragraph",
                            "text": "متن پژوهش",
                        }
                    ],
                    "mentions": [
                        {
                            "id": "mention:test",
                            "text": "پژوهش",
                            "entityRef": "concept:subject",
                            "contentBlockId": "block-one",
                            "start": -1,
                            "end": 5,
                            "resolutionStatus": "RESOLVED",
                        }
                    ],
                }
            ]
        }

        errors = []
        VALIDATOR.validate_research_mention_integrity(
            data,
            {"concept:subject"},
            errors,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "mention start must not be negative",
            errors[0],
        )


    def test_mention_start_must_be_before_end(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "title": {"fa": "بخش اول"},
                    "content": [
                        {
                            "id": "block-one",
                            "type": "paragraph",
                            "text": "متن پژوهش",
                        }
                    ],
                    "mentions": [
                        {
                            "id": "mention:test",
                            "text": "پژوهش",
                            "entityRef": "concept:subject",
                            "contentBlockId": "block-one",
                            "start": 5,
                            "end": 5,
                            "resolutionStatus": "RESOLVED",
                        }
                    ],
                }
            ]
        }

        errors = []
        VALIDATOR.validate_research_mention_integrity(
            data,
            {"concept:subject"},
            errors,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "mention start must be before end",
            errors[0],
        )


    def test_resolved_mention_requires_known_entity(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "title": {"fa": "بخش اول"},
                    "content": [
                        {
                            "id": "block-one",
                            "type": "paragraph",
                            "text": "متن پژوهش",
                        }
                    ],
                    "mentions": [
                        {
                            "id": "mention:test",
                            "text": "پژوهش",
                            "entityRef": "concept:unknown",
                            "contentBlockId": "block-one",
                            "start": 4,
                            "end": 6,
                            "resolutionStatus": "RESOLVED",
                        }
                    ],
                }
            ]
        }

        errors = []
        VALIDATOR.validate_research_mention_integrity(
            data,
            {"concept:subject"},
            errors,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "unknown mention entity concept:unknown",
            errors[0],
        )


    def test_resolved_mention_requires_entity_ref(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "title": {"fa": "بخش اول"},
                    "content": [
                        {
                            "id": "block-one",
                            "type": "paragraph",
                            "text": "متن پژوهش",
                        }
                    ],
                    "mentions": [
                        {
                            "id": "mention:test",
                            "text": "پژوهش",
                            "entityRef": None,
                            "contentBlockId": "block-one",
                            "start": 4,
                            "end": 6,
                            "resolutionStatus": "RESOLVED",
                        }
                    ],
                }
            ]
        }

        errors = []
        VALIDATOR.validate_research_mention_integrity(
            data,
            {"concept:subject"},
            errors,
        )

        self.assertEqual(len(errors), 1)
        self.assertIn(
            "resolved mention requires entityRef",
            errors[0],
        )


    def test_unresolved_mention_does_not_require_known_entity(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "title": {"fa": "بخش اول"},
                    "content": [
                        {
                            "id": "block-one",
                            "type": "paragraph",
                            "text": "متن پژوهش",
                        }
                    ],
                    "mentions": [
                        {
                            "id": "mention:test",
                            "text": "پژوهش",
                            "entityRef": "concept:unknown",
                            "contentBlockId": "block-one",
                            "start": 4,
                            "end": 6,
                            "resolutionStatus": "UNRESOLVED",
                        }
                    ],
                }
            ]
        }

        errors = []
        VALIDATOR.validate_research_mention_integrity(
            data,
            {"concept:subject"},
            errors,
        )

        self.assertEqual(errors, [])


    def test_rejected_mention_does_not_require_known_entity(self):
        data = {
            "sections": [
                {
                    "id": "section-one",
                    "title": {"fa": "بخش اول"},
                    "content": [
                        {
                            "id": "block-one",
                            "type": "paragraph",
                            "text": "متن پژوهش",
                        }
                    ],
                    "mentions": [
                        {
                            "id": "mention:test",
                            "text": "پژوهش",
                            "entityRef": "concept:unknown",
                            "contentBlockId": "block-one",
                            "start": 4,
                            "end": 6,
                            "resolutionStatus": "REJECTED",
                        }
                    ],
                }
            ]
        }

        errors = []
        VALIDATOR.validate_research_mention_integrity(
            data,
            {"concept:subject"},
            errors,
        )

        self.assertEqual(errors, [])


    def test_unknown_mention_content_block_is_checked_by_research_integrity(self):
        self.write_research_document({
            "id": "section-one",
            "title": {
                "fa": "بخش اول",
            },
            "content": [
                {
                    "id": "block-one",
                    "type": "paragraph",
                    "text": "متن پژوهش",
                }
            ],
            "mentions": [
                {
                    "id": "mention:test",
                    "text": "پژوهش",
                    "entityRef": "concept:subject",
                    "contentBlockId": "missing-block",
                    "start": 0,
                    "end": 2,
                    "resolutionStatus": "RESOLVED",
                }
            ],
        })

        errors = []
        entity_ids = {"concept:subject"}

        original = VALIDATOR.validate_research_mention_integrity

        try:
            called = []

            def spy(research_data, entity_ids, validation_errors):
                called.append(research_data)

            VALIDATOR.validate_research_mention_integrity = spy

            VALIDATOR.validate_research_documents(
                errors,
                entity_ids,
            )

            self.assertTrue(called)
        finally:
            VALIDATOR.validate_research_mention_integrity = original



if __name__ == "__main__":
    unittest.main()
