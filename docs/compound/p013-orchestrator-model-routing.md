---
title: "P-013: Orchestrator Rename + Structured Model Tier Routing"
problem_type: harness_architecture
category: agent_design
root_cause: unstructured_model_routing_string
tags: [orchestrator, model-tier, frontmatter, schema, verify-workspace, p013]
shipment: 013-S
pr: 46
merge_commit: e76b874d01bf4235522743a017ccd40db858d930
merged_at: "2026-05-08T13:07:22Z"
date: "2026-05-08"
---

> **Update (2026-07-11) — `model_tier` frontmatter retired (053.004-T).** The
> per-agent `model_tier` integer added by 013-S (Part 2 below) has been removed
> from all agent definitions. It duplicated a tier the template already selects
> and was the only field the frontmatter tier check still required beyond
> `max_subagent_tier`. Config-driven routing is unchanged: each agent's base tier
> is bound by the `model_routing` map in `.autoharness/config.yaml`, resolved at
> install into `model_family` / `model_provider` / `reasoning_effort`, and
> `max_subagent_tier` still declares the delegation ceiling. P-013.1/P-013.4 were
> reframed to config-resolved tier, and `_add_frontmatter_tier_check()` now
> validates only `max_subagent_tier`. The sections below reflect the original
> 013-S design; the base-tier column in the reference table is the config-resolved
> tier, no longer a `model_tier` frontmatter value.

## Problem

The `dispatch.agent.md.tmpl` used a plain prose `model_routing` string in
frontmatter (e.g., `"Tier 2 (Standard)"`). This was unstructured, not
machine-readable, and gave harness verification no way to enforce correct tier
assignments. Multiple agent templates had inconsistent or missing routing
declarations.

## Solution

**Part 1: Rename Dispatch → Orchestrator**

Renamed `templates/agents/dispatch.agent.md.tmpl` to `orchestrator.agent.md.tmpl`.
Updated all internal content (agent name, intercom broadcasts `[DISPATCH]` →
`[ORCHESTRATOR]`, stop conditions, model routing prose). Preserved verb "dispatch"
where appropriate (e.g., "dispatch reviewers", "Parallel Dispatch").
Updated install-harness SKILL.md Primitive 4 table and pipeline list.
Updated workflow-policies.md.tmpl P-010 cross-references.

**Part 2: Structured Integer Tier Fields**

Added `model_tier`, `max_subagent_tier`, and parameterized override fields
(`reasoning_effort`, `model_provider`, `model_family`) to all 16 agent
templates. Legacy `model_routing` string retained with `# DEPRECATED` comment
for backward compatibility.

Frontmatter pattern used across all agent templates (as-of-013-S; RETIRED — the
`model_routing` string was removed in 058-S and the `model_tier` integer in
053.004-T. Do NOT copy this block; the current pattern omits both — see the
Update banner above):
```yaml
model_routing: "Tier N (Label)"  # RETIRED (058-S)
model_tier: N                     # RETIRED (053.004-T) — base tier is config-resolved
max_subagent_tier: N
reasoning_effort: "{{TIER_N_REASONING_EFFORT}}"
model_provider: "{{TIER_N_PROVIDER}}"
model_family: "{{TIER_N_FAMILY}}"
```

**Part 3: Schema Enforcement**

- `schemas/harness-config.schema.json` — tier objects changed to `oneOf: [string, object]`
  with `required: ["model"]` + `additionalProperties: false` for backward compat.
- `verify_workspace.py` — added `_add_frontmatter_tier_check()` (YAML frontmatter
  parser; validates tier fields are integers 1–3). Two new
  FOUNDATION_ASSERTIONS: `orchestrator_tier_fields` and `p013_policy_in_workflow_policies`.
  (As of 2026-07-11 the check validates only `max_subagent_tier`; `model_tier` was retired.)
- `workflow-policies.md.tmpl` — added P-013 (4 sub-policies) + amendment log v1.8.0.
- `templates/harness-config.yaml.tmpl` — updated to emit new object form for tiers.

## Key Design Decisions

### YAML null vs empty string (harness-config.yaml.tmpl)
Optional placeholder fields (`reasoning_effort`, `model_provider`, `model_family`)
MUST be wrapped in double quotes in the template. Without quotes, an empty resolved
placeholder produces YAML null, which fails `type: string` schema validation.
Always quote optional string placeholders: `field: "{{VARIABLE}}"`.

### Legacy scalar tier config fallback
The schema allows a tier to be specified as either a plain string (legacy) or an
object. When resolving `{{MODEL_ROUTING_TIER1}}`, check whether `config.model_routing.tier1`
is a string or object. If string: use that as the model value; leave sub-fields empty.
If object: use `.model`, `.reasoning_effort`, etc.

### Environment agnosticism for tier routing
The `--tier N` CLI syntax is aspirational. Per Core Rule 3, it is NOT implemented
as a literal CLI flag. Instead, tier routing is expressed as intent annotations in
agent prose (e.g., "Request Tier 3 reasoning when invoking Stage for backlog synthesis").

### adversarial-review has max_subagent_tier: 1
Despite running at Tier 3, adversarial-review dispatches Tier-1 reviewer instances.
`max_subagent_tier` reflects the tier of subagents spawned, not the agent's own tier.

### harness-manifest.schema.json was NOT updated
The manifest is a deployment record, not a validator of agent frontmatter content.
Tier enforcement belongs in verify_workspace.py via `_add_frontmatter_tier_check()`.
A future PR could add manifest-level tier metadata tracking if needed.

### P-013 policy table format
Policy metadata tables in workflow-policies.md.tmpl use `| Field | Value |` as the
header row (with `|---|---|` separator), NOT the first data row as header. This is
the canonical format for P-010 through P-013 and must be followed in all future policies.

## Review Friction Points

- 3 rounds of Copilot review comments across 12 threads
- Most common issues: YAML null vs quoted string, table header format inconsistency,
  schema/template mismatch, spec accuracy (skill vs agent templates; manifest schema)
- Reply to review threads using `gh api graphql` mutation `addPullRequestReviewThreadReply`
- Resolve threads using `gh api graphql` mutation `resolveReviewThread`
- Use `--field query='mutation...'` form to avoid quoting issues with embedded single quotes

## Tier Assignment Reference

| Agent | base tier (config-resolved) | max_subagent_tier |
|---|---|---|
| orchestrator | 2 | 3 |
| ship | 2 | 2 |
| stage | 3 | 3 |
| adversarial-review | 3 | 1 |
| security-sentinel | 3 | 3 |
| language-engineer | 2 | 2 |
| prompt-builder | 1 | 1 |
| learnings-researcher | 1 | 1 |
| security-reviewer | 2 | 1 |
| security-lens-reviewer | 2 | 1 |
| all other review personas | 1 | 1 |
