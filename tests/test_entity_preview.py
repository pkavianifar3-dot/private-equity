"""Local-only Entity preview must leave the public build and URLs intact."""

import importlib.util
import json
import re
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
        public_article_path = ROOT / "articles/private-capital.html"
        article_before = public_article_path.read_bytes()
        public_research_index = ROOT / "atlas/discovery/research-by-entity.json"
        index_before = public_research_index.read_bytes()
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
            self.assertEqual(
                Path(handler.translate_path("/assets/css/exploration-preview.css")),
                output / "assets/css/exploration-preview.css",
            )
            catalog = json.loads((output / "atlas/catalog/index.json").read_text(encoding="utf-8"))
            entries = {item["id"]: item for item in catalog["entities"]}
            self.assertEqual(len(entries), 27)
            self.assertEqual(len(generated), 24)
            article = output / "articles/private-capital.html"
            preview_article = article.read_text(encoding="utf-8")
            self.assertIn('href="/atlas/concept/private-capital/"', preview_article)
            self.assertIn('class="explore-reading-layout"', preview_article)
            self.assertIn('class="explore-rail"', preview_article)
            self.assertIn('class="explore-mobile-toc"', preview_article)
            self.assertNotIn('data-research-connections', preview_article)
            self.assertNotIn('src="../assets/js/article-page.js"', preview_article)
            rail = preview_article.split('<aside class="explore-rail"', 1)[1].split('</aside>', 1)[0]
            self.assertEqual(rail.count('href="/atlas/concept/'), 12)
            self.assertIn('href="/articles/what-is-private-equity.html"', rail)
            self.assertIn('class="explore-more"', rail)
            self.assertIn('aria-label="راهنمای مطالعه"', rail)
            self.assertLess(rail.index('کاوش در پژوهش‌ها'), rail.index('کاوش در اطلس'))
            self.assertNotIn('انتخاب تحریریه', rail)
            self.assertIn('href="/articles.html"', rail)
            self.assertIn('href="/atlas/"', rail)
            self.assertIn('class="explore-card explore-mobile-card"', rail)
            self.assertIn('class="explore-lead"', preview_article)
            self.assertNotIn('پیش‌نمایش محلیِ مسیرهای کاوش', preview_article)
            heading_ids = re.findall(r'<h[23][^>]* id="(research-section-[^"]+)"', preview_article)
            toc_targets = re.findall(r'href="#(research-section-[^"]+)"', preview_article)
            self.assertGreaterEqual(len(heading_ids), 6)
            self.assertEqual(len(heading_ids), len(set(heading_ids)))
            self.assertEqual(set(heading_ids), set(toc_targets))
            self.assertIn('name="robots" content="noindex,nofollow"', preview_article)
            self.assertNotIn('<link rel="canonical"', preview_article)
            concept = (output / "atlas/concept/private-capital/index.html").read_text(encoding="utf-8")
            self.assertIn('href="/articles/private-capital.html"', concept)
            self.assertIn('class="explore-reading-layout atlas-reading-layout"', concept)
            atlas_rail = concept.split('<aside class="explore-rail"', 1)[1].split('</aside>', 1)[0]
            self.assertLess(atlas_rail.index('کاوش در اطلس'), atlas_rail.index('کاوش در پژوهش‌ها'))
            self.assertIn('class="explore-mobile-toc"', atlas_rail)
            atlas_heading_ids = re.findall(r'<h2[^>]* id="(atlas-section-[^"]+)"', concept)
            atlas_toc_targets = re.findall(r'href="#(atlas-section-[^"]+)"', atlas_rail)
            self.assertTrue(atlas_heading_ids)
            self.assertEqual(set(atlas_heading_ids), set(atlas_toc_targets))
            self.assertIn('href="/atlas/concept/private-equity/"', concept)
            self.assertNotIn('id="related-research-heading"', concept)
            self.assertIn('exploration-preview.css', concept)
            person = (output / "atlas/person/ali-sanginian/index.html").read_text(encoding="utf-8")
            self.assertIn('پژوهش مرتبطی ثبت نشده است.', person)
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
                    source = (ROOT / relative if path.startswith("/") else
                              ROOT / page.relative_to(output).parent / relative)
                    self.assertTrue(
                        target.is_file() or (target / "index.html").is_file()
                        or source.is_file() or (source / "index.html").is_file(),
                        f"{page}: broken link {href}",
                    )

        self.assertEqual(public_catalog_path.read_bytes(), before)
        self.assertEqual(public_article_path.read_bytes(), article_before)
        self.assertEqual(public_research_index.read_bytes(), index_before)
        self.assertFalse((ROOT / "atlas/_preview").exists())
        self.assertNotIn(
            "preview-url-resolver.js",
            (ROOT / "atlas/person/ali-sanginian/index.html").read_text(encoding="utf-8"),
        )

    def test_showcase_is_explicitly_synthetic_and_never_public(self):
        public_before = (ROOT / "atlas/discovery/research-by-entity.json").read_bytes()
        with tempfile.TemporaryDirectory() as temp_dir:
            overlay = Path(temp_dir)
            generated = preview.build_preview(overlay, showcase=True)
            self.assertEqual(len(generated), 25)
            concept = (overlay / "atlas/concept/private-capital/index.html").read_text(encoding="utf-8")
            self.assertIn('href="/articles/private-capital.html"', concept)
            self.assertIn('href="/articles/_preview/private-capital-note.html"', concept)
            self.assertIn('نمونهٔ نمایشی؛ فقط در preview', concept)
            demo = (overlay / "articles/_preview/private-capital-note.html").read_text(encoding="utf-8")
            self.assertIn('name="robots" content="noindex,nofollow"', demo)
            self.assertIn('این مقاله و ارتباط آن canonical نیست', demo)
            handler = object.__new__(preview.PreviewHandler)
            handler.directory = str(overlay)
            self.assertEqual(
                Path(handler.translate_path("/articles/_preview/private-capital-note.html")),
                overlay / "articles/_preview/private-capital-note.html",
            )
        self.assertEqual(public_before, (ROOT / "atlas/discovery/research-by-entity.json").read_bytes())
        self.assertFalse((ROOT / "articles/_preview").exists())

    def test_preview_output_cannot_be_inside_public_tree(self):
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            preview.build_preview(ROOT / "atlas/_preview")


if __name__ == "__main__":
    unittest.main()
