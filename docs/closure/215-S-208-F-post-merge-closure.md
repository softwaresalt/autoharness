---
shipment: 215-S
feature: 208-F
pr: 539
merge_commit: 8e807a255cd26c502a0d2e184925ccb1dfc9629d
reviewed_head: e312db3c
date: 2026-10-19
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/215-S-208-F-close-evidence.json
---

# 215-S / 208-F Post-Merge Closure: Model Routing Route Catalog and Subagent Site Bindings (schema 1.2.0)

## Summary

Shipment 215-S (feature 208-F, tasks 208.001-T through 208.014-T) merged through PR #539 as merge commit `8e807a255cd26c502a0d2e184925ccb1dfc9629d` (merge commit strategy, P-009; two parents verified, ancestor of `origin/main`). The change adds the tier-delta route catalog (`model_routing.routes`) and installed-agent site bindings (`model_routing.bindings`) as an additive harness-config schema 1.2.0 published as a new mirror (the 1.1.0 mirror is byte-identical and pinned by test), the resolver bound/unbound branches, the disk-first site registry, verify-workspace catalog, binding, site, inert-key, unknown-key and alias checks, the shared render-time site composition and installed-subagent route drift (bindings opt-in), install-harness and tune-harness surfaces, the P-013.5 amendment (policy 1.36.0) and the docs and changelog. No routing value changed; `.autoharness/config.yaml` changed only by its `schema_version` marker (operator confirmation 040-DL OQ9, 2026-10-12).

This closure was executed under the contract on `main` after the merge: the Ship agent instructions and the `shipment-reconcile` skill were unchanged by this shipment (no diff in either file), so the contract in force before and after the merge is identical.

## Predecessor exception (disclosed)

215-S depends on 214-S, whose closure evidence is permanently incomplete (cascade-close killed mid-run; `--recover` refuses because there is no journal). The operator-delegated bootstrap grant `.autoharness/bootstrap-grants/215-S.yaml` (merged in PR #538) was consumed at the Ship `ship_pre_branch` and `ship_pre_claim` sites (`forced: true`, token `PREDECESSOR_CLOSURE_INCOMPLETE`, predecessor `214-S`, head `8c13c9a3`); audit log `.autoharness/gates/pipeline-topology-force-audit.log`. No `--force` was used and no grant was authored or edited by Ship.

## Gates

* Reviewed HEAD of the PR: `e312db3c` (PR head at merge). Local multi-persona review at `ef81335e`: ten personas (Correctness, Python, Maintainability, Constitution, Learnings, Architecture, Scope Boundary, Security, Template Integrity, Schema-CLI-Docs Coupling); P0=0, P1=0. Five in-scope completions were fixed (`b434cd60`, `fe59badc`, `81c70983`, `8863111c`, `79ad507a`) and a delta review of them was clean. Remaining findings were deferred per P-021 C2 (see Follow-ups).
* Full local build: `PYTHONPATH=src python -m unittest discover -s tests` ran 4372 tests OK (63 skipped) at `79ad507a` and 4378 OK at `e312db3c`; the pre-push hook passed at both PR heads; CI `test` and `ci gate` green. Linux (WSL Ubuntu, `git archive` extract, no worktree): routing, schema, verify-workspace, policy and tune/install modules (175 + 169 + 27 + 24 + 21 + 14 tests) OK. markdownlint on touched markdown: only pre-existing MD041/MD001. `autoharness verify-workspace --workspace .`: 0 strict schema blockers, 0 blockers, 0 warnings.
* Copilot review: two rounds. Round 1 (`PRR_kwDORzpWpM8AAAABS8GbdA`, 1 threaded finding: re-render of a legacy schema_version must omit empty `routes`/`bindings`) was fixed in `e312db3c`, replied to and resolved. Round 2 (`PRR_kwDORzpWpM8AAAABS8WhnQ` at `e312db3c`) reported no open issues. P-018 gate `SATISFIED` (run twice, the second immediately before merge). Admin fallback not used. The review was requested through the GraphQL `requestReviews` technique recorded in `docs/compound/2026-10-12-requesting-copilot-review-via-graphql-bot-id.md`, per the operator's explicit session brief.
* Runtime verification: CLI surface only (`verify-workspace`); clean on this workspace as above.
* Releasability: `READY`.

## Shipment close

* Lifecycle topology gate (`pipeline-topology --mode agent --shipment 215-S --phase lifecycle`) before the safe-close: exit 0 (`BRANCH_POST_MERGE_CLOSURE_ELIGIBLE`).
* Pre-mode (`expected_status: done`): PROCEED. Report `.backlogit/reconcile/215-S-pre-20261019-022000.md`. 208-F is the qualifying feature (declared `active`, matched); the 14 tasks were declared `done` (resident in `archive/`, matched); no orphans.
* Step 0(d) agreement-check outcome: `agreed` (CASCADE, qualifying feature set `208-F` in both the pre-mode report and the `--classify-only` evidence record; engine VERIFIED on backlogit 1.11.0, CLI surface).
* Close path: `cascade`. `--classify-only` exited 0 (CASCADE). The mutating `autoharness shipment cascade-close` ran `--detach` (exit 9) then `--poll --wait` until exit 0, with `--timeout 2280` (N = 16, B = ceil(1.5 x (800 + 45 x 16)) = 2280 s), destructive-command approval taken from the operator's explicit session instruction to run `cascade-close` with `--detach` and `--poll` (not inferred from merge approval or dark-mode activation). The run lasted about 27 minutes (02:12:41Z to 02:39:31Z); `phase: post_close`, postcondition verdict `pass`, `returned_ids` empty, `archived_ids` = 208-F, 208.001-T through 208.014-T and 215-S, `parent_id` preserved, baseline invariant, linked-deliberation snapshot byte-identical, shipment `archived_status: shipped`. No direct `backlogit shipment ship` call was made and no `--recover` was needed. The timestamps inside the evidence record's `invocation.stderr.excerpt` are engine log lines (some say "index may be stale after mutation"), not archive timestamps; the per-record `updated_at` values in the archived files are the mutation times. The pre-mode and post-mode report `generated_at` values are approximate (hand-recorded); the evidence record is authoritative for ordering.
* Linked-Deliberation Disposition (P-015 INV-12): `DISPOSITION_COMPLETE`. `040-DL` and `037-DL` are `retained_shared_reference` (still referenced by other stash entries), byte-identical, nothing archived; no unresolved references.
* Post-mode: PROCEED. Report `.backlogit/reconcile/215-S-post-20261019-024500.md`.
* Lifecycle lock `.backlogit/queue/215-S.md` was acquired for the close and released after post-mode.

## Follow-ups

Deferred review findings (P-021 C2 captures, active stash intake for Stage triage; Ship does not triage them): `623963D0` (registry/render-seam unification), `81E933B2` (resolver and registry hardening), `7FB1D9BF` (test hygiene), `9669DD1E` (pre-existing and adjacent gaps). Post-merge follow-up stash captured at closure: `B891B448` (Ship template branch-naming mismatch with the topology branch-ownership check).

## Source artifact cleanup

* 215-S: `custom_fields.source_stash_id` none; `custom_fields.source_deliberation_id` none. No source stash entry was archived.
* 208-F: `custom_fields.source_stash_id` none; `custom_fields.source_deliberation_id` none. The feature description cites stash `BF66F08B` and `040-DL`; `BF66F08B` was already consumed and archived at Stage, and `040-DL` was retained (`retained_shared_reference`).
* The unrelated stash intake carried forward during the shipment was not touched.

## Residual risk and conditions

`closure_status: READY`. No open conditions. Invariants to preserve: the 1.1.0 config schema mirror stays byte-identical; `model_routing` is closed at 1.2.0; the renderer and the drift check read one shared composition function. Monitoring: `autoharness verify-workspace` on this workspace (strict blockers 0); the follow-up tune chore (stash `56654C18`) will refresh the 13 stale installed subagent frontmatters reported as info. Rollback: revert the merge commit through a PR; owner: Ship / operator.

## Compaction (P-020)

`compaction_status: done`. compact-context (`target: all`) ran a Tier-1 consolidation: the shared Stage memory `docs/memory/2026-10-11-stage-bf66f08b-model-routing-v2.md`, which 214-S deliberately left live for this shipment, was consolidated into `docs/memory/compacted/2026-10-19-215-s-208-f-compacted.md` and the original archived (`git mv`) to `docs/archive/memory/2026-10-11/stage-bf66f08b-model-routing-v2.md`. The 214-S closure artifact still names the former path; it was left unedited as a historical record and the compacted summary records the new location. The Ship session memory `docs/memory/2026-10-19/ship-215-s-208-f-post-merge-closure.md` stays live. The R1-A and R1-B plans and the 040-DL deliberation were deliberately not consolidated: R2 to R4 follow-ups still reference them. Unrelated historical memory was not compacted.

## Close evidence

Record: `docs/closure/evidence/215-S-208-F-close-evidence.json` (phase `post_close`).
