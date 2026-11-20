"""Neutral project outlines and generated environment-test data.

No bundled demo app, customer records or promotional example screenshots.
The diagnostic PNGs are generated locally and are never project evidence.
"""
import json
import struct
import zlib
from pathlib import Path

KINDS=('problem','compare','flow','demo','demo','evidence','evidence','closing')
TITLES=('누구를 위한 프로젝트인가','어떤 문제를 해결하는가','어떻게 동작하는가','실제 입력과 사용자 흐름','실제 결과와 예외 처리','무엇을 확인했는가','어떤 한계가 남아 있는가','다음 단계는 무엇인가')

def outline(title):
    scenes=[]
    for i,(kind,label) in enumerate(zip(KINDS,TITLES),1):
        sc={'id':f'scene-{i:02}','slide':i,'kind':kind,'title':label,
            'claim':'프로젝트 분석 후 확인한 사실로 작성하세요.','visual_label':'내용 작성 대기',
            'points':['실제 사용자와 상황','확인한 구현 또는 실행 결과','확인하지 못한 범위'],
            'verification':'unverified','evidence':[{'source':'inventory.json','finding':'파일 목록만 생성했습니다. 내용 검토나 실행 확인의 증거가 아닙니다.'}],
            'utterances':[{'id':'u01','text':'프로젝트 분석 후 발표 대본을 작성하세요.'}],
            'states':{},'beats':[]}
        if kind=='demo':sc['unavailable_reason']='실제 프로젝트의 실행 결과를 아직 확보하지 않았습니다.'
        if kind=='evidence':sc['table']=[['구현','프로젝트 코드 확인 필요','미확인'],['실행','실제 실행 결과 확인 필요','미확인'],['효과','측정한 수치만 기록','미측정']]
        scenes.append(sc)
    return {'schema_version':2,'profile':'sample','title':title,'audience':'발표 청중을 작성하세요',
            'message':'프로젝트의 핵심 가치를 작성하세요','accent':'#8dcfff',
            'voice':'ko-KR-SunHiNeural','rate':'+5%','scenes':scenes}

def diagnostic_png(path,alternate=False):
    """Write a deterministic RGB calibration image using only the standard library."""
    w,h=1280,560
    colors=[(224,235,244),(34,76,110),(87,143,157),(42,107,95),(217,226,237)]
    if alternate:colors=list(reversed(colors))
    row=b'\x00'+b''.join(bytes(colors[min(4,x*5//w)]) for x in range(w))
    def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
    data=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(row*h))+chunk(b'IEND',b'')
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)

def environment_fixture(out):
    """Seed diagnostic data for preflight and automated tests, never for a user deck."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    m=outline('Project Showcase 환경 검사')
    m['audience']='도구 환경을 점검하는 사용자';m['message']='한글·레이아웃·음성·이미지 전환을 검사합니다.'
    for name,alt in [('input',False),('result',True)]:diagnostic_png(out/'input'/f'{name}.png',alt)
    for sc in m['scenes']:
        sc.update(claim='환경 검사 전용 합성 데이터입니다. 실제 프로젝트가 아닙니다.',visual_label='한글 · 화면 · 음성 연결',
                  verification='unverified',evidence=[{'source':'bootstrap.environment_fixture','finding':'자동 생성한 진단 입력. 실제 제품·사용자·업무 효과를 나타내지 않습니다.'}])
        sc['points']=['입력과 결과 파일 연결','한글 제목과 본문 가독성','자동 검사와 실제 검토 구분']
        sc['utterances']=[{'id':f'u{i+1:02}','text':text} for i,text in enumerate(('한글 제목과 화면을 확인합니다.','발화와 시각 요소의 연결을 확인합니다.','환경 시험은 실제 프로젝트 검수를 대신하지 않습니다.'))]
        if sc['kind']=='demo':
            sc.pop('unavailable_reason',None)
            sc['states']={key:{'media':f'input/{key}.png','label':'진단 입력' if key=='input' else '진단 결과','source':'generated calibration PNG'} for key in ('input','result')}
            sc['beats']=[{'utterance':'u01','action':'replace','state':'input'},{'utterance':'u02','action':'highlight','state':'result','region':[.1,.1,.6,.6]},{'utterance':'u03','action':'focus','state':'result','region':[.2,.1,.6,.7]}]
        elif sc['kind'] in ('compare','flow'):
            for i,u in enumerate(sc['utterances']):u['emphasis_target']=i+1
    (out/'project.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return m
