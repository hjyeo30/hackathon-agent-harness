# 실행 예제 선택

모든 문제·데이터는 작은 합성 연습입니다. 실제 대회 출제 예측이나 실제 산업 성능의
증거가 아닙니다. 예제의 business policy는 실제 과제에서 다시 확인해야 합니다.

| 예제 | 잡으려는 오류 | 정답/관측 |
|---|---|---|
| [웹 CSV](web-filter-export/README.md) | 잘못된 비율, 필터/다운로드 불일치, 늦은 응답 | 실제 UI→HTTP→계산→파일 |
| [수율 집계](data-weighted-yield/README.md) | 비율의 단순 평균, 중복·무효 수량 | 10/100 손계산 |
| [SQL JOIN](sql-join-duplication/README.md) | 차원 키 중복으로 수량 증폭 | 작은 SQLite의 row count·합계 |
| [이미지 영역](image-components/README.md) | 축·경계·4/8 연결·임계값 오류 | 실제 PGM 픽셀과 SVG overlay |
| [API 멱등성](api-idempotency/README.md) | 반복 요청 중복 저장, 부분 실패 | SQLite durable rows와 transaction trace |
| [ML 누수](ml-leakage/README.md) | 평가 데이터로 전처리 학습 | train-only fit과 독립 평가 |
| [일정 제약](scheduling-constraints/README.md) | 겹침·선행·가용성 위반 | 독립 feasibility checker와 tiny oracle |
| [근거 검색](rag-grounding/README.md) | 근거 없는 답, 오래된 버전, 잘못된 인용 | local retrieval·원문 대조·abstention |
| [기존 코드 디버깅](existing-project-debugging/README.md) | CSV 마지막 행 유실 | 재현 fixture와 회귀 |
| [센서 시계열](timeseries-anomalies/README.md) | 누락·고착·급변·드리프트 혼동 | 합성 이상 위치와 단계 관측 |
| [대용량 집계](large-data/README.md) | chunk 평균 오류, 그룹 메모리 폭증 | 분할 불변성·실측 시간/할당 |

## 공통 실행

각 디렉터리에서 `python3 -m unittest discover -s tests -v`로 필요한 정답·경계·회귀
검사를 실행합니다. 루트 manifest는 예제들을 모아 evidence bundle을 남깁니다.

```bash
python3 scripts/verify.py --manifest verification.json --profile core
```

웹 E2E는 별도 의존성과 browser profile을 사용합니다. core 통과를 E2E 통과로
표현하지 않습니다. 실제 예제별 test 수와 실행 결과는 [검증 기록](../docs/validation.md)에 있습니다.

## 연습 순서

문제/업무 정책 읽기→작은 oracle 직접 확인→정상 실행→격리된 고의 결함이 어떤
검사에서 드러나는지 확인→수정/같은 검사 재통과→메인 직접 사용→사용자 설명.
`faults.py` 등은 연습용 변형이며 제품 코드의 숨은 fallback이 아닙니다.
반례와 오류 단계는 남기되 실제 과제 데이터나 민감한 로그를 이 공개 레포로 보내지 않습니다.

모바일/대화형 CLI는 [도구 레시피](../docs/tools/mobile-and-terminal.md)와
분야별 문서를 참고합니다. 실제 device가 없는 상태에서 모바일 E2E를 검증했다고
주장하지 않습니다. 네이티브 앱 스타터 전체를 기본 의존성으로 포함하지 않았습니다.
