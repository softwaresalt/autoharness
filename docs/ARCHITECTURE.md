---
title: Architecture
description: High-level autoharness architecture and ownership boundaries.
---

# Architecture

## Product Boundary

autoharness is a globally installed agent harness framework. It is operated from an autoharness home that contains templates, schemas, instructions, skills, policies, prompts, and documentation. Target workspaces receive generated harness artifacts and workspace-local state only.

## Telemetry Ownership

autoharness owns the local epoch time-series telemetry contract, local SQLite/JSONL sinks, reader normalization, aggregation formulas, report helpers, and eval-facing summary inputs. It records immutable `ExecutionEpoch v1.1` snapshots at task-close boundaries and reports over those persisted epochs.

backlogit owns backlog traceability: work item IDs, statuses, dependencies, comments, shipment manifests, task-level planned `size`, and computed-on-read hierarchy or shipment composition. autoharness snapshots those facts once at pre-execution via `WorkSizingSnapshot`; it does not become the backlog source of truth.

agent-engram remains the structural/graph ingestion consumer. It may ingest emitted epoch JSONL or roll-ups, but `src/autoharness/telemetry/` must not import agent-engram, CozoDB, eval, gates, install/tune, `verify_workspace`, or `schema_contracts`.

## Execution Lifecycle

Ship captures a pre-execution context using `autoharness telemetry begin` immediately after task claim and before implementation. The context carries a stable epoch ID, correlation fields, and optional `WorkSizingSnapshot`. At close, Ship records with `autoharness telemetry record --context-ref`, preserving the same epoch ID and context digest while adding close-time roll-up metrics.

## Boundaries and Deferrals

`ToolTelemetryEvent v1.0` is a forward-only contract. Live event model/sink/emission and deterministic event-to-epoch composition are deferred to 084-F if needed. 082-F maps real capability-pack evidence before broad adapter implementation, and 085-F builds benchmark suites on the stable telemetry inputs.
