# 모바일과 터미널을 직접 사용하기

## 모바일

먼저 모바일 웹/네이티브 구분, OS, 빌드 방식, 에뮬레이터·시뮬레이터·실기기,
설치·권한·외부 서비스 조건을 확인한다. 해당 기기가 없으면 네이티브 E2E는 BLOCKED다.
웹 viewport를 줄인 테스트를 네이티브 카메라·알림·백그라운드 검증으로 표현하지 않는다.

[Maestro MCP](https://docs.maestro.dev/get-started/maestro-mcp)는 CLI 설치와
실제 실행 가능한 대상 환경이 필요하다. `maestro mcp`가 연결돼도 앱 설치·launch·화면
읽기·실제 tap·결과 확인을 한 번 해야 동작 확인이다. 선택형 설정은 configs에 있다.

최소 flow 예시: 앱 launch→폼 입력→저장→화면 이동→재조회.
요구사항이 관련되면 권한 거절, 화면 회전, back, 앱 재시작, 네트워크 중단을 추가한다.
모든 경우를 무조건 테스트하지 않는다. 화면 상태와 persistent storage를 분리해 읽는다.
APK/시뮬레이터·기기별 로그·단계 시간·실패 화면을 관련 run에 연결한다.
실제 시험 기기·감독 장치를 자동화 대상으로 사용하지 않는다.

## CLI와 TUI

일반 CLI는 subprocess argv, stdin, stdout, stderr, returncode로 충분할 수 있다.
입력 prompt·terminal 상태가 중요한 프로그램에만 Pexpect/PTY를 선택한다.

```python
import pexpect

# Demonstration recipe: replace with the actual local application's contract.
child = pexpect.spawn("python3", ["interactive_app.py"], encoding="utf-8", timeout=5)
try:
    child.expect_exact("Name: ")
    child.sendline("sample")
    child.expect_exact("Saved: sample")
    child.expect(pexpect.EOF)
    child.close()
    assert child.exitstatus == 0
finally:
    if child.isalive():
        child.terminate(force=True)
```

이 snippet은 generic recipe이며 실행된 예제라고 주장하지 않는다. 실제 제품에서는
저장 파일을 별도로 읽어 내용도 확인한다. timeout은 실패 단계와 마지막 출력으로
보고하고 반복 enter나 blind sleep으로 숨기지 않는다.
EOF, 사용자 취소, 잘못된 인자, 공백 포함 경로, 두 번 실행했을 때 상태를 선택해서 검사한다.
자신이 만든 child만 정리하고 exit code를 확인한다.

출처: [Pexpect](https://github.com/pexpect/pexpect),
[Maestro](https://github.com/mobile-dev-inc/Maestro).
