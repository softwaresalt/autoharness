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
and `tests/support/git_env.py` are replaced accordingly.

**Amendment A1R (BINDING, supersedes A1's allowlist clause — cycle 2, Copilot
thread `PRRT_kwDORzpWpM6bXqlV`).** A1 originally set the Task 4 allowlist to
`frozenset({"_env_patch.py"})`. That is **wrong and is withdrawn**. The Task 4
guard forbids only the **destructive** forms — `patch.dict(os.environ, ...)`
and `os.environ.clear()`. `tests/_env_patch.py` implements **targeted
set/delete** (`os.environ[k] = v`, `del os.environ[k]`), which the guard does
**not** forbid, so the helper needs **no exemption at all**.

Worse, a path exemption would make the single file most likely to reintroduce
the defect the one file in which the destructive forms are **permitted** —
inverting the guard's entire purpose. The guard's job is to keep the destructive
forms out of `tests/`, and the helper is the file whose whole reason for
existing is that it does not use them.

Therefore: **`ENV_MUTATION_ALLOWLIST = frozenset()`** — empty, pinned, and
asserted exactly, with **no** path exemption for `_env_patch.py` or anything
else. `tests/_env_patch.py` is scanned by the guard on equal terms with every
other module and must contain **zero** forbidden forms.

Consequence for Task 2: its acceptance criterion "contains no
`os.environ.clear()` and no `patch.dict(os.environ, ...)` **beyond what the
guard allowlist authorizes**" is replaced by "contains **zero** forbidden forms
and is subject to the guard with **no exemption**".

Consequence for Task 4: the guard must be able to tell targeted set/delete apart
from the forbidden forms, so a non-vacuity **negative** case for
`os.environ[k] = v` and `del os.environ[k]` is now mandatory (they must NOT be
flagged).

### H2 — Task 1 lands a deliberately RED module; Ship needs a bounded expected-red contract (Amendment A2, BINDING)

Task 1's deliverable is a reproduction that **must fail** on Windows. Without an
explicit contract, Ship's per-task gate sees a red suite and halts, or worse,
someone "fixes" it by weakening the assertion.

**Amendment A2R (BINDING, supersedes A2 — cycle 2, consequence of A11).** Task
`144.001-T` declares an **enumerated, exhaustive expected-red set** at the
task's completion point. A11 adds a fourth test (the precondition/non-vacuity
lock), which is expected **GREEN**:

```text
EXPECTED RED AFTER 144.001-T (Windows only):
  tests/test_environ_restore_contract.py::...::test_bulk_environ_restore_preserves_empty_valued_variable_in_child_process
  tests/test_environ_restore_contract.py::...::test_bulk_environ_restore_preserves_git_config_triple_for_child_git
  + the five pre-existing canonical victims (unchanged)
EXPECTED GREEN ON BOTH PLATFORMS AFTER 144.001-T:
  tests/test_environ_restore_contract.py::...::test_blank_sentinel_survives_explicit_env_block_inheritance
  tests/test_environ_restore_contract.py::...::test_sentinel_variables_are_removed_from_the_process_environment
EXPECTED RED ON LINUX/CI AFTER 144.001-T: none
```

The task's gate is **failure-set equality against this enumeration**, not
`failures == 0`. Any failure outside the set, any missing expected failure, or
any red on Linux is a HALT. Task `144.002-T` restores `failures == 0` and is
wired `blocks`-adjacent to `144.001-T` so the expected-red window is exactly one
task wide. Under no circumstance is the expected-red window closed by
`skipTest`, `expectedFailure`, deletion, or assertion weakening.

**Why the precondition lock is a separate GREEN test, not a branch inside a RED
test.** If the blank sentinel fails to survive explicit-env-block inheritance,
the reproduction scenario is *invalid* — it proves nothing either way. Folding
that outcome into the RED tests would make it indistinguishable from a
successful reproduction, and the failure-set-equality gate would wave it
through as "expected red". As its own expected-GREEN test, an invalid
precondition shows up as a green-to-red flip **outside** the expected-red set,
which the equality gate turns into an automatic HALT with no special-casing.

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

### H8 — "Environment restoration proof" needs a specified, deterministic method (Amendment A8, WITHDRAWN — superseded by A8R)

"Capture the real process environment block" is not executable as written.
A8 specified this method:

```text
probe := python -c "import os,json,sys; sys.stdout.write(json.dumps(dict(os.environ), sort_keys=True))"
1. before := run probe as a child with env=None      -> capture stdout
2. run the canonical gate to completion
3. after  := run probe as a child with env=None      -> capture stdout
4. assert before == after (byte equality)
```

**A8 IS WITHDRAWN AS UNSOUND** (cycle 2, Copilot thread `PRRT_kwDORzpWpM6bXqlR`).

The three steps are **siblings** spawned from the same shell. The canonical gate
in step 2 runs in its own child process; every mutation it makes is to **its
own** environment block, which is destroyed when it exits. The step-3 probe is a
fresh child of the *shell*, not of the runner, so it inherits the shell's block —
which the runner never touched. `before == after` is therefore **trivially and
unconditionally true**, on every platform, whether or not the defect exists. It
proves nothing, and would have reported PASS against the un-fixed code.

### H8R — Environment restoration proof requires an in-process controller (Amendment A8R, BINDING)

**Amendment A8R (BINDING, replaces A8).** `144.007-T` step 3 uses a **three-level
process topology**. The suite runs **in-process inside the controller**, and the
probes are **children of that controller**, so the controller's own post-suite
block is what gets measured.

```text
L0 LAUNCHER  (the proof driver)
  env_block := dict(os.environ) | {"AUTOHARNESS_ENVPROBE_BLANK": "",
                                   "PYTHONPATH": "src"}
  spawn L1 with env=env_block          # explicit block: the ONLY way to
                                       # establish a blank-valued variable

L1 CONTROLLER  (long-lived; the suite runs HERE, in-process)
  a. pre  := probe()                   # L2 child, env=None
  b. PRECONDITION GATE: pre must contain AUTOHARNESS_ENVPROBE_BLANK, and every
     GIT_CONFIG_COUNT / GIT_CONFIG_KEY_n / GIT_CONFIG_VALUE_n that L0 passed in.
     If not -> emit {"status": "INVALID_PRECONDITION"} and exit. HALT at L0.
     This is neither a pass nor a fail: the measurement apparatus is invalid.
  c. run the canonical suite IN-PROCESS:
        prog = unittest.main(module=None,
                             argv=["python -m unittest", "discover", "-s", "tests"],
                             exit=False)
     -> same code path python -m unittest discover -s tests takes, so discovery,
        ordering and execution are identical; counts read from prog.result
  d. post := probe()                   # L2 child, env=None
  e. emit {"status":"OK","pre":pre,"post":post,
           "testsRun":…, "failures":…, "errors":…, "skipped":[…]}

L2 PROBE  (grandchild of L0, child of L1)
  python -c "import os,json,sys; sys.stdout.write(json.dumps(dict(os.environ), sort_keys=True))"
  spawned with env=None so it inherits L1's REAL block
```

L0 then asserts:

1. `status == "OK"` (the precondition held — non-vacuity).
2. `pre == post` byte-equality of the serialized payloads.
3. **By explicit key**: `AUTOHARNESS_ENVPROBE_BLANK` and every
   `GIT_CONFIG_COUNT` / `GIT_CONFIG_KEY_n` / `GIT_CONFIG_VALUE_n` present in
   `pre` is present in `post` with an identical value. This is separate from
   (2) because a whole-block comparison is satisfied by two blocks that are
   **both** missing the variable.
4. **Equivalence to the canonical gate**: `testsRun`, `failures`, `errors`, and
   the skipped set from the in-process run equal those from `144.007-T` proof 1's
   canonical subprocess run. If they differ, the in-process harness is not
   equivalent to the canonical entry point and the proof is void — HALT.

**Mandatory negative control.** Re-run the identical L0/L1/L2 topology with
step (c) replaced by a deliberate bare
`unittest.mock.patch.dict(os.environ, {"X": "y"})` enter/exit. On Windows,
`post` MUST then **lose** `AUTOHARNESS_ENVPROBE_BLANK` while `pre` had it.
Without this control, a green result in (2)/(3) could be vacuous — a probe that
captured nothing, or a topology that never carried the blank in the first place.
The negative control is a throwaway local measurement and is never committed.

**Why the blank sentinel can only come from L0's explicit block.** Setting it
in-process (`os.environ[name] = ""`) is *itself* the destructive operation under
study: on Windows that call reaches `SetEnvironmentVariableW(name, L"")` and
deletes the variable outright, so the precondition could never be established
that way. An explicit environment block handed to `CreateProcessW` carries a
`NAME=\0` entry and is inherited as a genuinely empty value. This asymmetry is
the entire reason the topology has an L0.

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

### H12 — The reproduction cannot establish its own precondition in-process (Amendment A11, BINDING)

**Copilot thread `PRRT_kwDORzpWpM6bXqlM`, cycle 2.** Task 1 as written said:

> Set a uniquely-named sentinel (e.g. `AUTOHARNESS_ENVTEST_EMPTY_<uuid4hex>`) to `""`.

and, for test 2:

> Build a self-consistent three-pair `GIT_CONFIG_*` triple **in-process** with
> the last `VALUE_n` empty.

Both are **self-defeating on the very platform they target**. `os.environ[name] = ""`
is *itself* the destructive operation under study: on Windows it reaches
`SetEnvironmentVariableW(name, L"")`, which deletes the variable from the real
process block immediately. The sentinel is therefore already gone **before** the
`patch.dict` round trip runs, so the reproduction would observe "sentinel
missing" for the wrong reason and appear to confirm a mechanism it never
exercised — a **false positive** that would have validated the entire design on
non-evidence.

**Amendment A11 (BINDING).** The reproduction uses the same **three-level
topology** as A8R. The blank sentinel is established **only** by an explicit
environment block handed to a child process, and its arrival is **verified**
before the round trip.

```text
L0 CONTROLLER  (the unittest test method)
  sentinel  := "AUTOHARNESS_ENVTEST_EMPTY_" + uuid4().hex
  env_block := dict(os.environ) | {sentinel: ""} | {"PYTHONPATH": "src"}
  spawn L1 with env=env_block, argv carrying sentinel name + variant

L1 RUNNER  (long-lived; the operation under test happens HERE)
  a. pre := probe()                    # L2 child, env=None
  b. PRECONDITION GATE: sentinel must be present in pre.
     If absent -> emit {"status":"INVALID_PRECONDITION"} and exit.
  c. operation under test, selected by --variant:
       destructive : bare unittest.mock.patch.dict(os.environ, {...}) enter/exit
       fixed       : patched_environ(...) enter/exit          (from 144.002-T on)
  d. post := probe()                   # L2 child, env=None
  e. emit {"status":"OK","pre_has_sentinel":…,"post_has_sentinel":…}

L2 PROBE  (child of L1, env=None -> inherits L1's REAL block)
  python -c "import os,json,sys; sys.stdout.write(json.dumps(dict(os.environ), sort_keys=True))"
```

Binding consequences:

1. **A fourth test is added**, `test_blank_sentinel_survives_explicit_env_block_inheritance`,
   which asserts only the precondition (`status == "OK"` and
   `pre_has_sentinel is True`). It is **expected GREEN on both platforms** and
   is the non-vacuity lock for the whole module. See A2R for why this must be a
   separate green test rather than a branch inside a red one.
2. **Test 1** (`..._preserves_empty_valued_variable_in_child_process`) asserts
   `post_has_sentinel is True` for the `destructive` variant — the desired
   invariant, hence RED on Windows at `144.001-T`, GREEN on Linux, and GREEN on
   both once re-pointed at the `fixed` variant in `144.002-T`.
3. **Test 2** (`..._preserves_git_config_triple_for_child_git`) uses the same
   topology: L0 puts a complete triple into the explicit block —
   `GIT_CONFIG_COUNT=3`, `KEY_0=safe.bareRepository`/`VALUE_0=explicit`,
   `KEY_1=credential.interactive`/`VALUE_1=never`, `KEY_2=core.fsmonitor`/
   `VALUE_2=""` — L1's precondition probe runs `git version` in L2 and requires
   exit 0, then after the round trip requires exit 0 again with no
   `missing config value` in stderr. The triple is **never** assembled by
   in-process assignment.
4. **ISOLATION (mandatory).** Every destructive environment operation is
   confined to the **L1 child**. The L0 test process must never execute
   `patch.dict(os.environ, ...)`, `os.environ.clear()`, or an empty-value
   assignment. Otherwise `tests/test_environ_restore_contract.py` becomes a
   **fourteenth polluting site** and corrupts the very suite it exists to
   measure — while also being flagged by the Task 4 guard it is supposed to
   satisfy.
5. `INVALID_PRECONDITION` is a **HALT**, distinguishable from both pass and
   fail. It means the platform did not carry a blank value through explicit
   block inheritance, so the scenario proves nothing and the design returns to
   Stage.

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
* **Cycle 2 addition.** A8 and A1's allowlist clause were both *unsound as
  written* and were caught by hosted review, not by this hardening pass. The
  common failure mode in both: a mechanism was specified at the level of
  intent ("probe the environment", "exempt the helper") without tracing the
  actual process/enforcement topology it would execute in. A8R and A11 now
  specify process levels explicitly (L0/L1/L2) precisely so the topology is
  reviewable rather than implied.

## Amendment Index

| ID | Binding on | Summary |
| --- | --- | --- |
| A1 | Tasks 2, 4, 5 | Flat `tests/_env_patch.py` + `tests/_git_env.py`; no new package or `__init__.py` |
| **A1R** | Tasks 2, 4 | **Supersedes A1's allowlist clause.** `ENV_MUTATION_ALLOWLIST = frozenset()` — EMPTY. No path exemption for `_env_patch.py`: targeted set/delete is not a forbidden form, and an exemption would legalise the destructive forms in the one file most likely to reintroduce them |
| ~~A2~~ | — | Superseded by A2R |
| **A2R** | Task 1 | Enumerated expected-red set **plus** an expected-GREEN set (precondition lock + sentinel cleanup); gate is failure-set equality; one-task window |
| A3 | Task 6 | `details['git_invocation_error']` additive-and-absent-on-success; verdict-equality test; consumer grep |
| A4 | Task 2 | `ValueError` on `""` overrides, uniformly on all platforms, before mutation |
| A5 | Task 2 | `RuntimeError` at entry if any touched key's prior value is `""`; fail closed, no torn state |
| A6 | Tasks 3, 6 | AIG-1..AIG-4 AST assertion-inventory equality with per-line citation |
| A7 | Task 5 | Exact `GIT_CONFIG_{COUNT,KEY_n,VALUE_n}` shape only; other `GIT_CONFIG*` pass through; never invent a count |
| ~~A8~~ | — | **WITHDRAWN AS UNSOUND** — sibling shell probes cannot observe a child runner's mutations; `before == after` was trivially true |
| **A8R** | Task 7 | L0/L1/L2 topology; suite runs **in-process** in L1; probes are L1's children; precondition gate, per-key assertion, canonical-equivalence check, mandatory negative control |
| A9 | Task 7 | Named skip-set subset check, not a bare count bound |
| A10 | Task 8 | `SUBSUMED` requires standalone + all five pairings + a reverted-checkout negative control |
| **A11** | Task 1 | L0/L1/L2 topology for the reproduction; blank sentinel established **only** via an explicit env block and **verified inherited** before the round trip; adds a fourth expected-GREEN precondition test; all destructive ops confined to L1 |
