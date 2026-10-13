// Use the public Pagefind API to map opaque index IDs to approved URLs.
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";
const directory = path.resolve(process.argv[2]);
globalThis.fetch = async input => {
    const url = new URL(typeof input === "string" ? input : input.url);
    const file = fileURLToPath(url);
    const relative = path.relative(directory, file);
    if (url.protocol !== "file:" || relative.startsWith("..") || path.isAbsolute(relative)) throw Error("Index inspection escaped staging");
    return new Response(await fs.readFile(file), { status: 200 });
};
const pagefind = await import(pathToFileURL(path.join(directory, "pagefind.js")));
await pagefind.options({ baseUrl: "/" });
const results = await pagefind.search(null);
const records = await Promise.all(results.results.map(async r => ({ pagefindId: r.id, url: (await r.data()).url })));
await pagefind.destroy();
console.log(JSON.stringify(records));
