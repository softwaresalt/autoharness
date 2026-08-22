---
title: "Plan Review: Contain Ambient GIT_CONFIG_* Environment Destruction"
date: 2026-08-22
reviews: docs/plans/2026-08-22-git-config-env-containment-plan.md
reviews_hardening: docs/plans/2026-08-22-git-config-env-containment-hardening.md
source_deliberation: docs/decisions/2026-08-22-ambient-git-config-env-destruction-containment-deliberation.md
source_stash: 9DD9E323
verdict: PASS
cycle: 2
cycle_context: "PR #397 Copilot review-fix cycle 1 (artifact cycle 2 of 3)"
reviewed_head: 72bfdd9c3964f04d3287a8d67914cbcd33572fe6
cycles_allowed: 3
unresolved_p0: 0
unresolved_p1: 0
source: docs/reviews/2026-08-22-git-config-env-containment-review.md
doc_type: plan-review
agent: stage
---

# Plan Review — `9DD9E323` / `144-F` + `145-F`

**Verdict: PASS** — 0 unresolved P0, 0 unresolved P1.

**Cycle 2** (PR #397 Copilot review-fix cycle 1) at head
`72bfdd9c3964f04d3287a8d67914cbcd33572fe6`. Cycle 1 findings F1–F9 remain
resolved and are retained below unchanged. Cycle 2 adds C1–C3 (hosted Copilot
threads) and N1–N3 (findings this cycle raised while fixing them). Cycles used:
2 of 3.

---

## Cycle 2 — PR #397 hosted review findings

All three Copilot threads are **P-021 C1 same-contract-surface corrections**:
each targets an artifact Stage owns (task carriers and the plan/hardening/review
they derive from), on the same contract surface this shipment already governs.
They are therefore fixed **in place** in this cycle — no deferred stash entry,
no scope expansion, no new feature.

Severity: **C1 and C2 are P0** — each would have produced a *false PASS* against
un-fixed code, which is worse than a red gate because it manufactures
unwarranted confidence. C3 is P1.

### C1 (P0, RESOLVED by A11 + R10) — `PRRT_kwDORzpWpM6bXqlM`, `.backlogit/queue/144.001-T.md`

**Thread:** the reproduction seeds the empty sentinel with `os.environ[name] = ""`,
but the root-cause model says that call *already* deletes it from the Win32
block. Seed the blank variable in an outer process's explicit environment block,
verify a child sees it before the round trip, then run the before/after probe
inside that process. Duplicate at ~line 41.

**Confirmed, and it is worse than a redundancy.** `os.environ[name] = ""` **is**
the destructive operation under study. On Windows it reaches
`SetEnvironmentVariableW(name, L"")`, which deletes the variable outright. The
sentinel would therefore be gone **before** the `patch.dict` round trip ever
ran, and test 1 would observe "sentinel missing" *for the wrong reason* — a
**false positive** confirming a mechanism it never exercised. The entire design
rests on `144.001-T`'s halt condition; a reproduction that cannot fail honestly
would have validated the whole feature on non-evidence.

The duplicate at line 41 is the same defect in test 2: "Build a self-consistent
three-pair `GIT_CONFIG_*` triple **in-process** with the last `VALUE_n` empty"
is unconstructible on Windows for exactly the same reason.

**Resolution — A11 (BINDING)** installs an executable three-level topology:
L0 controller seeds the blank **only** via an explicit env block handed to
`CreateProcessW`; L1 runner **verifies inheritance** with a probe before the
round trip, performs the destructive/fixed operation, and probes again; L2
probes are children of L1. A fourth test,
`test_blank_sentinel_survives_explicit_env_block_inheritance`, is added as an
expected-GREEN non-vacuity lock, and `INVALID_PRECONDITION` is a HALT
distinguishable from both pass and fail.

**R10 (BINDING)** adds the isolation constraint the thread implies but does not
state: every destructive operation is confined to the **L1 child**. Without it,
`tests/test_environ_restore_contract.py` would itself become a **fourteenth
polluting site**, corrupting the suite it exists to measure — and would be
flagged by the Task 4 guard it is supposed to satisfy.

Carriers corrected: `.backlogit/queue/144.001-T.md` (both occurrences),
`.backlogit/queue/144.002-T.md`, plan Task 1, hardening H12/A11 and A2R.

### C2 (P0, RESOLVED by A8R + R11) — `PRRT_kwDORzpWpM6bXqlR`, `.backlogit/queue/144.007-T.md`

**Thread:** the shell probes before/after the runner are siblings and cannot
detect child-runner mutations. Run the suite in-process inside a controller that
probes child inheritance before and after.

**Confirmed; A8 is unsound and is WITHDRAWN.** A8's three steps were all
children of the same shell. The canonical gate in step 2 runs in its own process
and every mutation it makes dies with that process. The step-3 probe is a fresh
child of the *shell*, whose block the runner never touched. `before == after` was
therefore **trivially and unconditionally true on every platform, defect present
or not** — proof 3 would have reported PASS against the un-fixed code, and would
have done so most convincingly precisely when it mattered least.

**Resolution — A8R (BINDING)** replaces A8 with the same L0/L1/L2 topology:
L1 runs the canonical suite **in-process** via
`unittest.main(module=None, argv=["python -m unittest", "discover", "-s", "tests"], exit=False)`
— literally the code path `python -m unittest discover -s tests` takes, so
discovery, ordering and execution are identical — and the probes are **L1's own
children**, so L1's post-suite block is what gets measured. Adds a precondition
gate, byte-equality, an explicit per-key `GIT_CONFIG_*` assertion, and a
**mandatory negative control** (bare `patch.dict` in place of the suite must
lose the blank sentinel on Windows) so a green result cannot be vacuous.

**R11 (BINDING)** adds the equivalence obligation A8R creates: running the suite
in-process is only a valid substitute for the canonical gate if it is
**count-equivalent** to it. `testsRun`, `failures`, `errors` and the skipped set
must match proof 1's subprocess run, else the harness has diverged and the proof
is void.

Carriers corrected: `.backlogit/queue/144.007-T.md`, plan Task 7 step 3,
hardening H8 (withdrawn) / H8R.

### C3 (P1, RESOLVED by A1R + R5R) — `PRRT_kwDORzpWpM6bXqlV`, `.backlogit/queue/144.004-T.md`

**Thread:** `_env_patch.py` should not be path-allowlisted. Targeted set/delete
is not forbidden; a path exemption would permit destructive forms. Keep the new
allowlist empty.

**Confirmed.** The guard forbids only `patch.dict(os.environ, ...)` and
`os.environ.clear()`. The helper implements **targeted set/delete**
(`os.environ[k] = v`, `del os.environ[k]`) — not a forbidden form, so it needs
**no exemption at all**. Granting one would make the single file most likely to
reintroduce the defect the one file in which the destructive forms are
*permitted*, inverting the guard's purpose. The original justification ("the
helper is the one legitimate place the underlying primitives may appear")
conflated *the primitives the helper uses* with *the forms the guard forbids*;
they are disjoint.

**Resolution — A1R (BINDING):** `ENV_MUTATION_ALLOWLIST = frozenset()` — empty,
pinned, asserted exactly, no exemption for anything. `tests/_env_patch.py` is
scanned on equal terms.

**R5R (BINDING, supersedes R5)** adds the consequence: the guard must now be
able to tell targeted set/delete apart from the forbidden forms, so a
non-vacuity **negative** case for `os.environ[k] = v` and `del os.environ[k]` is
mandatory. Without it the empty allowlist would be unworkable.

**R12 (BINDING)** corrects the downstream carrier: `144.002-T`'s acceptance
"contains no `os.environ.clear()` and no `patch.dict(os.environ, ...)` *beyond
what the guard allowlist authorizes*" becomes "contains **zero** forbidden forms
and is subject to the guard with **no exemption**".

Carriers corrected: `.backlogit/queue/144.004-T.md`,
`.backlogit/queue/144.002-T.md`, plan Task 4 and the A1/R4 superseded-paths
block, hardening A1R, review R4/R5 (below).

---

## Cycle 2 — findings raised while fixing the above

### N1 (P1, RESOLVED by A2R) — the precondition outcome would have been swallowed by the failure-set-equality gate

A11 introduces a third possible outcome, `INVALID_PRECONDITION`. Folded into the
RED tests it would be **indistinguishable from a successful reproduction**, and
A2's failure-set-equality gate would wave it through as "expected red" — a
second false-PASS path opened by the fix for the first one.

**A2R (BINDING)** makes the precondition its own **expected-GREEN** test. An
invalid precondition then appears as a green-to-red flip *outside* the
expected-red set, which the equality gate converts to an automatic HALT with no
special-casing. A2 is superseded; the enumeration now carries both an
expected-RED and an expected-GREEN set.

### N2 (P2, RESOLVED in A8R text) — the in-process controller needs `PYTHONPATH` and programmatic counts

`unittest.main(..., exit=False)` writes its summary to stderr; the controller
must read counts from `prog.result`, not by scraping. And `discover -s tests`
plus `import autoharness` requires `src` importable, which L0 must place in the
explicit env block it is already constructing. Both are now stated in A8R.

### N3 (P2, RESOLVED, no action) — A9's skip enumeration survives the topology change

A9 references "the git-unavailable skip in `tests/test_environ_restore_contract.py`".
Under A11 the `shutil.which("git")` check stays in L0, so the skip is still
raised by the same module and A9's named-set contract is unaffected. Recorded so
the reader does not have to re-derive it.

---

## Cycle 2 — verification

| Check | Result |
| --- | --- |
| Shipment manifests unchanged | PASS — `152-S` = 8 items, `153-S` = 3 items, byte-identical to cycle 1 |
| Dependency graph unchanged | PASS — 9 task edges + `153-S` -> `152-S`; acyclic |
| Claimability unchanged | PASS — `152-S` alone claimable; `153-S` blocked |
| Task sizing/complexity preserved | PASS — all 9 tasks retain `size` + `complexity` |
| No backlog item created, deleted, or re-parented | PASS — cycle 2 changed **contract text only** |
| Mechanism separation intact | PASS — no mechanism-B disposition added to `144-F` |
| Stage role boundary | PASS — no source/test edit, no build/test run, no commit/push/PR/thread/merge |

---

## Cycle 1 — original findings (retained, all resolved)

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
is `frozenset()` — **EMPTY**, per **A1R (cycle 2)**, which withdraws this
finding's original `frozenset({"_env_patch.py"})` value. See C3 above.

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

**SUPERSEDED BY R5R (cycle 2).** R5 originally pinned
`ENV_MUTATION_ALLOWLIST` to `frozenset({"_env_patch.py"})`. Per C3/A1R it is
now pinned **EMPTY**, and a non-vacuity negative case proving targeted
set/delete is not flagged becomes mandatory. The naming and byte-identical
clauses above stand unchanged.

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

### Cycle 2 (PR #397 review-fix cycle 1)

| ID | Binding on | Summary |
| --- | --- | --- |
| A1R | `144.002-T`, `144.004-T` | `ENV_MUTATION_ALLOWLIST = frozenset()` — EMPTY; no path exemption for `_env_patch.py` |
| A2R | `144.001-T` | Expected-RED **and** expected-GREEN sets; precondition lock is its own green test |
| A8R | `144.007-T` | L0/L1/L2 topology; suite runs in-process in L1; probes are L1's children; negative control mandatory |
| A11 | `144.001-T` | L0/L1/L2 reproduction topology; blank sentinel via explicit env block, inheritance verified before the round trip |
| R5R | `144.004-T` | Empty allowlist + mandatory negative case for targeted set/delete |
| R10 | `144.001-T` | All destructive env ops confined to the L1 child; L0 must not become a polluting site |
| R11 | `144.007-T` | In-process run must be count-equivalent to the canonical subprocess gate |
| R12 | `144.002-T` | Helper contains **zero** forbidden forms; guarded with no exemption |
| — | — | **WITHDRAWN:** A2 (superseded by A2R), A8 (unsound), R5 (superseded by R5R) |

### Cycle 1 (original local plan review)

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
