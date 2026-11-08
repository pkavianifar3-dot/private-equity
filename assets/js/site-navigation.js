/* Native page navigation; no application-menu roles or hidden mobile destinations. */
(function () {
    'use strict';
    function brandScrollState(previous, position, {mobile, locked=false, offset=52}) {
        const lastY=Math.max(0,position);
        if(!mobile||locked||lastY<=offset+12)return {hidden:false,lastY,direction:0,distance:0};
        const delta=lastY-previous.lastY;
        if(!delta)return {...previous,lastY};
        const direction=delta>0?1:-1;
        const distance=direction===previous.direction?previous.distance+Math.abs(delta):Math.abs(delta);
        const hidden=direction>0&&distance>=20?true:direction<0&&distance>=8?false:previous.hidden;
        return {hidden,lastY,direction,distance};
    }
    if(typeof module!=='undefined')module.exports={brandScrollState};
    if(typeof document==='undefined')return;
    const header=document.querySelector('body>header');
    if(header){
        const mobile=window.matchMedia('(max-width:760px)');
        const nav=header.querySelector('nav');
        const identity=header.querySelector('.svc-identity')||header.querySelector('.logo');
        const heightProperty=document.body.classList.contains('services-page')?'--svc-header-height':'--site-header-height';
        let state={hidden:false,lastY:window.scrollY,direction:0,distance:0};
        let offset=0;
        let height=0;
        let scheduled=false;
        function render(){
            header.toggleAttribute('data-brand-hidden',state.hidden);
            document.body.style.setProperty(heightProperty,`${height-(state.hidden?offset:0)}px`);
        }
        function update(){
            scheduled=false;
            const position=Math.min(window.scrollY,Math.max(0,document.documentElement.scrollHeight-window.innerHeight));
            const locked=!!header.querySelector('details[open]')||!!identity?.contains(document.activeElement);
            state=brandScrollState(state,position,{mobile:mobile.matches,locked,offset});
            render();
        }
        function schedule(){if(!scheduled){scheduled=true;requestAnimationFrame(update);}}
        function measure(){
            const rect=header.getBoundingClientRect();
            height=Math.ceil(rect.height);
            offset=nav?Math.round(nav.getBoundingClientRect().top-rect.top):0;
            header.style.setProperty('--header-brand-offset',`${offset}px`);
            update();
        }
        header.setAttribute('data-scroll-header','');
        measure();
        if(typeof ResizeObserver!=='undefined')new ResizeObserver(measure).observe(header);
        window.addEventListener('scroll',schedule,{passive:true});
        window.addEventListener('resize',measure,{passive:true});
        mobile.addEventListener('change',measure);
        header.addEventListener('toggle',schedule,true);
        header.addEventListener('focusin',()=>{
            state={hidden:false,lastY:window.scrollY,direction:0,distance:0};
            render();
        });
    }
    const menus = [...document.querySelectorAll('details.development-menu')];
    for (const menu of menus) {
        for (const link of menu.querySelectorAll('.development-submenu a')) {
            if (location.pathname === new URL(link.href).pathname) {
                link.setAttribute('aria-current', 'page');
                menu.setAttribute('data-current', 'true');
            }
        }
    }
    document.addEventListener('keydown', event => {
        if (event.key !== 'Escape') return;
        const menu = menus.find(item => item.open && item.contains(document.activeElement));
        if (menu) {
            menu.open = false;
            menu.querySelector('summary').focus();
            event.preventDefault();
        }
    });
    document.addEventListener('click', event => {
        for (const menu of menus) if (menu.open && !menu.contains(event.target)) menu.open = false;
    });
})();
