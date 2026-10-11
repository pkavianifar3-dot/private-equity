const assert = require("assert");
const fs = require("fs");
const os = require("os");
const child = require("child_process");
const path = require("path");
const { discover } = require("../atlas/tools/research-package");
const actual = discover();
assert.deepStrictEqual(actual.map(({data})=>data.id),["research:private-capital", "research:private-capital-research"]);
assert.strictEqual(actual[0].data.url,"/articles/private-capital.html");
const { createShell } = require("../atlas/tools/build-research-pages");
const shell = createShell({title:{fa:"عنوان پژوهش"},summary:{fa:"خلاصه"},sections:[
    {id:"introduction",title:{fa:"مقدمه"}}
]});
assert(shell.includes("<h1>عنوان پژوهش</h1>"));
assert(shell.indexOf('class="research-article-header"') < shell.indexOf('<article>'));
assert(shell.includes('src="/assets/js/research-notes.js"'));
assert(shell.includes('data-article-renderer-section="introduction"'));
assert(shell.includes("<div data-article-renderer-citations></div><br>"));
assert(shell.includes('data-research-connections'));
assert(shell.includes('rel="canonical"'));
// A newly PUBLISHED package has no earlier HTML and must complete static ->
// Research connections -> schema/registry validation in a disposable site root.
const fixture = fs.mkdtempSync(path.join(os.tmpdir(), "research-published-"));
try {
    fs.mkdirSync(path.join(fixture, "research/content/demo/new"), {recursive:true});
    fs.mkdirSync(path.join(fixture, "research"), {recursive:true});
    const article = {id:"research:new",type:"Research",schemaVersion:"2.0",
        url:"/articles/new.html",status:"PUBLISHED",title:{fa:"مقاله تازه"},
        summary:{fa:"متن آزمون"},publication:{datePublished:"2026-01-01",dateModified:null,authorRefs:[]},
        candidateClaimRefs:[],entityRefs:[],sourceRefs:[],sections:[
            {id:"opening",title:{fa:"آغاز"},content:[{id:"para",type:"paragraph",text:"متن کامل مقاله تازه"}]}
        ],citations:[], presentation:{mentionLinkPolicy:"first-per-section",referenceStyle:"inline-collapsible"}};
    article.sections[0].content[0].text="سرمایه خصوصی";
    article.sections[0].mentions=[{id:"mention",entityRef:"concept:review",text:"سرمایه خصوصی",
        contentBlockId:"para",start:0,end:12,resolutionStatus:"RESOLVED"}];
    const source = path.join(fixture,"research/content/demo/new/research.json");
    fs.writeFileSync(source,JSON.stringify(article));
    const entry = {id:article.id,url:article.url,status:article.status};
    fs.writeFileSync(path.join(fixture,"research/index.json"),JSON.stringify({research:[entry]}));
    const {buildArticle,loadRuntime} = require("../atlas/tools/build-research-pages");
    loadRuntime();
    const options = {outputRoot:fixture,registry:new Map([[article.id,entry]])};
    const entities={entities:[{id:"concept:review",type:"Concept",lifecycleStatus:"REVIEW"}]};
    article.primaryEntityRef="concept:review";
    article.entityRefs=["concept:review"];
    fs.writeFileSync(source,JSON.stringify(article));
    const result = buildArticle(source,entities,{sources:{}},new Map(),options);
    const page = fs.readFileSync(result.outputPath,"utf8");
    assert(page.includes("سرمایه خصوصی"));
    assert(!page.includes('href="/atlas/concept/review/"'),"new public Research must not link REVIEW Entity");
    assert(!page.includes('src="../assets/js/article-page.js"'),"source-less shell must not load renderer without dependencies");
    assert.strictEqual(buildArticle(source,entities,{sources:{}},new Map(),options).changed,false);
    assert(page.includes('data-research-connections'));
    const check = `import json,sys,importlib.util;from pathlib import Path;root=Path(sys.argv[1]);tools=Path(sys.argv[2]);sys.path.insert(0,str(tools));spec=importlib.util.spec_from_file_location('rc',tools/'research_connections.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);spec2=importlib.util.spec_from_file_location('build',tools/'build-research-connections.py');b=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(b);a=list(c.eligible_articles(root));assert len(a)==1;path=c.article_path(root,a[0]['url'],a[0]['id']);updated=b.updated_article(path,c.render_article_context(a[0],json.loads(sys.argv[4]),root));assert updated is None or 'data-research-connections' in updated;schema=json.loads((root.parent if False else Path(sys.argv[3])).read_text(encoding='utf-8'));from jsonschema import Draft202012Validator;assert not list(Draft202012Validator(schema).iter_errors(a[0]))`;
    child.execFileSync("python",["-c",check,fixture,path.join(__dirname,"../atlas/tools"),path.join(__dirname,"../research/schemas/research-schema-v2.json"),JSON.stringify(entities.entities)]);
    for (const primary of ["concept:missing",[]]) {
        fs.writeFileSync(source,JSON.stringify({...article,primaryEntityRef:primary}));
        assert.throws(()=>buildArticle(source,entities,{sources:{}},new Map(),options),/research:new.*primaryEntityRef/);
        assert.strictEqual(fs.readFileSync(result.outputPath,"utf8"),page,"invalid primary must not alter output");
    }
    fs.writeFileSync(source,JSON.stringify({...article,entityRefs:[]}));
    assert.throws(()=>buildArticle(source,entities,{sources:{}},new Map(),options),/primaryEntityRef/);
    article.status="REVIEW";entry.status="REVIEW";
    fs.writeFileSync(source,JSON.stringify(article));
    const previewRoot=path.join(fixture,"preview");
    const previewResult=buildArticle(source,entities,{sources:{}},new Map(),
        {preview:previewRoot,registry:new Map([[article.id,entry]])});
    const previewPage=fs.readFileSync(previewResult.outputPath,"utf8");
    assert(previewPage.includes('href="/atlas/concept/review/"'));
    assert(previewPage.includes('name="robots" content="noindex,nofollow"'));
    assert(!previewPage.includes('rel="canonical"'));
    assert.strictEqual(buildArticle(source,entities,{sources:{}},new Map(),options),null);
    fs.writeFileSync(source,JSON.stringify(article));
    assert.throws(()=>buildArticle(source,entities,{sources:{}},new Map(),
        {preview:path.join(__dirname,".."),registry:new Map([[article.id,entry]])}),
        /preview output must be outside/);
    for (const [from,to] of [["REVIEW","PUBLISHED"],["PUBLISHED","REVIEW"]]) {
        article.status=from; entry.status=to;
        fs.writeFileSync(source,JSON.stringify(article));
        assert.throws(()=>buildArticle(source,entities,{sources:{}},new Map(),options),/URL\/status mismatch/);
    }
} finally {
    fs.rmSync(fixture,{recursive:true,force:true});
}
console.log("Research package and new published article end-to-end contract PASSED");
