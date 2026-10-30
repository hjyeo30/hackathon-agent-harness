# ML: 전처리 누수와 성능 해석

## 실제로 구현한 범위
1차원 숫자 결측 평균대치 + 클래스별 중심까지 거리로 분류한다. 학습 데이터로만 대치 평균과 중심을 구하고 모델은 불변 객체다.
```bash
python3 model.py
python3 -m unittest discover -s tests -v
```
훈련 관측값 0,2,8,10의 평균은5. 결측을5로 채우면 음성 중심7/3, 양성 중심9이다.
이 손계산과 test [결측,1,9]의 예측 [0,0,1]을 확인한다.

## 실패 사례와 필요한 테스트
`faults.fit_with_test_imputation`은 평가 입력까지 대치 평균에 포함한다. 평가값100과 -100을 바꾸면 학습 모델이 바뀌므로 누수다.
정상 모델은 평가를 몇 번 하더라도 학습 파라미터가 바뀌지 않는다.
정상9/불량1에서 모두 정상으로 예측하면 accuracy90%지만 불량 recall0이다. 혼동행렬, precision(예측 양성 없으면 null), recall을 출력한다.

## 관측과 진단
CLI trace: fixed split→train fit→freeze→holdout evaluation. train/test 행수와 시간이 metrics다.
성능이 비정상적으로 좋으면 split identity/시간/그룹 중복→전처리 fit 범위→label leakage 순으로 조사한다.
이 예제는 합성 메커니즘 검증이며 100% 결과를 실제 예측 성능이라고 주장하지 않는다.
평가 데이터로 방법을 반복 선택했다면 untouched holdout이라 표현하지 않는다.

## 계획 질문과 사용자 확인
실제 업무에서는 예측 시점에 알 수 있는 입력인가, 같은 장비·제품이 양쪽 split에 있는가, 어느 실수 비용이 큰가를 먼저 정한다.
시계열/그룹 split, 기준선, 임계값 선택은 업무에 따라 추가한다. sklearn·GPU·실서비스는 이 예제에 필요하지 않다.
사용자는 fill/중심을 손계산하고, 90% accuracy가 실패를 감출 수 있음을 confusion matrix로 설명한다.
전처리·분할 수정이면 누수 회귀를, 지표 수정이면 minority/zero-denominator 검사를 수행한다.

`stage_summary`는 단계 설명이며 계측된 span이 아니다. 공통 verify runner의 trace.json은 검사 명령 단위 span을 기록한다.

## 실제 실패 span 관찰
```bash
python3 observe.py
python3 observe.py --fault leakage
```
공통 `src/harness/Evidence`를 쓰므로 저장소 안에서 실행한다. 두 번째 실행은 알려진 결함을 검출해 exit1이다.
매번 고유 `.harness/observations/<run>/`에 events.jsonl, metrics.json, trace.json, report.json을 남긴다.
실제 root/child span_id·parent_id·소요시간·status·error_type을 읽고 실패 단계 `compare_oracle`를 찾는다.
SQL은 load→key/orphan validation→join_and_aggregate→reconcile을, ML은 load_split→fit→transform→predict→evaluate→oracle을 계측한다.
SQL 중복은 JOIN 전에 차단되고, ML 누수는 계산이 성공해도 독립 oracle에서 탈락한다. 원문 데이터·비밀값을 덤프하지 않는다.
