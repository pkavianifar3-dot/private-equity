"""Serve an isolated Atlas Entity preview without writing public artifacts.

Run ``python atlas/tools/preview-entities.py`` and open the printed loopback URL.
The temporary overlay is removed when the server stops.
"""

import argparse
import importlib.util
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


def build_preview(output_root):
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
    catalog_builder.write_json(
        output_root / "atlas/catalog/index.json",
        {"version": "1.0", "entities": catalog},
    )

    generated = []
    for entry in catalog:
        route = entry.get("route")
        if not route:
            continue
        entity = entities[entry["id"]]
        output_path = output_root / route.lstrip("/") / "index.html"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            static_builder.render_entity(
                entity, claims, evidence, sources, entities, relation_contract,
                preview=True, route_resolver=preview_entity_url,
            ),
            encoding="utf-8",
        )
        generated.append(output_path)
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
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="atlas-entity-preview-") as temp_dir:
        generated = build_preview(temp_dir)
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
