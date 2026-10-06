---
type: session-memory
agent: ship
shipment: 195-S
feature: 189-F
date: 2026-10-06
mode: dark (P-017)
---

# Ship session: 195-S / 189-F (S(B-entry))

## Startup (2026-10-06T05:51Z to 06:01Z)

* Preflight by the Orchestrator at 05:51Z: backlogit 1.11.0 CLI, index
  synced, 99 checkpoints with 0 active and 0 quarantined (no recovery).
* Intercom, engram and graphtor tools are not exposed in this runtime
  (degraded visibility; milestones are reported with UTC timestamps).
* `uv run autoharness` cannot build here (no network for `hatchling`), and
  the global `autoharness.exe` is a stale non-editable 1.5.0 install. Every
  `autoharness` command in this session runs the checkout's own CLI:
  `python .proof-scratch/195-S/ah.py ...`, a git-ignored wrapper that puts
  `src` on `sys.path` and calls `autoharness.cli:main`.
* Temp reroute (Principle IV, stash `B99B661D`): every test run, hook and
  `git push` sets `TEMP`/`TMP`/`TMPDIR` and `GIT_CEILING_DIRECTORIES` to the
  git-ignored `.proof-scratch/195-S/tmp`.

## IM-14 harvest-commit audit (before the first claim, 05:57Z)

The plan's detector (`DETECTOR`, `normalize`, `_spanning` from
`tests/test_harness_noclaim_audit.py`) ran over every added line of each
non-merge harvest commit's own diff, including adjacent-line joins, plus a
camelCase scan:

| Commit | Content | Files | Added lines | Hits | Disposition |
|---|---|---:|---:|---:|---|
| `90f23361` | harvest S(B-entry) (195-S, 189-F, 189.001-T to 189.003-T) | 5 | 231 | 3 | All three are the AC "IM-14: no added text claims race, TOCTOU or hardlink-alias resistance." (non-claim) |
| `d633cd58` | AC bullet fix in S(B-core) tasks | 3 | 15 | 0 | none |
| `7ca13f66` | harvest S(IM-10) (190-F, 190.001-T, 190.002-T) | 6 | 168 | 3 | 190-F DoD and the 190.001-T / 190.002-T ACs, each the same IM-14 disclaimer (non-claim) |

No join hit and no camelCase hit. The harvest merge that brought these
commits to `main` is `e38ac305` (PR #457), conflict-free and audited at
193-S (IM-14-F67).

## Pre-claim decisions

* Working tree on `main` before branching: the uncommitted stash line
  `A34432A2` (left by a prior Orchestrator run) is carried unchanged into the
  first backlog commit on the feature branch. The operator-local
  `.github/copilot/settings.local.json` (modified) and
  `.github/copilot/settings.json` (untracked) are known out-of-scope operator
  state: never modified, stashed, discarded, staged or committed. The P-011
  clean-tree check is read as "no uncommitted work of this shipment"; these
  three paths are recorded here as the only exceptions.
* Stash `672A3F27` (B-entry design inputs from the 194-S review) is still
  untriaged by Stage. Ship reads it only as non-binding implementation
  guidance consistent with the frozen task ACs; it is neither triaged nor
  mutated (P-010).

## Claim (06:00Z)

* `pre_claim` on `main`: exit 0 (`BRANCH_CREATE_ELIGIBLE`, predecessor
  `194-S` explicit). Branch
  `feat/195-s-s-ship-lifecycle-unit-b-entry-ledger-and-digest-reducer-with-early-return-resolve-shipment-and-harness-resolve-cli`
  created from `main` at `1a6648de`. `pre_claim` again on the branch: exit 0
  (`BRANCH_OK`, `WORKTREE_TOPOLOGY_OK`). No bootstrap grant.
* `backlogit shipment claim 195-S` wrote the claim (195-S, 189-F and the
  three tasks all `active`, the P-002.7 post-claim state) but its process did
  not return; it was stopped after the write was confirmed.
* `post_claim`: exit 0, sole active shipment. CLI re-read: `status: active`.
  `CLAIM_VERIFY_OK: shipment 195-S reached active and is the sole active
  shipment`.
* Intake reconcile (`mode: pre`, `expected_status: active`): 4 items matched,
  0 orphans, record-consistent -> `PROCEED`.

## Task execution (06:02Z to 07:28Z)

Telemetry `begin` returned `status: disabled` for every task, so no context
was carried and no close was recorded. backlogit `move` (and the shipment
claim) write their change and then do not return; each was stopped once the
write was confirmed on disk and in `.backlogit/logs/<id>.jsonl`
(`pre_task_completion_gate_passed`, `artifact_mutation committed`).

Environment prechecks, before each task's first write: `git worktree list`
showed one worktree (`C:/Source/GitHub/autoharness`), `git status --porcelain`
showed no change to the task's files (only the operator-local Copilot
settings), and the canonical command ran from the repository root.

Canonical command, as run on this host: `$env:PYTHONPATH='src'; python -m unittest discover -s tests`
in PowerShell, with `TEMP`, `TMP`, `TMPDIR` and `GIT_CEILING_DIRECTORIES`
all set to `C:\Source\GitHub\autoharness\.proof-scratch\195-S\tmp` in the
same invocation. This is the plan's `PYTHONPATH=src python -m unittest discover -s tests`.

| Task | Start | RED commit | GREEN commit | Elapsed | Estimate |
|---|---|---|---|---:|---:|
| 189.001-T (B4a) | 06:02Z | `9b395203` | `e929dae5` (06:34Z) | 32 min | 85 min |
| 189.002-T (B4b) | 06:35Z | `68033fe5` | `99c496d0` (07:01Z) | 26 min | 110 min |
| 189.003-T (B5) | 07:03Z | `76df115c` | `83b57e87` (07:28Z) | 25 min | 80 min |

No task came near the 30-minute overrun stop.

### RED records (IM-13, FI-9)

Every RED run: native exit 1, and the only errors or failures are listed here.

* **189.001-T (B4a).** `Ran 3367 tests`, `FAILED (errors=13, skipped=57)`.
  Roster `LedgerDigestRosterTests`, each ERROR with
  `NotImplementedError("AHLC_B4A_LEDGER_DIGEST:<test>")`:
  `test_absent_candidate_appearing_before_recheck_is_input_changed`,
  `test_digest_binds_first_and_recheck_observations_on_mutation`,
  `test_digest_golden_fixture`,
  `test_digest_is_lowercase_hex_and_stable_across_runs_and_locations`,
  `test_digest_preimage_is_domain_separated_and_length_framed`,
  `test_empty_ledger_recheck_reads_nothing`,
  `test_every_bound_input_changes_the_digest`,
  `test_ledger_records_every_candidate_and_surface_read`,
  `test_mutated_record_between_read_and_recheck_is_input_changed`,
  `test_mutated_surface_between_read_and_recheck_is_input_changed`,
  `test_recheck_not_completed_manifest_is_manifest_unreadable`,
  `test_recheck_not_completed_maps_to_the_original_stage_code`,
  `test_recheck_reobserves_the_ledger_with_new_claims`.
  CONST-II-F01 determination: not applied (the golden digest test is a roster
  test). IM-14-F52: no detector hit added, so the audit test stayed out of
  B4a's Files.
* **189.002-T (B4b).** `Ran 3381 tests`, `FAILED (errors=11, skipped=57)`.
  Roster `ReducerRosterTests`, each ERROR with
  `NotImplementedError("AHLC_B4B_REDUCER_EARLY_RETURN:<test>")`:
  `test_class_1_and_1b_beat_every_lower_class`,
  `test_early_return_issues_no_recheck_after_a_first_pass_read_limit`,
  `test_higher_class_beats_lower_class_without_short_circuit`,
  `test_im04_byte_codes_never_raised_at_an_absent_candidate`,
  `test_im04_read_limit_injection_at_each_read_stage`,
  `test_im04_two_read_limit_errors_select_the_first_occurring_code`,
  `test_im16_a_completed_disagreement_before_a_read_limit_is_input_changed`,
  `test_im16_b_read_limit_first_gives_that_code_and_stops`,
  `test_no_surfaces_required_reads_no_surface`,
  `test_resolve_returns_the_result_and_the_reader_usage`,
  `test_resolve_shipment_calls_resolve_with_the_fi2_defaults`.
  An earlier B4b RED run was stopped and discarded before it finished,
  because a scratch normalization step had truncated the uncommitted test
  file; the file was recreated and the recorded run is the complete one.
* **189.003-T (B5).** `Ran 3391 tests`, `FAILED (failures=1, errors=7, skipped=57)`.
  Seven roster tests ERROR with `NotImplementedError("AHLC_B5_CLI_ENVELOPE:<test>")`;
  the RED stub raised that marker when `--workspace` was present and
  otherwise kept the existing `Unknown command` path (exit 1). Gap
  characterization (CONST-II-F01): the captured-help structural test FAILED
  with exit 1 `Unknown command`; the audit structural tests passed. The
  local review then moved three of the seven out of the roster, because they
  reach no CLI stub on their own: `test_all_47_codes_through_resolve_validate_against_the_schema`
  (characterization: it passes over the green B4b resolver),
  `test_parse_errors_emit_no_document` and
  `test_help_prints_to_stdout_and_emits_no_document` (gap characterization:
  the command did not exist). The RED roster of record is the remaining four:
  `test_one_document_per_state_through_the_cli`,
  `test_default_reachable_codes_through_resolve_shipment_and_the_cli`,
  `test_stdout_is_one_document_and_one_lf_in_a_real_process`,
  `test_invalid_shipment_id_is_a_document_not_a_parse_error`, each ERROR with
  its own marker in that run.

GREEN runs: B4a `Ran 3367 tests OK (skipped=57)`; B4b `Ran 3381 tests OK (skipped=57)`;
B5 `Ran 3391 tests OK (skipped=57)`; each native exit 0. A test or review
PASS confers no claim authority (IM-15).

## Local review (07:15Z to 07:33Z)

Nine personas, read-only (Correctness, Python, Security, Maintainability,
Architecture, Constitution, Scope Boundary, Schema-CLI-Docs Coupling,
Learnings) over `git diff 1a6648de` at the B5 GREEN content. Result before
fixes: `BLOCKED` (Constitution P1: three B5 roster tests were RED only
through a preamble call). All in-scope P1/P2 items and most in-scope P3 items
were fixed in the review-fix commit; out-of-scope items were captured as
P-021 deferred stash entries (see the PR body).

P-021 deferred captures from the local review (threadless, pre-PR): `8BB8CCD9` (YAML composer cost cap), `B868F321` (Windows UNC link targets), `09ECA5E2` (S(D) D1/D3, operator doc and CHANGELOG inputs), `7E1BC498` (resolver and test maintainability).
