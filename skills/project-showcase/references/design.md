# 프로젝트에 맞는 디자인 워크숍

새 프로젝트의 기본 흐름은 **근거 분석 → 디자인 브리프 → 네 방향 × 대표 세 장 → 사용자 선택 → 전체 제작**이다. 생성 속도보다 프로젝트 적합성·정보 전달·읽기 품질을 우선한다. 제작은 로컬 CLI, 브리프 해석과 실제 디자인 작성은 이 스킬을 사용하는 에이전트가 한다. CLI는 LLM을 호출하거나 자연어 요구를 자동 해석하지 않는다.

## 브리프와 소스 작성

아래 `project-showcase` 명령은 전역 설치 기준이다. ZIP/프로젝트 로컬 설치에서는 이 접두어를 `<PYTHON> <SKILL>/scripts/showcase.py`로 바꾼다. 비교 HTML이 복사하는 명령에는 실제 생성에 사용한 Python과 스크립트 절대경로가 들어간다.

`init`는 `design.mode=variants`로 시작한다. 분석과 실제 캡처 확보 후 다음을 실행한다.

```sh
project-showcase --out <OUT> design-scaffold --request '고객에게 신뢰감 있게 보여 주는 담백한 제품 소개'
```

`design-scaffold`의 네 방향은 **편집을 시작할 구성 예제**다. 그대로 완성 시안이라고 제시하지 않는다. 초기 시각 설정을 그대로 유지하면 `W_DESIGN_STARTER` 경고가 나온다. 맞춤 변경 또는 유지 근거를 실제 이미지와 함께 검토한다. 경고가 없다는 것만으로 맞춤 디자인 완성을 주장하지 않는다. `design/brief.json`과 `design/variants/<id>/{variant.json,style.css,shell.html}`을 프로젝트에 맞게 작성한다.

- 해석 우선순위: 사용자의 명시적 요청 → 제공한 브랜드 규칙 → 실제 프로젝트 성격·청중·발표 맥락. 충돌하면 브리프에 결정 이유를 남긴다. AX·업무용으로 한정하지 않는다.
- `brief.context`, `decision_notes`, `constraints`, `brand_guidelines`에 적용 근거를 기록한다. `request`는 project.json의 design.request와 일치시킨다. 각 variant의 `rationale`와 `request_mapping`에 해당 요구가 어떻게 반영됐는지 적는다.
- 네 방향을 매번 같은 이름·색·스타일 조합으로 고정하지 않는다. 예를 들어 개발 도구는 명령·출력, 소비자 제품은 사용 상황, 연구 도구는 근거·비교, 자동화는 입력·결과를 중심으로 설계한다. 스타일 선택은 업종 고정 규칙이 아니다.
- 레이아웃, 타이포그래피 위계, 이미지 처리, 밀도 중 최소 세 축이 각 방향 사이에서 다르도록 만든다. 색상만 다른 네 시안은 거절된다. 수치 차이만 충족했다고 실제 디자인 다양성을 주장하지 말고 이미지를 비교한다.
- 대표 장면은 `[표지 ID, demo ID, 가장 어려운 정보 장면 ID]` 순서다. 긴 표·다이어그램·긴 제목 등 실패 위험이 높은 장면을 선택하고 `representative_reason`을 적는다. 실행 불가 프로젝트는 그 사유가 명시된 demo를 사용한다.
- 네 방향에는 같은 내용·검증 범위·원본 화면을 사용한다. 스타일을 위해 주장·성과·UI를 새로 만들지 않는다. 원고가 너무 길면 공통 입력을 고친다.
- 한글 제목, 실제 화면의 중요한 글자, 표, 자막 여백을 실제로 확인한다. 장식보다 제품의 구체적인 동작을 보여 준다.

작성 완료 후 `brief.ready=true`로 바꾸고 실행한다.

```sh
project-showcase --out <OUT> design-preview
```

이 명령은 음성·타임라인 없이 세 장짜리 HTML과 실제 브라우저 PNG를 만든다. 1080p·720p에서 글자 잘림·겹침·숨김·화면 이미지·탐색을 검사한다. 자동 검사는 전문성이나 의미의 정확성을 보장하지 않는다. 비교 링크를 전달하기 전에 에이전트도 PNG를 열어 위계·가독성·차별성을 검토한다.

## 비교와 실제 선택

`<OUT>/design/index.html`에서 표지 네 개, 방향별 세 장 펼침, 전체 12장, 두 방향 비교, 전체 크기 보기를 제공한다. 좁은 화면에서는 두 방향도 한 열로 표시한다. HTML 선택 버튼은 **명령을 복사하며 선택을 저장하지 않는다**. 대화에서 방향과 리비전을 선택해도 된다.

```sh
project-showcase --out <OUT> design-select direction-b --revision r001 --by '실제 선택자' --reason '사용자가 B안의 화면 중심 구성을 선택'
```

선택자의 실제 답변을 근거로 기록한다. 에이전트가 선호를 지어내거나 응답 대기를 승인으로 처리하지 않는다. 선택이 없으면 브리프 보완·QA·비교 자료까지 마친 후 **선택 대기**로 멈춘다. full build, tts, timeline, resume, check, snapshots, render, finish, export는 선택 전 실행할 수 없다. 자동 테스트의 명시적인 fixture 선택은 사용자 선호·디자인 승인으로 보고하지 않는다.

정확한 최신 리비전과 소스·로컬 폰트·이미지·대표 내용·렌더러·미리보기 해시를 연결한다. 소스 변경 후 이전 선택 명령을 실행하면 실패한다. 재생성 시간과 사용자 선택 대기 시간은 별도 기록한다.

## 수정·재선택

- **일부 수정:** 해당 variant 원본을 고치고 `design-preview --variant direction-b`. 이전 r001은 그대로 남고 r002를 만든다. 변경된 시안을 다시 보고 새 리비전을 선택한다. 나머지 방향은 재생성하지 않는다.
- **혼합 요청:** 사용자가 고른 배치·타입·이미지 처리를 한 방향의 소스에 통합한다. 원본 방향과 통합 이유를 rationale에 적는다. 통합된 세 장을 새 리비전으로 만든 뒤 다시 선택받는다. 서로 다른 리비전의 조각을 승인 없이 전체 덱에 섞지 않는다.
- **전부 거절:** 새 브리프 작성 전 `design-scaffold --replace --request '수정 요구'`. 이전 디자인 폴더 전체와 선택 기록을 backups로 보존한다. 기존 생성 덱도 자동 덮어쓰기하지 않는다.
- **전체 디자인/브랜드 변경:** 선택 소스의 style.css·shell.html·토큰·폰트를 수정하고 대표 세 장부터 재선택한다. variants 모드의 project.extra_css는 금지된다.
- **장면 내용 수정:** 전체 스타일 선택은 유지하되 새 build와 전체 검사·최종 프레임 검토가 필요하다. 대표 장면의 시각 내용 또는 배치가 바뀌면 미리보기와 재선택도 필요하다. 발화만 바뀌면 스타일을 다시 선택할 필요 없다. 변경되지 않은 음성은 재사용한다.
- **미리보기 직접 수정:** 저장된 리비전은 보존되고 변조로 감지된다. variant 원본으로 수정 내용을 옮겨 새 리비전을 만든다. variants 모드의 제작 HTML 직접 수정은 check에서 차단한다. 전역 CSS 변경으로 선택을 우회하지 않도록 variant 또는 project 원본에 옮긴 뒤 재생성한다. 직접 고친 파일은 `--regenerate`로 백업한다. legacy만 기존 수동 HTML → check 경로를 유지한다.

## 구성 계약

`kind`는 내용 의미, `layout`은 표현 방식이다. 기본값은 variant.layouts에서 지정한다. 특정 장면의 scene.layout은 이 기본값을 덮어쓴다.

| kind | layout |
|---|---|
| problem / closing | split, center, rail, statement |
| compare | panels, stack, ledger, contrast |
| flow | steps, stack, rail, path |
| demo | side, stage, left, focus |
| evidence | table, cards, ledger, matrix |

`variant.tokens`는 bg/fg/muted/panel/accent 색, title-size/weight/tracking, radius, image-border, 선택적 heading-font/body-font다. 본문 색 대비는 4.5 이상을 요구한다. density는 balanced/spacious/compact/statement 중 하나이며 세부 스타일은 style.css로 조정한다. 사용자 요청을 이 네 단어로 한정하지 않는다.

`fonts`는 `{family, source, license}`, `assets`는 `{id, source, license}` 배열이다. 파일은 해당 variant 폴더 안에 둔다. 폰트는 WOFF2, 이미지는 PNG/JPG/WebP, license는 로컬 고지 파일 경로다. 외부 URL을 렌더 중 불러오지 않는다. `shell.html`은 `{{header}}`, `{{content}}`, `{{footer}}` 슬롯을 각각 한 번 포함하는 HTML 구조이며 선언한 이미지는 `<img src="{{asset:logo}}" alt="...">`로 삽입한다. 스크립트·이벤트 핸들러·외부 CSS는 지원하지 않는다. 컨텐츠를 슬롯 밖에 중복 입력하지 않는다.

슬라이드와 영상은 같은 HTML/CSS 렌더러를 사용한다. 영상에는 자막·진행 여백에 맞춘 축약이 있으므로 영상 프레임은 별도 확인한다. `data-role=scene/title/text/content/footer`, `data-content-id`가 검사·모션의 공통 연결점이다. 시각 클래스명으로 발화 의미를 연결하지 않는다.

새 입력은 `items: [{id,text}]`, 표는 `rows: [{id,cells:[항목,관찰,판정]}]`가 내용 원본이다. points/table은 로딩 시 파생된다. 순서를 바꿀 때 ID와 내용을 함께 이동한다. 발화의 `emphasis_id`는 이 ID를 가리킨다. `design-scaffold`는 기존 points/table과 emphasis_target을 백업 후 ID로 옮긴다.

기존 design 필드 없는 schema v1/v2는 legacy 경로로 유지한다. `init --legacy`는 명시적으로 예전 고정 스타일을 생성한다. 기존 프로젝트를 새 흐름에 넣을 때만 design-scaffold를 실행한다. preflight는 명시적 legacy 환경 fixture로, 디자인 선택이나 사용자 검수를 대신하지 않는다.
