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
    def test_every_rule_has_temporal_and_inverse_contract(self):
        with open("atlas/taxonomies/relation-rules.json", encoding="utf-8") as f:
            rules = json.load(f)["rules"]

        for rule in rules:
            self.assertIn("inverse", rule, rule["relation"])
            self.assertIsInstance(rule["inverse"], (str, type(None)), rule["relation"])
            self.assertIn("temporalAllowed", rule, rule["relation"])
            self.assertIsInstance(rule["temporalAllowed"], bool, rule["relation"])

    def test_inverse_relationships_are_symmetric(self):
        with open("atlas/taxonomies/relation-rules.json", encoding="utf-8") as f:
            rules = json.load(f)["rules"]

        by_relation = {rule["relation"]: rule for rule in rules}

        for relation, rule in by_relation.items():
            inverse = rule["inverse"]
            if inverse is None:
                continue

            self.assertIn(inverse, by_relation, relation)
            self.assertEqual(
                by_relation[inverse]["inverse"],
                relation,
                relation,
            )

    def test_cardinality_contract_for_entity_relations(self):
        with open("atlas/taxonomies/relation-rules.json", encoding="utf-8") as f:
            rules = json.load(f)["rules"]

        for rule in rules:
            if "object_types" in rule:
                self.assertIn("cardinality", rule, rule["relation"])
                self.assertEqual("many-to-many", rule["cardinality"], rule["relation"])
            else:
                self.assertNotIn("cardinality", rule, rule["relation"])

    def test_temporal_is_rejected_when_predicate_disallows_it(self):
        errors = []
        claims = [{
            "id": "claim:temporal-not-allowed",
            "subject": "concept:a",
            "predicate": "BROADER_THAN",
            "object": "concept:b",
            "temporal": {
                "precision": "year",
                "start": "1404",
                "end": None
            }
        }]
        entities = {
            "concept:a": {"type": "Concept"},
            "concept:b": {"type": "Concept"}
        }
        relation_types = {"BROADER_THAN"}
        relation_rules = {
            "BROADER_THAN": {
                "subject_types": ["Concept"],
                "object_types": ["Concept"],
                "temporalAllowed": False
            }
        }

        VALIDATOR.validate_claim_integrity(
            claims,
            entities,
            set(entities),
            relation_types,
            relation_rules,
            set(),
            errors
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("does not allow temporal", errors[0])

    def test_temporal_is_allowed_when_predicate_allows_it(self):
        errors = []
        claims = [{
            "id": "claim:temporal-allowed",
            "subject": "organization:a",
            "predicate": "WORKED_AT",
            "object": "organization:b",
            "temporal": {
                "precision": "year",
                "start": "1404",
                "end": None
            }
        }]
        entities = {
            "organization:a": {"type": "Organization"},
            "organization:b": {"type": "Organization"}
        }
        relation_types = {"WORKED_AT"}
        relation_rules = {
            "WORKED_AT": {
                "subject_types": ["Organization"],
                "object_types": ["Organization"],
                "temporalAllowed": True
            }
        }

        VALIDATOR.validate_claim_integrity(
            claims,
            entities,
            set(entities),
            relation_types,
            relation_rules,
            set(),
            errors
        )

        self.assertEqual(errors, [])

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

        self.assertEqual(relation_types, set(rendering))
        self.assertEqual(relation_types, rules)

        for predicate, config in rendering.items():
            self.assertIsInstance(config["forward_label_fa"], str)
            self.assertTrue(config["forward_label_fa"].strip(), predicate)
            self.assertIsInstance(config["forward_label_en"], str)
            self.assertTrue(config["forward_label_en"].strip(), predicate)
            self.assertIn("reverse_label_fa", config)
            self.assertIsInstance(config["subject_types"], list)
            self.assertIsInstance(config["object_types"], list)
            self.assertIsInstance(config["reverse_display_allowed"], bool)

            if config["reverse_display_allowed"]:
                self.assertIsInstance(config["reverse_label_fa"], str)
                self.assertTrue(config["reverse_label_fa"].strip(), predicate)
            else:
                self.assertIsNone(config["reverse_label_fa"], predicate)


if __name__ == "__main__":
    unittest.main()
