"""Deterministic public snapshot; canonical records and history remain complete."""
from collections import defaultdict
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

ROUTES = {'Person':'person','Organization':'organization','Investment':'investment','Concept':'concept'}
DIRS = {'Person':'persons','Organization':'organizations','Investment':'investments','Concept':'concepts'}

def read(path): return json.loads(path.read_text(encoding='utf-8'))
def encoded(data): return (json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
def records(root, family):
    data={};owners={}
    for path in sorted((root/'atlas'/family).glob('*.json')):
        if path.name=='index.json': continue
        for record in read(path).get(family,[]):
            if record['id'] in data: raise ValueError(f'{path}: duplicate {record["id"]}')
            data[record['id']]=record;owners[record['id']]=path.name
    return data,owners

def source_refs(value):
    if isinstance(value,dict):
        return set().union(*(source_refs(v) for v in value.values())) if value else set()
    if isinstance(value,list):
        return set().union(*(source_refs(v) for v in value)) if value else set()
    return {value} if isinstance(value,str) and value.startswith('source:') else set()

def profile_content(entity):
    p=entity.get('metadata',{}).get('public_profile')
    if not p: return None
    return {'entity':entity['id'],'title':entity['name'],'summary':p['text'],
            'sections':[{'id':'reviewed-profile','title_fa':'معرفی و دامنه','title_en':'Profile and scope',
                         'paragraphs':[{'text':p['text'],'sourceRefs':p['sourceRefs']}]}],
            'data_quality':{'title_fa':'دامنهٔ اطلاعات','text':'این پروفایل فقط مطالب بررسی‌شده را ارائه می‌کند؛ وجود سازمان یا مفهوم، تأیید همهٔ ادعاهای مرتبط نیست.'},
            'last_reviewed':'1405-07'}

def snapshot(root):
    entities={}
    for path in sorted((root/'atlas/entities').rglob('*.json')):
        if path.name=='index.json':continue
        e=read(path)
        if e.get('lifecycleStatus')=='PUBLISHED' and e.get('type') in ROUTES:
            entities[e['id']]=deepcopy(e)
    claims,claim_owners=records(root,'claims')
    evidence,evidence_owners=records(root,'evidence')
    sources,source_owners=records(root,'sources')
    superseded={c['supersedes'] for c in claims.values() if c.get('supersedes')}
    accepted={}
    for cid,c in claims.items():
        if cid in superseded or c['subject'] not in entities or c.get('object',c['subject']) not in entities:continue
        if c.get('status') not in ('VERIFIED','SUPPORTED','REPORTED'):continue
        refs=c.get('evidenceRefs',[])
        if not refs or any(r not in evidence for r in refs):continue
        if any(not evidence[r].get('locator') or not sources.get(evidence[r]['sourceRef'],{}).get('url') for r in refs):continue
        if c['status']=='REPORTED' and not c.get('context',{}).get('attribution'):continue
        accepted[cid]=deepcopy(c)
        # The public graph is a current snapshot, not the canonical revision log.
        accepted[cid].pop('supersedes',None)
    selected_evidence={r:evidence[r] for c in accepted.values() for r in c['evidenceRefs']}
    wanted_sources={e['sourceRef'] for e in selected_evidence.values()}
    for e in entities.values():
        e['domains']=[r for r in e.get('domains',[]) if r in entities]
        profile=e.get('metadata',{}).get('public_profile')
        if profile:
            if not profile.get('text') or not profile.get('sourceRefs') or len(profile.get('locators',[]))!=len(profile['sourceRefs']):
                raise ValueError(f'{e["id"]}: incomplete public profile provenance')
            for ref in profile['sourceRefs']:
                if not sources.get(ref,{}).get('url'):raise ValueError(f'{e["id"]}: missing profile source {ref}')
            wanted_sources.update(profile['sourceRefs'])
        e['metadata']={'public_profile':profile} if profile else {}
        for field in ('investor','target'):
            if e.get(field) and e[field] not in entities:
                raise ValueError(f'{e["id"]}: non-public {field}')
    registry=read(root/'research/index.json')['research']
    published_research={r['id'] for r in registry if r['status']=='PUBLISHED'}
    for path in (root/'research/content').rglob('research.json'):
        r=read(path)
        if r['id'] in published_research:wanted_sources.update(source_refs(r))
    if wanted_sources - sources.keys():raise ValueError(f'Missing public sources: {sorted(wanted_sources-sources.keys())}')
    selected_sources={s:sources[s] for s in sorted(wanted_sources)}
    return entities,accepted,selected_evidence,selected_sources,(claim_owners,evidence_owners,source_owners)

def overrides(root):
    entities,claims,evidence,sources,owners=snapshot(root)
    files={}
    index=read(root/'atlas/entities/index.json')
    index['projection']='public'
    index['entities']=[{k:v for k,v in row.items() if k!='domains' or all(x in entities for x in v)}
                       for row in index['entities'] if row['id'] in entities]
    files['atlas/entities/index.json']=encoded(index)
    catalog=read(root/'atlas/catalog/index.json')
    catalog['entities']=[{k:v for k,v in row.items() if k!='domains' or all(x in entities for x in v)}
                         for row in catalog['entities'] if row['id'] in entities]
    files['atlas/catalog/index.json']=encoded(catalog)
    for family,selected,owner in zip(('claims','evidence','sources'),(claims,evidence,sources),owners):
        grouped=defaultdict(list)
        for cid,record in sorted(selected.items()):grouped[owner[cid]].append(record)
        for name,items in grouped.items():
            version=read(root/'atlas'/family/name)['version']
            files[f'atlas/{family}/{name}']=encoded({'version':version,family:items})
        internal=read(root/'atlas'/family/'index.json')
        if family=='claims':
            internal['entities']={eid:sorted(c['id'] for c in claims.values() if c['subject']==eid or c.get('object')==eid) for eid in sorted(entities)}
        internal[family]={cid:owner[cid] for cid in sorted(selected)}
        files[f'atlas/{family}/index.json']=encoded(internal)
    spec=importlib.util.spec_from_file_location('public_static_builder',root/'atlas/tools/build-static-pages.py')
    builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
    builder.load_content=profile_content
    contract=builder.load_relation_contract()
    research_path=builder.research_connections.INDEX_PATH
    research_index=read(research_path) if research_path.exists() else None
    for eid,e in sorted(entities.items()):
        slug=eid.split(':',1)[1];kind=ROUTES[e['type']]
        files[f'atlas/entities/{DIRS[e["type"]]}/{slug}.json']=encoded(e)
        if e['type']=='Person':
            content=profile_content(e)
            if content is None:raise ValueError(f'{eid}: reviewed public Person content required')
            files[f'atlas/content/persons/{slug}.json']=encoded(content)
        html=builder.render_entity(e,list(claims.values()),evidence,sources,entities,contract,research_index=research_index)
        files[f'atlas/{kind}/{slug}/index.html']=html.encode('utf-8')
    return files

def private_paths(root):
    ids={e['id'] for e in read(root/'atlas/entities/index.json')['entities']
         if e.get('lifecycleStatus')!='PUBLISHED' or e.get('type') not in ROUTES}
    result=set()
    for e in read(root/'atlas/entities/index.json')['entities']:
        if e['id'] not in ids or e['type'] not in ROUTES:continue
        slug=e['id'].split(':',1)[1]
        result.update((f'atlas/{ROUTES[e["type"]]}/{slug}/index.html',f'atlas/entities/{DIRS[e["type"]]}/{slug}.json'))
    return ids,result

def check(root,output):
    """Inspect actual public bytes, graph closure, and forbidden identities."""
    errors=[]
    hidden,paths=private_paths(root)
    for rel in paths:
        if (output/rel).exists():errors.append(f'{rel}: non-public Entity file')
    for p in output.rglob('*'):
        if p.is_file() and p.suffix in ('.json','.html','.xml'):
            text=p.read_text(encoding='utf-8')
            for eid in hidden:
                if eid in text:errors.append(f'{p.relative_to(output)}: non-public reference {eid}')
    try:
        public_ids={e['id'] for e in read(output/'atlas/entities/index.json')['entities']}
        cs,_=records(output,'claims');es,_=records(output,'evidence');ss,_=records(output,'sources')
        for cid,c in cs.items():
            if c['subject'] not in public_ids or c.get('object',c['subject']) not in public_ids:
                errors.append(f'{cid}: dangling public Entity reference')
            if c.get('status') not in ('VERIFIED','SUPPORTED','REPORTED'):
                errors.append(f'{cid}: forbidden public Claim status')
            if c.get('status')=='REPORTED' and not c.get('context',{}).get('attribution'):
                errors.append(f'{cid}: REPORTED Claim lacks attribution')
            for ref in c.get('evidenceRefs',[]):
                if ref not in es or es[ref]['claimRef']!=cid:errors.append(f'{cid}: broken Evidence {ref}')
        for eid,e in es.items():
            if e['claimRef'] not in cs or e['sourceRef'] not in ss or not e.get('locator'):
                errors.append(f'{eid}: broken public provenance')
    except (ValueError,KeyError,FileNotFoundError) as error:errors.append(str(error))
    return sorted(set(errors))
