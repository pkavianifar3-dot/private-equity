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

    function entityURL(entityId) {
        if (typeof entityId !== "string" || !entityId.includes(":")) {
            return null;
        }

        const type = entityId.split(":")[0];

        switch (type) {
            case "person":
                return `../atlas/person.html?id=${encodeURIComponent(entityId)}`;

            case "organization":
                return `../atlas/organization.html?id=${encodeURIComponent(entityId)}`;

            case "investment":
                return `../atlas/investment.html?id=${encodeURIComponent(entityId)}`;

            case "concept":
                return `../atlas/concept.html?id=${encodeURIComponent(entityId)}`;

            default:
                return null;
        }
    }

    function renderTextWithMentions(text, blockId, mentions) {
        const value = String(text || "");

        if (!Array.isArray(mentions) || !mentions.length) {
            return escapeHtml(value);
        }

        const applicableMentions = mentions
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
                url: entityURL(mention.entityRef)
            }))
            .filter(mention => mention.url);

        if (!applicableMentions.length) {
            return escapeHtml(value);
        }

        applicableMentions.sort((a, b) => a.start - b.start);

        const parts = [];
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

        parts.push(escapeHtml(value.slice(cursor)));

        return parts.join("");
    }

    function renderBlock(block, mentions) {
        switch (block.type) {
            case "paragraph":
                return `<p>${renderTextWithMentions(
                    block.text || "",
                    block.id,
                    mentions
                )}</p>`;

            case "subheading":
                return `<h3>${renderTextWithMentions(
                    block.text || "",
                    block.id,
                    mentions
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

    function renderArticleContentInto(target, sections, mentions) {
        if (!target || typeof target.innerHTML !== "string") {
            throw new TypeError("Article renderer target must be a DOM element");
        }

        target.innerHTML = renderArticleContent(sections, mentions);
    }

    function renderArticleContent(sections, mentions) {
        if (!Array.isArray(sections)) {
            throw new TypeError("Article sections must be an array");
        }

        return sections.map(section => {
            const content = Array.isArray(section.content)
                ? section.content
                : [];

            return content
                .map(block => renderBlock(block, mentions))
                .join("\n");
        }).join("\n");
    }

    global.renderArticleContent = renderArticleContent;
    global.renderArticleContentInto = renderArticleContentInto;
})(typeof window !== "undefined" ? window : globalThis);
