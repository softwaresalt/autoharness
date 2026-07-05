---
title: "Dark Factory Brainstorm Intake Design"
description: "Design for a brainstorm-led requirements intake that precedes dark factory handoff while preserving autoharness' deliberate/impl-plan/harvest lineage."
topic: "How should autoharness support brainstorm-led research intake before dark factory execution?"
decision_status: "accepted"
source_documents:
  - "docs/decisions/2026-07-04-safe-dark-factory-mode-deliberation.md"
  - "docs/plans/2026-07-04-safe-dark-factory-mode-plan.md"
  - "references/atv-starterkit/.github/skills/ce-brainstorm/SKILL.md"
backlog_items:
  - "061-F"
  - "061.002-T"
tags:
  - "dark-factory"
  - "brainstorm"
  - "requirements"
  - "atv-starter-kit"
  - "deliberate"
---

# Dark Factory Brainstorm Intake Design

## Decision

Add a dedicated **brainstorm intake skill** for dark-factory handoff, but make it
deliberate-compatible rather than a replacement for `deliberate`.

The skill should be a requirements-and-decisions intake surface:

- it answers **what** and **why** before `impl-plan` answers **how**;
- it uses ATV Starter Kit's `/ce-brainstorm` interaction model as the reference
  pattern;
- it writes a durable requirements artifact under `docs/brainstorms/`;
- it may link to or invoke `deliberate` when trade-off analysis is needed;
- it hands a stable artifact to `impl-plan`, `plan-review`, and `harvest`;
- it must not perform implementation, template/source/config mutation, shipment
  claim, PR preparation, or Ship execution.

This preserves autoharness' existing `deliberate -> impl-plan -> plan-review ->
harvest` lineage while giving operators the explicit `/brainstorm` style entry
point they expect before handing work to dark factory mode.

## Why not only extend `deliberate`?

`deliberate` already covers research synthesis, option comparison, and queue
linkage. It is the right primitive for architectural or policy decisions.
However, the dark factory workflow needs a more product-shaped intake that can
produce stable requirements, scope boundaries, success criteria, and hard
questions before autonomous execution.

Extending `deliberate` directly would blur two outputs:

- **Deliberation**: option selection and rationale.
- **Brainstorm**: requirements, success criteria, scope, and handoff readiness.

A dedicated brainstorm skill can reuse deliberate concepts and call deliberate
when needed, while keeping the requirements artifact optimized for downstream
planning.

## ATV Starter Kit patterns to adopt

From `references/atv-starterkit/.github/skills/ce-brainstorm/SKILL.md`:

1. **Scope first**: classify work as lightweight, standard, or deep before
   adding ceremony.
2. **One question at a time**: ask single focused questions, preferably
   multiple-choice when it helps.
3. **Context scan before claims**: read relevant instructions and nearby
   artifacts before saying something exists or is absent.
4. **Pressure-test the problem**: challenge whether the request solves the real
   problem and whether a simpler or higher-leverage framing exists.
5. **Stable requirement IDs**: use `R1`, `R2`, etc. so planning and review can
   cite requirements unambiguously.
6. **Explicit outstanding questions**: separate "resolve before planning" from
   "deferred to planning."
7. **Document review before handoff**: run or define a review pass over the
   requirements artifact before planning starts.

## Autoharness-specific adaptations

### Artifact path

Brainstorm artifacts should live under:

```text
docs/brainstorms/YYYY-MM-DD-<topic>-requirements.md
```

This is distinct from:

- `docs/decisions/` for deliberations and durable decisions;
- `docs/plans/` for implementation plans;
- `.backlogit/` for active work items.

If a workspace config later needs a variable for this path, add it explicitly to
the docs path variable table. Do not hard-code it in generated artifacts without
documenting the variable.

### Artifact frontmatter

The requirements document should use frontmatter that makes handoff state
queryable:

```yaml
---
title: "<topic>"
date: "YYYY-MM-DD"
source_stash_ids: []
source_research:
  - "<repo-relative path or URL>"
scope: "lightweight|standard|deep"
handoff_status: "ready_for_plan|blocked_on_questions|deferred"
dark_factory_ready: false
requirement_ids:
  - "R1"
---
```

### Required sections

```markdown
# <Topic>

## Problem Frame

## Requirements

**<Group>**
- R1. ...
- R2. ...

## Success Criteria

## Scope Boundaries

## Key Decisions

## Assumptions

## Outstanding Questions

### Resolve Before Planning

### Deferred to Planning

## Handoff
```

## Handoff contract

The brainstorm output may enter the rest of the autoharness pipeline only when:

1. `Resolve Before Planning` is empty, or remaining items have been converted to
   explicit assumptions / deferred planning questions.
2. Each non-trivial requirement has a stable ID.
3. Scope boundaries and success criteria are explicit.
4. A document-review pass has completed or is explicitly deferred with rationale.
5. `handoff_status` is `ready_for_plan`.

When ready, the downstream handoff is:

```text
brainstorm requirements doc
  -> impl-plan source document
  -> plan-review
  -> harvest into backlog feature/tasks/shipments
  -> optional dark factory execution under P-017
```

## Dark factory handoff rules

Brainstorm does not activate dark mode by itself. It can mark a feature as a
candidate for dark mode only when:

- the operator used an explicit dark-mode trigger or the Orchestrator has
  already recorded `DARK_MODE_ACTIVE`;
- P-017's activation contract has a bounded scope;
- P-014 local readiness, P-016 branch/worktree topology, P-009 merge strategy,
  and CI/check gating remain mandatory for downstream Ship execution.

The brainstorm artifact should include a `Dark Factory Handoff` note only when
those conditions are satisfied or intentionally planned.

## Skill implementation recommendation

Create a new skill template:

```text
templates/skills/brainstorm/SKILL.md.tmpl
```

Install it as a standard planning skill when Primitive 4 is selected. The skill
should be described as a front-door requirements intake that complements
`deliberate`.

Recommended aliases:

- `brainstorm`
- `dark-factory-brainstorm` (only when dark mode is explicitly in scope)

The skill should reference `deliberate` as the escalation path for deep
trade-off analysis rather than duplicating all deliberation mechanics.

## Non-goals

- Do not implement Orchestrator dark-mode triggers in the brainstorm skill.
- Do not let brainstorm claim shipments or mark backlog items complete.
- Do not let brainstorm create implementation branches or worktrees.
- Do not replace `deliberate`; keep it as the option/rationale decision skill.
- Do not require interactive questions when the operator is unavailable in
  already-authorized dark mode; instead, convert unresolved product questions
  into explicit assumptions or blockers according to the handoff status.

## Verification expectations

Future implementation should verify:

1. The brainstorm skill writes only to `docs/brainstorms/` and optional backlog
   planning artifacts.
2. The skill refuses implementation and Ship execution.
3. Requirements docs contain stable IDs and a `handoff_status`.
4. A requirements doc with unresolved `Resolve Before Planning` items cannot be
   marked `ready_for_plan`.
5. `impl-plan` can accept the brainstorm artifact as a source document.
6. Dark factory handoff text references P-017 and does not weaken P-014, P-016,
   P-009, or CI/check requirements.

## Follow-up implementation surfaces

This design should feed future tasks that add:

- `templates/skills/brainstorm/SKILL.md.tmpl`;
- optional installed mirror under `.github/skills/brainstorm/SKILL.md`;
- install-harness registration in the planning/Primitive 4 skill set;
- docs path guidance for `docs/brainstorms/`;
- Orchestrator dark-mode trigger integration in `061.003-T`;
- final docs/verification updates in `061.007-T`.
