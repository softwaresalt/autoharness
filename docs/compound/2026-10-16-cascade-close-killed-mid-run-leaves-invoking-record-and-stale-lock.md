---
title: "cascade-close killed mid-run leaves an invoking record, a stale pair lock, and a half-archived backlog"
problem_type: workflow_recovery
category: shipment_closure
root_cause: caller_wait_shorter_than_cascade_close_supervision_budget
tags: [cascade-close, shipment-close, evidence-record, stale-lock, recovery, p015, p021]
shipment: 214-S
feature: 207-F
pr: 531
merge_commit: fe1cf82b6235e9a1908e3257bbe0f2a7a42e92e5
date: "2026-10-16"
source: docs/compound/2026-10-16-cascade-close-killed-mid-run-leaves-invoking-record-and-stale-lock.md
doc_type: learning
---

# cascade-close killed mid-run leaves an invoking record and stale lock

## What happened

During post-merge closure of 214-S (feature 207-F), the closure subagent ran the
mutating `autoharness shipment cascade-close` synchronously. The runtime/tool wait
was shorter than the command's supervision budget (`--timeout` + 600 s), so the
runtime killed the wrapper while `backlogit shipment ship` was mid-run.

State left behind:

* `.autoharness/gates/cascade-close/214-S-207-F.lock` held by a dead pid.
* `docs/closure/evidence/214-S-207-F-close-evidence.json` stuck at phase `invoking`
  (no exit code, finish time, stdout/stderr capture, parsed result, or
  postcondition verdict).
* A partially applied backlog mutation: the shipment record reads `shipped` and the
  feature and member records were moved under `.backlogit/archive/`, but the
  shipment record is still in `.backlogit/queue/` and the moved records still declare
  `status: done` (a completed cascade writes `status: archived` with
  `archived_status`).

## Why it was unrecoverable by an agent

Every sanctioned path was forbidden or inapplicable:

* Re-running `cascade-close` exits 7 (invoking record) and is forbidden after exits 5-8.
* A direct `backlogit shipment ship` is a P-005 deviation.
* Substituting `SAFE_CLOSE` is forbidden after a cascade-close failure exit, and a
  `safe_close` evidence record would misstate what ran.
* `--classify-only --replace-pre-close` only takes over a `pre_close` record.
* A hand-built `post_close` record would need engine-observed facts that were lost
  (exit code 0, stdout/stderr, the parsed ship response). Writing them would be fabrication.

The stale lock is operator-only to delete; the Orchestrator deleted it with explicit operator approval (Ship did not).

## Root cause and contributing causes

Root cause: the mutating command was run under a caller wait shorter than its own
supervision budget.

Contributing causes:

* No Ship guidance to launch the command as an attached async process polled with a
  total wait of at least `--timeout` + 600 s.
* No recovery subcommand for `invoking` records and no sanctioned way to reconstruct
  the lost post-close facts.
* The wrapper does not persist child stdout/stderr incrementally.
* No pre-flight check of the caller's maximum wait against `--timeout` + 600 s.

## Prevention

* ALWAYS run the mutating `cascade-close` in async/attached mode and poll with total
  patience >= `--timeout` + 600 s. Never run it synchronously. Size `--timeout` so the
  whole budget fits the caller's limits.
* Follow-ups, captured as P-021 deferred stash entries (not implemented here):
  `369F8062` (stdout journaling, `cascade-close --recover` that verifies postconditions
  and writes a `post_close` record explicitly marked recovered, and a wait pre-flight)
  and `E337551C` (Ship and shipment-reconcile guidance edits across template and
  installed pairs).

## Recovery performed for 214-S (disclosed)

The operator approved the lock deletion and an honesty-first alternative: no
fabricated `post_close` record. The `invoking` record is committed unmodified, the
independent read-only verification results are in the closure artifact, and the
closure status is `BLOCKED` with explicit conditions.
