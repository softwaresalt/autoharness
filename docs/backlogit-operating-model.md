---
title: "Backlogit operating model"
description: "Defines the stable backlogit contract autoharness can consume now and the promotion criteria for future workflow changes."
ms.date: 2026-04-05
ms.topic: concept
keywords:
  - autoharness
  - backlogit
  - operating model
  - capability packs
  - workflow
  - compatibility
---

## Overview

`backlogit` is the flagship first-party backlog backend for `autoharness`, but
it is not the only backlog shape the harness framework supports. This document
defines the current stable operating contract between the two repositories and
the graduation rule for pulling newer backlogit workflow ideas into
`autoharness` templates.

The short version is simple:

* `backlogit` incubates workflow changes inside its own repository
* `autoharness` consumes only the stable external contract
* promotion happens after validation, not during exploration

## Stable contract to consume now

`autoharness` can safely lean on the backlogit surface that is already stable,
documented, and wired through the existing capability-pack overlay.

| Surface | Stable today | Current use in autoharness |
|---|---|---|
| MCP and CLI presence | Yes | discovery and registry resolution |
| Query-driven lookup | Yes | token-efficient backlog state inspection |
| Queue-aware work selection | Yes | ready-work and sequencing guidance |
| Dependency operations | Yes | explicit ordering and graph reasoning |
| Memory and checkpoints | Yes | continuity at task and session boundaries |
| Comments and telemetry | Yes | traceability and operational notes |
| Commit tracking | Yes | task-to-commit linkage |
| Metadata catalog and command map | Yes | agent discovery and workflow introspection |
| Current backlogit multi-agent workflow | Yes | reference operating model for deep backlogit guidance |

These are the capabilities that the `backlogit` capability pack should continue
to deepen through:

* foundation docs
* backlogit-specific instructions
* backlog-aware agents
* tuning and verification checks

## Incubating workflow that should remain in backlogit for now

The next-generation backlogit workflow is the emerging two-agent design captured
in the backlogit repository's session memory and related planning artifacts.

That design currently includes:

* a `groomer` agent for deliberate → plan → review → harvest flow
* a `shipper` agent for harness → build → review → CI → PR lifecycle flow
* a four-stage storage pipeline: stash → backlog → shipment → shipped
* shipment artifacts that group one branch and one pull request
* possible stash migration from markdown to JSONL

This direction is promising, but it is not yet ready to become template truth in
`autoharness`.

Until backlogit proves that workflow in its own repository, `autoharness`
should **not** hardcode:

* `groomer` or `shipper` agent names
* shipment artifact assumptions
* stash JSONL assumptions
* new file naming rules that are still part of backlogit's internal refactor
* phase choreography that depends on unshipped backlogit behavior

## Promotion criteria

Backlogit workflow changes graduate into `autoharness` only when they satisfy
all of these conditions:

1. The behavior exists in backlogit as implemented runtime or artifact logic.
2. The external contract is clear.
   * stable MCP tool names or CLI commands
   * stable artifact types or status semantics
   * stable metadata catalog representation
3. The workflow is validated end to end inside backlogit.
4. The change can be expressed through the existing autoharness model:
   * discovery signals
   * backlog registry mappings
   * capability-pack behavior deltas
   * verification checks
   * tuning drift rules
5. The change improves the installed harness without forcing backlogit-specific
   engine internals onto non-backlogit workspaces.

If any of those are missing, keep the behavior in backlogit and continue to
monitor it there.

## Guidance for template authors

When editing backlog-aware templates in `autoharness`:

* use the registry abstraction first
* use the `backlogit` capability pack only for proven backlogit-native behavior
* document future backlogit workflow directions here, not inside generated
  template text
* prefer feature detection and verification checks over optimistic assumptions

Template authors should think in two layers:

* **generic backlog layer**: create, list, get, move, complete, archive
* **backlogit deep layer**: query, queue, dependencies, memory, checkpoints,
  comments, commit traceability, metadata discovery

The future two-agent workflow belongs to the deep layer only after it stops
being experimental.

## Guidance for tuning

The tuner should monitor backlogit evolution without forcing immediate adoption.

Good tuner actions include:

* detect when backlogit capabilities are available but unused by the harness
* recommend stronger backlogit-native guidance when stable features expand
* flag stale wording if the stable backlogit contract changes
* propose future adoption of a proven operating-model upgrade once backlogit has
  validated it

Bad tuner actions include:

* rewriting installed harnesses to use speculative agent names or unproven
  artifact flows
* treating backlogit's in-progress internal refactor as an already-stable public
  contract

## Current operating-model decision

Today, the right reference operating model is:

* keep `autoharness` and `backlogit` separate
* ship them as a first-party integrated stack when teams want the full experience
* let backlogit continue incubating the two-agent workflow internally
* pull that workflow into `autoharness` only after backlogit proves it

This keeps `autoharness` broadly useful while still letting backlogit act as the
highest-leverage operational backend for teams that want the full stack.

## Related docs

* [Capability Packs](capability-packs.md)
* [Backlogit Compatibility Matrix](backlogit-compatibility-matrix.md)
* [Backlogit Graduation Checklist](backlogit-graduation-checklist.md)
* [Installation Guide](installation-guide.md)
* [The 10 Irreducible Harness Primitives](primitives.md)
* [Tuning Guide](tuning-guide.md)

For the incubating workflow itself, see the backlogit repository's design and
memory artifacts that track the two-agent refactor.