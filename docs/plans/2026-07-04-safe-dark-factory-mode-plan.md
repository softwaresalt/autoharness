---
title: "Safe Dark Factory Mode — Implementation Plan"
description: "Plan for stashes E6DA0DCC and 67023DBA: define and implement a bounded dark factory mode with brainstorm intake, local-review-first readiness, PR merge authorization, admin fallback semantics, and safety telemetry."
source_documents:
  - "docs\\decisions\\2026-07-04-safe-dark-factory-mode-deliberation.md"
feature: "061-F"
tasks:
  - "061.001-T"
  - "061.002-T"
  - "061.003-T"
  - "061.004-T"
  - "061.005-T"
  - "061.006-T"
  - "061.007-T"
shipment: "064-S"
source_stash_ids:
  - "E6DA0DCC"
  - "67023DBA"
scope: "harness policy/templates/agent guidance/skills/docs only; no Stage implementation changes"
tags:
  - "dark-factory"
  - "orchestrator"
  - "brainstorm"
  - "local-review"
  - "merge-approval"
  - "operator-visibility"
---

# Safe Dark Factory Mode Implementation Plan

## Problem Frame

autoharness can already route stash through Stage and queued shipments through
Ship, but it does not yet have a safe dark factory mode where an operator can
pre-authorize autonomous Stage -> Ship execution and PR merge approval. Adding
that ability without a policy contract would create ambiguity around P-014 local
review readiness, explicit operator approval, branch protection, admin fallback,
P-016 branch/worktree safety, and telemetry.

The work should create a bounded dark mode that supports this desired flow:

```text
operator research -> brainstorm hard questions -> requirements decisions
                  -> implementation plan and backlog harvest
                  -> dark-mode autonomous Ship execution and merge
                  -> runtime/operational closure and telemetry
```

## Design Direction

Add a policy-first dark factory mode:

1. Define the autonomy contract before trigger or merge implementation.
2. Use the exact trigger `Run pipeline in dark mode` plus a small explicit alias
   set.
3. Keep P-001, P-014, P-016, P-009, and P-005 non-negotiable.
4. Treat local review readiness as authoritative and Copilot/GitHub hosted
   review as optional advisory shadow review by default.
5. Model branch protection and admin fallback explicitly and fail closed when
   authority is absent or ambiguous.
6. Weave safety telemetry and operator visibility through Orchestrator, Ship,
   PR lifecycle, and closure.
7. Use ATV Starter Kit's `/ce-brainstorm` design as input for a brainstorm
   surface that fits autoharness' existing `deliberate` -> `impl-plan` ->
   `plan-review` -> `harvest` chain.

## Requirements Trace

| Requirement | Source | Planned task |
|---|---|---|
| Exact dark-mode trigger and bounded autonomy contract | `E6DA0DCC` | `061.001-T`, `061.003-T` |
| Full PR merge approval ability after safe gates | `E6DA0DCC` | `061.001-T`, `061.005-T` |
| Branch protection and admin fallback semantics | `E6DA0DCC` | `061.001-T`, `061.005-T` |
| Local-review-first workflow with less Copilot review reliance | `67023DBA` | `061.004-T` |
| Brainstorm skill before dark-mode handoff | `67023DBA` | `061.002-T` |
| Safety, telemetry, and operator visibility | both | `061.006-T` |
| Docs and verification surfaces | both | `061.007-T` |

## Task Breakdown

### 061.001-T — Define dark factory autonomy policy contract

Define the governing contract before any implementation task depends on it.
Expected implementation surfaces include `templates\policies\workflow-policies.md.tmpl`,
foundation/constitution surfaces if needed, and installed dogfood mirrors where
autoharness keeps policy guidance in sync.

Acceptance:

- Exact trigger phrases are documented.
- Dark mode is bounded to one P-001 release unit at a time.
- P-014 local review readiness remains mandatory.
- P-016 branch/worktree topology remains mandatory.
- Copilot/GitHub shadow review is advisory by default.
- Admin fallback is fail-closed unless explicitly authorized by the contract.
- Downstream tasks can reference a concrete policy/contract ID.

Width: policy/contract surfaces only.

### 061.002-T — Design brainstorm-led research intake for dark factory handoff

Use ATV Starter Kit as research input and design the brainstorm intake that
precedes dark-mode handoff.

Research references:

- `references\atv-starterkit\.github\skills\ce-brainstorm\SKILL.md`
- `references\atv-starterkit\README.md`
- `references\atv-starterkit\DOCS.md`
- `templates\skills\deliberate\SKILL.md.tmpl`
- `templates\community\skills\brainstorming\SKILL.md.tmpl`

Acceptance:

- Decide whether to create a new brainstorm skill template, a deliberate-compatible
  alias/wrapper, or an extension to `deliberate`.
- Capture the handoff artifact schema: stable requirement IDs, scope boundaries,
  success criteria, decisions, assumptions, and deferred planning questions.
- Explain how brainstorm output feeds `impl-plan`, `plan-review`, and `harvest`.
- Preserve autoharness' current deliberate lineage and backlog linkage.
- Do not implement Orchestrator or Ship dark mode in this task.

Width: brainstorm skill design only.

### 061.003-T — Implement Orchestrator dark-mode trigger semantics

Teach Orchestrator to recognize dark-mode trigger phrases and manage
`DARK_MODE_ACTIVE` state after `061.001-T` defines the policy contract.

Acceptance:

- Canonical trigger `Run pipeline in dark mode` is recognized.
- Explicit alias `Run pipeline in dark factory mode` is recognized.
- Ambiguous autonomy language does not activate dark mode.
- Activation records scope, approval authority, admin fallback setting, and stop
  conditions.
- Normal `run pipeline` behavior remains unchanged.
- Stage and Ship role boundaries remain intact.

Width: Orchestrator trigger/state semantics only.

### 061.004-T — Define local-review-first dark-mode readiness workflow

Update Ship/review/PR lifecycle guidance so dark mode performs most review
locally and treats hosted reviews as advisory by default.

Acceptance:

- Local review readiness for current HEAD is the required merge gate.
- P0/P1 findings block dark-mode merge.
- `READY_WITH_FOLLOWUPS` requires explicit follow-up item IDs or residual-risk
  notes.
- Copilot/GitHub shadow review is optional and advisory unless explicitly
  elevated.
- Shadow-review timeout or unavailability does not block by default.

Width: local review/readiness workflow only.

### 061.005-T — Implement dark-mode merge approval and admin fallback semantics

Implement the pre-authorized merge approval behavior and branch protection/admin
fallback model.

Acceptance:

- Dark mode may satisfy the operator approval signal only for the bounded
  shipment/scope and only after P-014, CI/check, P-009, and P-016 gates pass.
- Normal merge is attempted before any fallback.
- Branch-protection rejection, required reviews, unresolved conversations, and
  missing admin rights are explicit states.
- Admin fallback is attempted only when explicitly authorized by the policy/mode.
- Every merge or fallback attempt records telemetry and PR/readiness evidence.
- No silent bypass of branch protection, local readiness, or merge strategy.

Width: PR merge approval/fallback behavior only.

### 061.006-T — Weave dark-mode safety telemetry and operator visibility

Add the safety and visibility layer so dark mode remains auditable while it runs
autonomously.

Acceptance:

- Define or emit events equivalent to `DARK_MODE_START`, `DARK_MODE_SCOPE`,
  `BRAINSTORM_HANDOFF_READY`, `LOCAL_REVIEW_READY`,
  `DARK_MODE_MERGE_AUTHORIZED`, `ADMIN_FALLBACK_ATTEMPTED`,
  `DARK_MODE_HALTED`, and `DARK_MODE_COMPLETE`.
- `agent-intercom` broadcasts are self-contained enough for a remote operator.
- Degraded visibility is declared, not hidden.
- Destructive actions, scope expansion, secrets exposure risk, failed local
  readiness, ambiguous admin state, and policy violations halt.
- P-005 telemetry records policy violations.

Width: safety/telemetry/operator-visibility surfaces only.

### 061.007-T — Update dark-mode docs and verification surfaces

Finish the weave after behavior is implemented.

Acceptance:

- `AGENTS.md`, foundation templates, harness architecture guidance, install/tune
  guidance, and prompt/skill references describe dark mode accurately.
- Generated-template and dogfooded installed surfaces agree.
- Cross-references resolve.
- No unresolved template variables are introduced.
- Verification covers policy, trigger, review, merge, telemetry, and
  branch/worktree gates.
- The docs note that CI build-minute optimization stash `8DBD43A1` is separate.

Width: docs/verification surfaces only.

## Dependencies

- `061.001-T` blocks all downstream implementation tasks because it defines the
  autonomy contract.
- `061.002-T`, `061.003-T`, and `061.004-T` depend on `061.001-T`.
- `061.005-T` depends on `061.001-T` and `061.004-T`.
- `061.006-T` depends on `061.001-T`, `061.003-T`, and `061.005-T`.
- `061.007-T` depends on `061.002-T`, `061.003-T`, `061.004-T`, `061.005-T`, and
  `061.006-T`.

## Shipment Recommendation

Queue the first shipment with **only `061.001-T`**.

Shipment: `064-S` — Dark factory autonomy policy contract.

Rationale: this is the safest first execution-ready slice because all later
trigger, review, merge, brainstorm, and telemetry work depends on the contract.
The parent feature `061-F` is intentionally excluded from the shipment manifest
to avoid partial-feature closure cascade risk.

## Verification for Ship

Ship should run the smallest relevant validation for each implementation slice,
including documentation/template checks where applicable:

- YAML frontmatter validity for changed Markdown/templates.
- Markdown heading hierarchy checks.
- Unresolved `{{VARIABLE}}` scan for rendered/installed output when templates
  change.
- Cross-reference checks for policy IDs, task IDs, and file paths.
- Search confirming dark mode cannot bypass P-014, P-016, or P-009.
- Scenario review for branch protection/admin fallback states.
- Local review readiness evidence on any PR produced by these tasks.

Stage did not run builds, tests, linters, or template validation in this session,
per role boundary and operator instruction.

## Plan Review

Stage reviewed this plan for execution readiness:

- The two high-priority dark-factory stashes are grouped because the trigger is
  unsafe without brainstorm, review, merge, fallback, and visibility semantics.
- The medium CI stash `8DBD43A1` remains active because it is unrelated to the
  dark factory contract.
- Each child task is single-domain and scoped to roughly two hours of human work.
- The first shipment contains only the policy/contract task.
- No implementation, source/config/template mutation, branch, worktree, build,
  test, lint, or PR action was performed by Stage.

## Remaining Work After 064-S

After `064-S` ships, queue follow-up shipments for:

1. `061.002-T` brainstorm-led research intake design.
2. `061.003-T` Orchestrator trigger/state semantics.
3. `061.004-T` local-review-first readiness workflow.
4. `061.005-T` merge approval/admin fallback semantics.
5. `061.006-T` safety telemetry/operator visibility.
6. `061.007-T` docs and verification surfaces.
