const fs = require("fs");
const path = require("path");
const vm = require("vm");

const ROOT = path.resolve(__dirname, "../..");
const { discover } = require("./research-package");

function loadJson(filePath) {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function loadScript(relativePath) {
    const filePath = path.join(ROOT, relativePath);
    vm.runInThisContext(
        fs.readFileSync(filePath, "utf8"),
        { filename: filePath }
    );
}

function loadRuntime() {
    global.window = global;

    loadScript("assets/js/core/url-resolver.js");
    loadScript("assets/js/core/entity-resolver.js");
    loadScript("assets/js/research/citation-renderer.js");
    loadScript("assets/js/article-renderer.js");
}

function loadSources(sourceRefs, sourceIndex) {
    if (!Array.isArray(sourceRefs) || !sourceRefs.length) {
        return [];
    }

    const sources = [];

    for (const sourceRef of sourceRefs) {
        const fileName = sourceIndex.sources?.[sourceRef];

        if (!fileName) {
            throw new Error(
                `Missing source index entry: ${sourceRef}`
            );
        }

        const sourcePath = path.join(
            ROOT,
            "atlas",
            "sources",
            fileName
        );

        const data = loadJson(sourcePath);
        const source = (data.sources || [])
            .find(item => item.id === sourceRef);

        if (!source) {
            throw new Error(
                `Missing source record: ${sourceRef}`
            );
        }

        sources.push(source);
    }

    return sources;
}

function unique(values) {
    return [...new Set(values.filter(Boolean))];
}

function collectSectionSourceRefs(section, citations) {
    const blockIds = new Set(
        (Array.isArray(section.content) ? section.content : [])
            .map(block => block && block.id)
            .filter(Boolean)
    );

    const citationSourceRefs = Array.isArray(citations)
        ? citations
            .filter(
                citation =>
                    citation &&
                    blockIds.has(citation.contentBlockId)
            )
            .map(citation => citation.sourceRef)
        : [];

    return unique([
        ...(Array.isArray(section.sourceRefs)
            ? section.sourceRefs
            : []),
        ...citationSourceRefs
    ]);
}

function renderResearch(research, entities, sourceIndex, options = {}) {
    if (!research || !Array.isArray(research.sections)) {
        throw new TypeError(
            "Research sections must be an array"
        );
    }

    const citations = Array.isArray(research.citations)
        ? research.citations
        : [];

    const entityResolver =
        global.PrivateCapitalEntityResolver.create(
            // Public articles resolve only approved PUBLISHED Entities.
            // Preview retains the complete canonical inventory.
            options.preview ? entities :
                {...entities, entities: (entities.entities || []).filter(entity => entity.lifecycleStatus === "PUBLISHED")},
            global.PrivateCapitalURL
        );

    const citationIndex =
        global.PrivateCapitalCitationRenderer.buildCitationIndex(
            research.sections,
            citations
        );
    for (const sourceRef of research.sourceRefs || []) {
        if (!citationIndex.has(sourceRef)) citationIndex.set(sourceRef, citationIndex.size + 1);
    }

    const renderOptions = {
        mentionLinkPolicy: research.presentation?.mentionLinkPolicy,
        referenceStyle: research.presentation?.referenceStyle
    };
    const renderedSections = new Map();

    for (const section of research.sections) {
        const sectionSourceRefs =
            collectSectionSourceRefs(section, citations);

        const sources =
            loadSources(sectionSourceRefs, sourceIndex);

        renderedSections.set(
            section.id,
            global.renderArticleContent(
                [section],
                Array.isArray(section.mentions)
                    ? section.mentions
                    : [],
                sources,
                citations,
                citationIndex,
                entityResolver,
                renderOptions
            )
        );
    }

    const citationSourceRefs = unique([
        ...citations.map(citation => citation && citation.sourceRef),
        ...(Array.isArray(research.sourceRefs) ? research.sourceRefs : [])
    ]);

    const citationSources =
        loadSources(citationSourceRefs, sourceIndex);

    const bibliography =
        global.PrivateCapitalCitationRenderer
            .renderCitationBibliographyHtml(
                citations,
                citationSources,
                citationIndex,
                renderOptions
            );

    return {
        renderedSections,
        notes: global.renderArticleNotes(research.sections, citations, citationIndex, entityResolver, renderOptions),
        bibliography
    };
}

function replaceSection(html, sectionId, renderedHtml) {
    const escapedId = sectionId.replace(
        /[.*+?^${}()|[\]\\]/g,
        "\\$&"
    );

    const pattern = new RegExp(
        `<div\\s+data-article-renderer-section="${escapedId}"[^>]*>`, "m"
    );
    const match = pattern.exec(html);
    if (!match) throw new Error(`Static article render target not found: ${sectionId}`);
    const tags = /<\/?div\b[^>]*>/g;
    tags.lastIndex = match.index + match[0].length;
    let depth = 1, tag;
    while ((tag = tags.exec(html))) {
        depth += tag[0].startsWith("</") ? -1 : 1;
        if (!depth) return html.slice(0, match.index) +
            `<div data-article-renderer-section="${sectionId}">${renderedHtml}</div>` + html.slice(tags.lastIndex);
    }
    throw new Error(`Unclosed static article render target: ${sectionId}`);
}

function replaceCitationBibliography(html, bibliography) {
    const pattern =
        /<div\s+data-article-renderer-citations[^>]*>[\s\S]*<\/div>(?=\s*<br>)/m;

    if (!pattern.test(html)) {
        throw new Error(
            "Static article citation render target not found"
        );
    }

    return html.replace(
        pattern,
        `<div data-article-renderer-citations>${bibliography}</div>`
    );
}

function escapeHtml(value) {
    return String(value || "").replace(/[&<>"']/g, char =>
        ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
}

function createShell(research) {
    const title = escapeHtml(research.title?.fa);
    const summary = escapeHtml(research.summary?.fa);
    const url = escapeHtml(research.url);
    const presentation = research.presentation || {};
    const author = presentation.byline ?
        `<div class="article-author research-byline">${presentation.portraitSrc ?
            `<img src="${escapeHtml(presentation.portraitSrc)}" alt="${escapeHtml(presentation.byline)}" width="48" height="48">` : ""}` +
        `<p><strong>نویسنده:</strong> ${escapeHtml(presentation.byline)}</p></div>` : "";
    const cover = presentation.coverSrc ?
        `<figure class="research-cover"><img src="${escapeHtml(presentation.coverSrc)}" ` +
        `alt="${escapeHtml(presentation.coverAlt || "")}"></figure>` : "";
    const opening = `<div class="research-opening"><p class="research-summary">${summary}</p>${cover}</div>`;
    const sections = research.sections.map(section =>
        `<section class="research-section"><h2>${escapeHtml(section.title?.fa)}</h2><div data-article-renderer-section="${escapeHtml(section.id)}"></div></section>`
    ).join("\n");
    const jsonLd = JSON.stringify({"@context":"https://schema.org","@type":"Article",
        headline:research.title?.fa,description:research.summary?.fa,
        mainEntityOfPage:`https://privatecapital.ir${research.url}`}).replace(/</g,"\\u003c");
    return `<!DOCTYPE html>\n<html lang="fa" dir="rtl"><head><meta charset="UTF-8">` +
        `<meta name="viewport" content="width=device-width, initial-scale=1">` +
        `<title>${title} | Private Capital</title><meta name="description" content="${summary}">` +
        `<link rel="canonical" href="https://privatecapital.ir${url}">` +
        `<link rel="stylesheet" href="/assets/css/style.css">` +
        `<link rel="icon" href="/assets/images/favicon.ico">` +
        `<script type="application/ld+json">${jsonLd}</script></head><body>` +
        `<header><div class="container"><div class="logo">Private Capital</div>` +
        `<nav><a href="/">خانه</a><a href="/watch.html">دیده‌بان</a>` +
        `<a href="/articles.html">پژوهش‌ها</a><a href="/atlas/">اطلس</a>` +
        `<a href="/services.html">خدمات</a><a href="/membership.html">عضویت ویژه</a>` +
        `<a href="/about.html">درباره ما</a><a href="/contact.html">تماس</a></nav></div></header>` +
        `<main><section class="research-page-section"><div class="container">` +
        `<div class="research-article-header"><h1>${title}</h1>${author}<hr></div>` +
        `<article>${opening}${sections}<div data-article-renderer-citations></div><br>` +
        `<div data-research-connections></div><!-- research-connections -->` +
        `</article></div></section></main>` +
        `<script src="/assets/js/research-notes.js"></script>` +
        `</body></html>\n`;
}

function copyPackageAssets(researchPath, research, collisionMap, destinationRoot = ROOT) {
    const assetDir = path.join(path.dirname(researchPath), "assets");
    if (!fs.existsSync(assetDir)) return;
    for (const file of fs.readdirSync(assetDir).sort()) {
        const source = path.join(assetDir,file);
        if (!fs.statSync(source).isFile()) throw new Error(`${source}: nested asset path unsupported`);
        const images = research.sections.flatMap(section => section.content || [])
            .filter(block => block.type === "figure" && path.basename(block.src || "") === file);
        if (!images.length || images.some(image => image.src !== images[0].src))
            throw new Error(`${source}: expected one public figure path`);
        const url = new URL(images[0].src, `https://local.invalid${research.url}`).pathname;
        if (!url.startsWith("/assets/images/") || url.includes(".."))
            throw new Error(`${source}: unsafe public asset path ${url}`);
        const dest = path.resolve(destinationRoot, `.${url}`), bytes = fs.readFileSync(source);
        if (collisionMap.has(dest) && !collisionMap.get(dest).equals(bytes))
            throw new Error(`${source}: public asset collision at ${url}`);
        collisionMap.set(dest, bytes);
        fs.mkdirSync(path.dirname(dest),{recursive:true});
        if (!fs.existsSync(dest) || !fs.readFileSync(dest).equals(bytes)) fs.writeFileSync(dest,bytes);
    }
}

function buildArticle(researchPath, entities, sourceIndex, collisionMap = new Map(), options = {}) {
    const research = loadJson(researchPath);

    if (research.type !== "Research") {
        return null;
    }

    const entry = options.registry?.get(research.id);
    if (!entry || entry.url !== research.url || entry.status !== research.status) {
        throw new Error(`${researchPath}: ${research.id}: registry URL/status mismatch`);
    }
    if (options.preview ? research.status !== "REVIEW" : research.status !== "PUBLISHED") {
        return null;
    }

    if (
        typeof research.url !== "string" ||
        !research.url.startsWith("/articles/")
    ) {
        throw new Error(
            `Research article URL is invalid: ${researchPath}`
        );
    }

    if (research.primaryEntityRef !== undefined &&
        (typeof research.primaryEntityRef !== "string" ||
         !(research.entityRefs || []).includes(research.primaryEntityRef) ||
         !(entities.entities || []).some(entity => entity.id === research.primaryEntityRef))) {
        throw new Error(`${researchPath}: ${research.id}: primaryEntityRef must resolve and be in article entityRefs`);
    }

    const destinationRoot = options.preview ? path.resolve(options.preview) : options.outputRoot ? path.resolve(options.outputRoot) : ROOT;
    if (options.preview && (destinationRoot === ROOT || destinationRoot.startsWith(ROOT + path.sep))) {
        throw new Error(`${researchPath}: preview output must be outside the repository`);
    }
    const outputPath = path.resolve(destinationRoot,
        options.preview ? `./__preview${research.url}` : `.${research.url}`);

    if (!outputPath.startsWith(path.join(destinationRoot, options.preview ? "__preview/articles" : "articles") + path.sep) ||
        path.extname(outputPath) !== ".html" || research.url.includes("..") ||
        research.url.includes("\\")) throw new Error(`${researchPath}: unsafe Research URL`);
    const originalHtml = !options.preview && fs.existsSync(outputPath)
        ? fs.readFileSync(outputPath,"utf8") : createShell(research);

    const newline =
        originalHtml.includes("\r\n")
            ? "\r\n"
            : "\n";

    const rendered =
        renderResearch(
            research,
            entities,
            sourceIndex,
            options
        );

    let html = originalHtml;

    for (const section of research.sections) {
        let sectionHtml =
            rendered.renderedSections.get(section.id)
                .replace(/[ \t]+(?=\r?\n)/g, "");

        if (typeof sectionHtml !== "string") {
            throw new Error(
                `Section was not rendered: ${section.id}`
            );
        }

        if (research.presentation?.referenceStyle === "inline-collapsible" && section.id === "introduction") {
            const cover = sectionHtml.match(/<figure>[\s\S]*?<\/figure>/);
            if (cover) sectionHtml = '<div class="research-opening explore-lead"><div class="explore-lead-text">' +
                sectionHtml.replace(cover[0], "") + '</div>' +
                cover[0].replace('<figure>', '<figure class="research-cover explore-lead-media">') + '</div>';
        }
        html = replaceSection(
            html,
            section.id,
            sectionHtml
        );
    }

    html = replaceCitationBibliography(
        html,
        (rendered.notes + rendered.bibliography).replace(/[ \t]+(?=\r?\n)/g, "")
    );

    html = html.replace(
        /\r?\n/g,
        newline
    );

    if (options.preview) {
        html = html.replace(`<link rel="canonical" href="https://privatecapital.ir${escapeHtml(research.url)}">`,
            '<meta name="robots" content="noindex,nofollow">');
    }
    // Render and validate all sections/sources before writing any assets or HTML.
    copyPackageAssets(researchPath,research,collisionMap,destinationRoot);
    if (html !== originalHtml || !fs.existsSync(outputPath)) {
        fs.mkdirSync(path.dirname(outputPath), { recursive: true });
        fs.writeFileSync(
            outputPath,
            html,
            "utf8"
        );
    }

    return {
        outputPath,
        sections: research.sections.length,
        mentions: research.sections
            .flatMap(section => section.mentions || [])
            .length,
        changed: html !== originalHtml
    };
}

function generate(options = {}) {
    loadRuntime();

    const entities =
        loadJson(
            path.join(
                ROOT,
                "atlas",
                "entities",
                "index.json"
            )
        );

    const sourceIndex =
        loadJson(
            path.join(
                ROOT,
                "atlas",
                "sources",
                "index.json"
            )
        );

    const records = discover();
    const registry = new Map(loadJson(path.join(ROOT,"research/index.json")).research.map(row => [row.id,row]));
    const collisions = new Map();
    for (const {file} of records) {
        const result =
            buildArticle(
                file,
                entities,
                sourceIndex,
                collisions, {...options,registry}
            );

        if (!result) {
            continue;
        }

        console.log(
            `${result.changed ? "Generated" : "Unchanged"} ${path.relative(ROOT, result.outputPath)} (${result.sections} sections, ${result.mentions} mentions).`
        );
    }
}

module.exports = { createShell, buildArticle, generate, loadRuntime };

if (require.main === module) {
    const previewArg = process.argv.slice(2).find(arg => arg.startsWith("--preview-dir="));
    generate(previewArg ? {preview:previewArg.slice("--preview-dir=".length)} : {});
}
