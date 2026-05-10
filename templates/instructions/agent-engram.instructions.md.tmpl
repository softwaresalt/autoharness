---
description: "Agent-engram workflow rules for indexed search, workspace binding, code graph lookup, and freshness checks"
applyTo: '**'
---

# Agent-Engram Instructions

Use these rules when the workspace enabled the `agent-engram` capability pack. This pack is not a
generic search preference toggle. It weaves engram-first indexed retrieval and code-graph-aware
reasoning through the harness workflow.

## Required Tool Surface

The workspace should expose an engram-style tool surface for these behaviors:

* **lifecycle / status** — `get_daemon_status`, `get_workspace_status`, and `set_workspace` when binding is required
* **indexing / freshness** — `index_workspace`, `sync_workspace`, and, when used by the workspace, `flush_state`
* **semantic and contextual search** — `unified_search`, `query_memory`
* **code graph lookup** — `list_symbols`, `map_code`, `impact_analysis`
* **advanced read-only graph queries** — `query_graph`

Use the workspace's registered engram tool names or aliases. Do not bypass indexed lookup by
defaulting immediately to grep-heavy exploration.

## Workspace Lifecycle Protocol

Before relying on engram results:

1. Verify the daemon or MCP surface is reachable.
2. Verify the workspace is already bound.
3. If the daemon auto-binds the workspace, use `get_workspace_status` to verify the binding and do not call `set_workspace` again.
4. If the workspace is not bound and explicit binding is required, call `set_workspace` once with the repository root.
5. If the workspace is bound but not indexed or appears stale, run `index_workspace` or `sync_workspace` as appropriate.

Do not spam lifecycle calls on every trivial step. Check once per major workflow phase or when results appear wrong.

The daemon now handles OOM conditions and startup failures gracefully (034-S). Do not assume daemon failure from a single timeout — retry once before falling back to file-based tools.

## Search Protocol

Use the most specific engram tool first:

| Need | Preferred Tool |
|---|---|
| Broad discovery across code, docs, and history | `unified_search` |
| Search workspace memory, notes, or content records | `query_memory` |
| List symbols in a file or matching a concept | `list_symbols` |
| Understand callers, callees, and local graph context | `map_code` |
| Assess blast radius before modifying a symbol | `impact_analysis` |
| Run advanced read-only graph queries | `query_graph` |
| Traverse typed edges from a known node to explore local graph neighborhood | `query_graph_neighborhood` |

Prefer these before file-based fallback whenever the question is structural or conceptual.

Use `query_graph` for ad-hoc Cypher-style read-only queries across the full graph. Use `query_graph_neighborhood` for structured node-centric traversal when exploring typed edges from a known node (033-S). Prefer the neighborhood API when you have a specific starting node.

## Fallback Protocol

Fall back to grep, glob, or direct file reading only when:

* the engram daemon is unavailable
* the workspace is not yet bound or indexed
* the query is literal-text or regex oriented rather than symbol or concept oriented
* you already know the exact file path and need line-level source confirmation
* indexed results are insufficient even after using the most specific engram tool

If semantic search is unavailable, degraded, or returns a database / embedding failure, do not keep
retrying the same broad search. Fall back to `list_symbols` + `map_code` + `impact_analysis` for
the same discovery problem before broad raw-file scanning.

Engram now internally retries on SQLITE_BUSY (032-S). If you see a transient database error, retry
the operation once before falling back to grep — the internal retry may resolve the contention.

## Freshness Protocol

If code changed outside the expected indexing flow, or the daemon reports stale state:

1. Run `sync_workspace` for incremental refresh.
2. Use `index_workspace` only when a full rebuild is actually needed.
3. Treat stale results as suspect until freshness is restored.
4. If `sync_workspace` returns an error, check `get_health_report` before assuming the workspace is corrupted (032-S). Sync errors may indicate transient conditions rather than data loss.

## Data Ownership Rule

Treat `.engram/` artifacts as tool-managed state. Do not hand-edit generated registry, code-graph,
or cache artifacts as a substitute for lifecycle, indexing, or flush operations.

## Observability & Diagnostics Protocol

When observability tools are available, use them to verify workspace health before attributing
failures to query issues:

| Need | Preferred Tool |
|---|---|
| Workspace-level indexing coverage and stats | `get_workspace_statistics` |
| Daemon and workspace health diagnostics | `get_health_report` |
| Evaluation and quality metrics | `get_evaluation_report` |
| Per-branch indexing and activity metrics | `get_branch_metrics` |
| Token efficiency and savings data | `get_token_savings_report` |
| Retry and resilience metrics for mutable scripts | `get_mutable_script_retry_metrics` |
| Git blame and history indexing for attribution | `index_git_history` |

1. Prefer `get_health_report` for daemon troubleshooting; prefer `get_workspace_statistics` for indexing coverage gaps.
2. Use `get_evaluation_report` and `get_branch_metrics` to assess quality trends before and after major changes.
3. `index_git_history` is expensive — run it once per session when git attribution is needed, not on every query.
4. Use `get_token_savings_report` to verify engram is delivering token efficiency gains; investigate if savings are unexpectedly low.
5. Check `get_mutable_script_retry_metrics` when mutable script operations show intermittent failures.

Generated by autoharness | Template: agent-engram.instructions.md.tmpl