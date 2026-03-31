---
title: The 8 Irreducible Harness Primitives
description: Deep documentation of each primitive, its purpose, implementation patterns, and how autoharness adapts it per workspace
---

## Overview

Through empirical evaluation of production agent harnesses, we identified 8 irreducible primitives that every effective harness implements. These primitives are technology-agnostic: a Rust project, a TypeScript monorepo, and a Python ML pipeline all need the same structural elements, though the specific implementations differ.

autoharness packages these primitives as customizable templates. The workspace-discovery skill identifies which technology-specific adaptations are needed, and the install-harness skill composes the final artifacts.

## Primitive 1: State and Context Management

### The Problem

AI agents operate within finite context windows. Long-running sessions accumulate memory files, checkpoint files, and tracking artifacts that dilute the semantic density of the context. Without active management, agents experience "model drift" where adherence to core instructions degrades as the context fills with historical noise.

### The Solution

Three interconnected mechanisms manage state and context:

1. **Memory Agent**: Persists session state in structured Markdown with YAML frontmatter. Supports manual saves (user-invoked) and checkpoints (build-orchestrator-invoked). Every checkpoint captures tasks completed, files modified, decisions made, failed approaches, and next steps.

2. **Compact-Context Skill**: Monitors tracking artifact volume. When files exceed thresholds (default: 40 files or 500 KB), it summarizes and archives verbose originals, preserving only the dense, high-signal content.

3. **Compound Skill**: Captures hard-won solutions (build errors, debugging insights, configuration gotchas) in a searchable library. The learnings-researcher subagent retrieves relevant past solutions when similar problems recur.

### Adaptation Points

* Memory file paths adapt to the workspace's directory structure
* Compaction thresholds are configurable per workspace
* Compound categories adapt to the workspace's technology domain

## Primitive 2: Task Granularity and Horizon Scoping

### The Problem

Agent reliability drops below 50% for tasks exceeding 2 hours of human-equivalent effort and approaches 0% beyond 4 hours (METR Time Horizons research). Sequential error compounding means that each step in a long task has a probability of failure, and these probabilities multiply across steps.

### The Solution

Three constraints enforce proper granularity:

1. **2-Hour Rule**: Every task is scoped to roughly 2 hours of human effort. Heuristics: fewer than 3 files modified, fewer than 5 functions changed, fewer than 4 test scenarios. These heuristics approximate 2 hours because a focused developer can typically review and implement changes across 2-3 files in that timeframe.

2. **Width Isolation**: Each task targets a single skill domain. Code changes, documentation updates, test infrastructure, and configuration modifications are separate tasks. This prevents context-switching within a task, which is where agents most commonly introduce errors.

3. **Atomic Milestone**: Every task must produce a verifiable state change: a passing test, a successful build, or a measurable output. This creates natural checkpoints where the agent can validate its work before proceeding.

### Adaptation Points

* The heuristics (file count, function count, test count) may be adjusted for different codebases
* Domain boundaries depend on the workspace's technology stack (e.g., "infrastructure" means Terraform in one workspace and Docker in another)

## Primitive 3: Model Routing and Escalation

### The Problem

Using a single, expensive frontier model for all tasks wastes compute on low-complexity work. Conversely, routing complex architectural decisions to a fast/cheap model produces poor results. Without explicit routing, all agents default to whatever model the IDE is configured with.

### The Solution

Agents are assigned to model tiers based on task complexity:

| Tier | Model Class | Typical Agents | Use Cases |
|---|---|---|---|
| **Tier 1** | Fast/Cheap | memory, doc-ops, prompt-builder, learnings-researcher | State persistence, docs, prompt editing |
| **Tier 2** | Standard | build-orchestrator, pr-review, language-engineer | Code writing, orchestration, review |
| **Tier 3** | Frontier | backlog-harvester, harness-architect | Architecture, planning, complex analysis |

**Escalation**: When a Tier 1 or Tier 2 agent fails 3 consecutive times, the orchestrator escalates to a Tier 3 model and retries before halting. This prevents cheaper models from being stuck on tasks above their capability.

### Adaptation Points

* Specific model names are not hardcoded — they depend on what the user has access to
* The tier assignments may shift based on the workspace's complexity
* Escalation thresholds are configurable

## Primitive 4: Orchestration and Delegation

### The Problem

Building a feature involves multiple distinct capabilities: planning, test harness construction, implementation, code review, and CI management. No single agent can perform all of these well, and attempting to do so within one context window leads to context overflow and instruction confusion.

### The Solution

A pipeline of specialized agents, each with a narrow role:

1. **Brainstorm Skill**: Explore requirements through dialogue
2. **Backlog Harvester**: Plan → review → decompose into tasks
3. **Harness Architect**: Generate test harnesses and stubs (TDD gate)
4. **Build Orchestrator**: Claim tasks, delegate to build-feature skill, verify quality
5. **PR Review**: Analyze diff, delegate to review personas, create PR
6. **Fix-CI**: Resolve CI failures and review comments

**Stop conditions** prevent infinite loops:

* Task count limits (max 20 per session)
* Consecutive failure limits (max 3 before escalation)
* Cycle limits on review-fix and CI-fix loops
* Stall timeouts on long-running commands

### Adaptation Points

* Build/test/lint commands differ per technology
* CI pipeline order varies across platforms
* Stall timeouts may need adjustment for slower build systems

## Primitive 5: Tool Execution and Guardrails

### The Problem

Agents operating with filesystem access can create, modify, or delete any file. Without guardrails, a hallucinating agent could overwrite core configuration, delete source files, or execute destructive terminal commands.

### The Solution

Layered safety controls:

1. **Workspace containment**: All file operations resolve within the workspace root
2. **Non-destructive direct writes**: File creation and modification proceed without approval
3. **Destructive approval workflow**: Deletions and removals require operator approval
4. **Terminal command policy**: Destructive commands require approval regardless of permissive flags
5. **Feature flags**: New agent-generated modules are gated behind feature flags

### Adaptation Points

* Approval workflow integration depends on available communication channels
* Terminal command auto-approve patterns are workspace-specific
* Feature flag mechanisms differ by technology

## Primitive 6: Injection Points and Dynamic Reminders

### The Problem

Front-loading all instructions into a system prompt creates the "lost in the middle" phenomenon: agents forget rules by step 5 of a multi-step task because the instructions are buried in a long context preamble.

### The Solution

Instructions are loaded dynamically based on relevance:

1. **applyTo patterns**: Instruction files declare glob patterns. An instruction about Rust conventions loads only when the agent touches `.rs` files.

2. **Instruction reinforcement**: The build-feature skill re-reads coding standards before every fix attempt. The build-orchestrator re-reads constitution principles at session start.

3. **Definition of Done checks**: Before completing a task, agents verify acceptance criteria from the task file.

### Adaptation Points

* `applyTo` patterns match the workspace's file extensions and directory structure
* Which instructions are "always-on" versus "conditional" depends on the technology mix
* Reinforcement points map to the workspace's build/test cycle

## Primitive 7: Observability and Evaluation

### The Problem

Agents run autonomously for extended periods. Without evaluation mechanisms, low-quality outputs propagate unchecked until a human reviews the PR, by which time the cost of rework is high.

### The Solution

Multi-persona review evaluates every change from multiple perspectives:

1. **Always-on reviewers**: Constitution compliance and language-specific safety/correctness
2. **Conditional reviewers**: Architecture, concurrency, scope boundary — activated based on diff content
3. **Cross-model diversity**: When possible, different reviewer personas use different models to reduce blind spots

Findings use a structured severity and action system:

* Severities: P0 (critical) → P3 (advisory)
* Actions: safe_auto, gated_auto, manual, advisory

Compound learnings capture post-mortem insights for future reference.

### Adaptation Points

* Review personas adapt to the workspace's technology (Rust safety → Python type safety, etc.)
* Conditional activation patterns match the workspace's concurrency and architecture patterns
* Severity definitions may need calibration for different codebases

## Primitive 8: Workflow Policy

### The Problem

Agent definitions describe what an agent does, but nothing prevents invoking agents out of sequence. Without cross-agent policies, the build-orchestrator could claim a task before the harness-architect generates the test harness, violating the TDD mandate.

### The Solution

A declarative policy registry defines:

* **Gate points**: Specific moments where policies are checked
* **Preconditions**: What must be true before proceeding
* **Postconditions**: What must hold after the step completes
* **Violation actions**: What to do when a policy is breached

Five core policies:

| Policy | Gate | Purpose |
|---|---|---|
| P-001 | Build orchestrator pre-flight | Only one feature in progress at a time |
| P-002 | Task claiming | TDD gate — `harness-ready` label required |
| P-003 | Pre-harvest | Decomposition chain integrity validated |
| P-004 | Harness approval | Red phase confirmed before implementation |
| P-005 | Any violation | All violations recorded as telemetry |

### Adaptation Points

* Policy violation actions depend on available communication channels
* Gate points map to the workspace's specific pipeline stages
* Additional policies may be needed for domain-specific concerns
