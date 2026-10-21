---
title: "Backlogit compatibility matrix"
description: "Compatibility matrix describing which backlogit surfaces autoharness can consume now, which require validation, and which are still incubating."
ms.date: 2026-04-05
ms.topic: reference
keywords:
  - autoharness
  - backlogit
  - compatibility
  - operating model
  - capability packs
---

> **Navigation**: [README](../README.md) · [Getting Started](getting-started.md) · [Installation](installation.md) · [Environment Setup](environment-setup.md) · [Primitives](primitives.md) · [Capability Packs](capability-packs.md) · [Tuning Guide](tuning-guide.md) · [Backlog Integration](backlog-integration.md) · [Credits](credits.md)

## Overview

This matrix describes compatibility between `autoharness` and `backlogit` at the
contract level.

Compatibility is currently **contract-based, not version-number-based**. The key
question is not whether two repositories happen to be updated on the same day.
The key question is whether a backlogit surface is stable enough to be consumed
by `autoharness` discovery, registry mapping, capability-pack weaving,
verification, and tuning.

Use this matrix together with:

* [Backlogit Operating Model](backlogit-operating-model.md)
* [Backlogit Graduation Checklist](backlogit-graduation-checklist.md)
* [Capability Packs](capability-packs.md)

## Compatibility states

| State | Meaning |
|---|---|
| **Compatible now** | Safe for autoharness to consume and teach through templates, overlays, and tuning |
| **Compatible with validation** | Safe only when the workspace actually exposes the feature and autoharness verifies it explicitly |
| **Incubating** | Keep in backlogit until implementation and validation are complete |

## Current matrix

| Backlogit surface | Current state | How autoharness should use it | Notes |
|---|---|---|---|
| Backlogit detection through workspace markers | Compatible now | Use for workspace discovery and backlog tool selection | Backed by directory, config, and MCP or CLI detection |
| Registry-backed CRUD operations | Compatible now | Use through the generic backlog abstraction | Core interoperability layer |
| Declared MCP and CLI operation surfaces | Compatible now | Treat each declared surface as an equal supported surface per operation (P-012); report `TOOL_OK: {operation} via {mcp\|cli}` | Hook poll and ack declare `backlogit hooks poll` / `backlogit hooks ack`; `log_telemetry` stays MCP-only |
| Backlogit engine line v1.11.0 (cascade engine semantics) | Compatible now | Verified line `1.11` for P-015 `CASCADE`; see [Engine-Line Verification](engine-line-verification.md) | Verified against `archive.go` at `v1.11.0`; `ci.yml` pins backlogit v1.9.0 for its structural checks, and the pin tests do not require a newer pin (no `ci.yml` change) |
| Backlogit engine line HEAD v1.11.0-829-ga623b0af | Incubating | Treat as unverified; closes select `SAFE_CLOSE`. A development build cannot qualify even if the runbook comparison passes; only a future released line can | Changed areas: `archive.go` item-log lock ordering and CAS stash effects, `shipment.go`, `queue.go` shipped-only readiness (188-S) |
| Shipment dispose (`backlogit_dispose_shipment` / `backlogit shipment dispose`) | Incubating | Do not register; deferred until backlogit 194-F ships, then Stage-only (backlogit condition G-B) | Not implemented in backlogit 1.11.0 or HEAD |
| Queue view shipment `blocks` release (188-S) | Compatible with validation | The backlogit HEAD queue view releases a shipment `blocks` edge only when the predecessor is `shipped`; the Orchestrator keeps the queue listing as a first filter with `pre_claim` as the sole authority | Hides blocked shipments earlier than backlogit 1.11; no queue-selection wording change |
| SQL query surface | Compatible with validation | Prefer for targeted backlog lookup when the pack is enabled and the tool is reachable | Must verify MCP or CLI availability first |
| YAML frontmatter tooling coverage | Compatible now | Use to teach when MCP-backed updates are enough and when direct Markdown edits plus index refresh are required | Stable because it documents both supported fields and known gaps such as `custom_fields` and post-create `references` |
| Queue-aware work selection | Compatible with validation | Use for ready-work and sequencing guidance | Requires queue operations to be reachable and trustworthy |
| Dependency operations | Compatible with validation | Use for explicit ordering rather than prose-only sequencing | Should be expressed through registry and instructions |
| Memory and checkpoints | Compatible with validation | Use for continuity summaries in addition to harness markdown memory | Only when the advertised operations are available |
| Comments and telemetry | Compatible with validation | Use for operational traceability and handoff notes | Comments should stay concise and factual |
| Commit tracking | Compatible with validation | Use to associate commits with work items | Stable value when the workspace wants deeper traceability |
| Metadata catalog and command map | Compatible now | Use for agent discovery and tool-surface introspection | Strong bridge between backlogit runtime and autoharness templates |
| Source artifact cleanup via `custom_fields.source_*` | Compatible with validation | Use only in backlogit-specific ship/closure guidance when the metadata contract and cleanup tools are reachable | Prefer explicit source IDs over heuristic stale-artifact searches |
| Current multi-agent backlogit workflow | Compatible now | Use as the reference operating model for deep backlogit guidance | Safe because it reflects today's working backlogit workflow |
| Stage and Ship two-agent workflow | Compatible now | Stage and Ship are autoharness-native agent templates (`_stage.agent.md.tmpl`, `_ship.agent.md.tmpl`) installed into target workspaces; backlogit is the first consumer | Not a backlogit graduation item — these originate from autoharness Primitive 4 (Orchestration) |
| Shipment lifecycle envelope | Compatible now | Shipment type suffix (`S`), ID format, `custom_fields.items` grouping, 7 MCP tools, and 6 CLI subcommands are proven and production-quality; consume through the backlogit capability pack and registry | Stable artifact type, status lifecycle (`queued → active → shipped/abandoned`) plus archive move, with claim-blocking gates expressed through `item_deps` `blocks` edges while a successor remains `queued`, and full CRUD+lifecycle MCP/CLI surface |
| Four-stage stash → backlog → shipment → shipped pipeline | Compatible now | Pipeline is implemented: Stage owns stash-to-backlog, Ship owns backlog-to-shipped, shipments are the lifecycle envelope | Stash storage shape (Markdown vs JSONL) is the remaining incubating question |
| Stash JSONL source of truth | Incubating | Do not assume in autoharness discovery or instructions yet | Current stable stash guidance remains the active contract |
| New internal file naming conventions tied to the two-agent workflow | Incubating | Do not hardcode in templates yet | Must survive backlogit implementation and migration decisions |

## How to use this matrix

### For template authors

If a surface is **Compatible now**, it can appear in:

* generated instructions
* capability-pack deltas
* verification checks
* tuner drift logic

If a surface is **Compatible with validation**, it can appear only when:

* the workspace advertises the capability
* the pack is enabled where required
* the generated harness checks reachability before depending on it

If a surface is **Incubating**, keep it out of generated template behavior and
record it only in durable architecture docs such as the operating-model and
graduation-checklist documents.

### For tuner work

The tuner should treat the matrix as an adoption boundary:

* recommend stable backlogit-native behaviors when missing
* verify conditional behaviors when present
* monitor incubating workflow changes, but do not auto-promote them

### For future promotion

When an incubating surface becomes real in backlogit, reclassify it only after
it passes the checks in [Backlogit Graduation Checklist](backlogit-graduation-checklist.md).