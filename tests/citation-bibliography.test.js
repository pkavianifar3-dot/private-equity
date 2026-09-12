const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const context = { window: {} };
vm.createContext(context);

vm.runInContext(
    fs.readFileSync("assets/js/research/citation-renderer.js", "utf8"),
    context
);

const renderer = context.window.PrivateCapitalCitationRenderer;

const citations = [
    {
        id: "citation:a1",
        sourceRef: "source:a",
        contentBlockId: "b",
        start: 0,
        end: 2
    },
    {
        id: "citation:a2",
        sourceRef: "source:a",
        contentBlockId: "b",
        start: 3,
        end: 5
    },
    {
        id: "citation:b1",
        sourceRef: "source:b",
        contentBlockId: "b",
        start: 6,
        end: 8
    }
];

const sources = [
    {
        id: "source:a",
        title_fa: "منبع اول",
        publisher: "ناشر اول",
        url: "https://example.com/a"
    },
    {
        id: "source:b",
        title_fa: "منبع دوم",
        publisher: "ناشر دوم",
        url: "https://example.com/b"
    }
];

const index = new Map([
    ["source:a", 1],
    ["source:b", 2]
]);

const html = renderer.renderCitationBibliographyHtml(
    citations,
    sources,
    index
);

assert.strictEqual(
    (html.match(/id="citation-source-1"/g) || []).length,
    1
);

assert(html.includes('id="citation-source-2"'));
assert(html.includes('href="#citation-location-citation:a1"'));
assert(html.includes('href="#citation-location-citation:a2"'));
assert(html.includes('href="#citation-location-citation:b1"'));
assert(html.indexOf("[1]") < html.indexOf("[2]"));

console.log("Citation bibliography HTML contract PASSED");
