import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    errors = []

    index = load_json(ROOT / "entities" / "index.json")

    entity_ids = {
        entity["id"]
        for entity in index.get("entities", [])
        if "id" in entity
    }

    claim_ids = set()
    source_ids = set()

    # Collect all sources
    sources_dir = ROOT / "sources"

    for path in sources_dir.glob("*.json"):
        data = load_json(path)

        for source in data.get("sources", []):
            source_id = source.get("id")

            if source_id:
                if source_id in source_ids:
                    errors.append(
                        f"Duplicate source ID: {source_id}"
                    )
                source_ids.add(source_id)

    # Collect and validate claims
    claims_dir = ROOT / "claims"

    for path in claims_dir.glob("*.json"):
        data = load_json(path)

        for claim in data.get("claims", []):
            claim_id = claim.get("id")

            if not claim_id:
                errors.append(
                    f"{path}: claim without id"
                )
                continue

            if claim_id in claim_ids:
                errors.append(
                    f"Duplicate claim ID: {claim_id}"
                )

            claim_ids.add(claim_id)

            has_object = "object" in claim
            has_value = "value" in claim

            if has_object == has_value:
                errors.append(
                    f"{claim_id}: exactly one of object/value is required"
                )

            subject = claim.get("subject")

            if not subject:
                errors.append(
                    f"{claim_id}: missing subject"
                )

    # Validate references inside evidence
    evidence_dir = ROOT / "evidence"

    for path in evidence_dir.glob("*.json"):
        data = load_json(path)

        for evidence in data.get("evidence", []):
            claim_id = evidence.get("claim")
            source_id = evidence.get("source")

            if claim_id not in claim_ids:
                errors.append(
                    f"{evidence.get('id')}: unknown claim {claim_id}"
                )

            if source_id not in source_ids:
                errors.append(
                    f"{evidence.get('id')}: unknown source {source_id}"
                )

    # Validate claim object references
    for path in claims_dir.glob("*.json"):
        data = load_json(path)

        for claim in data.get("claims", []):
            claim_id = claim.get("id")

            if "object" in claim:
                object_id = claim["object"]

                if object_id not in entity_ids:
                    errors.append(
                        f"{claim_id}: unknown object entity {object_id}"
                    )

    if errors:
        print("Atlas validation FAILED")
        print()

        for error in errors:
            print(f"- {error}")

        sys.exit(1)

    print("Atlas validation PASSED")


if __name__ == "__main__":
    main()
