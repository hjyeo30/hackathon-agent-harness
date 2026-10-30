# 웹 CSV 분석 · 필터 · 다운로드

Python 3.9+ 표준 라이브러리의 실제 HTTP 앱과 Playwright 사용자 흐름 검사다.
모든 데이터는 직접 만든 합성 fixture이고 외부 서비스/키가 필요 없다.

## 문제와 먼저 결정할 것

설비별 생산 CSV를 분석하고 기간·설비로 필터한 결과를 다운로드한다. 먼저 수율이
배치 비율 평균인지 전체 양품/검사 비율인지, 날짜 양끝 포함 여부, 중복 batch,
분모 0, 결과 없음의 의미를 확인한다. 여기서는 **전체 양품/검사**, 날짜 양끝 포함,
중복/분모 0 거절, 필터 결과 없음은 `yield_rate: null`로 정했다.

필수 흐름은 입력→정확한 집계→조회→같은 조건의 다운로드다. 로그인·DB·캐시는
이 과제에 요구되지 않으므로 추가하지 않는다. 1 MiB 요청 제한의 작은 예제다.
큰 파일 streaming을 검증했다고 주장하지 않는다.

## 실행

예제 디렉터리에서:

```bash
python3 server.py --host 127.0.0.1 --port 8765 --log-dir .runs/web
```

브라우저에서 `http://127.0.0.1:8765`를 연다. 대회 내부 Browser에 제공할 때는
`--host 0.0.0.0`으로 실행하고 실제 포트 8765를 지정한다. 서버를 실행한 터미널을
유지하고 종료 시 그 프로세스에 Ctrl+C를 보낸다. 전체 이름으로 프로세스를 죽이지 않는다.
`/health`는 앱 이름과 실행 run_id를 반환한다.

## 사용자가 직접 확인

1. `fixtures/unequal-batches.csv`를 선택하고 분석: 2개 배치, 양품 10/검사 100, **10.00%**.
2. 종료일 2026-10-01 선택: 이전 다운로드가 비활성화되어야 한다. 다시 분석: **90.00%**, A 한 행.
3. CSV 다운로드 후 내용을 열어 A만 들어 있는지 확인한다.
4. `fixtures/multi-equipment.csv`로 교체·분석 후 E2 선택·분석: **100.00%**.
5. good를 total보다 크게 만든 파일은 명확한 오류가 나고 이전 성공값을 보이지 않아야 한다.

손계산 근거: A 9/10, B 1/90 → (9+1)/(10+90)=0.1. 단순 평균 약 45.56%는 틀리다.

## 필요한 검사와 명령

```bash
python3 -m unittest discover -s tests -v
```

Python 검사는 계산·경계값·실제 HTTP·CSV export·trace를 확인한다. 브라우저 확인을
대신하지 않는다. Node 20+와 pnpm을 준비한 뒤:

```bash
pnpm install --frozen-lockfile
node node_modules/@playwright/test/cli.js install chromium
node node_modules/@playwright/test/cli.js test
```

`@playwright/test` 1.64.1은 `package.json`과 pnpm lock에 고정했다. 브라우저 바이너리와
Linux 공유 라이브러리는 별도 환경 조건이다. 설치 불가를 검증 성공으로 표시하지 않는다.
기존 서비스가 8765를 사용하면 테스트는 실패한다. 임의로 해당 서비스를 종료하지 않는다.

Playwright는 실제 UI→HTTP→집계를 통과한다. API를 정답 응답으로 대체하지 않는다.
늦은 응답 회귀만 요청의 **전달 시점**을 제어하며 계산은 실제 서버에 맡긴다.
각 테스트는 새 브라우저 컨텍스트다. 재시도로 우연한 통과를 숨기지 않는다.

캡처/trace는 기본 꺼짐이다. 해당 환경에서 허용되었을 때만:

```bash
CAPTURE_BROWSER_EVIDENCE=1 node node_modules/@playwright/test/cli.js test
```

기본 결과는 `.runs/playwright-report.json`, 실패 artifact는 `.runs/playwright/`에 남는다.

## 로그·메트릭·트레이스로 원인 찾기

서버 `.runs/web/events.jsonl`은 `run_id`, `trace_id`, `span_id`, `parent_id`,
`stage`, `status`, `error_type`, `duration_ms`를 기록한다. request 아래 decode→parse→filter→aggregate/export
단계를 연결한다. input_rows/output_rows와 HTTP 상태/소요 시간을 기록하며 CSV 원문은 기록하지 않는다.
UI 확인 ID와 응답 `X-Trace-Id`로 동일 요청을 찾는다.

- 400 + parse FAIL: 열/날짜/수량/중복 계약 위반. UI 코드부터 고치지 않는다.
- 집계 정답은 맞고 표시가 다름: API 수치와 DOM을 비교한다.
- 다운로드만 다름: `/api/export`의 필터 및 출력 행을 검사한다.
- 이전 응답이 덮음: 브라우저 요청 순서와 request 소유권(sequence/AbortController)을 확인한다.
- 500: unhandled 이벤트의 exception type·traceback을 확인한다. 성공 화면으로 덮지 않는다.

오류 원인은 증거와 가설을 구분해 기록한다. 수정 후 실패 재현 검사와 영향받는 계산/화면
검사를 다시 실행한다. CSS만 바꾼 경우 SQL·ML 예제 전체를 반복할 이유는 없다.

## 한계와 회귀의 효력

`test_weighted_not_mean_of_percentages`는 격리된 단순 평균 변형이 정답과 다른지 확인한다.
실제 코드에 고의 결함 스위치를 넣지 않았다. CSV formula로 해석될 수 있는 문자열은
export에서 작은따옴표를 붙인다. 인증·동시 공유 저장·대규모 업로드·브라우저 전종은 범위 밖이다.
이 예제의 성공은 이 계약과 합성 fixture에 대한 증거다.
