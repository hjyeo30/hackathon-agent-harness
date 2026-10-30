# 출처와 참고 범위

확인일: 2026-10-31. 링크는 원 저자/공식 프로젝트 문서입니다. 이 kit의 코드와
문서는 직접 작성했으며 외부 구현을 통째로 vendor하지 않습니다. 도구를 추가하면
그 프로젝트의 라이선스와 배포 조건을 별도로 따릅니다.

## Codex

- [Skills](https://learn.chatgpt.com/docs/build-skills): 이름·설명으로 발견하고 필요할 때
  본문·참고 자료를 읽는 구조, repository skill 위치를 참고했습니다.
- [AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md): 프로젝트 지침
  발견 경로를 확인했습니다. 하위 폴더에 Clone했다는 이유만으로 자동 적용된다고 하지 않습니다.
- [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): custom TOML,
  부모 설정 상속과 역할 지침/실제 권한의 차이를 확인했습니다.
- [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference):
  선택형 MCP 설정의 필드를 참고했습니다. 현장 버전에서 동작 확인이 필요합니다.
- [Rethinking skills and prompts](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
  (2026-09-11): 스킬의 범위를 좁히고 조건별 자료를 선택하는 원리. 특정 모델의 능력에
  대한 설명을 다른 대회 모델의 성능 보장으로 옮기지 않았습니다.

## pstack

- [Guide](https://github.com/cursor/plugins/tree/main/pstack/docs/guide): 상황별 절차를 선택하는
  생각을 참고했습니다. Cursor의 라우터·swarm·shipping 절차를 복제하지 않습니다.
- [sharpen](https://github.com/cursor/plugins/blob/main/pstack/skills/sharpen/SKILL.md):
  사용자가 말하지 못한 전문적 고려·원자료·독립 판정 기준을 드러내는 질문.
- [create-verification-skill](https://github.com/cursor/plugins/blob/main/pstack/skills/create-verification-skill/SKILL.md):
  실제 프로젝트에서 실행·조작·관찰 경로를 찾는 방식.
- [maintain-verification-skill](https://github.com/cursor/plugins/blob/main/pstack/skills/maintain-verification-skill/SKILL.md):
  기능 변경 후 검증법이 낡지 않았는지 확인하는 방식.
- [show-me-your-work](https://github.com/cursor/plugins/blob/main/pstack/skills/show-me-your-work/SKILL.md):
  중요한 결정·이유·증거·결과만 남기는 기록 원리. 별도의 무조건적 cross-model 심사나
  자동 PR 생성은 도입하지 않았습니다.

## 하네스·평가·도구 설계

- [Effective harnesses for long-running agents](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
  (2025-11-26): 작은 기능 진행과 이어받을 수 있는 상태 기록.
- [Harness design for long-running application development](https://www.anthropic.com/research/harness-design-long-running-apps)
  (2026-03-24): 구현과 평가의 분리, 실제 앱 사용, 모델과 작업에 따라 절차 비용 재검토.
- [Demystifying evals for AI agents](https://www.anthropic.com/research/demystifying-evals-for-ai-agents)
  (2026-01-09): transcript의 주장과 환경의 실제 결과 구분, 코드·모델·사람 평가 조합.
- [Writing effective tools for agents](https://www.anthropic.com/research/writing-tools-for-agents)
  (2025-09-11): 목적이 좁고 관찰 결과가 유용한 도구, 실제 작업을 통한 검증.

이 사례들의 대규모 토큰 예산·긴 자율 실행·특정 모델 구성을 180분 작업에 그대로
적용하지 않습니다. 이 kit의 역할 분리와 사용자 확인은 사용자의 명시적인 선호입니다.

## 실행·분석 도구

- [Playwright best practices](https://playwright.dev/docs/best-practices)
- [Playwright CLI](https://github.com/microsoft/playwright-cli), [MCP](https://github.com/microsoft/playwright-mcp)
- [Chrome DevTools MCP](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- [agent-browser](https://github.com/vercel-labs/agent-browser)
- [Hypothesis](https://hypothesis.readthedocs.io/), [fast-check](https://github.com/dubzzz/fast-check)
- [Schemathesis](https://schemathesis.readthedocs.io/en/stable/)
- [Maestro MCP](https://docs.maestro.dev/get-started/maestro-mcp)
- [Pexpect](https://github.com/pexpect/pexpect), [MCP Inspector](https://github.com/modelcontextprotocol/inspector)
- [pandas scale](https://pandas.pydata.org/docs/user_guide/scale.html): 입력 크기와 메모리·중간 복사·분할 가능성 구분.
- [scikit-learn pitfalls](https://scikit-learn.org/stable/common_pitfalls.html): train/evaluation 분리와 전처리 누수.

## 대회 맥락

[COFA Probe](https://www.getcofa.com/ko/probe)의 공개 설명은 결과와 문제 정의·도구 사용·
검증·설명을 함께 보는 일반 방향을 제시합니다. 이 kit는 특정 대회의 상세 배점이나
실제 출제 유형을 안다고 주장하지 않습니다. 개인에게 제공된 안내문 원본과 사적
프로젝트의 코드·문서·경로는 공개 저장소에 포함하지 않습니다.
