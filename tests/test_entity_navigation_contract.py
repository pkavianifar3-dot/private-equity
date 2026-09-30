"""Verify existing public paths and direction policies before the stage 3 URL gate."""
import importlib.util
import json
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]


def load_builder(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "atlas/tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CATALOG = load_builder("build-catalog")
STATIC = load_builder("build-static-pages")


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.canonicals = []
        self.entity = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonicals.append(attrs.get("href"))
        if attrs.get("id") == "atlas-root":
            self.entity = attrs


class EntityNavigationContractTests(unittest.TestCase):
    def test_catalog_static_builders_and_pages_agree(self):
        self.assertEqual(CATALOG.ROUTES, STATIC.ROUTES)
        entries = json.loads((ROOT / "atlas/catalog/index.json").read_text(encoding="utf-8"))["entities"]
        entities = STATIC.load_entities()
        self.assertEqual({e["id"] for e in entries}, set(entities))
        for entry in entries:
            with self.subTest(entity=entry["id"]):
                url = CATALOG.entity_url(entry["id"], entry["type"])
                self.assertEqual(url, STATIC.entity_url(entry["id"], entry["type"]))
                self.assertEqual(url, entry.get("route"))
                if not url:
                    continue
                page = ROOT / url.lstrip("/") / "index.html"
                parser = PageLinks()
                parser.feed(page.read_text(encoding="utf-8"))
                self.assertEqual(parser.canonicals, ["https://privatecapital.ir" + url])
                self.assertEqual(parser.entity["data-entity-id"], entry["id"])
                self.assertEqual(parser.entity["data-static-rendered"], "true")
                for href in parser.links:
                    parsed = urlparse(href)
                    if parsed.scheme or parsed.netloc or not parsed.path:
                        continue
                    path = unquote(parsed.path)
                    target = ROOT / path.lstrip("/") if path.startswith("/") else page.parent / path
                    self.assertTrue(target.is_file() or (target / "index.html").is_file(), f"{page}: {href}")

    def test_missing_or_unsupported_route_inputs_are_controlled(self):
        for resolver in (CATALOG.entity_url, STATIC.entity_url):
            for entity_id in (None, 42, {}, [], "", "invalid", "person:"):
                with self.subTest(resolver=resolver.__module__, entity_id=entity_id):
                    self.assertIsNone(resolver(entity_id, "Person"))
            for entity_type in (None, {}, [], 42, "OrganizationUnit", "Project", "Sector", "Fund", "InvestorCategory"):
                self.assertIsNone(resolver("organization:test", entity_type))

    def test_live_claims_obey_forward_and_reverse_contract(self):
        contract = STATIC.load_relation_contract()
        entities = STATIC.load_entities()
        for claim in STATIC.load_claims():
            with self.subTest(claim=claim["id"]):
                forward = STATIC.render_claim_relation(claim, claim["subject"], contract)
                if not claim.get("object"):
                    self.assertIsNone(forward)
                    continue
                config = contract["relations"][claim["predicate"]]
                self.assertEqual(forward, {"direction": "forward", "target_id": claim["object"], "label": config["forward_label_fa"]})
                reverse = STATIC.render_claim_relation(claim, claim["object"], contract)
                if config["reverse_display_allowed"] is True:
                    self.assertEqual(reverse, {"direction": "reverse", "target_id": claim["subject"], "label": config["reverse_label_fa"]})
                else:
                    self.assertIsNone(reverse)
                self.assertIsNone(STATIC.render_claim_relation(claim, "concept:unrelated", contract))
                for current, direction in ((claim["subject"], forward), (claim["object"], reverse)):
                    rendered = STATIC.render_claims([claim], current, entities, contract)
                    if not direction:
                        self.assertNotIn("atlas-relations-overview", rendered)
                        continue
                    self.assertIn(direction["label"], rendered)
                    target = entities[direction["target_id"]]
                    target_url = STATIC.entity_url(target["id"], target["type"])
                    if target_url:
                        self.assertIn(f'href="{target_url}"', rendered)
                    else:
                        self.assertNotIn('href="/atlas/', rendered)

    def test_incomplete_relations_and_non_boolean_reverse_flag_are_hidden(self):
        contract = STATIC.load_relation_contract()
        sample = {"subject": "concept:a", "object": "concept:b", "predicate": "INCLUDES"}
        for claim in (None, [], {}, dict(sample, object=None), dict(sample, object="concept:a"), dict(sample, predicate=[])):
            self.assertIsNone(STATIC.render_claim_relation(claim, "concept:a", contract))
        for label in (None, 7, {}, "", "  "):
            config = dict(contract["relations"]["INCLUDES"], forward_label_fa=label, reverse_label_fa=label)
            for current in ("concept:a", "concept:b"):
                self.assertIsNone(STATIC.render_claim_relation(sample, current, {"relations": {"INCLUDES": config}}))
        for flag in (False, None, "true", 1):
            config = dict(contract["relations"]["INCLUDES"], reverse_display_allowed=flag)
            self.assertIsNone(STATIC.render_claim_relation(sample, "concept:b", {"relations": {"INCLUDES": config}}))
        self.assertIsNone(STATIC.render_claim_relation(sample, "concept:a", {"relations": []}))


if __name__ == "__main__":
    unittest.main()
