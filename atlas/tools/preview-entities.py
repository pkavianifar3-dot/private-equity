"""Serve an isolated Atlas Entity preview without writing public artifacts.

Run ``python atlas/tools/preview-entities.py`` and open the printed loopback URL.
The temporary overlay is removed when the server stops.
"""

import argparse
import importlib.util
import json
import re
import tempfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote


SITE_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = Path(__file__).resolve().parent
PREVIEW_TYPES = {
    "Project": ("project", "project"),
    # The canonical ID is organization:..., but the type is OrganizationUnit.
    "OrganizationUnit": ("organization", "organization-unit"),
}


def load_builder(filename):
    spec = importlib.util.spec_from_file_location(filename, TOOLS_DIR / f"{filename}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


catalog_builder = load_builder("build-catalog")
static_builder = load_builder("build-static-pages")
exploration = load_builder("exploration")


def showcase_article(output_root, index, catalog):
    """An explicitly synthetic fixture, confined to the optional overlay."""
    fixture = json.loads((SITE_ROOT / "tests/fixtures/exploration-showcase.json").read_text(encoding="utf-8"))
    known = {entry["id"] for entry in catalog}
    for ref in fixture["entityRefs"]:
        if ref not in known:
            raise ValueError(f"Preview fixture references missing Entity: {ref}")
        index["entities"].setdefault(ref, []).append({
            "id": fixture["id"], "url": fixture["url"], "title": fixture["title"],
            "previewFixture": True,
        })
        index["entities"][ref].sort(key=lambda item: item["id"])
    destination = output_root / fixture["url"].lstrip("/")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        '<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta name="robots" content="noindex,nofollow">'
        '<title>سناریوی نمایشی پژوهش | Private Capital</title>'
        '<link rel="stylesheet" href="/assets/css/style.css">'
        '<link rel="stylesheet" href="/assets/css/exploration-preview.css">'
        '</head><body><main class="container" style="padding:70px 0">'
        '<p class="explore-preview-note">نمونهٔ نمایشی مخصوص preview؛ این مقاله و ارتباط آن canonical نیست.</p>'
        '<h1>سناریوی نمایشی پژوهش دوم</h1>'
        '<p>این صفحه فقط برای آزمودن چیدمان چند پژوهش در صفحهٔ Atlas ساخته شده است.</p>'
        '<p><a href="/atlas/concept/private-capital/">بازگشت به مدخل سرمایه خصوصی در Atlas</a></p>'
        '</main></body></html>', encoding="utf-8",
    )
    return destination


def preview_research_page(page, article, catalog):
    """Compose a reading-first rail from the built article, only in memory."""
    marker = '<div data-research-connections>'
    end_marker = '</div><!-- research-connections -->'
    start = page.find(marker)
    end = page.find(end_marker, start)
    if start < 0 or end < 0:
        raise ValueError(f"{article['id']}: Research connections target missing")
    page = page[:start] + page[end + len(end_marker):]
    opening, closing = '<article>', '</article>'
    start, end = page.find(opening), page.find(closing)
    if start < 0 or end < start:
        raise ValueError(f"{article['id']}: article element missing")
    body = page[start + len(opening):end]
    # Keep the authored lead text and image together, without modifying the article source.
    lead = re.compile(r'<div data-article-renderer-section="introduction">(.*?)'
                      r'(<figure>.*?</figure>)</div>', re.S)
    body, replaced = lead.subn(
        lambda match: ('<div class="explore-lead"><div class="explore-lead-text" '
                       'data-article-renderer-section="introduction">' + match.group(1)
                       + '</div>' + match.group(2).replace('<figure>',
                                                           '<figure class="explore-lead-media">', 1)
                       + '</div>'), body, count=1,
    )
    if replaced != 1:
        raise ValueError(f"{article['id']}: lead introduction/figure contract missing")
    body, headings = exploration.article_toc(body)
    rail = exploration.research_rail(
        article, catalog, SITE_ROOT, preview_entity_url,
        static_builder.research_connections.editorial_related, headings,
    )
    layout = ('<div class="explore-reading-layout"><article class="explore-reading">'
              + body
              + '</article>' + rail + '</div>')
    page = page[:start] + layout + page[end + len(closing):]
    # The static article is complete. Its client re-render would discard H3 IDs.
    runtime_script = '<script src="../assets/js/article-page.js"></script>'
    if page.count(runtime_script) != 1:
        raise ValueError(f"{article['id']}: unexpected Article enhancement script")
    page = page.replace(runtime_script, '')
    page = page.replace('</head>',
                        '<link rel="stylesheet" href="/assets/css/exploration-preview.css">\n</head>', 1)
    canonical = '<link rel="canonical" href="https://privatecapital.ir' + article["url"] + '">'
    if page.count(canonical) != 1:
        raise ValueError(f"{article['id']}: preview requires one canonical link to replace")
    return page.replace(canonical, '<meta name="robots" content="noindex,nofollow">')


def preview_atlas_page(page, entity_id, claims, entities, relation_contract, research_index):
    """Place the Entity's rendered sections beside a TOC and exploration rail."""
    hero = page.find('<section class="page-hero">')
    hero_end = page.find('</section>', hero)
    root_end = page.find('\n</div>\n\n</main>', hero_end)
    if hero < 0 or hero_end < 0 or root_end < 0:
        raise ValueError(f"{entity_id}: Atlas root/hero contract missing")
    hero_end += len('</section>')
    content, headings = exploration.article_toc(
        page[hero_end:root_end], levels=(2,), prefix="atlas",
    )
    rail = exploration.atlas_rail(
        entity_id, claims, entities, relation_contract, preview_entity_url,
        static_builder.render_claim_relation, research_index, headings,
    )
    layout = ('<div class="explore-reading-layout atlas-reading-layout">'
              '<div class="atlas-primary">' + content + '</div>' + rail + '</div>')
    return (page[:hero_end] + layout + page[root_end:]).replace(
        '</head>', '<link rel="stylesheet" href="/assets/css/exploration-preview.css">\n</head>', 1,
    )


def preview_entity_url(entity_id, entity_type):
    public_url = static_builder.entity_url(entity_id, entity_type)
    if public_url:
        return public_url
    if not isinstance(entity_id, str) or not isinstance(entity_type, str):
        return None
    config = PREVIEW_TYPES.get(entity_type)
    if not config:
        return None
    namespace, segment = config
    prefix = namespace + ":"
    if not entity_id.startswith(prefix) or len(entity_id) == len(prefix):
        return None
    slug = entity_id[len(prefix):]
    return f"/atlas/_preview/{segment}/{quote(slug, safe='')}/"


def build_preview(output_root, *, showcase=False):
    output_root = Path(output_root).resolve()
    if output_root == SITE_ROOT or SITE_ROOT in output_root.parents:
        raise ValueError("Preview output must be outside the repository")

    entities = static_builder.load_entities()
    claims = static_builder.load_claims()
    evidence = static_builder.load_evidence()
    sources = static_builder.load_sources()
    relation_contract = static_builder.load_relation_contract()
    catalog = catalog_builder.collect_entities()
    catalog_builder.validate_unique_ids(catalog)

    for entry in catalog:
        if entry["type"] in PREVIEW_TYPES:
            entry["route"] = preview_entity_url(entry["id"], entry["type"])
            if not entry["route"]:
                raise ValueError(f"Invalid preview Entity ID/type: {entry['id']} / {entry['type']}")
    catalog.sort(key=lambda entry: entry["id"])
    research_index = static_builder.research_connections.reverse_index(
        SITE_ROOT, catalog, preview=True, preview_resolver=preview_entity_url,
    )
    generated = []
    if showcase:
        generated.append(showcase_article(output_root, research_index, catalog))
    catalog_builder.write_json(
        output_root / "atlas/discovery/research-by-entity.json", research_index,
    )
    catalog_builder.write_json(
        output_root / "atlas/catalog/index.json",
        {"version": "1.0", "entities": catalog},
    )

    preview_css = output_root / "assets/css/exploration-preview.css"
    preview_css.parent.mkdir(parents=True, exist_ok=True)
    preview_css.write_bytes((TOOLS_DIR / "exploration-preview.css").read_bytes())
    for entry in catalog:
        route = entry.get("route")
        if not route:
            continue
        entity = entities[entry["id"]]
        output_path = output_root / route.lstrip("/") / "index.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        page = static_builder.render_entity(
            entity, claims, evidence, sources, entities, relation_contract,
            preview=True, route_resolver=preview_entity_url,
        )
        page = preview_atlas_page(
            page, entry["id"], claims, entities, relation_contract, research_index,
        )
        output_path.write_text(
            page,
            encoding="utf-8",
        )
        generated.append(output_path)
    # The public article remains untouched; the overlay shows REVIEW context
    # only on loopback, with noindex and no canonical declaration.
    for article in static_builder.research_connections.eligible_articles(SITE_ROOT):
        source = static_builder.research_connections.article_path(
            SITE_ROOT, article["url"], article["id"]
        )
        page = preview_research_page(source.read_text(encoding="utf-8"), article, catalog)
        destination = output_root / article["url"].lstrip("/")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(page, encoding="utf-8")
        generated.append(destination)
    return generated


class PreviewHandler(SimpleHTTPRequestHandler):
    """Prefer generated preview files; read all other assets from the site tree."""

    def translate_path(self, path):
        overlay_path = Path(super().translate_path(path))
        if overlay_path.is_file() or (overlay_path / "index.html").is_file():
            return str(overlay_path)
        return str(SITE_ROOT / overlay_path.relative_to(self.directory))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--showcase", action="store_true",
                        help="Add an explicitly synthetic second Research item to the temporary Atlas preview")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="atlas-entity-preview-") as temp_dir:
        generated = build_preview(temp_dir, showcase=args.showcase)
        handler = lambda *a, **kw: PreviewHandler(*a, directory=temp_dir, **kw)
        with ThreadingHTTPServer(("127.0.0.1", args.port), handler) as server:
            print(f"Generated {len(generated)} preview pages in a temporary overlay.", flush=True)
            print(f"Open http://127.0.0.1:{server.server_port}/atlas/", flush=True)
            print("Press Ctrl+C to stop and remove the preview.", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass


if __name__ == "__main__":
    main()
