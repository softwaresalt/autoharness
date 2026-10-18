---
shipment: 218-S
feature: 211-F
pr: 536
merge_commit: 03216ce01fce1f4ea22eb48f63704c0a57c8ccc0
reviewed_head: 961e4f2e
date: 2026-10-18
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/218-S-211-F-close-evidence.json
---

# 218-S / 211-F Post-Merge Closure: Cascade-Close Journaling, Detach/Poll and Provenance-Marked Recovery

## Summary

Shipment 218-S (feature 211-F, tasks 211.001-T through 211.016-T) merged through PR #536 as merge commit `03216ce01fce1f4ea22eb48f63704c0a57c8ccc0` (merge commit strategy, P-009; two parents verified, ancestor of `origin/main`). The change makes the mutating `autoharness shipment cascade-close` survive a killed wrapper (the 214-S incident): a durable OS-level output journal with an exit sentinel, `--detach` / `--poll` supervision (exits 9 and 10), safe stale-lock takeover only when the owner is provably dead, and an idempotent evidence-only `--recover` that writes a schema-valid, provenance-marked `post_close` record without fabricating unobserved facts. Shipment-reconcile, Ship, operational-closure and circuit-breaker guidance and their installed mirrors were propagated in the same PR.

This closure was executed under the just-merged contract: the freshly merged `shipment-reconcile` skill (detach/poll run mode, recovery routing, flag-combination rules) was re-read before the close.

## Gates

* Reviewed HEAD of the PR: `961e4f2e` (PR head at merge). Local multi-persona review: six personas (Correctness, Security, Concurrency, Python, Schema-CLI-Docs Coupling, Maintainability) at `62f5c176` plus delta Correctness/Concurrency passes on `814971dc` and `71907548`; P0=0, P1=0. P2 findings fixed in the PR (hostile-JSON TypeError hardening, attached shim child-pid journaling and spawn-window group kill, supervisor pre-spawn failure semantics, poll trust-walk and exit-0 corroboration, doc drift); remaining P2/P3 findings deferred (see Follow-ups).
* Full local build: `PYTHONPATH=src python -m unittest discover -s tests` ran 4132 tests, OK (skipped=63); pre-push hook (unittest and markdownlint) passed at the reviewed HEAD; the cascade-close modules were re-verified on Linux (WSL); `autoharness verify-workspace --workspace .` blockers=0.
* Copilot review: four rounds. Every threaded finding was fixed or answered and resolved (the PR body records rounds 1-3 as 4 + 2 threaded findings, fixed in `71907548`, `3d2483ab`, `d636d40e`); no review-body finding was left undispositioned. P-018 gate `SATISFIED`; CI green at merge. Admin fallback not used.
* Runtime verification: not required (CLI and library only). The 214-S incident is replayed by `tests/test_shipment_close_incident_replay.py`.
* Releasability: `READY`.

## Shipment close

* Lifecycle topology gate (`pipeline-topology --mode agent --shipment 218-S --phase lifecycle`): exit 0 (`BRANCH_POST_MERGE_CLOSURE_ELIGIBLE`).
* Pre-mode (`expected_status: done`): PROCEED. Report `.backlogit/reconcile/218-S-pre-20261018-045300.md`. 211-F is the qualifying feature; 211.011-T through 211.016-T were pre-archived (tolerated).
* Step 0(d) agreement-check outcome: `agreed` (CASCADE, qualifying feature set `211-F` in both the pre-mode report and the `--classify-only` evidence record; engine VERIFIED on backlogit 1.11.0, CLI surface).
* Close path: `cascade`. `--classify-only` exited 0 (CASCADE), then the mutating `autoharness shipment cascade-close` ran attached with destructive-command approval from the dark-mode operator authority, `--timeout 2415` (N = 18, B = ceil(1.5 x (800 + 45 x 18)) = 2415 s) and `--caller-wait 3015` (timeout + 600 s). It exited 0 after about 16 minutes (04:52:54Z to 05:09:09Z); `phase_written: post_close`, postcondition verdict `pass`, `returned_ids` empty, `archived_ids` = 211-F, 211.001-T through 211.010-T and 218-S, `parent_id` preserved, baseline invariant, linked-deliberation snapshot byte-identical, shipment `archived_status: shipped`. No direct `backlogit shipment ship` call was made and no `--recover` was needed.
* Linked-deliberation disposition (P-015 INV-12): `DISPOSITION_COMPLETE`. `041-DL` (linked from 211-F by description mention) is `retained_description_mention`, byte-identical, nothing archived. `stranded_linked_deliberation` advisory: 041-DL stays live.
* Post-mode: PROCEED. Report `.backlogit/reconcile/218-S-post-20261018-051100.md`.
* Lifecycle lock `.backlogit/queue/218-S.md` was acquired for the close and released promptly after post-mode.

## Chronology disclosure

The Pre-Mode report was produced before the `--classify-only` evidence record (evidence `pre_close.captured_at` 04:52:13Z; report `generated_at` 04:53:00Z is the report timestamp written at creation after the in-process step 2b read at about 04:51Z). The `agreed` outcome rests on content comparison of verdict and qualifying feature set.

## POSIX portability note

The PR's first CI run failed on Linux. Fixed in the PR (`fix(cascade-close): POSIX portability and Copilot round 1`): the Linux open-writer probe now tolerates hidden same-uid helper processes that predate the journal, and foreign-uid fd tables no longer make the writer scan fail. The affected modules were verified on Linux under WSL Ubuntu. Process-race tests were made deterministic under load (hold barrier; the finished-in-window detach outcome is accepted).

## Follow-ups

Deferred review findings and operator-listed items were captured as stash entries per P-021 C2: `967F9DC1`, `F0EF3FC2`, `50548692`, `B6D2B6FE`, `7CDE1693`, `E99F6EC9`, `F1AEC34D`, `EB8888A2`, `A22A7FD5`, `C3FBB38D`. They remain active stash intake for Stage triage; Ship does not triage them.

## Source artifact cleanup

* 218-S: `custom_fields.source_stash_id` none; `custom_fields.source_deliberation_id` none. No source stash entry was archived.
* 211-F: `custom_fields.source_stash_id` none; `custom_fields.source_deliberation_id` none.
* The unrelated stash intake carried forward in the branch's first commit was not touched.

## Residual risk and conditions

`closure_status: READY`. No open conditions. The invariants to preserve: a killed or detached `cascade-close` never leaves unrecoverable state (journal plus `--recover`), and `--recover` never fabricates unobserved facts. Monitoring: the next cascade-close run should use `--detach` followed by `--poll` (or attached with `--caller-wait`), and the closure-evidence gate remains the verifier. Rollback: revert the merge commit through a PR (merge commit revert); owner: Ship / operator.

## Compaction (P-020)

`compaction_status: done`. compact-context (`target: all`) ran a Tier-1 consolidation of this release unit's memory: the Stage memory `docs/memory/2026-10-16-stage-369f8062-cascade-close-recovery.md` was consolidated into `docs/memory/compacted/2026-10-18-218-s-211-f-compacted.md` and the original archived to `docs/archive/memory/2026-10-16/stage-369f8062-cascade-close-recovery.md` (nothing else referenced it). The Ship session memory `docs/memory/2026-10-18/ship-218-s-211-f-post-merge-closure.md` stays live (linked from the summary), per the 213-S precedent. The plan `docs/plans/2026-10-16-cascade-close-recovery-and-journaling-plan.md` and its hardening record were deliberately not consolidated into a decided-plan: they stay live as the reference for the implemented design and the open OQ-4 decision (repair of the 214-S evidence). Unrelated historical memory was not compacted.

## Close evidence

Record: `docs/closure/evidence/218-S-211-F-close-evidence.json` (phase `post_close`).
