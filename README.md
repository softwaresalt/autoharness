---
title: autoharness
description: Installable agent harness framework that adapts AI coding assistant primitives to any repository workspace
---

# autoharness

An installable agent harness framework that composes AI coding assistant primitives into any repository workspace. Each workspace has its own technology stack, goals, target platforms, and methodologies. autoharness discovers those characteristics, then generates and installs a customized set of agents, instructions, skills, prompts, policies, and constitutional foundations that conform to the workspace's unique needs.

## The Problem

Modern AI coding assistants (GitHub Copilot, Claude Code, Cursor) operate more effectively when guided by structured harness artifacts: agent definitions, skill workflows, coding instructions, review personas, and workflow policies. Building these from scratch for every repository is tedious and error-prone. Maintaining them as the codebase evolves is worse.

## The Solution

autoharness extracts the **8 universal primitives** of any agent harness (identified through empirical evaluation of production harnesses) and packages them as customizable templates. Two core workflows drive the system:

1. **Install**: Discover the target workspace's profile (tech stack, conventions, tools) and compose a tailored harness from primitive templates.
2. **Tune**: Iteratively adapt the installed harness as the codebase, documentation, and team conventions evolve over time.

## The 8 Primitives

Every effective agent harness implements these irreducible primitives, regardless of language, framework, or domain:

| # | Primitive                             | Purpose                                            | Key Artifacts                                              |
|---|---------------------------------------|----------------------------------------------------|------------------------------------------------------------|
| 1 | **State & Context Management**        | Durable memory, checkpoints, context compaction    | Memory agent, compact-context skill, checkpoint patterns   |
| 2 | **Task Granularity & Horizon Scoping** | Decompose work to prevent error compounding        | 2-hour rule, width isolation, atomic milestones            |
| 3 | **Model Routing & Escalation**        | Match model capability to task complexity           | Tier configuration, escalation laddering, cost tracking    |
| 4 | **Orchestration & Delegation**        | Sequence agents through a feature lifecycle         | Pipeline agents, handoff rules, stop conditions            |
| 5 | **Tool Execution & Guardrails**       | Safe environment mutation with policy enforcement  | Approval workflows, feature flags, sandboxing              |
| 6 | **Injection Points & Dynamic Reminders** | Surface constraints exactly when needed          | applyTo patterns, instruction reinforcement, DoD checks    |
| 7 | **Observability & Evaluation**        | Track agent efficacy and output quality             | Review personas, metrics, automated grading                |
| 8 | **Workflow Policy**                   | Cross-agent sequencing and gate enforcement         | Policy registry, preconditions, violation telemetry        |

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
autoharness/
  README.md                              # This file
  AGENTS.md                              # Authoritative rules for agents in this repo
  .github/
    copilot-instructions.md              # Development guidelines for autoharness itself
    agents/
      harness-installer.agent.md         # Discovers workspace, composes and installs harness
      harness-tuner.agent.md             # Iteratively adapts harness to codebase changes
    skills/
      install-harness/SKILL.md           # Multi-phase installation workflow
      tune-harness/SKILL.md              # Maintenance and tuning workflow
      workspace-discovery/SKILL.md       # Discover workspace tech stack and conventions
    instructions/
      harness-architecture.instructions.md  # How the 8 primitives work together
    prompts/
      install-harness.prompt.md          # User-facing prompt to install a harness
      tune-harness.prompt.md             # User-facing prompt to tune an installed harness
  templates/
    foundation/                          # Constitutional and root-level templates
      AGENTS.md.tmpl                     # Root AGENTS.md for target workspaces
      copilot-instructions.md.tmpl       # Root copilot-instructions.md
      constitution.instructions.md.tmpl  # Constitutional principles (tech-stack adapted)
    agents/                              # Agent definition templates
      backlog-harvester.agent.md.tmpl
      build-orchestrator.agent.md.tmpl
      harness-architect.agent.md.tmpl
      doc-ops.agent.md.tmpl
      memory.agent.md.tmpl
      pr-review.agent.md.tmpl
      prompt-builder.agent.md.tmpl
      review/                            # Review persona templates
        architecture-strategist.agent.md.tmpl
        constitution-reviewer.agent.md.tmpl
        scope-boundary-auditor.agent.md.tmpl
        technology-reviewer.agent.md.tmpl  # Generic tech reviewer (adapts to stack)
        concurrency-reviewer.agent.md.tmpl
      research/
        learnings-researcher.agent.md.tmpl
    skills/                              # Skill workflow templates
      brainstorm/SKILL.md.tmpl
      build-feature/SKILL.md.tmpl
      compact-context/SKILL.md.tmpl
      compound/SKILL.md.tmpl
      fix-ci/SKILL.md.tmpl
      impl-plan/SKILL.md.tmpl
      plan-review/SKILL.md.tmpl
      review/SKILL.md.tmpl
    instructions/                        # Instruction templates
      commit-message.instructions.md.tmpl
      markdown.instructions.md.tmpl
      writing-style.instructions.md.tmpl
      git-merge.instructions.md.tmpl
      pull-request.instructions.md.tmpl
      prompt-builder.instructions.md.tmpl
      technology.instructions.md.tmpl    # Generic tech instructions (adapts to stack)
      backlog-integration.instructions.md.tmpl  # Backlog tool abstraction layer
    policies/
      workflow-policies.md.tmpl          # Workflow policy registry
    prompts/
      ping-loop.prompt.md.tmpl           # Heartbeat loop prompt
    backlog/
      config.yml.tmpl                    # Backlog configuration
      queue.md.tmpl                      # Unrefined ideas queue
      registries/                        # Pre-built backlog tool registries
        backlogit.registry.yaml          # Registry for backlogit
        backlog-md.registry.yaml         # Registry for backlog-md
  schemas/
    workspace-profile.schema.json        # Schema for workspace discovery output
    harness-manifest.schema.json         # Schema for tracking installed harness state
    backlog-tool-registry.schema.json    # Schema for backlog tool registration
  docs/
    primitives.md                        # Deep documentation of each primitive
    installation-guide.md                # How to install into a workspace
    tuning-guide.md                      # How to tune and maintain the harness
    customization-guide.md               # How to customize templates for specific needs
```

## Quick Start

### Install a harness into a workspace

Open the target workspace in VS Code with autoharness in the multi-root workspace, then invoke the installer:

```text
@harness-installer Install a harness for this workspace
```

The installer will:

1. **Discover** the workspace profile (languages, frameworks, build tools, test runners, CI/CD)
2. **Present** a proposed harness configuration for your review
3. **Generate** customized agents, skills, instructions, policies, and constitutional docs
4. **Install** the artifacts into the workspace's `.github/` directory
5. **Verify** the installation is coherent and all cross-references resolve

### Tune an existing harness

After the codebase evolves, invoke the tuner to bring the harness up to date:

```text
@harness-tuner Tune the harness for current workspace state
```

## Design Principles

1. **Templates over code generation.** Harness artifacts are Markdown files with placeholder variables, not programmatically generated code. Human-readable, Git-friendly, and manually editable.

2. **Discovery before composition.** The installer never guesses. It scans the workspace, identifies the tech stack, and presents findings before generating anything.

3. **Primitives are universal; implementations are specific.** Every workspace needs state management, task decomposition, and workflow policies. The specific agents, review personas, and quality gates vary by technology and team conventions.

4. **Tuning is continuous.** Harnesses degrade as codebases evolve. The tuner agent detects drift between the installed harness and the current workspace state, then proposes targeted updates.

5. **Composition over monolith.** Each primitive is independently installable. Teams can adopt the full framework or select specific primitives that address their needs.

## License

MIT