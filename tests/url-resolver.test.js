const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const window = {};
const source = fs.readFileSync("assets/js/core/url-resolver.js", "utf8");
vm.runInNewContext(source, { window });
const resolver = window.PrivateCapitalURL;

assert.strictEqual(
    resolver.entityURL("person:ali-sanginian", "atlas"),
    "/atlas/person/ali-sanginian/"
);

assert.strictEqual(
    resolver.entityURL("concept:private-equity", "research"),
    "/atlas/concept/private-equity/"
);

assert.strictEqual(
    resolver.entityCanonicalURL("organization:foo-bar"),
    "https://privatecapital.ir/atlas/organization/foo-bar/"
);

assert.strictEqual(
    resolver.entityURL("project:test-project", "atlas"),
    null
);

assert.strictEqual(
    resolver.entityURL("invalid-id", "atlas"),
    null
);

assert.strictEqual(
    resolver.entityURL(null, "atlas"),
    null
);

console.log("URL resolver tests PASSED");
