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

assert.strictEqual(
  totalEvidence,
  26,
  `Expected 26 Evidence records, found ${totalEvidence}`
);

console.log("Evidence provenance data contract: PASS");
