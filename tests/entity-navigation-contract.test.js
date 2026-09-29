const assert = require("assert");
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const root = path.resolve(__dirname, "..");
const read = name => JSON.parse(fs.readFileSync(path.join(root, name), "utf8"));
const window = {};
for (const name of ["url-resolver", "entity-resolver", "relation-renderer"]) {
    vm.runInNewContext(fs.readFileSync(path.join(root, `assets/js/core/${name}.js`), "utf8"), { window });
}
const urls = window.PrivateCapitalURL;
const registry = read("atlas/entities/index.json");
const entities = window.PrivateCapitalEntityResolver.create(registry, urls);
const catalog = read("atlas/catalog/index.json").entities;
assert.deepStrictEqual(catalog.map(e => e.id).sort(), registry.entities.map(e => e.id).sort());
for (const entity of catalog) {
    assert.strictEqual(urls.entityURL(entity.id, entity.type), entity.route || null, entity.id);
    const resolved = entities.resolve(entity.id);
    if (entity.route) {
        assert.strictEqual(resolved.url, entity.route, entity.id);
        assert.strictEqual(urls.entityCanonicalURL(entity.id, entity.type), `https://privatecapital.ir${entity.route}`);
        assert(fs.existsSync(path.join(root, entity.route.slice(1), "index.html")), entity.id);
    } else {
        assert.strictEqual(resolved, null, `${entity.id} must not invent a URL`);
    }
}
assert.strictEqual(entities.resolve("person:missing-from-registry"), null);
for (const type of ["OrganizationUnit", "Project", "Sector", "Fund", "InvestorCategory", "Role", "Source", "Claim", "toString", "__proto__", "constructor"]) {
    assert.strictEqual(urls.entityURL("organization:test", type), null, type);
}
for (const id of [null, undefined, 42, {}, [], "", "invalid", "person:"]) {
    assert.strictEqual(urls.entityURL(id, "Person"), null);
}
for (const type of [null, undefined, 42, {}, []]) {
    assert.strictEqual(urls.entityURL("person:test", type), null);
}
// Same slug in different namespaces must not collapse into one destination.
assert.strictEqual(urls.entityURL("concept:private-equity", "Concept"), "/atlas/concept/private-equity/");
assert.strictEqual(urls.entityURL("sector:private-equity", "Sector"), null);
const projectPreview = "/atlas/_preview/project/dadman/";
const unitPreview = "/atlas/_preview/organization-unit/tehran-chamber-money-capital-commission/";
vm.runInNewContext(fs.readFileSync(path.join(root, "atlas/tools/preview-url-resolver.js"), "utf8"), { window });
const previewURLs = window.PrivateCapitalURL;
const previewEntities = window.PrivateCapitalEntityResolver.create(registry, previewURLs);
assert.strictEqual(previewURLs.entityURL("project:dadman", "Project"), projectPreview);
assert.strictEqual(previewURLs.entityURL("organization:tehran-chamber-money-capital-commission", "OrganizationUnit"), unitPreview);
assert.strictEqual(previewEntities.resolve("project:dadman").url, projectPreview);
assert.strictEqual(previewEntities.resolve("organization:tehran-chamber-money-capital-commission").url, unitPreview);
assert.strictEqual(previewEntities.resolve("project:missing"), null);
assert.strictEqual(urls.entityURL("organization:tehran-chamber-money-capital-commission", "OrganizationUnit"), null);
assert.strictEqual(urls.entityURL("project:dadman", "Project"), null);
assert.strictEqual(previewURLs.entityURL("project:dadman", "OrganizationUnit"), null);
assert.strictEqual(previewURLs.entityURL("organization:tehran-chamber-money-capital-commission", "Project"), null);
assert.strictEqual(previewURLs.entityURL("sector:private-equity", "Sector"), null);
assert.strictEqual(previewURLs.entityURL("concept:private-equity", "Concept"), "/atlas/concept/private-equity/");

const types = read("atlas/taxonomies/relation-types.json");
const rules = read("atlas/taxonomies/relation-rules.json");
const rendering = read("atlas/taxonomies/relation-rendering.json");
const render = (claim, current, contract = rendering) =>
    window.PrivateCapitalRelationRenderer.renderRelation(claim, current, types, rules, contract);

const claims = fs.readdirSync(path.join(root, "atlas/claims"))
    .filter(name => name.endsWith(".json") && name !== "index.json")
    .flatMap(name => read(`atlas/claims/${name}`).claims);
for (const claim of claims) {
    const forward = render(claim, claim.subject);
    if (!claim.object) {
        assert.strictEqual(forward, null, "Value claims are not entity relations");
        continue;
    }
    const contract = rendering.relations[claim.predicate];
    assert.strictEqual(forward.direction, "forward", claim.id);
    assert.strictEqual(forward.targetId, claim.object, claim.id);
    assert.strictEqual(forward.label, contract.forward_label_fa, claim.id);
    const reverse = render(claim, claim.object);
    if (contract.reverse_display_allowed === true) {
        assert.strictEqual(reverse.direction, "reverse", claim.id);
        assert.strictEqual(reverse.targetId, claim.subject, claim.id);
        assert.strictEqual(reverse.label, contract.reverse_label_fa, claim.id);
    } else {
        assert.strictEqual(reverse, null, claim.id);
    }
    assert.strictEqual(render(claim, "concept:unrelated"), null);
}
const sample = { subject: "concept:a", object: "concept:b", predicate: "INCLUDES" };
for (const claim of [null, {}, { ...sample, object: null }, { ...sample, object: "concept:a" }, { ...sample, predicate: "UNKNOWN" }]) {
    assert.strictEqual(render(claim, "concept:a"), null);
}
for (const label of [null, 7, {}, "", "   "]) {
    const contract = { relations: { INCLUDES: { ...rendering.relations.INCLUDES, forward_label_fa: label, reverse_label_fa: label } } };
    assert.strictEqual(render(sample, sample.subject, contract), null);
    assert.strictEqual(render(sample, sample.object, contract), null);
}
for (const flag of [false, null, "true", 1]) {
    const contract = { relations: { INCLUDES: { ...rendering.relations.INCLUDES, reverse_display_allowed: flag } } };
    assert.strictEqual(render(sample, sample.object, contract), null);
}
assert.strictEqual(render(sample, sample.subject, { relations: {} }), null);
assert.strictEqual(window.PrivateCapitalRelationRenderer.renderRelation(sample, sample.subject, types, { rules: {} }, rendering), null);
assert.strictEqual(window.PrivateCapitalRelationRenderer.renderRelation(sample, sample.subject, { relation_types: {} }, rules, rendering), null);
console.log(`Entity navigation contract PASSED: ${catalog.length} entities, ${claims.length} claims`);
