const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const source = fs.readFileSync(
    "assets/js/core/data-loader.js",
    "utf8"
);

const requests = [];
const responses = new Map();

const context = {
    console,
    fetch: async path => {
        requests.push(path);
        const response = responses.get(path);

        if (response instanceof Error) {
            throw response;
        }

        return {
            ok: true,
            json: async () => response
        };
    }
};

context.window = context;
vm.createContext(context);
vm.runInContext(source, context);

const loader = context.PrivateCapitalDataLoader.create("../atlas");

(async () => {
    responses.set("../atlas/entities/test.json", { id: "test" });

    const first = await loader.loadJSON("../atlas/entities/test.json");
    assert.deepStrictEqual(first, { id: "test" });

    const p1 = loader.loadCachedJSON("../atlas/entities/test.json");
    const p2 = loader.loadCachedJSON("../atlas/entities/test.json");

    assert.strictEqual(p1, p2);
    await p1;

    assert.strictEqual(
        requests.filter(path => path === "../atlas/entities/test.json").length,
        2
    );

    responses.set("../atlas/entities/failing.json", new Error("temporary failure"));
    await assert.rejects(
        loader.loadCachedJSON("../atlas/entities/failing.json"),
        /temporary failure/
    );

    responses.set("../atlas/entities/failing.json", { id: "recovered" });
    const recovered = await loader.loadCachedJSON("../atlas/entities/failing.json");
    assert.deepStrictEqual(recovered, { id: "recovered" });

    assert.strictEqual(
        requests.filter(path => path === "../atlas/entities/failing.json").length,
        2
    );

    console.log("Data Loader behavior PASSED");
})();
