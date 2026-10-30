# Working agreements

This is a preparation kit. Existing task instructions and the user's accepted
scope take precedence over sample workflows. Never import example business
assumptions into a real task without checking their meaning.

## Understand and plan

- Read the task requirements, relevant project instructions, and owning code or
  raw data. Separate observed facts, assumptions, proposals, and user decisions.
- Surface domain constraints the user may not know when they affect correctness,
  usability, resource limits, or verification. Explain their practical impact.
- Agree on required outcomes and an evidence-based plan before substantial new
  implementation. Compare alternatives only when the decision matters.
- Build the smallest complete user workflow first. Do not add speculative layers,
  silent fallback behavior, compatibility shims, or adjacent features.

## Delegate and collaborate

- Main agent owns user dialogue, planning, integration, direct use, and explanation.
- Delegate agreed chunks to `hackathon-implementer`. Use `hackathon-reviewer` for
  consequential plan assumptions and independent review of completed chunks.
- Give delegates the goal, requirement IDs, relevant evidence, ownership, oracle,
  verification path, and stop conditions. Do not delegate vague completion.
- One owner edits product code; one driver owns each shared browser/server state.
  Reviewers do not edit product source. Role instructions are not OS isolation.
- Complete implementation, focused repair, verification, and main-agent direct use
  before presenting a chunk. Wait for user confirmation before the next chunk.
- Explicit user authorization for an entire batch overrides per-chunk approval;
  keep updates and final review. Never ask again for authority already granted.

## Observe, verify, and diagnose

- Define the result, failure to catch, input choice, and independent expected value.
  Select unit/integration/E2E and regression checks by the affected boundary.
- Observe real output and side effects. Build success, HTTP 200, screenshots, and
  agent summaries alone do not prove the accepted behavior.
- Record meaningful logs, unit-bearing metrics, and causal spans where they help
  distinguish failure stages. Use local evidence and small summaries; avoid raw
  secrets, environment dumps, or needless full-dataset logging.
- For failures record expected/observed values, reproduction, evidence, hypotheses,
  root cause or remaining uncertainty, correction, and same-check re-verification.
- Separate product defects, harness defects, and environment blockers. Never obtain
  PASS by inventing data, swallowing errors, weakening assertions, or skipping a
  required check. A required check that did not run is not successful.
- Rerun the reproducer and affected regression checks after fixes. Repeat broad
  validation only for relevant changes or unresolved risk. Stop speculative patching
  when repeated attempts produce no new evidence; investigate or ask a real decision.
- Keep evidence tied to code/build and input identity. Do not use stale results to
  certify changed behavior. Keep the original plan and record deviations separately.

## Explain and hand off

- Distinguish implemented, agent-verified, and user-confirmed states.
- At a checkpoint provide the working result, exact demo path, expected result,
  verification, known limits, and next proposed chunk.
- On recap, use actual code, decisions, verification, and user feedback. Distinguish
  human actions from agent actions; do not invent alternatives, measurements, or
  personal experience. Recap is preparation before any AI-prohibited exam stage.

## Find the relevant material

Start with `START_HERE.md`; select only relevant skills, domain references, and
examples. Follow `.agents/skills/*/SKILL.md` for workflow-specific instructions.
Use `docs/tools/catalog.md` for tool selection and `docs/guides/` for testing and
observability. `docs/implementation-plan.md` and progress record govern kit work.
Core check: `python3 scripts/verify.py --manifest verification.json --profile core`.
Browser checks require the setup in `examples/web-filter-export/README.md`.
