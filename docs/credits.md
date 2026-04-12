---
title: Credits and Acknowledgements
description: Sources of inspiration, research, methodologies, and tools that shaped autoharness
---

# Credits and Acknowledgements

autoharness draws on empirical research, production harness work, and established
software engineering practice from a range of sources. This document gives proper
credit to each.

---

## Research

### METR Time Horizons

The 2-hour task-granularity rule in **Primitive 2** is grounded in METR's
*Time Horizons* empirical research, which measured agent reliability as a function
of task duration. Key findings used in autoharness:

- Agent reliability drops below 50% for tasks exceeding 2 hours of
  human-equivalent effort
- Reliability approaches 0% for tasks exceeding 4 hours
- Sequential error compounding multiplies individual step failure probabilities
  across long task chains

These findings motivate the hard decomposition constraints baked into the
harness: the 2-hour rule, width isolation, and the atomic milestone requirement.

**Source**: METR, *Measuring AI Agent Task Reliability Across Time Horizons*  
**Where it appears**: `docs/primitives.md` (Primitive 2), `.github/instructions/harness-architecture.instructions.md`

---

### OpenAI Harness Engineering Experiment

The guiding principle for **Primitive 9** (Repository Knowledge and Agent
Legibility) — that `AGENTS.md` should be a short map pointing agents to
deeper sources of truth, not a monolithic instruction manual — was validated
by an OpenAI harness engineering experiment with Codex:

> "Give Codex a map, not a 1,000-page instruction manual."

This is why autoharness generates a concise (~100 line) `AGENTS.md` that
functions as a table of contents, deferring domain details to structured
`docs/` artifacts.

**Where it appears**: `docs/primitives.md` (Primitive 9)

---

### Anthropic Constitutional AI

The **constitutional** artifact pattern — a single governing document
(`constitution.instructions.md`) with named principles, amendment procedures,
and cross-references that all other harness artifacts cite — draws from
Anthropic's Constitutional AI framing. Anthropic's work demonstrated that
giving an AI system an explicit, stable, self-referencing constitution of
governing principles produces more coherent, reviewable behavior than
distributing constraints across many disconnected instructions.

In autoharness, the constitution is a Primitive 5 artifact: it governs
workspace isolation, containment, destructive-action approval, and safety
posture. The `strict-safety` capability pack extends it with explicit
`ProposedAction` / `ActionRisk` / `ActionResult` tracking.

**Source**: Anthropic, *Constitutional AI: Harmlessness from AI Feedback* (2022)  
<https://www.anthropic.com/research/constitutional-ai-harmlessness-from-ai-feedback>  
**Where it appears**: `templates/foundation/constitution.instructions.md.tmpl`,
`templates/instructions/strict-safety.instructions.md.tmpl`

---

## Frameworks and Projects

### atv-starterkit

[atv-starterkit](https://github.com/microsoft/atv-starterkit) is a Compound
Engineering harness for GitHub Copilot. A structured read-only evaluation of
its architecture (documented in
`docs/research/2026-04-10-atv-starterkit-integration-analysis.md`) shaped
several autoharness capabilities:

| atv-starterkit concept | autoharness influence |
|---|---|
| `observe` / `learn` / `evolve` continuous learning loop | `continuous-learning` capability pack; `observe/SKILL.md.tmpl`, `learn/SKILL.md.tmpl`, `evolve/SKILL.md.tmpl` templates |
| `ce-compound-refresh` knowledge maintenance workflow | `compound-refresh/SKILL.md.tmpl` — first-class maintenance workflow for stale compound learnings |
| `deployment-verification-agent` invariant / pre/post check model | Primitive 10 operational closure depth; `runtime-verification/SKILL.md.tmpl` |
| `test-browser` headed/headless recipes, route selection, human pauses | `browser-verification` capability pack; `runtime-verification/SKILL.md.tmpl` |
| Additive `stack_packs` and preset composition model | `stack_packs` / `install_layers` fields in workspace profile schema; preset system in `install-harness` SKILL |
| Deterministic drift classification | Checksum-based artifact scanning in `tune-harness` SKILL |
| Persona-based review model | Multi-persona review layer; always-on and conditional review personas |

The autoharness **primitive model** and **capability-pack overlay contract**
predate the atv integration; atv contributed concrete workflow recipes and
learning-loop mechanics layered on top of that foundation.

---

### Compound Engineering / DeerFlow

The **Compound Engineering** (CE) workflow used in atv-starterkit — a phased
plan → work → review → compound cycle with explicit artifact gates — traces
its lineage to the **DeerFlow** agentic workflow framework. The `compound`
knowledge-capture pattern (hard-won solutions stored with searchable YAML
frontmatter for future retrieval) enters autoharness through this lineage.

**Where it appears**: `templates/skills/compound/SKILL.md.tmpl`,
`templates/agents/research/learnings-researcher.agent.md.tmpl`,
`templates/skills/compact-context/SKILL.md.tmpl`

---

### backlogit

[backlogit](https://github.com/softwaresalt/backlogit) is a structured
work-item management tool with an MCP transport layer and SQL query engine.
It co-evolved with autoharness and had deep bidirectional influence on the
harness architecture:

- The **two-agent stage/ship model** (stash-to-backlog → backlog-to-shipped)
  was refined through production use with backlogit's task/dependency model
- The **durable knowledge vs. active work** directory boundary (`docs/` vs.
  backlog `queue/`) emerged from operating the harness against backlogit's
  storage model
- The **backlog tool registry** abstraction layer (mapping abstract harness
  operations to tool-specific MCP tool names and CLI commands) was designed
  specifically to keep the harness portable as backlogit evolves
- The **chore as a first-class release unit** (alongside features) was
  formalised after observing that production harnesses regularly needed
  non-feature work items with the same decomposition and closure discipline

**Where it appears**: `schemas/backlog-tool-registry.schema.json`,
`templates/backlog/registries/backlogit.registry.yaml`, all stage/ship agent
templates, `templates/policies/workflow-policies.md.tmpl`

---

## Software Engineering Practice

### Test-Driven Development

The TDD gate policies (**P-002** and **P-004**) implement the red-green-refactor
discipline codified by Kent Beck in *Test-Driven Development: By Example* (2002).
P-002 requires the test harness to be in place (`harness-ready` label) before
implementation begins. P-004 requires tests to compile and fail (the red phase)
before implementation is written. This ensures agents cannot skip verification
by generating tests that are pre-wired to pass.

**Source**: Kent Beck, *Test-Driven Development: By Example* (2002)  
**Where it appears**: `templates/policies/workflow-policies.md.tmpl` (P-002, P-004),
`templates/skills/harness-architect/SKILL.md.tmpl`,
`templates/skills/build-feature/SKILL.md.tmpl`

---

### Circuit Breaker Pattern

The circuit breaker stop-condition protocol in `circuit-breaker.instructions.md`
implements the resilience pattern described by Michael Nygard in
*Release It! Design and Deploy Production-Ready Software* (2007). In the agent
context, the circuit breaker prevents agents from entering infinite retry loops
on persistent failures: after 3 consecutive failures of the same operation, the
agent stops, logs, and surfaces the problem to the operator rather than
compounding the damage.

**Source**: Michael Nygard, *Release It!* (2007)  
**Where it appears**: `templates/instructions/circuit-breaker.instructions.md.tmpl`

---

## Related Work

The following projects address adjacent problems and are integrated with or
supported by autoharness as target deployment environments:

| Project | Relationship |
|---|---|
| [GitHub Copilot](https://github.com/features/copilot) | Primary target runtime; harness artifacts use `agent.md`, `SKILL.md`, and `.instructions.md` conventions |
| [Claude Code](https://www.anthropic.com/claude) | Supported runtime; `setup-claude` copies agents and skills to `~/.claude/` |
| [OpenAI Codex](https://platform.openai.com/docs/codex) | Supported runtime; `setup-codex` copies skills to `~/.codex/` |
| [backlog-md](https://github.com/peterbe/backlog-md) | Supported backlog tool; first-party registry included |
| [engram](https://github.com/softwaresalt/engram) | Workspace semantic index; `agent-engram` capability pack deepens analysis workflows |
