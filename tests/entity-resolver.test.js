const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const context = {
    window: {}
};

vm.createContext(context);

vm.runInContext(
    fs.readFileSync("assets/js/core/entity-resolver.js", "utf8"),
    context
);

const registry = {
    entities: [
        {
            id: "person:ali-sanginian",
            type: "Person",
            name: { fa: "علی سنگینیان", en: "Ali Sanginian" }
        },
        {
            id: "project:dadman",
            type: "Project",
            name: { fa: "دادمان", en: "Dadman" }
        }
    ]
};

const urlResolver = {
    entityURL(entityRef) {
        if (entityRef === "person:ali-sanginian") {
            return "/atlas/person/ali-sanginian/";
        }

        return null;
    }
};

const resolver = context.window.PrivateCapitalEntityResolver.create(
    registry,
    urlResolver
);

const resolved = resolver.resolve(
    "person:ali-sanginian",
    "research"
);

assert(resolved);
assert.strictEqual(resolved.entity.id, "person:ali-sanginian");
assert.strictEqual(
    resolved.url,
    "/atlas/person/ali-sanginian/"
);

assert.strictEqual(
    resolver.resolve("project:dadman", "research"),
    null
);

assert.strictEqual(
    resolver.resolve("person:unknown", "research"),
    null
);

assert.strictEqual(
    resolver.resolve(null, "research"),
    null
);

console.log("Entity resolver contract PASSED");
