# Research source architecture

Research v2 source packages are stored beneath
`content/<domain>/<slug>/research.json`, with article assets in that same
package. `index.json` owns canonical IDs, publication state and public URLs.
See `docs/research-stage-4.5.md` for the ingestion and validation workflow.

`research:private-capital` has a structured package in `private-markets`.
`research:private-equity` has only the preserved legacy HTML page and is
explicitly marked `legacy-html` in the registry. No structured source is
inferred from it. Candidate mappings are article-scoped under
`mappings/private-capital/`; they do not become canonical Atlas records.
