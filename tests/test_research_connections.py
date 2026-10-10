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
                    mentions=(), related=(), primary=None):
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
        if primary is not None:
            article["primaryEntityRef"] = primary
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
        index = connections.reverse_index(self.root, self.catalog)
        self.assertEqual(list(index["entities"]), ["concept:one"])
        self.assertEqual(len(index["entities"]["concept:one"]), 1)
        self.add_article("registry-draft", ["concept:one"], registry_status="DRAFT")
        with self.assertRaisesRegex(ValueError, "research:registry-draft.*URL/status"):
            connections.reverse_index(self.root, self.catalog)
        self.registry.pop()
        (self.root / "research/content/registry-draft.json").unlink()
        write(self.root / "research/index.json", {"research": self.registry})
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

    def test_same_subject_is_automatic_bidirectional_and_title_independent(self):
        first = self.add_article("first", ["concept:one"], primary="concept:one")
        second = self.add_article("second", ["concept:one"], primary="concept:one")
        self.add_article("mention-only", ["concept:one"], mentions=[{"entityRef":"concept:one"}])
        self.add_article("other-subject", ["concept:one","concept:two"], primary="concept:two")
        select = connections.research_selector(self.root, self.catalog)
        self.assertEqual(select(first,self.root), [{"url":"/articles/second.html", "title":"second", "reason":"same-primary-entity"}])
        self.assertEqual(select(second,self.root)[0]["url"], "/articles/first.html")
        self.assertEqual(select({**first,"primaryEntityRef":None},self.root), [])

    def test_editorial_priority_self_dedup_status_and_stable_peer_order(self):
        first = self.add_article("first", ["concept:one"], primary="concept:one",
                                 related=["research:z", "research:b", "research:z", "research:first", "research:review"])
        self.add_article("z")
        self.add_article("b", ["concept:one"], primary="concept:one")
        self.add_article("a", ["concept:one"], primary="concept:one")
        for status in ["DRAFT","REVIEW","ARCHIVED"]:
            self.add_article(status.lower(), ["concept:one"], status=status, primary="concept:one")
        select = connections.research_selector(self.root, self.catalog)
        selected = select(first,self.root)
        self.assertEqual([row["url"] for row in selected], ["/articles/z.html","/articles/b.html","/articles/a.html"])
        self.assertEqual([row["reason"] for row in selected], ["editorial","editorial","same-primary-entity"])
        self.assertEqual(select(first,self.root),selected)

    def test_review_entity_subject_does_not_expand_public_atlas(self):
        first = self.add_article("first", ["concept:review"], primary="concept:review")
        self.add_article("second", ["concept:review"], primary="concept:review")
        select = connections.research_selector(self.root, self.catalog)
        self.assertEqual(select(first,self.root)[0]["url"], "/articles/second.html")
        self.assertEqual(connections.reverse_index(self.root,self.catalog)["entities"],{})
        panel = connections.render_article_context(first,self.catalog,self.root,related_selector=select)
        self.assertNotIn('/atlas/concept/review/',panel)

    def test_invalid_primary_and_missing_peer_page_fail_with_owner(self):
        first = self.add_article("bad", ["concept:one"], primary="concept:missing")
        with self.assertRaisesRegex(ValueError, "research:bad.*primaryEntityRef.*entityRefs"):
            connections.research_selector(self.root,self.catalog)
        first["entityRefs"].append("concept:missing")
        write(self.root/"research/content/bad.json",first)
        with self.assertRaisesRegex(ValueError,"research:bad.*unknown primaryEntityRef"):
            connections.research_selector(self.root,self.catalog)
        first["primaryEntityRef"]="concept:one"
        write(self.root/"research/content/bad.json",first)
        second=self.add_article("second",["concept:one"],primary="concept:one")
        (self.root/second["url"].lstrip('/')).unlink()
        with self.assertRaisesRegex(ValueError,"research:bad.*page missing"):
            connections.research_selector(self.root,self.catalog)(first,self.root)

    def test_selection_caps_peers_and_reuses_a_consistent_build_snapshot(self):
        first=self.add_article("root",["concept:one"],primary="concept:one")
        for n in reversed(range(12)):
            self.add_article(f"peer-{n:02d}",["concept:one"],primary="concept:one")
        select=connections.research_selector(self.root,self.catalog)
        expected=[f"/articles/peer-{n:02d}.html" for n in range(8)]
        self.assertEqual([row["url"] for row in select(first,self.root)],expected)
        self.add_article("new-earlier",["concept:one"],primary="concept:one")
        self.assertEqual([row["url"] for row in select(first,self.root)],expected)
        self.assertEqual(connections.research_selector(self.root,self.catalog)(first,self.root)[0]["url"],
                         "/articles/new-earlier.html")
        with self.assertRaisesRegex(ValueError,"research:root.*research:absent"):
            select({**first,"relatedResearchRefs":["research:absent"]},self.root)

    def test_real_articles_share_confirmed_subject_without_needing_editorial_edge(self):
        catalog=connections.read_json(ROOT/"atlas/catalog/index.json")["entities"]
        select=connections.research_selector(ROOT,catalog)
        for slug,other in [("private-capital","private-capital-research"),("private-capital-research","private-capital")]:
            article=connections.read_json(ROOT/f"research/content/private-markets/{slug}/research.json")
            self.assertEqual(article["primaryEntityRef"],"concept:private-capital")
            automatic=select({**article,"relatedResearchRefs":[]},ROOT)
            self.assertEqual(automatic,[{"url":f"/articles/{other}.html",
                                          "title":connections.structured_articles(ROOT)[f"research:{other}"]["title"]["fa"],
                                          "reason":"same-primary-entity"}])

    def test_real_published_article_has_six_preview_refs_and_no_public_refs(self):
        root = ROOT
        catalog = connections.read_json(root / "atlas/catalog/index.json")["entities"]
        article = connections.read_json(root / "research/content/private-markets/private-capital/research.json")
        self.assertEqual(len(article["entityRefs"]), 6)
        self.assertEqual(connections.reverse_index(root, catalog)["entities"], {})
        panel = connections.render_article_context(article, catalog, root)
        self.assertNotIn('id="research-atlas-heading"', panel)
        self.assertIn('/articles/what-is-private-equity.html', panel)


if __name__ == "__main__":
    unittest.main()
