"""Discover Research packages independent of URL or source filename."""
import json
from pathlib import Path


def content_files(root):
    root = Path(root)
    if not root.is_dir():
        raise ValueError(f"{root}: Research content directory missing")
    all_json = sorted(root.rglob("*.json"), key=lambda p: p.as_posix())
    for path in all_json:
        relative = path.relative_to(root)
        if path.parent != root and "assets" not in relative.parts and path.name not in ("research.json", "editorial-review.json"):
            raise ValueError(f"{path}: unexpected JSON in Research package")
        if path.name == "research.json" and len(relative.parts) != 3:
            raise ValueError(f"{path}: expected <domain>/<slug>/research.json")
    return [p for p in all_json if p.name == "research.json" or p.parent == root]


def discover(root):
    records = {}
    slugs = {}
    for path in content_files(root):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            raise ValueError(f"{path}: cannot read Research JSON: {exc}") from exc
        research_id = data.get("id")
        if not isinstance(research_id, str) or not research_id.startswith("research:"):
            raise ValueError(f"{path}: invalid Research ID {research_id!r}")
        slug = research_id.split(":", 1)[1]
        if research_id in records or slug.casefold() in slugs:
            raise ValueError(f"{path}: Research ID/slug collision {research_id}; first: {slugs.get(slug.casefold())}")
        records[research_id] = (path, data)
        slugs[slug.casefold()] = path
    return dict(sorted(records.items()))


def registry(root, records):
    path = Path(root) / "research/index.json"
    items = json.loads(path.read_text(encoding="utf-8"))["research"]
    found = {}
    urls = {}
    for row in items:
        identity, url = row["id"], row["url"]
        if (not isinstance(url, str) or not url.startswith("/articles/")
                or not url.endswith(".html") or ".." in url or "\\" in url
                or "?" in url or "#" in url):
            raise ValueError(f"{path}: {identity}: invalid public URL {url!r}")
        if identity in found:
            raise ValueError(f"{path}: duplicate ID {identity}")
        if url.casefold() in urls:
            raise ValueError(f"{path}: URL collision {url} for {identity} and {urls[url.casefold()]}")
        found[identity] = row
        urls[url.casefold()] = identity
        if identity not in records:
            legacy_page = Path(root) / url.lstrip("/")
            if row.get("sourceMode") != "legacy-html" or not legacy_page.is_file():
                raise ValueError(f"{path}: {identity}: source missing or legacy HTML page absent")
    for identity, (source, data) in records.items():
        row = found.get(identity)
        if not row or row["url"] != data.get("url") or row["status"] != data.get("status"):
            raise ValueError(f"{source}: {identity}: missing registry entry or URL/status mismatch")
    return found
