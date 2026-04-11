---
title: "Backlogit harness evolution analysis"
description: "Comparative analysis of backlogit's installed harness vs autoharness templates, identifying three improvement areas with distinct integration approaches"
ms.date: 2026-04-08
ms.topic: research
keywords:
  - autoharness
  - backlogit
  - harness evolution
  - gap analysis
  - template improvements
  - two-agent workflow
  - instruction templates
  - skill templates
---

## Purpose

Backlogit's installed agent harness has evolved beyond what the current
autoharness templates produce. This document captures the divergence,
classifies each gap, and proposes three improvement areas with a different
integration approach for each — respecting the operating-model boundary
documented in `docs/backlogit-operating-model.md`.

## Methodology

1. Inventoried every installed harness artifact in backlogit's `.github/`
   directory (agents, skills, instructions, prompts, foundation files,
   policies, review personas).
2. Inventoried every autoharness template in `templates/` including the
   staged but uncommitted additions on the `new_workitem_type` branch
   (harvest, pr-lifecycle, ci-security, AGENTS.md deprecated section,
   constitution governance section).
3. Compared each artifact class side-by-side, noting what backlogit has
   that autoharness doesn't, what is workspace-specific, and what
   represents a generalizable improvement.
4. Cross-referenced against the graduation checklist and operating-model
   boundary to determine which improvements can flow back now vs later.

## Summary of staged work already in progress

The `new_workitem_type` branch (commit `029c2bc`) plus staged changes
already address several gaps:

| Staged change | Status |
|---|---|
| `harvest/SKILL.md.tmpl` — new skill template | Staged, untracked |
| `pr-lifecycle/SKILL.md.tmpl` — new skill template | Staged, untracked |
| `ci-security.instructions.md.tmpl` — new instruction template | Staged, untracked |
| `AGENTS.md.tmpl` — deprecated agents section and revised pipeline | Staged, modified |
| `constitution.instructions.md.tmpl` — governance section with amendment rules | Staged, modified |
| `install-harness/SKILL.md` — CI_WORKFLOW_GLOB var, primitive 4 skill refs | Staged, modified |

These staged changes are good starting points. The analysis below builds
on what remains after accounting for them.

---

## Improvement area 1: Missing skill and instruction templates

### Integration approach: Direct template creation

These are concrete gaps where backlogit has production-quality artifacts and
autoharness has no corresponding template. They don't involve the two-agent
workflow boundary and can be created immediately.

### Gap 1.1: Harness-architect skill template

**Current state**: Autoharness has `templates/agents/harness-architect.agent.md.tmpl`
(the orchestrating agent) but no `templates/skills/harness-architect/SKILL.md.tmpl`
(the leaf skill the agent invokes).

**Backlogit reference**: `.github/skills/harness-architect/SKILL.md` — 150+
lines covering BDD test harness scaffolding, red-phase verification, language-
specific stub generation, and P-002/P-004 policy compliance.

**Why it matters**: The harness-architect agent delegates to the skill for
actual test scaffold generation. Without the skill template, installed
harnesses have an agent that references a non-existent skill.

**Integration approach**: Create `templates/skills/harness-architect/SKILL.md.tmpl`
using backlogit's skill as a reference. Parameterize with `{{PRIMARY_LANGUAGE}}`,
`{{TEST_COMMAND}}`, `{{BUILD_CHECK_COMMAND}}`, `{{TEST_DIR}}`. Strip backlogit-
specific artifact types and Go patterns. Add agent-intercom broadcast table
following the pattern established in harvest and pr-lifecycle templates.

**Template variables to add**: None new — all required variables already exist
in the resolution table.

### Gap 1.2: MCP server instruction template

**Current state**: No autoharness template exists for MCP server development
guidance.

**Backlogit reference**: `.github/instructions/go-mcp-server.instructions.md` —
300+ lines covering mcp-go SDK usage, project structure, server factory
patterns, tool/resource registration, error formatting for MCP responses, and
query gate implementation.

**Why it matters**: Any workspace building an MCP tool needs structured
guidance for agent-readable API design. This is a cross-cutting concern that
applies to Go, TypeScript, and Python MCP server projects.

**Integration approach**: Create `templates/instructions/mcp-server.instructions.md.tmpl`
as a technology-agnostic template. Use `{{PRIMARY_LANGUAGE}}` and new variables
like `{{MCP_SDK}}`, `{{MCP_TRANSPORT}}`, and `{{MCP_PROJECT_STRUCTURE}}` for
language-specific SDK guidance. The template should cover:

* Project structure conventions for MCP servers
* Tool registration and parameter validation patterns
* Error response formatting for agent consumption
* Query gate patterns (read-only enforcement)
* Resource exposure patterns
* Context efficiency in tool responses (Principle IX alignment)

**Template variables to add to the resolution table**:

| Variable | Profile field | Example values |
|---|---|---|
| `{{MCP_SDK}}` | `frameworks.mcp_sdk` | `mcp-go`, `@modelcontextprotocol/sdk`, `mcp` |
| `{{MCP_TRANSPORT}}` | `frameworks.mcp_transport` | `stdio`, `sse`, `streamable-http` |
| `{{MCP_PROJECT_STRUCTURE}}` | Derived | Language-specific directory layout |

**Discovery signal**: Workspace-discovery should detect MCP server projects by
looking for mcp-go imports in `go.mod`, `@modelcontextprotocol/sdk` in
`package.json`, or `mcp` in `pyproject.toml`/`requirements.txt`.

### Gap 1.3: GitHub Actions workflow instruction template

**Current state**: `ci-security.instructions.md.tmpl` is staged and covers
dependency pinning, permissions, and credentials. Backlogit also has
`workflows.instructions.md` covering broader workflow structure.

**Backlogit reference**: `.github/instructions/workflows.instructions.md` —
150+ lines covering GitHub Actions structural requirements, validation scripts,
release workflow patterns, and matrix testing conventions.

**Why it matters**: CI workflow files are a high-risk surface for supply chain
attacks. The staged ci-security template covers security, but structural
conventions (job naming, artifact handling, caching, matrix patterns) are not
yet covered.

**Integration approach**: Extend `ci-security.instructions.md.tmpl` to also
cover structural conventions, OR create a separate
`workflows.instructions.md.tmpl` for non-security workflow conventions. The
recommendation is to keep them separate:

* `ci-security.instructions.md.tmpl` — security-focused (already staged)
* `workflows.instructions.md.tmpl` — structural conventions template

Both should use `applyTo: '{{CI_WORKFLOW_GLOB}}'`. The workflows template
should cover:

* Job naming conventions
* Artifact upload/download patterns
* Caching strategy
* Matrix testing structure
* Reusable workflow patterns
* Environment and deployment gate conventions

### Gap 1.4: Language-specific instruction depth

**Current state**: `templates/instructions/technology.instructions.md.tmpl`
exists but is a thin skeleton with placeholder variables and no production-
grade guidance patterns.

**Backlogit reference**: `.github/instructions/go.instructions.md` — 400+
lines of comprehensive Go conventions including error handling patterns, data
modeling with validator tags, path handling with security, and a commands
reference section.

**Why it matters**: Agents need deep, specific guidance to write idiomatic code.
The current template produces an instructions file that says "follow
`{{ERROR_HANDLING_RULES}}`" without defining what those rules look like.

**Integration approach**: This is a workspace-discovery-driven problem. The
template variable `{{ERROR_HANDLING_RULES}}` should resolve to a substantive
block, not a one-liner. Options:

1. **Thick template with conditional blocks**: Single template with language-
   specific sections gated by `{{PRIMARY_LANGUAGE}}`. Gets unwieldy.
2. **Language-specific template variants** (recommended): Create
   `templates/instructions/technology-go.instructions.md.tmpl`,
   `technology-typescript.instructions.md.tmpl`, etc. The installer selects
   the right variant based on `{{PRIMARY_LANGUAGE}}`. The install-harness
   SKILL.md already resolves technology variables per language — this extends
   that pattern to the instruction body.

**New files needed**:

* `templates/instructions/technology-go.instructions.md.tmpl`
* `templates/instructions/technology-typescript.instructions.md.tmpl`
* `templates/instructions/technology-python.instructions.md.tmpl`
* `templates/instructions/technology-rust.instructions.md.tmpl`

Each should contain production-grade patterns for the language's error handling,
naming, testing tiers, tooling commands, and idiomatic constructs.

### Estimated scope for area 1

| Item | New files | Modified files |
|---|---|---|
| Harness-architect skill | 1 | install-harness SKILL.md |
| MCP server instructions | 1 | install-harness SKILL.md, workspace-profile schema |
| Workflows instructions | 1 | install-harness SKILL.md |
| Language-specific instructions | 4 | install-harness SKILL.md |
| **Total** | **7** | **2** |

---

## Improvement area 2: Foundation template structural improvements

### Integration approach: Evolve existing templates

These are structural patterns in backlogit's foundation files that improve
agent orientation and governance. They don't introduce new artifacts but
deepen existing templates.

### Gap 2.1: Repository operating model section in AGENTS.md

**Current state**: AGENTS.md.tmpl has Core Rules, Quality Gates, Code Style,
Development Workflow, Task Granularity, Terminal Policy, Repository Knowledge,
Deprecated Agents (staged), and Session Completion.

**Backlogit addition**: A "Repository operating model" section that explains
the data architecture — what is source of truth, what is cache, what is
history. This section appears early in the file (before core rules) and gives
agents a mental model of the workspace before diving into rules.

**Integration approach**: Add a new section to AGENTS.md.tmpl between the
frontmatter and Core Rules:

```markdown
## Repository operating model

{{REPOSITORY_OPERATING_MODEL}}
```

The variable `{{REPOSITORY_OPERATING_MODEL}}` resolves based on workspace
characteristics. For a standard codebase it might be minimal:

> This repository follows a code-first model. Source files are the system of
> record. Durable knowledge lives in `{{DOCS_ROOT}}/`. The backlog directory
> tracks active work items.

For a backlogit-like CQRS workspace, it would be richer. The installer should
generate appropriate content based on detected architecture patterns.

### Gap 2.2: Constitution rationale subsections

**Current state**: The autoharness constitution template lists principles but
several lack explicit rationale blocks explaining why the principle exists.

**Backlogit addition**: Every principle in backlogit's constitution has a
`**Rationale**:` paragraph immediately after the principle text, grounding the
rule in a concrete engineering concern.

**Integration approach**: Add `**Rationale**:` subsections to each principle
in `constitution.instructions.md.tmpl`. Use template variables where the
rationale depends on technology:

```markdown
### Principle I: Safety-First {{PRIMARY_LANGUAGE}}

{{LANGUAGE_SAFETY_PRINCIPLE_TEXT}}

**Rationale**: {{LANGUAGE_SAFETY_RATIONALE}}
```

For principles that are universal (workspace isolation, destructive command
approval), write the rationale directly in the template without variables.

### Gap 2.3: Compliance review requirement in constitution

**Current state**: The staged governance section adds amendment versioning and
conflict resolution, but does not include the compliance review requirement.

**Backlogit addition**: "Every implementation plan MUST include a 'Constitution
Check' section that maps the proposed work against these principles and
documents any justified violations."

**Integration approach**: Add this to the staged governance section. It is
universally applicable and belongs in every constitution:

```markdown
- **Compliance review**: Every implementation plan MUST include a
  "Constitution Check" section that maps the proposed work against
  these principles and documents any justified violations.
```

This is already in the staged diff but needs verification. If present, this
gap is closed.

### Gap 2.4: Agent context efficiency principle

**Current state**: The autoharness constitution does not have a principle
explicitly about preserving agent context windows through minimal, targeted
tool responses.

**Backlogit addition**: Principle IX (Agent Context Efficiency) states that
tools must return minimal data, queries are preferred over file scanning, and
the CQRS architecture exists to serve token-efficient results.

**Integration approach**: Add a new principle to the constitution template.
This is universally applicable — every workspace benefits from agents that
conserve context tokens:

```markdown
### Principle X: Agent Context Efficiency

Tools and data access patterns MUST preserve agent context windows by
returning minimal, targeted data. When a structured query can replace
directory scanning or bulk file reading, agents MUST prefer the query.
Tool responses MUST be structured (JSON or YAML), not raw file content,
unless the agent explicitly needs the full document.

**Rationale**: AI agents operate within finite context windows. Every
token consumed by bulk data is a token unavailable for reasoning and
code generation. Data access architecture should serve token-efficient
query results to agents.
```

### Gap 2.5: Session continuity as mandatory protocol

**Current state**: AGENTS.md.tmpl has a Session Completion section with 7
steps, but it reads as advisory guidance.

**Backlogit addition**: Both groomer and shipper treat session continuity as
a mandatory protocol with explicit mid-session checkpoints, compound learnings
capture, and compact-context invocation thresholds.

**Integration approach**: Strengthen the Session Completion section in
AGENTS.md.tmpl to use MUST language and add mid-session checkpoint guidance:

```markdown
## Session Completion (MANDATORY)

Every working session MUST persist state before ending:

1. Write a memory checkpoint to `{{DOCS_MEMORY}}/`
2. Capture compound learnings when hard-won solutions were discovered
3. Update backlog task state through the tool surface
4. Invoke compact-context when tracking exceeds the configured threshold
5. Leave the branch and working tree in a reviewable state
```

### Estimated scope for area 2

| Item | New files | Modified files |
|---|---|---|
| Repository operating model section | 0 | AGENTS.md.tmpl, install-harness SKILL.md |
| Rationale subsections | 0 | constitution.instructions.md.tmpl |
| Compliance review requirement | 0 | constitution.instructions.md.tmpl (verify staged) |
| Agent context efficiency principle | 0 | constitution.instructions.md.tmpl |
| Session continuity strengthening | 0 | AGENTS.md.tmpl |
| **Total** | **0** | **3** |

---

## Improvement area 3: Two-agent consolidation pattern

### Integration approach: Incubate as optional capability pack

The groomer/shipper two-agent model is the most significant architectural
evolution in backlogit's harness. It consolidates 7 classical agents into 2
orchestrators with clearer lifecycle boundaries. However, the operating-model
boundary documented in `docs/backlogit-operating-model.md` and the graduation
checklist in `docs/backlogit-graduation-checklist.md` explicitly state this
should NOT be hardcoded into autoharness templates until backlogit has fully
validated it.

### What the two-agent model provides

**Groomer** (stash-to-backlog):
* Consolidates: deliberator + backlog-harvester + memory (planning phase)
* Owns: stash triage → deliberation routing → planning → review gating → harvest
* Session continuity: mandatory mid-session checkpoints, compact at 10-file threshold
* Agent-intercom: 8 broadcast events

**Shipper** (backlog-to-shipped):
* Consolidates: build-orchestrator + harness-architect + pr-review + doc-ops + memory (execution phase)
* Owns: shipment validation → harness → build → review → CI → PR lifecycle → post-merge closure
* Session continuity: mandatory with post-merge documentation updates
* Agent-intercom: 10+ broadcast events
* Post-merge closure: invokes operational-closure, updates ARCHITECTURE.md and README.md

### Why it can't be a direct template yet

Per the graduation checklist, these items are NOT yet confirmed:

* Shipment artifact stability
* Stash storage shape finalization
* Contract test coverage of new MCP tools
* End-to-end validation on real work items across multiple sessions
* Clear migration story from classical to two-agent model

### Proposed integration approach: Capability pack definition

Create a capability pack definition (`two-agent-workflow`) that:

1. **Remains disabled by default** in `harness-config.yaml`
2. **Documents the pattern** so workspaces that want to adopt it can
3. **Provides overlay targets** showing which classical agents it replaces
4. **Defines verification checks** for correct weaving
5. **Includes tuning drift detection** for partial adoption

This follows the existing capability-pack architecture documented in
`docs/capability-packs.md` and `.github/instructions/harness-architecture.instructions.md`.

### Capability pack definition sketch

```yaml
# In schemas/harness-config.schema.json capability_packs enum:
two-agent-workflow

# Pack definition:
name: two-agent-workflow
description: >
  Consolidates classical multi-agent orchestration into two primary
  agents (planner + executor) with mandatory session continuity and
  post-merge closure protocols.
eligibility_signals:
  - workspace has backlog tool with stash/queue/shipment lifecycle
  - workspace has 5+ classical agents that could consolidate
recommendation_logic: >
  Recommend when workspace discovery detects a mature backlog tool
  with stash-to-shipped lifecycle support.
overlay_targets:
  - agents/planner.agent.md (replaces deliberator + backlog-harvester + memory planning)
  - agents/executor.agent.md (replaces build-orchestrator + harness-architect + pr-review + doc-ops + memory execution)
  - foundation/AGENTS.md (adds two-agent pipeline, populates deprecated table)
  - skills/harvest (unchanged, invoked by planner)
  - skills/pr-lifecycle (unchanged, invoked by executor)
behavior_deltas:
  - session continuity becomes mandatory with mid-session checkpoints
  - post-merge closure ritual added to executor
  - compound learnings capture integrated into build and CI phases
  - deprecated agents moved to deprecated/ subdirectory
verification_checks:
  - planner agent exists and references deliberate, spike, impl-plan, plan-review, harvest skills
  - executor agent exists and references harness-architect, build-feature, review, fix-ci, pr-lifecycle skills
  - deprecated agents directory exists with superseded agents
  - AGENTS.md deprecated table is populated
  - session continuity sections in both agents use MUST language
tuning_drift_checks:
  - classical agents still active alongside two-agent agents (conflict)
  - deprecated directory missing when pack is enabled
  - session continuity sections use advisory language instead of MUST
```

### Why a capability pack and not a direct template

1. **Respects the operating-model boundary**: The pack is optional and
   off-by-default, matching the documented conservative posture.
2. **Supports gradual adoption**: Workspaces can enable it when ready
   without being forced into a two-agent model.
3. **Follows established architecture**: Capability packs are the
   documented mechanism for optional workflow overlays.
4. **Enables backlogit to graduate later**: When backlogit validates the
   model, the pack can become a recommended default without template
   restructuring.

### Prerequisite for this pack

The graduation checklist must be substantially complete. The pack definition
document can be written now as a placeholder, but the actual agent templates
(`planner.agent.md.tmpl`, `executor.agent.md.tmpl`) should wait until
backlogit's validation is further along.

### Estimated scope for area 3

| Item | New files | Modified files |
|---|---|---|
| Capability pack definition doc | 1 | docs/capability-packs.md |
| Pack eligibility in schema | 0 | schemas/harness-config.schema.json |
| Planner agent template (future) | 1 | — |
| Executor agent template (future) | 1 | — |
| **Total (now)** | **1** | **2** |
| **Total (after graduation)** | **3** | **2** |

---

## Cross-cutting observations

### Agent-intercom treatment

Backlogit treats agent-intercom broadcasts as built-in workflow events in
every skill and agent. Autoharness templates treat them as optional overlay
content gated by the capability pack.

**Recommendation**: Keep the optional treatment in templates. The capability
pack overlay model is correct — not every workspace needs agent-intercom.
The staged harvest and pr-lifecycle templates already handle this well with
"when the agent-intercom capability pack is installed" phrasing.

### Backlogit MCP guidelines block

Backlogit's AGENTS.md starts with a `CRITICAL_INSTRUCTION` block that teaches
agents to call `backlogit_get_metadata_catalog` immediately. This is a
backlogit capability-pack concern.

**Recommendation**: Do not add this to the base AGENTS.md template. It belongs
in the backlogit capability-pack overlay logic. When the backlogit pack is
enabled, the installer should inject this block. Update the backlogit
capability pack overlay targets to include AGENTS.md header injection.

### Technology-specific constitution principles

Backlogit has principles that are deeply Go-specific (Type-Safe Go, Single-
Binary Simplicity) and architecture-specific (CQRS, MCP Protocol Fidelity).

**Recommendation**: Do not try to generalize these into template variables.
Instead, let the technology.instructions.md template (or its language-specific
variants from area 1) carry language-specific depth. The constitution should
stay at the principle level (safety-first language usage, test-first
development, workspace isolation) with `{{VARIABLE}}` blocks for language-
specific instantiation.

---

## Priority and sequencing

| Priority | Area | Integration approach | Blocking dependency |
|---|---|---|---|
| 1 (immediate) | Area 1: Harness-architect skill | Direct template creation | None |
| 2 (immediate) | Area 2: Constitution and AGENTS.md | Evolve existing templates | None |
| 3 (near-term) | Area 1: Language-specific instructions | Direct template creation | None |
| 4 (near-term) | Area 1: MCP server instructions | Direct template creation | None |
| 5 (near-term) | Area 1: Workflows instructions | Direct template creation | None |
| 6 (deferred) | Area 3: Two-agent capability pack | Capability pack definition | Backlogit graduation checklist |

Items 1-2 can start immediately and should be part of the current
`new_workitem_type` branch or a follow-up branch. Items 3-5 can follow
as a separate branch. Item 6 is blocked on backlogit validation progress.

---

## Appendix: Files referenced

### Backlogit installed harness (d:\Source\GitHub\backlogit\.github\)

* `agents/groomer.agent.md` — primary stash-to-backlog orchestrator
* `agents/shipper.agent.md` — primary backlog-to-shipped orchestrator
* `agents/deprecated/` — 7 superseded agent files
* `agents/go-engineer.agent.md` — Go-specific engineering agent
* `agents/go-mcp-expert.agent.md` — MCP server design advisor
* `agents/prompt-builder.agent.md` — prompt engineering assistant
* `agents/review/` — review persona agents
* `skills/harness-architect/SKILL.md` — BDD test scaffold generation
* `skills/harvest/SKILL.md` — plan-to-backlog decomposition
* `skills/pr-lifecycle/SKILL.md` — branch-to-merged management
* `skills/build-feature/SKILL.md` — TDD implementation loop
* `instructions/go.instructions.md` — Go-specific conventions (400+ lines)
* `instructions/go-mcp-server.instructions.md` — MCP server patterns (300+ lines)
* `instructions/workflows.instructions.md` — GitHub Actions conventions (150+ lines)
* `instructions/constitution.instructions.md` — 9 principles with governance

### Autoharness templates (d:\Source\GitHub\autoharness\templates\)

* `agents/harness-architect.agent.md.tmpl` — agent only, no skill template
* `skills/harvest/SKILL.md.tmpl` — staged, new
* `skills/pr-lifecycle/SKILL.md.tmpl` — staged, new
* `instructions/ci-security.instructions.md.tmpl` — staged, new
* `instructions/technology.instructions.md.tmpl` — thin skeleton
* `foundation/AGENTS.md.tmpl` — staged modifications (deprecated agents, pipeline)
* `foundation/constitution.instructions.md.tmpl` — staged modifications (governance)

### Boundary documents (d:\Source\GitHub\autoharness\docs\)

* `backlogit-operating-model.md` — stable contract definition
* `backlogit-graduation-checklist.md` — promotion criteria for two-agent workflow
* `capability-packs.md` — capability pack definitions
