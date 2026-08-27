---
title: "shipment-reconcile pre-mode: shipment-record-status integrity classification"
type: impl-plan
date: 2026-08-01
route: claude-opus-4.8 / anthropic / high (P-013.5)
source_stash: 2970FA4E
source_spike: docs/decisions/2026-07-30-ship-claim-integrity-preflight-spike.md
scope_part: "2970FA4E part (1) READY-FOR-PLANNING + part (3) LEARNING-FOLLOW-UP"
requires_plan_hardening: no
requires_plan_hardening_rationale: >
  Single template family (templates/skills/shipment-reconcile/SKILL.md.tmpl only),
  additive detect-and-report classification consistent with the skill's existing
  report-and-halt / no-auto-repair posture. No schema change, no CLI distribution
  change, no multi-template-family blast radius, no auto-mutation. Fail-safe: the
  new classification can only HALT (surface for operator reconcile), never mutate
  backlog state. Blast radius is therefore LOW and does not trip the P-006
  hardening signals (schemas / CLI distribution / multiple template families).
---

## Problem

`2970FA4E` part (1) asks to make `shipment-reconcile` pre-mode the long-term
integrity-check home by adding a **shipment-record-status classification** that
compares the shipment record's *own* status against its manifest-task statuses.

Grounding (verified against `templates/skills/shipment-reconcile/SKILL.md.tmpl`):
pre-mode today classifies each **manifest ITEM (task)** against `expected_status`
(`matched` / `pre-archived` / `missing` / `status-mismatch`) and runs an orphan
scan. It **never** compares the **shipment record's own** `status` against the
statuses of the tasks in its manifest. So the "shipment stays `queued` while its
tasks are `active`/`done`" inconsistency (observed on `103-S`, root cause of the
claim-integrity spike) is outside pre-mode's current checks. Adding it is
**additive, not redundant** (spike finding #4).

Out of scope (surfaced, not built here):
- part (2) true self-repair / auto re-claim — DECISION-GATED on the operator
  deliberately lifting the skill's no-auto-repair stance. NOT planned.
- The backlogit-internal `active->queued` transition guard — EXTERNAL; route
  upstream to the backlogit project. NOT harvested.

## Design

Additive, detect-and-report, fail-safe. Extend pre-mode only.

1. **New classification `record-status-inconsistent`** (shipment-record scope,
   distinct from the five per-item classifications). Add a `shipment-record-status`
   comparison that reads the shipment record's own `status` and cross-checks it
   against the aggregate of its manifest tasks' statuses. The four cases are
   **mutually exclusive**, partitioned first by the record's own status
   (`queued` vs. `blocked`), with an explicit precedence rule for the
   blocked case so `blocked` + `active` and `blocked` + `done` never both match:
   - `record-consistent` — record status is compatible with member-task states
     (e.g. record `queued` and all tasks `queued`; record `active` with tasks
     `active`/`queued`; record `done`/archived with tasks `done`).
   - `record-queued-with-active-work` — record status is `queued` AND at least
     one manifest task is `active` or `done`. This is the `103-S` failure
     mode: a silently-dropped `claim_shipment` leaves the record `queued` while
     per-task moves proceed. (Scoped to `queued` only — the `blocked` record
     case is fully covered by the two classifications below, so this case does
     not overlap with them.)
   - `record-blocked-with-active-work` — record status is `blocked` AND at
     least one manifest task is `active`. **Precedence**: when a `blocked`
     record has both an `active` task and a `done` task, classify here —
     `active` work is the more severe/earlier-stage drift signal and takes
     precedence over `record-blocked-with-done-work`.
   - `record-blocked-with-done-work` — record status is `blocked` AND no
     manifest task is `active` AND at least one manifest task is `done`.
2. **Gate wiring**: when the shipment-record-status check yields any inconsistent
   result, the pre-mode `recommendation` becomes
   `HALT — operator reconcile required` (reuse the existing pre-mode HALT path;
   no new terminal state). Emit the offending shipment id + record status +
   conflicting task ids in the report. NO auto-repair.
3. **Intake placement**: the check must run in pre-mode at Ship Step 0.5 intake
   (`expected_status: {{STATUS_QUEUED}}` / `{{STATUS_ACTIVE}}`) — the exact locus
   where the inconsistency first becomes observable — and again at Step 6 pre.
4. **Self-verification**: extend the skill's own **Quality Criteria** to require
   the shipment-record-status classification be represented, so the skill's
   quality contract (its verifiable acceptance surface) covers the new check. The
   rendered template must contain no unresolved `{{...}}` placeholders.

## Affected Surface (exhaustive)

- `templates/skills/shipment-reconcile/SKILL.md.tmpl` — Output classification
  table + semantics, Required Protocol > Pre-Mode step (record-vs-tasks compare +
  gate), Quality Criteria row. (No installed `.github/skills/shipment-reconcile`
  dogfood instance exists — template-only skill; no dogfood parity edit needed.)
- `docs/compound/2026-08-01-shipment-record-status-integrity.md` (NEW) — compound
  learning for 2970FA4E part (3): `CLAIM_VERIFY_FAILED`,
  `SHIPMENT_STATE_INCONSISTENT`, and the queued-with-active-work pattern; cross-ref
  the claim-integrity spike + 106-S claim-integrity guards.

## Tasks (each single-concern, < 2h, verifiable)

- **T1 (skill template)** — Add the shipment-record-status classification +
  pre-mode compare step + gate wiring + Quality Criteria coverage to
  `SKILL.md.tmpl`. Verify: new classification present in Output table; the four
  cases are mutually exclusive with the blocked+active-over-blocked+done
  precedence rule stated explicitly; Pre-Mode protocol step reads record status
  and compares to manifest tasks; recommendation HALTs on inconsistency; no
  unresolved `{{...}}`.
- **T2 (docs / compound learning — part 3)** — Author the compound learning doc.
  Verify: file exists; captures the three signals; cross-refs the spike + 106-S.
  Depends on T1 (documents the shipped classification).

Width isolation preserved: T1 is skill-template family only; T2 is docs only.

## Explicitly NOT in this plan

- part (2) self-repair auto-mutation (decision-gated) — re-stashed as a deferred
  entry for operator routing.
- backlogit-internal transition guard (EXTERNAL) — upstream referral, re-stashed.

## Requires plan hardening?

**No.** See frontmatter `requires_plan_hardening_rationale`: single template
family, additive, fail-safe (HALT-only, no auto-mutation), no schema/CLI/
multi-family blast radius. P-006 hardening signals not tripped.
