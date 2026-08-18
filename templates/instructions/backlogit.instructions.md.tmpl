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

1. Prefer targeted query operations over reading many `.backlog/` markdown files directly (`.backlog` is the default for new installs; legacy `.backlogit/` remains supported. When no valid `BACKLOGIT_WORKSPACE_DIR` override resolves the root, both roots present at once must fail closed until the operator resolves the ambiguity; a valid override resolves the root per precedence and is not itself an ambiguity).
2. Use direct item retrieval for current-state lookups.
3. Fall back to file reads only when the query surface cannot answer the question.

The goal is token-efficient lookup, not ritual compliance.

## Queue and Dependency Protocol

When selecting work or establishing execution order:

1. Prefer queue-aware operations for ready-work selection when supported.
2. Use explicit dependency operations to encode task ordering that truly matters.
3. Do not hide critical sequencing only in prose when the dependency graph can represent it.
4. Re-check unfinished dependencies before claiming a task that appears ready.

## Shipment Sequencing Protocol

When parcelling a chosen or calculated sequence of shipments — for example an
Orchestrator working a multi-shipment dark run one shipment at a time — reuse the
`queue view` + `item_deps` primitives rather than a standalone scheduler or a
sequence-manifest file. This protocol builds directly on the Queue and Dependency
Protocol above.

* **Select the next *eligible* shipment (execution)**: run
  `queue view --type shipment --status queued` as a first-pass filter. It returns
  **all** queued shipments in execution order (`custom_fields.queue_position`
  first, then priority); there is no separate shipment `blocked` status in
  backlogit 1.8.0. Then **re-check the candidate's `item_deps` + status before
  claiming** — per "Re-check unfinished dependencies before claiming" in the
  Queue and Dependency Protocol — rather than trusting the query alone: a stale or
  non-filtering `queue view` could surface a successor early. A queued shipment is
  only ELIGIBLE for claim once every `blocks`-type predecessor it depends on has
  reached `shipped`; if any predecessor remains unmet, skip/withhold the
  candidate. This matches the Ship agent's own readiness rule that treats unmet
  `dependencies` as blocking eligibility through `dependencies`, not through a
  shipment `blocked` status.
* **Reconstruct the full ordered sequence (scope / audit / resume)**: because
  every dependency-gated successor stays `status: queued` from creation and none
  are hidden behind a separate `blocked` status, a single `queue view --type
  shipment --status queued` (or an unfiltered shipment listing) already surfaces
  the complete candidate set. Traverse the `item_deps` blocks-edges across that
  set to rebuild the ordered sequence and its restart cursor, then evaluate which
  queued successors are currently eligible by checking whether all blocking
  predecessors have reached `shipped`. This is the ordered scope P-017 records as
  `DARK_MODE_SCOPE` resume/audit evidence.
* **Chain shipments into a self-enforcing sequence**: express ordering that must
  gate execution with `dep add <next-shipment> <prev-shipment> --type blocks`, so
  `<next-shipment>` cannot be claimed until `<prev-shipment>` has shipped.
* **Re-evaluate queued successors after each predecessor ships (required)**: once
  `<prev-shipment>` reaches `shipped`, its `blocks` edge is satisfied and every
  queued successor that depends on it becomes eligible on the very next explicit
  eligibility check. The closing owner — Ship's post-merge closure, or the
  Orchestrator immediately before its next queue selection — MUST simply
  re-evaluate queued successors against their `blocks` edges; no shipment-status
  mutation is performed or required. This is the supported backlogit 1.8.0 model
  documented in `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`
  and ratified by 109.019-T.
* **Honor `custom_fields.queue_position`** for explicit manual ordering among
  eligible shipments; set it when you need a deterministic order that priority
  alone does not express.
* **`dep_type` collapse note**: `dep_type` collapses to `blocks` on
  sync/rehydrate, so author sequencing edges with `--type blocks` explicitly and
  do not rely on other dependency types surviving a sync.
* **Reconciliation — queued shipment status + `item_deps` blocks-chain**: the
  `item_deps` blocks-edge is the sole dependency-gate mechanism. Shipment `status`
  only ever holds `queued`, `active`, `shipped`, or `abandoned`, and eligibility
  is computed as `status == "queued"` **and** every `blocks`-type predecessor
  is `status == "shipped"`. Use the blocks-edge to encode ordering and to audit
  which predecessor gated a queued successor; do not model dependency gating with
  a separate shipment `blocked` status. (Consistent with the Semantic Links vs
  Dependencies guidance below — `blocks` is an execution-blocking dependency, not
  an informational link.)

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
2. When memory or checkpoint operations are supported, also persist a concise structured summary through backlogit, conforming to the Checkpoint Payload Contract below.
3. Summaries should capture outcome, changed files or surfaces, decisions, blockers, and next steps.
4. Do not dump raw transcript logs into backlogit memory fields.

### Checkpoint Payload Contract

Applies to backlogit structured checkpoints only. The markdown `docs/memory/`
continuity artifact is a separate mechanism and takes no `schema_version`.

A backlogit structured checkpoint payload MUST:

1. declare `"schema_version": 1` as a top-level field — without it backlogit
   skips V1 validation and auto-population entirely and writes the payload
   through unvalidated;
2. be written through the official create operation — MCP
   `backlogit_create_checkpoint` (`state_dump`) or CLI
   `backlogit checkpoint create --state-dump` — never by writing a file into
   the checkpoints directory directly;
3. carry `agent` (`stage` or `ship`), `session_id`, `phase`, and a
   `resume_hint` specific enough to support a later recovery decision;
4. nest all domain data (feature/shipment/stash IDs, artifact paths, branch
   state, completed/blocked items, mode, route) inside the `context` object —
   these MUST NOT be hoisted to the top level;
5. rely on backlogit to populate `created_at`, `updated_at`, and `status`,
   which it does only when rule 1 is satisfied.

```json
{
  "schema_version": 1,
  "agent": "stage",
  "session_id": "stage-2026-08-17-example",
  "phase": "harvest",
  "resume_hint": "Harvest complete; next step is shipment assembly.",
  "context": {
    "feature_id": "130-F",
    "shipment_id": "139-S",
    "artifacts": { "plan": "docs/plans/example-plan.md" }
  }
}
```

## Traceability Protocol

When work changes backlog state materially:

1. Append concise comments for notable outcomes, blocked conditions, or handoff notes when supported.
2. Associate commits with task IDs when commit-tracking is supported.
3. Keep comments focused on operationally relevant facts rather than verbose narration.

## Index Freshness Rule

If `.backlog/` or legacy `.backlogit/` content was edited outside the usual backlogit mutation flow (and if both roots are present with no valid `BACKLOGIT_WORKSPACE_DIR` override resolving the root, fail closed until the operator resolves the ambiguity), refresh the index
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

## Checkpoint-Recovery / Prune-on-Restore Protocol

This section defines the bounded context-pruning behavior an owning agent (Stage or Ship)
applies when it restores a checkpoint it has been explicitly operator-confirmed to resume
(see each owner agent template's Crash-Resumption / Startup Recovery Protocol, and the
Orchestrator's owner-exclusive routing in its own template). It reuses the existing
backlogit checkpoint API and the existing context-efficiency / P-020 compaction substrate —
it does not introduce a new checkpoint-schema field or a new runtime engine.

**Applicability — engram-pack-conditioned, not a backlogit-only blocker**: this
prune-on-restore step applies only when the `agent-engram` capability pack is
installed/active in this workspace (there is a bound context substrate to prune). When
`agent-engram` is NOT installed, prune-on-restore is a supported, non-degraded no-op:
skip directly from restore to resume (restore → resume, no prune/gate step) — a
backlogit-only installation is never forced to halt at pruning, because a package with
no engram pack has no engram-bound state to summarize in the first place. This static
configuration fact (`agent-engram` not installed) is distinct from the runtime-failure
case in point 4 below (`agent-engram` IS installed but unreachable at the moment of
restore), which fails closed to operator handoff.

1. **Bounded read-select-summarize on restore**: the owner sequence is
   restore → prune/gate → resume, never restore → resume → prune. After the operator
   explicitly confirms and the checkpoint's `state_dump` is loaded (restore), but BEFORE
   execution resumes, read the restored `state_dump` and any bound engram state, then
   produce a bounded summary of that state rather than replaying the full
   action-observation history verbatim. Prune-on-restore drops ONLY superseded
   action-observation history — turns and tool traces that have already been synthesized
   into the recorded state and are no longer needed to continue the work. Only after this
   prune/gate step completes (or is explicitly not needed, per the Applicability note
   above) does the owning agent resume execution from the recorded phase.
2. **Prune allowlist (never prune)**: the following are NEVER pruned, regardless of how old
   or verbose the surrounding history is:
   * the active-shipment / active-task cursor (the single-active resumption point),
   * the unresolved-checkpoint pointer itself (the checkpoint being resumed),
   * recorded gate verdicts (quality gates, review verdicts, CI/PR gate outcomes).
   These three classes of state are safety-critical to resuming correctly and must survive
   pruning intact.
3. **Ties to the existing context-efficiency / P-020 substrate**: prune-on-restore is a
   restore-time application of the same context-efficiency discipline used elsewhere in the
   harness (session memory checkpoints, `compact-context`, P-020 compaction). It does not
   invent a separate pruning engine, schema, or storage surface.
4. **Degraded fallback — `agent-engram` installed but unreachable at restore**: when the
   `agent-engram` capability pack IS installed/active, and the bound engram substrate is
   unreachable when attempting to read state for pruning, FAIL CLOSED to OPERATOR HANDOFF —
   NO prune and NO resume. This is a single, unambiguous behavior: a bounded file-based prune
   degradation is NOT used, because it was never proven safe and explicitly non-resuming.
   Whenever a required, installed substrate (backlogit OR an installed `agent-engram`) is
   unavailable, the crash-resumption protocol fails closed to operator handoff rather than
   attempting a speculative degraded prune or a speculative resume. This mirrors the
   Tool-Availability-Gate (P-012) and `ENGRAM_DEGRADED` fallback patterns used elsewhere in
   the harness, and it is distinct from the supported backlogit-only no-prune path in the
   Applicability note above, which is never a degraded or fail-closed condition.
5. **No unresolved placeholders**: any workspace-specific customization point in this section
   resolves fully at install time — installed output must never retain an unresolved template
   variable placeholder — and the protocol stays technology-agnostic (no provider or binary
   hardcoding).

## Lifecycle Hygiene Protocol

When lifecycle and maintenance operations are supported:

1. Use `archive_item` to move completed or abandoned artifacts to the archive. Include `commit_sha` when archiving work that has a final commit for traceability.
2. Use `adopt_item` to re-parent orphaned tasks under the correct feature when hierarchy errors are detected.
3. Run `doctor` periodically (at session start or after bulk edits) to detect orphaned artifacts and duplicate IDs. Use `fix_orphans: true` only when confident the detected orphans should be archived.
4. **Use `cleanup_checkpoints` to prune stale checkpoint files, but ONLY after every active checkpoint has reached ACTUAL resolution or an explicit separate archival/abandonment decision — a fail-closed operator handoff is NEITHER and does NOT satisfy this gate.** `cleanup_checkpoints` (retention-based) archives checkpoints that are either resolved OR merely older than the retention cutoff — including still-`active` records. A fail-closed operator handoff, by design, performs NO resolve and deliberately leaves the checkpoint `active`/unresolved so the recovery candidate is preserved for the next session; treating handoff as sufficient disposition would let `cleanup_checkpoints` archive that exact checkpoint immediately afterward purely for being old, erasing the unresolved state the handoff existed to protect. Require, for every checkpoint returned by the owner-scoped ZERO-CANDIDATE / EXPLICIT-OPERATOR-SELECTION enumeration, ONE of: (a) `status: resolved` via `resolve_checkpoint` after a confirmed successful resume, or (b) a separate, explicit, named operator decision to archive or abandon that specific checkpoint (distinct from, and never implied by, a fail-closed handoff) — BEFORE invoking `cleanup_checkpoints` against that same checkpoint population. A checkpoint left in the `active`/unresolved state by a fail-closed handoff MUST remain excluded from `cleanup_checkpoints` eligibility regardless of its age until one of these two explicit dispositions occurs. Override `retention_days` only when the default is inappropriate.
5. Treat hygiene findings as first-class maintenance signals — address orphans and duplicates promptly rather than allowing them to accumulate.

Generated by autoharness | Template: backlogit.instructions.md.tmpl