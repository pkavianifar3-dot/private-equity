# Public Atlas exploration presentation

The Entity static builder now composes the shared exploration layout used by
Research and isolated Atlas previews. The release public projection uses this
same builder over its existing closed, PUBLISHED-only graph. No IDs, schemas,
publication decisions, public routes or workflow permissions are changed.

- Actual Entity H2 sections supply stable TOC anchors.
- Atlas exploration precedes Research exploration; both reuse the existing
  four-visible/four-disclosed cards, directory links and mobile disclosures.
- Related Entities come from direct canonical relations with existing forward
  and reverse-display rules, published targets and supported routes.
- Research comes from the generated publication-filtered reverse index.
  Synthetic preview fixtures never enter the public rail.
- Public generation defaults to public filtering; preview inclusion is explicit.
- Legacy query shells load the same stylesheet when their existing renderer
  reuses the verified static Entity content.
- A repeated composition replaces the rail instead of duplicating it.

Regression tests cover the actual public package, every published Entity page,
all four supported builder types, legacy shells, TOC targets, missing routes,
REVIEW filtering, preview fixtures and the existing isolated preview contract.

This corrects the Stage 4.7 limitation: the Atlas presentation had remained
preview-only while Research presentation was already in public generation.
Publication and deployment remain subject to the existing Stage 5 gates.
