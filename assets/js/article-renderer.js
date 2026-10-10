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
        entityResolver,
        noteMarkers = [],
        options = {}
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
                        citationIndex,
                        options
                    )
                    : "";

            if (!marker) {
                return;
            }

            const markers = markersByEnd.get(citation.end) || [];
            markers.push(marker);
            markersByEnd.set(citation.end, markers);
        });

        noteMarkers.forEach(note => {
            const markers = markersByEnd.get(note.anchor.offset) || [];
            markers.push(`<sup class="research-note-ref"><a href="#research-note-${escapeHtml(note.id)}" ` +
                `aria-label="یادداشت ${escapeHtml(note.noteNumber)}">${escapeHtml(note.noteNumber)}</a></sup>`);
            markersByEnd.set(note.anchor.offset, markers);
        });

        if (options.referenceStyle === "inline-collapsible") {
            const boundaries = [...new Set([0, value.length,
                ...applicableMentions.flatMap(mention => [mention.start, mention.end]),
                ...markersByEnd.keys()])].sort((a, b) => a - b);
            const output = [...(markersByEnd.get(0) || [])];
            for (let index = 1; index < boundaries.length; index++) {
                const start = boundaries[index - 1], end = boundaries[index];
                const fragment = escapeHtml(value.slice(start, end));
                const mention = applicableMentions.find(item => item.start <= start && item.end >= end &&
                    (typeof item.text !== "string" || item.text === value.slice(item.start, item.end)));
                output.push(mention ? `<a href="${escapeHtml(mention.url)}">${fragment}</a>` : fragment);
                output.push(...(markersByEnd.get(end) || []));
            }
            return output.join("");
        }

        if (options.referenceStyle === "inline-collapsible") {
            const boundaries = [...new Set([0, value.length,
                ...applicableMentions.flatMap(mention => [mention.start, mention.end]),
                ...markersByEnd.keys()])].sort((a, b) => a - b);
            const output = [...(markersByEnd.get(0) || [])];
            for (let index = 1; index < boundaries.length; index++) {
                const start = boundaries[index - 1], end = boundaries[index];
                const fragment = escapeHtml(value.slice(start, end));
                const mention = applicableMentions.find(item => item.start <= start && item.end >= end &&
                    (typeof item.text !== "string" || item.text === value.slice(item.start, item.end)));
                output.push(mention ? `<a href="${escapeHtml(mention.url)}">${fragment}</a>` : fragment);
                output.push(...(markersByEnd.get(end) || []));
            }
            return output.join("");
        }

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
        entityResolver,
        noteMarkers = [],
        options = {}
    ) {
        switch (block.type) {
            case "paragraph":
                return `<p>${renderTextWithMentions(
                    block.text || "",
                    block.id,
                    mentions,
                    citations,
                    effectiveCitationIndex,
                    entityResolver,
                    noteMarkers,
                    options
                )}</p>`;

            case "subheading":
                return `<h${[3,4,5,6].includes(block.level) ? block.level : 3}>${renderTextWithMentions(
                    block.text || "",
                    block.id,
                    mentions,
                    citations,
                    effectiveCitationIndex,
                    entityResolver,
                    noteMarkers,
                    options
                )}</h${[3,4,5,6].includes(block.level) ? block.level : 3}>`;

            case "note":
                // Notes are collected at the end of the article by renderArticleNotes.
                return "";

            case "figure":
                return `
<figure>
<img src="${escapeHtml(block.src || "")}" alt="${escapeHtml(block.alt || "")}">
${block.caption || block.credit ? `<figcaption>${block.credit ? `${block.caption ? `<span class="research-caption">${escapeHtml(block.caption)}</span>` : ""}<span class="figure-credit research-credit">${escapeHtml(block.credit)}</span>` : escapeHtml(block.caption)}</figcaption>` : ""}
</figure>`;

            case "list":
                return `
<${block.ordered ? "ol" : "ul"}>
${(block.items || []).map(
    item => `<li>${escapeHtml(item)}</li>`
).join("\n")}
</${block.ordered ? "ol" : "ul"}>`;

            case "table": {
                const direction = block.direction === "rtl" || block.direction === "ltr" ?
                    ` dir="${block.direction}"` : "";
                const captionId = `research-caption-${escapeHtml(block.id)}`;
                const caption = block.caption || block.credit ?
                    `<div class="research-table-caption" id="${captionId}">${block.caption ?
                        `<span class="research-caption">${escapeHtml(block.caption)}</span>` : ""}${block.credit ?
                        `<span class="research-credit">${escapeHtml(block.credit)}</span>` : ""}</div>` : "";
                const rows = (block.rows || []).map((row, index) =>
                    `<tr>${row.map((cell, column) => {
                        const markers = noteMarkers.filter(note =>
                            note.anchor.row === index && note.anchor.column === column);
                        const cellHtml = markers.length ? renderTextWithMentions(
                            cell, block.id, [], [], effectiveCitationIndex, entityResolver, markers, options
                        ) : escapeHtml(cell);
                        return direction && index === 0 ?
                            `<th scope="col">${cellHtml}</th>` : `<td>${cellHtml}</td>`;
                    }).join("")}</tr>`
                ).join("\n");
                return `${caption}<div class="research-table-scroll"><table${direction}${caption ?
                    ` aria-describedby="${captionId}"` : ""}>\n${rows}\n</table></div>`;
            }

            default:
                throw new Error(`Unsupported article content block: ${block.type}`);
        }
    }

    function renderArticleNotes(sections, citations, citationIndex, entityResolver, options = {}) {
        const notes = (sections || []).flatMap(section =>
            (section.content || []).filter(block => block.type === "note").map(block => {
                const direction = /[\u0600-\u06FF]/.test(block.text || "") ? "rtl" : "ltr";
                return `<li id="research-note-${escapeHtml(block.id)}" value="${escapeHtml(block.noteNumber)}" ` +
                    `dir="${direction}">${renderTextWithMentions(block.text || "", block.id,
                        section.mentions || [], citations, citationIndex, entityResolver, [], options)}</li>`;
            })
        );
        return notes.length ? `<details class="research-notes research-endmatter"><summary>پانوشت‌ها و یادداشت‌ها (${notes.length})</summary>` +
            `<div class="research-panel-body"><ol>${notes.join("\n")}</ol></div></details>` : "";
    }

    function renderArticleContentInto(
        target,
        sections,
        mentions,
        sources,
        citations,
        citationIndex,
        entityResolver,
        options
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
            entityResolver,
            options
        );
    }

    function renderArticleContent(
        sections,
        mentions,
        sources,
        citations,
        citationIndex,
        entityResolver,
        options = {}
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
            const content = Array.isArray(section.content) ? section.content : [];
            const byId = new Map(content.map(block => [block.id, block]));
            const anchoredNotes = new Map();
            for (const note of content.filter(block => block.type === "note" && block.anchor)) {
                const {contentBlockId, offset, row, column} = note.anchor;
                const target = byId.get(contentBlockId);
                const cell = target?.type === "table" && Number.isInteger(row) && Number.isInteger(column) ?
                    target.rows?.[row]?.[column] : undefined;
                const text = target?.type === "paragraph" || target?.type === "subheading" ? target.text : cell;
                if (typeof text !== "string" || !Number.isInteger(offset) || offset < 0 || offset > text.length ||
                    (target?.type === "table" && (row === undefined || column === undefined))) {
                    throw new Error(`Invalid note anchor ${note.id} → ${contentBlockId}`);
                }
                const notes = anchoredNotes.get(contentBlockId) || [];
                notes.push(note);
                anchoredNotes.set(contentBlockId, notes);
            }
            // The editorial policy is scoped to this section. Unroutable or rejected
            // mentions do not consume the one available link for an Entity.
            let selectedMentions = mentions;
            if (options.mentionLinkPolicy === "first-per-section") {
                const order = new Map(content.map((block, index) => [block.id, index]));
                const seen = new Set();
                selectedMentions = (Array.isArray(mentions) ? mentions : [])
                    .slice().sort((a, b) =>
                        (order.get(a.contentBlockId) ?? Infinity) - (order.get(b.contentBlockId) ?? Infinity) ||
                        (a.start ?? Infinity) - (b.start ?? Infinity))
                    .filter(mention => {
                        const block = byId.get(mention.contentBlockId);
                        if (!block || typeof block.text !== "string" ||
                            block.text.slice(mention.start, mention.end) !== mention.text ||
                            mention.resolutionStatus !== "RESOLVED" ||
                            !resolveMention(mention.entityRef, entityResolver) || seen.has(mention.entityRef)) return false;
                        seen.add(mention.entityRef);
                        return true;
                    });
            }
            return content.map((block, index) => {
                if (block.type === "note") return "";
                const rendered = renderBlock(block, selectedMentions, citations,
                    effectiveCitationIndex, entityResolver, anchoredNotes.get(block.id) || [], options);
                const legacyMarkers = [];
                for (let next = index + 1; next < content.length && content[next].type === "note"; next++) {
                    const note = content[next];
                    if (!note.anchor) legacyMarkers.push(`<sup class="research-note-ref"><a href="#research-note-${escapeHtml(note.id)}" ` +
                        `aria-label="یادداشت ${escapeHtml(note.noteNumber)}">${escapeHtml(note.noteNumber)}</a></sup>`);
                }
                if (!legacyMarkers.length) return rendered;
                return block.type === "paragraph" ?
                    rendered.replace(/<\/p>$/, `${legacyMarkers.join("")}</p>`) :
                    rendered + `<span class="research-note-refs">${legacyMarkers.join("")}</span>`;
            }).filter(Boolean).join("\n");
        }).join("\n");
    }

    global.renderArticleContent = renderArticleContent;
    global.renderArticleNotes = renderArticleNotes;
    global.renderArticleContentInto = renderArticleContentInto;
})(typeof window !== "undefined" ? window : globalThis);
