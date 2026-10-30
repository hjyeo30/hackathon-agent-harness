# 구현 진행 기록

기준선: [implementation-plan.md](implementation-plan.md). 2026-10-31.
사용자가 전체 구현·독립 검토·수정·공개를 승인한 작업이다.

## 계획과 책임 분리 — completed

R01–R14와 완료 증거를 먼저 작성하고 메인, 실행 코어, 스킬/문서, 분석 예제,
앱/상태 예제로 구현 소유권을 나눴다. 별도의 runtime/계획/행동 검토자를 사용했다.
Python 기반은 현재 환경과 호환되는 표준 라이브러리 3.9+로 구체화했다.

## 구현 — completed

- 7개 스킬, 2개 custom-agent 역할, 8개 기록 템플릿과 로컬 issues 공간.
- 10개 운영 가이드, 10개 분야 참고와 색인, Python/TypeScript 판단 가이드.
- 11개 실행 예제: 웹, 데이터, SQL, 이미지, API 멱등성, ML 누수, 일정 제약,
  RAG 근거, 시계열 이상, 기존 코드 디버깅, 스트리밍 집계.
- doctor/verify/final-check/bootstrap, schema 검증, argv 실행, timeout 정리,
  로컬 로그·단위 메트릭·부모/자식 트레이스와 실패 증거.
- 조사한 GitHub 도구 11종과 선택형 MCP 설정 3개. 전체 후보 실행 성공으로 표시하지 않는다.

## 구현 중 발견과 대응

- runtime `.runs/` 출력이 source hash를 바꾸지 않도록 캐시 경계와 ignore를 일치시켰다.
- 단계 이름만 나열한 요약은 `stage_summary`라 부르고, 분석 observe 스크립트에는
  실제 시작/종료/부모 관계/예외를 측정하는 Evidence를 연결했다.
- 최초 웹 검사에서 select 접근성 이름 문제를 발견했다. 테스트를 약화하지 않고
  UI의 이름을 명시하고 실패 검사와 영향받는 전체 흐름을 재검증했다.
- main 설치 검토에서 configs payload 누락을 발견해 MCP fragment 복사를 추가했다.

## 독립 검토 — completed

[runtime review](reviews/runtime-review.md)의 5건 모두 원래 반례로 수정 확인했다.
RAG null/미등록 인용, 상충 버전 입력 순서, 실행 권한 변경, 파손된 trace,
CSV 교체 후 숨은 이전 설비 필터가 대상이다. 필수 수정 미해결 없음.

[계획 대응](reviews/plan-coverage-review.md)은 R01–R14를 실제 파일과 대조했다.
[행동 리허설](reviews/behavior-review.md)은 계획·거짓 PASS·recap 귀속의 3상황을
별도 에이전트가 수행했다. 세 P3 제안은 시간 예산에 맞춘 계획 간소화, 좁은 recap,
0개 검사의 BLOCKED/제품 NOT RUN 구분으로 반영했다. 원래 review는 보존했다.

## 통합과 직접 사용 — completed

모든 13개 검사 명령, Python 115개와 브라우저 5개가 통과했다.
메인은 별도 입력의 실제 웹 업로드→50% 확인→E2 필터→CSV 내용 확인과 화면 검토를 했다.
별도 기존 프로젝트 설치 후 지침/설정 보존, 재설치, 참고 링크, 복사된 core 실행을 확인했다.
공식 스킬 검증, TOML 파싱, 전체 상대 링크를 확인했다. 세부 증거는
[validation](validation.md)에 기록했다.

## 공개 준비

원본 자료·개인 경로·비밀·runtime 산출물을 제외하고 MIT 원본 저작물만 배포한다.
공개 대상은 `hjyeo30/hackathon-agent-harness`다. 최종 commit과 GitHub 원격 일치는
push 후 확인한다. 실제 대회 문제/답안은 이 준비 저장소에 push하지 않는다.
사용자 직접 조작 확인은 이번 에이전트 검증과 별개의 후속 단계다.
