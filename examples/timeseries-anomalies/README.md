# 센서 시계열: 급변·지속 변화·고착·누락

## 실행과 정책
```bash
python3 sensors.py
python3 -m unittest discover -s tests -v
```
측정 전에 확보한 reference의 중앙값을 baseline으로 쓴다. 샘플 시간 간격1을 가정한다.
급변은 |측정-baseline|>3, 지속변화는 같은 방향으로0.5 이상인3개 연속 관측,
고착 후보는 완전히 같은 값4회 연속이다. gap/null은 연속성을 끊는다.
이 숫자는 합성 예제 계약이며 실제 장비 임계값이 아니다. 정상 steady-state도 고착 후보가 될 수 있다.

## 독립 oracle와 입력
reference median=10. t4에 10.6,10.8,11의3회 변화, t5에14.1 급변,
t6에 누락, t9에12의3회 변화, t10에12의4회 고착 후보가 발생한다.
`faults.zero_fill_spikes`는 null을0으로 바꿔 가짜 급변을 만든다. 명시적인 missing 사건과 비교한다.
경계값13은 급변이 아니고13.01은 급변이다. 순서를 섞어도 같아야 한다는 변형 테스트는 이 시계열에는 잘못된 가정이다.

## 관측·진단·회귀
event에는 시간과 종류·편차/지속길이가 있어 실패 시 어느 구간에서 어떤 규칙이 작동했는지 추적한다.
CLI의 readings/events/duration_ms와 reference→order→missing→candidate 단계, runner의 실행 trace를 함께 본다.
오경보는 누락 대치→기준선 출처→시간 순서→임계값→정상 운전 상태 순으로 조사한다.
임계값/전처리를 바꾸면 알려진 사건과 정상 구간을 함께 재검증한다. 합성 테스트 통과를 실제 recall/precision으로 표현하지 않는다.
실제 공정에서는 규격 한계와 통계적 관리 한계, 설비 상태별 기준선, 센서 정밀도를 사용자/업무 담당자와 확인한다.
사용자는 fixture 시간표와 event 목록을 대조한다. 원인 고장 진단이나 실제 장비 제어는 범위 밖이다.

`stage_summary`는 단계 설명이며 계측된 span이 아니다. 공통 verify runner의 trace.json은 검사 명령 단위 span을 기록한다.
