# 계획 대비 독립 검토

검토일: 2026-10-31. 검토자: 제작 담당과 분리된 coverage review agent.
기준: 원 요청의 협업·검증·관측·재사용 요구와 `docs/implementation-plan.md` R01–R14.
제품 코드는 수정하지 않았다. 이 문서는 검토 시점의 범위와 증거를 기록하며
최종 공개·최종 통합 실행의 성공을 미리 선언하지 않는다.

## 판정

**검토한 구현·문서의 요구사항 대응은 적절하다.** 확인된 필수 수정 결함은 없다.
최종 통합 브라우저 실행, cold-start 행동 리허설, 공개 전 검사와 GitHub push는
별도 완료 증거가 필요하다. 그 결과는 `../validation.md`와 진행 기록으로 확인한다.
작성 중이던 Python/TypeScript 문서는 완료 후 다시 읽고 상대 링크도 확인했다.

## 요구사항 대응

| ID | 확인한 구현·문서 | 독립 확인과 한계 |
|---|---|---|
| R01 | `START_HERE.md`, hackathon-start, first-prompt guide, bootstrap, `tests/test_bootstrap.py` | 기존 지침/코드 우선, dry-run/apply, 충돌 거절, 설치 멱등성·링크·symlink 검사 존재. 실제 클라이언트의 skill 발견은 설치 후 확인하도록 명시함. |
| R02 | frame-and-plan, domain-discovery, 계획 템플릿, 분야별 참고 | 사실/가정/사용자 결정 분리, 사용자 소유의 의미와 직접 조사할 기술 사실 분리. 모든 전문 고려를 의무 구현으로 확대하지 않음. |
| R03 | `AGENTS.md`, 두 custom-agent TOML, workflow, handoff/checkpoint | 메인 직접 사용, 독립 검토, 묶음별 사용자 확인, 이미 승인한 batch 존중이 일관됨. 역할 read-only를 OS 격리로 표현하지 않음. |
| R04 | `src/harness/evidence.py`, observability/debugging, failure template, 4개 분석 observe.py, 웹 request spans | 분석 observe 검사의 실제 실패 span·traceback 검사가 통과함. 단순 단계 목록은 `stage_summary`로 표시하여 계측 trace와 구별. 전체 분산 관측을 제공한다고 주장하지 않음. |
| R05 | testing guide, 각 manifest reason/oracle, fixtures/faults/tests | 테스트 범위·목적·판정·입력 전략을 구별. 아래의 72개 예제 검사 통과. 손계산과 명시적 계약이 존재하며 모든 입력을 랜덤에 맡기지 않음. |
| R06 | doctor/verify/final-check, `tests/test_runtime.py` | timeout, 0개, skip, 누락 profile, stale evidence, 필수 로그 손실 등에 대한 검사 존재. 세부 실행 코어 반례는 별도 runtime review 범위. |
| R07 | `examples/README.md`의 11개 예제 | 각 예제가 실행 가능한 source/tests/manifest와 정답 설명을 가짐. API는 SQLite 서비스 계층, RAG는 로컬 검색·추출 기준선으로 범위를 정직하게 제한함. |
| R08 | 웹 실제 HTML/server, Playwright 4개 검사, verification-notes | 업로드→계산→기간/설비 필터→다운로드 내용, 오류 상태, 늦은 응답 회귀를 검사함. 이 검토자는 브라우저를 직접 구동하지 않았으므로 최종 E2E 결과는 메인의 통합 증거 필요. |
| R09 | tools/catalog, browser/mcp/API/mobile recipes, `configs/mcp/` | upstream, 확인 버전, 전제, 도입/비도입 기준, 통신과 실행 상태 구별. Inspector를 server로 설치하지 않으며 선택형 설정으로 기존 config 보존. 후보 전체 설치 성공 주장은 없음. |
| R10 | recap skill/guide/template, 웹 recap 사례 | 예상 질문이 실제 작업 근거에서 나옴. 인간 직접 행동·agent 실행·보고서 열람을 구분하고 기록 없는 1인칭 경험을 만들지 않음. 실제 출제 문항이라고 주장하지 않음. |
| R11 | issues, progress/failure/handoff/review 템플릿, workflow | 최초 계획 보존, 변경 근거·원인 분석·재개 상태·미검증 표시에 적합한 공간이 있음. 실제 문제 기록을 공개 GitHub Issues에 자동 전송하지 않음. |
| R12 | MIT LICENSE, sources, ignore, exam-environment | 원문 문서/개인 저장소를 배포물이라고 삼지 않음. 실제 tracked 파일 검사와 공개 remote/pushed commit 확인은 출판 담당 메인의 완료 작업. |
| R13 | 본 검토, 별도 runtime review, behavioral-evals | 요구사항 매핑과 실제 예제 실행을 독립 확인함. 행동 평가 설계만으로 리허설 성공을 주장하지 않음. cold-start 실험의 결과 문서가 추가로 필요. |
| R14 | large-data/domain discovery, 규모 예제, Python/TypeScript 참고 | N/2N, cardinality, chunk 결합, 중간 메모리, 자료구조 판단을 제공. tracemalloc을 RSS로 부르지 않음. Python 입력/수치/프로세스와 TS 외부 입력/숫자/비동기 경계를 확인함. |

## 실제 실행한 확인

각 예제 디렉터리에서 다음 명령을 별도의 subprocess로 실행했다.

```bash
python3 -m unittest discover -s tests -v
```

| 예제 | 검사 수 | 결과 |
|---|---:|---|
| api-idempotency | 6 | PASS |
| data-weighted-yield | 9 | PASS |
| existing-project-debugging | 5 | PASS |
| image-components | 7 | PASS |
| large-data | 6 | PASS |
| ml-leakage | 6 | PASS |
| rag-grounding | 7 | PASS |
| scheduling-constraints | 6 | PASS |
| sql-join-duplication | 6 | PASS |
| timeseries-anomalies | 6 | PASS |
| web-filter-export Python | 8 | PASS |

총 72개, 모든 subprocess exit 0. 이는 에이전트가 실행한 결과이며 사용자 직접
확인이나 실제 대회 환경 실행을 뜻하지 않는다.

검사 코드도 읽어 정답 근거를 확인했다. 예를 들어 이미지의 비정사각형 픽셀 좌표,
스케줄 J2 3시간 뒤 J3 1시간의 makespan 하한 4, SQL 원자료 합계 150,
수율 10/100, 스트리밍 불균등 chunk 평균 반례는 구현 출력의 단순 복사가 아니다.
웹 다운로드 검사는 화면 문구만 보지 않고 받은 CSV의 행과 값을 읽는다.
ML 합성 holdout의 100% 결과가 산업 예측 성능의 증거라고 표시되지 않은 것도 확인했다.

runtime/dependency 디렉터리를 제외한 저장소 Markdown의 상대 링크를 실제 경로와
대조했고 누락된 대상은 0개였다. 웹 외부 링크의 도달성과 anchor ID까지 검사한 것은 아니다.

## 범위와 완료 시 주의점

- 네이티브 모바일은 device 전제와 Maestro 사용법을 제공하는 참고 경로다.
  이 kit에 네이티브 앱·기기 E2E가 구현/실행되어 있다고 표현하면 안 된다.
- tool catalogue는 조사된 후보 목록이다. 모든 MCP의 실제 연결 검증과 구분한다.
- 상시 지침은 짧고 세부 분야는 선택해서 읽는다. 참고 자료 수를 실제 과제의
  의무 체크리스트나 일괄 설치 목록으로 바꾸지 않는다.
- source fingerprint는 내부 파일의 신선도 증거이며 외부 데이터·실행 중인 서버의
  동일성을 저절로 보장하지 않는다. 실제 과제 입력/인스턴스 식별은 별도로 남긴다.
- 행동 리허설, 최종 브라우저 통합, 공개의 완료 여부는 최종
  validation/progress에서 실제 결과를 확인한다. 검토자가 보지 않은 성공을 이 문서에
  소급해서 꾸며 넣지 않는다.
