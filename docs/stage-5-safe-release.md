# Stage 5 — safe release and URL alignment

**Date:** 2026-10-10. **Roadmap:** principal section 4.5, step 5 (not the later Similarity step).
**Baseline:** `f82938a15c8ae3090277992d230511623f4da728` on `feat/research-content-ingestion-foundation`.
**Status:** local implementation and verification; public release blocked pending the approved migration decisions below. No commit, push, merge, deployment or remote settings change in this step.

## Approved interpretation of the REVIEW conflict

The user explicitly approved: preserve current URLs/runtime in a **local compatibility candidate**, while blocking public upload/deploy until the REVIEW migration is separately approved. This resolves the conflicting requirements of keeping existing REVIEW addresses and excluding REVIEW from publicly accessible release artifacts. A local allowlist entry does not grant publication permission.

ADR-004 stays unchanged. No lifecycle promotion, filtering cutover, URL deletion, redirect, Entity noindex, Project/OrganizationUnit/Sector public route, or Atlas exploration rail activation occurs here. The previously approved Research publication remains intact.

## Release architecture

`tools/release.py verify` is the entry point shared by local work and CI:

1. Validate canonical Atlas and Research.
2. Run every Python test and every `tests/*.test.js`; check every browser JavaScript file's syntax.
3. Build index, catalog, Research, Research connections, static Atlas, and sitemap.
4. Compare pre/post generated snapshots, including additions/deletions. In CI also enforce clean Git diffs, no untracked generated files, and a clean source tree.
5. Verify the deterministic URL disposition matrix.
6. Build an isolated candidate from `tools/release/site-policy.json`, the published Research registry, approved route types, existing REVIEW inventory, runtime index closure and declared assets.
7. Check actual candidate bytes, link/anchor closure, CSS/manifest assets, indexed JSON dependencies, canonical/sitemap/robots alignment and preview/editorial exclusion.
8. HTTP-test every candidate file, the custom 404, and the absence of directory listings through the same loopback inspection handler.
9. Write a hash manifest **next to**, not inside, the candidate: file hashes, aggregate hash, baseline commit, dirty-worktree flag/diff hash, runtime versions, run ID and publication blockers.
10. A separate publication gate rejects any non-PUBLISHED Entity and any unapproved Entity type in the delivered entity/catalog indexes. Only a main run with explicit activation and correct Pages source can upload; deploy uses that exact run's artifact, named after that commit.

The local manifest names the baseline commit and records a dirty worktree. It must not be represented as proof that the Stage 5 edits already exist in that commit. CI checks the committed event SHA and a clean checkout. The candidate hash covers normalized LF text and exact binary bytes, making artifact bytes independent of Windows Git line endings.

## Public artifact boundary

The current local candidate has **124 files / 40 HTML pages**. It includes:

- Explicit existing site pages and a minimal custom `404.html` with navigation back to Home, Research and Atlas.
- The three PUBLISHED Research pages from `research/index.json`.
- The four existing legacy Entity template entry points and 21 static Entity pages, preserving their current URLs.
- Assets actually declared by HTML/CSS/webmanifest: scripts, styles, fonts, images and icons.
- Catalog and full entity metadata; the supported types' Entity JSON, Person narrative JSON, Claim/Evidence/Source files obtained through their generated indexes, and three relation contracts required by legacy runtime rendering.
- `CNAME`, `robots.txt` and generated `sitemap.xml`.

It excludes repository metadata, workflows, tools, tests, docs, schemas, unused discovery indexes, Research source packages/mappings, editorial-review files and preview components. JSON copied for runtime is still canonical-derived existing data; it is not another edited source of truth. Unsupported Entity types do not acquire new individual public routes through packaging. The old OrganizationUnit prefix is not mapped into Organization routing.

The complete existing runtime entity/catalog indexes still contain **26 REVIEW Entities**, including **20 with static URLs**. The strict publication command therefore fails. Future public delivery needs an approved closed projection of canonical data, not just deletion of JSON files. New non-public Entities cannot silently enlarge the local legacy exposure inventory.

## Workflow and action compatibility

The existing `Validate Atlas` workflow is extended rather than paired with a racing deploy workflow. It checks out `${{ github.sha }}`, never a moving `main` branch. PRs/feature branches run verification but upload no site candidate. Main upload additionally requires `PAGES_RELEASE_ENABLED=true`, the publication gate, Pages `build_type=workflow`, and a matching current main SHA. The deploy job has `needs: validate-atlas`, no checkout/build, minimum `pages:write` / `id-token:write`, the `github-pages` environment and serial concurrency.

Main validation and deployment share branch-level concurrency without cancelling a deployment mid-flight. Deployments additionally share `github-pages` concurrency. Required review/allowed-branch protection of the environment is a remote configuration decision and has not been changed here.

Official release API, pinned `action.yml` and deploy-pages README were inspected on 2026-10-10:

| Action | Version | Runtime / immutable commit |
| --- | --- | --- |
| checkout | 7.0.1 | Node 24 / `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| setup-python | 7.0.0 | Node 24 / `5fda3b95a4ea91299a34e894583c3862153e4b97` |
| setup-node | 7.1.0 | Node 24 / `949feb2413d6458794dcd2491c4babbbce0c15c1` |
| upload-pages-artifact | 5.0.0 | composite, pinned upload-artifact dependency / `fc324d3547104276b827a68afc52ff2a11cc49c9` |
| deploy-pages | 5.0.1 | Node 24 / `368f82528645a54fb793d4d04e342629a3f51346` |

`ubuntu-24.04` replaces the moving `ubuntu-latest` label. Python 3.14.0 and Node 24.21.0 match the local verification environment; existing Python dependencies and their closure are constrained in `requirements-release.txt`. The seven constrained packages resolved/downloaded successfully as CPython 3.14-compatible Linux/manylinux wheels, including the native rpds-py dependency. No new project dependency or service is introduced. The workflow was linted using the official, checksum-verified actionlint 1.7.12 executable. Shellcheck/pyflakes were not installed or run. The new hosted Ubuntu workflow has **not** executed remotely; that requires a later authorized commit/push. Its result must be reviewed before a production activation.

## Actual GitHub Pages and domain state

Read-only GitHub settings inspection confirmed on 2026-10-10:

- Repository visibility: **public**. `gh` is not installed locally. Public API could read metadata/history; the unauthenticated Pages API returned 404. Authenticated Chrome settings supplied the actual Pages configuration.
- Pages source: **Deploy from a branch — main / root**, not GitHub Actions.
- Last observed production deployment: 2026-09-30, commit `f1290095abafacb01a3b0d59010d29b1c14a840d`, environment `github-pages`, workflow `pages build and deployment`.
- Custom domain matches the unchanged CNAME: `privatecapital.ir`.
- Settings displayed DNS check in progress, certificate request error, and unavailable Enforce HTTPS.
- HTTPS client requests succeeded through Cloudflare. This computer's Avast TLS scanner presented its own certificate; the origin certificate/Cloudflare-to-GitHub TLS state is therefore **unverified**. Successful client HTTPS does not resolve the GitHub certificate warning.

**The current branch-based Pages publisher bypasses the new repository gates. Do not merge this work into main under that publisher.** The separately approved activation must move Pages source to GitHub Actions before main integration, configure the environment/branch protections, resolve public projection decisions, and only then enable the production variable. Changing the Pages source is a remote deployment change, so this step deliberately leaves it untouched.

## Sitemap and canonical decisions

The sitemap now has **14 deterministic URLs**. Published Research is derived from registry; future articles do not require manual sitemap editing. Only PUBLISHED Atlas entries with approved, existing routes enter it. Existing REVIEW pages retain their current canonical/indexability but are not newly added to sitemap.

Nine existing main/index pages receive self-canonical tags. Resources keeps its existing canonical alias to `/atlas/` and stays out of sitemap. Copyright and Atlas Explore are self-canonical and included. Legacy query shells get their Entity canonical through the existing Atlas runtime and are not separately listed.

Unsubstantiated historic root-page lastmod values are removed. The old structured article uses its existing publication metadata; the legacy article uses its embedded Article JSON-LD date. No lastmod is invented for the new article or other undated pages. Build date is never used. Unnecessary hand-tuned changefreq/priority entries are not recreated.

The webmanifest referenced two absent root icon URLs. Those references now point to the existing `/assets/images/...` files; no new asset endpoint or duplicate image was created.

## URL inventory and migration

`docs/stage-5-url-disposition.md` contains the full local matrix: 40 pages, their 24 explicit index.html aliases, and 21 legacy query entry points; Entity status, canonical, inbound HTML/catalog-runtime links, sitemap/indexability, proposal, risk and test. It records the 20 REVIEW static addresses and the old Research inline references. Proposed migration actions are **not executed**.

For each REVIEW record, editorial approval must decide whether to KEEP and publish adequately sourced content, redirect to a genuinely relevant approved destination, deindex, or remove with 404. NOINDEX alone is not ADR-004 publication approval. Shared runtime/catalog/research links and JSON projection must migrate together. No blanket redirect to Atlas home is proposed.

## Preview using the same artifact

PowerShell from the repository, choosing a fresh output directory each time:

```powershell
python -m pip install -r requirements.txt -c requirements-release.txt
$candidatePath = Join-Path $env:TEMP ('privatecapital-candidate-' + [guid]::NewGuid())
python tools/release.py verify --output $candidatePath
if ($LASTEXITCODE -ne 0) { throw 'Release verification failed' }
python tools/preview-release.py --artifact $candidatePath --port 8780
```

The server binds only `127.0.0.1`, adds noindex headers, prevents directory listings, serves a real 404, and suppresses production canonical/SEO URLs in HTML responses. A small observer removes canonical tags injected by the unchanged legacy runtime. Candidate files remain byte-for-byte unchanged. This is an inspection transport over the already verified output, not another build pipeline or a public preview deployment.

```powershell
python tools/release.py check --output $candidatePath
python tools/release.py smoke --output $candidatePath
python tools/release.py publication --output $candidatePath  # expected exit 1 while REVIEW remains
python tools/release.py sitemap --check
python tools/release.py inventory --output docs/stage-5-url-disposition.md
```

Current preview is on port 8780. Both structured articles, the legacy article, Atlas home/static Person, Watch, Services, Contact and all sitemap URLs are reachable there. Chrome also exercised Person, Organization, Concept and Investment legacy query pages with no console errors. The new Research article's assets loaded and reciprocal exploration link remained present; the static Atlas page still has no preview exploration rail.

## Rollback procedure

No rollback or deployment is performed here. After an approved cutover, use a **known-good release that passed the same strict publication gate**, recording its commit, run ID, artifact hash and public URL dispositions. A pre-cutover artifact containing REVIEW is not automatically a safe rollback target.

1. If a production release is faulty, disable further authorized activation and record the faulty and last good deployment identities. Do not modify canonical records to force a green gate.
2. Prepare `git revert <faulty-commit>` on the approved integration branch, or `git revert -m 1 <faulty-merge>` when the release is a merge. Review the actual inverse diff; do not reset/rebase/force-push history. This requires separate authorization and is not a command to run in this Stage 5 worktree.
3. Reconcile release gates/workflow compatibility if older content predates them. Rebuild from the reverted state with current approved gates, inspect the resulting candidate and compare URL/canonical/publication behavior to the known-good release.
4. Run all checks. If the gate rejects unpublished data, stop; never bypass it or restore a whole-repository artifact.
5. With explicit approval, integrate the revert into main and deploy its verified artifact through the same pipeline. Verify live Home, Research, Atlas, Watch, Services, Contact, sitemap, assets, 404 and domain/TLS after deployment.

Local rehearsal verified identical artifact bytes from two builds, preserved bytes during preview, and rejection of tampered/missing/extra files. An actual Git revert/deployment rehearsal is not performed because it is outside the authorized operations of this step. Short artifact retention is not the rollback mechanism; reconstruction from Git plus the approved pipeline is.

## Verification and limits

- Validator PASS; 174 Python tests (22 new release regressions) and all 20 JavaScript test files PASS.
- Five existing builders and deterministic sitemap PASS; generated output unchanged by repeat verification.
- 124 allowlisted files, 40 HTML pages, 14 sitemap URLs; 1041 link/runtime checks and 150 local HTTP checks PASS (including 24 filename aliases).
- Publication eligibility deliberately FAILS (64 diagnostic entries across entity/catalog indexes); no upload, no public candidate, no deployment.
- `git diff --check` PASS. Canonical source data, Research content, public Atlas static pages, relation contracts, discovery/catalog bytes and public URL resolver remain unchanged.
- Limited credential-format/filename scan: no matching credential found in 27 tracked Research/docs/workflow text files. This is **not** a full history or confidentiality audit. Editorial-review and Research mapping/source files remain visible in the **public GitHub repository**, even though the candidate excludes them. Owners must confirm whether any such content requires a separate confidentiality response; no visibility/history change occurs here.
- Live Home, article index, old structured/legacy articles, Atlas, Person, Watch, Services, Contact, robots and sitemap returned 200; an unknown route returned 404. The new feature-branch article returned 404 on production, as expected before main integration/deployment.
- Intermediate local HTTP runs intermittently timed out receiving large script/image responses or reset a connection; an isolated script transfer using bounded reads returned all 107217 bytes in 0.045 seconds. The precise environmental cause is unproven. The handler materializes exact bytes before headers and uses the standard library's buffered transfer; the client uses bounded receive buffers and validates Content-Length as well as artifact bytes. Loopback proxy bypass is explicit. Idempotent smoke GETs allow one recorded retry for socket timeout/reset/abort only (15-second deadline per attempt); status/content/framing/byte mismatches never retry, and exhausted transport failures reject the release. The manifest records retries. A real HTTP fixture covers proxy bypass; deterministic transport fixtures cover successful retry and exhausted retry. The subsequent complete verification passed, with one recorded timeout/retry for `/assets/images/privatecapital.png`; the retried response passed framing and byte equality checks.
- Final verified artifact SHA-256: `1f7b9525bfa5020d341e7d040a41d3962720c8dd1e7a887cb3de03d79d77f8bb`, identical to the earlier independent candidate. The sidecar accurately records the baseline commit and dirty working tree; Stage 5 edits have not been committed.
- Production settings migration, hosted execution of the new workflow, public projection and origin TLS resolution remain approval/operational gates. This implementation does not claim production is already protected by the new workflow.

## Decisions before production activation

1. Approve per-Entity disposition/promotion and the closed public data projection; do not bulk-promote REVIEW merely to preserve URLs.
2. Approve switching Pages from branch publishing to Actions **before main integration**, and define `github-pages` allowed branch/review protection. Enable `PAGES_RELEASE_ENABLED` only after strict gates can pass.
3. Resolve/verify DNS and GitHub origin certificate state with the existing domain owner; do not change domain or weaken HTTPS protections.
4. Confirm whether existing public GitHub editorial/source material contains information that requires a separate access/history response.

Atlas rail activation and Similarity remain separate scope decisions. The implementation is ready for local review; public activation remains blocked as explicitly agreed.

Suggested commit: `feat(release): add gated Pages pipeline and deterministic public artifact checks`.

## Final closure review (2026-10-10)

The requested final local run passed again: validator, 174 Python tests, all 20 JavaScript test files, five builders, generated drift, 1041 link/runtime checks and 150 HTTP checks. This run required no transport retry. Its artifact SHA-256 matches the earlier independent candidates. The 64 publication diagnostics remain blockers; no REVIEW promotion or public URL disposition was applied. Actionlint passed again. Git diff checks confirm no canonical/content/runtime changes or staged files; the branch and baseline commit remain unchanged.

Live HTTPS checks still show the existing public pages responding, with the feature-branch article returning 404. Direct local A/AAAA DNS lookups timed out; that does not establish that authoritative DNS is wrong. TLS inspection still sees the local Avast scanning certificate, so GitHub-origin TLS remains unverified. Recheck Pages DNS/certificate status and the authoritative domain configuration manually before activation. The previously observed Pages source was main/root; it has not been changed here. No remote CI run, commit, push, merge or deployment was performed.

The public repository still contains `research/content/private-markets/private-capital-research/editorial-review.json` and the source/claim/mapping files under `research/mappings/private-capital/`. These are excluded from the site candidate, but require an owner confidentiality review because GitHub visibility is public. The limited scan found no credential-format matches in 27 tracked text files; it is not a full secret/history audit.

## Authorized branch submission

The owner authorized committing and pushing Stage 5 to `feat/research-content-ingestion-foundation` for remote CI review, without main integration, deployment or settings changes. Pre-commit verification passed again with the same artifact hash, all tests/builds/drift checks and 150 HTTP checks. One image response (`private-equity-guide.png`) needed a recorded transport retry and passed byte/framing validation. Publication still rejects the compatibility candidate with 64 diagnostics. Remote CI status is pending at initial submission and will be recorded after the run completes; local success is not remote CI approval.
