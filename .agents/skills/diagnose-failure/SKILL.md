---
name: diagnose-failure
description: Investigate an unexplained failure, contradictory verification, or repeated ineffective fixes using a minimal reproducer and causal evidence.
---

# Diagnose a failure

## Freeze the useful evidence

Capture the original error, exact command/action, input identity, code/build state,
expected/observed result, relevant run/span IDs, and current modifications. Stop broad
patching when attempts repeat without new evidence. Preserve the failing fixture.
Use [failure record](../../../templates/failure-analysis.md) beside the active issue.

## Locate the first divergence

Classify product / harness / environment before choosing a fix. Confirm the right
instance, input, credentials/configuration presence, and dependency version without
printing secrets. Follow the flow from input to output and find the earliest stage
whose observation differs from the contract. A last error is not necessarily the cause.

Choose one discriminating measurement per hypothesis. Examples:
- UI wrong, API correct → inspect selected state/render conversion and request ordering.
- API and UI agree but wrong → compare aggregate with the independent small fixture.
- OOM → measure peak memory and intermediates; don't merely add retries or workers.
- timeout → split queue, network, processing and write spans rather than raise every timeout.
- test intermittently fails → isolate state/order/clock before adding sleep or retries.

Use [observability](../../../docs/guides/observability.md) and
[debugging guide](../../../docs/guides/debugging.md). Record evidence that supports AND
rejects a hypothesis. Correlation is not proof of cause. Reduce input while preserving
the failure, and distinguish a diagnostic mock from proof of full integration.

## Fix and prove

Make the smallest fix that restores the accepted behavior. Never turn invalid input into
empty success or loosen the expected answer. Rerun the identical reproducer, then the
neighboring regression risk. Add a durable regression only when it prevents a named
recurrence; reuse an existing failing check instead of duplicating it.

If blocked, return a bounded report with known facts, tried hypotheses, unresolved
question, next useful experiment, and the user/environment decision needed. Don't hide
uncertainty behind a root-cause claim. Resume after new evidence or a decision.

## Closeout

Record cause (confirmed or suspected), correction, before/after evidence, regression,
remaining limits, and whether the project verification recipe needs updating. Feed
important decisions to progress/recap; don't invent a narrative for experiments not run.
