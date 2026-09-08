# ADR-002 — Predicate Contract

- Status: Proposed
- Scope: Architecture v1 — Relationship / Predicate Model

## Decision

Atlas predicates are defined by relation-types.json and constrained by relation-rules.json.

A predicate has an immutable id and bilingual labels. Its domain is defined by subject_types. Its target is defined by object_types or value_type.

The validator is the enforcement boundary. Renderer code must not define predicate semantics.

## Predicate Categories

- Entity relationships use object_types.
- Value predicates use value_type.
- Knowledge-object relations are kept separate from domain relationships.

A Claim remains the authoritative factual assertion. A predicate defines what kind of assertion is allowed; it does not itself constitute a fact.

## Semantic Safety

Do not infer inverse, symmetric, transitive, reflexive, or temporal semantics from a predicate name.

Similar predicates remain distinct until their semantic boundaries are explicitly established.

## Current Inventory

17 predicates are currently used by Claims. 14 predicates are defined but unused and remain reserved.

Unused predicates must not be populated speculatively.

## Known Gaps

- VICE_CHAIR_OF currently targets Organization while CHAIR_OF targets OrganizationUnit.
- Some role predicates may have overlapping semantics and require future review.
- Value predicates may require a richer value model in future.

## Non-Goals

This ADR does not migrate Claims, rename predicates, add inferred inverses, change URLs, or change renderer behavior.
