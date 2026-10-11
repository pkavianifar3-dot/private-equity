import importlib.util
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ingest_docx", ROOT / "research/tools/ingest-docx.py")
ingest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ingest)

DOC = '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:c="http://schemas.openxmlformats.org/drawingml/2006/chart"><w:body>
 <w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>عنوان واقعی</w:t></w:r></w:p>
 <w:p><w:commentRangeStart w:id="3"/><w:r><w:t>متن </w:t></w:r><w:hyperlink r:id="rLink"><w:r><w:t>منبع</w:t></w:r></w:hyperlink>
 <w:r><w:footnoteReference w:id="1"/></w:r><w:r><w:endnoteReference w:id="3"/></w:r><w:drawing><a:blip r:embed="rImage"/><c:chart r:id="rChart"/></w:drawing></w:p>
 <w:tbl><w:tr><w:tc><w:p><w:r><w:t>سلول</w:t></w:r><w:r><w:footnoteReference w:id="2"/></w:r></w:p></w:tc></w:tr></w:tbl>
 </w:body></w:document>'''
RELS = '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Id="rLink" Type="hyperlink" Target="https://example.org/" TargetMode="External"/>
 <Relationship Id="rImage" Type="image" Target="media/image1.png"/>
 <Relationship Id="rChart" Type="chart" Target="charts/chart1.xml"/>
 </Relationships>'''
NOTES = '''<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:footnote w:id="1"><w:p><w:r><w:t>یادداشت</w:t></w:r></w:p></w:footnote><w:footnote w:id="2"><w:p><w:r><w:t>یادداشت جدول</w:t></w:r></w:p></w:footnote></w:footnotes>'''


class IngestionTests(unittest.TestCase):
    def test_text_order_media_table_links_and_notes_survive_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            file = root / "input.docx"
            with ZipFile(file, "w") as archive:
                for path, value in (("word/document.xml", DOC), ("word/_rels/document.xml.rels", RELS),
                                    ("word/footnotes.xml", NOTES),
                                    ("word/endnotes.xml", '<w:endnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:endnote w:id="3"><w:p><w:r><w:t>یادداشت پایانی</w:t></w:r></w:p></w:endnote></w:endnotes>'),
                                    ("word/comments.xml", '<w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:comment w:id="3"><w:p><w:r><w:t>بازبینی</w:t></w:r></w:p></w:comment></w:comments>'), ("word/media/image1.png", b"fake-png"),
                                    ("word/charts/chart1.xml", b"<chart/>")):
                    archive.writestr(path, value)
            result = ingest.extract(file, root / "staging")
            self.assertEqual([item["kind"] for item in result["blocks"]], ["heading", "paragraph", "table"])
            self.assertEqual(result["blocks"][1]["hyperlinks"][0]["target"], "https://example.org/")
            self.assertEqual([m["kind"] for m in result["blocks"][1]["media"]], ["image", "chart"])
            self.assertEqual(result["blocks"][2]["rows"], [["سلول"]])
            self.assertEqual(result["blocks"][2]["noteIds"], ["2"])
            self.assertEqual(result["notes"]["word/footnotes.xml"][0]["text"], "یادداشت")
            self.assertEqual(result["notes"]["word/endnotes.xml"][0]["text"], "یادداشت پایانی")
            self.assertIn({"id":"3","kind":"endnote","offset":8}, result["blocks"][1]["noteRefs"])
            self.assertIn({"id":"2","kind":"footnote","offset":4,"row":0,"column":0},
                          result["blocks"][2]["noteRefs"])
            self.assertEqual(len(result["assets"]), 2)
            self.assertEqual(result["comments"], [{"id":"3","blockIndex":1,"text":"بازبینی"}])
            with self.assertRaisesRegex(ValueError, "empty"):
                ingest.extract(file, root / "staging")


if __name__ == "__main__":
    unittest.main()
