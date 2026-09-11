const assert = require("assert");
const fs = require("fs");
const path = require("path");

const validator = path.join(
  __dirname,
  "..",
  "atlas",
  "tools",
  "validate-atlas.py"
);

const validatorSource = fs.readFileSync(
  validator,
  "utf8"
);

assert.ok(
  validatorSource.includes('evidence.get("excerpt")'),
  "Validator must inspect excerpt"
);

assert.ok(
  validatorSource.includes('evidence.get("locator")'),
  "Validator must inspect locator"
);

assert.ok(
  validatorSource.includes("not isinstance(excerpt, str)"),
  "Validator must validate excerpt type"
);

assert.ok(
  validatorSource.includes("not isinstance(locator, dict)"),
  "Validator must validate locator type"
);

assert.ok(
  validatorSource.includes("elif not locator:"),
  "Validator must reject an empty locator object"
);

console.log("Evidence provenance policy contract: PASS");
