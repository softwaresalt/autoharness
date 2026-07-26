---
shipment: 094-S
feature: 089-F
pr: 232
merge_commit: afa25f2e27abe32b89981cf2a280cdab0349ae13
merged_at: "2026-07-26T08:56:28Z"
closure_status: READY
---

# 094-S / 089-F Post-Merge Closure — 088-F Review-Followup Hardening

Two small TDD hardening fixes for two Copilot review follow-up findings
against the throwaway, disabled-by-default 088-F compression experiment.
Low blast radius: 2 files changed (`workspace.py`, `benchmark.py`), 3 test
files extended, no schema/CLI-distribution changes, nothing in
`src/autoharness` imports the experiment.

## Merge Confirmation

- `gh pr view 232 --json state,mergedAt,mergeCommit` → `state: MERGED`,
  `mergedAt: 2026-07-26T08:56:28Z`, `mergeCommit.oid: afa25f2e27abe32b89981cf2a280cdab0349ae13`.
- Merge commit verified 2 parents (`83a96432792194abea11cf53909dc041f3ba103d`
  main tip, `fd76df4afc16c89f03c6d6257224c85ceffbf150` feature branch HEAD) —
  a genuine merge commit (P-009 / Constitution XI, no squash/rebase).
- Present on `origin/main` (`git branch -r --contains afa25f2e...` → `origin/main`).

## Runtime Verification

**Surface**: the only runtime surface touched is the 088-F experiment itself
(disabled by default via `BRAINSPACE_EXPERIMENT_ENABLED`, unset = no-op
pass-through, no store created). No base-harness runtime path changed.

| Check | Method | Result |
|---|---|---|
| Isolation — nothing in `src/autoharness` imports the experiment | `Get-ChildItem src\autoharness -Filter *.py -Recurse \| Select-String brainspace` | **PASS** — zero matches |
| Fail-safe `{}` passthrough for non-string payload `cwd` (089.001-T) | `test_dict_payload_with_non_string_cwd_raises_containment_error` + `test_non_string_payload_cwd_is_safe_noop_not_a_crash` (resolver + subprocess entrypoint levels) | **PASS** |
| Benchmark early-decline evidence carries `capture_failed`/`provenance` (089.002-T) | `test_early_decline_case_carries_capture_failed_into_result` + `test_early_decline_case_carries_non_live_provenance_into_result` | **PASS** |
| Experiment suite at merged HEAD | `python -m pytest experiments/088-compression-experiment/tests -q` | **PASS** — 231 passed, 2 skipped (tiktoken-dependent, expected) |
| Base harness regression | `python -m pytest tests -q --ignore=experiments` | **PASS** — 680 passed, 140 subtests passed, unchanged from baseline |
| CI (GitHub Actions) at merge SHA | `gh pr checks 232` pre-merge | **PASS** — `ci gate`, `detect code changes`, `test` all green |

No manual/human checkpoint required — no UI, no deployed service, no
operator-facing runtime change.

## Operational Closure

- **Healthy signals**: full test suites green pre- and post-merge; P-018
  copilot-review gate SATISFIED/PASS at merge HEAD `fd76df4a`; 1 Copilot
  review finding (test non-determinism re: `tiktoken` availability) fixed,
  replied, and resolved before merge — 0 unresolved threads.
- **Failure signals to watch**: none identified; the experiment remains
  disabled by default and isolated, so no production monitoring applies.
- **Rollback**: revert the merge commit `afa25f2e27abe32b89981cf2a280cdab0349ae13`
  on `main` (single commit revert; no dependent commits followed it before
  this closure).
- **Owner**: Ship agent (autonomous dark-mode execution); operator
  `@softwaresalt` for any follow-up routing.
- **Residual follow-ups**: none opened by this shipment. (The two prior
  093-S follow-ups — `workspace.py:152` non-string `cwd` and
  `benchmark.py:215` early-decline evidence gap — are exactly what 089.001-T
  and 089.002-T closed; no new findings surfaced during this shipment's
  build or review.)

**Closure verdict: READY.** No conditions outstanding.

## Backlog Reconciliation

Single-artifact safe-close (no `backlogit shipment ship` cascade):
`089.001-T` and `089.002-T` archived; shipment record `094-S` archived.
Feature `089-F` preserved `active` in the queue (094-S's manifest was
task-only, not the full feature).
