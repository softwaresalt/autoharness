---
title: "Release 1.4.4 Closure — Session Memory"
shipment: "037-S"
feature: "041-F"
version: "1.4.4"
merge_sha: "d37547430c6eefe5cff2576a70b3abb590024423"
tag: "v1.4.4"
pr: 94
pr_url: "https://github.com/softwaresalt/autoharness/pull/94"
release_url: "https://github.com/softwaresalt/autoharness/releases/tag/v1.4.4"
release_workflow_run: 26017396539
pypi_confirmed: true
date: "2026-05-18"
---

# Release 1.4.4 Closure — Session Memory

## Release Summary

autoharness **v1.4.4** was released on 2026-05-18.

| Artifact | Value |
|---|---|
| Merge SHA | `d37547430c6eefe5cff2576a70b3abb590024423` |
| Tag | `v1.4.4` |
| PR | [#94](https://github.com/softwaresalt/autoharness/pull/94) |
| Release | [v1.4.4](https://github.com/softwaresalt/autoharness/releases/tag/v1.4.4) |
| Workflow run | [26017396539](https://github.com/softwaresalt/autoharness/actions/runs/26017396539) |
| PyPI | `autoharness==1.4.4` confirmed at `05/18/2026 06:31:18 UTC` |

## Scope

This release covers changes merged since v1.4.3:

- **PR #90** — P-014 Copilot Review Merge Gate (§1.9 defense-in-depth pre-merge verification +
  §1.10 post-merge closure PR Copilot surveillance protocol). Added to `ship.agent.md`,
  `pr-lifecycle/SKILL.md.tmpl`, and `workflow-policies.md.tmpl`.
- **PR #91** — 036-S backlog reconciliation: corrected `035-S` archive frontmatter (status=shipped,
  commit SHA=38a6c77).
- **PR #93** — 036-S post-merge closure: archived 036-S shipment artifacts and session memory;
  corrected `archived_from` queue paths in frontmatter.

## Release Pipeline Execution (037-S / 041-F)

All tasks executed within a single Ship session:

| Task | Outcome |
|---|---|
| `041.002-T` — Version bump | Done. 1.4.3→1.4.4 across `pyproject.toml`, `__init__.py`, `plugin.json`, `marketplace.json`, `uv.lock` |
| `041.003-T` — CHANGELOG | Done. `## 1.4.4 - 2026-05-17` section authored and merged |
| `041.004-T` — Parity validation | Done. All four version surfaces confirmed at 1.4.4 |
| `041.005-T` — PR + P-014 + merge | Done. PR #94 merged via admin bypass (Ruleset PR-Required, bypass_actors: Admin). P-014 §1.9 gate passed: Copilot COMMENTED at HEAD `f0f5e45`, zero unresolved threads |
| `041.006-T` — Tag push + release workflow | Done. `v1.4.4` annotated tag pushed; release workflow run 26017396539 completed success; all 17 steps green |
| `041.007-T` — Post-release closure | This document |

## Key Decisions

### Admin Bypass for PR Merge

**Situation**: PR #94 had `mergeStateStatus: BLOCKED` / `reviewDecision: REVIEW_REQUIRED`. The
Copilot reviewer left a `COMMENTED` state (not `APPROVED`). Classic branch protection showed
`required_pull_request_reviews: null`, but a repository ruleset "PR-Required" (ID 14577755)
requires 1 approving review with `require_code_owner_review: true` and
`require_last_push_approval: true`.

**Resolution**: The ruleset `bypass_actors` includes role 5 (Admin) with `bypass_mode: pull_request`.
The `softwaresalt` account is the repo owner (Admin). P-014 §1.9 gate was fully verified (all 3
checks passed). With explicit operator approval, the merge proceeded via `gh pr merge --admin`.

**Learning**: When the GitHub classic branch protection API shows `null` for required reviews but
`mergeStateStatus` is still `BLOCKED`, always check rulesets via
`gh api repos/{owner}/{repo}/rulesets` — rulesets are the modern protection mechanism and
override classic protection. Admin bypass actors in rulesets use numeric role IDs (5=Admin).

### Ruleset Enforces Merge-Only

The "PR-Required" ruleset `allowed_merge_methods: ["merge"]` independently enforces P-009
(merge commits only). No squash or rebase is possible even if attempted.

### PyPI Trusted Publisher

The OIDC Trusted Publisher configured during 033-S continued to work without reconfiguration.
The release workflow `release.yml` triggers on `v*` tag pushes and uses the same environment
name — no token rotation or publisher update needed.

## Post-Release State

- Branch `chore/release-1.4.4` merged and can be deleted
- Shipment `037-S` shipped at merge SHA `d37547430c6eefe5cff2576a70b3abb590024423`
- Feature `041-F` and all 041.xxx-T tasks archived

## Next Steps / Follow-Up

- `035.001-T` (queued): Plan batching-rule guidance across Orchestrator/Ship follow-up flow —
  this is the next staged item for feature 035-F when 037-S fully closes.
- Future release prep: The Copilot "COMMENTED" review state does not satisfy branch-protection
  approval rules. Consider requesting a human review OR adjusting the ruleset to count Copilot
  COMMENTED reviews as approvals, to avoid needing admin bypass on every release PR.
