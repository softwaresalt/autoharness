---
problem_type: claim-integrity
category: ship-workflow
root_cause: backlogit-shipment-record-status-not-cross-checked-against-manifest-tasks
tags: [backlogit, shipment, claim, status, blocked, queued, active, shipment-reconcile, ship-agent, guard-token, p-018]
shipment: 109-S
feature: 105-F
source_stash: 2970FA4E
tokens: [CLAIM_VERIFY_FAILED, SHIPMENT_STATE_INCONSISTENT, record-consistent, record-queued-with-active-work, record-blocked-with-active-work, record-blocked-with-done-work]
source: docs/compound/2026-08-01-shipment-record-status-integrity.md
doc_type: learning
title: "109-S / 105-F: Shipment-Record-Status Integrity — the Long-Term Home in `shipment-reconcile`"
---

# 109-S / 105-F: Shipment-Record-Status Integrity — the Long-Term Home in `shipment-reconcile`

Shipment `109-S` closes `2970FA4E` part (1) READY-FOR-PLANNING and part (3)
LEARNING-FOLLOW-UP by giving `shipment-reconcile` pre-mode a permanent,
reusable **shipment-record-status classification**: a check that compares the
shipment record's **own** status against the aggregate status of its manifest
tasks, independent of any single Ship session's claim flow. This is the
long-term integrity-check home referred to by `106-S-claim-integrity-guards.md`
as a deferred follow-up ("C11 / P3-3").

## The Three Signals

1. **`CLAIM_VERIFY_FAILED`** — Ship's post-claim verification signal (Unit A,
   shipped in `106-S`/`102-F`): after `shipment claim`, re-read the shipment
   record's own status and assert it reached `active`. Retry-once ONLY when the
   re-read status is `queued`; halt immediately with `CLAIM_VERIFY_FAILED` (no
   retry, no re-claim) when the re-read status is `blocked`.
2. **`SHIPMENT_STATE_INCONSISTENT`** — Ship's intake early-warning signal
   (Unit B, also shipped in `106-S`/`102-F`): scan immediately after the
   shipment record is loaded, before both status/scope validation and the
   claim, and halt when the loaded record is `queued`/`blocked` while a
   manifest task is already `active`/`done`.
3. **The queued-with-active-work failure pattern** — the underlying inconsistency
   both signals guard against: a shipment record stays `queued` (or `blocked`)
   while its manifest tasks proceed to `active`/`done`, because the backlogit
   claim transition is not always atomic/consistent against the manifest task
   states (observed on `103-S`; root cause of the original claim-integrity
   spike, `docs/decisions/2026-07-30-ship-claim-integrity-preflight-spike.md`).

## The Long-Term Home: `shipment-reconcile` Pre-Mode

`106-S` shipped the two Ship-session-scoped guards (`CLAIM_VERIFY_FAILED` at
post-claim, `SHIPMENT_STATE_INCONSISTENT` at intake) directly in the Ship agent
claim flow. Those guards only run inside a live Ship session claiming a
shipment. `109-S` (`105-F` / `105.002-T`) adds the durable, tool-invocable home
for the same class of check: `shipment-reconcile` pre-mode now also classifies
the **shipment-record-status** relationship, independent of whether the check
is running as part of a fresh claim, an ad-hoc audit, or Ship Step 6 closure.

Four mutually exclusive cases, partitioned first by the record's own status
(`queued` vs `blocked`):

| Classification | Condition |
|---|---|
| `record-consistent` | Record status compatible with member-task states |
| `record-queued-with-active-work` | Record `queued` AND a manifest task `active`/`done` — the `103-S` pattern |
| `record-blocked-with-active-work` | Record `blocked` AND a manifest task `active` — precedence over the case below when both apply |
| `record-blocked-with-done-work` | Record `blocked` AND no task `active` AND a manifest task `done` |

The check reuses data already read by pre-mode (the shipment record loaded via
`{{OP_GET_SHIPMENT_MCP}}`, the manifest item statuses read during the per-item
check) — **no new scan**. This is **detect-and-report only**: on any
non-`record-consistent` classification, the pre-mode recommendation becomes
`HALT — operator reconcile required`, naming the shipment id, the record's own
status, and the conflicting manifest task ids. It never mutates the shipment
record or any task.

## Why a Second Home for the Same Failure Class?

The Ship-session guards (`CLAIM_VERIFY_FAILED` / `SHIPMENT_STATE_INCONSISTENT`)
only protect a shipment while Ship itself is actively claiming and running it.
`shipment-reconcile` pre-mode is invoked more broadly — Ship Step 0.5 intake,
Ship Step 6 closure, and ad-hoc operator audits — so giving it its own
shipment-record-status classification means the same inconsistency is caught
even outside the narrow claim-flow window the Ship-session guards cover (for
example, a shipment that drifted `blocked` with active work during a *prior*
session, then re-examined in pre-mode without a fresh claim). This is additive,
not redundant: pre-mode previously classified only per-item state
(`matched` / `pre-archived` / `missing` / `status-mismatch` / `orphan`) and
never cross-checked the record's own status against its tasks.

## Explicitly Deferred / Not This Shipment's Scope

* **True self-repair / auto re-claim** (`2970FA4E` part (2)) remains
  **decision-gated** on the operator deliberately lifting `shipment-reconcile`'s
  "no auto-repair" stance. This shipment does not lift that stance; the new
  classification is detect-and-report only, matching the skill's existing
  report-and-halt / no-auto-repair posture.
* The **backlogit-internal `active → queued` transition guard** is **EXTERNAL**
  to this repo (backlogit is an external binary; its source is not here) and was
  routed upstream, not patched here.
* Remediation for a `blocked` record is unchanged: resolve the blocking gate and
  transition `blocked → queued` before any claim — never re-claim-to-`active`
  directly on a `blocked` record. See
  `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md:32-44`.

## Cross-References

* `docs/decisions/2026-07-30-ship-claim-integrity-preflight-spike.md` — the
  originating spike (proceed / high confidence) that first identified the
  queued-with-active-work failure mode and scoped the in-repo mitigation.
* `docs/compound/106-S-claim-integrity-guards.md` — the Ship-session-scoped
  `CLAIM_VERIFY_FAILED` (Unit A) and `SHIPMENT_STATE_INCONSISTENT` (Unit B)
  guards this shipment's `shipment-reconcile` classification complements.
* `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md` —
  backlogit's silent-accept behavior and the valid shipment lifecycle
  (`blocked → queued` before any claim).
* `templates/skills/shipment-reconcile/SKILL.md.tmpl` — the implementation
  surface (Output classification table, Pre-Mode protocol step, Quality
  Criteria).

## Verification Pattern

1. Ship-session guards (`106-S`): `SHIPMENT_STATE_INCONSISTENT` at intake before
   validation/claim; `CLAIM_VERIFY_FAILED` after claim, before the task loop.
2. `shipment-reconcile` pre-mode (`109-S`): shipment-record-status classification
   computed from data already in hand (steps 2–3), any non-consistent result
   HALTs with the shared `HALT — operator reconcile required` recommendation.
3. Both layers are detect-and-report only; auto-repair remains decision-gated
   and the backlogit-internal guard remains an external, upstream-routed
   referral.
