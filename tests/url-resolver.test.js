const fs = require("fs");
const vm = require("vm");
const assert = require("assert");

const window = {};
const source = fs.readFileSync("assets/js/core/url-resolver.js", "utf8");
vm.runInNewContext(source, { window });
const resolver = window.PrivateCapitalURL;

assert.strictEqual(resolver.entityURL("person:ali-sanginian", "atlas"), "person.html?id=person%3Aali-sanginian");
assert.strictEqual(resolver.entityURL("concept:private-equity", "research"), "../atlas/concept.html?id=concept%3Aprivate-equity");
assert.strictEqual(resolver.entityCanonicalURL("organization:foo-bar"), "https://privatecapital.ir/atlas/organization.html?id=organization%3Afoo-bar");
assert.strictEqual(resolver.entityURL("project:test-project", "atlas"), null);
assert.strictEqual(resolver.entityURL("invalid-id", "atlas"), null);
assert.strictEqual(resolver.entityURL(null, "atlas"), null);

console.log("URL resolver tests PASSED");
