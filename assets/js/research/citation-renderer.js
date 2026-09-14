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
                .map((citation, index) =>
                    `<a href="#citation-location-${escapeHtml(citation.id)}">↩ ${index + 1}</a>`
                )
                .join(" · ");

            const sourceLink =
                typeof entry.source.url === "string" && entry.source.url
                    ? `<a href="${escapeHtml(entry.source.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(label)}</a>`
                    : escapeHtml(label);

            return `<li id="citation-source-${entry.number}"><strong>[${entry.number}]</strong> ${sourceLink}${locations ? ` ${locations}` : ""}</li>`;
        });

        return `<div class="article-citations"><p>منابع</p><ul>${items.join("\n")}</ul></div>`;
    }

    function renderInlineCitations(text, blockId, citations, citationIndex) {
        const value = String(text || "");
        const items = getBlockCitations(citations, blockId, value.length);
        if (!items.length) return escapeHtml(value);

        const parts = [];
        let cursor = 0;
        let i = 0;

        while (i < items.length) {
            const c = items[i];

            if (c.start < cursor) {
                i++;
                continue;
            }

            parts.push(escapeHtml(value.slice(cursor, c.end)));

            const sameRange = [c];
            let j = i + 1;

            while (
                j < items.length &&
                items[j].start === c.start &&
                items[j].end === c.end
            ) {
                sameRange.push(items[j]);
                j++;
            }

            sameRange.forEach(item => {
                parts.push(renderCitationMarker(item, citationIndex));
            });

            cursor = c.end;
            i = j;
        }

        parts.push(escapeHtml(value.slice(cursor)));
        return parts.join("");
    }

    global.PrivateCapitalCitationRenderer = { buildCitationIndex, getBlockCitations, renderInlineCitations, renderCitationMarker, renderCitationBibliography, renderCitationBibliographyHtml };
})(window);
