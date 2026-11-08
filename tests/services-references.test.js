const assert=require('assert/strict');
const {createReferences}=require('../atlas/tools/public-reference');
const base={
    entities:[
        {id:'concept:approved',type:'Concept',lifecycleStatus:'PUBLISHED'},
        {id:'concept:review',type:'Concept',lifecycleStatus:'REVIEW'},
        {id:'concept:absent',type:'Concept',lifecycleStatus:'PUBLISHED'},
        {id:'sector:unrouted',type:'Sector',lifecycleStatus:'PUBLISHED'}
    ],
    research:[
        {id:'research:approved',url:'/articles/approved.html',status:'PUBLISHED'},
        {id:'research:legacy',url:'/articles/legacy.html',status:'PUBLISHED',sourceMode:'legacy-html'},
        {id:'research:withheld',url:'/articles/withheld.html',status:'REVIEW'},
        {id:'research:mismatch',url:'/articles/mismatch.html',status:'PUBLISHED'},
        {id:'research:absent',url:'/articles/absent.html',status:'PUBLISHED',sourceMode:'legacy-html'},
        {id:'research:missing-source',url:'/articles/missing-source.html',status:'PUBLISHED'}
    ],
    structured:new Map([
        ['research:approved',{status:'PUBLISHED',url:'/articles/approved.html'}],
        ['research:mismatch',{status:'REVIEW',url:'/articles/mismatch.html'}]
    ]),
    exists:url=>!url.includes('absent')
};
const refs=createReferences(base);
assert.equal(refs.resolve({entityRef:'concept:approved'}),'/atlas/concept/approved/');
for(const id of ['concept:review','concept:absent','concept:unknown','sector:unrouted','../../bad']) {
    assert.equal(refs.resolve({entityRef:id}),null,id);
    assert.equal(refs.inline({entityRef:id,label:'متن ساده'}),'متن ساده');
}
assert.equal(refs.resolve({researchRef:'research:approved'}),'/articles/approved.html');
assert.equal(refs.resolve({researchRef:'research:legacy'}),'/articles/legacy.html');
for(const id of ['research:withheld','research:mismatch','research:absent','research:unknown','research:missing-source']) assert.equal(refs.resolve({researchRef:id}),null,id);
assert.equal(refs.inline(['درباره ',{entityRef:'concept:approved',label:'مفهوم'},' بیشتر بدانید.']),'درباره <a href="/atlas/concept/approved/">مفهوم</a> بیشتر بدانید.');
assert.equal(refs.inline({entityRef:'concept:unknown',label:'<img onerror="bad">'}),'&lt;img onerror=&quot;bad&quot;&gt;');
const missing=createReferences({...base,exists:()=>false});
assert.equal(missing.resolve({entityRef:'concept:approved'}),null);
assert.equal(missing.resolve({researchRef:'research:approved'}),null);
console.log('Services references: explicit identity, publication, destination, structured/legacy source and escaping passed.');
