---
shipment: 159-S
feature: 151-F
pr: 435
merge_commit: cb474a0a7d1fdfe2bbfe0dd3e2a6110aefb533ab
reviewed_head: 494089ab638a7d111618ff6f9fd30febbc635934
surface: cli
verdict: PASS
---

# 159-S / 151-F Runtime Verification -- SHIP-1 v1.5.0 Shipped-Guardrail Contract Restoration

## Scope

Feature `151-F` (7 tasks, `151.001-T`..`151.007-T`) restored the
`closure_source_artifact_cleanup` and `ship_release_closure_sequence`
`verify-workspace` guardrail assertions that were unsatisfiable against the
templates that generate the artifacts they check (root cause: no test
validated a guardrail against a *rendered* template). PR #435 merged this
work to `main` (merge commit `cb474a0a7d1fdfe2bbfe0dd3e2a6110aefb533ab`,
reviewed HEAD `494089ab638a7d111618ff6f9fd30febbc635934`).

## Validator Contract

Per `.autoharness/workspace-profile.yaml` `runtime_validation`:

* `validator_manifest.surfaces`: `cli` only, adapter hint `command`, probe
  `cli-help` (`uv run autoharness --help`), required.
* `validation_expectations`: `surfaces_expected: [cli]`, `minimum_verdict: PASS`,
  invariant "the autoharness CLI starts without import, packaging, or
  option-parsing failures", release blocker "the CLI help smoke check fails".
* `releasability.required`: `false` for this workspace profile.

## Execution

* Adapter: `command` (CLI adapter, per `adapter_hint`).
* Command: `uv run autoharness --help` (post-merge, on `main`-equivalent
  worktree state at merge commit ancestor).
* Expected: command exits 0 and prints CLI help text.
* Observed: exit code `0`; full command listing printed (`autoharness home`,
  `version`, `verify-workspace`, `gate check`, `gate size`,
  `gate copilot-review`, `gate pipeline-topology`, `gate dag-readiness`,
  `telemetry begin`/`record`, `eval`, `setup-*`, `help`).
* Additional context: the shipped work's own executable acceptance criteria
  (151.003-T's render-aware template-resolution harness and 151.004-T's
  table-driven assertion sweep) already exercise the `closure_source_artifact_cleanup`
  and `ship_release_closure_sequence` guardrails against *rendered* template
  output as part of the merged test suite (`2057 tests, OK (skipped=20)` per
  the PR's Local Review Readiness record) -- this is the change's own
  in-repo regression coverage for the defect it fixes, and is not re-run here
  since it is already CI-verified evidence, not a separate runtime surface.

## Verdict

**PASS.** The only declared runtime surface (`cli`) starts cleanly with no
import, packaging, or option-parsing failures. No release blocker condition
observed. No manual checkpoints were declared in the validator manifest.

## Follow-Ups

None beyond the pre-existing, already-captured P-021 deferred entry `24A85BF8`
for the unrelated flaky `test_graphtor_mcp_shim.py` test (stash follow-up
recorded on PR #435, requires Stage deliberation, low priority) -- out of
scope for this shipment's runtime surface and not a release blocker.
