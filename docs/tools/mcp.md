# MCP를 연결하고 실제 동작 확인하기

MCP는 도구 연결 방식입니다. 연결 성공, tool 목록 조회, 실제 작업 성공은 별개입니다.
이 kit는 임의의 MCP 서버를 새로 만드는 대신 검증된 도구를 선택해 사용합니다.

## 선택형 설정

`configs/mcp/*.toml`은 **설정 조각**입니다. 자동 설치하거나 기존 config를 덮어쓰지
않습니다. 현재 환경의 MCP 목록을 확인하고 중복되는 서버가 없을 때 필요한 조각만
부모 Codex 설정에 병합합니다. 프로젝트 설정의 trust와 지원 필드는 현재 버전에서
확인합니다. 서브에이전트 파일에 별도 MCP를 넣어 격리되는 것으로 가정하지 않습니다.

현재 공식 문서: [Codex 설정](https://learn.chatgpt.com/docs/config-file/config-reference),
[Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## 진단 순서

1. 실행 파일/버전과 transport(stdio 또는 HTTP)를 확인한다.
2. 서버 기동 로그와 protocol initialize를 확인한다.
3. tools/list가 반환하는 실제 도구 이름·입력 schema를 읽는다.
4. 로컬 합성 입력에 작은 read-only call을 실행한다.
5. 결과를 대상 앱/파일의 별도 관측과 대조한다.
6. 무효 입력 하나로 오류가 정상적으로 전파되는지 확인한다.

stdout을 JSON-RPC transport로 쓰는 stdio 서버라면 디버그 log는 stderr로 보내야 합니다.
MCP가 성공 응답을 돌려줘도 결과에 tool error가 있는지 확인합니다. 빈 응답을 정상
값으로 바꾸지 않습니다. schema drift·연결 timeout·브라우저 launch failure를 구분합니다.

Inspector는 서버가 아니라 진단 client입니다. 현재 v2 명령은 버전별 help로 확인합니다.

```bash
npx --yes @modelcontextprotocol/inspector@2.13.0 --cli --help
```

공식 README의 v1 예제와 v2를 섞지 않습니다. 개인 서비스 토큰이 필요한 후보는
대회에서 제공된 허용 경로가 없는 한 기본 구성에 포함하지 않습니다.

## 외부 통신과 선택 범위

Chrome DevTools의 사용 통계와 CrUX 요청은 README에 문서화되어 있습니다.
선택형 config에는 `--no-usage-statistics`, `--no-performance-crux`를 넣었습니다.
이 옵션만으로 모든 프로그램의 모든 외부 통신이 차단된다는 뜻은 아닙니다.
설치 시 package/browser 다운로드도 필요할 수 있으므로 작업 전 확인합니다.
문제·원자료·로그를 hosted debugger나 외부 observability 서비스에 보내지 않습니다.

문제 재현을 위해 플랫폼 관리 프로세스·보안 설정·감독 연결을 변경하지 않습니다.
연결할 수 없는 경우 evidence를 BLOCKED로 기록하고 필요한 공식 지원 경로를 사용합니다.
