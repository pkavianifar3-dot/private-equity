const assert = require("assert");
const fs = require("fs");
const path = require("path");

const evidenceDir = path.join(__dirname, "..", "atlas", "evidence");
const sourceDir = path.join(__dirname, "..", "atlas", "sources");

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, "utf8"));
}

const sourceIds = new Set();

for (const file of fs.readdirSync(sourceDir).filter(
  name => name.endsWith(".json") && name !== "index.json"
)) {
  const data = readJson(path.join(sourceDir, file));

  for (const source of data.sources || []) {
    sourceIds.add(source.id);
  }
}

let totalEvidence = 0;
const evidenceIds = new Set();

for (const file of fs.readdirSync(evidenceDir).filter(
  name => name.endsWith(".json") && name !== "index.json"
)) {
  const data = readJson(path.join(evidenceDir, file));

  assert.ok(
    Array.isArray(data.evidence),
    `${file}: evidence must be an array`
  );

  for (const evidence of data.evidence) {
    totalEvidence += 1;
    assert(!evidenceIds.has(evidence.id), `${file}: duplicate Evidence ${evidence.id}`);
    evidenceIds.add(evidence.id);

    assert.ok(
      evidence.id,
      `${file}: evidence record must have id`
    );

    assert.ok(
      evidence.claimRef,
      `${evidence.id}: claimRef is required`
    );

    assert.ok(
      evidence.sourceRef,
      `${evidence.id}: sourceRef is required`
    );

    assert.ok(
      sourceIds.has(evidence.sourceRef),
      `${evidence.id}: sourceRef must resolve to an existing Source`
    );

    if (evidence.excerpt !== undefined) {
      assert.strictEqual(
        typeof evidence.excerpt,
        "string",
        `${evidence.id}: excerpt must be a string when present`
      );

      assert.ok(
        evidence.excerpt.trim().length > 0,
        `${evidence.id}: excerpt must be non-empty when present`
      );
    }

    if (evidence.locator !== undefined) {
      assert.strictEqual(
        typeof evidence.locator,
        "object",
        `${evidence.id}: locator must be an object when present`
      );

      assert.ok(
        !Array.isArray(evidence.locator),
        `${evidence.id}: locator must not be an array`
      );

      assert.ok(
        Object.keys(evidence.locator).length > 0,
        `${evidence.id}: locator must not be empty when present`
      );
    }
  }
}

const indexedEvidence = readJson(path.join(evidenceDir, "index.json")).evidence;
assert(totalEvidence >= 26, "Existing evidence must remain present");
assert.deepStrictEqual([...evidenceIds].sort(), Object.keys(indexedEvidence).sort(),
  "Evidence index must cover every record exactly once");
for (const [id, file] of Object.entries(indexedEvidence)) {
  assert(readJson(path.join(evidenceDir, file)).evidence.some(e => e.id === id),
    `${id}: Evidence index must point to its actual owning file`);
}

console.log("Evidence provenance data contract: PASS");
