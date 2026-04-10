---
description: "Reference architecture for the 10 irreducible harness primitives and how they compose into a complete agent harness"
applyTo: '**'
---

# Harness Architecture Instructions

This document defines the reference architecture for the 10 irreducible primitives that compose any effective agent harness. Use this as a guide when creating, modifying, or reviewing harness templates and installed harness artifacts.

autoharness operates as a global tool: templates and schemas live in the autoharness installation (`autoharness_home`), and only the generated harness artifacts are installed into target workspaces. All artifact paths below refer to locations in the target workspace after installation. The templates that produce them live in `{autoharness_home}/templates/`.

## Capability-Pack Overlay Pattern

Capability packs are optional **overlay compositions** applied on top of the 10 primitives. They are not additional primitives and must not be treated as substitute architecture layers.

### Overlay Rules

* A capability pack may deepen one or more primitives, but it must not redefine the primitive model
* Packs are applied **after** base primitive selection and **before** installation verification
* Packs may touch multiple artifact classes at once: foundation docs, instruction files, agent definitions, skills, prompts, and policies
* Packs must be woven coherently across all declared targets; a single isolated instruction file is not sufficient for a cross-cutting pack
* Packs must remain optional. If disabled, the base primitive system still forms a coherent harness

### Required Overlay Contract

Every capability pack definition must include:

* **Eligibility signals** — workspace markers that justify recommending the pack
* **Recommendation logic** — how workspace discovery decides the pack should be proposed
* **Overlay targets** — the exact artifacts or artifact classes affected by the pack
* **Behavior deltas** — the workflow differences that appear when the pack is enabled
* **Verification checks** — installation-time checks proving the overlay was applied consistently
* **Tuning drift checks** — how tuning detects that the overlay is stale, missing, or partially woven

### Example

The `agent-intercom` pack is a model overlay because it changes how the harness behaves across multiple primitives and artifacts:

* Primitive 4 — orchestration agents announce milestones and use operator wait flows
* Primitive 5 — destructive actions route through approval workflows
* Primitive 6 — intercom instructions are injected at the right moments
* Primitive 7 / 10 — review, verification, and closure broadcast status and degraded-mode signals

This is why `agent-intercom` must be woven through the harness rather than installed as a single detached add-on.

## Primitive 1: State, Context, and Knowledge Retrieval

**Purpose**: Maintain durable state across sessions, retrieve relevant prior learnings at the point of work, manage the context window, and prevent token overflow.

**Key Artifacts**:

* `stage.agent.md` — Session state persistence is inline in both primary agents
* `research/learnings-researcher.agent.md` — Retrieves relevant prior solutions before planning and review
* `compact-context/SKILL.md` — Mandatory workflow step: consolidates memory, plans, and closure artifacts in the docs root; archives verbose originals to docs/archive/
* `compound/SKILL.md` — Captures institutional knowledge to `docs/compound/` (default; configurable)

**Design Rules**:

* Memory files use structured Markdown with YAML frontmatter for searchability
* Checkpoints capture: tasks completed, files modified, decisions, failed approaches, next steps
* Learnings retrieval runs before planning and review work, not just after failures
* Compact-context is a mandatory workflow step (invoked by stage or ship agent at checkpoint threshold and at batch completion), not an advisory suggestion
* Session continuity protocols in stage and ship agents handle state persistence at Tier 1 (Fast/Cheap) — recommended model: GPT-5.4-mini or equivalent
* Compaction triggers when file count exceeds threshold (default 40) or total size exceeds 500 KB
* Compound entries use searchable frontmatter fields: `problem_type`, `category`, `root_cause`, `tags`

## Primitive 2: Task Granularity and Horizon Scoping

**Purpose**: Decompose work to prevent exponential error compounding during agent execution.

**Key Artifacts**:

* Embedded in `AGENTS.md` (Task Granularity section)
* `stage.agent.md` — Enforces granularity during decomposition via harvest skill
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
* `ship.agent.md` — Implements escalation logic

**Design Rules**:

* **Tier 1 (Fast/Cheap)**: Low-complexity tasks — memory, docs, prompt editing, knowledge search
* **Tier 2 (Standard)**: Routine tasks — orchestration, code writing, review coordination
* **Tier 3 (Frontier)**: Complex tasks — planning, architecture, specialized domain analysis
* **Escalation**: When a Tier 1/2 agent fails 3 consecutive times, escalate to Tier 3 before halting

## Primitive 4: Orchestration, Delegation, and Lifecycle Handoffs

**Purpose**: Sequence agents through the feature/chore lifecycle with clear handoffs, preserved release context, and stop conditions.

**Key Artifacts**:

* `stage.agent.md` — Stash-to-backlog pipeline (triage → deliberate/spike → impl-plan → plan-review → harvest)
* `ship.agent.md` — Backlog-to-shipped pipeline (harness → build → review → PR → fix-ci → closure)
* `harness-architect/SKILL.md` — TDD harness generation
* `build-feature/SKILL.md` — Harness loop execution
* `deliberate/SKILL.md` — Structured deliberation and decision capture
* `spike/SKILL.md` — Time-boxed investigation and findings capture
* `fix-ci/SKILL.md` — CI failure resolution
* `pr-lifecycle/SKILL.md` — PR creation and follow-up
* `runtime-verification/SKILL.md` — Runtime surface validation before closure
* `operational-closure/SKILL.md` — Release readiness, monitoring, and feedback capture

**Design Rules**:

* Pipeline: Deliberate/Spike → Plan → Review → Harvest → Harness → Build → Review → PR → Fix-CI → Runtime Verification → Operational Closure
* Each agent declares its maximum subagent depth
* Skills are leaf executors (no subagent spawning)
* Handoff contracts preserve verification and closure expectations from planning through release
* Stop conditions prevent infinite loops (circuit breakers on task count, failure count, cycle count)
* Stall detection enforces timeouts on long-running commands

## Primitive 5: Tool Execution, Safety Modes, and Guardrails

**Purpose**: Allow agents to mutate the environment safely with policy enforcement, interactive safety modes, and architectural boundary protection.

**Key Artifacts**:

* `constitution.instructions.md` — Principles III-V (workspace isolation, containment, destructive approval)
* `workflow-policies.md` — P-001 through P-005
* `safety-modes/SKILL.md` — Interactive careful / freeze-scope / investigate-first workflows
* Custom architectural linters — Enforce dependency direction, naming, and layering (generated per workspace)

**Design Rules**:

* File creation and modification proceed directly (non-destructive)
* Safety modes are explicit and user-legible when risk increases
* Destructive operations (deletion, directory removal) require approval workflow
* CLI workspace containment: no writes outside cwd
* Feature flags gate new agent-generated modules to prevent system instability
* Terminal commands run one at a time (no chaining)
* Architectural linters enforce structural boundaries with agent-readable error messages
* Lint error messages include remediation instructions so agents can self-correct

## Primitive 6: Injection Points and Dynamic Reminders

**Purpose**: Surface critical constraints exactly when the agent needs them, not as front-loaded system prompt bulk.

**Key Artifacts**:

* Instruction files with `applyTo` glob patterns
* `build-feature/SKILL.md` — Instruction reinforcement at each fix iteration
* `ship.agent.md` — Constitution re-read at session start

**Design Rules**:

* Instructions use `applyTo` patterns to scope rules to relevant file types
* Agents re-read coding standards before every fix attempt (instruction reinforcement)
* Technology-specific instructions are loaded only when touching files of that type
* The constitution is re-read at session start and phase boundaries

## Primitive 7: Observability and Evaluation

**Purpose**: Track agent efficacy and output quality through automated evaluation, and continuously manage codebase entropy.

**Key Artifacts**:

* Review persona agents (`review/` directory)
* `review/SKILL.md` — Multi-persona code review
* `plan-review/SKILL.md` — Multi-persona plan review
* `compound/SKILL.md` — Post-mortem knowledge capture
* Ship agent post-merge closure — Documentation gardening and entropy cleanup

**Design Rules**:

* Review personas are leaf executors with domain-specific focus
* Always-on personas review every change; conditional personas activate based on diff content
* Findings use a 4-level severity system (P0-P3) with action classes (safe_auto, gated_auto, manual, advisory)
* Cross-model diversity is preferred (different models for different personas) but not blocking
* Compound learnings capture hard-won solutions for future reference
* Entropy management: the ship agent's post-merge closure scans for pattern deviations, updates quality grades, and applies documentation fixes
* Cleanup functions as garbage collection — paying down technical debt continuously in small increments

## Primitive 8: Workflow Policy

**Purpose**: Enforce cross-agent sequencing, gate conditions, and violation handling.

**Key Artifacts**:

* `workflow-policies.md` — Policy registry with P-001 through P-005
* Agent definitions (each references applicable policies at gate points)

**Design Rules**:

* Policies are declarative: precondition, postcondition, gate point, violation action
* P-001: Single top-level release-unit completion (no parallel features or chores)
* P-002: TDD gate (`harness-ready` label required before implementation)
* P-003: Decomposition chain integrity (validated parent-child references)
* P-004: Red phase before implementation (tests compile and fail)
* P-005: Policy violation telemetry (all violations recorded and broadcast)
* Policy violations are first-class observability signals

## Primitive 9: Repository Knowledge and Agent Legibility

**Purpose**: Structure the repository as a navigable, self-maintaining knowledge base that agents can reason over through progressive disclosure.

**Key Artifacts**:

* `AGENTS.md` — Short entry point (~100 lines) serving as table of contents, not encyclopedia
* `docs/ARCHITECTURE.md` — Top-level map of domains, package layering, and dependency direction
* `docs/` directory — Durable knowledge (design docs, product specs, quality grades, references)
* Ship agent post-merge closure — Documentation gardening that scans for stale docs, applies fixes, and graduates knowledge from completed backlog work
* `architecture-doc.instructions.md` — Rules for maintaining architecture documentation

**Design Rules**:

* AGENTS.md is a map, not a manual — agents start with a small entry point and are taught where to look next
* Repository knowledge is the system of record — anything not discoverable in the repo doesn't exist to the agent
* `docs/` holds durable knowledge; the backlog directory holds active work items — different lifecycles, different concerns
* Knowledge graduation: when backlog work completes, architectural decisions and design rationale are distilled into `docs/design-docs/`; compound learnings are stored in `docs/compound/` (default; configurable) — NOT in the backlog
* Documentation is mechanically validated: CI checks verify freshness, cross-links, and structural correctness
* Doc-gardening runs as part of ship agent post-merge closure, scanning for obsolete content that no longer reflects code
* Progressive disclosure depth scales with codebase complexity
* Quality grades per domain track which areas are well-documented vs. fragile

## Primitive 10: Operational Closure and Feedback

**Purpose**: Ensure changes are not only implemented but safely validated, observed, and fed back into the harness after review and CI.

**Key Artifacts**:

* `runtime-verification/SKILL.md` — Validates affected runtime surfaces with the appropriate depth
* `operational-closure/SKILL.md` — Produces release-readiness, monitoring, rollback, and follow-up artifacts
* `ship.agent.md` — Carries verification and closure expectations into PR descriptions via pr-lifecycle skill
* `fix-ci/SKILL.md` — Ensures green CI is not the final stop when runtime validation is still required

**Design Rules**:

* Green tests are necessary but not sufficient; runtime validation requirements must be explicit
* Closure artifacts record healthy signals, failure signals, validation windows, rollback triggers, and owner
* Runtime findings feed back into compound learnings, documentation updates, and tuning proposals
* Primitive 10 is the formal handoff from “implemented” to “safely absorbed by the running system”

## Primitive Interaction Map

```text
┌────────────────────────────────────────────────────────────┐
│ 8. Workflow Policy                                          │
│   Governs sequencing across all other primitives            │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  2. Task Granularity ──→ 4. Orchestration                    │
│     (scope work)            (execute pipeline + handoffs)    │
│         │                        │                           │
│         ▼                        ▼                           │
│  3. Model Routing ───→ 5. Guardrails                         │
│     (assign models)       (enforce safety + boundaries)      │
│         │                        │                           │
│         ▼                        ▼                           │
│  6. Injection Points    7. Observability                     │
│     (surface rules)       (evaluate output + manage entropy) │
│         │                        │                           │
│         └────────────┬───────────┘                           │
│                      ▼                                       │
│   10. Operational Closure & Feedback                         │
│       (verify runtime, monitor outcomes, feed learnings)     │
│                      │                                       │
│                      ▼                                       │
│  9. Repo Knowledge ──→ 1. State & Context                    │
│     (structure the       (persist + retrieve everything)     │
│      knowledge base)                                         │
│                                                              │
└────────────────────────────────────────────────────────────┘
```
