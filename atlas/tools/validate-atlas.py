import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main():
    errors = []

    # ---------------------------------------------------------
    # Load canonical entity registry
    # ---------------------------------------------------------

    index = load_json(ROOT / "entities" / "index.json")

    entities = index.get("entities", [])

    entity_by_id = {
        entity["id"]: entity
        for entity in entities
        if "id" in entity
    }

    entity_ids = set(entity_by_id.keys())

    # ---------------------------------------------------------
    # Load relation taxonomy
    # ---------------------------------------------------------

    relation_types_data = load_json(
        ROOT / "taxonomies" / "relation-types.json"
    )

    relation_types = {
        item["id"]
        for item in relation_types_data.get("relation_types", [])
        if "id" in item
    }

    relation_rules_data = load_json(
        ROOT / "taxonomies" / "relation-rules.json"
    )

    relation_rules = {
        rule["relation"]: rule
        for rule in relation_rules_data.get("rules", [])
        if "relation" in rule
    }

    # ---------------------------------------------------------
    # Validate taxonomy consistency
    # ---------------------------------------------------------

    for relation in relation_rules:
        if relation not in relation_types:
            errors.append(
                f"Relation rule references unknown predicate: {relation}"
            )

    # ---------------------------------------------------------
    # Collect sources
    # ---------------------------------------------------------

    source_ids = set()

    sources_dir = ROOT / "sources"

    for path in sources_dir.glob("*.json"):
        data = load_json(path)

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

    # ---------------------------------------------------------
    # Collect and validate claims
    # ---------------------------------------------------------

    claim_ids = set()
    claims = []

    claims_dir = ROOT / "claims"

    for path in claims_dir.glob("*.json"):
        data = load_json(path)

        for claim in data.get("claims", []):
            claims.append(claim)

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

            subject_id = claim.get("subject")
            predicate = claim.get("predicate")

            # -------------------------------------------------
            # Subject validation
            # -------------------------------------------------

            if not subject_id:
                errors.append(
                    f"{claim_id}: missing subject"
                )

            elif subject_id not in entity_ids:
                errors.append(
                    f"{claim_id}: unknown subject entity {subject_id}"
                )

            # -------------------------------------------------
            # Predicate validation
            # -------------------------------------------------

            if not predicate:
                errors.append(
                    f"{claim_id}: missing predicate"
                )

            elif predicate not in relation_types:
                errors.append(
                    f"{claim_id}: unknown predicate {predicate}"
                )

            # -------------------------------------------------
            # object/value exclusivity
            # -------------------------------------------------

            has_object = "object" in claim
            has_value = "value" in claim

            if has_object == has_value:
                errors.append(
                    f"{claim_id}: exactly one of object/value is required"
                )

            # -------------------------------------------------
            # Object validation
            # -------------------------------------------------

            if has_object:
                object_id = claim.get("object")

                if not isinstance(object_id, str):
                    errors.append(
                        f"{claim_id}: object must be a string entity ID"
                    )

                elif object_id not in entity_ids:
                    errors.append(
                        f"{claim_id}: unknown object entity {object_id}"
                    )

            # -------------------------------------------------
            # Rule validation
            # -------------------------------------------------

            rule = relation_rules.get(predicate)

            if rule and subject_id in entity_ids:
                subject_type = entity_by_id[subject_id].get("type")

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
                        f"{subject_type} is not allowed for "
                        f"{predicate}"
                    )

                # ---------------------------------------------
                # Object type validation for relation claims
                # ---------------------------------------------

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

                # ---------------------------------------------
                # Value type validation for quantitative claims
                # ---------------------------------------------

                if has_value:
                    expected_value_type = rule.get("value_type")

                    value = claim.get("value")

                    if not isinstance(value, dict):
                        errors.append(
                            f"{claim_id}: value must be an object"
                        )
                    else:
                        actual_unit = value.get("unit")

                        if (
                            expected_value_type
                            and actual_unit
                            != expected_value_type
                        ):
                            errors.append(
                                f"{claim_id}: value unit "
                                f"{actual_unit} does not match "
                                f"expected type "
                                f"{expected_value_type}"
                            )

    # ---------------------------------------------------------
    # Validate evidence references
    # ---------------------------------------------------------

    evidence_dir = ROOT / "evidence"

    for path in evidence_dir.glob("*.json"):
        data = load_json(path)

        for evidence in data.get("evidence", []):
            evidence_id = evidence.get("id")
            claim_id = evidence.get("claim")
            source_id = evidence.get("source")

            if not evidence_id:
                errors.append(
                    f"{path}: evidence without id"
                )

            if claim_id not in claim_ids:
                errors.append(
                    f"{evidence_id}: unknown claim {claim_id}"
                )

            if source_id not in source_ids:
                errors.append(
                    f"{evidence_id}: unknown source {source_id}"
                )
    # ---------------------------------------------------------
    # Validate Research mappings
    # ---------------------------------------------------------

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
        research_claims_data = load_json(
            research_claims_path
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
            predicate = claim.get("predicate")
            object_id = claim.get("object")

            # ---------------------------------------------
            # Research subject/object references
            # ---------------------------------------------

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

            # ---------------------------------------------
            # Research predicate validation
            # ---------------------------------------------

            if research_predicates_path.exists():
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

                if predicate not in research_predicates:
                    errors.append(
                        f"{claim_id}: unknown research "
                        f"predicate {predicate}"
                    )
            # ---------------------------------------------
            # Canonical Atlas claim reference validation
            # ---------------------------------------------

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
    # ---------------------------------------------------------
    # Validate Research source mappings
    # ---------------------------------------------------------

    if research_sources_path.exists():
        research_sources_data = load_json(
            research_sources_path
        )

        for item in research_sources_data.get(
            "sources",
            []
        ):
            atlas_source_id = item.get("atlasSourceId")
            decision = item.get("decision")

            if (
                decision == "EXISTING_SOURCE"
                and atlas_source_id
                and atlas_source_id not in source_ids
            ):
                errors.append(
                    f"{item.get('candidateId')}: unknown "
                    f"Atlas source {atlas_source_id}"
                )
    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    if errors:
        print("Atlas validation FAILED")
        print()

        for error in errors:
            print(f"- {error}")

        sys.exit(1)

    print("Atlas validation PASSED")


if __name__ == "__main__":
    main()
