---
title: 088-F review-followup hardening — resolver fail-safe + benchmark honesty
date: 2026-07-26
source_stash: A351DB70, C2F7BB15
origin_feature: 088-F (copilot-cli-output-compression-experiment, archived)
---

# 088-F Review-Followup Hardening Plan

## Problem Frame

PR #229 (088-F compression experiment) Copilot review surfaced two follow-up
findings against the throwaway, disabled-by-default `experiments/088-compression-experiment/`
module. Both are isolated to that experiment; nothing in `src/autoharness`
imports it, so blast radius is low.

1. **A351DB70 (bug, medium)** — `brainspace/workspace.py::resolve_workspace_root`
   (~L151-167). When a hook payload is a dict whose `cwd` value is a truthy
   non-string (e.g. `{"cwd": [...]}`), the code passes the
   `isinstance(payload, dict)` guard and the `payload.get("cwd")` truthiness
   guard, then calls `_validate_related_to_process_cwd(payload_cwd, ...)`,
   which calls `os.path.realpath(candidate)` on the non-string value. This
   raises an uncaught `TypeError` (not `WorkspaceContainmentError`).
   `hook_cli.py::main` (L47-55) only catches `WorkspaceContainmentError`
   around the `resolve_workspace_root` call, so the `TypeError` propagates
   unhandled and crashes the hook subprocess instead of emitting the
   required fail-safe `{}` passthrough (the same invariant already proven
   for JSON-decode errors at L40-45 and for non-dict payloads in
   `test_non_dict_payload_falls_back_to_process_cwd_instead_of_crashing`).
   Existing test coverage (`test_workspace_resolution.py`,
   `test_hook_cli_entrypoint.py`) proves the non-dict-payload and
   unrelated-string-cwd cases but has no case for a dict payload carrying a
   non-string `cwd` — this is the coverage gap the finding identifies.

2. **C2F7BB15 (chore, medium)** — `brainspace/benchmark.py::_run_compression_case`
   (L203-215). The early-decline branch (`"modifiedResult" not in result`)
   returns a `CaseResult` with only `criteria={"compressed_at_all": False}`
   and a fixed `notes` string. It drops `case.capture_failed` and
   `case.provenance`, both of which the full (non-declined) path at
   L266/289-296 always carries into `criteria`/`notes`. A case built with
   `capture_failed=True` or a non-`"live"` `provenance` that also happens to
   decline (no `modifiedResult`) therefore reports a `CaseResult` that hides
   why/how that input was captured — an evidence-report honesty gap for the
   benchmark's declared invariant (`benchmark.py` L49-56 docstring: provenance
   and capture-failure status must always be documented).

## Requirements Trace

| Requirement | Implementation action |
|---|---|
| A351DB70: non-string `cwd` must never crash the hook; must fail-safe to `{}` passthrough | Task 1: type-guard `payload_cwd` in `resolve_workspace_root` before validation/realpath |
| C2F7BB15: early-decline `CaseResult` must carry `capture_failed`/`provenance` | Task 2: extend the early-decline return in `_run_compression_case` |
| Both: TDD red-then-green, tests co-located with existing suite | Task 1 and Task 2 each specify failing tests first |
| Both: no weakening of decide-then-stash / byte-equivalent retrieval / secret-screen-before-store invariants | Confirmed in Risks — neither fix touches those code paths |

## Implementation Units

### Task 1 — `resolve_workspace_root` non-string `cwd` fail-safe (A351DB70)

* **Files** (1): `experiments/088-compression-experiment/brainspace/workspace.py`
  (plus its test file — 2 files total, within the 2-Hour Rule's <3-file bound)
* **Test file**: `experiments/088-compression-experiment/tests/test_workspace_resolution.py`
  (co-located with the existing `resolve_workspace_root` suite)
* **Execution posture**: test-first (red → green)
* **Tests to add first (must fail before the fix)**:
  1. `test_dict_payload_with_non_string_cwd_raises_containment_error` — a
     dict payload whose `cwd` is a non-string truthy value (e.g. `["a", "b"]`)
     must raise `WorkspaceContainmentError` (fail-safe, catchable by
     `hook_cli.py`'s existing except clause), NOT an uncaught `TypeError`.
     Assert via `pytest.raises(WorkspaceContainmentError)`, and assert (using
     `pytest.raises` context or a direct call wrapped in `try/except
     TypeError: pytest.fail(...)`) that a bare `TypeError` is never raised.
  2. **Negative control**: `test_dict_payload_with_valid_string_cwd_still_resolves`
     — a dict payload with an ordinary valid string `cwd` (matching the
     existing `test_payload_cwd_used_when_no_env_pin` pattern) still resolves
     normally, proving the fix doesn't regress the valid-string path.

  A third, end-to-end `hook_cli.py` subprocess scenario (mirroring
  `test_unrelated_payload_cwd_is_safe_noop_not_a_crash` in
  `test_hook_cli_entrypoint.py`) was considered but is deliberately **out of
  scope for this task** — adding it would touch a 3rd file, exceeding the
  2-Hour Rule's `<3 files` bound (see Plan Review). The unit test pair above
  already proves the fail-safe exception is raised instead of a bare
  `TypeError`, and `hook_cli.py`'s existing `except WorkspaceContainmentError`
  clause (unchanged by this fix) already has direct test coverage via
  `test_unrelated_payload_cwd_is_safe_noop_not_a_crash` for the same catch
  path with a different trigger. Recorded as an optional P3 follow-up, not
  required for this fix's correctness.
* **Fix**: in `resolve_workspace_root`, before calling
  `_validate_related_to_process_cwd(payload_cwd, source="payload cwd")`,
  add `isinstance(payload_cwd, str)` check. If not a `str`, raise
  `WorkspaceContainmentError` (the module's existing fail-safe exception
  type, already caught by `hook_cli.py`) with a message identifying the
  non-string payload cwd, rather than falling through to
  `os.path.realpath()`. This keeps the fail-safe surface consistent with
  the module's established pattern (round-3/round-7/final-convergence
  findings already documented in the module's own docstrings): reject with
  the module's containment exception, never let a raw Python `TypeError`
  escape past `hook_cli.py`'s catch clause.
* **Verification**: `pytest experiments/088-compression-experiment/tests/test_workspace_resolution.py -v`

### Task 2 — `_run_compression_case` early-decline provenance carry-through (C2F7BB15)

* **Files** (1): `experiments/088-compression-experiment/brainspace/benchmark.py`
  (plus its test file — 2 files total)
* **Test file**: `experiments/088-compression-experiment/tests/test_benchmark_runner.py`
  (co-located with the existing `_run_compression_case` suite)
* **Execution posture**: test-first (red → green)
* **Tests to add first (must fail before the fix)**:
  1. `test_early_decline_case_carries_capture_failed_into_result` — build a
     `BenchmarkCase` with `capture_failed=True` and text/tool_name that the
     hook declines (no `modifiedResult`, e.g. a tiny/policy-declined input
     using the same fixture pattern as
     `test_capture_failed_case_is_never_a_safe_win_even_if_all_else_passes`
     but steered to the early-decline branch). Assert the returned
     `CaseResult.criteria` (or an equivalent explicit field) reflects
     `capture_failed=True` and that `safe_win` is `False`.
  2. `test_early_decline_case_carries_non_live_provenance_into_result` — same
     shape, with `provenance="replayed"` (or another non-`"live"` value) and
     no `capture_failed`. Assert the returned result's `criteria`/`notes`
     documents the non-live provenance the same way the full path's
     `notes = f"{notes} [{case.provenance}]"` does (L295-296), instead of
     silently reporting the decline as if it were unconditionally live.
* **Fix**: extend the early-decline `CaseResult` construction (L209-215) to
  include `capture_failed`/`provenance` evidence, matching the same
  reporting shape the full path already uses: add
  `"capture_succeeded": not case.capture_failed` to the `criteria` dict, and
  append the provenance/capture-failed annotations to `notes` using the same
  logic already present at L288-296 (extract that logic into a small shared
  helper, or duplicate the two `if` blocks, whichever keeps the diff
  smallest — reviewer's call at harvest/build time, not prescribed here).
* **Verification**: `pytest experiments/088-compression-experiment/tests/test_benchmark_runner.py -v`

## Dependency Graph

Task 1 and Task 2 touch disjoint files (`workspace.py`+its tests vs.
`benchmark.py`+its tests) and have no shared state or ordering requirement.
They may be implemented in either order or in parallel within the same build
session. No cycles.

## Decisions and Rationale

* **Raise `WorkspaceContainmentError` rather than returning a sentinel for
  non-string `cwd`** — the module already funnels every other rejected
  candidate (unrelated path, empty explicit root, unbounded ancestor)
  through this single exception type, and `hook_cli.py` already has a
  fail-safe catch for exactly this type. Reusing it keeps the fail-safe
  contract centralized in one place (the module) instead of adding a second
  ad hoc guard in `hook_cli.py`. This directly satisfies the stash's "and/or
  wrap in hook_cli try/except" alternative by making the existing
  `hook_cli.py` except clause sufficient without modifying `hook_cli.py`.
* **Extend the existing `criteria`/`notes` shape rather than adding new
  `CaseResult` fields** — `CaseResult` is a plain dataclass with a fixed
  shape (`name, category, safe_win, criteria, notes, decline_correct`)
  already used across ~10 test files and the markdown/JSON report renderers.
  Adding `capture_failed`/`provenance` as first-class dataclass fields would
  widen the change surface (report renderers, JSON schema of the report)
  beyond a 2-file/1-function fix. Carrying them through the existing
  `criteria` dict and `notes` string (the same containers the full path
  already uses) keeps the fix minimal and consistent with existing report
  consumers.

## Risks and Caveats

* **Risk**: broadening the `WorkspaceContainmentError` raise path could, in
  theory, change hook behavior for some currently-untested edge case.
  **Mitigation**: the new check only fires when `payload_cwd` is
  simultaneously truthy AND not a `str` — a state no existing passing test
  exercises (confirmed: `test_non_dict_payload_falls_back_to_process_cwd_instead_of_crashing`
  covers non-dict *payload*, not non-string *payload["cwd"]* on an
  otherwise-valid dict payload). No existing green test can regress.
* **Risk**: duplicating the notes-building logic between the early-decline
  and full paths in `benchmark.py` could drift out of sync later.
  **Mitigation**: flag this as a P2 "extract shared helper" follow-up if
  plan-review raises it; not required for correctness of the fix itself.
* **Invariant preservation**: neither fix touches decide-then-stash ordering,
  byte-equivalent retrieval, or secret-screen-before-store logic (those live
  in `hook.py`/`store.py`/`secret_screen.py`, untouched by this plan). Both
  fixes are purely defensive/reporting additions.

## Plan Hardening Signals (REQUIRED)

* Public API, schema, or contract change: **absent** — no `.mcp.json`/CLI
  surface change; `CaseResult`'s existing dataclass shape is unchanged (only
  dict/string contents populated more completely).
* Security, auth, permission, or compliance-sensitive behavior: **present
  (narrow)** — `resolve_workspace_root` is a containment-security function
  (Constitution IV), but this fix *tightens* an existing fail-safe rather
  than introducing new privileged behavior; no new attack surface is added,
  an existing gap (uncaught crash) is closed.
* Migration, backfill, destructive data/config action, or irreversible step:
  **absent**.
* External integration, operator checkpoint, or external dependency:
  **absent** — the disabled-by-default hook has no live external caller in
  this scope.
* High runtime, rollout, or rollback risk: **absent** — throwaway,
  flag-gated, isolated experiment; no default install; prior compound
  learning (`docs/compound/093-S-review-loop-convergence.md`) already
  established this experiment as low-blast-radius with no base-harness
  dependency.

**Requires plan hardening: no.** The one "present" signal (containment-security
touch) is narrow, additive-only (tightens an existing fail-safe path, adds no
new capability), fully covered by test-first red/green verification, and
scoped to a throwaway disabled-by-default experiment with no downstream
dependents. Plan-review should still confirm this conclusion; escalate to
`plan-harden` only if review disagrees.

## Runtime Verification and Closure

* Neither task changes a runtime surface exposed to operators or other
  harness components (no CLI, API, browser UI, or background job changes;
  the experiment's hook/benchmark CLIs are unchanged in interface).
* **Runtime verification**: `pytest` green for both modified test files is
  sufficient proof of absorption — there is no separate manual/browser
  checkpoint needed for a disabled-by-default local experiment.
* **Operational closure artifact**: none required beyond the PR's local
  review readiness record; this is not a monitored production surface.

Generated by: Stage (dark-factory-mode staging session) | 088-F review-followup hardening

## Plan Review

**Gate decision: PASS** (after one in-session revision; see Finding P1-1 below).

Cross-model persona spawning was not available in this session (single-model
Stage context); all personas below were evaluated by the caller model. This is
non-blocking per the plan-review skill contract ("If cross-model invocation is
not available, run all personas with the caller's model. Multi-model is
preferred but not blocking.").

### Plan Hardening Requirement Check

The plan declares `Requires plan hardening: no`. Reviewed against the one
"present (narrow)" signal (containment-security touch in Task 1): the
touch is additive-only (raises the module's own existing fail-safe exception
type earlier in the call path; introduces no new capability, no new inputs
accepted, no privilege change), is fully covered by red/green tests, and is
scoped to a throwaway disabled-by-default experiment with no downstream
dependents (confirmed via `docs/compound/093-S-review-loop-convergence.md`).
**Hardening requirement confirmed as satisfied without invoking `plan-harden`.**

### Findings

| ID | Severity | Persona | Finding | Resolution |
|---|---|---|---|---|
| P1-1 | P1 | Scope Boundary Auditor / Python Reviewer | Task 1 originally specified a 3rd test file (`test_hook_cli_entrypoint.py`) alongside the fix file and its primary test file, totaling 3 files — violating the 2-Hour Rule's `<3 files` bound for a single task. | **Resolved in this plan revision**: the end-to-end subprocess test was moved out of Task 1's required scope and recorded as an optional P3 follow-up. Task 1 now touches exactly 2 files (`workspace.py` + `test_workspace_resolution.py`). |
| P2-1 | P2 | Python Reviewer | Task 2's fix note allows either extracting a shared notes-building helper or duplicating the two `if` blocks between the early-decline and full paths, deferring the choice to build time. This risks minor logic drift between the two call sites if duplicated. | Accepted as a backlog follow-up, not blocking. Recorded in the plan's own Risks section. Build should prefer extraction if it doesn't expand the file/function count beyond the 2-Hour Rule. |
| P3-1 | P3 | Scope Boundary Auditor | The optional end-to-end `hook_cli.py` test for the non-string-cwd case (dropped from Task 1 per P1-1) would still be a reasonable defense-in-depth addition. | Advisory only. Left out of scope; may be picked up in a future stash entry if desired. |

### Persona Notes

* **Constitution Reviewer**: No violations. Principle II (TDD) satisfied by
  test-first sequencing in both tasks. Principle IV (CLI workspace
  containment) directly relevant to Task 1; the fix strengthens rather than
  weakens containment enforcement.
* **Python Reviewer**: Both fixes use idiomatic, minimal changes consistent
  with existing code shape (dataclass field reuse, existing exception type
  reuse). See P1-1 and P2-1.
* **Scope Boundary Auditor**: Confirmed both tasks stay within the two
  stash-specified files/functions; no schema, CLI-distribution, or
  cross-experiment scope creep. See P1-1.
* **Learnings Researcher**: `docs/compound/093-S-review-loop-convergence.md`
  confirms 088-F is a throwaway, isolated, disabled-by-default experiment
  with no base-harness dependency — supports the "no hardening" conclusion
  and the low-risk framing of the containment-function touch. No contrary
  prior learning found.
* **Architecture Strategist**: Task 1 and Task 2 are fully decoupled (disjoint
  files, no shared state); no coupling or sequencing risk.
* **Security Lens Reviewer** (triggered — Task 1 touches a containment-security
  function): The fix adds a strict `isinstance(payload_cwd, str)` type check
  before any path resolution occurs; no new candidate values are accepted
  that weren't already implicitly expected to be strings, and rejection
  routes through the module's existing fail-safe exception. No new attack
  surface. No P0/P1 security finding.
* **Agent-Native Parity Reviewer**: Not triggered — no MCP tool surface,
  schema, or agent-facing contract is added or changed by either fix.

### Runtime Verification and Closure Check

Confirmed adequate: both tasks are local, disabled-by-default, non-runtime-surface
changes; `pytest` green is sufficient absorption evidence. No monitoring,
rollback, or operator checkpoint artifacts are required.

