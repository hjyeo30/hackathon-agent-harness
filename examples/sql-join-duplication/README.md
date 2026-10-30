# SQL JOIN 중복 집계

## 요구와 실행
생산 40+60+50=150을 설비별 100,50으로 집계한다. 설비 차원 키는 유일하고 모든 생산 설비가 등록되어야 한다.
```bash
python3 join_analysis.py
python3 -m unittest discover -s tests -v
```

## 실패 입력과 oracle
M1 차원 행을 한 번 복제하면 JOIN 뒤 합계는 250이 된다. SQL은 정상 실행되어도 답은 틀린다.
`faults.unchecked_total`이 250을 내는 것을 검사하고, 올바른 구현이 중복 키를 거절하는지 확인한다.
알 수 없는 설비는 INNER JOIN에서 조용히 소실되므로 별도로 검출한다. 빈 테이블의 합계0과 그룹 없음은 이 예제의 정책이다.
실제 DB 경계를 통과하는 통합 테스트를 쓴다. SQL 문자열 자체나 호출 횟수를 비교하지 않는다.

## 관측과 진단
생산 행 수→차원 키 유일성→orphan 수→JOIN 후 합계→그룹 수를 추적한다. CLI는 metrics와 단계 순서를 출력한다.
총합 증가: 키 multiplicity 확인. 감소: orphan/필터 확인. 총합은 맞지만 그룹이 틀림: GROUP BY와 업무 키 확인.
트랜잭션 도중 중복 PK 오류를 주입하고 첫 INSERT도 롤백되는지 재조회한다.

## 사용자 확인과 범위
사용자는 원자료 3개와 그룹 결과를 비교하고 중복 차원을 추가했을 때 오류가 나는 이유를 설명한다.
변경된 JOIN·키·필터가 있으면 이 통합/회귀를 실행한다. 대규모 query plan/인덱스는 실제 규모가 요구할 때 측정한다.
`fixtures/expected.json`은 손계산 참조다. 중복을 임의 DISTINCT로 숨기는 수정은 정책 합의 없이 하지 않는다.

`stage_summary`는 단계 설명이며 계측된 span이 아니다. 공통 verify runner의 trace.json은 검사 명령 단위 span을 기록한다.

## 실제 실패 span 관찰
```bash
python3 observe.py
python3 observe.py --fault duplicate
```
공통 `src/harness/Evidence`를 쓰므로 저장소 안에서 실행한다. 두 번째 실행은 알려진 결함을 검출해 exit1이다.
매번 고유 `.harness/observations/<run>/`에 events.jsonl, metrics.json, trace.json, report.json을 남긴다.
실제 root/child span_id·parent_id·소요시간·status·error_type을 읽고 실패 단계 `validate_dimension_key`를 찾는다.
SQL은 load→key/orphan validation→join_and_aggregate→reconcile을, ML은 load_split→fit→transform→predict→evaluate→oracle을 계측한다.
SQL 중복은 JOIN 전에 차단되고, ML 누수는 계산이 성공해도 독립 oracle에서 탈락한다. 원문 데이터·비밀값을 덤프하지 않는다.
