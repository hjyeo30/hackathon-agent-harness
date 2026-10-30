# 재시도와 중복 작업 · SQLite 멱등성

외부 API에 연결하지 않고 요청 처리의 핵심 상태 전이를 실제 SQLite에서 실행한다.
HTTP 라우터 예제가 아니라 API 내부 서비스 함수다. 이름만 성공이라고 표시하는 대신
`requests`와 `work_orders`의 저장 상태를 독립 SQL 조회로 확인한다.

## 먼저 합의할 정책

같은 request key + 같은 payload는 같은 결과를 반환한다. 같은 key + 다른 payload는
충돌 오류다. 다른 key는 내용이 같아도 별개 작업이다. 요청 식별과 실제 작업 생성을
한 트랜잭션에 묶는다. 키 보관 기간, 사용자별 key 범위, 실제 외부 시스템 side effect는
생산 환경의 별도 설계이며 이 작은 예제에서 exactly-once 외부 효과를 보장하지 않는다.

## 실행과 직접 관찰

```bash
python3 ledger.py --db .runs/orders.sqlite
python3 -m unittest discover -s tests -v
```

데모는 같은 이벤트를 세 번 보내며 첫 created=true, 이후 false를 반환한다. 처음 실행의
저장 행 수는 요청/작업 각각 1이다. 재실행해도 1이어야 한다. 새 실험은 다른 `--db`를 사용한다.
상태를 직접 확인하려면 Python sqlite3 또는 SQLite 도구로 두 테이블을 조회한다.
`.runs/orders.events.jsonl`에 transaction trace와 결과·시간이 남는다. payload 원문은 남기지 않는다.

## 입력과 oracle

| 상황 | 독립 정답 | 잡는 실패 |
|---|---|---|
| 같은 요청 3회, 연결 재개 | 두 테이블 각각 1행·동일 결과 ID | retry마다 효과 생성 |
| 같은 key 다른 내용 | Conflict, 기존 상태 그대로 | key만 보고 잘못된 성공 반환 |
| commit 직전 실패 | 두 테이블 모두 0행 | 부분 저장·유령 성공 |
| 실패 후 retry | 두 테이블 각각 1행 | 재개 불능 또는 중복 |
| 두 스레드 같은 key | created 합계 1 | check-then-insert 경쟁 |
| 다른 key 동일 내용 | 작업 2행 | 과도한 중복 제거 |

`fail_before_commit`는 테스트용 오류 주입 지점이며 fallback이 아니다. 실패는 예외로 전파하고
rollback한다. 테스트는 정상 구현이 실패를 드러내는지, 재실행 후 저장 상태가 일치하는지 본다.

## 실패 분석과 범위

trace의 FAIL/Conflict/RuntimeError를 먼저 확인하고, 같은 임시 DB의 두 테이블 행을 조회한다.
lock timeout은 경쟁/환경 문제이며 validation 오류와 구분한다. DB 오류를 retry 무한 루프로
감싸지 않는다. SQLite 파일에 두 레코드를 원자적으로 저장할 수 있다는 범위만 증명한다.
외부 결제·메일·메시지는 별도의 outbox/수신자 멱등성 같은 경계를 검토해야 한다.

recap에서는 실제로 관찰한 중복 방지와 rollback을 설명한다. 실제 외부 API 장애를 경험했다고
말하지 않는다. 필수 검사는 중복·충돌·부분 실패이고, 분산 부하 시험은 현재 범위 밖이다.
