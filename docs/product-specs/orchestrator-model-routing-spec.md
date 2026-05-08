---
title: "Execution Plan: P-013 Orchestrator Persona and Model Tier Routing"
date: 2026-05-07
problem_type: architectural-spec
category: harness-design
tags: [p-013, model-routing, persona-isolation, orchestrator]
status: pending
---

## Execution Plan: P-013 Orchestrator Persona and Model Tier Routing

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

Every agent and skill template MUST declare:

## Replaces unstructured 'model_routing'

model_tier: 2             # The base tier this entity runs on
max_subagent_tier: 3      # The maximum tier it is authorized to invoke

## Environment-configurable overrides (resolved via config.yaml)

reasoning_effort: "{{TIER_2_REASONING_EFFORT}}"  
model_provider: "{{TIER_2_PROVIDER}}"  
model_family: "{{TIER_2_FAMILY}}"  

Environment Agnosticism Constraint: To satisfy Core Rule 3 (Environment Agnosticism), the fields reasoning_effort, model_provider, and model_family MUST NOT be hardcoded to specific vendor strings (e.g., "anthropic" or "high") in the .tmpl files. They must be parameterized using {{VARIABLE}} syntax and resolved strictly from .autoharness/config.yaml during the auto-mergeinstall and auto-tune routines.

P-013.4: Upward/Downward Invocation Protocol

Sub-agent invocations must explicitly declare the required tier. Orchestrator (Tier 2) must explicitly request a Tier 3 invocation when calling Stage.

Agent prompt instructions must reflect this syntax. For example, Orchestrator's prompt must contain:

"To invoke the Stage agent, you must execute the subagent tool with --tier 3 to allocate sufficient reasoning capacity for backlog synthesis."

3. Required Artifact Modifications

Phase 1: Nomenclature & Migration

Rename File: templates/agents/dispatch.agent.md.tmpl -> templates/agents/orchestrator.agent.md.tmpl.

Update Content: Replace all internal references from "Dispatch" to "Orchestrator". Retain existing references to "Operator" ONLY when referring to pausing/halting for human review.

Update Manifest: Modify install-harness/SKILL.md (Step 2.4 and Primitive 4 mappings) to wire orchestrator instead of dispatch.

Phase 2: Schema & Frontmatter Enforcement

Modify App Schemas: Update schemas/harness-manifest.schema.json to require model_tier (integer 1-3) and max_subagent_tier (integer 1-3). Make reasoning_effort, model_provider, and model_family optional string fields. Deprecate model_routing.

Modify Config Schemas: Update schemas/harness-config.schema.json to support a new model_routing block where users define their preferred mappings (e.g., defining TIER_2_REASONING_EFFORT: "high").

Update Agent Templates:

orchestrator.agent.md.tmpl: model_tier: 2, max_subagent_tier: 3 (plus parameterized overrides)

ship.agent.md.tmpl: model_tier: 2, max_subagent_tier: 2 (plus parameterized overrides)

stage.agent.md.tmpl: model_tier: 3, max_subagent_tier: 3 (plus parameterized overrides)

adversarial-review.agent.md.tmpl: model_tier: 3, max_subagent_tier: 1 (plus parameterized overrides)

Update Policy Docs: Append P-013 to templates/policies/workflow-policies.md.tmpl.

Phase 3: Assertion Coverage (verify_workspace.py)

Add the following assertions to src/autoharness/verify_workspace.py:

assert_no_operator_persona: Scans all templates/agents/*.md.tmpl to ensure name: Operator or You are the Operator does not exist.

assert_tier_schema_validity: Verifies all frontmatter YAML contains integer bounds for model_tier and max_subagent_tier.

assert_tier_hierarchy: Validates that no agent's model_tier exceeds its caller's max_subagent_tier within known dependency graphs (e.g., if Orchestrator has max_subagent_tier: 2, it would flag a failure when trying to map Stage which requires model_tier: 3).

4. Rollout Strategy

Stash this plan as a raw requirement.

Stage it into an active shipment (e.g., 013-S).

Run Ship to execute the schema migrations, rename operations, update the installer variable resolution table, and add verify_workspace.py tests.
