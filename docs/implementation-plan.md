# 구현 계획 — 해커톤 Agent Harness

상태: 사용자 승인 범위의 구현 기준선 · 2026-10-31

## 목적과 승인 범위

공개 준비 저장소를 만들어 처음 보는 실무 과제를 사용자와 계획하고,
별도 구현자·검토자와 해결하며, 실제 산출물을 조작·관찰·검증하고 설명한다.
사용자는 이번 저장소의 전체 제작, 독립 subagent 검토, 수정, GitHub 공개를
명시적으로 승인했다. 이번 제작의 각 내부 작업마다 재승인을 요구하지 않는다.
저장소를 사용하는 미래 과제에서는 기능 묶음별 사용자 확인을 기본으로 한다.
사용자가 전체 범위를 명시적으로 일괄 승인했다면 그 범위의 권한을 존중한다.

이 문서는 원래 결정 기준선이다. 구현 발견·변경·실측 검증은
`implementation-progress.md`에 기록하고 완료한 것처럼 기준선을 고쳐 쓰지 않는다.

## 확인된 환경과 경계

- 사용자 확인: 실제 환경에서 Codex CLI, subagent, Browser, MCP 사용 가능.
- 개별 버전·패키지·브라우저 자동 캡처 허용은 별도 조건이다.
- 대회용 준비: 과제 180분, 공개 자료 반입 가능, 실제 문제·답안 외부 전송 금지.
- 실제 문제·가이드 원본·개인 원격 저장소 자료를 공개 레포에 포함하지 않는다.
- 후속 서술형에서는 AI 사용 금지. recap은 그 단계 진입 전 학습용이다.
- Python 핵심 도구·예제는 3.9+ 표준 라이브러리로 동작하게 만든다.
- 웹 브라우저 검증은 별도 Node/Playwright 의존성을 사용하며 실행 여부를 분리한다.
- 한국어 설명과 영어 코드·식별자를 사용한다. 특정 모델 이름을 강제하지 않는다.

## 요구사항과 수용 기준

| ID | 요구사항 | 수용 증거 |
|---|---|---|
| R01 | 첫 프롬프트로 새/기존 과제에 적응 | START_HERE, 설치 리허설, 기존 파일 보존·재실행 검사 |
| R02 | 사용자 의도·필수조건·도메인 공백을 근거 있게 계획 | 계획 skill, 분야별 결정 질문, 계획 템플릿 |
| R03 | 메인/구현자/독립 검토자, 자연스러운 기능 묶음과 사용자 확인 | AGENTS, custom agents, 인계·체크포인트 사례 |
| R04 | 상황별 로그·메트릭·트레이스·원인 분석 기록 | 실행 evidence bundle, 실제 실패와 성공 기록, 관측 가이드 |
| R05 | 필요한 테스트·입력·정답·회귀·재검증 분배 | 테스트 선택 문서, 각 예제의 실패 가설·oracle·회귀 검사 |
| R06 | 반복 작업 스크립트, 실패/미실행을 성공으로 위장하지 않음 | doctor/verify/final-check, exit code·timeout·0개검사 테스트 |
| R07 | 다양한 실제 실행 예제와 고의 결함 | 데이터/SQL/이미지/API/ML/일정/RAG/시계열/디버깅/대용량 예제 |
| R08 | 웹을 AI가 실제 조작·관찰하고 결과 검증 | 로컬 웹+CSV 앱, Playwright E2E, 직접 브라우저 확인 |
| R09 | 공개 GitHub 도구·MCP 사용법과 조건 | 도구 카탈로그, 선택형 설정, 상태·버전·외부 통신 구분 |
| R10 | 실제 기록 기반 recap과 예상 질문 | recap skill·템플릿·가상 사례, 인간/AI 행위 구분 |
| R11 | 중단·재개·진행·판단 기록 | issues 공간, 인계 템플릿, 실패 재현 기록 |
| R12 | 공개 가능한 원본 저작물과 검토 기록 | 라이선스, 출처, 공개 전 diff 검사, 원격 URL |
| R13 | 계획 대비 독립 검토 및 행동 검증 | review 문서, 누락 수정, cold-start skill 리허설 |
| R14 | 알고리즘·자료구조·메모리·시간·언어 고려 | Python/TS/scale 참고, 계측 가능한 규모 예제 |

## 설계 결정

### 작은 공통 규칙과 선택형 지식

AGENTS는 협업·판정·증거·사용자 인계만 규정한다. 7개 공통 스킬
`hackathon-start`, `frame-and-plan`, `implement-chunk`, `review-and-challenge`,
`verify-result`, `diagnose-failure`, `recap`은 필요할 때 참고 자료를 읽는다.
도메인/언어 참고 문서는 풍부하게 제공하되 전부 읽게 하지 않는다.
계획에서 중요한 공백을 발견하면 관찰·공식 자료·작은 측정으로 먼저 해결하고,
업무 의미·우선순위·범위 결정은 사용자에게 추천안과 함께 질문한다.

### 역할과 실행 소유권

메인은 계획·위임·통합·직접 사용·대화를 소유한다. 구현자는 맡은 제품 코드를
변경하고 검증한다. 검토자는 요구사항·계획·실행을 독립 비교하며 제품 소스를
고치지 않는다. 읽기 전용 역할 지침을 OS 권한 격리라고 설명하지 않는다.
부모 Codex의 권한·MCP를 상속하고, 단일 서버·탭은 한 명만 조작한다.
기본 subagent는 두 역할이고 재귀 위임·상시 swarm·다중 모델 심사는 넣지 않는다.

### 도구와 관측

로그는 사건/오류, 메트릭은 양·시간·자원, 트레이스는 단계 인과관계다.
로컬 JSON/JSONL과 텍스트 로그로 시작하고 외부 관측 서버를 요구하지 않는다.
run_id, span_id/parent_id, stage, duration, status, error_type 및 단위가 있는
메트릭을 사용한다. 명령·입력 ID·코드 상태·기대/관찰·원인 가설을 연결한다.
필요한 경우에만 CPU/RAM/행 수/요청/브라우저 관측을 추가한다.
원문 데이터·환경 비밀·토큰을 무차별 덤프하지 않는다.
실행 명령을 문자열 shell 평가하지 않고 argv로 실행한다.
필수 검사 실패·시간 초과·도구 불가·0개 검사는 전체 PASS가 될 수 없다.

### 검증 원칙

검사마다 요구사항, 잡을 결함, 입력 선정 이유, 독립 oracle을 명시한다.
단위/통합/E2E는 계층, 회귀는 목적, golden/invariant/metamorphic는 판정 방법,
경계값/속성생성/오류주입은 입력 전략으로 구분한다.
기능 추가는 핵심 성공 흐름과 실제 위험 경계, 버그는 최소 재현 회귀,
리팩터는 기존 동작 유지, 성능은 같은 입력·정답 보존·전후 실측을 우선한다.
같은 결과를 다시 얻으려고 전체 테스트를 무작정 반복하지 않는다.
고의 결함은 격리된 테스트용 변형으로 관리하고 실제 코드에 숨은 fallback을 넣지 않는다.

### 재사용과 공개

소스는 직접 작성한다. 외부 자료에서 아이디어를 참고하고 출처·라이선스 경계를 적는다.
부트스트랩은 기존 AGENTS/config를 덮어쓰지 않고 설치 파일을 이름공간으로 분리한다.
설치 계획을 먼저 보여주고, 명시적인 apply에서만 복사한다. 충돌은 중단하고 설명한다.
현재 프로젝트 전용 실행·조작·검증 절차는 실제 과제에서 발견한 명령으로 작성한다.
가상의 버튼/경로를 실제 프로젝트의 검증법인 것처럼 저장하지 않는다.

## 구현 작업 묶음과 소유 범위

1. 기준선/공개 루트: 메인 소유. 계획, README, START_HERE, AGENTS, 출처,
   도구 카탈로그, 선택형 MCP 설정, 통합·공개·최종 기록.
2. 하네스 실행 코어: 구현 agent. `src/harness/`, `scripts/`, `tests/`,
   Python 패키지 설정. 관측, command runner, verify, doctor, final-check,
   bootstrap과 독립 fixtures 테스트. 외부 agent 예제와 공통 인터페이스 합의.
3. 스킬/운영 문서: 구현 agent. `.agents/skills/`, `.codex/agents/`,
   `templates/`, `docs/guides/`, `docs/domains/`, `docs/languages/`, `issues/`.
4. 분석/알고리즘 예제: 구현 agent. data-weighted-yield, sql-join-duplication,
   image-components, ml-leakage, scheduling-constraints, timeseries-anomalies,
   large-data 예제와 각 tests/README/oracle/fault 설명.
5. 앱/상태 예제: 구현 agent. web-filter-export, api-idempotency,
   rag-grounding, existing-project-debugging 예제와 각 tests/README/fault.
   웹 실제 UI+API+다운로드 및 Playwright 검증 포함.
6. 독립 검토: 새 review agent가 R01~R14와 전체 구현을 대응시킨다.
   별도 agent가 처음 보는 가상 과제로 스킬 행동을 전향 검증한다.
7. 메인 통합: 모든 예제 실행, 브라우저 직접 조작, 기록/누락 수정,
   공개 전 파일 검토 후 gh로 public repository 생성·push.

## 공통 예제 인터페이스

- 각 예제는 `README.md`, `tests/`, 실제 source, 작은 합성 입력/oracle 설명을 둔다.
- Python 검사: 예제 디렉터리에서 `python3 -m unittest discover -s tests -v`.
- 예제마다 `verification.json`: schema_version=1, checks 배열.
- check 필드: id, requirement, kind, argv(list), cwd(해당 manifest 기준),
  timeout_seconds, required(bool), reason, oracle.
- stdout/stderr와 exit code를 runner가 저장하며 timeout을 구분한다.
- root `verification.json`은 root-relative cwd로 core와 각 예제를 연결한다.
- browser 검사는 별도 필수 profile로 명시하며 core의 성공을 browser 성공으로
  표현하지 않는다. 실제 browser 실행 결과를 최종 progress에 기록한다.
- 예제 코드는 machine path나 네트워크 서비스/개인 API 키를 필요로 하지 않는다.

## 검증 계획과 완료 판정

1. 코어의 실제 실패·타임아웃·누락·재실행·설치 충돌·보존 동작 테스트.
2. 모든 예제 정상 검사 및 알려진 결함을 잡는 oracle 검증.
3. 웹 브라우저의 업로드→계산→필터→다운로드, 오류 화면, 회귀 검사.
4. 스킬 frontmatter/참고 링크/명령이 완결되어 있는지 검사.
5. 신규/기존 임시 프로젝트에 설치 후 기존 파일이 보존되는지 리허설.
6. independent review에서 blocker 수정, 지적별 처리 결과 기록.
7. 행동 리허설에서 계획 없는 구현·가짜 PASS·사용자 행위 조작 여부 확인.
8. 민감정보·개인 경로·원본 문서·runtime 산출물 제외를 전체 tracked 파일로 검사.
9. GitHub public URL과 push된 commit 일치 확인.

모든 후보 MCP의 실제 설치·대회 환경 검증을 주장하지 않는다. 실제 실행되지 않은
도구는 문서 확인 상태로 표시한다. 실제 Codex CLI에서의 모든 모델 조합/서비스
권한 보장은 범위 밖이며, 로컬 리허설과 사용자 확인 환경을 구분한다.

## 위험과 대응

- 자료량이 컨텍스트를 잠식: 짧은 entrypoint와 분야별 선택 로딩.
- 설치가 과제 파일을 덮음: dry-run, 이름공간, 충돌 거절, idempotence 테스트.
- 검증이 구현과 같은 오해: 손계산 fixture, 변형 관계의 전제, 독립 reviewer.
- 코드 변경 후 오래된 증거 사용: run별 코드/입력 식별과 재검증 범위 기록.
- 하네스 비용이 구현을 압도: stdlib 기본, 도구 선택 설치, scoped verification.
- 조사/리뷰가 무한 반복: 새 증거 없는 수정 중단, 필수 결함과 deferred 구분.
- 사용자 설명이 사실과 불일치: recap의 evidence·행위 주체·미검증 구분.

## 참고 기준

- Codex skills/custom agents/AGENTS 공식 문서.
- pstack sharpen/create-verification-skill/maintain-verification-skill/decision trail.
- Anthropic long-running harness와 agent evals/tool design 문서.
- Playwright 공식 CLI/MCP/Test 문서와 도구별 공식 GitHub.
- 직접 재작성한 일반 원칙만 사용하며 개인 저장소의 원문은 공개하지 않는다.
