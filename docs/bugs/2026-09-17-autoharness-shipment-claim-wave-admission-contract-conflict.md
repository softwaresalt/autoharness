---
chunk_strategy: h1-h2-h3
description: "autoharness integration defect: backlogit ClaimShipment intentionally activates the shipment and every queued manifest member (documented and asserted by TestClaimShipment_ActivatesIncludedScope), while the autoharness P-002.6 wave-admission policy treats any active member at Ship Step 4.0 as an active residual and halts with WAVE_NO_PROGRESS. The two contracts were introduced at different times and never reconciled, so every Ship run over a freshly claimed multi-task shipment hard-stops before building anything. backlogit behaves per its documented and tested contract; the ownership is the autoharness integration."
doc_type: guide
docline:
  author: Stage
  date: 2026-09-17
  status: draft-for-transfer
external_provenance:
  origin_repository: softwaresalt/backlogit
  origin_pull_request: "N/A - authored directly in the backlogit workspace during Stage session stage-2026-09-17-fd0ccb42; not opened as a backlogit-side PR"
  origin_source_path: docs/scratch/bugs/2026-09-17-autoharness-shipment-claim-wave-admission-contract-conflict.md
  note: "origin_source_path is a SOURCE-WORKSPACE path in softwaresalt/backlogit. It does NOT resolve in this repository."
ingested_at: "2026-09-17T00:00:00Z"
schema_version: "1.0"
source: docs/bugs/2026-09-17-autoharness-shipment-claim-wave-admission-contract-conflict.md
title: "autoharness shipment-claim vs wave-admission contract conflict — ClaimShipment activates every member, P-002.6 halts on active residual"
---

> **Transfer note and lifecycle.** This document was authored in the `backlogit`
> workspace but describes an integration defect that is primarily owned by the
> **autoharness harness/policy layer**, not by the `backlogit` binary. It is
> written to be self-contained so it can be copied verbatim into the autoharness
> workspace as a bug report or issue. No fix is applied in `backlogit`, and no
> `backlogit` source, template, or configuration is changed by this report.
> `backlogit` carries only this documentation and a tracking stash entry that
> references this path. The active shipment `149-S`, its members, its checkpoint,
> and its feature branch were not modified while authoring this report.

# autoharness shipment-claim vs wave-admission contract conflict

## Summary

Two contracts that must interoperate disagree about what status a shipment's
member tasks hold immediately after the shipment is claimed:

* `backlogit` `ClaimShipment` moves a queued shipment to `active` **and marks
  every included queued work item `active`** in the same operation. This is the
  documented and tested behavior.
* The autoharness `P-002.6` wave-admission policy (Ship Step 4.0) treats **any
  member still `active` at wave admission** as an unfinished claim from a prior
  wave — an "active residual" — and halts the entire release unit with
  `WAVE_NO_PROGRESS` (detail: `active residual`).

The result is a deterministic deadlock: the Ship agent's own required claim step
puts every task into exactly the status that its own required admission step
refuses to schedule over. A multi-task shipment can never reach its first wave.

Primary ownership is the **autoharness integration**. `backlogit` is behaving
exactly as its documented and unit-tested contract specifies; the harness policy
was authored later against an assumption about post-claim task status that the
`backlogit` claim contract does not satisfy.

## Impact

* **Severity: high.** Every Ship run over a freshly claimed shipment that
  contains two or more member tasks hard-stops at Step 4.0 before any harness is
  generated, any task is claimed, or any code is built.
* The stop is fail-closed and correct **given the installed policy** — Ship must
  not reset member statuses, amend the manifest, or weaken the active-residual
  gate, so it has no in-role recovery and must return the release unit to Stage
  or the operator.
* Work stalls at the handoff boundary. The shipment is `active`, its branch and
  worktree exist, and its checkpoint is written, but no forward progress is
  possible without a governed correction.
* The defect is silent until claim time: schedule construction, scheduler
  simulation (`WAVE_SIM_OK`), and the repo-wide compile check all pass, so the
  halt surfaces only after the operator has committed a branch and a claim.

## Reproduction Sequence

1. Stage assembles a shipment with a covering feature and multiple queued member
   tasks (for `149-S`: covering feature `168-F` plus 19 task members
   `168.001-T` through `168.018-T` and `168.020-T`). All members are `queued`.
2. Ship begins its pipeline and reaches the claim step.
3. Ship runs `backlogit shipment claim 149-S`.
4. `ClaimShipment` moves the shipment to `active` and, in the same all-or-nothing
   operation, moves the covering feature and every queued member task to
   `active`.
5. Ship advances to Step 4.0 (Wave Admission) and takes the first live snapshot
   of the frozen task set `M`.
6. The census shows `count(M) = 19`, `terminal_success = 0`, `queued = 0`,
   `active = 19`, `blocked = 0`, `unsupported = 0`.
7. Step 4.0 item 4 fires: any member still `active` at wave admission is an
   active residual, and admission halts with `WAVE_NO_PROGRESS`
   (detail: `active residual`), listing all 19 active members.
8. Ship halts fail-closed with no in-role recovery and returns the release unit
   to Stage or the operator.

## Expected vs Actual Behavior

**Expected:** After a shipment is claimed, its member tasks are available to the
wave scheduler as `queued`, and the scheduler activates only the ready frontier
`ready_k` (queued members whose every dependency has reached a terminal-success
status). Wave 1 admits the tasks with no unfinished dependencies; later waves
admit the rest as dependencies complete.

**Actual:** The claim eagerly activates every member task, so at the very first
wave admission the entire frozen set is `active`. The scheduler correctly refuses
to admit a wave over `active` members, and the release unit stops before wave 1.

## Root Cause

Two independently correct contracts overlap on the meaning of member `active`
status and were never reconciled:

* **`backlogit` claim contract.** `internal/core/shipment_lifecycle.go` documents
  `ClaimShipment` as "moves a queued shipment to active and marks the included
  work scope active," and implements exactly that: it transitions the shipment,
  then walks every included item and calls
  `setArtifactStatus(..., models.StatusActive, "shipment claimed")` for each
  member still `queued`, with cascade activation of parents. The unit test
  `TestClaimShipment_ActivatesIncludedScope`
  (`internal/core/shipment_test.go`) asserts that after a claim both the member
  task and its covering feature are `StatusActive`. All-member activation is a
  guaranteed, tested property, and other callers may depend on it.
* **autoharness wave-admission contract.** `.github/policies/workflow-policies.md`
  `P-002.6` defines `ready_k = { t in queued : deps(t) subset of terminal_success }`
  and states that "a member still carrying `active` at wave admission is a claim
  from a prior wave that never reached `done` — a stalled or abandoned build, not
  progress," halting with `WAVE_NO_PROGRESS` (detail: `active residual`). The Ship
  agent encodes this at `.github/agents/_ship.agent.md` Step 4.0 item 4.

The wave scheduler's `active`-means-in-flight-build assumption is sound in
isolation: within a wave, `active` marks a task the agent has claimed and is
building. But the claim operation stamps `active` on tasks the agent has **not**
started, so the scheduler cannot distinguish "claimed by this claim call, never
started" from "started in a prior wave and stalled." The two states are
observationally identical, and the policy correctly refuses to guess.

The temporal gap is the mechanical cause: the claim semantics date to April 2026;
the conflicting active-residual wave policy was added in August 2026. The later
policy was written against an assumed post-claim state (members remain `queued`
until the scheduler activates them) that the pre-existing claim contract does not
produce, and no reconciliation shipped between the two.

## Historical Recurrence

This is not a first occurrence. Shipment `140-S` hit the identical defect on
2026-09-10 at the same Step 4.0 wave-admission gate: after claim, all eight
members `158.001-T` through `158.008-T` were `active`, and admission halted with
`WAVE_NO_PROGRESS` (detail: `active residual`). That session captured deferred
stash entry `CC0EBB59` for "the shared shipment-claim/wave-scheduler contract
mismatch" and returned the release unit for a governed correction.

The shared defect was never resolved, so it recurred on `149-S` on 2026-09-17
with 19 active members. The recurrence confirms the root cause is structural and
shared across shipments, not specific to any one manifest. Evidence:

* `docs/archive/memory/2026-09-10-ship-140-s-wave-admission-halt.md`
* `docs/memory/2026-09-17-ship-149-s-wave-no-progress.md`

`CC0EBB59` is referenced here as prior evidence only. It is not retrievable in
the current workspace's active stash (it lives in the `140-S` branch history);
this report does not edit or archive it.

## Affected Contracts and Surfaces

* `internal/core/shipment_lifecycle.go` — `ClaimShipment` documentation and
  implementation (all-member activation, cascade to parents, all-or-nothing
  rollback).
* `internal/core/shipment_test.go` — `TestClaimShipment_ActivatesIncludedScope`
  pins member and feature activation as a contract.
* `.github/policies/workflow-policies.md` — `P-002.6` wave model
  (`ready_k`, `terminal_success`, active-residual halt, `WAVE_NO_PROGRESS`).
* `.github/agents/_ship.agent.md` — Step 4.0 wave admission (item 4 active
  residual halt) and Step 4.6 convergence (active-member halt).
* Any non-Ship caller of `ClaimShipment` that relies on member tasks being
  `active` immediately after claim — the reason the claim semantics must not be
  changed casually.

## Safety Implications

* **Ignoring active tasks is not an acceptable resolution.** Silencing the
  active-residual halt — for example, treating `active` members as schedulable or
  as satisfied — would destroy DAG frontier correctness: the scheduler could
  admit or complete tasks whose dependencies are not terminal, and it could mask
  a genuinely interrupted or stalled prior-wave build. The active-residual gate
  is a real safety invariant, not noise. The fix must make the post-claim state
  truthful, not blind the gate.
* **The claim contract must remain trustworthy for its other consumers.** Because
  other callers may depend on all-member activation, weakening or silently
  redefining `ClaimShipment` risks breaking unrelated flows. Any change to shared
  claim semantics must be explicit, versioned, and reviewed.
* **Fail-closed behavior is preserved.** The current halt is safe; it stops
  forward motion rather than proceeding on an ambiguous frontier. The correction
  should keep that property while removing the false-positive residual.

## Recommendation

Adopt the direction of **separating shipment ownership activation from task
execution activation**. Claiming or activating a shipment should establish
ownership and move the shipment record to `active`, but should **leave member
tasks `queued`**. The wave scheduler then remains the sole authority that
activates tasks, and it activates only `ready_k`. This makes member `active`
status mean exactly one thing again — "a wave has claimed this task and a build
is in flight" — which is precisely what the active-residual gate assumes.

Do **not** casually change the existing `backlogit` `ClaimShipment` semantics,
because other callers may rely on all-member activation. Evaluate two resolution
options and choose between them only after a spike:

* **Option A — autoharness-only, using existing governed operations.** If
  `backlogit` already exposes governed status operations that can return the
  claimed shipment's member tasks to `queued` (or claim ownership without
  activating members) **while preserving every claim, topology, and event
  invariant** — rollback safety, parent-status cascade correctness, membership
  locks, and emitted lifecycle events — then the correction lives entirely in the
  autoharness harness/policy layer and calls those existing operations. This
  option changes no `backlogit` contract.
* **Option B (preferred if A is insufficient) — explicit backlogit
  shipment-only claim operation or activation-scope option.** If existing
  operations cannot separate ownership activation from member activation without
  violating an invariant, add an explicit `backlogit` capability: either a
  shipment-only claim operation, or an activation-scope option on the claim that
  selects "shipment record only" versus the current "shipment plus all members."
  The existing all-member behavior remains the default (or a named mode) so
  current callers are unaffected, and the harness opts into the shipment-only
  scope.

**Require an API and contract spike before implementation.** The spike must
determine whether Option A's existing operations preserve all claim, topology,
and event invariants, or whether Option B's new capability is required, and must
confirm the chosen path does not regress `TestClaimShipment_ActivatesIncludedScope`
or any other caller. Implementation must not begin until the spike resolves which
option is correct.

**Secondary planning and dependency gap.** Beyond the primary contract conflict,
later shipments were queued and claimed without carrying an explicit dependency
on the known enabling correction that `140-S` had already surfaced. The shared
defect was recorded (`CC0EBB59`) but subsequent release units did not declare a
blocking dependency on its resolution, which is why `149-S` was allowed to reach
the same halt. Future shipments that depend on the corrected claim/activation
model should declare an explicit dependency edge on the correction's release unit
so they are not scheduled ahead of it.

## Acceptance Criteria

* After a shipment is claimed, the shipment record is `active` and every member
  task is `queued` (under the chosen resolution mode).
* Ship Step 4.0 wave admission over a freshly claimed multi-task shipment admits
  wave 1 (`ready_k` non-empty) instead of halting with `WAVE_NO_PROGRESS`
  (active residual).
* The wave scheduler is the only surface that transitions a member task to
  `active`, and it does so only for `ready_k`.
* A member that is genuinely `active` from a stalled prior-wave build still halts
  admission with `WAVE_NO_PROGRESS` (detail: `active residual`) — the gate is not
  weakened, only the false positive is removed.
* Existing `ClaimShipment` callers that rely on all-member activation retain that
  behavior (default mode unchanged, or an explicit opt-in for the new scope).
* No `backlogit` claim, topology, or lifecycle-event invariant regresses:
  all-or-nothing rollback, parent-status cascade, membership locking, and event
  emission all still hold.
* The correction ships as a separately reviewed release unit and is verified
  before any operator-confirmed resumption of a blocked shipment such as `149-S`.

## Test Matrix

| Scenario | Precondition | Action | Expected result |
|---|---|---|---|
| Multi-task claim, new scope | Shipment + N queued member tasks | Claim under shipment-only scope | Shipment `active`; all members `queued` |
| Wave 1 admission after claim | Members `queued`, some deps terminal | Ship Step 4.0 | `ready_k` non-empty; wave admitted; no `WAVE_NO_PROGRESS` |
| Genuine active residual | A prior-wave member left `active` | Ship Step 4.0 | Halt `WAVE_NO_PROGRESS` (active residual) — gate still fires |
| Legacy all-member activation | Existing caller expecting active members | Claim under default mode | All members `active` (unchanged behavior) |
| Rollback safety | Mid-claim item load/activate failure | Claim | Shipment and any activated items restored to pre-claim state |
| Parent cascade | Covering feature over member tasks | Claim (either mode) | Feature status consistent with member statuses; no torn parent |
| Scheduler activation authority | Members `queued` post-claim | Wave loop advances | Only `ready_k` members become `active`; others stay `queued` |
| Regression pin | Existing unit contract | Run `TestClaimShipment_ActivatesIncludedScope` | Passes under default mode; new mode covered by a new test |
| Dependency gating | Shipment depends on correction release unit | Attempt claim before correction ships | Blocked by explicit dependency edge, not by Step 4.0 halt |

## Migration and Compatibility Risks

* **Shared-contract breakage.** Changing default claim behavior would break any
  caller that expects members `active` after claim. Mitigation: keep all-member
  activation as the default and gate the new behavior behind an explicit
  operation or scope option (Option B), or keep the change entirely in the
  harness (Option A).
* **Test contract drift.** `TestClaimShipment_ActivatesIncludedScope` encodes the
  current behavior. If Option B introduces a new mode, add a parallel test for the
  shipment-only scope rather than altering the existing assertion, unless the
  default is deliberately and reviewably changed.
* **In-flight blocked shipments.** `149-S` (and any other shipment already claimed
  into the all-active state) needs a governed transition of its members back to a
  policy-admissible state as part of adopting the fix. This transition must be
  performed through the governed backlog path by Stage or the operator, not by
  Ship, and not by this documentation task.
* **Event and audit consumers.** Any consumer of claim-time lifecycle events that
  assumes member-activation events fire at claim must tolerate their absence (or a
  new event shape) under the shipment-only scope.

## Rollback Approach

* If the correction is delivered as an opt-in `backlogit` capability (Option B),
  rollback is reverting the harness to the default (all-member) claim scope; the
  new capability remains dormant and no caller is affected.
* If the correction is harness-only (Option A), rollback is reverting the harness
  policy/agent change; `backlogit` is untouched, so there is nothing to revert on
  the binary side.
* Any in-flight member status transitions applied to unblock a specific shipment
  are recorded through the governed backlog path and can be re-applied or reverted
  by the same path, preserving auditability.
* Because the fix is a separately reviewed release unit, its revert is isolated
  from unrelated shipment work.

## Recommendation Summary

Separate shipment ownership activation from task execution activation so member
tasks stay `queued` after claim and only the wave scheduler activates `ready_k`.
Prefer a harness-only correction (Option A) if existing governed operations
preserve every claim, topology, and event invariant; otherwise add an explicit
`backlogit` shipment-only claim operation or activation-scope option (Option B)
with the current all-member behavior preserved as the default. Do not weaken the
active-residual gate. Gate implementation behind an API and contract spike, ship
the correction as a separately reviewed release unit, and only then resume any
blocked shipment such as `149-S` under operator confirmation.
