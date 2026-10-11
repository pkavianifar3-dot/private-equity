"""Prepare a DRAFT Research v2 package from reviewed DOCX extraction.

Metadata is supplied by an editor. Missing citations, Entity mentions and image
alt text remain explicit review tasks; no canonical references are invented.
"""
import argparse
import json
import re
import shutil
from pathlib import Path

IDENTITY = re.compile(r"^research:[a-z0-9]+(?:-[a-z0-9]+)*$")
URL = re.compile(r"^/articles/[a-z0-9]+(?:-[a-z0-9]+)*\.html$")


def prepare(extraction_path, metadata_path, output):
    extraction_path, metadata_path, output = map(Path, (extraction_path, metadata_path, output))
    extraction = json.loads(extraction_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    identity, url = metadata.get("id"), metadata.get("url")
    if not isinstance(identity,str) or not IDENTITY.fullmatch(identity) or not isinstance(url,str) or not URL.fullmatch(url):
        raise ValueError("Editorial metadata requires valid explicit id and public URL")
    for name in ("title", "summary"):
        if not isinstance(metadata.get(name), dict) or not metadata[name].get("fa"):
            raise ValueError(f"Editorial metadata requires {name}.fa")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Output package must be empty: {output}")
    slug = identity.split(":",1)[1]
    assets = {a["source"]: a["file"] for a in extraction["assets"]}
    sections = []
    review = []
    section = None
    index = 0

    def block(kind, **fields):
        nonlocal index, section
        if section is None:
            section = {"id": "introduction", "title": {"fa": "مقدمه"}, "content": []}
            sections.append(section)
        index += 1
        section["content"].append({"id": f"block-{index:04d}", "type": kind, **fields})

    for item in extraction["blocks"]:
        item_anchor_target = None
        kind = item["kind"]
        if kind == "heading" and item.get("level") == 1:
            if item["text"].strip() != metadata["title"]["fa"].strip():
                review.append(f"H1 differs from editorial title: {item['text']}")
            continue
        if kind == "heading" and item.get("level") == 2:
            index += 1
            section = {"id": f"section-{index:04d}", "title": {"fa": item["text"]}, "content": []}
            sections.append(section)
            continue
        if kind == "heading":
            block("subheading", text=item["text"], **({"level": item["level"]} if item.get("level", 3) != 3 else {}))
        elif kind == "table":
            block("table", rows=item["rows"])
            item_anchor_target = section["content"][-1]
        elif kind == "list-item":
            ordered = item.get("numbering") == "ordered"
            level = item.get("level", 0)
            if item.get("numbering") == "review" or level:
                review.append(f"List numbering/indentation requires review near block {index}: {item['text']}")
            if section and section["content"] and section["content"][-1]["type"] == "list" and section["content"][-1].get("ordered", False) == ordered and not level:
                section["content"][-1]["items"].append(item["text"])
            else:
                block("list", items=[item["text"]], ordered=ordered)
        elif kind == "caption":
            if section and section["content"] and section["content"][-1]["type"] == "figure":
                section["content"][-1]["caption"] = item["text"]
            else:
                block("paragraph", text=item["text"])
                review.append(f"Caption placement needs review: {item['text']}")
        elif kind == "paragraph":
            if item.get("text"):
                block("paragraph", text=item["text"])
                item_anchor_target = section["content"][-1]
            for media in item.get("media", []):
                source = media["source"]
                # Word relationships are relative to word/document.xml.
                source_key = "word/" + source.lstrip("/")
                if media["kind"] == "image" and source_key in assets:
                    filename = Path(assets[source_key]).name
                    block("figure", src=f"/assets/images/research/{slug}/{filename}", alt=media.get("alt", ""))
                    review.append(f"Image alt/credit/caption requires editorial review: {filename}")
                else:
                    review.append(f"Embedded {media['kind']} needs visual/data review: {source}")
        if item.get("hyperlinks"):
            review.append(f"Inline hyperlinks require citation/source mapping near block {index}")
        note_refs = item.get("noteRefs") or [
            {"id": note_id, "kind": "footnote"} for note_id in item.get("noteIds", [])
        ]
        anchor_target = item_anchor_target
        for note in note_refs:
            location = "word/footnotes.xml" if note["kind"] == "footnote" else "word/endnotes.xml"
            source_note = next((entry for entry in extraction.get("notes", {}).get(location, [])
                                if entry["id"] == note["id"]), None)
            if source_note is None:
                review.append(f"Unresolved {note['kind']} {note['id']} near block {index}")
                continue
            anchor = {"contentBlockId": anchor_target["id"], "offset": note["offset"]} if (
                anchor_target and "offset" in note and anchor_target["type"] in ("paragraph", "table")
            ) else None
            if anchor and "row" in note:
                anchor.update(row=note["row"], column=note["column"])
            block("note", text=source_note["text"], noteNumber=int(note["id"]),
                  **({"anchor": anchor} if anchor else {}))
        if note_refs:
            review.append(f"Footnote/endnote references require editorial citation review: {note_refs}")
    if not sections:
        raise ValueError("DOCX extraction has no structured article body")
    doc = {"id": identity, "type": "Research", "schemaVersion": "2.0", "url": url,
           "status": "DRAFT", "title": metadata["title"], "summary": metadata["summary"],
           "publication": {"datePublished": None, "dateModified": None, "authorRefs": []},
           "entityRefs": [], "claimRefs": [], "candidateClaimRefs": [], "evidenceRefs": [],
           "sourceRefs": [], "relatedResearchRefs": [], "sections": sections, "citations": []}
    output.mkdir(parents=True, exist_ok=True)
    (output / "research.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for asset in extraction["assets"]:
        source = extraction_path.parent / asset["file"]
        dest = output / "assets" / Path(asset["file"]).name
        dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, dest)
    (output / "editorial-review.json").write_text(json.dumps({"checks": review + extraction["editorialChecks"], "notes": extraction.get("notes", {}), "comments": extraction.get("comments", [])}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("extraction", type=Path)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    article = prepare(args.extraction, args.metadata, args.out)
    print(f"Prepared {article['id']} as DRAFT with {len(article['sections'])} sections; editorial review required")
