---
type: session-memory
agent: Ship
date: 2026-07-03
session: post-merge closure — 053-F Construct 1 model_routing frontmatter removal
shipment: 058-S
pr: 130
merge_commit: 04b8532825b04e0114e1b85273ff19eef22ad29c
tags: [ship, closure, backlogit, safe-close, cascade-guard, P-009, P-014, P-015, model-routing, construct1, partial-feature-shipment]
---

# Ship Session — 053-F Construct 1 `model_routing` Frontmatter Removal (058-S)

## Summary

Post-merge closure of shipment **058-S** — "053-F Construct 1: remove deprecated
`model_routing` frontmatter + carry-along 0CF1D6CF". Delivered via PR
[#130](https://github.com/softwaresalt/autoharness/pull/130), merged into `main`
as merge commit `04b8532825b04e0114e1b85273ff19eef22ad29c` on 2026-07-03 using a
**merge commit** (P-009: no squash, no rebase; merged with `--admin` because
branch protection reported `reviewDecision: REVIEW_REQUIRED` / `mergeStateStatus:
BLOCKED` and the operator had explicitly approved the merge).

This is a **partial-feature shipment**: it ships only the P-013-safe Construct 1
work under feature `053-F` and deliberately leaves the active Construct 2 config
binding for the deferred, operator-gated task `053.004-T`. Feature `053-F` stays
in the queue carrying that remaining scope.

## Construct distinction (why this is only part of 053-F)

`model_routing` is overloaded across two distinct constructs (per deliberation
`053.001-DL`):

| Construct | Meaning | This shipment |
|---|---|---|
| **C1** — per-agent frontmatter `model_routing:` string | Legacy/deprecated, superseded by integer `model_tier` | **Removed** |
| **C2** — config `model_routing:` object (tier→model binding in `.autoharness/config.yaml`) | Active, core to P-013 | **Preserved (untouched)** — deferred to `053.004-T` |
| **C3** — docs/spec/compound/memory references | Historical, C2-coupled | **Untouched** |

Construct 1 removal is safe because integer `model_tier` (+ `max_subagent_tier`)
already supersedes the deprecated string. Construct 2 removal is **not** safe
without a named replacement binding, so it remains blocked/operator-gated.

## What shipped (058-S manifest)

Manifest items `053.001-T`, `053.002-T`, `053.003-T` under covering feature
`053-F`:

- **053.001-T** — installed workflow agents (carry-along stash `0CF1D6CF`).
  `.github/agents/.ship.agent.md`, `.github/agents/.stage.agent.md`, and
  `.github/agents/_orchestrator.agent.md` backfilled with integer tier metadata
  (`model_tier` / `max_subagent_tier` / `reasoning_effort` / `model_provider` /
  `model_family`) and the deprecated `model_routing` frontmatter removed. The
  orchestrator body Model-Routing prose was aligned to Tier 3 (Frontier).
- **053.002-T** — agent templates (20 `templates/agents/*.agent.md.tmpl` and
  nested `review/`, `research/` templates): pure single-line frontmatter deletion
  of the deprecated `model_routing:` line. The Construct 2 config-example block and
  `config.model_routing.orchestrator` prose in `_orchestrator.agent.md.tmpl` were
  **preserved**.
- **053.003-T** — Construct-1 prose reconciliation:
  `templates/policies/workflow-policies.md.tmpl` (P-013.4) and
  `templates/skills/doc-review/SKILL.md.tmpl` (Check 6) dropped the deprecated
  `model_routing` string reference while retaining the `model_tier` /
  `max_subagent_tier` requirement.

## Carry-along agent-file edits and `.mcp.json` exclusion

- The three installed workflow-agent edits (`.ship`, `.stage`, `_orchestrator`)
  originated as operator-approved metadata drift in stash `0CF1D6CF` and were
  carried into 058-S as task `053.001-T`, keeping the installed agents in sync
  with their templates.
- A separate local stash `stash@{0}: On main: 058-S-mcp-env-drift` holds
  `.mcp.json` local environment drift. It was intentionally **excluded** from the
  shipment and from this closure. `.mcp.json` was **not** modified or committed at
  any point. The stash is left untouched for the operator.

## Review remediation carried by the PR

PR #130 commit chain (base `48b2e8f` → head `45c095b`):

- `64076d5` — remove C1 frontmatter from installed workflow agents (053.001-T).
- `4dba0c2` — remove C1 frontmatter from agent templates (053.002-T).
- `3ac38d0` — reconcile C1 prose in policy + doc-review (053.003-T).
- `639c39c` — record 058-S task state transitions in `.backlogit/`.
- `4414763` — **review P2 fix**: align installed orchestrator body tier prose with
  `model_tier: 3`.
- `45c095b` — **Copilot review fix (PR HEAD)**: restore Backlogit section markers
  (description / implementation-notes blocks) for the `053-F` / `053.004-T`
  artifacts flagged for structural-integrity. Both Copilot review threads
  (`.backlogit/queue/053-F.md`, `.backlogit/queue/053.004-T.md`) were **resolved**
  prior to merge.

## P-014 pre-merge gate (main PR)

Verified before merge: PR head `45c095b7fa59349a46abe085d07291277d9d596b` matched
the PR body `## Local Review Readiness` block; outcome `READY_WITH_FOLLOWUPS`;
blocking findings `P0=0, P1=0`; follow-up = `053.004-T` (deferred Construct 2
config-binding decision, operator-gated, tracked under active feature `053-F`);
shadow review not requested. `reviewDecision` was `REVIEW_REQUIRED` (branch
protection) — explicit operator approval + `--admin` used. **P-014 GATE PASSED.**

## Merge confirmation

- `gh pr view 130` → `state: MERGED`, `mergeCommit.oid:
  04b8532825b04e0114e1b85273ff19eef22ad29c`, `mergedBy: softwaresalt`.
- Merge commit has **two parents** (`33119b5` main + `45c095b7` PR head) —
  confirmed a real merge commit (P-009), not a squash/rebase.
- `git merge-base --is-ancestor 04b8532… origin/main` → exit 0.
- Local `main` fast-forwarded to the merge SHA (`--delete-branch` removed the PR
  head branch `chore/remove-model-routing-frontmatter` and switched to `main`).

## Closure method — safe-close (P-015), item-by-item, NO shipment ship

`backlogit shipment ship` (the cascade op) was **never** called. This is a
partial-feature shipment, so the **protected set = {`053-F`, `053.004-T`}** (the
covering feature plus its one unshipped, blocked sibling). Steps performed:

1. `backlogit sync` — index rehydrated (348 artifacts).
2. Baseline gate — `git status --short -- .backlogit/` clean; `053-F` and
   `053.004-T` present in `.backlogit/queue/` (`053.004-T` has `parent_id: 053-F`,
   status `blocked`), neither archived.
3. Manifest items — `053.001-T`, `053.002-T`, `053.003-T` were **already in
   `.backlogit/archive/`** (pre-archived by the merged PR content), so each was
   **classified `pre-archived` and skipped** per the safe-close exemption. No
   mutation; protected set verified still in queue.
4. Shipment record `058-S` closed as a single artifact:
   - `backlogit move 058-S --status done` (relocated queue → archive per registry
     routing).
   - `backlogit archive 058-S` (formalized; status `archived`).
   - `backlogit update 058-S --commit 04b8532…` (recorded merge SHA on the archived
     shipment record — `commit:` field now persisted).
   - Verify-after-each: `053-F` and `053.004-T` stayed in `.backlogit/queue/`,
     never in `.backlogit/archive/`.
5. P-007 archive integrity re-verify — manifest items + `058-S` all present under
   `.backlogit/archive/`; protected set present in `.backlogit/queue/`; no
   working-tree deletions in `.backlogit/archive/`.
6. `backlogit sync` — `CLOSURE_INDEX_SYNC_OK`.

`backlogit doctor` reported **no findings** for any `053` / `058` ID; only
pre-existing historical warnings on 003–046 (`archived_from_self_ref`) and 048
(`orphaned_artifact`), all unrelated to this closure.

**Protected-set result: `053-F` (blocked) and `053.004-T` (blocked) preserved in
the queue with the parent relation intact. No cascade.**

## Remaining / deferred work

- **053.004-T** — Construct 2 config-binding decision (rename vs
  remove-with-replacement vs keep) plus schema-version skew reconciliation.
  **Blocked / operator-gated.** Feature `053-F` remains active in the queue
  carrying this scope; it is intentionally **not** archived.

## Compound learning

None created. The hard-won lessons (partial-feature safe-close prevents cascade;
C1 vs C2 `model_routing` overloading; deferring the active binding to an
operator-gated task) are already captured by policy **P-015**, the
`shipment-reconcile` safe-close mode, Ship agent Step 5, deliberation
`053.001-DL`, and the prior 056-S / 057-S closure memories. Session memory is
sufficient.

## Notes / state

- Local stash `stash@{0}: On main: 058-S-mcp-env-drift` left **untouched** (never
  popped/applied/dropped). `.mcp.json` was not touched or committed.
- This closure is delivered as a **separate PR** from `chore/close-058s`; per
  P-014 it is **not merged** and requires separate explicit operator approval.
