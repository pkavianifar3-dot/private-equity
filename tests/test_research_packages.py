"""Regression coverage for package discovery and source/URL independence."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("research_packages", ROOT / "atlas/tools/research_packages.py")
packages = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packages)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class PackageContractTests(unittest.TestCase):
    def test_nested_file_location_does_not_determine_public_url(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root / "research/content/markets/a/research.json", {"id": "research:alpha", "url": "/articles/unrelated.html", "status": "PUBLISHED"})
            write(root / "research/index.json", {"research": [{"id": "research:alpha", "url": "/articles/unrelated.html", "status": "PUBLISHED"},
                                                         {"id": "research:old", "url": "/articles/old.html", "status": "PUBLISHED", "sourceMode": "legacy-html"}]})
            legacy = root / "articles/old.html"
            legacy.parent.mkdir(parents=True)
            legacy.write_text("<article>legacy</article>", encoding="utf-8")
            records = packages.discover(root / "research/content")
            self.assertEqual(records["research:alpha"][0].name, "research.json")
            self.assertEqual(packages.registry(root, records)["research:alpha"]["url"], "/articles/unrelated.html")

    def test_collision_and_missing_source_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("a", "b"):
                write(root / f"research/content/markets/{name}/research.json", {"id": "research:same", "url": "/articles/a.html", "status": "PUBLISHED"})
            with self.assertRaisesRegex(ValueError, "collision"):
                packages.discover(root / "research/content")
            (root / "research/content/markets/b/research.json").unlink()
            write(root / "research/index.json", {"research": [{"id": "research:same", "url": "/articles/a.html", "status": "PUBLISHED"},
                                                         {"id": "research:other", "url": "/articles/a.html", "status": "PUBLISHED"}]})
            with self.assertRaisesRegex(ValueError, "URL collision"):
                packages.registry(root, packages.discover(root / "research/content"))
            write(root / "research/index.json", {"research": [{"id": "research:same", "url": "/articles/a.html", "status": "PUBLISHED"},
                                                         {"id": "research:other", "url": "/articles/other.html", "status": "PUBLISHED"}]})
            with self.assertRaisesRegex(ValueError, "source missing"):
                packages.registry(root, packages.discover(root / "research/content"))

    def test_registry_source_status_mismatch_fails_before_publication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write(root / "research/content/markets/new/research.json",
                  {"id": "research:new", "url": "/articles/new.html", "status": "PUBLISHED"})
            write(root / "research/index.json", {"research": [
                {"id": "research:new", "url": "/articles/new.html", "status": "REVIEW"}]})
            with self.assertRaisesRegex(ValueError, "research:new.*URL/status mismatch"):
                packages.registry(root, packages.discover(root / "research/content"))

    def test_actual_legacy_article_has_no_fabricated_source(self):
        records = packages.discover(ROOT / "research/content")
        registry = packages.registry(ROOT, records)
        self.assertIn("research:private-capital", records)
        self.assertNotIn("research:private-equity", records)
        self.assertEqual(registry["research:private-equity"]["sourceMode"], "legacy-html")
        self.assertTrue((ROOT / "articles/what-is-private-equity.html").is_file())


if __name__ == "__main__":
    unittest.main()
