---
description: "Reference architecture for the 8 irreducible harness primitives and how they compose into a complete agent harness"
applyTo: '**'
---

# Harness Architecture Instructions

This document defines the reference architecture for the 8 irreducible primitives that compose any effective agent harness. Use this as a guide when creating, modifying, or reviewing harness templates and installed harness artifacts.

autoharness operates as a global tool: templates and schemas live in the autoharness installation (`autoharness_home`), and only the generated harness artifacts are installed into target workspaces. All artifact paths below refer to locations in the target workspace after installation. The templates that produce them live in `{autoharness_home}/templates/`.

## Primitive 1: State and Context Management

**Purpose**: Maintain durable state across sessions, manage the context window, and prevent token overflow.

**Key Artifacts**:

* `memory.agent.md` — Persists session state to `.backlog/memory/`
* `compact-context/SKILL.md` — Archives stale tracking artifacts
* `compound/SKILL.md` — Captures institutional knowledge

**Design Rules**:

* Memory files use structured Markdown with YAML frontmatter for searchability
* Checkpoints capture: tasks completed, files modified, decisions, failed approaches, next steps
* Compaction triggers when file count exceeds threshold (default 40) or total size exceeds 500 KB
* Compound entries use searchable frontmatter fields: `problem_type`, `category`, `root_cause`, `tags`

## Primitive 2: Task Granularity and Horizon Scoping

**Purpose**: Decompose work to prevent exponential error compounding during agent execution.

**Key Artifacts**:

* Embedded in `AGENTS.md` (Task Granularity section)
* `backlog-harvester.agent.md` — Enforces granularity during decomposition
* `impl-plan/SKILL.md` — Produces granular implementation units

**Design Rules**:

* **2-Hour Rule**: Every task scoped to roughly 2 hours of human effort (fewer than 3 files, 5 functions, 4 test scenarios)
* **Width Isolation**: Each task targets a single skill domain
* **Atomic Milestone**: Every task produces a verifiable outcome (passing test, successful build)

**Rationale**: METR Time Horizons research shows agent reliability drops below 50% for tasks exceeding 2 hours and approaches 0% beyond 4 hours.

## Primitive 3: Model Routing and Escalation

**Purpose**: Match model capability to task complexity for cost efficiency and quality.

**Key Artifacts**:

* Agent definitions (each declares its tier)
* `build-orchestrator.agent.md` — Implements escalation logic

**Design Rules**:

* **Tier 1 (Fast/Cheap)**: Low-complexity tasks — memory, docs, prompt editing, knowledge search
* **Tier 2 (Standard)**: Routine tasks — orchestration, code writing, review coordination
* **Tier 3 (Frontier)**: Complex tasks — planning, architecture, specialized domain analysis
* **Escalation**: When a Tier 1/2 agent fails 3 consecutive times, escalate to Tier 3 before halting

## Primitive 4: Orchestration and Delegation

**Purpose**: Sequence agents through the feature lifecycle with clear handoffs and stop conditions.

**Key Artifacts**:

* `backlog-harvester.agent.md` — Planning pipeline (impl-plan → plan-review → harvest)
* `harness-architect.agent.md` — TDD harness generation
* `build-orchestrator.agent.md` — Implementation execution loop
* `pr-review.agent.md` — PR lifecycle management
* `build-feature/SKILL.md` — Harness loop execution
* `fix-ci/SKILL.md` — CI failure resolution

**Design Rules**:

* Pipeline: Brainstorm → Plan → Review → Harvest → Harness → Build → Review → PR → Fix-CI → Merge
* Each agent declares its maximum subagent depth
* Skills are leaf executors (no subagent spawning)
* Stop conditions prevent infinite loops (circuit breakers on task count, failure count, cycle count)
* Stall detection enforces timeouts on long-running commands

## Primitive 5: Tool Execution and Guardrails

**Purpose**: Allow agents to mutate the environment safely with policy enforcement.

**Key Artifacts**:

* `constitution.instructions.md` — Principles III-V (workspace isolation, containment, destructive approval)
* `workflow-policies.md` — P-001 through P-005

**Design Rules**:

* File creation and modification proceed directly (non-destructive)
* Destructive operations (deletion, directory removal) require approval workflow
* CLI workspace containment: no writes outside cwd
* Feature flags gate new agent-generated modules to prevent system instability
* Terminal commands run one at a time (no chaining)

## Primitive 6: Injection Points and Dynamic Reminders

**Purpose**: Surface critical constraints exactly when the agent needs them, not as front-loaded system prompt bulk.

**Key Artifacts**:

* Instruction files with `applyTo` glob patterns
* `build-feature/SKILL.md` — Instruction reinforcement at each fix iteration
* `build-orchestrator.agent.md` — Constitution re-read at session start

**Design Rules**:

* Instructions use `applyTo` patterns to scope rules to relevant file types
* Agents re-read coding standards before every fix attempt (instruction reinforcement)
* Technology-specific instructions are loaded only when touching files of that type
* The constitution is re-read at session start and phase boundaries

## Primitive 7: Observability and Evaluation

**Purpose**: Track agent efficacy and output quality through automated evaluation.

**Key Artifacts**:

* Review persona agents (`review/` directory)
* `review/SKILL.md` — Multi-persona code review
* `plan-review/SKILL.md` — Multi-persona plan review
* `compound/SKILL.md` — Post-mortem knowledge capture

**Design Rules**:

* Review personas are leaf executors with domain-specific focus
* Always-on personas review every change; conditional personas activate based on diff content
* Findings use a 4-level severity system (P0-P3) with action classes (safe_auto, gated_auto, manual, advisory)
* Cross-model diversity is preferred (different models for different personas) but not blocking
* Compound learnings capture hard-won solutions for future reference

## Primitive 8: Workflow Policy

**Purpose**: Enforce cross-agent sequencing, gate conditions, and violation handling.

**Key Artifacts**:

* `workflow-policies.md` — Policy registry with P-001 through P-005
* Agent definitions (each references applicable policies at gate points)

**Design Rules**:

* Policies are declarative: precondition, postcondition, gate point, violation action
* P-001: Single-feature completion (no parallel features)
* P-002: TDD gate (`harness-ready` label required before implementation)
* P-003: Decomposition chain integrity (validated parent-child references)
* P-004: Red phase before implementation (tests compile and fail)
* P-005: Policy violation telemetry (all violations recorded and broadcast)
* Policy violations are first-class observability signals

## Primitive Interaction Map

```text
┌─────────────────────────────────────────────────────┐
│ 8. Workflow Policy                                   │
│   Governs sequencing across all other primitives     │
├─────────────────────────────────────────────────────┤
│                                                       │
│  2. Task Granularity ──→ 4. Orchestration            │
│     (scope work)            (execute pipeline)        │
│         │                        │                    │
│         ▼                        ▼                    │
│  3. Model Routing ───→ 5. Guardrails                 │
│     (assign models)       (enforce safety)            │
│         │                        │                    │
│         ▼                        ▼                    │
│  6. Injection Points    7. Observability              │
│     (surface rules)       (evaluate output)           │
│         │                        │                    │
│         └────────┬───────────────┘                    │
│                  ▼                                    │
│         1. State & Context                            │
│            (persist everything)                       │
│                                                       │
└─────────────────────────────────────────────────────┘
```
