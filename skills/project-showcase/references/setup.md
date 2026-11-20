# 설치와 환경 점검

저장소의 `scripts/install_global.py`로 전역 설치한다. 설치가 끝난 환경은 SKILL.md 마지막의 Prepared global runtime 경로를 사용한다. 소스 폴더에서 작업한다면 아래처럼 전용 환경을 만든다. 기존 프로젝트의 `.venv`를 바꾸지 않는다.

```sh
python3.12 -m venv .showcase-venv
.showcase-venv/bin/python -m pip install -r skills/project-showcase/requirements.txt
npm ci --prefix skills/project-showcase
.showcase-venv/bin/python skills/project-showcase/scripts/showcase.py --out showcase-output/preflight preflight
```

Windows는 `py -3.12`, `.showcase-venv\Scripts\python.exe`, `npm.cmd`를 사용한다. Node 22+, Python 3.12 권장, Chrome, FFmpeg/ffprobe가 필요하다. 특수 Chrome 경로는 `CHROME_PATH`로 지정한다.

- `doctor`: 도구 버전 확인. `--online`은 음성 목록도 확인한다.
- `preflight`: 자동 생성한 진단 입력으로 실제 합성·레이아웃 검사·프레임·짧은 시험 렌더를 수행한다. 환경 확인이며 프로젝트 내용·디자인·최종 청취 검수를 대체하지 않는다.

제작은 `init` → 실제 근거 작성 → `validate` → `design-scaffold` → 브리프·시안 작성 → `design-preview` → 사용자 선택·`design-select` → `build` → `tts` → `timeline` → `build --timed` → `check` → `snapshots` → 프레임 리뷰 → `render` → 전체 청취 → `finish` → `export` 순서다. 기존 design 필드 없는 입력은 legacy 경로를 유지한다. 청취 전 전달은 `export --draft`다.
