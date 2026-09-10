const assert = require("assert");
const fs = require("fs");

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

console.log("Provenance renderer contract PASSED");
