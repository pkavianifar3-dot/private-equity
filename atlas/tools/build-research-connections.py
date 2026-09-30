"""Generate public Research ↔ Entity index and static article context panels."""

import importlib.util
import json
import re
from pathlib import Path

import research_connections as connections


ROOT = Path(__file__).resolve().parents[2]


def load_catalog():
    spec = importlib.util.spec_from_file_location("build_catalog", ROOT / "atlas/tools/build-catalog.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def updated_article(path, panel):
    original = path.read_text(encoding="utf-8")
    pattern = r'(<div data-research-connections>)[\s\S]*?(</div><!-- research-connections -->)'
    updated, count = re.subn(pattern, lambda match: match.group(1) + panel + match.group(2), original)
    if count != 1:
        raise ValueError(f"{path}: expected one Research connections target, got {count}")
    return updated if updated != original else None


def main():
    catalog = load_catalog().collect_entities()
    index = connections.reverse_index(ROOT, catalog)
    updates = []
    for article in connections.eligible_articles(ROOT):
        path = connections.article_path(ROOT, article["url"], article["id"])
        updated = updated_article(
            path, connections.render_article_context(article, catalog, ROOT)
        )
        if updated is not None:
            updates.append((path, updated))
    connections.INDEX_PATH.write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    for path, updated in updates:
        path.write_text(updated, encoding="utf-8", newline="")
    print(f"Generated Research connections for {len(index['entities'])} public Entities.")


if __name__ == "__main__":
    main()
