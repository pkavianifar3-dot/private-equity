# Stage 6 — implementation and verification

Date: 2026-10-12. Branch: feat/stage-6-static-search.
Base: origin/main e9edde57303ad3de573da68a1ba29817b04b6936.
No merge, deploy, environment/DNS/Pages change or publication-status change.
GitHub repository variable PAGES_RELEASE_ENABLED was read as false.
Remote CI belongs to the subsequent feature commit/PR; its actual result is
reported separately after push, not inferred from local tests.

## Design and architecture

Atlas: search, three real public categories (8 Concepts, 3 Organizations, 1 Person),
six deliberately ordered foundations, and a metadata-backed Research bridge.
Research: editorial hero, an explicitly selected published feature with real cover
and byline, registry-generated remaining articles, and title/body search.
Shared dark/gold typography and controls; Research's ivory feature adds an
editorial hierarchy rather than copying the Atlas card grid.
No invented popularity, dates, read times, empty categories or AI controls.

15 approved searchable documents: 12 public Entities and 3 published articles.
Search metadata plus pinned Pagefind 1.5.2; one JS normalization/ranking contract.
Only approved public staging supplies searchable bodies/catalog. Approved registry
and package metadata supply published Research identity/presentation.
Name/alias exact, prefix, name tokens, substring precede literal body phrases.
Results deduplicate canonical identities and keep existing URLs and query state.
Body phrases intentionally require actual phrase presence, including hyphenated
English words; no inferred similarity or stemming/fuzzy expansion is presented
as a literal text match. Noncontiguous/reordered body words are a current limit.
Atlas name/alias discovery still supports prefix matching.
Only visible body snippets are fetched. Bounded pagination can grow with content.

## Local automated verification

- Atlas validator PASS.
- 224 Python tests PASS, including 7 public-search staging/recovery regressions.
- All 23 JavaScript test files PASS, plus all JS syntax checks.
- 34/34 real pinned-engine query expectations PASS; actual public aliases,
  exclusive alias fixture and every exact Research title have additional checks.
- Actual UI module tested against delayed responses: stale results cannot replace
  the latest query or mounted input.
- Build Entity/index/catalog, Research pages/connections, static Atlas pages PASS.
- Generated snapshot and URL disposition drift PASS; no canonical data changed.
- Public package: 114 files, 31 HTML pages, 25 sitemap URLs; 1,012 link/runtime
  checks and 158 loopback HTTP checks PASS; zero publication blockers.
- One bounded HTTP retry for a local image timeout succeeded; not suppressed.
- Artifact SHA-256: 8202672fe75043fe796ee7c9d62a4fde5506ef323da6c3cdb3c6f8096f534104.
- Previous actual main tree builds/checks a pre-search public bundle and passes
  current-approval recovery checks. Recovery authorization conditions unchanged.

Publication regressions exclude REVIEW Entity identities and unpublished Research,
reject corrupt metadata/index bytes and unknown/dead result URLs, exclude template
navigation/rails/CTA/bibliography from article text, and retain approved prose that
mentions a private topic without exposing its Entity. No editorial/release manifest
is a website file. Raw repository serving is not the preview for this generated index.

## Browser and visual evidence

Chrome 155 on Windows; loopback Python HTTP, no network/CPU throttling, HTTP responses
no-store/noindex. Desktop CSS viewport measured 1600x1111 (browser zoom affects the
1440x1000 override). Responsive screenshots initially use a 390x844 override;
additional DOM checks observed 390px Atlas / 373px Research widths with no horizontal
overflow. Desktop and mobile screenshots were visually inspected and saved outside
the repository. Later final screenshot recaptures timed out; subsequent checks used
fresh DOM, not a claimed new screenshot. Existing captures show the same layout;
final delta removes logo underline and corrects body relevance.

Real browser checks: Arabic/Persian normalization, canonical top result, legacy
Deal Sourcing/Carried Interest, merged scope, type filter, Back/Forward query+filter
restoration, Enter, Escape, empty state, no console errors in healthy searches.
A controlled metadata HTTP 503 displayed error/retry; retry then rendered 12 results.
After rebuilding the filter, Tab moved from Concept to Organization, proving focus
continuity. Labels, live status and focus styles checked; no screen-reader audit claimed.
Screenshots: stage6-atlas-desktop.jpg, stage6-research-desktop.jpg,
stage6-atlas-mobile.jpg, stage6-research-mobile.jpg in the chat deliverable directory.

## Actual browser performance and output sizes

All search metadata/API/worker/index/fragment/WASM files: **200,053 raw bytes**,
**131,500 gzip bytes** (sum of individually gzip-compressed files). Some engine
files are already compressed, so gzip is not a promised CDN transfer size.

Research initial observed subresources: 346,535 body bytes (excluding HTML), DOMContentLoaded 64.3 ms, load 97.3 ms. Search-index requests on opening: 0.

Atlas initial observed subresources: 169,497 body bytes (excluding HTML), DOMContentLoaded 115.4 ms, load not captured after load completion. Search-index requests on opening: 0.

Both homes download zero metadata/Pagefind files before a query. Shared UI scripts
are small; the first query fetches metadata and engine on demand. Server requests
confirm worker-internal assets absent from the top-frame Resource Timing view.
Observed first-query file bodies: 186,281 bytes; gzip estimate 117,406 bytes, excluding HTTP headers.

`Deal Sourcing`: 164 ms from Enter/submit to completed result DOM; ۱ نتیجه برای «Deal Sourcing».

`Carried Interest`: 28.3 ms from Enter/submit to completed result DOM; ۱ نتیجه برای «Carried Interest».

These are local single-run browser observations, not production latency or a
Core Web Vitals assessment. Node query timing observations are separate from these browser measurements.
The two homes do not load WASM/index on opening; this is the measured loading design,
not a quantified comparison with the old production homepage.

## All 34 grounded queries

Rank is one-based within the requested scope; multiple expected IDs preserve their order.
For negative cases, forbidden identities must be absent. Query 32 corrects the earlier
audit: Dadman is absent from actual approved text; a default prefix hit was not proof
of presence. It now yields zero results. Query 33 is the actual positive private-topic
prose case and excludes the non-public Concept result.

| # | Query | Scope | Expected IDs / actual ranks | Results | Outcome |
|---|---|---|---|---:|---|
| 1 | سرمایه خصوصی | atlas | `concept:private-capital` / 1 | 8 | PASS |
| 2 | Private Capital | atlas | `concept:private-capital` / 1 | 3 | PASS |
| 3 | سرمايه خصوصي | atlas | `concept:private-capital` / 1 | 8 | PASS |
| 4 | سرمایه‌خصوصی | atlas | `concept:private-capital` / 1 | 8 | PASS |
| 5 | سرمایه‌گذاری خصوصی | atlas | `concept:private-equity` / 1 | 4 | PASS |
| 6 | سرمایه گذاری خصوصی | atlas | `concept:private-equity` / 1 | 4 | PASS |
| 7 | سرمایهگذاری خصوصی | atlas | `concept:private-equity` / 1 | 1 | PASS |
| 8 | سرمایه‌گذاری خُصوصی | atlas | `concept:private-equity` / 1 | 4 | PASS |
| 9 | private equity | atlas | `concept:private-equity` / 1 | 1 | PASS |
| 10 | Equi | atlas | `concept:private-equity` / 1 | 1 | PASS |
| 11 | Venture Capital | atlas | `concept:venture-capital` / 1 | 1 | PASS |
| 12 | سرمایه‌گذاری خطرپذیر | atlas | `concept:venture-capital` / 1 | 3 | PASS |
| 13 | سرمایه رشد | atlas | `concept:growth-capital` / 1 | 3 | PASS |
| 14 | Growth | atlas | `concept:growth-capital` / 1 | 1 | PASS |
| 15 | دارایی‌های واقعی | atlas | `concept:real-assets` / 1 | 2 | PASS |
| 16 | دارايي‌هاي واقعي | atlas | `concept:real-assets` / 1 | 2 | PASS |
| 17 | طبقه‌بندی سرمایه خصوصی | atlas | `concept:private-capital-classification` / 1 | 2 | PASS |
| 18 | طبقه بندی سرمایه خصوصی | atlas | `concept:private-capital-classification` / 1 | 2 | PASS |
| 19 | تأمین سرمایه امین | atlas | `organization:amin-investment-bank` / 1 | 2 | PASS |
| 20 | Amin | atlas | `organization:amin-investment-bank` / 1 | 1 | PASS |
| 21 | سرمایه خصوصی Private Capital | all | `concept:private-capital` / 1; `research:private-capital` / 2; `research:private-capital-research` / 3 | 4 | PASS |
| 22 | علي سنگينيان | atlas | `person:ali-sanginian` / 1 | 1 | PASS |
| 23 | آچاره | atlas | `organization:achareh` / 1 | 1 | PASS |
| 24 | Kian | atlas | `organization:kian-financial-group` / 1 | 1 | PASS |
| 25 | Deal Sourcing | research | `research:private-equity` / 1 | 1 | PASS |
| 26 | Carried Interest | research | `research:private-equity` / 1 | 1 | PASS |
| 27 | High-Net-Worth Individuals | research | `research:private-equity` / 1 | 1 | PASS |
| 28 | ECB | atlas | `concept:private-equity` / 3 | 4 | PASS |
| 29 | سازوکار تأمین مالی | research | `research:private-capital-research` / 1 | 1 | PASS |
| 30 | xyzq987noresult | all | No result | 0 | PASS |
| 31 | گروه کیسون | all | Forbidden identities absent | 0 | PASS |
| 32 | دادمان | all | No result | 0 | PASS |
| 33 | اجزای قراردادی | all | `research:private-capital` / 1 | 1 | PASS |
| 34 | گروه مالي كيان | atlas | `organization:kian-financial-group` / 1 | 1 | PASS |

## Inspect and reproduce

```powershell
npm ci --ignore-scripts
python -B tools/release.py verify --output "$env:TEMP/privatecapital-stage6-inspect"
python -B tools/preview-release.py --public --artifact "$env:TEMP/privatecapital-stage6-inspect" --port 8786
```

Use a fresh output directory each time. Current isolated preview:

- http://127.0.0.1:8786/atlas/
- http://127.0.0.1:8786/articles.html
- http://127.0.0.1:8786/atlas/explore/?q=Private%20Equity

The local server must remain running. The old published site is unchanged.
No route, redirect, canonical Entity/Research schema, ID, status, Claim/Evidence/Source
or sitemap surface was changed. Search assets are derived and included in release
hashes; temporary Pagefind corpus/default UI are not public assets.
The single pinned build dependency also installs in the existing recovery job;
feature/PR candidates remain ineligible for production recovery sources or deploy.

## Files changed

- `.github/workflows/validate-atlas.yml`
- `.gitignore`
- `articles.html`
- `assets/css/discovery.css`
- `assets/js/atlas-explore.js`
- `assets/js/atlas-home.js`
- `assets/js/kaavosh-core.js`
- `assets/js/kaavosh-ui.js`
- `atlas/explore/index.html`
- `atlas/index.html`
- `docs/stage-5-url-disposition.md`
- `docs/stage-6-search-contract.md`
- `docs/stage-6-verification.md`
- `package-lock.json`
- `package.json`
- `tests/fixtures/kaavosh-queries.json`
- `tests/kaavosh-search.test.js`
- `tests/kaavosh-ui.test.js`
- `tests/research-static-page.test.js`
- `tests/test_public_search.py`
- `tools/preview-release.py`
- `tools/recovery.py`
- `tools/search-home.json`
- `tools/search-inspect.mjs`
- `tools/search.py`
- `tools/site_release.py`

## Remaining decisions and limits

Visual/editorial acceptance, PR approval and any subsequent merge/release require
the owner's next instruction. No new architecture decision is needed for this scope.
Future typo-tolerant/semantic search must keep match labels and relevance tests honest.
No backend/AI, Topic landing pages, Similarity, Watch changes or Stage 7 work.
Performance should be sampled on production/mobile networks after a separately
authorized release. No production deployment or protected recovery was tested here.

## Remote checkout correction

Initial push/PR CI for 3f8e17efb762f896b1c2ee9d494679024a1dfdd9 failed in the
validation step. Existing depth-1 checkout lacks the actual Stage 5 baseline
commit required by the historical recovery regression. This was reproduced in
an isolated depth-1 clone (baseline object unavailable). Validation checkout
now fetches history; the test, publication rules and deployment gates remain
enabled. Follow-up push/PR CI must succeed independently for the corrected SHA.

## Homepage refinement verification — 2026-10-13

- Local `tools/release.py verify`: Atlas validator passed; 231 Python tests and all 23 JavaScript test files passed, including 34/34 grounded Pagefind queries. All index/catalog/Research/connections/static builders and generated drift checks passed.
- Added seven focused homepage tests: fixed ceilings on a larger synthetic corpus; stable ordering; invalid/bool/over-limit config rejection; nonpublic and missing identities excluded; semantic index required; trusted public URLs used instead of index URLs; shared header/footer parity. Search UI regression also checks feature hiding/restoration.
- Final responsive CSS fixes were followed by a fresh exact artifact build/check, publication check and HTTP smoke: 114 files, 31 HTML pages, 25 sitemap URLs, 1,035 link/runtime checks, 158 HTTP checks, zero publication blockers.
- Chrome desktop: split Research hero, three distinct Atlas category cards, 30px bridge padding and real reciprocal cards confirmed. Search `Private Equity` produced three results, hid both discovery sections and feature, and expanded the search area. Escape restored discovery; Tab moved from search input to scope selector. No browser console errors on either homepage.
- Chrome narrow viewport: both pages had equal clientWidth/scrollWidth (345px during the check), one-column category/bridge layout, 20px bridge padding and retained discovery cards. Mobile screenshot capture timed out on two attempts; mobile geometry/DOM were verified, but a captured mobile visual review is not claimed. Desktop capture succeeded before the final spacing refinement.
- Preview uses the actual isolated approved public artifact at `http://127.0.0.1:8787/atlas/` and `/articles.html`; it does not serve raw canonical inputs. No canonical data, publication statuses, public URLs, sitemap URLs or deployment workflow changed. The URL disposition document changed only to record restored existing header/footer inbound links.
- These refinements remain local and uncommitted pending visual review. Previous remote CI success does not verify these new working-tree changes. No merge, deploy or release-gate change was performed.

## Shared signature and compact discovery — 2026-10-13

This revision supersedes the earlier four/three-item caps and screenshot limitations above.

- Full local release verification passed: Atlas validator, 238 Python tests, all 23 JavaScript test files, 34/34 grounded search queries, all builders and deterministic drift checks. One image HTTP timeout retried successfully; no validation was skipped.
- Added shared search markup tests for exact form/helper parity, native GET actions and default scopes, accessible SVG submit and escaping, compact rail placement, relation-label ordering and editorial label placement. Added six-item editorial curation and nonpublic-feature rejection regressions.
- Chrome screenshots succeeded for both discovery homes on desktop/mobile. The Research feature is dark and its full image uses contain. Actual browser inspection caught a missing display:grid on the compact Research list; that was corrected and verified before final artifact checks. With two articles the grid fits two cards; with more it supports three columns and at most six cards.
- Actual public artifact: 115 files, 31 HTML pages, 25 sitemap URLs, 1,056 link/runtime checks, zero publication blockers. The final CSS-only/grid and label changes were followed by a fresh artifact build/check and focused markup tests; final publication/HTTP smoke are reported after completion below.
- Real home search `Deal Sourcing` reached `/atlas/?q=Deal+Sourcing&scope=all` and found the approved Private Equity article. Real Entity rail search `Carried Interest` reached the same Atlas route with scope=all. The Research rail contains no brand/filter and begins with search before TOC. Entity relation labels precede their target names and keep the target links.
- Narrow viewport inspection: clientWidth=scrollWidth=375px on Atlas, Research, root home and structured article; category strip about 55px high; discovery grids and crosslinks use one column; reading rail becomes static; home search field remains about 266px with the brand to its left. Desktop category strip about 60px. Mobile screenshots were saved outside the repository.
- Source review verified 23 regenerated reading pages differ only in their exploration rails and the new search stylesheet link; article/Entity main content was unchanged. Canonical data, statuses, IDs, publication boundary, sitemap URL set and deployment workflows were unchanged.
- New shared CSS is a public asset; the Python helper and editorial settings are build inputs and are not copied into the public artifact. Changes are local and uncommitted; prior remote CI results do not cover this revision. No merge/deploy or gate/settings change occurred.

Final exact-artifact checks passed: publication eligibility and all 159 HTTP smoke requests. The final smoke retried one private-capital.png timeout successfully (bounded 1/1); no missing asset was ignored. git diff --check passed. Final desktop Research screenshot confirms the corrected grid; browser console errors were empty on both discovery homes. Local preview remains at port 8788.

## Centered discovery introductions — 2026-10-13

Supersedes the previous root search presentation with a brand-free, selector-free native form; its hidden scope remains all. Both discovery homes retain their native scope selector, placed below-left. Intro text, decorative quotation and themed lens labels follow the approved wording. Atlas editorial feature is left, intro right. Desktop Atlas rail adds 30px above its search.

- Full local release verification passed: Atlas validator, 239 Python tests, all 23 JavaScript test files, 34/34 grounded ranked queries, builders and deterministic drift checks. Test HTTP transport retried atlas.js within the existing bounded policy; all tests passed.
- Exact public artifact: 115 files, 31 HTML pages, 25 sitemap URLs, 1,056 link/runtime checks, 159 HTTP requests, zero publication blockers. Final artifact HTTP verification needed no transport retries.
- Actual Chrome desktop screenshots reviewed both discovery introductions; Atlas feature is left and intro right. Root field center deviation: 0px horizontal, 0.5px vertical. Atlas rail gap: 30px.
- Mobile viewport 390px (375px content area): root, both discovery homes and Atlas Entity had no horizontal overflow; both hero headlines occupied one line. Research and Atlas mobile screenshots reviewed.
- Native root submission of Deal Sourcing navigated to /atlas/ and found the approved Research result with default all scope. Native selector changed Research scope to all and back, and Tab advanced to the next link. Research console had no errors. Native OS dropdown appearance cannot be fully captured/controlled by page CSS.
- Preview: http://127.0.0.1:8788/ from the verified artifact privatecapital-kaavosh-centered-20261013. No commit, push, deploy, workflow or publication-policy changes. Prior remote CI does not cover these local edits.

## Unified signature, Research entry point and Persian header — 2026-10-13

- Removed residual badge in Explore; made scope placement shared. Corrected helper compact CSS coupling: only actual rails get compact sizing. Homepage search measured 760x64px desktop, 58px high mobile, with proportionate input and magnifier.
- Root and both rail native forms submit to /articles.html with scope=all. Direct Research default and existing Atlas/Explore routing remain unchanged. Header wordmark/image is a native accessible home link; static and Research builders generate it.
- Focused presentation/search/exploration tests: 31 passed. Full release verification: validator, 241 Python tests, all 23 JS test files, 34/34 grounded ranked queries, builders/drift all passed. Initial partial rebuilding left old Research TOC anchors; running the existing connection builder reconciled them before the successful full verification. No checks were disabled.
- Verified public artifact: 115 files, 31 HTML pages, 25 sitemap URLs, 1,103 link/runtime checks, 159 HTTP smoke requests, zero blockers. Artifact digest e1ae9b3404acc315fd65bbd327736754719f2afb4fb971ffc6f46e5a0e1179ea. Final smoke needed no retries; two existing test-only atlas.js transport retries recovered within their bounded policy.
- Chrome actual root, Atlas rail and Research rail submissions reached Research with explicit all scope. Actual wordmark click returned to /. Desktop screenshot confirmed nav right, brand left, no Explore badge, scope below-left. 1024px viewport had no header overlap. 390px viewport (375px content): root and Explore had no horizontal overflow; root mobile screenshot reviewed. Explore screenshot bridge scaled inconsistently despite DOM width 375px and correct 32px heading style; DOM geometry was verified, final mobile visual review remains available in preview.
- No browser console errors observed on Explore. Temporary viewport reset. Local preview port 8788 uses privatecapital-kaavosh-unified-20261013. No commit/push/merge/deploy or settings/publication-policy changes. Prior remote CI does not cover these local edits.

## Authorized final registration checkpoint — 2026-10-13

Fetched main e9edde57303ad3de573da68a1ba29817b04b6936; feature head 6060ab931f8bf0389d48c3e83d27a8a7bcf9886c is two ahead, zero behind. GitHub PR 18 is open to main and repository gate reads false. User explicitly authorized this feature commit/push and PR update, excluding merge/deploy/settings changes. Final repeat of full local release verification passed (241 Python tests, 23 JS test files, 34 ranked queries, validator/build/drift, 115 files, 31 HTML pages, 25 sitemap URLs, 1,103 link/runtime and 159 HTTP checks, zero blockers). npm.ps1 was blocked by local execution policy; npm.cmd ci --ignore-scripts succeeded without policy change. Search tests and exact artifact/publication checks passed after the clean install. Remote CI for the new registration must be verified separately and its run links recorded in the PR/final response.
