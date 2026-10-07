// Deterministic Research source discovery and build input contracts.
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "../..");
const CONTENT = path.join(ROOT, "research", "content");
function files(dir) {
    return fs.readdirSync(dir, { withFileTypes: true }).sort((a,b)=>a.name.localeCompare(b.name,"en"))
        .flatMap(entry => entry.isDirectory() ? files(path.join(dir,entry.name))
            : entry.isFile() && (entry.name === "research.json" || dir === CONTENT && entry.name.endsWith(".json"))
                ? [path.join(dir,entry.name)] : []);
}
function discover() {
    const registry = JSON.parse(fs.readFileSync(path.join(ROOT,"research/index.json"),"utf8")).research;
    const records = new Map(), urls = new Map(), identities = new Map();
    for (const row of registry) {
        if (identities.has(row.id)) throw new Error(`research/index.json: duplicate ID ${row.id}`);
        if (urls.has(row.url.toLowerCase())) throw new Error(`research/index.json: URL collision ${row.url}`);
        identities.set(row.id,row); urls.set(row.url.toLowerCase(),row.id);
    }
    for (const file of files(CONTENT)) {
        const data = JSON.parse(fs.readFileSync(file,"utf8"));
        if (!/^research:[a-z0-9]+(?:-[a-z0-9]+)*$/.test(data.id||"")) throw new Error(`${file}: invalid ID`);
        if (records.has(data.id)) throw new Error(`${file}: duplicate Research ID ${data.id}`);
        const entry = identities.get(data.id);
        if (!entry || entry.url !== data.url) throw new Error(`${file}: ${data.id}: registry URL mismatch`);
        records.set(data.id,{file,data});
    }
    for (const row of registry) if (!records.has(row.id) &&
        (row.sourceMode !== "legacy-html" || !fs.existsSync(path.join(ROOT,row.url.replace(/^\//,"")))))
        throw new Error(`research/index.json: ${row.id}: structured source or verified legacy HTML missing`);
    return [...records].sort(([a],[b])=>a.localeCompare(b,"en")).map(([,record])=>record);
}
module.exports={discover};
