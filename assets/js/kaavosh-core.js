/* Shared public retrieval contract; no DOM and no canonical writes. */
(function (root, factory) {
    const api = factory();
    if (typeof module === "object" && module.exports) module.exports = api;
    else root.KaavoshCore = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
    "use strict";
    const GROUPS = { actors: ["Person", "Organization", "OrganizationUnit"], "capital-transactions": ["Investment", "Fund"], "business-projects": ["Organization", "Project"], "concepts-domains": ["Concept", "Sector"] };
    function normalize(value) {
        return String(value ?? "").normalize("NFKC").replace(/[يى]/g, "ی").replace(/ك/g, "ک").replace(/[ۀة]/g, "ه")
            .replace(/[\u064b-\u065f\u0670\u0640]/g, "").replace(/[۰-۹]/g, c => String(c.charCodeAt(0) - 0x06f0))
            .replace(/[٠-٩]/g, c => String(c.charCodeAt(0) - 0x0660)).replace(/\u200c/g, " ").replace(/\s+/g, " ").trim().toLowerCase();
    }
    const tokens = value => normalize(value).match(/[\p{L}\p{N}]+/gu) || [];
    const compact = value => tokens(value).join("");
    function match(doc, query) {
        const q = normalize(query);
        if (!q) return { tier: 5, matchType: "browse" };
        const names = [doc.title, doc.english, ...(doc.aliases || [])].filter(Boolean).map(normalize);
        if (doc.scope === "atlas" && doc.english) names.push(normalize(doc.title + " " + doc.english));
        const c = compact(q);
        if (names.some(n => n === q || (c && compact(n) === c))) return { tier: 0, matchType: "exact" };
        if (names.some(n => n.startsWith(q) || (c && compact(n).startsWith(c)))) return { tier: 1, matchType: "prefix" };
        const words = tokens(q), allNames = names.flatMap(tokens);
        if (words.length && words.every(w => allNames.some(n => n.startsWith(w)))) return { tier: 2, matchType: "tokens" };
        if (names.some(n => n.includes(q))) return { tier: 3, matchType: "partial" };
        return null;
    }
    function stateFromURL(search, defaultScope = "atlas") {
        const p = new URLSearchParams(search);
        return { query: p.get("q") || "", scope: ["atlas", "research", "all"].includes(p.get("scope")) ? p.get("scope") : defaultScope,
            type: p.get("type") || "", group: p.get("group") || "", page: /^[1-9]\d*$/.test(p.get("page") || "") ? Math.min(Number(p.get("page")), Number.MAX_SAFE_INTEGER) : 1 };
    }
    function queryString(state, defaultScope = "atlas") {
        const p = new URLSearchParams();
        if (state.query) p.set("q", state.query);
        if (state.scope !== defaultScope) p.set("scope", state.scope);
        if (state.type) p.set("type", state.type);
        if (state.group) p.set("group", state.group);
        if (state.page > 1) p.set("page", String(state.page));
        return p.toString();
    }
    function validate(data) {
        if (data?.version !== 1 || !Array.isArray(data.documents)) throw Error("قرارداد دادهٔ کاوش معتبر نیست.");
        const ids = new Set(), urls = new Set(), pf = new Set();
        const docs = data.documents;
        for (const d of docs) {
            if (!d.id || !d.title || typeof d.summary !== "string" || !d.pagefindId || ids.has(d.id) || urls.has(d.url) || pf.has(d.pagefindId)) throw Error("شناسهٔ تکراری یا ناقص در کاوش.");
            const research = d.scope === "research" && d.kind === "research" && d.type === "Research" && /^research:[a-z0-9-]+$/.test(d.id) && /^\/articles\/[a-z0-9-]+\.html$/.test(d.url);
            const routes = { Person: "person", Organization: "organization", Investment: "investment", Concept: "concept" };
            const slug = d.id.split(":")[1];
            const entity = d.scope === "atlas" && routes[d.type] && d.kind === (d.type === "Concept" ? "concept" : "entity") && /^[a-z]+:[a-z0-9-]+$/.test(d.id) && d.url === `/atlas/${routes[d.type]}/${slug}/`;
            if (!research && !entity) throw Error("مسیر نتیجهٔ کاوش معتبر نیست.");
            ids.add(d.id); urls.add(d.url); pf.add(d.pagefindId);
        }
        return docs;
    }
    function merge(docs, query, state, fulltext = []) {
        const hits = new Map(fulltext.map((r, i) => [r.id, { order: i, data: r.data }]));
        const rows = [], seen = new Set();
        for (const d of docs) {
            if (seen.has(d.id) || (state.scope !== "all" && d.scope !== state.scope) || (state.type && d.type !== state.type)) continue;
            if (GROUPS[state.group] && !GROUPS[state.group].includes(d.type)) continue;
            const hit = hits.get(d.pagefindId), named = match(d, query);
            const relevance = named || (hit && normalize(query) ? { tier: 4, matchType: "body" } : null);
            if (!relevance) continue;
            seen.add(d.id); rows.push({ ...d, ...relevance, fulltextOrder: hit?.order ?? Infinity, loadExcerpt: hit?.data });
        }
        rows.sort((a, b) => a.tier - b.tier || (a.tier === 4 ? a.fulltextOrder - b.fulltextOrder : 0) ||
            ((a.kind === "research" ? 1 : 0) - (b.kind === "research" ? 1 : 0)) || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
        return rows;
    }
    function createClient({ fetchDocuments, loadPagefind }) {
        let documents, engine;
        async function getDocuments() {
            if (!documents) documents = Promise.resolve().then(fetchDocuments).then(validate).catch(e => { documents = null; throw e; });
            return documents;
        }
        return { documents: getDocuments, async search(query, state) {
            const docs = await getDocuments();
            if (!normalize(query)) return merge(docs, "", state);
            if (!engine) engine = Promise.resolve().then(loadPagefind).catch(e => { engine = null; throw e; });
            const pf = await engine;
            // Literal normalized phrases in body search avoid unrelated fuzzy/prefix hits.
            // Prefix discovery remains available through the shared name matcher.
            const terms = tokens(query);
            if (!terms.length) return merge(docs, query, state);
            const response = await pf.search('"' + normalize(query).replace(/"/g, " ").trim() + '"');
            return merge(docs, query, state, response.results);
        } };
    }
    function pageWindow(current, total) {
        const pages = [...new Set([1, total, ...Array.from({ length: 5 }, (_, i) => current - 2 + i)])]
            .filter(p => p >= 1 && p <= total).sort((a, b) => a - b);
        const result = [];
        for (const p of pages) {
            if (result.length && p - result[result.length - 1] > 1) result.push(null);
            result.push(p);
        }
        return result;
    }
    return { normalize, tokens, match, stateFromURL, queryString, validate, merge, createClient, pageWindow, GROUPS };
});
