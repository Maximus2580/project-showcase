# v2 설치와 환경 점검

Node 22+, Python 3.12 권장(최소 3.10), FFmpeg와 ffprobe, Google Chrome을 먼저 설치합니다. 수업 전에 설치를 마치고 패키지 lockfile의 버전을 사용합니다. 기존 프로젝트의 `.venv`에 설치하지 않습니다.

ZIP을 프로젝트 최상위에 풀어 `.claude/skills/project-showcase/SKILL.md`를 확인합니다. 아래 명령은 프로젝트 최상위에서 실행합니다.

## macOS

`python3`이 지원 버전인지 먼저 확인합니다. 다른 이름으로 설치했다면 해당 실행 파일을 사용합니다.

```sh
python3 --version
python3 -m venv .showcase-venv
.showcase-venv/bin/python -m pip install -r .claude/skills/project-showcase/requirements.txt
npm ci --prefix .claude/skills/project-showcase
.showcase-venv/bin/python .claude/skills/project-showcase/scripts/showcase.py --out showcase-output/practice preflight
```

## Windows PowerShell

Python 실행기는 `py`, Node·FFmpeg는 PATH에 있어야 합니다. FFmpeg 압축을 풀었다면 bin 경로를 등록합니다. 가상환경 활성화 정책을 변경할 필요 없이 실행 파일을 직접 사용합니다.

```powershell
py -3.12 -m venv .showcase-venv
.\.showcase-venv\Scripts\python.exe -m pip install -r .claude/skills/project-showcase/requirements.txt
npm ci --prefix .claude/skills/project-showcase
.\.showcase-venv\Scripts\python.exe .claude/skills/project-showcase/scripts/showcase.py --out showcase-output/practice preflight
```

3.12가 없다면 먼저 지원 Python을 설치합니다. Chrome 특수 경로는 `CHROME_PATH`에 지정합니다. Windows 안내가 있다는 것과 실기기 시험 완료는 다릅니다. 검증 기록을 확인하세요.

## doctor와 preflight의 차이

- `doctor`: 실행 도구·패키지 버전 확인. `--online`이면 한국어 음성 목록도 조회합니다. 음성 생성과 렌더 성공을 뜻하지 않습니다.
- `preflight`: doctor, 짧은 한국어 실제 합성, 보드 생성, 검사·스냅샷, 시험 렌더와 스트림·길이 확인까지 수행합니다. 별도 하위 작업 폴더와 `preflight.json`을 만듭니다.
- preflight PASS는 **환경 시험만 통과**입니다. 실제 프로젝트의 근거 확인, 디자인 리뷰, 전체 청취, 수업의 30분 합격을 대신하지 않습니다.

## 제작 명령

이후 같은 Python과 CLI 접두어를 사용합니다.

`init --project <프로젝트>` → 입력 작성 → `validate` → `estimate` → `build` → 정지 화면 검토 → `tts` → `timeline` → `build --timed` → `check` → `snapshots` → 실제 프레임 리뷰 → `render` → 전체 청취 → `finish` → `export`.

각 리뷰 기록의 정확한 명령은 SKILL.md를 참고합니다. 청취 전 검토용 전달은 `export --draft`입니다. 기존 v1 입력은 `migrate`로 백업·변환한 뒤 화면 연결을 직접 검토합니다.
