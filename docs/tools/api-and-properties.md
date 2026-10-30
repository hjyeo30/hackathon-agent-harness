# API와 속성 기반 검사

고정된 작은 정답 사례부터 시작합니다. 속성 생성기는 정답을 대신 발견해 주지 않습니다.

## API 최소 검사

- 정상 입력의 response shape뿐 아니라 중요한 값과 저장 side effect를 확인한다.
- 무효 입력은 합의된 오류로 끝나고 잘못된 값이 저장되지 않아야 한다.
- 인증이 요구되면 신원 확인과 자원 접근 권한을 구분한다. JWT부터 선택하지 않는다.
- 재시도가 있는 변경 요청은 같은 key의 반복과 다른 payload 충돌을 구분한다.
- DB commit 전후의 실패 위치를 관측하고 실제 재시작 결과를 확인한다.

관측 필드: request_id, operation, status, duration_ms, retry_attempt,
validation_error_code, affected_rows. 토큰·전체 body·개인정보는 기록하지 않는다.
retry는 일시 실패에만 제한하고 여러 계층의 중첩 재시도는 피한다.

## Schemathesis를 선택한다면

[공식 문서](https://schemathesis.readthedocs.io/en/stable/)의 버전에 맞춰 로컬 API의
OpenAPI를 입력한다. 먼저 스키마의 필수/nullable/경계 정의가 실제 약속과 같은지 읽는다.
stateful operation은 disposable DB에서 실행한다. 실패 입력과 재현 명령을 보존한다.
생성 검사가 모두 통과해도 비율 집계·권한·업무 의미가 맞는지는 별도 oracle로 판단한다.

## 좋은 속성과 나쁜 속성

| 대상 | 유용한 관계 | 전제 |
|---|---|---|
| 합계/수율 집계 | 행 순서 변경에도 결과 동일 | 순서가 의미 없는 연산 |
| 분할 집계 | 부분 분자·분모 합산 결과 = 전체 집계 | 비율 자체의 평균 금지 |
| parser/serializer | parse(serialize(x))가 의미를 보존 | 표현 손실 정책 명시 |
| 일정 | 겹침 없음·선행 관계 유지 | 별도 verifier가 제약을 검사 |
| 요청 재실행 | 최종 저장 상태가 한 번 실행과 동일 | 동일 key/payload와 정해진 의미 |

항상 정렬한 뒤 시계열을 비교하거나 모든 문자열을 trim한 뒤 결과를 비교하는 식으로
차이를 지워 버리지 않는다. 그 정규화가 업무 정의에 포함되는지 먼저 확인한다.

Hypothesis/fast-check에는 유효 범위와 무효 범위를 별도로 준다. 큰 random 표본만
실행하기보다 빈값·하나·경계±1·중복·비대칭 입력을 명시한다. seed와 축소된 반례를
보존해 회귀 테스트로 옮긴다. 통과 횟수가 전체 입력에 대한 증명은 아니다.

출처: [Hypothesis](https://hypothesis.readthedocs.io/),
[fast-check](https://github.com/dubzzz/fast-check),
[Schemathesis](https://github.com/schemathesis/schemathesis).
