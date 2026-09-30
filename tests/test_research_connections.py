"""Regression fixtures for the two independent Research navigation contracts."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "research_connections", ROOT / "atlas/tools/research_connections.py"
)
connections = importlib.util.module_from_spec(spec)
spec.loader.exec_module(connections)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


class ResearchConnectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.catalog = [
            {"id": "concept:one", "type": "Concept", "lifecycleStatus": "PUBLISHED",
             "route": "/atlas/concept/one/", "name": {"fa": "یک", "en": "One"}},
            {"id": "concept:two", "type": "Concept", "lifecycleStatus": "PUBLISHED",
             "route": "/atlas/concept/two/", "name": {"fa": "دو", "en": "Two"}},
            {"id": "concept:review", "type": "Concept", "lifecycleStatus": "REVIEW",
             "route": "/atlas/concept/review/", "name": {"fa": "بازبینی"}},
            {"id": "sector:no-route", "type": "Sector", "lifecycleStatus": "PUBLISHED",
             "name": {"fa": "بدون مسیر"}},
        ]
        self.registry = []

    def add_article(self, slug, refs=(), *, status="PUBLISHED", registry_status=None,
                    mentions=(), related=()):
        article_id = "research:" + slug
        url = "/articles/" + slug + ".html"
        self.registry.append({"id": article_id, "url": url,
                              "status": registry_status or status})
        article = {
            "id": article_id, "type": "Research", "status": status,
            "url": url, "title": {"fa": slug},
            "publication": {"datePublished": "2026-01-01"},
            "entityRefs": list(refs), "relatedResearchRefs": list(related),
            "sections": [{"mentions": list(mentions)}],
        }
        write(self.root / "research/content" / (slug + ".json"), article)
        path = self.root / url.lstrip("/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"<h1>{slug}</h1>", encoding="utf-8")
        write(self.root / "research/index.json", {"research": self.registry})
        return article

    def test_one_or_many_articles_and_entities_are_deduplicated(self):
        first = self.add_article("first", ["concept:one", "concept:one", "concept:two"],
                                 mentions=[{"entityRef": "concept:one"}] * 3)
        self.add_article("second", ["concept:one"])
        self.add_article("none")
        index = connections.reverse_index(self.root, self.catalog)
        self.assertEqual([item["id"] for item in index["entities"]["concept:one"]],
                         ["research:first", "research:second"])
        self.assertEqual(len(index["entities"]["concept:two"]), 1)
        self.assertEqual(len(index["entities"]), 2)
        panel = connections.render_article_context(first, self.catalog, self.root)
        self.assertEqual(panel.count('href="/atlas/concept/one/"'), 1)
        self.assertIn('href="/atlas/concept/two/"', panel)
        self.assertEqual(connections.render_atlas_research("concept:two", index).count(
            'href="/articles/first.html"'), 1)
        self.assertEqual(connections.render_atlas_research("concept:unknown", index), "")

    def test_publication_and_routes_filter_both_directions(self):
        article = self.add_article("first", ["concept:one", "concept:review", "sector:no-route"])
        self.add_article("draft", ["concept:one"], status="DRAFT")
        self.add_article("registry-draft", ["concept:one"], registry_status="DRAFT")
        index = connections.reverse_index(self.root, self.catalog)
        self.assertEqual(list(index["entities"]), ["concept:one"])
        self.assertEqual(len(index["entities"]["concept:one"]), 1)
        public_panel = connections.render_article_context(article, self.catalog, self.root)
        self.assertNotIn("concept/review", public_panel)
        self.assertNotIn("sector/no-route", public_panel)
        preview_url = lambda entity_id, entity_type: (
            "/atlas/_preview/review/" if entity_id == "concept:review" else
            "/atlas/concept/one/" if entity_id == "concept:one" else None
        )
        preview_index = connections.reverse_index(
            self.root, self.catalog, preview=True, preview_resolver=preview_url,
        )
        self.assertIn("concept:review", preview_index["entities"])
        self.assertNotIn("sector:no-route", preview_index["entities"])
        self.assertIn("/atlas/_preview/review/", connections.render_article_context(
            article, self.catalog, self.root, preview=True, preview_resolver=preview_url,
        ))

    def test_missing_entity_fails_with_research_id(self):
        self.add_article("broken", ["concept:missing"])
        with self.assertRaisesRegex(ValueError, "research:broken.*concept:missing"):
            connections.reverse_index(self.root, self.catalog)

    def test_missing_or_unsafe_research_page_fails_closed(self):
        article = self.add_article("first", ["concept:one"])
        page = self.root / article["url"].lstrip("/")
        page.unlink()
        with self.assertRaisesRegex(ValueError, "research:first.*page missing"):
            connections.reverse_index(self.root, self.catalog)
        article["url"] = "/articles/../../private.html"
        self.registry[0]["url"] = article["url"]
        write(self.root / "research/content/first.json", article)
        write(self.root / "research/index.json", {"research": self.registry})
        with self.assertRaisesRegex(ValueError, "research:first.*invalid Research URL"):
            connections.reverse_index(self.root, self.catalog)

    def test_curated_related_research_does_not_affect_entity_index(self):
        first = self.add_article("first", ["concept:one"], related=["research:second"])
        self.add_article("second")
        index = connections.reverse_index(self.root, self.catalog)
        self.assertEqual(len(index["entities"]["concept:one"]), 1)
        panel = connections.render_article_context(first, self.catalog, self.root)
        self.assertIn('href="/articles/second.html"', panel)
        self.assertIn('id="research-related-heading"', panel)
        self.assertEqual(connections.render_article_context(
            self.add_article("empty"), self.catalog, self.root), "")
        first["relatedResearchRefs"] = ["research:absent"]
        with self.assertRaisesRegex(ValueError, "research:first.*research:absent"):
            connections.render_article_context(first, self.catalog, self.root)

    def test_real_published_article_has_six_preview_refs_and_no_public_refs(self):
        root = ROOT
        catalog = connections.read_json(root / "atlas/catalog/index.json")["entities"]
        article = connections.read_json(root / "research/content/private-capital.json")
        self.assertEqual(len(article["entityRefs"]), 6)
        self.assertEqual(connections.reverse_index(root, catalog)["entities"], {})
        panel = connections.render_article_context(article, catalog, root)
        self.assertNotIn('id="research-atlas-heading"', panel)
        self.assertIn('/articles/what-is-private-equity.html', panel)


if __name__ == "__main__":
    unittest.main()
