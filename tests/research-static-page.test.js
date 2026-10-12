const fs = require("fs");
const assert = require("assert");

const html = fs.readFileSync(
    "articles/private-capital.html",
    "utf8"
);

assert(
    /<title>[^<]+<\/title>/s.test(html),
    "static research page must contain a title"
);

assert(
    (html.match(/<h1\b/g) || []).length === 1,
    "static research page must contain exactly one H1"
);

assert(
    html.includes(
        '<link rel="canonical" href="https://privatecapital.ir/articles/private-capital.html">'
    ),
    "static research page must contain the canonical URL"
);

assert(
    html.includes(
        '<script type="application/ld+json">'
    ),
    "static research page must contain Article JSON-LD"
);

const sectionIds = [
    "introduction",
    "definition-and-scope",
    "main-blocks",
    "private-equity",
    "private-credit",
    "real-assets",
    "conclusion"
];

for (const sectionId of sectionIds) {
    assert(
        new RegExp(
            `data-article-renderer-section="${sectionId}"[^>]*>[\\s\\S]+</`
        ).test(html),
        `${sectionId} must contain static rendered content`
    );
}

assert(
    !new RegExp(
        'data-article-renderer-section="(?:' +
        sectionIds.join("|") +
        ')">\\s*</'
    ).test(html),
    "static research page must not contain empty section placeholders"
);

const expectedSemanticLinks = [
    "/atlas/concept/private-capital/",
    "/atlas/concept/private-equity/",
    "/atlas/concept/private-credit/",
    "/atlas/concept/real-assets/",
    "/atlas/concept/venture-capital/",
    "/atlas/concept/growth-capital/"
];

for (const url of expectedSemanticLinks) {
    assert(
        html.includes(`href="${url}"`),
        `static research page must contain semantic link ${url}`
    );
}

const articleBody = html.replace(/<aside class="explore-rail"[\s\S]*?<\/aside>/g, "");
const conceptLinks = articleBody.match(/href="\/atlas\/concept\/[^"]+\/"/g) || [];
assert(
    conceptLinks.length === 9,
    "static research page must contain exactly 9 concept semantic link occurrences"
);

assert(
    new Set(conceptLinks).size === 6,
    "static research page must contain exactly 6 unique concept semantic links"
);

for (const citationId of [
    "citation-source-1",
    "citation-source-2",
    "citation-source-3"
]) {
    assert(
        html.includes(`id="${citationId}"`),
        `static research page must contain ${citationId}`
    );
}

assert(
    html.includes("../assets/js/article-page.js"),
    "runtime article enhancement must remain available"
);

const connections = html.match(
    /<div data-research-connections>([\s\S]*?)<\/div><!-- research-connections -->/
);
assert(connections, "static Research connections target must exist");
assert(
    connections[1].includes('href="/articles/what-is-private-equity.html"'),
    "curated related Research must link to its published page"
);
assert(
    expectedSemanticLinks.every(url => connections[1].includes(`href="${url}"`)),
    "Approved PUBLISHED Entity refs must remain discoverable in the context panel"
);

for (const slug of ["private-capital","private-capital-research"]) {
    const page=fs.readFileSync(`articles/${slug}.html`,"utf8");
    assert.strictEqual((page.match(/data-research-exploration/g)||[]).length,1);
    assert(page.includes('class="research-article-header"'));
    assert(page.includes('class="research-bibliography research-endmatter"'));
    assert(!page.includes('<sup class="citation"'));
    assert(page.includes('src="/assets/js/research-notes.js"'));
    const other=slug==="private-capital"?"private-capital-research":"private-capital";
    const rail=page.split('<aside class="explore-rail"')[1].split('</aside>')[0];
    assert(rail.includes(`href="/articles/${other}.html"`),"the two approved articles must cross-link in exploration");
    assert(!rail.includes(`href="/articles/${slug}.html"`),"exploration must not link to the current article");
    const tocTargets=[...page.matchAll(/href="#(research-section-[^"]+)"/g)].map(m=>m[1]);
    assert(tocTargets.length>0);
    for (const target of tocTargets) assert(page.includes(`id="${target}"`));
}
const newPage=fs.readFileSync("articles/private-capital-research.html","utf8");
assert(newPage.includes("مفهوم، دامنه، تمایز و سازوکار"));
assert(newPage.includes('href="/atlas/concept/private-capital/'),"new page must link to its approved primary Entity");
const entities=JSON.parse(fs.readFileSync("atlas/entities/index.json","utf8")).entities;
for (const e of entities.filter(e=>e.lifecycleStatus!=="PUBLISHED" && e.type==="Concept")) {
    const url=`/atlas/concept/${e.id.split(":")[1]}/`;
    assert(!html.includes(`href="${url}"`) && !newPage.includes(`href="${url}"`),
      `${e.id}: non-public concepts must not gain Research links`);
}
assert.strictEqual((newPage.match(/class="research-note-ref"/g)||[]).length,20);
// Stage 6 builds discovery from the approved registry into the public artifact.
const generatedHome = require("node:child_process").execFileSync("python", ["-B", "-c",
    "from pathlib import Path;import sys;sys.path.insert(0,'tools');import search;sys.stdout.buffer.write(search.files(Path('.').resolve())['articles.html'])"], {encoding:"utf8"});
assert(generatedHome.includes('href="/articles/private-capital-research.html"'));
assert(fs.readFileSync("sitemap.xml","utf8").includes('https://privatecapital.ir/articles/private-capital-research.html'));
console.log("Research static HTML contract PASSED");
