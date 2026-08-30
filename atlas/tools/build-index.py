import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENTITIES_DIR = ROOT / "entities"
ENTITIES_INDEX_PATH = ENTITIES_DIR / "index.json"

CLAIMS_DIR = ROOT / "claims"
CLAIMS_INDEX_PATH = CLAIMS_DIR / "index.json"


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def collect_entities():
    entities = []

    for path in sorted(ENTITIES_DIR.rglob("*.json")):
        if path == ENTITIES_INDEX_PATH:
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


def collect_claims_by_entity():
    claims_by_entity = {}

    for path in sorted(CLAIMS_DIR.glob("*.json")):
        if path == CLAIMS_INDEX_PATH:
            continue

        data = load_json(path)

        if "claims" not in data:
            raise ValueError(
                f"{path.relative_to(ROOT)}: missing required field: claims"
            )

        for claim in data["claims"]:
            claim_id = claim.get("id")

            if not claim_id:
                raise ValueError(
                    f"{path.relative_to(ROOT)}: claim missing required field: id"
                )

            linked_entity_ids = set()

            subject = claim.get("subject")
            object_id = claim.get("object")

            if isinstance(subject, str):
                linked_entity_ids.add(subject)

            if isinstance(object_id, str):
                linked_entity_ids.add(object_id)

            for entity_id in sorted(linked_entity_ids):
                claims_by_entity.setdefault(entity_id, set()).add(claim_id)

    return {
        entity_id: sorted(claim_ids)
        for entity_id, claim_ids in sorted(claims_by_entity.items())
    }


def write_json(path, output):
    with path.open("w", encoding="utf-8") as f:
        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )
        f.write("\n")


def main():
    entities = collect_entities()

    validate_unique_ids(entities)

    entities.sort(
        key=lambda entity: entity["id"]
    )

    entity_index_output = {
        "version": "1.0",
        "entities": entities
    }

    write_json(
        ENTITIES_INDEX_PATH,
        entity_index_output
    )

    claims_by_entity = collect_claims_by_entity()

    claims_index_output = {
        "version": "1.0",
        "entities": claims_by_entity
    }

    write_json(
        CLAIMS_INDEX_PATH,
        claims_index_output
    )

    print(
        f"Generated {ENTITIES_INDEX_PATH.relative_to(ROOT)} "
        f"with {len(entities)} entities."
    )

    print(
        f"Generated {CLAIMS_INDEX_PATH.relative_to(ROOT)} "
        f"with {len(claims_by_entity)} entities linked to claims."
    )


if __name__ == "__main__":
    main()
