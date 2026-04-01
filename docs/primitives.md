---
title: The 9 Irreducible Harness Primitives
description: Deep documentation of each primitive, its purpose, implementation patterns, and how autoharness adapts it per workspace
---

## Overview

Through empirical evaluation of production agent harnesses, we identified 9 irreducible primitives that every effective harness implements. These primitives are technology-agnostic: a Rust project, a TypeScript monorepo, and a Python ML pipeline all need the same structural elements, though the specific implementations differ.

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
6. **Architecture enforcement**: Custom linters and structural tests enforce dependency direction, naming conventions, and layering boundaries. Lint error messages are written for agent consumption, providing remediation instructions directly in context. Agents operate within strict boundaries but have freedom in implementation within those boundaries.

### Adaptation Points

* Approval workflow integration depends on available communication channels
* Terminal command auto-approve patterns are workspace-specific
* Feature flag mechanisms differ by technology
* Architecture enforcement linters are generated from the workspace's layering model and naming conventions
* Lint error messages adapt to the primary language's toolchain (clippy for Rust, eslint for TypeScript, ruff for Python)

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

4. **Entropy management and continuous cleanup**: Agents replicate patterns already present in the repository — including suboptimal ones. Over time, this leads to drift and architectural decay. Background cleanup agents run on a regular cadence to scan for deviations from established patterns, update quality grades, and open targeted refactoring PRs. This functions like garbage collection: technical debt is paid down continuously in small increments rather than compounding into painful bursts.

### Adaptation Points

* Review personas adapt to the workspace's technology (Rust safety → Python type safety, etc.)
* Conditional activation patterns match the workspace's concurrency and architecture patterns
* Severity definitions may need calibration for different codebases
* Entropy management cadence depends on the workspace's change velocity and team size
* Cleanup scope is technology-specific (pattern deduplication, naming alignment, dependency hygiene)

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

## Primitive 9: Repository Knowledge and Agent Legibility

### The Problem

Agents can only reason about what they can see in context. Knowledge that lives in chat threads, Google Docs, or people's heads is invisible to the agent. When the repository lacks structured, navigable documentation, agents guess at architecture, repeat solved problems, and make decisions that conflict with established patterns. A monolithic instruction file (the "one big AGENTS.md" approach) fails because it crowds out the task, makes everything equally "important," rots instantly, and resists mechanical validation.

OpenAI's harness engineering experiment validated this: *"give Codex a map, not a 1,000-page instruction manual."*

### The Solution

The repository is structured as a self-maintaining knowledge base that agents can navigate through progressive disclosure:

1. **AGENTS.md as table of contents**: A short (~100 line) entry point that serves as a map to deeper sources of truth. It points agents to the right documentation rather than containing everything itself.

2. **Structured knowledge directory**: A `docs/` directory treated as the system of record:
   * `ARCHITECTURE.md` — Top-level map of domains, package layering, and dependency direction
   * `design-docs/` — Catalogued design documentation with verification status
   * `exec-plans/` — Active and completed execution plans with progress logs
   * `product-specs/` — Product requirements and acceptance criteria
   * `references/` — External documentation relevant to the codebase (llms.txt files, API docs)
   * Quality grades per domain — tracking which areas are well-covered vs. fragile

3. **Progressive disclosure**: Agents start with a small, stable entry point and are taught where to look next, rather than being overwhelmed up front. Each level of documentation points deeper when needed.

4. **Doc-gardening agent**: A background agent that runs on a regular cadence to scan for stale or obsolete documentation that no longer reflects the codebase. It opens targeted fix-up PRs to keep documentation in sync with code. This prevents the knowledge base from rotting.

5. **Mechanical enforcement**: CI-integrated checks validate that the knowledge base is up to date, cross-linked, and structurally correct. Custom linters verify documentation freshness, coverage, and ownership.

### Adaptation Points

* The `docs/` directory structure adapts to the workspace's existing documentation patterns
* Doc-gardening frequency depends on the workspace's change velocity
* Progressive disclosure depth varies by codebase complexity (a small CLI tool needs less than a large monorepo)
* Architecture documentation captures whatever layering and domain boundaries the workspace uses
* Quality grading categories adapt to the workspace's technology domains
