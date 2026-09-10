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

console.log("Provenance renderer behavior PASSED");

console.log("Provenance renderer contract PASSED");
