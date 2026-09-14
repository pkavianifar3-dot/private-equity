const assert=require("assert"),fs=require("fs"),vm=require("vm");const c={window:{}};vm.createContext(c);vm.runInContext(fs.readFileSync("assets/js/research/citation-renderer.js","utf8"),c);const r=c.window.PrivateCapitalCitationRenderer;const sections=[{content:[{id:"b1"},{id:"b2"}]}];const citations=[{id:"citation:b1",sourceRef:"source:b",contentBlockId:"b2",start:0,end:2},{id:"citation:a",sourceRef:"source:a",contentBlockId:"b1",start:5,end:7},{id:"citation:b2",sourceRef:"source:b",contentBlockId:"b2",start:8,end:10}];const index=r.buildCitationIndex(sections,citations);assert.strictEqual(index.get("source:a"),1);assert.strictEqual(index.get("source:b"),2);assert.strictEqual(r.getBlockCitations(citations,"b2",10).length,2);console.log("Citation renderer contract PASSED");

const sameRangeCitations=[
    {id:"citation:same-a",sourceRef:"source:a",contentBlockId:"same",start:0,end:5},
    {id:"citation:same-b",sourceRef:"source:b",contentBlockId:"same",start:0,end:5}
];

const sameRangeIndex=r.buildCitationIndex([{content:[{id:"same"}]}],sameRangeCitations);

const sameRangeHtml=r.renderInlineCitations("متن آزمایشی","same",sameRangeCitations,sameRangeIndex);

assert.ok(sameRangeHtml.includes("#citation-source-1"));
assert.ok(sameRangeHtml.includes("#citation-source-2"));