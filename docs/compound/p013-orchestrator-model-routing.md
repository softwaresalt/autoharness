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

Frontmatter pattern used across all agent templates:
```yaml
model_routing: "Tier N (Label)"  # DEPRECATED — use model_tier
model_tier: N
max_subagent_tier: N
reasoning_effort: "{{TIER_N_REASONING_EFFORT}}"
model_provider: "{{TIER_N_PROVIDER}}"
model_family: "{{TIER_N_FAMILY}}"
```

**Part 3: Schema Enforcement**

- `schemas/harness-config.schema.json` — tier objects changed to `oneOf: [string, object]`
  with `required: ["model"]` + `additionalProperties: false` for backward compat.
- `verify_workspace.py` — added `_add_frontmatter_tier_check()` (YAML frontmatter
  parser; validates `model_tier`/`max_subagent_tier` are integers 1–3). Two new
  FOUNDATION_ASSERTIONS: `orchestrator_tier_fields` and `p013_policy_in_workflow_policies`.
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

| Agent | model_tier | max_subagent_tier |
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
