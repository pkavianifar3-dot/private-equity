"""Local-only Entity preview must leave the public build and URLs intact."""

import importlib.util
import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("entity_preview", ROOT / "atlas/tools/preview-entities.py")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href"):
            self.hrefs.append(attrs["href"])


class EntityPreviewTests(unittest.TestCase):
    def test_preview_routes_are_explicit_and_namespace_safe(self):
        self.assertEqual(
            preview.preview_entity_url("project:dadman", "Project"),
            "/atlas/_preview/project/dadman/",
        )
        self.assertEqual(
            preview.preview_entity_url(
                "organization:tehran-chamber-money-capital-commission", "OrganizationUnit"
            ),
            "/atlas/_preview/organization-unit/tehran-chamber-money-capital-commission/",
        )
        for entity_id, entity_type in (
            ("project:dadman", "OrganizationUnit"),
            ("organization:tehran-chamber-money-capital-commission", "Project"),
            ("sector:private-equity", "Sector"),
            ("project:", "Project"),
            (None, "Project"),
        ):
            self.assertIsNone(preview.preview_entity_url(entity_id, entity_type))
        self.assertEqual(
            preview.preview_entity_url("person:ali-sanginian", "Person"),
            "/atlas/person/ali-sanginian/",
        )

    def test_preview_catalog_pages_links_and_public_isolation(self):
        public_catalog_path = ROOT / "atlas/catalog/index.json"
        before = public_catalog_path.read_bytes()
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir)
            generated = preview.build_preview(output)
            handler = object.__new__(preview.PreviewHandler)
            handler.directory = str(output)
            self.assertEqual(Path(handler.translate_path("/")), ROOT)
            self.assertEqual(Path(handler.translate_path("/atlas/")), ROOT / "atlas")
            self.assertEqual(
                Path(handler.translate_path("/atlas/catalog/index.json")),
                output / "atlas/catalog/index.json",
            )
            catalog = json.loads((output / "atlas/catalog/index.json").read_text(encoding="utf-8"))
            entries = {item["id"]: item for item in catalog["entities"]}
            self.assertEqual(len(entries), 27)
            self.assertEqual(len(generated), 23)
            self.assertNotIn("route", entries["sector:private-equity"])

            for entity_id, segment in (
                ("project:dadman", "project/dadman"),
                ("organization:tehran-chamber-money-capital-commission",
                 "organization-unit/tehran-chamber-money-capital-commission"),
            ):
                route = f"/atlas/_preview/{segment}/"
                self.assertEqual(entries[entity_id]["route"], route)
                page = output / route.lstrip("/") / "index.html"
                html = page.read_text(encoding="utf-8")
                self.assertIn(f'data-entity-id="{entity_id}"', html)
                self.assertIn('name="robots" content="noindex,nofollow"', html)
                self.assertNotIn('<link rel="canonical"', html)
                self.assertNotIn('application/ld+json', html)
                self.assertIn('<script src="/atlas/tools/preview-url-resolver.js"></script>', html)
                # Both live Claims are incoming and reverse display is forbidden.
                self.assertNotIn('class="atlas-section atlas-relations-overview"', html)
                self.assertIn('atlas-provenance-section', html)

            person = (output / "atlas/person/ali-sanginian/index.html").read_text(encoding="utf-8")
            organization = (output / "atlas/organization/kian-private-equity-management/index.html").read_text(encoding="utf-8")
            self.assertIn('href="/atlas/_preview/organization-unit/tehran-chamber-money-capital-commission/"', person)
            self.assertIn('href="/atlas/_preview/project/dadman/"', organization)
            for page in generated:
                parser = Links()
                parser.feed(page.read_text(encoding="utf-8"))
                for href in parser.hrefs:
                    parsed = urlparse(href)
                    if parsed.scheme or parsed.netloc or not parsed.path:
                        continue
                    path = unquote(parsed.path)
                    relative = path.lstrip("/")
                    target = output / relative if path.startswith("/") else page.parent / relative
                    source = ROOT / relative if path.startswith("/") else page.parent / relative
                    self.assertTrue(
                        target.is_file() or (target / "index.html").is_file()
                        or source.is_file() or (source / "index.html").is_file(),
                        f"{page}: broken link {href}",
                    )

        self.assertEqual(public_catalog_path.read_bytes(), before)
        self.assertFalse((ROOT / "atlas/_preview").exists())
        self.assertNotIn(
            "preview-url-resolver.js",
            (ROOT / "atlas/person/ali-sanginian/index.html").read_text(encoding="utf-8"),
        )

    def test_preview_output_cannot_be_inside_public_tree(self):
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            preview.build_preview(ROOT / "atlas/_preview")


if __name__ == "__main__":
    unittest.main()
