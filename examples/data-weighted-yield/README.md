# 배치 수율: 그럴듯한 숫자와 올바른 숫자

## 문제와 먼저 합의할 것
배치별 양품 수/검사 수를 합쳐 전체 수율을 구한다. 수율은 전체 양품/전체 검사로 정의한다.
0분모·빈 입력은 미정이므로 오류, 중복 배치 ID는 오류로 정했다. 이 정책은 예제의 선택이며 실제 업무 정의를 먼저 확인한다.

## 실행
```bash
python3 yield_analysis.py fixtures/batches.csv
python3 -m unittest discover -s tests -v
```
저장소 루트에서 evidence bundle까지 남기려면:
```bash
python3 scripts/verify.py --manifest examples/data-weighted-yield/verification.json
```

## 독립 정답과 입력 선정
9/10과 1/90을 합치면 10/100 = 10%이다. 배치 수율 평균은 41/90 약 45.56%라서 틀린다.
동일 크기 배치만 테스트하면 이 오류가 숨는다. `faults.py`는 고의로 틀린 구현이며 제품에 사용하지 않는다.
행 순서 변경은 집계의 순서 불변성을, (1,90)을 (1,45)+(0,45)로 분할하는 검사는 가중 합산을 확인한다.
음수·분모0·양품>전체·비정수·중복 ID는 실제 입력 계약 경계다. 무한한 랜덤 수는 필요하지 않다.

## 관측과 실패 분석
CLI JSON은 실패 stage/error_type, 성공 rows/good_count/total_count/duration_ms와 단계 순서를 낸다.
행 수가 다르면 CSV/중복 정책, 합계가 다르면 입력·집계, 합계는 맞고 비율만 틀리면 분모·평균 정책을 조사한다.
상세 시간 span/명령/stdout/stderr는 공통 verify runner가 기록한다. 입력 전문 대신 fixture 경로와 개수를 남긴다.

## 회귀와 사용자 확인
계산 수정 시 이 suite를, CSV 파서 변경 시 스키마·중복 검사를 포함한다. UI-only 변경 때문에 이 검사를 매번 반복할 필요는 없다.
사용자는 CLI의 10%와 원자료 두 행을 직접 비교한다. Fraction은 작은 정확 정답을 위한 선택이며 대용량 엔진 권장이 아니다.
선택 확장: 날짜별/설비별 필터, 고정소수점 표시, 결측 배치 정책. 현재 분석에 필요하지 않은 웹·DB는 추가하지 않는다.

`stage_summary`는 단계 설명이며 계측된 span이 아니다. 공통 verify runner의 trace.json은 검사 명령 단위 span을 기록한다.

## 실제 nested trace와 실패 증거 실습
저장소의 공통 Evidence API를 쓰는 `observe.py`는 별도의 실행이다. 외부 패키지는 필요 없지만 저장소의 `src/harness`가 필요하다.
```bash
python3 observe.py
python3 observe.py --fault mean
```
두 번째 명령은 의도한 결함 때문에 exit1이어야 정상적인 검증이다. 성공으로 위장하지 않는다.
출력된 `.harness/observations/<run>/`의 report.json, events.jsonl, metrics.json, trace.json을 읽는다.
root/child span과 parent_id, 실제 duration_seconds, 실패 stage/error_type을 확인한다.
정상 실행에서는 oracle이 일치한다. 결함 실행에서는 계산/라벨링은 실행됐지만 compare_oracle에서 실패한다.
이미지는 실패한 경우에도 overlay.svg가 남아 좌표와 결과를 직접 볼 수 있다. 출력 디렉터리 재사용은 거절한다.
