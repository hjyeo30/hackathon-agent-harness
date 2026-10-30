# 로그·메트릭·트레이스와 실패 원인

관측의 목적은 많은 출력을 만드는 것이 아니라 “어느 입력의 어느 단계가 왜 틀렸는가”를
판별하는 것이다. 결과의 정답은 여전히 업무 규칙/oracle이 결정한다.

## 최소 개념

- 로그: 사건과 오류. 단계, 입력 ID, 오류 종류, 필요한 위치를 담는다.
- 메트릭: 크기·시간·자원. 값과 단위를 함께 담는다.
- 트레이스: 한 요청/실행이 통과한 단계와 부모-자식 관계, 각 단계의 결과와 시간.
- 증거 묶음: 이 관측을 명령·입력·코드 상태·기대값·실제 출력에 연결한 기록.

로컬 JSONL + 요약 JSON + stdout/stderr로 시작한다. 관측 서버, exporter,
OpenTelemetry 배포를 기본 의존성으로 요구하지 않는다. 필요할 때만 기존 시스템을 쓴다.

## 선택할 필드

| 공통 | 의미 |
|---|---|
| run_id | 같은 검증 실행을 묶는 ID |
| span_id, parent_id | 단계의 인과관계 |
| stage | parse/validate/aggregate/export 같은 실제 경계 |
| status | 시작/완료/실패 및 전체 검사 결과 |
| duration + unit | 경과 시간, 측정 단위 명시 |
| error_type | validation/timeout/io 등 분류 가능한 오류 |
| input_id, code/build identity | 어떤 자료와 코드의 결과인지 |

runner는 명령 단위 관측을 제공한다. 앱의 내부 단계는 그 앱에서 별도 계측해야 한다.
runner가 한 subprocess를 감쌌다는 사실을 전체 분산 trace라고 부르지 않는다.

## 상황별 관측

| 상황 | 로그 | 메트릭 | 유용한 span |
|---|---|---|---|
| 웹/API | 요청 ID, route, 상태, error category | latency ms, 요청/실패 count | receive→parse→compute→persist |
| CSV/SQL | 잘못된 행의 번호/종류, 키 정책 | input/valid/output rows, groups count | read→validate→join→aggregate |
| 이미지 | dimensions, 채널/좌표 변환, 입력 ID | pixels, components, duration ms | decode→transform→detect→overlay |
| ML | split/feature/seed 설정, 평가셋 ID | class counts, confusion counts, 지표 | split→fit→predict→evaluate |
| RAG/Agent | 문서 ID, tool call ID, 종료 이유 | retrieved count, tool calls, latency | retrieve→select→answer→check |
| 대용량 | partition ID, 중간 실패 | throughput rows/s, peak memory bytes | read batch→compute→write |

전체 데이터나 환경변수를 덤프하지 않는다. 오류가 난 행의 위치/종류로 충분하면
원문을 로그에 넣지 않는다. 키·토큰·쿠키는 기록하지 않는다. 로컬 로그도 민감정보가
될 수 있다. 공개 레포에는 합성 fixture와 의도한 예시만 남긴다.

## 계측 해석

시간은 경과 측정에 monotonic clock을 쓰고 사람이 읽을 시각은 별도 UTC timestamp로
남긴다. peak memory 측정은 도구·단위·OS·자식 프로세스 포함 여부를 적는다.
`tracemalloc` 값은 Python에서 추적한 할당이며 전체 RSS와 같지 않다. 리눅스와 macOS의
자원 수치 단위를 추정해 섞지 않는다. 처리량은 입력 크기와 wall time을 같이 적는다.

표본 하나로 복잡도를 증명하지 않는다. N/2N 또는 편향된 입력에서 변화가 의미 있는지
보고, warmup/cache/환경 차이를 구분한다. 오차가 큰 측정으로 미세 최적화를 주장하지 않는다.

## 실패 조사 공간

active issue의 `failure-*.md`에 최초 실패, 최소 재현, 가설, 판별 실험, 실제 결과,
원인 확인 수준, 수정, 같은 검사의 재통과를 기록한다. 긴 로그는 evidence 경로로 연결한다.

예: 다운로드 합계가 증가했다면 export span만 보지 않는다. input rows 20 → join rows 26이
처음 어긋난 지점이면 중복 키를 조사한다. HTTP 200이나 빨라진 처리 시간이 정답을
보장하지 않는다. 같은 단계의 오류 로그를 모든 계층에서 중복 출력할 필요도 없다.

## 증거 수명

관련 코드/입력/설정/서버 인스턴스가 바뀌면 이전 PASS의 유효성을 재평가한다.
검증마다 현재 build 또는 source fingerprint를 남기고, 실행 중에 소스가 바뀌었다면
결과를 확정 증거로 사용하지 않는다. cleanup은 프로세스/scratch를 정리하고 evidence는 남긴다.

## 내부 단계 계측 코드 예시

kit root에서 `PYTHONPATH=src`로 실행하거나 설치된 kit의 src를 Python 경로에 넣는다.
이 예제는 매 실행 고유 디렉터리를 생성하고 실패 때도 evidence를 저장한다.
앱의 실제 source/input identity는 runner report 또는 별도 필드로 연결한다.

```python
from pathlib import Path
import uuid
from harness.evidence import Evidence

output = Path(".harness/runs") / ("analysis-" + uuid.uuid4().hex)
evidence = Evidence(output)
report = {"status": "FAIL", "input_id": "two-batches-v1"}
try:
    with evidence.span("analysis") as parent:
        with evidence.span("validate", parent_id=parent["span_id"]):
            batches = [(9, 10), (1, 90)]
            if any(total <= 0 for _, total in batches):
                raise ValueError("nonpositive denominator")
            evidence.metric("input_rows", len(batches), "count")
        with evidence.span("aggregate", parent_id=parent["span_id"]):
            result = sum(g for g, _ in batches) / sum(t for _, t in batches)
            evidence.metric("yield_rate", result, "ratio")
            assert abs(result - 0.1) < 1e-12
    report.update(status="PASS", expected=0.1, observed=result)
except Exception as error:
    report.update(error_type=type(error).__name__)
    raise
finally:
    evidence.finish(report)
```

`events.jsonl`은 시작/끝 사건, `trace.json`은 부모-자식 span과 실패 traceback,
`metrics.json`은 값/단위, `report.json`은 이 예제의 판정을 담는다. 내부 span이 성공했다고
업무 결과를 자동 추론하지 않는다. 위 코드에서도 독립 assertion이 별도로 필요하다.
실패 기록은 [failure-analysis template](../../templates/failure-analysis.md)에서
이 파일들을 가리켜 원인 가설과 판별 실험을 설명한다.
