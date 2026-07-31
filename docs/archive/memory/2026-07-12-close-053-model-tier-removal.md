# Close 053-F / 053.004-T: Remove model_tier from Agent Frontmatter

**Date**: 2026-07-12
**PR**: #208 — merged `51299af` (merge commit, P-009)
**Branch**: `feat/remove-model-tier` (deleted)

## Summary

Removed the redundant per-agent `model_tier` frontmatter integer from all agent
definitions while keeping config-driven model routing fully intact. This closes
the re-scoped feature 053-F and its last child task 053.004-T.

### Scope (operator-confirmed)

Remove **only** `model_tier`. Keep the `model_routing` config block plus
`max_subagent_tier`, `model_family`, `model_provider`, `reasoning_effort`, and
`subagent_depth`. The operator was explicit: model/agent routing is a wanted
autoharness capability — configured via `.autoharness/config.yaml`
`model_routing`, not via a duplicated per-agent `model_tier` integer.

### Why removal is behavior-neutral

`model_tier: N` only *documented* an agent's base tier. Routing is driven by:

1. The tier selection baked into each agent template (which `{{TIER_n_*}}`
   placeholders it resolves — ship=`TIER_2`, stage=`TIER_3`,
   orchestrator=`ORCHESTRATOR_*`), and
2. The installer binding `config.model_routing.tierN` → the agent's resolved
   `model_family` / `model_provider` / `reasoning_effort` frontmatter.

`model_tier` participated in neither path, so removing it does not change which
model any agent or subagent runs on.

## Changes

- Removed `model_tier:` from **20 agent templates** + **3 installed instances**
  (`.github/agents/{.ship,.stage,_orchestrator}.agent.md`). `auto-mergeinstall`
  / `auto-tune` never carried it.
- `verify_workspace.py`: `_add_frontmatter_tier_check` validates only
  `max_subagent_tier`; `p013_policy_in_workflow_policies` must_contain drops
  `model_tier`.
- `workflow-policies.md.tmpl`: P-013.1 renamed to "Resolved Tier Compliance";
  P-013.4 reframed so `max_subagent_tier` is the sole required frontmatter tier
  field and the base tier is config-resolved. P-013.2 / P-013.3 unchanged.
- `doc-review` Check 6: a missing `max_subagent_tier` is a P-013.4 **manual**
  conformance finding (not merely advisory).
- Product-spec + compound doc annotated with dated amendment banners
  (historical narrative preserved, not rewritten).
- Refreshed 3 installed-agent manifest checksums.
- Added a backward-compat test proving a leftover `model_tier` on an already
  installed agent is ignored (existing installs do not regress).

## Verification

- Full suite: **508 passed, 138 subtests** on merged HEAD `1788c4d`.
- Dogfood `verify_workspace(".", ".")`: 0 blockers, 0 strict-schema blockers,
  `orchestrator_tier_fields` ok, 0 unresolved placeholders.
- CI on HEAD: `ci gate` / `detect code changes` / `test` all pass.

## Review

- Pre-PR adversarial: code-review (correct & complete) + rubber-duck
  (no blocker; 3 coherence fixes applied).
- Copilot review — 2 rounds:
  1. **Real defect caught**: the P-013 policy test body had been folded into the
     new legacy-field test, so the policy contract was not exercised
     independently. Restored `test_verify_workspace_checks_p013_policy_in_workflow_policies`
     as its own method. Fixed in `1788c4d`.
  2. doc-review Check 6 reclassified missing `max_subagent_tier` as a P-013.4
     manual finding. Fixed in `1788c4d`.
  - Both threads replied-after-push and resolved; P-018 gate SATISFIED.

## Follow-ups / residual notes

- The numeric base tier is now implicit (config binding + template selection +
  persona prose). Escalation and tier legibility remain prose-level, as the
  operator directed — no replacement tier registry was added.
- Parked local commit `24a053a` (FD962DCC `.mcp.json` launcher intake) preserved
  on branch `park/fd962dcc-intake` for a future staging cycle.
