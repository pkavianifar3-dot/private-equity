const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const rendererJS = fs.readFileSync(
    "assets/js/core/provenance-renderer.js",
    "utf8"
);

assert(
    rendererJS.includes("function buildSourceIndex(sourceData)"),
    "provenance renderer must expose buildSourceIndex"
);

assert(
    rendererJS.includes("global.PrivateCapitalProvenanceRenderer"),
    "provenance renderer must expose the public API"
);

assert(
    rendererJS.includes("sourceIndex[source.id] = source"),
    "source index must be keyed by canonical source id"
);

assert(
    !rendererJS.includes("source_refs"),
    "provenance renderer must not use legacy source_refs"
);


const window = {};
vm.runInNewContext(rendererJS, { window });

const sourceA = {
    id: "source:a",
    title_fa: "منبع الف"
};

const sourceB = {
    id: "source:b",
    title_fa: "منبع ب"
};

const index = window.PrivateCapitalProvenanceRenderer.buildSourceIndex({
    sources: [sourceA, sourceB]
});

const references = window.PrivateCapitalProvenanceRenderer.buildSourceReferenceIndex({
    sources: [sourceA, sourceB]
});

assert.strictEqual(
    references.sourceNumbers["source:a"],
    1,
    "first canonical source must receive reference 1"
);

assert.strictEqual(
    references.sourceNumbers["source:b"],
    2,
    "second canonical source must receive reference 2"
);

assert.strictEqual(
    references.sourceIndex["source:a"],
    sourceA,
    "reference index must preserve source records"
);

assert.strictEqual(
    index["source:a"],
    sourceA,
    "source index must preserve the original source record"
);

assert.strictEqual(
    index["source:b"],
    sourceB,
    "source index must resolve each canonical source id"
);

assert.strictEqual(
    index["source:missing"],
    undefined,
    "source index must not fabricate missing sources"
);

assert.strictEqual(
    window.PrivateCapitalProvenanceRenderer.evidenceTypeLabel("authoritative_publication"),
    "انتشار مرجع معتبر",
    "technical evidence types must have readable Persian labels"
);
assert.strictEqual(
    window.PrivateCapitalProvenanceRenderer.evidenceTypeLabel("investment_announcement"),
    "اعلام سرمایه‌گذاری"
);
assert.strictEqual(
    window.PrivateCapitalProvenanceRenderer.strengthLabel("strong"),
    "اعتبار بالا",
    "evidence strength must have a readable Persian label"
);
assert.strictEqual(
    window.PrivateCapitalProvenanceRenderer.evidenceTypeLabel("unknown_type"),
    "نوع شاهد نامشخص",
    "unknown values must not expose raw technical keys"
);

const sourceIds = Array.from(
    window.PrivateCapitalProvenanceRenderer.collectSourceIds(
        [{ sourceRef: "source:b" }, { sourceRef: "source:a" }],
        {
            sections: [
                { paragraphs: [{ sourceRefs: ["source:a", "source:only-content"] }] }
            ]
        }
    )
);
assert.deepStrictEqual(
    sourceIds,
    ["source:a", "source:only-content", "source:b"],
    "content citations and evidence must share ordered, deduplicated sources"
);

console.log("Provenance renderer behavior PASSED");

console.log("Provenance renderer contract PASSED");
