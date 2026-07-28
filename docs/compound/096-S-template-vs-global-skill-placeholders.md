---
problem_type: template-placeholder-resolution
category: template-authoring
root_cause: Source-controlled global skills were treated like rendered templates, but only `templates/*.tmpl` artifacts receive install-time `{{VARIABLE}}` substitution.
tags: [templates, global-skills, placeholders, model-routing, anchor-review, verify-harness, install-harness]
shipment: 096-S
feature: 091-F
pr: 238
merged_at: "2026-07-28T06:22:42Z"
---

# Template Placeholders Do Not Resolve in Global Skills

## Problem

`{{VARIABLE}}` placeholders are valid customization points inside rendered
`templates/*.tmpl` files, but source-controlled global skills under
`.github/skills/*/SKILL.md` are not rendered during installation. Embedding a
placeholder such as `{{ANCHOR_REVIEW_PROVIDER}}` in a global skill leaves a
literal unresolved token in the installed harness and can make verification or
review routing lie about the effective configuration.

## Durable Rule

Use placeholders only in rendered templates. For global skills, load runtime
values from the target workspace configuration, for example
`<workspace>/.autoharness/config.yaml` `model_routing.anchor_review`, and apply
literal in-skill defaults when the config key is absent.

For 096-S, the correct split is:

- `.github/skills/verify-harness/SKILL.md` is global/non-rendered, so it resolves
  `model_routing.anchor_review` from the target workspace at dispatch time and
  defaults to `openai` / `gpt-5.6-sol` / `high` before probing dispatch.
- `templates/agents/adversarial-review.agent.md.tmpl` and
  `templates/instructions/adversarial-review.instructions.md.tmpl` are rendered,
  so they may contain `{{ANCHOR_REVIEW_PROVIDER}}`, `{{ANCHOR_REVIEW_FAMILY}}`,
  and `{{ANCHOR_REVIEW_REASONING_EFFORT}}` placeholders.

## Verification Pattern

Add deterministic tests that assert global skill files do **not** contain the new
placeholder family while rendered templates do. Also test that the global skill
states the config path and default behavior explicitly.
