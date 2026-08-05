---
title: Pipeline-Topology Gate Reference
description: The deterministic autoharness gate pipeline-topology CLI — shipment-active invariants, branch/worktree ownership, the pre_claim/post_claim/lifecycle/ambient phase contract, exit codes (including the read-only CLAIM_NOT_OBSERVED retry-required outcome), opt-in hook install/activation, the audited --force override, and cross-machine scope limits
doc_type: reference
source: docs/pipeline-topology-gate.md
---

> **Navigation**: [README](../README.md) · [Validation Gates Reference](gates-reference.md) · [Copilot-Review Merge Gate Reference](copilot-review-gate.md) · [Primitives](primitives.md) · [Tuning Guide](tuning-guide.md)

## Overview

The **pipeline-topology gate** is a deterministic, non-LLM, read-only, exit-code-based
check that guards the P-001 (at-most-one-active-shipment) and P-016 (single
implementation worktree/branch) topology invariants at every point in the Stage →
Ship shipment lifecycle: before a shipment/task is claimed, immediately after a
claim, across build/PR/closure, and — non-shipment-scoped — as an ambient
advisory check from local git hooks and CI.

Like the [copilot-review merge gate](copilot-review-gate.md), this gate is
**fail-closed** for its scoped phases: when the active-shipment invariant, branch
ownership, worktree uniqueness, or shipment readiness checks fail, the gate
**BLOCKS** (exit 1). Unlike copilot-review, it also has a distinct **read-only
retry-required** outcome (exit 3, `CLAIM_NOT_OBSERVED`) for the one case where a
single stateless read cannot distinguish a merely-delayed claim from a genuinely
failed one — see [The `CLAIM_NOT_OBSERVED` Retry-Required Contract](#the-claim_not_observed-retry-required-contract).

The gate's active-shipment scan and worktree-uniqueness check are **local to the
current checkout** — see [Cross-Machine Scope Limitation](#cross-machine-scope-limitation).

## The `autoharness gate pipeline-topology` CLI Contract

```bash
autoharness gate pipeline-topology [--mode agent|manual|ci]
                        [--shipment <shipment_id>]
                        [--phase pre_claim|post_claim|lifecycle|ambient]
                        [--json] [--force]
```

| Flag | Default | Description |
|---|---|---|
| `--mode <m>` | `manual` | `agent` \| `manual` \| `ci` — see [Modes](#modes). |
| `--shipment <id>` | — | Explicit shipment target. **Required** in `agent` mode, and required in **any** mode whenever `--phase` resolves to `pre_claim`, `post_claim`, or `lifecycle` (only `ambient` is meaningful without one). |
| `--phase <p>` | `ambient` (manual/ci); none (agent) | `pre_claim` \| `post_claim` \| `lifecycle` \| `ambient`. **Required** in `agent` mode. |
| `--json` | off | Emit the topology gate result as a machine-readable JSON object. |
| `--force` | off | Operator-only audited override of a BLOCK (exit 1) verdict. Does **not** affect a `CLAIM_NOT_OBSERVED` (exit 3) retry-required result — there is nothing to override; the caller must retry the claim, not bypass the read. |

All reads are performed through injected, read-only reader interfaces
(`FilesystemTopologyReaders` in production); the gate never mutates backlog state,
git state, or any other artifact.

### The `--shipment <SHIPMENT_ID>` Target Contract

* **Agent shipment-scoped modes** (`--mode agent`, or any mode with
  `--phase pre_claim|post_claim|lifecycle`): `--shipment` is **REQUIRED**.
  Omitting it is fail-closed — exit **2** (invalid arguments), never inferred.
* **Non-shipment hook/CI contexts** (`--mode manual|ci` with `--phase ambient`,
  the default when `--phase` is omitted in those modes): the target is resolved
  **deterministically and implicitly**:
  1. If exactly one shipment is currently active, that shipment is the target.
  2. Otherwise, the target is resolved from the current branch slug
     (`feat/{slug}` / `chore/{slug}` matched against known shipment branch
     aliases).
  3. If neither resolves, there is **no target** — this is not an error; the
     gate proceeds in **ambient-only, existence-guarded** mode (see the phase
     table below).

### The `--phase <pre_claim|post_claim|lifecycle|ambient>` Contract

* **Agent shipment-scoped mode** (`--mode agent`): `--phase` is **REQUIRED** and
  fail-closed (exit **2** if missing). It **MUST** be one of the shipment-scoped
  values `pre_claim | post_claim | lifecycle`. The non-scoped `ambient` value is
  explicitly **rejected as invalid** in agent mode ("agent mode requires
  `--phase pre_claim|post_claim|lifecycle`") — ambient is never inferred for an
  agent-mode invocation.
* **Non-shipment hook/CI contexts** (`--mode manual|ci`): `--phase` **defaults to
  `ambient`** when omitted — **not** `lifecycle`. `ambient` is deliberately
  distinct from `lifecycle` at the zero-active row: `ambient` **PASSES**
  (non-blocking) with zero active shipments; `lifecycle` **BLOCKS**
  (`LIFECYCLE_NO_ACTIVE_SHIPMENT`) with zero active shipments. Never conflate
  the two.

#### Phase semantics matrix

| Phase | Zero active shipments | Exactly one active, matches target | Exactly one active, does **not** match target (or no target) | Two or more active |
|---|---|---|---|---|
| `pre_claim` | **PASS** — required precondition before a claim | n/a (a claim has not yet happened) | `PRECLAIM_ACTIVE_SHIPMENT_PRESENT` — **BLOCK** | `PRECLAIM_ACTIVE_SHIPMENT_PRESENT` — **BLOCK** |
| `post_claim` | `LIFECYCLE_NO_ACTIVE_SHIPMENT` — **BLOCK** | **PASS** | `LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH` — **BLOCK** | `LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS` — **BLOCK** |
| `lifecycle` | `LIFECYCLE_NO_ACTIVE_SHIPMENT` — **BLOCK** | **PASS** | `LIFECYCLE_ACTIVE_SHIPMENT_MISMATCH` — **BLOCK** | `LIFECYCLE_MULTIPLE_ACTIVE_SHIPMENTS` — **BLOCK** |
| `ambient` | **PASS** — existence-guarded, non-blocking (no claim to validate) | **PASS** | `AMBIENT_TARGET_REQUIRED_FOR_ACTIVE_SHIPMENT` (no resolvable target) or `AMBIENT_ACTIVE_SHIPMENT_MISMATCH` — **BLOCK** | `AMBIENT_MULTIPLE_ACTIVE_SHIPMENTS` — **BLOCK** |

`post_claim` additionally runs the [`CLAIM_NOT_OBSERVED` retry-required
contract](#the-claim_not_observed-retry-required-contract) instead of an
immediate block when the target is still `queued` with zero active shipments —
see below.

`ambient` also validates branch ownership, worktree uniqueness, and the
detect-before consistency scan whenever a target *does* resolve; it is only
the **zero-active / no-target** case that is non-blocking. A mismatched single
active shipment, or two or more active shipments, still **blocks fail-closed**
regardless of the hook's advisory toggle (the hook may choose not to fail the
git operation, but the gate itself still reports BLOCK).

#### Which lifecycle point passes which phase

| Lifecycle point | Phase |
|---|---|
| Ship: branch/worktree creation (P-011) | `pre_claim` — branch/worktree creation always **precedes** the claim and is **never** `post_claim` |
| Ship: the immediately-before-claim check | `pre_claim` |
| Ship: the immediate post-claim verification | `post_claim` |
| Ship: build / PR lifecycle / closure | `post_claim` or `lifecycle` |
| Orchestrator: route-to-Ship eligibility + cursor-advance | `pre_claim`, against the candidate/successor shipment ID |
| Local git hooks (`pre-commit`, `pre-push`) | `ambient` (non-shipment-scoped, no `--shipment`) |
| CI ambient runs | `ambient` (non-shipment-scoped, no `--shipment`) |

### Modes

| Mode | Behavior |
|---|---|
| `agent` | Fail-closed shipment-scoped invocation. Requires both `--shipment` and an explicit scoped `--phase`. Used by Ship and Orchestrator at claim/route/build/PR/closure points. |
| `manual` (default) | Human-invoked (or hook-invoked) check. `--phase` defaults to `ambient`; `--shipment` is optional unless a scoped `--phase` is explicitly passed. |
| `ci` | Same resolution rules as `manual`, used from CI ambient runs. **Detached-HEAD branch fallback**: when the checkout is on a detached HEAD (`git branch --show-current` reports empty — the state `actions/checkout` and equivalent CI checkout actions always leave a runner in, for both `push`- and `pull_request`-triggered runs), `--mode ci` resolves the real branch name from CI-platform environment variables before falling back to the fail-closed `BRANCH_MISMATCH: detached HEAD` outcome: `GITHUB_HEAD_REF` first (set only for `pull_request` events — the PR's actual source branch, always a trustworthy short branch name), then `GITHUB_REF_NAME` **only when** `GITHUB_REF_TYPE == "branch"` (set for `push` events to the pushed branch name — disambiguated from a tag push, where `GITHUB_REF_TYPE == "tag"` and `GITHUB_REF_NAME` is a version string, not a branch; this is why the check is `GITHUB_REF_TYPE`-based rather than a naive "does the name contain a slash" heuristic, which would incorrectly reject a legitimate slash-containing push-triggered branch name such as this repo's own `feat/…`/`chore/…` convention). This fallback is strictly gated on `mode == "ci"` — `agent`/`manual` mode detached-HEAD checkouts are unaffected and keep failing closed exactly as before, even if a `GITHUB_HEAD_REF`-shaped variable happens to be present in the environment. Without this fallback, the CI topology-check entrypoint (Gate C) would report `BRANCH_MISMATCH` on every single CI run, since every CI checkout is detached by default. |

### Exit Codes

| Code | Meaning |
|---|---|
| `0` | PASS — all checks passed for the resolved phase/target, or an audited `--force` override of a BLOCK. |
| `1` | BLOCK — the active-shipment invariant, branch ownership, worktree uniqueness, or shipment readiness check failed for the resolved phase/target. |
| `2` | Invalid arguments or invalid gate configuration: unknown mode/flag, missing `--phase` value, missing `--shipment` when a scoped phase or agent mode requires it, `ambient` passed in agent mode, or an unresolvable explicit `--shipment` target. |
| `3` | `CLAIM_NOT_OBSERVED` — read-only retry-required outcome. Only reachable at `--phase post_claim` when the target shipment is still `queued` with zero active shipments after a claim was attempted. See below. |

## The `CLAIM_NOT_OBSERVED` Retry-Required Contract

A single stateless read of backlog state **cannot distinguish** "the claim is
merely delayed" from "the claim genuinely failed" — both look identical: the
target shipment is `queued` and zero shipments are active. The gate therefore:

* performs **exactly one** read at `post_claim` (no internal double-read, no
  internal retry — a second read with no intervening claim/mutation could never
  observe a different state anyway, and pretending otherwise was the illusory
  self-retry this contract replaces);
* returns `CLAIM_NOT_OBSERVED` (exit 3, `status: "retry_required"`) rather than
  guessing PASS or BLOCK;
* leaves convergence entirely to an **external actor**: the Ship agent's bounded,
  double-claim-guarded reclaim-and-reverify sequence performs one additional
  claim attempt and one additional `post_claim` re-verification. If the second
  `post_claim` read still reports `CLAIM_NOT_OBSERVED` (or any other non-pass
  outcome), Ship terminally reports `CLAIM_VERIFY_FAILED` — it does not loop
  further.

`CLAIM_NOT_OBSERVED` is a **first-class token**, not a variant of BLOCK: `--force`
does not act on it (there is no blocking verdict to override), and CLI telemetry
classifies it as `outcome: "failed"` (a non-zero, non-forced result) rather than
silently defaulting to `success` or misreporting it as `blocked`.

## Where the Harness Invokes the Gate

* **Ship** (`_ship` agent): `pre_claim` before branch/worktree creation (P-011)
  and again immediately before the claim; `post_claim` immediately after the
  claim, running the bounded `CLAIM_NOT_OBSERVED` reclaim-and-reverify sequence
  above; `post_claim`/`lifecycle` across build, PR lifecycle, and closure.
* **Orchestrator** (`_orchestrator` agent): `pre_claim` at the route-to-Ship
  eligibility check and at cursor-advance, against the candidate/successor
  shipment ID.
* **Local git hooks**: `templates/scripts/pre-push-quality-gates.{sh,ps1}.tmpl`
  and `templates/scripts/pre-commit-pipeline-topology.{sh,ps1}.tmpl` invoke
  `--mode manual --phase ambient` with **no** `--shipment` — the non-shipment-
  scoped, deterministic ambient contract described above.
* **CI**: `templates/ci/ci-topology-check.sh.tmpl` (109.011-T) is the fail-closed
  CI entrypoint wrapping this same `ambient` invocation as an independent
  backstop for the (skippable, `--no-verify`) local hooks; see
  [CI Topology-Check Entrypoint (Gate C)](#ci-topology-check-entrypoint-gate-c)
  below.

## Opt-In Install / Activation

The pipeline-topology gate ships as part of the `autoharness` CLI itself (always
present — it is not a capability pack). Its **hook** artifacts, however, are
opt-in, mirroring the existing markdownlint and pre-push quality-gate hooks:

1. **install-harness** copies the rendered hook scripts into
   `{workspace}/scripts/`:
   * `pre-push-quality-gates.sh` / `.ps1` (now also invoking the ambient
     topology check — see [B1](../templates/scripts/pre-push-quality-gates.sh.tmpl))
   * `pre-commit-pipeline-topology.sh` / `.ps1` (new — see
     [B2](../templates/scripts/pre-commit-pipeline-topology.sh.tmpl))
2. **Activation into `.git/hooks/` (or a custom `core.hooksPath`) is a separate,
   manual, explicit operator step.** The harness **never** silently overwrites an
   existing `.git/hooks/pre-commit` or `.git/hooks/pre-push`, and never sets
   `core.hooksPath` automatically. See each template's own header-comment install
   instructions, including how to chain with an existing markdownlint pre-commit
   hook rather than overwrite it.
3. **tune-harness** recognizes both hook families as tracked artifacts and flags
   drift (missing file, regressed contract, or a hook hardened to fail-by-default)
   as P1 Degrading — see the "Pipeline-topology hook drift" check.
4. **verify-workspace** (`autoharness verify-workspace`) asserts the install/tune
   wiring itself is present and coherent via the
   `pipeline_topology_gate_install_wiring` and `pipeline_topology_gate_tune_wiring`
   `FOUNDATION_ASSERTIONS` entries.

## Bypass / Audit

`--force` is an **operator-only** control that converts a BLOCK (exit 1) verdict
into an exit-0 pass. It must never be invoked from an agent surface. Every use is
appended to a gitignored, append-only audit log:

```text
.autoharness/gates/pipeline-topology-force-audit.log
```

Each line is a JSON object recording the timestamp, actor (`$USERNAME`/`$USER`),
mode, phase, resolved target shipment, the overridden token, and the message —
consistent with the P-005 telemetry audit style used by the
[copilot-review force override](copilot-review-gate.md#audited---force-override).

## Manual-Developer Compatibility (Advisory-Degrade Mode)

The **hook** invocations (`pre-push-quality-gates.*`, `pre-commit-pipeline-topology.*`)
are **advisory-first by default**: a BLOCK result from the gate prints a warning
but does **not** fail the git operation unless the developer has explicitly opted
into blocking mode by setting `AUTOHARNESS_TOPOLOGY_GATE_BLOCKING=true` in their
environment. This keeps the local developer experience non-disruptive during
staged rollout while CI (and Ship's own `agent`-mode, fail-closed invocations at
claim/build/PR/closure points) remain the actual enforcement backstop. Absent the
`autoharness` binary entirely, both hooks warn and skip — never a hard failure.
Both hooks are a single deterministic pass with no retry loop (circuit-breaker
compatible), and both honor the standard `--no-verify` bypass.

## CI Topology-Check Entrypoint (Gate C)

Gate C (`116-S`, this shipment) completes the staged A→B→C rollout by adding the
server-side, **non-bypassable** CI backstop: local hooks are always skippable via
`git ... --no-verify`, and Git has no pre-worktree-add hook at all, so CI is the
authoritative re-validation point for the P-001/P-016 invariants once a checkout
syncs.

* **Entrypoint** (109.011-T): `templates/ci/ci-topology-check.sh.tmpl` resolves to
  `{workspace}/scripts/ci-topology-check.sh`. It invokes
  `autoharness gate pipeline-topology --mode ci --phase ambient --json` — the
  exact same non-shipment-scoped, deterministic target resolution as the local
  ambient hooks (no human-supplied `--shipment`) — and propagates the gate's raw
  exit code **unmodified**. Unlike the local hooks, this entrypoint carries **no**
  advisory-degrade toggle: a missing `autoharness` binary is a CI configuration
  failure (exit 1), not a warn-and-skip.
* **Workflow wiring** (109.014-T): `templates/ci/ci.yml.tmpl` adds an
  always-running `topology-check` job that checks out the repo, installs the
  `autoharness` package, and runs the entrypoint script. The
  **required-vs-advisory** decision is an explicit **operator toggle** applied at
  the job level via `continue-on-error: ${{ vars.PIPELINE_TOPOLOGY_GATE_REQUIRED
  != 'true' }}` — default unset means advisory (non-blocking; the job's result is
  still reported to dependents as `success` even if the gate itself reported
  BLOCK), and setting the `PIPELINE_TOPOLOGY_GATE_REQUIRED` repository variable to
  `'true'` flips it to required (blocking) with **no workflow re-render needed**.
* **Rollout staging** (109.012-T): see
  [`docs/pipeline-topology-gate-ci-rollout.md`](pipeline-topology-gate-ci-rollout.md)
  for the advisory→required staged rollout narrative, the local-hook-vs-CI
  responsibility split, and CI-path test coverage.

## Cross-Machine Scope Limitation

The gate's active-shipment scan and its worktree-uniqueness check are **local to
the current checkout**. backlogit provides no workspace-wide claim lock, so:

* the **active-shipment invariant** is **detection-only** — it is not serialized
  or leased at any scope (repo, machine, or cluster). Concurrent work claimed
  from a different checkout can still race this gate; the gate detects topology
  drift after the fact, it does not prevent it.
* **worktree uniqueness** (P-016) is evaluated against `git worktree list` on the
  **current machine/checkout only**. A second, independent clone on another
  machine is invisible to this check.

Treat the gate as a deterministic **guardrail**, not a distributed lock.

## Runtime Artifacts

`autoharness gate pipeline-topology` writes only its audit log and (when telemetry
is enabled) a structured tool-event journal entry, under the same gitignored
runtime directory used by the other gates:

* `.autoharness/gates/pipeline-topology-force-audit.log` — append-only `--force`
  override audit.

Running the gate never dirties tracked working-tree state.

## References

* [Validation Gates Reference](gates-reference.md) — the separate, advisory-by-default `autoharness gate check` CLI
* [Copilot-Review Merge Gate Reference](copilot-review-gate.md) — the sibling fail-closed pre-merge gate and its `--force` audit pattern
* [`docs/compound/010-S-session-lifecycle-gates.md`](compound/010-S-session-lifecycle-gates.md) — the install/tune assertion-registration pattern this gate's install wiring follows
* [`docs/plans/2026-08-05-114s-closure-preactivation-fixes-plan.md`](plans/2026-08-05-114s-closure-preactivation-fixes-plan.md) — design rationale for the `CLAIM_NOT_OBSERVED` contract and the closure-status enforcement fix
* [`_ship` agent definition](../.github/agents/_ship.agent.md)
* [`_orchestrator` agent definition](../.github/agents/_orchestrator.agent.md)
* `templates/scripts/pre-push-quality-gates.sh.tmpl` / `.ps1.tmpl`
* `templates/scripts/pre-commit-pipeline-topology.sh.tmpl` / `.ps1.tmpl`
* `templates/ci/ci-topology-check.sh.tmpl` — the CI entrypoint (Gate C)
* [`docs/pipeline-topology-gate-ci-rollout.md`](pipeline-topology-gate-ci-rollout.md) — the advisory→required staged rollout doc (Gate C)
