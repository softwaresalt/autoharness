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

Performed as **local backlogit single-artifact operations** (`backlogit move`),
consistent with this repo's established closure pattern: backlog queue→archive
relocations are kept as local backlog state and are not committed into the PR
diff (this closure PR commits only the memo). The repository state on `main`
therefore still shows the queue files until a later backlog-state reconciliation.

- `083-S` manifest `items`: `[071.001-T]` (single-task feature).
- `071.001-T` task (manifest item): queued → active → done → archived.
- `083-S` shipment record: queued → active → done → archived (never the cascade
  `shipment ship`).
- `071-F` feature: queued → active → done → archived. **Rationale:** 071-F has
  exactly one task, `071.001-T`, which is the shipment's sole manifest item, so
  the feature is *fully* shipped with **no unshipped siblings**. P-015's
  protected set is "the covering feature plus every **unshipped** sibling not in
  the manifest"; with zero unshipped siblings this is feature-complete closure,
  not the partial-feature parent-cascade P-015 guards against. The operator
  explicitly directed archiving the completed parent and defined the protected
  set to exclude 071-F.
- Cascade guard verified after each op: the protected set (024/025/026/027/028/
  029/030/033-S shipped, 053-F + 053.004-T blocked, 065-F queued) remained intact
  — no unshipped sibling or unrelated artifact was touched.
- Backlog index resynced.

## Follow-ups

1. **Reconcile local `main`** (owner: next Stage/Ship session on this
   workstation). Local `main` remains diverged at `e2f6c2a`, a harmless leftover
   from the cherry-pick base used to bring the 083-S planning commit into the PR.
   Fast-forward/reset local `main` to `origin/main` at a convenient point; no
   remote history is affected.
2. **Backlog-state reconciliation** (owner: next backlog-maintenance pass). The
   local queue→archive relocations for `071.001-T`/`071-F`/`083-S` live in local
   backlog state per this repo's closure pattern; a later pass may reconcile the
   committed `.backlogit/` tree with archived reality.
