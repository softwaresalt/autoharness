---
title: autoharness
description: Globally-installed agent harness framework that generates AI coding assistant primitives into any target workspace
---

# autoharness

A globally-installed agent harness framework that composes AI coding assistant primitives into any repository workspace. Each workspace has its own technology stack, goals, target platforms, and methodologies. autoharness discovers those characteristics, then generates and installs a customized set of agents, instructions, skills, prompts, policies, and constitutional foundations that conform to the workspace's unique needs.

autoharness is installed once in a global location and invoked against target workspaces — it does not install itself into the target. The target receives only the generated harness artifacts it needs to function.

## The Problem

Modern AI coding assistants (GitHub Copilot, Claude Code, Cursor, Codex) operate more effectively when guided by structured harness artifacts: agent definitions, skill workflows, coding instructions, review personas, and workflow policies. Building these from scratch for every repository is tedious and error-prone. Maintaining them as the codebase evolves is worse.

## The Solution

autoharness extracts the **10 universal primitives** of an effective agent harness (identified through empirical evaluation of production harnesses) and packages them as customizable templates. Two core workflows drive the system:

1. **Install**: Discover the target workspace's profile (tech stack, conventions, tools) and compose a tailored harness from primitive templates.
2. **Tune**: Iteratively adapt the installed harness as the codebase, documentation, and team conventions evolve over time.

### Global Tool, Local Output

```text
┌──────────────────────────┐       ┌──────────────────────────┐
│  autoharness (global)    │       │  target workspace        │
│                          │       │                          │
│  templates/              │──────▶│  AGENTS.md               │
│  schemas/                │ reads │  .github/agents/         │
│  agents/                 │ tmpl, │  .github/skills/         │
│  skills/                 │ writes│  .github/instructions/   │
│  docs/                   │ output│  .github/policies/       │
│                          │       │  .backlog/               │
│                          │       │  .autoharness/           │
└──────────────────────────┘       └──────────────────────────┘
```

The target workspace never contains autoharness engine files. It gets only the finished, workspace-adapted harness artifacts.

## The 10 Primitives

Every effective agent harness implements these irreducible primitives, regardless of language, framework, or domain:

| # | Primitive                             | Purpose                                            | Key Artifacts                                              |
|---|---------------------------------------|----------------------------------------------------|------------------------------------------------------------|
| 1 | **State, Context & Knowledge Retrieval** | Durable memory, checkpoints, retrieval, compaction | Memory agent, learnings researcher, compact-context, compound |
| 2 | **Task Granularity & Horizon Scoping** | Decompose work to prevent error compounding        | 2-hour rule, width isolation, atomic milestones            |
| 3 | **Model Routing & Escalation**        | Match model capability to task complexity           | Tier configuration, escalation laddering, cost tracking    |
| 4 | **Orchestration, Delegation & Lifecycle Handoffs** | Sequence agents through a feature/chore lifecycle | Pipeline agents, handoff rules, stop conditions, verification handoffs |
| 5 | **Tool Execution, Safety Modes & Guardrails** | Safe environment mutation with policy enforcement | Approval workflows, safety modes, feature flags, architecture linters |
| 6 | **Injection Points & Dynamic Reminders** | Surface constraints exactly when needed          | applyTo patterns, instruction reinforcement, DoD checks    |
| 7 | **Observability & Evaluation**        | Track agent efficacy, output quality, and entropy  | Review personas, metrics, grading, cleanup agents          |
| 8 | **Workflow Policy**                   | Cross-agent sequencing and gate enforcement         | Policy registry, preconditions, violation telemetry        |
| 9 | **Repository Knowledge & Agent Legibility** | Structure the repo as a navigable knowledge base | Progressive disclosure, doc-gardening, architecture docs   |
| 10 | **Operational Closure & Feedback**   | Verify runtime behavior and close the delivery loop | Runtime verification, operational closure, monitoring plans |

## Installation Presets and Capability Packs

autoharness now supports a lighter-weight composition model so teams can adopt the framework without absorbing every moving part on day one.

### Presets

| Preset | Default Scope | Best For |
|---|---|---|
| **starter** | Core planning, execution, guardrails, and repo knowledge | Smaller repos, first adoption, low-ceremony teams |
| **standard** | Full 10-primitive harness | Most application and service repositories |
| **full** | Full 10-primitive harness plus recommended capability packs | Teams that want deeper verification and stronger operational guidance |

### Capability Packs

| Pack | Purpose |
|---|---|
| **agent-intercom** | Weaves remote operator visibility, heartbeat, approval routing, and steering waits through the harness lifecycle |
| **agent-engram** | Weaves engram-first indexed search, code graph lookup, workspace binding, and query-driven context retrieval through analysis-heavy workflows |
| **backlogit** | Deepens backlogit-native query, queue, dependency, memory, checkpoint, comment, and traceability workflows |
| **browser-verification** | Adds browser-aware runtime verification guidance for web-facing projects |
| **strict-safety** | Emphasizes careful / freeze-scope / investigate-first operating modes |
| **release-observability** | Strengthens operational closure with monitoring and validation checklists |

### Formal overlay pattern

Capability packs are **not extra primitives**. They are cross-cutting overlays that deepen one or more of the 10 primitives by weaving coordinated changes through multiple harness artifacts.

Every capability pack should define:

* **Eligibility signals** — what discovery looks for before recommending the pack
* **Target artifacts** — which foundation docs, instructions, agents, skills, prompts, or policies are affected
* **Behavior deltas** — what changes in the installed harness when the pack is enabled
* **Verification checks** — how installation confirms the overlay was applied consistently
* **Tuning drift rules** — how the tuner decides the overlay is missing, stale, or only partially woven

See [Capability Packs](docs/capability-packs.md) for the full overlay contract.

For the current first-party backlogit guidance, including what is stable now
versus what is still incubating in backlogit's next workflow revision, see
[Backlogit Operating Model](docs/backlogit-operating-model.md),
[Backlogit Compatibility Matrix](docs/backlogit-compatibility-matrix.md), and
[Backlogit Graduation Checklist](docs/backlogit-graduation-checklist.md).

## Backlog Tool Integration

A structured backlog tool is essential for effective agent harness operation. Agents need a machine-queryable work queue to pull tasks from, track status transitions, and manage decomposition hierarchies. autoharness supports pluggable backlog tools through a registry abstraction layer.

### Supported Tools

| Tool | Runtime | Directory | Transport | Key Differentiators |
|------|---------|-----------|-----------|---------------------|
| **backlogit** | Go binary | `.backlogit/` | MCP (stdio) + CLI | SQL query engine, telemetry, memory/checkpoints, sections |
| **backlog-md** | Node.js (npm) | `backlog/` | MCP (stdio) + CLI | Milestones, documents, Definition of Done, workflow guides |

### How It Works

1. **Detection**: The workspace-discovery skill scans for backlog tool markers (config files, directories, MCP registrations)
2. **Registry**: A pre-built registry YAML maps abstract operations (create, list, update, move) to the tool's specific MCP tool names and CLI commands
3. **Abstraction**: All agent templates reference abstract operations (`{{OP_CREATE_MCP}}`, `{{STATUS_TODO}}`), which are resolved to tool-specific values during installation
4. **Migration**: The harness-tuner detects tool switches and generates migration proposals that update all harness references

### Manual Registration

If autoharness does not detect your backlog tool, or you use a custom tool, you can register it manually by creating `.autoharness/backlog-registry.yaml` following the schema in `schemas/backlog-tool-registry.schema.json`.

## Project Structure

```text
autoharness/                             # Global installation (e.g. ~/.autoharness/)
  README.md                              # This file
  AGENTS.md                              # Rules for agents working on autoharness itself
  .github/
    copilot-instructions.md              # Dev guidelines for autoharness contributors
    agents/
      harness-installer.agent.md         # Discovers workspace, composes and installs harness
      harness-tuner.agent.md             # Iteratively adapts harness to codebase changes
    skills/
      install-harness/SKILL.md           # Multi-phase installation workflow
      tune-harness/SKILL.md              # Maintenance and tuning workflow
      workspace-discovery/SKILL.md       # Discover workspace tech stack and conventions
    instructions/
      harness-architecture.instructions.md  # How the 10 primitives work together
    prompts/
      install-harness.prompt.md          # User-facing prompt to install a harness
      tune-harness.prompt.md             # User-facing prompt to tune an installed harness
  templates/                             # Parameterized templates (read-only during install)
    foundation/                          # Constitutional and root-level templates
      AGENTS.md.tmpl
      copilot-instructions.md.tmpl
      constitution.instructions.md.tmpl
    agents/                              # Agent definition templates
    skills/                              # Skill workflow templates
    instructions/                        # Instruction file templates
    policies/                            # Policy registry templates
    prompts/                             # Prompt templates
    backlog/                             # Backlog structure and registry templates
      registries/
        backlogit.registry.yaml
        backlog-md.registry.yaml
  schemas/                               # JSON schemas for profiles, manifests, registries
  docs/                                  # Documentation
```

## Quick Start

### 1. Install autoharness globally

**With uv (recommended)**:

```bash
uv tool install git+https://github.com/softwaresalt/autoharness.git
```

Update when improvements are available:

```bash
uv tool upgrade autoharness
```

**With git clone** (alternative):

```bash
git clone https://github.com/softwaresalt/autoharness.git ~/.autoharness
```

Update: `cd ~/.autoharness && git pull`

**Verify** the installation:

```bash
autoharness home      # prints the installation path
autoharness version   # prints the version
```

### 2. Register with your AI coding environment

autoharness works across any environment that supports agent and skill conventions.

**VS Code with GitHub Copilot** — Add autoharness as a workspace folder alongside your target project (multi-root workspace), or register its skills globally:

```jsonc
// .vscode/settings.json (in your target workspace)
{
  "github.copilot.chat.agentWorkspaceFolders": ["~/.autoharness"]
}
```

**GitHub Copilot CLI** — Invoke with the autoharness directory available:

```bash
ghcp agent @harness-installer workspace=/path/to/target
```

**Claude Code** — Reference autoharness in your project config or invoke directly:

```bash
claude --agent ~/.autoharness/.github/agents/harness-installer.agent.md
```

**Cursor** — Add autoharness as an agent source in Cursor settings.

**Codex** — Reference the autoharness AGENTS.md or invoke with system context.

### 3. Install a harness into a target workspace

From any registered environment:

```text
@harness-installer workspace=/path/to/my-project preset=standard
```

The installer will:

1. **Discover** the target workspace profile (languages, frameworks, build tools, test runners, CI/CD)
2. **Present** a proposed harness configuration for your review
3. **Generate** customized agents, skills, instructions, policies, and constitutional docs
4. **Install** the artifacts into the target workspace's `.github/` directory
5. **Verify** the installation is coherent and all cross-references resolve

Optional examples:

```text
@harness-installer workspace=/path/to/my-project preset=starter
@harness-installer workspace=/path/to/my-project preset=full capability_packs=agent-intercom,browser-verification,release-observability
```

### 4. Tune an existing harness

After the codebase evolves, invoke the tuner:

```text
@harness-tuner workspace=/path/to/my-project
```

## Design Principles

1. **Global tool, local output.** autoharness is installed once globally and invoked against target workspaces. The target receives only generated harness artifacts — never autoharness engine files, templates, or schemas.

2. **Environment agnostic.** The generated artifacts use standard paths (`.github/`, `AGENTS.md`, `.backlog/`) that work across VS Code with GitHub Copilot, GitHub Copilot CLI, Codex, Cursor, Claude Code, and any environment that supports agent conventions.

3. **Templates over code generation.** Harness artifacts are Markdown files with placeholder variables, not programmatically generated code. Human-readable, Git-friendly, and manually editable.

4. **Discovery before composition.** The installer never guesses. It scans the workspace, identifies the tech stack, and presents findings before generating anything.

5. **Primitives are universal; implementations are specific.** Every workspace needs state management, task decomposition, and workflow policies. The specific agents, review personas, and quality gates vary by technology and team conventions.

6. **Tuning is continuous.** Harnesses degrade as codebases evolve. The tuner agent detects drift between the installed harness and the current workspace state, then proposes targeted updates.

7. **Composition over monolith.** Each primitive is independently installable. Teams can adopt the full framework or select specific primitives that address their needs.

## License

MIT