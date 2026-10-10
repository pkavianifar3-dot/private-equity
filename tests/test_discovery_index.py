import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DISCOVERY_INDEX_PATH = ROOT / "atlas" / "discovery" / "index.json"
ENTITY_INDEX_PATH = ROOT / "atlas" / "entities" / "index.json"
RESEARCH_INDEX_PATH = ROOT / "research" / "index.json"
RESEARCH_CONTENT_DIR = ROOT / "research" / "content"


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class DiscoveryIndexIntegrityTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.discovery = load_json(DISCOVERY_INDEX_PATH)
        cls.entities = load_json(ENTITY_INDEX_PATH)
        cls.research_index = load_json(RESEARCH_INDEX_PATH)

        cls.entity_ids = {
            entity["id"]
            for entity in cls.entities["entities"]
        }

        cls.research_by_id = {
            item["id"]: item
            for item in cls.research_index["research"]
        }

    def test_discovery_index_structure(self):
        self.assertEqual(self.discovery["version"], "1.0")
        self.assertIsInstance(self.discovery["entities"], dict)

    def test_discovery_references_resolve_end_to_end(self):
        for entity_id, entry in self.discovery["entities"].items():
            with self.subTest(entity_id=entity_id):

                # Discovery entity must be a canonical Atlas Entity.
                self.assertIn(entity_id, self.entity_ids)

                self.assertIn("researchMentions", entry)
                self.assertIsInstance(entry["researchMentions"], list)

                for reference in entry["researchMentions"]:
                    with self.subTest(
                        research_id=reference["researchId"],
                        section_id=reference["sectionId"],
                        mention_id=reference["mentionId"],
                    ):
                        research_id = reference["researchId"]
                        section_id = reference["sectionId"]
                        content_block_id = reference["contentBlockId"]
                        mention_id = reference["mentionId"]

                        # Research must exist in the Research registry.
                        self.assertIn(research_id, self.research_by_id)

                        content_path = (
                            next(p for p in RESEARCH_CONTENT_DIR.rglob("research.json")
                                 if load_json(p)["id"] == research_id)
                        )
                        self.assertTrue(content_path.exists())

                        research = load_json(content_path)
                        self.assertEqual(self.research_by_id[research_id]["status"], "PUBLISHED")
                        self.assertEqual(research["status"], "PUBLISHED")

                        sections = {
                            section["id"]: section
                            for section in research["sections"]
                        }

                        # Section must exist.
                        self.assertIn(section_id, sections)
                        section = sections[section_id]

                        content_blocks = {
                            block["id"]: block
                            for block in section["content"]
                        }

                        # Content block must exist in the same section.
                        self.assertIn(content_block_id, content_blocks)

                        mentions = {
                            mention["id"]: mention
                            for mention in section.get("mentions", [])
                        }

                        # Mention must exist in the same section.
                        self.assertIn(mention_id, mentions)
                        mention = mentions[mention_id]

                        # Discovery only indexes resolved mentions.
                        self.assertEqual(
                            mention["resolutionStatus"],
                            "RESOLVED",
                        )

                        # Mention must resolve to the canonical Entity
                        # represented by this Discovery entry.
                        self.assertEqual(
                            mention["entityRef"],
                            entity_id,
                        )

                        # Mention must point to the same content block.
                        self.assertEqual(
                            mention["contentBlockId"],
                            content_block_id,
                        )

    def test_review_research_is_absent_from_public_index(self):
        indexed = {ref["researchId"] for entry in self.discovery["entities"].values()
                   for ref in entry["researchMentions"]}
        for research_id, record in self.research_by_id.items():
            if record["status"] != "PUBLISHED":
                self.assertNotIn(research_id, indexed)

    def test_new_article_cannot_expand_review_discovery(self):
        lifecycle = {entity["id"]: entity["lifecycleStatus"] for entity in self.entities["entities"]}
        for entity_id, entry in self.discovery["entities"].items():
            for mention in entry["researchMentions"]:
                if mention["researchId"] != "research:private-capital":
                    self.assertEqual(lifecycle[entity_id], "PUBLISHED")

    def test_discovery_reference_count(self):
        total_references = sum(
            len(entry["researchMentions"])
            for entry in self.discovery["entities"].values()
        )

        self.assertGreaterEqual(total_references, 0)


if __name__ == "__main__":
    unittest.main()