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
`tests/test_scope_containment_*` modules are ABSENT FROM THE RUN (an OBSERVED
result - re-derive it with the positive dotted-name enumeration in Task 1
step 2, since the canonical runner has no deselect flag).

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
2. Confirm the "exclusion" result. `python -m unittest` has NO deselect /
   `--ignore` facility, so this step MUST be run as a POSITIVE dotted-name
   enumeration of the COMPLEMENT SET (amendment A5), produced by a
   deterministic generator rather than hand-listed:

   ```powershell
   $env:PYTHONPATH = 'src'
   $mods = Get-ChildItem tests -Filter 'test_*.py' -Name |
       Where-Object { $_ -notlike 'test_scope_containment_*' } |
       ForEach-Object { 'tests.' + $_.Substring(0, $_.Length - 3) } |
       Sort-Object
   python -m unittest $mods
   ```

   At plan time this selects 82 of the 85 `tests/test_*.py` modules; the three
   `test_scope_containment_*` modules are exactly the complement. `Sort-Object`
   makes the ordering deterministic across rounds. Record the generated count
   and the exact module list alongside the result. Expect green.
   **If NOT green, the entry premise is falsified - STOP and return to Stage.**
3. Binary-search the polluting set. Each round runs only
   {candidate subset} + {the five victims}. Halve by module, then by TestCase
   class, then by test method. Bound: <= 8 rounds.
4. Record the minimal reproducing pair (polluter test ID -> victim test ID) and
   the observed mechanism, quoting the captured git stderr verbatim.
5. **TIME-BOX EXHAUSTION (amendment A2R).** If the minimal pair is not isolated
   within the time box, STOP the search, record the NARROWED CANDIDATE SET and the
   rounds performed, and record `VERDICT: INCONCLUSIVE`. The task then closes
   `done`; it is NEVER returned blocked. Do NOT proceed to a speculative fix -
   there is no remediation work in this shipment to slip into, because remediation
   is a separate successor shipment (151-S). No fourth attempt.

**Terminal outcome contract (amendment A2R).** This task has exactly TWO terminal
outcomes and BOTH of them close it `done`: `VERDICT: PAIR-ISOLATED` or
`VERDICT: INCONCLUSIVE`. It is never returned blocked and never left in any other
status.

**Acceptance criteria.**
* AC1. (PAIR-ISOLATED only) A minimal reproducing pair is recorded as an exact,
  re-runnable command that fails, plus the same command minus the polluter that
  passes.
* AC2. The `git init` exit-128 stderr text is recorded verbatim. Binding in BOTH
  verdicts - it is captured in step 1, before any bisection begins.
* AC3. (PAIR-ISOLATED only) The mechanism is stated as a causal claim with
  evidence, not a guess.
* AC4. (INCONCLUSIVE only) The narrowed candidate set, the rounds performed and
  the subsets enumerated are recorded in a form Task 3b can consume, and the task
  is closed `done` - NOT returned blocked.
* AC5. Exactly one `VERDICT:` token is recorded on the task record. Task 3b's
  Step 0 precondition gate reads this token and cannot proceed without it.

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

## Shipment boundary (amendment A2R - operative)

Tasks 1 and 2 are UNCONDITIONALLY executable and ship together as **149-S**
(covering feature 141-F). Tasks 3a and 3b depend on Task 1's *result* and
therefore ship SEPARATELY as the successor shipment **151-S** (covering feature
143-F). This boundary is the mechanism that replaces the original "return Task 3
blocked and close the feature partially" resolution, which was un-executable; see
amendment A2R.

### Task 3a - Make the two git subprocess sites self-diagnosing (UNCONDITIONAL)

**Shipment.** 151-S. **Dependency.** None on Task 1's result. This work is correct
whatever the bisect concluded and must not be trapped behind a conditional gate.

**Steps.** Capture stdout/stderr at both `check=True` git subprocess sites and
include the captured stderr in the failure message, so the next exit-128 names its
own cause instead of surfacing as a bare `CalledProcessError`. Sites:
`tests/test_gate_pipeline_topology_cli.py` (the `git init` path in
`test_backlog_only_workspace_succeeds`) and
`tests/test_telemetry_gitignore_template.py` (`MetricsEmissionHardGateTests._git`).

**Acceptance criteria.**
* AC11. Both `check=True` git sites surface captured stderr on failure.
* AC11b. `git diff` shows ZERO assertion-line edits in either module; victims #1
  and #5 live in these files and their assertions must be unchanged.
* AC11c. Both modules pass in isolation before and after with identical pass counts.

### Task 3b - Remediate the confirmed polluter, or record an evidenced no-remediation disposition

**Shipment.** 151-S. **Dependency.** Task 3a, plus Task 1's recorded `VERDICT`
token (consumed by the Step 0 gate below, not by a task-status edge).

**Step 0 - precondition gate (read-only, run first, record the result).** Read
Task 1's `VERDICT`. If `PAIR-ISOLATED`, re-run the recorded minimal reproducing
command at THIS shipment's head. Select the disposition from the observed result,
never from prose:

* **R1** - verdict `PAIR-ISOLATED` and the reproducer still FAILS -> remediate the
  polluter at its own source (fixture/teardown scoping in the POLLUTING test),
  citing Task 1's minimal pair. Do not modify any victim's assertions.
* **R2** - verdict `PAIR-ISOLATED` but the reproducer now PASSES (Task 2's anchor
  work, or the variable-derivation shipment, already removed it) -> make NO source
  edit; record the now-passing output and the likely intervening cause.
* **R3** - verdict `INCONCLUSIVE` -> make NO source edit. There is no
  speculative-fix path. Re-measure the canonical gate. If green, record it. If
  still red, record the residual failure set plus Task 1's narrowed candidate set
  and capture a NEW deferred stash entry under P-021 C2.

**All three dispositions terminate in `done` with recorded evidence.** This task is
never returned blocked, and 151-S is never abandoned.

**Acceptance criteria.**
* AC7a. The selected disposition (R1/R2/R3) is recorded with the verbatim Step 0
  command output. An unrecorded disposition is not acceptable, including a null
  result.
* AC8. (R1 only) The canonical full-suite gate is GREEN on Windows: zero failures,
  zero errors (skips unchanged).
* AC9. (R1 only) The minimal reproducing command from AC1 now passes.
* AC10. All five victim tests retain their original assertions verbatim -
  demonstrated by diff (no victim assertion line changed). Binding in EVERY
  disposition.
* AC12. Hosted CI remains green (no Linux regression from the anchor changes).
* AC13. No source edit under `tests/` is made in any disposition without citing
  Task 1's recorded minimal reproducing pair. This is the structural replacement
  for the former hard-stop-and-block rule: a speculative fix cannot produce the
  citation.
* AC14. (R3-still-red only) A new deferred stash entry exists carrying the
  residual failure set and the narrowed candidate set.

## Width isolation (P-003)

Tasks 1, 2, 3a and 3b are all `tests/`-surface work. No production code, no
templates, no schemas, no CLI. If Task 1 implicates production code, STOP
(024-DL R5).

## Harvest note

Task 2's 58 sites are split per module so each unit stays inside the 2-hour rule.
The structural guard lands with the FIRST subtask carrying an EXPLICIT SHRINKING
ALLOWLIST seeded with the four known offending modules, and each subtask removes
its own module from that allowlist in the SAME change that fixes that module's
call sites. The guard is therefore GREEN after every subtask and NO intermediate
commit carries a deliberately-red test (amendment A4). The final subtask empties
the allowlist and asserts it is empty. (Rewritten in review-fix cycle 2: this note
previously said the guard "is expected to stay RED until the last subtask
completes", which directly contradicted A4 and would have forced a P-018 gate
bypass on every intermediate subtask.)

**Harvest mapping.** Tasks 1-2 -> shipment 149-S / feature 141-F as 141.001-T,
141.002-T, 141.003-T, 141.004-T. Tasks 3a-3b -> successor shipment 151-S /
feature 143-F as 143.001-T, 143.002-T. The original combined 141.005-T is archived
as SUPERSEDED and remains a pre-archived member of the 149-S manifest, which
`.github/agents/_ship.agent.md:325-340` defines as expected and tolerated
(`pre_archived_skipped`).

## Amendments applied from hardening (P-006)

Source: `docs/plans/2026-08-21-full-suite-test-isolation-hardening.md` (HARDENED).

* **A1 (H1)** - Task 3 AC10 is extended: the five victim tests must additionally
  be re-run IN ISOLATION with identical pass/fail semantics, and the task record
  must carry the verbatim `git diff` of the five victim files showing either no
  change, or changes confined to `setUp`/`tearDown`/imports with **zero
  assertion-line edits**.
* **A2R (H2R; A2 SUPERSEDED in review-fix cycle 2)** - Conditional remediation is
  separated from unconditional work by a SHIPMENT BOUNDARY, not by a task status.
  Tasks 1-2 ship as 149-S; Tasks 3a-3b ship as the successor 151-S. Task 1 has two
  terminal outcomes and both close it `done` (`VERDICT: PAIR-ISOLATED` /
  `VERDICT: INCONCLUSIVE`); Task 3b has three dispositions and all three close it
  `done`. No task in either shipment can end `blocked`, so neither shipment can
  deadlock and neither needs abandonment.
  **Why A2 was withdrawn:** A2 required Task 3 to be "returned blocked via the
  official return-blocked operation" while "the shipment closes with Tasks 1-2
  only". Per `.github/agents/_ship.agent.md:325-340`, the shipment manifest is the
  closure membership record, is "never mutated to make execution proceed", and any
  member status outside `queued`/`active`/`done`/pre-archived is a FAIL-CLOSED
  HALT, never a skip. A blocked member therefore deadlocks the entire shipment
  instead of permitting a partial close; backlogit 1.8.0 has no shipment `blocked`
  status to fall back on (`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`);
  and the installed Ship contract never instructs Ship to use
  `backlogit_return_blocked` at all - `.github/agents/_ship.agent.md` contains ZERO
  prose references to it (verified across all `return_blocked` / `return-blocked` /
  `return blocked` variants). Ship does hold tool ACCESS via the `'backlogit/*'`
  wildcard in its frontmatter, but access is not instruction: no step, gate, or
  failure path in the contract gives the operation any semantics, and the Step 2
  derivation makes a `blocked` member a fail-closed halt regardless of who set it.
  A2 therefore depended on Ship behaviour that its contract does not define.
  **H2's intent is preserved structurally:** there is no remediation work inside
  149-S to slip into under time pressure, and Task 3b AC13 forbids any source edit
  that does not cite Task 1's recorded minimal reproducing pair - a citation a
  speculative fix cannot produce.
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
  as an escape hatch. The Harvest note's contradictory "expected to stay RED"
  wording was REWRITTEN (not merely superseded) in review-fix cycle 2, so the plan
  no longer carries two conflicting operative instructions.
* **A5 (P1-2; made EXECUTABLE in review-fix cycle 1)** - The bisect protocol runs
  on the canonical runner using EXPLICIT DOTTED-NAME ENUMERATION, never
  exclusion: `$env:PYTHONPATH='src'; python -m unittest <module-or-test-ids...>`.
  `unittest discover` has no deselect facility, so every round names its subset
  positively. Where a round needs a COMPLEMENT of some excluded set, it MUST be
  produced by the deterministic generator shown in Task 1 step 2 (filter the
  `tests/test_*.py` listing, map to `tests.<module>` dotted names, `Sort-Object`)
  and the generated list recorded with the result. No step in this plan may be
  phrased as "excluded"/"without" without an accompanying runnable positive
  enumeration. pytest may be used as a cross-reference only and never as the
  measurement gate (`docs/compound/097-S-canonical-unittest-gate.md`).

## Amendments applied in review-fix cycle 2 (PR #386)

Threads: `PRRT_kwDORzpWpM6bSzLz`, `PRRT_kwDORzpWpM6bSzMM`, `PRRT_kwDORzpWpM6bSzMz`,
`PRRT_kwDORzpWpM6bSzNF`, `PRRT_kwDORzpWpM6bSzOQ`.

* **A2R** - replaces A2. Conditional remediation moves to successor shipment
  151-S / feature 143-F; every task in both shipments has only terminal outcomes
  that close `done`. Recorded in full above.
* **A6** - Task 1's hard stop is now a TIME-BOX EXHAUSTION rule producing
  `VERDICT: INCONCLUSIVE` and a `done` close, with the narrowed candidate set as
  the deliverable. AC4 rewritten; AC5 added (exactly one `VERDICT:` token).
* **A7** - Task 3 is split into Task 3a (unconditional git-subprocess
  self-diagnosis) and Task 3b (three always-terminating dispositions R1/R2/R3),
  with AC13 (no uncited source edit) as the structural anti-speculation guard.
* **A8** - the Harvest note is REWRITTEN to match A4 (guard green after every
  subtask) and now carries the explicit harvest mapping to 149-S and 151-S.

All five threads are corrections to staging artifacts only - `.backlogit/` and
`docs/{plans,reviews,memory}`. No `src/`, `templates/`, `tests/`, `schemas/` or
`.github/` path is touched, so this cycle is SAME-CONTRACT-SURFACE under P-021 C1
and requires no new deferred capture.
