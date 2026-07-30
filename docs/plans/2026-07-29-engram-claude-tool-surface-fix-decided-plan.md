---
title: Engram Available-Tools table + workflow correction in .claude/instructions.md — decided plan
doc_type: decided-plan
status: shipped
created: 2026-07-29
feature: 099-F
task: 099.002-T
shipment: 104-S
source_stash_id: CBE3684E
prior_work: 036.005-T, 094-F (612f47d)
supersedes: docs/archive/plans/2026-07-29-engram-claude-tool-surface-fix-plan.md
---

# Decided Plan: Correct stale engram tool-surface table + workflow in `.claude/instructions.md`

**Outcome:** Shipped as feature `099-F` / task `099.002-T` / shipment `104-S`
(PR #263, merge commit `a560d1a`). Plan-review verdict: READY, P0 = 0, P1 = 0;
P-006 hardening not required. This decided-plan replaces the verbose original
(problem statement, ground-truth verification, full suggested table/workflow, and
inline four-persona review), archived for traceability at
`docs/archive/plans/2026-07-29-engram-claude-tool-surface-fix-plan.md`.

## Decision

Reconcile the `<!-- engram:start -->` block of `.claude/instructions.md` (the
Claude Code editor-local mirror) with the canonical Engram tool surface in
`.github/instructions/agent-engram.instructions.md`. Remove three non-Engram /
non-canonical entries and add the missing canonical families, editing the
hand-authored, repo-owned file directly (no `.tmpl` generates it; the canonical
instruction and its `.tmpl` are already correct and are NOT modified).

- **Remove** `create_task`, `update_task` (backlogit owns task management), and
  `query_changes` (not in the canonical Engram surface) from both the "Available
  Tools" table and the "Recommended Workflow".
- **Add** the full canonical surface: lifecycle (`get_daemon_status`,
  `get_workspace_status` — required binding verification, `set_workspace`),
  indexing (`index_workspace`, `sync_workspace`, `flush_state`), code-graph
  (`list_symbols`, `map_code`, `impact_analysis`, `query_graph`), search
  (`query_memory`, `unified_search`).
- **Rewrite** the "Recommended Workflow" to reference only canonical tools with an
  explicit session-start lifecycle check (`get_daemon_status` +
  `get_workspace_status`) and a freshness/indexing step
  (`sync_workspace`/`index_workspace`/`flush_state`).
- Preserve line 4 (stdio transport, corrected by 094-F/`612f47d`) and the
  `<!-- engram:start -->` / `<!-- engram:end -->` block markers.

## Scope (width-isolated, single concern)

Single editor-local documentation file, engram block only (lines 6–24). No schema,
CLI, template, or base-harness change. One concern: align the Claude Code mirror's
Engram tool surface with the canonical instruction. Minimal blast radius.

## Implementation (1 task — done)

| Task | Scope |
|---|---|
| 099.002-T | Edit `.claude/instructions.md` engram block: Available Tools table + Recommended Workflow reconciled to the canonical surface (size S; task-only manifest per the 097-S safe-close contract) |

## Acceptance criteria (all met)

1. "Available Tools" table contains no `create_task` / `update_task` /
   `query_changes` entries.
2. Table makes the full lifecycle check explicit (`get_daemon_status`,
   `get_workspace_status` required, `set_workspace`) and includes the full
   indexing surface (`index_workspace`, `sync_workspace`, `flush_state`) plus
   `list_symbols`, `map_code`, `impact_analysis`, `query_graph`, `query_memory`,
   `unified_search`.
3. "Recommended Workflow" references only canonical Engram tools with the explicit
   session-start lifecycle check and full freshness/indexing surface.
4. `grep -E 'create_task|update_task|query_changes' .claude/instructions.md`
   returns no matches.
5. Tool set consistent with `.github/instructions/agent-engram.instructions.md`.
6. No other files modified; Markdown table/frontmatter valid; engram block markers
   preserved (P-008 unaffected).

## Key constraints preserved

- **Canonical surface is authoritative** — the table/workflow are cross-checked
  against `.github/instructions/agent-engram.instructions.md`, not against the
  drifted mirror (compound `2026-05-05-agent-tool-list-completeness.md`).
- **No live same-file conflict with 094-F** — 094-F edits line 4 (transport,
  already merged `612f47d`); this fix edits the disjoint lines 6–24. A
  `relates_to` lineage link is recorded (shared file/block, shared 036.005-T /
  094-F lineage), not a hard dependency.
- **Required-minimum AC set** — AC #2 lists a required-minimum tool set, so the
  post-review additive `query_graph_neighborhood` row strengthens AC #5 fidelity
  rather than violating scope.

## Rejected / deferred alternatives

- **Add a backlogit task-management pointer** — deferred: this fix only removes the
  incorrect Engram task-management claim; adding a backlogit pointer is a separate
  documentation concern.
- **Modify `.github/instructions/agent-engram.instructions.md` or its `.tmpl`** —
  rejected: already canonical/correct; out of scope.
- **Modify `copilot-instructions.md`** — rejected: its engram table was corrected
  earlier by `036.005-T`.

## Post-review refinement folded in

Copilot shadow review on PR #263 flagged that the mirror omitted
`query_graph_neighborhood`, which the canonical search-protocol table (line 55,
tied to 033-S) lists as a first-class tool distinct from `query_graph`. Added the
row (commit `05f4b82`), replied with the fixing commit, and resolved the thread —
an additive superset fix consistent with the required-minimum AC #2.
