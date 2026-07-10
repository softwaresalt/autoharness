# CI Required-Check Operator Guide

**Date:** 2026-07-10

**Status:** Active

**Target Repositories:** autoharness (and any workspace that installs the unified CI + local-gating primitive)

## 1. Purpose

The unified CI + local-gating primitive produces two enforcement surfaces:

* a remote GitHub Actions CI workflow whose **aggregation gate** job is the
  single status check intended to be *required* by a branch ruleset, and
* an opt-in cross-platform pre-push quality-gate hook (P-019) that shifts the
  fast-feedback gates left onto the contributor's machine.

The harness **produces the check and the guidance; it never edits branch
rulesets**. Adding, re-adding, or renaming a *required* status check is an
operator configuration action. This guide documents that contract so the
required-check wiring stays a deliberate, auditable operator decision.

## 2. The required-check contract

* The CI workflow's aggregation gate job runs with `if: always()`, `needs` all
  other jobs, and asserts every dependency succeeded or was legitimately
  skipped. It reports **success** even when the expensive test/build job is
  skipped (for example on a docs-only PR filtered out by the fail-closed
  `changes` job). This is why the aggregation gate — not the expensive job — is
  the correct required check: a required check that names a skippable job would
  block docs-only PRs forever.
* The aggregation gate's job `name:` is the value that a branch ruleset must
  require. In the autoharness dogfood instance that name is **`build`**.
* If a ruleset already requires a check by a specific name, set the workspace
  profile's `ci.required_check_name` (template variable
  `{{CI_REQUIRED_CHECK_NAME}}`) to that exact name so the produced check
  satisfies the existing requirement with **no ruleset edit**.

## 3. Operator action: re-adding the required check

When a branch ruleset should enforce the aggregation gate, an operator (not the
harness, not an automated agent) performs the configuration change:

1. Confirm the CI workflow is merged to the default branch and has produced at
   least one check run with the expected job name (readback the check name from
   a real PR before requiring it).
2. In the repository's branch ruleset (Settings → Rules → Rulesets), add a
   **Require status checks to pass** rule and select the aggregation gate check
   by its exact job name (e.g. `build`).
3. Save the ruleset. From that point the required check blocks merges until the
   aggregation gate reports success.

Renaming the required check later is the inverse operator action: update both
the workflow job `name:` (or the `ci.required_check_name` profile value) **and**
the ruleset entry so they continue to match. A mismatch silently blocks every
PR, because a ruleset can require a check that no workflow ever produces.

## 4. Why the harness does not automate ruleset edits

Editing a security-relevant branch ruleset to force a merge is explicitly out of
scope for the harness and its agents. The Ship agent must never reconfigure a
ruleset to unblock its own merge. Keeping required-check wiring as an operator
action preserves a clear human decision boundary around merge-gating
configuration.

## 5. Related policies and artifacts

* **P-019 — Local Pre-Push Quality-Gate Enforcement** (policy registry): the
  local, opt-in counterpart of the remote aggregation gate.
* **P-009 — Merge-commit-only**: governs how the merge itself is performed once
  the required check is satisfied.
* `templates/ci/ci.yml.tmpl` and `templates/ci/README.md`: the language-agnostic
  CI template and its operator-facing required-check contract section.
* `.github/workflows/ci.yml`: the autoharness dogfood instance whose aggregation
  gate job is named `build`.
