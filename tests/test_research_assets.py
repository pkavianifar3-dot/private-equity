import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validator", ROOT / "atlas/tools/validate-atlas.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)

class ResearchAssetTests(unittest.TestCase):
    def test_published_figure_requires_package_bytes_and_alt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "domain" / "slug" / "research.json"
            path.parent.mkdir(parents=True)
            doc = {"id":"research:slug", "status":"PUBLISHED", "sections":[
                {"content":[{"id":"image", "type":"figure", "src":"/assets/images/research/slug/image.png", "alt":""}]}]}
            errors = []
            validator.validate_research_package_assets(doc, path, errors)
            self.assertTrue(any("alt text" in error and "research:slug:image" in error for error in errors))
            self.assertTrue(any("package asset missing" in error for error in errors))
            (path.parent / "assets").mkdir()
            (path.parent / "assets/image.png").write_bytes(b"image")
            doc["sections"][0]["content"][0]["alt"] = "شرح تصویر"
            errors.clear()
            validator.validate_research_package_assets(doc, path, errors)
            self.assertFalse(errors)
            doc["status"] = "DRAFT"
            (path.parent / "assets/image.png").unlink()
            validator.validate_research_package_assets(doc, path, errors)
            self.assertFalse(errors)

if __name__ == "__main__": unittest.main()
