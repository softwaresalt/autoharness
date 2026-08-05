---
title: Pipeline-Topology Gate — CI Rollout (Advisory → Required)
description: Staged advisory-to-required rollout plan for the pipeline-topology CI backstop (Gate C), the local-hook-vs-CI responsibility split, and the operator toggle contract
doc_type: reference
source: docs/pipeline-topology-gate-ci-rollout.md
---

> **Navigation**: [README](../README.md) · [Pipeline-Topology Gate Reference](pipeline-topology-gate.md) · [Validation Gates Reference](gates-reference.md)

> **Status**: authored by `109.012-T` (Shipment C / `116-S`, gate C of the staged
> A→B→C `autoharness gate pipeline-topology` rollout). See
> [Pipeline-Topology Gate Reference](pipeline-topology-gate.md#ci-topology-check-entrypoint-gate-c)
> for the entrypoint script and workflow job this rollout doc governs.

## Overview

`012-DL` resolved rollout as **staged advisory → required**: local pre-commit /
pre-push hooks ship opt-in and default to advisory-warn, and the CI backstop
(Gate C, this doc) likewise ships **advisory by default** and is promoted to
**required** by an explicit operator action — never a workflow re-render. This
document is the operator-facing rollout narrative: what advisory and required
mean concretely, why CI (not local hooks) is the authoritative backstop, how to
flip the toggle, and what to verify before doing so.

## Applicability: Backlogit-Only

This entire rollout — advisory, bake-in, and required — applies **only** to
workspaces whose backlog tool is `backlogit`. `install-harness` installs the
`topology-check` job (and its `scripts/ci-topology-check.sh` entrypoint) only
when `{{FEATURE_SHIPMENTS}}` is `true`; for backlog-md, manual, or any other
non-shipment-capable install, the job and entrypoint are omitted entirely, not
rendered advisory-only. This is because the gate's backlog reader
(`FilesystemTopologyReaders`) currently reads only `.backlogit/`: installing
the job unconditionally for those workspaces would leave it permanently
reporting `BACKLOG_UNAVAILABLE`, which becomes a hard, unrecoverable BLOCK the
moment `PIPELINE_TOPOLOGY_GATE_REQUIRED` is promoted to required. Omission is
a single atomic composition step: `install-harness` must also strip
`topology-check` from `ci-gate`'s `needs:` array and its
`needs['topology-check'].result` reference from the result-aggregation line —
otherwise the rendered workflow references an undefined job, which is invalid
GitHub Actions YAML and breaks `ci-gate` (all of CI), not merely the absent
backstop. If this product later generalizes the topology reader to other
backlog registries, this applicability note and the install-time gating in
`.github/skills/install-harness/SKILL.md` must be revisited together.

## Why a Remote CI Backstop Is Necessary (Not Just Local Hooks)

Local hooks (`pre-commit-pipeline-topology.*`, `pre-push-quality-gates.*`) give
fast, in-loop feedback, but they have two structural gaps that make them
insufficient as the sole enforcement point for the P-001 (at-most-one-active-
shipment) and P-016 (single implementation worktree/branch) invariants:

1. **Local hooks are always bypassable.** `git commit`/`git push --no-verify`
   skips the hook entirely. A skipped hook runs no code and emits no telemetry —
   there is no local observer at skip time, so a `--no-verify` bypass is
   **inherently unobservable** to local audit tooling. This is different from
   an audited `autoharness gate pipeline-topology --force` invocation, which
   *does* run the gate and *does* write to the force-audit log — the two are
   not equivalent bypasses (see
   [Pipeline-Topology Gate Reference § Bypass / Audit](pipeline-topology-gate.md#bypass--audit)).
2. **Git has no pre-worktree-add hook at all.** There is no local git hook that
   can intercept `git worktree add`, so the P-016 single-worktree invariant has
   no local enforcement point for that specific operation.

CI is therefore the **only** re-validation point that is not subject to either
gap: a CI run is triggered by the platform, not by the developer's local git
invocation, so it cannot be skipped with `--no-verify`, and it re-reads
backlogit state from the **synced** repository — the same state a second
checkout would eventually converge on. This is a **detect-at-sync** backstop,
not a lock: it catches topology divergence when checkouts converge in CI (push
or PR), but it does not serialize concurrent claims or prevent a race in real
time. See
[Cross-Machine Scope Limitation](pipeline-topology-gate.md#cross-machine-scope-limitation)
for the precise boundary of what detection does and does not guarantee.

## Local-Hook vs CI Responsibility Split

| Concern | Local hooks (pre-commit / pre-push) | CI `topology-check` job (this doc) |
|---|---|---|
| **Invocation** | `--phase ambient`, `--mode manual` | `--phase ambient`, `--mode ci` |
| **Scope target** | Non-shipment-scoped (ambient resolution) | Non-shipment-scoped (ambient resolution) |
| **Default posture** | Advisory (warn, never blocks commit/push) | Advisory (`continue-on-error: true`) until promoted |
| **Bypassable?** | Yes — `git ... --no-verify` skips it entirely, unobservably | No — CI cannot be skipped by the developer; it always runs and reports a result |
| **Worktree check (P-016)** | Machine-local `git worktree list` at commit/push time | Not meaningful on an ephemeral CI runner (single checkout); the entrypoint does not depend on runner worktree count |
| **Speed / feedback loop** | Fast, in-loop, pre-push | Slower (full CI run), but authoritative |
| **Purpose** | Fast feedback for a developer working normally in a synced checkout | Server-side, non-bypassable backstop once a checkout syncs |
| **Failure on missing `autoharness` binary** | Warn-and-skip (advisory-degrade; a developer machine may legitimately lack the CLI) | **Fail-closed** — a missing binary is a CI configuration failure (exit 1), never an advisory skip |

Both layers invoke the **same gate core** (`autoharness gate pipeline-topology
--phase ambient`) and the **same non-shipment-scoped target resolution** — there
is no divergent logic between "local" and "CI" invariant checking, only a
difference in bypassability and default blocking posture.

## The Operator Toggle: `PIPELINE_TOPOLOGY_GATE_REQUIRED`

The required-vs-advisory decision for the CI `topology-check` job is an
explicit **repository variable**, not a template variable resolved at install
time:

```yaml
topology-check:
  name: pipeline-topology (ambient)
  continue-on-error: ${{ vars.PIPELINE_TOPOLOGY_GATE_REQUIRED != 'true' }}
```

* **Unset (default) → advisory.** `continue-on-error` evaluates to `true`, so a
  BLOCK verdict from the gate is still recorded on the job (visible in the run
  log and the job's own status), but the job's **result reported to
  dependents** — including the `ci-gate` aggregation job — is `success`
  regardless. Ordinary CI stays green during the bake-in period even if the
  gate detects a topology violation.
* **Set to `'true'` → required.** `continue-on-error` evaluates to `false`, so
  a BLOCK verdict fails the `topology-check` job for real, which in turn fails
  `ci-gate` (the aggregation job that branch protection should require), which
  blocks the PR from merging.

Flipping the toggle is a **GitHub repository (or organization) variable
change** — `Settings → Secrets and variables → Actions → Variables` — made by
an operator with repository admin rights. **No workflow file edit and no
`install-harness` re-render is required** to promote advisory → required, or
to revert required → advisory if a false positive is discovered.

## Staged Rollout Plan

Per `012-DL`'s chosen rollout order — (A) deterministic gate core, (B)
hooks/install adapters, (C) remote CI validation, all now shipped — the
**operator-facing** staging for the CI backstop specifically is:

1. **Ship advisory (default).** `PIPELINE_TOPOLOGY_GATE_REQUIRED` is unset.
   The `topology-check` job runs on every push/PR, reports its verdict in the
   run log, but never blocks a merge. This is the state this shipment (`116-S`)
   leaves the repository in.
2. **Bake-in period.** Observe the job's advisory verdicts across normal PR/push
   traffic. A healthy bake-in means the job consistently reports PASS for
   ordinary, single-active-shipment work, and only reports BLOCK when a real
   topology anomaly exists (e.g., two active shipments merged from divergent
   checkouts, a stray worktree artifact). There is no fixed time-box in this
   doc; the operator judges bake-in sufficiency from observed signal quality,
   not a calendar date.
3. **Promote to required.** Set `PIPELINE_TOPOLOGY_GATE_REQUIRED=true` as a
   repository variable. From this point, a BLOCK verdict fails `ci-gate` and
   blocks merge until the underlying topology issue (extra active shipment,
   worktree, or branch-ownership mismatch) is remediated per
   [Pipeline-Topology Gate Reference § Failure Recovery](pipeline-topology-gate.md).
4. **Revert if needed.** If required mode produces a false-positive block
   (e.g., a legitimate exceptional condition the gate does not yet model),
   the operator may revert the variable to unset/`false` to return to
   advisory while the underlying gate logic is corrected — this is the same
   single-variable change as promotion, in reverse, and requires no code or
   workflow change.

## What to Verify Before Promoting to Required

Before setting `PIPELINE_TOPOLOGY_GATE_REQUIRED=true`, an operator should
confirm:

* The `topology-check` job has been running (advisory) for a representative
  sample of normal PR/push traffic, and its PASS/BLOCK verdicts match observed
  reality (no unexplained BLOCKs on known-clean topology).
* Any known BLOCK verdicts during the advisory period have a clear, already-
  remediated root cause (not an open gate defect).
* The repository's branch protection rule requires the `ci-gate` check (the
  aggregation job name), not the `topology-check` job directly — this is
  already the general convention for this CI shape (see
  [`templates/ci/README.md`](../templates/ci/README.md)) and does not change
  when the toggle is promoted.

## CI-Path Test Coverage

CI-path behavior for the entrypoint and workflow wiring is covered by:

* `tests/test_ci_topology_check_entrypoint.py` — structural assertions on
  `templates/ci/ci-topology-check.sh.tmpl` (fail-closed missing-binary
  handling, raw exit-code propagation, no advisory-degrade toggle in the
  script itself) plus behavioral subprocess tests (skipped on `win32`, since
  bash on Windows in this environment is WSL) that exercise PASS (exit 0),
  BLOCK (exit 1), and missing-`autoharness`-binary (exit 1) outcomes.
* `tests/test_ci_template_rendering.py::TopologyCheckJobTests` — structural
  assertions on `templates/ci/ci.yml.tmpl`'s `topology-check` job across all
  three rendered test profiles actually defined in that test module
  (`rust`, `typescript`, `python` — see `tests/test_ci_template_rendering.py`
  lines 34-85): job presence, always-runs (not gated on `changes`), the
  toggle being a repository variable (`vars.PIPELINE_TOPOLOGY_GATE_REQUIRED`)
  rather than a `{{TEMPLATE_VAR}}`, advisory-by-default via
  `continue-on-error`, correct entrypoint invocation, `autoharness` install
  command resolution per profile, and `ci-gate` aggregation inclusion
  (`needs['topology-check'].result`, bracket notation for the hyphenated job
  ID).
* Both advisory mode (default, `continue-on-error: true`) and required mode
  (`vars.PIPELINE_TOPOLOGY_GATE_REQUIRED == 'true'`, `continue-on-error:
  false`) are exercised behaviorally by
  `test_continue_on_error_expression_evaluates_both_toggle_states`, which
  extracts the rendered `continue-on-error` expression and evaluates it
  against unset, `'false'`, and `'true'` values for the repository variable —
  asserting the actual advisory/required outcome each value produces, not
  merely the exact expression string.

## References

* [Pipeline-Topology Gate Reference § CI Topology-Check Entrypoint (Gate C)](pipeline-topology-gate.md#ci-topology-check-entrypoint-gate-c)
* [Pipeline-Topology Gate Reference § Cross-Machine Scope Limitation](pipeline-topology-gate.md#cross-machine-scope-limitation)
* [Pipeline-Topology Gate Reference § Bypass / Audit](pipeline-topology-gate.md#bypass--audit)
* `templates/ci/ci-topology-check.sh.tmpl` — the CI entrypoint (109.011-T / Gate C)
* `templates/ci/ci.yml.tmpl` — the `topology-check` job + toggle (109.014-T / Gate C)
* `templates/ci/README.md` — the four-job CI shape and variable reference table
* `tests/test_ci_topology_check_entrypoint.py`, `tests/test_ci_template_rendering.py::TopologyCheckJobTests` — CI-path test coverage (109.012-T / Gate C)
* `012-DL` — the deliberation resolving the staged advisory→required rollout order and the five hard questions (authority boundary, race behavior, manual-developer compatibility, bypass auditing, failure recovery)
