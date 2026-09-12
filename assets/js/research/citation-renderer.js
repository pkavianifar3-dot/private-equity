(function (global) {
    "use strict";

    function escapeHtml(value) { return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;"); }

    function buildCitationIndex(sections, citations) {
        const index = new Map();
        const items = Array.isArray(citations) ? citations : [];
        (Array.isArray(sections) ? sections : []).forEach(section => {
            (Array.isArray(section.content) ? section.content : []).forEach(block => {
                items.filter(c => c && c.contentBlockId === block.id && typeof c.sourceRef === "string" && typeof c.start === "number").sort((a, b) => a.start - b.start).forEach(c => {
                    if (!index.has(c.sourceRef)) index.set(c.sourceRef, index.size + 1);
                });
            });
        });
        return index;
    }

    function getBlockCitations(citations, blockId, textLength) {
        return (Array.isArray(citations) ? citations : []).filter(c => c && c.contentBlockId === blockId && typeof c.sourceRef === "string" && typeof c.start === "number" && typeof c.end === "number" && c.start >= 0 && c.end > c.start && c.end <= textLength).sort((a, b) => a.start - b.start);
    }

    function renderCitationMarker(citation, citationIndex) {
        const number =
            citationIndex &&
            citationIndex.get(citation && citation.sourceRef);

        if (!number) {
            return "";
        }

        const citationId =
            citation && typeof citation.id === "string"
                ? citation.id
                : `citation-${number}`;

        return ` <sup class="citation" id="citation-location-${escapeHtml(citationId)}"><a href="#citation-source-${number}">[${number}]</a></sup>`;
    }

    function renderCitationBibliography(citations, sources, citationIndex) {
        if (!Array.isArray(citations) || !citations.length) {
            return "";
        }

        if (!Array.isArray(sources) || !sources.length) {
            return "";
        }

        const sourceById = new Map(
            sources
                .filter(source => source && typeof source.id === "string")
                .map(source => [source.id, source])
        );

        const entries = [];

        for (const [sourceRef, number] of citationIndex || []) {
            const source = sourceById.get(sourceRef);

            if (!source) {
                continue;
            }

            entries.push({
                sourceRef,
                number,
                source
            });
        }

        if (!entries.length) {
            return "";
        }

        return entries;
    }

    function renderCitationBibliographyHtml(citations, sources, citationIndex) {
        const entries = renderCitationBibliography(
            citations,
            sources,
            citationIndex
        );

        if (!entries.length) {
            return "";
        }

        const items = entries.map(entry => {
            const title =
                typeof entry.source.title_fa === "string"
                    ? entry.source.title_fa
                    : typeof entry.source.title_en === "string"
                        ? entry.source.title_en
                        : entry.source.id || "";

            const publisher =
                typeof entry.source.publisher === "string"
                    ? entry.source.publisher
                    : "";

            const label = publisher
                ? `${title} — ${publisher}`
                : title;

            const locations = (Array.isArray(citations) ? citations : [])
                .filter(citation =>
                    citation &&
                    citation.sourceRef === entry.sourceRef &&
                    typeof citation.id === "string"
                )
                .map(citation =>
                    `<a href="#citation-location-${escapeHtml(citation.id)}">↩</a>`
                )
                .join(" ");

            const sourceLink =
                typeof entry.source.url === "string" && entry.source.url
                    ? `<a href="${escapeHtml(entry.source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`
                    : escapeHtml(label);

            return `<li id="citation-source-${entry.number}"><strong>[${entry.number}]</strong> ${sourceLink}${locations ? ` ${locations}` : ""}</li>`;
        });

        return `<div class="article-citations"><p>منابع</p><ol>${items.join("\n")}</ol></div>`;
    }

    function renderInlineCitations(text, blockId, citations, citationIndex) {
        const value = String(text || "");
        const items = getBlockCitations(citations, blockId, value.length);
        if (!items.length) return escapeHtml(value);
        const parts = []; let cursor = 0;
        items.forEach(c => {
            if (c.start < cursor) return;
            parts.push(escapeHtml(value.slice(cursor, c.end)));
            parts.push(renderCitationMarker(c, citationIndex));
            cursor = c.end;
        });
        parts.push(escapeHtml(value.slice(cursor)));
        return parts.join("");
    }

    global.PrivateCapitalCitationRenderer = { buildCitationIndex, getBlockCitations, renderInlineCitations, renderCitationMarker, renderCitationBibliography, renderCitationBibliographyHtml };
})(window);
