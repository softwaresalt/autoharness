---
problem_type: persona-dispatch-paths
category: agent-install-layout
root_cause: Review persona adapter tables used the retired categorized `.github/agents/review/` and `.github/agents/research/` layout instead of the canonical flat `.github/agents/subagents/` install destination.
tags: [subagents, review-personas, install-harness, plan-review, path-mapping, copilot-review, cross-reference]
shipment: 096-S
feature: 091-F
pr: 238
merged_at: "2026-07-28T06:22:42Z"
---

# Non-Top-Level Agents Install Flat Under `.github/agents/subagents/`

## Problem

Plans and adapter tables can accidentally revive the retired categorized layout
for review personas and researchers:

- `.github/agents/review/<name>.agent.md`
- `.github/agents/research/<name>.agent.md`

That layout is not where generated non-top-level agents are installed. Dispatch
logic that follows those paths looks up nonexistent files and then degrades or
fails even though the persona exists.

## Durable Rule

Every non-top-level agent identity path used by generated skills, adapter tables,
or cross-reference tests must point to the canonical flat destination:

```text
.github/agents/subagents/<name>.agent.md
```

The source templates may still live under categorized template directories such as
`templates/agents/review/` or `templates/agents/research/`; only the installed
artifact identity path is flat.

## 096-S Lesson

The reviewed 096-S plan itself named the retired `review/` and `research/`
installed paths for Unit G. Copilot review caught the mismatch only after the
regression test encoded the same wrong paths. The fix normalized the generated
plan-review adapter table, install-harness persona mapping text, and regression
test expected paths to `.github/agents/subagents/` while leaving template source
paths unchanged.

## Verification Pattern

For persona adapter changes, test both sides:

1. installed identity path keys use `.github/agents/subagents/`
2. source template paths still resolve to the expected categorized template files

Also grep PR-touched surfaces for `.github/agents/review/` and
`.github/agents/research/` before declaring review routing complete.
