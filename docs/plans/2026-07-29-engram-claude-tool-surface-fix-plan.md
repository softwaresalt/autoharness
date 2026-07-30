---
title: Engram Available-Tools table + workflow correction in .claude/instructions.md
doc_type: plan
status: reviewed
created: 2026-07-29
source_stash_id: CBE3684E
prior_work: 036.005-T, 094-F (612f47d)
sibling_precedent: docs/plans/2026-07-29-engram-claude-instructions-transport-fix-plan.md
---

# Plan: Correct stale engram tool-surface table + workflow in `.claude/instructions.md`

## Problem

The `<!-- engram:start -->` block in `.claude/instructions.md` (the Claude Code
editor-local mirror) documents an **Engram** tool surface that has drifted from
the canonical protocol in `.github/instructions/agent-engram.instructions.md`:

- **Stale/legacy tool names** — the "Available Tools" table lists `create_task`
  (line 12), `update_task` (line 13), and `query_changes` (line 16). None of these
  are Engram tools: `create_task`/`update_task` are backlog-tool operations
  (backlogit owns task management in this workspace) and `query_changes` is not in
  the canonical Engram surface. Their presence mis-advertises Engram's capability
  and conflates it with the backlog tool.
- **Missing canonical tools** — the table omits `list_symbols`, `impact_analysis`,
  `sync_workspace`, `index_workspace`, and `query_graph`, all of which the
  canonical instruction lists as first-class Engram operations.
- **Workflow references the stale tools** — the "Recommended Workflow" section
  compounds the drift: step 3 ("Task management: Track all work items with
  `create_task` and `update_task`") and step 5 ("Change awareness: Use
  `query_changes`") point agents at non-Engram / non-existent tools.

This is the **distinct tool-surface follow-up** that the 094-F plan explicitly
deferred: "The same block still lists `create_task` / `update_task` /
`query_changes` ... a separate concern (tool-surface accuracy, not transport) ...
Flag for a follow-up stash entry." Stash `CBE3684E` is that follow-up.

## Ground-truth verification (done before planning)

- **Canonical surface** — `.github/instructions/agent-engram.instructions.md`
  (lines 22–26) enumerates the authoritative families:
  - lifecycle / status: `get_daemon_status`, `get_workspace_status`, `set_workspace`
  - indexing / freshness: `index_workspace`, `sync_workspace`, `flush_state`
  - semantic / contextual search: `unified_search`, `query_memory`
  - code graph lookup: `list_symbols`, `map_code`, `impact_analysis`
  - advanced read-only graph queries: `query_graph` (`query_graph_neighborhood`)
- **Drift confirmed** — `.claude/instructions.md` currently has 5 live stale-tool
  references (lines 12, 13, 16, 22, 24) and 0 references to the 5 missing canonical
  tools.
- **Transport already fixed** — line 4 was corrected to the stdio note by 094-F
  (commit `612f47d`, already merged to `main`). This plan touches lines 6–24 only,
  a **different section**, so there is **no live same-file conflict** with 094-F.
- **Not template-generated** — per the 094-F plan, no `.tmpl` generates
  `.claude/instructions.md`; it is hand-authored and repo-owned. The fix edits the
  file directly (no template change required). The canonical
  `.github/instructions/agent-engram.instructions.md` and its `.tmpl` are already
  correct and are NOT modified.

## Scope (width-isolated, single concern)

Single editor-local documentation file: `.claude/instructions.md`, engram block
only (lines 6–24). No schema, no CLI, no template, no base-harness change. One
concern: align the Claude Code mirror's Engram tool surface with the canonical
instruction. Blast radius is minimal.

## Fix

Replace the "Available Tools" table and reconcile the "Recommended Workflow" so
they reflect the canonical Engram surface. Implementer may refine wording but must
preserve intent and the canonical tool set. Suggested target:

**Available Tools** (drop `create_task`, `update_task`, `query_changes`; make the
full lifecycle check explicit — `get_daemon_status` + `get_workspace_status`
(required, not optional) alongside `set_workspace`; add the code-graph tools
`list_symbols`, `impact_analysis`, `query_graph`; add the full applicable indexing
surface `sync_workspace`, `index_workspace`, `flush_state`; retain `query_memory`,
`map_code`, `unified_search`):

| Tool | Purpose |
|------|---------|
| `get_daemon_status` | Confirm the Engram daemon / MCP surface is reachable (lifecycle check) |
| `get_workspace_status` | Verify workspace binding and index freshness (required binding verification) |
| `set_workspace` | Bind this workspace at session start (when explicit binding is required) |
| `query_memory` | Retrieve stored context, notes, and content records |
| `unified_search` | Broad semantic search across code, docs, and history |
| `list_symbols` | List symbols in a file or matching a concept |
| `map_code` | Explore callers, callees, and local graph context |
| `impact_analysis` | Assess blast radius before modifying a symbol |
| `query_graph` | Run advanced read-only graph queries |
| `sync_workspace` | Incremental index refresh when the workspace is stale |
| `index_workspace` | Full index rebuild when needed |
| `flush_state` | Flush pending index state when the workspace uses it |

**Recommended Workflow** — remove the `create_task`/`update_task` "Task
management" step and the `query_changes` "Change awareness" step (task management
is backlogit's job, not Engram's), and replace with Engram-appropriate steps:

1. **Session start**: confirm the daemon / MCP surface is reachable with
   `get_daemon_status`, verify binding and index freshness with
   `get_workspace_status`, and call `set_workspace` only if explicit binding is
   required.
2. **Context loading**: call `query_memory` / `unified_search` to retrieve prior
   context.
3. **Code exploration**: use `list_symbols`, `map_code`, and `impact_analysis`
   when navigating unfamiliar modules or assessing blast radius.
4. **Freshness**: run `sync_workspace` (or `index_workspace` for a full rebuild)
   when the index is stale, and use `flush_state` when the workspace requires a
   pending-state flush.

## P-006 plan-hardening assessment

**Requires plan hardening: no.** Blast radius is minimal — a single, repo-owned
documentation file; no schema change, no CLI/distribution surface, no multiple
template families, no base-harness contract. This mirrors the 094-F sibling
correction, which also concluded P-006 hardening was not required. `plan-harden`
is not invoked.

## Sequencing / related work

- **094-F** (`Engram .claude/instructions.md stdio-transport correction`) edits the
  same file's line 4 and is already merged to `main` (`612f47d`); its backlog
  feature is still `active` (backlog/commit drift, not this plan's concern). No
  hard dependency is required because the transport hunk is already landed and this
  plan touches a disjoint section. A `relates_to` lineage link is recorded for
  traceability (shared file/block, shared 036.005-T / 094-F correction lineage).

## Out of scope

- Any change to `.github/instructions/agent-engram.instructions.md` or its
  `.tmpl` (already canonical/correct).
- Any change to `copilot-instructions.md` (its engram table was corrected by
  `036.005-T`).
- Backlog-tool wiring: this plan does not add a backlogit task-management pointer;
  it only removes the incorrect Engram task-management claim. A backlogit pointer,
  if desired, is a separate documentation concern.

## Acceptance criteria

1. `.claude/instructions.md` "Available Tools" table contains no `create_task`,
   `update_task`, or `query_changes` entries.
2. The table makes the full lifecycle check explicit (`get_daemon_status`,
   `get_workspace_status`, `set_workspace`) and includes the full applicable
   indexing surface (`index_workspace`, `sync_workspace`, `flush_state`) plus the
   canonical code-graph / search tools (`list_symbols`, `map_code`,
   `impact_analysis`, `query_graph`, `query_memory`, `unified_search`).
   `get_workspace_status` is required binding verification, not optional.
3. The "Recommended Workflow" no longer instructs agents to use `create_task`,
   `update_task`, or `query_changes`; it references only canonical Engram tools and
   explicitly includes the lifecycle check (`get_daemon_status` +
   `get_workspace_status`) at session start and the full indexing surface
   (`sync_workspace` / `index_workspace` / `flush_state`) for freshness.
4. `grep -E 'create_task|update_task|query_changes' .claude/instructions.md`
   returns no matches.
5. The tool set is consistent with `.github/instructions/agent-engram.instructions.md`.
6. No other files modified. Markdown table/frontmatter remain valid (P-008 heading
   hierarchy unaffected; engram block markers preserved).

## Learnings applied (Step 1.8)

- **Sibling precedent 094-F** — same file, same width-isolated single-concern
  pattern, inline multi-persona review, P-006 not required.
- **`docs/compound/2026-05-05-agent-tool-list-completeness.md`** — tool lists must
  be cross-checked against the authoritative surface; stale/mismatched tool
  entries are a recurring defect class. Here the authoritative surface is the
  canonical Engram instruction.

## Plan review (multi-persona, inline — small doc fix, matches 094-F precedent)

- **Correctness reviewer**: target table/workflow match the canonical Engram
  surface in `.github/instructions/agent-engram.instructions.md`; the three stale
  tools are correctly removed; the five missing tools are added. PASS.
- **Scope / width-isolation reviewer**: single repo-owned doc file, single concern
  (Engram tool-surface accuracy); no schema/CLI/template coupling; task-management
  wiring correctly deferred. PASS.
- **Evidence-integrity reviewer**: canonical surface and current drift verified by
  grep/line inspection before planning; transport-hunk-already-merged confirmed via
  git log (`612f47d`); no stale assumptions carried from stash text. PASS.
- **Cross-reference reviewer**: referenced canonical instruction file and `.mcp.json`
  exist; engram block markers preserved; no dangling references introduced. PASS.

Outcome: **READY** — P0=0, P1=0. Cleared for harvest.
