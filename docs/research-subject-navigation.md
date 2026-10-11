# Research main-subject navigation policy

## Contract approved by the owner

`Research.primaryEntityRef` is an optional canonical Atlas Entity ID, explicitly
confirmed by the editor as the main subject of the entire article. It must
resolve and appear in the article's `entityRefs`. This is additive Research
editorial metadata; Atlas canonical records, IDs and lifecycle do not change.
Existing packages without the field keep their editorial navigation.

The title and its aliases can inform the editorial decision, but no title,
heading, mention count or first entry in `entityRefs` automatically assigns the
subject. Articles that compare multiple subjects or have an uncertain focus
leave the field absent. The ingestion pipeline does not invent this value.
After reviewing an article, add the confirmed Entity ID to `entityRefs` and
`primaryEntityRef`, then run the validator before publication. Changing a title
does not silently change the subject or the article's public URL.

## Deterministic selection

1. Keep published targets from `relatedResearchRefs` in editorial order.
2. Add other published structured Research with the exact same `primaryEntityRef`,
   sorted by Research ID. This also provides the reverse link automatically.
3. Exclude the current article, duplicates, DRAFT/REVIEW/ARCHIVED Research and
   invalid/missing public Research destinations. Broken contracts fail the build
   with an owner ID. No similarity, Jaccard, title guessing or broad overlap is used.
4. Reuse the shared exploration card: at most eight entries, four initially
   visible and up to four under progressive disclosure, followed by the directory.

The build reads a single snapshot and constructs an in-memory subject map once,
then reuses it for every article. The selector stops at eight accepted items
so each card does not materialize an unbounded peer list. It creates no new service, dependency or
independently edited index. The selector returns `editorial` or
`same-primary-entity` as an explainable reason; the compact UI omits redundant
badges. Both real Private Capital articles declare `concept:private-capital`
and retain the owner's explicitly requested reciprocal editorial links.

## Publication boundary

Research-to-Research navigation links only published Research pages. The subject
Entity may remain REVIEW because matching its identity does not expose a new
Entity URL or promote it. Research-to-Atlas cards and new article inline Entity
links still require a published Entity with a supported public route. The Atlas
reverse index continues to use article-level `entityRefs`, independently of the
primary subject and editorial links. ADR-004's global cutover remains deferred.

## Sticky navigation

The sidebar's containing block spans the primary content. Its inner rail sticks
below the existing site header and is constrained by the reading area, so it
does not overlap the footer. Long rails scroll within the available viewport
height. Under 980px the rail is static, uses the existing accessible mobile
disclosures, and leaves the main document free of horizontal overflow. The
public Research and isolated local Atlas layouts share the same stylesheet.
