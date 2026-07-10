---
type: operational-closure
shipment: 083-S
feature: 071-F
task: 071.001-T
title: "Operational Closure — Rename Dogfood CI Aggregation Gate build to ci gate"
status: READY
merged_pr: 191
merge_commit: eb1b18217a31880c392f3e8c0658e2116d1d8af5
closed_at: 2026-07-10T09:33:00Z
doc_type: memory
source: docs/memory/083-S-closure.md
tags:
  - ci
  - github-actions
  - dogfood-parity
  - cleanup
  - closure
---

# Operational Closure — 083-S

## Shipment

Rename the always-running aggregation-gate job in the dogfood workflow
`.github/workflows/ci.yml` from job id `build` (`name: build`) to `ci-gate`
(`name: ci gate`), and rewrite the two comment blocks that justified the old
`build` name. Single-file, near-zero-risk dogfood correction.

Authority:

- `docs/decisions/2026-07-10-ci-gate-rename-decision.md`
- `docs/plans/2026-07-10-ci-gate-rename-plan.md`

## What shipped

- PR **#191** → merged to `main` as merge commit
  `eb1b18217a31880c392f3e8c0658e2116d1d8af5` (2 parents: `6fdb7c1` base +
  `501f854` head; P-009 merge-commit satisfied).
- `.github/workflows/ci.yml`: job id `build` → `ci-gate`; `name: build` →
  `name: ci gate`; header + inline comments rewritten to describe the
  aggregation gate without the obsolete deleted-ruleset rationale.
- Gate logic preserved exactly: `if: always()`, `needs: [changes, test]`, fails
  only on a needed job that is `failure`/`cancelled`; a skipped `test` job is OK.
- Template `templates/ci/ci.yml.tmpl` and the unrelated local build-evidence
  gate wording were left untouched (out of scope).

## Runtime verification (depth: trivial — workflow rename)

The change is a GitHub Actions workflow job rename. Its runtime surface is the
CI pipeline itself, which was exercised directly by PR #191:

- Actions run **29082926357** on head `501f854` reported all three jobs green:
  `detect code changes` = pass, `test` = pass, `ci gate` = pass.
- The renamed job reports under its new check name `ci gate` (not `build`),
  confirming the rename took effect end-to-end.
- Local: `PYTHONPATH=src python -m unittest discover -s tests` → `Ran 445 tests
  ... OK` (no test references the dogfood `.github/workflows/ci.yml`; only the
  template is under test).

## Releasability

**READY.** Behavior preserved, YAML valid, CI green under the new name, no
required-check dependency (no required status checks in the PR-Required ruleset).
No monitoring or rollback triggers apply to a comment/name rename. Rollback, if
ever needed, is a trivial revert of the single commit.

## Copilot review

One advisory thread (Copilot) on `.backlogit/queue/083-S.md` noting the shipment
was still `queued` at PR time and suggesting `claim_shipment` first. Declined as
an advisory process note (not a code defect): the PR's only implementation change
is the ci.yml rename; the committed `083-S.md` is the Stage-time planning
snapshot, and lifecycle transitions are handled by the P-015 single-artifact
closure after merge. Thread resolved.

## Backlog closure (P-015 single-artifact ops)

- `071.001-T` task: queued → active → done → archived.
- `071-F` feature: queued → active → done → archived.
- `083-S` shipment: queued → active → done → archived (never `shipment ship`).
- Cascade guard verified after each op: protected set (024/025/026/027/028/029/
  030/033-S shipped, 053-F + 053.004-T blocked, 065-F queued) remained intact.
- Backlog index resynced.

## Follow-ups

None. Local `main` remains diverged at `e2f6c2a` (harmless leftover from the
cherry-pick base, noted for later reconciliation).
