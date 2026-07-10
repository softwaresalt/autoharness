---
title: "Unified CI + Local-Gating Harness Primitive"
description: "Deliberated design for a technology-agnostic CI-workflow template, a cross-platform local pre-push quality-gate hook template, an autoharness dogfood CI instance producing a satisfiable build check, and the workspace-discovery + policy wiring that ties them together."
topic: "How should autoharness deliver unified, technology-agnostic remote CI plus local pre-push enforcement as harness artifacts, and how does the autoharness repo dogfood it?"
depth: "hardened"
decision_status: "accepted"
doc_type: decision
source: docs/decisions/2026-07-10-unified-ci-local-gating-primitive-deliberation.md
source_stash_ids:
  - "EFA0CA31"
  - "BA28AE56"
  - "0B3F546C"
  - "027B60E8"
supersedes:
  - "docs/decisions/2026-07-05-ci-build-action-scope.md"
linked_artifacts:
  - ".github/workflows/release.yml"
  - "templates/scripts/pre-commit-markdownlint.ps1.tmpl"
  - "templates/scripts/pre-commit-markdownlint.sh.tmpl"
  - "templates/policies/workflow-policies.md.tmpl"
  - "schemas/workspace-profile.schema.json"
  - ".github/skills/workspace-discovery/SKILL.md"
tags:
  - "ci"
  - "github-actions"
  - "pre-push-hook"
  - "local-gating"
  - "required-status-check"
  - "aggregation-gate"
  - "fail-closed"
  - "primitive-5"
  - "primitive-8"
  - "primitive-10"
---

# Unified CI + Local-Gating Harness Primitive

## Problem

Four related stash entries describe one coherent capability with heavy overlap:

* **`EFA0CA31`** (high, umbrella) — synthesize three sibling CI patterns (docline,
  backlogit, graphtor) into a single technology-agnostic CI + local-enforcement
  design and templatize it, delivering **both** a language-agnostic CI-workflow
  template and a local pre-push hook enforcement template wired through
  workspace-discovery.
* **`BA28AE56`** (high, dogfood) — the autoharness repo itself has a `main`
  ruleset requiring a status check named `build` that **no workflow produces**
  (only `release.yml`, tag-scoped). PRs stay pending on `build` forever and
  require `--admin` bypass. Needs a real PR-triggered workflow that reports a
  satisfiable `build` check running the Python test suite.
* **`0B3F546C`** (medium) — templatize the fail-closed denylist +
  always-running aggregation-gate pattern as a reusable CI primitive.
* **`027B60E8`** (medium) — catalog the deterministic mechanisms (hooks, gates)
  for enforcing layered review + local build/lint/test before PRs.

`EFA0CA31` subsumes `0B3F546C` and `027B60E8`; `BA28AE56` is the concrete
autoharness instance. This deliberation consumes **all four** as one feature.

## Prior art superseded

`docs/decisions/2026-07-05-ci-build-action-scope.md` (stash `8DBD43A1`)
deliberately **deferred** adding a PR build workflow to conserve Actions minutes,
and recorded a "Future Rule" for when one is eventually added (path-impact as the
source of truth, title conditions advisory only, keep a lightweight safety check
when expensive jobs skip). This stash group is the trigger that "future" contemplated.
This decision advances and supersedes it: we now build the workflow, and we honor
its Future Rule verbatim (fail-closed path filtering is authoritative; `chore:`/`docs:`
title guards are advisory; the always-running aggregation gate is the lightweight
safety check that reports when expensive jobs skip).

## Decision

Deliver a **unified CI + local-gating primitive** as a base-primitive deepening
(not a capability pack — see rationale below), composed of four artifact families:

1. **Language-agnostic CI-workflow template** (`templates/ci/ci.yml.tmpl`) with
   `{{VARIABLE}}` swap points for per-ecosystem job internals.
2. **Cross-platform local pre-push hook template** (PowerShell + POSIX sh) that
   runs the workspace's discovered build + test + lint + format + typecheck gates
   and blocks the push on failure; opt-in and installable.
3. **autoharness dogfood instances**: the repo's own
   `.github/workflows/ci.yml` (producing a satisfiable `build` check) and its own
   installed pre-push hook.
4. **Wiring**: workspace-discovery profile fields + install variable table + a new
   policy **P-019** + operator documentation.

### D1 — Aggregation gate is the single required status check

The one branch-rule-required check is an **always-running aggregation job**
(`if: always()`, `needs: [all jobs]`) that fails only when a needed job result is
`failure` or `cancelled` and treats `skipped` as OK. This solves the
required-check × skipped-job gotcha: expensive jobs may be skipped on docs-only or
`chore:`/`docs:` PRs without blocking the merge, because the required check is the
gate, not the guarded jobs.

* **Generic template**: the required-check name is a variable
  `{{CI_REQUIRED_CHECK_NAME}}` (default `ci gate`, matching docline's `name: ci gate`).
* **autoharness dogfood**: the aggregation job's `name:` is set to **`build`** so it
  satisfies the existing `main` ruleset's required `build` check **without any
  ruleset edit**. This is the minimal, immediate fix for `BA28AE56` — the harness
  produces the check; re-adding or renaming a required check remains an operator
  config action, and here no operator action is even required because the produced
  check name already matches.

Every job carries an explicit `name:` attribute so any job is branch-rule-referenceable.

### D2 — Fail-closed path filtering (synthesized default)

Use a lightweight always-running `changes` job (graphtor's `name: detect code changes`
shape) built on `dorny/paths-filter` with `predicate-quantifier: every` over a
**denylist** (backlogit's pattern): `['**', '!**/*.md', '!docs/**', '!.backlogit/**',
'!.autoharness/**']`. `every` makes the `!` negations actually exclude docs/backlog;
any code/config/unknown-type change fails **closed** into the expensive gate. The
expensive job runs only when `changes.outputs.code == 'true'`. `paths-ignore` on the
`on:` triggers (docline/graphtor style) is offered as a simpler alternative
`{{CI_PATH_FILTER_MODE}}`, but the fail-closed `changes` job is the recommended default
because it never silently skips the security-sensitive gate on a new file type.

### D3 — Regular CI is Linux-only; cross-OS deferred to release

Regular PR/push CI runs `ubuntu-latest` only (graphtor rationale): the operator
devbox is Windows and already runs the full local gate before push, so redundant
cross-OS matrix runs waste minutes. macOS/Windows verification stays in
`release.yml` on `v*` tags. The template exposes `{{CI_RUNNER_OS}}` /
`{{CI_ENABLE_OS_MATRIX}}` for workspaces that want a matrix.

### D4 — Title guards are advisory, path filter is authoritative

Expensive jobs carry a `chore:`/`docs:` PR-title guard (docline pattern), inert on
non-PR events. Per the superseded doc's Future Rule, title guards are **advisory
convenience only**; the fail-closed path filter is the safer source of truth.

### D5 — Local pre-push hook enforcement (the critical implication)

Because remote CI is intentionally minimal/Linux-only and trusts local
verification, the harness MUST enforce local build + test + lint + format +
typecheck **before push**. Delivered as a cross-platform pre-push hook
(`pre-push-quality-gates.ps1.tmpl` + `.sh.tmpl`) that:

* reads the discovered gate commands from the workspace profile (variables such as
  `{{TEST_COMMAND}}`, `{{LINT_COMMAND}}`, `{{FORMAT_CHECK_COMMAND}}`,
  `{{TYPECHECK_COMMAND}}`, `{{BUILD_CHECK_COMMAND}}`; missing gates are skipped, not
  failed — mirrors the existing `pre-commit-markdownlint` "tool not found → warn
  and skip" convention);
* runs each present gate and **blocks the push (exit 1)** on any failure;
* is **opt-in / installable** (the harness writes the script and install guidance;
  it does not silently overwrite a user's `.git/hooks`);
* respects the circuit-breaker instruction — the hook is a single deterministic
  pass with no internal retry loop, so it cannot spin; a failing gate surfaces
  immediately for the developer/agent to fix.

### D6 — autoharness dogfood specifics (real, discoverable tooling only)

The autoharness repo's **real** toolchain (verified this session) is:

* Test: `python -m unittest discover -s tests` (**416 tests**, stdlib `unittest`).
  `pyproject.toml` has a `[tool.pytest.ini_options]` stub but **pytest is not a
  declared or locked dependency** (`uv.lock` locks only `jsonschema` + `PyYAML`).
* Lint/format/typecheck: **none configured** (no `ruff`, no `pyright`, no config
  files). The only doc gate is `markdownlint` (already enforced by the existing
  `pre-commit-markdownlint` hook, P-008).

Therefore the dogfood CI `build` job runs `python -m unittest discover -s tests`
(with `PYTHONPATH=src`) and MUST NOT invent ruff/pyright steps. The dogfood
pre-push hook runs the same unittest suite plus `markdownlint`. Any templated
Python profile must reflect this real, discoverable tooling — not assumptions.

The dogfood `ci.yml` must NOT duplicate `release.yml` (tag-scoped, `job name:
release`); it produces only the PR/push `build` check.

## Architecture framing: base-primitive deepening, not a capability pack

CI + local pre-push gating is **near-universal** for any repo with a remote and a
toolchain, and should be a **default-recommended** part of the harness rather than
an optional overlay. It deepens existing base primitives:

* **Primitive 5 (Tool Execution, Safety Modes & Guardrails)** — the pre-push hook is
  a deterministic local guardrail; a new policy P-019 formalizes it.
* **Primitive 8 (Workflow Policy)** — P-019 governs local-gate enforcement sequencing.
* **Primitive 7 (Observability & Evaluation)** — the always-running aggregation gate
  is the single observable, always-reported merge signal.
* **Primitive 10 (Operational Closure & Feedback)** — remote CI + local gate close the
  loop that a change is verified before it can merge.

It is therefore **not** modeled as a capability pack: it does not redefine the
primitive model, it is not optional-by-default, and forcing it through the overlay
contract (eligibility/recommendation/overlay-targets/behavior-deltas/verification/
drift for six artifact classes) would add ceremony without benefit. Conditionality
is handled the normal way — workspace-discovery only emits the CI workflow when a CI
platform + toolchain is detected, and the pre-push hook remains opt-in.

## How this fixes the build-check-no-producer gap

The `main` ruleset requires a check named `build`. Today only `release.yml`
(tag-scoped) exists, so `build` never runs on a PR → every PR is stuck pending →
merges require `--admin`. Naming the always-running aggregation job's check `build`
makes the required check **genuinely satisfiable on every PR** (it reports success
when tests pass or are legitimately skipped) with **no ruleset change** and **no
admin bypass**.

## Source patterns referenced

* `C:\Source\GitHub\docline\.github\workflows\ci.yml` — named jobs, `chore:`/`docs:`
  title guards, `ci-gate` always-running aggregation (`name: ci gate`, `if: always()`,
  `needs` all, skipped-is-OK).
* `C:\Source\GitHub\backlogit\.github\workflows\ci.yml` — `dorny/paths-filter` +
  `predicate-quantifier: every` fail-closed denylist `changes` job.
* `C:\Source\GitHub\graphtor\.github\workflows\ci.yml` — Linux-only rationale +
  `changes` (`name: detect code changes`) job gating the heavy build.
* `C:\Source\GitHub\autoharness\.github\workflows\release.yml` — existing tag-scoped
  release; CI must not duplicate it.

## Consolidation outcome

All four stashes consumed into one feature. None deferred. Decomposed into six
width-isolated tasks (see the plan doc). Estimated ~12h total (6 × ~2h).
