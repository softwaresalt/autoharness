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
* `preset`: (Optional, default `standard`) One of `starter`, `standard`, or `full`. Presets define the default primitive set and capability-pack defaults.
* `primitives`: (Optional) Comma-separated list of primitive numbers (1-10) to install. Defaults to the selected preset.
* `capability_packs`: (Optional) Comma-separated list of capability packs: `agent-intercom`, `agent-engram`, `backlogit`, `browser-verification`, `strict-safety`, `release-observability`.
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

#### Step 1.0b: Load Operator Configuration

Check for `.autoharness/config.yaml` in the target workspace. If present:

1. Validate against `{autoharness_home}/schemas/harness-config.schema.json`
2. Extract operator preferences for: preset, capability packs, backlog configuration (tool, directory, prefix map), docs directory structure, model routing, and template variable overrides
3. Merge with the workspace profile — operator config values take precedence over auto-detected profile values
4. If the config specifies `backlog.prefix_map`, use those prefixes in the generated `config.yml` instead of the defaults
5. If the config specifies `docs.root` or `docs.subdirectories`, use those paths for knowledge artifact output directories
6. If the config specifies `overrides`, apply those template variable values directly, overriding any profile-derived values

If the file does not exist, proceed with profile-only installation using default values. The operator can create `.autoharness/config.yaml` later and re-run install or tune to apply preferences.

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

**Capability-Pack Variables** (derived from `capability_packs` and integration signals in the profile):

| Template Variable | Source | Example (enabled) | Example (disabled) |
|---|---|---|---|
| `{{AGENT_INTERCOM_ENABLED}}` | `capability_packs` contains `agent-intercom` | `true` | `false` |
| `{{AGENT_INTERCOM_DETECTED}}` | `agent_intercom.detected` | `true` | `false` |
| `{{AGENT_INTERCOM_CONFIG_PATHS}}` | `agent_intercom.config_paths[]` | `.vscode/mcp.json, .intercom/settings.json` | empty |
| `{{AGENT_ENGRAM_ENABLED}}` | `capability_packs` contains `agent-engram` | `true` | `false` |
| `{{AGENT_ENGRAM_DETECTED}}` | `agent_engram.detected` | `true` | `false` |
| `{{AGENT_ENGRAM_CONFIG_PATHS}}` | `agent_engram.config_paths[]` | `.vscode/mcp.json, .engram/config.toml` | empty |

#### Step 1.3: Select Preset, Primitive Set, and Capability Packs

Resolve the installation shape in this order:

1. If `primitives` input is provided, use it directly.
2. Otherwise, use the primitive set implied by `preset`.
3. If no preset is provided, default to `standard`.

Preset defaults:

| Preset | Default Primitives | Default Capability Packs | Best For |
|---|---|---|---|
| `starter` | 1, 2, 4, 5, 6, 8, 9 | none | First-time adoption, smaller repos |
| `standard` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | `strict-safety` when runtime risk is detected | Most repositories |
| `full` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | All recommended packs from the profile | Higher-operational-maturity teams |

If `capability_packs` input is omitted, use the profile's `harness_recommendations.capability_packs` for `full`, or apply no optional packs for `starter`/`standard` unless a pack is strongly recommended by detected runtime surfaces.

Capability-pack overlays:

| Capability Pack | Overlay Behavior |
|---|---|
| `agent-intercom` | Installs `agent-intercom.instructions.md` and threads heartbeat, broadcast, approval-routing, and operator-wait expectations through foundation docs, pipeline agents, long-running skills, and the ping-loop prompt |
| `agent-engram` | Installs `agent-engram.instructions.md` and threads engram-first indexed search, workspace binding, freshness checks, and code-graph-driven analysis through foundation docs and analysis-heavy workflows |
| `backlogit` | Installs `backlogit.instructions.md` and threads backlogit-native query, queue, dependency, memory, checkpoint, comment, and commit-trace workflows through backlog-aware artifacts |
| `browser-verification` | Strengthens browser-specific runtime verification guidance |
| `strict-safety` | Makes safety-mode usage more explicit and more frequent |
| `release-observability` | Deepens operational closure and post-release monitoring guidance |

#### Step 1.3b: Apply the Formal Overlay Contract

Treat every selected capability pack as a cross-cutting overlay rather than a single-file option.

For each selected pack, define and apply:

1. **Eligibility signals** — why the pack was selected or recommended
2. **Overlay targets** — the artifact classes that must be updated together
3. **Behavior deltas** — the changes to workflow behavior introduced by the pack
4. **Verification checks** — how install verification proves the overlay is coherently woven

Overlay targets may span:

* Foundation docs (`AGENTS.md`, `copilot-instructions.md`, constitution)
* Instruction files
* Pipeline agents
* Long-running or gating skills
* Prompts
* Policies

Example overlay target map for `agent-intercom`:

| Overlay Element | Required Targets |
|---|---|
| Startup / liveness | foundation docs, `ping-loop.prompt.md`, long-running agents / skills |
| Approval routing | constitution, intercom instructions, risky execution skills |
| Progress visibility | pipeline agents, review / verification / closure skills |
| Operator wait flows | pipeline agents and long-running skills that block on clarification |

Do not model a capability pack as a single isolated artifact when its behavior is inherently cross-cutting.

Example overlay target map for `backlogit`:

| Overlay Element | Required Targets |
|---|---|
| Token-efficient lookup | foundation docs, backlog instructions, backlog-aware agents |
| Ready-work selection | build-orchestrator and backlog-aware instructions |
| Agent continuity | memory agent, foundation docs |
| Traceability | backlog-aware agents and instructions |

Example overlay target map for `agent-engram`:

| Overlay Element | Required Targets |
|---|---|
| Indexed search routing | foundation docs, `agent-engram.instructions.md`, research / planning / build workflows |
| Workspace binding and freshness | instructions plus workflows that depend on indexed results |
| Code-graph blast radius analysis | harness / build / repair workflows that inspect symbols and callers |

Map primitives to template groups:

| Primitive | Template Groups |
|---|---|
| 1 - State & Context | `agents/memory`, `agents/research/learnings-researcher`, `skills/compact-context`, `skills/compound` |
| 2 - Task Granularity | Embedded in `foundation/AGENTS.md`, `agents/backlog-harvester` |
| 3 - Model Routing | Embedded in `foundation/AGENTS.md`, all agent definitions |
| 4 - Orchestration | `agents/deliberator`, `agents/backlog-harvester`, `agents/build-orchestrator`, `agents/harness-architect`, `agents/pr-review`, `skills/deliberate`, `skills/spike`, `skills/build-feature`, `skills/fix-ci` |
| 5 - Guardrails | `foundation/constitution`, `policies/workflow-policies`, `foundation/AGENTS.md`, `skills/safety-modes` |
| 6 - Injection Points | `instructions/*`, `foundation/copilot-instructions` |
| 7 - Observability | `agents/review/*`, `agents/doc-ops`, `skills/review`, `skills/plan-review` |
| 8 - Workflow Policy | `policies/workflow-policies` |
| 9 - Repo Knowledge | `foundation/AGENTS.md` (progressive disclosure), `instructions/architecture-doc`, `agents/doc-ops` |
| 10 - Operational Closure | `skills/runtime-verification`, `skills/operational-closure`, PR and CI handoff sections in pipeline templates |

### Phase 2: Template Composition

#### Step 2.1: Foundation Layer

Generate the constitutional foundation first, as all other artifacts reference it:

1. **Constitution** (`constitution.instructions.md`): Adapt principles for the target technology. Replace language-specific rules (e.g., `unsafe` code policy becomes TypeScript strict mode, Python type-hint enforcement, etc.). Preserve all 10 universal principles.

2. **AGENTS.md**: Generate the root AGENTS.md with technology-specific quality gates, code style conventions, error handling patterns, and terminal command policies.

3. **copilot-instructions.md**: Generate shared development guidelines with project structure, commands, and conventions.

If the `agent-intercom` capability pack is enabled, weave the intercom operating model into both files so heartbeat, milestone broadcasting, approval routing, and degraded-mode handling are part of the normal harness narrative.

If the `agent-engram` capability pack is enabled, weave the engram-first search operating model into both files so indexed lookup, workspace binding, and freshness / fallback behavior become part of the normal harness narrative.

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

4. **Capability-pack instructions**: When `agent-intercom` is enabled, install `agent-intercom.instructions.md` and use it as the authoritative reference for heartbeat, remote approval, operator steering, and standby workflows.
   When `agent-engram` is enabled, install `agent-engram.instructions.md` and use it as the authoritative reference for engram-first search, workspace binding, index freshness, and indexed-search fallback workflows.
   When `backlogit` is enabled, install `backlogit.instructions.md` and use it as the authoritative reference for backlogit-native query, queue, dependency, memory, checkpoint, comment, and traceability workflows.

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

1. **Pipeline agents**: deliberator, backlog-harvester, build-orchestrator, harness-architect, pr-review
   * Adapt build/test/lint commands throughout
   * Adapt quality gate sequences
   * Adapt model routing tiers (preserve structure, adjust agent assignments if needed)
   * When `agent-intercom` is enabled, add explicit workflow guidance for ping/heartbeat, broadcast milestones, approval routing, and operator clarification waits
   * When `agent-engram` is enabled, add explicit workflow guidance for engram-first search, workspace binding/index verification, and code-graph or impact-analysis style diagnostics
   * When `backlogit` is enabled, add explicit workflow guidance for queue-first work selection, dependency-aware planning, checkpoint persistence, and commit traceability

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

#### Step 2.5: Skill Layer

Generate skill files:

1. **Technology-adapted skills**:
   * `build-feature/SKILL.md` — Adapt test runner commands, compilation checks, stall timeouts
   * `fix-ci/SKILL.md` — Adapt CI pipeline order, tool-specific fix strategies
   * `impl-plan/SKILL.md` — Adapt execution postures for the technology

2. **Universal skills** (minimal adaptation; install only when their governing primitives are selected):
   * `deliberate/SKILL.md`
   * `spike/SKILL.md`
   * `compact-context/SKILL.md`
   * `compound/SKILL.md`
   * `plan-review/SKILL.md`
   * `review/SKILL.md`
   * `safety-modes/SKILL.md` — Install when Primitive 5 is selected
   * `runtime-verification/SKILL.md` — Install when Primitive 10 is selected
   * `operational-closure/SKILL.md` — Install when Primitive 10 is selected

When `agent-intercom` is enabled, weave operator visibility guidance into the long-running and gating skills rather than treating it as a separate isolated instruction.

When `agent-engram` is enabled, weave indexed-search guidance into research, planning, build, and repair skills rather than treating it as a generic footnote.

#### Step 2.6: Policy Layer

Generate the workflow policy registry from `workflow-policies.md.tmpl`:

* P-001 (Single-Feature Completion) — Universal
* P-002 (TDD Gate) — Adapt test commands and red-phase detection
* P-003 (Decomposition Chain) — Universal
* P-004 (Red Phase Before Implementation) — Adapt compilation and test failure detection
* P-005 (Policy Violation Telemetry) — Universal

#### Step 2.7: Prompt Layer

Generate prompt files:

* `ping-loop.prompt.md` — Universal

#### Step 2.8: Backlog Structure

Initialize the backlog directory. Backlog tools are used **exclusively for workflow management** — active work items live in `queue/`, completed items move to `archive/`. Long-lived knowledge artifacts (compound learnings, plans, decisions, memory, closure records) are stored in `docs/` at the workspace root, not in the backlog.

```text
{{BACKLOG_DIRECTORY}}/
  config.yml          # Backlog tool configuration (prefix map, statuses, labels)
  queue/              # Active work items — flat directory, no subdirectories
    .stash.md         # Parked ideas and deferred outcomes not yet promoted
  archive/            # Completed and archived work items
```

Work items in `queue/` follow the naming convention:

```text
{prefix}-{NNN}-{slug}.md               # Level 1 (features, epics)
{prefix}-{NNN}.{NNN}-{slug}.md         # Level 2 (tasks, sub-epics)
{prefix}-{NNN}.{NNN}.{NNN}-{slug}.md   # Level 3 (subtasks)
```

The prefix map is configured in `config.yml` with concrete single or two-letter defaults:

| Type | Prefix | Example filename |
|---|---|---|
| Feature | `F` | `F-001-user-auth.md` |
| Task | `T` | `T-001.001-add-login-endpoint.md` |
| Spike | `S` | `S-002-evaluate-caching.md` |
| Deliberation | `D` | `D-003-api-strategy.md` |
| Bug | `B` | `B-004-null-pointer-fix.md` |
| Epic | `E` | `E-005-auth-overhaul.md` |
| Subtask | `ST` | `ST-001.001.001-write-unit-test.md` |

When the `backlogit` capability pack is active, the installer reads prefixes from backlogit's project YAML metadata and overrides these defaults during installation.

Long-lived knowledge structure (in `docs/` at workspace root):

```text
docs/
  compound/           # Institutional learnings organized by category
  plans/              # Implementation plans (compacted: plan + reviews → decided-plan)
  decisions/          # ADRs and deliberation outcomes
  memory/             # Session state and checkpoints
  closure/            # Runtime verification, code review, safety-check, and closure records
```

Reviews are appended to the plan they review (not separate files). The compact-context skill consolidates plan + appended reviews into a decided-plan.

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
| Backlog config + stash | `{workspace}/{BACKLOG_DIRECTORY}/` (queue/, archive/, config.yml, queue/.stash.md) |
| Knowledge directories | `{workspace}/docs/` (compound/, plans/, decisions/, memory/, closure/) |

#### Step 3.3: Write Installation Manifest

Create `.autoharness/harness-manifest.yaml` recording:

```yaml
schema_version: "1.0.0"
installed_at: "{{ISO_8601_TIMESTAMP}}"
autoharness_version: "1.0.0"
autoharness_home: "{{AUTOHARNESS_HOME}}"
profile_hash: "{{SHA256_OF_PROFILE}}"
config_hash: "{{SHA256_OF_CONFIG_OR_NULL}}"  # null if no .autoharness/config.yaml was present
install_preset: "{{PRESET}}"
capability_packs: [{{CAPABILITY_PACKS}}]
# Example when Engram is enabled:
# capability_packs: ["agent-engram"]
capability_pack_overlays:
  - pack: "{{PACK_NAME}}"
    overlay_targets: [{{OVERLAY_TARGETS}}]
    verification_checks: [{{OVERLAY_VERIFICATION_CHECKS}}]
  # Example agent-engram overlay:
  # - pack: "agent-engram"
  #   overlay_targets: ["foundation-docs", "instructions", "analysis-workflows"]
  #   verification_checks: ["agent-engram instruction installed", "engram-first search guidance woven"]
primitives_installed: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
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
* If `agent-intercom` is enabled, the intercom instruction file is installed and the affected agents / skills reference heartbeat, broadcast, or approval-routing behavior consistently
* If `agent-engram` is enabled, the engram instruction file is installed and the affected agents / skills reference indexed search, workspace binding, freshness, or fallback behavior consistently
* If `backlogit` is enabled, the backlogit instruction file is installed and the affected agents / skills reference query, queue, checkpoint, or traceability behavior consistently
* If any capability pack is enabled, its declared overlay targets and verification checks are satisfied rather than only the pack name being recorded

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
Primitives installed: selected subset / 10
Preset: {{PRESET}}
Capability packs: {{CAPABILITY_PACKS_OR_NONE}}

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
