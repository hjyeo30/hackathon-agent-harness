---
name: review-and-challenge
description: Independently challenge a material plan or review an implemented chunk against original requirements and reproducible outcomes.
---

# Independent challenge

## Review contract

Read original requirements and accepted decisions before the implementer's summary.
Identify review mode: plan, code, runtime, or recap evidence. Inspect enough adjacent
code/data to determine actual consumer impact. Do not expand into a general redesign.

This is a product-source read-only role, not a promise of OS sandbox isolation. Use
separate scratch data to run checks; coordinate ownership of any live app/browser.
Do not edit product source, expected results, accepted requirements, or user records.

## Plan review

Check goal alignment, existing evidence, significant missing semantics, scale/resource
assumptions, ownership, and independent verification. Keep only consequential findings.
A proposed risk needs a failure scenario and the smallest useful clarification or spike.
Do not demand exhaustive hardening or a second specification for its own sake.

## Implementation and runtime review

Compare requirements → plan → progress → diff → actual outcome. A well-supported plan
variance within accepted scope is not a defect. Trace at least the critical changed
path and exercise it when possible. Check a relevant counterexample the implementer
may have missed. Read [testing](../../../docs/guides/testing.md) and the applicable
[domain reference](../../../docs/domains/README.md), not all documents.

Inspect observation quality: do logs/metrics/spans locate the failure, does evidence
belong to this code/build/input, and did the command truly exercise the promised path?
Classify product defects, harness defects, and environment blockers separately.
Check for removed assertions, required checks skipped, zero tests, stale server instances,
or screenshots/agent summaries used as substitutes for the actual contract.

## Findings and completion

Each finding includes requirement ID, file/location when relevant, expected vs observed,
reproducer/evidence, practical impact, and minimal correction. Separate must-fix defects
from optional improvements. Reproduce claims when feasible; label inference honestly.
No finding is a valid result. Review counts are not a quality target.

Return [review](../../../templates/review.md) with APPROVE / CHANGES NEEDED /
INCONCLUSIVE and explicit verification gaps. A reachable critical path not exercised
cannot be called verified. Recheck addressed findings and affected behavior; do not
restart the entire review without new changes or concerns.
