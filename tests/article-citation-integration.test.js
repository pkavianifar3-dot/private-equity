const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const context = {
    window: {
        PrivateCapitalURL: {
            entityURL: () => "/atlas/concept.html"
        }
    }
};

vm.createContext(context);

vm.runInContext(
    fs.readFileSync("assets/js/research/citation-renderer.js", "utf8"),
    context
);

vm.runInContext(
    fs.readFileSync("assets/js/article-renderer.js", "utf8"),
    context
);

const section = {
    id: "b",
    content: [
        {
            id: "b",
            type: "paragraph",
            text: "سرمایه‌گذاری خصوصی معتبر"
        }
    ],
    mentions: [
        {
            id: "m",
            text: "سرمایه‌گذاری خصوصی",
            entityRef: "concept:private-equity",
            contentBlockId: "b",
            start: 0,
            end: 18,
            resolutionStatus: "RESOLVED"
        }
    ]
};

const citations = [
    {
        id: "citation:test",
        sourceRef: "source:test",
        contentBlockId: "b",
        start: 19,
        end: 24
    }
];

const citationIndex =
    context.window.PrivateCapitalCitationRenderer.buildCitationIndex(
        [section],
        citations
    );

const html = context.window.renderArticleContent(
    [section],
    section.mentions,
    [],
    citations,
    citationIndex
);

assert(html.includes("[1]"));
assert(html.includes("#citation-source-1"));
assert(html.includes("/atlas/concept.html"));
assert(html.includes("سرمایه‌گذاری خصوصی"));
assert(html.includes("معتبر"));

console.log("Mention + Citation integration contract PASSED");
