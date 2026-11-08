// Services are presentation content, never Research or canonical Atlas records.
const fs = require('fs');
const path = require('path');
const {spawnSync} = require('child_process');
const {createReferences, escape: e} = require('./public-reference');
const {discover} = require('./research-package');
const ROOT = path.resolve(__dirname, '../..');
const data = JSON.parse(fs.readFileSync(path.join(ROOT, 'corporate/content.json'), 'utf8'));
const route = row => `/corporate/${row.slug}/`;
const link = (url, label, attrs='') => `<a href="${e(url)}" ${attrs}>${label}</a>`;
const cta = (label='همکاری و طرح مسئله') => link('/corporate/collaboration/',label,'class="svc-button"');
const numbered = n => String(n).padStart(2,'0');
function references() {
    return createReferences({
        entities: JSON.parse(fs.readFileSync(path.join(ROOT,'atlas/entities/index.json'),'utf8')).entities,
        research: JSON.parse(fs.readFileSync(path.join(ROOT,'research/index.json'),'utf8')).research,
        structured: new Map(discover().map(({data})=>[data.id,data])),
        exists: url => {
            const file=path.join(ROOT,(url.endsWith('/')?url+'index.html':url).slice(1));
            return fs.existsSync(file)&&fs.statSync(file).isFile();
        }
    });
}
function searchForm() {
    // Reuse the site's search signature; search here stays within Services.
    const result=spawnSync(process.env.PYTHON||'python',['-c',"import sys;sys.path.insert(0,'tools');from kaavosh_markup import search_form;sys.stdout.buffer.write(search_form(action='/corporate/solutions/',home=True).encode('utf-8'))"],{cwd:ROOT,encoding:'utf8'});
    if(result.status!==0) throw Error(`Shared search markup failed: ${result.stderr}`);
    return result.stdout.replace(' data-kaavosh','').replace('مفهومی که در جست‌وجوی آن هستید…','مسئله یا راهکار مورد نظر شما…').replace('جست‌وجو در اطلس و پژوهش‌ها','جست‌وجو در راهکارهای خدمات شرکتی');
}
function header(active, context={url:'/corporate/',label:'خدمات شرکتی',shortLabel:'خدمات شرکتی'}) {
    const current=id=>active===id?'aria-current="page"':'';
    const navLabel=(full,short)=>`<span class="svc-label-full" aria-hidden="true">${full}</span><span class="svc-label-short" aria-hidden="true">${short}</span>`;
    const homeLabel=e(context.label).split(' ').map(word=>`<span>${word}</span>`).join(' ');
    const homeIcon='<svg class="svc-home-icon" viewBox="0 0 24 24" width="15" height="15" aria-hidden="true" focusable="false"><path d="m3 10 9-7 9 7M5 9v12h5v-7h4v7h5V9" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    const items=`${link('/corporate/partners/','شرکای ما',`aria-label="شرکای ما" ${current('partners')}`)}${link('/corporate/team/','تیم ما',current('team'))}<details class="svc-solutions-menu"${active==='solutions'||data.solutions.some(row=>row.slug===active)?' data-current="true"':''}><summary>راهکارها <span aria-hidden="true">⌄</span></summary><div class="svc-submenu">${link('/corporate/solutions/','همهٔ راهکارها',current('solutions'))}${data.solutions.map(row=>link(route(row),e(row.title),current(row.slug))).join('')}</div></details>${link('/corporate/collaboration/',navLabel('همکاری و طرح مسئله','همکاری<span class="svc-cooperation-tail"> با ما</span>'),'aria-label="همکاری و طرح مسئله" '+current('collaboration'))}${link('https://xsynplatform.ir/',navLabel('خدمات پیشرفتۀ اکسین','اکسین')+'<svg class="svc-lightning" viewBox="0 0 20 24" width="16" height="20" aria-hidden="true" focusable="false"><path fill="currentColor" d="M11.6 1 2.5 13.2h6L7.5 23 18 9.8h-6.2z"/></svg>','aria-label="خدمات پیشرفتۀ اکسین"')}`;
    return `<a class="svc-skip" href="#main">رفتن به محتوا</a><header class="svc-header"><div class="container svc-header-row"><nav class="svc-primary-nav" aria-label="پیمایش ${e(context.label)}">${items}</nav><div class="svc-identity"><a class="logo" href="/" aria-label="Private Capital — خانهٔ سایت اصلی"><img src="/assets/images/privatecapital.png" alt="" width="43" height="52"><span dir="ltr">Private Capital</span></a>${link(context.url,homeIcon+`<span class="svc-home-text">${homeLabel}</span>`,`class="svc-home" aria-label="خانهٔ ${e(context.label)}" ${current('home')}`)}</div></div></header>`;
}
function footer() {
    return fs.readFileSync(path.join(ROOT,'tools/templates/site-footer.html'),'utf8').trim();
}
function page(title,description,url,body,active='') {
    if(active!=='home') {
        const marker='<!-- services-intro-end -->';
        const boundary=body.indexOf(marker);
        if(boundary<0)throw Error(`Missing Services intro boundary: ${url}`);
        const prefix=body.slice(0,boundary),content=body.slice(boundary+marker.length);
        const result=spawnSync(process.env.PYTHON||'python',['tools/services_presentation.py'],{cwd:ROOT,input:JSON.stringify({body:content,url,has_search:body.includes('role="search"'),directory_empty:active==='partners'?!data.partners?.some(p=>p.visible===true):active==='team'?!data.team?.some(m=>m.visible===true):false}),encoding:'utf8'});
        if(result.status!==0)throw Error(`Services reading layout failed: ${result.stderr}`);
        body=prefix+result.stdout;
    }
    return `<!DOCTYPE html>
<!-- Generated by atlas/tools/build-services-pages.js; edit corporate/content.json or the builder. -->
<html lang="fa" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>${e(title)} | Private Capital</title><meta name="description" content="${e(description)}"><link rel="canonical" href="https://privatecapital.ir${url}"><link rel="stylesheet" href="/assets/css/style.css"><link rel="stylesheet" href="/assets/css/kaavosh.css"><link rel="stylesheet" href="/assets/css/exploration.css"><link rel="stylesheet" href="/assets/css/services.css"><link rel="stylesheet" href="/assets/css/site-footer.css"><link rel="icon" href="/assets/images/favicon.ico"><script src="/assets/js/site-navigation.js" defer></script><script src="/assets/js/services-ui.js" defer></script></head><body class="services-page">${header(active)}<main id="main" tabindex="-1">${body}</main>${footer()}</body></html>\n`;
}
function breadcrumb(title) {
    return `<div class="container svc-breadcrumb"><nav aria-label="مسیر صفحه">${link('/corporate/','خدمات شرکتی')}<span aria-hidden="true">/</span><span aria-current="page">${e(title)}</span></nav></div>`;
}
const mobileIntros={
    'در کنار تصمیم‌گیران شرکت':['کنار تصمیم‌گیران','همکاری با مالکان و مدیران شرکت‌ها'],
    'تیم ما':['آدم‌ها، پشت تصمیم‌ها','آشنایی با تیم تحلیل و همراهی شرکت‌ها'],
    'راهکارها':['از مسئله تا راهکار','مسیر متناسب با تصمیم شرکت را بیابید'],
    'از مسئله تا همکاری':['از مسئله تا همکاری','مراحل و شرایط همکاری را بشناسید'],
    'سرمایه و گذار مالکیت':['سرمایه و مالکیت روشن','تأمین منابع و تنظیم حقوق مالکان'],
    'معاملات و تملک':['از فرصت تا معامله','ارزیابی و ساختاردهی خرید و فروش شرکت'],
    'خلق ارزش و راهبری':['رشد با راهبری روشن','برنامهٔ رشد، مسئولیت‌ها و سنجش عملکرد'],
    'پژوهش و ارزیابی سرمایه‌گذاری':['شواهد برای تصمیم','بررسی فرصت، ارزش و ریسک سرمایه‌گذاری']
};
function intro(title,lead) {
    const [shortTitle,shortLead]=mobileIntros[title]||[title,lead];
    const introSearch=title==='راهکارها'?`<div class="svc-intro-search">${searchForm()}</div>`:'';
    return `<section class="svc-page-intro"><div class="container"><h1><span class="svc-intro-full">${e(title)}</span><span class="svc-intro-mobile"><span class="svc-quote" aria-hidden="true">“</span>${e(shortTitle)}</span></h1><p class="svc-lead"><span class="svc-intro-full">${e(lead)}</span><span class="svc-intro-mobile">${e(shortLead)}</span></p>${introSearch}</div></section><!-- services-intro-end -->`;
}
function heading(kicker,title,step) {
    return `<div class="svc-section-heading"><div>${kicker?`<p class="svc-kicker">${kicker}</p>`:''}<h2${step?` data-service-step="${e(step)}"`:""}>${title}</h2></div></div>`;
}
function decisionCard() {
    return `<aside class="svc-decision" aria-label="چارچوب تصمیم"><p class="svc-kicker">پیش از تعهد، روشن کنیم</p><h2>چه چیزی باید<br>در شرکت تغییر کند؟</h2><ol><li><span>۰۱</span><div><strong>سرمایه</strong><p>منابع، زمان و ظرفیت بازپرداخت</p></div></li><li><span>۰۲</span><div><strong>مالکیت</strong><p>حقوق، کنترل و تداوم رهبری</p></div></li><li><span>۰۳</span><div><strong>رشد</strong><p>اولویت، اجرا و سنجش نتیجه</p></div></li></ol><p class="svc-note">رویکرد پرایوت اکوئیتی: دیدن تصمیم مالی در کنار مالکیت و عملکرد واقعی کسب‌وکار.</p></aside>`;
}
function homePage() {
    return page(data.title,'نقطهٔ شروع تصمیم‌های سرمایه، مالکیت و رشد برای مالکان و مدیران شرکت‌های غیربورسی.','/corporate/',`<section class="svc-landing"><div class="container svc-hero-grid"><div class="svc-landing-intro"><p class="svc-title-badge">خدمات شرکتی</p><h1><span class="svc-quote" aria-hidden="true">“</span>سرمایه، مالکیت و رشد</h1><p><span class="svc-intro-full">برای مرحلهٔ بعدی شرکت، از یک تصمیم اصولی شروع کنید.</span><span class="svc-intro-mobile">راهکارهای سرمایه و رشد شرکت‌ها</span></p><div class="svc-landing-search">${searchForm()}</div>${link('/corporate/solutions/','مشاهدهٔ راهکارها','class="svc-text-link"')}</div>${decisionCard()}</div></section>`,'home');
}
function partnersPage() {
    const categories=[
        {id:'owners',title:'مالکان و مدیران',text:'توسعهٔ شرکت، ورود و خروج شریک، یا انتقال نسلی؛ تصمیم‌های سرمایه و رهبری باید به یک مسیر روشن برسند.'},
        {id:'investors',title:'سرمایه‌گذاران و خریداران',text:'ارزیابی فرصت، خرید یا مشارکت؛ از منطق اقتصادی معامله تا برنامهٔ پس از آن.'},
        {id:'lenders',title:'اعتباردهندگان',text:'شناخت کسب‌وکار، کیفیت جریان نقد و ظرفیت بازپرداخت؛ پیش از تعهد منابع.'}
    ];
    const partners=(data.partners||[]).filter(p=>p.visible===true);
    if(partners.some(p=>!categories.some(c=>c.id===p.category)))categories.push({id:'other',title:'سایر شرکا',text:'دیگر همکاری‌های تأییدشده.'});
    const refs=partners.length?references():null;
    const directory=categories.map(category=>{
        const members=partners.filter(p=>category.id==='other'?!categories.some(c=>c.id!=='other'&&c.id===p.category):p.category===category.id);
        return `<section class="svc-partner-group" aria-labelledby="partners-${category.id}"><h2 id="partners-${category.id}" data-service-step="${e(category.title)}">${e(category.title)}</h2>${members.length?`<div class="svc-partner-grid">${members.map(p=>renderPartner(p,refs)).join('')}</div>`:'<div class="svc-directory-empty"><p>معرفی شرکای این دسته به‌زودی منتشر می‌شود.</p></div>'}</section>`;
    }).join('');
    return page('شرکای تجاری ما','همکاری با مالکان، مدیران، سرمایه‌گذاران، خریداران و اعتباردهندگان در تصمیم‌های شرکت.','/corporate/partners/',`${breadcrumb('شرکای تجاری ما')}${intro('در کنار تصمیم‌گیران شرکت','اولویت ما مالکان و مدیران شرکت‌های غیربورسی، به‌ویژه شرکت‌های صنعتی‌اند.')}<section class="svc-section"><div class="container svc-audiences">${categories.map(category=>`<article><h2>${link('#partners-'+category.id,e(category.title))}</h2><p>${e(category.text)}</p>${link('#partners-'+category.id,'مشاهدهٔ این دسته <span aria-hidden="true">↓</span>')}</article>`).join('')}</div></section><section class="svc-section svc-partner-directory"><div class="container">${directory}</div></section>`,'partners');
}
function renderPartner(partner,refs) {
    const label=/^(?:person|organization):/.test(partner.entityRef||'')?refs.inline({entityRef:partner.entityRef,label:partner.name}):e(partner.name);
    const validLogo=typeof partner.logo==='string'&&/^\/assets\/images\/[\w/-]+\.(?:png|jpe?g|webp|avif)$/i.test(partner.logo)&&fs.existsSync(path.join(ROOT,partner.logo.slice(1)));
    const logo=validLogo?`<img src="${e(partner.logo)}" alt="${e(partner.name)}" loading="lazy" width="400" height="225">`:`<span aria-hidden="true">${e(partner.name.trim().slice(0,1))}</span>`;
    return `<article class="svc-partner"><div class="svc-partner-logo">${logo}</div><h3>${label}</h3>${partner.description?`<p>${e(partner.description)}</p>`:''}</article>`;
}
function renderTeamMember(member,refs) {
    const name=member.entityRef?.startsWith('person:')?refs.inline({entityRef:member.entityRef,label:member.name}):e(member.name);
    const portrait=typeof member.portrait==='string'&&/^\/assets\/images\/[\w/-]+\.(?:png|jpe?g|webp|avif)$/i.test(member.portrait)&&fs.existsSync(path.join(ROOT,member.portrait.slice(1)))?`<img src="${e(member.portrait)}" alt="${e(member.name)}" loading="lazy" width="480" height="600">`:`<div class="svc-portrait-initial" aria-hidden="true">${e(member.name.trim().slice(0,1))}</div>`;
    return `<article class="svc-team-member"><div class="svc-portrait">${portrait}</div><h3>${name}</h3><p>${e(member.role||'')}</p></article>`;
}
function teamPage(refs) {
    const members=(data.team||[]).filter(m=>m.visible===true);
    const groups=[...new Set(members.map(m=>m.group||'تیم ما'))];
    const body=members.length?groups.map(group=>`<section class="svc-team-section"><div class="container"><h2>${e(group)}</h2><div class="svc-team-grid">${members.filter(m=>(m.group||'تیم ما')===group).map(m=>renderTeamMember(m,refs)).join('')}</div></div></section>`).join(''):`<section class="svc-section"><div class="container"><div class="svc-team-empty"><span class="svc-team-mark" aria-hidden="true">PC</span><div><h2>آدم‌ها، پشت تصمیم‌ها</h2><p>معرفی اعضای تیم به‌زودی در این صفحه منتشر می‌شود.</p></div></div></div></section>`;
    return page('تیم ما','آشنایی با افرادی که در تحلیل، طراحی و همراهی تصمیم‌های شرکت نقش دارند.','/corporate/team/',`${breadcrumb('تیم ما')}${intro('تیم ما','تحلیل دقیق، نگاه مستقل و همراهی مسئولانه.','PRIVATE CAPITAL')}<div id="team-directory" data-service-step="معرفی اعضای تیم">${body}</div>`,'team');
}
function paths() {
    return `<div class="svc-paths">${data.solutions.map(row=>link(route(row),`<div><h2>${e(row.title)}</h2><p>${e(row.summary)}</p></div><span class="svc-arrow" aria-hidden="true">↗</span>`,`class="svc-path" data-service-card data-search="${e([row.title,row.summary,row.situation,...row.work].join(' '))}"`)).join('')}</div>`;
}
function solutionsPage() {
    const situations=[['سرمایهٔ توسعه',0],['ورود یا خروج شریک',0],['انتقال نسلی',0],['خرید یا فروش شرکت',1],['رشد پس از سرمایه‌گذاری',2],['ارزیابی فرصت',3]];
    return page('راهکارها','چهار مسیر برای تصمیم‌های سرمایه، مالکیت، معاملات و رشد شرکت.','/corporate/solutions/',`${breadcrumb('راهکارها')}${intro('راهکارها','از مسئلهٔ شرکت شروع کنید؛ مسیر متناسب با تصمیم پیش رو را پیدا کنید.')}<section class="svc-section"><div class="container"><p class="svc-note" data-service-status role="status" aria-live="polite"></p><div id="service-solutions" data-service-step="یافتن راهکار متناسب" data-service-results>${paths()}</div><div class="svc-search-empty" data-service-empty hidden><h2>راهکاری با این عبارت پیدا نشد</h2><p>عبارت کوتاه‌تری بنویسید یا مسئلهٔ خود را با ما در میان بگذارید.</p>${cta()} ${link('/corporate/solutions/','همهٔ راهکارها')}</div><noscript><p class="svc-note">چهار راهکار در همین صفحه در دسترس‌اند؛ برای جست‌وجوی متنی، JavaScript مرورگر باید فعال باشد.</p></noscript></div></section><section class="svc-section svc-tinted"><div class="container">${heading('','از کدام تصمیم شروع می‌کنید؟','انتخاب بر اساس موقعیت شرکت')}<div class="svc-situation-links">${situations.map(([title,i])=>link(route(data.solutions[i]),title)).join('')}</div></div></section>`,'solutions');
}
function collaborationPage() {
    const stages=[['شناخت مسئله','هدف مالکان، موقعیت شرکت و تصمیم پیش رو را روشن می‌کنیم.'],['بررسی شواهد','اطلاعات موجود، کیفیت داده و ابهام‌ها را بررسی می‌کنیم.'],['مقایسهٔ گزینه‌ها','سناریوهای سرمایه، ارزش، ریسک و اجرا را کنار هم می‌گذاریم.'],['تعریف مأموریت و اجرا','دامنه، خروجی، مسئولیت، زمان و حق‌الزحمه مکتوب می‌شود.'],['پایش','پیشرفت و فرض‌های تصمیم را در موعدهای توافق‌شده مرور می‌کنیم.']];
    return page('همکاری و طرح مسئله','از گفت‌وگوی نخست تا تعریف مأموریت، اجرا و پایش؛ با دامنه و مسئولیت روشن.','/corporate/collaboration/',`${breadcrumb('همکاری و طرح مسئله')}${intro('از مسئله تا همکاری','ابتدا تصمیم پیش رو را روشن کنیم؛ سپس دربارهٔ مأموریت توافق کنیم.','همکاری و طرح مسئله')}<section class="svc-section"><div class="container"><div class="svc-contact-panel"><div><p class="svc-kicker">گفت‌وگوی نخست</p><h2 data-service-step="آماده‌شدن برای گفت‌وگوی نخست">چه چیزی باید در شرکت تغییر کند؟</h2><p>شرح کوتاهی از فعالیت شرکت، موضوع تصمیم و هدف خود آماده کنید. در این مرحله اطلاعات عمومی و غیرمحرمانه کافی است.</p></div>${link('/contact.html','طرح مسئله و تماس','class="svc-button"')}</div></div></section><section class="svc-section svc-tinted"><div class="container">${heading('روش همکاری','از شناخت مسئله تا پایش','مراحل همکاری')}<ol class="svc-process">${stages.map(([title,text],i)=>`<li><span>${numbered(i+1)}</span><h3>${title}</h3><p>${text}</p></li>`).join('')}</ol></div></section><section class="svc-section"><div class="container svc-working-notes"><article><h2 data-service-step="شرایط پذیرش مأموریت">پذیرش مأموریت</h2><p>هدف مشخص، دسترسی قانونی به اطلاعات کافی، همکاری تصمیم‌گیران و نبود تعارض منافع حل‌نشده، مبنای بررسی همکاری است. دامنه، خروجی، زمان و حق‌الزحمه پیش از شروع توافق می‌شوند.</p></article><article><h2 data-service-step="محرمانگی اطلاعات">محرمانگی</h2><p>اسناد حساس را از طریق سایت ارسال نکنید. در صورت توافق بر ادامه، شرایط محرمانگی و شیوهٔ تبادل امن اطلاعات مشخص می‌شود.</p></article><article><h2 data-service-step="حدود مسئولیت‌ها">حدود مسئولیت</h2><p>نقش ما تحلیل، مشاوره، ساختاردهی و همراهی در مأموریت توافق‌شده است. تأمین منابع، بازده یا تکمیل معامله تضمین نمی‌شود.</p></article><article><h2>خدمات تخصصی</h2><p>مسئولیت تصمیم نهایی با تصمیم‌گیر است. امور حقوقی، مالیاتی و خدمات نیازمند مجوز، با متخصص واجد صلاحیت و توافق روشن هماهنگ می‌شوند.</p></article></div></section>`,'collaboration');
}
function solutionPage(row,index) {
    const list=values=>`<ul class="svc-list">${values.map(value=>`<li>${e(value)}</li>`).join('')}</ul>`;
    return page(row.title,row.summary,route(row),`${breadcrumb(row.title)}${intro(row.title,row.subtitle,`راهکار ${numbered(index+1)} / ${data.title}`)}<div class="container svc-solution-body"><div><section class="svc-section">${heading('موقعیت','برای چه موقعیتی؟','آیا این خدمت مناسب مسئلهٔ من است؟')}<p>${e(row.situation)}</p></section><section id="decision" class="svc-section">${heading('تصمیم','چه چیزی باید روشن شود؟','موضوعات اصلی تصمیم')}${list(row.decision)}</section><section class="svc-section">${heading('مأموریت','کارهای ما','چه کارهایی انجام می‌دهیم؟')}${list(row.work)}</section><section class="svc-section">${heading('حدود خدمت','توافق روشن، مسئولیت مشخص','حدود و شرایط خدمت')}<p>${e(row.scope)}</p></section></div><aside class="svc-deliverables"><p class="svc-kicker">حاصل همکاری</p><h2 data-service-step="چه خروجی دریافت می‌کنم؟">خروجی قابل‌تحویل</h2>${list(row.outputs)}<p class="svc-note">ترکیب نهایی خروجی‌ها، زمان و مسئولیت‌ها در پیشنهاد همکاری تعیین می‌شود.</p>${cta('طرح مسئله و روش همکاری')}</aside></div><div class="container svc-next"><span>دیگر مسیرهای خدمات</span><nav aria-label="راهکارهای دیگر">${data.solutions.filter(x=>x!==row).map(x=>link(route(x),e(x.title))).join('')}</nav></div>`,row.slug);
}
function build() {
    const outputs=new Map([['corporate/index.html',homePage()],['corporate/partners/index.html',partnersPage()],['corporate/team/index.html',teamPage(references())],['corporate/solutions/index.html',solutionsPage()],['corporate/collaboration/index.html',collaborationPage()],...data.solutions.map((row,i)=>[`corporate/${row.slug}/index.html`,solutionPage(row,i)])]);
    for(const [relative,html] of outputs){const file=path.join(ROOT,relative);fs.mkdirSync(path.dirname(file),{recursive:true});if(!fs.existsSync(file)||fs.readFileSync(file,'utf8')!==html)fs.writeFileSync(file,html,'utf8');}
    console.log(`Generated ${outputs.size} Services pages.`);
}
if(require.main===module)build();
module.exports={build,renderTeamMember,renderPartner,header,footer,searchForm};
