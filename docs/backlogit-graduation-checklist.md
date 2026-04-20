---
title: "Backlogit graduation checklist"
description: "Checklist for deciding when backlogit's emerging two-agent workflow is ready to graduate into autoharness templates and capability-pack guidance."
ms.date: 2026-04-05
ms.topic: reference
keywords:
  - autoharness
  - backlogit
  - graduation
  - stage
  - ship
  - checklist
---

> **Navigation**: [README](../README.md) · [Getting Started](getting-started.md) · [Environment Setup](environment-setup.md) · [Primitives](primitives.md) · [Capability Packs](capability-packs.md) · [Tuning Guide](tuning-guide.md) · [Backlog Integration](backlog-integration.md) · [Credits](credits.md)

## Overview

Use this checklist to decide when backlogit-specific workflow surfaces are
ready to graduate into `autoharness` operating-model guidance, templates,
discovery, verification, and tuning logic.

Note: Stage and Ship agents are autoharness-native templates (Primitive 4:
Orchestration), not backlogit-originated surfaces. They do not need to
graduate from backlogit. This checklist covers the backlogit-specific surfaces
that those agents consume: shipment envelopes, stash storage, queue semantics,
and MCP/CLI tool contracts.

The default posture is conservative:

* backlogit can explore quickly
* autoharness promotes slowly

Promotion should happen only when the workflow is real, stable, and expressible
through the existing harness composition model.

## Graduation gate

Do **not** promote a backlogit-specific workflow surface into `autoharness`
until every required item below is complete.

## 1. Runtime implementation

- [x] Stage and Ship agent templates are implemented in autoharness and installed into backlogit as the primary two-agent workflow (autoharness-native; not a graduation item)
- [x] the current replacement path for legacy multi-agent flow is clear (legacy agents archived in backlogit AGENTS.md with superseded-by mapping)
- [x] shipment envelopes are implemented as stable lifecycle artifacts with finalized frontmatter schema and lifecycle states (shipment is a lifecycle envelope implemented as a first-class artifact type with suffix `S`, wrapping work items via `custom_fields.items`; 7 MCP tools and 6 CLI subcommands are production-quality)
- [ ] stash storage shape is finalized
- [ ] queue and status semantics for the new workflow are finalized

## 2. External contract clarity

- [ ] any new MCP tools have stable names and documented parameters
- [ ] any new CLI commands have stable names and documented behavior
- [ ] any new artifact types have stable frontmatter and lifecycle semantics (shipment envelopes are graduated — see §1)
- [ ] any new status values are represented in the metadata catalog and are intended to be durable (shipment uses standard statuses plus `archived`; shipment-specific lifecycle: queued → active → shipped/abandoned)
- [ ] autoharness can describe the new behavior in registry, discovery, and overlay terms without depending on backlogit-internal implementation details

## 3. Validation inside backlogit

- [ ] contract tests cover any new external tool surface
- [ ] integration tests cover the key handoffs in the new workflow
- [ ] end-to-end validation demonstrates the workflow on real backlogit work items
- [ ] failure handling is defined for blocked, partial, and rollback scenarios
- [ ] the team has used the workflow enough to identify at least the first round of operational rough edges

## 4. Documentation readiness

- [ ] backlogit docs describe the new workflow as the current stable path
- [ ] backlogit docs clearly mark any superseded workflow as legacy or transitional
- [ ] the migration or coexistence story between old and new workflow is documented
- [ ] durable design notes have been distilled out of session memory into stable docs where appropriate

## 5. Autoharness expression test

- [ ] workspace discovery can identify the new workflow through stable signals
- [ ] the backlog registry can represent the new stable operations and semantics
- [ ] the backlogit capability pack can express the behavior as overlay targets and behavior deltas
- [ ] verification checks can detect correct weaving of the new behavior
- [ ] tuning rules can detect stale, missing, or partially applied adoption

## 6. Promotion decision

Promote into `autoharness` only when all statements below are true:

- [ ] the new workflow is better than the current contract in a measurable way
- [ ] the benefits are durable, not artifacts of a short design window
- [ ] the promoted behavior will help target workspaces instead of exposing backlogit-specific churn
- [ ] there is a clear deprecation story for any old autoharness wording that becomes stale after promotion

## Promotion outputs

When the checklist is fully green, the expected `autoharness` updates are:

1. update [Backlogit Operating Model](backlogit-operating-model.md)
2. update [Backlogit Compatibility Matrix](backlogit-compatibility-matrix.md)
3. update the `backlogit` section in [Capability Packs](capability-packs.md)
4. update installation and tuning docs
5. update templates, verification checks, and tuning drift logic together

## Related docs

* [Backlogit Operating Model](backlogit-operating-model.md)
* [Backlogit Compatibility Matrix](backlogit-compatibility-matrix.md)
* [Capability Packs](capability-packs.md)
* [Tuning Guide](tuning-guide.md)