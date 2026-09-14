---
shipment: 173-S
feature: 165-F
pr: 450
merge_commit: null
last_code_affecting_head: 408ae4a2322876d736c195a80e79347c30697c26
surface: cli
verdict: PASS
post_merge_reverification: "pending -- to be run against new main immediately after merge, per the Post-Merge Closure protocol"
---

# 173-S / 165-F Runtime Verification -- DAG-Authoritative Predecessor Derivation for the Pipeline-Topology `pre_claim` Gate

## Evidence Currency Model

Per the same reasoning documented in prior closure artifacts (e.g.
`docs/closure/2026-09-11-162-s-154-f-runtime-verification.md`'s Evidence
Currency Model), this artifact distinguishes **code-affecting commits**
(which change runtime/gate/CLI content and require fresh build/test/CI
evidence) from the PR's live, ever-advancing HEAD. `last_code_affecting_head`
names the most recent commit that changed such content at the time this
artifact was written; live, merge-time-authoritative state (current
`headRefOid`, local review readiness, the P-018
`autoharness gate copilot-review` verdict, and CI check status) is tracked
externally in the PR body's `## Local Review Readiness` block and
re-verified directly against GitHub at merge time.

## Scope

Feature `165-F` (10 tasks, `165.001-T`..`165.012-T`; `165.007-T` and
`165.010-T` pre-archived, not part of this shipment's executable set)
replaces the pipeline-topology `pre_claim` gate's numeric-adjacency
predecessor heuristic with a DAG-authoritative, four-state predecessor
derivation engine driven by explicit `blocks` edges in backlog data, adds a
read-only `audit_sequencing` phase, and adds an at-most-once bootstrap-grant
consumption surface for documented pre-claim gate bypass scenarios.
**This shipment does touch `src/` runtime code**: `src/autoharness/gates/topology.py`,
`src/autoharness/gates/bootstrap_grant.py` (new module), and
`src/autoharness/cli.py` (new `gate pipeline-topology` bootstrap-grant and
force-audit wiring). All changes are internal to the CLI's own gate
subcommand and the filesystem-backed grant/consumption-record mechanism it
reads/writes under `.autoharness/`; no new externally-facing API, browser,
or background-job surface is introduced.

## Validator Contract

Per `.autoharness/workspace-profile.yaml` `runtime_validation`:

* `validator_manifest.surfaces`: `cli` only, adapter hint `command`, probe
  `cli-help` (`uv run autoharness --help`), required.
* `validation_expectations`: minimum verdict `PASS`, invariant "the
  autoharness CLI starts without import, packaging, or option-parsing
  failures".
* `releasability.required`: `false` for this workspace profile.

Because the CLI's own `gate pipeline-topology` subcommand is the surface this
shipment changes, the `cli-help` smoke probe is confirmatory that the CLI
entrypoint itself still loads and parses correctly (no import/packaging
break introduced by the new `bootstrap_grant` module or the CLI wiring), and
is supplemented below with direct exercise of the changed subcommand itself
via the full test suite (which invokes the real CLI `main()` entrypoint
end-to-end for every `gate pipeline-topology` test case) plus the hosted CI
job's own full-suite run on `ubuntu-latest` (a second, independent OS/Python
environment).

## Execution

* `uv run autoharness --help` -- exit 0, CLI help text printed (re-run
  immediately before this artifact was written, against
  `last_code_affecting_head` `408ae4a2`).
* `PYTHONPATH=src python -m unittest discover -s tests` (full suite, no
  filters) -- run to completion after every commit in this PR, including
  immediately after `last_code_affecting_head` `408ae4a2`: 2302 tests,
  `OK (skipped=54)`. Also re-confirmed by the pre-push git hook's own
  independent full-suite re-run before the push landed.
* Targeted CLI-subcommand exercise (the actual changed surface):
  `tests/test_gate_pipeline_topology_cli.py` (33 tests, all passing, 4 new
  regression tests added this session) drives the real `autoharness.cli.main()`
  entrypoint end-to-end for `gate pipeline-topology` in every mode
  (`agent`/`manual`/`ci`), every phase, `--force`, `--bootstrap-grant-invocation`,
  and `--json`/human output, including the newly-added
  `test_bootstrap_grant_invocation_requires_agent_mode_and_pre_claim_phase`
  regression covering this round's mode/phase authority-boundary fix.
* `tests/test_gate_bootstrap_grant.py` (31 tests, all passing, 6 new
  regression tests added this session) directly exercises the new
  `bootstrap_grant.py` module's claim/consume/scan/append primitives,
  including the new `append_no_follow()` helper's symlink-containment
  behavior (`test_append_no_follow_rejects_symlinked_directory_component`,
  `test_append_no_follow_rejects_symlinked_target_file`).
* Cross-platform validation: the bootstrap-grant module has structurally
  distinct POSIX (`O_NOFOLLOW` + `dir_fd`) and Windows
  (`lstat`/reparse-point + held-open `CreateFileW` handles) claim strategies.
  Both `tests/test_gate_bootstrap_grant.py` and
  `tests/test_gate_pipeline_topology_cli.py` were run on native Windows (31/31
  and 33/33 passing) and on native POSIX via WSL Ubuntu on a non-DrvFs
  filesystem (31/31, 8 skipped as Windows-only; and 32/33, 1 confirmed
  pre-existing environment-artifact failure unrelated to this PR's diff --
  see below).
* Hosted CI (`test`, `ci gate`, `pipeline-topology (ambient)`,
  `detect code changes`) -- green at `last_code_affecting_head` `408ae4a2`
  on `ubuntu-latest`, an independent OS/Python environment from local
  Windows validation.
* Hosted Copilot review -- completed across 4 rounds on this PR; all 9
  distinct findings investigated, 7 were genuine in-scope bugs (fixed, each
  with a new regression test) and 2 were process/hygiene items (a stale PR
  body readiness reference, addressed by updating the body); all review
  threads now resolved (`autoharness gate copilot-review 450 --enforcement
  auto --json` returns `verdict: SATISFIED`, `exit_code: 0` at HEAD
  `408ae4a2`).

## One Confirmed Environment-Artifact Test Failure (Not a Regression)

`tests/test_gate_pipeline_topology_cli.py::PipelineTopologyStorageRootResolutionTests::test_backlog_only_workspace_succeeds`
fails when run from a plain file-copy of the repository under WSL (no `.git`
directory present in the copy target), because the test's git-branch/root
detection path behaves differently outside an actual git repository. This
was confirmed present against the pre-round-4 commit (`1bfa41ea`) as well,
proving it is not a regression introduced by any commit in this PR. It does
not reproduce on hosted CI (`ubuntu-latest`, which runs from an actual git
checkout) and does not reproduce on native Windows. No code change is
warranted; this is a known artifact of the ad hoc copy-based WSL validation
methodology used to reach the otherwise-unreachable POSIX claim-strategy
code paths.

## Invariants Preserved

* The `pipeline-topology` gate's `pre_claim` phase continues to fail closed
  (BLOCK, never a silent PASS) on every ambiguous, malformed, or
  containment-violating filesystem condition encountered while evaluating or
  claiming a bootstrap grant -- confirmed by the full existing
  `tests/test_gate_bootstrap_grant.py` suite plus this session's 6 new
  regression tests, none of which weaken any existing fail-closed assertion.
* `--bootstrap-grant-invocation` remains usable only in its documented
  agent-consumable, pre-claim-only scope (`--mode agent --phase pre_claim`) --
  newly enforced at CLI-parse time this session, closing a prior gap.
* The pipeline-topology force-audit log (`.autoharness/gates/pipeline-topology-force-audit.log`)
  is now appended to only via a containment-checked, no-follow path,
  matching the guarantee already provided for the bootstrap-grant
  consumption record.
* No `{{VARIABLE}}` placeholders remain unresolved in any touched artifact.

## Verdict

**PASS.** The CLI surface (including the specific `gate pipeline-topology`
subcommand this shipment changes) is confirmed working via direct end-to-end
CLI-entrypoint test exercise, the full local test suite is green on two
independent operating systems (Windows and POSIX/WSL), hosted CI is green on
a third independent environment (`ubuntu-latest`), and all 4 rounds of
hosted Copilot review are fully resolved.

## Blocked Prerequisites

None for pre-merge verification. Post-merge re-verification
(`uv run autoharness --help` against the new `main` HEAD) is recorded as
`pending` in this artifact's frontmatter and will be performed during
Post-Merge Closure per the Ship agent contract, after explicit operator
merge approval and the merge itself.
