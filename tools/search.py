"""Derived Kaavosh files. Inputs are an isolated approved public staging site."""
from pathlib import Path
from html.parser import HTMLParser
from html import escape
from hashlib import sha256
import gzip
import json
import re
import subprocess
import tempfile
import unicodedata

ENGINE_VERSION = '1.5.2'
_cache = {}
VOID = {'img','meta','link','input','br','hr','source','wbr','area','base','col','embed','param','track'}
EXCLUDE = {'cta','explore-rail','atlas-identity-card','atlas-provenance-section','atlas-inline-sources',
           'atlas-source-ref','atlas-meta','atlas-claim-meta','atlas-claim-label','atlas-status',
           'atlas-overview-link','atlas-data-quality','article-author','research-byline',
           'research-bibliography','citation-bibliography','research-sources','research-note-ref',
           'citation-inline','article-cta','atlas-provenance-card'}

class Element:
    def __init__(self, tag='root', attrs=None):
        self.tag=tag;self.attrs=attrs or {};self.children=[]
    def find(self, predicate):
        found=[self] if predicate(self) else []
        for child in self.children:
            if isinstance(child,Element):found.extend(child.find(predicate))
        return found
    def text(self):
        if self.tag in {'nav','aside','script','style','footer','form','button'} or EXCLUDE.intersection(self.attrs.get('class','').split()):return ''
        if self.attrs.get('id') in {'research-bibliography','research-sources'}:return ''
        if self.tag=='a' and self.attrs.get('href','').split('?')[0] in {'/contact.html','../contact.html','/services.html','../services.html','/articles.html','../articles.html'}:return ''
        return ' '.join(c.text() if isinstance(c,Element) else c for c in self.children)

class Tree(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True);self.root=Element();self.stack=[self.root];self.feed(text)
    def handle_starttag(self, tag, attrs):
        e=Element(tag,dict(attrs));self.stack[-1].children.append(e)
        if tag not in VOID:self.stack.append(e)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:self.stack=self.stack[:i];return
    def handle_data(self, text):self.stack[-1].children.append(text)

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def clean(text):return re.sub(r'\s+',' ',text).strip()
def normalize(text):
    text=unicodedata.normalize('NFKC',text).lower().translate(str.maketrans({'ي':'ی','ى':'ی','ك':'ک','ۀ':'ه','ة':'ه'}))
    text=''.join(str(unicodedata.digit(c)) if c.isdecimal() else c for c in text)
    return clean(re.sub('[\u064b-\u065f\u0670\u0640]','',text).replace('\u200c',' '))
def short(text, length=240):
    text=clean(text)
    return text if len(text)<=length else text[:length].rsplit(' ',1)[0]+'…'
def fa(value):return value.get('fa','') if isinstance(value,dict) else value or ''
def file_for(url):return url.lstrip('/')+('index.html' if url.endswith('/') else '')

def documents(root, stage):
    catalog=read(stage/'atlas/catalog/index.json')['entities']
    registry=read(root/'research/index.json')['research']
    docs=[];bodies={};public_ids={e['id'] for e in catalog}
    for e in catalog:
        if e['lifecycleStatus']!='PUBLISHED' or not e.get('route'):raise ValueError('Search refuses non-public Entity '+e['id'])
        tree=Tree((stage/file_for(e['route'])).read_text(encoding='utf-8')).root
        mains=tree.find(lambda x:'atlas-primary' in x.attrs.get('class','').split())
        if len(mains)!=1:raise ValueError(e['id']+': missing unique public Entity content')
        summaries=tree.find(lambda x:'atlas-summary' in x.attrs.get('class','').split())
        bodies[e['id']]=clean(mains[0].text())
        docs.append(dict(id=e['id'],kind='concept' if e['type']=='Concept' else 'entity',scope='atlas',type=e['type'],
                         title=e['name']['fa'],english=e['name'].get('en',''),aliases=e.get('aliases',[]),
                         url=e['route'],summary=short(summaries[0].text()) if summaries else ''))
    packages={}
    for p in (root/'research/content').rglob('research.json'):
        r=read(p);packages[r['id']]=r
    for r in registry:
        if r['status']!='PUBLISHED':continue
        tree=Tree((stage/file_for(r['url'])).read_text(encoding='utf-8')).root
        article=tree.find(lambda x:x.tag=='article')
        titles=tree.find(lambda x:x.tag=='h1')
        if not article or len(titles)!=1:raise ValueError(r['id']+': missing public article/title')
        package=packages.get(r['id'],{}) if r.get('sourceMode')!='legacy-html' else {}
        # Only an approved registry record can select structured presentation.
        if package and package.get('status')!='PUBLISHED':raise ValueError(r['id']+': registry/package publication mismatch')
        paragraphs=article[0].find(lambda x:x.tag=='p' and bool(x.text().strip()))
        plain=[clean(p.text()) for p in paragraphs if not clean(p.text()).startswith(('نویسنده:','تاریخ انتشار:'))]
        summary=fa(package.get('summary')) or (plain[0] if plain else '')
        d=dict(id=r['id'],kind='research',scope='research',type='Research',title=fa(package.get('title')) or clean(titles[0].text()),
               english=package.get('title',{}).get('en',''),aliases=[],url=r['url'],summary=short(summary))
        presentation=package.get('presentation',{})
        if presentation.get('byline'):d['byline']=presentation['byline']
        if presentation.get('coverSrc'):
            cover=presentation['coverSrc']
            if not cover.startswith('/assets/images/') or not (stage/cover.lstrip('/')).is_file():raise ValueError('Search cover outside public staging')
            d['cover']=cover;d['coverAlt']=presentation.get('coverAlt','')
        primary=package.get('primaryEntityRef')
        if primary in public_ids:d['primaryEntityId']=primary
        docs.append(d);bodies[d['id']]=clean(article[0].text())
    if len({d['id'] for d in docs})!=len(docs) or len({d['url'] for d in docs})!=len(docs):raise ValueError('Duplicate search identity or URL')
    return sorted(docs,key=lambda d:d['id']),bodies

def card(d, extra=''):
    label={'concept':'مفهوم','entity':{'Person':'شخص','Organization':'سازمان','Investment':'سرمایه‌گذاری'}.get(d['type'],'مدخل'),'research':'پژوهش'}[d['kind']]
    english=f'<bdi dir="ltr">{escape(d["english"])}</bdi>' if d.get('english') and d['scope']=='atlas' else ''
    return f'<a class="discovery-card {extra}" href="{escape(d["url"])}"><span class="discovery-card-meta">{label} {english}</span><h3>{escape(d["title"])}</h3><p>{escape(d["summary"])}</p><span class="discovery-card-link">{ "مطالعه پژوهش" if d["scope"]=="research" else "شناخت این مدخل" } <span aria-hidden="true">←</span></span></a>'

def home_html(root, docs):
    config=read(root/'tools/search-home.json');by_id={d['id']:d for d in docs}
    featured=by_id.get(config['featuredResearchRef'])
    if not featured or featured['scope']!='research':raise ValueError('Featured Research is not approved/public')
    concepts=[by_id[eid] for eid in config['conceptOrder'] if eid in by_id and by_id[eid]['kind']=='concept']
    # A withdrawn concept is omitted; curation never grants publication.
    related=[d for d in docs if d.get('primaryEntityId')=='concept:private-capital']
    paths=[]
    for t,label,description in [('Concept','مفاهیم','تعریف‌ها، دامنه و تمایزها'),('Organization','سازمان‌ها','شناخت بازیگران و ساختارها'),('Person','اشخاص','افراد و ارتباط‌های مستند')]:
        count=sum(d['type']==t for d in docs)
        if count:paths.append(f'<a class="discovery-path" href="/atlas/explore/?type={t}"><span>{label}</span><span class="discovery-path-count">{count}</span><p>{description}</p></a>')
    atlas=(root/'atlas/index.html').read_text(encoding='utf-8').replace('<!--KAAVOSH_PATHS-->',''.join(paths)).replace('<!--KAAVOSH_CONCEPTS-->',''.join(card(d) for d in concepts))
    atlas=atlas.replace('<!--KAAVOSH_RESEARCH-->',''.join(f'<a class="discovery-reading-link" href="{escape(d["url"])}">{escape(d["title"])} <span aria-hidden="true">←</span></a>' for d in related))
    cover=f'<figure class="research-feature-cover"><img src="{escape(featured["cover"])}" alt="{escape(featured.get("coverAlt",""))}" width="800" height="560"></figure>' if featured.get('cover') else ''
    byline=f'<p class="discovery-byline">{escape(featured["byline"])}</p>' if featured.get('byline') else ''
    feature=f'<div class="research-feature-text"><span class="discovery-eyebrow">پژوهش منتخب · انتخاب تحریریه</span><h2><a href="{escape(featured["url"])}">{escape(featured["title"])}</a></h2><p>{escape(featured["summary"])}</p>{byline}<a class="discovery-primary-link" href="{escape(featured["url"])}">مطالعه پژوهش <span aria-hidden="true">←</span></a></div>{cover}'
    research=(root/'articles.html').read_text(encoding='utf-8').replace('<!--KAAVOSH_FEATURE-->',feature)
    research=research.replace('<!--KAAVOSH_ARTICLES-->',''.join(card(d,'research-list-card') for d in docs if d['scope']=='research' and d['id']!=featured['id']))
    return {'atlas/index.html':atlas.encode('utf-8'),'articles.html':research.encode('utf-8')}

def compile_index(root, docs, bodies):
    key=sha256(json.dumps([docs,bodies,ENGINE_VERSION],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    if key in _cache:return _cache[key]
    installed_root=Path(__file__).resolve().parents[1]
    binary=installed_root/'node_modules/.bin'/('pagefind.cmd' if __import__('os').name=='nt' else 'pagefind')
    package=installed_root/'node_modules/pagefind/package.json'
    if not package.is_file() or read(package).get('version')!=ENGINE_VERSION:raise ValueError('Pinned Pagefind missing; run npm ci')
    with tempfile.TemporaryDirectory(prefix='privatecapital-public-search-') as temp:
        directory=Path(temp)
        for d in docs:
            p=directory/file_for(d['url']);p.parent.mkdir(parents=True,exist_ok=True)
            names=' '.join([d['title'],d.get('english',''),*d.get('aliases',[])])
            page=f'<!doctype html><html lang="fa"><head><title>{escape(d["title"])}</title></head><body><main data-pagefind-body><h1>{escape(normalize(names))}</h1><p>{escape(normalize(bodies[d["id"]]))}</p></main></body></html>'
            p.write_text(page,encoding='utf-8',newline='\n')
        subprocess.run([str(binary),'--site',str(directory)],cwd=root,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        pf=directory/'pagefind'
        result=subprocess.run(['node',str(root/'tools/search-inspect.mjs'),str(pf)],check=True,capture_output=True,text=True,encoding='utf-8')
        mapping=json.loads(result.stdout)
        by_url={r['url']:r['pagefindId'] for r in mapping}
        if len(mapping)!=len(docs) or set(by_url)!={d['url'] for d in docs}:raise ValueError('Pagefind/public corpus identity mismatch')
        records=[dict(d,pagefindId=by_url[d['url']]) for d in docs]
        files={}
        for p in pf.rglob('*'):
            if not p.is_file():continue
            name=p.relative_to(pf).as_posix()
            if name in {'pagefind.js','pagefind-worker.js','pagefind-entry.json'} or re.fullmatch(r'(?:wasm\.[a-z]+\.pagefind|pagefind\.[a-z0-9_]+\.pf_meta|(?:fragment|index|filter)/[a-z0-9_]+\.pf_(?:fragment|index|filter))',name):
                files['search/pagefind/'+name]=p.read_bytes()
        files['search/documents.json']=(json.dumps({'version':1,'engineVersion':ENGINE_VERSION,'documents':records},ensure_ascii=False,separators=(',',':'))+'\n').encode()
        _cache[key]=files
        return files

def files(root):
    # This uses the actual packager/projection, not a scan of canonical inputs.
    import site_release as site
    with tempfile.TemporaryDirectory(prefix='privatecapital-search-staging-') as temp:
        stage=Path(temp)/'public'
        site.package(root,stage,public=True,include_search=False)
        docs,bodies=documents(root,stage)
    return {**compile_index(root,docs,bodies),**home_html(root,docs)}

def check(root, output, require_coverage=True):
    import public_projection
    try:
        entities=public_projection.snapshot(root)[0]
        research={r['id']:r for r in read(root/'research/index.json')['research'] if r['status']=='PUBLISHED'}
        data=read(output/'search/documents.json')
        if data.get('version')!=1 or data.get('engineVersion')!=ENGINE_VERSION:raise ValueError('Search contract/version mismatch')
        records=data['documents'];seen=set();urls=set();pf=set()
        for d in records:
            if d['id'] in seen or d['url'] in urls or d['pagefindId'] in pf:raise ValueError('Duplicate public search identity')
            seen.add(d['id']);urls.add(d['url']);pf.add(d['pagefindId'])
            if d['scope']=='atlas':
                e=entities.get(d['id'])
                if not e or d['type']!=e['type'] or d['kind']!=('concept' if e['type']=='Concept' else 'entity'):raise ValueError('Unapproved search Entity '+d['id'])
                route='/atlas/'+public_projection.ROUTES[e['type']]+'/'+e['id'].split(':',1)[1]+'/'
                if d['url']!=route:raise ValueError('Search Entity URL mismatch')
            elif d['scope']=='research':
                r=research.get(d['id'])
                if not r or d['url']!=r['url'] or d['kind']!='research' or d['type']!='Research':raise ValueError('Unapproved search Research '+d['id'])
            else:raise ValueError('Unknown search scope')
            if not (output/file_for(d['url'])).is_file():raise ValueError('Dead search URL')
        if require_coverage and seen!=set(entities)|set(research):raise ValueError('Public search coverage mismatch')
        return []
    except (ValueError,KeyError,OSError,TypeError) as error:return ['Search publication: '+str(error)]
