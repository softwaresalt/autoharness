---
title: "Unified CI + Local-Gating Harness Primitive — Implementation Plan"
description: "Impl-plan, plan-hardening (P-006), and plan-review verdict for the unified CI-workflow template, cross-platform pre-push hook template, autoharness dogfood CI + hook instances, workspace-discovery wiring, and policy P-019."
doc_type: plan
source: docs/plans/2026-07-10-unified-ci-local-gating-primitive-plan.md
decision_doc: docs/decisions/2026-07-10-unified-ci-local-gating-primitive-deliberation.md
source_stash_ids:
  - "EFA0CA31"
  - "BA28AE56"
  - "0B3F546C"
  - "027B60E8"
requires_plan_hardening: "yes"
plan_review_verdict: "approved"
tags:
  - "ci"
  - "pre-push-hook"
  - "workspace-discovery"
  - "policy-p019"
  - "dogfood-parity"
---

# Unified CI + Local-Gating Harness Primitive — Implementation Plan

See `docs/decisions/2026-07-10-unified-ci-local-gating-primitive-deliberation.md`
for the design rationale. This plan decomposes the feature into six
width-isolated, ≤2h, ≤~3-file tasks and enumerates risks (P-006).

## Task decomposition & dependency graph

```text
T5 (schema + discovery + variable table)   ── foundational, no deps
  ├── T1 (language-agnostic CI-workflow template)   depends on T5
  │       └── T3 (autoharness dogfood ci.yml → build check)   depends on T1
  └── T2 (cross-platform pre-push hook template)     depends on T5
          └── T4 (autoharness dogfood pre-push hook instance)  depends on T2
T6 (policy P-019 + primitive doc + operator docs)   depends on T1, T2
```

### T5 — Profile fields + workspace-discovery detection + variable table

* **Scope**: Extend `schemas/workspace-profile.schema.json` `ci` object with
  `required_check_name`, `linux_only` (bool), `path_filter_mode`
  (`fail_closed_changes_job` | `paths_ignore`), and `docs_only_paths` (array); add a
  `local_gating` object (`pre_push_enabled`, `pre_push_gates` array). Wire detection
  guidance into `.github/skills/workspace-discovery/SKILL.md` (Phase 1/2) so the
  profile captures CI platform + toolchain + which quality gates exist. Add the new
  variables to the install-harness SKILL.md variable resolution table.
* **Files (≤3)**: `schemas/workspace-profile.schema.json`,
  `.github/skills/workspace-discovery/SKILL.md`, `.github/skills/install-harness/SKILL.md`.
* **Verify**: schema validates; JSON parses; variable table lists every new `{{VAR}}`.

### T1 — Language-agnostic CI-workflow template

* **Scope**: Create `templates/ci/ci.yml.tmpl`: always-running `changes` job
  (`name: detect code changes`, dorny/paths-filter `every` denylist), guarded
  expensive job (`name: {{CI_EXPENSIVE_JOB_NAME}}`,
  `if: changes.outputs.code == 'true'` — path impact is the SOLE condition; the
  originally-planned `chore:`/`docs:` title guard was rejected as fail-open during
  081-S review, see decision D1a — swappable per-ecosystem internals via
  `{{CI_SETUP_STEPS}}` / `{{TEST_COMMAND}}` / `{{LINT_COMMAND}}` etc.), and the
  always-running aggregation gate (`name: {{CI_REQUIRED_CHECK_NAME}}`, `if: always()`,
  `needs` all, skipped-is-OK). SHA-pinned actions, `permissions: contents: read`,
  concurrency cancellation. Linux-only default with `{{CI_ENABLE_OS_MATRIX}}` escape.
* **Files (≤3)**: `templates/ci/ci.yml.tmpl`, a short `templates/ci/README.md`
  (variable + usage doc), variable-table addition already covered by T5.
* **Verify**: all `{{VAR}}` documented; template is valid YAML once variables resolve
  against ≥3 profiles (Python/unittest, Rust/cargo, TypeScript/node).

### T2 — Cross-platform pre-push hook template

* **Scope**: Create `templates/scripts/pre-push-quality-gates.ps1.tmpl` and
  `.sh.tmpl`. Each runs discovered gates (`{{TEST_COMMAND}}`, `{{LINT_COMMAND}}`,
  `{{FORMAT_CHECK_COMMAND}}`, `{{TYPECHECK_COMMAND}}`, `{{BUILD_CHECK_COMMAND}}`),
  skipping absent gates (tool-not-found → warn+skip, per existing markdownlint hook),
  blocking push (exit 1) on any failure. Single deterministic pass (no retry loop —
  circuit-breaker compatible). Opt-in install guidance in a header comment.
* **Files (≤3)**: `templates/scripts/pre-push-quality-gates.ps1.tmpl`,
  `templates/scripts/pre-push-quality-gates.sh.tmpl`, install wiring note in
  `.github/skills/install-harness/SKILL.md`.
* **Verify**: both scripts parse (pwsh `-NoProfile` parse / `bash -n`); exit-code
  semantics documented.

### T3 — autoharness dogfood `.github/workflows/ci.yml`

* **Scope**: Create the repo's own PR/push CI: `changes` job (denylist incl.
  `.autoharness/**`, `.backlogit/**`, `docs/**`, `**/*.md`); expensive job runs
  `PYTHONPATH=src python -m unittest discover -s tests` (416 tests) on
  `ubuntu-latest` only; aggregation gate `name: build` (matches ruleset). MUST NOT
  duplicate `release.yml`. SHA-pinned actions, least-privilege perms, concurrency.
* **Files (≤1)**: `.github/workflows/ci.yml`.
* **Verify**: `actionlint`/YAML valid; the produced check name is exactly `build`;
  no ruff/pyright steps invented.

### T4 — autoharness dogfood pre-push hook instance

* **Scope**: Install autoharness's own opt-in pre-push hook running the unittest
  suite + `markdownlint`, committed as a tracked script (e.g.
  `scripts/hooks/pre-push.ps1`) with install guidance, consistent with the existing
  `pre-commit-markdownlint` instance.
* **Files (≤2)**: tracked hook script + a one-line install note in docs.
* **Verify**: script parses; running it locally blocks on a failing gate.

### T6 — Policy P-019 + primitive doc + operator docs

* **Scope**: Add **P-019 (Local Pre-Push Quality-Gate Enforcement)** to
  `templates/policies/workflow-policies.md.tmpl` (precondition/postcondition/gate
  point/violation action). Add a base-primitive-deepening note referencing
  Primitives 5/7/8/10 (harness-architecture instruction or docs). Add operator
  documentation covering the required-check contract — that re-adding/renaming a
  required status check in a branch ruleset is an operator config action (the
  harness produces the check + guidance, it does not edit rulesets).
* **Files (≤3)**: `templates/policies/workflow-policies.md.tmpl`, one instruction/doc
  file, one operator doc. **Policy registry is template-only** (no installed copy) —
  do NOT add an installed `.github` policy file.
* **Verify**: P-019 frontmatter/table matches P-001..P-018 shape; markdownlint clean.

## Plan Hardening (P-006)

This plan has **elevated blast radius** (schema evolution + multiple template
families + a new policy + dogfood CI that touches merge-gating), so hardening is
required. Enumerated risks and mitigations:

| # | Risk | Likelihood | Blast radius | Mitigation (owned by task) |
|---|------|-----------|--------------|----------------------------|
| R1 | **Required-check misconfig** — dogfood aggregation job named wrong, so ruleset `build` still never satisfied | Med | Blocks all PRs | T3: assert produced check name is exactly `build`; verify with a real PR check-run readback before closure. Document that renaming is an operator action. |
| R2 | **Skipped-job merge-block regression** — required job is a guarded/skippable job instead of the always-running gate | Med | Blocks docs-only PRs | T1/T3: only the `if: always()` aggregation gate is the required check; expensive jobs are never the required check. Gate treats `skipped` as OK, fails on `failure`/`cancelled`. |
| R3 | **Hook cross-platform breakage** — ps1 works, sh fails (or vice versa), or hook hard-fails when a gate tool is absent | Med | Blocks pushes locally | T2/T4: mirror existing markdownlint hook's tool-not-found→warn+skip; parse-check both scripts; single deterministic pass (no retry). Opt-in install so it never silently breaks a user's push. |
| R4 | **Template variable drift** — unresolved `{{VAR}}` in generated output or variables not in the install-harness table | Med | Broken installs | T5 owns the variable table as the single registry; T1/T2 must add every new var to it; verify no `{{...}}` remains after resolution against ≥3 profiles. |
| R5 | **Dogfood-parity drift** — behavioral change to a `templates/*.tmpl` not mirrored into the autoharness `.github/` instance (or vice versa) | Med | Silent divergence | T3/T4 are explicit dogfood mirrors of T1/T2; plan-review and Ship review must diff template intent vs dogfood instance. Note: dogfood CI/hook are *instances* of the template design, not literal `.tmpl` copies. |
| R6 | **SHA-pin staleness** — pinned action SHAs go stale/insecure over time | Low | Supply-chain drift | T1/T3: pin to the same SHAs the sibling repos use (verified current: checkout v6.0.3 `df4cb1c`, setup-python v6.2.0 `a309ff8`, paths-filter v3.0.3 `d1c1ffe`); document that pin refresh is a periodic maintenance chore, not this feature's concern. |
| R7 | **Fail-open path filter** — `predicate-quantifier` omitted so `**` marks everything matched and negations never apply | Low | Security gate silently skipped | T1: hard-code `predicate-quantifier: every` and document why (backlogit lesson); default mode is fail-closed `changes` job, not bare `paths-ignore`. |
| R8 | **Actions-minute cost regression** — reintroducing a PR workflow reverses the cost-saving that the superseded 2026-07-05 decision protected | Low | Billing | Linux-only + fail-closed path filter keep docs/backlog PRs off the expensive job (title guards were rejected as fail-open — see D1a); only real code changes spend minutes. Documented in decision doc. |
| R9 | **Scope creep** — inventing ruff/pyright gates autoharness doesn't actually have | Med | Broken dogfood CI | T3/T6: dogfood reflects only real discoverable tooling (unittest + markdownlint); template keeps ecosystem internals as swappable variables, not hard-coded tools. |

**Hardening conclusion**: risks are bounded and each is owned by a specific task
with a concrete verification. No risk requires operator input to *plan*; R1
(required-check readback) and the ruleset-reconfiguration note are the two items
that touch operator-visible config and are explicitly documented rather than
silently automated.

## Plan Review

* **Granularity (2-hour rule)**: all six tasks ≤~3 files, single concern each. PASS.
* **Width isolation**: schema (T5) / CI template (T1) / hook template (T2) / dogfood
  CI (T3) / dogfood hook (T4) / policy+docs (T6) are cleanly separated. PASS.
* **Dependency integrity (P-003)**: T1,T2→T5; T3→T1; T4→T2; T6→T1,T2. Acyclic. PASS.
* **Dogfood parity**: T3/T4 explicitly mirror T1/T2 design. PASS.
* **Policy registry convention**: P-019 in template only; no installed copy. PASS.
* **Real-tooling constraint**: dogfood uses verified `unittest` (416 tests), no
  invented linters. PASS.
* **Verdict**: **APPROVED** for harvest.
