---
title: "Ship session memory: 214-S / 207-F post-merge closure (interrupted cascade)"
date: 2026-10-16
agent: ship
shipment: 214-S
feature: 207-F
---

# Ship session memory: 214-S / 207-F post-merge closure

## Outcome

* PR #531 merged as `fe1cf82b` (merge commit). 207-F delivered the model-routing resolver (R1-A).
* The cascade close was interrupted: the mutating `autoharness shipment cascade-close` was run synchronously and the runtime killed the wrapper after `backlogit shipment ship` began. The evidence record is stuck at `invoking` and the lock was deleted by the Orchestrator with operator approval.
* Resumed Ship session: independent read-only verification found the shipment `shipped` but not archived, and 207-F and 207.001-T under `archive/` still declaring `status: done`. No fabricated `post_close` record. Post-mode first returned `HALT — restore archives`.
* Operator then authorised completing the archive for manifest IDs only (explicit `backlogit archive <id>`, no ship, no cascade-close re-run). Done and verified: 214-S `archived_status: shipped`; 207-F and 207.001-T through 207.006-T `archived_status: done`. Post-mode re-run returned `PROCEED` (`.backlogit/reconcile/214-S-post-20261016-185200.md`). Archival is NOT outstanding.
* Closure stays `BLOCKED` because the engine completion evidence (exit code, stdout/stderr, parsed ship response) was lost and the evidence record stays at `invoking`.
* Closure record: `docs/closure/214-S-207-F-post-merge-closure.md`. RCA: `docs/compound/2026-10-16-cascade-close-killed-mid-run-leaves-invoking-record-and-stale-lock.md`.
* P-021 deferred captures: `369F8062` (recovery subcommand, stdout journaling, wait pre-flight) and `E337551C` (Ship and shipment-reconcile guidance).

## Learnings

* Run the mutating `cascade-close` only as an attached async process polled for at least `--timeout` + 600 s.
* A killed cascade leaves a half-archived backlog; verify members and shipment archive form against a completed cascade (for example 206-F and 213-S) rather than trusting the shipment status alone.
