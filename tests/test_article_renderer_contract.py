import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESEARCH_PATH = ROOT / "research" / "content" / "private-capital.json"
ARTICLE_PATH = ROOT / "articles" / "private-capital.html"


class ArticleRendererContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with RESEARCH_PATH.open(encoding="utf-8") as f:
            cls.research = json.load(f)

        cls.article = ARTICLE_PATH.read_text(encoding="utf-8")

    def test_research_content_block_types_are_supported(self):
        supported = {
            "paragraph",
            "subheading",
            "figure",
            "list",
            "table",
        }

        actual = {
            block["type"]
            for section in self.research["sections"]
            for block in section.get("content", [])
        }

        self.assertTrue(actual)
        self.assertTrue(
            actual.issubset(supported),
            f"Unsupported content block types: {actual - supported}",
        )

    def test_research_has_expected_article_sections(self):
        section_ids = [
            section["id"]
            for section in self.research["sections"]
        ]

        self.assertEqual(
            section_ids,
            [
                "introduction",
                "definition-and-scope",
                "main-blocks",
                "private-equity",
                "private-credit",
                "real-assets",
                "conclusion",
            ],
        )

    def test_research_sections_have_renderable_content(self):
        for section in self.research["sections"]:
            self.assertIn("id", section)
            self.assertIn("title", section)
            self.assertIn("content", section)
            self.assertIsInstance(section["content"], list)

            for block in section["content"]:
                self.assertIn("id", block)
                self.assertIn("type", block)


    def test_existing_article_contains_research_figures(self):
        for section in self.research["sections"]:
            for block in section.get("content", []):
                if block["type"] != "figure":
                    continue

                src = block["src"]
                article_src = src.removeprefix("../")

                self.assertIn(
                    article_src,
                    self.article,
                    f"Research figure missing from article: {src}",
                )


if __name__ == "__main__":
    unittest.main()


class ArticleRendererInterfaceTests(unittest.TestCase):
    def test_renderer_module_exists(self):
        renderer_path = ROOT / "assets" / "js" / "article-renderer.js"
        self.assertTrue(
            renderer_path.exists(),
            "Article Renderer module is missing",
        )

    def test_renderer_exposes_content_renderer(self):
        renderer_path = ROOT / "assets" / "js" / "article-renderer.js"
        if not renderer_path.exists():
            self.skipTest("Renderer module not created yet")

        renderer = renderer_path.read_text(encoding="utf-8")

        self.assertIn(
            "renderArticleContent",
            renderer,
            "renderArticleContent interface is missing",
        )


class ArticleRendererBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.renderer = (
            ROOT / "assets" / "js" / "article-renderer.js"
        ).read_text(encoding="utf-8")

    def test_renderer_supports_all_content_block_types(self):
        for block_type in (
            "paragraph",
            "subheading",
            "figure",
            "list",
            "table",
        ):
            self.assertIn(
                f'"{block_type}"',
                self.renderer,
                f"Renderer does not support {block_type}",
            )

    def test_renderer_escapes_html_in_text_content(self):
        self.assertIn(
            "escapeHtml",
            self.renderer,
            "Renderer must escape text content",
        )

    def test_renderer_rejects_unsupported_block_types(self):
        self.assertIn(
            "Unsupported article content block",
            self.renderer,
            "Renderer must reject unsupported block types",
        )

    def test_renderer_rejects_invalid_sections_input(self):
        self.assertIn(
            "Article sections must be an array",
            self.renderer,
            "Renderer must validate sections input",
        )


class ArticleRendererBoundaryTests(unittest.TestCase):
    def test_renderer_does_not_own_article_shell(self):
        renderer = (
            ROOT / "assets" / "js" / "article-renderer.js"
        ).read_text(encoding="utf-8")

        for shell_marker in (
            "article-author",
            "article-date",
            "cta",
            "sources",
            "copyright",
        ):
            self.assertNotIn(
                shell_marker,
                renderer,
                f"Renderer must not own article shell: {shell_marker}",
            )

    def test_research_block_types_are_content_only(self):
        import json

        research = json.loads(
            (ROOT / "research" / "content" / "private-capital.json")
            .read_text(encoding="utf-8")
        )

        allowed = {
            "paragraph",
            "subheading",
            "figure",
            "list",
            "table",
        }

        for section in research["sections"]:
            for block in section["content"]:
                self.assertIn(block["type"], allowed)


class ArticleRendererLegacyPresentationBaselineTests(unittest.TestCase):
    def test_legacy_article_presentation_baseline(self):
        from html.parser import HTMLParser

        class Parser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.counts = {
                    "title": 0,
                    "meta": 0,
                    "canonical": 0,
                    "json_ld": 0,
                    "a": 0,
                    "button": 0,
                    "img": 0,
                }

            def handle_starttag(self, tag, attrs):
                if tag in ("title", "meta", "a", "button", "img"):
                    self.counts[tag] += 1

                attrs = dict(attrs)

                if tag == "link" and attrs.get("rel") == "canonical":
                    self.counts["canonical"] += 1

                if (
                    tag == "script"
                    and attrs.get("type") == "application/ld+json"
                ):
                    self.counts["json_ld"] += 1

            def handle_startendtag(self, tag, attrs):
                self.handle_starttag(tag, attrs)

        html = (
            ROOT / "articles" / "private-capital.html"
        ).read_text(encoding="utf-8")

        parser = Parser()
        parser.feed(html)

        import json

        baseline = json.loads(
            (
                ROOT
                / "tests"
                / "fixtures"
                / "private-capital-legacy-baseline.json"
            ).read_text(encoding="utf-8")
        )

        for key in (
            "title",
            "meta",
            "canonical",
            "json_ld",
            "a",
            "button",
            "img",
        ):
            self.assertEqual(
                parser.counts[key],
                baseline["counts"][key],
                f"Legacy presentation baseline mismatch: {key}",
            )


class ArticleRendererLegacyBaselineTests(unittest.TestCase):
    def test_legacy_article_baseline_counts(self):
        from html.parser import HTMLParser

        class Parser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.counts = {
                    "h1": 0,
                    "h2": 0,
                    "h3": 0,
                    "p": 0,
                    "figure": 0,
                    "ul": 0,
                    "table": 0,
                    "cta": 0,
                }

            def handle_starttag(self, tag, attrs):
                if tag in self.counts:
                    self.counts[tag] += 1

                if tag == "div":
                    attrs = dict(attrs)
                    if "cta" in attrs.get("class", "").split():
                        self.counts["cta"] += 1

        article = (
            ROOT / "articles" / "private-capital.html"
        ).read_text(encoding="utf-8")

        parser = Parser()
        parser.feed(article)

        import json

        baseline = json.loads(
            (
                ROOT
                / "tests"
                / "fixtures"
                / "private-capital-legacy-baseline.json"
            ).read_text(encoding="utf-8")
        )

        for key in (
            "h1",
            "h2",
            "h3",
            "p",
            "figure",
            "ul",
            "table",
            "cta",
        ):
            self.assertEqual(
                parser.counts[key],
                baseline["counts"][key],
                f"Legacy article baseline mismatch: {key}",
            )


class ArticleRendererIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.article = (
            ROOT / "articles" / "private-capital.html"
        ).read_text(encoding="utf-8")

    def test_article_loads_renderer_module(self):
        self.assertIn(
            '<script src="../assets/js/article-renderer.js"></script>',
            self.article,
        )

    def test_article_keeps_main_script(self):
        self.assertIn(
            '<script src="../assets/js/main.js"></script>',
            self.article,
        )

    def test_article_keeps_presentation_shell(self):
        for marker in (
            'class="article-author"',
            'class="article-date"',
            'class="cta"',
            "<h2>منابع</h2>",
            'class="article-copyright"',
        ):
            self.assertIn(
                marker,
                self.article,
                f"Article shell marker missing: {marker}",
            )

class ArticleRendererIntroductionBoundaryTests(unittest.TestCase):
    def test_introduction_migration_boundary_markers_exist(self):
        article = (
            ROOT / "articles" / "private-capital.html"
        ).read_text(encoding="utf-8")

        self.assertIn(
            '<h2>سرمایه خصوصی چیست؟</h2>',
            article,
        )
        self.assertIn(
            'class="cta"',
            article,
        )
        self.assertIn(
            "<h2>منابع</h2>",
            article,
        )

        self.assertIn(
            "«سرمایه خصوصی» (Private Capital)، چتر مفهومی اصلی",
            article,
        )
        self.assertIn(
            "از آنجا که سرمایه خصوصی (Private Capital)",
            article,
        )


if __name__ == "__main__":
    unittest.main()


class ArticleRendererMigrationBoundaryTests(unittest.TestCase):
    def test_introduction_legacy_order_is_explicit(self):
        article = (
            ROOT / "articles" / "private-capital.html"
        ).read_text(encoding="utf-8")

        figure_pos = article.index("<figure>")
        first_paragraph_pos = article.index(
            "«سرمایه خصوصی» (Private Capital)"
        )
        second_paragraph_pos = article.index(
            "از آنجا که سرمایه خصوصی (Private Capital)"
        )

        self.assertLess(
            figure_pos,
            first_paragraph_pos,
            "Legacy HTML currently places the introduction figure first",
        )
        self.assertLess(
            first_paragraph_pos,
            second_paragraph_pos,
            "Legacy HTML introduction paragraphs must preserve order",
        )

    def test_research_introduction_order_is_explicit(self):
        import json

        research = json.loads(
            (
                ROOT
                / "research"
                / "content"
                / "private-capital.json"
            ).read_text(encoding="utf-8")
        )

        introduction = next(
            section
            for section in research["sections"]
            if section["id"] == "introduction"
        )

        self.assertEqual(
            [block["type"] for block in introduction["content"]],
            ["paragraph", "paragraph", "figure"],
        )

class ArticleRendererResearchSourceContractTests(unittest.TestCase):
    def test_private_capital_research_source_path_is_stable(self):
        article = (
            ROOT / "articles" / "private-capital.html"
        ).read_text(encoding="utf-8")

        research_path = (
            ROOT
            / "research"
            / "content"
            / "private-capital.json"
        )

        self.assertTrue(
            research_path.exists(),
            "private-capital Research source must exist",
        )

        self.assertNotIn(
            "research/content/private-capital.json",
            article,
            "Research source should not be hardcoded into article HTML yet",
        )

class ArticleRendererPageIntegrationTests(unittest.TestCase):
    def test_article_page_integration_exists(self):
        integration = ROOT / "assets" / "js" / "article-page.js"

        self.assertTrue(
            integration.exists(),
            "article-page integration module must exist",
        )

    def test_article_page_integration_owns_research_loading(self):
        integration = (
            ROOT / "assets" / "js" / "article-page.js"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'fetch(path, {',
            integration,
        )
        self.assertIn(
            'const RESEARCH_PATH = "../research/content/private-capital.json";',
            integration,
        )

    def test_article_page_integration_uses_renderer(self):
        integration = (
            ROOT / "assets" / "js" / "article-page.js"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "global.renderArticleContent([section])",
            integration,
        )
        self.assertNotIn(
            "function renderArticleContent(",
            integration,
        )

    def test_article_page_integration_preserves_failure_fallback(self):
        integration = (
            ROOT / "assets" / "js" / "article-page.js"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'renderMainBlocks().catch(error => {',
            integration,
        )
        self.assertIn(
            'console.error("Article Research rendering failed:", error);',
            integration,
        )

    def test_private_capital_loads_page_integration_after_renderer(self):
        article = (
            ROOT / "articles" / "private-capital.html"
        ).read_text(encoding="utf-8")

        renderer_pos = article.index(
            '<script src="../assets/js/article-renderer.js"></script>'
        )
        integration_pos = article.index(
            '<script src="../assets/js/article-page.js"></script>'
        )
        main_pos = article.index(
            '<script src="../assets/js/main.js"></script>'
        )

        self.assertLess(renderer_pos, integration_pos)
        self.assertLess(integration_pos, main_pos)

    def test_private_capital_has_main_blocks_fallback_marker(self):
        article = (
            ROOT / "articles" / "private-capital.html"
        ).read_text(encoding="utf-8")

        self.assertEqual(
            article.count(
                'data-article-renderer-section="main-blocks"'
            ),
            1,
        )


    def test_private_capital_page_replaces_only_main_blocks_target(self):
        integration = (
            ROOT / "assets" / "js" / "article-page.js"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'document.querySelector(TARGET_SELECTOR)',
            integration,
        )
        self.assertIn(
            'target.replaceWith(template.content)',
            integration,
        )
        self.assertNotIn(
            'document.querySelector("article")',
            integration,
        )
        self.assertNotIn(
            'article.innerHTML',
            integration,
        )

    def test_private_capital_page_does_not_render_other_sections(self):
        integration = (
            ROOT / "assets" / "js" / "article-page.js"
        ).read_text(encoding="utf-8")

        self.assertIn(
            'const SECTION_ID = "main-blocks";',
            integration,
        )
        self.assertNotIn(
            'SECTION_ID = "introduction"',
            integration,
        )
        self.assertNotIn(
            'SECTION_ID = "private-equity"',
            integration,
        )
        self.assertNotIn(
            'SECTION_ID = "private-credit"',
            integration,
        )
        self.assertNotIn(
            'SECTION_ID = "real-assets"',
            integration,
        )
