---
title: The 10 Irreducible Harness Primitives
description: Deep documentation of each primitive, its purpose, implementation patterns, and how autoharness adapts it per workspace
---

## Overview

Through empirical evaluation of production agent harnesses, we identified 10 irreducible primitives that every effective harness implements. These primitives are technology-agnostic: a Rust project, a TypeScript monorepo, and a Python ML pipeline all need the same structural elements, though the specific implementations differ.

autoharness packages these primitives as customizable templates. The workspace-discovery skill identifies which technology-specific adaptations are needed, and the install-harness skill composes the final artifacts.

## Capability packs are overlays, not primitives

Capability packs are the mechanism autoharness uses for optional, cross-cutting composition on top of the 10 primitives.

They do **not** add an eleventh primitive. Instead, a pack deepens existing primitives by weaving coordinated changes across multiple artifacts. For example, `agent-intercom` strengthens Primitive 4 (handoffs), Primitive 5 (approval routing), Primitive 6 (instruction injection), and Primitive 7/10 (operator visibility and closure signaling) without redefining the primitive model itself.

Every formal capability pack follows the same overlay contract:

1. **Eligibility signals** discovered from the workspace profile
2. **Recommendation logic** that proposes the pack during discovery
3. **Overlay targets** listing the artifacts that must be updated together
4. **Behavior deltas** that describe what the enabled harness does differently
5. **Verification checks** that confirm the pack is fully woven after installation
6. **Tuning drift rules** that detect stale or partially applied overlays over time

The full pattern lives in [Capability Packs](capability-packs.md).

## Primitive 1: State, Context, and Knowledge Retrieval

### The Problem

AI agents operate within finite context windows and finite recall. Long-running sessions accumulate memory files, checkpoint files, and tracking artifacts that dilute the semantic density of the context. Even worse, solved problems from prior work are frequently invisible at the moment a new plan or review is being produced. Without active management and retrieval, agents repeat mistakes, re-run investigations, and lose adherence to core instructions as the context fills with historical noise.

### The Solution

Four interconnected mechanisms manage state, recall, and retrieval:

1. **Session Continuity Protocols**: State persistence is inline in the stage and ship agents. Every checkpoint captures tasks completed, files modified, decisions made, failed approaches, and next steps.

2. **Learnings Researcher**: Searches the compound library before planning and review work begins. Retrieval is not optional bookkeeping; it is the mechanism that turns institutional knowledge into immediate task context.

3. **Compact-Context Skill**: Monitors tracking artifact volume. When files exceed thresholds (default: 40 files or 500 KB), it summarizes and archives verbose originals, preserving only the dense, high-signal content.

4. **Compound Skill**: Captures hard-won solutions (build errors, debugging insights, configuration gotchas) in a searchable library with reusable tags, categories, and citations back to the originating task, plan, or PR.

### Adaptation Points

* Memory file paths adapt to the workspace's directory structure
* Retrieval scope adapts to where durable learnings live (`docs/compound/`, `docs/decisions/`, or configured paths)
* Compaction thresholds are configurable per workspace
* Compound categories and ranking heuristics adapt to the workspace's technology domain

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
| **Tier 1** | Fast/Cheap | prompt-builder, learnings-researcher | Prompt editing, knowledge search |
| **Tier 2** | Standard | ship, language-engineer | Code writing, orchestration, review |
| **Tier 3** | Frontier | stage, harness-architect | Architecture, planning, complex analysis |

**Escalation**: When a Tier 1 or Tier 2 agent fails 3 consecutive times, the orchestrator escalates to a Tier 3 model and retries before halting. This prevents cheaper models from being stuck on tasks above their capability.

### Adaptation Points

* Specific model names are not hardcoded — they depend on what the user has access to
* The tier assignments may shift based on the workspace's complexity
* Escalation thresholds are configurable

## Primitive 4: Orchestration, Delegation, and Lifecycle Handoffs

### The Problem

Shipping a top-level release unit — whether a feature or a chore — involves multiple distinct capabilities: planning, test harness construction, implementation, code review, runtime verification, and CI management. No single agent can perform all of these well, and attempting to do so within one context window leads to context overflow and instruction confusion. Even when the implementation itself succeeds, many harnesses fail at the handoff boundaries: planning knowledge does not reach implementation, PR metadata does not reach deployment validation, and finished work never enters a structured closure loop.

### The Solution

A pipeline of specialized agents, each with a narrow role and explicit handoff expectations:

1. **Deliberate Skill**: Explore requirements, research options, and capture decisions through structured operator dialogue
2. **Spike Skill**: Execute time-boxed investigations to answer technical questions, evaluate feasibility, and capture findings
3. **Stage Agent**: Triage stash → deliberate/spike → plan → review → harvest into backlog
4. **Harness Architect**: Generate test harnesses and stubs (TDD gate)
5. **Ship Agent**: Claim tasks, delegate to build-feature skill, verify quality, manage review/CI/PR lifecycle, runtime verification, and operational closure
6. **Fix-CI**: Resolve CI failures and review comments while preserving release readiness context
7. **Runtime Verification**: Validate runtime behavior against the surfaces changed by the work
8. **Operational Closure**: Convert implementation success into release readiness, monitoring intent, and structured follow-up

**Stop conditions** prevent infinite loops:

* Task count limits (max 20 per session)
* Consecutive failure limits (max 3 before escalation)
* Cycle limits on review-fix and CI-fix loops
* Stall timeouts on long-running commands

**Handoff contracts** keep lifecycle context intact:

* Planning must emit verification and closure expectations, not just code change lists
* Review must identify which runtime surfaces require validation
* PR creation must carry forward operational validation and monitoring sections
* Completion does not mean “green tests only” — it means the work is ready to enter Primitive 10

### Adaptation Points

* Build/test/lint commands differ per technology
* CI pipeline order varies across platforms
* Runtime verification depth differs by project surface (CLI, API, browser, background jobs)
* Stall timeouts may need adjustment for slower build systems

## Primitive 5: Tool Execution, Safety Modes, and Guardrails

### The Problem

Agents operating with filesystem access can create, modify, or delete any file. Without guardrails, a hallucinating agent could overwrite core configuration, delete source files, or execute destructive terminal commands. Declarative rules alone are not enough: when risk rises, the harness needs explicit operating modes that slow the agent down, narrow its scope, and require investigation before mutation.

### The Solution

Layered safety controls:

1. **Workspace containment**: All file operations resolve within the workspace root
2. **Non-destructive direct writes**: File creation and modification proceed without approval
3. **Safety modes**: Interactive operating modes add structure when work is risky:
   * **Careful mode** — enumerate risks, pause before destructive or high-blast-radius actions
   * **Freeze-scope mode** — constrain edits to a declared directory or subsystem boundary
   * **Investigate-first mode** — gather evidence before proposing or applying fixes
4. **Destructive approval workflow**: Deletions and removals require operator approval
5. **Terminal command policy**: Destructive commands require approval regardless of permissive flags
6. **Feature flags**: New agent-generated modules are gated behind feature flags
7. **Architecture enforcement**: Custom linters and structural tests enforce dependency direction, naming conventions, and layering boundaries. Lint error messages are written for agent consumption, providing remediation instructions directly in context. Agents operate within strict boundaries but have freedom in implementation within those boundaries.

### Adaptation Points

* Approval workflow integration depends on available communication channels
* Safety-mode prompts and freeze boundaries depend on the available UX (editor prompts, CLI confirmations, review comments)
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

2. **Instruction reinforcement**: The build-feature skill re-reads coding standards before every fix attempt. The ship agent re-reads constitution principles at session start.

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

Agent definitions describe what an agent does, but nothing prevents invoking agents out of sequence. Without cross-agent policies, the ship agent could claim a task before the harness-architect generates the test harness, violating the TDD mandate.

### The Solution

A declarative policy registry defines:

* **Gate points**: Specific moments where policies are checked
* **Preconditions**: What must be true before proceeding
* **Postconditions**: What must hold after the step completes
* **Violation actions**: What to do when a policy is breached

Five core policies:

| Policy | Gate | Purpose |
|---|---|---|
| P-001 | Ship agent pre-flight | Only one top-level release unit (feature or chore) in progress at a time |
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

2. **Structured knowledge directory**: A `docs/` directory treated as the system of record for **durable knowledge** — information that persists and evolves with the codebase:
   * `ARCHITECTURE.md` — Top-level map of domains, package layering, and dependency direction
   * `design-docs/` — Catalogued design decisions and rationale (graduated from completed work)
   * `product-specs/` — Product requirements and acceptance criteria
   * `references/` — External documentation relevant to the codebase (llms.txt files, API docs)
   * Quality grades per domain — tracking which areas are well-covered vs. fragile

3. **Separation from backlog**: The `docs/` directory holds durable knowledge; the backlog directory (`.backlog/`, `.backlogit/`, or `backlog/`) holds active work items in a flat `queue/` directory. These serve different lifecycles:

   | Directory | Contains | Lifecycle |
   |---|---|---|
   | Backlog `queue/` | Work items (features, chores, tasks, spikes, deliberations, bugs) typed by prefix | Queued → Active → Done → Archived |
   | `docs/compound/` | Institutional learnings organized by category | Persists and grows with codebase |
   | `docs/plans/` | Implementation plans (compacted into decided-plans with appended reviews) | Persists after compaction |
   | `docs/decisions/` | Deliberation outcomes and spike findings | Persists and evolves with codebase |
   | `docs/memory/` | Session state, checkpoints (compacted periodically) | Persists after compaction |
   | `docs/closure/` | Runtime verification, code review, safety-check, and operational closure records | Persists with release history |
   | `docs/design-docs/` | Graduated architectural decisions and design rationale | Persists and evolves with codebase |

   > **Note**: All `docs/` paths above reflect the default docs root (`docs/`). The root and all subdirectory names are configurable via `.autoharness/config.yaml` (`docs.root` and `docs.subdirectories`).

   Work items live in the backlog because they're managed by the backlog tool. The *knowledge artifacts* they produce live in `docs/` as durable records. The compact-context skill consolidates verbose memory and plans into dense summaries, archiving originals to `docs/archive/`.

4. **Knowledge graduation**: When backlog work completes, the ship agent evaluates during post-merge closure whether the work produced reference-worthy knowledge:
   * **Architectural decisions** from completed plans → `docs/design-docs/` as design records
   * **Hard-won solutions** from compound learnings → already in `docs/compound/` (searchable)
   * **New domain patterns** discovered during implementation → update `docs/ARCHITECTURE.md`
   * **Product requirements** that emerged during deliberation or spike investigation → `docs/product-specs/`

   Graduation is not copying — it's distilling the durable insight from the ephemeral work item. The backlog work item is archived by the backlog tool; the knowledge it produced lives on in `docs/`.

5. **Progressive disclosure**: Agents start with a small, stable entry point and are taught where to look next, rather than being overwhelmed up front. Each level of documentation points deeper when needed.

6. **Doc-gardening**: The ship agent runs doc-gardening as part of its post-merge closure protocol to scan for stale or obsolete documentation that no longer reflects the codebase. It applies targeted fixes to keep documentation in sync with code and runs the graduation process after features or chores complete.

7. **Mechanical enforcement**: CI-integrated checks validate that the knowledge base is up to date, cross-linked, and structurally correct. Custom linters verify documentation freshness, coverage, and ownership.

### Adaptation Points

* The `docs/` directory structure adapts to the workspace's existing documentation patterns
* Doc-gardening frequency depends on the workspace's change velocity
* Progressive disclosure depth varies by codebase complexity (a small CLI tool needs less than a large monorepo)
* Architecture documentation captures whatever layering and domain boundaries the workspace uses
* Quality grading categories adapt to the workspace's technology domains

## Primitive 10: Operational Closure and Feedback

### The Problem

Many harnesses stop too early. The code compiles, the tests pass, and a PR exists — but the system still lacks release readiness, runtime verification evidence, monitoring expectations, and feedback capture. Without an explicit closure primitive, teams merge code that has never been validated against real runtime surfaces and never feeds production learnings back into the harness.

### The Solution

Operational closure turns “implementation complete” into “change safely closed over” through four mechanisms:

1. **Runtime Verification Skill**: Validate the affected runtime surfaces using the right depth for the work. For a CLI tool this may be smoke commands; for an API this may be endpoint probes; for a web application this may include browser-backed validation.

2. **Operational Closure Skill**: Produce structured closure artifacts covering release readiness, monitoring expectations, rollback triggers, ownership, validation windows, and follow-up actions.

3. **PR and CI Handoff Sections**: Pull request descriptions and CI remediation workflows carry explicit runtime verification and operational validation sections so the release context survives past implementation.

4. **Feedback Loop into the Harness**: Runtime findings, canary issues, and post-deploy observations become compound learnings, documentation updates, or tuning proposals. Primitive 10 is the bridge from delivery to adaptation.

### Why It Matters as a Compositional Piece

Primitive 10 is what closes the loop on the rest of the system:

* Primitive 4 can now hand off to a defined closure mechanism rather than ending ambiguously at “PR created” or “CI green”
* Primitive 7 gains runtime evidence rather than relying only on static review findings
* Primitive 1 receives higher-quality learnings because they include runtime outcomes, not just build-time fixes
* Primitive 9 stays current because operational learnings graduate back into durable repository knowledge

Without Primitive 10, the harness is excellent at producing changes but weaker at proving the changes are safely absorbed by the running system.

### Adaptation Points

* Verification depth adapts to the project surface (library, CLI, API, browser UI, batch jobs)
* Monitoring steps adapt to the workspace’s telemetry stack and deployment platform
* Closure artifacts adapt to the team’s release process (merge, deploy, canary, handoff, maintenance window)
* Feedback destinations adapt to where the workspace stores durable learnings (`docs/compound/`, `docs/decisions/`, issue trackers)
