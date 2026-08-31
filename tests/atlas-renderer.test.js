const fs = require("fs");
const assert = require("assert");

const atlasJS =
    fs.readFileSync(
        "assets/js/atlas.js",
        "utf8"
    );

assert(
    atlasJS.includes("async function renderPerson"),
    "renderPerson is missing"
);

assert(
    atlasJS.includes("async function renderOrganization"),
    "renderOrganization is missing"
);

assert(
    atlasJS.includes("async function renderInvestment"),
    "renderInvestment is missing"
);

assert(
    atlasJS.includes("async function renderConcept"),
    "renderConcept is missing"
);

assert(
    atlasJS.includes('entityId.startsWith("person:")'),
    "person dispatch is missing"
);

assert(
    atlasJS.includes('entityId.startsWith("organization:")'),
    "organization dispatch is missing"
);

assert(
    atlasJS.includes('entityId.startsWith("investment:")'),
    "investment dispatch is missing"
);

assert(
    atlasJS.includes('entityId.startsWith("concept:")'),
    "concept dispatch is missing"
);

console.log("Atlas renderer structure PASSED");
