---
title: "Model-Routing Hierarchy Correctness + Dynamic Session-Start Reload (F02FD596 + E8B5B3C5)"
date: "2026-08-07"
description: "Deliberation resolving the F02FD596 routing-hierarchy defect (flat model_routing.escalation → nested per-role escalation) and framing the E8B5B3C5 dynamic session-start config reload, with fail-closed migration and P-013.5/P-013.6 compatibility."
topic: "How should escalation routes be nested per role, and how should the harness re-resolve routes at session start, without regressing P-013.5/P-013.6 or the ESCALATION_DEGRADED guard?"
depth: "decision"
decision_status: "decided"
doc_type: decision
source: docs/decisions/2026-08-07-model-routing-hierarchy-dynamic-reload-deliberation.md
stash_ids:
  - "F02FD596"
  - "E8B5B3C5"
model_route:
  model_family: claude-opus-4.8
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - ".autoharness/config.yaml"
  - "schemas/harness-config/1.0.0.schema.json"
  - "schemas/harness-config.schema.json"
  - "src/autoharness/verify_workspace.py"
  - "templates/instructions/escalation-protocol.instructions.md.tmpl"
tags: ["model-routing", "P-013.5", "P-013.6", "escalation", "F02FD596", "E8B5B3C5"]
---

# Model-Routing Hierarchy Correctness + Dynamic Session-Start Reload

## Problem frame

Two stash entries share the `model_routing` code surface and compose:

* **F02FD596 (high bug)**: `model_routing.escalation` is a **flat sibling** of
  `ship`/`stage` — a single role-agnostic escalation route. The operator intends a
  **nested per-role** hierarchy (e.g., `ship.escalation`: start `gpt-5.6-terra`,
  escalate to `claude-sonnet-5`). Requires config/schema/template/loader/verification/
  migration changes with P-013.5/P-013.6 compatibility, failing closed on ambiguous
  legacy config.
* **E8B5B3C5 (high feature)**: the harness must **re-read `.autoharness/config.yaml`
  at every session start** and re-resolve role/model/escalation routes instead of
  relying on baked/stale state — enabling provider model updates without reinstall.

## Verified current state (read-only)

* `.autoharness/config.yaml`: `model_routing` has `tier1..3`, `orchestrator`,
  `stage {claude-opus-5,high}`, `ship {claude-sonnet-5,high}`, and a **flat**
  `escalation {gpt-5.6-sol,high}`.
* `schemas/harness-config/1.0.0.schema.json`: `escalation` is a top-level object
  ("the halting agent's escalation directive", per-field tier3 fallback, explicit
  **ESCALATION_DEGRADED same-route guard**). `additionalProperties:false` on each route.
* `src/autoharness/verify_workspace.py` is the loader/verification surface.
* Escalation-protocol template + agent templates + workflow-policies reference the
  route.

## F02FD596 — options

* **Option A — Rename only** flat `escalation` → `ship.escalation`. *Rejected*:
  silently strands Stage's escalation route (currently the flat `gpt-5.6-sol` this
  session depends on) and breaks the role-agnostic ESCALATION_DEGRADED guard.
* **Option B — Nested per-role escalation with legacy flat fallback (CHOSEN)**:
  introduce `model_routing.ship.escalation` and `model_routing.stage.escalation`
  (each `{model_provider?, model_family?, reasoning_effort?}`,
  `additionalProperties:false`, per-field fallback). Resolution precedence for an
  acting role's escalation: `<role>.escalation` → flat `model_routing.escalation`
  (legacy, **deprecated**) → per-field `tier3`. The ESCALATION_DEGRADED same-route
  guard is preserved and compares the resolved escalation tuple against the **acting
  role's own resolved route**.
* **Option C — Hard cutover** (drop flat `escalation`). *Rejected*: regresses every
  existing workspace and this session's own escalation resolution; violates "fail
  closed / no silent loss".

### Chosen migration (fail-closed)

| Config shape | Behavior |
|---|---|
| Only flat `escalation` | Legacy shared escalation; resolvable by all roles as today + **deprecation warning**. No regression. |
| Only nested `<role>.escalation` | New per-role behavior. |
| **Both** flat AND any nested present | **AMBIGUOUS → schema/loader ERROR, fail closed, halt for operator disambiguation.** Never silently reassign the flat route to a role. |
| Neither | Per-field `tier3` fallback (unchanged). |

### Config-data vs structural split (operator confirmation deferred)

The **structural** change (schema + loader + templates + verify + migration) is
unambiguous and staged now. The stash's specific dogfood **data** values (Ship
start `gpt-5.6-terra` → escalate `claude-sonnet-5`) conflict with the current
`ship=claude-sonnet-5` baseline and the flat-escalation comment, so writing those
concrete values into `.autoharness/config.yaml` is flagged for **explicit operator
confirmation at Ship time**. Staging fails closed on the data ambiguity while the
structural fix proceeds.

## E8B5B3C5 — options

* **Option A — keep baked-at-install routes**. *Rejected*: the whole point is to
  drop reinstall-to-update.
* **Option B — session-start reload with fail-closed validation (CHOSEN)**: at each
  new agent session start, re-read `.autoharness/config.yaml`, validate against the
  harness-config schema, re-resolve role + escalation routes (including F02FD596
  nested escalation), and invalidate any cached/baked route. **Degraded/fail-closed**:
  on missing/invalid/schema-failing config at session start, **halt to operator** —
  do NOT silently run on stale baked routes. Propagate the freshly resolved route as
  the invocation-time directive to invoked agents and **inherited skills** (P-013.5),
  and to the escalation directive (P-013.6). Depends on F02FD596's nested resolver so
  reload resolves the corrected hierarchy.

## Composability decision

F02FD596 (bug, reliability) sequences **before** E8B5B3C5 (feature): the reload must
resolve the corrected nested hierarchy, and reliability supersedes feature work. The
schema+resolver land first; the reload consumes them.

## Open questions (recorded, not silently decided)

1. Concrete dogfood escalation values (terra/sonnet-5) — operator-confirmed at Ship.
2. Reload cadence: session-start only (chosen) vs. mid-session watch — mid-session
   watch is out of scope (adds TOCTOU/consistency risk); session-start is sufficient
   for the stated goal.
3. Last-known-good caching on invalid reload — **rejected** in favor of fail-closed
   halt (safety over availability), consistent with the operator's fail-closed directive.

## Decision

Adopt **F02FD596 Option B** (nested per-role escalation + legacy flat fallback +
both-present fail-closed) and **E8B5B3C5 Option B** (session-start fail-closed
reload), harvested as one covering feature with F02FD596 sequenced first. Elevated
blast radius (schema + routing semantics + multiple template families) → **P-006
plan hardening REQUIRED**.
