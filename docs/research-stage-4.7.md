# Stage 4.7 — Research content onboarding and ingestion hardening

## Identity and publication

The attached `DOC-000001-Private Capital.docx` has been ingested as
`research:private-capital-research` in
`research/content/private-markets/private-capital-research/research.json`.
Its registry URL is `/articles/private-capital-research.html`. The owner has
approved publication and the final title “سرمایه خصوصی (Private Capital) چیست؟ |
مفهوم، دامنه، تمایز و سازوکار”; source and registry status are `PUBLISHED`.
The existing `/articles/private-capital.html`, its title, canonical ID and
publication date are preserved. Both articles coexist with the owner-approved reciprocal editorial links
and confirmed primary subject. No redirect is introduced. Final page review
precedes commit/push.

## Document mapping

The source contains one H1, four H2 sections, 37 extracted paragraphs,
one five-row table, two embedded PNG figures, 20 referenced footnotes and
24 Word comments. A separate author line precedes the body. The comments
carry editorial/structural tags; they and the original bibliography are kept
in the article-local `editorial-review.json`, with the DOCX SHA-256 and asset
hashes. Email handles in comment metadata are redacted from the repository;
the original DOCX remains the audit source. Comments are not public content. Footnotes are represented as `note`
blocks following their containing paragraph/table; this optional v2 content
block is backward compatible. The table caption/credit and both figure
captions/credits are preserved. The separately supplied FIG PNGs match the
embedded images byte for byte and therefore only one copy of each is kept.
Source assets remain inside the package; the approved public build copies
the referenced images into the public asset directory. Preview stays isolated. No chart values were reconstructed from image pixels.

Six bibliography entries have documented URLs in the Word file. They are
represented by new canonical Source records in
`atlas/sources/private-capital-word-2026.json`. Authored in-text citations
map to those same records, including the Preqin parenthetical and the CFA
citation inside a footnote. A cited Source and an uncited bibliography Source
use the same renderer and source index. No new Entity IDs were minted:
article-level `entityRefs` include only the confirmed Private Capital and
Private Equity concepts; `mentions` are precise occurrences in text.
REVIEW Entities remain outside public exploration.

## Publication approval and remaining metadata

The owner approved the article for publication after visual review. Source
attribution is preserved from the Word file; this implementation does not claim
independent verification of the underlying source publications. No author Entity
or publication date is fabricated where none was supplied. Approval of this
Research article does not promote any Atlas Entity or activate ADR-004's global
cutover. The old guide retains its existing inline REVIEW references as the
explicit transitional exception; new published Research inline links and
exploration cards require a PUBLISHED Entity with a supported public route.

## Pipeline and verification

- JavaScript discovery and direct article builds reject mismatched source and
  registry URL/status before writing HTML or assets.
- Python registry, Research connections and discovery index enforce the same
  boundary. Discovery excludes REVIEW Research and new REVIEW Entity references;
  the old guide's nine discovery references are preserved until ADR-004 cutover.
- New PUBLISHED structured packages can generate a complete static article
  without earlier HTML. A disposable end-to-end fixture covers static HTML,
  connections and schema validation; CI already runs that test.
- `python atlas/tools/preview-entities.py --port 8767` serves the isolated
  overlay; open `http://127.0.0.1:8767/articles/private-capital-research.html`.
  Atlas concept preview pages link back to this article.
- Verification: `python atlas/tools/validate-atlas.py`,
  `python -m unittest discover -s tests -p 'test_*.py'`, all `*.test.js`,
  index/catalog, static Research, Research connections, static Atlas builders,
  generated artifact drift, and local HTTP link/asset checks.

## Editorial presentation review

The Word title is displayed as a descriptive editorial headline; the original
H1 remains recorded in the extraction. The author line now appears as an
explicit byline, using the same existing portrait and topic cover as the
published guide. No publication date is fabricated. The new article keeps
its reading-first rail after a full-width article heading. All 20 Word notes
remain in the source; compact linked endnotes live in one collapsed section
at the end of the article, with citations preserved. The source table's
physical Word cell order was reversed to produce a right-to-left header
starting with “مفهوم”. Figure/table captions and credits occupy separate,
centered lines. Bibliography direction follows the visible source language.

## Editorial reference and Entity-link presentation

The 20 footnote positions were reconciled against the original DOCX XML:
15 positions in paragraphs and five positions in right-to-left table cells.
The optional note `anchor` records the target block and exact text offset
(with row and column for a table); the ingester and preparation step retain
those offsets for future packages. Invalid anchors fail the static renderer.
Inline bracketed Source references use the text baseline, while the notes
and six bibliography entries live in matching, accessible collapsed panels.
Hash navigation opens either panel before jumping to an entry. The package
opts into `first-per-section` Entity linking and `inline-collapsible`
references via presentation metadata. Each routed Entity receives at most
one link per section. This policy remains opt-in for structured packages;
the owner explicitly approved applying it to the existing conceptual guide too.
Both pages reuse the approved reading layout, inline references and collapsible
bibliography; the new article retains all 20 exact Word note anchors. Shared
exploration cards use public filtering, while the localhost overlay may include
REVIEW Entity context. TOCs are rebuilt from actual headings without duplicate
rails. The approved new article is added to the articles directory and sitemap.


## Final release verification

The final pass completed Atlas validation, 152 Python tests and all 20
JavaScript test files. Repeating index/catalog, Research page, connection and
Atlas page builds produced zero drift across 47 artifacts. The two generated
articles passed 151 local HTTP/anchor checks with unique IDs. Existing public
Atlas pages, catalog and mention discovery remain unchanged. Chrome DOM and
computed layout checks confirmed mobile cards, no document overflow, scrollable
RTL tables, source baseline markers, superscript note markers, language-aware
references, note-link disclosure and keyboard bibliography disclosure. Screenshot
capture timed out; the owner reviews both final pages before commit/push.

Run `python -m http.server 8771 --bind 127.0.0.1` from the repository for the
actual public output (no REVIEW overlay). Open:

- `http://127.0.0.1:8771/articles/private-capital-research.html`
- `http://127.0.0.1:8771/articles/private-capital.html`


## Follow-up: same-subject Research and sticky navigation

The owner approved the additive optional `primaryEntityRef` Research field.
Both articles declare `concept:private-capital`. The validator requires a known
canonical Entity listed in article-level `entityRefs`; static builds also fail
before writing output for an invalid declaration. The shared selector loads one
build snapshot, keeps published editorial targets first, and adds exact same-
subject published Research in stable ID order, capped at eight. No title-based
guessing, similarity or topic-page implementation is introduced. Regression
fixtures verify automatic reciprocal navigation even without editorial refs,
deduplication, self-exclusion, status filtering, invalid subjects, missing pages
and reuse of a build snapshot. Full policy: `research-subject-navigation.md`.

The public Research rail's inner containing block now spans the whole article,
allowing its existing sticky layout to remain below the header while scrolling.
The shared local Atlas rail follows the same behavior. Browser checks observed
the rail at approximately 96px after scrolling Research 2,437px and Atlas 1,000px,
below the approximately 83px header. Mobile checks confirmed static disclosures
and no horizontal overflow. Public Atlas HTML, catalog and mention discovery
remain unchanged; Atlas rail changes are verified in the isolated preview.

Current preview links:

- Actual public output: `http://127.0.0.1:8771/articles/private-capital.html`
- Actual public output: `http://127.0.0.1:8771/articles/private-capital-research.html`
- Isolated Atlas preview: `http://127.0.0.1:8773/atlas/concept/private-capital/`

The owner approved the final review and instructed commit/push to the
existing `feat/research-content-ingestion-foundation` branch. No merge to main
or deployment change is included in this approval.
