---
shipment: 216-S
feature: 209-F
pr: 541
merge_commit: 30a6bd9cdddcb71c150422269c91fb418437fd53
reviewed_head: b75e6c34
date: 2026-10-19
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/216-S-209-F-close-evidence.json
---

# 216-S / 209-F Post-Merge Closure: Removal of the agent-intercom Capability Pack

## Summary

Shipment 216-S (feature 209-F, tasks 209.001-T through 209.023-T) merged through PR #541 as merge commit `30a6bd9cdddcb71c150422269c91fb418437fd53` (merge commit strategy, P-009; two parents verified, ancestor of `origin/main`). The change removes the agent-intercom capability pack from the product and the dogfood harness (operator decision, stash 0FD06900): a shrinking-ledger guard test (enforced empty, scoped tombstones), schema contract bumps with new published mirrors (workspace-profile 1.1.0, harness-manifest 1.1.0, harness-config 1.3.0; every older mirror byte-identical), the Dark Factory Visibility Protocol relocated into workflow-policies P-017 (policy 1.37.0), legacy tolerance (`removed-capability-pack` warning and `remove-retired-capability-pack` proposal, never a blocker), the constitution amendment 1.0.0 to 1.1.0 with its sync-impact report, sweeps of instructions, agents, skills, foundation docs, docs and telemetry docs, deploy wrapper warn-and-skip, and removal of the registry entry and overlay files. `.autoharness/config.yaml` changed by exactly one removed line (the pack entry).

This closure was executed under the contract on `main` after the merge. This shipment itself edited the Ship agent and the `shipment-reconcile` skill (broadcast and approval-channel wording only); both merged versions were re-read before the close (`git diff` of the two files between the pre-merge and merge commits): the safe-close and cascade-close algorithm is unchanged, and the destructive-command approval wording now reads "explicit operator clearance through the workspace's native approval path".

## Gates

* Reviewed HEAD of the PR: `b75e6c34` (PR head at merge). Local multi-persona review at `36455082`: nine personas (Correctness, Python, Maintainability, Constitution, Learnings, Template Integrity, Schema-CLI-Docs Coupling, Scope Boundary, Security); one P1 (a legacy manifest overlay artifact record would have raised a `missing-template-source` blocker) and several P2 were fixed in `32078923`, `528ef1bb`, `7a2e5aca`, `b88ec43f`, `173537d9`, and a delta review was clean. The remaining findings were deferred per P-021 C2 (see Follow-ups).
* Full local build: `PYTHONPATH=src python -m unittest discover -s tests` ran 4542 tests OK at the PR head (pre-push hook, plus `markdownlint **/*.md`); CI `test` and `ci gate` green. Linux (WSL Ubuntu, `git archive` extract, no worktree): deploy-wrapper (sh), removed-pack guard and tolerance, schema-contract, registry, dogfood-state, install/discovery/tune and visibility modules OK. `autoharness verify-workspace --workspace .`: 0 strict schema blockers, 0 blockers, 0 warnings (ten targeted checks and the CLI exit status are unchanged from the pre-shipment baseline).
* DoD evidence: `git grep -il intercom` over live surfaces returns only classified frozen mirrors, telemetry vocabulary and scoped tombstones; no historical record was rewritten; legacy fixtures (manifest 1.0.0, profile 1.0.0, config 1.0.0-1.2.0) still warn without crashing.
* Copilot review: two rounds. Round 1 (`PRR_kwDORzpWpM8AAAABTG6oBw`, two threaded findings): the pr-lifecycle unconditional STOP that conflicted with the DARK_MODE_ACTIVE approval path (also in the Ship template) was fixed in `d2103336`; the wrapper/home version-skew finding was deferred to stash `D1D24EA6`; both threads replied to and resolved. Round 2 (`PRR_kwDORzpWpM8AAAABTHueKA` at `b75e6c34`) reported no open issues. P-018 gate `SATISFIED` (run twice, the second immediately before merge). Admin fallback not used. The review was requested through the GraphQL `requestReviews` technique recorded in `docs/compound/2026-10-12-requesting-copilot-review-via-graphql-bot-id.md`, per the operator's explicit session brief.
* Runtime verification: CLI surface only (`verify-workspace`, deploy wrappers); clean as above.
* Releasability: `READY`.

## Shipment close

* Lifecycle topology gate (`pipeline-topology --mode agent --shipment 216-S --phase lifecycle`) before the safe-close: exit 0 (`BRANCH_POST_MERGE_CLOSURE_ELIGIBLE`).
* Pre-mode (`expected_status: done`): PROCEED. Report `.backlogit/reconcile/216-S-pre-20261019-093000.md`. 209-F is the qualifying feature (declared `active`, matched); the 23 tasks were declared `done` (resident in `archive/`, matched); no orphans.
* Step 0(d) agreement-check outcome: `agreed` (CASCADE, qualifying feature set `209-F` in both the pre-mode report and the `--classify-only` evidence record; engine VERIFIED on backlogit 1.11.0, CLI surface).
* Close path: `cascade`. `--classify-only` exited 0 (CASCADE). Two `--detach` attempts each ended `never_started` (`--poll` exit 2; the journal proves no child was spawned, nothing was mutated and the evidence record rolled back to `pre_close`; cause and routing in `docs/compound/2026-10-19-cascade-close-never-started-under-host-load.md`). The mutating `autoharness shipment cascade-close` then ran attached with `--timeout 2888` (N = 25, B = ceil(1.5 x (800 + 45 x 25)) = 2888 s) and `--caller-wait 3488` (timeout + 600 s), destructive-command approval taken from the operator's explicit session instruction to run `cascade-close` (not inferred from merge approval or dark-mode activation). It exited 0 after about 47 minutes (21:57:32Z to 22:44:26Z); `phase: post_close`, postcondition verdict `pass`, `returned_ids` empty, `archived_ids` = the 24 manifest items plus 216-S, `parent_id` preserved, baseline invariant, linked-deliberation snapshot byte-identical, shipment `archived_status: shipped`. No direct `backlogit shipment ship` call was made and no `--recover` was needed. The timestamps in the evidence record's `invocation.stderr.excerpt` are engine log lines (some say "index may be stale after mutation"), not archive timestamps; the pre-mode and post-mode report `generated_at` values are approximate (hand-recorded) and the evidence record is authoritative for ordering.
* Linked-Deliberation Disposition (P-015 INV-12): `DISPOSITION_COMPLETE`. The snapshot found no linked deliberations (empty disposition set, no unresolved references); nothing archived.
* Post-mode: PROCEED. Report `.backlogit/reconcile/216-S-post-20261019-224500.md`.
* Lifecycle lock `.backlogit/queue/216-S.md` was acquired for the close and released after post-mode.

## Follow-ups

Deferred review findings (P-021 C2 captures, active stash intake for Stage triage; Ship does not triage them): `D34EDB2F` (deploy wrapper hardening), `342325D6` (policy and constitution wording), `B060EF22` (schema-contract chain and planner purity), `A36DC144` (test hygiene), `D1D24EA6` (wrapper/home version skew, from the Copilot thread). Post-merge follow-up captured at closure: `76120114` (cascade-close timeout calibration and the detach authorization window under host load).

## Source artifact cleanup

* 216-S: `custom_fields.source_stash_id` none; `custom_fields.source_deliberation_id` none. No source stash entry was archived (the staging stash `0FD06900` was already consumed and archived at Stage).
* 209-F: `custom_fields.source_stash_id` none; `custom_fields.source_deliberation_id` none.
* The unrelated stash intake carried forward during the shipment was not touched.

## Residual risk and conditions

`closure_status: READY`. No open conditions. Invariants to preserve: no live surface references the retired pack outside the guard's classified allowlist (the guard test is enforced); published schema mirrors stay byte-identical; legacy documents listing the retired pack only warn. Monitoring: `autoharness verify-workspace` on this workspace (strict blockers 0). The cascade-close run finished 74 s inside its sized timeout (2814 s run, 2888 s timeout) on a loaded host; the stash entry `76120114` states 62 s, which is a measurement slip (the evidence record gives 74 s) and is left unedited under the P-021 single-write rule. The next closure should recompute the budget with margin (stash `76120114`). Rollback: revert the merge commit through a PR; owner: Ship / operator.

## Compaction (P-020)

`compaction_status: done`. compact-context (`target: all`) ran a Tier-1 consolidation: the Stage memory `docs/memory/2026-10-14-stage-0fd06900-remove-agent-intercom.md` was consolidated into `docs/memory/compacted/2026-10-19-216-s-209-f-compacted.md` and the original archived (`git mv`) to `docs/archive/memory/2026-10-14/stage-0fd06900-remove-agent-intercom.md` (nothing else referenced it). The Ship session memory `docs/memory/2026-10-19/ship-216-s-209-f-post-merge-closure.md` stays live. The plan, plan review and constitution sync-impact report were deliberately not consolidated: they remain the reference for the retired-pack guard and tombstones. Unrelated historical memory was not compacted.

## Close evidence

Record: `docs/closure/evidence/216-S-209-F-close-evidence.json` (phase `post_close`).
