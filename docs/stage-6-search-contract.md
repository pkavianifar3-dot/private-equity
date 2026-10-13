# Stage 6 — Kaavosh public search

Baseline: origin/main e9edde57303ad3de573da68a1ba29817b04b6936.

## Product and source boundary
Search-first, guided discovery; Atlas is entity-first and Research is editorial.
No new public route, canonical model, publication status, backend or AI API.
`/atlas/` and `/atlas/explore/` default to all scope; `/articles.html` defaults to Research.
Both accept q, scope (atlas/research/all), type, group, page. Existing q/type/group/page links remain supported.

The release packager first stages the existing approved public projection.
Only that staging directory supplies searchable Entity records and article HTML.
Published Research registry entries determine identity and URL; approved structured
metadata supplies title/summary/byline, never unpublished package text. Legacy
Research is extracted from its actual public article. Navigation, rails, CTAs,
bibliography, identity/status blocks and template notices are excluded.

The generated `search/documents.json` is a public metadata artifact, not a source
of truth. Records have id, kind (concept/entity/research), scope, type, title,
English name, aliases, summary, URL, and derived Pagefind identity. Presentation
and curated references come from tools/search-home.json; article lists come from
the registry. Neither release manifests nor editorial files enter the site.

Pagefind 1.5.2 is pinned with npm lockfile. A normalized, temporary HTML corpus is
built exclusively from approved staging. Only its API, worker and index assets
are packaged, never temporary corpus HTML or default Pagefind UI bundles.
Every derived byte joins the existing release allowlist, hashes and recovery.
Pre-Stage-6 historical source trees keep their original package contract; the
actual baseline tree has a recovery regression. Current trees require derived bytes.
Historical recovery additionally checks search identities against current approval.

## Ranking
Shared normalization: NFKC, Arabic/Persian letters and digits, case, diacritics,
tatweel, whitespace and ZWNJ. Compact name comparison handles joined Persian
variants; full-text requires the normalized literal phrase, including hyphenated English terms.
This intentionally avoids fuzzy/prefix body hits; name discovery still supports
prefixes and aliases. Body words separated/reordered differently are not phrase hits. Canonical/alias exact = tier 0;
prefix = 1; all query tokens in name fields = 2; substring = 3; body match = 4.
In all-scope ties, concepts/entities precede Research; Pagefind body order is
retained within body matches. Stable IDs settle other ties. A published article
may match a private topic in prose; the private Entity is never a result.
Duplicate identities/URLs and unapproved Pagefind hits are rejected/ignored.

## Loading and accessibility
Home content is rendered at build time and works without JavaScript. No Pagefind
download on empty home view. Explore loads metadata for browsing; Research loads
search on interaction/query. Result snippets are fetched for the visible page
only. One shared renderer preserves the form/focus, announces status via live
region, handles errors/retry, pagination, Enter, Escape, slash, and popstate.
Desktop and mobile use the same accessible controls and content hierarchy.

## Acceptance
34 grounded queries specify scope, expected identities and rank, independently
of publication tests. The earlier Dadman audit hit was a prefix false positive:
actual public prose has no Dadman occurrence. Query 32 now correctly asserts zero
results. The positive private-topic prose regression uses actual contractual-components
text, separately from forbidden Entity identities. Alias-only, exact Research titles, deduplication, bad URL,
unknown type/group, stale requests, unpublished Research and REVIEW fixtures are
additional regressions. Full release checks remain mandatory. Pagefind presence
alone is not relevance proof. Browser/network measurements and screenshots are
recorded after implementation; no merge/deploy is authorized.

## Homepage refinement — 2026-10-13

Discovery homes and Explore reuse the established site header/logo/navigation and full footer. Research uses a responsive split hero with one editorial feature; Atlas uses a compact category strip. Reciprocal crosslinks derive from the existing entityRefs reverse index and are resolved against the approved public document set. Fixed ceilings: six curated Concepts, six editorially curated Research cards, six semantic links per cross-lens section. Full discovery remains available through the existing paginated search routes. See `stage-6-discovery-editorial.md` for the editorial controls and deterministic ordering.

Search presentation now shares one native markup helper and stylesheet across home, discovery and reading rails. Atlas and Explore default to all scope; Research defaults to research. Atlas home accepts shareable search parameters without renaming its route. Research feature images use contain, editorial labels precede images, and relation labels precede Entity names in the rail.

## Final signature and entry points — 2026-10-13

All current discovery/search forms omit the redundant Kaavosh badge, keep a white native search field and place the visible scope control below-left. The homepage and both reading rails submit to /articles.html with explicit scope=all. Direct /articles.html still defaults to research; existing Atlas and Explore routes retain their query contracts and all defaults. Compact sizing belongs only to reading rails, independently of badge visibility.

All existing headers link their wordmark and logo to /. Navigation stays in Persian order on the right on desktop; brand sits left. Responsive mobile navigation wraps without reversing tab order. Static/Research builders preserve this contract on regeneration.
