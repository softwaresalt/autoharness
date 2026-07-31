---
title: "Can the Ship workflow mitigate the backlogit queued-with-active-work inconsistency without touching backlogit internals?"
type: spike
date: 2026-07-30
time_box: "2h"
conclusion: "proceed"
confidence: "high"
linked_parent_work_item: null
promoted_to: ["plan"]
plan_artifact: "docs/plans/2026-07-30-ship-claim-integrity-preflight-plan.md"
stash_ref: "6D6CACC1"
tags:
  - "ship-agent"
  - "backlogit-shipment"
  - "claim-integrity"
---

## Goal

Stash entry `6D6CACC1` asks for a "backlogit active→queued transition-guard
hardening": a shipment (observed on `103-S`) stayed `queued` because the build
loop never committed an `active` claim, and recovery required a manual
archived-status surgical fix. The core ask targets backlogit's **own internal**
transition guard/self-repair. This spike answers a narrower, in-repo question:

> **Can the autoharness Ship agent workflow reliably prevent and/or self-report
> the "shipment stays queued while its tasks go active" inconsistency, without
> modifying backlogit internals — and is that mitigation bounded enough to stage
> now?**

## Success Criteria

A sufficient answer demonstrates:

1. Whether the mitigation is implementable **inside this repo** (autoharness
   product templates) versus only in the external backlogit binary.
2. Whether the existing Ship workflow / `shipment-reconcile` skill already covers
   the failure mode (i.e., is this redundant?).
3. The concrete insertion point(s) and mechanism if feasible.
4. A bounded scope estimate (fits the 2-hour rule) or a defer recommendation.

## Scope Constraints

* **Read-only investigation.** No template/source/config mutation, no shipment
  claim, no PR preparation, no Ship execution (Stage P-016 spike exception).
* Time-boxed to 2h; single worktree (no parallel branch/worktree created).

## Investigation Approach

1. Read the Ship agent claim flow in both the installed dogfood instance
   (`.github/agents/_ship.agent.md`) and the product template
   (`templates/agents/_ship.agent.md.tmpl`).
2. Read the `shipment-reconcile` skill template to determine whether its
   pre-mode already detects a shipment-record-status inconsistency.
3. Check the compound learnings library for prior art on backlogit shipment
   status semantics.
4. Confirm where the guard must live (autoharness vs backlogit) and identify the
   exact insertion point + mechanism, or conclude defer.

## Findings

### What Was Discovered

**1. The core internal-guard ask is genuinely EXTERNAL.** backlogit is an
external binary (`C:\Tools\backlogit.exe`, v1.7.0) whose source is not in this
repo. An internal transition guard / self-repair in backlogit itself cannot be
implemented here and should be routed upstream to the backlogit project. This
confirms the prior triage.

**2. The in-repo mitigation is real and lives in autoharness product templates.**
The Ship agent — an autoharness template artifact — is what claims shipments:

* `templates/agents/_ship.agent.md.tmpl` Step 0.5.4:
  *"If the shipment is still in `{{STATUS_QUEUED}}` status, claim it using
  `{{OP_CLAIM_SHIPMENT_MCP}}` before build work begins."*
* Installed dogfood `.github/agents/_ship.agent.md` Step 0.5.4:
  *"Claim the shipment via `backlogit_claim_shipment` (first mutation, only after
  branch gate passes)."*
* Step 2.1 then moves each **task** to `active` via `backlogit_move_item`.

There is **no post-claim assertion** that the shipment *record's own* status
actually transitioned `queued → active` before the per-task loop begins moving
tasks to `active`. If `backlogit_claim_shipment` silently fails or is skipped,
the tasks still get moved to `active` in Step 2.1 — producing exactly the
"queued-with-active-work" inconsistency the stash describes.

**3. The failure trigger is observable and current.** During this very Stage
session the backlogit MCP surface repeatedly returned `Transport closed` on
`backlogit_get_version` / `backlogit_list_shipments` (CLI fallback was used
throughout). A transient MCP drop on the single `backlogit_claim_shipment` call
would leave the shipment `queued` while CLI-driven per-task moves succeed — the
exact mechanism behind the `103-S` incident. The hole is not hypothetical.

**4. `shipment-reconcile` does NOT already cover this.** The `shipment-reconcile`
pre-mode (`templates/skills/shipment-reconcile/SKILL.md.tmpl`) classifies each
**manifest item (task)** against `expected_status` (matched / status-mismatch /
missing / pre-archived) and scans for orphan queue files. It does **not** compare
the **shipment record's own** status against its tasks' statuses. So the
"shipment queued but its tasks active/done" inconsistency is outside its current
checks. The mitigation is additive, not redundant. (The skill also explicitly
documents "no auto-repair — auto-mutation reserved for a future version", so a
detect-and-report posture is consistent with its design.)

**5. Prior art confirms the guard belongs in the workflow, not the tool.**
Compound learning `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`
records that *"the `backlogit move` CLI does not validate against the schema — it
silently accepts invalid status values, which only surface as issues during
review or downstream processing,"* and documents the valid shipment lifecycle
(`queued → active` on claim). backlogit will not self-guard; the guard must be a
Ship-workflow invariant.

**6. Template/dogfood drift noted (not this spike's fix).** The product template
`_ship.agent.md.tmpl` Step 0.5 has a step 6 "Intake reconciliation check"
(`shipment-reconcile mode: pre`); the installed dogfood `.github/agents/_ship.agent.md`
Step 0.5 stops at step 4 (claim) and lacks that intake reconcile step. The plan
must therefore add the post-claim verification to **both** files and account for
the dogfood's missing intake step when adding the early-warning check.

### What Was Tried and Failed

Nothing failed — the investigation was a read/trace exercise. No prototype was
built (none required to answer the feasibility question).

### Remaining Unknowns

* **Frequency.** The queued-with-active-work incident was observed once (`103-S`).
  Low frequency, but high recovery cost (manual archived-status surgery). Value is
  defense-of-integrity, not throughput.
* **Auto-repair vs report.** Whether to *self-repair* the inconsistency (re-issue
  the claim to reconcile the shipment record) versus *detect-and-report* for
  operator/reconcile handling. The `shipment-reconcile` skill's "no auto-repair"
  stance argues for **prevent (post-claim verify) + detect-and-report**, leaving
  true auto-repair as a deferred follow-up. This is a design choice the plan
  resolves; it does not block staging.

## Recommendation

**Conclusion**: proceed
**Confidence**: high

Split the disposition of `6D6CACC1`:

* **Core internal-guard ask → EXTERNAL.** Route upstream to the backlogit project;
  it cannot be implemented in this repo.
* **In-repo mitigation → STAGE NOW.** Add a **post-claim shipment-status
  verification** to Ship Step 0.5 (after `backlogit_claim_shipment`, re-read the
  shipment and assert `status == active`; on `queued`, retry the claim once via
  CLI fallback, then halt fail-closed with `CLAIM_VERIFY_FAILED` **before** any
  task is moved to `active`). Add a complementary **queued-with-active-work
  early-warning** at Ship intake (detect a shipment whose record is `queued`/
  `blocked` while a manifest task is already `active`/`done`, and halt for
  reconcile rather than requiring manual archived-status surgery). Both are
  additive, fail-safe instruction edits to a single template family (agent
  templates), each well under the 2-hour rule.

This resolves the prior triage's "needs a spike, NOT staged now" — the spike has
now resolved the unknowns: the mitigation is in-repo, bounded, not redundant, and
grounded in an observable failure mode.

## Next Steps

1. Promote to `impl-plan` → `docs/plans/2026-07-30-ship-claim-integrity-preflight-plan.md`.
2. Plan-review gate, then harvest into a covering feature + task-only shipment.
3. Record the external portion (backlogit internal guard) as an upstream referral;
   optionally stash a deferred follow-up for true self-repair auto-mutation and for
   extending `shipment-reconcile` pre-mode with a shipment-record-status check.

## References

* `.github/agents/_ship.agent.md` — Step 0.5.4 claim (dogfood, no post-claim verify)
* `templates/agents/_ship.agent.md.tmpl` — Step 0.5.4 claim + Step 0.5.6 intake reconcile
* `templates/skills/shipment-reconcile/SKILL.md.tmpl` — pre-mode item-status checks (no shipment-record-status check)
* `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md` — backlogit silent-accept + valid shipment lifecycle
* Stash `6D6CACC1` — original ask + prior EXTERNAL triage note
* Observed this session: `backlogit MCP: Transport closed` on claim-class calls (transient-drop trigger)
