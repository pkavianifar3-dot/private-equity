# Atlas ↔ Research connections (Stage 4)

Research content is the authoring source for article-level `entityRefs`. They
assert an editorial association between an article and canonical Atlas Entity
IDs. Section-level `entityRefs` provide section context; they do not silently
promote an Entity into the article-level association. `mentions[].entityRef`
identifies an occurrence in text for precise inline rendering and discovery;
repeated mentions do not increase association strength or create index rows.

`relatedResearchRefs` is a separate, curated Research → Research link. It is
rendered as further reading only for a published registry target with an
existing page (and, if structured, published content). It never contributes
to the Entity reverse index. Legacy articles without structured content have
no inferred Entity associations.

`python atlas/tools/build-research-connections.py` writes the deterministic
`atlas/discovery/research-by-entity.json` projection and the Research context
panel in structured, published article HTML. Run it **after**
`node atlas/tools/build-research-pages.js`; CI regenerates both and checks for
drift. The static Atlas builder reads that index for its analysis section.
Missing associations yield no empty public panel. Ordering is canonical ID
order in the reverse index; article context preserves the author's `entityRefs`
order. Neither order represents a similarity score.

Public projections require PUBLISHED in both the Research registry and
structured content, and PUBLISHED Entity with an existing public route.
Invalid refs fail validation/build. The local-only `preview-entities.py` uses
the same association logic with an in-memory REVIEW projection, written solely
to a temporary overlay. It renders the article context and Atlas analysis
there, and marks preview pages noindex without canonical links. No REVIEW
association is added to the public index or public panels. Existing inline
mention links are governed by the separate deferred publication cutover in
ADR-004.

At this snapshot, the one structured article has six article-level Entity
references and nine inline mentions, but all six Entities are REVIEW. Thus
the public reverse index is empty, the public Entity context panel is absent,
and the existing curated Research → Research reading link is visible. The
overlay demonstrates both directions without changing public artifacts.

## Local exploration presentation (preview only)

The Stage 4 presentation preview composes four navigation paths over these
existing contracts without changing the checked-in public HTML, stylesheet,
index, routes or canonical records. Run:

```text
python atlas/tools/preview-entities.py --port 8765 --showcase
```

Open `/articles/private-capital.html` for the reading-first article: its
desktop rail contains a TOC generated from the *rendered* H2/H3 headings,
then Research from `relatedResearchRefs`, then Atlas from authored `entityRefs`
order. Its text-derived heading IDs survive unrelated insertions. The lead
image is paired with the introduction on desktop and appears first on mobile.
The preview uses the static built article and disables client section
replacement so heading anchors remain in sync. On mobile the TOC and both
exploration cards are independent native disclosures immediately before the
article, preserving a compact reading flow.

Open `/atlas/concept/private-capital/` for the data-first Entity page. Its
desktop rail has an automatic TOC of rendered H2 sections, then Atlas, then
Research. The same three native disclosures precede the factual sections on
mobile. Research items come from the reverse index (ID order); related Entities come from
direct canonical Claim object edges with forward relations first, or incoming
edges only when `reverse_display_allowed` is true. Missing, unpublished or
unrouted targets never get a public exploration link. Preview may show routed
REVIEW entities inside its noindex overlay. Each card shows four items, up to
four more in a native disclosure, and an explicit link to `/atlas/` or
`/articles.html`. Empty cards get one short sentence. The shared cards use
the Persian name «کاوش». There is no inferred similarity or quality ranking.

The real data contains only one structured Research association for a given
Entity. The optional `--showcase` flag adds an explicitly labeled synthetic
second Research fixture from `tests/fixtures/exploration-showcase.json`, plus
its temporary noindex page at `/articles/_preview/private-capital-note.html`.
It is never read by the public builder or added to canonical Research content.
Without `--showcase`, the normal preview contains only actual associations.
Preview styles live in `atlas/tools/exploration-preview.css` and are copied
only to the temporary overlay. The public stylesheet and HTML remain as they
were at the end of the connection-contract implementation.
