# 검증 기록

검증일: 2026-10-31 (KST). 실제 로컬 실행과 독립 검토를 기록한다.
Python 3.9.6, Node 24.19.0, Playwright 1.64.1 및 Chromium 환경이다.
이 결과는 실제 대회 환경이나 모든 후보 MCP의 동작을 보장하지 않는다.

## 통합 실행

```bash
python3 scripts/verify.py --manifest verification.json
```

core/browser 모든 profile을 선택해 **13개 검사 명령 PASS**를 확인했다.
총 **Python 115개 + 실제 브라우저 5개 = 120개 검사 PASS**, skip 없음.
core 40개, 분석 예제 46개, 웹/API/RAG/디버깅 Python 29개다.
run 시작/끝 source fingerprint는 같았다. 최종 배포 전 문서 갱신 후에도
동일 명령과 아래 final-check로 현재 소스와 증거를 맞춘다.

```bash
python3 scripts/final-check.py --manifest verification.json --report .harness/runs/RUN_ID/report.json
```

`RUN_ID`는 방금 실행이 출력한 실제 ID로 바꾼다. core만 실행한 report로 전체
준비 완료를 선언하면 browser 누락으로 BLOCKED가 되어야 한다.
로컬 `.harness/runs/<run_id>/`에 report, events, metrics, trace, 명령별 stdout/stderr가
남는다. 실행 로그에는 로컬 경로 등이 포함되므로 공개 Git에는 포함하지 않는다.

## 실제 산출물 확인

- 웹: 메인이 새 합성 CSV X=2/4, Y=8/16을 실제 Chromium에서 업로드했다.
  50.00%, 2행을 확인하고 화면을 직접 보았다. E2 필터 후 1행, 다운로드 CSV의
  Y,E2,8,16을 읽었고 X 행이 없는지 확인했다. page error 0개.
- 브라우저 회귀 5개: 업로드/기간/다운로드, 설비/빈 결과, 무효 수량,
  늦은 이전 응답, 파일 교체 후 설비 초기화. HTTP 응답을 가짜 정답으로 바꾸지 않았다.
- 분석 예제: 데이터/SQL/이미지/ML의 실제 내부 span, 실패 traceback, parent 관계를
  검사한다. 이미지 담당자는 PGM→SVG 결과를 렌더링해 비정사각형 좌표 정렬을 확인했다.
- 작은 합성 데이터의 정답을 실제 산업 예측 성능이나 대규모 운영 보장으로 표현하지 않는다.

## 새 프로젝트 설치 리허설

메인이 별도 임시 기존 프로젝트에 실제 kit를 설치했다.

- dry-run에서 `.harness`가 생성되지 않았다.
- 기존 `AGENTS.md`, `.codex/config.toml` 바이트를 보존했다.
- 7개 스킬, 2개 역할, namespaced kit 및 MCP 설정 fragment가 설치됐다.
- 두 번째 설치의 모든 파일이 unchanged였다.
- 설치된 skill 로컬 링크 26개가 실제 경로에 연결됐다.
- 복사된 kit 안에서 core 검증 12개 명령이 PASS였다. browser는 명시적으로 NOT RUN.

공식 skill-creator 검증기에서 7개 스킬 frontmatter PASS, 2개 agent와 3개 MCP
TOML 파싱 성공, 전체 Markdown 상대 링크 누락 0개를 확인했다.
실제 Codex CLI 자동 discovery를 모든 버전에서 인증한 결과는 아니다.

## 독립 검토와 수정

- [계획 대응](reviews/plan-coverage-review.md): R01–R14와 실제 파일·검사 대응.
- [실행 코어·앱](reviews/runtime-review.md): 구현자가 아닌 검토자가 5건의 반례를
  발견했다. null 인용, 문서 버전 충돌 순서, 실행 권한 freshness, 손상된 evidence,
  파일 교체 후 이전 설비 필터를 모두 수정하고 원래 반례로 재검증했다. 최종 APPROVE.
- [행동 리허설](reviews/behavior-review.md): 불명확한 새 과제, 0개/오래된 증거,
  행위 주체가 다른 recap의 세 가상 상황을 실제 에이전트 응답으로 평가했다.
  제품 실행이나 인간 확인을 대체하는 검사는 아니다.

행동 리허설의 P3 제안 중 시간 부족 시 간결한 계획과 좁은 recap 응답을 스킬에
명시했다. 0개 검사는 runner의 실제 BLOCKED 표기를 유지하고 제품 자체는 NOT RUN임을
명확히 했다. 리허설 원문은 변경 전 관찰 기록으로 보존했다.

## 공개 전 확인과 남은 경계

tracked 후보에서 원본 안내문/개인 프로젝트 자료, 비밀 키, 개인 절대 경로,
runtime 로그, node_modules가 포함되지 않았는지 검사한다. 공개 여부와 원격 commit은
GitHub 생성/push 뒤 원격 상태로 별도 확인한다. 이 문서는 공개 직전의 로컬 증거 기록이다.

Playwright Test 외 후보 CLI/MCP는 공식 문서/registry 확인 상태다. 네이티브 모바일은
기기 조건·선택 도구·검증 recipe를 제공하며 실제 앱/기기 E2E를 실행하지 않았다.
사용자의 직접 조작 확인은 아직 별도 상태이며 에이전트 실행을 사용자 경험으로 기록하지 않는다.
