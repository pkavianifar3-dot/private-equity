import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

ENTITIES_DIR = ROOT / "entities"
ENTITIES_INDEX_PATH = ENTITIES_DIR / "index.json"

CLAIMS_DIR = ROOT / "claims"
CLAIMS_INDEX_PATH = CLAIMS_DIR / "index.json"

EVIDENCE_DIR = ROOT / "evidence"
EVIDENCE_INDEX_PATH = EVIDENCE_DIR / "index.json"

SOURCES_DIR = ROOT / "sources"
SOURCES_INDEX_PATH = SOURCES_DIR / "index.json"


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
    claim_sources = {}
    seen_claim_ids = set()

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
                    f"{path.relative_to(ROOT)}: "
                    "claim missing required field: id"
                )

            if claim_id in seen_claim_ids:
                raise ValueError(
                    f"Duplicate claim ID: {claim_id}"
                )

            seen_claim_ids.add(claim_id)
            claim_sources[claim_id] = path.name

            linked_entity_ids = set()

            subject = claim.get("subject")
            object_id = claim.get("object")

            if isinstance(subject, str):
                linked_entity_ids.add(subject)

            if isinstance(object_id, str):
                linked_entity_ids.add(object_id)

            for entity_id in sorted(linked_entity_ids):
                claims_by_entity.setdefault(
                    entity_id,
                    set()
                ).add(claim_id)

    claims_by_entity = {
        entity_id: sorted(claim_ids)
        for entity_id, claim_ids
        in sorted(claims_by_entity.items())
    }

    claim_sources = {
        claim_id: claim_sources[claim_id]
        for claim_id in sorted(claim_sources)
    }

    return claims_by_entity, claim_sources


def collect_evidence_index():
    evidence_sources = {}
    evidence_by_claim = {}
    seen_evidence_ids = set()

    for path in sorted(EVIDENCE_DIR.glob("*.json")):
        if path == EVIDENCE_INDEX_PATH:
            continue

        data = load_json(path)

        if "evidence" not in data:
            raise ValueError(
                f"{path.relative_to(ROOT)}: "
                "missing required field: evidence"
            )

        if not isinstance(data["evidence"], list):
            raise ValueError(
                f"{path.relative_to(ROOT)}: "
                "evidence must be an array"
            )

        for evidence in data["evidence"]:
            evidence_id = evidence.get("id")
            claim_id = evidence.get("claim")

            if not evidence_id:
                raise ValueError(
                    f"{path.relative_to(ROOT)}: "
                    "evidence missing required field: id"
                )

            if not claim_id:
                raise ValueError(
                    f"{path.relative_to(ROOT)}: "
                    f"evidence {evidence_id} "
                    "missing required field: claim"
                )

            if evidence_id in seen_evidence_ids:
                raise ValueError(
                    f"Duplicate evidence ID: {evidence_id}"
                )

            seen_evidence_ids.add(evidence_id)

            evidence_sources[evidence_id] = path.name

            evidence_by_claim.setdefault(
                claim_id,
                set()
            ).add(evidence_id)

    return {
        "evidence": {
            evidence_id: evidence_sources[evidence_id]
            for evidence_id in sorted(evidence_sources)
        },
        "claims": {
            claim_id: sorted(evidence_ids)
            for claim_id, evidence_ids
            in sorted(evidence_by_claim.items())
        }
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

    claims_by_entity, claim_sources = collect_claims_by_entity()

    claims_index_output = {
        "version": "1.0",
        "entities": claims_by_entity,
        "claims": claim_sources
    }

    write_json(
        CLAIMS_INDEX_PATH,
        claims_index_output
    )

    evidence_index = collect_evidence_index()
    
    evidence_index_output = {
        "version": "1.0",
        "evidence": evidence_index["evidence"],
        "claims": evidence_index["claims"]
    }

    write_json(
        EVIDENCE_INDEX_PATH,
        evidence_index_output
    )

    source_sources = collect_record_sources(
        SOURCES_DIR,
        "sources",
        "source"
    )

    source_index_output = {
        "version": "1.0",
        "sources": source_sources
    }

    write_json(
        SOURCES_INDEX_PATH,
        source_index_output
    )

    print(
        f"Generated {ENTITIES_INDEX_PATH.relative_to(ROOT)} "
        f"with {len(entities)} entities."
    )

    print(
        f"Generated {CLAIMS_INDEX_PATH.relative_to(ROOT)} "
        f"with {len(claims_by_entity)} entities linked to claims "
        f"and {len(claim_sources)} claims indexed."
    )

    print(
        f"Generated {EVIDENCE_INDEX_PATH.relative_to(ROOT)} "
        f"with {len(evidence_index['evidence'])} evidence items indexed "
        f"across {len(evidence_index['claims'])} claims."
    )

    print(
        f"Generated {SOURCES_INDEX_PATH.relative_to(ROOT)} "
        f"with {len(source_sources)} sources indexed."
    )


if __name__ == "__main__":
    main()
