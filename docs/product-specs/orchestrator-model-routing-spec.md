---
title: "Execution Plan: P-013 Orchestrator Persona and Model Tier Routing"
date: 2026-05-07
problem_type: architectural-spec
category: harness-design
tags: [p-013, model-routing, persona-isolation, orchestrator]
status: implemented
---

## Execution Plan: P-013 Orchestrator Persona and Model Tier Routing

> **Amendment (2026-07-11) — `model_tier` frontmatter retired.** The redundant
> per-agent `model_tier` integer described below has been removed from all agent
> definitions (053.004-T). Config-driven model routing is unchanged: each agent's
> base tier is bound by the `model_routing` map in `.autoharness/config.yaml` and
> resolved at install time into its `model_family` / `model_provider` /
> `reasoning_effort` frontmatter, while `max_subagent_tier` still declares the
> delegation ceiling. The base tier is defined by that config binding and the
> template's tier selection rather than a duplicate frontmatter integer. P-013.1
> and P-013.4 were reframed to config-resolved tier, and `verify-workspace` now
> validates only `max_subagent_tier`. Sections below reflect the original
> 2026-05-07 design and are annotated inline where superseded.

> **Amendment (2026-08-01) — P-013.5: invocation-time model-routing
> enforcement (104-F / 108-S).** Config-resolved tier binding (above) governs
> an agent's *installed* frontmatter, but did not make routing verifiable at
> **invocation** time: the Orchestrator's Steps 1/2 previously invoked
> Stage/Ship with no explicit model-override directive, so sub-sessions could
> silently inherit the current session's model instead of the intended route.
> P-013.5 closes this gap:
>
> - **First-class role routes.** `model_routing.stage` / `model_routing.ship`
>   are new optional route objects (`model_provider`, `model_family`,
>   `reasoning_effort`; `additionalProperties: false`; no required fields —
>   mirrors the `alt_review` pattern) added to both `schemas/harness-config.schema.json`
>   and `schemas/harness-config/1.0.0.schema.json`. When a route or one of its
>   sub-fields is absent/empty, resolution falls back **per field** to
>   `model_routing.tier3` (Stage) / `model_routing.tier2` (Ship) — P-013's tier
>   taxonomy is preserved, nothing regresses for workspaces that never declare
>   an explicit stage/ship route.
> - **Installer variables.** `install-harness/SKILL.md`'s variable table gained
>   `STAGE_REASONING_EFFORT` / `STAGE_PROVIDER` / `STAGE_FAMILY` and the
>   `SHIP_*` equivalents, each with the same per-sub-field tier3/tier2
>   fallback described above.
> - **Orchestrator invocation directive.** Steps 1 and 2 of both
>   `templates/agents/_orchestrator.agent.md.tmpl` and the installed
>   `.github/agents/_orchestrator.agent.md` now include an explicit "Resolve
>   routed model (P-013.5)" step before each subagent invocation: resolve
>   `config.model_routing.stage` / `.ship`, declare the resolved
>   `model_family`/`model_provider` as the invocation override, and emit
>   `ROUTING_DEGRADED` explicitly when the runtime cannot honor a
>   per-invocation model override — the Orchestrator must never silently fall
>   back to its own session model.
> - **Skill-delegation inheritance.** A new "Skill-Delegation Model
>   Inheritance (P-013.5)" section in `role-enforcement.instructions.md`
>   (template + installed) states that skills are leaf executors that inherit
>   the invoking agent's already-routed session model, must not re-resolve
>   per skill, and must carry forward any `ROUTING_DEGRADED` state rather than
>   silently resolving on their own.
> - **Policy.** `### P-013.5 — Invocation-Time Model-Routing Enforcement` was
>   appended to the P-013 family in `templates/policies/workflow-policies.md.tmpl`
>   (Resolve / Declare / Degrade-explicitly / Skill-inheritance /
>   Fail-closed-verification / Violation-Action structure); Amendment Log
>   bumped to `1.16.0`.
> - **Fail-closed verification.** Three new gated `verify_workspace.py`
>   checks — see Phase 3 below (`orchestrator_model_routing_fields` /
>   `stage_model_routing_fields` / `ship_model_routing_fields`,
>   `orchestrator_invocation_routing_directive`, `role_route_resolution`).
>
> Dogfood assignment for this repository: Stage → `claude-opus-4.8`
> (anthropic, high), Ship → `claude-sonnet-5` (anthropic, high), per
> `.autoharness/config.yaml`.

1. Problem Statement

The current agent architecture suffers from two critical flaws:

Persona Collision: Utilizing names like "Operator" for orchestration agents collides with the established definition of the human-in-the-loop, risking severe unauthorized state changes if an agent hallucinates authorization to bypass circuit breakers. The current dispatch name implies passive routing rather than active pipeline coordination.

Compute Inefficiency & Reasoning Failures: Hardcoding model_routing strings (e.g., "Tier 2 (Standard)") without a functional enforcement mechanism causes Tier 1 utility tasks to burn expensive Tier 3 compute, while Tier 3 adversarial reasoning tasks fail when executed by Tier 1/2 models due to context window limitations or lack of depth.

2. P-013 Policy Definition

This plan establishes P-013: Explicit Model Routing & Persona Isolation, which mandates the following constraints across the autoharness workspace.

P-013.1: Persona Isolation (The "Operator" Constraint)

The term Operator is strictly reserved for the human user overseeing the system.

No agent, skill, or tool prompt may use "Operator" to describe an AI persona.

The agent responsible for pipeline coordination, Step 0.0 gating, and Stage/Ship routing must be named Orchestrator. (Replacing Dispatch).

P-013.2: Model Tier Taxonomy

All operations must be explicitly categorized into one of three compute tiers.

Tier 1: Utility & Formatting (e.g., Haiku, GPT-4o-mini)

Scope: Highly structured, low-ambiguity tasks with binary outcomes.

Target Operations: Pre-flight tool availability gates (Step 0.0), markdown linting, YAML verification, log aggregation, and cross-reference resolution.

Tier 2: Orchestration & Execution (e.g., Sonnet, GPT-4o)

Scope: Strict rule adherence, tool calling, Git branch manipulation, and workflow coordination.

Target Operations: The Orchestrator agent's sequential pipeline loops; the Ship agent's codebase manipulation and test execution.

Tier 3: Synthesis & Deep Reasoning (e.g., Opus, Sona 4.6, o1/o3)

Scope: High-ambiguity planning, adversarial auditing, root-cause architectural debugging, and backlog synthesis.

Target Operations: The Stage agent's shipment planning from unstructured stash entries; the verify-harness multi-model adversarial review; complex CI remediation strategies.

P-013.3: Strict YAML Frontmatter Schema

The autoharness template frontmatter schema must be updated to enforce integer-based capability declarations instead of unstructured strings, while allowing advanced routing configurations to be injected via workspace configuration.

Every agent template MUST declare (skill templates are not required to carry tier fields — skills are leaf executors invoked by agents, not independently routed):

## Config-resolved tier binding (model_routing) + frontmatter delegation ceiling

max_subagent_tier: 3      # The maximum tier it is authorized to invoke
# (base tier is config-resolved via model_routing — the standalone `model_tier`
#  integer shown in the original design was retired 2026-07-11)

## Environment-configurable overrides (resolved via config.yaml)

reasoning_effort: "{{TIER_2_REASONING_EFFORT}}"  
model_provider: "{{TIER_2_PROVIDER}}"  
model_family: "{{TIER_2_FAMILY}}"  

Environment Agnosticism Constraint: To satisfy Core Rule 3 (Environment Agnosticism), the fields reasoning_effort, model_provider, and model_family MUST NOT be hardcoded to specific vendor strings (e.g., "anthropic" or "high") in the .tmpl files. They must be parameterized using {{VARIABLE}} syntax and resolved strictly from .autoharness/config.yaml during the auto-mergeinstall and auto-tune routines.

P-013.4: Upward/Downward Invocation Protocol

Sub-agent invocations must explicitly declare the required tier. Orchestrator (Tier 2) must explicitly request a Tier 3 invocation when calling Stage.

**Implementation note**: The `--tier 3` CLI syntax described below is the aspirational interface. Per Core Rule 3 (Environment Agnosticism), this syntax is NOT implemented as a literal CLI flag — the environment may not support it. Instead, tier routing is expressed as **intent annotations in agent prose** (e.g., "Request Tier 3 reasoning capacity when invoking the Stage agent for backlog synthesis"). This achieves the same routing intent without binding the harness to a specific CLI contract.

Agent prompt instructions must reflect this intent. For example, Orchestrator's model routing section must document that Stage requires Tier 3 reasoning capacity for backlog synthesis work.

3. Required Artifact Modifications

Phase 1: Nomenclature & Migration

Rename File: templates/agents/dispatch.agent.md.tmpl -> templates/agents/orchestrator.agent.md.tmpl.

Update Content: Replace all internal references from "Dispatch" to "Orchestrator". Retain existing references to "Operator" ONLY when referring to pausing/halting for human review.

Update Manifest: Modify install-harness/SKILL.md (Step 2.4 and Primitive 4 mappings) to wire orchestrator instead of dispatch.

Phase 2: Schema & Frontmatter Enforcement

Modify Config Schemas: Update schemas/harness-config.schema.json to support a new model_routing block where users define their preferred mappings (e.g., defining TIER_2_REASONING_EFFORT: "high"). Each tier accepts either a legacy plain string (backward compat) or an object with `model` (required) plus optional `reasoning_effort`, `model_provider`, `model_family`. ✅ Implemented.

**Note on harness-manifest.schema.json**: The original spec proposed updating the manifest schema to require `model_tier`/`max_subagent_tier`. This was intentionally not done — the harness manifest is a deployment record (which primitives/artifacts were installed) and is not the appropriate place to validate agent frontmatter content. Agent tier field enforcement is handled at harness-verification time by `_add_frontmatter_tier_check()` in `verify_workspace.py`, which parses installed agent files directly. A future refinement could add a manifest-level signal if tier metadata is worth tracking at the artifact registry level.

Update Agent Templates (base tier config-resolved via `model_routing`; only `max_subagent_tier` is a frontmatter integer — the `model_tier` values below reflect the original design and were retired 2026-07-11):

orchestrator.agent.md.tmpl: Tier 2, max_subagent_tier: 3 (plus parameterized overrides)

ship.agent.md.tmpl: Tier 2, max_subagent_tier: 2 (plus parameterized overrides)

stage.agent.md.tmpl: Tier 3, max_subagent_tier: 3 (plus parameterized overrides)

adversarial-review.agent.md.tmpl: Tier 3, max_subagent_tier: 1 (plus parameterized overrides)

Update Policy Docs: Append P-013 to templates/policies/workflow-policies.md.tmpl.

Phase 3: Assertion Coverage (verify_workspace.py and tests)

The following assertions and tests were added:

**`test_no_operator_ai_persona_in_agent_templates`** (test_verify_workspace.py): Scans all `templates/agents/*.agent.md.tmpl` to ensure `name: Operator` or `You are the Operator` does not appear (P-013.1 persona isolation). This is a template-level scan, not a workspace targeted check.

**`orchestrator_tier_fields`** (FOUNDATION_ASSERTIONS via `_add_frontmatter_tier_check()`): Validates that the installed `orchestrator.agent.md` declares `max_subagent_tier` as an integer in range 1–3 within its YAML frontmatter block. Rejects missing, string-valued, and out-of-range values. (As of 2026-07-11 `model_tier` is no longer required or validated — the base tier is config-resolved via `model_routing`.)

**`p013_policy_in_workflow_policies`** (FOUNDATION_ASSERTIONS): Verifies the installed `workflow-policies.md` contains P-013 and `max_subagent_tier` text (confirming the policy was installed).

**`test_all_agent_templates_have_max_subagent_tier_and_no_model_tier`** (test_verify_workspace.py): Confirms all agent template files declare `max_subagent_tier:` and that none declare `model_tier:` in their frontmatter. A companion **`test_no_agent_definition_declares_model_tier`** extends the same guard to installed instances under `.github/agents/`.

**`orchestrator_model_routing_fields` / `stage_model_routing_fields` / `ship_model_routing_fields`**
(`_add_frontmatter_model_routing_check()` in `verify_workspace.py`, wired per-agent gated on
`file_path.exists()`): validates that each installed pipeline agent (`_orchestrator.agent.md`,
`_stage.agent.md`, `_ship.agent.md`) declares a non-empty `model_family` and `model_provider`
in its YAML frontmatter, with no unresolved `{{...}}` placeholder. Unlike `orchestrator_tier_fields`
(called unconditionally), these three checks are only registered when the corresponding agent file
exists, so partial fixtures/workspaces that omit one of the three pipeline agents never register a
false failure. (104.007-T)

**`orchestrator_invocation_routing_directive`** (FOUNDATION_ASSERTIONS, gated on
`.github/agents/_orchestrator.agent.md` existing): verifies the installed Orchestrator's content
references `P-013.5`, `config.model_routing.stage`, `config.model_routing.ship`, and
`ROUTING_DEGRADED` — i.e., that the invocation-time routing directive was actually installed, not
merely documented in the template source. (104.008-T)

**`role_route_resolution`** (`_add_role_route_resolution_check()`, evaluated only when
`.autoharness/config.yaml` declares a `model_routing` block at all): verifies that the `stage` and
`ship` role routes each resolve to a non-empty `model_family`, either from an explicit
`model_routing.stage`/`model_routing.ship` route or via per-field fallback to
`model_routing.tier3`/`model_routing.tier2` respectively (`ROLE_ROUTE_TIER_FALLBACK`). Fails closed:
an unresolvable role route (no route, no fallback with a usable `model`/`model_family`) is a
verification failure rather than a silent pass. (104.008-T)

**Implementation note on `assert_tier_hierarchy`**: The strict caller/callee tier dependency graph check (e.g., flagging Orchestrator if `max_subagent_tier < Stage's model_tier`) was reviewed during deliberation and deferred. A static dependency graph cannot be reliably inferred from agent templates alone without a formal invocation registry. The `orchestrator_tier_fields` frontmatter check and the P-013 policy prose enforce the intent; a future `assert_tier_hierarchy` can be added when the dependency graph is formalized.

4. Rollout Strategy

Stash this plan as a raw requirement.

Stage it into an active shipment (e.g., 013-S).

Run Ship to execute the schema migrations, rename operations, update the installer variable resolution table, and add verify_workspace.py tests.
