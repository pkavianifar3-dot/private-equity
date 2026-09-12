import json
import unittest


class RelationRenderingContractTests(unittest.TestCase):
    def test_rendering_relations_are_known_predicates(self):
        with open("atlas/taxonomies/relation-types.json", encoding="utf-8") as f:
            predicates = {item["id"] for item in json.load(f)["relation_types"]}
        with open("atlas/taxonomies/relation-rendering.json", encoding="utf-8") as f:
            relations = json.load(f)["relations"]
        self.assertTrue(set(relations).issubset(predicates))

    def test_reverse_labels_are_non_empty_strings(self):
        with open("atlas/taxonomies/relation-rendering.json", encoding="utf-8") as f:
            relations = json.load(f)["relations"]
        for predicate, config in relations.items():
            self.assertIsInstance(config["reverse_label_fa"], str)
            self.assertTrue(config["reverse_label_fa"].strip(), predicate)


if __name__ == "__main__":
    unittest.main()
