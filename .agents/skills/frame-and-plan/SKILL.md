---
name: frame-and-plan
description: Plan a new feature, analysis, migration, or cross-file change from real task evidence; surface consequential domain gaps and define testable chunks.
---

# Frame and plan

## Ground the decision

Read the request, accepted scope, closest instructions, owning code/tests, and raw data
needed to follow one input to one result. Mark facts separately from assumptions.
Use [expert questions](../../../docs/guides/domain-discovery.md) to find missing domain
constraints. Name the concrete failure and scope impact of each retained concern.
Classify concerns as must-address, useful-within-scope, or deferred. Do not transform
all theoretical risks into required functionality.

Ask users about semantics and preferences they own. Resolve observable facts through
inspection, primary documentation, or a bounded experiment. For an unfamiliar/current
external interface, read its official version-specific docs and record the decision
implication. Do not collect links without changing a decision.

## Plan a complete result

When little time remains, compress the plan to the blocking business decisions,
first complete slice, independent oracle, and time reserved for verification and
user inspection. Do not let template completion consume the implementation window.
Expand the durable record only as useful facts and decisions arrive.

Use [implementation-plan](../../../templates/implementation-plan.md) for non-trivial
work. Define requirement IDs, smallest complete user workflow, submission artifacts,
serious alternatives, ownership boundaries, and chunks that can each be demonstrated.
Choose algorithms/data structures against input scale and measured bottlenecks. Read
[large data](../../../docs/domains/large-data.md) when resources affect correctness;
read the relevant language reference only for its touched boundary.

For each important requirement, state an independent oracle and the smallest check
that proves it. Use [testing](../../../docs/guides/testing.md). For a ratio, a small
hand-calculated unequal-size example is often more revealing than random inputs.
For subjective UX, name observable usability criteria and a user check.

Plan observability with [observability](../../../docs/guides/observability.md): select
stages to trace, events to log, and metrics with units that distinguish likely failures.
Connect input identity, code/build identity, run ID, expected result, and evidence path.
Do not require a tracing service or capture secrets/raw records by default.

## Review and agreement

Delegate a focused plan challenge to `hackathon-reviewer` when consequential assumptions
or boundaries merit it. The reviewer gets original requirements and supporting evidence,
not only your preferred design. Resolve blocking findings; keep optional hardening apart.
Present the plan and meaningful tradeoffs to the user. Respect already-granted batch
approval. Unapproved business meaning remains pending even if other work is authorized.

## Output

A grounded plan with required outcomes, chunks, oracle/input rationale, selected checks,
observability, user checkpoints, out-of-scope work, and unresolved decisions.
Do not invent private function names or line-level edits before inspecting code.
Keep this plan as the original baseline; later changes belong in progress records.
