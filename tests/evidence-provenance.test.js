const assert = require("assert");
const fs = require("fs");
const path = require("path");

const validatorPath = path.join(
  __dirname,
  "..",
  "atlas",
  "tools",
  "validate-atlas.py"
);

assert.ok(
  fs.existsSync(validatorPath),
  "atlas/tools/validate-atlas.py must exist"
);

// R1-A contract baseline:
// Evidence may currently omit excerpt/locator.
// This test intentionally verifies the existing contract boundary
// before the validator is strengthened.

const evidenceSchemaPath = path.join(
  __dirname,
  "..",
  "atlas",
  "schemas",
  "evidence-schema-v2.json"
);

const schema = JSON.parse(
  fs.readFileSync(evidenceSchemaPath, "utf8")
);

const evidenceRecord = schema.$defs.evidenceRecord;

assert.ok(
  evidenceRecord.properties.excerpt,
  "Evidence schema must define optional excerpt"
);

assert.ok(
  evidenceRecord.properties.locator,
  "Evidence schema must define optional locator"
);

assert.ok(
  !evidenceRecord.required.includes("excerpt"),
  "excerpt must remain optional at this checkpoint"
);

assert.ok(
  !evidenceRecord.required.includes("locator"),
  "locator must remain optional at this checkpoint"
);

console.log("Evidence provenance contract baseline: PASS");
