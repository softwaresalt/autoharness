---
description: "Multi-phase installation workflow that composes harness primitives from templates into a target workspace based on its discovered profile"
---

## Install Harness

Compose and install a complete agent harness into a target workspace. Uses the workspace profile from the workspace-discovery skill to customize universal templates for the target environment's specific technology stack, conventions, and workflow requirements.

autoharness operates as a globally-installed tool. Templates are read from the autoharness home directory; only generated harness artifacts are written to the target workspace. The target workspace never contains autoharness engine files — only the output artifacts it needs to function.

## When to Use

Invoke this skill after workspace-discovery has produced a profile, or let the harness-installer agent invoke it automatically. The skill handles template selection, variable substitution, artifact generation, and installation verification.

## Inputs

* `autoharness_home`: (Required) Absolute path to the autoharness installation (contains `templates/`, `schemas/`). Resolved by the invoking agent via: `AUTOHARNESS_HOME` env var → `autoharness home` CLI → agent directory traversal → `~/.autoharness/`.
* `workspace_path`: (Required) Absolute path to the target workspace root. Must be a different directory from `autoharness_home`.
* `profile_path`: (Required) Path to workspace profile YAML (typically `{workspace_path}/.autoharness/workspace-profile.yaml`).
* `primitives`: (Optional) Comma-separated list of primitive numbers (1-9) to install. Defaults to all.
* `dry_run`: (Optional, default false) When true, generate artifacts to a staging directory without installing.

## Output

* Harness artifacts installed in target workspace's `.github/` directory
* Backlog structure initialized in `.backlog/`
* `AGENTS.md` created at workspace root
* Installation manifest at `.autoharness/harness-manifest.yaml`

## Required Protocol

### Phase 1: Profile Loading and Validation

#### Step 1.0: Validate autoharness Home

Verify the `autoharness_home` path contains the expected structure:

* `{autoharness_home}/templates/` — template files
* `{autoharness_home}/schemas/` — JSON schemas for validation
* `{autoharness_home}/templates/backlog/registries/` — pre-built backlog tool registries

If any are missing, halt and report the issue. The autoharness installation may be corrupt or incomplete.

Verify that `workspace_path` is NOT inside `autoharness_home` and vice versa.

All template reads in subsequent phases use `{autoharness_home}/templates/` as the base path. All artifact writes use `{workspace_path}` as the base path.

#### Step 1.1: Load Profile

Read the workspace profile from `profile_path`. Validate against the workspace profile schema. If validation fails, halt and report the specific schema violations.

#### Step 1.2: Compute Template Variables

Derive all template variables from the profile. The variable resolution table defines how profile fields map to template placeholders:

| Template Variable | Source | Example (Rust) | Example (TypeScript) | Example (Python) |
|---|---|---|---|---|
| `{{PROJECT_NAME}}` | Directory name of workspace | `my-service` | `my-app` | `my-api` |
| `{{PRIMARY_LANGUAGE}}` | `languages.primary` | `Rust` | `TypeScript` | `Python` |
| `{{LANGUAGE_EDITION}}` | Language version from config | `edition 2024` | `ES2022` | `3.12` |
| `{{BUILD_COMMAND}}` | `build.command` | `cargo build` | `npm run build` | `python -m build` |
| `{{TEST_COMMAND}}` | `test.command` | `cargo test` | `npm test` | `pytest` |
| `{{LINT_COMMAND}}` | `lint.command` | `cargo clippy -- -D warnings` | `npm run lint` | `ruff check .` |
| `{{FORMAT_COMMAND}}` | `format.command` | `cargo fmt --all -- --check` | `npx prettier --check .` | `ruff format --check .` |
| `{{FORMAT_FIX_COMMAND}}` | Derived from format tool | `cargo fmt --all` | `npx prettier --write .` | `ruff format .` |
| `{{TEST_DIR}}` | `test.directory` | `tests/` | `__tests__/` | `tests/` |
| `{{SOURCE_DIR}}` | `structure.source_layout` | `src/` | `src/` | `src/` |
| `{{CI_PLATFORM}}` | `ci.platform` | `GitHub Actions` | `GitHub Actions` | `GitHub Actions` |
| `{{PACKAGE_MANAGER}}` | `build.tool` or detected | `cargo` | `npm` | `pip` |
| `{{UNSAFE_POLICY}}` | Language-specific safety rules | `#![forbid(unsafe_code)]` | `strict TypeScript` | `type hints required` |
| `{{ERROR_PATTERN}}` | Language-specific error handling | `Result<T, Error>` | `try/catch + custom errors` | `raise/except` |
| `{{DOC_COMMENT_STYLE}}` | Language convention | `/// doc comment` | `/** JSDoc */` | `"""docstring"""` |
| `{{QUALITY_GATES}}` | Ordered from CI pipeline | check → clippy → fmt → test | lint → typecheck → test | lint → typecheck → test |

**Backlog Tool Variables** (derived from `backlog_tool` profile section):

| Template Variable | Source | Example (backlogit) | Example (backlog-md) |
|---|---|---|---|
| `{{BACKLOG_TOOL_NAME}}` | `backlog_tool.tool_name` | `backlogit` | `backlog-md` |
| `{{BACKLOG_DIRECTORY}}` | `backlog_tool.directory` | `.backlogit` | `backlog` |
| `{{BACKLOG_TOOL_TYPE}}` | `backlog_tool.tool_type` | `both` | `both` |
| `{{OP_CREATE_MCP}}` | Registry `operations.create_task.mcp_tool` | `backlogit_create_item` | `task_create` |
| `{{OP_LIST_MCP}}` | Registry `operations.list_tasks.mcp_tool` | `backlogit_list_items` | `task_list` |
| `{{OP_GET_MCP}}` | Registry `operations.get_task.mcp_tool` | `backlogit_get_item` | `task_view` |
| `{{OP_UPDATE_MCP}}` | Registry `operations.update_task.mcp_tool` | `backlogit_update_item` | `task_edit` |
| `{{OP_MOVE_MCP}}` | Registry `operations.move_task.mcp_tool` | `backlogit_move_item` | `task_edit` |
| `{{OP_SEARCH_MCP}}` | Registry `operations.search_tasks.mcp_tool` | `backlogit_search_items` | `task_search` |
| `{{OP_COMPLETE_MCP}}` | Registry `operations.complete_task.mcp_tool` | `backlogit_move_item` | `task_complete` |
| `{{STATUS_TODO}}` | Registry `status_values.todo` | `queued` | `To Do` |
| `{{STATUS_IN_PROGRESS}}` | Registry `status_values.in_progress` | `active` | `In Progress` |
| `{{STATUS_DONE}}` | Registry `status_values.done` | `done` | `Done` |
| `{{STATUS_BLOCKED}}` | Registry `status_values.blocked` | `blocked` | `Blocked` |
| `{{FIELD_TASK_ID}}` | Registry `field_mapping.task_id` | `id` | `id` |
| `{{FIELD_TITLE}}` | Registry `field_mapping.title` | `title` | `title` |
| `{{FIELD_STATUS}}` | Registry `field_mapping.status` | `status` | `status` |
| `{{FIELD_LABELS}}` | Registry `field_mapping.labels` | `labels` | `labels` |
| `{{BACKLOG_TOOLS}}` | Backlog MCP server name from registry | `backlog` | `backlog` |

#### Step 1.3: Select Primitive Set

If `primitives` input is provided, filter the installation to only the requested primitives. Otherwise, install all 9.

Map primitives to template groups:

| Primitive | Template Groups |
|---|---|
| 1 - State & Context | `agents/memory`, `skills/compact-context`, `skills/compound` |
| 2 - Task Granularity | Embedded in `foundation/AGENTS.md`, `agents/backlog-harvester` |
| 3 - Model Routing | Embedded in `foundation/AGENTS.md`, all agent definitions |
| 4 - Orchestration | `agents/backlog-harvester`, `agents/build-orchestrator`, `agents/harness-architect`, `agents/pr-review`, `skills/build-feature`, `skills/fix-ci` |
| 5 - Guardrails | `foundation/constitution`, `policies/workflow-policies`, `foundation/AGENTS.md` |
| 6 - Injection Points | `instructions/*`, `foundation/copilot-instructions` |
| 7 - Observability | `agents/review/*`, `agents/doc-ops`, `skills/review`, `skills/plan-review` |
| 8 - Workflow Policy | `policies/workflow-policies` |
| 9 - Repo Knowledge | `foundation/AGENTS.md` (progressive disclosure), `instructions/architecture-doc`, `agents/doc-ops` |

### Phase 2: Template Composition

#### Step 2.1: Foundation Layer

Generate the constitutional foundation first, as all other artifacts reference it:

1. **Constitution** (`constitution.instructions.md`): Adapt principles for the target technology. Replace language-specific rules (e.g., `unsafe` code policy becomes TypeScript strict mode, Python type-hint enforcement, etc.). Preserve all 9 universal principles.

2. **AGENTS.md**: Generate the root AGENTS.md with technology-specific quality gates, code style conventions, error handling patterns, and terminal command policies.

3. **copilot-instructions.md**: Generate shared development guidelines with project structure, commands, and conventions.

#### Step 2.2: Instruction Layer

Generate instruction files. These use `applyTo` patterns to scope their rules:

1. **Technology instructions** (`{language}.instructions.md`): Language-specific coding conventions, error handling, naming, documentation standards. Use `technology.instructions.md.tmpl` as the base.

2. **Universal instructions** (no technology adaptation needed):
   * `commit-message.instructions.md` — Adapt scopes to match workspace directory structure
   * `markdown.instructions.md` — Universal (install as-is with minimal adaptation)
   * `writing-style.instructions.md` — Universal (install as-is)
   * `git-merge.instructions.md` — Universal (install as-is)
   * `pull-request.instructions.md` — Universal (install as-is)
   * `prompt-builder.instructions.md` — Universal (install as-is)
   * `architecture-doc.instructions.md` — Progressive disclosure and architecture documentation rules (Primitive 9)

3. **Backlog integration instructions** (`backlog-integration.instructions.md`): Generated from the backlog tool registry. Maps abstract operations to the specific tool's MCP names and CLI commands. Only generated when a backlog tool is detected or registered.

#### Step 2.3: Backlog Tool Registration

If the workspace profile includes a detected backlog tool (`backlog_tool.detected: true`):

1. **Copy the matching registry**: Load the pre-built registry from `{autoharness_home}/templates/backlog/registries/{tool_name}.registry.yaml`
2. **Install as `.autoharness/backlog-registry.yaml`** in the target workspace
3. **Resolve backlog template variables** from the registry into all templates
4. **Add the backlog MCP server** to the tools list in all agent definitions that interact with the backlog

If no backlog tool is detected:

1. **Ask the user** if they want to register a backlog tool manually
2. If yes, present the available registries (backlogit, backlog-md) and let them choose or provide a custom registry
3. If no, skip backlog integration — agents will use manual `.backlog/` markdown files without tool integration
4. Generate a minimal backlog structure regardless (`.backlog/` or tool-specific directory)

If the user wants to use a tool not yet in the registry:

1. Generate a skeleton registry from `{autoharness_home}/schemas/backlog-tool-registry.schema.json`
2. Present it to the user for completion
3. Install the completed registry

#### Step 2.4: Agent Layer

Generate agent definitions. Each agent template has technology-specific sections that vary:

1. **Pipeline agents**: backlog-harvester, build-orchestrator, harness-architect, pr-review
   * Adapt build/test/lint commands throughout
   * Adapt quality gate sequences
   * Adapt model routing tiers (preserve structure, adjust agent assignments if needed)

2. **Support agents**: memory, doc-ops, prompt-builder
   * Minimal technology adaptation needed
   * Adapt file path patterns for the workspace structure

3. **Expert agent**: Generate a technology-specific expert agent (equivalent to `rust-engineer.agent.md` but for the target language). Name it `{language}-engineer.agent.md`.

4. **Review personas**: Generate from review persona templates
   * `architecture-strategist.agent.md` — Universal with domain adaptation
   * `constitution-reviewer.agent.md` — References local constitution
   * `scope-boundary-auditor.agent.md` — Universal
   * `technology-reviewer.agent.md` → `{language}-reviewer.agent.md` — Fully technology-specific
   * `concurrency-reviewer.agent.md` — Include only for languages with concurrency primitives
   * `learnings-researcher.agent.md` — Universal

#### Step 2.4: Skill Layer

Generate skill files:

1. **Technology-adapted skills**:
   * `build-feature/SKILL.md` — Adapt test runner commands, compilation checks, stall timeouts
   * `fix-ci/SKILL.md` — Adapt CI pipeline order, tool-specific fix strategies
   * `impl-plan/SKILL.md` — Adapt execution postures for the technology

2. **Universal skills** (minimal adaptation):
   * `brainstorm/SKILL.md`
   * `compact-context/SKILL.md`
   * `compound/SKILL.md`
   * `plan-review/SKILL.md`
   * `review/SKILL.md`

#### Step 2.5: Policy Layer

Generate the workflow policy registry from `workflow-policies.md.tmpl`:

* P-001 (Single-Feature Completion) — Universal
* P-002 (TDD Gate) — Adapt test commands and red-phase detection
* P-003 (Decomposition Chain) — Universal
* P-004 (Red Phase Before Implementation) — Adapt compilation and test failure detection
* P-005 (Policy Violation Telemetry) — Universal

#### Step 2.6: Prompt Layer

Generate prompt files:

* `ping-loop.prompt.md` — Universal

#### Step 2.7: Backlog Structure

Initialize the backlog directory:

```text
.backlog/
  config.yml          # Backlog tool configuration
  queue.md            # Unrefined ideas
  tasks/              # Empty, ready for task creation
  plans/              # Empty, ready for plans
  brainstorm/         # Empty, ready for brainstorm docs
  compound/           # Empty, ready for learnings
  reviews/            # Empty, ready for review artifacts
  memory/             # Empty, ready for session memory
  completed/          # Empty, archive for done work
```

### Phase 3: Installation

#### Step 3.1: Staging

If `dry_run` is true, write all artifacts to `.autoharness/staging/` and report what would be installed. Halt here.

#### Step 3.2: Write Artifacts

Write generated artifacts to the target workspace. Use the following directory mapping:

| Source Template Group | Target Location |
|---|---|
| Foundation / AGENTS.md | `{workspace}/AGENTS.md` |
| Foundation / copilot-instructions.md | `{workspace}/.github/copilot-instructions.md` |
| Foundation / constitution | `{workspace}/.github/instructions/constitution.instructions.md` |
| Instructions | `{workspace}/.github/instructions/` |
| Agents | `{workspace}/.github/agents/` |
| Review Personas | `{workspace}/.github/agents/review/` |
| Research Agents | `{workspace}/.github/agents/research/` |
| Skills | `{workspace}/.github/skills/{name}/SKILL.md` |
| Policies | `{workspace}/.github/policies/` |
| Prompts | `{workspace}/.github/prompts/` |
| Backlog | `{workspace}/.backlog/` |

#### Step 3.3: Write Installation Manifest

Create `.autoharness/harness-manifest.yaml` recording:

```yaml
schema_version: "1.0.0"
installed_at: "{{ISO_8601_TIMESTAMP}}"
autoharness_version: "1.0.0"
autoharness_home: "{{AUTOHARNESS_HOME}}"
profile_hash: "{{SHA256_OF_PROFILE}}"
primitives_installed: [1, 2, 3, 4, 5, 6, 7, 8, 9]
artifacts:
  - path: ".github/instructions/constitution.instructions.md"
    primitive: 5
    template: "foundation/constitution.instructions.md.tmpl"
    checksum: "{{SHA256}}"
  # ... all installed artifacts
variables_used:
  PROJECT_NAME: "{{value}}"
  PRIMARY_LANGUAGE: "{{value}}"
  # ... all resolved variables
```

### Phase 4: Verification

#### Step 4.1: Cross-Reference Validation

Verify all installed artifacts are internally consistent:

* Every agent's `tools:` field references tools that exist in the workspace (or are standard VS Code tools)
* Every agent's skill references point to installed skill SKILL.md files
* Every instruction's `applyTo` pattern matches at least one file in the workspace
* Every policy references agents that were installed
* The constitution references technology-specific rules that match the installed language instructions

#### Step 4.2: Structural Validation

* All YAML frontmatter is valid
* All Markdown files pass basic structural checks (headings, code fences closed)
* No template variables remain unresolved (no `{{...}}` in output files)
* File paths in cross-references resolve to actual files

#### Step 4.3: Report

Present an installation summary:

```text
Harness Installation Complete
─────────────────────────────
Workspace: {{PROJECT_NAME}}
Language:  {{PRIMARY_LANGUAGE}}
Primitives installed: 8/8

Artifacts created:
  Instructions:    {{count}}
  Agents:          {{count}}
  Review Personas: {{count}}
  Skills:          {{count}}
  Policies:        {{count}}
  Prompts:         {{count}}
  Backlog dirs:    {{count}}

Verification: {{PASS/FAIL with details}}
```

## Quality Criteria

* No template variables remain in output files
* All cross-references between artifacts resolve
* The installed harness passes structural validation
* The installation manifest accurately records every artifact and variable
* A second run with the same profile produces identical output (idempotent)
