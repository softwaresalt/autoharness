---
title: Backlog Integration
description: How autoharness detects, abstracts, and integrates structured backlog tools into the installed harness
---

> **Navigation**: [README](../README.md) · [Getting Started](getting-started.md) · [Environment Setup](environment-setup.md) · [Primitives](primitives.md) · [Capability Packs](capability-packs.md) · [Tuning Guide](tuning-guide.md) · [Backlog Integration](backlog-integration.md) · [Credits](credits.md)

## Why a Structured Backlog Tool Matters

A structured backlog tool is essential for effective agent harness operation. Agents need a machine-queryable work queue to pull tasks from, track status transitions, and manage decomposition hierarchies. Without one, agents cannot reliably sequence work, preserve task context across sessions, or enforce workflow policies like single-release-unit completion (P-001).

autoharness supports pluggable backlog tools through a registry abstraction layer that keeps agent templates tool-agnostic while resolving to tool-specific operations at install time.

## Supported Tools

| Tool | Runtime | Directory | Transport | Key Differentiators |
|------|---------|-----------|-----------|---------------------|
| **backlogit** | Go binary | `.backlogit/` | MCP (stdio) + CLI | SQL query engine, telemetry, memory/checkpoints, sections |
| **backlog-md** | Node.js (npm) | `backlog/` | MCP (stdio) + CLI | Milestones, documents, Definition of Done, workflow guides |

## How Detection and Registry Abstraction Works

1. **Detection**: The workspace-discovery skill scans for backlog tool markers (config files, directories, MCP registrations)
2. **Registry**: A pre-built registry YAML maps abstract operations (create, list, update, move) to the tool's specific MCP tool names and CLI commands
3. **Abstraction**: All agent templates reference abstract operations (`{{OP_CREATE_MCP}}`, `{{STATUS_QUEUED}}`), which are resolved to tool-specific values during installation
4. **Migration**: The Auto-Tune agent detects tool switches and generates migration proposals that update all harness references

Pre-built registries live in `templates/backlog/registries/` inside the autoharness installation:
- `backlogit.registry.yaml`
- `backlog-md.registry.yaml`

## Manual Registration

If autoharness does not detect your backlog tool, or you use a custom tool, you can register it manually by creating `.autoharness/backlog-registry.yaml` following the schema in `schemas/backlog-tool-registry.schema.json`.

The registry file maps:
- **MCP tool names** — the exact tool names your backlog MCP server exposes
- **CLI commands** — fallback CLI equivalents for each operation
- **Status values** — how your tool represents queued, in-progress, done, blocked, etc.
- **Field names** — the field identifiers for title, description, parent, priority, etc.

## Backlogit Capability Pack

When the `backlogit` capability pack is enabled, autoharness layers backlogit-native guidance on top of the generic backlog abstraction. This includes SQL query access, prioritized queue retrieval, dependency traversal, agent memory, checkpoints, comments, and commit traceability.

See the following guides for the current first-party backlogit contract:

- **[Backlogit Operating Model](backlogit-operating-model.md)** — Defines what autoharness can consume now and the promotion criteria for future workflow changes
- **[Backlogit Compatibility Matrix](backlogit-compatibility-matrix.md)** — Which backlogit surfaces are stable, which require validation, and which are still incubating
- **[Backlogit Graduation Checklist](backlogit-graduation-checklist.md)** — When backlogit's emerging workflow is ready to graduate into autoharness templates

## Next Steps

- **[Getting Started](getting-started.md)** — Install a harness with backlog integration
- **[Capability Packs](capability-packs.md)** — Full overlay pattern and pack catalog
- **[Tuning Guide](tuning-guide.md)** — How the tuner detects backlog tool changes
