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

## Predicate Boundaries

- CEO_OF asserts a CEO relationship.
- EXECUTIVE_ROLE_AT asserts a general executive role and may carry a role value.
- INVESTMENT_EXECUTIVE_OF asserts a specialized investment-executive relationship.
- These predicates are not interchangeable, and one must not be inferred from another without explicit evidence.


## Reserved Predicate Review

The current taxonomy contains 14 predicates with no live Claims. They remain reserved and must not be populated speculatively.

Two predicates require explicit architectural review before activation:

- `VICE_CHAIR_OF`: the current rule targets `Organization`, while `CHAIR_OF` targets `OrganizationUnit`. This mismatch is intentionally unresolved until the canonical organization/organization-unit boundary is settled.
- `SUPPORTED_BY`: this is a knowledge-object relation from `Claim` to `Source` or `Evidence`, not a domain-entity relationship. It remains reserved pending the Claim/Evidence/Source relationship model.

The remaining unused predicates are reserved without changing their current rules or creating inferred Claims.


## Claim / Evidence / Source Boundary

The current provenance model is `Claim <- Evidence -> Source`. Evidence is a first-class knowledge object that references exactly one Claim and one Source in the current schema. Claim status such as `SUPPORTED` is epistemic status and is distinct from the `SUPPORTED_BY` predicate. Therefore `SUPPORTED_BY` remains a reserved knowledge-object predicate and is not used as an alternative provenance path unless the provenance model is explicitly redesigned.
