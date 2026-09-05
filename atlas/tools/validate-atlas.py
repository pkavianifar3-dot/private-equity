import json
import sys
from pathlib import Path

import jdatetime

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
    canonical_entity_ids = set()

    for path in sorted(
        ROOT.joinpath("entities").rglob("*.json")
    ):
        if path.name == "index.json":
            continue

        data = load_registry(path, errors)

        entity_id = data.get("id")

        if entity_id:
            canonical_entity_ids.add(entity_id)

    for entity_id in sorted(
        entity_ids - canonical_entity_ids
    ):
        errors.append(
            f"{entity_id}: present in entities/index.json "
            f"but missing from canonical entity file"
        )
    return entity_by_id, entity_ids


def collect_claims(errors):
    claim_ids = set()
    claims = []

    for path in sorted(
        (ROOT / "claims").glob("*.json")
    ):
        if path.name == "index.json":
            continue

        data = load_registry(path, errors)

        add_schema_errors(
            data,
            SCHEMAS_DIR / "claim-file-schema-v1.json",
            str(path.relative_to(ROOT)),
            errors
        )

        for claim in data.get("claims", []):
            claim_id = claim.get(
                "id",
                "<missing-id>"
            )

            if "id" not in claim:
                errors.append(
                    f"{path.relative_to(ROOT)}: "
                    f"claim without id"
                )
                continue

            if claim_id in claim_ids:
                errors.append(
                    f"Duplicate claim ID: {claim_id}"
                )

            claim_ids.add(claim_id)
            claims.append(claim)

    return claim_ids, claims

def collect_sources(errors, source_types):
    source_ids = set()
    sources = []

    for path in sorted(
        (ROOT / "sources").glob("*.json")
    ):
        if path.name == "index.json":
            continue
        data = load_registry(path, errors)

        add_schema_errors(
            data,
            SCHEMAS_DIR / "source-file-schema-v1.json",
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
            source_type = source.get("source_type")

            if source_type not in source_types:
                errors.append(
                    f"{source_id}: unknown source_type "
                    f"{source_type}"
                )
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
        if path.name == "index.json":
            continue
        data = load_registry(path, errors)

        add_schema_errors(
            data,
            SCHEMAS_DIR / "evidence-file-schema-v1.json",
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

    role_types_data = load_registry(
        ROOT / "taxonomies" / "role-types.json",
        errors
    )

    source_types_data = load_registry(
        ROOT / "taxonomies" / "source-types.json",
        errors
    )

    relation_types = {
        item["id"]
        for item in relation_types_data.get(
            "relation_types",
            []
        )
        if isinstance(item, dict)
        and "id" in item
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

    role_types = {
        item["id"]
        for item in role_types_data.get(
            "roles",
            []
        )
        if isinstance(item, dict)
        and "id" in item
    }

    source_types = {
        item["id"]
        for item in source_types_data.get(
            "source_types",
            []
        )
        if isinstance(item, dict)
        and "id" in item
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

    return (
        relation_types,
        relation_rules,
        role_types,
        source_types
    )


def validate_claim_integrity(
    claims,
    entity_by_id,
    entity_ids,
    relation_types,
    relation_rules,
    role_types,
    errors
):
    for claim in claims:
        claim_id = claim.get("id", "<missing-id>")
        subject_id = claim.get("subject")
        predicate = claim.get("predicate")
        role = claim.get("role")

        if role is not None and role not in role_types:
            errors.append(
                f"{claim_id}: unknown role {role}"
            )
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
                continue

            expected_value_type = rule.get("value_type")

            if expected_value_type:
                actual_value_type = value.get("unit")

                if actual_value_type != expected_value_type:
                    errors.append(
                        f"{claim_id}: value unit "
                        f"{actual_value_type} does not match "
                        f"expected value type "
                        f"{expected_value_type}"
                    )


def jalali_month_age(last_reviewed, today=None):
    try:
        year, month = (
            int(part)
            for part in last_reviewed.split("-")
        )
    except (AttributeError, TypeError, ValueError):
        return None

    if month < 1 or month > 12:
        return None

    if today is None:
        today = jdatetime.date.today()

    return (
        (today.year - year) * 12
        + (today.month - month)
    )


def validate_claim_review_metadata(claims, warnings, today=None):
    for claim in claims:
        claim_id = claim.get("id", "<missing-id>")
        last_reviewed = claim.get("last_reviewed")

        if last_reviewed is None:
            continue

        age = jalali_month_age(
            last_reviewed,
            today=today
        )

        if age is None:
            continue

        cycle = claim.get(
            "review_cycle_months",
            6
        )

        if age > cycle:
            warnings.append(
                f"{claim_id}: review is overdue "
                f"({age} months since last_reviewed; "
                f"cycle is {cycle} months)"
            )


def validate_claim_versioning(claims):
    errors = []

    claim_by_id = {
        claim.get("id"): claim
        for claim in claims
        if claim.get("id")
    }

    children_by_parent = {}

    for claim in claims:
        claim_id = claim.get("id", "<missing-id>")
        revision = claim.get("revision")

        if (
            isinstance(revision, bool)
            or not isinstance(revision, int)
            or revision < 1
        ):
            errors.append(
                f"{claim_id}: revision must be an integer >= 1"
            )
            continue

        parent_id = claim.get("supersedes")

        if parent_id is None:
            if revision != 1:
                errors.append(
                    f"{claim_id}: revision {revision} "
                    f"must supersede a previous claim"
                )
            continue

        if parent_id == claim_id:
            errors.append(
                f"{claim_id}: claim cannot supersede itself"
            )
            continue

        parent = claim_by_id.get(parent_id)

        if parent is None:
            errors.append(
                f"{claim_id}: supersedes unknown claim "
                f"{parent_id}"
            )
            continue

        parent_revision = parent.get("revision")

        if parent_revision != revision - 1:
            errors.append(
                f"{claim_id}: revision {revision} "
                f"must supersede revision {revision - 1}"
            )

        children_by_parent.setdefault(
            parent_id,
            []
        ).append(claim_id)

    for parent_id, children in children_by_parent.items():
        if len(children) > 1:
            errors.append(
                f"{parent_id}: multiple claims supersede "
                f"the same claim: {children}"
            )

    for claim_id in claim_by_id:
        visited = set()
        current_id = claim_id

        while current_id:
            if current_id in visited:
                errors.append(
                    f"{claim_id}: supersedes chain contains a cycle"
                )
                break

            visited.add(current_id)

            current = claim_by_id.get(current_id)

            if current is None:
                break

            current_id = current.get("supersedes")

    return errors


def collect_research_ids(errors):
    research_root = ROOT.parent / "research"
    content_root = research_root / "content"

    research_ids = set()

    if not content_root.exists():
        errors.append(
            "research/content: directory not found"
        )
        return research_ids

    for path in sorted(content_root.glob("*.json")):
        data = load_registry(path, errors)

        research_id = data.get("id")

        if not research_id:
            continue

        if research_id in research_ids:
            errors.append(
                f"Duplicate research ID: {research_id}"
            )

        research_ids.add(research_id)

    return research_ids


def validate_claim_analysis_integrity(
    claims,
    claim_ids,
    research_ids,
    errors
):
    based_on_graph = {}

    for claim in claims:
        claim_id = claim.get("id", "<missing-id>")
        claim_origin = claim.get("claim_origin")

        if claim_origin == "sourced":
            if "evidenceRefs" not in claim:
                errors.append(
                    f"{claim_id}: sourced claim must have evidenceRefs"
                )

        elif claim_origin == "internal_analysis":
            based_on = claim.get("based_on")
            authored_in = claim.get("authored_in")

            if not isinstance(based_on, list) or not based_on:
                errors.append(
                    f"{claim_id}: internal_analysis claim "
                    f"must have non-empty based_on"
                )
            else:
                seen = set()

                for ref in based_on:
                    if ref in seen:
                        errors.append(
                            f"{claim_id}: based_on contains duplicate "
                            f"claim {ref}"
                        )
                    seen.add(ref)

                    if ref == claim_id:
                        errors.append(
                            f"{claim_id}: based_on cannot reference "
                            f"itself"
                        )
                    elif ref not in claim_ids:
                        errors.append(
                            f"{claim_id}: unknown based_on claim "
                            f"{ref}"
                        )

                based_on_graph[claim_id] = [
                    ref for ref in based_on
                    if ref in claim_ids
                ]

            if not authored_in:
                errors.append(
                    f"{claim_id}: internal_analysis claim "
                    f"must have authored_in"
                )
            elif authored_in not in research_ids:
                errors.append(
                    f"{claim_id}: unknown authored_in research "
                    f"{authored_in}"
                )

    visited = set()
    active = set()

    def visit(claim_id):
        if claim_id in active:
            errors.append(
                f"{claim_id}: based_on chain contains a cycle"
            )
            return

        if claim_id in visited:
            return

        active.add(claim_id)

        for parent_id in based_on_graph.get(claim_id, []):
            visit(parent_id)

        active.remove(claim_id)
        visited.add(claim_id)

    for claim_id in based_on_graph:
        visit(claim_id)


def validate_evidence_integrity(
    evidence_records,
    claims,
    claim_ids,
    source_ids,
    errors
):
    claim_to_evidence = {}
    evidence_by_id = {}

    for evidence in evidence_records:
        evidence_id = evidence.get("id")
        claim_id = evidence.get("claim")
        source_id = evidence.get("source")

        if evidence_id:
            evidence_by_id[evidence_id] = evidence

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

        actual_refs = sorted(
            claim_to_evidence.get(
                claim_id,
                []
            )
        )

        declared_refs = sorted(
            claim.get(
                "evidenceRefs",
                []
            )
        )

        if not actual_refs:
            if claim.get("claim_origin") != "internal_analysis":
                errors.append(
                    f"{claim_id}: missing evidence"
                )
            elif declared_refs:
                errors.append(
                    f"{claim_id}: evidenceRefs do not match "
                    f"Evidence records"
                )
            continue

        unknown_refs = [
            ref
            for ref in declared_refs
            if ref not in evidence_by_id
        ]

        if unknown_refs:
            errors.append(
                f"{claim_id}: unknown evidenceRefs "
                f"{unknown_refs}"
            )

        if declared_refs != actual_refs:
            errors.append(
                f"{claim_id}: evidenceRefs do not match "
                f"Evidence records"
            )
def validate_research_integrity(
    entity_ids,
    claim_ids,
    source_ids,
    errors
):
    """
    Validate Research mappings against canonical Atlas data.

    Research may contain candidate claims, but once a research
    claim is marked PROMOTED it must point to a valid canonical
    Atlas claim.
    """

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

    if research_claims_path.exists():
        research_claims_data = load_registry(
            research_claims_path,
            errors
        )

        research_claims = research_claims_data.get(
            "claims",
            []
        )

        if not isinstance(research_claims, list):
            errors.append(
                "research/mappings/private-capital-claims-v1.json: "
                "'claims' must be an array"
            )
            research_claims = []

        for claim in research_claims:
            claim_id = claim.get(
                "id",
                "<missing-id>"
            )

            subject = claim.get("subject")
            object_id = claim.get("object")
            canonical_claim_ref = claim.get(
                "canonicalClaimRef"
            )
            status = claim.get("status")

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

            if canonical_claim_ref:
                if canonical_claim_ref not in claim_ids:
                    errors.append(
                        f"{claim_id}: unknown canonical claim "
                        f"{canonical_claim_ref}"
                    )

            if (
                status == "PROMOTED"
                and not canonical_claim_ref
            ):
                errors.append(
                    f"{claim_id}: PROMOTED research claim "
                    f"must have canonicalClaimRef"
                )

    if research_sources_path.exists():
        research_sources_data = load_registry(
            research_sources_path,
            errors
        )

        research_sources = research_sources_data.get(
            "sources",
            []
        )

        if not isinstance(research_sources, list):
            errors.append(
                "research/mappings/private-capital-sources-v1.json: "
                "'sources' must be an array"
            )
            research_sources = []

        for item in research_sources:
            candidate_id = item.get(
                "candidateId",
                "<missing-candidate-id>"
            )

            atlas_source_id = item.get(
                "atlasSourceId"
            )

            decision = item.get(
                "decision"
            )

            if (
                decision == "EXISTING_SOURCE"
                and atlas_source_id
                and atlas_source_id not in source_ids
            ):
                errors.append(
                    f"{candidate_id}: unknown Atlas source "
                    f"{atlas_source_id}"
                )

    research_content_root = research_root / "content"

    if research_content_root.exists():
        for path in sorted(
            research_content_root.glob("*.json")
        ):
            data = load_registry(
                path,
                errors
            )

            if not isinstance(data, dict):
                continue

            sections = data.get("sections", [])

            if not isinstance(sections, list):
                continue

            for section in sections:
                if not isinstance(section, dict):
                    continue

                section_id = section.get(
                    "id",
                    "<missing-section-id>"
                )

                claim_refs = section.get(
                    "claimRefs",
                    []
                )

                if isinstance(claim_refs, list):
                    for claim_ref in claim_refs:
                        if claim_ref not in claim_ids:
                            errors.append(
                                f"{path.relative_to(ROOT.parent)}:"
                                f"{section_id}: unknown canonical claim "
                                f"{claim_ref}"
                            )

                source_refs = section.get(
                    "sourceRefs",
                    []
                )

                if isinstance(source_refs, list):
                    for source_ref in source_refs:
                        if source_ref not in source_ids:
                            errors.append(
                                f"{path.relative_to(ROOT.parent)}:"
                                f"{section_id}: unknown canonical source "
                                f"{source_ref}"
                            )


def validate_research_documents(errors):
    research_root = ROOT.parent / "research"

    schema_path = (
        research_root
        / "schemas"
        / "research-schema-v2.json"
    )

    content_root = research_root / "content"

    if not schema_path.exists():
        errors.append(
            "research/schemas/research-schema-v2.json: "
            "schema file not found"
        )
        return

    if not content_root.exists():
        errors.append(
            "research/content: directory not found"
        )
        return

    for path in sorted(
        content_root.glob("*.json")
    ):
        data = load_registry(
            path,
            errors
        )

        add_schema_errors(
            data,
            schema_path,
            str(path.relative_to(ROOT.parent)),
            errors
        )
def main():
    errors = []
    warnings = []

    entity_by_id, entity_ids = collect_entities(errors)

    relation_types, relation_rules, role_types, source_types = load_taxonomies(
        errors
    )

    source_ids, _ = collect_sources(
        errors,
        source_types
    )

    claim_ids, claims = collect_claims(errors)

    research_ids = collect_research_ids(errors)

    validate_claim_integrity(
        claims,
        entity_by_id,
        entity_ids,
        relation_types,
        relation_rules,
        role_types,
        errors
    )

    errors.extend(validate_claim_versioning(claims))
    validate_claim_analysis_integrity(
        claims,
        claim_ids,
        research_ids,
        errors
    )
    validate_claim_review_metadata(
        claims,
        warnings
    )

    _, evidence_records = collect_evidence(errors)

    validate_evidence_integrity(
        evidence_records,
        claims,
        claim_ids,
        source_ids,
        errors
    )
    validate_research_integrity(
        entity_ids,
        claim_ids,
        source_ids,
        errors
    )
    validate_research_documents(errors)    
    if errors:
        print("Atlas validation FAILED")
        print()

        for error in errors:
            print(f"- {error}")

        print()
        print(f"Total errors: {len(errors)}")
        sys.exit(1)

    print("Atlas validation PASSED")

    if warnings:
        print()
        print("Warnings:")
        for warning in warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
