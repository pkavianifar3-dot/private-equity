const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const window = {};
const source = fs.readFileSync("assets/js/core/url-resolver.js", "utf8");
vm.runInNewContext(source, { window });
const resolver = window.PrivateCapitalURL;

assert.strictEqual(
    resolver.entityURL("person:ali-sanginian", "Person"),
    "/atlas/person/ali-sanginian/"
);

assert.strictEqual(
    resolver.entityURL("concept:private-equity", "Concept"),
    "/atlas/concept/private-equity/"
);

assert.strictEqual(
    resolver.entityCanonicalURL(
        "organization:foo-bar",
        "Organization"
    ),
    "https://privatecapital.ir/atlas/organization/foo-bar/"
);

assert.strictEqual(
    resolver.entityURL(
        "organization:tehran-chamber-money-capital-commission",
        "OrganizationUnit"
    ),
    null
);

assert.strictEqual(
    resolver.entityURL("project:test-project", "Project"),
    null
);

assert.strictEqual(
    resolver.entityURL("invalid-id", "Person"),
    null
);

assert.strictEqual(
    resolver.entityURL(null, "Person"),
    null
);

console.log("URL resolver tests PASSED");
