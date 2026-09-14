(function (global) {
    "use strict";

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function resolveMention(entityRef, entityResolver) {
        if (
            entityResolver &&
            typeof entityResolver.resolve === "function"
        ) {
            const resolved = entityResolver.resolve(entityRef, "research");
            return resolved ? resolved.url : null;
        }

        return global.PrivateCapitalURL.entityURL(entityRef, "research");
    }

    function renderTextWithMentions(
        text,
        blockId,
        mentions,
        citations,
        citationIndex,
        entityResolver
    ) {
        const value = String(text || "");
        const mentionItems = (Array.isArray(mentions) ? mentions : []);

        const applicableMentions = mentionItems
            .filter(mention =>
                mention &&
                mention.contentBlockId === blockId &&
                mention.resolutionStatus === "RESOLVED" &&
                typeof mention.entityRef === "string" &&
                typeof mention.start === "number" &&
                typeof mention.end === "number" &&
                mention.start >= 0 &&
                mention.end > mention.start &&
                mention.end <= value.length
            )
            .map(mention => ({
                ...mention,
                url: resolveMention(
                    mention.entityRef,
                    entityResolver
                )
            }))
            .filter(mention => mention.url);

        applicableMentions.sort((a, b) => a.start - b.start);

        const citationRenderer = global.PrivateCapitalCitationRenderer;
        const citationItems =
            citationRenderer &&
            typeof citationRenderer.getBlockCitations === "function"
                ? citationRenderer.getBlockCitations(
                    citations,
                    blockId,
                    value.length
                )
                : [];

        const parts = [];
        const markersByEnd = new Map();

        citationItems.forEach(citation => {
            const marker =
                citationRenderer &&
                typeof citationRenderer.renderCitationMarker === "function"
                    ? citationRenderer.renderCitationMarker(
                        citation,
                        citationIndex
                    )
                    : "";

            if (!marker) {
                return;
            }

            const markers = markersByEnd.get(citation.end) || [];
            markers.push(marker);
            markersByEnd.set(citation.end, markers);
        });

        let cursor = 0;

        applicableMentions.forEach(mention => {
            if (mention.start < cursor) {
                return;
            }

            const mentionText = value.slice(
                mention.start,
                mention.end
            );

            if (
                typeof mention.text === "string" &&
                mention.text !== mentionText
            ) {
                return;
            }

            parts.push(
                escapeHtml(value.slice(cursor, mention.start))
            );

            parts.push(
                `<a href="${escapeHtml(mention.url)}">${escapeHtml(mentionText)}</a>`
            );

            cursor = mention.end;
        });

        for (const [end, markers] of [...markersByEnd.entries()].sort(
            ([a], [b]) => a - b
        )) {
            if (end < cursor) {
                continue;
            }

            parts.push(escapeHtml(value.slice(cursor, end)));
            parts.push(markers.join(""));
            cursor = end;
        }

        parts.push(escapeHtml(value.slice(cursor)));

        return parts.join("");
    }

    function renderBlock(
        block,
        mentions,
        citations,
        effectiveCitationIndex,
        entityResolver
    ) {
        switch (block.type) {
            case "paragraph":
                return `<p>${renderTextWithMentions(
                    block.text || "",
                    block.id,
                    mentions,
                    citations,
                    effectiveCitationIndex,
                    entityResolver
                )}</p>`;

            case "subheading":
                return `<h3>${renderTextWithMentions(
                    block.text || "",
                    block.id,
                    mentions,
                    citations,
                    effectiveCitationIndex,
                    entityResolver
                )}</h3>`;

            case "figure":
                return `
<figure>
<img src="${escapeHtml(block.src || "")}" alt="${escapeHtml(block.alt || "")}">
${block.caption ? `<figcaption>${escapeHtml(block.caption)}</figcaption>` : ""}
</figure>`;

            case "list":
                return `
<ul>
${(block.items || []).map(
    item => `<li>${escapeHtml(item)}</li>`
).join("\n")}
</ul>`;

            case "table":
                return `
<table>
${(block.rows || []).map(
    row => `<tr>${row.map(
        cell => `<td>${escapeHtml(cell)}</td>`
    ).join("")}</tr>`
).join("\n")}
</table>`;

            default:
                throw new Error(`Unsupported article content block: ${block.type}`);
        }
    }

    function renderArticleContentInto(
        target,
        sections,
        mentions,
        sources,
        citations,
        citationIndex,
        entityResolver
    ) {
        if (!target || typeof target.innerHTML !== "string") {
            throw new TypeError("Article renderer target must be a DOM element");
        }

        target.innerHTML = renderArticleContent(
            sections,
            mentions,
            sources,
            citations,
            citationIndex,
            entityResolver
        );
    }

    function renderArticleContent(
        sections,
        mentions,
        sources,
        citations,
        citationIndex,
        entityResolver
    ) {
        if (!Array.isArray(sections)) {
            throw new TypeError("Article sections must be an array");
        }

        const effectiveCitationIndex =
            citationIndex ||
            global.PrivateCapitalCitationRenderer.buildCitationIndex(
                sections,
                citations
            );

        return sections.map(section => {
            const content = Array.isArray(section.content)
                ? section.content
                : [];

            const renderedContent = content
                .map(block =>
                    renderBlock(
                        block,
                        mentions,
                        citations,
                        effectiveCitationIndex,
                        entityResolver
                    )
                )
                .join("\n");

            return renderedContent;
        }).join("\n");
    }

    global.renderArticleContent = renderArticleContent;
    global.renderArticleContentInto = renderArticleContentInto;
})(typeof window !== "undefined" ? window : globalThis);
