import json
import unittest


class PredicateArchitectureTests(unittest.TestCase):
    def test_every_relation_type_has_a_rule(self):
        with open("atlas/taxonomies/relation-types.json", encoding="utf-8") as f:
            relation_types = {item["id"] for item in json.load(f)["relation_types"]}
        with open("atlas/taxonomies/relation-rules.json", encoding="utf-8") as f:
            rules = {item["relation"] for item in json.load(f)["rules"]}
        self.assertEqual(relation_types, rules)


if __name__ == "__main__":
    unittest.main()
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
