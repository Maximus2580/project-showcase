"""Shared, composable slide renderer for design previews, decks and video.

The legacy renderer stays unchanged. Content roles and IDs are the public hooks;
visual classes and the optional shell/CSS are deliberately not animation APIs.
"""
import html
from pathlib import Path

E = lambda value: html.escape(str(value), quote=True)
LAYOUTS = {
    'problem': ('split', 'center', 'rail', 'statement'),
    'closing': ('split', 'center', 'rail', 'statement'),
    'compare': ('panels', 'stack', 'ledger', 'contrast'),
    'flow': ('steps', 'stack', 'rail', 'path'),
    'demo': ('side', 'stage', 'left', 'focus'),
    'evidence': ('table', 'cards', 'ledger', 'matrix'),
}

CSS = '''
.designed{background:var(--bg);color:var(--fg);padding:72px 100px 160px;font-family:var(--body-font,Showcase),sans-serif}
.designed .rule{display:none}.designed .eyebrow{color:var(--muted);font-size:24px;letter-spacing:0;margin:0 0 22px}
.designed h1{font-family:var(--heading-font,Showcase),sans-serif;font-size:var(--title-size,72px);font-weight:var(--title-weight,760);line-height:1.13;letter-spacing:var(--tracking,-2px);max-width:none;margin:0 0 20px}
.designed .claim{font-size:30px;color:var(--muted);line-height:1.4;max-width:1600px}
.designed .layout{height:470px;margin-top:36px}
.designed .foot{left:100px;right:100px;color:var(--muted);font-size:24px;bottom:48px}
.designed .hero{font-size:68px;line-height:1.2;font-weight:750;letter-spacing:-2px;color:var(--accent);padding:0;margin:0;max-width:none}
.design-items{display:flex;gap:26px;flex-direction:column;justify-content:center;margin:0;padding:0;list-style:none}
.design-item{font-size:32px;line-height:1.45;word-break:keep-all;overflow-wrap:anywhere}
.design-hero{height:100%;display:grid;grid-template-columns:1fr 1fr;align-items:center;gap:90px}
.layout-center .design-hero{grid-template-columns:1fr;text-align:center;gap:44px;align-content:center}
.layout-center .design-items,.layout-statement .design-items{flex-direction:row;justify-content:space-between;gap:36px}
.layout-center .design-item,.layout-statement .design-item{flex:1}
.layout-rail .design-hero{grid-template-columns:1fr 1.5fr;border-left:14px solid var(--accent);padding-left:50px;gap:70px}
.layout-statement .design-hero{display:flex;flex-direction:column;align-items:stretch;justify-content:center;gap:62px;padding:28px 0}
.layout-statement .hero{font-size:88px;max-width:1450px}
.design-compare{height:100%;display:grid;grid-template-columns:1fr 1fr;gap:30px;align-content:start}
.design-panel{background:var(--panel);border-radius:var(--radius);padding:32px 38px;min-height:290px}
.design-panel .tag{font-size:26px;color:var(--muted);margin:0 0 20px}
.design-panel .big{font-size:46px;line-height:1.3}.design-panel:last-of-type{border-top:6px solid var(--accent)}
.design-note{grid-column:1/-1;font-size:30px;line-height:1.4;margin:0}
.layout-stack .design-compare,.layout-ledger .design-compare{grid-template-columns:1fr;gap:22px}
.layout-stack .design-panel,.layout-ledger .design-panel{min-height:0;padding:22px 32px;display:grid;grid-template-columns:240px 1fr;gap:24px;align-items:center}
.layout-stack .design-panel .tag,.layout-ledger .design-panel .tag{margin:0}
.layout-stack .design-panel .big,.layout-ledger .design-panel .big{font-size:38px}
.layout-ledger .design-panel{background:transparent;border-bottom:2px solid var(--muted);border-top:none;border-radius:0}
.layout-contrast .design-panel:first-child{background:transparent;border:2px solid var(--muted)}
.design-flow{display:flex;gap:40px;list-style:none;margin:0;padding:25px 0;height:100%}
.design-step{flex:1;font-size:36px;line-height:1.4;border-top:5px solid var(--accent);padding-top:25px;word-break:keep-all}
.design-step b{display:block;font-size:58px;color:var(--accent);margin-bottom:20px}
.layout-stack .design-flow,.layout-rail .design-flow{flex-direction:column;gap:18px;padding:0}
.layout-stack .design-step,.layout-rail .design-step{display:flex;align-items:center;gap:35px;border-top:0;padding:16px 28px;background:var(--panel);border-radius:var(--radius);font-size:32px}
.layout-stack .design-step b,.layout-rail .design-step b{margin:0;font-size:42px}
.layout-rail .design-step{border-left:6px solid var(--accent);background:transparent}
.layout-path .design-step{border:0;border-left:3px solid var(--accent);padding:30px}
.designed .demo-grid{grid-template-columns:2.4fr 1fr;gap:36px}.designed .screen{border-radius:var(--radius);background:var(--panel);border:var(--image-border)}
.designed .screen svg{background:var(--panel)}.designed .aside{font-size:28px;gap:18px}.designed .aside .tag{font-size:24px;color:var(--muted)}
.designed .aside .point{border:0;padding:0;font-size:28px}.designed .state-tabs{gap:8px}.designed .state-tabs button{font-size:22px!important;padding:8px 10px!important;background:var(--panel);color:var(--fg);border:1px solid var(--muted)}
.designed .state-tabs button[aria-pressed=true]{background:var(--fg)!important;color:var(--bg)!important}
.layout-left .demo-grid{grid-template-columns:1fr 2.4fr}.layout-left .screen{order:2}
.designed.layout-stage .layout{height:510px}.layout-stage .demo-grid{grid-template-columns:1fr;grid-template-rows:420px 1fr;gap:20px}
.layout-stage .aside{display:grid;grid-template-columns:repeat(3,1fr);align-items:start;gap:22px}
.layout-stage .aside .tag{display:none}.layout-stage .state-tabs{position:absolute;right:12px;top:12px;z-index:1}
.layout-stage .aside .point{font-size:25px}.layout-focus .demo-grid{grid-template-columns:3.2fr 1fr;gap:26px}.layout-focus .aside .point{font-size:26px}
.design-table{width:100%;border-collapse:collapse;font-size:30px;line-height:1.4}
.design-table th{font-size:24px;color:var(--muted);text-align:left;border-bottom:3px solid var(--accent);padding:16px 24px}
.design-table td{padding:22px 24px;border-bottom:1px solid var(--muted);word-break:keep-all}
.design-table td:first-child{width:24%;font-weight:700}.design-table td:nth-child(2){width:40%}
.design-legend{font-size:24px;color:var(--muted);height:42px}.design-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:26px;height:calc(100% - 42px)}
.design-card{background:var(--panel);border-radius:var(--radius);padding:34px;display:flex;flex-direction:column;justify-content:space-between;gap:24px;line-height:1.4}
.design-card h2{font-size:32px;margin:0}.design-card p{font-size:30px;margin:0}.design-card small{font-size:26px;color:var(--muted)}
.layout-matrix .design-cards{grid-template-columns:1fr;gap:18px}
.layout-matrix .design-card{display:grid;grid-template-columns:1fr 1.4fr 1.2fr;align-items:center;padding:24px 30px;border-left:6px solid var(--accent)}
.layout-ledger .design-table td{padding:28px 24px}.layout-ledger .design-table th{border-bottom:4px solid var(--fg)}
.designed.video .layout{height:420px;margin-top:28px}.designed.video h1{font-size:min(var(--title-size),66px)}
.designed.video .hero{font-size:60px}.designed.video.layout-statement .hero{font-size:74px}
.designed.video .design-item{font-size:30px}.designed.video.layout-stage .demo-grid{grid-template-rows:350px 1fr}
.designed.video.layout-stage .layout{height:450px}.designed.video .design-panel{min-height:260px}.designed.video.layout-stack .design-panel,.designed.video.layout-ledger .design-panel{min-height:0}
.designed.video .design-table td{padding:18px 24px}
'''

def stylesheet(config, source):
    tokens = config['tokens']
    vars_ = ';'.join('--'+k+':'+v for k, v in tokens.items())
    fonts = ''
    for i, f in enumerate(config.get('fonts', [])):
        fonts += f'@font-face{{font-family:"{f["family"]}";src:url("assets/design-font-{i}.woff2");font-weight:100 900;font-display:block}}'
    density={'balanced':'','spacious':'.designed .design-items{gap:42px}','compact':'.designed .layout{margin-top:28px}.designed .design-items{gap:18px}','statement':'.designed .design-item{font-weight:650}'}[config['density']]
    return CSS + density + f'.designed{{{vars_}}}' + fonts + (source / 'style.css').read_text(encoding='utf-8')

def content_hook(sc, index, row=False):
    values = sc.get('rows' if row else 'items', [])
    key = values[index]['id'] if index < len(values) else f'item-{index+1}'
    return f'data-content-id="{E(key)}"'

def body(sc, m, assets, video=False):
    from render import screen, LABELS
    config = m['_design']['config']; source = Path(m['_design']['source'])
    kind = sc['kind']; sid = sc['id']; points = sc['points']
    layout = sc.get('layout') or config['layouts'][kind]
    if layout not in LAYOUTS[kind]:
        raise ValueError('E_LAYOUT: '+sid+' / '+layout)
    hook = lambda i, row=False: content_hook(sc, i, row)
    if kind == 'demo' and not sc.get('unavailable_reason'):
        tabs = '' if video else '<div class="state-tabs" aria-label="데모 화면 선택">'+''.join(f'<button data-role="text" data-scene="{sid}" data-state="{E(k)}" aria-pressed="{str(i==0).lower()}">{E(v["label"])}</button>' for i,(k,v) in enumerate(sc.get('states',{}).items()))+'</div>'
        content = f'<div class="demo-grid">{screen(sc,assets,video)}<div class="aside"><div class="tag">{E(sc["visual_label"])}</div>{tabs}'+''.join(f'<div class="point" data-role="text" {hook(i)}>{E(x)}</div>' for i,x in enumerate(points))+'</div></div>'
    elif kind == 'compare':
        content = '<div class="design-compare">'+''.join(f'<div class="design-panel" {hook(i)}><p class="tag" data-role="text">{"기존 흐름" if i==0 else "개선 흐름"}</p><div class="big" data-role="text">{E(x)}</div></div>' for i,x in enumerate(points[:2]))
        content += (f'<p class="design-note" data-role="text" {hook(2)}>{E(points[2])}</p>' if len(points)>2 else '')+'</div>'
    elif kind == 'flow':
        content = '<ol class="design-flow">'+''.join(f'<li class="design-step" {hook(i)}><b data-role="text">{i+1:02}</b><span data-role="text">{E(x)}</span></li>' for i,x in enumerate(points))+'</ol>'
    elif kind == 'evidence':
        rows = sc.get('table') or [[str(i+1), x, '확인 범위 명시'] for i,x in enumerate(points)]
        if layout in ('cards','matrix'):
            content = '<div class="design-legend" data-role="text">확인 항목 → 관찰한 결과 → 판정 / 한계</div><div class="design-cards">'+''.join(f'<article class="design-card" {hook(i,bool(sc.get("rows")))}><h2 data-role="text">{E(row[0])}</h2><p data-role="text">{E(row[1])}</p><small data-role="text">{E(row[2])}</small></article>' for i,row in enumerate(rows))+'</div>'
        else:
            content = '<table class="design-table"><thead><tr>'+''.join(f'<th data-role="text">{x}</th>' for x in ('확인 항목','관찰한 결과','판정 / 한계'))+'</tr></thead><tbody>'+''.join(f'<tr {hook(i,bool(sc.get("rows")))}>'+''.join(f'<td data-role="text">{E(x)}</td>' for x in row)+'</tr>' for i,row in enumerate(rows))+'</tbody></table>'
    else:
        label = '실행 화면 미확보' if sc.get('unavailable_reason') else sc['visual_label']
        values = [sc['unavailable_reason']] if sc.get('unavailable_reason') else points
        content = f'<div class="design-hero"><div class="hero" data-role="text">{E(label)}</div><ul class="design-items">'+''.join(f'<li class="design-item" data-role="text" {hook(i)}>{E(x)}</li>' for i,x in enumerate(values))+'</ul></div>'
    header = f'<header data-role="header"><p class="eyebrow" data-role="text">{E(m["title"])}</p><h1 data-role="title">{E(sc["title"])}</h1><p class="claim" data-role="text">{E(sc["claim"])}</p></header>'
    main = f'<div class="layout" data-role="content" id="{sid}-content">{content}</div>'
    footer = f'<footer class="foot" data-role="footer"><span data-role="text">{LABELS[sc["verification"]]}{" · 학습 예제" if m["profile"]=="sample" else ""}</span><span data-role="text">{sc["slide"]:02} / 08</span></footer>'
    shell = (source / 'shell.html').read_text(encoding='utf-8')
    for asset in config.get('assets',[]):
        shell=shell.replace('{{asset:'+asset['id']+'}}','assets/design-'+asset['id']+Path(asset['source']).suffix.lower())
    for key, value in [('header',header),('content',main),('footer',footer)]:
        shell = shell.replace('{{'+key+'}}',value)
    return f'<section id="{sid}-scene" data-role="scene" data-layout="{layout}" class="scene designed {kind} layout-{layout} {"video" if video else ""}">{shell}</section>'
