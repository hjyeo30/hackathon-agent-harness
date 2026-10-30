# 도구 카탈로그와 선택 기준

확인일: 2026-10-31. 공식 저장소/문서와 npm registry를 읽은 후보 목록입니다.
개별 도구의 로컬 실행 상태는 [검증 기록](../validation.md)을 보세요.
이 표 자체는 설치·브라우저 실행·대회 허용 확인을 의미하지 않습니다.

## 빠른 선택

| 필요한 관측/조작 | 우선 경로 | 도입하지 않아도 되는 경우 |
|---|---|---|
| 웹 사용자 흐름 | 기존 브라우저 도구 또는 Playwright CLI/MCP 하나 | API/배치만 있는 과제 |
| 반복 웹 회귀 | Playwright Test | 한 번의 단순 수동 확인이면 충분 |
| 네트워크/렌더링/메모리 원인 | Chrome DevTools MCP/CLI | 실제 병목 증거 없음 |
| Python 입력 공간 | Hypothesis | 작은 고정 oracle로 충분 |
| JS/TS 입력 공간 | fast-check | 불변조건을 설명할 수 없음 |
| API schema 경계 | Schemathesis | API 몇 개를 직접 검사하는 편이 간단 |
| 네이티브 모바일 | Maestro + 실행 가능한 기기 | 에뮬레이터/기기가 없음 |
| 대화형 터미널 | Pexpect | 일반 subprocess로 충분 |
| MCP 연결/도구 진단 | MCP Inspector | MCP를 이미 정상 사용 중 |

공식 CLI/MCP가 있으면 직접 다시 만들지 않습니다. 모든 도구를 한번에 설치하거나
모든 MCP schema를 메인 컨텍스트에 로드하지 않습니다. 도구는 관찰 수단이며
업무 정답을 대신 정하지 않습니다.

## 확인한 후보

| 도구 | 저장소 | 확인한 배포 버전 | 관찰 결과 |
|---|---|---|---|
| Playwright Test | [microsoft/playwright](https://github.com/microsoft/playwright) | 1.64.1, Node >=20 | assertion, 사용자 동작, report, 선택형 trace |
| Playwright CLI | [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli) | 0.1.22, Node >=18 | snapshot, click/fill, console/network, script |
| Playwright MCP | [microsoft/playwright-mcp](https://github.com/microsoft/playwright-mcp) | 0.0.83, Node >=18 | 접근성 tree와 브라우저 동작 |
| Chrome DevTools | [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) | 1.12.0, 해당 package engines 확인 | console/network/performance/memory 진단 |
| agent-browser | [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) | 0.41.0 | snapshot refs, CLI browser 동작 |
| Hypothesis | [HypothesisWorks/hypothesis](https://github.com/HypothesisWorks/hypothesis) | 미고정, 선택 시 설치 버전 검증 | 반례 생성·축소·재현 |
| fast-check | [dubzzz/fast-check](https://github.com/dubzzz/fast-check) | 미고정, 선택 시 설치 버전 검증 | TS/JS property·state model 검사 |
| Schemathesis | [schemathesis/schemathesis](https://github.com/schemathesis/schemathesis) | 미고정, 선택 시 설치 버전 검증 | OpenAPI/GraphQL 경계·stateful 검사 |
| Maestro | [mobile-dev-inc/Maestro](https://github.com/mobile-dev-inc/Maestro) | 미고정, 대상 환경에서 검증 | 실제 기기/시뮬레이터 UI 흐름 |
| Pexpect | [pexpect/pexpect](https://github.com/pexpect/pexpect) | 미고정, 선택 시 설치 버전 검증 | PTY 입출력·EOF·timeout |
| MCP Inspector | [modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector) | 2.13.0, Node >=22.19 | MCP tools/list/call과 연결 진단 |

Chrome DevTools 1.12.0 engines: `^20.19.0 || ^22.12.0 || >=23`.
agent-browser npm 0.41.0 engines에는 Node >=24, pnpm >=11이 기재되어 있으나
native binary 경로와 source build 요건은 다릅니다. 설치 방식에 맞는 README를 확인하세요.
브라우저 바이너리와 Linux 시스템 라이브러리는 Node와 별도 전제입니다.
Inspector는 MCP **client**이므로 Codex의 MCP server 목록에 등록하지 않습니다.

## 각 후보의 도입 조건과 확인 절차

### Playwright CLI / MCP / Test

CLI는 간결한 명령으로 탐색하기 좋고 MCP는 대화 중 구조화된 상태를 반복 읽기에
편리합니다. Test는 결정적인 반복 assertion을 남깁니다. 처음 두 개 중 하나를
선택하고 유용한 성공 경로를 Test로 고정하세요. [브라우저 레시피](browser.md).

### Chrome DevTools

구체적인 느린 렌더링·요청 실패·메모리 증가를 조사할 때 사용합니다.
처음에는 사용자 입력→문제 요청→서버 결과→화면 상태의 경로를 좁힙니다.
성능 개선은 같은 입력, 실행 조건, 정답 보존을 확인한 뒤 전후 측정합니다.
툴을 연결했다는 이유만으로 성능 검사 완료라고 표시하지 않습니다.
공식 bundled skills 중 cookie-debugging, memory-leak-debugging 등 필요한 것만
읽습니다. 도구 버전과 skill 버전을 함께 맞춥니다.

### agent-browser

별도 CLI 대안입니다. snapshot으로 얻은 현재 ref를 사용하고 페이지가 바뀌면
다시 읽습니다. 이전 상태의 ref를 계속 클릭하지 않습니다.
기존 Playwright 경로가 정상이라면 추가 도입할 이유를 먼저 설명하세요.
제공된 코딩 에이전트에서 CLI를 호출하며 별도의 외부 AI chat 기능을 요구하지 않습니다.

### Hypothesis / fast-check

먼저 성립 범위를 정의합니다. 순서 무관 집계에는 permutation invariance가 맞지만
시계열 상태 기계에는 그대로 적용되지 않습니다. 입력 생성기는 유효 입력과 무효
입력을 구분하고 경계 분포를 고려합니다. 발견된 반례와 seed/replay 정보를 보존합니다.
동일한 구현 로직을 expected 계산에 복사하지 않습니다. [API/속성 검사](api-and-properties.md).

### Schemathesis

스키마가 실제 약속과 맞는지 먼저 읽습니다. 스키마 자체가 틀리면 생성 검사가
잘못된 기대를 반복합니다. 로컬 테스트 API와 격리된 데이터에서 실행하고 쓰기
연산의 영향을 확인합니다. schema validation은 업무 계산 정답 검사를 대체하지 않습니다.

### Maestro / Pexpect

실제 device/PTY 상태와 side effect를 확인합니다. 모바일 웹 성공을 네이티브 기능
성공으로 표현하지 않습니다. CLI는 문구뿐 아니라 exit code·파일 상태·취소 후
잔여 프로세스를 봅니다. [모바일/터미널 레시피](mobile-and-terminal.md).

### MCP Inspector

연결 실패가 MCP protocol인지 대상 앱인지 분리할 때 사용합니다. transport→initialize
→tool 목록→작은 정상 call→무효 입력 순으로 확인합니다. 버전 2는 v1과 CLI가
달라 오래된 명령을 그대로 실행하지 않습니다. [MCP 연결 레시피](mcp.md).

## 도구 카드 작성 형식

추가 도구는 목적, 적용/비적용 조건, upstream URL, 확인일/버전, runtime,
install/start/health/drive/observe/cleanup, 외부 통신, 실패 경로, 실제 확인 상태를
한 카드에 적습니다. 도구는 오류를 감추는 자동 fallback 체인으로 연결하지 않습니다.
