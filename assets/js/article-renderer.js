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

    function renderBlock(block) {
        switch (block.type) {
            case "paragraph":
                return `<p>${escapeHtml(block.text || "")}</p>`;

            case "subheading":
                return `<h3>${escapeHtml(block.text || "")}</h3>`;

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

    function renderArticleContent(sections) {
        if (!Array.isArray(sections)) {
            throw new TypeError("Article sections must be an array");
        }

        return sections.map(section => {
            const content = Array.isArray(section.content)
                ? section.content
                : [];

            return content.map(renderBlock).join("\n");
        }).join("\n");
    }

    global.renderArticleContent = renderArticleContent;
})(typeof window !== "undefined" ? window : globalThis);
