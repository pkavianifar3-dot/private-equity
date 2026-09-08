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
