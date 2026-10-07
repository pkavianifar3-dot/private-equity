const assert = require("assert");
const fs = require("fs");
const vm = require("vm");
const scope = { window: {} };
vm.createContext(scope);
vm.runInContext(fs.readFileSync("assets/js/research/citation-renderer.js","utf8"),scope);
vm.runInContext(fs.readFileSync("assets/js/article-renderer.js","utf8"),scope);
const html = scope.window.renderArticleContent([{content:[
  {id:"heading",type:"subheading",level:4,text:"زیربخش"},
  {id:"list",type:"list",items:["یک"],ordered:true},
  {id:"figure",type:"figure",src:"/assets/images/test.png",alt:"تصویر",caption:"شرح",credit:"منبع"}
]}],[],[],[],undefined,null);
assert(html.includes("<h4>زیربخش</h4>"));
assert(html.includes("<ol>") && html.includes("</ol>"));
assert(html.includes('<span class="figure-credit">منبع</span>'));
assert(html.includes('alt="تصویر"'));
console.log("Research rich block backward-compatible contract PASSED");
