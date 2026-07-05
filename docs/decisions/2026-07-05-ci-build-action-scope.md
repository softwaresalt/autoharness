---
title: "CI Build Action Scope for Non-Code PRs"
description: "Decision for stash 8DBD43A1: avoid adding or modifying build actions because the repository has no tracked pull-request build workflow; preserve future guidance for code-relevant PR filters."
topic: "Should autoharness add paths-ignore or PR-title build skipping now?"
depth: "standard"
decision_status: "accepted"
doc_type: decision
source: docs/decisions/2026-07-05-ci-build-action-scope.md
source_stash_ids:
  - "8DBD43A1"
backlog_items:
  - "063-F"
  - "063.001-T"
  - "073-S"
linked_artifacts:
  - ".github/workflows/release.yml"
tags:
  - "ci"
  - "github-actions"
  - "build-minutes"
  - "pr-readiness"
---

# CI Build Action Scope for Non-Code PRs

## Decision

Do not add `paths-ignore`, PR-title conditions, or a new pull-request build
workflow in this slice.

The only tracked GitHub Actions workflow is `.github/workflows/release.yml`, and
it runs only for version tag pushes. There is no tracked `pull_request` build
workflow currently consuming build minutes for documentation-only, backlog-only,
or chore-only PRs. Adding a new PR workflow to demonstrate skip behavior would
increase Actions usage, which is the opposite of stash `8DBD43A1`.

## Future Rule

If a tracked PR build workflow is added later, expensive build/test/package jobs
should be gated conservatively:

1. Run for source, tests, templates, schemas, packaging, release, and workflow
   changes.
2. Allow documentation-only or backlog-only PRs to skip expensive build jobs.
3. Treat PR-title conditions such as `chore:` or `docs:` as advisory only; path
   impact must remain the safer source of truth.
4. Keep lightweight safety checks available when expensive build jobs are skipped.

## Verification

The repository was checked for tracked workflow triggers and build commands. The
tracked workflow surface contains only the release workflow, and the release
workflow is tag-scoped rather than PR-scoped.
