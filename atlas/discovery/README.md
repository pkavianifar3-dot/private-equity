# Discovery Index

The Discovery Index is a generated Atlas artifact for reverse discovery.

Its purpose is to expose references from canonical Atlas Entities to
Research Mentions that refer to those Entities.

## Responsibilities

The Discovery Index answers:

> Where is this canonical Entity referenced by a resolved Research Mention?

It does not define new entities, claims, evidence, sources, relations,
or research documents.

## Source of Truth

The Discovery Index is generated from canonical data.

It is not a source of truth and must not contain duplicated canonical
Entity, Claim, Evidence, Source, or Research content.

## Data Direction

Canonical Research Mention:

Research
→ Section
→ Mention
→ Entity

Reverse discovery:

Entity
→ Discovery Index
→ Research Mention

## Entry Contract

Each Entity entry may contain:

- `researchId`
- `sectionId`
- `contentBlockId`
- `mentionId`

The references must resolve to existing canonical records.

## URL Policy

The Discovery Index does not store Entity URLs.

Canonical Entity URLs must continue to be resolved through the existing
canonical Entity URL mechanism.

## Generation

`atlas/discovery/index.json` is generated and must be reproducible.

It must not be manually maintained as an independent source of truth.

## Integrity

Every generated Research Mention reference must satisfy:

1. The referenced Research document exists in the Research registry.
2. The referenced Research content exists.
3. The referenced Section exists in that Research document.
4. The referenced Content Block exists in that Section.
5. The referenced Mention exists in that Section.
6. The Mention has `resolutionStatus` equal to `RESOLVED`.
7. The Mention's `entityRef` resolves to a canonical Atlas Entity.
8. The `entityRef` of the Mention matches the Entity under which the
   discovery entry is indexed.

## Scope

This phase provides discovery and backlink data only.

It does not implement a general search engine, graph database,
recommendation system, graph UI, or new knowledge model.