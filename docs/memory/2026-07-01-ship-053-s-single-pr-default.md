---
type: session-memory
agent: Ship
date: 2026-07-01
session: backlog-to-shipped — single-PR-at-a-time default (autonomous)
shipment: 053-S
tags: [workflow-policy, single-pr, P-001, ship, closure, autonomous]
---

# Ship Session — Single-PR-at-a-time Default (052-F)

## Summary

Shipped shipment **053-S** (feature **052-F**, task **052.001-T**): made
**sequential single-PR-at-a-time** the *explicit documented default* of the
generated harness, consistent with P-001, with parallel/pipelined shipping
labeled explicit opt-in. Documentation/template change only. Merged via PR
[#117](https://github.com/softwaresalt/autoharness/pull/117) as merge commit
`5daa1a67c9a36019a17f76b3adebbb0f0a8e1d5e`.

## What shipped

- `templates/policies/workflow-policies.md.tmpl` — P-001 "Default workflow" note
  (at most one release-unit PR in flight; zero when idle).
- `templates/agents/_orchestrator.agent.md.tmpl` — Execution-Modes preamble;
  "Pipelined Mode (opt-in; when P-001 permits)".
- `templates/agents/.ship.agent.md.tmpl` — P-001 Gate states the single-PR default.
- `templates/prompts/feature-flow.prompt.md.tmpl` — labeled the default.
- `templates/prompts/feature-flow-parallel.prompt.md.tmpl` — labeled opt-in.

## Review

Full adversarial review: two cross-model reviewers (Claude Sonnet 4.6 + GPT-5.4).
No P0/P1. Addressed P2 ("exactly one" → "at most one" cap semantics across the
three files) and P3 (feature-flow prompt now explicitly says "default"). Tests:
126 passed.

## Closure

`backlogit shipment ship 053-S --sha 5daa1a6…` → shipped/archived (052-F +
052.001-T + 053-S). No release obligations (feature; no tag/publish).

## Autonomous session context

Cycle 1 of the autonomous overnight run. Next queued: 054-F (record autoharness
version on install), then 053-F (remove model_routing — needs 053.001-DL
deliberation first), then 051-F (Phase 2 Telemetry & Evaluation Engine).
