---
title: "Plan: Contain Ambient GIT_CONFIG_* Environment Destruction and Restore the Canonical Windows Full-Suite Gate"
date: 2026-08-22
source_deliberation: docs/decisions/2026-08-22-ambient-git-config-env-destruction-containment-deliberation.md
source_stash: 9DD9E323
requires_plan_hardening: yes
hardening_artifact: docs/plans/2026-08-22-git-config-env-containment-hardening.md
review_artifact: docs/reviews/2026-08-22-git-config-env-containment-review.md
review_verdict: PASS
amendments_binding: [A1, A1R, A2R, A3, A4, A5, A6, A7, A8R, A9, A10, A11, R1, R2, R3, R4, R5R, R6, R7, R8, R9, R10, R11, R12]
withdrawn_amendments: [A2, A8, R5]
review_cycle: 2
review_cycle_context: "PR #397 Copilot review-fix cycle 1 (artifact cycle 2 of 3)"
features: [144-F, 145-F]
shipments: [152-S, 153-S]
source: docs/plans/2026-08-22-git-config-env-containment-plan.md
doc_type: plan
agent: stage
---

# Plan: Contain Ambient `GIT_CONFIG_*` Environment Destruction

## Requires plan hardening

**yes.** Signals: the change touches many modules across the `tests/` family
*and* one `src/autoharness/` diagnostic seam; it alters process-environment
handling for the entire suite; it has platform-divergent behavior
(Windows vs. POSIX) that must be proven CI-neutral; and it introduces a new
structural guard that constrains all future test authoring. See
`docs/plans/2026-08-22-git-config-env-containment-hardening.md`.

## Objective

The canonical gate

```text
PYTHONPATH=src python -m unittest discover -s tests
```

must pass on Windows **and** on Linux/CI, with:

* zero skipped, `expectedFailure`d, deleted, or weakened assertions;
* every ambient, well-formed `GIT_CONFIG_*` injection still in effect for
  child git processes;
* no mutation of global, system, or ambient-shell configuration;
* the real Win32 process environment block byte-identical before and after
  every test that touches the environment.

## Scope Guard

| Surface | In scope | Out of scope |
| --- | --- | --- |
| `tests/**` | yes | — |
| `src/autoharness/gates/topology.py` | `_run_git` diagnostic seam only (Task 6) | any change to gate verdict semantics, tokens, or exit codes |
| `.github/workflows/ci.yml` | no | — |
| `pyproject.toml` | no | — |
| Global/system/user git config | no | — |
| `templates/**`, `schemas/**`, `docs/**` (except plan/closure artifacts) | no | — |

Adding `tests/__init__.py` or `tests/conftest.py` is **explicitly forbidden**
(deliberation R8): it changes `unittest discover` top-level-directory
resolution suite-wide.

## Mechanism Separation (binding)

Mechanism **A** (ambient `GIT_CONFIG_*` destruction) is feature `144-F` /
shipment `152-S`. Mechanism **B** (`BranchOwnershipTests` intra-file order) is
feature `145-F` / shipment `153-S`, which is **blocked by** `152-S`.

No task in `144-F` may claim to fix mechanism B. No task in `145-F` may be
closed by asserting mechanism A's fix without the explicit re-measurement in
`145.001-T`. The two are not merged, not conflated, and not co-scheduled.

---

## Shipment 152-S / Feature 144-F — Mechanism A

### Task 1 (`144.001-T`) — Test-first reproduction (must be RED before any fix)

**Deliverable:** a new module `tests/test_environ_restore_contract.py`
containing an executable reproduction of the destruction mechanism.

**Process topology (amendment A11, BINDING).** The blank sentinel CANNOT be
established in-process: `os.environ[name] = ""` *is* the destructive operation
under study and deletes the variable on Windows before the round trip runs.
Every test below therefore uses a three-level topology in which L0 seeds the
blank via an **explicit environment block**, L1 verifies it arrived and performs
the operation under test, and L2 probes L1's real block.

```text
L0 CONTROLLER  (the unittest test method)
  sentinel  := "AUTOHARNESS_ENVTEST_EMPTY_" + uuid4().hex
  env_block := dict(os.environ) | {sentinel: ""} | {"PYTHONPATH": "src"}
  spawn L1 with env=env_block, argv carrying the sentinel name + variant

L1 RUNNER  (long-lived; the operation under test happens HERE)
  a. pre := probe()                    # L2 child, env=None
  b. PRECONDITION GATE: sentinel present in pre?
     no -> emit {"status":"INVALID_PRECONDITION"}; exit   (HALT at L0)
  c. operation under test (--variant):
       destructive : bare unittest.mock.patch.dict(os.environ, {...}) enter/exit
       fixed       : patched_environ(...) enter/exit      (from 144.002-T on)
  d. post := probe()                   # L2 child, env=None
  e. emit {"status":"OK","pre_has_sentinel":…,"post_has_sentinel":…}

L2 PROBE  (child of L1, env=None -> inherits L1's REAL block)
  python -c "import os,json,sys; sys.stdout.write(json.dumps(dict(os.environ), sort_keys=True))"
```

**ISOLATION (mandatory, A11.4).** Every destructive environment operation is
confined to the **L1 child**. The L0 test process must never execute
`patch.dict(os.environ, ...)`, `os.environ.clear()`, or an empty-value
assignment — otherwise this module becomes a fourteenth polluting site and
corrupts the very suite it measures, and is flagged by the Task 4 guard.

**Required tests:**

0. `test_blank_sentinel_survives_explicit_env_block_inheritance`
   Runs L0 -> L1 and asserts only the precondition: `status == "OK"` and
   `pre_has_sentinel is True`. This is the **non-vacuity lock** for the whole
   module. **Expected GREEN on both platforms.** A failure here means the
   platform did not carry a blank value through explicit-block inheritance, the
   scenario proves nothing, and the design returns to Stage — see A2R for why
   this is a separate green test rather than a branch inside a red one.
1. `test_bulk_environ_restore_preserves_empty_valued_variable_in_child_process`
   Runs the `destructive` variant and asserts `post_has_sentinel is True` —
   the **desired invariant**, so on Windows it is RED today and on Linux it is
   GREEN today. It must NOT be platform-gated, skipped, or `expectedFailure`d.
2. `test_bulk_environ_restore_preserves_git_config_triple_for_child_git`
   Same topology. L0 puts a complete triple into the explicit block:
   `GIT_CONFIG_COUNT=3`, `KEY_0=safe.bareRepository`/`VALUE_0=explicit`,
   `KEY_1=credential.interactive`/`VALUE_1=never`,
   `KEY_2=core.fsmonitor`/`VALUE_2=""`. L1's precondition probe runs
   `git version` in L2 and requires exit 0; after the round trip it requires
   exit 0 again with no `missing config value` in stderr. The triple is
   **never** assembled by in-process assignment. Skip **only** if
   `shutil.which("git")` is None, matching the existing precedent at
   `tests/test_repo_root_artifacts.py:23`.
3. `test_sentinel_variables_are_removed_from_the_process_environment`
   `tearDown`-verified: every sentinel this module introduces is gone from
   `os.environ` **and** from a freshly spawned child's environment when the
   module finishes. Because all seeding happens in L0's *explicit block* rather
   than in `os.environ`, this should hold trivially — which is exactly what it
   locks in. **Expected GREEN on both platforms.**

**Halt condition (mandatory):** if test 1 does **not** fail on Windows at the
current head, the deliberation's mechanism is not confirmed. Stop, record the
observation on the task, and return the shipment blocked. Do not proceed to
Task 2 on an unconfirmed hypothesis. Separately, if test 0 fails, the
measurement apparatus is invalid — also a HALT, and distinguishable from both
pass and fail.

**Acceptance:** RED on Windows (tests 1 and 2), GREEN on Linux, tests 0 and 3
GREEN on both, at the branch head *before* Task 2 lands. Record the verbatim
failure output on the task.

---

### Task 2 (`144.002-T`) — Restore-by-diff environment helper

**Deliverable:** `tests/support/env_patch.py` (new package dir
`tests/support/` with **no** `__init__.py` at `tests/` level — the support
package gets its own `tests/support/__init__.py`, which does not affect
top-level discovery because `unittest discover -s tests` only imports modules
matching the `test*.py` pattern).

**API:**

```python
@contextlib.contextmanager
def patched_environ(**overrides: str | None) -> Iterator[None]:
    """Set/delete only the named keys; restore only those keys on exit.

    A value of ``None`` deletes the key for the duration of the block.
    Restoration is by targeted diff: keys absent before are deleted, keys
    present before are re-set to their prior value. ``os.environ.clear()``
    is NEVER called, so untouched variables are never removed and re-added
    and therefore never destroyed by the Win32 empty-value-delete behavior.
    """
```

**Required properties, each with its own test in
`tests/test_environ_restore_contract.py`:**

* Restores a pre-existing key to its exact prior value.
* Deletes a key that did not exist before the block.
* Restores a key that existed before and was deleted inside the block.
* Re-entrant / nestable without cross-talk.
* Exception-safe: restoration happens on exception, and the exception
  propagates unchanged.
* **Non-destruction:** an untouched variable whose value is `""` is still
  visible to a spawned child process after the block exits. This is the test
  from Task 1 re-pointed at the helper, and it must go GREEN on Windows here.
* **No-op equivalence:** a `patched_environ()` block with zero overrides leaves
  a spawned child's environment byte-identical (compare the child's
  serialized `os.environ` before and after).

**Acceptance:** Task 1's tests 1 and 2 become GREEN on Windows when the bare
`patch.dict` is replaced by `patched_environ`; still GREEN on Linux. The
helper module itself contains no `os.environ.clear()` and no
`patch.dict(os.environ...)`.

---

### Task 3 (`144.003-T`) — Migrate every bulk `os.environ` mutation under `tests/`

**Sites (from a direct literal-text scan; the task must re-scan and reconcile
before editing, and record any site the scan finds that this list omits):**

| Module | Lines |
| --- | --- |
| `tests/test_gates_topology.py` | 1004, 1023, 1045, 1069, 1090, 1112, 1141, 1173, 1207, 1236, 1266 |
| `tests/test_gate_dag_readiness_cli.py` | 217 |
| `tests/test_gate_pipeline_topology_cli.py` | 273 |

The five explicitly named mechanism-B polluters (`test_gates_topology.py`
lines 994, 1017, 1038, 1062, 1085) are inside this set and are migrated here
**as mechanism-A sites**, not as a mechanism-B fix.

**Rules:**

* Replace `patch.dict('os.environ', {...})` with `patched_environ(...)`.
* Replace the `import os as _os; _os.environ.pop('X', None)` idiom inside a
  block with an explicit `X=None` override on the helper call.
* **Zero assertion-line edits.** Assertion callsites, their arguments, and
  their messages are byte-identical before and after. Diff review must confirm
  changes are confined to import lines, `with` statements, and the deleted
  `pop` idiom lines.
* No test is renamed, reordered, added, or removed in this task.

**Acceptance:** the canonical Windows full suite goes from `failures=5` to
`failures=0` (or, if any failure remains, it is captured verbatim and handed
to Task 7 — it must not be masked). Linux/CI result unchanged. An AST-extracted
inventory of assertion callsites in every touched module is identical
pre/post.

---

### Task 4 (`144.004-T`) — AST structural regression guard

**Deliverable:** new test class in the existing
`tests/test_test_suite_isolation_contract.py`, following that module's
established shape.

**Guard:** recursively over every `*.py` under `tests/`, an `ast.NodeVisitor`
flags:

* any call to `patch.dict` / `mock.patch.dict` / `unittest.mock.patch.dict`
  whose first argument is `os.environ` or the string literal `'os.environ'`;
* any call to `os.environ.clear()` / `environ.clear()`.

Per compound learning
`docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md`,
this is AST-structural, **not** a line regex, and must match regardless of
line wrapping, argument ordering, decorator vs. context-manager form, or
import alias.

**Required companion tests (mirroring the existing module's contract):**

* `test_env_mutation_allowlist_is_exactly_expected` — allowlist pinned to
  **`frozenset()`** (EMPTY) and asserted exactly, so it cannot silently grow.
  **Amendment A1R (BINDING):** there is **no** path exemption for
  `tests/_env_patch.py`. The guard forbids only the *destructive* forms
  (`patch.dict(os.environ, ...)`, `os.environ.clear()`); the helper implements
  *targeted set/delete* (`os.environ[k] = v`, `del os.environ[k]`), which is
  not forbidden, so it needs no exemption. Exempting it by path would legalise
  the destructive forms inside the one file most likely to reintroduce them,
  inverting the guard's purpose.
* Non-vacuity positive: a synthetic source string using each forbidden shape
  (context-manager form, decorator form, aliased import, multi-line call,
  string-literal `'os.environ'` first argument, `os.environ.clear()`) is
  detected.
* Non-vacuity negative: `patched_environ(...)`,
  `patch.dict(some_other_dict, ...)`, and — **mandatory under A1R** — the
  targeted forms `os.environ[k] = v` and `del os.environ[k]` are **not**
  flagged. Without this case the guard could not distinguish the helper's
  legitimate implementation from the forbidden forms, which is what makes the
  empty allowlist workable.
* The failure message names every offending `path:line`.

**Acceptance:** guard is GREEN at head (after Task 3) with an EMPTY allowlist —
including over `tests/_env_patch.py`, which is scanned on equal terms — and
provably fails if any migrated site is reverted.

---

### Task 5 (`144.005-T`) — `GIT_CONFIG_*` self-consistency normalizer (defense in depth)

**Deliverable:** `tests/support/git_env.py` exposing

```python
def consistent_git_env(base: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return an environment mapping whose GIT_CONFIG_* triple is
    self-consistent: only (KEY_n, VALUE_n) pairs where BOTH are present are
    kept, survivors are renumbered contiguously from 0, and GIT_CONFIG_COUNT
    is set to the surviving count. Every other variable passes through
    unchanged."""
```

**Binding properties, each individually tested:**

* **Preservation:** every well-formed pair survives with its key and value
  unchanged, in original relative order. `safe.bareRepository=explicit` and
  `credential.interactive=never` specifically must survive.
* **Narrowness:** only a pair whose `VALUE_n` is genuinely **absent** is
  dropped. A pair whose value is present-but-empty on a platform that can
  represent it is **kept**.
* **Provable no-op:** when the input triple is already self-consistent, the
  returned mapping is `==` to the input, including `GIT_CONFIG_COUNT` and key
  ordering. This is what makes the change a no-op on Linux and in CI, and it
  is asserted, not assumed.
* **No `GIT_CONFIG_*` at all:** input without the triple is returned unchanged.
* **Malformed `GIT_CONFIG_COUNT`** (non-integer, negative): returned unchanged
  and left for git to reject — the normalizer never invents a value.
* **Never clears:** the function is pure; it does not mutate `os.environ`.

Wire `env=consistent_git_env()` into the direct git-invoking test seams:
`tests/test_repo_root_artifacts.py:34`, `tests/test_telemetry_gitignore_template.py:42/65/104`.

**Acceptance:** all new property tests GREEN on both platforms; the four wired
seams unchanged in assertion content; suite still green.

---

### Task 6 (`144.006-T`) — Assertion integrity: stop masking infrastructure failures

Two independent mis-diagnoses, fixed without weakening any assertion.

1. **`src/autoharness/gates/topology.py:200` `_run_git`.**
   Currently `check=False` and `return ""` on nonzero — an infrastructure
   failure is laundered into "no branch". Change: on a nonzero exit, still
   return `""` (verdict semantics **unchanged**, no token or exit-code change)
   but additionally emit the captured `stderr` on a diagnostic channel that
   surfaces in the check `details`. Add a test asserting that a simulated
   nonzero git exit produces the same token and exit code as today **and**
   carries the captured stderr in `details`.
   Same anti-pattern as compound learning
   `2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md`.

2. **`tests/test_telemetry_gitignore_template.py:33`.**
   `assertEqual(result.returncode, 0, f"{rel} is not gitignored")` reports a
   gitignore defect when git actually died at config-parse time.
   `git check-ignore` returns `0` = ignored, `1` = not ignored, `>=128` = error.
   Change: keep the `returncode == 0` assertion **exactly as strong**, but
   branch the *message* on `returncode >= 2` to report the captured stderr as
   a git invocation failure rather than a gitignore defect.

**Acceptance:** no assertion is removed, relaxed, or made conditional; only
failure-path diagnosis changes. A test proves the new message appears for a
simulated `returncode=128` and the original message for `returncode=1`.

---

### Task 7 (`144.007-T`) — Full-suite proof and environment-restoration verification

**Deliverable:** recorded evidence, no production edit.

1. Run the canonical gate on Windows: `PYTHONPATH=src python -m unittest discover -s tests`.
   Record the verbatim tail. **Required:** `failures=0, errors=0`, skip count
   not greater than the pre-change baseline of 20.
2. Run the canonical gate a second time in the **same** shell session to prove
   the fix is order- and repetition-stable.
3. Prove environment restoration **under amendment A8R** (the original A8 is
   WITHDRAWN AS UNSOUND: three sibling probes spawned from one shell can never
   observe a child runner's mutations, so `before == after` was trivially true
   on every platform and would have reported PASS against the un-fixed code).

   A8R requires a three-level topology in which the suite runs **in-process**
   inside a controller, and the probes are that controller's **children**:

   ```text
   L0 LAUNCHER   env_block := dict(os.environ) | {"AUTOHARNESS_ENVPROBE_BLANK": "",
                                                  "PYTHONPATH": "src"}
                 spawn L1 with env=env_block

   L1 CONTROLLER (long-lived; the suite runs HERE, in-process)
     a. pre  := probe()                       # L2 child, env=None
     b. PRECONDITION GATE: pre must contain AUTOHARNESS_ENVPROBE_BLANK and every
        GIT_CONFIG_COUNT / KEY_n / VALUE_n L0 passed in; else INVALID_PRECONDITION -> HALT
     c. prog = unittest.main(module=None,
                             argv=["python -m unittest","discover","-s","tests"],
                             exit=False)      # same code path as the canonical gate
     d. post := probe()                       # L2 child, env=None
     e. emit pre, post, and prog.result counts

   L2 PROBE      python -c "import os,json,sys; sys.stdout.write(json.dumps(dict(os.environ), sort_keys=True))"
                 spawned with env=None -> inherits L1's REAL block
   ```

   L0 asserts: (i) `status == "OK"`; (ii) `pre == post` byte-equality;
   (iii) by **explicit key**, `AUTOHARNESS_ENVPROBE_BLANK` and every
   `GIT_CONFIG_COUNT`/`KEY_n`/`VALUE_n` in `pre` is present in `post` with an
   identical value — separate from (ii) because a whole-block comparison is
   satisfied by two blocks that are **both** missing the variable;
   (iv) **canonical equivalence**: the in-process run's `testsRun`, `failures`,
   `errors` and skipped set equal proof 1's canonical subprocess run, else the
   harness is not equivalent and the proof is void.

   **Mandatory negative control:** re-run the identical topology with step (c)
   replaced by a deliberate bare `patch.dict(os.environ, {"X": "y"})`
   enter/exit; on Windows `post` MUST then lose the blank sentinel. Without it,
   a green (ii)/(iii) could be vacuous. Throwaway local measurement, never
   committed.
4. Confirm Linux/CI parity: CI green on the PR with no new skips.
5. Confirm no global/system git config was touched:
   `git config --global --list` and `git config --system --list` identical
   before and after.
6. Record the outcome and hand any residual to Task `145.001-T` — do not
   absorb a mechanism-B residual into this feature.

**Acceptance:** all six recorded; feature closes only on `failures=0, errors=0`.

---

## Shipment 153-S / Feature 145-F — Mechanism B (ordered after 152-S)

### Task 8 (`145.001-T`) — Re-measure the intra-file order dependence (diagnosis only, terminal disposition)

Runs at `152-S`'s merged head. **Changes no source file.**

1. Run `tests/test_gates_topology.py` standalone (94 tests) exactly as
   `141.004-T` did.
2. Run each of the five named polluters immediately followed by victim #2:
   `test_ci_mode_detached_head_resolves_via_github_head_ref`,
   `test_ci_mode_detached_head_resolves_via_github_ref_name_for_push`,
   `test_ci_mode_push_branch_name_with_slash_is_accepted`,
   `test_ci_mode_tag_push_does_not_resolve_as_branch`,
   `test_ci_mode_detached_head_with_no_env_fallback_still_blocks`
   -> `test_empty_queue_and_archive_dirs_pass_as_zero_shipments`.
3. Record a **terminal disposition**:
   * `SUBSUMED` — all five pairings pass. Evidence must include the passing
     output for all five pairings **and** the standalone run, plus a causal
     statement tying the disappearance to `144.003-T`'s migration. `145.002-T`
     then closes as a recorded no-op.
   * `SURVIVES` — any pairing still fails. Capture the verbatim failure and the
     minimal reproducing pair, then proceed to `145.002-T`.

**Acceptance:** a terminal disposition is recorded. `INCONCLUSIVE` is **not**
an accepted outcome here — unlike `141.001-T`, the candidate set is now five
named tests and one named victim, so exhaustive pairwise measurement is
bounded and complete.

### Task 9 (`145.002-T`) — Remediate a surviving mechanism B, or record an evidenced no-op

* If `145.001-T` recorded `SUBSUMED`: close as a recorded no-op citing that
  evidence. No source edit.
* If `SURVIVES`: isolate the residual shared state from the minimal reproducing
  pair and remove it at its source. Same constraints as Task 3 — zero assertion
  edits, no skip/`expectedFailure`, no test deletion or reordering. Re-run the
  standalone file and the full canonical suite as proof.

**De-risking note:** this task is rated `complexity: high` because its content
is unknown until `145.001-T` reports. `145.001-T` **is** its mandatory
de-risking predecessor, satisfying the two-axis granularity gate.

---

## Test-First / Red-Green Matrix

| Task | RED before | GREEN after | Platform |
| --- | --- | --- | --- |
| `144.001-T` | reproduction tests fail on Windows | — (RED is the deliverable) | Win RED / Linux GREEN |
| `144.002-T` | Task 1 tests | Task 1 tests + helper property tests | both GREEN |
| `144.003-T` | 5 canonical victims | 5 canonical victims | both GREEN |
| `144.004-T` | guard fails on un-migrated source | guard passes; fails on revert | both GREEN |
| `144.005-T` | normalizer property tests | normalizer property tests | both GREEN |
| `144.006-T` | masking-diagnosis tests | masking-diagnosis tests | both GREEN |
| `144.007-T` | — | full canonical suite | both GREEN |
| `145.001-T` | — | disposition recorded | Win measured |
| `145.002-T` | surviving pair (if any) | surviving pair | both GREEN |

## Rollback

Each task is independently revertible. Reverting `144.003-T` alone restores the
prior red state without breaking anything else; the Task 4 guard would then
fail, which is the intended signal. `144.006-T` is behavior-preserving for gate
verdicts and can be reverted independently of the rest.

## Risks

| Risk | Mitigation |
| --- | --- |
| Win32 empty-value-delete hypothesis is wrong | `144.001-T` halt condition: no RED reproduction -> stop and re-deliberate |
| `patched_environ` misses a restore edge case | Six explicit property tests including exception-safety and nesting |
| Guard is over-broad and blocks legitimate future use | **Empty** allowlist asserted exactly, plus mandatory negative non-vacuity cases proving targeted set/delete and `patch.dict(other_dict, ...)` are not flagged (A1R/R5R) |
| Normalizer changes CI behavior | Provable-no-op property test asserts `==` on already-consistent input |
| Assertion integrity work weakens a gate | `144.006-T` changes messages/diagnostics only; verdict-equality test required |
| Mechanism B silently folded into A | `145.001-T` is a mandatory, separately-shipped, terminal-disposition measurement |

---

## Binding Amendments (hardening A1–A11, review R1–R12)

This section is normative and **supersedes** the task text above wherever they
differ. Full text: `docs/plans/2026-08-22-git-config-env-containment-hardening.md`
and `docs/reviews/2026-08-22-git-config-env-containment-review.md`.

### Superseded paths (A1 / R4)

All references to `tests/support/env_patch.py` and `tests/support/git_env.py`
above are **superseded** by flat modules with **no new package and no new
`__init__.py`**:

* `tests/_env_patch.py` — `patched_environ`
* `tests/_git_env.py` — `consistent_git_env`

Imported as `from _env_patch import patched_environ`. Task 4's allowlist is
`ENV_MUTATION_ALLOWLIST = frozenset()` — **EMPTY**, with no path exemption for
`_env_patch.py` (amendment **A1R**, cycle 2).

### Canonical invocations (R3, BINDING — `pytest` substitution forbidden)

```powershell
# full canonical suite (Windows / PowerShell)
$env:PYTHONPATH = 'src'; python -m unittest discover -s tests

# single-module standalone (145.001-T)
$env:PYTHONPATH = 'src'; python -m unittest discover -s tests -p test_gates_topology.py

# ordered pair (145.001-T)
$env:PYTHONPATH = 'src'; python -m unittest test_gates_topology.BranchOwnershipTests.<name> `
    test_gates_topology.FilesystemTopologyReadersTests.test_empty_queue_and_archive_dirs_pass_as_zero_shipments
```

CI equivalent (unchanged, `.github/workflows/ci.yml:112`):
`PYTHONPATH=src python -m unittest discover -s tests`.

### Amendment summary

| ID | Binding on | Requirement |
| --- | --- | --- |
| A1 / R4 | Tasks 2, 4, 5 | Flat `tests/_env_patch.py` + `tests/_git_env.py`; no new package or `__init__.py` |
| **A1R** | Tasks 2, 4 | **Supersedes A1's allowlist clause.** `ENV_MUTATION_ALLOWLIST = frozenset()` — EMPTY, no path exemption for `_env_patch.py`; targeted set/delete is not a forbidden form, and an exemption would legalise the destructive forms in the file most likely to reintroduce them |
| ~~A2 / R6~~ | — | Superseded by **A2R** |
| **A2R** | Task 1 | Expected-RED set (tests 1–2 + 5 victims) **and** expected-GREEN set (test 0 precondition lock + test 3 sentinel cleanup); gate is failure-set **equality**, not `failures == 0`; one-task window |
| A3 | Task 6 | `details['git_invocation_error']` additive, **absent** on success; verdict-equality test; consumer grep re-run at edit time |
| A4 | Task 2 | `ValueError` on any `""` override, uniformly on all platforms, raised before any mutation |
| A5 | Task 2 | `RuntimeError` at entry if any touched key's prior value is `""`; fail closed, no torn state |
| A6 | Tasks 3, 6 | AIG-1..AIG-4 AST assertion-inventory equality, N1–N3 change allowlist, per-line citation |
| A7 | Task 5 | Only the exact `GIT_CONFIG_{COUNT,KEY_n,VALUE_n}` triple; `GIT_CONFIG_PARAMETERS`/`GLOBAL`/`SYSTEM`/`NOSYSTEM` pass through untouched; never invent a count |
| ~~A8~~ | — | **WITHDRAWN AS UNSOUND** — three sibling shell probes cannot observe a child runner's mutations; `before == after` was trivially true |
| **A8R** | Task 7 | L0/L1/L2 topology; suite runs **in-process** in L1 via `unittest.main(module=None, argv=[...], exit=False)`; probes are L1's children; precondition gate, byte-equality, per-key assertion, canonical-equivalence check, mandatory negative control |
| A9 | Task 7 | Named skip-**set** subset check, not a bare count bound |
| A10 | Task 8 | `SUBSUMED` requires standalone + all five pairings + a reverted-checkout negative control; otherwise `INCONCLUSIVE-VACUOUS` -> treat as `SURVIVES` |
| **A11** | Task 1 | L0/L1/L2 topology for the reproduction; blank sentinel established **only** via an explicit env block and **verified inherited** before the round trip; adds expected-GREEN test 0; all destructive ops confined to L1 |
| R1 | Tasks 1, 7 | Pin which module holds victim #1 from the verbatim baseline; assert **both** modules green at Task 7 |
| R2 | Task 3 | Acceptance = AIG pass **and** (victims green **or** residual captured verbatim and routed to Tasks 5/6/7); `failures=0` lives at Task 7 |
| R3 | all measurement tasks | Pinned PowerShell invocations above; `pytest` MUST NOT be substituted |
| ~~R5~~ | — | Superseded by **R5R** |
| **R5R** | Task 4 | `ENV_MUTATION_ALLOWLIST` is EMPTY and pinned by its own test; existing `ALLOWLIST` and its test left byte-identical; mandatory negative case proving targeted set/delete is not flagged |
| R7 | Task 9 | Return blocked for Stage re-decomposition rather than expand past the 2-hour rule |
| R8 | Task 3 | Migration is **mechanism-A only**; `145.001-T` stays mandatory and unconditional; no `144-F` task records a mechanism-B disposition |
| R9 | Task 2 | Module-top import in the contract test proves discovery importability; no `tests/__init__.py`, no `tests/conftest.py` |
| **R10** | Task 1 | L0 test process performs **no** destructive env operation; the module must not become a fourteenth polluting site |
| **R11** | Task 7 | A8R's in-process run must be **count-equivalent** to the canonical subprocess gate, else the proof is void |
| **R12** | Task 2 | `tests/_env_patch.py` contains **zero** forbidden forms and is guarded with no exemption |
