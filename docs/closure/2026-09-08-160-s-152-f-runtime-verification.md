---
shipment: 160-S
feature: 152-F
pr: 439
merge_commit: 12b2d4a36f0cdcd9a07aa2cfc13b372cea2ef386
last_code_affecting_head: 373a24ea777bd19aa11c54fe655c99b34c8bb8e2
surface: cli
verdict: PASS
post_merge_reverification: "uv run autoharness --help re-run on new main post-merge; exit 0, CLI help text printed"
---

# 160-S / 152-F Runtime Verification -- SHIP-2 Release and CI Pipeline Fail-Closed Gates

## Scope

Feature `152-F` (3 tasks, `152.001-T`..`152.003-T`) hardens the PyPI
pre-publish probe used by `.github/workflows/release.yml` so that host
identity, response body shape, and exact version identity are all validated
before the probe reports the target version as already published (bindings
H2a/H2b), and the CLI wrapper now fails closed (exit 2 with an explicit
remedy message) instead of silently exiting 0. This report originally
recorded pre-merge validator evidence while PR #439 was still open against
`main`; PR #439 has since merged (`merge_commit`
`12b2d4a36f0cdcd9a07aa2cfc13b372cea2ef386`, frontmatter above), and the CLI
help smoke check was re-confirmed on the new `main` post-merge
(`post_merge_reverification` frontmatter above: exit 0, CLI help text
printed). The evidence below remains anchored to `last_code_affecting_head`
`373a24ea777bd19aa11c54fe655c99b34c8bb8e2` -- the most recent commit that
changed reviewed code -- and is unaffected by the merge itself, since no
further code changes occurred between that commit and merge. It is not a
claim about any HEAD later than the merge commit: see the Evidence Currency
Model in the companion
`docs/closure/2026-09-08-160-s-152-f-closure.md` for why this artifact
never asserts current-HEAD readiness for itself. Before the merge, the PR's
live current HEAD and P-018 Copilot-review state were tracked externally in
the PR body's `## Local Review Readiness` block and via `autoharness gate copilot-review
439`, evaluated at merge time.

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
* Command: `uv run autoharness --help`, run at `last_code_affecting_head`
  `373a24ea777bd19aa11c54fe655c99b34c8bb8e2` on the shipment branch worktree.
* Expected: command exits 0 and prints CLI help text.
* Observed: exit code `0`; CLI help text printed (`autoharness home`,
  `version`, ...).
* Additional context: this shipment does not touch the `autoharness` CLI
  package (`src/autoharness/`) at all -- its changes are confined to a new
  non-runtime module (`build_support/pypi_probe.py`, imported only by
  `.github/workflows/release.yml`'s release-time probe step, never by the
  installed package) and to `tests/`. The declared runtime surface (`cli`)
  is therefore unaffected by construction; the probe above confirms no
  incidental packaging or import regression was introduced. The change's own
  executable acceptance criteria -- the C1-C6 case table in
  `tests/test_build_support_pypi_probe.py` (20 tests, hermetic, no network
  I/O per binding H4) and the extended AST guard plus end-to-end push-context
  test in `tests/test_gates_topology.py` (113 tests) -- are this shipment's
  in-repo regression coverage for the release-workflow behavior it changes,
  and are CI-verified (full canonical suite: 2087 tests, 0 failures, 20
  skipped, re-run at each review-fix HEAD, including this
  `last_code_affecting_head`) rather than a separate runtime
  surface requiring live PyPI network verification. The release workflow
  itself (`.github/workflows/release.yml`) is not a runtime surface exercised
  by an operator; it fires on tag push and is out of scope for a pre-merge
  CLI/API/browser/background-job runtime probe -- its behavioral contract is
  what the hermetic test suite above verifies directly against injected
  responses.

## Verdict

**PASS.** The only declared runtime surface (`cli`) starts cleanly with no
import, packaging, or option-parsing failures at `last_code_affecting_head`.
No release blocker condition observed. No manual checkpoints were declared
in the validator manifest.

## Follow-Ups

Three new P-021 deferred-scope-expansion stash entries were captured this
session (all out of scope for this shipment, none affecting the runtime
surface verified above):

* `364681C4` -- `.github/workflows/release.yml` has no concurrency group;
  a same-tag concurrent-run race could let a losing run publish via
  `skip-existing: true`. Out of scope per plan binding H3 (no trigger
  configuration changes).
* `D25080A3` -- the `GithubHeadRefClearHelperGuardTests` AST guard doesn't
  detect `patched_environ(GITHUB_HEAD_REF=...)` calls nested inside wrapping
  expressions. Out of scope: task 152.003-T's freeze-scope is `tests/`-only
  and bounded to this one guard.
* `65402F31` -- `tests/test_gates_topology.py`'s `if __name__ == '__main__'`
  guard is misplaced ahead of 13 pre-existing classes plus this shipment's 2
  new ones, so direct-execution invocation misses most of the file's tests.
  Pre-existing (verified present in `main` baseline commit `04832c9e`);
  out of scope for 152.003-T; does not affect this project's canonical test
  invocation (`python -m unittest discover`).

Plus the pre-existing, already-captured P-021 deferred entry `24A85BF8`
(reused, not newly created) for the unrelated flaky
`test_graphtor_mcp_shim.py` test, first captured under shipment 159-S --
out of scope for this shipment's runtime surface and not a release blocker.

None of the four follow-ups above blocked this shipment's release-blocker
condition (the CLI help smoke check), and none required action before the
merge completed. All four remain open P-021 items for Stage triage and
deliberation; see the companion closure artifact's CI Status and Review
section for the same list.
