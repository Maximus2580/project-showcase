# v2 참고와 배포 고지

조사일: 2026-11-20~21. 링크의 최신 내용과 고정한 배포판이 다를 수 있다. 실제 설치 버전으로 검증한다.

- HyperFrames 공식: https://github.com/heygen-com/hyperframes (Apache-2.0)
- 제작 spec: https://github.com/heygen-com/hyperframes/blob/main/skills/hyperframes/references/spec.md
- storyboard: https://github.com/heygen-com/hyperframes/blob/main/skills/hyperframes/references/storyboard-format.md
- review: https://github.com/heygen-com/hyperframes/blob/main/skills/hyperframes/references/review.md
- composition 계약: https://github.com/heygen-com/hyperframes/blob/main/skills/hyperframes/references/format.md
- edge-tts: https://github.com/rany2/edge-tts (LGPLv3, srt_composer.py는 MIT). 코드 복제 없이 고정 버전을 의존성으로 설치한다. 온라인 서비스 연결과 로컬 렌더는 별개다.
- frontend-slides: https://github.com/zarazhangrui/frontend-slides (참고 사례, 소스 복제 없음)
- HeyGen 제작 사례: https://x.com/HeyGen/status/2044827454460871072
- 발표 슬라이드 제작 사례: https://x.com/zarazhangrui/status/2025847511613919488
- 한국어 비교 사례: https://www.threads.com/@imusiro/post/DfbJiotI_dZ

위 소셜 사례는 작성자의 제작 진술이며 이 패키지의 실행 시간 또는 품질 보증이 아니다.

사용자의 로컬 html-slide는 1920×1080 덱, 한글 폰트, 스크린샷 검증 구조를 참고했다. 기존 소스는 수정하지 않았다. 배포용 HTML/Python/JS는 새로 작성했다. PretendardVariable.woff2는 동봉한 SIL Open Font License를 유지한다. GSAP·HyperFrames·Playwright는 npm 의존성으로 설치하며 해당 패키지 고지를 유지한다. 배포 ZIP에는 node_modules와 계정 정보가 들어가지 않는다.


v2 기능의 근거는 현재 패키지 소스와 검증 기록이다. 위 외부 사례 또는 v1 실행 수치로 v2 품질·시간·Windows 지원을 입증하지 않는다.

Project Showcase의 직접 작성한 코드·문서는 저장소 루트의 MIT LICENSE를 따른다. Pretendard 및 npm/Python 의존성의 라이선스는 각각 유지하며, Project Showcase의 MIT 라이선스로 대체하지 않는다.
