# Private Capital Atlas

This directory contains the core data contract for the Private Capital financial knowledge graph.

## Structure

- `schemas/` — machine-readable data schemas
- `taxonomies/` — controlled vocabularies
- `entities/` — Atlas entities
- `claims/` — atomic claims
- `sources/` — source records
- `evidence/` — evidence records

## Core principles

1. Entity identity is separate from relations.
2. Claims are separate from sources.
3. Evidence is separate from source records.
4. Claim status is separate from confidence.
5. Dates are structured, not free-text.
6. Unknown values remain null rather than guessed.
7. Corporate investment must not be attributed to an individual without evidence.
8. Canonical IDs are English, lowercase and stable.
9. Existing website presentation files must not be treated as the source of truth.

## ID convention

`<type>:<canonical-slug>`

Examples:

- `person:ali-sanginian`
- `organization:amin-investment-bank`
- `organization:kian-financial-group`
- `project:dadman`
