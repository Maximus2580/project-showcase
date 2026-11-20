"""Local design workshop: source → four previews → exact revision selection.

No LLM, network or audio synthesis. The calling agent authors the creative brief
and sources; this module owns validation, immutable preview revisions and gates.
"""
import copy
import html
from html.parser import HTMLParser
import itertools
import json
import re
import shlex
import shutil
import sys
import time
from pathlib import Path
import showcase as s
from design_render import LAYOUTS

ID = r'[a-z][a-z0-9-]{0,39}'
SHELL = '{{header}}\n{{content}}\n{{footer}}\n'

def enabled(m):
    return m.get('design', {}).get('mode') == 'variants'

def normalize(m):
    for sc in m.get('scenes', []):
        if 'items' in sc:
            sc['points'] = [x['text'] for x in sc['items']]
        if 'rows' in sc:
            sc['table'] = [x['cells'] for x in sc['rows']]
    return m

def validate_model(m):
    mode = m.get('design', {}).get('mode', 'legacy')
    if mode not in ('legacy', 'variants'):
        raise ValueError('E_DESIGN_MODE: legacy / variants')
    if enabled(m) and m.get('extra_css'):
        raise ValueError('E_DESIGN_CSS: put global styles in the selected variant/style.css')
    for sc in m.get('scenes', []):
        if sc.get('layout') and sc['layout'] not in LAYOUTS.get(sc.get('kind'), ()):
            raise ValueError('E_LAYOUT: '+sc['id'])
        for field in ('items', 'rows'):
            if field not in sc:
                continue
            ids = [x.get('id') for x in sc[field]]
            if not ids or len(ids) != len(set(ids)) or any(not isinstance(x,str) or not re.fullmatch(ID,x) for x in ids):
                raise ValueError('E_CONTENT_ID: '+sc['id'])
        if 'rows' in sc and any(len(x.get('cells',[]))!=3 or any(not isinstance(v,str) for v in x['cells']) for x in sc['rows']):
            raise ValueError('E_ROWS: three string cells required')
        ids = {x['id'] for x in sc.get('rows' if sc.get('table') else 'items', [])}
        for u in sc.get('utterances', []):
            if 'emphasis_id' in u and (u['emphasis_id'] not in ids or sc['kind']=='demo' or 'emphasis_target' in u):
                raise ValueError('E_EMPHASIS_ID: '+sc['id'])
            if enabled(m) and 'emphasis_target' in u:
                raise ValueError('E_EMPHASIS_ID: use a stable content ID in design mode')

def representatives(m):
    cover = next(sc for sc in m['scenes'] if sc['slide']==1)
    demo = next(sc for sc in m['scenes'] if sc['kind']=='demo')
    rest = [sc for sc in m['scenes'] if sc['id'] not in (cover['id'], demo['id'])]
    dense = max(rest, key=lambda sc: len(json.dumps(sc.get('table',sc['points']),ensure_ascii=False)))
    return [cover['id'], demo['id'], dense['id']]

def add_content_ids(m):
    for sc in m['scenes']:
        sc.setdefault('items',[{'id':f'point-{i+1}','text':x} for i,x in enumerate(sc['points'])])
        if sc.get('table'):
            sc.setdefault('rows',[{'id':f'row-{i+1}','cells':row} for i,row in enumerate(sc['table'])])
        for u in sc.get('utterances',[]):
            if 'emphasis_target' in u:
                field = 'rows' if sc.get('table') else 'items'
                u['emphasis_id'] = sc[field][u.pop('emphasis_target')-1]['id']

def scaffold(args):
    out = args.out; m = s.load(out); root = out/'design'
    if (root/'brief.json').exists():
        if not getattr(args,'replace',False):
            raise ValueError('E_DESIGN_EXISTS: edit the existing sources, or --replace to archive all four')
        dest = out/'backups'/f'design-{time.time_ns()}'
        dest.parent.mkdir(parents=True,exist_ok=True); shutil.copytree(root,dest)
        shutil.rmtree(root)
        print('디자인 원본·시안·선택 백업: '+str(dest))
    # A source-model backup precedes adding stable content IDs and opt-in mode.
    root.mkdir(parents=True,exist_ok=True)
    s.write(root/f'project-before-design-{time.time_ns()}.json',s.read(out/'project.json'))
    add_content_ids(m)
    request = getattr(args,'request',None) or m.get('design',{}).get('request','')
    m['design'] = {'mode':'variants','request':request}
    reps = getattr(args,'representatives',None)
    reps = reps.split(',') if reps else representatives(m)
    s.write(out/'project.json',m)
    # These are editable construction examples, never an approved creative result.
    brief = {'schema_version':1,'ready':False,'title':m['title'],'audience':m['audience'],
             'request':request,'brand_guidelines':'','context':'','constraints':[],
             'representatives':reps,'representative_reason':'표지, 실제 데모 또는 실행 불가 사유, 정보량이 많은 장면',
             'decision_notes':'','variants':['direction-a','direction-b','direction-c','direction-d']}
    s.write(root/'brief.json',brief)
    palettes = [('#f5f7fb','#142846','#47566b','#e5ebf3','#204daf'),
                ('#12243b','#f4f7fc','#bdcedf','#233952','#81c9ff'),
                ('#fff9ed','#382e27','#695849','#efe6d3','#963e23'),
                ('#f4f1ff','#30254d','#655777','#e6def4','#6540a7')]
    type_axes = [('72px','760','-2px'),('80px','600','-3px'),('64px','850','-1px'),('88px','720','-3px')]
    names = ['제품 흐름 중심','결과를 크게 보여 주기','근거를 따라 읽기','핵심 메시지 중심']
    starter={}
    for i, ident in enumerate(brief['variants']):
        folder = root/'variants'/ident; folder.mkdir(parents=True)
        bg,fg,muted,panel,accent = palettes[i];size,weight,tracking = type_axes[i]
        config = {'id':ident,'name':names[i],'rationale':'','request_mapping':[],
                  'layouts':{kind:choices[i] for kind,choices in LAYOUTS.items()},
                  'tokens':{'bg':bg,'fg':fg,'muted':muted,'panel':panel,'accent':accent,
                            'title-size':size,'title-weight':weight,'tracking':tracking,
                            'radius':['8px','20px','0px','4px'][i],
                            'image-border':['1px solid var(--muted)','0px solid transparent','4px solid var(--fg)','8px solid var(--panel)'][i]},
                  'density':['balanced','spacious','compact','statement'][i],
                  'fonts':[],'assets':[]}
        s.write(folder/'variant.json',config)
        (folder/'style.css').write_text('/* Add project-specific, local declarative styles here. */\n',encoding='utf-8')
        (folder/'shell.html').write_text(SHELL,encoding='utf-8')
        starter[ident]=visual_source_digest(config,folder)
    s.write(root/'scaffold.json',starter)
    s.invalidate(out,'build');set_phase(out,'preparing')
    print('design/brief.json과 네 방향의 소스를 만들었습니다. 에이전트가 요청·근거·스타일을 작성하고 ready=true로 설정한 뒤 design-preview를 실행하세요.')

def set_phase(out,phase,**extra):
    st=s.state(out);st['design']={'phase':phase,**extra};s.write(out/'state.json',st)

def visual_source_digest(config,folder):
    return s.digest({'config':{k:config.get(k) for k in ('tokens','layouts','density','fonts','assets')},'css':s.filehash(folder/'style.css'),'shell':s.filehash(folder/'shell.html')})

def luminance(color):
    channels=[int(color[i:i+2],16)/255 for i in (1,3,5)]
    v=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in channels]
    return sum(a*b for a,b in zip(v,(.2126,.7152,.0722)))

def contrast(a,b):
    x,y=sorted((luminance(a),luminance(b)));return (y+.05)/(x+.05)

class ShellValidator(HTMLParser):
    def __init__(self,assets):super().__init__();self.assets=assets
    def handle_starttag(self,tag,attrs):
        if tag not in ('div','article','aside','section','img'):
            raise ValueError('E_DESIGN_SHELL: shell permits structural tags and local images only')
        data=dict(attrs)
        if any(k not in ('class','id','src','alt','aria-label') for k in data):
            raise ValueError('E_DESIGN_SHELL: unsupported attribute')
        if tag=='img' and (not data.get('alt') or data.get('src') not in {'{{asset:'+x+'}}' for x in self.assets}):
            raise ValueError('E_DESIGN_ASSET: local declared image and alt required')
        if tag!='img' and 'src' in data:raise ValueError('E_DESIGN_SHELL: src only on image')

def sources(out,ident):
    if not re.fullmatch(ID,ident):raise ValueError('E_VARIANT_ID')
    folder=s.safe(out,'design/variants/'+ident)
    config=s.read(folder/'variant.json')
    if config.get('id')!=ident or not config.get('name') or not config.get('rationale'):
        raise ValueError('E_DESIGN_RATIONALE: write name and project-specific rationale for '+ident)
    for kind,values in LAYOUTS.items():
        if config.get('layouts',{}).get(kind) not in values:raise ValueError('E_LAYOUT: '+ident+'/'+kind)
    tokens=config.get('tokens',{})
    for key in ('bg','fg','muted','panel','accent'):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',tokens.get(key,'')):raise ValueError('E_DESIGN_COLOR: '+key)
    for bg in ('bg','panel'):
        for fg in ('fg','muted','accent'):
            if contrast(tokens[bg],tokens[fg])<4.5:raise ValueError('E_DESIGN_CONTRAST: '+ident+'/'+bg+'/'+fg)
    patterns={'title-size':r'(6[0-9]|[78][0-9]|90)px','title-weight':r'[4-8][0-9]0',
              'tracking':r'-?[0-4]px','radius':r'([0-9]|[12][0-9])px',
              'image-border':r'([0-9]|1[0-2])px solid (transparent|var\(--(fg|muted|panel|accent)\))',
              'heading-font':r'[A-Za-z][A-Za-z0-9-]{0,39}','body-font':r'[A-Za-z][A-Za-z0-9-]{0,39}'}
    if set(tokens)-set(patterns)-{'bg','fg','muted','panel','accent'}:raise ValueError('E_DESIGN_TOKEN')
    for key,pattern in patterns.items():
        if key not in ('heading-font','body-font') or key in tokens:
            if not re.fullmatch(pattern,tokens.get(key,'')):raise ValueError('E_DESIGN_TOKEN: '+key)
    if config.get('density') not in ('balanced','spacious','compact','statement'):raise ValueError('E_DESIGN_DENSITY')
    paths={n:folder/n for n in ('variant.json','style.css','shell.html')}
    for kind in ('fonts','assets'):
        ids=[]
        for item in config.get(kind,[]):
            if not item.get('license'):raise ValueError('E_DESIGN_LICENSE')
            key=item.get('family' if kind=='fonts' else 'id','')
            if not re.fullmatch(r'[A-Za-z][A-Za-z0-9-]{0,39}',key) or key in ids:raise ValueError('E_DESIGN_ASSET_ID')
            ids.append(key)
            for field in ('source','license'):
                p=s.safe(folder,item[field])
                if not p.is_file():raise ValueError('E_DESIGN_ASSET_MISSING: '+str(p))
                paths[item[field]]=p
            suffix=Path(item['source']).suffix.lower()
            if suffix not in (('.woff2',) if kind=='fonts' else ('.png','.jpg','.jpeg','.webp')):raise ValueError('E_DESIGN_ASSET_TYPE')
    families={x['family'] for x in config.get('fonts',[])}|{'Showcase'}
    if any(tokens.get(k,'Showcase') not in families for k in ('heading-font','body-font')):raise ValueError('E_DESIGN_FONT')
    css=paths['style.css'].read_text(encoding='utf-8')
    # Escapes could disguise url/import; trusted local CSS is kept declarative.
    if re.search(r'url\s*\(|@import|</style|\\|expression\s*\(',css,re.I):raise ValueError('E_DESIGN_CSS: external URLs/imports/scripts/escapes are unsupported')
    shell=paths['shell.html'].read_text(encoding='utf-8')
    for name in ('header','content','footer'):
        if shell.count('{{'+name+'}}')!=1:raise ValueError('E_DESIGN_SHELL: exactly one '+name+' slot required')
    declared={x['id'] for x in config.get('assets',[])}
    slots={'header','content','footer'}|{'asset:'+x for x in declared}
    if set(re.findall(r'{{(.*?)}}',shell))-slots:raise ValueError('E_DESIGN_SHELL: unknown slot')
    ShellValidator(declared).feed(shell)
    return config,folder,paths

def workshop(out,m):
    brief=s.read(out/'design/brief.json');ids=brief.get('variants',[])
    if not brief.get('ready') or not brief.get('context') or not brief.get('decision_notes'):
        raise ValueError('E_DESIGN_BRIEF: fill context and decision_notes, then ready=true')
    if brief.get('request','')!=m['design'].get('request',''):
        raise ValueError('E_DESIGN_REQUEST: project and brief request differ')
    if len(ids)!=4 or len(set(ids))!=4:raise ValueError('E_DESIGN_FOUR: exactly four stable variant IDs required')
    reps=brief.get('representatives',[]);byid={x['id']:x for x in m['scenes']}
    if len(reps)!=3 or len(set(reps))!=3 or any(x not in byid for x in reps):raise ValueError('E_DESIGN_REPRESENTATIVES')
    if byid[reps[0]]['slide']!=1 or byid[reps[1]]['kind']!='demo':raise ValueError('E_DESIGN_REPRESENTATIVES: cover, demo, dense content in order')
    if not brief.get('representative_reason'):raise ValueError('E_DESIGN_REPRESENTATIVES: explain the dense slide choice')
    configs={i:sources(out,i) for i in ids}
    if brief.get('request') and any(not c.get('request_mapping') for c,_,_ in configs.values()):
        raise ValueError('E_DESIGN_REQUEST: each direction must explain how it addresses the request')
    # Compare actual settings, never self-reported labels alone. Color is not an axis.
    def axes(c):
        t=c['tokens']
        return [c['layouts'],[t[k] for k in ('title-size','title-weight','tracking')]+[t.get('heading-font','Showcase')],
                [t['radius'],t['image-border'],c['layouts']['demo']],c['density']]
    for a,b in itertools.combinations(ids,2):
        if sum(x!=y for x,y in zip(axes(configs[a][0]),axes(configs[b][0])))<3:
            raise ValueError('E_DESIGN_DIVERSITY: '+a+' / '+b+' must differ on three non-color axes')
    baseline=out/'design/scaffold.json'
    if baseline.exists():
        initial=s.read(baseline)
        unchanged=[i for i,(c,folder,_) in configs.items() if initial.get(i)==visual_source_digest(c,folder)]
        if unchanged:print('W_DESIGN_STARTER: '+', '.join(unchanged)+' retains the starter visual settings. Verify project-specific suitability; QA is not creative approval.')
    return brief,configs

def fingerprint(out,m,brief,ident,config_paths):
    # Speech edits and non-representative scene edits do not revoke the style choice.
    # They still invalidate all affected production artifacts via build_signature.
    visual_keys=('id','slide','kind','title','claim','visual_label','points','items','table','rows','states','media','unavailable_reason','verification','layout')
    reps=[{k:sc[k] for k in visual_keys if k in sc} for key in brief['representatives'] for sc in m['scenes'] if sc['id']==key]
    media=s.referenced_inputs({'scenes':reps},out)
    scripts=('render.py','design_render.py','check-deck.mjs')
    return s.digest({'brief':{k:v for k,v in brief.items() if k!='variants'},'title':m['title'],'profile':m['profile'],
                     'scenes':reps,'source':{k:s.filehash(p) for k,p in config_paths.items()},
                     'media':{k:s.filehash(p) for k,p in media.items()},
                     'renderer':{k:s.filehash(s.SKILL/'scripts'/k) for k in scripts},
                     'fonts':{p.name:s.filehash(p) for p in (s.SKILL/'assets/fonts').iterdir() if p.is_file()}})

def artifact_hash(folder):
    return s.digest({p.relative_to(folder).as_posix():s.filehash(p) for sub in ('deck','qa','source') for p in sorted((folder/sub).rglob('*')) if p.is_file()})

def preview(args):
    from render import build_deck
    out=args.out;m=s.load(out)
    if not enabled(m):raise ValueError('E_DESIGN_MODE: run design-scaffold to opt in')
    started=time.monotonic();brief,configs=workshop(out,m)
    chosen=getattr(args,'variant',None)
    if chosen and chosen not in configs:raise ValueError('E_VARIANT_ID')
    for ident,(config,source,paths) in configs.items():
        if chosen and ident!=chosen:continue
        root=out/'design/previews'/ident;root.mkdir(parents=True,exist_ok=True)
        current=root/'current.json';old=s.read(current) if current.exists() else {}
        sig=fingerprint(out,m,brief,ident,paths)
        if old.get('source_digest')==sig:
            previous=root/old['revision']
            if old.get('artifact_digest')!=artifact_hash(previous):
                raise ValueError('E_DESIGN_PREVIEW_EDIT: preserved preview was edited; edit source and preview a new revision')
            if old.get('ok'):continue
        # Append only; a failed or manually edited revision is never overwritten.
        nums=[int(p.name[1:]) for p in root.iterdir() if p.is_dir() and re.fullmatch(r'r\d+',p.name)]
        revision=f'r{max(nums,default=0)+1:03}';dest=root/revision;dest.mkdir()
        for name,p in paths.items():
            target=dest/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        model=copy.deepcopy(m);model['_preview']=True;model['_design']={'config':config,'source':str(dest/'source')}
        model['scenes']=[next(sc for sc in model['scenes'] if sc['id']==sid) for sid in brief['representatives']]
        report={'id':ident,'revision':revision,'source_digest':sig,'ok':False,'created_at':time.time()}
        s.write(dest/'manifest.json',report);s.write(current,report)
        try:
            build_deck(model,out,dest/'deck',s.SKILL)
            s.run(['node',s.SKILL/'scripts/check-deck.mjs',dest/'deck/index.html',dest/'qa'],timeout=180)
            report['ok']=s.read(dest/'qa/report.json')['ok']
        finally:
            report['artifact_digest']=artifact_hash(dest)
            s.write(dest/'manifest.json',report);s.write(current,report)
    comparison(out,m,brief,configs)
    if all((out/'design/previews'/ident/'current.json').exists() for ident in configs):
        s.run(['node',s.SKILL/'scripts/check-design.mjs',out/'design/index.html',out/'design/comparison-qa'],timeout=120)
    previous=s.state(out).get('design',{})
    now=time.time()
    preview_set=s.digest({ident:s.read(out/'design/previews'/ident/'current.json') for ident in configs if (out/'design/previews'/ident/'current.json').exists()})
    waiting=previous.get('awaiting_since',now) if previous.get('phase')=='awaiting-selection' and previous.get('preview_set')==preview_set else now
    phase=status(out,m)['phase']
    set_phase(out,phase if phase in ('selected','production') else 'awaiting-selection',awaiting_since=waiting,preview_set=preview_set,generation_seconds=round(time.monotonic()-started,3))
    print(out/'design/index.html')

def current_preview(out,m,brief,ident,paths):
    root=out/'design/previews'/ident
    if not (root/'current.json').exists():raise ValueError('E_DESIGN_PREVIEW_REQUIRED: '+ident)
    report=s.read(root/'current.json')
    if not report.get('ok') or report.get('source_digest')!=fingerprint(out,m,brief,ident,paths):raise ValueError('E_DESIGN_STALE: '+ident+' needs design-preview')
    folder=s.safe(root,report['revision'])
    if report.get('artifact_digest')!=artifact_hash(folder):raise ValueError('E_DESIGN_PREVIEW_EDIT: '+ident)
    return report

def select(args):
    out=args.out;m=s.load(out)
    if not enabled(m):raise ValueError('E_DESIGN_MODE')
    brief,configs=workshop(out,m);ident=args.variant
    if ident not in configs:raise ValueError('E_VARIANT_ID')
    # All four alternatives must be current for a fair, reviewable choice.
    reports={i:current_preview(out,m,brief,i,paths) for i,(_,_,paths) in configs.items()}
    report=reports[ident]
    if getattr(args,'revision',None)!=report['revision']:
        raise ValueError('E_DESIGN_REVISION: choose the exact current --revision shown in the comparison')
    if not getattr(args,'by','').strip() or not getattr(args,'reason','').strip():raise ValueError('E_DESIGN_SELECTION: record the actual chooser and their request')
    old=out/'design/selection.json'
    if old.exists():
        archive=out/'design/selections'/f'{time.time_ns()}.json';archive.parent.mkdir(exist_ok=True);shutil.copy2(old,archive)
    phase=s.state(out).get('design',{});wait=max(0,time.time()-phase.get('awaiting_since',time.time()))
    selected={**report,'selected_at':time.time(),'by':args.by,'reason':args.reason,'waiting_seconds':round(wait,3)}
    s.write(old,selected);m['design']['selected']={'id':ident,'revision':report['revision'],'source_digest':report['source_digest']};s.write(out/'project.json',m)
    s.invalidate(out,'build');set_phase(out,'selected',selection=m['design']['selected'],waiting_seconds=selected['waiting_seconds'])
    print(f'{ident} {report["revision"]} 선택 기록. 이제 build / tts / resume가 가능합니다.')

def require_selected(out,m=None):
    m=m or s.load(out)
    if not enabled(m):return None
    if not (out/'design/selection.json').exists():raise ValueError('E_DESIGN_SELECTION_REQUIRED: four previews and an explicit user selection are required before production')
    selection=s.read(out/'design/selection.json');ident=selection.get('id','')
    brief=s.read(out/'design/brief.json');config,source,paths=sources(out,ident)
    if not brief.get('ready') or brief.get('request','')!=m['design'].get('request','') or ident not in brief.get('variants',[]):raise ValueError('E_DESIGN_STALE: brief changed')
    report=current_preview(out,m,brief,ident,paths)
    reference={k:selection[k] for k in ('id','revision','source_digest')}
    if m['design'].get('selected')!=reference or any(selection.get(k)!=report.get(k) for k in ('revision','source_digest','artifact_digest')):
        raise ValueError('E_DESIGN_STALE: reselect the current reviewed revision')
    return {'config':config,'source':str(source),'selection':selection}

def selected_files(out,m):
    design=require_selected(out,m)
    if not design:return {}
    _,_,paths=sources(out,design['config']['id'])
    result={p.relative_to(out).as_posix():p for p in paths.values()}
    for name in ('brief.json','selection.json'):
        result['design/'+name]=out/'design'/name
    ident=design['config']['id'];revision=design['selection']['revision']
    root=out/'design/previews'/ident
    result[(root/'current.json').relative_to(out).as_posix()]=root/'current.json'
    for p in sorted((root/revision).rglob('*')):
        if p.is_file():result[p.relative_to(out).as_posix()]=p
    return result

def status(out,m):
    if not enabled(m):return {'phase':'legacy'}
    if not (out/'design/selection.json').exists():
        return {'phase':'awaiting-selection' if (out/'design/index.html').exists() else 'preparing'}
    try:
        require_selected(out,m)
        return {'phase':'production' if s.state(out)['steps'].get('build') else 'selected'}
    except (ValueError,KeyError,FileNotFoundError) as e:return {'phase':'awaiting-selection','reason':str(e)}

def comparison(out,m,brief,configs):
    cards=[]
    for ident,(config,_,paths) in configs.items():
        root=out/'design/previews'/ident
        if not (root/'current.json').exists():continue
        report=s.read(root/'current.json');rev=report['revision'];base=f'previews/{ident}/{rev}'
        current=report.get('ok') and report['source_digest']==fingerprint(out,m,brief,ident,paths)
        command=shlex.join([sys.executable,str(s.SKILL/'scripts/showcase.py'),'--out',str(out),'design-select',ident,'--revision',rev,'--by','사용자','--reason','비교 화면에서 선택'])
        images=''.join(f'<a href="{base}/deck/index.html#slide={i}" target="_blank" rel="noopener"><img loading="lazy" src="{base}/qa/slide-{i}.png" alt="{html.escape(config["name"])} — {label}"></a>' for i,label in ((1,'표지'),(2,'실제 데모'),(3,'정보가 많은 장면')))
        cards.append(f'<article data-variant="{ident}"><h2>{html.escape(config["name"])}</h2><p class="meta">{ident} / {rev} / {"자동 구조 검사 통과 · 시각 검토 별도" if current else "재생성 필요"}</p><p>{html.escape(config["rationale"])}</p><div class="slides">{images}</div><div class="actions"><button class="expand" aria-expanded="false">3장 펼치기</button><label><input type="checkbox" class="compare"> 나란히 비교</label><button class="choose" data-command="{html.escape(command,quote=True)}" {"" if current else "disabled"}>선택 명령 복사</button><a href="{base}/deck/index.html" target="_blank" rel="noopener">전체 크기</a></div><details><summary>선택 명령 보기</summary><code>{html.escape(command)}</code></details></article>')
    doc='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>디자인 방향 비교</title><style>
+*{box-sizing:border-box}body{margin:0;padding:40px;background:#eef2f7;color:#172638;font:16px/1.6 system-ui,sans-serif}main{max-width:1800px;margin:auto}h1{font-size:36px;margin:0}h2{font-size:24px;margin:0}.intro{max-width:900px}.toolbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:24px 0}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}article{background:white;padding:24px;border-radius:10px;border:1px solid #ccd5e1;min-width:0}article>p{min-height:26px}.meta{font-size:14px;color:#526176}img{display:block;width:100%;height:auto}.slides{display:grid;gap:12px}.slides a:not(:first-child){display:none}article.expanded .slides a,.all .slides a{display:block}.actions{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-top:20px}button{font:inherit;border:1px solid #4b6380;background:white;color:#172638;border-radius:5px;padding:8px 14px;cursor:pointer}button:disabled{opacity:.5;cursor:default}button:focus-visible,a:focus-visible,input:focus-visible{outline:3px solid #2063ce;outline-offset:4px}.choose{background:#183b65;color:white}.pair article:not(.paired){display:none}code{display:block;white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}#feedback{min-height:30px}details{margin-top:16px}a{color:#164d91}@media(max-width:850px){body{padding:20px}.grid{grid-template-columns:1fr}.pair .grid{grid-template-columns:1fr}.pair article{padding:10px}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
+</style><body><main><h1>어떤 방향이 프로젝트에 어울리나요?</h1><p class="intro">네 방향 모두 같은 내용과 실제 화면을 사용합니다. 먼저 표지를 비교하고, 각 방향의 데모와 복잡한 장면까지 살펴보세요. 이 화면은 선택을 저장하지 않습니다. 명령을 실행하거나 대화에서 방향과 리비전을 알려 주세요.</p><div class="toolbar"><button id="grid-toggle" aria-pressed="false">12장 모두 보기</button><button id="pair-toggle">선택한 두 방향 비교</button><button id="reset">전체 방향 보기</button><span id="feedback" role="status" aria-live="polite"></span></div><div class="grid">CARDS</div></main><script>
+const feedback=document.querySelector('#feedback');document.querySelectorAll('.expand').forEach(b=>b.onclick=()=>{const on=b.closest('article').classList.toggle('expanded');b.setAttribute('aria-expanded',on);b.textContent=on?'표지만 보기':'3장 펼치기'});
+document.querySelector('#grid-toggle').onclick=e=>{const on=document.body.classList.toggle('all');e.target.setAttribute('aria-pressed',on);e.target.textContent=on?'표지 중심 보기':'12장 모두 보기'};
+document.querySelectorAll('.compare').forEach(b=>b.onchange=()=>{if(document.querySelectorAll('.compare:checked').length>2){b.checked=false;feedback.textContent='두 방향만 선택해 주세요.'}});
+document.querySelector('#pair-toggle').onclick=()=>{const checked=[...document.querySelectorAll('.compare:checked')];if(checked.length!==2){feedback.textContent='비교할 두 방향을 선택해 주세요.';return}document.querySelectorAll('article').forEach(a=>a.classList.toggle('paired',a.querySelector('.compare').checked));document.body.classList.add('pair','all');document.querySelector('#grid-toggle').setAttribute('aria-pressed','true');document.querySelector('#grid-toggle').textContent='표지 중심 보기';feedback.textContent='선택한 두 방향의 3장을 비교합니다.'};
+document.querySelector('#reset').onclick=()=>{document.body.classList.remove('pair');feedback.textContent='네 방향을 모두 표시합니다.'};
+document.querySelectorAll('.choose').forEach(b=>b.onclick=async()=>{try{await navigator.clipboard.writeText(b.dataset.command);feedback.textContent='선택 명령을 복사했습니다. 실행 후 선택이 저장됩니다.'}catch(e){b.closest('article').querySelector('details').open=true;feedback.textContent='아래 명령을 직접 복사해 실행하세요.'}});
+</script></body></html>'''.replace('\n+','\n').replace('CARDS',''.join(cards))
    (out/'design/index.html').write_text(doc,encoding='utf-8')
