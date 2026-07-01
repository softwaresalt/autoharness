---
title: "model_routing Removal: Deliberation and Deferral Recommendation"
description: "Resolves the open questions for feature 053-F (Remove model_routing field): what model_routing actually is, its P-013 dependency, removal options, and a recommendation to DEFER execution pending operator intent"
topic: "Determine WHY model_routing should be removed and WHAT (if anything) replaces it, before any decomposition of 053-F"
depth: "deep"
decision_status: "deferred"
promoted_to: "none"
linked_artifacts:
  - "docs/product-specs/orchestrator-model-routing-spec.md"
  - "docs/compound/p013-orchestrator-model-routing.md"
  - "schemas/harness-config.schema.json"
  - "templates/harness-config.yaml.tmpl"
source_stash_ids:
  - "F6490D72"
backlog_items:
  - "053-F"
  - "053.001-DL"
tags:
  - "cleanup"
  - "model-routing"
  - "p013"
  - "schema"
  - "deferred"
  - "operator-intent"
---

## Problem Frame

Feature **053-F** (source stash `F6490D72`, kind: cleanup) requests: *"Remove the
`model_routing` field."* The request describes `model_routing` as appearing in
"~101 places across `.autoharness/config.yaml`, schemas/, agent frontmatter,
skills, templates, and docs" and explicitly flags a potential conflict with
shipped work **013-S / P-013 (Orchestrator Persona & Model Tier Routing)** and
`docs/product-specs/orchestrator-model-routing-spec.md`.

The removal request supplies **no rationale** (no WHY) and **no replacement**
(no WHAT). Deliberation task **053.001-DL** frames the unresolved questions:

> Is removal a full deletion or a rename/migration? What replaces per-agent tier
> declarations? How is P-013 routing preserved? Which artifact families (schema,
> agent frontmatter, config, docs, compound) are in scope?

This document resolves the *analysis* of those questions but concludes that the
*intent* questions can only be answered by the operator. **This is a
deliberation only — no `model_routing` was removed, and no agent, schema,
config, or template was modified.**

## Central Finding: `model_routing` Is Overloaded Across Two Distinct Constructs

The single token `model_routing` names **two semantically different things**
plus a body of documentation. Conflating them is the root of the removal
request's ambiguity.

### Construct 1 — Agent frontmatter `model_routing:` string (LEGACY / DEPRECATED)

A per-agent, human-readable tier label in YAML frontmatter, e.g.:

```yaml
model_routing: "Tier 2 (Standard)"  # DEPRECATED — use model_tier
model_tier: 2
max_subagent_tier: 3
```

- P-013 **explicitly replaced** this unstructured string with the structured
  integer field `model_tier` (see spec §P-013.3: *"Replaces unstructured
  'model_routing'"* and compound `root_cause: unstructured_model_routing_string`).
- It is retained only *"for backward compatibility"* with a `# DEPRECATED`
  comment (compound doc, Part 2).
- It is **not enforced** by harness verification. `verify_workspace.py`
  validates `model_tier` and `max_subagent_tier` (integers 1–3) via
  `_add_frontmatter_tier_check()` — never `model_routing`.
- Present on line 6 of all agent templates and their installed copies.
- **Exception:** the installed repo-local workflow agents
  `.github/agents/.stage.agent.md` and `.github/agents/.ship.agent.md` currently
  carry ONLY `model_routing` and have no `model_tier`/`max_subagent_tier`. For
  those two files, `model_routing` is the *only* tier marker.

**Removing Construct 1 is LOW risk for every agent that already declares
`model_tier`** — there it is dead/deprecated metadata superseded by the verified
integer field. It is NOT yet safe for `.stage.agent.md` / `.ship.agent.md`, which
must first be backfilled with `model_tier` (and `max_subagent_tier`) so removal
does not strip their only tier declaration.

### Construct 2 — Config `model_routing:` object (ACTIVE / CORE to P-013)

A block in `.autoharness/config.yaml` (schema:
`schemas/harness-config.schema.json`, template:
`templates/harness-config.yaml.tmpl`) that maps tiers to concrete model
identifiers and per-tier settings:

```yaml
model_routing:
  tier1: { model: gpt-5.4-mini, reasoning_effort: "", model_provider: "", model_family: "" }
  tier2: { model: claude-sonnet-4.6, ... }
  tier3: { model: claude-opus-4.6, ... }
  orchestrator: { model_family: gpt-5.4, ... }
```

- This is the **functional tier→model resolution mechanism** that P-013.3
  introduced (*"advanced routing configurations injected via workspace
  configuration"*).
- It drives ~15 installer variable resolutions in
  `.github/skills/install-harness/SKILL.md` (`{{MODEL_ROUTING_TIER1..3}}`,
  `{{TIER_n_REASONING_EFFORT}}`, `{{TIER_n_PROVIDER}}`, `{{TIER_n_FAMILY}}`,
  `{{ORCHESTRATOR_*}}`, and `alt_review` / `alt_doc_review` provider/family
  resolution).
- It is **not** a schema-`required` field (only `schema_version` is required),
  but the installer reads it to populate every agent's `model_family` /
  `model_provider` / `reasoning_effort` frontmatter.

**Removing Construct 2 is HIGH risk** — it deletes the mechanism that binds
tiers to real models. Without a named replacement this directly regresses P-013
routing behavior.

### Construct 3 — Documentation / spec references

`docs/product-specs/orchestrator-model-routing-spec.md`,
`docs/compound/p013-orchestrator-model-routing.md`, `docs/getting-started.md`,
prior decision/memory files. These describe both constructs and would need
coordinated updates under any removal.

## Current State — Inventory of `model_routing` Usage

A scoped scan (`*.md`, `*.tmpl`, `*.json`, `*.yaml`; excluding `.venv`,
`.backlogit`, `.copilot`, `.git`) found **70 matches across 37 files**. (The
stash's "~101" estimate is an over-count relative to this scoped scan; the
discrepancy is itself a signal that the blast radius was estimated, not
measured.) Python sources reference only `model_tier` — **never**
`model_routing`.

| Artifact family | Representative paths | Count / notes |
|---|---|---|
| **Config schema** (Construct 2) | `schemas/harness-config.schema.json`, `schemas/harness-config/1.0.0.schema.json` | 1 field def each; `type: object`, **not required**. Schema-version skew: the unversioned schema defines tier1/2/3 as `oneOf:[string,object]`, but the versioned `1.0.0` schema still defines them as plain strings — any rename/remove plan must reconcile both |
| **Config template** (Construct 2) | `templates/harness-config.yaml.tmpl` (lines 64–84) | `model_routing:` block with tier1/2/3/orchestrator |
| **Live self-config** (Construct 2) | `.autoharness/config.yaml` | 1 block |
| **Agent frontmatter** (Construct 1) | 16 agent `*.agent.md.tmpl` (line 6) + `.github/agents/{_orchestrator,.stage,.ship}.agent.md` | 19 legacy `model_routing:` strings. All *templates* also carry `model_tier`; but installed `.stage.agent.md` / `.ship.agent.md` carry ONLY `model_routing` (no `model_tier`) and must be backfilled before removal |
| **Installer resolution** (Construct 2) | `.github/skills/install-harness/SKILL.md` | 21 references (`config.model_routing.*` variable-resolution table) |
| **Orchestrator prose** (Construct 2) | `templates/agents/_orchestrator.agent.md.tmpl` (config example ~line 313) | 3 references |
| **Spec / compound** (Construct 3) | `docs/product-specs/orchestrator-model-routing-spec.md`, `docs/compound/p013-orchestrator-model-routing.md` | 8 references |
| **Docs / memory / decisions** (Construct 3) | `docs/getting-started.md`, `docs/memory/*`, `docs/decisions/2026-06-30-validation-gates-config-schema-deliberation.md`, `templates/skills/doc-review/SKILL.md.tmpl`, `templates/policies/workflow-policies.md.tmpl` | remainder |

Enforcement anchor: `src/autoharness/verify_workspace.py`
(`_add_frontmatter_tier_check`, `FOUNDATION_ASSERTIONS`) plus
`tests/test_verify_workspace.py` assert `model_tier` / `max_subagent_tier`
integers — confirming Construct 1 is *not* load-bearing and Construct 2 is the
functional mechanism.

## P-013 Dependency Analysis — What Breaks If Removed

P-013 (shipped as 013-S, PR #46, merge `e76b874`) provides tier-based model
routing through three layers:

1. **Tier taxonomy (Tier 1/2/3)** — declared per agent via `model_tier` /
   `max_subagent_tier`. **Independent of `model_routing`.** Not affected by
   removing either construct.
2. **Tier→model binding** — the config **`model_routing` object** (Construct 2)
   maps each tier to a concrete `model` / `model_family` / `model_provider` /
   `reasoning_effort`, which the installer resolves into agent frontmatter.
   **This is the load-bearing dependency.** Deleting Construct 2 without a
   replacement leaves the installer unable to resolve `{{MODEL_ROUTING_TIER*}}`
   and `{{TIER_*_FAMILY/PROVIDER/REASONING_EFFORT}}`, breaking cross-provider
   routing and the documented orchestrator override.
3. **Legacy prose label** — the frontmatter `model_routing:` string
   (Construct 1). **Superseded and non-functional.** Removing it regresses
   nothing, provided `model_tier` remains.

**Conclusion:** Removing Construct 1 preserves P-013. Removing Construct 2
regresses P-013 unless an equivalent tier→model binding mechanism is introduced.

## Options

### Option A — Full removal + named replacement for tier→model binding

Remove both constructs; introduce a new mechanism (e.g., rename the config block
to `model_tiers` / `tier_models`, or fold tier→model mapping directly into agent
frontmatter defaults) that preserves P-013 tier→model resolution.

- **Pros:** Eliminates the overloaded token; delivers the requested cleanup;
  can simultaneously retire the deprecated Construct 1 string.
- **Cons:** Largest blast radius (schema + template + installer table + spec +
  compound + tests); requires designing and validating the replacement across ≥3
  tech profiles; touches shipped P-013 contract.
- **Risk:** High. Regresses P-013 if the replacement is incomplete.
- **Effort:** High (multi-domain: schema, templates, installer, docs, tests).

### Option B — Rename/migrate while preserving behavior

Keep the tier→model binding but rename the config field to something
unambiguous (e.g., `model_tiers`), and drop only the deprecated Construct 1
frontmatter string. Add a schema alias / migration note for backward compat.

- **Pros:** Preserves P-013 behavior; removes the *naming* collision the request
  may actually be targeting; retires the dead Construct 1 string cleanly.
- **Cons:** Still touches schema, template, installer resolution table, and docs;
  requires a config-migration path for existing installs.
- **Risk:** Medium. Behavior preserved; risk is mechanical (migration
  completeness) rather than functional regression.
- **Effort:** Medium.

### Option C — Keep as-is / reject removal

Treat the request as predating or conflicting with shipped P-013 and decline the
removal, optionally scoping it down to only deleting the deprecated Construct 1
frontmatter string.

- **Pros:** Zero risk to P-013; smallest or no change; honors the fact that
  `model_routing` (Construct 2) is the *intended* P-013 mechanism.
- **Cons:** Does not satisfy the request as literally worded; leaves the
  overloaded token in place.
- **Risk:** Low.
- **Effort:** Low to none.

### Option D (Hybrid) — Retire Construct 1 now, defer Construct 2 decision

Scope 053-F to **only** removing the deprecated Construct 1 frontmatter
`model_routing:` string (low risk, P-013-safe) from agents that already declare
`model_tier`, and split the Construct 2 config-block decision (rename vs remove vs
keep) into a separate operator-gated item. **Prerequisite:** first backfill
`model_tier`/`max_subagent_tier` into `.github/agents/.stage.agent.md` and
`.ship.agent.md` (which today carry only `model_routing`), or exclude those two
files from the cleanup, so removal never strips an agent's only tier marker.

- **Pros:** Delivers safe, verifiable cleanup immediately; isolates the risky
  design decision behind operator intent; aligns with P-013's own stated goal of
  retiring the unstructured string.
- **Cons:** Requires operator confirmation that Construct 1 is the intended
  target; partial satisfaction of the literal request.
- **Risk:** Low for the executed part; Construct 2 risk is deferred, not taken.
- **Effort:** Low (Construct 1) + deferred.

## Risk Analysis

- **Preserving P-013 under each option:** A requires a fully designed
  replacement binding; B requires a complete rename + migration path; C/D
  require leaving Construct 2 intact. Only A takes on functional-regression risk.
- **Reversibility:** Construct 1 removal is trivially reversible (re-add a
  deprecated string). Construct 2 removal is expensive to reverse once installer
  resolution and schema are changed and workspaces reinstall.
- **Migration cost:** Any change to Construct 2 forces a config-migration story
  for existing `.autoharness/config.yaml` files and updates to the installer
  variable-resolution table (21 references) plus verify tests.
- **Blast-radius accuracy:** The measured 70/37 footprint (vs the estimated
  ~101) means execution planning must re-scan, not trust the estimate.

## Unresolved Operator-Intent Questions

These cannot be answered from the codebase; only the operator holds the design
intent:

1. **WHY remove `model_routing`?** Is the motivation the naming collision
   (overloaded token), dead-metadata cleanup (Construct 1), or a genuine intent
   to eliminate tier→model config (Construct 2)?
2. **WHICH construct is in scope?** The deprecated frontmatter string
   (Construct 1), the active config block (Construct 2), or both?
3. **WHAT replaces per-agent tier→model binding** if Construct 2 is removed?
   Does `model_tier` alone suffice, or is a renamed config block preferred?
4. **Full deletion vs rename/migration?** If the concern is naming, a rename
   (Option B) preserves behavior; if it is genuine removal, a replacement must be
   named.
5. **Artifact-family scope:** schema only, agent frontmatter only, config +
   installer, docs/compound — or all of them?
6. **P-013 relationship:** Should this supersede/amend the shipped P-013
   contract and its spec, or explicitly preserve it?

## Recommendation — DEFER

**Recommendation: DEFER execution of 053-F pending operator input.** Do **not**
decompose or execute 053-F until the operator resolves the intent questions
above.

Autonomous removal is **unsafe**: the removal request gives no rationale and no
replacement, while `model_routing` (Construct 2) is the load-bearing tier→model
binding that shipped P-013 depends on. Naively deleting it would regress
deliberately-shipped tier-routing behavior with no known replacement.

When the operator is available, the recommended path is **Option D (Hybrid)** as
the safest forward motion: retire the deprecated Construct 1 frontmatter string
(P-013-safe, verifiable) and route the Construct 2 config-block decision
(rename per Option B vs remove-with-replacement per Option A vs keep per
Option C) through explicit operator intent. Until then, 053-F remains **queued /
blocked** and this deliberation (053.001-DL) is marked done.

**Deliberation guardrails honored:** No `model_routing` field was removed. No
agent, schema, config, or template was modified. No PR was opened.
