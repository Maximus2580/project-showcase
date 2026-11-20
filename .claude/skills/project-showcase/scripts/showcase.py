#!/usr/bin/env python3
"""Project Showcase: local, resumable pipeline. All subprocesses use argv, never a shell."""
import argparse, asyncio, hashlib, html, importlib.metadata, json, math, os, re
import shutil, subprocess, sys, time, uuid, zipfile, tempfile, platform
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
KINDS = {'problem', 'compare', 'demo', 'flow', 'evidence', 'closing'}
SKIP = {'.git', '.env', '.venv', '.showcase-venv', 'venv', 'node_modules', 'dist', 'build', '__pycache__', '.next', '.claude', 'showcase-output', 'artifacts'}
FPS = 30
RUN_LOG_DIR = None

def read(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def write(p, obj):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'); tmp.replace(p)

def digest(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()

def filehash(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def safe(root, name):
    if not isinstance(name,str) or Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name:
        raise ValueError('상대 경로와 / 구분자를 사용하세요: '+str(name))
    p = (Path(root) / name).resolve()
    if not p.is_relative_to(Path(root).resolve()):
        raise ValueError('출력 폴더 밖의 경로는 사용할 수 없습니다: ' + str(name))
    return p

def run(argv, cwd=None, timeout=300, env=None):
    started=time.monotonic()
    try:
        result = subprocess.run([str(a) for a in argv], cwd=cwd, env=env, text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        if RUN_LOG_DIR:
            write(RUN_LOG_DIR/f'{time.time_ns()}.json',{'argv':list(map(str,argv)),'timeout':timeout,'stdout':str(e.stdout or ''),'stderr':str(e.stderr or '')})
        raise RuntimeError(f'E_TIMEOUT: {Path(str(argv[0])).name} ({timeout}초); logs 폴더 확인') from e
    if RUN_LOG_DIR:
        write(RUN_LOG_DIR/f'{time.time_ns()}.json',{'argv':list(map(str,argv)),'cwd':str(cwd) if cwd else None,'seconds':time.monotonic()-started,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    if result.returncode:
        raise RuntimeError(f'{Path(str(argv[0])).name} 실패 ({result.returncode})\n{result.stderr[-2500:]}\n{result.stdout[-1500:]}')
    return result.stdout

def hf(*args, cwd=None, timeout=300):
    cli = SKILL / 'node_modules/hyperframes/dist/cli.js'
    if not cli.exists():
        pkg = read(SKILL / 'node_modules/hyperframes/package.json')
        binary = pkg['bin']; binary = binary['hyperframes'] if isinstance(binary, dict) else binary
        cli = SKILL / 'node_modules/hyperframes' / binary
    env=dict(os.environ)
    if env.get('CHROME_PATH'):env.setdefault('HYPERFRAMES_BROWSER_PATH',env['CHROME_PATH'])
    return run(['node', cli, *args], cwd, timeout, env=env)

def probe(p):
    data = json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', p]))
    return data

def duration(p):
    value = float(probe(p)['format']['duration'])
    if not math.isfinite(value) or value <= 0: raise ValueError('음성 길이가 유효하지 않습니다')
    return value

def state(out):
    p = out / 'state.json'
    return read(p) if p.exists() else {'status': '진행 중', 'steps': {}, 'reviews': {}}

def record(out, step, payload):
    s = state(out); s['steps'][step] = payload; s['status'] = '진행 중'; s.pop('error', None)
    write(out / 'state.json', s)

def load(out):
    m = read(out / 'project.json')
    if m.get('schema_version') == 2:
        for sc in m.get('scenes', []):
            sc['narration'] = ' '.join(u.get('text','') for u in sc.get('utterances', []))
    validate(m, out); return m

def validate(m, out):
    errors = []
    if m.get('schema_version') not in (1,2): errors.append('E_SCHEMA: schema_version은 1 또는 2')
    if m.get('profile') not in ('production', 'sample'): errors.append('profile은 production 또는 sample')
    if not m.get('title') or not m.get('audience') or not m.get('message'): errors.append('title, audience, message 필수')
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', m.get('accent', '')): errors.append('accent는 #RRGGBB')
    if m.get('voice') not in ('ko-KR-SunHiNeural', 'ko-KR-InJoonNeural'): errors.append('검증 대상 한국어 음성을 선택하세요')
    if not re.fullmatch(r'[+-]\d{1,2}%', m.get('rate', '+0%')): errors.append('rate 형식 오류')
    scenes = m.get('scenes', []); ids = set(); slides = set()
    if not scenes: errors.append('scenes가 비었습니다')
    for sc in scenes:
        sid = sc.get('id', '')
        if not re.fullmatch(r'[a-z][a-z0-9-]{0,39}', sid) or sid in ids: errors.append('장면 id 중복 또는 형식 오류: ' + sid)
        ids.add(sid)
        if sc.get('kind') not in KINDS: errors.append(sid + ': kind 오류')
        if type(sc.get('slide')) is not int or not 1 <= sc['slide'] <= 8: errors.append(sid + ': slide는 1~8')
        else: slides.add(sc['slide'])
        for field in ('title', 'claim', 'narration', 'visual_label'):
            if not isinstance(sc.get(field), str) or not sc[field].strip(): errors.append(sid + ': ' + field + ' 필수')
        if len(sc.get('title', '')) > 50: errors.append(sid + ': 제목은 50자 이하')
        if len(sc.get('claim', '')) > 110: errors.append(sid + ': claim은 110자 이하')
        points = sc.get('points', [])
        if not 1 <= len(points) <= 3 or any(not isinstance(x, str) or len(x) > 90 for x in points): errors.append(sid + ': points는 90자 이하 1~3개')
        if sc.get('verification') not in ('executed', 'code-reviewed', 'unverified'): errors.append(sid + ': verification 필수')
        evidence = sc.get('evidence', [])
        if not evidence or any(not e.get('source') or not e.get('finding') for e in evidence): errors.append(sid + ': evidence에 source/finding 필수')
        if sc.get('media'):
            p = safe(out, sc['media'])
            if not p.is_file() or p.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp'): errors.append(sid + ': 로컬 화면 이미지가 필요합니다')
        unavailable=sc.get('unavailable_reason')
        if unavailable and (not isinstance(unavailable,str) or not unavailable.strip() or sc.get('verification')=='executed' or sc.get('media') or sc.get('states') or sc.get('beats')):errors.append('E_UNAVAILABLE_DEMO: '+sid)
        if m.get('profile') == 'production' and sc.get('kind') == 'demo' and not sc.get('media') and not sc.get('states') and not unavailable: errors.append(sid + ': production 데모는 실제 캡처 이미지 또는 실행 불가 사유 필수')
    if m.get('schema_version') == 2: validate_v2(m,out,errors)
    if slides != set(range(1, 9)): errors.append('8장 슬라이드 모두에 장면을 연결하세요')
    if not any(sc.get('kind') == 'demo' for sc in scenes): errors.append('데모 장면이 필요합니다')
    if errors: raise ValueError('\n'.join(errors))

def inventory(project, out):
    project = project.resolve(); rows = []; skipped = 0
    for base, dirs, files in os.walk(project, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in SKIP and not (Path(base)/d).is_symlink() and (Path(base)/d).resolve() != out.resolve())
        for name in sorted(files):
            p = Path(base)/name
            if p.is_symlink() or name.startswith('.env') or p.suffix.lower() in ('.pem','.key','.p12') or re.search(r'credential|secret|token', name, re.I):
                skipped += 1; continue
            rows.append({'path': p.relative_to(project).as_posix(), 'bytes': p.stat().st_size})
    write(out/'inventory.json', {'project': str(project), 'files': rows, 'excluded_sensitive_files': skipped, 'notice': '파일 목록입니다. 기능 실행 또는 내용 검토의 증거가 아닙니다.'})

def init(args):
    out = args.out
    if (out/'project.json').exists(): raise ValueError('기존 project.json을 보존합니다. 다른 --out을 사용하세요')
    out.mkdir(parents=True, exist_ok=True)
    example = read(SKILL/'examples/project.json')
    write(out/'project.json', example)
    shutil.copytree(SKILL/'examples/input',out/'input',dirs_exist_ok=True)
    inventory(args.project, out)
    record(out, 'init', {'at': time.time(), 'profile': 'sample'})
    print('sample 프로젝트를 만들었습니다. inventory.json을 검토하고 project.json을 실제 프로젝트 근거로 수정하세요.')

def doctor(args):
    write(args.out/'doctor.json',{'ok':False,'status':'checking','at':time.time()})
    checks = {}
    for name, argv in {'node':['node','--version'], 'python':[sys.executable,'--version'], 'ffmpeg':['ffmpeg','-version'], 'ffprobe':['ffprobe','-version']}.items():
        try:
            checks[name] = {'ok': True, 'version':run(argv).splitlines()[0]}
            if name=='node': checks[name]['ok']=int(checks[name]['version'].lstrip('v').split('.')[0])>=22
            if name=='python': checks[name]['ok']=sys.version_info >= (3,10)
        except Exception as e: checks[name] = {'ok':False, 'error':str(e)}
    try:
        v = importlib.metadata.version('edge-tts'); checks['edge-tts'] = {'ok':v == '7.3.1', 'version':v}
    except importlib.metadata.PackageNotFoundError: checks['edge-tts'] = {'ok':False}
    try:
        checks['hyperframes'] = {'ok':True, 'version':hf('--version').strip()}
        checks['hyperframes']['ok']=checks['hyperframes']['version']=='0.9.72'
    except Exception as e: checks['hyperframes'] = {'ok':False,'error':str(e)}
    if args.online:
        import edge_tts
        voices = asyncio.run(edge_tts.list_voices())
        names = [v['ShortName'] for v in voices if v['Locale'] == 'ko-KR']
        checks['korean_voices'] = {'ok':'ko-KR-SunHiNeural' in names, 'voices':names}
    report = {'checks':checks, 'ok':all(c['ok'] for c in checks.values()), 'note':'Chrome 브라우저·폰트·음성·렌더 검증은 sample 실행으로 확인합니다.'}
    write(args.out/'doctor.json', report); print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report['ok']: raise ValueError('환경 점검 실패: doctor.json 확인')

def stamp(seconds):
    ms = round(seconds * 1000); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def srt(cues):
    return '\n\n'.join(f'{i+1}\n{stamp(c["start"])} --> {stamp(c["end"])}\n{c["text"]}' for i,c in enumerate(cues))+'\n'

def voice_key(m, sc):
    return digest({'text':sc['narration'], 'voice':m['voice'], 'rate':m.get('rate','+0%'), 'engine':'edge-tts-7.3.1', 'boundary':'SentenceBoundary'})

async def synth(m, sc, mp3):
    import edge_tts
    com = edge_tts.Communicate(sc['narration'], m['voice'], rate=m.get('rate','+0%'), boundary='SentenceBoundary', connect_timeout=10, receive_timeout=30)
    cues = []
    with mp3.open('wb') as f:
        async for c in com.stream():
            if c['type'] == 'audio': f.write(c['data'])
            elif c['type'] == 'SentenceBoundary': cues.append({'start':c['offset']/1e7, 'end':(c['offset']+c['duration'])/1e7, 'text':c['text']})
    if not cues: raise ValueError('발화 경계가 없습니다. 무자막 음성을 완료 처리하지 않습니다')
    return cues

def tts(args):
    invalidate(args.out,'tts')
    out=args.out; m=load(out); folder=out/'audio'; folder.mkdir(exist_ok=True)
    for sc in voice_units(m):
        key=voice_key(m, sc); base=folder/key; meta=base.with_suffix('.json'); mp3=base.with_suffix('.mp3')
        if meta.exists() and mp3.exists() and read(meta).get('audio_sha256')==filehash(mp3):
            print(sc['id']+': 캐시 사용', flush=True); continue
        for attempt in range(3):
            tmp=base.with_suffix('.part.mp3')
            try:
                cues=asyncio.run(asyncio.wait_for(synth(m, sc, tmp), timeout=90)); length=duration(tmp)
                for cue in cues:
                    if not 0 <= cue['start'] < cue['end'] <= length + .15: raise ValueError('발화 경계가 음성 길이를 벗어납니다')
                    cue['end']=min(cue['end'],length)
                tmp.replace(mp3)
                write(meta, {'key':key,'duration':length,'cues':cues,'audio_sha256':filehash(mp3)})
                base.with_suffix('.srt').write_text(srt(cues),encoding='utf-8'); print(sc['id']+f': {length:.2f}초',flush=True); break
            except Exception:
                tmp.unlink(missing_ok=True)
                if attempt==2: raise
                time.sleep((2,5)[attempt])
    record(out,'tts',{'voice_keys':[voice_key(m,s) for s in voice_units(m)]})

def make_timeline(m,out):
    frame=0; scenes=[]; captions=[]
    for i,sc in enumerate(m['scenes']):
        first=frame; clips=[]; utterance_times={}
        units=sc.get('utterances') if m.get('schema_version')==2 else [{'id':sc['id'],'text':sc['narration']}]
        for j,u in enumerate(units):
            unit={'narration':u['text']};key=voice_key(m,unit)
            meta=read(out/'audio'/f'{key}.json');mp3=out/'audio'/f'{key}.mp3'
            if meta['audio_sha256']!=filehash(mp3): raise ValueError('E_AUDIO_CHANGED: tts를 재실행하세요')
            length=meta['duration']
            if not math.isfinite(length) or length<=0: raise ValueError('E_AUDIO_DURATION')
            start=frame/FPS;utterance_times[u['id']]=(frame-first)/FPS
            clips.append({'utterance':u['id'],'start':start,'local_start':(frame-first)/FPS,'duration':length,'audio':f'assets/audio/{key}.mp3'})
            previous=0
            for ci,cue in enumerate(meta['cues']):
                if not previous<=cue['start']<cue['end']<=length+.01:raise ValueError('E_CUE_RANGE')
                previous=cue['start'];end=cue['end']
                if ci+1<len(meta['cues']):
                    following=meta['cues'][ci+1]['start']
                    # Sentence events can overlap by 50 ms. Trim display only;
                    # larger overlaps fail and the audio itself is unchanged.
                    if end-following>.101:raise ValueError('E_CUE_OVERLAP')
                    end=min(end,following)
                if end<=cue['start']:raise ValueError('E_CUE_RANGE')
                captions.append({'scene':sc['id'],'utterance':u['id'],'start':start+cue['start'],'end':start+end,'text':cue['text']})
            gap=(1 if i==len(m['scenes'])-1 else .3) if j==len(units)-1 else .08
            frame+=math.ceil((length+gap)*FPS)
        beats=[dict(beat,time=utterance_times[beat['utterance']]) for beat in sc.get('beats',[])]
        scenes.append({'id':sc['id'],'start_frame':first,'frames':frame-first,'start':first/FPS,'duration':(frame-first)/FPS,'clips':clips,'beats':beats,'audio_duration':sum(x['duration'] for x in clips)})
    if m['profile']=='production' and not 170<=frame/FPS<=190:
        lengths=', '.join(f"{x['id']}={x['duration']:.1f}s" for x in scenes)
        raise ValueError(f'E_DURATION: {frame/FPS:.2f}초. 170~190초 필요. 장면별: {lengths}')
    return {'fps':FPS,'width':1920,'height':1080,'frames':frame,'duration':frame/FPS,'scenes':scenes,'captions':captions}

def timeline(args):
    protect_edits(args)
    m=load(args.out); t=make_timeline(m,args.out)
    invalidate(args.out,'build')
    write(args.out/'timeline.json', t)
    (args.out/'captions.srt').write_text(srt(t['captions']),encoding='utf-8')
    st=state(args.out)
    for name in ('timeline.json','captions.srt'):
        st.setdefault('last_generated',{})[name]=filehash(args.out/name)
    write(args.out/'state.json',st)
    record(args.out,'timeline',{'digest':digest(t),'duration':t['duration']}); print(f'{t["duration"]:.2f}초 / {t["frames"]} frames')

def referenced_inputs(m,out):
    names=set()
    for sc in m['scenes']:
        if sc.get('media'):names.add(sc['media'])
        names.update(x['media'] for x in sc.get('states',{}).values())
    return {name:safe(out,name) for name in sorted(names)}

def inputs_digest(m,out):
    return digest({name:filehash(p) for name,p in referenced_inputs(m,out).items()})

def build_signature(out):
    paths=[]
    for dirname in ('deck','video'):
        for p in sorted((out/dirname).rglob('*')):
            if p.is_file() and not any(x in p.relative_to(out/dirname).parts for x in ('.hyperframes','renders','node_modules')):
                paths.append((p.relative_to(out).as_posix(),filehash(p)))
    m=read(out/'project.json')
    return digest({'project':m,'files':paths,'inputs':{name:filehash(p) for name,p in referenced_inputs(m,out).items()},'sidecars':{name:filehash(out/name) if (out/name).exists() else None for name in SIDECARS}})

def build(args):
    from render import build_outputs
    m=load(args.out)
    protect_edits(args)
    invalidate(args.out,'build')
    t=make_timeline(m,args.out) if args.timed else None
    if t:
        write(args.out/'timeline.json',t); (args.out/'captions.srt').write_text(srt(t['captions']),encoding='utf-8')
    build_outputs(m,t,args.out,SKILL)
    record(args.out,'build',{'signature':build_signature(args.out),'timed':bool(t),'project_digest':digest(m),'inputs_digest':inputs_digest(m,args.out),'generated':generated_files(args.out),'at':time.time()})
    print('생성: deck/index.html, video/index.html, SPEC.md, STORYBOARD.md, SCRIPT.md')

def parse_json(text):
    # CLI may prefix progress. Only accept a complete JSON object envelope.
    decoder=json.JSONDecoder()
    for i,c in enumerate(text):
        if c=='{':
            try:
                obj,end=decoder.raw_decode(text[i:])
                if isinstance(obj,dict) and 'ok' in obj: return obj
            except ValueError: pass
    raise ValueError('검사 JSON을 읽을 수 없습니다')

def gate_hf(r):
    if r.get('ok') is not True or r.get('browserSkipped') is not False: return False
    layout=r.get('layout',{})
    # Fail closed when the pinned report shape changes.
    return isinstance(layout,dict) and (isinstance(layout.get('samples'),list) and len(layout['samples'])>0 or any(type(layout.get(k)) in (int,float) and layout[k]>0 for k in ('samples','samplesChecked','sampleCount')))

def check(args):
    out=args.out; invalidate(out,'check'); m=load(out); st=state(out)
    b=st['steps'].get('build',{})
    if not b.get('timed') or b.get('project_digest')!=digest(m): raise ValueError('최신 timed build가 필요합니다')
    if b.get('inputs_digest')!=inputs_digest(m,out):raise ValueError('E_INPUTS_CHANGED: 원본 화면이 변경되었습니다. build --timed 또는 resume로 재생성하세요.')
    qa=out/'qa'; qa.mkdir(exist_ok=True)
    run(['node',SKILL/'scripts/check-deck.mjs',out/'deck/index.html',qa/'deck'],timeout=180)
    deck=read(qa/'deck/report.json')
    run(['node',SKILL/'scripts/check-captions.mjs',out/'video/index.html',qa/'captions.json'],timeout=120)
    lint=hf('lint',cwd=out/'video'); (qa/'lint.txt').write_text(lint,encoding='utf-8')
    raw=hf('check','--json',cwd=out/'video',timeout=300); (qa/'hyperframes-raw.txt').write_text(raw,encoding='utf-8')
    result=parse_json(raw); write(qa/'hyperframes.json',result)
    ok=deck['ok'] and gate_hf(result)
    record(out,'check',{'ok':ok,'signature':build_signature(out),'id':str(uuid.uuid4()),'at':time.time()})
    if not ok: raise ValueError('게이트 실패 또는 미실행: qa 보고서 확인')
    print('자동 검사 통과. snapshot 후 실제 이미지 리뷰가 필요합니다.')

def snapshots(args):
    out=args.out; invalidate(out,'snapshots'); t=read(out/'timeline.json'); times={0, max(0,t['duration']-1/FPS)}
    for sc in t['scenes']:
        times.update([sc['start']+.7, sc['start']+sc['duration']/2])
        for beat in sc.get('beats',[]): times.update([sc['start']+beat['time'],sc['start']+beat['time']+.5])
        if sc['start']>0: times.update([sc['start']-1/FPS,sc['start'],sc['start']+.2])
    values=','.join(f'{v:.4f}' for v in sorted(times) if v<t['duration'])
    result=hf('snapshot','--at',values,cwd=out/'video',timeout=300)
    (out/'qa').mkdir(exist_ok=True); (out/'qa/snapshots.txt').write_text(result,encoding='utf-8')
    record(out,'snapshots',{'signature':build_signature(out),'times':sorted(times),'at':time.time()}); print(result)

def review(args):
    out=args.out; st=state(out); sig=build_signature(out)
    if args.kind=='frames':
        if not st['steps'].get('check',{}).get('ok') or st['steps']['check'].get('signature')!=sig: raise ValueError('최신 자동 검사 통과 필요')
        if st['steps'].get('snapshots',{}).get('signature')!=sig: raise ValueError('최신 snapshots 필요')
    else:
        r=st['steps'].get('render',{})
        if r.get('signature')!=sig or not (out/r.get('file','missing')).is_file() or filehash(out/r['file'])!=r.get('sha256'): raise ValueError('최신 MP4 검증 필요')
    st['reviews'][args.kind]={'signature':sig,'reviewer':args.reviewer,'notes':args.notes,'at':time.time(), 'render_sha256':st['steps'].get('render',{}).get('sha256'), 'check_id':st['steps'].get('check',{}).get('id')}
    write(out/'state.json',st); print('리뷰 기록. 실제로 확인한 사람과 범위만 기록하세요.')

def render(args):
    out=args.out; sig=build_signature(out); st=state(out)
    require_frames(out)
    invalidate(out,'render')
    target=out/'renders'/f'showcase-{time.time_ns()}.mp4'; target.parent.mkdir(exist_ok=True)
    started=time.monotonic()
    result=hf('render','--quality','delivery','--fps','30','-o',str(target),cwd=out/'video',timeout=900)
    (out/'qa/render.txt').write_text(result,encoding='utf-8')
    p=probe(target); streams=p['streams']; v=next((s for s in streams if s['codec_type']=='video'),{}); aud=next((s for s in streams if s['codec_type']=='audio'),{})
    t=read(out/'timeline.json')
    if v.get('width')!=1920 or v.get('height')!=1080 or not aud or abs(float(p['format']['duration'])-t['duration'])>.15: raise ValueError('최종 파일 스펙/길이/음성 트랙 검사 실패')
    n,d=map(int,v.get('avg_frame_rate','0/1').split('/'))
    if d==0 or abs(n/d-30)>.01: raise ValueError('최종 프레임률 오류')
    write(out/'qa/ffprobe.json',p)
    record(out,'render',{'signature':sig,'sha256':filehash(target),'file':target.relative_to(out).as_posix(),'elapsed_seconds':time.monotonic()-started})
    st=state(out); st['status']='검수 대기'; write(out/'state.json',st)
    write(out/'REVIEW.json',{'status':'검수 대기','reviews':st['reviews'],'render':st['steps']['render'],'pending':['최종 MP4 전체 청취 및 화면-음성 일치 확인']})
    print(str(target))

def finish(args):
    out=args.out; m=load(out); require_frames(out); assert_sidecars(out); st=state(out); sig=build_signature(out); render=st['steps'].get('render',{})
    if st['steps'].get('check',{}).get('signature')!=sig or not st['steps'].get('check',{}).get('ok'): raise ValueError('최신 자동 검사 필요')
    if render.get('signature')!=sig: raise ValueError('최신 렌더 필요')
    for k in ('frames','listening'):
        r=st['reviews'].get(k,{})
        if r.get('signature')!=sig: raise ValueError(k+' 최신 리뷰 필요')
    if st['reviews']['listening'].get('render_sha256')!=render.get('sha256'): raise ValueError('현재 렌더 청취 필요')
    if not render.get('file') or filehash(out/render['file'])!=render.get('sha256'): raise ValueError('렌더 파일 변경 감지')
    if m['profile']=='sample': st['status']='검수 대기'; st['note']='예제입니다. 실제 프로젝트 또는 강사 합격으로 표시하지 않습니다.'
    else: st['status']='완료'
    write(out/'state.json',st)
    report={'status':st['status'],'profile':m['profile'],'reviews':st['reviews'],'steps':st['steps'],'deliverables':['deck/index.html',render['file'],'captions.srt','SCRIPT.md','SPEAKER-NOTES.md','STORYBOARD.md','SPEC.md']}
    write(out/'REVIEW.json',report); print(st['status'])

def resume(args):
    out=args.out;m=load(out);protect_edits(args)
    st=state(out);b=st['steps'].get('build',{})
    if b.get('project_digest')!=digest(m) or b.get('inputs_digest')!=inputs_digest(m,out) or not b.get('timed'):
        tts(args);args.timed=True;build(args)
    st=state(out)
    if st['steps'].get('check',{}).get('signature')!=build_signature(out) or not st['steps'].get('check',{}).get('ok'):check(args)
    st=state(out)
    if st['steps'].get('snapshots',{}).get('signature')!=build_signature(out):snapshots(args)
    print('필요한 단계만 재개했습니다. frames 리뷰 → render → 전체 청취 → listening 리뷰 → finish/export')

SIDECARS=('timeline.json','captions.srt','SCRIPT.md','SPEAKER-NOTES.md','SPEC.md','STORYBOARD.md','BEATS.json')
STAGES=['tts','build','check','snapshots','render','finish']

def invalidate(out,stage):
    st=state(out);start=STAGES.index(stage)
    for key in STAGES[start:]:
        if key in st['steps']:
            if key=='build': st['last_generated']=st['steps'][key].get('generated',{})
            st.setdefault('history',[]).append({'stage':key,'result':st['steps'].pop(key),'invalidated_at':time.time()})
    if start<=STAGES.index('snapshots'): st['reviews'].clear()
    else:st['reviews'].pop('listening',None)
    st['status']='진행 중';write(out/'state.json',st)

def require_frames(out):
    st=state(out);sig=build_signature(out);check=st['steps'].get('check',{});rev=st['reviews'].get('frames',{})
    if not check.get('ok') or check.get('signature')!=sig:raise ValueError('E_CHECK_REQUIRED: 최신 검사 합격 필요')
    if not check.get('id') or rev.get('check_id')!=check['id'] or rev.get('signature')!=sig:raise ValueError('E_FRAMES_REQUIRED: 최신 프레임 리뷰 필요')
    if st['steps'].get('snapshots',{}).get('signature')!=sig:raise ValueError('E_SNAPSHOTS_REQUIRED')

def assert_sidecars(out):
    for name in SIDECARS:
        if not (out/name).is_file():raise ValueError('E_DELIVERABLE_MISSING: '+name)

def generated_files(out):
    result={}
    for folder in ('deck','video'):
        for p in sorted((out/folder).rglob('*')):
            if p.is_file() and not {'.hyperframes','renders','node_modules'}&set(p.relative_to(out/folder).parts):result[p.relative_to(out).as_posix()]=filehash(p)
    for name in SIDECARS:
        if (out/name).is_file():result[name]=filehash(out/name)
    return result

def protect_edits(args):
    out=args.out;old=state(out)['steps'].get('build',{}).get('generated',state(out).get('last_generated',{}))
    changed=[name for name,sha in old.items() if not (out/name).exists() or filehash(out/name)!=sha]
    if old:changed+=sorted(set(generated_files(out))-set(old))
    if not changed:return
    if not getattr(args,'regenerate',False):raise ValueError('E_MANUAL_EDITS: '+', '.join(changed)+'; 보존하려면 check 사용. 다시 생성하려면 --regenerate (자동 백업).')
    dest=out/'backups'/str(time.time_ns());dest.mkdir(parents=True)
    for p in out.iterdir():
        if p.name in ('backups','.pipeline.lock'):continue
        if p.is_dir():shutil.copytree(p,dest/p.name)
        else:shutil.copy2(p,dest/p.name)
    print('수동 수정 백업: '+str(dest))

def voice_units(m):
    for sc in m['scenes']:
        if m.get('schema_version')==2:
            for u in sc['utterances']:yield {'id':sc['id']+'/'+u['id'],'narration':u['text']}
        else:yield sc

def validate_v2(m,out,errors):
    for sc in m['scenes']:
        sid=sc['id'];units=sc.get('utterances',[]);ids=[u.get('id') for u in units]
        if not units or len(ids)!=len(set(ids)) or any(not isinstance(i,str) or not re.fullmatch(r'[a-z][a-z0-9-]*',i) for i in ids):errors.append('E_UTTERANCES: '+sid)
        if any(not isinstance(u.get('text'),str) or not u['text'].strip() for u in units):errors.append('E_UTTERANCE_TEXT: '+sid)
        count=len(sc.get('table') or sc.get('points',[]))
        if any('emphasis_target' in u and (type(u['emphasis_target']) is not int or not 1<=u['emphasis_target']<=count or sc['kind']=='demo') for u in units):errors.append('E_EMPHASIS_TARGET: '+sid)
        states=sc.get('states',{});order=[]
        for key,item in states.items():
            if not re.fullmatch(r'[a-z][a-z0-9-]*',key):errors.append('E_STATE_ID: '+sid)
            if not item.get('source') or not item.get('label'):errors.append('E_STATE_EVIDENCE: '+sid)
            if not item.get('media') or not safe(out,item['media']).is_file() or Path(item.get('media','')).suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):errors.append('E_STATE_MEDIA: '+sid)
        for beat in sc.get('beats',[]):
            uid=beat.get('utterance')
            if uid not in ids:errors.append('E_BEAT_UTTERANCE: '+sid);continue
            order.append(ids.index(uid))
            if beat.get('state') not in states:errors.append('E_BEAT_STATE: '+sid)
            if beat.get('action') not in ('replace','focus','highlight'):errors.append('E_BEAT_ACTION: '+sid)
            if beat.get('action') in ('focus','highlight'):
                r=beat.get('region',[])
                if len(r)!=4 or any(type(x) not in (int,float) or not math.isfinite(x) for x in r) or (len(r)==4 and (min(r)<0 or r[2]<=0 or r[3]<=0 or r[0]+r[2]>1 or r[1]+r[3]>1)):errors.append('E_BEAT_REGION: '+sid)
        if order!=sorted(set(order)):errors.append('E_BEAT_ORDER: '+sid)
        if sc['kind']=='demo' and not sc.get('unavailable_reason') and (not sc.get('beats') or (ids and sc['beats'][0].get('utterance')!=ids[0])):errors.append('E_DEMO_BEATS: '+sid)
        if m['profile']=='production' and sc.get('needs_visual_review'):errors.append('E_MIGRATION_REVIEW: '+sid)

def migrate(args):
    p=args.out/'project.json';m=read(p)
    if m['schema_version']==2:print('이미 v2입니다');return
    shutil.copy2(p,args.out/f'project-v1-{time.time_ns()}.json')
    for sc in m['scenes']:
        sc['utterances']=[{'id':'u01','text':sc.pop('narration')}];sc['states']={};sc['beats']=[]
        if sc.get('media'):
            sc['states']['original']={'media':sc['media'],'label':sc['visual_label'],'source':sc['evidence'][0]['source']}
            sc['beats']=[{'utterance':'u01','action':'replace','state':'original'}]
        sc['needs_visual_review']=True
    m['schema_version']=2;write(p,m);invalidate(args.out,'tts');print('원본 백업 후 v2 변환. 화면 연결 검토 후 needs_visual_review를 해제하세요.')

def estimate(args):
    m=load(args.out);rows=[]
    for sc in m['scenes']:
        chars=len(re.sub(r'\s','',sc['narration']));rows.append({'id':sc['id'],'estimated_seconds':round(chars/5.5,1)})
    t=args.out/'timeline.json';report={'estimate_only':True,'total_seconds':round(sum(r['estimated_seconds'] for r in rows),1),'scenes':rows,'note':'한국어 5.5자/초 가정. 합성 후 실측이 기준.'}
    if t.exists():report['last_measured_seconds']=read(t)['duration']
    write(args.out/'estimate.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))

def recover(args):
    lock=args.out/'.pipeline.lock'
    if not lock.exists():print('잠금 없음');return
    data=read(lock)
    if data.get('host')!=platform.node():raise ValueError('E_LOCK_HOST: 다른 호스트 잠금은 수동 확인 필요')
    try:os.kill(data['pid'],0)
    except ProcessLookupError:lock.unlink();print('종료된 프로세스 잠금 정리');return
    except OSError:raise ValueError('E_LOCK_UNKNOWN: 프로세스 상태를 확인할 수 없습니다')
    raise ValueError('E_LOCK_ACTIVE: 실행 중 프로세스의 잠금은 제거하지 않습니다')

def export_bundle(args):
    out=args.out;m=load(out);assert_sidecars(out);require_frames(out)
    st=state(out);sig=build_signature(out);r=st['steps'].get('render',{})
    if r.get('signature')!=sig:raise ValueError('E_EXPORT_STALE: 영상과 현재 소스 불일치')
    video=safe(out,r.get('file','missing'))
    if not video.is_file() or filehash(video)!=r.get('sha256'):raise ValueError('E_EXPORT_VIDEO')
    if not getattr(args,'draft',False):
        listen=st['reviews'].get('listening',{})
        if listen.get('signature')!=sig or listen.get('render_sha256')!=r['sha256']:raise ValueError('E_LISTENING_REQUIRED: 미청취 결과는 --draft 사용')
    tracked=st['steps'].get('build',{}).get('generated',{})
    current=generated_files(out)
    if set(current)-set(tracked):raise ValueError('E_EXPORT_UNTRACKED: 생성 폴더에 등록되지 않은 파일이 있습니다. 별도 폴더로 옮기세요.')
    files={k:safe(out,k) for k in tracked}
    files['project.json']=out/'project.json';files['showcase.mp4']=video
    files.update(referenced_inputs(m,out))
    manifest={'schema_version':2,'signature':sig,'status':'검수 대기' if args.draft else '청취 확인','profile':read(out/'project.json')['profile'],'files':{n:filehash(p) for n,p in files.items()},'reviews':st['reviews']}
    target=out/'exports'/f"showcase-{'draft' if args.draft else 'reviewed'}-{time.time_ns()}.zip";target.parent.mkdir(exist_ok=True)
    tmp=target.with_suffix('.tmp')
    try:
        with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
            for name,p in files.items():z.write(p,name)
            z.writestr('MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
            z.writestr('START-HERE.txt',f"상태: {manifest['status']} / {manifest['profile']}\n슬라이드: deck/index.html\n영상: showcase.mp4\n미청취 결과는 배포 합격이 아닙니다.\n")
        if sig!=build_signature(out) or filehash(video)!=r['sha256']:raise ValueError('E_EXPORT_CHANGED')
        tmp.replace(target)
    finally:tmp.unlink(missing_ok=True)
    write(out/'delivery-manifest.json',manifest);print(target);return target


def preflight(args):
    write(args.out/'preflight.json',{'ok':False,'status':'checking','at':time.time()})
    args.online=True;doctor(args)
    work=args.out/'preflight'/str(time.time_ns());work.mkdir(parents=True)
    a=argparse.Namespace(out=work,project=args.out,timed=True,regenerate=False)
    init(a);m=read(work/'project.json')
    for sc in m['scenes']:
        sc['utterances']=[{'id':'u01','text':'한글 음성과 화면을 확인합니다.'}]
        sc['beats']=[dict(sc['beats'][0],utterance='u01')] if sc.get('beats') else []
    write(work/'project.json',m);tts(a);build(a);check(a);snapshots(a)
    # Environment test render is explicitly not a visual or listening approval.
    target=work/'environment-test.mp4'
    hf('render','--quality','draft','--fps','30','-o',str(target),cwd=work/'video',timeout=900)
    info=probe(target)
    if {x['codec_type'] for x in info['streams']}!={'audio','video'}:raise ValueError('E_PREFLIGHT_STREAMS')
    if abs(float(info['format']['duration'])-read(work/'timeline.json')['duration'])>.15:raise ValueError('E_PREFLIGHT_DURATION')
    write(args.out/'preflight.json',{'ok':True,'at':time.time(),'os':platform.platform(),'environment':read(args.out/'doctor.json'),'artifact':str(target),'sha256':filehash(target),'note':'환경 시험 통과. 디자인/청취/수업 합격을 뜻하지 않음'})
    print('preflight PASS: '+str(target))


def main():
    global RUN_LOG_DIR
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--out',type=Path,required=True)
    sp=p.add_subparsers(dest='command',required=True)
    s=sp.add_parser('init'); s.add_argument('--project',type=Path,default=Path.cwd())
    s=sp.add_parser('doctor'); s.add_argument('--online',action='store_true')
    sp.add_parser('validate'); sp.add_parser('tts'); sp.add_parser('timeline')
    s=sp.add_parser('build'); s.add_argument('--timed',action='store_true');s.add_argument('--regenerate',action='store_true')
    for name in ('check','snapshots','render','finish','status','estimate','preflight','migrate','recover'): sp.add_parser(name)
    s=sp.add_parser('resume');s.add_argument('--regenerate',action='store_true')
    s=sp.add_parser('export');s.add_argument('--draft',action='store_true')
    s=sp.add_parser('review'); s.add_argument('--kind',choices=['frames','listening'],required=True); s.add_argument('--reviewer',required=True); s.add_argument('--notes',required=True)
    a=p.parse_args(); a.out=a.out.resolve(); a.out.mkdir(parents=True,exist_ok=True); started=time.monotonic()
    if a.command=='status':
        print(json.dumps(state(a.out),ensure_ascii=False,indent=2));return 0
    if a.command=='recover': recover(a);return 0
    RUN_LOG_DIR=a.out/'logs'
    lock=a.out/'.pipeline.lock'
    try:
        fd=os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.write(fd,json.dumps({'pid':os.getpid(),'host':platform.node(),'started':time.time()}).encode()); os.close(fd)
    except FileExistsError:
        print('다른 명령이 실행 중입니다. status로 확인하세요. 비정상 종료였다면 recover 명령을 사용하세요.',file=sys.stderr); return 1
    try:
        st=state(a.out);st['active']={'command':a.command,'started':time.time(),'pid':os.getpid()};write(a.out/'state.json',st)
        if a.command=='validate': load(a.out); print('입력 검증 통과')
        elif a.command=='status': print(json.dumps(state(a.out),ensure_ascii=False,indent=2))
        else: globals()['export_bundle' if a.command=='export' else a.command](a)
    except Exception as e:
        st=state(a.out); st['status']='실패'; st['error']={'stage':a.command,'message':str(e),'resume':'입력과 오류를 수정한 뒤 같은 명령 또는 resume 실행'}; write(a.out/'state.json',st)
        print(str(e),file=sys.stderr); return 1
    finally:
        st=state(a.out);st.pop('active',None);write(a.out/'state.json',st)
        lock.unlink(missing_ok=True)
        with (a.out/'timings.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps({'command':a.command,'seconds':round(time.monotonic()-started,3),'at':time.time()})+'\n')
    return 0

if __name__=='__main__': sys.exit(main())
