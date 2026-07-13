---
title: "Cross-Pack Measurability and Standardized Telemetry Session"
date: "2026-07-13"
description: "Deliberation framing for a future session with read access to capability-pack workspaces so autoharness can standardize logging and telemetry across engram, backlogit, graphtor-docs, and agent-intercom."
topic: "What read access and data contract are required to make capability-pack behavior fully measurable across workspaces?"
depth: "framing"
decision_status: "proposed"
doc_type: decision
source: docs/decisions/2026-07-13-cross-pack-measurability-telemetry-deliberation.md
source_stash_ids:
  - "83854CD2"
backlog_items:
  - "082-F"
linked_artifacts:
  - ".github/instructions/agent-engram.instructions.md"
  - ".github/instructions/graphtor-docs.instructions.md"
  - ".github/instructions/agent-intercom.instructions.md"
  - ".autoharness/backlog-registry.yaml"
  - "docs/decisions/2026-07-13-harness-telemetry-data-contract-deliberation.md"
tags:
  - "capability-packs"
  - "telemetry"
  - "logging"
  - "measurability"
  - "operator-access"
  - "primitive-7"
  - "operator-decision"
---

# Cross-Pack Measurability and Standardized Telemetry Session

## Status

**PROPOSED — blocked on operator-provided read access and data-contract direction.**
This session only had access to the autoharness repository and its local dogfood
artifacts. It did not have read access to all capability-pack source workspaces,
so it cannot verify their real logging surfaces, metric schemas, retention
policies, or integration constraints. This deliberation is linked to **079-F**
because both items depend on a standardized tool-telemetry contract candidate
that still requires operator ratification.

## Problem (stash 83854CD2)

The stash asks for a session with read access to all capability-pack workspaces so
standardized logging/telemetry can enable full measurability. The target packs are
at least:

* `agent-engram` — indexed search, code graph lookup, workspace binding,
  freshness, diagnostics, and token-savings reporting.
* `backlogit` — queue, item lifecycle, dependencies, shipments, comments,
  traceability, index freshness, and backlog telemetry surfaces.
* `graphtor-docs` — documentation source indexing, keyword/semantic search,
  doc-link traversal, source status, and ingestion health.
* `agent-intercom` — heartbeat, broadcasts, approval routing, standby/wait flows,
  and degraded-visibility signals.

Full measurability requires observing how each pack records operations, failures,
latency, routing decisions, fallbacks, and token-efficiency outcomes. That cannot
be inferred safely from autoharness templates alone.

## What standardized logging/telemetry would require

| Requirement | Why it matters |
|---|---|
| Shared event envelope | Every pack needs common fields for event ID, timestamp, workspace, session, agent role, phase, backlog item, git commit, and correlation IDs. |
| Pack-specific payload namespaces | Engram graph queries, backlogit lifecycle moves, graphtor indexing/search, and intercom approvals need different details without forking the whole schema. |
| Operation outcome taxonomy | Cross-pack reporting needs consistent `success`, `degraded`, `blocked`, `skipped`, `failed`, and `operator_required` outcomes. |
| Token-efficiency fields | Graph routing, doc retrieval, compression, and fallback avoidance should report input/output tokens, estimated savings, cache hits, and raw-search avoidance where available. |
| Health/freshness fields | Retrieval packs must report index freshness, stale state, source coverage, daemon/server health, and fallback reasons. |
| Safety/sensitivity fields | Logs must classify internal/public/ambiguous data, redaction state, and whether payloads may leave the local workspace. |
| Evidence paths | Local artifacts such as JSONL, SQLite, gate evidence, or pack-specific diagnostic reports need stable paths and retention rules. |
| Version metadata | Tool version, schema version, pack version, and workspace profile/manifest version are needed to compare measurements over time. |

## Access blocker

This AFK session does **not** have read access to the external capability-pack
workspaces. Without that access, Stage cannot answer:

1. What telemetry/logging already exists in each pack?
2. Which fields are reliable vs derived/estimated?
3. Which logs may contain sensitive data?
4. Which command/API surfaces can emit structured events without breaking existing
   users?
5. Whether pack-specific telemetry should be adapted in the pack repo or only in
   autoharness templates.

Because ambiguous sensitivity defaults to internal, this gap must not be filled
with public web searches or guesses.

## Relationship to 079-F

079-F sketches a **candidate** tool-telemetry data contract and narrows the
operator decision to schema shape, reporting/aggregation ownership, and whether
the existing agent-engram ingestion boundary remains authoritative. 082-F is the
evidence-gathering and coordination session needed to validate that candidate
against the actual pack implementations. The two should be planned together:

* 079-F recommends, but does not select, a candidate schema/ownership direction.
* 082-F gathers **pack-specific evidence and adapter requirements** to support or
  revise that candidate.

## Recommendation

Do not attempt implementation from the autoharness repo alone. First, the
operator should provide a read-only bundle or local paths for each capability-pack
workspace plus any existing docs/log samples that are safe to inspect. Then run a
bounded cross-pack telemetry spike that maps current surfaces to the 079-F
candidate contract and reports gaps before the operator ratifies any ownership
model.

## Operator Decision Required

The operator must decide **which external capability-pack workspaces may be read,
what telemetry/log content is safe to inspect, who should own reporting/
aggregation, and whether the recommended 079-F candidate contract should be
autoharness-owned, agent-engram-owned, backlogit-viewed, externalized, or split
across adapters**. The operator must provide the actual read access or artifacts;
this session cannot infer them safely.

## Open questions

1. Which exact repositories or local paths represent the authoritative pack
   workspaces for Engram, backlogit, graphtor-docs, and agent-intercom?
2. Are sample logs/telemetry records available, and may they be committed as
   sanitized fixtures?
3. Which pack already has a token-savings or health-report schema that should be
   preserved?
4. Should cross-pack telemetry be emitted by the packs directly, by autoharness
   wrapper/adapters, or by both?
5. What retention and redaction policy applies to intercom approval/broadcast
   events and retrieved document/code snippets?
6. How should cross-pack measurements be reported back to backlog items and PR
   readiness without making backlogit the telemetry owner?
