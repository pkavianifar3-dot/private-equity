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
        const number = citationIndex && citationIndex.get(citation && citation.sourceRef);
        return number ? ` <sup class="citation"><a href="#citation-source-${number}">[${number}]</a></sup>` : "";
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

    global.PrivateCapitalCitationRenderer = { buildCitationIndex, getBlockCitations, renderInlineCitations, renderCitationMarker };
})(window);
