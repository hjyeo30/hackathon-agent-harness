# 대용량 데이터: 분할 의미와 자원 관측

## 실행
```bash
python3 stream_analysis.py --csv fixtures/groups.csv --chunk-size 2
python3 stream_analysis.py --benchmark --rows 10000 --chunk-size 1000 --max-groups 10
python3 -m unittest discover -s tests -v
```
생성 입력은 파일이나 메모리 전체 목록을 만들지 않는 iterator다. CSV도 행 단위로 읽는다.
각 chunk의 count/sum/min/max를 합친 후 마지막에 mean을 구한다. 고유 group 수는 명시한 max_groups를 넘으면 오류로 중단한다.
그룹 수 무제한에서도 bounded-memory라고 주장하지 않는다. 작업 메모리는 총 행수가 아니라 그룹 수에 좌우된다.

## 정답과 경계 입력
A=[0,0,9] 평균3, B=[100,-20] 평균40. chunk_size1/2/3/4/5/100에서도 같은 집계여야 한다.
[0,0]과[9]의 chunk 평균을 다시 평균내면4.5로 틀린다. faults.py가 이 결함을 보여준다.
빈 입력은 그룹 없음, 합계는 Python 정수로 보존한다. 평균은 float이며 큰 정수의 정확 소수 표현까지 보장하지 않는다.
단일 사용 iterator 검사는 데이터를 다시 훑는 구현을 잡는다. max_groups 초과는 잘라내기나 몰래 샘플링하지 않고 실패한다.

## 메트릭·로그·트레이스
실제 duration_ms, rows_per_second, python_peak_bytes(tracemalloc), rows/chunks/groups를 보고한다.
python_peak_bytes는 Python이 추적한 할당이며 OS RSS나 전체 브라우저/네이티브 메모리가 아니다.
chunk별 progress trace는 처음20개까지만 보존하고 누락 개수를 함께 보고한다. 모든 행을 로그로 출력하지 않는다.
N/2N benchmark는 같은 머신에서 비교하는 자료다. 머신마다 다른 초당 처리량을 보편 PASS 기준으로 쓰지 않는다.

## 원인 조사와 선택 기준
메모리 증가: 고유 그룹 수→중간 리스트/복사→출력 크기. 느림: CSV decode→자료형 변환→집계→출력 순으로 실측한다.
chunk 크기보다 group cardinality가 주원인이면 chunk만 줄여 해결했다고 하지 않는다. 전체 정렬·다대다 JOIN은 이 집계처럼 단순 분할 합성이 안 될 수 있다.
알고리즘/자료구조 변경 뒤 tiny oracle과 partition 회귀를 먼저 실행하고 필요한 규모 측정을 추가한다.
사용자는 결과가 같은지와 자원 측정을 함께 확인한다. 분산엔진·체크포인트·큐는 실패 비용과 규모가 요구할 때만 도입한다.
