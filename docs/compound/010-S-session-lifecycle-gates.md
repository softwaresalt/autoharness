---
problem_type: agent-workflow
category: session-lifecycle
root_cause: missing-deterministic-gate
tags: [backlogit, index-sync, merge-confirmation, session-gates, ship-agent, stage-agent]
shipment: 010-S
pr: 38
merged_at: "2026-05-07T01:53:32Z"
---

# 010-S: Session Lifecycle Gates and Backlogit Sync

## Problem

Stage and Ship agents had no deterministic gates for:
1. Index staleness at session start — agents could read stale backlogit index data
2. Merge confirmation before post-merge closure — agents could begin archival/graduation work before a PR was truly in `main`'s history
3. Closure index resync after mutations — archival operations left the index stale

## Solution

### Backlog Index Sync Gate (Step 0.1)

Added a `Step 0.1 — Backlog Index Sync` to both Stage and Ship agent templates.
It runs **after** Step 0.0 tool availability probes (lightweight checks) and
**before** any semantic backlog reads. Uses `{{OP_SYNC_INDEX_MCP}}` with
`{{OP_SYNC_INDEX_CLI}}` CLI fallback. Logs `INDEX_SYNC_OK` or `INDEX_SYNC_WARN`.

**Key wording lesson**: "Before any backlog reads" conflicts with Step 0.0 MCP
probes, which are themselves backlog reads. The correct framing is
"after tool probes, before semantic reads". Copilot review caught this ambiguity.

### Merge Confirmation Gate (NON-NEGOTIABLE)

Added before Ship Step 6.0 (post-merge branch protocol). Uses two sequential checks:
1. `gh pr view {pr_number} --json state,mergedAt,mergeCommit` — confirms `state == MERGED`
2. `git merge-base --is-ancestor {merge_sha} origin/{{DEFAULT_BRANCH}}` — confirms SHA in history

**Why `merge-base --is-ancestor` and not `git log --oneline -1`**: The tip check
only works if the merge is the latest commit. `merge-base --is-ancestor` checks
containment regardless of tip, which is correct when main has advanced.

### Closure DB Resync

Added as Ship Step 6 step 9 (after compact-context). Calls `{{OP_SYNC_INDEX_MCP}}`
after all archival mutations. Failure logs `CLOSURE_INDEX_SYNC_WARN` and gates the
broadcast behind `agent-intercom` pack (avoids invalid guidance when pack absent).

## verify_workspace Assertions Added

- `stage_index_sync_gate` → `PACK_ASSERTIONS["backlogit"]`
- `ship_index_sync_gate` → `PACK_ASSERTIONS["backlogit"]`
- `ship_merge_confirmation_gate` → `FOUNDATION_ASSERTIONS`

## Template Variables Added

- `{{OP_SYNC_INDEX_MCP}}` → resolves from `operations.sync_index.mcp_tool` (e.g., `backlogit_sync_index`)
- `{{OP_SYNC_INDEX_CLI}}` → resolves from `operations.sync_index.cli_command` (e.g., `backlogit sync`)
