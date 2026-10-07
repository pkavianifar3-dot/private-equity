const assert = require("assert");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { discover } = require("../atlas/tools/research-package");
const actual = discover();
assert.deepStrictEqual(actual.map(({data})=>data.id),["research:private-capital"]);
assert.strictEqual(actual[0].data.url,"/articles/private-capital.html");
const { createShell } = require("../atlas/tools/build-research-pages");
const shell = createShell({title:{fa:"عنوان پژوهش"},summary:{fa:"خلاصه"},sections:[
    {id:"introduction",title:{fa:"مقدمه"}}
]});
assert(shell.includes("<h1>عنوان پژوهش</h1>"));
assert(shell.includes('data-article-renderer-section="introduction"'));
assert(shell.includes("<div data-article-renderer-citations></div><br>"));
console.log("Research package discovery and new static shell contract PASSED");
