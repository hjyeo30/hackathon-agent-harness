---
name: implement-chunk
description: Implement one agreed behavior chunk, instrument relevant boundaries, run focused verification, and return reproducible evidence to the coordinator.
---

# Implement one chunk

## Start contract

Read the delegated requirement IDs, plan, accepted decisions, relevant code/tests, and
closest instructions. Confirm the plan matches the current tree. Receive explicit
ownership of files, app instance/port, data directory, and any browser session.
Do not start the next chunk or delegate recursively.

## Execute

Follow the lightest existing project pattern. Build the required user behavior before
optional polish. Do not add speculative abstractions, hidden compatibility paths,
fabricated data, swallowed errors, or fallback success responses.

Use [testing](../../../docs/guides/testing.md) to select checks. A deterministic bug or
calculation often benefits from a failing example first; do not enforce TDD for every
visual or documentation edit. If reporting a red-to-green cycle, actually observe both.

Instrument relevant stages using [observability](../../../docs/guides/observability.md).
Record a useful error category and context at the boundary that owns it; don't duplicate
an entire traceback at every layer. Capture counts/time/resources only where those
measurements answer a concrete correctness or performance question.

Run the check against real behavior. Save the command, input, expectation, result,
code/build identity, and logs/metrics/trace pointers. The kit's
[verify runner](../../../scripts/verify.py) can collect command evidence from a manifest;
read its `--help` and the [verification guide](../../../docs/guides/verification.md).
It does not infer business correctness from a zero exit code.

## Failure and change

Classify failure as product, verification, or environment. Reproduce and narrow the
first divergence; use `diagnose-failure` when attempts lack new evidence. After fixing,
rerun that reproducer and affected regression checks. Avoid repeated full suites on
unchanged code. Never weaken an accepted assertion to manufacture PASS.

Improve private implementation details when evidence supports a better path. Record
why in [progress](../../../templates/implementation-progress.md). Return to the main
agent for changes to accepted semantics, scope, a significant dependency, or authority.
Do not silently rewrite the plan baseline.

## Handoff

Use [handoff](../../../templates/handoff.md): changed requirements/files, exact startup
and verification commands, real outcomes, evidence, deviations, remaining limitations,
and one short user demo. Implementation-complete is not agent-verified or user-confirmed.
Do not commit, publish, or submit unless that action is within explicit task authority.
