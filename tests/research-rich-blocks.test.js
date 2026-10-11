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
assert(html.includes('<span class="research-caption">شرح</span><span class="figure-credit research-credit">منبع</span>'));
assert(html.includes('alt="تصویر"'));
console.log("Research rich block backward-compatible contract PASSED");

const structured = [{content:[
  {id:"body",type:"paragraph",text:"متن دارای یادداشت"},
  {id:"note",type:"note",noteNumber:1,text:"توضیح مستند"},
  {id:"matrix",type:"table",direction:"rtl",caption:"عنوان جدول",credit:"منبع: سند",rows:[["مفهوم","نمونه"],["اعتبار خصوصی","وام"]]}
]}];
const content = scope.window.renderArticleContent(structured,[],[],[],undefined,null);
assert(content.includes('href="#research-note-note"'));
assert(!content.includes('توضیح مستند'));
assert(content.includes('<table dir="rtl"'));
assert(content.includes('<th scope="col">مفهوم</th>'));
assert(content.includes('<span class="research-caption">عنوان جدول</span><span class="research-credit">منبع: سند</span>'));
const notes = scope.window.renderArticleNotes(structured,[],new Map(),null);
assert(notes.includes('<details class="research-notes research-endmatter">'));
assert(notes.includes('پانوشت‌ها و یادداشت‌ها (1)'));
assert(notes.includes('id="research-note-note"'));
const bibliography = scope.window.PrivateCapitalCitationRenderer.renderCitationBibliographyHtml(
  [{id:"citation:en",sourceRef:"source:en"},{id:"citation:fa",sourceRef:"source:fa"}],
  [{id:"source:en",title_fa:"Private capital",publisher:"CFA Institute"},
   {id:"source:fa",title_fa:"سرمایه خصوصی",publisher:"نهاد پژوهشی"}],
  new Map([["source:en",1],["source:fa",2]])
);
assert(bibliography.includes('id="citation-source-1" dir="ltr" lang="en"'));
assert(bibliography.includes('id="citation-source-2" dir="rtl"'));

// Exact inline anchors use the source Word offsets, including separate table cells.
const anchored = [{content:[
  {id:"p1",type:"paragraph",text:"سرمایه خصوصی و سرمایه خصوصی"},
  {id:"n1",type:"note",text:"تعریف",noteNumber:1,anchor:{contentBlockId:"p1",offset:12}},
  {id:"p2",type:"paragraph",text:"سرمایه خصوصی در بخش بعد"},
  {id:"matrix2",type:"table",direction:"rtl",rows:[["مفهوم"],["اعتبار خصوصی وام"]]},
  {id:"n2",type:"note",text:"توضیح",noteNumber:2,anchor:{contentBlockId:"matrix2",row:1,column:0,offset:13}}
]}];
const opts = {mentionLinkPolicy:"first-per-section",referenceStyle:"inline-collapsible"};
const resolver = {resolve:id=>({url:"/atlas/concept/private-capital/"})};
const mention = [{contentBlockId:"p1",start:0,end:12,text:"سرمایه خصوصی",resolutionStatus:"RESOLVED",entityRef:"concept:private-capital"},
                 {contentBlockId:"p1",start:15,end:27,text:"سرمایه خصوصی",resolutionStatus:"RESOLVED",entityRef:"concept:private-capital"},
                 {contentBlockId:"p2",start:0,end:12,text:"سرمایه خصوصی",resolutionStatus:"RESOLVED",entityRef:"concept:private-capital"}];
const anchoredHtml = scope.window.renderArticleContent(anchored,mention,[],[],new Map(),resolver,opts);
assert(anchoredHtml.includes('سرمایه خصوصی</a><sup class="research-note-ref"'));
assert.strictEqual((anchoredHtml.match(/href="\/atlas\/concept\/private-capital\/"/g)||[]).length,1);
assert(anchoredHtml.includes('اعتبار خصوصی <sup class="research-note-ref"'));
assert(!anchoredHtml.includes('بخش بعد<sup'));
assert.throws(()=>scope.window.renderArticleContent([{content:[{id:"p1",type:"paragraph",text:"کوتاه"},
    {id:"bad",type:"note",noteNumber:1,anchor:{contentBlockId:"p1",offset:999}}]}],[],[],[],new Map(),null,opts),/Invalid note anchor/);
const inline = scope.window.PrivateCapitalCitationRenderer.renderCitationMarker({id:"citation:test",sourceRef:"source:test"},new Map([["source:test",1]]),opts);
assert(inline.includes('<span class="citation citation-inline"') && !inline.includes('<sup'));
const collapsedSources = scope.window.PrivateCapitalCitationRenderer.renderCitationBibliographyHtml(
  [{id:"citation:test",sourceRef:"source:test"}],
  [{id:"source:test",title_en:"Private capital"}],new Map([["source:test",1]]),opts);
assert(collapsedSources.includes('<details class="research-bibliography research-endmatter">'));
// The real article preserves every Word note in the expected block and
// limits routed Entity links to one occurrence per section.
const real = JSON.parse(fs.readFileSync('research/content/private-markets/private-capital-research/research.json','utf8'));
const realOpts = {mentionLinkPolicy:real.presentation.mentionLinkPolicy,referenceStyle:real.presentation.referenceStyle};
const allNotes = real.sections.flatMap(section=>section.content.filter(block=>block.type==='note'));
assert.strictEqual(allNotes.length,20);
assert.strictEqual(allNotes.filter(note=>Number.isInteger(note.anchor.row)).length,5);
for (const section of real.sections) {
  const ids = new Map(section.content.map(block=>[block.id,block]));
  for (const note of section.content.filter(block=>block.type==='note')) {
    const target=ids.get(note.anchor.contentBlockId);
    const targetText=target.type==='table' ? target.rows[note.anchor.row][note.anchor.column] : target.text;
    assert(note.anchor.offset>=0 && note.anchor.offset<=targetText.length,`invalid ${note.id}`);
  }
  const realResolver={resolve:id=>({url:'/atlas/concept/'+id.split(':')[1]+'/'})};
  const html=scope.window.renderArticleContent([section],section.mentions||[],[],real.citations,new Map(),realResolver,realOpts);
  assert.strictEqual((html.match(/class="research-note-ref"/g)||[]).length,
    section.content.filter(block=>block.type==='note').length);
  assert((html.match(/href="\/atlas\/concept\/private-capital\/"/g)||[]).length<=1);
  assert((html.match(/href="\/atlas\/concept\/private-equity\/"/g)||[]).length<=1);
  assert(!html.includes('<sup class="citation"'));
}
