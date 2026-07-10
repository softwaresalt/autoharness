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

## Three-job shape

Each variable below is the human-facing **check context** (`name:`), which may
contain spaces or slashes. The underlying GitHub Actions **job IDs are fixed,
valid slugs** — `changes`, `expensive`, and `ci-gate` — because job IDs may not
contain spaces. Branch rulesets match on the check context (`name:`), not the
job ID.

| Job (`name:`) | Job ID | Runs | Purpose |
|---|---|---|---|
| `detect code changes` | `changes` | always | Fail-closed `dorny/paths-filter` (`predicate-quantifier: every`) over a denylist. Outputs `code` = `true` unless the change touches only docs/backlog paths. |
| `{{CI_EXPENSIVE_JOB_NAME}}` | `expensive` | when `code == 'true'` and not a `chore:`/`docs:` PR | The expensive lint/format/typecheck/test/build gate. Never the required check. |
| `{{CI_REQUIRED_CHECK_NAME}}` | `ci-gate` | always (`if: always()`) | Aggregation gate. **This is the only check a branch ruleset should require.** Treats a skipped expensive job as OK; fails only when a needed job is `failure`/`cancelled`. |

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
| `{{CI_RUNNER_OS}}` | `ubuntu-latest` when `ci.linux_only` (default) | Regular CI is Linux-only; cross-OS stays in release-tag workflows. |
| `{{CI_ENABLE_OS_MATRIX}}` | inverse of `ci.linux_only` | When true, replace `runs-on: {{CI_RUNNER_OS}}` with a matrix. |
| `{{CI_DOCS_ONLY_PATHS}}` | `ci.docs_only_paths` | Rendered as indented denylist negations, e.g. `- '!**/*.md'` / `- '!docs/**'`. |
| `{{CI_SETUP_STEPS}}` | per-ecosystem toolchain setup | Checkout + SDK setup + dependency install steps for the expensive job. |
| `{{LINT_COMMAND}}` | `lint.command` | Omit the step when no lint gate is discovered. |
| `{{FORMAT_CHECK_COMMAND}}` | `format.check_command` | Omit the step when no format gate is discovered. |
| `{{TYPECHECK_COMMAND}}` | `typecheck.command` | Omit the step when no typecheck gate is discovered. |
| `{{TEST_COMMAND}}` | `test.command` | The primary gate. |
| `{{BUILD_CHECK_COMMAND}}` | `build.check_command` | Omit the step when no build-check gate is discovered. |

### Optional gate steps

The expensive job lists Lint / Format check / Typecheck / Test / Build check
steps. During resolution, **drop any step whose command variable has no
discovered value** — leaving an unresolved `{{...}}` in output is an installation
error. Keep only the gates the workspace actually has (the same set recorded in
`local_gating.pre_push_gates`).

## Path-filter modes

`ci.path_filter_mode` selects the strategy:

* `fail_closed_changes_job` (default, rendered above) — the recommended pattern.
* `paths_ignore` — a simpler alternative that skips whole runs via `paths-ignore`
  on the `on:` triggers. Only use when the operator explicitly prefers it; it can
  silently skip the gate on a new file type. To use it, remove the `changes` job
  and the expensive job's `needs`/`code` guard, and add:

  ```yaml
  on:
    push:
      branches: [main]
      paths-ignore: [{{CI_DOCS_ONLY_PATHS}}]
    pull_request:
      branches: [main]
      paths-ignore: [{{CI_DOCS_ONLY_PATHS}}]
  ```

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
