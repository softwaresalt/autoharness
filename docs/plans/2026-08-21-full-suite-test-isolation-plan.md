---
title: "Full-suite test-order/global-state pollution - bisect to a minimal reproducing pair, then fix at source"
date: 2026-08-21
stash_id: E8158860
deliberation: ".backlogit/queue/024-DL.md"
hardening: docs/plans/2026-08-21-full-suite-test-isolation-hardening.md
requires_plan_hardening: yes
hardening_present: yes
blast_radius: "elevated (root cause unknown at plan time; 58 mechanical call-site edits across four test modules; genuine masking hazard on five existing regression guards)"
---

# Implementation Plan - full-suite test-isolation repair

Date: 2026-08-21
Agent: Stage (planning only - Ship executes)
Stash source: `E8158860`
Deliberation: `024-DL`
Classification: **bug / test-suite global-state pollution (Windows-local, canonical-gate-visible)**
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Goal

Make the canonical local test gate GREEN by removing the cross-test state
pollution that fails five tests only in a full-suite run - fixing the POLLUTER,
not the victims, and leaving all five victim assertions intact.

## Non-goals

* No relaxation, skip, xfail, or platform-gating of any of the five victim tests.
* No pinning or forcing of test execution order.
* No change to production code under `src/autoharness/`. If the bisect shows the
  pollution originates there, that is a different contract surface and re-enters
  P-021 capture (024-DL R5).
* No new test dependency (no `pytest-randomly`, no plugin additions).

## Baseline

Victims (3 failures + 2 errors; the 2 errors are the two `check=True` git
subprocess paths):

1. `tests/test_gate_pipeline_topology_cli.py::PipelineTopologyStorageRootResolutionTests::test_backlog_only_workspace_succeeds` (`git init` exit 128)
2. `tests/test_gates_topology.py::FilesystemTopologyReadersTests::test_empty_queue_and_archive_dirs_pass_as_zero_shipments`
3. `tests/test_repo_root_artifacts.py::RepoRootTrackedJsonAllowlistTest::test_root_tracked_json_matches_allowlist`
4. `tests/test_telemetry_gitignore_template.py::MetricsGitignoreTests::test_git_check_ignore_matches_metrics_artifacts`
5. `tests/test_telemetry_gitignore_template.py::MetricsEmissionHardGateTests::test_emitted_metrics_artifacts_are_never_tracked`

Established facts (024-DL): reproduces on the CANONICAL gate and on pytest;
does NOT reproduce on hosted Linux CI (146-S and 147-S closure records);
pre-existing on merge-base `b9d91b18`; all five pass when the three
`tests/test_scope_containment_*` modules are excluded.

Stage static findings that REFUTE the entry's own hypotheses: there is no
`os.chdir` anywhere in `tests/`; there is no bare `os.environ[...]` assignment
anywhere in `tests/`; every `patch.dict(os.environ, ...)` is context-managed and
no `mock.patch(...).start()` is left unstopped; the three suspected polluter
modules write nothing into the live working tree.

Leading structural suspect: **58** `tempfile.TemporaryDirectory(dir=Path.cwd())`
sites creating temp trees INSIDE the live working tree -
`test_gates_topology.py` (34), `test_backlog_root.py` (16),
`test_gate_pipeline_topology_cli.py` (5), `test_gate_dag_readiness_cli.py` (3).

## Task breakdown

### Task 1 - Bounded empirical bisection to a minimal reproducing pair

This task produces EVIDENCE, not a fix. It is deliberately first because the
causal predecessor is not determinable within Stage's role boundary.

**Protocol (fixed, do not improvise).**
1. Baseline on the canonical gate (`$env:PYTHONPATH='src'; python -m unittest
   discover -s tests`, per `docs/compound/097-S-canonical-unittest-gate.md`).
   Capture the five IDs AND the full verbatim stderr for each - especially the
   `git init` exit-128 message text, which has never been recorded.
2. Confirm the exclusion result: rerun with the three
   `tests/test_scope_containment_*` modules excluded. Expect green.
   **If NOT green, the entry premise is falsified - STOP and return to Stage.**
3. Binary-search the polluting set. Each round runs only
   {candidate subset} + {the five victims}. Halve by module, then by TestCase
   class, then by test method. Bound: <= 8 rounds.
4. Record the minimal reproducing pair (polluter test ID -> victim test ID) and
   the observed mechanism, quoting the captured git stderr verbatim.
5. **HARD STOP.** If the minimal pair is not isolated within the time box, STOP
   and hand back to Stage with the narrowed candidate set. Do NOT proceed to a
   speculative fix. No fourth attempt.

**Acceptance criteria.**
* AC1. A minimal reproducing pair is recorded as an exact, re-runnable command
  that fails, plus the same command minus the polluter that passes.
* AC2. The `git init` exit-128 stderr text is recorded verbatim.
* AC3. The mechanism is stated as a causal claim with evidence, not a guess.
* AC4. On hard stop, the narrowed candidate set is recorded and the task is
  returned blocked rather than closed.

**Constraint.** This task changes NO source or test file. It is diagnosis only.

### Task 2 - Remove ambient-cwd coupling from temp-directory creation

Correct regardless of Task 1's finding.

**Test-first requirement.** Add an AST-based structural guard
`tests/test_test_suite_isolation_contract.py` asserting that no module under
`tests/` calls `tempfile.TemporaryDirectory` with a `dir=` keyword whose value
is a `Path.cwd()` call. RED before (58 hits), GREEN after. Use an AST visitor,
not a line regex, per
`docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md`.

**Steps.** Replace each `dir=Path.cwd()` with a deterministic anchor.
**Per-file containment review is mandatory before editing**: several of these
tests exercise workspace-containment logic where "inside the repository" is
semantically required. Where containment is required, anchor to
`Path(__file__).resolve().parents[1]` (deterministic repo root). Where it is
not, use plain `tempfile.TemporaryDirectory()` (system temp). Never relocate a
containment test to system temp.

**Acceptance criteria.**
* AC5. Zero `dir=Path.cwd()` sites remain under `tests/`; the structural guard
  passes.
* AC6. Each of the four affected modules has a recorded containment
  determination (required / not required) with a one-line justification.
* AC7. Every test in the four modules passes IN ISOLATION before and after,
  with identical pass counts. No assertion is weakened.

**Size note.** 58 sites across 4 modules exceeds one 2-hour unit; this task is
decomposed into per-module subtasks at harvest (see Harvest note below).

### Task 3 - Fix the confirmed polluter and make the git subprocess sites self-diagnosing

**Dependency.** Depends on Task 1 (needs the minimal pair) and Task 2.

**Steps.**
1. Remediate the confirmed polluter at its own source - fixture/teardown scoping
   in the POLLUTING test. Do not modify any victim's assertions.
2. Make the two `check=True` git subprocess sites self-diagnosing: capture
   stdout/stderr and include the captured stderr in the failure message, so the
   next exit-128 names its own cause instead of surfacing as a bare
   `CalledProcessError`.

**Acceptance criteria.**
* AC8. The canonical full-suite gate is GREEN on Windows: zero failures, zero
  errors (skips unchanged).
* AC9. The minimal reproducing command from AC1 now passes.
* AC10. All five victim tests retain their original assertions verbatim -
  demonstrated by diff (no victim assertion line changed).
* AC11. Both `check=True` git sites now surface captured stderr on failure.
* AC12. Hosted CI remains green (no Linux regression from the anchor changes).

## Width isolation (P-003)

Tasks 1-3 are all `tests/`-surface work. No production code, no templates, no
schemas, no CLI. If Task 1 implicates production code, STOP (024-DL R5).

## Harvest note

Task 2's 58 sites are split per module so each unit stays inside the 2-hour
rule; the structural guard lands with the first subtask and is expected to stay
RED until the last subtask completes.

## Amendments applied from hardening (P-006)

Source: `docs/plans/2026-08-21-full-suite-test-isolation-hardening.md` (HARDENED).

* **A1 (H1)** - Task 3 AC10 is extended: the five victim tests must additionally
  be re-run IN ISOLATION with identical pass/fail semantics, and the task record
  must carry the verbatim `git diff` of the five victim files showing either no
  change, or changes confined to `setUp`/`tearDown`/imports with **zero
  assertion-line edits**.
* **A2 (H2)** - Task 3 is BLOCKED on Task 1 producing AC1. If Task 1 hard-stops,
  Task 3 is returned blocked via the official return-blocked operation with the
  narrowed candidate set, and the shipment closes with Tasks 1-2 only. Tasks 1
  and 2 are independently valuable and independently mergeable; Task 3 is not.
  This is encoded as a real dependency edge at harvest, not as prose.
* **A3 (H4)** - The AST structural guard must assert the ABSENCE of the
  anti-pattern (not the presence of a fix) and must name every offending file
  and line in its failure message.
* **H3 refinement** - the containment determination required by AC6 is
  per-CALL-SITE (not per-module) for `test_gates_topology.py` and
  `test_gate_pipeline_topology_cli.py`. Default when uncertain: anchor to
  `Path(__file__).resolve().parents[1]`; never relocate a containment test to
  system temp.

## Amendments applied from plan review

Source: `docs/reviews/2026-08-21-full-suite-test-isolation-review.md` (PASS).

* **A4 (P1-1)** - The AST structural guard in Task 2 is written with an EXPLICIT,
  SHRINKING ALLOWLIST of the known offending modules
  (`test_gates_topology.py`, `test_backlog_root.py`,
  `test_gate_pipeline_topology_cli.py`, `test_gate_dag_readiness_cli.py`). Each
  per-module subtask removes its own module from the allowlist in the SAME change
  that fixes that module's call sites, so the guard is GREEN after every subtask
  and no intermediate commit carries a deliberately-red test. The final subtask
  empties the allowlist and asserts it is empty, so the allowlist cannot persist
  as an escape hatch. This supersedes the Harvest note's "expected to stay RED"
  wording.
* **A5 (P1-2)** - The bisect protocol runs on the canonical runner using EXPLICIT
  DOTTED-NAME ENUMERATION, never exclusion:
  `$env:PYTHONPATH='src'; python -m unittest <module-or-test-ids...>`.
  `unittest discover` has no deselect facility, so every round names its subset
  positively. pytest may be used as a cross-reference only and never as the
  measurement gate (`docs/compound/097-S-canonical-unittest-gate.md`).
