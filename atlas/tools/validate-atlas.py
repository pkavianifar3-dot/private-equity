import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, RefResolver


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "schemas"


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def add_schema_errors(instance, schema_path, label, errors):
    try:
        schema = load_json(schema_path)

        resolver = RefResolver(
            schema_path.resolve().as_uri(),
            schema
        )

        validator = Draft202012Validator(
            schema,
            resolver=resolver
        )

        for error in sorted(
            validator.iter_errors(instance),
            key=lambda e: list(e.absolute_path)
        ):
            location = ".".join(
                str(part) for part in error.absolute_path
            )

            if location:
                errors.append(
                    f"{label}: schema error at "
                    f"{location}: {error.message}"
                )
            else:
                errors.append(
                    f"{label}: schema error: {error.message}"
                )

    except Exception as exc:
        errors.append(
            f"{label}: schema validation failed: {exc}"
        )


def load_registry(path, errors):
    try:
        return load_json(path)
    except Exception as exc:
        errors.append(
            f"{path.relative_to(ROOT)}: invalid JSON: {exc}"
        )
        return {}


def collect_entities(errors):
    index_path = ROOT / "entities" / "index.json"
    index = load_registry(index_path, errors)

    entities = index.get("entities", [])

    if not isinstance(entities, list):
        errors.append(
            "entities/index.json: 'entities' must be an array"
        )
        return {}, set()

    entity_by_id = {}
    entity_ids = set()

    for entity in entities:
        entity_id = entity.get("id")

        if not entity_id:
            errors.append(
                "entities/index.json: entity without id"
            )
            continue

        add_schema_errors(
            entity,
            SCHEMAS_DIR / "atlas-schema-v1.json",
            f"entities/index.json:{entity_id}",
            errors
        )

        if entity_id in entity_ids:
            errors.append(
                f"Duplicate entity ID: {entity_id}"
            )

        entity_ids.add(entity_id)
        entity_by_id[entity_id] = entity

    for path in sorted(
        ROOT.joinpath("entities").rglob("*.json")
    ):
        if path.name == "index.json":
            continue

        data = load_registry(path, errors)

        add_schema_errors(
            data,
            SCHEMAS_DIR / "atlas-schema-v1.json",
            str(path.relative_to(ROOT)),
            errors
        )

        entity_id = data.get("id")

        if not entity_id:
            errors.append(
                f"{path.relative_to(ROOT)}: missing entity id"
            )
            continue

        if entity_id not in entity_ids:
            errors.append(
                f"{path.relative_to(ROOT)}: entity {entity_id} "
                f"is missing from entities/index.json"
            )
            continue

        indexed = entity_by_id[entity_id]

        if indexed.get("name") != data.get("name"):
            errors.append(
                f"{entity_id}: index name does not match "
                f"canonical entity file"
            )

        if indexed.get("type") != data.get("type"):
            errors.append(
                f"{entity_id}: index type does not match "
                f"canonical entity file"
            )

        if (
            indexed.get("lifecycleStatus")
            != data.get("lifecycleStatus")
        ):
            errors.append(
                f"{entity_id}: index lifecycleStatus does not "
                f"match canonical entity file"
            )

    return entity_by_id, entity_ids


def collect_claims(errors):
    claim_ids = set()
    claims = []

    for path in sorted(
    (ROOT / "claims").glob("*.json")
):
    data = load_registry(path, errors)

    if "version" not in data:
        errors.append(
            f"{path.relative_to(ROOT)}: missing 'version'"
        )

    if not isinstance(data.get("claims"), list):
        errors.append(
            f"{path.relative_to(ROOT)}: "
            f"'claims' must be an array"
        )
        continue

        for claim in data["claims"]:
            claim_id = claim.get("id", "<missing-id>")

            add_schema_errors(
                claim,
                SCHEMAS_DIR / "claim-schema-v1.json",
                f"{path.relative_to(ROOT)}:{claim_id}",
                errors
            )

            if "id" not in claim:
                errors.append(
                    f"{path.relative_to(ROOT)}: claim without id"
                )
                continue

            if claim_id in claim_ids:
                errors.append(
                    f"Duplicate claim ID: {claim_id}"
                )

            claim_ids.add(claim_id)
            claims.append(claim)

    return claim_ids, claims


def collect_sources(errors):
    source_ids = set()
    sources = []

    for path in sorted(
        (ROOT / "sources").glob("*.json")
    ):
        data = load_registry(path, errors)

        add_schema_errors(
            data,
            SCHEMAS_DIR / "source-schema-v1.json",
            str(path.relative_to(ROOT)),
            errors
        )

        source_list = data.get("sources", [])

        if not isinstance(source_list, list):
            errors.append(
                f"{path.relative_to(ROOT)}: "
                f"'sources' must be an array"
            )
            continue

        for source in source_list:
            source_id = source.get("id")

            if not source_id:
                errors.append(
                    f"{path.relative_to(ROOT)}: source without id"
                )
                continue

            if source_id in source_ids:
                errors.append(
                    f"Duplicate source ID: {source_id}"
                )

            source_ids.add(source_id)
            sources.append(source)

    return source_ids, sources


def collect_evidence(errors):
    evidence_ids = set()
    evidence_records = []

    for path in sorted(
        (ROOT / "evidence").glob("*.json")
    ):
        data = load_registry(path, errors)

        add_schema_errors(
            data,
            SCHEMAS_DIR / "evidence-schema-v1.json",
            str(path.relative_to(ROOT)),
            errors
        )

        evidence_list = data.get("evidence", [])

        if not isinstance(evidence_list, list):
            errors.append(
                f"{path.relative_to(ROOT)}: "
                f"'evidence' must be an array"
            )
            continue

        for evidence in evidence_list:
            evidence_id = evidence.get("id")

            if not evidence_id:
                errors.append(
                    f"{path.relative_to(ROOT)}: "
                    f"evidence without id"
                )
                continue

            if evidence_id in evidence_ids:
                errors.append(
                    f"Duplicate evidence ID: {evidence_id}"
                )

            evidence_ids.add(evidence_id)
            evidence_records.append(evidence)

    return evidence_ids, evidence_records


def load_taxonomies(errors):
    relation_types_data = load_registry(
        ROOT / "taxonomies" / "relation-types.json",
        errors
    )

    relation_rules_data = load_registry(
        ROOT / "taxonomies" / "relation-rules.json",
        errors
    )

    relation_types = {
        item["id"]
        for item in relation_types_data.get(
            "relation_types",
            []
        )
        if isinstance(item, dict) and "id" in item
    }

    relation_rules = {
        item["relation"]: item
        for item in relation_rules_data.get(
            "rules",
            []
        )
        if isinstance(item, dict)
        and "relation" in item
    }

    for relation in relation_rules:
        if relation not in relation_types:
            errors.append(
                f"Relation rule references unknown predicate: "
                f"{relation}"
            )

    for relation in sorted(
        relation_types - set(relation_rules)
    ):
        errors.append(
            f"Relation type has no rule: {relation}"
        )

    return relation_types, relation_rules


def validate_claim_integrity(
    claims,
    entity_by_id,
    entity_ids,
    relation_types,
    relation_rules,
    errors
):
    for claim in claims:
        claim_id = claim.get("id", "<missing-id>")
        subject_id = claim.get("subject")
        predicate = claim.get("predicate")

        if subject_id not in entity_ids:
            errors.append(
                f"{claim_id}: unknown subject entity "
                f"{subject_id}"
            )

        if predicate not in relation_types:
            errors.append(
                f"{claim_id}: unknown predicate "
                f"{predicate}"
            )

        has_object = "object" in claim
        has_value = "value" in claim

        if has_object == has_value:
            errors.append(
                f"{claim_id}: exactly one of object/value "
                f"is required"
            )
            continue

        rule = relation_rules.get(predicate)

        if not rule:
            continue

        if subject_id in entity_by_id:
            subject_type = entity_by_id[
                subject_id
            ].get("type")

            allowed_subject_types = rule.get(
                "subject_types",
                []
            )

            if (
                allowed_subject_types
                and subject_type
                not in allowed_subject_types
            ):
                errors.append(
                    f"{claim_id}: subject type "
                    f"{subject_type} is not allowed "
                    f"for {predicate}"
                )

        if has_object:
            object_id = claim.get("object")

            if object_id not in entity_ids:
                errors.append(
                    f"{claim_id}: unknown object entity "
                    f"{object_id}"
                )
                continue

            object_type = entity_by_id[
                object_id
            ].get("type")

            allowed_object_types = rule.get(
                "object_types",
                []
            )

            if (
                allowed_object_types
                and object_type not in allowed_object_types
            ):
                errors.append(
                    f"{claim_id}: object type "
                    f"{object_type} is not allowed "
                    f"for {predicate}"
                )

        if has_value:
            value = claim.get("value")

            if not isinstance(value, dict):
                errors.append(
                    f"{claim_id}: value must be an object"
                )


def validate_evidence_integrity(
    evidence_records,
    claims,
    claim_ids,
    source_ids,
    errors
):
    claim_to_evidence = {}

    for evidence in evidence_records:
        evidence_id = evidence.get("id")
        claim_id = evidence.get("claim")
        source_id = evidence.get("source")

        if claim_id not in claim_ids:
            errors.append(
                f"{evidence_id}: unknown claim "
                f"{claim_id}"
            )
        else:
            claim_to_evidence.setdefault(
                claim_id,
                []
            ).append(evidence_id)

        if source_id not in source_ids:
            errors.append(
                f"{evidence_id}: unknown source "
                f"{source_id}"
            )

    for claim in claims:
        claim_id = claim.get("id")

        if not claim_id:
            continue

        if claim_id not in claim_to_evidence:
            errors.append(
                f"{claim_id}: missing evidence"
            )


def main():
    errors = []

    entity_by_id, entity_ids = collect_entities(errors)

    relation_types, relation_rules = load_taxonomies(
        errors
    )

    source_ids, _ = collect_sources(errors)

    claim_ids, claims = collect_claims(errors)

    validate_claim_integrity(
        claims,
        entity_by_id,
        entity_ids,
        relation_types,
        relation_rules,
        errors
    )

    _, evidence_records = collect_evidence(errors)

    validate_evidence_integrity(
    evidence_records,
    claims,
    claim_ids,
    source_ids,
    errors
)

    if errors:
        print("Atlas validation FAILED")
        print()

        for error in errors:
            print(f"- {error}")

        print()
        print(f"Total errors: {len(errors)}")
        sys.exit(1)

    print("Atlas validation PASSED")


if __name__ == "__main__":
    main()
