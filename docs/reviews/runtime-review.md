# 독립 runtime·앱 검토

검토일: 2026-10-31. 검토자: 구현을 소유하지 않은 `runtime_review` agent.
범위: 계획 R01/R04/R05/R06/R08, `src/harness`, `scripts`, 코어 테스트,
웹/API/RAG/기존 코드 디버깅 예제. 제품 소스는 수정하지 않았다.
발견은 담당 구현자에게 전달했고 아래 수정 결과를 별도로 기록한다.

## 독립적으로 확인한 기본 동작

- 코어 `python3 -m unittest discover -s tests -v`: 수정 전 36개 PASS.
  기본 suite가 모두 성공했어도 아래 반례를 추가로 발견했다.
- 실제 kit를 별도 임시 기존 프로젝트에 설치: 158개 파일, 7개 skill.
  기존 `AGENTS.md`와 `.codex/config.toml` 내용 보존. 두 번째 설치 전부 unchanged.
  설치된 skill의 로컬 Markdown 링크 26개를 실제 경로로 해석: 누락 0개.
- 예제별 동일 unittest 명령: API 6개, 디버깅 5개, 웹 HTTP 8개 PASS.
- 웹 독립 검사는 별도 ephemeral localhost 포트와 실제 Chromium을 사용했다.
  공유 8765 서버를 조작하지 않았고 독립 서버/브라우저는 종료했다.
- 검토 중 GitHub, 외부 계정, 제출에 대한 변경은 수행하지 않았다.

## 발견 사항과 재현

### RV-01 · P1 · R05 · 없는 인용이 grounding 검사를 통과

위치: `examples/rag-grounding/grounding.py`, `is_grounded`.
원래 구현은 `current.get(identity) == citation.get('quote') == result.get('answer')`를
사용해 세 값 모두 `None`이면 true를 반환했다.

```python
is_grounded({'status': 'supported', 'answer': None, 'citations': [{}]}, docs)
# 실제 수정 전: True / 기대: False
is_grounded({'status': 'supported', 'answer': None,
             'citations': [{'id': 'made-up', 'version': 99, 'quote': None}]}, docs)
# 실제 수정 전: True / 기대: False
```

영향: 근거 누락·잘못된 응답 schema를 잡아야 하는 독립 oracle 자체가 거짓 PASS를 낸다.
최소 수정: 유효한 answer/citation 형태와 현재 문서 identity 존재를 먼저 검사한 뒤 비교.

### RV-02 · P2 · R05 · 상충 문서 검증이 입력 순서에 의존

위치: 같은 파일, `latest_documents`.
같은 id의 v1 내용 `one`, v1 내용 `conflict`, v2 내용 `newest`를 준비했다.
`[v1a,v1b,v2]`는 ValueError지만 `[v2,v1a,v1b]`는 v2를 정상 반환했다.
README의 같은 ID/version 상충 거절 계약과 달랐다.
최소 수정: 최신본 선택과 별도로 모든 `(id,version)`의 일관성을 검사.

### RV-03 · P2 · R04/R06 · 실행 권한 변경 후 오래된 PASS가 유효

위치: `src/harness/evidence.py`, `fingerprint`; `cli.py`, `check_final`.
별도 프로젝트에 `#!/bin/sh\nexit 0\n`인 `run.sh`를 만들고 0755로 설정했다.
필수 smoke 검사 argv `['./run.sh']`를 실행해 PASS를 받았다.
내용을 바꾸지 않고 0644로 바꾸면 과거 report의 final-check는 여전히 PASS였다.
동일 manifest를 실제 다시 실행하면 BLOCKED / PermissionError였다.
최소 수정: 실행에 영향을 주는 execute permission bits를 source identity에 포함.

### RV-04 · P2 · R04/R06 · 파손된 trace를 완전한 evidence로 인정

위치: `src/harness/cli.py`, `check_final`의 bundle 검사.
정상 run의 `trace.json` 내용만 `not json`으로 바꾸면 final-check가 PASS였다.
원인은 존재 여부만 확인하고 파싱 가능성·실행 ID·필수 구조를 확인하지 않은 것이다.
최소 수정: JSON/JSONL 파싱과 기본 구조 및 run identity를 확인하고 실패는 BLOCKED.
이는 evidence 사용 가능성 검사이며 변조 방지 서명 요구가 아니다.

### RV-05 · P2 · R08 · CSV 교체 후 숨은 이전 설비 필터 적용

위치: `examples/web-filter-export/index.html`의 file change 및 equipment 갱신.
실제 브라우저 재현:

1. multi-equipment fixture 업로드·분석 → E2 선택·분석.
2. `Z,E1,2026-10-01,9,10` 한 행만 있는 CSV로 교체·분석.
3. 실제 요청 filters.equipment는 E2였다. 응답 count=0, yield_rate=null.
4. 새 option에는 E1만 있어 select.value='', selectedIndex=-1이 된다.
   화면은 데이터 없음인데 다운로드가 활성화되고 이전 E2 조건을 사용한다.
5. 같은 입력으로 한 번 더 분석하면 빈 필터가 전송돼 90%가 된다.

영향: 화면의 필터·결과·다운로드 의미가 달라지고 같은 조작을 반복해야 바로잡힌다.
최소 수정: 파일 교체 때 설비 옵션/선택을 명시적으로 초기화하거나 사라진 선택을
사용자에게 명확히 보존. 다른 설비 집합의 파일 교체를 실제 브라우저 회귀로 추가.

## 수정 후 독립 재검증

- RV-01/RV-02: 구현자의 명시적 자료형/identity 검사와 전체 version 충돌 검사를
  읽었다. RAG unittest 10개 PASS를 직접 실행했다. null/unknown citation 반례와
  상충 문서 순열 검사가 포함되어 있다.
- RV-03: 원래 chmod 재현을 별도 프로젝트에서 그대로 반복했다. 최초 PASS,
  0755→0644 변경 후 과거 report는 이제 BLOCKED이며 source 변경 이유를 표시한다.
  0755 복원 후에는 다시 정상 PASS였다.
- RV-04: 정상 run의 trace.json, metrics.json, events.jsonl을 각각 `not json`으로
  바꾸어 모두 BLOCKED를 확인했다. trace run_id를 다른 값으로 바꾸어도
  `Evidence run identity mismatch: trace.json`으로 BLOCKED였다.
- RV-05: 새 ephemeral 서버와 실제 Chromium에서 같은 파일 교체를 반복했다.
  교체 즉시 all-equipment와 비활성 다운로드, 첫 분석 request의 빈 equipment,
  결과 1행/90%, DOM 90.00%/selectedIndex=0을 assertion으로 확인했다.
  실제 다운로드 파일에도 Z,E1 행이 포함됐다. 서버/브라우저를 종료했다.
- 코어 수정 후 전체 코어 unittest 40개 PASS를 직접 실행했다. source 변경,
  파손/다른 실행의 evidence, 기존 파일 보존을 포함한다.

최종 판정: **APPROVE (검토 범위 한정)** — 위 5개 발견을 담당 구현자가 수정했고,
검토자가 원래 반례를 재실행하여 모두 해결을 확인했다. 남은 필수 수정 없음.
이 문서는 전체 저장소·도구 설치·대회 환경을 모두 검증했다는 주장이 아니다.
