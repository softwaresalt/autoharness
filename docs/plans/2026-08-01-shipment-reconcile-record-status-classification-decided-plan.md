---
source: docs/plans/2026-08-01-shipment-reconcile-record-status-classification-decided-plan.md
title: "Shipment-record-status integrity classification for shipment-reconcile pre-mode"
doc_type: decided-plan
status: planned
created: 2026-08-01
supersedes:
  - docs/archive/plans/2026-08-01-shipment-reconcile-record-status-classification-plan.md
---

# Decided Plan: Shipment-record-status integrity classification for shipment-reconcile pre-mode

**Outcome:** Planned from stash `2970FA4E`, grounded in the claim-integrity spike. No shipping evidence is recorded in the source plan, so status remains `planned`. The decided scope is a fail-safe additive pre-mode check: compare each shipment record's own status to the aggregate status of its manifest tasks, halt for operator reconcile when the record is inconsistent, and capture the reusable learning as a companion compound entry.

## Decisions

- Make `shipment-reconcile` pre-mode the long-term home for shipment-record status integrity checks. This is additive because pre-mode already classifies manifest items and scans for orphans, but it does **not** compare the shipment record's own `status` against the statuses of its member tasks.
- Add four mutually exclusive shipment-record outcomes:
  - `record-consistent`
  - `record-queued-with-active-work`
  - `record-blocked-with-active-work`
  - `record-blocked-with-done-work`
- Preserve the explicit precedence rule for blocked records: when a blocked record has both `active` and `done` work, classify it as `record-blocked-with-active-work` so the earlier-stage, more severe drift signal wins.
- Any inconsistent record outcome reuses the existing pre-mode recommendation path: `HALT — operator reconcile required`. The report must surface the shipment id, the record status, and the conflicting task ids. No new terminal state is introduced.
- Run the comparison at both places where the inconsistency matters operationally: Ship Step 0.5 intake and Step 6 pre.
- Extend the skill's Quality Criteria so the rendered template explicitly includes the new classification and still contains no unresolved `{{...}}` placeholders.

## Implementation (2 tasks)

- **T1 — Skill template update:** extend `templates/skills/shipment-reconcile/SKILL.md.tmpl` with the new record-status classification table, pre-mode compare step, gate wiring, and quality-criteria coverage.
- **T2 — Compound learning capture:** add `docs/compound/2026-08-01-shipment-record-status-integrity.md` so the queued-with-active-work pattern, `CLAIM_VERIFY_FAILED`, and `SHIPMENT_STATE_INCONSISTENT` are retained as reusable learning.

## Key constraints preserved

- The change is **detect-and-report only**. The skill remains HALT-only on inconsistency and never claims, mutates, or auto-repairs backlog state.
- The design stays bounded to one skill-template family plus one documentation artifact; there is no schema change, CLI distribution change, or multi-template-family blast radius.
- The record-level classification is distinct from the existing per-item classifications; it complements rather than replaces them.
- The check remains honest about what autoharness owns: shipment-record drift is surfaced here, but backlogit-internal transition behavior is not repaired here.

## Rejected alternatives

- **True self-repair / auto re-claim** — rejected for this plan because it would require deliberately lifting the skill's no-auto-repair posture. The decided design keeps pre-mode read-only and operator-routed.
- **Backlogit-internal active→queued transition guard** — rejected as autoharness scope. That belongs upstream in backlogit, not in this additive skill change.
- **Relying on per-item checks alone** — rejected because it misses the `103-S` class of failure where manifest tasks advance while the shipment record itself still says `queued`.