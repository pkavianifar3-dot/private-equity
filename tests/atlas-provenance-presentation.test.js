const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const window = {
    location: { pathname: "/atlas/" },
    PrivateCapitalURL: { entityURL: () => "" },
    PrivateCapitalDataLoader: { create: () => ({}) }
};
vm.runInNewContext(
    fs.readFileSync("assets/js/core/provenance-renderer.js", "utf8"),
    { window }
);
const atlas = fs.readFileSync("assets/js/atlas.js", "utf8")
    .replace(/\}\)\(\);\s*$/, `
        window.__renderEvidenceSection = renderEvidenceSection;
        window.__renderOverviewLink = renderOverviewLink;
        relationContract = {
            relationTypes: {
                relation_types: [{ id: "INCLUDES", label_fa: "شامل" }]
            }
        };
    })();`);
vm.runInNewContext(atlas, { window });
assert.strictEqual(typeof window.__renderEvidenceSection, "function");

const claims = [
    { id: "claim:a", subject: "subject:a", predicate: "INCLUDES", object: "object:b", status: "SUPPORTED", confidence: "HIGH", evidenceRefs: ["evidence:a", "evidence:a2"] },
    { id: "claim:b", subject: "subject:a", predicate: "INCLUDES", object: "object:c", status: "SUPPORTED", confidence: "HIGH", evidenceRefs: ["evidence:b"] }
];
const evidence = { evidence: [
    { id: "evidence:a", claimRef: "claim:a", sourceRef: "source:shared", evidenceType: "authoritative_publication", strength: "strong" },
    { id: "evidence:a2", claimRef: "claim:a", sourceRef: "source:shared", evidenceType: "authoritative_publication", strength: "strong" },
    { id: "evidence:b", claimRef: "claim:b", sourceRef: "source:shared", evidenceType: "authoritative_publication", strength: "strong" }
] };
const sources = { sources: [
    { id: "source:shared", title_fa: "مرجع مشترک", publisher: "ناشر", url: "https://example.com/shared" },
    { id: "source:content", title_fa: "منبع متن", url: "https://example.com/content" }
] };
const entities = {
    "subject:a": { name: { fa: "سرمایه خصوصی" } },
    "object:b": { name: { fa: "سهام خصوصی" } },
    "object:c": { name: { fa: "اعتبار خصوصی" } }
};
const html = window.__renderEvidenceSection(claims, evidence, sources, entities);

const count = needle => html.split(needle).length - 1;
assert.strictEqual(count('<section class="atlas-section atlas-provenance-section">'), 1);
assert.strictEqual(count('class="card atlas-evidence-group atlas-provenance-card"'), 2);
assert.strictEqual(count('id="claim-claim:a"'), 1);
assert.strictEqual(count('class="atlas-evidence-item"'), 3);
const condensed = html.replace(/\s+/g, " ");
assert.match(condensed, /<div class="atlas-evidence-header"> <a class="atlas-source-ref" href="#source-source:shared" aria-label="[^"]+"><bdi dir="ltr">\[1\]<\/bdi><\/a> <strong>[^<]+<\/strong> <\/div>/);
assert.strictEqual(count('class="atlas-provenance-source-heading"'), 3);
assert.match(condensed, /class="atlas-provenance-source-title"><a [^>]*>[^<]+<\/a><\/div> <span class="atlas-source-number"><bdi dir="ltr">\[1\]<\/bdi><\/span>/);
assert(!html.includes("منبع ["));
assert.strictEqual(count('id="source-source:shared"'), 1, "shared source anchor must be unique");
assert.strictEqual(count('class="atlas-provenance-source-title"'), 3, "source details appear once per claim plus text source");
assert.strictEqual(count('id="source-source:content"'), 1, "content-only source must have an anchor");
assert.strictEqual(count("\u0645\u0631\u062c\u0639 \u0645\u0634\u062a\u0631\u06a9"), 2, "source detail appears once in each claim");
assert(html.includes("سرمایه خصوصی شامل سهام خصوصی"), "claim title must be human readable");
assert(html.includes("نوع شاهد: انتشار مرجع معتبر"));
assert(html.includes("اعتبار: اعتبار بالا"));
assert(html.includes('شناسه شاهد: <bdi dir="ltr">evidence:a</bdi>'), "evidence ID must be secondary metadata");
assert(!html.includes("authoritative_publication"));
assert(!html.includes("قدرت: strong"));
assert(html.includes('class="atlas-provenance-extras"'), "content-only source must remain in the section");
assert.strictEqual(count('class="atlas-provenance-technical"'), 2);
assert.strictEqual(count('class="atlas-provenance-sources"'), 2);
assert(html.includes('\u062c\u0632\u0626\u06cc\u0627\u062a \u0641\u0646\u06cc'));
assert(html.includes('href="#source-source:shared"'));
assert(window.__renderOverviewLink(claims[0], evidence.evidence, sources.sources).includes('\u06f2 \u0634\u0627\u0647\u062f \u00b7 \u06f1 \u0645\u0646\u0628\u0639'));
assert(window.__renderOverviewLink(claims[0], evidence.evidence, sources.sources).includes('href="#claim-claim:a"'));
assert.strictEqual(window.__renderOverviewLink({ id: "claim:none", evidenceRefs: [] }, evidence.evidence, sources.sources), "");
assert.strictEqual(
    window.__renderEvidenceSection([], { evidence: [] }, { sources: [] }, {}),
    "",
    "empty provenance should not create an empty section"
);
console.log("Atlas provenance presentation PASSED");
