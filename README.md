# Hackathon Agent Harness

사용자와 근거 있게 계획하고, 구현자와 검토자가 작업하고, 메인 에이전트가 실제
결과를 사용한 뒤 사용자가 확인하는 해커톤 준비용 도구 모음입니다.
SK하이닉스 AI 해커톤 준비를 계기로 만들었으며 공식 대회 배포물은 아닙니다.

풍부한 예제와 참고 자료 중 **현재 과제에 필요한 것만 선택**합니다. 필수 조건을
먼저 완성하고, 테스트 수보다 오류 발견력과 정답 근거를 중시합니다.

## 처음 시작

```bash
gh repo clone hjyeo30/hackathon-agent-harness
cd hackathon-agent-harness
```

새 과제에서 [START_HERE.md](START_HERE.md)를 에이전트에게 읽히세요.
기존 프로젝트를 준비된 스타터로 대체하지 않습니다.

```text
이 저장소의 START_HERE.md를 읽고 현재 과제에 맞게 적용해줘.
README·기존 지침·코드·데이터를 먼저 확인하고 나와 필수 조건과 계획을 합의해.
구현자와 검토자를 사용하고, 각 기능 묶음은 네가 직접 사용한 뒤 내가 확인하게 해줘.
```

레포 자체를 연습하려면 Python 3.9+에서 다음을 실행합니다.

```bash
python3 scripts/doctor.py --manifest verification.json
python3 scripts/verify.py --manifest verification.json --profile core
```

웹 브라우저 검증은 Node 20+ 및 Chromium 설치가 추가로 필요합니다.
정확한 명령은 [웹 예제](examples/web-filter-export/README.md)를 따르세요.
core 통과를 브라우저 검증 통과로 해석하지 않습니다.

```bash
python3 scripts/verify.py --manifest verification.json --profile browser
```

전체 실행 결과와 독립 검토 상태는 [검증 기록](docs/validation.md)에 남깁니다.
도구의 문서 확인, 실제 로컬 실행, 대회 환경 확인은 서로 다른 상태입니다.

## 운영 흐름

```text
문제·환경 확인 → 사용자와 계획 → 구현자에게 한 묶음 위임
→ 독립 검토 → 메인의 직접 사용 → 사용자 확인 → 다음 묶음
```

- 메인: 사용자 의도·계획·통합·직접 사용·설명.
- 구현자: 합의된 범위의 코드·검증·인계.
- 검토자: 계획 오류·실제 결함·검증 공백·과잉 구현을 근거로 판단.
- 기능 묶음은 파일 개수가 아닌 **끝까지 사용 가능한 동작** 단위입니다.
- 사용자가 전체 범위를 명시적으로 일괄 승인한 작업에는 그 권한을 존중합니다.

## 무엇이 들어 있는가

| 위치 | 용도 |
|---|---|
| [AGENTS.md](AGENTS.md) | 상시 협업·완료·증거 규칙 |
| [.agents/skills](.agents/skills) | 시작·계획·구현·검토·검증·진단·recap |
| [.codex/agents](.codex/agents) | 구현자·검토자 역할 |
| [docs/guides](docs/guides) | 테스트 분배, 관측, 실패 분석, 운영 |
| [docs/domains](docs/domains) | 웹/API/데이터/이미지/ML/모바일 등 선택 참고 |
| [docs/languages](docs/languages) | Python·TypeScript 판단 기준 |
| [docs/tools/catalog.md](docs/tools/catalog.md) | GitHub 도구·MCP 선택과 실제 사용 조건 |
| [templates](templates) | 계획·진행·실패·검증·사용자 확인·recap |
| [examples](examples/README.md) | 합성 입력·정답·고의 결함이 있는 실행 예제 |
| [src/harness](src/harness) / [scripts](scripts) | 반복 가능한 관측·검증·적용 도구 |
| [issues](issues/README.md) | 과제 내부의 판단·진행·실패 기록 공간 |

## 실제 관측과 정답

실행마다 `.harness/runs/` 아래에 요약, stdout/stderr, 사건 로그, 메트릭,
단계 트레이스를 남깁니다. 바깥 명령의 성공과 앱 내부 단계의 정확성은 구분합니다.
`FAIL`, `BLOCKED`, `NOT RUN`을 `PASS`로 바꾸거나 숨기지 않습니다.

정답은 요구사항·손계산·업무 불변조건·독립 검증기에서 가져옵니다.
AI의 완료 선언, 컴파일 성공, HTTP 200만으로 기능 완료를 판정하지 않습니다.

`recap`을 요청하면 실제 기록에서 핵심 동작·선택·수정·검증·한계를 추립니다.
AI가 실행한 검사와 사용자가 직접 확인한 행동을 구분하며 경험을 꾸며내지 않습니다.
AI 사용이 금지된 후속 서술형 단계에서는 사용하지 않습니다.

## 공개와 재사용 경계

모든 예제는 합성 자료입니다. 실제 시험 문제·답안·작업 기록은 이 공개 저장소에
push하지 않습니다. 준비 자료 반입과 답안 외부 전송은 다릅니다.
MCP·스크린샷·외부 통신 등 실제 사용 조건은 [환경 안내](docs/exam-environment.md)를
확인하고 해당 과제의 최신 지침을 따릅니다.

원본 코드와 문서는 MIT입니다. 외부 도구는 각 라이선스를 따릅니다.
출처와 참고한 원리는 [sources.md](docs/sources.md)에 정리했습니다.
