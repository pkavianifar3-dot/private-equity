# Phase 1 baseline — privatecapital.ir

**Date:** 2026-09-29 (1405-07-07)
**Roadmap authority:** section 4.1, “گام ۱ — تثبیت خط مبنا”; later repeated numbering is implementation guidance.
**Repository:** `C:\Users\No1\architecture-v3`
**Commit:** `c202823` (`2026-09-25 17:58:01 +0330`)
**Branch:** `fix/atlas-entity-navigation`, tracking `origin/fix/atlas-entity-navigation`
**Remote:** `https://github.com/pkavianifar3-dot/private-equity.git`
**Starting worktree:** clean.

## Reproduce the baseline

From a clean checkout of the commit above, with `requirements.txt` installed, run:

```powershell
python atlas/tools/validate-atlas.py
python -m unittest discover -s tests -p 'test_*.py'
Get-ChildItem tests -Filter '*.test.js' | ForEach-Object { node $_.FullName; if ($LASTEXITCODE -ne 0) { throw $_.Name } }
python atlas/tools/build-index.py
python atlas/tools/build-catalog.py
node atlas/tools/build-research-pages.js
python atlas/tools/build-static-pages.py
git diff --exit-code -- atlas/entities/index.json atlas/claims/index.json atlas/evidence/index.json atlas/sources/index.json atlas/discovery/index.json atlas/catalog/index.json articles/private-capital.html atlas/person atlas/organization atlas/investment atlas/concept
```

The builders write tracked artifacts. Run them in a disposable clean checkout if local edits must remain untouched. This investigation replayed the four builders from a `git archive HEAD` snapshot and compared every generated tracked file with `HEAD` after normalizing CRLF/LF; no content drift was found. It did not run a remote GitHub Actions job. The CI workflow runs validation, Python tests, index/catalog generation and drift checks, Research page generation and drift check, selected JavaScript syntax checks and **three** JavaScript test files. It does not build or diff the static Atlas entity pages; it also does not deploy.

**Local environment/results:** Python 3.14.0; Node 24.14.0 (CI requests Python `3.x`, Node 20); validator PASS with `jsonschema.RefResolver` deprecation warning; 98 Python tests PASS; all 17 JavaScript test files PASS. Build output: 27 entities, 23 claims, 26 evidence records, 15 sources, discovery for 6 entities / 9 research mentions, 27 catalog entries, one Research page unchanged, 21 static Atlas pages. No generated content drift. A passing gate does not establish correctness of publication policy or user-visible routes.

## Contract and inventory reconciliation

Canonical input lives in `atlas/entities`, `claims`, `evidence`, `sources`, `schemas`, and `taxonomies`; `research/content` carries analysis and references. `atlas/tools/validate-atlas.py` checks schemas and cross-file references. `atlas/tools/build-index.py` builds the entity/claim/evidence/source and discovery indexes; `build-catalog.py` builds Atlas search entries; `build-research-pages.js` builds the Research article; `build-static-pages.py` builds entity pages. `assets/js/core/url-resolver.js`, the two Python route maps, and relation rendering govern navigation. The relevant Python and JavaScript tests are under `tests/`.

There are 27 entity source files (Concept 11, Organization 8, Sector 4, Person 1, Investment 1, Project 1, OrganizationUnit 1); 26 are `REVIEW` and one is `PUBLISHED`. There are 23 Claims (7 `VERIFIED`, 15 `SUPPORTED`, 1 `REPORTED`), all with `evidenceRefs`, 26 Evidence and 15 Sources. The current 16 used predicates exist in all three relation contracts (31 entries each). The validator already checks Claim supersedes chains/cycles, evidence/source links, and Research references; the roadmap's illustrative request to add those from scratch is outdated. No live Claim uses `supersedes`, so the passing data run does not exercise a real revision chain. The schema files inspected prohibit unknown root properties. `research/index.json` registers two published articles; one has structured `research/content` and a generated page, the other is a legacy HTML article.

The ten `sitemap.xml` URLs have matching local files or directory indexes, including `watch.html` and `services.html`. This is a repository check, not an HTTP check of the deployed site. Existing Atlas Explore searches a generated catalog. Research already has `entityRefs`, `claimRefs`, mentions and a discovery index. The sample `entity_refs` field and sample URL paths in the roadmap are not the current contract. A root `package.json` is not needed to invoke the current Research builder in CI.

## Prioritized follow-up backlog

| Priority | Risk / evidence | User effect and dependency | Regression check for a later phase |
| --- | --- | --- | --- |
| P0 — publication policy, phase 2/5 | `build-catalog.py` and `build-static-pages.py` include 20 routed `REVIEW` entities; their static pages are tracked. CI does not build or diff those pages. | Review content can appear in the public artifact if this repository is deployed as-is. First agree what `REVIEW` means for public Atlas, then implement a build/publish gate without changing canonical IDs. | A REVIEW fixture must be accepted/rejected from catalog and generated pages according to the agreed policy; CI must detect static page drift. |
| P1 — entity navigation, phase 3 | Catalog entries for one OrganizationUnit, one Project and four Sectors have no route; JS resolver, catalog builder and static builder cover only Person, Organization, Investment and Concept. | Search can show an entity without a click-through page; decide support versus explicit exclusion before routes/public URLs change. | For every supported type, resolve ID to route, generate page, and follow catalog link; unsupported types must be handled explicitly. |
| P1 — data gate, phase 2 | Existing validator enforces many references and revision rules; live data has no supersedes chain. Three relation files match for current predicates, but adding a predicate touches all three contracts. | Future edits could weaken a gate or leave a relation invisible despite a green current-data run. Preserve status/confidence and evidence requirements. | Negative fixtures for missing evidence/source/entity, malformed IDs, object/value XOR, status/confidence and revision cycle; assert taxonomy/renderer alignment. |
| P1 — Atlas/Research link, phase 4 | `entityRefs` and resolved mentions exist, but discovery indexes only the structured Research content and there is no general two-way article-by-entity index for both published articles. | Related reading is incomplete, especially for the legacy article. Define metadata/coverage policy before building a new index. | Missing entity and unpublished article references fail validation; generated links resolve in both directions. |
| P2 — publication and URL, phase 5 | Workflow validates and builds selected artifacts but contains no deployment step. All 10 sitemap targets exist locally; live HTTP responses were not tested. | Green validation alone does not show what was published or that live URLs work. Deployment and public URL changes require a separate decision. | Preview/rollback exercise, deployment gate, and live URL check after the deployment design is agreed. |
| P2 — search/Watch/backend, phases 6–8 | Atlas catalog search exists; `watch.html` exists, but the event model and freshness needs are not established. No backend requirement follows from the current static workflow. | Avoid promising search quality or freshness before measuring actual queries and update needs. | Persian query set and index size/latency; event provenance/freshness scenarios; ADR only if static limits are demonstrated. |

The old `docs/baseline/2026-09-07-baseline.md` captures another branch/commit and counts 24 Claims/14 Sources; preserve it as history. Roadmap sections after the principal eight steps suggest automatic deploy, Pagefind, package scripts and topic pages. Treat these as conditional notes, not authorized changes in phase 1. The roadmap's sitemap absence concern is resolved locally; its cross-reference and cycle-detection suggestions are already represented in the current validator. Its architectural separation of Atlas structured facts, Research analysis and generated artifacts remains applicable.

## Decisions before the next phase

1. Define whether `REVIEW` Atlas entities may be public and what the gate should exclude from catalog, pages, indexes and deployment.
2. Confirm the supported public Entity types and any URL migration/redirect contract before changing route maps.
3. Clarify whether the legacy published Research article should gain structured metadata for bidirectional linking, and who owns that editorial conversion.
4. Before phase 5, decide deployment ownership, preview/rollback and whether the current public URL set should change.
