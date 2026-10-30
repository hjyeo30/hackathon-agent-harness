---
name: hackathon-start
description: Adapt this preparation kit to a new or existing hackathon task, inspect its real environment, and begin a grounded planning conversation.
---

# Start a task

## Input and scope

Use the actual user request and task workspace. Public-kit examples are learning materials,
not requirements or a replacement application. The task's README, submission rules,
existing project instructions, and the user's accepted intent govern the solution.

## Inspect before adapting

1. Read the task README and closest applicable instructions; identify required artifacts,
   paths, time budget, and accepted authority. Preserve unrelated user changes.
2. Inspect the actual entry point, relevant source/tests, and a small data sample.
   For an existing application, attempt its documented startup and one focused check.
   Distinguish pre-existing failures from changes you later introduce.
3. Check the available runtime, Codex/subagent/MCP capabilities, browser route, and resource
   constraints. A connected MCP is not proof that its browser or tool works.
4. Select only relevant [domain references](../../../docs/domains/README.md). Do not load
   the entire catalog. Separate facts, assumptions, proposed decisions, and user decisions.
5. If asked to install, inspect [bootstrap](../../../scripts/bootstrap.py) `--help`, preview
   its plan, then apply within the user's existing authorization. Never replace task
   AGENTS/config/package files with kit defaults. A collision requires explanation, not
   an alternate hidden copy. Confirm discoverable skills/agents and usable reference paths.

## First conversation

Restate the smallest valuable outcome. Present the two or three unresolved choices that
would materially change it, with a recommended option and consequences. Investigate
observable technical facts yourself. Ask the user about business meaning and priority.
Continue independent inspection while waiting; do not implement dependent choices.

Hand the accepted scope to `frame-and-plan`. For a small established local fix, use a
concise inline plan; for a new multi-file task, use a durable plan. An explicit current
approval for the whole task must not be reset to unapproved by this workflow.

## Output and stopping point

Return: required outcome and submission paths; current stack and baseline; activated
references/tools; unresolved consequential questions; first complete chunk; exact next
verification route. Default checkpoint is plan agreement before substantive new
implementation. See [workflow](../../../docs/guides/workflow.md) and
[first-prompt examples](../../../docs/guides/first-prompt.md).

Do not imply browser screenshots, extra providers, external uploads, or public Git pushes
are allowed merely because an example mentions them. Exam artifacts remain local.
