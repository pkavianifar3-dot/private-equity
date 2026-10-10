import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / f"research/tools/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

ingest = load("ingest-docx")
prepare = load("prepare-research")

DOC = '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><w:body>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>عنوان</w:t></w:r></w:p>
<w:p><w:r><w:t>مقدمه</w:t></w:r><w:r><w:footnoteReference w:id="1"/></w:r><w:drawing><a:blip r:embed="rImage"/></w:drawing></w:p>
<w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr><w:r><w:t>بخش</w:t></w:r></w:p>
<w:p><w:pPr><w:pStyle w:val="Heading4"/></w:pPr><w:r><w:t>زیربخش</w:t></w:r></w:p>
<w:p><w:pPr><w:pStyle w:val="ListNumber"/></w:pPr><w:r><w:t>گزینه نخست</w:t></w:r></w:p>
</w:body></w:document>'''
RELS = '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rImage" Type="image" Target="media/image1.png"/></Relationships>'''

class PrepareTests(unittest.TestCase):
    def test_extraction_to_draft_keeps_content_and_requires_mapping(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            docx = root / "article.docx"
            with ZipFile(docx, "w") as zipfile:
                zipfile.writestr("word/document.xml", DOC)
                zipfile.writestr("word/_rels/document.xml.rels", RELS)
                zipfile.writestr("word/media/image1.png", b"image")
                zipfile.writestr("word/footnotes.xml", '<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:footnote w:id="1"><w:p><w:r><w:t>Footnote</w:t></w:r></w:p></w:footnote></w:footnotes>')
            ingest.extract(docx, root / "extract")
            metadata = root / "metadata.json"
            metadata.write_text(json.dumps({"id":"research:demo","url":"/articles/demo.html",
                                           "title":{"fa":"عنوان"},"summary":{"fa":"خلاصه"}}),encoding="utf-8")
            result = prepare.prepare(root / "extract/extraction.json", metadata, root / "package")
            schema = json.loads((ROOT / "research/schemas/research-schema-v2.json").read_text(encoding="utf-8"))
            self.assertEqual(list(Draft202012Validator(schema).iter_errors(result)), [])
            self.assertEqual(result["status"], "DRAFT")
            self.assertEqual(result["citations"], [])
            self.assertEqual(result["entityRefs"], [])
            self.assertEqual(result["sections"][1]["content"][0]["level"], 4)
            self.assertEqual(result["sections"][1]["content"][1]["type"], "list")
            self.assertTrue(result["sections"][1]["content"][1]["ordered"])
            self.assertTrue((root / "package/assets").is_dir())
            self.assertIn("Footnote", (root / "package/editorial-review.json").read_text(encoding="utf-8"))
            notes = [b for section in result["sections"] for b in section["content"]
                     if b["type"] == "note"]
            self.assertEqual(len(notes), 1)
            self.assertEqual(notes[0]["text"], "Footnote")
            self.assertEqual(notes[0]["anchor"], {"contentBlockId": "block-0001", "offset": 5})

if __name__ == "__main__": unittest.main()
