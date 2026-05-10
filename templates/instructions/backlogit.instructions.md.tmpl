---
description: "Backlogit workflow rules for query-driven lookup, explicit dependency wiring, checkpoints, and execution traceability"
applyTo: '**'
---

# Backlogit Instructions

Use these rules when the workspace enabled the `backlogit` capability pack. This pack deepens the
generic backlog integration with backlogit-native query, queue, dependency, continuity, and
traceability workflows.

## Required Tool Surface

The workspace should expose a backlogit-style tool surface for these behaviors when the registry
advertises them:

* **query / SQL lookup** — retrieve targeted backlog state without scanning many markdown files
* **queue view** — list ready or grouped work in execution order
* **dependency operations** — create, remove, and inspect explicit work dependencies
* **memory / checkpoint** — persist concise agent continuity state between sessions or phases
* **comments** — append operator- or agent-visible execution notes to a task
* **commit tracking** — associate commits with task IDs for traceability
* **sync / rehydrate** — refresh the query index after out-of-band edits
* **hook event polling** — check priority signals at session start when the registry advertises hook operations

Use the workspace's registered backlogit operation names or aliases. Do not invent a parallel task
tracking system when backlogit is available.

## Query-First Protocol

When inspecting backlog state:

1. Prefer targeted query operations over reading many `.backlogit/` markdown files directly.
2. Use direct item retrieval for current-state lookups.
3. Fall back to file reads only when the query surface cannot answer the question.

The goal is token-efficient lookup, not ritual compliance.

## Queue and Dependency Protocol

When selecting work or establishing execution order:

1. Prefer queue-aware operations for ready-work selection when supported.
2. Use explicit dependency operations to encode task ordering that truly matters.
3. Do not hide critical sequencing only in prose when the dependency graph can represent it.
4. Re-check unfinished dependencies before claiming a task that appears ready.

## Hook Signal Protocol

When hook event polling operations are supported:

1. Poll for unacknowledged hook events at session start before normal stash or shipment queue selection.
2. Treat returned hook events as higher-priority signals than raw queue scans.
3. Acknowledge only the highest processed concrete event sequence; never acknowledge derived signals.

## Intercom Coherence Rule

When the `backlogit` and `agent-intercom` capability packs are both enabled and
an agent is presenting queue, stash, or triage choices remotely:

1. Include item IDs, priority, kind or type, and a one-line summary in the
   broadcast.
2. Include the recommended ordering and the exact choice being requested.
3. Prefer self-contained broadcasts over "see chat above" summaries.

## Continuity Protocol

At meaningful boundaries such as task completion, review handoff, or session end:

1. Write the normal markdown memory artifact required by the harness.
2. When memory or checkpoint operations are supported, also persist a concise structured summary through backlogit.
3. Summaries should capture outcome, changed files or surfaces, decisions, blockers, and next steps.
4. Do not dump raw transcript logs into backlogit memory fields.

## Traceability Protocol

When work changes backlog state materially:

1. Append concise comments for notable outcomes, blocked conditions, or handoff notes when supported.
2. Associate commits with task IDs when commit-tracking is supported.
3. Keep comments focused on operationally relevant facts rather than verbose narration.

## Index Freshness Rule

If `.backlogit/` content was edited outside the usual backlogit mutation flow, refresh the index
before relying on query or queue output. Treat stale index results as suspect until rehydration completes.

## Data Ownership Rule

Treat backlogit's markdown files as the current-state source of truth, its query index as a
disposable cache, and its event or telemetry streams as append-only tool-managed history. Do not
edit generated cache artifacts directly.

## Stash Protocol

When stash operations are supported:

1. Use `fetch_stash` to list active stash entries, optionally filtering by `kind` or `priority`.
2. Use `stash` to add new intake items. Always set `kind` and `priority` at creation.
3. Use `stash_get` to inspect a single entry before triage decisions.
4. Use `stash_edit` to refine kind, priority, or text as understanding improves during triage.
5. Use `deliberate` to create a structured deliberation artifact from a stash entry before harvesting complex items.
6. Use `harvest_stash` to promote a stash entry into a work item (feature, task, or subtask). Set `parent_id` when the harvest target belongs under an existing feature.
7. Use `stash_archive` to retire consumed or obsolete entries. Prefer `stash_archive` over `stash_remove` — archiving preserves traceability; removal is destructive and deprecated.

## Semantic Links Protocol

When link operations are supported:

1. Use typed links (`add_link`, `remove_link`, `get_links`) for relationships that are informational — `related_to`, `duplicate_of`, `informs`, `supersedes`, `spike_ref`.
2. Use dependency operations (`add_dependency`, `remove_dependency`) for relationships that are execution-blocking — `blocks`, `relates_to`, `parent_of`.
3. Do not duplicate a dependency as a link or vice versa. Each relationship type has one home.
4. Note the naming similarity: `related_to` (link, informational) vs `relates_to` (dependency, execution-blocking). When in doubt, ask: "Does this relationship block execution?" If yes, use a dependency. If no, use a link.
5. Before creating a `duplicate_of` link, verify the entries are truly duplicates, not just related.
6. Use `get_links` to inspect existing relationships before adding new ones to avoid redundancy.

## Discovery & Introspection Protocol

When discovery operations are supported:

1. Use `get_metadata_catalog` to retrieve the full catalog of available metadata and configuration at session start.
2. Use `get_wit_metadata` to inspect field definitions, allowed values, and constraints for a specific artifact type before creating or updating items.
3. Use `list_types` to discover the set of artifact types the workspace supports.
4. Use `list_templates` to discover available artifact templates for structured creation.
5. Use `get_version` to confirm the backlogit version when diagnosing compatibility issues.
6. Use `export_command_map` to generate a human-readable command reference when onboarding or debugging.
7. Use `merge_sync` with `dry_run: true` to preview index drift before committing a full sync.

## Lifecycle Hygiene Protocol

When lifecycle and maintenance operations are supported:

1. Use `archive_item` to move completed or abandoned artifacts to the archive. Include `commit_sha` when archiving work that has a final commit for traceability.
2. Use `adopt_item` to re-parent orphaned tasks under the correct feature when hierarchy errors are detected.
3. Run `doctor` periodically (at session start or after bulk edits) to detect orphaned artifacts and duplicate IDs. Use `fix_orphans: true` only when confident the detected orphans should be archived.
4. Use `cleanup_checkpoints` to prune stale checkpoint files. Override `retention_days` only when the default is inappropriate.
5. Treat hygiene findings as first-class maintenance signals — address orphans and duplicates promptly rather than allowing them to accumulate.

Generated by autoharness | Template: backlogit.instructions.md.tmpl