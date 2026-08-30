import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTITIES_DIR = ROOT / "entities"
INDEX_PATH = ENTITIES_DIR / "index.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def collect_entities():
    entities = []

    for path in sorted(ENTITIES_DIR.rglob("*.json")):
        if path == INDEX_PATH:
            continue

        data = load_json(path)

        required_fields = [
            "id",
            "type",
            "name",
            "lifecycleStatus"
        ]

        missing = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing:
            raise ValueError(
                f"{path.relative_to(ROOT)}: "
                f"missing required fields: "
                f"{', '.join(missing)}"
            )

        entity = {
            "id": data["id"],
            "type": data["type"],
            "name": data["name"],
            "lifecycleStatus": data["lifecycleStatus"]
        }

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


def main():
    entities = collect_entities()

    validate_unique_ids(entities)

    entities.sort(
        key=lambda entity: entity["id"]
    )

    output = {
        "version": "1.0",
        "entities": entities
    }

    with INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )
        f.write("\n")

    print(
        f"Generated {INDEX_PATH.relative_to(ROOT)} "
        f"with {len(entities)} entities."
    )


if __name__ == "__main__":
    main()
