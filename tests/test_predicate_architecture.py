import json
import importlib.util
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location(
    "validate_atlas",
    Path("atlas/tools/validate-atlas.py")
)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class PredicateArchitectureTests(unittest.TestCase):
    def test_every_relation_type_has_a_rule(self):
        with open("atlas/taxonomies/relation-types.json", encoding="utf-8") as f:
            relation_types = {item["id"] for item in json.load(f)["relation_types"]}
        with open("atlas/taxonomies/relation-rules.json", encoding="utf-8") as f:
            rules = {item["relation"] for item in json.load(f)["rules"]}
        self.assertEqual(relation_types, rules)

    def test_every_rule_references_a_relation_type(self):
        with open("atlas/taxonomies/relation-types.json", encoding="utf-8") as f:
            relation_types = {item["id"] for item in json.load(f)["relation_types"]}
        with open("atlas/taxonomies/relation-rules.json", encoding="utf-8") as f:
            rules = {item["relation"] for item in json.load(f)["rules"]}
        self.assertEqual(rules, relation_types)
    def test_value_predicate_enforces_value_type(self):
        errors = []
        entities = {"investment:test": {"type": "Investment"}}
        relations = {"INVESTMENT_AMOUNT"}
        rules = {"INVESTMENT_AMOUNT": {"subject_types": ["Investment"], "value_type": "amount"}}
        valid = {"id": "claim:valid", "subject": "investment:test", "predicate": "INVESTMENT_AMOUNT", "value": {"amount": 10, "currency": "USD", "unit": "amount", "raw": "10", "period_type": "reported"}}
        VALIDATOR.validate_claim_integrity([valid], entities, set(entities), relations, rules, set(), errors)
        self.assertEqual(errors, [])

        errors = []
        invalid = dict(valid, id="claim:invalid", value=dict(valid["value"], unit="percentage"))
        VALIDATOR.validate_claim_integrity([invalid], entities, set(entities), relations, rules, set(), errors)
        self.assertEqual(len(errors), 1)
        self.assertIn("does not match expected value type", errors[0])
    def test_every_relation_rendering_is_a_known_relation(self):
        with open("atlas/taxonomies/relation-types.json", encoding="utf-8") as f:
            relation_types = {item["id"] for item in json.load(f)["relation_types"]}
        with open("atlas/taxonomies/relation-rules.json", encoding="utf-8") as f:
            rules = {item["relation"] for item in json.load(f)["rules"]}
        with open("atlas/taxonomies/relation-rendering.json", encoding="utf-8") as f:
            rendering = json.load(f)["relations"]

        self.assertTrue(set(rendering).issubset(relation_types))
        self.assertTrue(set(rendering).issubset(rules))

        for predicate, config in rendering.items():
            self.assertIsInstance(config["reverse_label_fa"], str)
            self.assertTrue(config["reverse_label_fa"].strip(), predicate)


if __name__ == "__main__":
    unittest.main()
