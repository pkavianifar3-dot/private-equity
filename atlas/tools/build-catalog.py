import json
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]

ENTITIES_DIR = ROOT / "entities"
CATALOG_DIR = ROOT / "catalog"
CATALOG_PATH = CATALOG_DIR / "index.json"

SITE_ORIGIN = "https://privatecapital.ir"

ROUTES = {
    "Person": "person",
    "Organization": "organization",
    "Investment": "investment",
    "Concept": "concept",
}


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def entity_url(entity_id, entity_type):
    if not entity_id or ":" not in entity_id:
        return None

    _, slug = entity_id.split(":", 1)

    if not slug:
        return None

    route = ROUTES.get(entity_type)

    if not route:
        return None

    return f"/atlas/{route}/{quote(slug, safe='')}/"


def collect_entities():
    entities = []

    for path in sorted(ENTITIES_DIR.rglob("*.json")):
        if path == ENTITIES_DIR / "index.json":
            continue

        data = load_json(path)

        entity_id = data.get("id")
        entity_type = data.get("type")
        name = data.get("name")
        lifecycle_status = data.get("lifecycleStatus")

        if not entity_id:
            raise ValueError(
                f"{path.relative_to(ROOT)}: missing required field: id"
            )

        if not entity_type:
            raise ValueError(
                f"{path.relative_to(ROOT)}: missing required field: type"
            )

        if not isinstance(name, dict):
            raise ValueError(
                f"{path.relative_to(ROOT)}: name must be an object"
            )

        if not lifecycle_status:
            raise ValueError(
                f"{path.relative_to(ROOT)}: "
                "missing required field: lifecycleStatus"
            )

        entity = {
            "id": entity_id,
            "type": entity_type,
            "name": {
                "fa": name.get("fa"),
                "en": name.get("en"),
            },
            "lifecycleStatus": lifecycle_status,
        }

        aliases = data.get("aliases")

        if aliases:
            entity["aliases"] = aliases

        domains = data.get("domains")

        if domains:
            entity["domains"] = domains

        route = entity_url(entity_id, entity_type)

        if route:
            entity["route"] = route

        entities.append(entity)

    return entities


def validate_unique_ids(entities):
    seen = set()

    for entity in entities:
        entity_id = entity["id"]

        if entity_id in seen:
            raise ValueError(
                f"Duplicate entity ID: {entity_id}"
            )

        seen.add(entity_id)


def write_json(path, output):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2,
        )
        f.write("\n")


def main():
    entities = collect_entities()

    validate_unique_ids(entities)

    entities.sort(key=lambda entity: entity["id"])

    output = {
        "version": "1.0",
        "entities": entities,
    }

    write_json(CATALOG_PATH, output)

    print(
        f"Generated {CATALOG_PATH.relative_to(ROOT.parent)} "
        f"with {len(entities)} entities."
    )


if __name__ == "__main__":
    main()
