import importlib.util
import unittest


SPEC = importlib.util.spec_from_file_location(
    "build_static_pages",
    "atlas/tools/build-static-pages.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class StaticProvenancePresentationTests(unittest.TestCase):
    def setUp(self):
        self.claims = [
            {
                "id": "claim:test",
                "evidenceRefs": ["evidence:test"],
            }
        ]
        self.evidence = {
            "evidence:test": {
                "id": "evidence:test",
                "claimRef": "claim:test",
                "sourceRef": "source:test",
                "evidenceType": "authoritative_publication",
                "strength": "strong",
            }
        }
        self.sources = {
            "source:test": {
                "id": "source:test",
                "title_fa": "Test Source Title",
                "publisher": "Test Publisher",
                "url": "https://example.com/source",
            }
        }

        self.source_index = MODULE.build_source_index(
            self.sources,
            self.claims,
            self.evidence,
        )

    def test_evidence_does_not_duplicate_full_source(self):
        html = MODULE.render_evidence(
            self.claims,
            self.evidence,
            self.source_index,
        )

        self.assertIn("authoritative_publication", html)
        self.assertIn("strong", html)
        self.assertIn("[1]", html)

        self.assertNotIn("Test Source Title", html)
        self.assertNotIn("Test Publisher", html)
        self.assertNotIn("https://example.com/source", html)

    def test_sources_keep_full_source_details(self):
        html = MODULE.render_sources(
            self.sources,
            self.claims,
            self.evidence,
            self.source_index,
        )

        self.assertIn("Test Source Title", html)
        self.assertIn("https://example.com/source", html)


if __name__ == "__main__":
    unittest.main()
