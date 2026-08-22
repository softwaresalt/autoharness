---
title: "Plan Hardening: Contain Ambient GIT_CONFIG_* Environment Destruction (P-006)"
date: 2026-08-22
policy: P-006
hardens: docs/plans/2026-08-22-git-config-env-containment-plan.md
source_deliberation: docs/decisions/2026-08-22-ambient-git-config-env-destruction-containment-deliberation.md
source_stash: 9DD9E323
features: [144-F, 145-F]
shipments: [152-S, 153-S]
source: docs/plans/2026-08-22-git-config-env-containment-hardening.md
doc_type: plan-hardening
agent: stage
---

# Plan Hardening (P-006)

## Why hardening is required

`requires_plan_hardening: yes`. Four independent elevated-blast-radius signals:

1. **Breadth across a template/test family.** 13+ modules under `tests/`, plus
   a new shared helper every future test may depend on.
2. **Cross-surface reach.** `tests/**` plus one `src/autoharness/` seam
   (`gates/topology.py`), i.e. product code, not just tests.
3. **Platform-divergent semantics.** The whole defect is a Windows/POSIX
   environment-block divergence; a fix that is correct on one platform can be
   silently wrong on the other, and CI only exercises one of them.
4. **New standing constraint.** The Task 4 AST guard permanently restricts how
   every future test may mutate the environment.

## Hardening Findings and Binding Amendments

### H1 — `tests/support/` package would change discovery surface and import naming (Amendment A1, BINDING)

The plan proposed `tests/support/env_patch.py` with a `tests/support/__init__.py`.
Three problems:

* `unittest discover -s tests` recurses into a directory only when it is an
  importable package. Adding `tests/support/__init__.py` makes discovery
  descend into it — harmless today (nothing matches `test*.py`), but it enlarges
  the discovery surface for no benefit.
* With no `tests/__init__.py`, `top_level_dir` is `tests/`, so the import spelling
  is `from support.env_patch import ...`, **not** `tests.support.env_patch`. A
  top-level module named `support` is a generic name occupying `sys.path[0]` for
  the whole test process — a real collision hazard.
* It creates a second, subtly different answer to "is `tests/` a package?",
  which is exactly the ambiguity R8 rejected.

**Amendment A1 (BINDING).** Use **flat, underscore-prefixed modules directly
under `tests/`**, with **no** new `__init__.py` anywhere:

* `tests/_env_patch.py` — exports `patched_environ`.
* `tests/_git_env.py` — exports `consistent_git_env`.

Imported as `from _env_patch import patched_environ`. These names do not match
the `test*.py` discovery pattern, so they are never collected as test modules,
and they add no package. All plan references to `tests/support/env_patch.py`
and `tests/support/git_env.py` are replaced accordingly, including the Task 4
allowlist, which becomes `frozenset({"_env_patch.py"})` (matched on
`path.name`, consistent with the existing `ALLOWLIST` semantics in
`tests/test_test_suite_isolation_contract.py`).

### H2 — Task 1 lands a deliberately RED module; Ship needs a bounded expected-red contract (Amendment A2, BINDING)

Task 1's deliverable is a reproduction that **must fail** on Windows. Without an
explicit contract, Ship's per-task gate sees a red suite and halts, or worse,
someone "fixes" it by weakening the assertion.

**Amendment A2 (BINDING).** Task `144.001-T` declares an **enumerated,
exhaustive expected-red set** at the task's completion point:

```text
EXPECTED RED AFTER 144.001-T (Windows only):
  tests/test_environ_restore_contract.py::...::test_bulk_environ_restore_preserves_empty_valued_variable_in_child_process
  tests/test_environ_restore_contract.py::...::test_bulk_environ_restore_preserves_git_config_triple_for_child_git
  + the five pre-existing canonical victims (unchanged)
EXPECTED RED ON LINUX/CI AFTER 144.001-T: none
```

The task's gate is **failure-set equality against this enumeration**, not
`failures == 0`. Any failure outside the set, any missing expected failure, or
any red on Linux is a HALT. Task `144.002-T` restores `failures == 0` and is
wired `blocks`-adjacent to `144.001-T` so the expected-red window is exactly one
task wide. Under no circumstance is the expected-red window closed by
`skipTest`, `expectedFailure`, deletion, or assertion weakening.

### H3 — `_run_git` diagnostic must be strictly additive and schema-safe (Amendment A3, BINDING)

Task 6 adds captured stderr to the topology check `details`. Verified during
hardening: there is **no** JSON schema for topology gate output under
`schemas/` (the schema set is execution-epoch, harness-config,
harness-manifest, tool-telemetry-event, validation-gates, workspace-profile),
and `tests/test_gates_topology.py` asserts `details` via individual key
lookups (`details['current_branch']`, `['default_branch']`,
`['detached_head']`, `['resolved_via_ci_env_fallback']`,
`['default_branch_resolved_via_ci_env_fallback']`), never by whole-dict
equality. An additive key is therefore safe — but only if it stays additive.

**Amendment A3 (BINDING).** The diagnostic is added under one **new** key,
`details['git_invocation_error']`, and:

* it is **absent** (key not present at all) whenever every git invocation
  succeeded — so the success-path `details` payload is byte-identical to today;
* it never replaces, renames, or reorders an existing key;
* `_run_git`'s return contract is unchanged: still `""` on nonzero exit, so the
  gate's token and exit code are **identical** on every path;
* Task 6 must add a test asserting **verdict equality**: for a simulated
  nonzero git exit, `result.exit_code`, `check.token`, and every pre-existing
  `details` key are equal to the pre-change behavior;
* Task 6 must grep `scripts/ci-topology-check.sh` and
  `tests/test_ci_topology_check_entrypoint.py` for whole-`details` equality or
  strict-key consumption and record the finding. If any consumer does compare
  exactly, the diagnostic is routed to stderr logging only and the `details`
  key is dropped.

### H4 — `patched_environ` must reject empty-string overrides uniformly (Amendment A4, BINDING)

`patched_environ(X="")` would itself invoke the exact Win32 empty-value delete
this plan exists to avoid, producing a helper that is correct on Linux and
broken on Windows — a platform-divergent trap worse than the original bug.

**Amendment A4 (BINDING).** `patched_environ` raises `ValueError` on any
override whose value is `""`, **on every platform** (uniform behavior, no
platform branch), with a message directing the author to pass `None` to delete
the key or a real value to set it. Required test: the `ValueError` is raised on
the current platform, is raised **before** any mutation occurs, and leaves
`os.environ` untouched.

### H5 — Restoring a key whose prior value was empty is impossible on Windows; fail closed at entry (Amendment A5, BINDING)

If a caller overrides a key that already held `""` (exactly `GIT_CONFIG_VALUE_2`'s
shape), then on exit the helper must restore `""` — which on Windows deletes it.
The helper would silently reintroduce the defect through its own restore path.

**Amendment A5 (BINDING).** At **entry**, before any mutation, `patched_environ`
inspects the prior value of every key it is about to touch. If any prior value
is `""`, it raises `RuntimeError` naming the key and explaining that an
empty-valued variable cannot be faithfully restored on this platform. Fail
closed at entry means nothing has been mutated yet, so there is no torn state.
Required tests: raised before mutation; `os.environ` unchanged after the raise;
the message names the offending key.

### H6 — Assertion integrity needs a mechanical check, not a promise (Amendment A6, BINDING)

Tasks 3 and 6(2) claim "zero assertion-line edits". Prose claims of this kind
have failed in this repository before (the `141-F`/`143-F` cycle needed a
canonical assertion-integrity gate for exactly this reason).

**Amendment A6 (BINDING).** For every module touched by `144.003-T` and by
`144.006-T` part 2, the task must produce an **AST-extracted assertion
inventory** and assert pre/post equality:

* **AIG-1** — for every `self.assert*` / `self.fail` callsite: method name, the
  `ast.unparse` of each positional argument, and the `ast.unparse` of each
  keyword argument, in source order. Pre and post lists must be **equal**.
* **AIG-2** — the only permitted exception is `144.006-T` part 2's message
  argument on `tests/test_telemetry_gitignore_template.py:33`, which must be
  cited line-by-line in the task record as the single authorized divergence,
  and whose *non-message* arguments (`result.returncode`, `0`) must still
  compare equal.
* **AIG-3** — authorized change classes for `144.003-T` are exhaustively:
  (N1) import lines, (N2) `with` statement headers, (N3) removal of the
  `import os as _os` / `_os.environ.pop(...)` idiom inside a migrated block.
  Any edit outside N1–N3 is disallowed.
* **AIG-4** — every diff line must be cited to one of N1–N3 (or to AIG-2);
  uncited edits fail the task.

### H7 — The normalizer must not touch `GIT_CONFIG_PARAMETERS` or invent values (Amendment A7, BINDING)

Git has a second, unrelated injection channel, `GIT_CONFIG_PARAMETERS`, plus
`GIT_CONFIG_GLOBAL`/`GIT_CONFIG_SYSTEM`/`GIT_CONFIG_NOSYSTEM`. A normalizer that
"tidies `GIT_CONFIG_*`" by prefix match would silently disable them.

**Amendment A7 (BINDING).** `consistent_git_env` operates **only** on the
`GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_<n>` / `GIT_CONFIG_VALUE_<n>` triple,
matched by exact name shape with an integer suffix. `GIT_CONFIG_PARAMETERS`,
`GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM`, `GIT_CONFIG_NOSYSTEM`, and any other
`GIT_CONFIG*` name are passed through **untouched**, with a dedicated
pass-through test for each. The function never invents, defaults, or repairs a
malformed `GIT_CONFIG_COUNT` — a non-integer or negative count is returned
unchanged for git itself to reject.

### H8 — "Environment restoration proof" needs a specified, deterministic method (Amendment A8, BINDING)

"Capture the real process environment block" is not executable as written.

**Amendment A8 (BINDING).** `144.007-T` step 3 uses exactly this method, in one
shell session:

```text
probe := python -c "import os,json,sys; sys.stdout.write(json.dumps(dict(os.environ), sort_keys=True))"
1. before := run probe as a child with env=None      -> capture stdout
2. run the canonical gate to completion
3. after  := run probe as a child with env=None      -> capture stdout
4. assert before == after (byte equality)
5. additionally assert, by explicit key, that GIT_CONFIG_COUNT and every
   GIT_CONFIG_KEY_n / GIT_CONFIG_VALUE_n present in `before` is present in
   `after` with an identical value
```

Step 5 is separate from step 4 because a whole-block comparison can be
satisfied by two blocks that are both missing the variable.

### H9 — Skip-count baseline must be enumerated, not just bounded (Amendment A9, BINDING)

`144.007-T` accepts "skips not greater than the baseline of 20". A bound alone
allows a *substitution* — a newly skipped real test offset by a no-longer-skipped
one.

**Amendment A9 (BINDING).** Record the **named set** of skipped tests before and
after. The post set must be a subset of the pre set, plus at most the
git-unavailable skip in `tests/test_environ_restore_contract.py`, which must be
enumerated explicitly and must **not** trigger on a machine where
`shutil.which("git")` is non-None. Any newly skipped canonical test is a HALT.

### H10 — Mechanism-B subsumption must not be provable by mechanism-A's own runner (Amendment A10, BINDING)

`145.001-T`'s `SUBSUMED` disposition could be recorded from a single full-suite
green run, which proves nothing about the *intra-file* order dependence that
`141.004-T` measured standalone.

**Amendment A10 (BINDING).** `SUBSUMED` requires **all** of:

1. the standalone `tests/test_gates_topology.py` run (94 tests) green;
2. **all five** explicit polluter -> victim pairings run individually and green;
3. a negative control: the same five pairings executed against a checkout with
   `144.003-T`'s migration reverted, reproducing the original failure — proving
   the pairings are still capable of failing and the measurement is not vacuous.

Without item 3 the disposition is `INCONCLUSIVE-VACUOUS` and `145.002-T`
proceeds as if `SURVIVES`. The negative control is a throwaway local
measurement; it is never committed or pushed.

### H11 — Residual risk accepted, recorded

* The Win32 empty-value-delete behavior is inferred from documented platform
  behavior plus the captured failure signature. `144.001-T`'s halt condition is
  the control; there is no other mitigation and none is claimed.
* Reproduction test 1 is a near-tautology on Linux (the invariant already
  holds). It is retained anyway as a cross-platform invariant lock, and this
  weakness is recorded rather than hidden.
* `144.006-T` part 1 touches product code for a diagnosis-quality reason. It is
  independently justified by compound learning
  `2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md` and is
  verdict-preserving under A3, but it is a real, if small, scope widening beyond
  `tests/` and is declared as such rather than smuggled in.

## Amendment Index

| ID | Binding on | Summary |
| --- | --- | --- |
| A1 | Tasks 2, 4, 5 | Flat `tests/_env_patch.py` + `tests/_git_env.py`; no new package or `__init__.py`; allowlist `{"_env_patch.py"}` |
| A2 | Task 1 | Enumerated expected-red set; gate is failure-set equality; one-task window |
| A3 | Task 6 | `details['git_invocation_error']` additive-and-absent-on-success; verdict-equality test; consumer grep |
| A4 | Task 2 | `ValueError` on `""` overrides, uniformly on all platforms, before mutation |
| A5 | Task 2 | `RuntimeError` at entry if any touched key's prior value is `""`; fail closed, no torn state |
| A6 | Tasks 3, 6 | AIG-1..AIG-4 AST assertion-inventory equality with per-line citation |
| A7 | Task 5 | Exact `GIT_CONFIG_{COUNT,KEY_n,VALUE_n}` shape only; other `GIT_CONFIG*` pass through; never invent a count |
| A8 | Task 7 | Specified child-probe byte-equality method plus explicit per-key `GIT_CONFIG_*` assertion |
| A9 | Task 7 | Named skip-set subset check, not a bare count bound |
| A10 | Task 8 | `SUBSUMED` requires standalone + all five pairings + a reverted-checkout negative control |
