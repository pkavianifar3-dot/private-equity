const assert=require('node:assert/strict');
const {test}=require('node:test');
const {brandScrollState}=require('../assets/js/site-navigation');
const initial={hidden:false,lastY:0,direction:0,distance:0};
const mobile={mobile:true,offset:52};

test('brand collapses after deliberate downward movement and returns after a short upward movement',()=>{
    let state=brandScrollState(initial,60,mobile);
    assert.equal(state.hidden,false);
    state=brandScrollState(state,160,mobile);
    assert.equal(state.hidden,true);
    state=brandScrollState(state,158,mobile);
    assert.equal(state.hidden,true);
    state=brandScrollState(state,152,mobile);
    assert.equal(state.hidden,false);
});

test('direction changes reset travel so small scroll jitter does not flicker the brand',()=>{
    let state=brandScrollState(initial,200,mobile);
    for(const position of [198,199,197,200,196,201]){
        state=brandScrollState(state,position,mobile);
        assert.equal(state.hidden,true);
    }
    state=brandScrollState(state,192,mobile);
    assert.equal(state.hidden,false);
    state=brandScrollState(state,193,mobile);
    assert.equal(state.hidden,false);
    state=brandScrollState(state,212,mobile);
    assert.equal(state.hidden,true);
});

test('top of page, desktop and active header interaction always reveal the brand',()=>{
    const hidden=brandScrollState(initial,300,mobile);
    assert.equal(brandScrollState(hidden,-20,mobile).hidden,false);
    assert.equal(brandScrollState(hidden,40,mobile).hidden,false);
    assert.equal(brandScrollState(hidden,400,{...mobile,mobile:false}).hidden,false);
    assert.equal(brandScrollState(hidden,400,{...mobile,locked:true}).hidden,false);
});
