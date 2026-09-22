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

const conceptLinks = html.match(/href="\/atlas\/concept\/[^"]+\/"/g) || [];
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

console.log("Research static HTML contract PASSED");
