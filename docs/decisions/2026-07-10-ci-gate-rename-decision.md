---
title: "Rename Dogfood CI Aggregation Gate from build to ci gate"
description: "Operator-directed chore: the dogfood CI aggregation-gate job in .github/workflows/ci.yml was named build only to satisfy a now-deleted main-protected ruleset. Rename it to ci-gate / ci gate to remove the misleading name and match the template default."
topic: "Should the vestigial build-named CI aggregation gate be renamed to ci gate?"
depth: "trivial"
decision_status: "accepted"
doc_type: decision
source: docs/decisions/2026-07-10-ci-gate-rename-decision.md
source_stash_ids: []
backlog_items:
  - "071-F"
  - "071.001-T"
  - "083-S"
linked_artifacts:
  - ".github/workflows/ci.yml"
  - "templates/ci/ci.yml.tmpl"
tags:
  - "ci"
  - "github-actions"
  - "dogfood-parity"
  - "cleanup"
---

# Rename Dogfood CI Aggregation Gate from build to ci gate

## Decision

Rename the always-running aggregation-gate job in the dogfood workflow
`.github/workflows/ci.yml` from job id `build` (`name: build`) to job id
`ci-gate` (`name: ci gate`), and rewrite the two comment blocks that justified
the `build` name so they describe the `ci gate` aggregation gate without the
obsolete ruleset rationale.

This is a purely dogfood-instance correction. No template, schema, or agent
behavior changes.

## Rationale

* The `build` name was chosen **only** to satisfy a `main-protected` repository
  ruleset that required a status check literally named `build`, with no ruleset
  edit. The operator has since **deleted that ruleset**, so the name is now
  vestigial.
* The name is actively misleading: it reads as "run a build on every PR," which
  contradicts the CI-gate cost design. autoharness has **no build step** — the
  expensive job is the `test` unittest suite, which is skipped for
  docs/backlog-only PRs; only the cheap always-running gate reports.
* The operator has decided **not** to require any status check in branch
  protection, so this gate is not a required check. Renaming removes the
  confusion at its root.
* The template `templates/ci/ci.yml.tmpl` is **already correct**: it uses job id
  `ci-gate` and `name: {{CI_REQUIRED_CHECK_NAME}}` (default `ci gate`). So no
  template change is needed — this change simply aligns the dogfood instance with
  the template's own default.

## Scope boundary

* Single file: `.github/workflows/ci.yml`. `build` is the last job; nothing else
  `needs:` it, so renaming the job id has zero downstream `needs` breakage.
* Out of scope (do not touch): the template `ci.yml.tmpl`; the local
  build-evidence gate wording in `.github/agents/.ship.agent.md` and
  `.github/instructions/github-pr-automation.instructions.md` (a different
  concept); `release.yml` "Build wheel and sdist" (unrelated packaging).
* `.autoharness/workspace-profile.yaml` records **no** `ci.required_check_name`
  field (only a generic `ci.pipeline_steps` list), so no profile edit is
  required.

## Verification expectation (for Ship)

After the rename, `.github/workflows/ci.yml` must remain valid YAML and preserve
behavior: the aggregation gate still runs with `if: always()` and
`needs: [changes, test]`, and fails only when a needed job is `failure` or
`cancelled` (a skipped `test` job remains OK).
