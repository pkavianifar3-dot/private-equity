# ADR-003 — Research Citation Contract

- Status: Proposed
- Scope: Architecture v1 — Research Citation Model

## Decision

Citations are Research-specific knowledge objects. A Citation is not an Entity, Predicate, Claim, Source, or Evidence.

A Citation connects a Research document to a Source and may optionally identify supporting Evidence. Citation identity and display numbering are local to the Research document.

## Model Boundary

- Source identifies the underlying information source.
- Evidence identifies evidence supporting a Claim.
- Claim remains the authoritative factual assertion.
- Citation records how a Research document refers to a Source or Evidence.
- Display references such as [1] are generated within the Research document and are not Source identifiers.

## Reference Chain

The canonical provenance model remains:

Claim <- Evidence -> Source

Research -> Citation -> Source

When applicable:

Research -> Citation -> Evidence -> Claim

Citation does not replace the existing Claim / Evidence / Source provenance model.

## Source Identity

Citation references canonical Source IDs. Legacy local citation numbers such as "1" or "10" must not be treated as Source identity.

## Scope

Citation belongs to the Research model and is not added to the Atlas Entity taxonomy or predicate inventory.

## Non-Goals

This ADR does not migrate existing Research content, define renderer behavior, remove legacy citation_refs, or change Source, Evidence, or Claim schemas.

## Future Implementation

The Research schema will define Citation records with canonical Source references, optional Evidence references, and optional content-location metadata. Validation and rendering rules will be defined separately during implementation.
