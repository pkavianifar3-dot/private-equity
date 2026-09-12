const assert = require("assert");
const fs = require("fs");

const rendererJS = fs.readFileSync("assets/js/core/relation-renderer.js", "utf8");

assert(rendererJS.includes("function renderRelation"), "renderRelation is missing");
assert(rendererJS.includes("currentEntityId"), "currentEntityId handling is missing");
assert(rendererJS.includes("reverse_label_fa"), "reverse label handling is missing");
assert(rendererJS.includes("subject === currentEntityId"), "forward direction handling is missing");
assert(rendererJS.includes("object === currentEntityId"), "reverse direction handling is missing");
assert(rendererJS.includes("subject === object"), "self-reference handling is missing");

console.log("Relation renderer behavior contract PASSED");
