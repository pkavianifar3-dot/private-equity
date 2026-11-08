/* Progressive enhancement for Services; links and native menus work without JS. */
(function () {
    'use strict';
    function normalize(value) {
        return String(value).normalize('NFKC').toLowerCase().replace(/ي/g,'ی').replace(/ك/g,'ک').replace(/[\u064b-\u065f]/g,'').replace(/[\u200c\u200f\u200e]/g,' ').replace(/[^\p{L}\p{N}]+/gu,' ').trim();
    }
    function matches(text,query) {
        const haystack=normalize(text);
        return normalize(query).split(/\s+/).filter(Boolean).every(word=>haystack.includes(word));
    }
    if(typeof module!=='undefined')module.exports={normalize,matches};
    if(typeof document==='undefined')return;
    const menus=[...document.querySelectorAll('.services-page header details')];
    document.addEventListener('keydown',event=>{
        if(event.key!=='Escape')return;
        const current=menus.filter(menu=>menu.open&&menu.contains(document.activeElement)).pop();
        if(current){current.open=false;current.querySelector('summary').focus();event.preventDefault();}
    });
    document.addEventListener('click',event=>{for(const menu of menus)if(menu.open&&!menu.contains(event.target))menu.open=false;});
    const guide=document.querySelector('[data-service-guide]');
    if(guide){
        const mobile=window.matchMedia('(max-width:980px)');
        const summary=guide.querySelector('summary');
        const entries=[...guide.querySelectorAll('[data-service-guide-link]')].map(link=>({link,target:document.getElementById(link.hash.slice(1))})).filter(entry=>entry.target);
        function responsiveGuide(){guide.open=!mobile.matches;}
        responsiveGuide();
        mobile.addEventListener('change',responsiveGuide);
        summary.addEventListener('click',event=>{if(!mobile.matches)event.preventDefault();});
        // The guide remains native and all destinations work without JavaScript.
        // A passive, frame-limited scroll update only adds the current-section cue.
        let scheduled=false;
        function markSection(){
            scheduled=false;
            const offset=Math.max(80,(document.querySelector('header')?.getBoundingClientRect().bottom||86)+24);
            let current=null;
            for(const entry of entries)if(entry.target.getBoundingClientRect().top<=offset)current=entry;
            if(window.scrollY+window.innerHeight>=document.documentElement.scrollHeight-2){
                for(const entry of entries)if(entry.target.getBoundingClientRect().top<window.innerHeight)current=entry;
            }
            for(const entry of entries){
                if(entry===current)entry.link.setAttribute('aria-current','location');
                else entry.link.removeAttribute('aria-current');
            }
        }
        function scheduleSection(){if(!scheduled){scheduled=true;requestAnimationFrame(markSection);}}
        window.addEventListener('scroll',scheduleSection,{passive:true});
        window.addEventListener('resize',scheduleSection,{passive:true});
        window.addEventListener('hashchange',scheduleSection);
        markSection();
    }
    const results=document.querySelector('[data-service-results]');
    if(!results)return;
    const form=document.querySelector('form[role="search"]'),input=form.elements.q;
    const cards=[...results.querySelectorAll('[data-service-card]')];
    const status=document.querySelector('[data-service-status]'),empty=document.querySelector('[data-service-empty]');
    function render(updateURL=false){
        const query=input.value.trim();let count=0;
        for(const card of cards){card.hidden=!matches(card.dataset.search,query);if(!card.hidden)count++;}
        status.textContent=query?`${count.toLocaleString('fa-IR')} راهکار برای «${query}»`:'';
        empty.hidden=count!==0;
        if(updateURL){const url=new URL(location.href);if(query)url.searchParams.set('q',query);else url.searchParams.delete('q');url.searchParams.delete('scope');history.replaceState(null,'',url.pathname+url.search);}
    }
    function fromURL(){input.value=new URLSearchParams(location.search).get('q')||'';render();}
    form.addEventListener('submit',event=>{event.preventDefault();render(true);});
    input.addEventListener('input',()=>render(true));
    window.addEventListener('popstate',fromURL);
    fromURL();
})();
