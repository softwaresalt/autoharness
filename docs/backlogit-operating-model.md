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

> **Navigation**: [README](../README.md) · [Getting Started](getting-started.md) · [Environment Setup](environment-setup.md) · [Primitives](primitives.md) · [Capability Packs](capability-packs.md) · [Tuning Guide](tuning-guide.md) · [Backlog Integration](backlog-integration.md) · [Credits](credits.md)

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
| SQL schema reference and read-only cache usage | Yes | targeted `SELECT` lookup guidance through `backlogit_query_sql` |
| Dependency operations | Yes | explicit ordering and graph reasoning |
| Memory and checkpoints | Yes | continuity at task and session boundaries |
| Comments and telemetry | Yes | traceability and operational notes |
| Commit tracking | Yes | task-to-commit linkage |
| Metadata catalog and command map | Yes | agent discovery and workflow introspection |
| YAML frontmatter and tooling coverage | Yes | deciding when MCP updates are sufficient and when direct Markdown edits plus index refresh are required |
| Shipment lifecycle envelopes | Yes | release grouping, claim/ship lifecycle, and commit traceability through 7 MCP tools and 6 CLI subcommands |
| Source artifact cleanup via `source_stash_id` / `source_deliberation_id` | Yes | backlogit-specific ship and closure guidance can retire consumed source artifacts without heuristic backlog sweeps |
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

* a **Stage** agent for deliberate → plan → review → harvest flow
* a **Ship** agent for harness → build → review → CI → PR lifecycle flow
* a four-stage storage pipeline: stash → backlog → shipment → shipped
* shipment envelopes that group one branch and one pull request around existing work items
* possible stash migration from markdown to JSONL

Stage and Ship are **autoharness-native agent templates** (`stage.agent.md.tmpl`
and `ship.agent.md.tmpl`) that implement Primitive 4 (Orchestration). They are
not backlogit-originated workflow surfaces that need to graduate into
autoharness — the dependency runs the other direction. Backlogit is the first
target workspace to consume these templates.

The earlier design notes used the names "groomer" and "shipper". The stable
names are **Stage** and **Ship**.

### Shipment design decision: lifecycle envelope

Shipment is a **lifecycle envelope**, not implementable work. It groups one or
more existing backlog work items together with a branch and pull request to
track their journey from claimed to shipped. Despite being a lifecycle envelope
conceptually, shipment is implemented as a first-class artifact type in
backlogit's type system with its own suffix (`S`), ID format (`NNN-S`), and
file in `.backlogit/queue/`.

Concrete shape (from real backlogit shipments):

Active shipment (in `queue/`):

```yaml
---
artifact_type: shipment
id: 014-S
status: done
title: Stash Lifecycle & Hygiene
custom_fields:
    items:
        - 030-F
        - 030.001-T
        - 030.002-T
created_at: 2026-04-12T19:14:53Z
updated_at: 2026-04-12T19:52:22Z
---
```

Archived shipment (moved to `archive/`):

```yaml
---
artifact_type: shipment
id: 013-S
status: archived
archived_from: .backlogit/queue/013-S.md
commit: aeee58e
title: Correctness & Safety Fixes
custom_fields:
    items:
        - 029-F
        - 029.001-T
        - 029.002-T
        - 029.003-T
        - 029.004-T
        - 029.005-T
created_at: 2026-04-12T12:47:24Z
updated_at: 2026-04-12T15:33:48Z
---
```

Key implications:

* `suffix_map` includes `shipment: "S"` because it uses the standard ID
  hierarchy and lives in the queue directory
* Shipment references its wrapped work items via `custom_fields.items`
* Shipment uses the following lifecycle statuses: `queued` (created, waiting
  to be claimed), `active` (claimed, work in progress), `shipped` (PR merged,
  closure complete), `abandoned` (cancelled before shipping), and `archived`
  (moved from `queue/` to `archive/` after shipping or abandonment)
* Archived shipments gain `archived_from` (origin path) and may carry a
  `commit` field linking the shipment to its final merge commit
* Note: the `done` status visible in some early shipment artifacts is
  equivalent to `shipped` — backlogit normalizes both to the same terminal state
* Ship agent creates and manages shipments; Stage agent does not
* Unlike features, chores, and tasks, a shipment does not contain
  implementation detail — it is a release grouping artifact

Stable MCP tools (7): `backlogit_create_shipment`, `backlogit_get_shipment`,
`backlogit_list_shipments`, `backlogit_claim_shipment`,
`backlogit_ship_shipment`, `backlogit_add_to_shipment` (MCP-only, no CLI
subcommand), `backlogit_return_blocked`.

Stable CLI subcommands (6): `backlogit shipment create`, `get`, `list`,
`claim`, `ship`, `return-blocked`.

Shipment lifecycle: `queued → active → shipped/abandoned → archived`.

Error sentinels: `ErrShipmentNotFound`, `ErrShipmentConflict`,
`ErrItemAlreadyAssigned`, `ErrCannotReturnItem`.

The shipment surface is graduated and wired into the backlogit registry
template. The remaining incubating items (stash JSONL, file naming
conventions) are independent of the shipment contract.

The remaining two-agent choreography is promising, but it is not yet ready to
become template truth in `autoharness`.

Until backlogit proves the remaining workflow in its own repository,
`autoharness` should **not** hardcode:

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
  comments, commit traceability, metadata discovery, SQL schema reference,
  YAML/frontmatter tooling coverage, source artifact cleanup

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
* [Getting Started](getting-started.md)
* [The 10 Irreducible Harness Primitives](primitives.md)
* [Tuning Guide](tuning-guide.md)

For the incubating workflow itself, see the backlogit repository's design and
memory artifacts that track the two-agent refactor.