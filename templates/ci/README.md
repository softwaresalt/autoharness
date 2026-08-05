---
title: CI Workflow Template
description: "Language-agnostic GitHub Actions CI template implementing the unified CI + local-gating primitive: a fail-closed change-detection job, a guarded expensive gate, and an always-running aggregation gate that is the single required status check."
doc_type: reference
---

# CI Workflow Template

`ci.yml.tmpl` is the language-agnostic remote-CI half of the unified CI +
local-gating harness primitive (the local half is
`../scripts/pre-push-quality-gates.*.tmpl`). It renders to
`.github/workflows/ci.yml` in the target workspace.

## Four-job shape

Each variable below is the human-facing **check context** (`name:`), which may
contain spaces or slashes. The underlying GitHub Actions **job IDs are fixed,
valid slugs** — `changes`, `expensive`, `topology-check`, and `ci-gate` —
because job IDs may not contain spaces. Branch rulesets match on the check
context (`name:`), not the job ID.

| Job (`name:`) | Job ID | Runs | Purpose |
|---|---|---|---|
| `detect code changes` | `changes` | always | Fail-closed `dorny/paths-filter` (`predicate-quantifier: every`) over a denylist. Outputs `code` = `true` unless the change touches only docs/backlog paths. |
| `{{CI_EXPENSIVE_JOB_NAME}}` | `expensive` | when `code == 'true'` (path impact only) | The expensive lint/format/typecheck/test/build gate. Never the required check. |
| `pipeline-topology (ambient)` | `topology-check` | always | The CI topology-check backstop (Gate C, P-001/P-016) — see [Pipeline-Topology CI Backstop](#pipeline-topology-ci-backstop-gate-c) below. Required-vs-advisory via a repository variable, not a path condition. |
| `{{CI_REQUIRED_CHECK_NAME}}` | `ci-gate` | always (`if: always()`) | Aggregation gate. **This is the only check a branch ruleset should require.** Treats a skipped expensive job as OK; fails only when a needed job is `failure`/`cancelled` (or, once `topology-check` is flipped to required, when it fails for real). |

### Why the aggregation gate is the required check

A required status check that names a skippable job blocks docs-only PRs forever:
GitHub reports the skipped job as not-successful. The always-running aggregation
gate avoids this — the expensive job may be legitimately skipped while the
required check still reports success.

### Why fail-closed path filtering

Under `dorny/paths-filter`'s default `some` quantifier, a leading `'**'` marks
every file matched and the `'!'` negations never apply — the security-sensitive
gate silently skips on new file types (fail-open). `predicate-quantifier: every`
requires all patterns to match per file, so the negations exclude docs/backlog and
any code/config/unknown-type change falls through into the gate (fail-closed).

## Variables

| Variable | Resolved from | Notes |
|---|---|---|
| `{{CI_REQUIRED_CHECK_NAME}}` | `ci.required_check_name` (default `ci gate`) | The aggregation gate's check context (`name:`). May contain spaces/slashes. Set to an already-required ruleset check name (e.g. `build`) so no ruleset edit is needed. The job ID is always the fixed slug `ci-gate`. |
| `{{CI_EXPENSIVE_JOB_NAME}}` | synthesized from the primary ecosystem (e.g. `test`, `build`) | The expensive job's check context (`name:`). Should differ from the required-check name. The job ID is always the fixed slug `expensive`. |
| `{{CI_RUNNER_OS}}` | `ubuntu-latest` (regular CI is Linux-only per `ci.linux_only`) | Regular CI is Linux-only; cross-OS verification stays in release-tag workflows. This template does not auto-generate a multi-OS matrix. |
| `{{CI_DOCS_ONLY_PATHS}}` | `ci.docs_only_paths` | Rendered as indented denylist negations, e.g. `- '!docs/**'` / `- '!.backlogit/**'`. Prefer positively-identified docs/state **directories**. Avoid an extension-wide glob like `- '!**/*.md'` when Markdown is executable product (agent/skill/instruction files), or those changes skip the gate while the aggregation check still passes. |
| `{{CI_SETUP_STEPS}}` | per-ecosystem toolchain setup | Checkout + SDK setup + dependency install steps for the expensive job. |
| `{{LINT_COMMAND}}` | `lint.command` | Omit the step when no lint gate is discovered. |
| `{{FORMAT_CHECK_COMMAND}}` | `format.check_command` | Omit the step when no format gate is discovered. |
| `{{TYPECHECK_COMMAND}}` | `typecheck.command` | Omit the step when no typecheck gate is discovered. |
| `{{TEST_COMMAND}}` | `test.command` | The primary gate. |
| `{{BUILD_CHECK_COMMAND}}` | `build.check_command` | Omit the step when no build-check gate is discovered. |
| `{{CI_AUTOHARNESS_INSTALL_COMMAND}}` | `ci.autoharness_install_command` (default `pip install autoharness`) | Installs the `autoharness` package on the `topology-check` job's runner so `scripts/ci-topology-check.sh` can invoke the CLI. This product is always a pip-installable Python CLI regardless of the consuming workspace's own primary language; a self-hosting dogfood install (this repo) resolves it to `pip install -e .` instead. |

### Optional gate steps

The expensive job lists Lint / Format check / Typecheck / Test / Build check
steps. During resolution, **drop any step whose command variable has no
discovered value** — leaving an unresolved `{{...}}` in output is an installation
error. Keep only the gates the workspace actually has (the same set recorded in
`local_gating.pre_push_gates`).

## Pipeline-Topology CI Backstop (Gate C)

**Backlogit-only precondition**: this job is installed **only** when the
workspace's backlog tool is `backlogit` (`{{FEATURE_SHIPMENTS}}` is `true`).
The gate's backlog reader (`FilesystemTopologyReaders`) currently reads only
`.backlogit/`; installing this job for a backlog-md/manual/non-shipment-capable
workspace would always resolve `BACKLOG_UNAVAILABLE`, which becomes a
permanent BLOCK once `PIPELINE_TOPOLOGY_GATE_REQUIRED` is promoted to
required. `install-harness` omits the job and its entrypoint script entirely
for those workspaces rather than rendering it advisory-only as a workaround.

The always-running `topology-check` job checks out the repo, installs
`autoharness`, and runs `scripts/ci-topology-check.sh` (resolved from
`templates/ci/ci-topology-check.sh.tmpl` — see
[`docs/pipeline-topology-gate.md`](../../docs/pipeline-topology-gate.md#ci-topology-check-entrypoint-gate-c)).
It is **not** gated on the `changes` job's path-filter output — the ambient
check is inexpensive and non-shipment-scoped, and skipping it for docs/backlog
-only changes would leave exactly the commits most likely to touch
`.backlogit/` state unchecked.

**Required-vs-advisory** is an explicit **operator toggle**, not a template
variable: `continue-on-error: ${{ vars.PIPELINE_TOPOLOGY_GATE_REQUIRED !=
'true' }}`. Leaving the `PIPELINE_TOPOLOGY_GATE_REQUIRED` repository variable
unset keeps the job advisory (its result is reported as `success` to
`ci-gate` even when the gate itself reports BLOCK); setting it to `'true'`
flips the job to required (a BLOCK verdict fails `topology-check` for real,
and therefore `ci-gate`) with **no workflow re-render needed**. See
[`docs/pipeline-topology-gate-ci-rollout.md`](../../docs/pipeline-topology-gate-ci-rollout.md)
for the staged advisory→required rollout narrative.

## Path-filter mode

`ci.path_filter_mode` has a single supported value: `fail_closed_changes_job`
(rendered above). The always-running `changes` job evaluates a fail-closed
denylist with `predicate-quantifier: every`, so any path outside the docs/backlog
denylist sets `code == 'true'` and forces the expensive job to run. A trigger-level
`paths-ignore` alternative was intentionally **not** adopted: it silently skips the
whole run (including the aggregation gate) when a new/unlisted file type appears,
which is unsafe for a required-check contract.

## Required-check contract (operator action)

The harness produces the aggregation-gate check and this guidance; it does **not**
edit branch rulesets. **Re-adding or renaming a required status check in a branch
ruleset is an operator configuration action.** If a ruleset already requires a
check by name, set `{{CI_REQUIRED_CHECK_NAME}}` to that exact name so the produced
check satisfies it with no ruleset edit. See P-019 in the policy registry.

## Action pins

Pinned to the SHAs the sibling reference workflows use (verified current):

* `actions/checkout` v6.0.3 `df4cb1c069e1874edd31b4311f1884172cec0e10`
* `dorny/paths-filter` v3.0.3 `d1c1ffe0248fe513906c8e24db8ea791d46f8590`

Add `actions/setup-*` pins inside `{{CI_SETUP_STEPS}}` per ecosystem. Refreshing
pins is a periodic maintenance chore.
