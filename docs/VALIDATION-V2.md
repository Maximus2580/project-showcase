# Project Showcase v2 검증 기록

## 2.1.0 이름 변경·공개 준비 검증

- 이름·슬러그·호출 명령·전역 설치를 project-showcase로 변경했다. 설명은 웹앱·도구·스크립트·프로토타입을 포괄한다.
- 회귀 테스트 44개 통과(실제 Chrome 3개 포함). 신규 전역 설치 프로그램의 설치·기존 파일 보존·명시적 교체 백업을 검증했다.
- 새 전역 명령으로 실제 한국어 합성·브라우저 검사·시험 MP4를 포함한 preflight 통과.
- 새 브랜딩의 덱·자막·HyperFrames 검사 및 188.933초 MP4 렌더 통과. 전체 파일 디코딩과 0.7/99.7/188.9초 추출 프레임 직접 확인.
- 공개 파일 51개를 점검했다. 개인 절대 경로, 기존 스킬 식별자, 대표적인 비밀키 형식이 발견되지 않았고 캐시·의존성·계정 파일을 제외했다. 이는 모든 형태의 비밀정보를 탐지한다는 보증이 아니다.
- 전체 음성 청취, Windows 실기기, 실제 사용자의 30분 완주는 계속 미검증이다. 예제 ZIP은 검수 대기 상태를 유지한다.

아래 내용은 이전 v2 생성·리뷰의 상세 이력이다.

검증일: 2026-11-21 (KST). 상태: 구현·자동 검사·시각 검토 완료, 최종 MP4 전체 청취 대기. v1 원본과 배포물은 `artifacts/backups/before-v2-1795188993.zip`에 보관했다. 이 문서의 v2 검증 당시에는 외부 게시나 수강생 배포를 수행하지 않았다.

## 구현 범위

스펙·보드·대본 → 발화별 TTS → 실측 타임라인 → 상태와 beat 연결 → 자동 게이트 → 프레임 리뷰 → 렌더 → 전체 청취 → 제출 ZIP 흐름을 제공한다. v2는 각 입력의 실제 결과를 states로 분리하고, utterance 시작에 replace/focus/highlight를 연결한다. 본문 강조는 의미를 확인한 emphasis_target만 사용한다.

8장 덱은 문제·비교·흐름·실제 데모·근거 표·마무리 구성을 구분했다. 데모 상태 선택, 키보드 이동, 처음/끝 버튼, 도움말을 제공하며 720p 탐색 UI와 페이지번호의 겹침을 제거했다. 실행할 수 없는 프로젝트는 화면을 꾸미지 않고 이유와 실행 미확인을 표시한다.

재검사 실패 시 이전 승인 무효화, SRT·대본·노트·스펙·보드·원본 화면 해시 연결, 원본 변경 시 재생성, 수동 수정과 새 파일 보호·백업, 읽기 전용 status, 종료된 프로세스 잠금 recover, 현재 소스와 렌더 일치 검사, 미참조 input 제외 및 원자적 ZIP 생성을 반영했다.

## 수행한 검증

| 항목 | 실제 결과 | 범위 |
|---|---|---|
| 회귀 테스트 | 43개 통과 | 상태·계약 40개, 실제 Chrome 3개. mock 오디오는 품질 근거로 쓰지 않음 |
| 전용 Python 환경 | 신규 .showcase-venv 설치·43개 테스트 통과 | 기존 프로젝트 .venv를 변경하지 않음. 같은 macOS 장비 |
| 환경 preflight | 실제 한국어 합성·브라우저 검사·27.9초 시험 MP4 통과 | 환경 시험이며 프레임/청취 합격 아님 |
| 주 예제 자동 검사 | deck 8장+상태4장, 자막46구간, HF lint/runtime/layout 통과 | HF layout 9시점, contrast 59/59. 별도 motion 검사 disabled는 수행으로 계산하지 않음 |
| 주 예제 프레임 | 50개 스냅샷, 변경 구간 재검토 | 상세 방법과 한계는 REVIEW-V2.md |
| 최종 MP4 | 188.933초, 1920×1080, 30fps, AAC 음성 | 영상 제작 76.0초. 전체 과정 30분 실측이 아님 |
| 최종 파일 확인 | 전체 디코딩 통과, MP4에서 24프레임 추출 | 장면 경계·데모 전환·끝 프레임 검토용 |
| 최종 MP4 시각 검토 | 실제 추출 11프레임 직접 검토 통과 | 배송·환불·미분류·장면 경계·마지막. 전체 연속 재생/청취 아님 |
| ZIP 검증 | 두 ZIP의 전 파일 MANIFEST 해시 일치·제외 항목·상대 링크 통과 | 학생 ZIP 새 폴더 추출 후 npm ci + doctor 통과. Python은 신규 .showcase-venv 사용 |
| 음량 측정 | mean −17.5 dB, peak −2.9 dB | 수치 측정이며 실제 발음·청감·싱크 청취를 대신하지 않음 |
| 비웹 자동화 fixture | CSV 합성5행 → JSON/HTML 결과 대조, 35.57초 TTS·보드·게이트·스냅샷 통과 | 완료2/지연2/진행1. 이 fixture의 최종 MP4·청취는 미실시 |
| 실행 불가 fixture | 38.57초 TTS·보드·게이트·스냅샷 통과 | 실행 화면 미확보·사유 표시. 앱 실행 성공을 뜻하지 않음 |

실행 환경: macOS, Python 3.12.13, Node 22.23.2, FFmpeg 8.0.1, HyperFrames 0.9.72, Playwright 1.65.1, edge-tts 7.3.1. 브라우저 자동 갱신 과정의 일시적인 Chrome 라이브러리 로드 실패 1회는 실패로 기록했고 동일 명령 재실행 후 통과했다. 관련 로그는 출력 폴더 logs에 남겼다.

## 아직 검증하지 않은 것

- 최종 MP4를 처음부터 끝까지 사람이 청취한 결과: 미검증. listening 승인이나 finish 완료를 기록하지 않았다. 예제 ZIP은 --draft, 검수 대기 상태다.
- Windows 실기기 및 새 장비의 네이티브 도구 설치: 미검증.
- 실제 학생 프로젝트 전체 분석의 정확성, 학생 2~3대 동시 온라인 TTS, 준비 완료 후 실제 30분 완주: 미검증.
- 실제 행사장 프로젝터 가독성, 타사 앱·API와 연결된 학생 프로젝트: 미검증.

다음 수업 전 실제 확인 순서는 INSTRUCTOR-CHECKLIST.md를 따른다. 이 구현의 테스트 통과를 수업 현장 합격이나 업무 성과로 표현하지 않는다.

## 재현과 전달

```sh
.showcase-venv/bin/python -m unittest discover -s tests -q
.showcase-venv/bin/python scripts/package.py --draft
```

학생용은 `artifacts/project-showcase-v2-student.zip`, 검토용 예제는 `artifacts/project-showcase-v2-example.zip`이다. 압축을 푼 예제의 시작 파일은 `artifacts/project-showcase-example/deck/index.html`, 영상은 `artifacts/project-showcase-example/showcase.mp4`다. MANIFEST.json에는 실제 파일별 해시와 검수 상태가 있다. 로컬 QA 상세 근거는 `showcase-output/v2-example/qa/`와 state.json에 남겼다.
