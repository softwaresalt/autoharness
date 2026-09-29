---
title: "Ship 190-S / 184-F full lifecycle (compacted)"
description: "Compacted Tier-1 release-unit memory for 190-S / 184-F (Windows temp-dir teardown repair, test-only, P-020). Covers Stage staging as a separate P-021 unit, execution, PR #464 merge, the backlogit 1.11.0 CASCADE linked-deliberation halt, and the operator-approved 034-DL deviation."
doc_type: memory
source: docs/memory/compacted/2026-09-29-ship-190-s-184-f-full-lifecycle-compacted.md
date: 2026-09-29
agent: ship
session_id: ship-2026-09-29-190s-closure
compacted_from:
  - docs/archive/memory/2026-09-29-ship-190-s-184-f-session.md
  - docs/archive/memory/2026-09-20-stage-windows-temp-cleanup-defect.md
---

# Ship 190-S / 184-F Full Lifecycle (Compacted)

The verbose originals are listed in `compacted_from`. Closure record:
`docs/closure/190-S-184-F-post-merge-closure.md`. Close evidence:
`.backlogit/reconcile/190-S-cascade-close-20260929-061541.md`. Decision:
`docs/decisions/2026-09-20-windows-temp-cleanup-teardown-defect-deliberation.md`.

## Defect and Staging (Stage, 2026-09-20)

* After `622a41a1` (183.001-T), the canonical suite failed twice at
  `CapabilityPackEnforcementVerifierTests.test_orphaned_manifest_entry_without_pack_fails`.
  The failure was in `TemporaryDirectory.__exit__` → `shutil.rmtree`
  (`PermissionError` WinError 32/5). It was a teardown failure, not an
  assertion failure. A read-only review found no production handle leak, so
  the repair is test-only and `src/` must not change.
* Under P-021 C1 the defect was out of scope for the discovering 183.001-T
  cycle, so it was staged as a separate unit:
  * stash `78548873`, archived at harvest
  * deliberation `034-DL`
  * feature `184-F`, task `184.001-T` (size S)
  * shipment `190-S` (SHIP-24)
* The Graphtor `tearDown` leak `8CB606F8` stays a separate, deferred P2 item.
  `AD0F128D` is a separate, different mechanism.
* Selected repair: a bounded retry on WinError 32/5 with a final re-raise.
  `ignore_cleanup_errors` and `ignore_errors` were rejected.
* The four-step verification order: the exact test, cross-module runs with the
  Graphtor module in both orderings, a no-lingering-process/dir check, then the
  canonical suite.
* No `blocks` edge was added to 189-S, because one would deadlock. 190-S lands
  first.

## Execution and Merge (Ship, 2026-09-29)

* The implementing change `6ce8bfc3` had already landed via PR #457. PR #464
  carried only lifecycle commits.
* PR #464 merged as `ef661e90`:
  * reviewed HEAD `934cbfe5`, `READY`, P0=0, P1=0
  * canonical suite: 2469 tests OK (54 skipped)
  * cross-module runs: 27/27 OK in both orderings
  * no lingering processes or temp dirs

## Closure Incident

* The close was classified `CASCADE`. `034-DL` (description-linked from 184-F)
  was put in `required_ids` per the shipment-reconcile Linked-deliberation
  snapshot extension.
* backlogit 1.11.0 `shipment ship` archived only `[184.001-T, 184-F, 190-S]`.
  The run halted fail-closed with a P-005 event, and nothing was committed.
* Root cause: backlogit `5a4b70dd` (174.058-T, v1.11.0) removed
  linked-deliberation archival (`collectArchiveCandidateIDs`,
  `internal/core/shipment_lifecycle.go:716`, lines 734–735).
* The operator approved a deviation ("option 1"): `034-DL` was archived
  standalone (`archived_status: queued`). The follow-up is stash `8FEE91F4`
  (bug/high, requires deliberation).

## Learnings

* Engine release changes are contract inputs. A skill postcondition that was
  derived from reading engine source goes stale silently when the engine
  flattens scope.
* The two-set postcondition gate caught the drift before commit, as designed.
