const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { pathToFileURL, fileURLToPath } = require("node:url");
const { execFileSync } = require("node:child_process");
const core = require("../assets/js/kaavosh-core.js");
const root = path.resolve(__dirname, "..");
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "privatecapital-kaavosh-test-"));
const output = path.join(temporary, "site");
(async () => {
    execFileSync("python", ["-B", "-c", "import sys;from pathlib import Path;sys.path.insert(0,'tools');import site_release as s;s.package(Path('.').resolve(),Path(sys.argv[1]),public=True)", output], { cwd: root });
    const payload = JSON.parse(fs.readFileSync(path.join(output, "search/documents.json"), "utf8"));
    const docs = core.validate(payload), pfdir = path.join(output, "search/pagefind");
    const fetched = [];
    global.fetch = async input => {
        const url = new URL(typeof input === "string" ? input : input.url), p = fileURLToPath(url), rel = path.relative(pfdir, p);
        assert.ok(!rel.startsWith("..") && !path.isAbsolute(rel));
        fetched.push(rel); return new Response(fs.readFileSync(p), { status: 200 });
    };
    let loads = 0;
    const client = core.createClient({ fetchDocuments: () => payload, loadPagefind: async () => {
        loads++; const pf = await import(pathToFileURL(path.join(pfdir, "pagefind.js"))); await pf.options({ baseUrl: "/" }); return pf;
    } });
    await client.search("", { scope: "atlas" }); assert.equal(loads, 0, "empty browsing must not load Pagefind");
    const cases = JSON.parse(fs.readFileSync(path.join(__dirname, "fixtures/kaavosh-queries.json"), "utf8"));
    const outcomes = [];
    for (const c of cases) {
        const start = performance.now(); const rows = await client.search(c.query, { scope: c.scope });
        const ids = rows.map(r => r.id);
        let previous = -1;
        for (const id of c.expected) {
            const at = ids.indexOf(id); assert.ok(at >= 0, `${c.n}: ${c.query}: missing ${id}`);
            assert.ok(at + 1 <= c.maxRank, `${c.n}: ${c.query}: ${id} rank ${at + 1} > ${c.maxRank}`);
            assert.ok(at > previous, `${c.n}: expected ordered subset ${c.expected}`); previous = at;
        }
        for (const id of c.forbidden) assert.ok(!ids.includes(id), `private identity ${id}`);
        if (c.empty) assert.deepEqual(ids, []);
        outcomes.push({ n: c.n, query: c.query, scope: c.scope, ids, expected: c.expected, ranks: c.expected.map(id => ids.indexOf(id) + 1), ms: +(performance.now() - start).toFixed(2), passed: true });
    }
    for (const d of docs.filter(d => d.scope === "research")) {
        assert.equal((await client.search(d.title, { scope: "research" }))[0].id, d.id, "exact Research title must lead");
    }
    for (const d of docs.filter(d => d.scope === "atlas")) for (const a of d.aliases) {
        assert.equal((await client.search(a, {scope:"atlas"}))[0].id, d.id, "actual public canonical alias must lead");
    }
    const alias = { ...docs[0], aliases: ["Alias exclusive fixture"] };
    assert.equal(core.match(alias, "Alias exclusive fixture").tier, 0);
    assert.equal(core.merge([alias], "Alias exclusive fixture", { scope: "atlas" })[0].id, alias.id);
    assert.deepEqual(core.normalize("سرمايه‌گذاري كيان ۱۲٣"), core.normalize("سرمایه گذاری کیان 123"));
    assert.equal(core.normalize("خُصوصی"), "خصوصی");
    assert.deepEqual(core.merge(docs, "", { scope: "atlas", type: "Sector" }), []);
    assert.ok(core.merge(docs, "", { scope: "atlas", group: "actors" }).every(d => ["Person", "Organization"].includes(d.type)));
    assert.equal(core.stateFromURL("?q=Amin&page=999999&type=Organization").query, "Amin");
    assert.equal(core.stateFromURL("?page=2garbage").page, 1);
    assert.equal(core.stateFromURL("?scope=invalid", "research").scope, "research");
    const state = { query: "سرمایه خصوصی", scope: "all", type: "Concept", group: "actors", page: 2 };
    assert.deepEqual(core.stateFromURL("?" + core.queryString(state)), state);
    assert.throws(() => core.validate({ ...payload, documents: [docs[0], docs[0]] }), /تکراری/);
    assert.throws(() => core.validate({ ...payload, documents: [{ ...docs[0], url: "https://evil.invalid/" }] }), /مسیر/);
    assert.equal(core.merge(docs, "not-indexed", { scope: "all" }, [{ id: "private-unknown", data: () => {} }]).length, 0);
    assert.equal(core.merge([docs[0], docs[0]], docs[0].title, { scope: "all" }).length, 1);
    // Body result excerpt uses the real legacy article, not its related cards.
    const body = (await client.search("Deal Sourcing", { scope: "research" }))[0];
    assert.match((await body.loadExcerpt()).excerpt.replace(/<[^>]+>/g, ""), /Deal Sourcing/i);
    assert.deepEqual(core.pageWindow(1, 2), [1, 2]);
    assert.deepEqual(core.pageWindow(50, 100), [1, null, 48, 49, 50, 51, 52, null, 100]);
    let attempts = 0;
    const retryClient = core.createClient({ fetchDocuments: () => { if (++attempts === 1) throw Error("offline"); return payload; }, loadPagefind: () => { throw Error("offline engine"); } });
    await assert.rejects(retryClient.search("", {scope:"atlas"}), /offline/);
    assert.equal((await retryClient.search("", {scope:"atlas"})).length, 12);
    await assert.rejects(retryClient.search("PE", {scope:"atlas"}), /offline engine/);
    const report = { queries: outcomes, count: cases.length, passed: outcomes.length, engineLoads: loads, fetchedFiles: [...new Set(fetched)] };
    if (process.env.KAAVOSH_REPORT) fs.writeFileSync(process.env.KAAVOSH_REPORT, JSON.stringify(report, null, 2));
    const pf = await import(pathToFileURL(path.join(pfdir, "pagefind.js"))); await pf.destroy();
    console.log(`Kaavosh: ${outcomes.length}/${cases.length} grounded ranked queries, alias, exact-title, URL, dedup and lazy-load contracts PASSED`);
})().catch(e => { console.error(e); process.exitCode = 1; }).finally(() => {
    assert.ok(path.resolve(temporary).startsWith(path.resolve(os.tmpdir()) + path.sep)); fs.rmSync(temporary, { recursive: true, force: true });
});
