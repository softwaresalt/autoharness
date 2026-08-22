---
title: "Plan Review: Contain Ambient GIT_CONFIG_* Environment Destruction"
date: 2026-08-22
reviews: docs/plans/2026-08-22-git-config-env-containment-plan.md
reviews_hardening: docs/plans/2026-08-22-git-config-env-containment-hardening.md
source_deliberation: docs/decisions/2026-08-22-ambient-git-config-env-destruction-containment-deliberation.md
source_stash: 9DD9E323
verdict: PASS
cycle: 1
cycles_allowed: 3
unresolved_p0: 0
unresolved_p1: 0
source: docs/reviews/2026-08-22-git-config-env-containment-review.md
doc_type: plan-review
agent: stage
---

# Plan Review — `9DD9E323` / `144-F` + `145-F`

**Verdict: PASS** — 0 unresolved P0, 0 unresolved P1. Review-fix cycle 1 of 3.
Nine findings raised (2 pre-verified as non-issues, 7 resolved by amendments
R1–R9 folded into the plan).

## Gate Checklist

| Gate | Result |
| --- | --- |
| Deliberation exists and is cited (P-021 C6) | PASS — `docs/decisions/2026-08-22-ambient-git-config-env-destruction-containment-deliberation.md` |
| P-006 hardening applied where required | PASS — `requires_plan_hardening: yes`, reasoned not defaulted; A1–A10 binding |
| Options considered and rejections reasoned | PASS — R1–R9 in the deliberation, each with a criterion-linked rejection |
| Success criterion is falsifiable | PASS — `failures=0, errors=0` on the named canonical command, both platforms |
| No hidden failures (skip / xfail / weakened assertion) | PASS — prohibited in the plan, mechanically enforced by A6 (AIG-1..4) and A9 |
| Global/system config untouched | PASS — forbidden by scope guard; verified by `144.007-T` step 5 |
| Legitimate git config injections preserved | PASS — Layer 1 touches no `GIT_CONFIG_*` at all; A7 constrains Layer 4 |
| Mechanisms A and B kept separate | PASS — two features, two ordered shipments, mandatory re-measurement (A10) |
| Every task within the 2-hour rule | PASS — see sizing table below |
| Width isolation (no template+CLI+schema mixing) | PASS — `tests/**` plus one named `src/` seam, declared |
| Rollback path stated | PASS |

## Findings

### F1 (P1, RESOLVED by R1) — Victim #1 module is ambiguous

The plan lists `test_backlog_only_workspace_succeeds` at **two** locations:
`tests/test_gate_dag_readiness_cli.py:182` and
`tests/test_gate_pipeline_topology_cli.py:226`. The canonical signature is
exactly five failures with five distinct names, so exactly one of these two is
the victim. Leaving it unresolved invites a false "already green" reading and
makes the failure-set-equality gate (A2) unverifiable.

**R1 (BINDING).** `144.001-T` must record, from the verbatim baseline output
(which carries the module path), **which** module's
`test_backlog_only_workspace_succeeds` is failing, and pin it into the A2
expected-red enumeration. `144.007-T` must assert **both** modules green
regardless of which was the victim.

### F2 (P1, RESOLVED by R2) — Task 3's acceptance is not evaluable at its own boundary

Task 3 is graded on "`failures=5` -> `failures=0`", but Tasks 5 and 6 have not
landed at that point. If any seam turns out to pass an explicit `env=` copy,
Task 3 would be judged failed for work that is by design assigned to Task 5 —
and the likely reaction (widening Task 3) would breach the 2-hour rule and the
mechanism separation.

**R2 (BINDING).** `144.003-T`'s acceptance is: (a) AIG-1..AIG-4 pass, **and**
(b) the five canonical victims are green **or** every residual is captured
verbatim and explicitly routed to `144.005-T` / `144.006-T` / `144.007-T`. The
absolute `failures=0, errors=0` requirement lives at `144.007-T` only. A
residual may be routed but never masked, absorbed, or silenced.

### F3 (P1, RESOLVED by R3) — The canonical **Windows** invocation is never spelled out

The plan cites `PYTHONPATH=src python -m unittest discover -s tests`, which is
the bash form from `.github/workflows/ci.yml:112` and is **not valid
PowerShell**. Ship would improvise. Improvising to `pytest` would be actively
harmful: pytest changes collection order and grouping, which would silently
invalidate every order-dependence measurement in `144.001-T`, `144.007-T` step 2,
and all of `145.001-T`.

**R3 (BINDING).** Pin the canonical local invocation, and forbid substitution:

```powershell
# canonical full suite (Windows / PowerShell)
$env:PYTHONPATH = 'src'; python -m unittest discover -s tests

# canonical single-module standalone run (used by 145.001-T)
$env:PYTHONPATH = 'src'; python -m unittest discover -s tests -p test_gates_topology.py

# canonical single-test / ordered-pair run (used by 145.001-T)
$env:PYTHONPATH = 'src'; python -m unittest test_gates_topology.BranchOwnershipTests.<name> `
    test_gates_topology.FilesystemTopologyReadersTests.test_empty_queue_and_archive_dirs_pass_as_zero_shipments
```

`pytest` MUST NOT be substituted for any measurement, reproduction, or proof in
this plan. `pyproject.toml` declares `[tool.pytest.ini_options]` but the repo's
only real gate is the stdlib unittest suite (`ci.yml` header, lines 22–23).

### F4 (P1, RESOLVED by R4) — Hardening A1 leaves stale paths in the plan body

A1 replaced `tests/support/env_patch.py` and `tests/support/git_env.py` with
flat `tests/_env_patch.py` and `tests/_git_env.py`, but Tasks 2, 4 and 5 in the
plan body still spell the old paths, and Task 4's allowlist still reads
`frozenset({"tests/support/env_patch.py"})`.

**R4 (BINDING).** A1's spelling supersedes every `tests/support/` reference in
the plan. The harvested tasks carry only the A1 spelling; the Task 4 allowlist
is `frozenset({"_env_patch.py"})`, matched on `path.name` to match the existing
`ALLOWLIST` semantics in `tests/test_test_suite_isolation_contract.py`.

### F5 (P1, RESOLVED by R9) — Helper importability depends on a discovery-mode invariant

`from _env_patch import patched_environ` works only because
`unittest discover -s tests` sets `top_level_dir` to `tests/` and inserts it at
`sys.path[0]` (there is no `tests/__init__.py`, confirmed). That is correct for
the canonical command and for `python tests/test_x.py`, but it is an implicit
invariant that nothing currently asserts, and R8 in the deliberation
permanently forbids the `__init__.py` that would make it explicit.

**R9 (BINDING).** `144.002-T` places the helper import at module top level of
`tests/test_environ_restore_contract.py`, so canonical discovery itself proves
importability — a broken import becomes a collection ERROR in the canonical
gate, not a silent skip. `144.002-T` must additionally record, on the task, the
two supported invocations from R3 under which the import resolves, and must
**not** add `tests/__init__.py` or `tests/conftest.py` to make it work.

### F6 (P2, RESOLVED by R6) — A2's expected-red enumeration omits the third reproduction test

`test_sentinel_variables_are_removed_from_the_process_environment` is expected
**GREEN** at `144.001-T`; A2 lists only the two expected-red tests, so a
failure-set-equality gate would not notice if the third test were also red
(which would mean the reproduction module leaks sentinels into the suite).

**R6 (BINDING).** A2's enumeration explicitly lists
`test_sentinel_variables_are_removed_from_the_process_environment` as
expected-GREEN on both platforms. Its failure is a HALT, not an expected red.

### F7 (P2, RESOLVED by R5) — Two allowlists in one module invite confusion

`tests/test_test_suite_isolation_contract.py` already has `ALLOWLIST` (pinned
`frozenset()`) for the cwd-anchored-tempdir guard, and
`test_allowlist_is_exactly_expected` asserting it. Task 4 adds a second guard
with a **non-empty** allowlist to the same module. A future editor could
reasonably conflate them and relax the wrong one.

**R5 (BINDING).** The new allowlist is named `ENV_MUTATION_ALLOWLIST` and is
pinned by its own `test_env_mutation_allowlist_is_exactly_expected`. The
existing `ALLOWLIST` and `test_allowlist_is_exactly_expected` are left
**byte-identical** (they are covered by AIG-1 as an untouched-assertion check).

### F8 (P2, RESOLVED by R7) — `145.002-T` is unbounded above

`145.002-T` carries `complexity: high` with content unknown until `145.001-T`
reports. The de-risking predecessor satisfies the two-axis gate, but nothing
prevents the task from ballooning past 2 hours once its content is known.

**R7 (BINDING).** If, once `145.001-T` reports `SURVIVES`, the remediation is
assessed to exceed the 2-hour rule, `145.002-T` MUST return blocked with the
measured scope for Stage re-decomposition. It MUST NOT expand in place, and it
MUST NOT be closed by skipping, reordering, or deleting a test.

### F9 (P2, RESOLVED by R8) — Migrating the five mechanism-B polluters inside `144-F` could read as mechanism-B work

`144.003-T` migrates `tests/test_gates_topology.py` lines 994/1017/1038/1062/1085
— the five tests `141.004-T` named as the mechanism-B polluters. A reader could
conclude mechanism B was fixed in `144-F` and skip `145.001-T`, which is exactly
the conflation the operator directive forbids.

**R8 (BINDING).** `144.003-T`'s description states explicitly that migrating a
site is a **mechanism-A** change (it removes the destructive restore), that it
is **not** a mechanism-B remediation, and that `145.001-T`'s measurement remains
**mandatory and unconditional** regardless of `144-F`'s outcome. No `144-F` task
may record a mechanism-B disposition.

### N1 (pre-verified, NOT a finding) — A3's consumer grep

Hardening A3 required a grep for whole-`details` consumption. Performed during
review: `scripts/ci-topology-check.sh` contains **zero** references to
`details`; `tests/test_ci_topology_check_entrypoint.py` contains **zero**; and
every `details` assertion in `tests/test_gates_topology.py` is an individual key
lookup (`['current_branch']`, `['default_branch']`, `['detached_head']`,
`['resolved_via_ci_env_fallback']`, `['default_branch_resolved_via_ci_env_fallback']`),
never a whole-dict equality. There is **no** JSON schema for topology output
under `schemas/`. The additive `details['git_invocation_error']` key is
therefore safe. `144.006-T` must still re-run the grep at its own head and
record the result — a pre-verification at plan time is not a substitute for
verification at edit time.

### N2 (pre-verified, NOT a finding) — `tests/` is not a package

Confirmed: `tests/__init__.py` does not exist and `tests/conftest.py` does not
exist. R8's prohibition therefore preserves the status quo rather than reverting
anything, and A1's flat-module choice introduces no package.

## Sizing Review (two-axis, 2-hour rule)

| Task | Size | Complexity | Justification |
| --- | --- | --- | --- |
| `144.001-T` | S | medium | One new module, three tests; complexity is in getting the child-process probe right |
| `144.002-T` | M | medium | One helper + eight property tests incl. A4/A5 fail-closed paths |
| `144.003-T` | M | low | 13 mechanical call-site migrations; volume, not difficulty; AIG makes correctness checkable |
| `144.004-T` | S | low | One AST visitor + 4 tests, following an established in-repo pattern |
| `144.005-T` | M | medium | Pure function + six property tests + four call-site wirings |
| `144.006-T` | S | medium | Two small edits; complexity is proving verdict equality |
| `144.007-T` | S | low | Measurement and recording only; no edits |
| `145.001-T` | S | medium | Bounded: 5 pairings + standalone + negative control |
| `145.002-T` | M | high | Content unknown until `145.001-T`; de-risked by that predecessor and bounded by R7 |

No task exceeds 2 hours of human-equivalent effort. The single `complexity: high`
task has a mandatory measurement predecessor and an explicit return-blocked
bound (R7), satisfying the two-axis granularity gate.

## Amendment Index (this review)

| ID | Binding on | Summary |
| --- | --- | --- |
| R1 | `144.001-T`, `144.007-T` | Pin which module holds victim #1; assert both green at Task 7 |
| R2 | `144.003-T` | Acceptance = AIG pass + victims green **or** residual routed verbatim; `failures=0` lives at Task 7 |
| R3 | all measurement tasks | Pinned PowerShell canonical invocations; `pytest` substitution forbidden |
| R4 | Tasks 2, 4, 5 | A1's flat `tests/_env_patch.py` / `tests/_git_env.py` spelling supersedes `tests/support/` |
| R5 | `144.004-T` | New guard uses `ENV_MUTATION_ALLOWLIST`; existing `ALLOWLIST` left byte-identical |
| R6 | `144.001-T` | Third reproduction test enumerated as expected-GREEN; its failure is a HALT |
| R7 | `145.002-T` | Return blocked for re-decomposition rather than expand past the 2-hour rule |
| R8 | `144.003-T` | Migration is mechanism-A only; `145.001-T` stays mandatory and unconditional |
| R9 | `144.002-T` | Module-top import proves discovery importability; no `__init__.py`/`conftest.py` |
