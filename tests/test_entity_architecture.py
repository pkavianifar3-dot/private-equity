import importlib.util
import unittest

SPEC = importlib.util.spec_from_file_location(
    "validate_atlas", "atlas/tools/validate-atlas.py"
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class EntityArchitectureTests(unittest.TestCase):

    def test_valid_namespace_matches_entity_type(self):
        errors = []
        VALIDATOR.validate_entity_identity(
            {"id": "organization:test-org", "type": "Organization"},
            "test",
            errors,
        )
        self.assertEqual(errors, [])

    def test_invalid_namespace_is_rejected(self):
        errors = []
        VALIDATOR.validate_entity_identity(
            {"id": "person:test-org", "type": "Organization"},
            "test",
            errors,
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("namespace does not match", errors[0])

    def test_type_specific_field_is_allowed(self):
        errors = []
        VALIDATOR.validate_entity_type_fields(
            {
                "id": "organization:test-org",
                "type": "Organization",
                "organization_type": "private_company",
            },
            "test",
            errors,
        )
        self.assertEqual(errors, [])

    def test_wrong_type_specific_field_is_rejected(self):
        errors = []
        VALIDATOR.validate_entity_type_fields(
            {
                "id": "concept:test",
                "type": "Concept",
                "organization_type": "private_company",
            },
            "test",
            errors,
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("not valid for entity type Concept", errors[0])

    def test_domain_must_reference_sector(self):
        errors = []
        entities = {
            "sector:test-sector": {"type": "Sector"},
        }
        VALIDATOR.validate_entity_domains(
            {"id": "person:test", "type": "Person", "domains": ["sector:test-sector"]},
            entities,
            "test",
            errors,
        )
        self.assertEqual(errors, [])

    def test_domain_to_non_sector_is_rejected(self):
        errors = []
        entities = {
            "concept:test": {"type": "Concept"},
        }
        VALIDATOR.validate_entity_domains(
            {"id": "person:test", "type": "Person", "domains": ["concept:test"]},
            entities,
            "test",
            errors,
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("must reference a Sector", errors[0])

    def test_missing_domain_is_rejected(self):
        errors = []
        VALIDATOR.validate_entity_domains(
            {"id": "person:test", "type": "Person", "domains": ["sector:missing"]},
            {},
            "test",
            errors,
        )
        self.assertEqual(len(errors), 1)
        self.assertIn("missing from entities/index.json", errors[0])
