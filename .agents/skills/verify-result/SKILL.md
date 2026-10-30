---
name: verify-result
description: Drive a real application, analysis, CLI, or tool output and compare its behavior with independent expectations; maintain the project-specific verification recipe.
---

# Verify the result

## Establish the actual surface

Read the required behavior, known inputs/oracles, existing run commands, tests, and
current app state. Select the surface users really use: browser, CLI, file, API, image,
report, or device. A lower-layer pass cannot prove an unexercised upper layer.
Use [verification](../../../docs/guides/verification.md) and the matching domain guide.

Create or update a project-specific [verification recipe](../../../templates/verification.md)
from observed commands/selectors/routes, never guessed names. Include startup/readiness,
isolation, input, actions, expected output/side effect, evidence and cleanup. Existing
project tooling wins when adequate. After route/label/schema changes, verify the recipe
still reaches the intended behavior; don't turn a regression into a documentation edit.

## Drive, observe, judge

1. Confirm this is the intended app/build/data state, and establish one owner per session.
2. Execute the real critical path with a small independently checkable input.
3. Observe actions AND results: UI/response plus saved state or exported file when relevant.
4. Compare with a hand calculation, accepted business rule, invariant, labelled fixture,
   reference algorithm, or defined human rubric. State the oracle's limitations.
5. Collect relevant logs, metrics and causal spans. Prefer local bounded evidence over
   giant snapshots or external tracing. Separate test doubles from live integration.
6. If failure appears, preserve the reproducer and evidence before cleanup; classify it
   and send concrete feedback. Use `diagnose-failure` when root cause is unclear.
7. After the fix, rerun the reproducer plus affected regression checks once.

## Outcome

Return requirement-by-requirement PASS / FAIL / BLOCKED / NOT RUN with exact commands,
input/code identity, expected vs observed, evidence location and limitations.
Do not promote required missing checks, a zero-test run, or tool failure to PASS.
For example, exit 0 with zero collected tests is BLOCKED in this kit: investigate
test discovery/configuration; the underlying product behavior remains NOT RUN.
This proves a verification problem, not a reproduced product defect.
Record what was checked by the agent separately from what the user has confirmed.

Clean up only processes/scratch state this run owns; keep evidence. The coordinator
then directly uses the critical result and presents [user checkpoint](../../../templates/user-checkpoint.md).
A user confirmation is a separate state and cannot be inferred from silence.
