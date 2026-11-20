"""Synthetic CSV fixture; no external service or customer data."""
import csv, html, json
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parent
rows=list(csv.DictReader((ROOT/'tasks.csv').open(encoding='utf-8')))
counts=Counter(r['status'] for r in rows)
summary={'rows':len(rows),'by_status':dict(counts)}
(ROOT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
items=''.join(f'<tr><td>{html.escape(k)}</td><td>{v}</td></tr>' for k,v in counts.items())
(ROOT/'report.html').write_text(f'''<!doctype html><html lang="ko"><meta charset="utf-8"><title>작업 현황 집계</title><style>*{{box-sizing:border-box}}body{{font:32px system-ui;background:#ecf2ef;color:#15372e;padding:50px}}main{{background:white;padding:40px;border-radius:20px}}h1{{font-size:48px;margin-top:0}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;padding:24px;border-bottom:1px solid #bbcfc5}}small{{font-size:22px}}</style><main><small>CSV 집계 · 합성 데이터</small><h1>작업 {len(rows)}건의 현황</h1><table><tr><th>상태</th><th>건수</th></tr>{items}</table><p>외부 전송 없음 · 합성 예제 5행</p></main></html>''',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False))
