# 사용자 전역 설치

저장소를 내려받고 Python 3.12 환경에서 실행합니다.

```sh
python3 scripts/install_global.py
```

Windows에서는 `py -3.12 scripts/install_global.py`를 사용합니다. 설치 프로그램은 기존 프로젝트의 가상환경을 변경하지 않고 별도의 Python 환경과 고정 Node 의존성을 준비합니다. 전체 제작의 Windows 실기기 검증은 아직 수행하지 않았습니다.

| 대상 | 사용자 홈 기준 경로 |
|---|---|
| 공통 스킬 | `~/.agents/skills/project-showcase` |
| Claude Code 스킬 | `~/.claude/skills/project-showcase` |
| 전용 실행 환경 | `~/.local/share/project-showcase/venv` |
| 명령 | `~/.local/bin/project-showcase` (Windows: `.cmd`) |
| 설치 기록·백업 | `~/.local/share/project-showcase/` |

Claude Code 경로는 공통 스킬을 가리킵니다. Windows에서 심볼릭 링크를 만들 수 없으면 스킬 안내를 복사하고 공통 실행 환경을 사용합니다. 기존 설치는 보존하며, 교체는 `--replace`로 백업 후 진행합니다.

설치 후 새 대화에서 `/project-showcase` 또는 `project-showcase 스킬로 현재 프로젝트를 소개해 줘`라고 요청합니다. 같은 이름의 프로젝트 로컬 스킬이 있으면 로컬 우선순위가 적용될 수 있습니다. 전역 CLI는 공통 설치본을 사용합니다.

```sh
project-showcase --out showcase-output/preflight preflight
project-showcase --out showcase-output/demo init --project .
```

preflight는 실제 합성·브라우저 검사·짧은 시험 렌더를 수행하는 환경 검사입니다. init는 sample을 생성하므로 실제 프로젝트 근거와 화면으로 수정해야 합니다. 준비된 결과물을 완성으로 판정하려면 프레임 리뷰와 최종 MP4 전체 청취가 필요합니다.
