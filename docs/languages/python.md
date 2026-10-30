# Python 작업에서 필요한 판단

모든 Python 작업에 아래 항목을 의무 적용하지 않는다. 바뀌는 경계에 해당하는 부분을
읽고 현재 프로젝트 환경과 단순한 해법을 우선한다.

## 환경과 실행

기존 pyproject/requirements/lockfile과 Python 버전을 확인한다. 다른 프로젝트의 가상환경을
우연히 사용하지 않는다. 핵심 kit는 Python 3.9+ 표준 라이브러리로 실행한다. 문제에서
추가 라이브러리가 필요하면 설치·버전·실행 가능 여부를 확인하고 성공을 실제 import로 본다.
빌드/타입/lint/테스트를 각각 무엇의 증거인지 구분한다.

## 수치와 입력

외부 CSV/JSON/CLI의 타입·누락·범위를 신뢰 경계에서 검증한다. 문자열 ID를 숫자로
바꾸면 선행 0을 잃는지 확인한다. NaN/Inf가 허용되는지, bool이 숫자처럼 처리되는지,
소수 오차가 업무 결과에 영향을 주는지 고려한다. 금액·정밀 비율의 요구에 따라 적절한
표현을 선택하고 무조건 float나 Decimal로 통일하지 않는다.

기대값은 현재 함수의 출력을 복사하지 말고 작은 손계산/명시적 규칙에서 만든다.
부동소수점 비교 허용오차는 값의 규모와 단위에 맞게 정한다. 날짜는 시간대/날짜 경계를
명시하고 naive/aware datetime을 무심코 섞지 않는다.

## 자료구조와 자원

반복 membership/lookup이 많으면 list scan과 set/dict의 시간·메모리를 비교한다.
대량 파일은 iterator/chunk가 가능한지 확인한다. generator라고 해도 마지막에 전부
list로 만들면 메모리 이점이 사라질 수 있다. 반복 concat·불필요한 copy·join 폭증을 조사한다.

동시성이 필요한 이유를 먼저 측정한다. CPU 연산과 I/O 대기에는 다른 선택이 필요하며,
worker 수 증가가 항상 속도 향상을 뜻하지 않는다. in-flight 작업/queue/결과 모음의
크기를 제한한다. 작은 순차 처리에 async framework를 추가하지 않는다.

## 파일·실패·부분 결과

경로는 pathlib 등으로 다루고 사용자 입력을 shell 명령으로 보간하지 않는다.
subprocess에는 argv, cwd, 유한 timeout을 준다. 필요할 때 자신이 시작한 자식
프로세스 그룹까지 정리한다. stdout/stderr와 return code를 모두 읽는다.

읽기/쓰기 오류와 입력 validation 오류를 구분한다. broad except 후 빈 목록 반환은
실패를 숨긴다. 독자가 부분 결과를 보면 안 되는 파일은 임시 출력→검증→전환 경계를
고려하되 cheap rerun 작업마다 manifest/checkpoint 시스템을 만들지 않는다.

## 검증과 관측

계산은 단위/golden, 파일·DB·프로세스는 통합, 사용자 명령은 CLI smoke로 검증한다.
pytest가 없으면 프로젝트 표준 또는 stdlib unittest로 충분할 수 있다. 패키지 선정 자체가
목표가 아니다. 중요한 속성이 있을 때 Hypothesis를 고려한다.

perf_counter로 경과 시간을, 필요한 경우 tracemalloc이나 OS 도구로 메모리를 본다.
tracemalloc과 전체 RSS를 혼동하지 않는다. 예외 경계에는 오류 종류와 stage/input ID를
남기고 민감 원문/환경 전체를 로그로 덤프하지 않는다. [관측](../guides/observability.md),
[대용량](../domains/large-data.md)을 필요한 경우 함께 읽는다.
