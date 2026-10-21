---
shipment: 221-S
feature: 214-F
pr: 548
merge_commit: 114625743ebbd9c5583a1d3b754ad33ed8a5bea5
reviewed_head: da218a62
date: 2026-10-21
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/221-S-214-F-close-evidence.json
---

# 221-S / 214-F Post-Merge Closure: backlog CLI first-class peer of MCP

## Summary

Shipment 221-S (feature 214-F, tasks 214.001-T through 214.005-T; release 1.6.0 chain 3/6) merged through PR #548 as merge commit `114625743ebbd9c5583a1d3b754ad33ed8a5bea5` (merge commit strategy, P-009; two parents verified, in `origin/main`). The change declares verified `cli_command` mappings (hook poll/ack and others) in the backlogit registry, amends P-012 (policy 1.38.0) so declared MCP and CLI surfaces are equal per-operation peers, updates Stage/Ship/Orchestrator Step 0.0 wording and the backlog instructions and docs, and adds a `backlog_registry_cli_surface` verify check with a pinned command-inventory fixture and hook poll/ack contract tests. Closure ran on `post-merge/221-s-g2-backlog-cli-peer` under dark mode (P-017).

## Gates

* Reviewed HEADs: `4ffbbea3` (local review READY, no P0/P1), `275b52ab`, then `da218a6244a3dd79739823e9d750facccbf91460` (merged HEAD). P-014 readiness `READY_WITH_FOLLOWUPS` recorded in the PR body for the merged HEAD.
* CI: all required checks passed on the merged HEAD (one unrelated `test_telemetry_jsonl_sink` flake on an earlier HEAD passed on rerun). Pre-push hook full unittest passed.
* P-018 copilot-review gate: `SATISFIED` before and immediately before merge. Two Copilot rounds, 6 findings: 5 fixed (`f2c61298`, `da218a62`), 1 deferred to stash `3D06D419` (P-021 C1); all threads resolved and body-disposition comments posted.
* Dark mode: no admin fallback, no tag created.

## Process deviation

The shipment claim command was chained after a `pre_claim` gate that returned `BRANCH_MISMATCH` (branch name lacked the `221-s` form). The branch was renamed before any work and `pre_claim` (exit 0) and `post_claim` then passed on the claimed state. No other shipment was affected.

## Shipment close

* Lifecycle topology gate: exit 0 (`BRANCH_POST_MERGE_CLOSURE_ELIGIBLE`) before the close.
* Pre-mode (`expected_status: done`): PROCEED. Report `.backlogit/reconcile/221-S-pre-20261021-173600.md`. 214-F is the qualifying feature.
* Step 0(d) agreement-check outcome: `agreed` (CASCADE, qualifying feature set `214-F`; engine VERIFIED on backlogit 1.11.0).
* Close path: `cascade` via the mutating `autoharness shipment cascade-close` (`--detach` then `--poll`; final exit 0, postcondition `pass`). No direct `backlogit shipment ship` call.
* Linked-Deliberation Disposition (P-015 INV-12): `DISPOSITION_COMPLETE` (empty set).
* Post-mode: PROCEED. Report `.backlogit/reconcile/221-S-post-20261021-175500.md`.
* Final: 221-S `archived_status: shipped`; 214-F and its five tasks `archived_status: done`.

## Follow-ups

* Stash `3D06D419` (medium, requires deliberation): package the pinned backlogit command inventory into the verify-workspace check.
* Stash `89948730` (low): hook CLI template variables and remaining "CLI fallback" wording in Ship/Stage closure steps.

## Source artifact cleanup

No source stash or deliberation cleanup performed (source stash 9CC3C661 no longer present in the active stash; no `source_stash_id` recorded on the shipment).

## Residual risk and conditions

`closure_status: READY`. No open conditions. Rollback: revert the merge commit through a PR; owner: Ship / operator.

## Compaction (P-020)

`compaction_status: done`. compact-context (`target: all`) archived this unit's session memory to `docs/archive/memory/2026-10-21/ship-221-s-214-f-post-merge-closure.md` with a summary at `docs/memory/compacted/2026-10-21-221-s-214-f-compacted.md`. Unrelated and active Stage chain memory were not compacted.

## Close evidence

Record: `docs/closure/evidence/221-S-214-F-close-evidence.json` (phase `post_close`).
