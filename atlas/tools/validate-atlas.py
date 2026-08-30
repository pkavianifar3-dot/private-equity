import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, RefResolver
except ImportError:
    print("Atlas validation FAILED")
    print("- Missing dependency: jsonschema")
    sys.exit(1)


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS_DIR = ROOT / "schemas"


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_json_schema(instance, schema_path, label, errors):
    """
    Validate one object against one JSON Schema.

    Schema errors are returned as readable validation messages.
    """
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
            key=lambda e: list(e.path)
        ):
            location = ".".join(
                str(item) for item in error.absolute_path
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


def collect_entities(errors):
    """
    Load the current entity index.

    The index is still the current operational registry.
    Canonical/index synchronization will be hardened separately.
    """
    index_path = ROOT / "entities" / "index.json"

    try:
        index = load_json(index_path)
    except Exception as exc:
        errors.append(
            f"entities/index.json: cannot load: {exc}"
        )
        return {}, set()

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

        if entity_id in entity_ids:
            errors.append(
                f"Duplicate entity ID: {entity_id}"
            )

        entity_ids.add(entity_id)
        entity_by_id[entity_id] = entity

    return entity_by_id, entity_ids


def collect_sources(errors):
    source_ids = set()
    sources = []

    sources_dir = ROOT / "sources"

    for path in sorted(sources_dir.glob("*.json")):
        try:
            data = load_json(path)
        except Exception as exc:
            errors.append(
                f"{path}: invalid JSON: {exc}"
            )
            continue

        validate_json_schema(
            data,
            SCHEMAS_DIR / "source-schema-v1.json",
            str(path.relative_to(ROOT)),
            errors
        )

        for source in data.get("sources", []):
            source_id = source.get("id")

            if not source_id:
                errors.append(
                    f"{path}: source without id"
                )
                continue

            if source_id in source_ids:
                errors.append(
                    f"Duplicate source ID: {source_id}"
                )

            source_ids.add(source_id)
            sources.append(source)

    return source_ids, sources


def collect_claims(errors):
    claim_ids = set()
    claims = []

    claims_dir = ROOT / "claims"

    for path in sorted(claims_dir.glob("*.json")):
        try:
            data = load_json(path)
        except Exception as exc:
            errors.append(
                f"{path}: invalid JSON: {exc}"
            )
            continue

        for claim in data.get("claims", []):
            claim_id = claim.get("id", "<missing-id>")

            validate_json_schema(
                claim,
                SCHEMAS_DIR / "claim-schema-v1.json",
                f"{path.relative_to(ROOT)}:{claim_id}",
                errors
            )

            if "id" not in claim:
                errors.append(
                    f"{path}: claim without id"
                )
                continue

            if claim_id in claim_ids:
                errors.append(
                    f"Duplicate claim ID: {claim_id}"
                )

            claim_ids.add(claim_id)
            claims.append(claim)

    return claim_ids, claims


def collect_evidence(errors):
    evidence_ids = set()
    evidence_records = []

    evidence_dir = ROOT / "evidence"

    for path in sorted(evidence_dir.glob("*.json")):
        try:
            data = load_json(path)
        except Exception as exc:
            errors.append(
                f"{path}: invalid JSON: {exc}"
            )
            continue

        validate_json_schema(
            data,
            SCHEMAS_DIR / "evidence-schema-v1.json",
            str(path.relative_to(ROOT)),
            errors
        )

        for evidence in data.get("evidence", []):
            evidence_id = evidence.get("id")

            if not evidence_id:
                errors.append(
                    f"{path}: evidence without id"
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
    relation_types_path = (
        ROOT / "taxonomies" / "relation-types.json"
    )

    relation_rules_path = (
        ROOT / "taxonomies" / "relation-rules.json"
    )

    try:
        relation_types_data = load_json(
            relation_types_path
        )
    except Exception as exc:
        errors.append(
            f"{relation_types_path}: cannot load: {exc}"
        )
        relation_types_data = {}

    try:
        relation_rules_data = load_json(
            relation_rules_path
        )
    except Exception as exc:
        errors.append(
            f"{relation_rules_path}: cannot load: {exc}"
        )
        relation_rules_data = {}

    relation_types = {
        item["id"]
        for item in relation_types_data.get(
            "relation_types",
            []
        )
        if "id" in item
    }

    relation_rules = {
        rule["relation"]: rule
        for rule in relation_rules_data.get(
            "rules",
            []
        )
        if "relation" in rule
    }

    for relation in relation_rules:
        if relation not in relation_types:
            errors.append(
                f"Relation rule references unknown predicate: "
                f"{relation}"
            )

    missing_rules = relation_types - set(relation_rules)

    for relation in sorted(missing_rules):
        errors.append(
            f"Relation type has no rule: {relation}"
        )

    return relation_types, relation_rules


def validate_claim_integrity(
    claims,
    claim_ids,
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

        if not subject_id:
            errors.append(
                f"{claim_id}: missing subject"
            )
        elif subject_id not in entity_ids:
            errors.append(
                f"{claim_id}: unknown subject entity "
                f"{subject_id}"
            )

        if not predicate:
            errors.append(
                f"{claim_id}: missing predicate"
            )
        elif predicate not in relation_types:
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

        if has_object:
            object_id = claim.get("object")

            if object_id not in entity_ids:
                errors.append(
                    f"{claim_id}: unknown object entity "
                    f"{object_id}"
                )

        if rule and subject_id in entity_by_id:
            subject_type = entity_by_id[
                subject_id
            ].get("type")

            allowed_subject_types = rule.get(
                "subject_types",
                []
            )

            if (
                allowed_subject_types
                and subject_type not in allowed_subject_types
            ):
                errors.append(
                    f"{claim_id}: subject type "
                    f"{subject_type} is not allowed "
                    f"for {predicate}"
                )

            if has_object:
                object_id = claim.get("object")

                if object_id in entity_by_id:
                    object_type = entity_by_id[
                        object_id
                    ].get("type")

                    allowed_object_types = rule.get(
                        "object_types",
                        []
                    )

                    if (
                        allowed_object_types
                        and object_type
                        not in allowed_object_types
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
                    continue

                expected_value_type = rule.get(
                    "value_type"
                )

                actual_unit = value.get("unit")

                if (
                    expected_value_type
                    and actual_unit != expected_value_type
                ):
                    errors.append(
                        f"{claim_id}: value unit "
                        f"{actual_unit} does not match "
                        f"expected type "
                        f"{expected_value_type}"
                    )


def validate_evidence_integrity(
    evidence_records,
    evidence_ids,
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

        if source_id not in source_ids:
            errors.append(
                f"{evidence_id}: unknown source "
                f"{source_id}"
            )

        claim_to_evidence.setdefault(
            claim_id,
            []
        ).append(evidence_id)

    return claim_to_evidence


def validate_research(
    entity_ids,
    claim_ids,
    source_ids,
    errors
):
    research_root = ROOT.parent / "research"

    research_claims_path = (
        research_root
        / "mappings"
        / "private-capital-claims-v1.json"
    )

    research_sources_path = (
        research_root
        / "mappings"
        / "private-capital-sources-v1.json"
    )

    research_predicates_path = (
        research_root
        / "taxonomies"
        / "research-predicate-types-v1.json"
    )

    if research_claims_path.exists():
        try:
            research_claims_data = load_json(
                research_claims_path
            )
        except Exception as exc:
            errors.append(
                f"{research_claims_path}: invalid JSON: {exc}"
            )
            research_claims_data = {}

        research_predicates = set()

        if research_predicates_path.exists():
            try:
                predicate_data = load_json(
                    research_predicates_path
                )

                research_predicates = {
                    item["id"]
                    for item in predicate_data.get(
                        "predicate_types",
                        []
                    )
                    if "id" in item
                }
            except Exception as exc:
                errors.append(
                    f"{research_predicates_path}: "
                    f"invalid JSON: {exc}"
                )

        for claim in research_claims_data.get(
            "claims",
            []
        ):
            claim_id = claim.get("id")

            if not claim_id:
                errors.append(
                    "Research claim without id"
                )
                continue

            subject = claim.get("subject")
            object_id = claim.get("object")
            predicate = claim.get("predicate")

            if subject and not (
                subject in entity_ids
                or subject.startswith("candidate:")
            ):
                errors.append(
                    f"{claim_id}: unknown research subject "
                    f"{subject}"
                )

            if object_id and not (
                object_id in entity_ids
                or object_id.startswith("candidate:")
            ):
                errors.append(
                    f"{claim_id}: unknown research object "
                    f"{object_id}"
                )

            if (
                research_predicates
                and predicate not in research_predicates
            ):
                errors.append(
                    f"{claim_id}: unknown research "
                    f"predicate {predicate}"
                )

            canonical_claim_ref = claim.get(
                "canonicalClaimRef"
            )

            if canonical_claim_ref:
                if canonical_claim_ref not in claim_ids:
                    errors.append(
                        f"{claim_id}: unknown canonical "
                        f"claim {canonical_claim_ref}"
                    )

            if (
                claim.get("status") == "PROMOTED"
                and not canonical_claim_ref
            ):
                errors.append(
                    f"{claim_id}: PROMOTED research claim "
                    f"must have canonicalClaimRef"
                )

    if research_sources_path.exists():
        try:
            research_sources_data = load_json(
                research_sources_path
            )
        except Exception as exc:
            errors.append(
                f"{research_sources_path}: invalid JSON: {exc}"
            )
            research_sources_data = {}

        for item in research_sources_data.get(
            "sources",
            []
        ):
            atlas_source_id = item.get(
                "atlasSourceId"
            )

            decision = item.get("decision")

            if (
                decision == "EXISTING_SOURCE"
                and atlas_source_id
                and atlas_source_id not in source_ids
            ):
                errors.append(
                    f"{item.get('candidateId')}: "
                    f"unknown Atlas source "
                    f"{atlas_source_id}"
                )


def main():
    errors = []

    # ---------------------------------------------------------
    # Entity registry
    # ---------------------------------------------------------

    entity_by_id, entity_ids = collect_entities(errors)

    # ---------------------------------------------------------
    # Entity schema validation
    # ---------------------------------------------------------

    index_path = ROOT / "entities" / "index.json"

    try:
        index = load_json(index_path)

        for entity in index.get("entities", []):
            entity_id = entity.get(
                "id",
                "<missing-id>"
            )

            validate_json_schema(
                entity,
                SCHEMAS_DIR / "atlas-schema-v1.json",
                f"entities/index.json:{entity_id}",
                errors
            )
    except Exception:
        pass

    # ---------------------------------------------------------
    # Taxonomy
    # ---------------------------------------------------------

    relation_types, relation_rules = load_taxonomies(
        errors
    )

    # ---------------------------------------------------------
    # Sources
    # ---------------------------------------------------------

    source_ids, _ = collect_sources(errors)

    # ---------------------------------------------------------
    # Claims
    # ---------------------------------------------------------

    claim_ids, claims = collect_claims(errors)

    # ---------------------------------------------------------
    # Claim integrity
    # ---------------------------------------------------------

    validate_claim_integrity(
        claims,
        claim_ids,
        entity_by_id,
        entity_ids,
        relation_types,
        relation_rules,
        errors
    )

    # ---------------------------------------------------------
    # Evidence
    # ---------------------------------------------------------

    evidence_ids, evidence_records = (
        collect_evidence(errors)
    )

    validate_evidence_integrity(
        evidence_records,
        evidence_ids,
        claim_ids,
        source_ids,
        errors
    )

    # ---------------------------------------------------------
    # Research
    # ---------------------------------------------------------

    validate_research(
        entity_ids,
        claim_ids,
        source_ids,
        errors
    )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

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
