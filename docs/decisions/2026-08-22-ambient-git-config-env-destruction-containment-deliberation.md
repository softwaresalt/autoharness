---
title: "Containing Ambient GIT_CONFIG_* Environment Destruction in the Canonical Windows Test Suite"
date: 2026-08-22
status: decided
source_stash: 9DD9E323
ancestor_stash: E8158860
lineage_features: [141-F, 143-F]
lineage_shipments: [149-S, 151-S]
lineage_tasks: [141.001-T, 141.004-T, 143.001-T, 143.002-T]
lineage_pr: 393
source: docs/decisions/2026-08-22-ambient-git-config-env-destruction-containment-deliberation.md
doc_type: deliberation
agent: stage
route: claude-opus-5 / anthropic / high
engram_status: ENGRAM_DEGRADED
---

# Deliberation: Containing Ambient `GIT_CONFIG_*` Environment Destruction in the Canonical Windows Test Suite

## Provenance

Stash entry `9DD9E323` (kind `bug`, priority raised medium -> high at triage)
is the unresolved residual of operator-selected bug `E8158860`. It carries the
`DEFERRED SCOPE EXPANSION` marker, so P-021 C6 forced this deliberate route
regardless of shape or size, and no planning step was reachable until this
artifact existed.

Prior chain, all closed:

| Item | Outcome |
| --- | --- |
| `141-F` / `149-S` | Diagnosis. Terminal `VERDICT: INCONCLUSIVE`. All 58 ambient-cwd `dir=Path.cwd()` sites removed; `tests/test_test_suite_isolation_contract.py` created with an AST guard and an emptied allowlist. |
| `143-F` / `151-S` / `143.001-T` | Both `check=True` git subprocess sites in `tests/` made self-diagnosing (unconditional), which upgraded the five failures from `ERRORS` to `FAILURES` and captured verbatim stderr. |
| `143-F` / `151-S` / `143.002-T` | Disposition **R3-still-red**. No polluter isolated; "make NO source edit under `tests/`; there is no speculative-fix path." Residual captured as `9DD9E323`. PR #393, merged `f389fd59`. |

Hosted Linux CI has been green throughout. The canonical **local Windows** gate
is red with an identical five-test signature.

## The Defect

Canonical gate (identical in CI at `.github/workflows/ci.yml:112` and locally):

```text
PYTHONPATH=src python -m unittest discover -s tests
```

Five failures, stable and reproducible:

| # | Test | Module:line | Git subprocess seam |
| --- | --- | --- | --- |
| 1 | `test_backlog_only_workspace_succeeds` | `test_gate_dag_readiness_cli.py:182`, `test_gate_pipeline_topology_cli.py:226` | indirect, via the topology/DAG gate |
| 2 | `test_empty_queue_and_archive_dirs_pass_as_zero_shipments` | `test_gates_topology.py:112` | indirect, via `evaluate(mode='ci')` |
| 3 | `test_root_tracked_json_matches_allowlist` | `test_repo_root_artifacts.py:23` | direct, `git ls-files -z -- *.json` (`check=True`, self-diagnosing) |
| 4 | `test_git_check_ignore_matches_metrics_artifacts` | `test_telemetry_gitignore_template.py:33` | direct, `git check-ignore` (`check=False`, asserts `returncode == 0`) |
| 5 | `test_emitted_metrics_artifacts_are_never_tracked` | `test_telemetry_gitignore_template.py:74` | direct, `self._git(...)` (`check=True`, self-diagnosing) |

Captured verbatim stderr:

```text
error: missing config value GIT_CONFIG_VALUE_2
fatal: unable to parse command-line config
```

The ambient environment of this host carries a well-formed-looking git
command-line-config injection triple:

```text
GIT_CONFIG_COUNT=3
GIT_CONFIG_KEY_0=safe.bareRepository   GIT_CONFIG_VALUE_0=explicit
GIT_CONFIG_KEY_1=credential.interactive GIT_CONFIG_VALUE_1=never
GIT_CONFIG_KEY_2=core.fsmonitor         GIT_CONFIG_VALUE_2=(empty)
```

A fresh shell runs `git status` fine. The same triple, inherited by a
long-running `python -m unittest discover` process and passed to a child git
process *partway through the suite*, reports `VALUE_2` as **absent**, not empty.

## Evidence Developed in This Deliberation

`9DD9E323` records that a literal-text search for `GIT_CONFIG_COUNT` /
`GIT_CONFIG_KEY` / `GIT_CONFIG_VALUE` across `tests/`, `src/autoharness/`, and
installed `.venv` dependencies returned **zero** matches. That conclusion is
accepted and was not re-derived (ENGRAM_DEGRADED; no broad search repeated).

The decisive new evidence is that **no code needs to name those variables** to
destroy them. Direct literal-text scan of `tests/` for bulk-environment
mutation:

```text
test_gates_topology.py  L1004 L1023 L1045 L1069 L1090 L1112 L1141 L1173 L1207 L1236 L1266
                        with patch.dict('os.environ', ...)
test_gate_dag_readiness_cli.py      L217  mock.patch.dict(os.environ, {...})
test_gate_pipeline_topology_cli.py  L273  mock.patch.dict(os.environ, {...})
```

`unittest.mock.patch.dict` restores a patched mapping by **clear-then-update**,
not by targeted diff: `_unpatch_dict` calls `_clear_dict(in_dict)` followed by
`in_dict.update(original)`. For `os.environ` that is `__delitem__` (`unsetenv`)
for every key, then `__setitem__` (`putenv`) for every key. The `clear=False`
argument controls only what is visible *inside* the block; the exit path is
clear-then-update either way. That is why `clear=False` sites
(`test_gates_topology.py:1090`, `:1045`, `:1069`) are still implicated.

On Windows, `putenv` reaches `SetEnvironmentVariableW(name, L"")` for an
empty value, and that call **deletes** the variable from the true Win32
process environment block rather than storing an empty one. CPython's
`os.environ` keeps its own dict entry showing `''`, so the destruction is
invisible from Python. `subprocess.run([...])` with `env=None` passes
`lpEnvironment=NULL` to `CreateProcessW`, so the child inherits the *real*,
now-inconsistent block: `GIT_CONFIG_COUNT=3` and `GIT_CONFIG_KEY_2` present,
`GIT_CONFIG_VALUE_2` gone. Git then fails exactly as captured.

This single mechanism explains every otherwise-puzzling observation:

* **Zero code references.** Nothing names the variables; a blanket
  clear-and-restore destroys them incidentally.
* **Only "partway through" a long process.** The destruction requires at least
  one `patch.dict(os.environ, ...)` block to *exit* first.
* **Fresh shell is fine.** The real block is intact until Python mutates it.
* **Linux/CI green.** POSIX `setenv(name, "")` stores an empty value; nothing
  is deleted, so the triple stays self-consistent.
* **`os.environ` "looks" correct in a debugger.** The Python-level dict and the
  Win32 block have diverged.

Two independent seams then convert the broken child environment into the
observed failures, and one of them is silent:

* `src/autoharness/gates/topology.py:200` `_run_git(...)` uses `check=False`
  and returns `""` on any nonzero exit. A git *infrastructure* failure is
  laundered into "no branch" -> `detached_head` -> `BRANCH_MISMATCH` ->
  `exit_code == 1`. Victims #1 and #2 assert `exit_code == 0` and therefore
  fail with a **false domain diagnosis**. This is the same failure shape as
  compound learning `2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md`.
* `tests/test_telemetry_gitignore_template.py:33` asserts
  `result.returncode == 0` with the message `"{rel} is not gitignored"`. When
  git dies at config-parse time the test reports a **gitignore defect that does
  not exist**.

### Relationship between the two recorded mechanisms

The operator directive requires the ambient `GIT_CONFIG_*` mechanism (A) and
the `BranchOwnershipTests` intra-file order mechanism (B) to be kept
**separate**, and they are kept separate in the harvested backlog: mechanism A
is `144-F`/`152-S`, mechanism B is `145-F`/`153-S`, ordered and not merged.

This deliberation nevertheless records a falsifiable prediction, because
refusing to state it would be withholding evidence:

* `unittest` sorts classes via `dir(module)` and methods alphabetically.
  `BranchOwnershipTests` (B) sorts before `FilesystemTopologyReadersTests` (F),
  so the five named polluters always run before victim #2 in the same file.
* All five named polluters are `patch.dict('os.environ', ...)` sites, i.e. they
  are exactly the mechanism-A destruction trigger.
* Victim #2 reaches git through `_run_git`'s silent `check=False` swallow,
  which is precisely why B *looked* like an unrelated mechanism.

Prediction: **B is a symptom of A and will disappear once A is contained.**
This prediction is *not* assumed. `145-F` opens with a dedicated re-measurement
task that must record a terminal disposition of `SUBSUMED` (with proof) or
`SURVIVES`, and only then, if it survives, remediates B on its own terms. No
mechanism-B work is skipped or folded into mechanism A on the strength of a
prediction.

## Decision Criteria

From the operator directive and the harness policy set:

1. The canonical **local Windows** suite must become green.
2. No real failure may be hidden — no skip, no `expectedFailure`, no weakened
   assertion, no broadened tolerance.
3. No mutation of global or system git configuration, and no mutation of the
   user's ambient shell environment outside the test process.
4. Repository-contained, deterministic normalization or containment at the
   **narrowest authoritative** test-runner or subprocess boundary.
5. Legitimate git config injections must **not** be indiscriminately cleared.
   `safe.bareRepository=explicit` and `credential.interactive=never` are
   protective settings; discarding them would silently change git's behavior
   under test.
6. A permanent red gate is not an acceptable outcome.
7. Linux/CI behavior must be provably unchanged.

## Options Considered

### R1 — Accept the residual as a permanent Windows-local known issue

Zero work; preserves the status quo. **Rejected.** Violates criteria 1 and 6
explicitly. A permanently red canonical gate trains every future agent and
operator to ignore the gate, which destroys the value of the other 1717 tests.

### R2 — Clear all `GIT_CONFIG_*` variables at test-runner start

Unset `GIT_CONFIG_COUNT`/`KEY_n`/`VALUE_n` once, before discovery.
**Rejected.** Directly violates criterion 5: it discards
`safe.bareRepository=explicit` and `credential.interactive=never`, changing
git's behavior under test in ways the suite does not model — a
`credential.interactive` change in particular could turn a hermetic test into
one that blocks on a credential prompt. It is also indiscriminate by
construction: it cannot distinguish the one malformed pair from the two
well-formed ones.

### R3 — Set `GIT_CONFIG_COUNT=0` for the suite

A cheaper spelling of R2. **Rejected** for the same reason, and it is *less*
honest: the `KEY_n`/`VALUE_n` variables remain set but inert, so a reader of
the environment cannot tell that the injections were disabled.

### R4 — Mutate global/system git config to compensate

**Rejected** outright. Violates criterion 3 and P-010 (Stage cannot authorize
work that mutates machine-global state to make a repository's tests pass).

### R5 — Skip, `expectedFailure`, or platform-gate the five victims

**Rejected.** Violates criterion 2. These five tests guard real invariants
(root-JSON allowlist, metrics artifacts never tracked, gitignore coverage,
zero-shipment topology). Suppressing them converts a fixable environment defect
into a permanent coverage hole, and would have hidden the `_run_git` masking
defect found above.

### R6 — Scrub the environment in `ci.yml` / a wrapper script

A CI/tooling configuration change. **Rejected on two independent grounds.**
First, it does not work: the destruction happens *mid-process*, when a
`patch.dict` block exits, so a pre-launch scrub cannot prevent it. Second, the
canonical local Windows invocation is not governed by `ci.yml`, so the fix
would not reach the surface that is actually red. It also fails criterion 4 —
a workflow file is not the narrowest authoritative boundary for an in-process
mutation.

### R7 — Fix only the production subprocess seams in `src/autoharness/`

Normalize the environment inside `_run_git` and the other 12 `subprocess.run`
sites under `src/`. **Rejected as the primary fix.** It changes shipped product
behavior to compensate for a test-environment defect, and it does not cover
victims #3/#4/#5, which invoke git directly from `tests/` and never enter
product code. (A narrow, separately-justified slice of this *is* retained — see
the accepted option's Layer 4, which improves diagnosis without changing the
gate's verdict semantics.)

### R8 — Process-wide bootstrap hook via a new `tests/__init__.py`

Install a normalizer once per test process. **Rejected.** `tests/` currently has
no `__init__.py` and no `conftest.py`; adding one changes `unittest discover`'s
top-level-directory resolution for the entire suite — a far larger blast radius
than the defect. It is also unnecessary: once restore-by-diff removes the
destruction at its source, no process-wide compensation is needed.

### R9 (ACCEPTED) — Restore-by-diff at the environment-mutation seam, with defense in depth

Fix the destruction where it happens, in `tests/`, and add layered protection
so it cannot silently return.

**Layer 1 — root fix.** A repository-contained helper under `tests/` provides a
`patched_environ(**overrides)` context manager that snapshots **only the keys it
touches** and restores by targeted set/delete. It never calls
`os.environ.clear()`, so no untouched variable is ever removed and re-added,
so `GIT_CONFIG_VALUE_2` is never destroyed. This is maximally narrow: it does
not read, interpret, or modify any `GIT_CONFIG_*` variable at all — it simply
stops corrupting them. Criterion 5 is satisfied perfectly rather than
approximately, because *no* injection is touched, legitimate or otherwise.

**Layer 2 — migration.** Every bulk `os.environ` mutation site under `tests/`
moves to the helper. Assertions are untouched.

**Layer 3 — regression guard.** An **AST-based** structural guard (per compound
learning `2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md`,
not a line regex) added to the existing
`tests/test_test_suite_isolation_contract.py`, forbidding bare
`patch.dict(os.environ, ...)` / `os.environ.clear()` under `tests/`, with a
pinned, asserted-empty allowlist and explicit non-vacuity positive and negative
cases — matching the established shape of the guard already in that module.

**Layer 4 — defense in depth at the subprocess boundary.** For git-invoking
seams, a deterministic self-consistency normalizer that drops only
`KEY_n`/`VALUE_n` pairs whose `VALUE_n` is genuinely absent from the real
process block, renumbers the survivors, and resets `GIT_CONFIG_COUNT` to the
surviving count. This preserves every well-formed injection, discards only a
pair that is already unusable, and is a **provable no-op** whenever the triple
is self-consistent — therefore a no-op on Linux and in CI by construction.

**Layer 5 — assertion integrity.** `_run_git`'s `check=False` -> `""` masking
and victim #4's `returncode == 0` -> "is not gitignored" mis-attribution are
made self-diagnosing, so an infrastructure failure can never again be reported
as a domain failure. **No assertion is weakened**; only the diagnosis on the
failure path is corrected.

Layer 1 alone is expected to turn the suite green. Layers 3–5 exist because a
green suite that can silently regress, or that lies about *why* it is red, is
the actual defect this whole chain has been chasing since `141-F`.

## Decision

**Adopt R9.** Layers 1–3 and 5 are `tests/`-surface work; Layer 4 spans the
`tests/` subprocess seams and the single `src/autoharness/gates/topology.py`
diagnostic seam, and is justified independently of the environment defect
because exit-status masking is a real product-diagnosis defect.

Work is decomposed into two features and two **ordered** shipments, keeping the
two recorded mechanisms strictly separate per the operator directive:

* `144-F` / `152-S` — mechanism A (ambient `GIT_CONFIG_*` destruction).
* `145-F` / `153-S` — mechanism B (`BranchOwnershipTests` intra-file order),
  blocked by `152-S`, opening with a re-measurement task whose terminal
  disposition is `SUBSUMED` or `SURVIVES`.

## Consequences

* Canonical Windows local gate expected green; Linux/CI provably unchanged.
* Zero assertions weakened; five real invariants stay enforced.
* No global, system, or ambient-shell configuration is mutated.
* All well-formed ambient git config injections keep working under test.
* A new AST guard prevents silent reintroduction of the destructive pattern.
* Residual risk: the Win32 empty-value-deletion behavior is asserted from
  documented behavior plus the captured failure signature, not yet from a
  local experiment. `144.001-T` is a **test-first reproduction** task that must
  demonstrate the mechanism RED before any fix lands; if that reproduction
  fails, the plan's Step 1 halt condition fires and the design is revisited
  rather than proceeding on an unconfirmed hypothesis.

## Prior Learnings Applied

| Learning | Application |
| --- | --- |
| `2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md` | Layer 3 guard is AST-based, recursive over `tests/`, with a pinned allowlist and non-vacuity cases. |
| `2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md` | Identified `_run_git`'s `check=False` -> `""` as the same exit-status-masking anti-pattern; drove Layer 5. |
| `141-F` / `143-F` chain history | Diagnosis-before-fix discipline retained: `144.001-T` reproduces RED first; `145.001-T` re-measures before remediating. |
