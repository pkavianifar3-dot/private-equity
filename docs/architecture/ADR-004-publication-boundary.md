# ADR-004 — Atlas publication boundary

**Status:** Accepted policy; public cutover deferred
**Date:** 2026-09-29
**Scope:** Decision gate from roadmap stage 2. No public behavior changes in this stage.

## Decision

`Entity.lifecycleStatus == "PUBLISHED"` is the eligibility rule for a public Atlas Entity representation. `DRAFT`, `REVIEW`, and `ARCHIVED` remain valid canonical records for validation, editorial work, and provenance, but are not eligible for *new* public Entity pages, catalog results, discovery entries, or public Entity references after the publication boundary is activated. A passing schema/validator result does not promote an Entity. Editorial review under `atlas/WORKFLOW.md` makes that decision.

This is an output and deployment rule, not a change to canonical identity, schema, or source of truth. The canonical `atlas/entities/**`, `claims/**`, `evidence/**`, and `sources/**` records, and the complete internal indexes used for validation, retain their current meaning. Any public projection must be generated from those records and checked for referential closure; it must not become an independently edited dataset. Claim `status` and `confidence` remain separate from Entity lifecycle. A published Entity may contain appropriately presented `SUPPORTED`, `REPORTED`, or `DISPUTED` Claims under the existing evidence and presentation rules.

During the transition, do not expand public exposure to additional `REVIEW` Entity types. Routing work in stage 3 may be verified in preview, but new public routes require the publication gate. Existing published artifacts stay unchanged until the coordinated cutover.

## Current state and affected paths

At the stage 2 baseline, 26 of 27 Entities are `REVIEW`; the public-facing catalog contains all 27, including 20 `REVIEW` entries with routes and tracked static pages. `atlas/discovery/index.json` has six Entity entries, all `REVIEW`. All six top-level `entityRefs` in the published structured Research article point to `REVIEW` Entities. The canonical entity index is also loaded by the Research renderer; Atlas pages load Entity and Claim indexes. Merely hiding catalog entries or deleting static pages would leave inconsistent public data or broken links.

The publication boundary therefore spans `atlas/tools/build-catalog.py`, `atlas/tools/build-static-pages.py`, the discovery output from `atlas/tools/build-index.py`, public delivery of the full Entity/Claim/Evidence/Source indexes, and generated or client-rendered links from Research and Atlas. The validation/build inputs remain complete internally. The public bundle must expose only a consistent projection whose links lead to published destinations; the exact packaging and deployment design belongs to roadmap stage 5.

## Cutover gate

1. Inventory every currently reachable `REVIEW` URL and reference. Review each Entity against the existing minimum publish gate; promote only with an editorial decision and adequate provenance. Do not change `lifecycleStatus` in bulk merely to preserve routes.
2. For entries that cannot be published, record an explicit URL disposition. Preserve an existing address with appropriate approved content or redirect it to a genuinely relevant published destination; if neither is defensible, document depublication and the resulting link impact. Do not silently redirect all pages to Atlas home.
3. Reconcile the published Research article's six Entity references and the discovery index before filtering public pages. Its analytical text must not be reclassified as canonical data. No public link may point to an unpublished or absent Entity.
4. Generate public projections from canonical inputs, test both accepted/rejected lifecycle fixtures and all cross-product links, and check build drift and URL compatibility in CI/preview. Activate the boundary only as one reviewed release with rollback. Keep the existing public outputs until this gate passes.

No route, URL, public artifact, deployment step, dependency, or canonical status is changed by this ADR. Stage 2 validation hardening is complete independently of the later publication cutover.
