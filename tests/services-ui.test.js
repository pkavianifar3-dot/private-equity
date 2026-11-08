const assert=require('assert/strict');
const {matches}=require('../assets/js/services-ui');
assert(matches('طراحی سرمایه و ترکیب مالکیت','سرمایه مالکیت'));
assert(matches('سرمایه‌گذاری خصوصی','سرمايه گذاري'));
assert(matches('مالکان شرکت','مالكان'));
assert(matches('خلق ارزش',''));
assert(!matches('معاملات و تملک','اعتباردهندگان'));
assert(!matches('خرید شرکت','<script>'));
const {createReferences}=require('../atlas/tools/public-reference');
const {renderTeamMember}=require('../atlas/tools/build-services-pages');
const refs=createReferences({entities:[{id:'person:approved',type:'Person',lifecycleStatus:'PUBLISHED'},{id:'person:review',type:'Person',lifecycleStatus:'REVIEW'}],research:[],exists:url=>!url.includes('missing')});
const member={name:'نام آزمایشی',role:'تحلیل',portrait:'/no-image.jpg'};
assert(renderTeamMember({...member,entityRef:'person:approved'},refs).includes('href="/atlas/person/approved/"'));
for(const entityRef of ['person:review','person:missing','organization:approved',undefined]){
    const html=renderTeamMember({...member,entityRef},refs);
    assert(!html.includes('<a '));
    assert(html.includes(member.name));
    assert(!html.includes('<img'));
}
assert(!renderTeamMember({...member,name:'<script>bad</script>'},refs).includes('<script>'));
console.log('Services search matching and explicit public Person references passed.');

const {renderPartner}=require('../atlas/tools/build-services-pages');
const partnerRefs=createReferences({entities:[{id:'organization:approved',type:'Organization',lifecycleStatus:'PUBLISHED'},{id:'organization:review',type:'Organization',lifecycleStatus:'REVIEW'},{id:'organization:missing',type:'Organization',lifecycleStatus:'PUBLISHED'}],research:[],exists:url=>!url.includes('missing')});
const partner={name:'Fixture partner',description:'Approved description'};
assert(renderPartner({...partner,entityRef:'organization:approved'},partnerRefs).includes('href="/atlas/organization/approved/"'));
for(const entityRef of ['organization:review','organization:missing','organization:unknown','concept:approved',undefined])assert(!renderPartner({...partner,entityRef},partnerRefs).includes('<a '));
assert(!renderPartner({...partner,name:'<script>bad</script>',logo:'../../private.png'},partnerRefs).includes('<script>'));
console.log('Partner identity, publication, missing destination and safe fallback passed.');
