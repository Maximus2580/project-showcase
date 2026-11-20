# 예제의 목적과 범위

- `project.json` + `input/`: 배송·환불·미분류를 실제 브라우저에서 확인한 약 3분 한국어 영상 입력. 규칙 기반 학습 앱이며 LLM 제품이 아닙니다. `demo-project/index.html`과 `scripts/capture-example.mjs`로 화면을 재현합니다.
- `automation-project/`: `summarize.py`가 합성 CSV 5행을 집계합니다. `scripts/capture-automation.mjs`는 실행 생성 report.html을 캡처합니다. `project.json`은 짧은 sample 파이프라인 검사 입력이며 3분 완성 예제가 아닙니다.
- `unlaunchable-project/`: 진입점·의존성이 없어 실행할 수 없는 의도적 fixture. 동작을 꾸미지 않고 `unavailable_reason`을 보여 주는 짧은 sample 입력입니다.

두 보조 fixture는 폴더의 project.json과 (있으면) input 폴더를 새 출력 폴더로 복사하고 `resume`을 실행합니다. 전체 프로젝트 분석은 이 고정 fixture 시험으로 검증되지 않습니다. 실제 학생 프로젝트 검증은 별도 필요합니다.
