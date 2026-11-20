# 실행 불가 fixture

이 폴더에는 애플리케이션 진입점과 실행 의존성이 없습니다. 실행할 수 없는 프로젝트를 분석한 상황을 재현하기 위한 입력입니다. 동작 여부는 unverified이며, 실행 화면이나 효과를 만들지 마세요.

데모 장면에는 `unavailable_reason: "진입점과 실행 의존성이 없어 실행 화면을 확보하지 못했습니다."`, `verification: "unverified"`를 사용하고 media/states/beats를 비웁니다. 결과에는 '실행 화면 미확보'가 표시되어야 합니다. 이 폴더의 `project.json`은 짧은 sample 검증 입력이며 완성 3분 예제가 아닙니다.
