# Atlas Home Architecture

## 1. Purpose

The Atlas home is the discovery gateway to the Private Capital knowledge graph.

Atlas Home is not an exhaustive entity list. It provides:

- Search
- Directory / Explore
- Discovery

The canonical entity model remains unchanged.

Architecture flow:

Canonical Entities
→ Generated Catalog
→ Atlas UI

The Catalog is a generated projection and is not a new source of truth.

---

## 2. Entity Type Map

Canonical entity types currently present in the Atlas data model:

- Person
- Organization
- OrganizationUnit
- Project
- Investment
- Fund
- Sector
- Concept
- InvestorCategory

Current entity routes remain limited to the routes already supported by the project:

- `/atlas/person/{slug}/`
- `/atlas/organization/{slug}/`
- `/atlas/investment/{slug}/`
- `/atlas/concept/{slug}/`

Entity types without an existing renderer route must not receive fabricated URLs.

---

## 3. Browse Group Map

The Explore interface groups entities for discovery without changing their canonical ontology.

### Actors

- Person
- Organization
- OrganizationUnit

### Capital & Transactions

- Investment
- Fund

### Business & Projects

- Organization
- Project

### Concepts & Domains

- Concept
- Sector

These are presentation-level browse groups. They are not replacements for canonical entity types.

---

## 4. Route Contract

### Atlas Home

`/atlas/`

Purpose:

- discovery
- search entry point
- browse entry point
- selected concepts and domains
- links toward deeper Atlas exploration

Atlas Home must not become an exhaustive entity directory.

### Atlas Explore

`/atlas/explore/`

Purpose:

- search
- filtering
- browsing
- directory/list presentation
- pagination
- URL-preserved state

Examples:

- `/atlas/explore/?type=Organization`
- `/atlas/explore/?q=کیان`
- `/atlas/explore/?type=Concept&q=capital`

### Browse Group State

Explore may preserve a presentation-level browse group through the `group` query parameter.

Examples:

- `/atlas/explore/?group=actors`
- `/atlas/explore/?group=capital-transactions`
- `/atlas/explore/?group=business-projects`
- `/atlas/explore/?group=concepts-domains`

A browse group maps to one or more canonical entity types according to the Browse Group Map.

The `group` parameter does not replace or alter the meaning of `type`.

If both `group` and `type` are present, `type` is the narrower filter and applies within the selected group.

### Entity Pages

Existing entity URLs remain stable.

No existing entity route should be changed as part of the Atlas Home redesign.

---

## 5. Search Contract

Initial search fields:

- `name.fa`
- `name.en`
- normalized name values

The catalog may also contain:

- aliases
- domains

Future search metadata may be generated from canonical data, but the generated Catalog remains a projection.

Search must not require changes to canonical entity files for normal UI behavior.

---

## 6. Catalog Contract

Canonical source:

`atlas/entities/**/*.json`

Generated projection:

`atlas/catalog/index.json`

Generator:

`atlas/tools/build-catalog.py`

The catalog must be reproducible from canonical entities.

The Catalog must not become a manually maintained second source of truth.

Adding a valid canonical entity should allow the generated Catalog to discover it without manually editing an Atlas UI list.

---

## 7. Naming & Scaling Convention

Atlas data files must scale by canonical entity type and stable entity slug.

Canonical entity storage follows:

`atlas/entities/{type-group}/{slug}.json`

Examples:

- `atlas/entities/concepts/private-equity.json`
- `atlas/entities/organizations/kian-private-equity-management.json`
- `atlas/entities/persons/ali-sanginian.json`
- `atlas/entities/investments/kayson-achareh.json`

Rules:

1. Use lowercase kebab-case for file and slug names.
2. Use the canonical entity ID as the basis for the filename.
3. Do not create duplicate files for alternate display names.
4. Keep one canonical entity per canonical entity file.
5. Do not use UI labels as filesystem structure.
6. Generated indexes and catalogs must remain generated artifacts.
7. Do not manually maintain exhaustive UI lists as entity count grows.
8. New entity types must not require restructuring existing entity directories.
9. New presentation groupings belong in the UI/catalog layer, not in canonical storage.
10. Existing entity files and URLs should remain stable when the UI grows.
11. If a directory becomes large, scaling should use deterministic type-based partitioning rather than arbitrary manual folders.
12. Any future partitioning convention must preserve deterministic discovery by generators.

This convention is intended to keep file naming, directory structure, generators, and UI discovery predictable as the Atlas dataset grows.

---

## 8. Navigation Semantics

The Atlas navigation hierarchy is:

Atlas
→ Explore
→ Entity

Home provides discovery.

Explore provides directory/search.

Entity pages provide detailed knowledge.

Research and Watch remain separate surfaces and are not redesigned by this Atlas Home project.

---

## 9. Visibility

`lifecycleStatus` remains part of the generated Catalog.

The current Atlas redesign must not silently reinterpret the canonical lifecycle model.

Any future public/private visibility policy must be explicitly defined rather than inferred from UI behavior.

---

## 10. Empty and Error States

Explore must provide explicit states for:

- no search query results
- no matching filters
- catalog loading failure
- invalid or unsupported entity route

The UI must not generate links to unsupported entity routes.

---

## 11. Scope Boundaries

This Atlas Home project does not redesign:

- canonical entity schema
- claims
- evidence
- sources
- Research
- Watch
- authentication
- CMS
- public API
- GraphQL
- graph database
- vector search
- embeddings
- RAG
- AI layer

The objective is to improve Atlas discovery while preserving the existing architecture.

---

## 12. Scaling Principle

The system must scale through data-driven discovery rather than manual page/list maintenance.

Target flow:

Canonical Entity
→ Generator
→ Catalog
→ Search / Browse
→ Existing Entity Page

Adding an entity should not require editing the Atlas Home or Explore interface manually.
