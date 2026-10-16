---
shipment: 214-S
feature: 207-F
pr: 531
merge_commit: fe1cf82b6235e9a1908e3257bbe0f2a7a42e92e5
reviewed_head: a1d8a8b9
date: 2026-10-16
closure_status: BLOCKED
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/214-S-207-F-close-evidence.json
---

# 214-S / 207-F Post-Merge Closure: Model Routing Resolver (R1-A)

## Summary

Shipment 214-S (feature 207-F, tasks 207.001-T through 207.006-T) merged through PR #531 as merge commit `fe1cf82b6235e9a1908e3257bbe0f2a7a42e92e5` (merge commit strategy, P-009). The cascade close was interrupted; closure is `BLOCKED` with the conditions below. Nothing was fabricated.

## Recovery disclosure

* The mutating `autoharness shipment cascade-close` was run synchronously by the closure subagent under a runtime wait shorter than its supervision budget (`--timeout` + 600 s). The runtime killed the wrapper after `backlogit shipment ship` had begun mutating the backlog.
* Lost facts: the child exit code, finish time, stdout and stderr, the parsed ship response, and the postcondition verdict. They were never persisted.
* The pair lock `.autoharness/gates/cascade-close/214-S-207-F.lock` (dead pid 3168) was deleted by the Orchestrator with explicit operator approval. Ship did not delete it.
* The evidence record stays at phase `invoking`, committed unmodified. No `post_close` record was built, and neither `backlogit shipment ship` nor `cascade-close` was run again (both are forbidden after this state).
* Operator decision (honesty-first): no hand-built record; closure is `BLOCKED`; continuing to 215-S and 216-S is delegated to Ship only if independent verification is clean and compaction is done.
* RCA: `docs/compound/2026-10-16-cascade-close-killed-mid-run-leaves-invoking-record-and-stale-lock.md`. Deferred stash entries (P-021 C2): `369F8062` (recovery subcommand, stdout journaling, wait pre-flight) and `E337551C` (Ship and shipment-reconcile guidance).

## Independent postcondition verification (read-only, after the interruption)

| Postcondition | Result (before archive completion) |
|---|---|
| Shipment `214-S` reads `shipped`, commit recorded | PASS (`backlogit shipment get 214-S`: `shipped`; commit `fe1cf82b…`) |
| Shipment record archived with `archived_status: shipped` | FAIL: the record is still `.backlogit/queue/214-S.md` |
| 207-F and 207.001-T through 207.006-T moved under `.backlogit/archive/` | PASS (all seven files present) |
| Members declare `status: archived` plus `archived_status` (as in a completed cascade, e.g. 206-F, 213-S) | FAIL: 207-F and 207.001-T declare `status: done` with no `archived_status` |
| Pre_close fingerprints | 207.002-T through 207.006-T byte-identical; 207-F and 207.001-T changed as expected for a cascade (commit, `updated_at`, move); shipment record changed as expected |
| `parent_id` preserved | PASS (207.001-T through 207.006-T keep `207-F`) |
| Out-of-manifest descendants | PASS (none; no other `parent_id: 207-*`) |
| Linked deliberation 040-DL (`retained_shared_reference`) | PASS (queue file byte-identical to `d0883ca1…`, clean in git) |
| Nothing else mutated | PASS (git diff shows only `.backlogit/queue/214-S.md`, `.backlogit/queue/207-F.md` deleted with `.backlogit/archive/207-F.md` added, `.backlogit/archive/207.001-T.md`, and this closure's new files) |
| Flat `allowed_ids` / `required_ids` postcondition and `returned_ids` empty | UNVERIFIABLE: the engine response was lost |

Verification outcome (before the operator-approved archive completion below): NOT CLEAN. The cascade stopped before the shipment record and members reached their final archived form.

## Operator-approved archive completion

The operator then authorised completing the half-finished archival with the shipment-reconcile single-artifact archive procedure, for manifest IDs only (214-S, 207-F, 207.001-T through 207.006-T): explicit `backlogit archive <id>`, one at a time. No `backlogit shipment ship` and no `cascade-close` re-run; no other IDs touched.

After (re-verified from the archive files): 214-S `status: archived`, `archived_status: shipped`, queue copy absent; 207-F and 207.001-T through 207.006-T `status: archived`, `archived_status: done`; 207.001-T through 207.006-T keep `parent_id: 207-F`; 040-DL untouched; no other artifact changed. Post-mode re-run: PROCEED, `.backlogit/reconcile/214-S-post-20261016-185200.md` (supersedes the earlier HALT report, which is kept).

Still unverifiable: the flat `allowed_ids`/`required_ids` postcondition and `returned_ids`, since the engine response was lost.

## Shipment close

* Pre-mode (`expected_status: done`): PROCEED, `.backlogit/reconcile/214-S-pre-20261016-174400.md`. Chronology disclosure: this report (generated_at 17:44:00Z) was produced after the evidence record's `pre_close.captured_at` (17:43:25Z) and after `invocation.started_at` (17:43:35Z), i.e. while `backlogit shipment ship` was already running. It is not backdated or edited, and its statement of the classify-only capture time (17:42:54Z) differs from the committed record's 17:43:25Z; the discrepancy is unexplained in the repo. It must not be read as a pre-mutation gate.
* Post-mode: first run `HALT — restore archives` (`.backlogit/reconcile/214-S-post-20261016-182500.md`); after the operator-approved archive completion, re-run PROCEED (`.backlogit/reconcile/214-S-post-20261016-185200.md`). Linked-deliberation disposition: 040-DL retained.

## Conditions (closure_status BLOCKED)

1. RESOLVED (operator-approved): the interrupted archive of `214-S`, `207-F` and `207.001-T` through `207.006-T` was completed (see above).
2. OPEN: the close evidence record cannot become `post_close` without engine-observed facts (exit code, stdout/stderr, parsed ship response, postcondition verdict). It is committed unmodified at `invoking`; `closure_status` therefore stays `BLOCKED` (`READY_WITH_CONDITIONS` would require every condition satisfied with evidence). A future recovery subcommand is captured as stash `369F8062`.
3. P-001 exception (operator-approved): closure is not gate-complete, but the operator authorised proceeding to 215-S and 216-S after the archive was completed and verified and compaction was done.

## Compaction (P-020)

`compaction_status: done`. compact-context (`target: all`) ran a Tier-1 consolidation of this release unit's memory into `docs/memory/compacted/2026-10-16-214-s-207-f-compacted.md`. The Ship session memory `docs/memory/2026-10-16/ship-214-s-207-f-post-merge-closure.md` stays live (linked here), per the 213-S precedent. The shared Stage memory `docs/memory/2026-10-11-stage-bf66f08b-model-routing-v2.md` was deliberately not archived because it still serves pending 215-S (208-F). Nothing else qualified.

## Close evidence

Record: `docs/closure/evidence/214-S-207-F-close-evidence.json` (phase `invoking`, unmodified).
