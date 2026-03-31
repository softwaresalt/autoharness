---
description: "Shared development guidelines for the autoharness project"
---

# autoharness Development Guidelines

Last updated: 2026-03-31

autoharness is an installable agent harness framework that composes AI coding assistant primitives into any repository workspace. It discovers workspace characteristics and generates customized agents, skills, instructions, policies, and constitutional foundations.

## Project Structure

```text
autoharness/
  .github/
    agents/                          # Agents that power autoharness itself
      harness-installer.agent.md     # Workspace discovery + harness composition
      harness-tuner.agent.md         # Iterative harness maintenance
    skills/
      install-harness/SKILL.md       # Multi-phase installation workflow
      tune-harness/SKILL.md          # Maintenance and tuning workflow
      workspace-discovery/SKILL.md   # Workspace tech stack discovery
    instructions/
      harness-architecture.instructions.md
    prompts/
      install-harness.prompt.md
      tune-harness.prompt.md
  templates/                         # Parameterized templates for target workspaces
    foundation/                      # Constitution, AGENTS.md, copilot-instructions
    agents/                          # Agent definition templates
    skills/                          # Skill workflow templates
    instructions/                    # Instruction file templates
    policies/                        # Policy registry templates
    prompts/                         # Prompt templates
    backlog/                         # Backlog structure templates
  schemas/                           # JSON schemas for profiles and manifests
  docs/                              # Documentation
```

## Core Concepts

### Templates

Templates are Markdown files with `{{VARIABLE}}` placeholders. The installer agent resolves these placeholders using the workspace profile during installation. Templates use the `.tmpl` extension to distinguish them from ready-to-use files.

Template variables follow these conventions:

* `{{UPPER_SNAKE_CASE}}` for all variables
* Variables are resolved from the workspace profile or derived during installation
* No nested variable references (variables cannot reference other variables)
* Unresolved variables in output files indicate an installation error

### Workspace Profile

The workspace profile is a YAML file produced by the workspace-discovery skill. It captures everything the installer needs to customize templates. The schema is defined in `schemas/workspace-profile.schema.json`.

### Harness Manifest

The harness manifest tracks what was installed, which templates were used, and the checksums of installed artifacts. The tuner uses this to detect drift. Schema: `schemas/harness-manifest.schema.json`.

### Backlog Tool Registry

The backlog tool registry is the abstraction layer between harness agents and the specific backlog management tool installed in a workspace. It maps abstract operations (create task, list tasks, move task) to tool-specific MCP tool names, CLI commands, field names, and status values. Pre-built registries for backlogit and backlog-md live in `templates/backlog/registries/`. Schema: `schemas/backlog-tool-registry.schema.json`.

### The 8 Primitives

1. State & Context Management
2. Task Granularity & Horizon Scoping
3. Model Routing & Escalation
4. Orchestration & Delegation
5. Tool Execution & Guardrails
6. Injection Points & Dynamic Reminders
7. Observability & Evaluation
8. Workflow Policy

## Development Conventions

### File Naming

* Templates: `{name}.{ext}.tmpl` (e.g., `constitution.instructions.md.tmpl`)
* Agent definitions: `{name}.agent.md`
* Skills: `{skill-name}/SKILL.md`
* Instructions: `{name}.instructions.md`
* Prompts: `{name}.prompt.md`

### Template Authoring

When creating or modifying templates:

* Use `{{VARIABLE_NAME}}` for all customization points
* Document every variable in the install-harness SKILL.md variable resolution table
* Test templates against at least 3 different technology profiles (e.g., Rust, TypeScript, Python)
* Templates must produce valid Markdown when all variables are resolved
* Templates must not contain technology-specific content outside of variable blocks

### Quality Gates

Templates are documentation artifacts, not code. Quality is verified through:

1. YAML frontmatter validity
2. Markdown structure (headings, code fences, tables)
3. Variable completeness (no `{{...}}` in output after resolution)
4. Cross-reference integrity (all referenced files, skills, agents exist)
