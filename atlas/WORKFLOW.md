# Private Capital Atlas — Entity Onboarding Workflow v1

## 1. Purpose

This workflow defines the standard process for adding, reviewing and publishing entities in the Private Capital financial knowledge graph.

It applies to all supported entity types:

- Person
- Organization
- OrganizationUnit
- Project
- Investment
- Fund
- Role
- Sector
- InvestorCategory
- Source
- Claim

The workflow is evidence-first and designed to prevent unsupported facts, duplicate entities, incorrect attribution and loss of provenance.

---

## 2. Core Principle

The Atlas separates:

Entity
→ Relation
→ Claim
→ Evidence
→ Source
→ Presentation

The website page is a presentation layer and is not the source of truth.

---

## 3. Entity ID Rules

Format:

`<type>:<canonical-slug>`

Examples:

`person:ali-sanginian`

`organization:kian-financial-group`

`organization:kian-private-equity-management`

`project:dadman`

`investment:kayson-achareh`

`sector:private-equity`

Rules:

1. IDs are lowercase.
2. IDs use English ASCII characters.
3. IDs use stable canonical slugs.
4. IDs must not contain titles, dates or temporary roles.
5. Existing IDs must not be changed merely because a display name changes.
6. A possible duplicate entity must be resolved before creating a new ID.

---

## 4. Source Intake

Before creating claims:

1. Collect available primary, corporate, regulatory, registry, historical market and professional sources.
2. Preserve the exact source URL when available.
3. Record the source type.
4. Do not invent missing URLs.
5. Keep self-reported information distinguishable from independently verified information.
6. Record the source before relying on it for a claim.

Preferred evidence hierarchy:

1. Registry / regulatory / official corporate source
2. Direct primary source
3. Historical market data
4. Strong independent professional or media source
5. Professional biography
6. Self-reported information

This hierarchy guides review but does not automatically determine confidence.

---

## 5. Identity Resolution

Before creating an Entity, determine whether the Entity already exists.

Check:

- Canonical name
- English name
- Aliases
- Legal name
- National ID
- Registration number
- Ticker
- Organization type
- Related organizations
- Historical names

Rules:

- Never create a duplicate Entity merely because two sources use different names.
- Never merge two entities only because their names are similar.
- Unknown legal identity remains unresolved until supported by evidence.
- Use aliases for alternate names.
- Keep historical labels when they are useful for provenance.

---

## 6. Entity Registry

Every Entity must first exist in the Registry.

Minimum fields:

`id`

`type`

`name.fa`

`name.en`

`status`

Additional identity metadata should be added only when supported.

Initial status:

`REVIEW`

Publication status:

`PUBLISHED`

Other allowed statuses:

- DRAFT
- REVIEW
- PUBLISHED
- ARCHIVED

---

## 7. Relation Rules

Every relation must use a predicate from:

`atlas/taxonomies/relation-types.json`

and comply with:

`atlas/taxonomies/relation-rules.json`

A relation must not be invented merely for convenience.

Examples:

Person → CEO_OF → Organization

Person → BOARD_MEMBER_OF → Organization

Person → CHAIR_OF → OrganizationUnit

Organization → SUBSIDIARY_OF → Organization

Organization → INVESTED_IN → Organization / Project

Organization → OPERATES_IN → Sector

---

## 8. Claims

A Claim is an atomic statement.

A Claim should normally represent one fact:

Subject

Predicate

Object

Optional:

Role

Temporal

Context

Status

Confidence

Do not combine unrelated facts in one claim.

Bad:

Ali was CEO of Amin and later invested in X.

Good:

Ali → CEO_OF → Amin

Ali → INVESTMENT_EXECUTIVE_OF → Kayson

Separate facts require separate Claims.

---

## 9. Claim Status

Allowed values:

- VERIFIED
- SUPPORTED
- REPORTED
- DISPUTED

Definitions:

### VERIFIED

Strong direct or primary evidence supports the claim.

### SUPPORTED

Multiple credible sources support the claim but primary confirmation may not yet be available.

### REPORTED

The claim exists in a source but independent verification is insufficient.

### DISPUTED

Credible sources conflict and the conflict has not been resolved.

---

## 10. Confidence

Allowed values:

- HIGH
- MEDIUM
- LOW
- UNKNOWN

Confidence is separate from Source Type.

For example:

source_type = personal_website

confidence = MEDIUM

is valid.

Self-reported identifies provenance, not truth value.

---

## 11. Temporal Data

Dates must be structured.

Preferred fields:

start

end

precision

status

Precision may be:

- day
- month
- year
- approximate
- unknown

Do not invent dates.

Example:

{
  "start": "1390-12",
  "end": "1395-12",
  "precision": "month",
  "status": "known"
}

For an active role:

{
  "start": "1405",
  "end": null,
  "precision": "year",
  "status": "current"
}

---

## 12. Money and Quantitative Data

Financial amounts must preserve:

1. Normalized value
2. Currency
3. Unit
4. Original source wording

Example:

{
  "value": 720000000000,
  "currency": "IRR",
  "unit": "amount",
  "raw": "۷۲۰ میلیارد ریال"
}

Do not silently convert:

- rial → toman
- million → billion
- billion → trillion
- reported financing → investment
- company investment → individual investment

When terminology is ambiguous, preserve the original wording.

---

## 13. Investment Events

A corporate investment must be modeled separately from the role of an executive.

Example:

Kayson
→ INVESTED_IN
→ Achareh

Investment Event:

investor = Kayson

target = Achareh

amount = 720 billion IRR

Ali Sanginian
→ INVESTMENT_EXECUTIVE_OF
→ Kayson

Do not infer:

Ali Sanginian → INVESTED_IN → Achareh

unless direct evidence supports personal investment.

---

## 14. Evidence

Every important Claim should have Evidence.

Evidence must point to:

Claim

Source

Evidence Type

Strength

Evidence should be specific enough to explain why the claim was accepted.

Do not create artificial Evidence merely to satisfy the schema.

---

## 15. Source

Every Source must have:

id

type = Source

source_type

title_fa

Preferred additional fields:

publisher

url

citation_refs

Unknown values remain null.

---

## 16. Content Layer

Biography and editorial content belong in:

`atlas/content/`

Content is derived from structured data and reviewed sources.

Do not treat the Biography as the primary source of truth.

The same Entity may later appear as:

- Atlas Person page
- Organization page
- Timeline
- Network
- Article reference
- Related Entity

---

## 17. Entity Navigation

An Entity should only be linked to an Entity Page when the destination page exists.

Never create known broken links.

If a target Entity exists in the Registry but its page is not yet implemented:

- keep the Entity in the Graph
- do not expose a public broken link
- enable navigation when the renderer becomes available

---

## 18. Review Process

Standard lifecycle:

DISCOVERED
↓
IDENTITY_RESOLVED
↓
REGISTERED
↓
CLAIMED
↓
EVIDENCE_ATTACHED
↓
REVIEWED
↓
PUBLISHED

A claim can remain:

SUPPORTED, REPORTED or DISPUTED

inside a published Entity.

Publishing an Entity does not mean every claim is VERIFIED.

---

## 19. Minimum Publish Gate

An Entity is ready for publication when:

- Identity is sufficiently resolved.
- Entity ID is stable.
- Required Entity fields exist.
- Claims have valid subjects and objects.
- Predicates exist in the relation taxonomy.
- Subject/Object types comply with relation rules.
- Important Claims have Evidence.
- Evidence points to existing Sources.
- Dates are not fabricated.
- Financial amounts preserve units.
- Corporate investments are not wrongly attributed to individuals.
- Content has been reviewed.
- Internal links do not produce known 404 errors.

---

## 20. What Must Never Be Done

Never:

1. Invent a date.
2. Invent a legal identity.
3. Invent a national ID or registration number.
4. Turn self-reported information into independently verified fact.
5. Attribute a corporate investment to an executive without evidence.
6. Merge similar entities without identity resolution.
7. Create a citation that does not point to a real source.
8. Create fake evidence.
9. Replace uncertainty with confident wording.
10. Modify an existing Entity ID merely for presentation reasons.

---

## 21. Reference Entity

`person:ali-sanginian` is the first Reference Entity.

Future Entity onboarding should follow the same principles demonstrated by this Entity:

- structured identity
- structured roles
- temporal relations
- evidence-backed claims
- explicit uncertainty
- source provenance
- separate investment events
- reusable content
- publishable Atlas presentation

---

## 22. Versioning

Schema changes must be versioned.

Current version:

`Atlas v1`

Do not silently change the meaning of existing fields or predicates.

Breaking changes require a new schema version.

---

## 23. Review Philosophy

The Atlas prioritizes:

Accuracy over completeness.

Explicit uncertainty over unsupported certainty.

Reusable structure over page-specific markup.

Provenance over convenience.

A smaller verified graph is preferable to a larger graph containing unverified assertions.

---

## 24. Claim Versioning

Published canonical Claims are immutable.

If a published Claim must be corrected, updated or materially
revised:

1. Do not edit the existing canonical Claim in place.
2. Create a new Claim.
3. Increment the `revision`.
4. Set `supersedes` to the previous Claim ID.
5. Preserve the original Claim and its provenance.
6. Do not create `superseded_by` as a second stored source of truth;
   reverse lineage may be derived from `supersedes`.

Revision rules:

- Revision 1 has no `supersedes`.
- Revision N must supersede Revision N-1.
- A Claim must not supersede itself.
- A Claim lineage must not contain cycles.
- Only one successor may supersede a given Claim.

`transaction_time` should only be populated when the recording
time and recorder are actually known. Historical values must not
be invented.

---

## 25. Claim Review Metadata

Claim review metadata is optional operational metadata stored directly
on the canonical Claim.

Supported fields:

- `last_reviewed` — the month in which the Claim was last reviewed,
  using the Jalali `YYYY-MM` format.
- `review_cycle_months` — the intended review interval as a positive
  integer number of months.

Review-cycle rules:

1. `last_reviewed` may be omitted when no review date is known.
2. `review_cycle_months` may be omitted.
3. When `last_reviewed` exists but `review_cycle_months` is omitted,
   the default review cycle is 6 months.
4. A Claim is considered overdue only when the elapsed time is greater
   than the applicable review cycle.
5. An overdue Claim produces a validation warning; it does not fail
   Atlas validation.
6. Historical `last_reviewed` values must not be invented or backfilled.
7. Review metadata is operational metadata and does not replace
   provenance, evidence or source fields.
