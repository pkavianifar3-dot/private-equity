const assert=require('assert');
const fs=require('fs');
const vm=require('vm');
async function rejected(id, records) {
    const requests=[];const metas=new Map();
    const root={dataset:{},innerHTML:''};let removed=false;
    const canonical={remove(){removed=true;}};
    const document={getElementById(){return root;},querySelector(selector){
        if(selector==='link[rel="canonical"]')return canonical;
        return metas.get(selector)||null;
    },createElement(){return {setAttribute(k,v){this[k]=v;}};},head:{appendChild(el){metas.set(`meta[name="${el.name}"]`,el);}}};
    const context={console:{error(){}},URLSearchParams,
        document,window:{location:{pathname:'/atlas/organization.html',search:'?id='+encodeURIComponent(id)},
        PrivateCapitalURL:{entityURL(){throw new Error('Must not resolve a hidden Entity');}},
        PrivateCapitalDataLoader:{create(){return {loadCachedJSON:async path=>{requests.push(path);return {entities:records};},loadRelationContract:async()=>{throw new Error('Must not load private relations');}};}}}};
    vm.createContext(context);vm.runInContext(fs.readFileSync('assets/js/atlas.js','utf8'),context);
    await context.window.Atlas.init();
    assert(root.innerHTML.includes('صفحه پیدا نشد'));
    assert(!root.innerHTML.includes(id));
    assert.strictEqual(metas.get('meta[name="robots"]').content,'noindex,nofollow');
    assert(removed);assert.deepStrictEqual(requests,['./entities/index.json']);
}
async function approved() {
    const requests=[];const nodes=new Map();
    const root={dataset:{},innerHTML:''};
    const document={getElementById(id){return id==='atlas-root'?root:nodes.get(id)||null;},
        querySelector(selector){return nodes.get(selector)||null;},
        createElement(){return {setAttribute(k,v){this[k]=v;}};},
        head:{appendChild(el){
            if(el.id)nodes.set(el.id,el);
            if(el.rel)nodes.set(`link[rel="${el.rel}"]`,el);
            if(el.name)nodes.set(`meta[name="${el.name}"]`,el);
        }}};
    const url='/atlas/concept/private-capital/';
    const page={title:'Reviewed title',getElementById(){return {
        dataset:{staticRendered:'true'},innerHTML:'<p>Reviewed definition and current claims</p>'
    };},querySelector(selector){return selector.startsWith('meta')?{content:'Reviewed description'}:
        {textContent:JSON.stringify({'@type':'DefinedTerm',name:'Reviewed concept'})};}};
    const context={console,document,URLSearchParams,DOMParser:class {parseFromString(){return page;}},
        fetch:async path=>{requests.push(path);return {ok:true,text:async()=>'<reviewed-page>'};},
        window:{location:{pathname:'/atlas/concept.html',search:'?id=concept:private-capital'},
        PrivateCapitalURL:{entityURL:()=>url,entityCanonicalURL:()=>`https://privatecapital.ir${url}`},
        PrivateCapitalDataLoader:{create(){return {loadCachedJSON:async path=>{
            requests.push(path);return {projection:'public',entities:[{
                id:'concept:private-capital',type:'Concept',lifecycleStatus:'PUBLISHED'
            }]};},loadRelationContract:async()=>{throw new Error('Must reuse the reviewed page');}};}}}};
    vm.createContext(context);vm.runInContext(fs.readFileSync('assets/js/atlas.js','utf8'),context);
    await context.window.Atlas.init();
    assert.strictEqual(root.innerHTML,page.getElementById().innerHTML);
    assert.deepStrictEqual(requests,['./entities/index.json',url]);
    assert.strictEqual(document.title,'Reviewed title');
    assert.strictEqual(nodes.get('link[rel="canonical"]').href,`https://privatecapital.ir${url}`);
    assert.strictEqual(JSON.parse(nodes.get('atlas-jsonld').textContent)['@type'],'DefinedTerm');
}
(async()=>{
    await rejected('organization:kayson-group',[{id:'organization:kayson-group',lifecycleStatus:'REVIEW'}]);
    await rejected('organization:absent',[]);
    await rejected('project:dadman',[]);
    await approved();
    console.log('Public legacy query rejection contract passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
