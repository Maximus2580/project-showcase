# v2 데이터 계약

내용 원본은 `project.json`, 예제는 `examples/project.json`입니다. `schema_version: 2`를 사용합니다. SPEC/STORYBOARD/SCRIPT 등 생성 문서만 직접 바꾸면 입력 원본을 수정한 것이 아닙니다.

## 공통과 장면

- profile: sample(학습·환경 예제), production(실제 프로젝트)
- title, audience, message: 대상과 핵심 결론
- accent: #RRGGBB. voice: ko-KR-SunHiNeural 또는 ko-KR-InJoonNeural. rate: 기본 +0%
- scenes: 순서 있는 영상 장면. slide는 1~8이며 모두 연결해야 합니다. 같은 slide가 여럿이면 덱에는 첫 장면이 사용됩니다.
- id: 장면마다 유일한 영문 소문자·숫자·하이픈. title 50자 이하, claim 110자 이하, points 1~3개(각 90자 이하)
- kind: problem / compare / flow / demo / evidence / closing
- verification: executed / code-reviewed / unverified
- evidence: source와 finding 배열. 실제 읽거나 실행한 근거로 작성하며 코드 존재와 실행 성공을 구분합니다.

## utterances → states → beats

`utterances`는 장면 안의 발화 단위 배열입니다. 각 항목에 유일한 id와 발음용 text를 넣습니다. 짧고 독립적인 설명 단위로 나누며, 수정된 발화만 음성을 재생성합니다.

`states`는 실제 화면 상태의 사전입니다. 각 상태는 media(출력 폴더 안 이미지 상대경로), label(보이는 내용), source(실제 근거)를 가집니다. 배송·환불·예외 결과를 설명한다면 **각 입력을 실제 실행한 결과 이미지**를 확보합니다. 한 결과 화면을 다른 입력의 결과처럼 재사용하지 않습니다.

`beats`는 발화와 화면을 연결하는 배열입니다.

```json
{
  "utterance": "u02",
  "action": "highlight",
  "state": "refund-result",
  "region": [0.1, 0.2, 0.7, 0.4]
}
```

- action: replace(화면 교체), focus(영역 집중), highlight(영역 강조)
- region: focus/highlight에 필요한 `[x,y,width,height]`. 원본 이미지 기준 0~1 정규화 좌표이며 영역이 이미지 안에 있어야 합니다.
- beat는 존재하는 utterance/state를 참조하고 발화 순서대로 배치합니다. 같은 발화에 중복 beat를 넣지 않습니다.
- 실행 화면이 있는 demo는 첫 발화부터 beat가 필요합니다. source 필드만 존재한다고 진실성이 자동 검증되지는 않습니다.
- 기존 scene.media는 호환 필드입니다. 새 v2 입력에 실제 이미지가 있는 states와 beats를 작성하면 scene.media를 중복 지정하지 않습니다.

실행 화면을 확보하지 못한 demo 장면은 `unavailable_reason`에 구체적인 사유를 적고, verification을 code-reviewed 또는 unverified로 둡니다. 이 경우 media/states/beats는 넣지 않습니다. 렌더에는 **실행 화면 미확보**가 표시됩니다. 실행한 것처럼 임의 화면을 만들지 않습니다.

## 타이밍과 수정

각 발화 음성은 같은 합성의 SentenceBoundary cue와 함께 저장합니다. 실제 음성 길이를 측정하고 발화 사이 0.08초, 장면 끝 0.3초, 영상 마지막 1초의 여유를 프레임 단위로 반영합니다. beat는 해당 발화 시작에 연결됩니다. 자막 시각을 글자 수로 추정하지 않습니다.

`estimate`는 한국어 문자량으로 분량을 미리 추정할 뿐입니다. `timeline`의 합성 후 실측이 기준이며 production은 170~190초가 필요합니다. 길이 오류에는 장면별 길이가 제공됩니다.

`migrate`는 v1 원본을 백업하고 narration을 utterance로 변환합니다. 화면 연결의 의미까지 자동 검증하지 않으므로 `needs_visual_review`를 실제 검토 후 해제합니다.

`build`와 `resume`은 이전 생성물의 수동 수정을 감지하면 멈춥니다. 유지할 수정이라면 check 경로를 쓰고, 다시 생성하려면 `--regenerate`를 사용합니다. 이때 자동 백업 경로가 출력됩니다.

원본 입력 이미지를 교체하면 `check`가 `E_INPUTS_CHANGED`로 멈춥니다. `resume` 또는 `build --timed`로 재생성하고 프레임·렌더·청취 검수를 다시 진행합니다.

주요 파일: inventory.json(파일 목록), audio/(음성 캐시), timeline.json, captions.srt, deck/, video/, qa/, state.json, timings.jsonl. 명령 소요 시간에는 별도의 학생 생각·수정 대기 시간을 추가해 수업 시간을 측정합니다.

### 문장별 본문 강조

비데모 장면의 utterance에 선택 필드 `emphasis_target: 1`을 넣으면 해당 발화에서 첫 번째 본문 항목을 강조합니다. 1부터 시작하며 compare는 기존/개선/보충 문장, flow는 단계, evidence는 표의 행, problem/closing은 핵심 항목 순서입니다. 발화의 실제 의미와 항목이 일치할 때만 지정합니다. 생략하면 모두 같은 명도로 표시합니다. 단순 발화 순번으로 자동 연결하지 않습니다. 데모는 states/beats를 사용합니다.

온라인 음성의 문장 경계가 최대 100ms 겹치면 자막 끝을 다음 시작까지 줄여 표시 중첩만 제거합니다. 음성을 자르지 않으며 더 큰 경계 겹침은 오류로 중단합니다.
