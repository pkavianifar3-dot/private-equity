import json
import unittest


class RelationRenderingContractTests(unittest.TestCase):
    def test_rendering_relations_are_known_predicates(self):
        with open("atlas/taxonomies/relation-types.json", encoding="utf-8") as f:
            predicates = {item["id"] for item in json.load(f)["relation_types"]}
        with open("atlas/taxonomies/relation-rendering.json", encoding="utf-8") as f:
            relations = json.load(f)["relations"]
        self.assertTrue(set(relations).issubset(predicates))

    def test_relation_rendering_contract_shape(self):
        with open("atlas/taxonomies/relation-rendering.json", encoding="utf-8") as f:
            relations = json.load(f)["relations"]

        for predicate, config in relations.items():
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
