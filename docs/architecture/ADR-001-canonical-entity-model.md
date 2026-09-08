# ADR-001 — Canonical Entity Model

**Status:** Proposed
**Date:** 2026-09-07
**Scope:** Atlas canonical model, Identity, Entity lifecycle, and URL abstraction

---

## 1. Decision

Private Capital Atlas uses a canonical Entity model with a shared identity envelope and type-specific properties.

Canonical Entity types:

- Person
- Organization
- OrganizationUnit
- Fund
- Investment
- Project
- Sector
- Concept
- InvestorCategory

Canonical knowledge objects:

- Claim
- Evidence
- Source

`Role` is currently not treated as a canonical Entity. It remains reserved as controlled vocabulary / relation semantics until a concrete first-class use case requires otherwise.

---

## 2. Canonical Ownership

Each piece of knowledge has one canonical owner.

- Entity → Atlas
- Claim → Atlas
- Evidence → Atlas
- Source → Atlas
- Candidate Claim → Research / Review

Editorial Research content may describe or reference canonical Atlas data, but does not become a second owner of the same canonical Entity or Claim.

---

## 3. Entity Identity

Canonical Entity IDs use:

`<type>:<local-slug>`

Examples:

- `person:ali-sanginian`
- `organization:kian-financial-group`
- `concept:private-equity`
- `sector:private-equity`

Canonical IDs are immutable.

Display names and aliases may change without changing the canonical ID.

Local slugs are not globally unique across Entity types.

Therefore `concept:private-equity` and `sector:private-equity` are distinct canonical Entities.

---

## 4. Common Entity Contract

All canonical Entities share:

- `id`
- `type`
- `name`
- `aliases` (optional)
- `lifecycleStatus`

`name` contains required Persian and English display names.

`aliases` remain simple strings in Architecture v1.

`lifecycleStatus` is independent from Claim status and confidence.

Allowed lifecycle states:

- DRAFT
- REVIEW
- PUBLISHED
- ARCHIVED

---

## 5. Type-specific Properties

### Person

- `honorific` (optional)
- `domains` (optional; references Sector Entities)

### Organization

- `organization_type` (optional)
- `legal_name_status` (optional)
- `national_id` (optional)
- `registration_number` (optional)

### OrganizationUnit

No additional mandatory properties are introduced at this stage.

### Project

- `project_type` (optional)
- `investment_stage` (optional)

### Investment

- `investor`
- `target`
- `investment_status`
- `date_status`

Investment represents a specific investment / transaction instance.

### Fund

Reserved canonical Entity type. No speculative type-specific fields are introduced until real data/use cases require them.

### Sector

Common Entity contract only at this stage.

### Concept

Common Entity contract only at this stage.

### InvestorCategory

Reserved canonical Entity type. No speculative type-specific fields are introduced until real data/use cases require them.

---

## 6. Entity vs Claim

Entity fields represent identity and intrinsic structured properties.

Claims represent factual assertions and relationships that require provenance.

Examples:

`organization:kian-private-equity-management`

may contain organization identity properties.

But:

`person:ali-sanginian`
→ `CEO_OF`
→ `organization:kian-private-equity-management`

is represented as a Claim.

Relationship facts must not be duplicated as competing canonical truths inside Entity metadata.

---

## 7. Investment Boundary

Investment is a canonical Entity representing a specific investment / transaction instance.

The current `investor` and `target` fields are retained during Architecture v1 design for compatibility with the existing data and renderer.

Their final canonical/projection semantics will be determined during schema and migration design.

The authoritative factual assertions and provenance remain in the Claim layer.

`INVESTED_IN` remains an Entity-to-Entity relationship:

Organization / Person → Organization / Project

`INVESTMENT_AMOUNT` remains a value Claim whose subject is an Investment Entity.

---

## 8. Review Semantics

Review timestamps are context-specific:

- Entity review
- Editorial Content review
- Claim review

These timestamps must not be treated as interchangeable.

Claim review continues to use the existing Claim-level review metadata.

---

## 9. Metadata Policy

`metadata` remains available as a compatibility / extension area.

However, a field must become an explicit schema property when it has canonical semantic meaning or is expected to be:

- validated
- queried
- filtered
- indexed
- rendered as a formal property

Metadata must not become a permanent substitute for type-specific schema.

---

## 10. URL Policy

Canonical URLs are projections of canonical Entity identity.

The current public URL shape is not changed in this ADR.

Architecture v1 will first introduce one shared URL resolution policy used by Atlas and Research.

Existing public URLs must remain compatible while the new resolution layer is introduced.

A future URL-shape migration, if justified, must include an explicit redirect and backward-compatibility plan.

---

## 11. Renderer Policy

Entity routing must not be independently hard-coded in multiple renderers.

Atlas and Research must consume the same canonical Entity URL resolver.

Every canonical Entity type that is exposed through Atlas must eventually have:

- canonical URL
- index representation
- presentation route
- renderer support
- validation coverage

---

## 12. Non-goals

This ADR does not:

- redesign the homepage
- implement Watch
- introduce a database backend
- introduce a graph API
- perform a framework migration
- define speculative Fund / InvestorCategory schemas
- change public URLs