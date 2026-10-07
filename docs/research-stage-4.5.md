# Research Stage 4.5 — source packages and ingestion foundation

## Boundary

`research/index.json` remains the publication registry and owns canonical `id`,
`status` and public `url`. A package path is an editorial location; the builders
discover it recursively and match by `id` and registry `url`. Atlas remains the
canonical Entity/Claim/Evidence/Source authority. No backend, CMS or new runtime
dependency is introduced.

```text
research/content/private-markets/private-capital/
  research.json                  # unchanged Research v2 data (moved)
  assets/                       # original source image bytes
research/mappings/private-capital/ # existing candidate/mapping records (moved)
articles/private-capital.html     # existing public URL, generated sections
assets/images/...                 # public images copied by the Research build
```

The one verified source domain is `private-markets`. The source of
`research:private-equity` does **not** exist in Research v2. Its
`/articles/what-is-private-equity.html` page contains an introduction, a
figure, multiple headings, a list and a comparison table, but lacks a
corresponding structured citation/mention model. The registry explicitly
marks it `sourceMode: legacy-html`; no JSON, citations or references have
been reverse engineered from the page. This exception is limited to the
verified existing legacy page; any new registry entry without a source fails
build/validation. Its HTML and URL are preserved.

`build-research-pages.js` discovers ordered packages, validates registry
identity and URL, renders existing sections and copies package images to the
specified public asset paths. A new **PUBLISHED** structured article may be
built into a minimal static shell at its registry URL if no HTML exists.
`article-page.js` no longer derives a source path from the URL; static
articles have no `data-research-source` opt-in and never fetch raw JSON at
runtime. The original published Research article remains byte-identical
after rebuild. The Research→Atlas reverse index and Atlas discovery index
walk the new packages.

## DOCX staging workflow

The Word file requested for this phase was absent from the supplied
attachment. No new Research article can be ingested without its bytes. For a
future DOCX, work in an empty staging directory outside the public tree:

```powershell
python research/tools/ingest-docx.py path/to/article.docx --out path/to/staging/extracted
python research/tools/prepare-research.py path/to/staging/extracted/extraction.json path/to/metadata.json --out path/to/staging/package
```

`metadata.json` must explicitly supply `id`, `url`, `title.fa`, `summary.fa`.
The extractor preserves ordered paragraphs, heading levels, tables,
hyperlinks, footnote/endnote text and image/chart/embedded assets with hashes.
The preparer creates **DRAFT** Research v2, a package `assets/` folder and
`editorial-review.json`. It does not invent numeric chart data, citation
Sources, Entity IDs, mention offsets, dates, alt text or credits. An
embedded chart without a reviewed image/data representation stays in staging
for editorial review; an image figure with empty alt needs an editor.

Before moving `research.json` and its assets under
`research/content/<domain>/<slug>/`, an editor must reconcile Word notes,
links, images, captions and figures against the original document; map
citations to verified canonical Sources and mentions/Entity refs to canonical
IDs; provide alt/credit; and choose the registry entry and publication state.
`editorial-review.json` is an audit note, not canonical content. Run the
validator and all tests, then the Research, Research connection, and Atlas
index/static builds; inspect the generated HTML at its stable public URL in
local preview. Only a reviewed PUBLISHED entry generates a public page.

The v2 schema gained optional `subheading.level` (H3–H6) and
`figure.credit`, plus `list.ordered` for numbered lists. Existing content
without these fields renders as before.
Tables, captions, figures, lists, paragraphs, mentions, citations and
bibliography already had v2 support. Charts remain figures if the input
only contains an image; data is never inferred from the image.

## Checks

```powershell
python atlas/tools/validate-atlas.py
python -m unittest discover -s tests -p 'test_*.py'
node atlas/tools/build-research-pages.js
python atlas/tools/build-research-connections.py
python atlas/tools/build-index.py
python atlas/tools/build-catalog.py
python atlas/tools/build-static-pages.py
node tests/research-package.test.js
```

Check tracked generated artifacts with `git diff --exit-code -- articles
assets/images atlas/discovery/index.json atlas/discovery/research-by-entity.json`;
check untracked assets too. This step has not imported a new Word article,
so a new-article preview URL remains pending the missing input.
