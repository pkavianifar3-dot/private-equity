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

function renderResearch(research, entities, sourceIndex) {
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
            entities,
            global.PrivateCapitalURL
        );

    const citationIndex =
        global.PrivateCapitalCitationRenderer.buildCitationIndex(
            research.sections,
            citations
        );

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
                entityResolver
            )
        );
    }

    const citationSourceRefs = unique(
        citations
            .map(citation => citation && citation.sourceRef)
            .filter(Boolean)
    );

    const citationSources =
        loadSources(citationSourceRefs, sourceIndex);

    const bibliography =
        global.PrivateCapitalCitationRenderer
            .renderCitationBibliographyHtml(
                citations,
                citationSources,
                citationIndex
            );

    return {
        renderedSections,
        bibliography
    };
}

function replaceSection(html, sectionId, renderedHtml) {
    const escapedId = sectionId.replace(
        /[.*+?^${}()|[\]\\]/g,
        "\\$&"
    );

    const pattern = new RegExp(
        `<([A-Za-z][\\w:-]*)\\s+data-article-renderer-section="${escapedId}"[^>]*>[\\s\\S]*?<\\/\\1>`,
        "m"
    );

    if (!pattern.test(html)) {
        throw new Error(
            `Static article render target not found: ${sectionId}`
        );
    }

    return html.replace(
        pattern,
        `<div data-article-renderer-section="${sectionId}">${renderedHtml}</div>`
    );
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
    const sections = research.sections.map(section =>
        `<h2>${escapeHtml(section.title?.fa)}</h2><div data-article-renderer-section="${escapeHtml(section.id)}"></div>`
    ).join("\n");
    return `<!doctype html>\n<html lang="fa" dir="rtl"><head><meta charset="utf-8">` +
        `<meta name="viewport" content="width=device-width,initial-scale=1">` +
        `<title>${escapeHtml(research.title?.fa)} | Private Capital</title>` +
        `<meta name="description" content="${escapeHtml(research.summary?.fa)}">` +
        `<link rel="stylesheet" href="/assets/css/style.css"></head><body>` +
        `<header><nav><a href="/">Private Capital</a><a href="/articles.html">پژوهش‌ها</a><a href="/atlas/">اطلس</a></nav></header>` +
        `<main class="container"><article><h1>${escapeHtml(research.title?.fa)}</h1>` +
        `<p>${escapeHtml(research.summary?.fa)}</p>${sections}` +
        `<div data-article-renderer-citations></div><br></article></main>` +
        `<script src="/assets/js/main.js"></script></body></html>\n`;
}

function copyPackageAssets(researchPath, research, collisionMap) {
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
        const dest = path.resolve(ROOT, `.${url}`), bytes = fs.readFileSync(source);
        if (collisionMap.has(dest) && !collisionMap.get(dest).equals(bytes))
            throw new Error(`${source}: public asset collision at ${url}`);
        collisionMap.set(dest, bytes);
        fs.mkdirSync(path.dirname(dest),{recursive:true});
        if (!fs.existsSync(dest) || !fs.readFileSync(dest).equals(bytes)) fs.writeFileSync(dest,bytes);
    }
}

function buildArticle(researchPath, entities, sourceIndex, collisionMap = new Map()) {
    const research = loadJson(researchPath);

    if (research.type !== "Research") {
        return null;
    }

    if (research.status !== "PUBLISHED") {
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

    const outputPath = path.resolve(
        ROOT,
        `.${research.url}`
    );

    if (!outputPath.startsWith(path.join(ROOT,"articles") + path.sep) ||
        path.extname(outputPath) !== ".html" || research.url.includes("..") ||
        research.url.includes("\\")) throw new Error(`${researchPath}: unsafe Research URL`);
    copyPackageAssets(researchPath,research,collisionMap);
    const originalHtml = fs.existsSync(outputPath)
        ? fs.readFileSync(outputPath,"utf8") : createShell(research);

    const newline =
        originalHtml.includes("\r\n")
            ? "\r\n"
            : "\n";

    const rendered =
        renderResearch(
            research,
            entities,
            sourceIndex
        );

    let html = originalHtml;

    for (const section of research.sections) {
        const sectionHtml =
            rendered.renderedSections.get(section.id)
                .replace(/[ \t]+(?=\r?\n)/g, "");

        if (typeof sectionHtml !== "string") {
            throw new Error(
                `Section was not rendered: ${section.id}`
            );
        }

        html = replaceSection(
            html,
            section.id,
            sectionHtml
        );
    }

    html = replaceCitationBibliography(
        html,
        rendered.bibliography.replace(/[ \t]+(?=\r?\n)/g, "")
    );

    html = html.replace(
        /\r?\n/g,
        newline
    );

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

function generate() {
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
    const collisions = new Map();
    for (const {file} of records) {
        const result =
            buildArticle(
                file,
                entities,
                sourceIndex,
                collisions
            );

        if (!result) {
            continue;
        }

        console.log(
            `${result.changed ? "Generated" : "Unchanged"} ${path.relative(ROOT, result.outputPath)} (${result.sections} sections, ${result.mentions} mentions).`
        );
    }
}

module.exports = { createShell, buildArticle, generate };

if (require.main === module) {
    generate();
}
