# Content Provenance Contract v1

## Scope

Person and other Atlas content may reference canonical Source records directly.

## Canonical field

Use `paragraph.sourceRefs` with canonical Source IDs such as `source:kian-direct-interview-1405` for Atlas content. Research section-level `sourceRefs` is a separate contract and is not changed by this document.

## Legacy field

The legacy `paragraph.source_refs` field uses local numeric citation references and is migration-only.

## Migration rule

Legacy numeric references MUST be resolved through the existing source citation mapping. They MUST NOT be interpreted as Source IDs.

## Provenance boundary

Content-to-Source provenance is independent from Claim-to-Evidence-to-Source provenance. A content paragraph MUST NOT require creation of an artificial Claim merely to preserve its source reference.

## Safety

Migration MUST be deterministic, idempotent, reversible, and MUST NOT delete provenance.
