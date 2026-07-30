---
shipment: 104-S
feature: 099-F
task: 099.002-T
feature_pr: 263
merge_commit: a560d1a3b6054129897b112d2f77a1266720ec54
merged_at: "2026-07-30T06:40:29Z"
reviewed_head: 05f4b828d27bf8c81cc376b8bab3d8efadc4cd80
closure_status: READY
compaction_status: done
---

# 104-S / 099-F Post-Merge Closure — Engram tool-surface correction in `.claude/instructions.md`

Shipment 104-S reconciled the `<!-- engram:start -->` block of
`.claude/instructions.md` (Available Tools table + Recommended Workflow) with the
canonical Engram tool surface in
`.github/instructions/agent-engram.instructions.md`. Documentation-content change;
no template, schema, CLI, or runtime-behavior change.

## Merge Confirmation

- PR #263 merged to `main` at `2026-07-30T06:40:29Z` with merge commit
  `a560d1a3b6054129897b112d2f77a1266720ec54`.
- The merge commit has **two parents** (`852ca37d…` base + `05f4b828d…` feature
  HEAD), preserving the P-009 merge-commit strategy (squash/rebase disabled at the
  repo level).
- Merge SHA confirmed as ancestor of `origin/main`; `.claude/instructions.md` change
  verified on `origin/main` (stale-tool grep returns no matches;
  `query_graph_neighborhood` present). Closure began from synced `main` at `a560d1a`.

## Review & Gate Outcomes

| Gate | Result |
| --- | --- |
| Reviewed HEAD | `05f4b828d27bf8c81cc376b8bab3d8efadc4cd80` (== PR HEAD at merge) |
| Local review (multi-persona inline) | **READY** — P0=0, P1=0 |
| §1.9 pre-merge readiness (Checks 1–5) | **PASS** (HEAD coverage, outcome, follow-ups, build N/A, P-018) |
| P-018 copilot-review gate | **SATISFIED** (exit 0, 0 unresolved threads; re-run unconditionally pre-merge) |
| Copilot shadow review | 1 thread (`query_graph_neighborhood`) — fixed in `05f4b82`, replied, resolved |
| CI (`ci gate`, `detect code changes`, `test`) | all **pass**; mergeState CLEAN |
| Review-fix cycles | 1 / 3 · Fix-CI cycles: 0 / 5 (no circuit breaker hit) |

## Runtime Verification

**Surface**: the only runtime surface in `runtime_validation.validator_manifest` is
`cli`. This change edits a documentation mirror file only — zero runtime blast
radius (no CLI, schema, template, or behavior change).

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | CLI (command) |
| Runtime probe | `uv run autoharness --help` |
| Result | **PASS** — exit 0, CLI help printed (stdout + exit-code evidence) |
| Manual checkpoints | none defined |
| Blocked prerequisites | none |
| Release blocker (`CLI help smoke check fails`) | NOT triggered |
| Verdict | **PASS** (meets `minimum_verdict: PASS`) |

No unsupported automation was fabricated.

## Backlog Reconciliation (single-artifact safe-close, P-015 / 097-S)

Safe-close used per-item / single-artifact operations only. The cascade command
`backlogit shipment ship 104-S` was **not** run.

| Item | Final state |
| --- | --- |
| `099.002-T` (manifest task) | pre-archived on merged `main` (v1.7.0 archives on `move --status done`); manifest-item skip applied; status `done` |
| `104-S` (shipment record) | moved `done` → **archived** as a single artifact (`backlogit archive 104-S`) |
| `099-F` (covering feature — **protected set**) | **preserved in `.backlogit/queue/` — NOT cascaded** |

- **Protected set = {`099-F`}**: `099.002-T` is the only task under `099-F`; no
  unshipped sibling tasks exist. Verify-after-each (`git status -- .backlogit/`) and
  the P-007 post re-verify confirmed `099-F` remained in queue and no archive
  deletions occurred after every mutation.
- `backlogit sync` completed after archive operations (589 artifacts). No
  `.backlogit/config.yaml` churn appeared.

## Context Compaction (P-020)

- **Status: `done`** (bounded Tier-1 per-release-unit post-merge floor).
- Invoked `compact-context` (target: all). Assessment: `docs/memory` = 53 files
  (> 40 file-count threshold; 180 KB < 500 KB size threshold), `docs/plans`,
  `docs/closure`.
- **Action taken**: consolidated this release unit's memory. The verbose Stage
  original `docs/memory/104-S-stage-session.md` was archived to
  `docs/archive/memory/104-S-stage-session.md`, and the dense per-release-unit
  summary was written to
  `docs/memory/compacted/2026-07-30-104S-099F-compacted.md` (traceable path
  preserved). No active-work checkpoints were compacted (none active).
- **Scope discipline**: the broad `docs/memory` over-threshold sweep is a **separate
  deferred stash entry `5F14396E`** (recorded by Stage: "run at next Ship P-020
  closure **or a dedicated pass**"). It is out of shipment 104-S's scope; this
  closure performed only the bounded per-release-unit floor and defers the full
  date-bucketed sweep to a dedicated compaction pass.

## Operational Closure

- **Healthy signals**:
  - Feature PR #263 merged with a merge commit (two parents; P-009 preserved).
  - Local review READY (P0=0/P1=0); §1.9 all-checks PASS; P-018 SATISFIED.
  - CI green at the merge gate; CLI smoke probe PASS.
  - Backlog safe-close archived task + shipment without the forbidden cascade;
    covering feature `099-F` preserved.
- **Failure signals to watch**:
  - Any future re-introduction of `create_task` / `update_task` / `query_changes`
    into the engram block (guard: AC#4 grep).
  - Future shipment manifests listing a covering feature inside
    `custom_fields.items` (must remain task-ID-only per the 097-S contract).
  - Divergence between `.claude/instructions.md` and the canonical
    `agent-engram.instructions.md` tool surface.
- **Releasability** (`runtime_validation.releasability.required: false`,
  `status_when_satisfied: READY`): monitoring N/A (no runtime behavior change);
  rollback = revert merge commit `a560d1a` (single doc change; no state migration);
  validation window = immediate post-merge on 2026-07-30 after `main` synced to
  `a560d1a`; owner = Ship agent (closure evidence), operator `@softwaresalt` (merge
  approval). **Releasability: READY.**
- **Follow-ups**:
  - Deferred stash `5F14396E` — broad `docs/memory` compaction (dedicated pass).
  - Backlog drift — stuck-active features `094-F` / `095-F` / `097-F` (zero active
    tasks, zero in-flight PRs; Stage-side hygiene).
  - External stash `6D6CACC1` — backlogit internals; route upstream.
  - Ship did not create any stash/backlog items for these (stash + backlog creation
    are forbidden by the Ship role boundary, P-010); routed to Stage/Orchestrator.

**Closure verdict: READY.** Merge confirmed (P-009 preserved), local review + §1.9 +
P-018 gates passed, runtime probe PASS, single-artifact safe-close complete with the
protected feature `099-F` intact, and P-020 context compaction status recorded as
`done`.
