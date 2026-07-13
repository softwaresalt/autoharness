---
title: "Harness Metrics, Reporting, Evals, and Tool-Telemetry Data Contract"
date: "2026-07-13"
description: "Deliberation on moving harness metrics/reporting/evals ownership out of backlogit, preserving backlog traceability, and sketching a standardized tool-telemetry data contract for tool usage and token-efficiency measurement."
topic: "Where should autoharness metrics, reporting, evals, and tool telemetry live, and what data contract should tools emit so token efficiency can be measured consistently?"
depth: "deliberation"
decision_status: "proposed"
doc_type: decision
source: docs/decisions/2026-07-13-harness-telemetry-data-contract-deliberation.md
source_stash_ids:
  - "6C5B3463"
backlog_items:
  - "079-F"
linked_artifacts:
  - "src/autoharness/telemetry/config.py"
  - "src/autoharness/telemetry/epoch.py"
  - "src/autoharness/telemetry/jsonl_sink.py"
  - "src/autoharness/telemetry/record.py"
  - "src/autoharness/telemetry/sqlite_sink.py"
  - "src/autoharness/eval/matrix.py"
  - "src/autoharness/eval/reviewer.py"
  - "src/autoharness/eval/runner.py"
  - "src/autoharness/eval/summary.py"
  - "docs/telemetry-reference.md"
  - "docs/design-docs/autoharness-evals-gates-design.md"
  - "docs/compound/2026-07-02-headless-eval-runner-deterministic-reviewer.md"
  - "docs/decisions/2026-07-13-cross-pack-measurability-telemetry-deliberation.md"
tags:
  - "telemetry"
  - "metrics"
  - "evals"
  - "backlogit"
  - "token-efficiency"
  - "primitive-7"
  - "operator-decision"
---

# Harness Metrics, Reporting, Evals, and Tool-Telemetry Data Contract

## Status

**PROPOSED — operator architecture decision required before implementation.** This
deliberation does not move metrics, reporting, or eval code. It records the
current telemetry boundary, the coupling question raised by the stash, and a
candidate data-contract shape. It is linked to **082-F**, which asks for a
cross-pack measurability session with read access to external capability-pack
workspaces.

## Problem (stash 6C5B3463)

The stash asks whether harness metrics, reporting, and evals should shift out of
backlogit, and asks for a tool-telemetry data contract that standardizes how
autoharness measures tool usage and token efficiency. This matters because
backlogit is the work-state system, but token economics and tool behavior cut
across agents, skills, capability packs, and CLI/runtime boundaries.

## Current state observed

This is **not greenfield**. The current autoharness implementation and design docs
already define several pieces of the telemetry/eval boundary, mostly independent
of backlogit:

* `src/autoharness/telemetry/epoch.py` defines an immutable `ExecutionEpoch`
  contract with four payload classes: `route`, `economics`, `operations`, and
  `outcome`.
* `config.py` loads an optional `telemetry` block. `mode: none` or an absent block
  disables telemetry; paths are resolved inside the workspace and fail open if
  they escape.
* `record.py` exposes `record_epoch` and the CLI-facing config loader. Sink
  failures are collected in a summary and never block completion.
* `sqlite_sink.py` writes one row per epoch to
  `.autoharness/metrics/execution_epochs.db` with columns for model, token, cost,
  duration, tool, gate, and blocked status.
* `jsonl_sink.py` appends one exact JSON object per line to
  `execution_epochs.jsonl` and explicitly stops at the file boundary: external
  ingestion is a later concern.
* `docs/telemetry-reference.md` documents this as a task-completion emission
  contract because autoharness is an install/tune tool, not an in-process model
  runtime.
* `src/autoharness/eval/` already exists (`matrix.py`, `reviewer.py`,
  `runner.py`, `summary.py`) and implements the headless eval/reviewer surface
  described by the Phase 2/Phase 3 work. The one-way **eval -> telemetry** flow
  is already established: eval can emit fail-open telemetry, while telemetry must
  not call back into eval.
* `docs/design-docs/autoharness-evals-gates-design.md` already assigns
  agent-engram/docline the structural-authority role: `engram verify <path>` (or
  docline verify) validates AST/frontmatter structure before graph ingestion, and
  agent-engram owns the CozoDB relational schema plus ingestion path that consumes
  autoharness-emitted ExecutionEpoch JSONL and links it to Task and Code nodes.

The remaining coupling is therefore more **workflow/data-ownership coupling**
than Python import coupling. Backlogit remains the source of work IDs, statuses,
shipments, dependencies, traceability, and queue state. Existing eval and
ExecutionEpoch capture are already present; the unresolved decision is narrower:
what cross-pack **tool-event** schema should sit below/alongside ExecutionEpoch,
who owns reporting/aggregation, and whether the existing agent-engram ingestion
boundary remains authoritative or is superseded.

## Options

### Option A — Keep metrics/reporting/evals inside backlogit

Backlogit would remain the source of truth for both work state and measured
execution outcomes.

* **Pros:** Simple operator mental model; every metric can be tied to a backlog
  item; backlogit already has queue/status/search surfaces.
* **Cons:** Turns a backlog tool into an observability/eval platform; creates
  product coupling for non-backlog metrics such as token efficiency, graph-route
  savings, compression ratios, and cross-pack health. Other tools would need to
  depend on backlogit semantics to report neutral telemetry.

### Option B — autoharness owns telemetry/evals; backlogit owns work state

Autoharness would continue defining its existing ExecutionEpoch/eval surfaces
and would additionally define a candidate tool-event schema plus reporting
adapters. Backlogit supplies IDs and links, but does not own metric storage or
evaluation logic.

* **Pros:** Matches current code direction; keeps metrics close to the harness
  primitives; lets non-backlog capability packs emit the same event contract.
* **Cons:** Requires a clear correlation contract so reports still explain which
  feature/task/shipment produced the evidence. Backlogit UIs would need adapters
  or links rather than embedded metrics.

### Option C — External observability store owns reporting

Autoharness would emit JSONL/SQLite locally, then an external tool (for example an
Engram-like analytics workspace or a data warehouse) ingests and reports.

* **Pros:** Scales across repositories and capability-pack workspaces; keeps
  runtime signals queryable outside the backlog.
* **Cons:** Requires operator-provided infrastructure, retention/privacy policy,
  and access. It cannot be completed in this AFK session.

### Option D — Hybrid contract + adapters

Autoharness would own the candidate contract and emitters pending operator
ratification. Backlogit, Engram, graphtor-docs, and agent-intercom could each
provide adapters or views that project the same event contract into their local UX
without owning the canonical schema.

* **Pros:** Separates source-of-truth responsibilities while preserving local UX;
  best path to cross-pack measurability.
* **Cons:** More coordination work and needs read access to those pack workspaces
  to avoid designing in a vacuum (see 082-F).

## Proposed tool-telemetry data-contract sketch

The existing `ExecutionEpoch` is a good **task-completion** record and already
has an agent-engram ingestion design. Tool-level measurability needs a more
granular candidate event stream that can roll up into epochs without replacing
the existing eval -> telemetry and JSONL -> agent-engram boundaries unless the
operator explicitly chooses to supersede them. A candidate v1 event shape:

| Field group | Candidate fields | Purpose |
|---|---|---|
| Identity/correlation | `schema_version`, `event_id`, `timestamp`, `workspace_id`, `repo`, `branch`, `commit_sha`, `session_id`, `agent_role`, `phase`, `backlog_item_id`, `shipment_id`, `parent_event_id` | Correlate a tool event to the work item, session, and git state without making backlogit the telemetry owner. |
| Tool invocation | `tool_surface` (`mcp`, `cli`, `shell`, `builtin`), `tool_name`, `operation`, `server_name`, `version`, `argv_shape` or safe command fingerprint, `cwd_scope` | Identify what was called while avoiding secret-bearing raw argv capture. |
| Timing/outcome | `start_time`, `end_time`, `duration_ms`, `status`, `exit_code`, `error_kind`, `retry_count`, `blocked`, `degraded_mode` | Measure reliability, latency, and failure modes. |
| Model/economics | `model`, `input_tokens`, `output_tokens`, `cached_input_tokens`, `cogs_usd`, `cumulative_context_input_tokens`, `transcript_tokens_before`, `transcript_tokens_after` | Extend current economics to support cumulative token-efficiency measurement. |
| Retrieval/routing | `retrieval_pack`, `route_kind`, `graph_route_used`, `raw_search_avoided`, `fallback_reason`, `stale_index`, `result_count` | Measure whether Engram/graphtor-docs routing actually replaced broad file search. |
| Compression/token savings | `compressor`, `content_type`, `raw_tokens`, `compressed_tokens`, `tokens_saved`, `ccr_ref_count`, `lossless_retrieval_verified`, `never_expand_applied` | Makes TokenMasterX/Brainspace-style ideas measurable if adopted. |
| Artifacts/gates | `artifacts_read`, `artifacts_written`, `gate_names`, `gate_exit_codes`, `evidence_path`, `policy_ids` | Link tool actions to validation and policy evidence. |
| Sensitivity | `sensitivity` (`public`, `internal`, `ambiguous`), `redaction_applied`, `secret_scan_status` | Prevent observability from becoming an exfiltration path. |

Candidate roll-up rule: **tool events compose into an `ExecutionEpoch`**, not
the other way around. Epochs remain the stable completion summary; tool events
provide detail for reports and token-efficiency analysis. The operator must decide
whether that roll-up feeds the existing agent-engram CozoDB ingestion path, a new
reporting store, backlogit views, or multiple adapters.

## Recommendation

Treat **Option D** as the recommended candidate, pending operator ratification:
autoharness would continue owning its existing ExecutionEpoch/eval emitters and
would propose the cross-pack tool-event contract; backlogit would remain the
canonical work-state and traceability tool; capability packs would expose adapters
or views as needed. This is a recommendation, not a decision. Do not move
implementation until the operator decides the cross-pack schema, reporting/
aggregation ownership, and whether the existing agent-engram ingestion boundary is
retained or superseded.

## Operator Decision Required

The operator must decide the **narrow remaining architecture questions**: the
cross-pack tool-event schema, reporting/aggregation ownership, and whether the
existing agent-engram ExecutionEpoch/CozoDB ingestion boundary is retained,
extended, or superseded. The operator must also ratify token-efficiency fields,
redaction/sensitivity rules, and whether backlogit is only a correlation source
or a reporting surface.

## Open questions

1. Should backlogit display metric summaries, or only link to autoharness-owned
   telemetry reports?
2. Which token metrics can the host reliably provide today, and which are estimates
   that must be labeled as such?
3. Is per-tool telemetry always emitted locally, or only during eval/staging/ship
   phases?
4. What redaction policy applies to command arguments and tool outputs?
5. Should `ExecutionEpoch` remain v1 while tool events get a separate schema, or
   should the epoch schema evolve to embed summarized tool-event metrics?
6. Does agent-engram remain the ingestion/reporting boundary for ExecutionEpoch and
   tool-event roll-ups, or should another reporting/aggregation owner supersede it?
7. What cross-pack fields are required by 082-F once external workspace evidence
   is available?
