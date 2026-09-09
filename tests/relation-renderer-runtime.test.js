const assert = require("assert");
const fs = require("fs");
global.window = global;
eval(fs.readFileSync("assets/js/core/relation-renderer.js", "utf8"));

const types = { relation_types: [{ id: "CEO_OF", labels: { fa: "مدیرعامل" } }, { id: "BROADER_THAN", labels: { fa: "کلی‌تر از" } }] };
const rules = { rules: [{ relation: "CEO_OF", subject_types: ["Person"], object_types: ["Organization"] }, { relation: "BROADER_THAN", subject_types: ["Concept"], object_types: ["Concept"] }] };
const rendering = { relations: { BROADER_THAN: { reverse_label_fa: "مفهوم بالاتر" } } };

const forward = PrivateCapitalRelationRenderer.renderRelation({ subject: "person:a", predicate: "CEO_OF", object: "organization:b" }, "person:a", types, rules, rendering);
assert.deepStrictEqual(forward, { predicate: "CEO_OF", direction: "forward", targetId: "organization:b", label: "مدیرعامل" });

const reverse = PrivateCapitalRelationRenderer.renderRelation({ subject: "concept:a", predicate: "BROADER_THAN", object: "concept:b" }, "concept:b", types, rules, rendering);
assert.deepStrictEqual(reverse, { predicate: "BROADER_THAN", direction: "reverse", targetId: "concept:a", label: "مفهوم بالاتر" });

assert.strictEqual(PrivateCapitalRelationRenderer.renderRelation({ subject: "concept:a", predicate: "BROADER_THAN", object: "concept:a" }, "concept:a", types, rules, rendering), null);
assert.strictEqual(PrivateCapitalRelationRenderer.renderRelation({ subject: "person:a", predicate: "CEO_OF", object: "organization:b" }, "person:x", types, rules, rendering), null);

console.log("Relation renderer runtime behavior PASSED");
