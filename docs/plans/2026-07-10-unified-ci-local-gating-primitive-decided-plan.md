---
title: "Unified CI + Local-Gating Harness Primitive"
doc_type: decided-plan
status: reviewed
created: 2026-07-10
source_stash_ids:
  - "EFA0CA31"
  - "BA28AE56"
  - "0B3F546C"
  - "027B60E8"
supersedes:
  - docs/archive/plans/2026-07-10-unified-ci-local-gating-primitive-plan.md
---

# Decided Plan: Unified CI + Local-Gating Harness Primitive

**Outcome:** Reviewed and approved for harvest with P-006 hardening. The source
plan defines the unified CI template, cross-platform pre-push hook template,
dogfood instances, discovery wiring, and policy `P-019`, but it includes no PR
or merge evidence, so this decided-plan records the reviewed state rather than
shipped status. This decided-plan replaces the verbose original, archived for
traceability at
`docs/archive/plans/2026-07-10-unified-ci-local-gating-primitive-plan.md`.

## Problem (settled)

Define one harness primitive that combines fail-closed CI merge gating with
opt-in local pre-push quality gates, while staying language-agnostic,
dogfood-parity-friendly, and honest about the real tooling each workspace has.

## Decisions

1. **Start with profile/discovery/schema support.** The workspace profile gains
   explicit `ci` and `local_gating` fields so templates and installed docs can
   rely on discovered gate names, path-filter mode, Linux-only behavior, and
   pre-push gate availability.
2. **Use a fail-closed CI shape.** The CI template has an always-running
   `changes` job, a guarded expensive job that runs only when code paths changed,
   and an always-running aggregation gate that serves as the required check.
3. **Make local gating opt-in and cross-platform.** The pre-push scripts run the
   discovered gates once, warn and skip when a tool is absent, and block push on
   real failures without inventing retry behavior.
4. **Keep dogfood instances grounded in real autoharness tooling.** The repo's
   CI instance runs the verified `unittest` suite on Linux and the tracked local
   gate uses the real `unittest` + `markdownlint` combination rather than adding
   speculative linters.
5. **Formalize the operator contract in P-019.** The harness emits the CI check,
   the local gate, and the documentation, but branch-ruleset naming remains an
   operator configuration concern rather than something the harness edits.

## Implementation (6 tasks)

- **T5 — Profile fields + discovery + variable table:** extend
  `schemas/workspace-profile.schema.json`, wire the guidance into
  `.github/skills/workspace-discovery/SKILL.md`, and register every new CI/local
  gating variable in `.github/skills/install-harness/SKILL.md`.
- **T1 — Language-agnostic CI workflow template:** add
  `templates/ci/ci.yml.tmpl` with `changes`, a guarded expensive job, and the
  always-running aggregation gate.
- **T2 — Cross-platform pre-push hook template:** add
  `templates/scripts/pre-push-quality-gates.ps1.tmpl` and `.sh.tmpl` with
  discovered gates, warn-and-skip tool absence, and blocking exit codes on
  actual failures.
- **T3 — autoharness dogfood CI:** add `.github/workflows/ci.yml` with the
  denylist-based `changes` job, Linux `unittest` run, and the dogfood
  aggregation gate named `build` to satisfy the then-current ruleset contract.
- **T4 — autoharness dogfood pre-push hook:** add the tracked pre-push script
  and a minimal install note consistent with the existing hook pattern.
- **T6 — Policy P-019 + primitive docs:** add the policy template entry plus the
  operator-facing documentation that explains the required-check contract.

## Key constraints preserved

- The required status check is the always-running aggregation gate, never the
  guarded expensive job.
- `dorny/paths-filter` must run with `predicate-quantifier: every` so the denylist
  is fail-closed rather than accidentally matching everything.
- The expensive job's condition is path impact only; skipped expensive jobs must
  not block docs-only or backlog-only PRs.
- Linux-only CI is explicit at this layer; the rejected OS-matrix escape does not
  linger as an unresolved variable.
- Templates stay parameterized and must resolve cleanly against multiple
  technology profiles with no leftover `{{...}}`.
- Dogfood parity is explicit, but the dogfood instance remains an instance of the
  template design rather than a literal copy.
- The harness must not invent ruff, pyright, or other gates the workspace has not
  actually discovered.

## Rejected alternatives

- **Title-based `chore:` / `docs:` guards for the expensive job** — rejected
  during review as fail-open; path impact alone is the safe gate.
- **`{{CI_ENABLE_OS_MATRIX}}` or a cross-OS matrix escape at this layer** —
  rejected as unimplemented; `ci.linux_only` stays explicit and release workflows
  own broader OS validation.
- **Making the guarded expensive job the required check** — rejected because that
  would block changes where the job is intentionally skipped.
- **Inventing dogfood gates such as ruff or pyright** — rejected because the
  primitive must reflect only real discovered tooling.
- **Having the harness edit GitHub branch rulesets** — rejected; the harness
  produces the check and documents the contract, but operator configuration stays
  outside the template.

## Review findings that changed the plan

Review tightened the primitive in two important ways. First, the originally
planned title-based guard for the expensive job was removed, making path impact
the sole condition. Second, the unimplemented OS-matrix escape was explicitly
rejected, locking in the Linux-only contract at this layer. The same review also
made the always-running aggregation gate and `predicate-quantifier: every` part
of the fail-closed definition rather than optional implementation details.