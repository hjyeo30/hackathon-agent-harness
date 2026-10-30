# 실행 가능한 검증과 증거

## 명령 실행

kit root에서 도움말을 확인한다. 설치된 kit root는 대상 프로젝트의 `.harness/kit`이다.
아래의 `verification.json`은 검증하려는 프로젝트의 실제 manifest 경로다.

```bash
python3 scripts/doctor.py --manifest verification.json
python3 scripts/verify.py --manifest verification.json
python3 scripts/verify.py --manifest verification.json --check data-golden
```

`data-golden`은 설명용 check ID다. 실제 manifest의 ID를 사용한다. `--profile`은 manifest에
정의된 검사 그룹 선택이며 core 통과를 browser 통과로 해석하지 않는다. 현재 지원
옵션과 report 위치는 실행하는 버전의 `--help`와 출력으로 확인한다.

## Manifest 계약

`schema_version: 1`, `checks` 배열을 사용한다. 각 check는 id, requirement, kind,
argv 배열, manifest 기준 cwd, timeout_seconds, required, reason, oracle을 가진다.
`profile`은 check별 선택 그룹이며 기본값은 core다. 테스트 명령에는 `test_framework`
(unittest/pytest/playwright)와 필요 시 `min_tests`를 지정해 0개/skip을 검사한다.
선택한 검사에는 실제 assertion을 실행하는 명령을 연결한다. 출력만 찍고 0으로
끝나는 스크립트는 업무 정답을 확인하지 못한다.

```json
{
  "schema_version": 1,
  "checks": [{
    "id": "data-golden",
    "requirement": "R1 overall yield",
    "kind": "unit",
    "test_framework": "unittest",
    "min_tests": 1,
    "argv": ["python3", "-m", "unittest", "discover", "-s", "tests", "-v"],
    "cwd": ".",
    "timeout_seconds": 30,
    "required": true,
    "reason": "Catch averaging unequal batch ratios",
    "oracle": "9/10 and 1/90 aggregate to 10/100"
  }]
}
```

이 예시의 tests 디렉터리는 대상 프로젝트에서 실제 작성되어야 한다. runner는
`argv`를 shell 문자열로 평가하지 않는다. fixture나 manifest를 외부에서 가져왔다면
실행 명령과 부작용을 먼저 읽는다. 의미 없는 명령을 PASS 제조용으로 등록하지 않는다.

## 판정과 범위

- PASS: 실행한 검사가 기대 조건을 만족.
- FAIL: 검사한 동작이 기대 조건과 다르거나 테스트가 실패.
- BLOCKED: 필수 도구/환경 등으로 필요한 실행을 완료하지 못함.
- NOT RUN: 해당 검사를 실행하지 않음.

실행 결과는 선택한 범위의 결과다. 요구사항 전체 완료나 사용자 확인을 자동으로
뜻하지 않는다. 필수 검사 누락, timeout, 발견 테스트 0개는 성공으로 처리하지 않는다.
테스트 프레임워크의 discover 경로가 맞는지 확인한다.

## 프로젝트 전용 recipe

[verification template](../../templates/verification.md)을 실제 명령과 동작으로 채운다.
readiness는 프로세스 존재가 아닌 사용 가능한 상태다. UI는 실제 입력/클릭을 거치고,
저장/다운로드는 별도로 결과를 읽는다. API와 UI가 같은 값이어도 함께 틀릴 수 있으므로
작은 독립 정답과 비교한다. 외부 경계 mock은 용도를 명시하고 실제 통합과 구분한다.

## 최종 확인

`final-check.py --help`를 읽고 최신 report와 필수 파일을 지정한다. 이 명령은 외부
제출을 자동으로 수행하지 않는다. 필수 파일 존재 외에도 문제의 저장 경로·형식·실행법,
코드 변경 이후 증거의 신선도, 미완료와 사용자 확인 상태를 메인이 판단한다.

한 기능을 고친 뒤 원래 reproducer와 영향받는 회귀를 실행한다. 추가 변경·실패·
불확실성이 없으면 전체 suite를 다시 돌리지 않는다.

## Fingerprint의 범위와 한계

runner의 source fingerprint는 프로젝트 파일(미추적 파일 포함)을 보수적으로 읽되
`.harness`, 캐시, 빌드 결과 등 runtime 디렉터리를 제외한다. 이는 현재 소스의 식별자이며
데이터 신뢰성이나 완전한 freshness의 증명이 아니다. 외부 경로의 데이터, symlink의
대상 내용, DB 상태, 원격 API 응답, 실행 중인 오래된 서버 메모리는 이 hash만으로
확인되지 않는다. 프로젝트별 recipe에 dataset 경로·크기·내용 hash/버전·snapshot ID 등
해당 입력을 재현할 식별자를 별도로 남긴다. 실제 서버의 build identity도 확인한다.

대규모 프로젝트를 매번 통째로 해시하는 비용이 클 수 있다. doctor와 실제 작은 실행으로
비용을 확인하고 검증 대상 프로젝트 경계를 적절히 잡는다. 동적 외부 데이터까지 같은
상태였다고 추정하지 않는다. 비용 때문에 검증을 생략하면 미검증으로 표시한다.
