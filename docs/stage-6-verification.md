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
