# 기존 프로젝트 디버깅 · CSV 마지막 행 누락

증상은 "내보낸 CSV의 마지막 항목이 사라짐"이다. 정상 구현은 `exporter.py`, 알려진
이전 결함은 제품 경로에서 호출하지 않는 `faults.py`에 격리되어 있다.

## 실행과 최소 재현

```bash
python3 exporter.py fixtures/last-row.csv
python3 -m unittest discover -s tests -v
```

fixture는 두 행 중 마지막 행만 active이고 마지막 줄바꿈도 없다. 정답은 item=last 한 행이다.
stdout은 CSV, stderr는 처리 행 수와 소요 시간 JSON으로 분리해 파이프로 연결할 수 있다.
오류는 비0 종료와 FAIL 진단으로 나타나며 빈 성공 CSV로 바꾸지 않는다.

## 원인 조사 기록 예시

- 관찰: 입력의 active 개수 1, 결함 구현 출력 0.
- 가설: 파일 끝 줄바꿈 처리 또는 마지막 원소를 버리는 slice.
- 근거: `faults.drops_last_row`가 `rows[:-1]`을 순회한다. 줄바꿈 여부와 무관하게 마지막 행을 버린다.
- 최소 수정: 모든 파싱 행을 순회. CSV 파싱은 표준 csv 모듈에 맡긴다.
- 회귀: 마지막 active 행, 한 행 입력, 인용부호 안 줄바꿈, 빈 필터 결과.
- 실행 경계: 실제 CLI stdout과 stderr, 종료 코드도 확인.

이 기록은 포함된 가상 결함의 설명이며 사용자가 실제로 과거에 겪은 사건이 아니다.
`test_regression_last_row_without_newline`은 결함 변형이 oracle과 다름도 확인한다.

## 테스트 선택

마지막 행 결함을 잡는데 브라우저/DB 테스트는 필요 없다. 계산 함수 검사만으로 CLI 출력이
오염되지 않았다는 결론은 낼 수 없어 subprocess 통합 검사를 하나 둔다. 모든 임의 CSV를
생성하는 fuzzing은 현재 핵심 경로보다 우선하지 않는다. 상태에 오탈자가 있으면 행을 조용히
제외하지 않고 입력 오류로 반환한다. 이 정책은 실제 과제에서는 사용자와 합의해야 한다.
