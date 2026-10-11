"""Loss-conscious DOCX extraction into a reviewable staging package (stdlib only).

This does not mint canonical IDs, citations, sources, or publish Research.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
C = "http://schemas.openxmlformats.org/drawingml/2006/chart"
PKG = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W, "r": R, "a": A, "c": C}
SAFE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def text(element):
    return "".join(node.text or "" for node in element.iter() if node.tag in (f"{{{W}}}t", f"{{{W}}}tab"))


def relations(archive):
    path = "word/_rels/document.xml.rels"
    if path not in archive.namelist():
        return {}
    tree = ET.fromstring(archive.read(path))
    return {node.get("Id"): {"target": node.get("Target"), "type": node.get("Type"),
                              "external": node.get("TargetMode") == "External"}
            for node in tree.findall(f"{{{PKG}}}Relationship")}


def note_positions(element):
    offsets, length = [], 0
    for node in element.iter():
        if node.tag == f"{{{W}}}t":
            length += len(node.text or "")
        elif node.tag in (f"{{{W}}}footnoteReference", f"{{{W}}}endnoteReference"):
            offsets.append({"id": node.get(f"{{{W}}}id"),
                            "kind": "footnote" if node.tag == f"{{{W}}}footnoteReference" else "endnote",
                            "offset": length})
    return offsets


def paragraph(p, rels):
    content = text(p)
    style = p.find("w:pPr/w:pStyle", NS)
    style = style.get(f"{{{W}}}val") if style is not None else ""
    heading = re.fullmatch(r"Heading([1-6])", style, re.I)
    kind = "heading" if heading else "caption" if style.lower().startswith("caption") else "paragraph"
    result = {"kind": kind, "text": content}
    if style:
        result["sourceStyle"] = style
    numbering = p.find("w:pPr/w:numPr", NS)
    if numbering is not None or style.lower().startswith(("listbullet", "listnumber")):
        result["kind"] = "list-item"
        level = numbering.find("w:ilvl", NS) if numbering is not None else None
        result["level"] = int(level.get(f"{{{W}}}val")) if level is not None else 0
        result["numbering"] = "ordered" if "number" in style.lower() else "unordered" if "bullet" in style.lower() else "review"
    if heading:
        result["level"] = int(heading.group(1))
    links = []
    for link in p.findall("w:hyperlink", NS):
        rid = link.get(f"{{{R}}}id")
        if rid in rels:
            links.append({"text": text(link), "target": rels[rid]["target"]})
    if links:
        result["hyperlinks"] = links
    notes = note_positions(p)
    if notes:
        result["noteIds"] = [note["id"] for note in notes]
        result["noteRefs"] = notes
    media = []
    for blip in p.findall(".//a:blip", NS):
        rid = blip.get(f"{{{R}}}embed")
        if rid in rels:
            doc_props = p.find(f".//{{{WP}}}docPr")
            media.append({"kind": "image", "source": rels[rid]["target"], "relationshipId": rid,
                          "alt": (doc_props.get("descr") or doc_props.get("title") or "") if doc_props is not None else ""})
    for chart in p.findall(".//c:chart", NS):
        rid = chart.get(f"{{{R}}}id")
        if rid in rels:
            media.append({"kind": "chart", "source": rels[rid]["target"], "relationshipId": rid})
    if media:
        result["media"] = media
    return result


def extract(docx, output):
    docx, output = Path(docx), Path(output)
    if not docx.is_file():
        raise ValueError(f"DOCX missing: {docx}")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Staging output must be empty: {output}")
    with ZipFile(docx) as archive:
        entries = archive.infolist()
        if sum(entry.file_size for entry in entries) > 500_000_000:
            raise ValueError("DOCX expanded content exceeds 500 MB")
        for entry in entries:
            if ".." in Path(entry.filename).parts or entry.filename.startswith("/"):
                raise ValueError(f"Unsafe DOCX entry: {entry.filename}")
        if "word/document.xml" not in archive.namelist():
            raise ValueError("DOCX lacks word/document.xml")
        rels = relations(archive)
        document = ET.fromstring(archive.read("word/document.xml"))
        body = document.find("w:body", NS)
        blocks = []
        comment_anchors = {}
        for child in body:
            if child.tag == f"{{{W}}}p":
                for anchor in child.iter():
                    if anchor.tag == f"{{{W}}}commentRangeStart":
                        comment_anchors[anchor.get(f"{{{W}}}id")] = len(blocks)
                item = paragraph(child, rels)
                if item["text"] or item.get("media") or item.get("noteIds"):
                    blocks.append(item)
            elif child.tag == f"{{{W}}}tbl":
                rows = [[" ".join(text(p) for p in cell.findall(".//w:p", NS))
                         for cell in row.findall("w:tc", NS)]
                        for row in child.findall("w:tr", NS)]
                note_refs = [{**ref, "row": row_index, "column": cell_index}
                             for row_index, row in enumerate(child.findall("w:tr", NS))
                             for cell_index, cell in enumerate(row.findall("w:tc", NS))
                             for ref in note_positions(cell)]
                table = {"kind": "table", "rows": rows}
                if note_refs:
                    table["noteIds"] = [note["id"] for note in note_refs]
                    table["noteRefs"] = note_refs
                blocks.append(table)
        output.mkdir(parents=True, exist_ok=True)
        media = []
        for entry in entries:
            if not entry.filename.startswith(("word/media/", "word/charts/", "word/embeddings/")) or entry.is_dir():
                continue
            blob = archive.read(entry)
            digest = hashlib.sha256(blob).hexdigest()[:12]
            name = f"{digest}-{Path(entry.filename).name}"
            dest = output / "assets" / name
            dest.parent.mkdir(exist_ok=True)
            if not dest.exists():
                dest.write_bytes(blob)
            media.append({"source": entry.filename, "file": f"assets/{name}", "sha256": hashlib.sha256(blob).hexdigest()})
        notes = {}
        for name in ("word/footnotes.xml", "word/endnotes.xml"):
            if name in archive.namelist():
                notes[name] = [{"id": e.get(f"{{{W}}}id"), "text": text(e)}
                               for e in ET.fromstring(archive.read(name))
                               if e.get(f"{{{W}}}id") not in ("-1", "0")]
        comments = []
        if "word/comments.xml" in archive.namelist():
            for comment in ET.fromstring(archive.read("word/comments.xml")):
                if comment.tag == f"{{{W}}}comment":
                    identifier = comment.get(f"{{{W}}}id")
                    comments.append({"id": identifier, "blockIndex": comment_anchors.get(identifier),
                                     "text": text(comment)})
        result = {"comments": comments, "sourceFile": docx.name, "sha256": hashlib.sha256(docx.read_bytes()).hexdigest(),
                  "blocks": blocks, "assets": sorted(media, key=lambda m: m["source"]), "notes": notes,
                  "editorialChecks": ["Confirm title, lead, heading hierarchy, captions, credit and alt text",
                                      "Map citations and bibliography to verified canonical Atlas Sources",
                                      "Map entity mentions to canonical IDs with exact offsets",
                                      "Approve public URL, publication status and article-specific assets"]}
        (output / "extraction.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    parser.add_argument("--out", type=Path, required=True, help="New empty staging directory, outside the public tree")
    args = parser.parse_args()
    result = extract(args.docx, args.out)
    print(f"Extracted {len(result['blocks'])} ordered blocks and {len(result['assets'])} assets to {args.out}")
