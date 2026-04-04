# Copilot Review Instructions

These instructions guide automated code review for the autoharness project.

## Project Context

autoharness is a **template-driven framework** that produces Markdown artifacts (agents, skills, instructions, policies, prompts) for AI coding assistant harnesses. It contains no application code — the product is templates, schemas, and documentation. Review through this lens.

## Critical Review Rules

### 1. Template Variable Discipline

There are two distinct uses of `{{UPPER_SNAKE_CASE}}` placeholders in this project:

**Install-time variables** — resolved by the installer when composing a template into a target workspace. These appear in `.tmpl` files and MUST:
- Use `{{UPPER_SNAKE_CASE}}` format
- Be documented in the install-harness SKILL.md variable resolution table or resolvable from the workspace profile
- Never use nested references (`{{VAR1_{{VAR2}}}}` is never valid)
- Never survive into installed output — if a `{{...}}` placeholder appears in non-`.tmpl` files, it is an installation error

**Runtime fill-in placeholders** — intentionally left as `{{PLACEHOLDER}}` in installed output because they represent values that agents or operators fill in at runtime. These appear inside fenced code blocks, artifact examples, and template snippets within skill/agent definitions. They are NOT installation errors. Examples: `{{TITLE}}`, `{{DESCRIPTION}}`, `{{YYYY-MM-DD}}` inside example work item templates.

When reviewing:
- Flag undocumented install-time variables in `.tmpl` files
- Do NOT flag `{{...}}` placeholders inside fenced code blocks or artifact examples — verify they are runtime fill-ins before flagging
- Flag any `{{...}}` in installed (non-`.tmpl`) output that is not clearly a runtime fill-in inside an example block

### 2. File Naming Conventions

Enforce these naming patterns strictly:

| Artifact Type | Pattern | Example |
|---|---|---|
| Template | `{name}.{ext}.tmpl` | `constitution.instructions.md.tmpl` |
| Agent definition | `{name}.agent.md` | `deliberator.agent.md` |
| Skill | `{skill-name}/SKILL.md` | `spike/SKILL.md` |
| Instruction | `{name}.instructions.md` | `agent-engram.instructions.md` |
| Prompt | `{name}.prompt.md` | `ping-loop.prompt.md` |
| Policy | `{name}-policies.md` | `workflow-policies.md` |

Flag files that don't follow these patterns.

### 3. YAML Frontmatter Validity

Every template must have valid YAML frontmatter. Check for:

- Agent templates require: `name`, `description`, `maturity`, `tools`
- Skill templates require: `description`
- Instruction templates require: `description` (and `applyTo` when scoped)
- Frontmatter must parse as valid YAML — watch for unescaped quotes and colons in description strings

### 4. Cross-Reference Integrity

When a change references another artifact (agent, skill, instruction, path), verify the target exists. Common violations:

- Pipeline descriptions listing a skill that has no template
- An agent referencing a skill directory that doesn't exist in `templates/skills/`
- Backlog path references that don't use `{{BACKLOG_DIRECTORY}}/queue/` for work items, or reference non-existent subdirectories under the backlog root
- Knowledge artifact paths that don't use `docs/` for long-lived content (compound/, plans/, decisions/, memory/, closure/)
- Capability pack conditional blocks referencing instructions that have no template

### 5. Capability Pack Overlay Coherence

If a change touches capability pack integration (`agent-intercom`, `agent-engram`, `backlogit`), verify it is **woven consistently** across all affected artifacts — not applied to just one file in isolation. A capability pack overlay must touch every artifact class it declares. A single isolated instruction block is not sufficient for a cross-cutting pack.

### 6. Primitive Model Integrity

The 10 primitives are the irreducible architecture. Flag changes that:

- Attempt to add an 11th primitive or redefine existing primitives
- Treat a capability pack as a primitive (packs are optional overlays, not architecture)
- Break the pipeline sequence without updating all references (pipeline: Deliberate/Spike → Plan → Review → Harvest → Harness → Build → Review → PR → Fix-CI → Runtime Verification → Operational Closure)
- Violate the 2-hour rule for task granularity without explicit justification

### 7. Global Tool / Local Output Boundary

autoharness engine files (templates, schemas, `.github/` agents and skills that power autoharness itself) must never be mixed with target workspace output artifacts. Flag any change that:

- Writes autoharness engine files to a target workspace path
- References `autoharness_home` paths in generated output templates
- Puts generated artifacts in the autoharness installation directory

### 8. Environment Agnosticism

All agents, skills, and generated artifacts must work across VS Code with GitHub Copilot, GitHub Copilot CLI, Codex, Cursor, Claude Code, and any agent-capable environment. Flag:

- IDE-specific API calls or tool names outside of `{{VARIABLE}}` blocks
- Hardcoded editor commands (e.g., VS Code command palette references)
- Assumptions about specific MCP server availability without capability pack guards

### 9. Schema Compliance

Changes to schemas (`schemas/*.schema.json`) must:

- Maintain backward compatibility (additive changes preferred)
- Use JSON Schema Draft 7
- Include `description` on new properties
- Keep `"version": "1.0.0"` or increment appropriately

Changes to templates that interact with schemas (workspace profile, harness manifest, backlog registry) must conform to the declared schema structure.

### 10. Agent and Skill Role Boundaries

- **Agents** orchestrate and may spawn subagents (up to their declared max depth)
- **Skills** are leaf executors — they must NOT spawn subagents
- Each agent must declare its **model routing tier** (Tier 1 Fast, Tier 2 Standard, Tier 3 Frontier) and **subagent depth**
- Flag skills that reference spawning subagents or agents that omit tier/depth declarations

## What NOT to Flag

- **Markdown style preferences** — heading levels, list formatting, and whitespace choices within templates are intentional and part of the generated artifact design
- **Long files** — template files are necessarily verbose; length alone is not a concern
- **Repeated content across templates** — each template must be self-contained since they are installed independently into target workspaces
- **`{{VARIABLE}}` placeholders in `.tmpl` files** — these are intentional; only flag them in non-template output files
- **Technology-specific content inside `{{VARIABLE}}` blocks** — that's the whole point of the template system
