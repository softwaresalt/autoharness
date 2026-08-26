---
title: "Rename Dogfood CI Aggregation Gate to ci gate"
doc_type: decided-plan
status: reviewed
created: 2026-07-10
feature: "071-F"
shipment: "083-S"
tasks: ["071.001-T"]
supersedes:
  - docs/archive/plans/2026-07-10-ci-gate-rename-plan.md
---

# Decided Plan: Rename Dogfood CI Aggregation Gate to ci gate

**Outcome:** Reviewed and approved for implementation as feature `071-F`, task
`071.001-T`, shipment `083-S`. The source plan records an approved one-task
dogfood chore but no PR or merge evidence, so this decided-plan preserves the
reviewed state rather than claiming shipment. This decided-plan replaces the
verbose original, archived for traceability at
`docs/archive/plans/2026-07-10-ci-gate-rename-plan.md`.

## Decision

Rename the dogfood CI aggregation job in `.github/workflows/ci.yml` from
`build` to `ci-gate` / `ci gate` and rewrite both explanatory comment blocks so
they describe the always-running aggregation gate rather than the deleted-ruleset
history. This is a dogfood-only cleanup of the aggregation gate introduced by
the unified CI + local-gating work; the shared template already uses the desired
naming, so `templates/ci/ci.yml.tmpl` stays untouched.

## Implementation (1 task)

- **071.001-T** — In `.github/workflows/ci.yml`, change job id `build:` to
  `ci-gate:` and `name: build` to `name: ci gate`; rewrite the header comment
  and the inline comment above the job; preserve the existing `if: always()`,
  `needs: [changes, test]`, and pass/fail semantics.

## Key constraints preserved

- Single-file scope only: `.github/workflows/ci.yml`.
- No behavior change: the aggregation gate still always runs, still depends on
  `changes` and `test`, still treats skipped `test` as acceptable, and still
  fails only when a needed job ends in `failure` or `cancelled`.
- No template, ship-agent, or PR-automation wording changes.
- No profile/schema change: `.autoharness/workspace-profile.yaml` has no
  `ci.required_check_name` field to update.
- Minimal blast radius: nothing `needs:` the final job, so the job-id rename
  does not break downstream workflow dependencies.

## Rejected alternatives

- **Broader CI/template sweep** — rejected because the shared template already
  matched the desired naming; only the dogfood workflow had stale naming and
  stale comments.
- **Required-check or profile reconfiguration** — rejected because the plan
  documented no `ci.required_check_name` field needing update, and the operator
  had already removed the deleted-ruleset dependency.
- **Changing local-build-evidence gate wording elsewhere** — rejected as
  unrelated to this one-file correction.

## Review findings that changed the plan

No separate review findings changed the one-task scope. The source plan's
self-review simply confirmed the rename, comment rewrites, no-`needs` breakage,
and behavior-preservation acceptance criteria, then approved the task for
harvest.