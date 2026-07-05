---
title: "Safe Dark Factory Mode: Deliberation and Direction"
description: "Decision for stashes E6DA0DCC and 67023DBA: add a bounded dark factory mode with local-review-first readiness, explicit merge authorization, brainstorm intake, and operator-visible safety telemetry."
topic: "How should autoharness support full dark factory mode safely?"
depth: "deep"
decision_status: "accepted"
promoted_to: "docs\\plans\\2026-07-04-safe-dark-factory-mode-plan.md"
linked_artifacts:
  - "docs\\plans\\2026-07-04-safe-dark-factory-mode-plan.md"
  - "templates\\agents\\_orchestrator.agent.md.tmpl"
  - "templates\\agents\\.ship.agent.md.tmpl"
  - "templates\\policies\\workflow-policies.md.tmpl"
  - "templates\\instructions\\github-pr-automation.instructions.md.tmpl"
  - "templates\\instructions\\agent-intercom.instructions.md.tmpl"
  - "templates\\skills\\deliberate\\SKILL.md.tmpl"
  - "references\\atv-starterkit\\.github\\skills\\ce-brainstorm\\SKILL.md"
source_stash_ids:
  - "E6DA0DCC"
  - "67023DBA"
backlog_items:
  - "007-DL"
  - "061-F"
  - "061.001-T"
  - "061.002-T"
  - "061.003-T"
  - "061.004-T"
  - "061.005-T"
  - "061.006-T"
  - "061.007-T"
  - "064-S"
tags:
  - "dark-factory"
  - "orchestrator"
  - "local-review"
  - "brainstorm"
  - "merge-approval"
  - "primitive-4"
  - "primitive-5"
  - "primitive-7"
  - "primitive-8"
---

# Safe Dark Factory Mode Deliberation

## Problem Frame

Stash `E6DA0DCC` asks autoharness to teach Orchestrator that prompts such as
`Run pipeline in dark mode` mean the agent harness should run autonomously in a
safe dark factory mode, including PR merge approval ability. The request is not
just a trigger alias: it changes approval semantics, local review authority,
branch protection behavior, and operator visibility.

Stash `67023DBA` asks for the broader operating model: start with substantial
research for a feature or epic, use a brainstorm skill to surface hard questions
and decisions, then hand off to dark mode for autonomous implementation while
performing most review locally and reducing reliance on GitHub Copilot reviews.
The ATV Starter Kit is the requested research input for brainstorm workflow
design.

The two high-priority stashes are one capability because the trigger is unsafe
without the review, brainstorm, merge, safety, and telemetry contract. The medium
CI build-minutes stash `8DBD43A1` is intentionally not grouped: it concerns CI
workflow cost controls, does not define dark-mode authority, and can ship later
without affecting the dark factory contract.

## Research Findings

### autoharness surfaces

- `templates\agents\_orchestrator.agent.md.tmpl` already owns trigger phrases,
  Stage to Ship routing, sequential execution, planning-overlap rules, and
  P-016 branch/worktree constraints.
- `templates\agents\.ship.agent.md.tmpl` already owns implementation execution,
  local review, PR lifecycle, CI, runtime verification, and operator-approved
  merge behavior.
- `templates\policies\workflow-policies.md.tmpl` currently defines P-014 local
  review readiness and explicit operator approval, P-016 no parallel
  branch/worktree execution, P-009 merge-commit-only, and P-005 violation
  telemetry. A dark factory mode needs a new policy contract after P-016 rather
  than an implicit exception to those policies.
- `templates\instructions\github-pr-automation.instructions.md.tmpl` already
  frames Copilot review as optional advisory shadow review by default and makes
  local review readiness the required pre-merge gate.
- `templates\skills\deliberate\SKILL.md.tmpl` says autoharness replaced the
  earlier brainstorm entry point with a richer deliberate protocol, so a new
  brainstorm surface must either be a deliberate-compatible wrapper/alias or a
  deliberately separate intake skill with a clear handoff contract.

### ATV Starter Kit input

- `references\atv-starterkit\README.md` presents a compound flow:
  `/ce-brainstorm` -> `/ce-plan` -> `/ce-work` -> `/ce-review` ->
  `/ce-compound`, with `/lfg` as the full autonomous pipeline.
- `references\atv-starterkit\.github\skills\ce-brainstorm\SKILL.md` frames
  brainstorm as deciding WHAT and WHY before planning HOW. It uses scope
  classification, one-question-at-a-time dialogue, context scanning, pressure
  tests, requirements with stable IDs, success criteria, scope boundaries, and
  document review before planning.
- `references\atv-starterkit\DOCS.md` shows the value of local review and a
  compound knowledge loop while preserving explicit safety guardrails.

## Options Evaluated

### Option A: Minimal trigger alias

Add `Run pipeline in dark mode` as a synonym for `run pipeline` and let existing
policies continue to govern behavior.

- **Pros:** Smallest implementation.
- **Cons:** Unsafe. Merge approval, admin fallback, review authority, and dark
  mode audit semantics remain implicit. It would create accidental policy
  exceptions instead of a safe mode.

### Option B: Policy-first bounded dark factory mode

Define a first-class dark factory autonomy contract first, then weave trigger
handling, brainstorm handoff, local review, merge approval, admin fallback,
telemetry, and verification through Orchestrator, Ship, skills, and docs.

- **Pros:** Makes autonomy explicit, auditable, and bounded. Preserves P-001,
  P-014, P-016, P-009, and branch protection. Allows local-review-first
  operation while reducing remote shadow-review reliance.
- **Cons:** Requires multiple coordinated template and installed-mirror updates.

### Option C: Local-review migration only

Reduce Copilot review reliance and strengthen local review readiness, but do not
add dark mode.

- **Pros:** Useful and lower risk.
- **Cons:** Does not satisfy the requested autonomous handoff and merge approval
  ability.

### Option D: Unchecked autonomous factory

Let the agent run, review, and merge without additional gates after the trigger.

- **Pros:** Maximum autonomy.
- **Cons:** Rejected. It conflicts with P-014, branch protection, operator trust,
  and the safety model of autoharness.

## Decision

Adopt **Option B**.

The next execution slice should define a policy-level dark factory autonomy
contract before implementation tasks depend on it. The expected policy slot is
P-017, but Ship can confirm the final ID during implementation. The contract
should make dark mode an explicit, bounded, auditable operating mode rather than
an informal instruction to skip approvals.

## Dark Factory Contract Direction

### Trigger semantics

- Canonical trigger: `Run pipeline in dark mode`.
- Acceptable explicit alias: `Run pipeline in dark factory mode`.
- Do not infer dark mode from vague words such as `autonomous`, `go fast`, or
  `run everything`.
- Activation must echo the selected scope, whether merge approval is
  pre-authorized, whether admin fallback is allowed, and the stop conditions.

### Scope semantics

- Dark mode remains bound by P-001: one release unit through merge and required
  closure before another Ship release unit starts.
- Dark mode remains bound by P-016: no parallel implementation branches or
  worktrees. Stage planning overlap is allowed only when P-016 allows it.
- The mode applies to the selected stash group or queued shipment set. It must
  not silently expand scope to unrelated stash items.

### Brainstorm handoff

The desired operator workflow is:

```text
research context -> brainstorm hard questions -> requirements/decisions
                -> impl-plan/harvest -> dark-mode Stage/Ship execution
```

The brainstorm surface should reuse ATV's useful design patterns while fitting
autoharness:

- classify scope before ceremony;
- scan existing instructions and relevant artifacts;
- ask one question at a time when interaction is available;
- capture stable requirement IDs, scope boundaries, success criteria, decisions,
  assumptions, and deferred planning questions;
- run or define a document-review pass before handoff;
- feed `impl-plan`, `plan-review`, and `harvest` without forcing implementation
  details into the brainstorm artifact.

### Local review and shadow review

- Local review readiness remains the authoritative merge gate under P-014.
- Dark mode cannot merge with unresolved P0/P1 findings.
- `READY_WITH_FOLLOWUPS` is allowed only with explicit residual-risk notes or
  follow-up item IDs.
- GitHub Copilot or other hosted review should be advisory shadow review by
  default in dark mode, not a required dependency, unless the operator elevates
  it for a specific shipment.

### Merge approval and admin fallback

Dark mode may satisfy the operator approval signal for a bounded shipment only
after all required gates pass:

- local review readiness covers the current HEAD;
- CI/check requirements are green or explicitly non-applicable;
- P-009 merge-commit-only is satisfied;
- P-016 worktree topology is clean;
- branch protection does not report a hard block that the contract says must
  stop execution.

Admin fallback must be explicit and fail closed. If the repository requires a
human review, unresolved conversation, or protected-branch bypass and dark mode
has not explicitly been granted admin fallback authority, Ship must halt with an
operator-visible reason. If fallback is granted, the attempt must be logged as a
first-class audit event and still cannot bypass local readiness, P-009, P-016,
secrets safety, or scope boundaries.

### Safety, telemetry, and operator visibility

Dark mode must emit self-contained progress and audit records, especially when
`agent-intercom` is installed. Minimum events should include:

- `DARK_MODE_START`
- `DARK_MODE_SCOPE`
- `BRAINSTORM_HANDOFF_READY`
- `LOCAL_REVIEW_READY`
- `DARK_MODE_MERGE_AUTHORIZED`
- `ADMIN_FALLBACK_ATTEMPTED`
- `DARK_MODE_HALTED`
- `DARK_MODE_COMPLETE`

Stop conditions include scope expansion, destructive action requiring approval,
failed local readiness, missing current-HEAD review coverage, branch/worktree
violations, secrets exposure risk, unavailable required tools with no fallback,
ambiguous branch protection/admin state, and any P0/P1 review finding.

## Backlog Harvest

- Parent feature: `061-F` — Safe dark factory mode orchestration.
- Child tasks: `061.001-T` through `061.007-T`.
- First queued shipment: `064-S` — Dark factory autonomy policy contract.
- Shipment `064-S` intentionally contains only `061.001-T`; it excludes parent
  feature `061-F` to avoid partial-feature cascade risk and to define the policy
  contract before implementation tasks depend on it.

## Rejected Grouping

Stash `8DBD43A1` stays active. It is a medium-priority CI cost-control item
about build workflow conditions. It has no dependency on the dark factory mode
contract and should be staged separately.

## Stage Review Outcome

Stage self-reviewed the plan and backlog structure for execution readiness:

- Every child task is scoped to one domain and approximately two hours of human
  work.
- All tasks have a covering parent feature.
- Downstream tasks depend on `061.001-T`, the policy/contract slice.
- The queued shipment contains the first execution-ready slice only.
- No source, config, template, branch, worktree, build, test, lint, or PR action
  was performed during staging.
