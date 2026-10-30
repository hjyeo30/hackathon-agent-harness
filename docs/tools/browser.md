# 브라우저: 탐색에서 반복 검증으로

## 먼저 구분할 것

Browser는 사람이 제공 미리보기를 사용하는 경로일 수 있습니다. 별도 Playwright
Chromium은 같은 서버를 보더라도 다른 브라우저 세션입니다. 로그인·쿠키·주소·빌드가
같다고 추정하지 마세요. 서버 소유자와 브라우저 driver를 한 명씩 정합니다.

## 설치와 작은 확인

아래는 문서 확인된 선택 명령입니다. 실제 실행 기록은 validation 문서를 봅니다.
설치가 허용되고 필요한 경우에만 수행합니다.

```bash
npm install --save-dev --save-exact @playwright/cli@0.1.22
npx playwright-cli --help
npx playwright-cli open http://127.0.0.1:8765
npx playwright-cli snapshot
```

ref는 snapshot의 현재 결과에서 읽습니다. 문서에 예제 `e3`를 고정해 재사용하지 않습니다.
한 입력을 넣고 누른 뒤 화면 값, 해당 요청, 서버 로그를 연결해 확인합니다.
MCP를 선택하면 `configs/mcp/playwright.toml`의 선택형 설정을 참조합니다.
처음부터 CLI와 MCP를 모두 설치할 필요는 없습니다.

## 사용자 경로와 정답

웹 예제의 정상 흐름은 CSV 입력→분석→설비/날짜 필터→화면 수치→다운로드입니다.
미리 준비한 작은 데이터의 손계산 값과 비교합니다. UI와 API가 같아도 둘 다
잘못될 수 있으므로 독립 oracle이 필요합니다.
저장 기능이면 새로고침·재조회나 DB의 read-only 확인으로 지속성을 봅니다.
E2E 중 내부 setter나 테스트 전용 API로 사용자 경로를 건너뛰지 않습니다.

## 관측과 원인 분리

| 현상 | 먼저 읽을 증거 | 다음 판단 |
|---|---|---|
| 서버에 연결 안 됨 | 실제 포트, process, ready log, HTTP health | 서버 미기동/주소/환경 |
| 클릭이 안 됨 | DOM snapshot, overlay, disabled/loading | UI 상태/locator |
| 요청이 없음 | click 결과, console exception | event 연결/클라이언트 오류 |
| 요청은 4xx/5xx | request_id와 서버 단계 log | 입력 계약/파싱/백엔드 |
| 200인데 숫자 틀림 | fixture, response, 계산 oracle | 계산 또는 데이터 정책 |
| API는 맞는데 UI 틀림 | 최신 요청 ID, DOM, render state | 표시/경쟁 응답 |
| 다운로드만 틀림 | 같은 필터, 파일 내용, row count | export 경로의 회귀 |

브라우저 console/pageerror, 요청/응답 상태와 duration, 서버 request_id를 연결합니다.
네트워크 body 전체·인증 쿠키를 무차별 기록하지 않습니다.

## 회귀로 남길 때

핵심 flow 한 개를 role/label/test-id 같은 안정적인 locator로 작성합니다.
임의 sleep 대신 관찰 가능한 상태와 응답을 기다립니다. API 오류를 주입한 UI 검사는
실제 서버 통합 검사가 아니라 오류 표시 검증이라고 적습니다.
실제 backend E2E에서는 결과 API를 가짜 정답으로 mock하지 않습니다.
재시도로 실패가 사라졌다면 flaky 증거를 숨기지 말고 원인을 조사합니다.

시각 증거는 허용 조건에 따라 수집합니다. screenshot은 한 시점이고 trace는
동작 순서·DOM·요청을 추적하는 자료입니다. 둘 다 업무 정답 자체가 아닙니다.
실행마다 모든 영상·trace를 켜기보다 실패 또는 중요한 사용자 흐름에 선택합니다.

## 정리

자신이 시작한 인스턴스/세션만 종료합니다. `killall node`나 공유 브라우저 전체 종료를
사용하지 않습니다. 테스트 데이터는 초기화하고 증거는 남깁니다.
정확한 자동 테스트 명령은 [웹 예제](../../examples/web-filter-export/README.md)에 있습니다.

출처: [Playwright best practices](https://playwright.dev/docs/best-practices),
[CLI](https://github.com/microsoft/playwright-cli),
[MCP](https://github.com/microsoft/playwright-mcp).
