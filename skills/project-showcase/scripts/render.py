"""Korean presentation and cue-driven HyperFrames renderer, schema v2."""
import html, json, math, shutil, struct, subprocess
from pathlib import Path
E=lambda value:html.escape(str(value),quote=True)
LABELS={'executed':'실행 확인','code-reviewed':'코드 검토 · 실행 미확인','unverified':'미검증 / 제안'}
CSS='''
@font-face{font-family:Showcase;src:url("assets/fonts/PretendardVariable.woff2") format("woff2");font-weight:100 900;font-display:block}
*{box-sizing:border-box}html,body{margin:0;background:#101923;color:#f2f5f1;font-family:Showcase,sans-serif}
.scene{position:absolute;inset:0;width:1920px;height:1080px;background:#101923;padding:82px 110px 180px;overflow:hidden}
.eyebrow{font-size:28px;letter-spacing:2px;color:#b9c8ce;margin:0 0 32px}h1{font-size:72px;line-height:1.12;letter-spacing:-2px;margin:0 0 24px;word-break:keep-all;max-width:1670px}
.claim{font-size:32px;line-height:1.4;color:#c5d2d7;margin:0;word-break:keep-all}.layout{height:465px;margin-top:42px;position:relative}
.foot{position:absolute;left:110px;right:110px;bottom:45px;display:flex;justify-content:space-between;color:#b5c5cc;font-size:28px}
.rule{position:absolute;top:48px;width:64px;height:5px;background:var(--accent)}
.hero{font-size:80px;line-height:1.25;letter-spacing:-2px;font-weight:760;max-width:1500px;color:var(--accent);word-break:keep-all;padding:40px 0}
.pills{display:flex;gap:24px;margin-top:30px}.pill{flex:1;font-size:32px;line-height:1.4;border-top:2px solid #506574;padding:25px 10px 0 0;word-break:keep-all}
.comparison{display:grid;grid-template-columns:1fr 1fr;gap:40px;height:340px}.panel{padding:40px;background:#223640;border-radius:12px}.panel.after{background:#dce8dd;color:#152a32}.tag{font-size:28px;margin-bottom:30px}.big{font-size:52px;line-height:1.3;font-weight:700;word-break:keep-all}.note{font-size:32px;margin-top:32px;color:#c5d2d7}
.flow-grid{display:flex;gap:30px;padding-top:40px}.step{flex:1;border-top:5px solid var(--accent);padding:30px 20px 30px 0;font-size:40px;line-height:1.4;word-break:keep-all}.step b{display:block;color:var(--accent);font-size:68px;margin-bottom:28px}
.demo-grid{display:grid;grid-template-columns:7fr 3fr;gap:42px;height:100%}.screen{position:relative;background:#e9eef0;border-radius:12px;overflow:hidden;height:100%}.screen svg{position:absolute;inset:0;width:100%;height:100%;background:#e9eef0}.screen rect{fill:none;stroke:#168069;stroke-width:5}.aside{display:flex;flex-direction:column;justify-content:center;gap:24px;font-size:32px;line-height:1.4;word-break:keep-all}.aside .tag{color:var(--accent);margin:0}.aside .point{border-left:3px solid #526a76;padding-left:20px}
.evidence-table{width:100%;border-collapse:collapse;font-size:34px}.evidence-table th{text-align:left;font-size:28px;color:#b9c8ce;padding:20px;border-bottom:2px solid #71858d}.evidence-table td{padding:25px 20px;border-bottom:1px solid #425965;line-height:1.35}.evidence-table td:last-child{color:var(--accent)}
.state-tabs{display:flex;gap:12px;flex-wrap:wrap}.state-tabs button{font:inherit;font-size:26px!important;padding:12px!important}.state-tabs button[aria-pressed=true]{background:#dce8dd!important;color:#152a32!important}
.closing .hero{font-size:72px;max-width:1600px}.closing .pill{border-top-color:var(--accent)}
.caption{position:absolute;left:192px;right:192px;bottom:110px;text-align:center;font-size:48px;line-height:1.25;z-index:40;word-break:keep-all;overflow-wrap:anywhere}.caption span{display:inline-block;background:#101923;padding:12px 24px;border-radius:8px;max-width:100%}
.video .layout{height:420px;margin-top:32px}.video h1{font-size:66px}.video .hero{font-size:64px;padding:24px 0}.video .pills{margin-top:18px}.video .comparison{height:290px}.video .big{font-size:46px}.video .step{font-size:36px}.video .step b{font-size:56px}.video .evidence-table td{padding:19px 20px}
.progress{position:absolute;left:0;bottom:0;height:5px;width:100%;background:var(--accent)}
'''

def dimensions(path):
    with path.open('rb') as f:
        header=f.read(24)
    if header[:8]==b'\x89PNG\r\n\x1a\n':return struct.unpack('>II',header[16:24])
    data=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(path)]))
    return data['streams'][0]['width'],data['streams'][0]['height']

def screen(sc,assets,video):
    states=sc.get('states',{})
    if not states and sc.get('media'):states={'original':{'media':sc['media'],'label':sc['visual_label']}}
    items=[]
    for i,(key,state) in enumerate(states.items()):
        meta=assets[state['media']];w,h=meta['size'];uid=f'{sc["id"]}-state-{key}'
        display='' if i==0 else 'display:none;'
        items.append(f'<svg id="{uid}" style="{display}" viewBox="0 0 {w} {h}" role="img" aria-label="{E(state["label"])}"><image href="{meta["path"]}" width="{w}" height="{h}"/><rect id="{uid}-mark" x="0" y="0" width="1" height="1" opacity="0"/></svg>')
    return '<div class="screen">'+''.join(items)+'</div>'

def body(sc,m,assets,video=False):
    if m.get('_design'):
        from design_render import body as designed_body
        return designed_body(sc,m,assets,video)
    points=sc['points'];sid=sc['id'];kind=sc['kind']
    if kind=='demo' and sc.get('unavailable_reason'):
        content='<div class="hero">실행 화면 미확보</div><div class="pills"><div class="pill">'+E(sc['unavailable_reason'])+'</div></div>'
    elif kind=='demo':
        tabs='' if video else '<div class="state-tabs" aria-label="데모 화면 선택">'+''.join(f'<button data-scene="{sid}" data-state="{E(key)}" aria-pressed="{"true" if i==0 else "false"}">{E(value["label"])}</button>' for i,(key,value) in enumerate(sc.get('states',{}).items()))+'</div>'
        content=f'<div class="demo-grid">{screen(sc,assets,video)}<div class="aside"><div class="tag">{E(sc["visual_label"])}</div>'+tabs+''.join(f'<div class="point">{E(x)}</div>' for x in points)+'</div></div>'
    elif kind=='compare':
        content='<div class="comparison">'+''.join(f'<div class="panel {"after" if i else ""}"><div class="tag">{"개선 흐름" if i else "기존 흐름"}</div><div class="big">{E(x)}</div></div>' for i,x in enumerate(points[:2]))+'</div>'+ (f'<p class="note">{E(points[2])}</p>' if len(points)>2 else '')
    elif kind=='flow':content='<div class="flow-grid">'+''.join(f'<div class="step"><b>0{i+1}</b>{E(x)}</div>' for i,x in enumerate(points))+'</div>'
    elif kind=='evidence':
        rows=sc.get('table') or [[str(i+1),x,'확인 범위 명시'] for i,x in enumerate(points)]
        content='<table class="evidence-table"><thead><tr><th>확인 항목</th><th>관찰한 결과</th><th>판정 / 한계</th></tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{E(x)}</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table>'
    else:content=f'<div class="hero">{E(sc["visual_label"])}</div><div class="pills">'+''.join(f'<div class="pill">{E(x)}</div>' for x in points)+'</div>'
    return f'''<section id="{sid}-scene" class="scene {kind} {'video' if video else ''}" style="--accent:{m['accent']}"><div class="rule"></div><p class="eyebrow">{E(m['title'])} / PROJECT SHOWCASE</p><h1>{E(sc['title'])}</h1><p class="claim">{E(sc['claim'])}</p><div class="layout" id="{sid}-content">{content}</div><div class="foot"><span>{LABELS[sc['verification']]}{' · 학습 예제' if m['profile']=='sample' else ''}</span><span>{sc['slide']:02} / 08</span></div></section>'''

def motion(sc,row,assets):
    sid=sc['id'];parts=["const tl=gsap.timeline({paused:true});",f"tl.fromTo('#{sid}-content',{{y:12}},{{y:0,duration:.4,ease:'power2.out'}},0);",f"tl.fromTo('#{sid}-progress',{{scaleX:0,transformOrigin:'left'}},{{scaleX:1,duration:{row['duration']},ease:'none'}},0);"]
    states=sc.get('states',{})
    if sc['kind']!='demo' and row.get('clips') and any('emphasis_id' in u for u in sc.get('utterances',[])):
        target=f'#{sid}-scene [data-content-id]'
        for clip in row['clips']:
            unit=next(u for u in sc['utterances'] if u['id']==clip['utterance'])
            parts.append(f"tl.set('{target}',{{opacity:1}},{clip['local_start']});")
            if unit.get('emphasis_id'):
                specific=target+f'[data-content-id=\"{unit["emphasis_id"]}\"]'
                parts.append(f"tl.set('{target}',{{opacity:.55}},{clip['local_start']});tl.to('{specific}',{{opacity:1,duration:.25}},{clip['local_start']});")
    elif sc['kind']!='demo' and row.get('clips') and any('emphasis_target' in u for u in sc.get('utterances',[])):
        selector={'compare':'.panel, .note','flow':'.step','evidence':'tbody tr'}.get(sc['kind'],'.pill')
        target=f'#{sid}-scene {selector}'.replace(', ',f', #{sid}-scene ')
        parts.append(f"const items=[...document.querySelectorAll('{target}')];")
        for clip in row['clips']:
            unit=next(u for u in sc['utterances'] if u['id']==clip['utterance'])
            if 'emphasis_target' in unit:
                i=unit['emphasis_target']-1
                parts.append(f"tl.set(items,{{opacity:.55}},{clip['local_start']});if(items[{i}])tl.to(items[{i}],{{opacity:1,duration:.25}},{clip['local_start']});")
            else:parts.append(f"tl.set(items,{{opacity:1}},{clip['local_start']});")
    for beat in row.get('beats',[]):
        t=beat['time'];key=beat['state'];w,h=assets[states[key]['media']]['size'];uid=f'{sid}-state-{key}'
        for other in states:parts.append(f"tl.set('#{sid}-state-{other}',{{display:'{'block' if other==key else 'none'}'}},{t});")
        # Each cue starts from explicit source geometry, so seeking backwards is stable.
        parts.append(f"tl.set('#{uid}',{{attr:{{viewBox:'0 0 {w} {h}'}}}},{t});tl.set('#{uid}-mark',{{opacity:0}},{t});")
        if beat['action']=='focus':
            x,y,rw,rh=beat['region'];box=f'{x*w} {y*h} {rw*w} {rh*h}'
            parts.append(f"tl.fromTo('#{uid}',{{attr:{{viewBox:'0 0 {w} {h}'}}}},{{attr:{{viewBox:'{box}'}},duration:.35,ease:'power2.out'}},{t});")
        elif beat['action']=='highlight':
            x,y,rw,rh=beat['region'];parts.append(f"tl.set('#{uid}-mark',{{attr:{{x:{x*w},y:{y*h},width:{rw*w},height:{rh*h}}},opacity:1}},{t});")
    parts.append(f"window.__timelines=window.__timelines||{{}};window.__timelines['{sid}']=tl;")
    return ''.join(parts)

NAV=r'''let current=0;const slides=[...document.querySelectorAll('.scene')];window.showSlide=n=>{current=Math.max(0,Math.min(slides.length-1,n));slides.forEach((s,i)=>s.style.display=i===current?'block':'none');document.getElementById('counter').textContent=(current+1)+'/'+slides.length;document.getElementById('prev').disabled=current===0;document.getElementById('next').disabled=current===slides.length-1;};const scale=()=>{document.getElementById('stage').style.transform=`translate(-50%,-50%) scale(${Math.min(innerWidth/1920,innerHeight/1080)})`;};addEventListener('resize',scale);addEventListener('keydown',e=>{if(['ArrowRight','Enter',' '].includes(e.key)){e.preventDefault();showSlide(current+1)}if(e.key==='ArrowLeft')showSlide(current-1);if(e.key==='Home')showSlide(0);if(e.key==='End')showSlide(slides.length-1);if(/^[1-8]$/.test(e.key))showSlide(Number(e.key)-1);if(e.key==='?')document.getElementById('help').hidden=!document.getElementById('help').hidden;if(e.key==='Escape')document.getElementById('help').hidden=true;if(e.key.toLowerCase()==='f')document.fullscreenElement?document.exitFullscreen():document.documentElement.requestFullscreen();});document.getElementById('prev').onclick=()=>showSlide(current-1);document.getElementById('next').onclick=()=>showSlide(current+1);document.getElementById('help-button').onclick=()=>document.getElementById('help').hidden=!document.getElementById('help').hidden;document.querySelectorAll('[data-state]').forEach(b=>b.onclick=()=>{const sc=document.getElementById(b.dataset.scene+'-scene');sc.querySelectorAll('.screen svg').forEach(v=>v.style.display=v.id===b.dataset.scene+'-state-'+b.dataset.state?'block':'none');sc.querySelectorAll('[data-state]').forEach(v=>v.setAttribute('aria-pressed',String(v===b)));});scale();showSlide(Number(location.hash.match(/slide=(\d+)/)?.[1]||1)-1);'''

def collect_assets(m,out):
    assets={}
    for sc in m['scenes']:
        for media in ([sc['media']] if sc.get('media') else [])+[x['media'] for x in sc.get('states',{}).values()]:
            if media not in assets:
                src=out/media;assets[media]={'path':f'assets/media/{len(assets):03}{src.suffix.lower()}','size':dimensions(src)}
    return assets

def prepare_assets(m,out,dest,skill):
    assets=collect_assets(m,out)
    dest.mkdir(parents=True,exist_ok=True)
    shutil.copytree(skill/'assets/fonts',dest/'assets/fonts',dirs_exist_ok=True)
    (dest/'assets/media').mkdir(exist_ok=True)
    for source,meta in assets.items():shutil.copy2(out/source,dest/meta['path'])
    if m.get('_design'):
        config=m['_design']['config'];source=Path(m['_design']['source'])
        for i,f in enumerate(config.get('fonts',[])):
            shutil.copy2(source/f['source'],dest/f'assets/design-font-{i}.woff2')
            shutil.copy2(source/f['license'],dest/f'assets/design-font-{i}-LICENSE.txt')
        for item in config.get('assets',[]):
            shutil.copy2(source/item['source'],dest/('assets/design-'+item['id']+Path(item['source']).suffix.lower()))
            shutil.copy2(source/item['license'],dest/('assets/design-'+item['id']+'-LICENSE.txt'))
    return assets

def style(m):
    custom=m.get('extra_css','')
    if '@import' in custom or 'url(' in custom:raise ValueError('extra_css에는 외부 리소스를 넣지 마세요')
    if m.get('_design'):
        from design_render import stylesheet
        return CSS+stylesheet(m['_design']['config'],Path(m['_design']['source']))+custom
    return CSS+custom

def build_deck(m,out,dest,skill):
    assets=prepare_assets(m,out,dest,skill);css=style(m)
    by_slide={}
    for sc in m['scenes']:by_slide.setdefault(sc['slide'],sc)
    order=list(by_slide) if m.get('_preview') else sorted(by_slide)
    slides=[body(by_slide[i],m,assets) for i in order]
    deck=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{E(m['title'])}</title><style>{css}#stage{{position:absolute;width:1920px;height:1080px;top:50%;left:50%;transform-origin:center}}nav{{position:fixed;bottom:8px;left:50%;transform:translateX(-50%);display:flex;gap:10px;align-items:center;font-size:14px;background:#223640;color:#fff;padding:4px 8px;border-radius:6px}}button{{background:#223640;color:white;border:1px solid #607780;padding:8px 14px;border-radius:4px}}button:disabled{{opacity:.35}}#help{{position:fixed;right:20px;bottom:60px;background:#223640;padding:24px;font-size:20px;z-index:99}}@media print{{#stage{{position:static;transform:none!important}}.scene{{display:block!important;position:relative;page-break-after:always}}nav,#help{{display:none}}}}</style><body><main id="stage">{''.join(slides)}</main><aside id="help" hidden>← → 이동 · 1–8 번호 이동 · Home / End · F 전체 화면 · ? 도움말</aside><nav><button id="prev" aria-label="이전 슬라이드">←</button><span id="counter"></span><button id="next" aria-label="다음 슬라이드">→</button><button id="help-button" aria-label="도움말">?</button></nav><script>{NAV}</script></body></html>'''
    (dest/'index.html').write_text(deck,encoding='utf-8')
    return assets

def build_outputs(m,t,out,skill):
    for dirname in ('deck','video'):
        dest=out/dirname
        if dest.exists():shutil.rmtree(dest)
    assets=build_deck(m,out,out/'deck',skill)
    prepare_assets(m,out,out/'video',skill)
    video=out/'video';(video/'compositions').mkdir(exist_ok=True);shutil.copy2(skill/'node_modules/gsap/dist/gsap.min.js',video/'assets/gsap.min.js')
    css=style(m)
    rows=t['scenes'] if t else [{'id':sc['id'],'start':i*5,'duration':5,'beats':[]} for i,sc in enumerate(m['scenes'])];total=t['duration'] if t else len(rows)*5
    mounts=[];audios=[];captions=[];beat_report=[]
    for sc,row in zip(m['scenes'],rows):
        sid=sc['id'];length=row['duration']
        mounts.append(f'<div id="{sid}" class="clip" data-composition-id="{sid}" data-composition-src="compositions/{sid}.html" data-start="{row["start"]}" data-duration="{length}" data-track-index="1" data-track-kind="graphics" data-width="1920" data-height="1080"></div>')
        comp=f'''<template><style>{css}#root{{position:absolute;inset:0}}</style><div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">{body(sc,m,assets,True)}<div class="progress" id="{sid}-progress" style="--accent:{m.get('_design',{}).get('config',{}).get('tokens',{}).get('accent',m['accent'])}"></div></div><script>{motion(sc,row,assets)}</script></template>'''
        (video/f'compositions/{sid}.html').write_text(comp,encoding='utf-8')
        for j,clip in enumerate(row.get('clips',[])):
            target=video/clip['audio'];target.parent.mkdir(exist_ok=True);shutil.copy2(out/'audio'/Path(clip['audio']).name,target)
            audios.append(f'<audio id="voice-{sid}-{j}" class="clip" src="{clip["audio"]}" data-start="{clip["start"]}" data-duration="{clip["duration"]}" data-track-index="3" data-volume="1"></audio>')
        for beat in row.get('beats',[]):beat_report.append({'scene':sid,**beat,'absolute_start':row['start']+beat['time'],'text':next(u['text'] for u in sc['utterances'] if u['id']==beat['utterance'])})
    if t:
        for i,c in enumerate(t['captions']):
            start=math.ceil(c['start']*30)/30;end=math.floor(c['end']*30)/30
            if i+1<len(t['captions']):end=min(end,math.ceil(t['captions'][i+1]['start']*30)/30-1/30)
            if end<=start:raise ValueError('자막 구간이 한 프레임보다 짧습니다')
            captions.append(f'<div id="caption-{i}" class="clip caption" data-start="{start}" data-duration="{end-start}" data-track-index="2" data-track-kind="captions"><span>{E(c["text"])}</span></div>')
    root=f'''<!doctype html><html lang="ko"><meta charset="utf-8"><title>{E(m['title'])}</title><style>{css}#root{{position:relative;width:1920px;height:1080px;overflow:hidden}}</style><script src="assets/gsap.min.js"></script><body><div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1920" data-height="1080">{''.join(mounts+audios+captions)}</div><script>window.__timelines=window.__timelines||{{}};window.__timelines.main=gsap.timeline({{paused:true}});</script></body></html>'''
    (video/'index.html').write_text(root,encoding='utf-8');(video/'hyperframes.json').write_text(json.dumps({'width':1920,'height':1080,'fps':30}))
    (out/'BEATS.json').write_text(json.dumps(beat_report,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'SPEC.md').write_text(f"# 제작 스펙\n\n{m['title']}\n\n청중: {m['audience']}\n\n메시지: {m['message']}\n\n{m['profile']} / HTML 8장 / 1920×1080 30fps / 실제 또는 예상 길이 {total:.2f}초\n\n음성: {m['voice']} / BGM 없음. 화면 연결은 BEATS.json과 실제 프레임으로 검토.\n",encoding='utf-8')
    board=['# 스토리보드'];script=['# 확정 대본'];notes=['# 5분 발표자 노트\n\n총 300초']
    for sc,row in zip(m['scenes'],rows):
        board.append(f"\n## {sc['id']} — {sc['title']}\n\n{row['start']:.2f}~{row['start']+row['duration']:.2f}초 / {sc['verification']}\n\n"+'\n'.join(f"- {e['source']}: {e['finding']}" for e in sc['evidence']))
        script.append(f"\n## {sc['id']}\n\n{sc['narration']}")
    for i,seconds in enumerate([30,35,35,50,50,40,30,30],1):
        sc=next(x for x in m['scenes'] if x['slide']==i);notes.append(f"\n## {i}. {sc['title']} — {seconds}초\n\n{sc['claim']}\n\n"+'\n'.join('- '+x for x in sc['points']))
    for name,lines in [('STORYBOARD.md',board),('SCRIPT.md',script),('SPEAKER-NOTES.md',notes)]:(out/name).write_text('\n'.join(lines),encoding='utf-8')
