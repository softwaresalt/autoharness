---
title: "model_routing Construct 1 Removal — Implementation Plan"
description: "Executes the safe, P-013-preserving part of feature 053-F: remove the deprecated per-agent frontmatter model_routing string (Construct 1) from agent templates and installed workflow-agent mirrors, carrying forward the intentional agent metadata edits captured in stash 0CF1D6CF. The active config.yaml tier-to-model binding (Construct 2) is explicitly deferred as an operator-gated decision."
source_documents:
  - "docs/decisions/2026-07-01-model-routing-removal-deliberation.md"
feature: "053-F"
tasks:
  - "053.001-T"
  - "053.002-T"
  - "053.003-T"
deferred_tasks:
  - "053.004-T"
shipment: "058-S"
source_stash_ids:
  - "0CF1D6CF"
scope: "agent frontmatter (installed mirrors + templates) + Construct-1 prose; NO schema/config/installer changes"
tags:
  - "cleanup"
  - "model-routing"
  - "construct1"
  - "p013-safe"
  - "agent-frontmatter"
  - "carry-along"
---

## Problem Frame

Feature **053-F** (source stash `F6490D72`) requests removal of the
`model_routing` field. Deliberation **053.001-DL**
(`docs/decisions/2026-07-01-model-routing-removal-deliberation.md`) established
that the single token `model_routing` is **overloaded across two distinct
constructs**, so a blanket removal is unsafe:

* **Construct 1 — per-agent frontmatter `model_routing:` string (LEGACY /
  DEPRECATED).** A human-readable tier label (e.g.
  `model_routing: "Tier 2 (Standard)"  # DEPRECATED — use model_tier`). P-013
  already superseded it with the structured integer `model_tier`; harness
  verification checks `model_tier` / `max_subagent_tier`, never `model_routing`.
  **Removing it is P-013-safe** for any agent that already declares `model_tier`.
* **Construct 2 — config `model_routing:` object (ACTIVE / CORE to P-013).** The
  `.autoharness/config.yaml` block (schema `schemas/harness-config*.schema.json`,
  template `templates/harness-config.yaml.tmpl`) that maps tiers to concrete
  models and drives ~21 installer variable resolutions
  (`{{MODEL_ROUTING_TIER1..3}}`, `{{TIER_n_*}}`, `{{ORCHESTRATOR_*}}`). Removing
  it **regresses shipped P-013** and no replacement binding was supplied.

The deliberation recommended **Option D (Hybrid)**: retire Construct 1 now
(low-risk, verifiable) and split the Construct 2 decision behind explicit
operator intent.

## Operator Decision (2026-07-02)

The operator confirmed **053-F is no longer blocked** and that the
`model_routing` **field** can be removed. Interpreted against the deliberation,
"the field" is **Construct 1** (the per-agent frontmatter string). The active
config **object** (Construct 2) still has no named replacement for the
tier-to-model binding, so it remains operator-gated. This plan executes
Construct 1 only.

### Carry-along stash `0CF1D6CF`

The working tree already contains the exact **Construct 1 prerequisite** the
deliberation called out: the installed workflow agents
`.github/agents/.stage.agent.md` and `.ship.agent.md` previously carried **only**
`model_routing` (no `model_tier`). The local edits backfill the structured
fields (`model_tier`, `max_subagent_tier`, `reasoning_effort`, `model_provider`,
`model_family`) into `.stage`/`.ship` and update `_orchestrator` tier metadata.
These edits are intentional agent metadata updates — carried along, not
discarded as drift. `.mcp.json` is local environment drift and is **excluded**.

> Stage does not commit the three `.github/agents/*.agent.md` edits or
> `.mcp.json`. Ship applies and commits the agent edits as part of shipment
> `058-S`.

## Measured Footprint (point-in-time)

`model_routing` occurs across tracked files (excluding `.backlogit` and the
2026-07-01 decision doc) as follows:

| Construct | Locations | In this plan |
|---|---|---|
| **C1 — frontmatter string** | 3 installed workflow agents (`.github/agents/{.stage,.ship,_orchestrator}.agent.md`) + 20 agent templates under `templates/agents/**/*.agent.md.tmpl` (all also declare `model_tier`) | **YES — remove** |
| **C1 — describing prose** | `templates/policies/workflow-policies.md.tmpl` (~L336), `templates/skills/doc-review/SKILL.md.tmpl` (~L173) | **YES — reconcile** |
| **C2 — config binding** | `.autoharness/config.yaml`, `schemas/harness-config.schema.json`, `schemas/harness-config/1.0.0.schema.json`, `templates/harness-config.yaml.tmpl`, `.github/skills/install-harness/SKILL.md` (21 refs), `templates/agents/_orchestrator.agent.md.tmpl` (~L296, ~L313) | **NO — deferred (053.004-T)** |
| **C3 — historical docs/spec** | `docs/product-specs/orchestrator-model-routing-spec.md`, `docs/compound/p013-orchestrator-model-routing.md`, `docs/getting-started.md`, `docs/memory/*`, `docs/decisions/2026-06-30-*` | **NO — point-in-time / C2-coupled** |

Safety confirmations gathered during planning:

* Every agent template that carries `model_routing` **also declares
  `model_tier`** — removal never strips an agent's only tier marker.
* The template `model_routing:` line is a **literal string**, not a `{{VARIABLE}}`
  — removal orphans no installer variable.
* Construct 2 variables (`{{MODEL_ROUTING_TIER*}}`, `{{TIER_*_*}}`,
  `{{ORCHESTRATOR_*}}`) resolve from the **config object**, not from the
  frontmatter string, and are untouched by Construct 1 removal.

## Task Breakdown (2-hour rule, width-isolated)

### 053.001-T — Installed workflow-agent mirrors (carry-along `0CF1D6CF`)

* Files: `.github/agents/.stage.agent.md`, `.github/agents/.ship.agent.md`,
  `.github/agents/_orchestrator.agent.md`.
* Apply the intentional working-tree frontmatter edits (backfill
  `model_tier`/`max_subagent_tier`/`reasoning_effort`/`model_provider`/`model_family`
  into `.stage`/`.ship`; update `_orchestrator` tier metadata), **then** remove
  the deprecated `model_routing` frontmatter line from all three.
* Do **not** touch `.mcp.json`.
* Acceptance: no `model_routing` frontmatter key remains; each file declares
  integer `model_tier` + `max_subagent_tier` and resolved
  `reasoning_effort`/`model_provider`/`model_family` literals; frontmatter valid;
  `verify_workspace` tier check passes.

### 053.002-T — Agent templates

* Remove the deprecated literal `model_routing:` frontmatter line from all 20
  `templates/agents/**/*.agent.md.tmpl` that carry it.
* **Do not** touch `_orchestrator.agent.md.tmpl` lines ~296 and ~313 (Construct 2
  config-example prose / `config.model_routing.orchestrator` override).
* Acceptance: no template frontmatter contains `model_routing`; `model_tier` and
  all `{{TIER_*}}` variables preserved; no unresolved template variables
  introduced; markdown/frontmatter valid.

### 053.003-T — Construct-1 prose reconciliation (depends on 053.002-T)

* Update `templates/policies/workflow-policies.md.tmpl` (~L336) and
  `templates/skills/doc-review/SKILL.md.tmpl` (~L173) so guidance no longer
  implies a per-agent `model_routing` string is present; retain the structured
  `model_tier`/`max_subagent_tier` requirement.
* Scope is Construct-1 prose **only**; Construct 2 docs stay untouched.
* Acceptance: no stale claim that agents carry a `model_routing` frontmatter
  string; cross-references resolve.

### 053.004-T — Construct 2 config binding (DEFERRED / BLOCKED)

* **Not in shipment `058-S`.** Operator-gated per the deliberation. Needs an
  explicit decision: rename to preserve behavior (Option B), remove with a named
  replacement binding (Option A), or keep (Option C). Also reconcile the
  schema-version skew (`oneOf:[string,object]` vs plain string in the `1.0.0`
  schema). Do not execute until the operator supplies WHY + WHAT-replaces.

## Shipment

* **`058-S`** = `[053.001-T, 053.002-T, 053.003-T]`.
* Manifest contains **only task IDs** — parent `053-F` is excluded
  (cascade-safety), and blocked `053.004-T` is excluded. `053-F` remains **active**
  after this shipment, carrying the deferred Construct 2 scope.

## Quality Gates

* YAML frontmatter validity on every edited `.agent.md` / `.tmpl`.
* No unresolved `{{...}}` introduced in any template.
* `model_tier` + `max_subagent_tier` present on every affected agent/template;
  `verify_workspace` frontmatter tier check passes.
* Installed mirrors align with their templates (minus the removed
  `model_routing` line).
* Cross-reference integrity: no dangling references to a removed frontmatter
  field; Construct 2 references intentionally preserved.
* Markdown structure (MD001/MD025/MD041) on edited docs/policy templates.

## Out of Scope / Deferred

* All Construct 2 work (`053.004-T`): config schema, config template, live
  `.autoharness/config.yaml`, installer variable-resolution table, orchestrator
  config-example prose.
* Construct 3 historical docs/spec/compound updates (tied to the Construct 2
  decision) and `docs/memory/*` point-in-time records.
* Residual feature `056-F` backlog hygiene (unrelated; left untouched).
