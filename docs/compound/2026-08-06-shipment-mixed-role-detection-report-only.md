---
problem_type: claim-integrity
category: ship-workflow
root_cause: shipment-record-status-not-cross-checked-per-task-role
tags: [backlogit, shipment, claim, queued, active, done, archived, shipment-reconcile, ship-agent, mixed-role, report-only, p-015]
shipment: 118-S
feature: 112-F
source_deliberation_id: 013-DL
source_stash_tracker_id: 936C68F3
tokens: [DETECTED, REPORTED, DEGRADED, live-queued, live-active, "archived-completed(done)", duplicate, conflicting, missing, malformed-provenance, any-other-archived-status, orphan, out-of-role, torn-partial, malformed-legacy]
source: docs/compound/2026-08-06-shipment-mixed-role-detection-report-only.md
doc_type: learning
title: "118-S / 112-F: Mixed-Role Shipment-Record-Status DETECTION + REPORT-ONLY Diagnostics (936C68F3 part 2)"
---

# 118-S / 112-F: Mixed-Role Shipment-Record-Status DETECTION + REPORT-ONLY Diagnostics (936C68F3 part 2)

`118-S` closes the report-only slice of `936C68F3` part 2 by giving
`shipment-reconcile` a new operator-invoked, strictly READ-ONLY
`mode: detect-mixed-role` that describes the queued-with-active-work /
"mixed-role silently-dropped-claim" signature at **per-task ROLE**
granularity, then documents why a record-only auto-repair is **DEFERRED as
unsupported** by backlogit 1.8.0. This is additive to, and distinct from, the
record-scope classification shipped in `109-S`/`105-F` (see
`docs/compound/2026-08-01-shipment-record-status-integrity.md`).

## Why This Exists: the Withdrawn Repair Premise

`013-DL` (deliberation) originally chose Option C: a CONSTRAINED,
operator-invoked, `--confirm`-gated `repair-record-status` mode that would
forward re-claim (`queued` → `active`) a shipment record whose manifest
tasks had silently kept progressing while the record itself never advanced.
Six rounds of independent re-review (Addenda A–F) progressively hardened the
precondition and per-task predicate for that repair mode. **Copilot PR #304
review finding 1** then invalidated the entire premise (Addendum G): verified
read-only against backlogit 1.8.0 source
(`internal/core/shipment_lifecycle.go` `ClaimShipment` / `NormalizeShipmentItems`
/ `rollbackShipmentClaim`; `internal/core/shipment.go`
`isValidShipmentTransition` — `C:\Source\GitHub\backlogit` NOT mutated):

* `ClaimShipment` is **NOT record-only**. It transitions the shipment
  `queued → active` **and then** iterates every manifest member still
  `queued`, activating each and cascading parent-feature status, with
  all-or-nothing rollback on any mid-flight failure — a **manifest-wide**
  activation, not a record-only flip. A "clean" record-only flip is
  structurally impossible.
* `ClaimShipment` is the **only** `queued → active` transition and is
  **STRICTLY SINGLE-SHOT**: `isValidShipmentTransition` permits only
  `queued → active` and `active → {shipped, abandoned}`; a re-claim on an
  already-`active` shipment returns `ErrShipmentConflict`. There is **no**
  `active → queued` edge and **no** `blocked` shipment status in 1.8.0.

Because inventing direct frontmatter mutation, locks/CAS/leases, or external
backlogit changes is explicitly out of scope, **no supported record-only
repair operation exists**. `112-F` (and this `118-S` shipment) therefore
RE-SCOPES the entire feature to READ-ONLY DETECTION + REPORT-ONLY diagnostics
+ operator-remediation guidance. True auto-repair is **DEFERRED**, not
abandoned — the historical repair-mode machinery in `013-DL` Addenda A–F
remains as rationale only and no longer gates anything.

## Per-Task ROLE Classification (Retained From the Withdrawn Repair, Repurposed for Description Only)

The per-task ALLOWED-STATE role predicate developed across `013-DL` Addenda
D/E/F survives the re-scope, but its purpose changes: it now **describes**
the inconsistency in a report, and is **never** used to gate a mutation.
Each task-artifact manifest item must be a UNIQUE, NON-CONFLICTING record for
exactly one role:

| Role | Definition |
|---|---|
| `live-queued` | Unique `queue/` record, `status: queued`, no archive copy |
| `live-active` | Unique `queue/` record, `status: active`, no archive copy |
| `archived-completed(done)` | Unique `archive/`-only record in EITHER valid representation: (a) terminal relocation `status: done` (no provenance required), or (b) explicit archival `status: archived` + `archived_status: done` + valid `archived_from` |

Both archive representations are real and observed in this very workspace
(`.backlogit/archive/002.001-T.md` / `104.001-T.md` for (a);
`.backlogit/archive/012-DL.md` for (b)) — a predicate admitting only one
representation would fail closed on legitimately archived tasks (the P1-2b
correction in `013-DL` Addendum F).

Per-item **anomalies** fail closed (report and halt on any): `duplicate`,
`conflicting` (including a live `status: done` found in the **queue**, which
never legitimately occurs), `missing`, `malformed-provenance` (an
archive-with-`archived: archived` record missing/ill-formed
`archived_status`/`archived_from` — note a bare `status: done` archive record
legitimately carries none), `any-other-archived-status`, `orphan`,
`out-of-role`, and `torn-partial`.

## The Mixed-Role Signature

A shipment record `queued` whose task-artifact manifest items include at
least one `live-active` or `archived-completed(done)` role task — with every
task otherwise role-clean — is the reportable "silently-dropped-claim"
signature: the claim never advanced the record even though its tasks kept
moving and, in the archived case, even finished. This is a stricter,
per-task-precise complement to the `record-queued-with-active-work`
record-scope classification from `109-S`/`105-F`, which only compares the
record's status against the *aggregate* active/done state of its manifest.

## Malformed-Legacy Shipment Records

Backlogit 1.8.0 has no `blocked` shipment status (`ShipmentStatus` is only
`queued|active|shipped|abandoned`). A shipment record whose persisted status
is not one of those four values (for example a legacy `blocked` value from
before this constraint was understood — see
`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`) is
classified `malformed-legacy` in the detection report. No `blocked → queued`
or any other transition is ever fabricated.

## Outcomes: DETECTED / REPORTED / DEGRADED

`mode: detect-mixed-role` produces exactly one outcome per candidate
shipment, mirroring the `pipeline-topology` gate's success/blocked/failed
telemetry mapping:

* **`DETECTED`** — the scan completed and found no mixed-role signature or
  anomaly for that candidate; nothing to report.
* **`REPORTED`** — the scan completed and found the mixed-role signature
  and/or one or more per-item anomalies; the report names the shipment id,
  record status, per-task roles, and each anomaly.
* **`DEGRADED`** — backlogit was unreachable; the degraded condition is
  reported and the scan halts. The mode never guesses or acts on partial
  data.

There is **no** `succeeded` / `repaired` / `refused` / two-active outcome —
nothing is ever mutated or repaired by this mode.

## Audit + Telemetry

Every outcome writes a structured JSON audit line to
`.autoharness/gates/shipment-reconcile-detection-audit.log` — mirroring the
existing `pipeline-topology` force-audit convention
(`src/autoharness/cli.py` `_audit_pipeline_topology_force` /
`_emit_pipeline_topology_telemetry`) — and a best-effort
`ToolTelemetryEvent` (`schemas/tool-telemetry-event.schema.json`) when a live
`context_ref` is available from an active Ship task epoch. There is
deliberately **no** `repair` / `mutation` / `confirm` / `post_condition`
field in the audit entry — those concepts never apply to this read-only
mode. A standalone/ad-hoc operator invocation with no `context_ref` skips the
telemetry event but still writes the audit-log entry, consistent with
telemetry's existing fail-open, observational contract.

## Operator-Remediation Runbook

autoharness performs **NO auto-repair** of a reported mixed-role
inconsistency. The supported manual remediation path is entirely through
backlogit's own sanctioned lifecycle transitions:

1. The operator inspects the shipment and its manifest tasks directly
   (`backlogit shipment get <id>` / `backlogit get <task_id>`).
2. If the tasks are legitimately progressing, the operator lets the
   shipment proceed to closure normally once every task completes, using
   `shipment-reconcile`'s own `mode: pre` → `mode: safe-close` →
   `mode: post` sequence (unchanged by this feature).
3. If the state instead reflects a genuinely torn/partial session, the
   operator investigates and resolves the affected tasks manually before
   any closure attempt.

No autoharness-issued mutation, no fabricated `active → queued` rollback,
and no fabricated `blocked → queued` transition is ever performed.

## Explicitly Deferred / Not This Shipment's Scope

* **True self-repair** (a record-only forward re-claim) remains **DEFERRED
  as unsupported** by backlogit 1.8.0 — not merely decision-gated as in the
  original `013-DL` framing, but structurally unreachable via any supported
  operation, per the evidence above. Any future work here would require
  either an upstream backlogit change or a fundamentally different
  mechanism than a shipment-record-only status fix.
* **Stash disposition**: `936C68F3` remains an **ACTIVE living tracker**.
  This feature consumes only the report-only detection slice; the
  auto-repair portion stays deferred, so `936C68F3` is **NOT** archived and
  **NOT** fully consumed. `112-F`'s provenance intentionally omits the
  cleanup-triggering `custom_fields.source_stash_id` field (which Ship's
  current cleanup contract retires unconditionally on close) and instead
  carries the non-cleanup `custom_fields.source_stash_tracker_id: 936C68F3`
  plus `source_stash_consumption: partial-report-only-slice` /
  `source_stash_disposition: active-living-tracker`.
  `custom_fields.source_deliberation_id: 013-DL` is retained because
  `013-DL` is already archived, making its cleanup an idempotent safe no-op.
* External `backlogit` (`C:\Source\GitHub\backlogit`) was inspected
  READ-ONLY for evidence; it was **not** mutated by this feature.

## Cross-References

* `docs/compound/2026-08-01-shipment-record-status-integrity.md` — the
  `109-S`/`105-F` record-scope classification (`record-consistent` /
  `record-queued-with-active-work` / `record-blocked-with-active-work` /
  `record-blocked-with-done-work`) this feature's per-task role
  classification complements.
* `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md` —
  backlogit's shipment lifecycle constraints (no `blocked` status, no
  `active → queued` edge).
* `templates/skills/shipment-reconcile/SKILL.md.tmpl` — the implementation
  surface (`mode: detect-mixed-role`: Inputs, Mixed-Role Detection
  Classification, Required Protocol, Operator-Remediation Guidance, Audit +
  Telemetry, Quality Criteria).
* `013-DL` (archived deliberation) — Option C chosen-direction, Addenda A–F
  (historical rationale for the withdrawn repair mode; per-task role
  predicate origin), and Addendum G (the re-scope to report-only per
  Copilot PR #304 finding 1) plus Addendum H (provenance-cleanup contract
  correction).
* `112.001-R` (archived review) — plan-review verdict PASS for the
  re-scoped read-only plan; full finding history across all re-reviews and
  publication-reviews.

## Verification Pattern

1. `109-S`/`105-F` record-scope classification (aggregate record-vs-tasks
   comparison) runs unchanged in `shipment-reconcile` pre-mode.
2. `118-S`/`112-F` `mode: detect-mixed-role` (this feature) runs as a
   separate, operator-invoked, read-only per-task role scan, describing the
   mixed-role signature and per-item anomalies without gating any mutation.
3. Both layers are detect-and-report only. The `936C68F3` auto-repair
   portion stays deferred and tracked as an active living stash until a
   safe mechanism (if ever found) is proposed and deliberated separately.
