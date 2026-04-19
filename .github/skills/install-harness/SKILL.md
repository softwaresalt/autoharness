---
description: "Multi-phase installation workflow that composes harness primitives from templates into a target workspace based on its discovered profile"
---

## Install Harness

Compose and install a complete agent harness into a target workspace. Uses the workspace profile from the workspace-discovery skill to customize universal templates for the target environment's specific technology stack, conventions, and workflow requirements.

autoharness operates as a globally-installed tool. Templates are read from the autoharness home directory; only generated harness artifacts are written to the target workspace. The target workspace never contains autoharness engine files — only the output artifacts it needs to function.

## When to Use

Invoke this skill after workspace-discovery has produced a profile, or let the auto-mergeinstall agent invoke it automatically. The skill handles template selection, variable substitution, artifact generation, and installation verification.

## Inputs

* `autoharness_home`: (Required) Absolute path to the autoharness installation (contains `templates/`, `schemas/`). Resolved by the invoking agent via: `AUTOHARNESS_HOME` env var → `autoharness home` CLI → agent directory traversal → `~/.autoharness/`.
* `workspace_path`: (Required) Absolute path to the target workspace root. Must be a different directory from `autoharness_home`.
* `profile_path`: (Required) Path to workspace profile YAML (typically `{workspace_path}/.autoharness/workspace-profile.yaml`).
* `preset`: (Optional, default `standard`) One of `starter`, `standard`, or `full`. Presets define the default primitive set and capability-pack defaults.
* `primitives`: (Optional) Comma-separated list of primitive numbers (1-10) to install. Defaults to the selected preset.
* `capability_packs`: (Optional) Comma-separated list of capability packs: `agent-intercom`, `agent-engram`, `backlogit`, `browser-verification`, `continuous-learning`, `strict-safety`, `release-observability`, `adversarial-review`.
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
2. Extract operator preferences for: preset, primary stack pack, stack packs, install layers, capability packs, backlog configuration (tool, directory, suffix map), docs directory structure, model routing, and template variable overrides
3. Merge with the workspace profile — operator config values take precedence over auto-detected profile values
4. Derive `{{SUFFIX_*}}` template variables from `backlog.suffix_map` (falling back to backlogit project YAML when backlogit pack is active, then schema defaults)
5. Derive `{{DOCS_ROOT}}` and `{{DOCS_*}}` template variables from `docs.root` and `docs.subdirectories` (falling back to schema defaults)
6. Derive `{{PRIMARY_STACK_PACK}}`, `{{STACK_PACKS_YAML}}`, `{{INSTALL_LAYERS_YAML}}`, and `{{CAPABILITY_PACKS_YAML}}` from the merged composition state for config write-back
7. If the config specifies `overrides`, apply those template variable values directly, overriding any profile-derived values

If the file does not exist, proceed with profile-only installation using schema default values for all suffix and docs variables. After installation, the installer writes the resolved `.autoharness/config.yaml` recording the actual values used (see Step 3.4).

#### Step 1.1: Load Profile

Read the workspace profile from `profile_path`. Validate against the workspace profile schema. If validation fails, halt and report the specific schema violations.

#### Step 1.2: Compute Template Variables

Derive all template variables from the profile. The variable resolution table defines how profile fields map to template placeholders:

| Template Variable | Source | Example (Rust) | Example (TypeScript) | Example (Python) |
|---|---|---|---|---|
| `{{PROJECT_NAME}}` | Directory name of workspace | `my-service` | `my-app` | `my-api` |
| `{{PRIMARY_LANGUAGE}}` | `languages.primary` | `Rust` | `TypeScript` | `Python` |
| `{{PRIMARY_LANGUAGE_LOWER}}` | `lowercase(languages.primary)` | `rust` | `typescript` | `python` |
| `{{LANGUAGE_VERSION}}` | `languages.version` (detected from toolchain config) | `2024` | `ES2022` | `3.12` |
| `{{LANGUAGE_NOTES}}` | Synthesized from language profile (key version/edition note) | `(Rust 2024 edition)` | `(strict mode)` | `(requires 3.12+)` |
| `{{BUILD_COMMAND}}` | `build.command` | `cargo build` | `npm run build` | `python -m build` |
| `{{TEST_COMMAND}}` | `test.command` | `cargo test` | `npm test` | `pytest` |
| `{{LINT_COMMAND}}` | `lint.command` | `cargo clippy -- -D warnings` | `npm run lint` | `ruff check .` |
| `{{FORMAT_COMMAND}}` | `format.command` | `cargo fmt --all -- --check` | `npx prettier --check .` | `ruff format --check .` |
| `{{FORMAT_FIX_COMMAND}}` | Derived from format tool | `cargo fmt --all` | `npx prettier --write .` | `ruff format .` |
| `{{BUILD_CHECK_COMMAND}}` | `build.check_command` (fast compilation check, no test) | `cargo check --all-targets` | `tsc --noEmit` | `python -m py_compile $(find src -name "*.py")` |
| `{{FORMAT_CHECK_COMMAND}}` | `format.check_command` (read-only format gate) | `cargo fmt --all -- --check` | `npx prettier --check .` | `ruff format --check .` |
| `{{TEST_DIR}}` | `test.directory` | `tests/` | `__tests__/` | `tests/` |
| `{{SOURCE_DIR}}` | `structure.source_layout` | `src/` | `src/` | `src/` |
| `{{CI_PLATFORM}}` | `ci.platform` | `GitHub Actions` | `GitHub Actions` | `GitHub Actions` |
| `{{CI_WORKFLOW_GLOB}}` | Derived from `ci.platform` | `**/.github/workflows/*.yml` | `**/.github/workflows/*.yml` | `**/.github/workflows/*.yml` |
| `{{REPO_OWNER}}` | Parsed from git remote URL (`owner/repo`) | `my-org` | `my-org` | `my-org` |
| `{{REPO_NAME}}` | Parsed from git remote URL (`owner/repo`) | `my-service` | `my-app` | `my-api` |
| `{{BUILD_TOOL}}` | `build.tool` | `cargo` | `npm` | `pip` |
| `{{FORMATTER}}` | `format.tool` | `rustfmt` | `prettier` | `ruff` |
| `{{LINTER}}` | `lint.tool` | `clippy` | `eslint` | `ruff` |
| `{{TEST_RUNNER}}` | `test.runner` | `cargo test` | `jest` | `pytest` |
| `{{UNSAFE_POLICY}}` | Language-specific safety rules | `#![forbid(unsafe_code)]` | `strict TypeScript` | `type hints required` |
| `{{ERROR_PATTERN}}` | Language-specific error handling | `Result<T, Error>` | `try/catch + custom errors` | `raise/except` |
| `{{DOC_COMMENT_STYLE}}` | Language convention | `/// doc comment` | `/** JSDoc */` | `"""docstring"""` |
| `{{LANGUAGE_FILE_GLOB}}` | Language convention | `**/*.rs` | `**/*.ts,**/*.tsx` | `**/*.py` |
| `{{UNIMPLEMENTED_MARKER}}` | Language convention | `unimplemented!("Worker: ...")` | `throw new Error("Not implemented: ...")` | `raise NotImplementedError("...")` |
| `{{MCP_SDK}}` | `frameworks.mcp_sdk` (when detected) | _(N/A)_ | `@modelcontextprotocol/sdk` | `mcp` |
| `{{MCP_TRANSPORT}}` | `frameworks.mcp_transport` (when detected) | _(N/A)_ | `stdio` | `stdio` |
| `{{MCP_PROJECT_STRUCTURE}}` | Derived from language and project layout | _(N/A)_ | _(project tree)_ | _(project tree)_ |
| `{{REPOSITORY_OPERATING_MODEL}}` | Derived from workspace architecture | _(brief description)_ | _(brief description)_ | _(brief description)_ |
| `{{QUALITY_GATE_1_NAME}}` | `ci.quality_gates[0]` (name) | `check` | `lint` | `lint` |
| `{{QUALITY_GATE_1}}` | `ci.quality_gates[0]` (command) | `cargo check --all-targets` | `npm run lint` | `ruff check .` |
| `{{QUALITY_GATE_2_NAME}}` | `ci.quality_gates[1]` (name) | `clippy` | `typecheck` | `typecheck` |
| `{{QUALITY_GATE_2}}` | `ci.quality_gates[1]` (command) | `cargo clippy -- -D warnings` | `tsc --noEmit` | `mypy src/` |
| `{{QUALITY_GATE_3_NAME}}` | `ci.quality_gates[2]` (name) | `fmt` | `test` | `test` |
| `{{QUALITY_GATE_3}}` | `ci.quality_gates[2]` (command) | `cargo fmt --all -- --check` | `npm test` | `pytest` |
| `{{QUALITY_GATE_4_NAME}}` | `ci.quality_gates[3]` (name, optional) | `test` | _(empty)_ | _(empty)_ |
| `{{QUALITY_GATE_4}}` | `ci.quality_gates[3]` (command, optional) | `cargo test` | _(empty)_ | _(empty)_ |

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
| `{{OP_CREATE_CLI}}` | Registry `operations.create_task.cli_command` | `backlogit add` | `backlog task create` |
| `{{OP_LIST_CLI}}` | Registry `operations.list_tasks.cli_command` | `backlogit list` | `backlog task list` |
| `{{OP_GET_CLI}}` | Registry `operations.get_task.cli_command` | `backlogit show {id}` | `backlog task view {id}` |
| `{{OP_UPDATE_CLI}}` | Registry `operations.update_task.cli_command` | `backlogit update {id}` | `backlog task edit {id}` |
| `{{OP_MOVE_CLI}}` | Registry `operations.move_task.cli_command` | `backlogit move {id} {status}` | `backlog task move {id}` |
| `{{OP_SEARCH_CLI}}` | Registry `operations.search_tasks.cli_command` | `backlogit search {query}` | `backlog task search` |
| `{{OP_COMPLETE_CLI}}` | Registry `operations.complete_task.cli_command` | `backlogit done {id}` | `backlog task complete {id}` |

**Status Variables** (derived from `registry.status_values` — these map abstract status names to tool-specific strings):

| `{{STATUS_QUEUED}}` | Registry `status_values.queued` | `queued` | `To Do` |
| `{{STATUS_ACTIVE}}` | Registry `status_values.active` | `active` | `In Progress` |
| `{{STATUS_DONE}}` | Registry `status_values.done` | `done` | `Done` |
| `{{STATUS_BLOCKED}}` | Registry `status_values.blocked` | `blocked` | `Blocked` |
| `{{FIELD_TASK_ID}}` | Registry `field_mapping.task_id` | `id` | `id` |
| `{{FIELD_TITLE}}` | Registry `field_mapping.title` | `title` | `title` |
| `{{FIELD_STATUS}}` | Registry `field_mapping.status` | `status` | `status` |
| `{{FIELD_LABELS}}` | Registry `field_mapping.labels` | `labels` | `labels` |
| `{{FIELD_PARENT_ID}}` | Registry `field_mapping.parent_id` | `parent` | `parent_id` |
| `{{FIELD_TYPE}}` | Registry `field_mapping.item_type` | `type` | `type` |
| `{{FIELD_DESCRIPTION}}` | Registry `field_mapping.description` | `description` | `description` |
| `{{BACKLOG_TOOLS}}` | Backlog MCP server name from registry | `backlog` | `backlog` |
| `{{EXTENDED_OPERATIONS_TABLE}}` | Registry `advanced_operations` formatted as Markdown table | _(backlogit-specific ops table)_ | _(empty string if not supported)_ |
| `{{FEATURE_SHIPMENTS}}` | Registry `features.shipments` | `true` | `false` |
| `{{OP_CREATE_SHIPMENT_MCP}}` | Registry `operations.create_shipment.mcp_tool` | `backlogit_create_shipment` | _(empty string)_ |
| `{{OP_GET_SHIPMENT_MCP}}` | Registry `operations.get_shipment.mcp_tool` | `backlogit_get_shipment` | _(empty string)_ |
| `{{OP_LIST_SHIPMENTS_MCP}}` | Registry `operations.list_shipments.mcp_tool` | `backlogit_list_shipments` | _(empty string)_ |
| `{{OP_CLAIM_SHIPMENT_MCP}}` | Registry `operations.claim_shipment.mcp_tool` | `backlogit_claim_shipment` | _(empty string)_ |
| `{{OP_SHIP_SHIPMENT_MCP}}` | Registry `operations.ship_shipment.mcp_tool` | `backlogit_ship_shipment` | _(empty string)_ |
| `{{OP_ADD_TO_SHIPMENT_MCP}}` | Registry `operations.add_to_shipment.mcp_tool` | `backlogit_add_to_shipment` | _(empty string)_ |
| `{{OP_RETURN_BLOCKED_MCP}}` | Registry `operations.return_blocked.mcp_tool` | `backlogit_return_blocked` | _(empty string)_ |

When the selected registry sets `features.shipments: false`, all `{{OP_*_SHIPMENT_MCP}}` variables MUST resolve to the empty string — never to a literal placeholder like "N/A". Shipment behavior is gated by the installed backlog capability/registry configuration (`features.shipments`), and generated artifacts should treat empty shipment-operation variables as the signal to omit shipment-specific commands or guidance.

**Suffix Variables** (derived from `config.backlog.suffix_map` → backlog tool auto-detection → schema defaults):

| Template Variable | Source | Default |
|---|---|---|
| `{{SUFFIX_FEATURE}}` | `config.backlog.suffix_map.feature` | `F` |
| `{{SUFFIX_CHORE}}` | `config.backlog.suffix_map.chore` | `C` |
| `{{SUFFIX_TASK}}` | `config.backlog.suffix_map.task` | `T` |
| `{{SUFFIX_SPIKE}}` | `config.backlog.suffix_map.spike` | `SP` |
| `{{SUFFIX_DELIBERATION}}` | `config.backlog.suffix_map.deliberation` | `D` |
| `{{SUFFIX_BUG}}` | `config.backlog.suffix_map.bug` | `B` |
| `{{SUFFIX_EPIC}}` | `config.backlog.suffix_map.epic` | `E` |
| `{{SUFFIX_SUBTASK}}` | `config.backlog.suffix_map.subtask` | `ST` |
| `{{SUFFIX_SHIPMENT}}` | `config.backlog.suffix_map.shipment` | `S` |

Resolution order: (1) operator `.autoharness/config.yaml` → (2) backlogit project YAML metadata (when backlogit capability pack is active) → (3) schema defaults above.

**Docs Path Variables** (derived from `config.docs.root` and `config.docs.subdirectories` → schema defaults):

| Template Variable | Source | Default | Description |
|---|---|---|---|
| `{{DOCS_ROOT}}` | `config.docs.root` | `docs` | Root directory for durable knowledge |
| `{{DOCS_COMPOUND}}` | `{DOCS_ROOT}/{config.docs.subdirectories.compound}` | `docs/compound` | Institutional learnings |
| `{{DOCS_PLANS}}` | `{DOCS_ROOT}/{config.docs.subdirectories.plans}` | `docs/plans` | Implementation plans |
| `{{DOCS_DECISIONS}}` | `{DOCS_ROOT}/{config.docs.subdirectories.decisions}` | `docs/decisions` | ADRs, deliberation outcomes, spike findings |
| `{{DOCS_MEMORY}}` | `{DOCS_ROOT}/{config.docs.subdirectories.memory}` | `docs/memory` | Session state and checkpoints |
| `{{DOCS_CLOSURE}}` | `{DOCS_ROOT}/{config.docs.subdirectories.closure}` | `docs/closure` | Verification, review, safety-check, closure records |
| `{{DOCS_DESIGN_DOCS}}` | `{DOCS_ROOT}/{config.docs.subdirectories.design_docs}` | `docs/design-docs` | Graduated design decisions and rationale |
| `{{DOCS_PRODUCT_SPECS}}` | `{DOCS_ROOT}/{config.docs.subdirectories.product_specs}` | `docs/product-specs` | Product requirements and acceptance criteria |

Resolution order: (1) operator `.autoharness/config.yaml` → (2) schema defaults. Docs path variables are computed paths (root + subdirectory name joined with `/`).

**Foundation and Conventions Variables** (derived from workspace profile `conventions` and synthesized language knowledge):

| Template Variable | Source | Example (Rust) | Example (TypeScript) | Example (Python) |
|---|---|---|---|---|
| `{{DATE}}` | Installation date (`YYYY-MM-DD`) | `2026-04-04` | `2026-04-04` | `2026-04-04` |
| `{{PROJECT_DESCRIPTION}}` | `harness_recommendations.project_description` or synthesized from README | `"A Rust REST API service"` | `"A React web application"` | `"A Python data pipeline"` |
| `{{PROJECT_STRUCTURE}}` | Synthesized directory tree from `structure.*` profile fields | _(directory tree block)_ | _(directory tree block)_ | _(directory tree block)_ |
| `{{CI_NOTES}}` | `ci.notes` or synthesized from `ci.platform` | `"Uses GitHub Actions with matrix builds"` | `"GitHub Actions + Nx affected"` | `"GitHub Actions + tox"` |
| `{{ADDITIONAL_STACK_ROWS}}` | Extra Markdown table rows for secondary tools (frameworks, DB, etc.) | _(0 or more rows)_ | _(0 or more rows)_ | _(0 or more rows)_ |
| `{{ADDITIONAL_COMMANDS}}` | Extra command entries for workspace-specific commands | _(0 or more lines)_ | _(0 or more lines)_ | _(0 or more lines)_ |
| `{{TEST_TIER_DESCRIPTION}}` | Synthesized from `test.*` profile fields | `"Unit: cargo test, Integration: cargo test --test"` | `"Unit: jest, E2E: playwright"` | `"Unit: pytest, Integration: pytest -m integration"` |
| `{{NAMING_CONVENTIONS}}` | Synthesized language naming rules | `"snake_case for variables, PascalCase for types"` | `"camelCase for variables, PascalCase for types"` | `"snake_case for everything"` |
| `{{DOCUMENTATION_CONVENTIONS}}` | Synthesized from language doc-comment style | `"/// doc comments on all public items"` | `"JSDoc on all exports"` | `"Google-style docstrings"` |
| `{{ERROR_HANDLING_CONVENTIONS}}` | Synthesized language error patterns | `"Result<T, E> for fallible operations"` | `"throw Error subclasses, catch at boundaries"` | `"raise specific Exception subclasses"` |
| `{{LINT_POLICY}}` | Synthesized from lint tool and profile strictness | `"All clippy warnings are hard errors"` | `"eslint --max-warnings 0"` | `"ruff check fails on any warning"` |
| `{{ERROR_HANDLING_POLICY}}` | Synthesized from `conventions.code_style` | `"All errors must be propagated via Result"` | `"Unhandled promise rejections are errors"` | `"All exceptions must be typed"` |
| `{{TEST_STRUCTURE}}` | Synthesized from `test.directory` and conventions | `"Unit tests in src/, integration tests in tests/"` | `"Unit tests in __tests__/, E2E in e2e/"` | `"Tests in tests/ directory"` |
| `{{COMMIT_SCOPES}}` | Derived from `structure.source_layout` top-level directories | `"api, cli, core, db"` | `"app, api, lib, ui"` | `"api, core, utils"` |
| `{{EXAMPLE_SCOPE}}` | First entry from `{{COMMIT_SCOPES}}` | `"api"` | `"app"` | `"api"` |

**Technology Instruction Variables** (language-knowledge-derived; synthesized per primary language):

| Template Variable | Source | Purpose |
|---|---|---|
| `{{LANGUAGE_FILE_GLOB}}` | Derived from `languages.primary` | File glob for language files (e.g., `**/*.rs`, `**/*.ts`, `**/*.py`) |
| `{{LANGUAGE_VERSION_DETAIL}}` | `languages.version` with edition/variant notes | Full version string (e.g., `Rust 2024 edition`, `TypeScript 5.4 strict`, `Python 3.12`) |
| `{{NAMING_RULES}}` | Synthesized language naming conventions | Bullet list of naming rules for the language |
| `{{CODE_ORGANIZATION_RULES}}` | Synthesized from language conventions | Module/package organization rules |
| `{{ERROR_HANDLING_RULES}}` | Synthesized from `{{ERROR_PATTERN}}` and language idioms | Error handling rules for the language |
| `{{SAFETY_RULES}}` | Synthesized from `{{UNSAFE_POLICY}}` and language safety model | Safety/correctness rules |
| `{{PERFORMANCE_RULES}}` | Synthesized from language performance idioms | Performance rules and anti-patterns |
| `{{TESTING_RULES}}` | Synthesized from `test.*` profile fields | Testing conventions and rules |
| `{{DOCUMENTATION_RULES}}` | Synthesized from `{{DOC_COMMENT_STYLE}}` | Documentation requirements |
| `{{DEPENDENCY_RULES}}` | Synthesized from build tool conventions | Dependency management rules |
| `{{ANTI_PATTERNS}}` | Synthesized language anti-patterns | Language-specific patterns to avoid |

**Review Persona Variables** (language-knowledge-derived; synthesized per primary language):

| Template Variable | Source | Purpose |
|---|---|---|
| `{{LANGUAGE_SAFETY_CHECKS}}` | Synthesized from language safety model | Bullet list of safety issues to check in code review |
| `{{LANGUAGE_IDIOM_CHECKS}}` | Synthesized from language idiomatic patterns | Bullet list of idiomatic pattern checks |
| `{{LANGUAGE_ERROR_HANDLING_CHECKS}}` | Synthesized from language error model | Bullet list of error handling review checks |
| `{{LANGUAGE_PERFORMANCE_CHECKS}}` | Synthesized from language performance model | Bullet list of performance review checks |
| `{{CONCURRENCY_PATTERNS}}` | Synthesized from language concurrency model | Comma-separated or bulleted concurrency patterns that trigger the concurrency reviewer |
| `{{FILE_EXT}}` | Derived from `languages.primary` | File extension (e.g., `rs`, `ts`, `py`, `go`) |
| `{{UNIMPLEMENTED_MARKER}}` | Derived from `languages.primary` | Language-specific stub marker (e.g., `unimplemented!()`, `throw new Error("Not implemented")`, `raise NotImplementedError`) |

**Config Write-Back Variables** (used only in `harness-config.yaml.tmpl` for the resolved config file):

| Template Variable | Source | Default | Description |
|---|---|---|---|
| `{{INSTALL_PRESET}}` | Selected preset from Step 1.3 | `standard` | Installation preset name |
| `{{PRIMARY_STACK_PACK}}` | Selected primary stack pack | `web-app` | Primary additive stack classification used during composition |
| `{{STACK_PACKS_YAML}}` | YAML list from selected stack packs | `["web-app", "deployable-service"]` | Rendered YAML array of additive stack packs |
| `{{INSTALL_LAYERS_YAML}}` | YAML list from resolved install layers | `["foundation", "instructions", "workflow", "review", "runtime", "backlog", "knowledge"]` | Rendered YAML array of explicit artifact-class layers |
| `{{CAPABILITY_PACKS_YAML}}` | YAML list from selected capability packs | `[]` | Rendered YAML array of enabled packs |
| `{{DOCS_COMPOUND_DIR}}` | `config.docs.subdirectories.compound` | `compound` | Subdirectory name only (not full path) |
| `{{DOCS_PLANS_DIR}}` | `config.docs.subdirectories.plans` | `plans` | Subdirectory name only |
| `{{DOCS_DECISIONS_DIR}}` | `config.docs.subdirectories.decisions` | `decisions` | Subdirectory name only |
| `{{DOCS_MEMORY_DIR}}` | `config.docs.subdirectories.memory` | `memory` | Subdirectory name only |
| `{{DOCS_CLOSURE_DIR}}` | `config.docs.subdirectories.closure` | `closure` | Subdirectory name only |
| `{{DOCS_DESIGN_DOCS_DIR}}` | `config.docs.subdirectories.design_docs` | `design-docs` | Subdirectory name only |
| `{{DOCS_PRODUCT_SPECS_DIR}}` | `config.docs.subdirectories.product_specs` | `product-specs` | Subdirectory name only |
| `{{CONTINUOUS_LEARNING_DIR}}` | `config.continuous_learning.directory` | `.autoharness/continuous-learning` | Repo-local directory for observation, instinct, and learned-artifact state |
| `{{CONTINUOUS_LEARNING_CAPTURE_HOOKS}}` | `config.continuous_learning.capture_hooks` | `false` | Whether environment-specific hook capture is enabled |
| `{{CONTINUOUS_LEARNING_ENVIRONMENT_ADAPTER}}` | `config.continuous_learning.environment_adapter` | `none` | Optional hook-capture adapter name |
| `{{CONTINUOUS_LEARNING_PROMOTION_THRESHOLD}}` | `config.continuous_learning.promotion_threshold` | `3` | Minimum corroborating observations before promotion to a learned artifact |
| `{{MODEL_ROUTING_TIER1}}` | `config.model_routing.tier1` | `gpt-5.4-mini` | Fast/cheap model identifier for memory, docs, compaction tasks |
| `{{MODEL_ROUTING_TIER2}}` | `config.model_routing.tier2` | `claude-sonnet-4.6` | Standard model identifier for orchestration, code writing, review |
| `{{MODEL_ROUTING_TIER3}}` | `config.model_routing.tier3` | `claude-opus-4.6` | Frontier model identifier for planning, architecture, analysis |
| `{{HARNESS_OVERRIDES_YAML}}` | `config.overrides` map | `{}` | Inline YAML map of explicit template variable overrides; `{}` when no overrides are set |

**AI Tools Variables** (used only in startup script generation):

| Template Variable | Source | Default | Description |
|---|---|---|---|
| `{{COPILOT_EXE_PATH}}` | `config.ai_tools.copilot_cli.exe_path` | `copilot` | Path to the Copilot CLI executable only (no arguments); resolved into `start.ps1` and `start.sh` |

Resolution order: (1) operator `.autoharness/config.yaml` `ai_tools.copilot_cli.exe_path` → (2) schema default `copilot` (expects it on PATH).
`exe_path` must be an executable path only. The generated scripts validate this at runtime.

**Capability-Pack Variables** (derived from `capability_packs` and integration signals in the profile):

| Template Variable | Source | Example (enabled) | Example (disabled) |
|---|---|---|---|
| `{{AGENT_INTERCOM_ENABLED}}` | `capability_packs` contains `agent-intercom` | `true` | `false` |
| `{{AGENT_INTERCOM_DETECTED}}` | `agent_intercom.detected` | `true` | `false` |
| `{{AGENT_INTERCOM_CONFIG_PATHS}}` | `agent_intercom.config_paths[]` | `.vscode/mcp.json, .intercom/settings.json` | empty |
| `{{AGENT_ENGRAM_ENABLED}}` | `capability_packs` contains `agent-engram` | `true` | `false` |
| `{{AGENT_ENGRAM_DETECTED}}` | `agent_engram.detected` | `true` | `false` |
| `{{AGENT_ENGRAM_CONFIG_PATHS}}` | `agent_engram.config_paths[]` | `.vscode/mcp.json, .engram/config.toml` | empty |
| `{{BROWSER_VERIFICATION_ENABLED}}` | `capability_packs` contains `browser-verification` | `true` | `false` |
| `{{CONTINUOUS_LEARNING_ENABLED}}` | `capability_packs` contains `continuous-learning` | `true` | `false` |
| `{{AGENT_NATIVE_REVIEWER_RECOMMENDED}}` | `agent_native.recommended_reviewer` | `true` | `false` |
| `{{AGENT_ADVERSARIAL_REVIEW_ENABLED}}` | `capability_packs` contains `adversarial-review` | `true` | `false` |

Note: These capability-pack and reviewer-selection variables are used internally by the installer during overlay composition. They drive conditional template selection and pack weaving logic. They are not emitted into installed artifact text — a capability pack's effects appear through the overlay content woven into templates, not through literal variable substitution.

#### Step 1.3: Select Preset, Primitive Set, and Capability Packs

Resolve the installation shape in this order:

1. If `primitives` input is provided, use it directly.
2. Otherwise, use the primitive set implied by `preset`.
3. If no preset is provided, default to `standard`.
4. Resolve `primary_stack_pack` from operator config first, then from the
   workspace profile.
5. Resolve additive `stack_packs` from operator config first, then from the
   workspace profile.
6. Resolve `capability_packs` from explicit input first, then operator config,
   then profile recommendations.
7. Resolve `install_layers` from operator config first; otherwise use
   `harness_recommendations.install_layers`; otherwise derive them from the
   selected preset and whether overlays are enabled.

Preset defaults:

| Preset | Default Primitives | Default Capability Packs | Best For |
|---|---|---|---|
| `starter` | 1, 2, 4, 5, 6, 8, 9 | none | First-time adoption, smaller repos |
| `standard` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | `continuous-learning`, `strict-safety`, `release-observability`, `adversarial-review` | Most repositories |
| `full` | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 | Standard packs plus `agent-intercom`, `agent-engram`, `backlogit`, `browser-verification` | Higher-operational-maturity teams |

If `capability_packs` input is provided explicitly, use it as-is regardless of preset. If `capability_packs` input is omitted: for `full`, install all standard packs (`continuous-learning`, `strict-safety`, `release-observability`, `adversarial-review`) plus `agent-intercom`, `agent-engram`, `backlogit`, and `browser-verification`; for `standard`, install `continuous-learning`, `strict-safety`, `release-observability`, and `adversarial-review`; for `starter`, apply no optional packs.

Additive stack packs are descriptive composition inputs rather than substitute
architectures. They capture multiple concurrent workspace shapes such as
`web-app`, `api-service`, `background-worker`, `deployable-service`,
`mcp-server`, `cli-tool`, or `library`.

Install-layer defaults:

| Preset | Default Install Layers |
|---|---|
| `starter` | `foundation`, `instructions`, `workflow`, `backlog`, `knowledge` |
| `standard` | `starter` layers + `review`, `runtime` |
| `full` | `standard` layers + `overlays` when recommended or explicitly selected packs are enabled |

Add the `overlays` layer whenever one or more capability packs are selected,
even if the chosen preset is `starter` or `standard`.

If `capability_packs` is non-empty but `install_layers` does not include
`overlays`, add `overlays` automatically and warn the operator. If
`install_layers` includes `overlays` but `capability_packs` is empty, warn the
operator that the overlays layer has no packs to weave.

Treat install layers as **explicit artifact-class composition**, not as a second
primitive system:

| Install Layer | Primary Artifact Classes |
|---|---|
| `foundation` | `AGENTS.md`, `copilot-instructions.md`, constitution |
| `instructions` | language instructions, workflow instructions, integration instructions |
| `workflow` | stage/ship/support agents, core skills, policies, prompts |
| `review` | review personas plus `review` / `plan-review` routing |
| `runtime` | runtime verification, operational closure, runtime-facing handoff guidance |
| `backlog` | backlog registry, backlog config, backlog integration guidance |
| `knowledge` | docs-root structure, compound/memory/closure/plans conventions |
| `overlays` | capability-pack-specific instructions plus woven overlay targets |

If operator-specified `install_layers` contradict the selected primitive set,
halt and ask for correction rather than silently producing an incoherent
composition.

Capability-pack overlays:

| Capability Pack | Overlay Behavior |
|---|---|
| `agent-intercom` | Installs `agent-intercom.instructions.md` and threads heartbeat, broadcast, approval-routing, and operator-wait expectations through foundation docs, pipeline agents, long-running skills, and the ping-loop prompt |
| `agent-engram` | Installs `agent-engram.instructions.md` and threads engram-first indexed search, workspace binding, freshness checks, and code-graph-driven analysis through foundation docs and analysis-heavy workflows |
| `backlogit` | Installs `backlogit.instructions.md` and threads backlogit-native query, queue, dependency, memory, checkpoint, comment, and commit-trace workflows through backlog-aware artifacts |
| `browser-verification` | Installs `browser-verification.instructions.md` and threads server readiness, route selection, headed/headless choice, and human-checkpoint handling through runtime verification and closure workflows |
| `continuous-learning` | Installs `continuous-learning.instructions.md` and `observe` / `learn` / `evolve` skills so recurring workflow practice can be captured, clustered, and promoted into explicit learned artifacts |
| `strict-safety` | Installs `strict-safety.instructions.md` and threads explicit `ProposedAction` / `ActionRisk` / `ActionResult` guidance through risky planning, safety, review, and closure workflows |
| `release-observability` | Installs `release-observability.instructions.md` and threads monitoring plan, pre-deploy audit, observation window, and rollback trigger expectations through operational closure and runtime verification workflows |
| `release-observability` | Deepens operational closure and post-release monitoring guidance |
| `adversarial-review` | Enables the standalone multi-model adversarial-review agent and review escalation path for higher-confidence consensus findings |

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
| Ready-work selection | ship agent and backlog-aware instructions |
| Agent continuity | stage and ship session continuity, foundation docs |
| Traceability | backlog-aware agents and instructions |

Example overlay target map for `agent-engram`:

| Overlay Element | Required Targets |
|---|---|
| Indexed search routing | foundation docs, `agent-engram.instructions.md`, research / planning / build workflows |
| Workspace binding and freshness | instructions plus workflows that depend on indexed results |
| Code-graph blast radius analysis | harness / build / repair workflows that inspect symbols and callers |

Example overlay target map for `browser-verification`:

| Overlay Element | Required Targets |
|---|---|
| Browser workflow rules | foundation docs, `browser-verification.instructions.md` |
| Verification discipline | `runtime-verification/SKILL.md`, closure-facing skills |
| Human checkpoints | runtime verification and closure artifacts that mention external flows |

Example overlay target map for `continuous-learning`:

| Overlay Element | Required Targets |
|---|---|
| Observation capture rules | foundation docs, `continuous-learning.instructions.md` |
| Observation lifecycle | `observe/SKILL.md`, `learn/SKILL.md`, `evolve/SKILL.md` |
| Learned-artifact promotion | tuning / maintenance guidance and explicit `learned-*` artifact pathways |

Example overlay target map for `strict-safety`:

| Overlay Element | Required Targets |
|---|---|
| Action contract | foundation docs, `strict-safety.instructions.md`, `safety-modes/SKILL.md` |
| Risky-plan legibility | `stage.agent.md`, `impl-plan/SKILL.md`, `plan-harden/SKILL.md`, `plan-review/SKILL.md` |
| Approval / rollback visibility | review, runtime-verification, and operational-closure workflows |

Example overlay target map for `release-observability`:

| Overlay Element | Required Targets |
|---|---|
| Monitoring plan discipline | foundation docs, `release-observability.instructions.md`, `operational-closure/SKILL.md` |
| Rollback trigger requirements | `operational-closure/SKILL.md`, `runtime-verification/SKILL.md` |
| Observation windows | closure-facing skills and PR lifecycle handoff sections |

Map primitives to template groups:

| Primitive | Template Groups |
|---|---|
| 1 - State & Context | `agents/stage` (session continuity), `agents/ship` (session continuity), `agents/research/learnings-researcher`, `skills/compact-context`, `skills/compound`, `skills/compound-refresh` |
| 2 - Task Granularity | Embedded in `foundation/AGENTS.md`, `agents/stage` |
| 3 - Model Routing | Embedded in `foundation/AGENTS.md`, all agent definitions |
| 4 - Orchestration | `agents/stage`, `agents/ship`, `skills/deliberate`, `skills/spike`, `skills/impl-plan`, `skills/plan-harden`, `skills/build-feature`, `skills/fix-ci`, `skills/harvest`, `skills/pr-lifecycle`, `skills/harness-architect` |
| 5 - Guardrails | `foundation/constitution`, `policies/workflow-policies`, `foundation/AGENTS.md`, `skills/safety-modes`, `skills/file-lock`, `instructions/circuit-breaker`, `instructions/concurrency`, optional `instructions/strict-safety` |
| 6 - Injection Points | `instructions/*`, `foundation/copilot-instructions`, `skills/skill-search` |
| 7 - Observability | `agents/review/*`, `skills/review`, `skills/plan-review` |
| 8 - Workflow Policy | `policies/workflow-policies` |
| 9 - Repo Knowledge | `foundation/AGENTS.md` (progressive disclosure), `instructions/architecture-doc` |
| 10 - Operational Closure | `skills/runtime-verification`, `skills/operational-closure`, PR and CI handoff sections in pipeline templates |

### Phase 2: Template Composition

#### Step 2.0: Resolve Layer Scope

Use `install_layers` as the explicit artifact-class composition contract for the
selected preset and overlays:

| Install Layer | Primary Phase 2 Targets |
|---|---|
| `foundation` | Step 2.1 |
| `instructions` | Step 2.2 |
| `workflow` | Step 2.4, Step 2.5, Step 2.6, Step 2.7 |
| `review` | Review personas plus `review` / `plan-review` routing in Step 2.4 and Step 2.5 |
| `runtime` | `runtime-verification`, `operational-closure`, and runtime-facing handoff text |
| `backlog` | Step 2.2 backlog integration plus Step 2.3 and Step 2.8 |
| `knowledge` | Docs-root conventions, compound/memory/closure/plans structure |
| `overlays` | Capability-pack instruction files and woven overlay target updates |

Stack packs influence why layers are present and which overlays are recommended,
but they do not replace the layer contract itself.

#### Step 2.1: Foundation Layer

Generate the constitutional foundation first, as all other artifacts reference it:

1. **Constitution** (`constitution.instructions.md`): Adapt principles for the target technology. Replace language-specific rules (e.g., `unsafe` code policy becomes TypeScript strict mode, Python type-hint enforcement, etc.). Preserve all 10 universal principles (I–X).

2. **AGENTS.md**: Generate the root AGENTS.md with technology-specific quality gates, code style conventions, error handling patterns, and terminal command policies.

3. **copilot-instructions.md**: Generate shared development guidelines with project structure, commands, and conventions.

If the `agent-intercom` capability pack is enabled, weave the intercom operating model into both files so heartbeat, milestone broadcasting, approval routing, and degraded-mode handling are part of the normal harness narrative.

If the `agent-engram` capability pack is enabled, weave the engram-first search operating model into both files so indexed lookup, workspace binding, and freshness / fallback behavior become part of the normal harness narrative.

If the `browser-verification` capability pack is enabled, weave browser
verification discipline into both files so server readiness, route selection,
headed/headless choice, and human-checkpoint expectations become part of the
normal harness narrative.

If the `continuous-learning` capability pack is enabled, weave recurring-practice
capture into both files so observation storage, evidence-backed instincts, and
promotion into explicit learned artifacts become part of the normal harness
narrative.

If the `strict-safety` capability pack is enabled, weave explicit risky-action
classification into both files so `ProposedAction`, `ActionRisk`, approval, and
`ActionResult` language becomes part of the normal harness narrative.

If the `release-observability` capability pack is enabled, weave monitoring plan,
pre-deploy audit, observation window, and rollback trigger expectations into both
files so structured release confidence becomes part of the normal harness narrative.

#### Step 2.2: Instruction Layer

Generate instruction files. These use `applyTo` patterns to scope their rules:

1. **Technology instructions** (`{language}.instructions.md`): Language-specific coding conventions, error handling, naming, documentation standards. Use the language-specific variant template when available (`technology-go.instructions.md.tmpl`, `technology-typescript.instructions.md.tmpl`, `technology-python.instructions.md.tmpl`, `technology-rust.instructions.md.tmpl`). Fall back to the generic `technology.instructions.md.tmpl` skeleton for languages without a variant.

2. **Universal instructions** (no technology adaptation needed):
   * `commit-message.instructions.md` — Adapt scopes to match workspace directory structure
   * `markdown.instructions.md` — Universal (install as-is with minimal adaptation)
   * `writing-style.instructions.md` — Universal (install as-is)
   * `git-merge.instructions.md` — Universal (install as-is)
   * `pull-request.instructions.md` — Universal (install as-is)
   * `prompt-builder.instructions.md` — Universal (install as-is)
   * `circuit-breaker.instructions.md` — Anti-spinning protocol with retry thresholds, escalation, and error logging. Universal (install as-is). Referenced by the constitution's Stop Conditions section.
   * `concurrency.instructions.md` — File operation locking protocol for multi-agent and human+agent concurrency control. Universal (install as-is). Requires the `file-lock` skill scripts to be installed alongside.
   * `architecture-doc.instructions.md` — Progressive disclosure and architecture documentation rules (Primitive 9)
   * `ci-security.instructions.md` — CI/CD security and hygiene conventions. Adapt `{{CI_WORKFLOW_GLOB}}` to match the workspace CI platform (e.g., `**/.github/workflows/*.yml` for GitHub Actions). Install when the workspace uses a CI system detected during discovery.
   * `workflows.instructions.md` — CI/CD workflow structural conventions (job naming, artifacts, caching, matrix, reusable workflows). Install alongside `ci-security.instructions.md` when a CI system is detected.
   * `github-pr-automation.instructions.md` — GitHub-specific PR automation: Copilot Review polling, review comment lifecycle (categorize, fix, reply, resolve threads via GraphQL), and CI check monitoring with back-off polling. Install when the workspace is hosted on GitHub (git remote contains `github.com` or `{{CI_PLATFORM}}` is `GitHub Actions`). Resolves `{{REPO_OWNER}}` and `{{REPO_NAME}}` from the git remote URL.
   * `mcp-server.instructions.md` — MCP server development conventions. Install when workspace-discovery detects an MCP server project (MCP SDK in dependencies). Resolves `{{MCP_SDK}}`, `{{MCP_TRANSPORT}}`, `{{MCP_PROJECT_STRUCTURE}}`.

3. **Backlog integration instructions** (`backlog-integration.instructions.md`): Generated from the backlog tool registry. Maps abstract operations to the specific tool's MCP names and CLI commands. Only generated when a backlog tool is detected or registered.

4. **Capability-pack instructions**: When `agent-intercom` is enabled, install `agent-intercom.instructions.md` and use it as the authoritative reference for heartbeat, remote approval, operator steering, and standby workflows.
   When `agent-engram` is enabled, install `agent-engram.instructions.md` and use it as the authoritative reference for engram-first search, workspace binding, index freshness, and indexed-search fallback workflows.
   When `backlogit` is enabled, install `backlogit.instructions.md` and use it as the authoritative reference for backlogit-native query, queue, dependency, memory, checkpoint, comment, and traceability workflows.
   When `browser-verification` is enabled, install `browser-verification.instructions.md` and use it as the authoritative reference for browser-ready server checks, route selection, headed/headless choice, and human checkpoints.
   When `continuous-learning` is enabled, install `continuous-learning.instructions.md` and use it as the authoritative reference for observation capture, instinct formation, and learned-artifact promotion.
   When `strict-safety` is enabled, install `strict-safety.instructions.md` and use it as the authoritative reference for `ProposedAction`, `ActionRisk`, `ActionResult`, approval routing, and risky-work legibility.
   When `release-observability` is enabled, install `release-observability.instructions.md` and use it as the authoritative reference for monitoring plans, pre-deploy audits, observation windows, and rollback trigger discipline.
   When `adversarial-review` is enabled, install `adversarial-review.instructions.md` and use it as the authoritative reference for multi-model dispatch, consensus assembly, confidence tiers, and remediation queue structure.

#### Step 2.3: Backlog Tool Registration

If the workspace profile includes a detected backlog tool (`backlog_tool.detected: true`):

If `tool_name` is `"manual"`: skip registry installation, generate minimal
backlog structure (queue/, archive/), skip backlog MCP tool registration in
agent definitions. Agents will use file-based backlog scanning only.

Otherwise:

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

Generate agent definitions. Each agent template has technology-specific sections that vary.

**Deprecated agent exclusion**: Do not install agent templates from
`{autoharness_home}/templates/agents/deprecated/`. If an existing workspace
contains deprecated agent files listed in AGENTS.md's deprecation table (during
merge install), flag them for removal.

1. **Pipeline agents**: stage, ship, harness-architect
   * Adapt build/test/lint commands throughout
   * Adapt quality gate sequences
    * Adapt model routing tiers (preserve structure, adjust agent assignments if needed)
    * When `agent-intercom` is enabled, add explicit workflow guidance for ping/heartbeat, broadcast milestones, approval routing, and operator clarification waits
    * When `agent-engram` is enabled, add explicit workflow guidance for engram-first search, workspace binding/index verification, and code-graph or impact-analysis style diagnostics
    * When `backlogit` is enabled, add explicit workflow guidance for queue-first work selection, dependency-aware planning, checkpoint persistence, and commit traceability
    * When `strict-safety` is enabled, keep risky planning and approval vocabulary visible through stage, review, verification, and closure handoffs
    * When `release-observability` is enabled, ensure operational-closure and runtime-verification carry monitoring plan, observation window, and rollback trigger expectations

2. **Support agents**: prompt-builder
   * Minimal technology adaptation needed
   * Adapt file path patterns for the workspace structure

3. **Expert agent**: Generate a technology-specific expert agent (equivalent to `rust-engineer.agent.md` but for the target language). Name it `{language}-engineer.agent.md`.

4. **Review personas**: Generate from review persona templates when the `review`
   layer is active
   * `architecture-strategist.agent.md` — Universal with domain adaptation
   * `constitution-reviewer.agent.md` — References local constitution
   * `scope-boundary-auditor.agent.md` — Universal
    * `technology-reviewer.agent.md` → `{language}-reviewer.agent.md` — Fully technology-specific
    * `concurrency-reviewer.agent.md` — Include only for languages with concurrency primitives
    * `agent-native-parity-reviewer.agent.md` — Include when `agent_native.recommended_reviewer` is true in the workspace profile
    * `learnings-researcher.agent.md` — Universal

5. **Orchestrating review skills**: `plan-review/SKILL.md`, `review/SKILL.md` — dispatch persona subagents during plan and code review at subagent depth 1. Install when the `review` layer is active. `adversarial-review.agent.md` is a standalone agent at depth 2 (dispatches multiple parallel reviewer instances).
   * Minimal technology adaptation needed
   * Install as skills (not agents)

#### Step 2.5: Skill Layer

Generate skill files:

1. **Technology-adapted skills**:
   * `build-feature/SKILL.md` — Adapt test runner commands, compilation checks, stall timeouts
   * `fix-ci/SKILL.md` — Adapt CI pipeline order, tool-specific fix strategies
   * `impl-plan/SKILL.md` — Adapt execution postures for the technology

2. **Universal skills** (minimal adaptation; install only when their governing primitives are selected):
    * `deliberate/SKILL.md`
    * `spike/SKILL.md`
    * `plan-harden/SKILL.md` — Install when Primitive 4 is selected so risky plans can be strengthened before review
    * `compact-context/SKILL.md`
    * `compound/SKILL.md`
   * `compound-refresh/SKILL.md` — Install when Primitive 1 is selected so the workspace can maintain stale or overlapping institutional learnings over time
   * `harness-architect/SKILL.md` — Install when Primitive 4 is selected. Adapts test patterns, failure markers, and file placement for `{{PRIMARY_LANGUAGE}}`
   * `harvest/SKILL.md` — Install when Primitive 4 is selected. Resolves backlog tool variables from the registry
   * `pr-lifecycle/SKILL.md` — Install when Primitive 4 is selected. Language-agnostic; uses `gh` CLI
   * `safety-modes/SKILL.md` — Install when Primitive 5 is selected
    * `file-lock/SKILL.md` — Install when Primitive 5 is selected. Provides `scripts/acquire_lock.ps1`, `scripts/acquire_lock.sh`, `scripts/release_lock.ps1`, and `scripts/release_lock.sh` for file-level concurrency control. Copy all scripts from `{autoharness_home}/templates/skills/file-lock/scripts/` into `{workspace_path}/scripts/`.
    * `skill-search/SKILL.md` — Install when Primitive 6 is selected. Provides `scripts/search.ps1` and `scripts/search.sh` for dynamic on-demand skill discovery. Copy all scripts from `{autoharness_home}/templates/skills/skill-search/scripts/` into `{workspace_path}/scripts/`.
    * `runtime-verification/SKILL.md` — Install when the `runtime` layer is active (normally because Primitive 10 is selected)
    * `operational-closure/SKILL.md` — Install when the `runtime` layer is active (normally because Primitive 10 is selected)
    * `observe/SKILL.md`, `learn/SKILL.md`, `evolve/SKILL.md` — Install when `continuous-learning` is enabled

When `agent-intercom` is enabled, weave operator visibility guidance into the long-running and gating skills rather than treating it as a separate isolated instruction.

When `agent-engram` is enabled, weave indexed-search guidance into research, planning, build, and repair skills rather than treating it as a generic footnote.

When `browser-verification` is enabled, weave browser-specific guidance into
runtime verification and operational closure rather than leaving browser work as
an implicit manual step.

When `continuous-learning` is enabled, install and reference the observation
lifecycle skills rather than relying on invisible prompt behavior.

When `strict-safety` is enabled, weave the action contract through `plan-harden`,
`safety-modes`, review, and closure skills rather than treating the pack as a
single isolated instruction file.

When `release-observability` is enabled, weave monitoring plan and rollback trigger
expectations through `runtime-verification` and `operational-closure` rather than
treating the pack as a standalone instruction file.

#### Step 2.6: Policy Layer

Generate the workflow policy registry from `workflow-policies.md.tmpl`:

* P-001 (Single-Release-Unit Completion) — Universal
* P-002 (TDD Gate) — Adapt test commands and red-phase detection
* P-003 (Decomposition Chain) — Universal
* P-004 (Red Phase Before Implementation) — Adapt compilation and test failure detection
* P-005 (Policy Violation Telemetry) — Universal
* P-006 (Plan Hardening Gate) — Universal

#### Step 2.7: Prompt Layer

Generate prompt files:

* `ping-loop.prompt.md` — Universal

#### Step 2.8: Backlog Structure

Initialize the backlog directory. Backlog tools are used **exclusively for workflow management** — active work items live in `queue/`, completed items move to `archive/`. Long-lived knowledge artifacts (compound learnings, plans, decisions, memory, closure records) are stored in `{{DOCS_ROOT}}/` at the workspace root, not in the backlog.

```text
{{BACKLOG_DIRECTORY}}/
  config.yml          # Backlog tool configuration (prefix map, statuses, labels)
  queue/              # Active work items — flat directory, no subdirectories
    .stash.md         # Parked ideas and deferred outcomes not yet promoted
  archive/            # Completed and archived work items
```

Work items in `queue/` follow the naming convention:

```text
{NNN}-{suffix}-{slug}.md               # Level 1 (features, chores, epics)
{NNN}.{NNN}-{suffix}-{slug}.md         # Level 2 (tasks, sub-epics)
{NNN}.{NNN}.{NNN}-{suffix}-{slug}.md   # Level 3 (subtasks)
```

The suffix map is configured in `config.yml` with concrete single or two-letter defaults:

| Type | Suffix | Example filename |
|---|---|---|
| Feature | `{{SUFFIX_FEATURE}}` | `001-F-user-auth.md` |
| Chore | `{{SUFFIX_CHORE}}` | `002-C-python-312-migration.md` |
| Task | `{{SUFFIX_TASK}}` | `001.001-T-add-login-endpoint.md` |
| Spike | `{{SUFFIX_SPIKE}}` | `002-S-evaluate-caching.md` |
| Deliberation | `{{SUFFIX_DELIBERATION}}` | `003-D-api-strategy.md` |
| Bug | `{{SUFFIX_BUG}}` | `004-B-null-pointer-fix.md` |
| Epic | `{{SUFFIX_EPIC}}` | `005-E-auth-overhaul.md` |
| Subtask | `{{SUFFIX_SUBTASK}}` | `001.001.001-ST-write-unit-test.md` |

Suffix values are resolved from: (1) operator `.autoharness/config.yaml` → (2) backlogit project YAML (when active) → (3) schema defaults (F, C, T, S, D, B, E, ST). The resolved values are written into both `config.yml` and `.autoharness/config.yaml` at installation time.

Long-lived knowledge structure (full paths at workspace root):

```text
{{DOCS_ROOT}}/          # Documentation root
{{DOCS_COMPOUND}}/      # Institutional learnings organized by category
{{DOCS_PLANS}}/         # Implementation plans (compacted: plan + reviews → decided-plan)
{{DOCS_DECISIONS}}/     # ADRs and deliberation outcomes
{{DOCS_MEMORY}}/        # Session state and checkpoints
{{DOCS_CLOSURE}}/       # Runtime verification, code review, safety-check, and closure records
```

Reviews are appended to the plan they review (not separate files). The compact-context skill consolidates plan + appended reviews into a decided-plan.

#### Step 2.9: Startup Scripts

Generate workspace-root startup scripts from `{autoharness_home}/templates/scripts/`:

1. **`start.ps1`** (from `start.ps1.tmpl`) — PowerShell startup script; sets `COPILOT_HOME` and other AI tool env vars to workspace-local directories, then launches the selected AI CLI tool.
2. **`start.sh`** (from `start.sh.tmpl`) — Bash equivalent. Set execute permission after install: `chmod +x start.sh`.

Both scripts redirect AI tool state to workspace-local hidden directories (`.copilot`, `.claude`, etc.) so that agent memories, checkpoints, and database files are git-visible and project-scoped rather than shared across all workspaces. Sections for GitHub Copilot CLI, Claude Code, and OpenAI Codex are included; only the relevant section is active — the others are commented out for reference.

Resolve `{{COPILOT_EXE_PATH}}`:
- From `config.ai_tools.copilot_cli.exe_path` if present in `.autoharness/config.yaml`
- Otherwise default to `copilot` (expects the executable on PATH)

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
| Scripts (when Primitive 5 or 6 selected) | `{workspace}/scripts/` — copy all `.ps1` and `.sh` files from `{autoharness_home}/templates/skills/{skill-name}/scripts/` for each skill that includes scripts (file-lock, skill-search) |
| Startup scripts | `{workspace}/start.ps1`, `{workspace}/start.sh` — generated from `{autoharness_home}/templates/scripts/start.ps1.tmpl` and `start.sh.tmpl`; always installed at workspace root regardless of preset |
| Policies | `{workspace}/.github/policies/` |
| Prompts | `{workspace}/.github/prompts/` |
| Backlog config + stash | `{workspace}/{{BACKLOG_DIRECTORY}}/` (queue/, archive/, config.yml, queue/.stash.md) |
| Knowledge directories | `{workspace}/` ({{DOCS_COMPOUND}}/, {{DOCS_PLANS}}/, {{DOCS_DECISIONS}}/, {{DOCS_MEMORY}}/, {{DOCS_CLOSURE}}/) |

#### Step 3.2b: Update .gitignore

If the `file-lock` skill is being installed (Primitive 5 selected), ensure the
workspace `.gitignore` contains entries for agent lock files:

1. If `.gitignore` does not exist, create it with:
   * `.*.lock`
   * `**/.*.lock`
2. If `.gitignore` exists but does not contain these dotfile lock patterns,
   append any missing entries:
   * `.*.lock`
   * `**/.*.lock`
3. Record this action in the manifest so the tuner can detect if it was removed

#### Step 3.2c: Write VS Code User Settings

When `vscode.detected` is true in the workspace profile, automatically apply the
autoharness agent discovery settings to the **VS Code user settings file** so
GitHub Copilot in VS Code can locate the autoharness agents and prompts from any
workspace without manual configuration.

> **User settings, not workspace settings.** autoharness is a global tool. The
> Auto-MergeInstall and Auto-Tune agents must be reachable from every
> workspace, not just the one they are being installed into. Write to user
> settings — never to the target workspace's `.vscode/settings.json`.

> **Resolved paths only — no tilde.** `~` is not expanded in VS Code JSON
> settings path keys on Windows. Always use the absolute path returned by
> `autoharness home`.

**Detect the user settings path from the platform:**

| Platform | User settings path |
|---|---|
| Windows | `%APPDATA%\Code\User\settings.json` (resolve `%APPDATA%`) |
| macOS | `$HOME/Library/Application Support/Code/User/settings.json` |
| Linux | `$HOME/.config/Code/User/settings.json` |

Platform is determined from the OS reported by the agent runtime. On Windows,
resolve `%APPDATA%` to its actual value (e.g. `C:\Users\alice\AppData\Roaming`).
Never use `~` in the resulting path string.

1. **Resolve the autoharness home path** — run `autoharness home` or use the
   already-resolved value from Step 1.0. This produces an absolute path with no
   tilde (e.g. `C:\Users\alice\AppData\Roaming\uv\tools\autoharness\Lib\site-packages\autoharness\data`).
2. **Detect the user settings path** from the platform as above
3. **Read the user settings file** if it exists; parse as JSONC (preserving
   existing content); if it does not exist, start with an empty object
4. **Merge autoharness discovery entries** without removing existing keys:
   * Add `"{autoharness_home}/.github/agents": true` under
     `chat.agentFilesLocations` (create the key if absent; merge into it if
     present, preserving any existing entries)
   * Add `"{autoharness_home}/.github/skills": true` under
     `chat.agentSkillsLocations` (same merge rule)
   * Add `"{autoharness_home}/.github/prompts": true` under
     `chat.promptFilesLocations` (same merge rule — makes `/install-harness`
     and `/tune-harness` available as slash commands from any workspace)
5. **Write the result back** to the user settings file as valid JSON (2-space
   indentation; existing keys and values are preserved, but JSONC comments and
   non-standard formatting are not round-tripped)
6. **Skip this step** silently if `vscode.has_agent_settings` is already true
   (the entries are already correct — avoid duplicating or overwriting)
7. **Record this action** in the manifest under a `vscode_settings` key so the
   tuner can detect if the entries were removed from user settings

When `vscode.detected` is false, skip this step entirely.

#### Step 3.3: Write Installation Manifest

Create `.autoharness/harness-manifest.yaml` recording install-time checksums that
the tuner can later re-hash for deterministic drift detection:

```yaml
schema_version: "1.0.0"
installed_at: "{{ISO_8601_TIMESTAMP}}"
autoharness_version: "1.0.0"
autoharness_home: "{{AUTOHARNESS_HOME}}"
profile_hash: "{{SHA256_OF_PROFILE}}"
config_hash: "{{SHA256_OF_CONFIG_OR_NULL}}"  # null if no .autoharness/config.yaml was present
install_preset: "{{PRESET}}"
primary_stack_pack: {{PRIMARY_STACK_PACK}}
stack_packs: [{{STACK_PACKS}}]
install_layers: [{{INSTALL_LAYERS}}]
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
vscode_settings:
  applied: true|false               # false when vscode.detected was false
  user_settings_path: "C:\\Users\\alice\\AppData\\Roaming\\Code\\User\\settings.json"  # resolved absolute path, no tilde
  entries_added:
    - "chat.agentFilesLocations[\"{{AUTOHARNESS_HOME}}/.github/agents\"]"
    - "chat.agentSkillsLocations[\"{{AUTOHARNESS_HOME}}/.github/skills\"]"
    - "chat.promptFilesLocations[\"{{AUTOHARNESS_HOME}}/.github/prompts\"]"
  skipped_because: null             # "already_present" when has_agent_settings was true
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

#### Step 3.4: Write Resolved Configuration

Write (or update) `.autoharness/config.yaml` using the `harness-config.yaml.tmpl` template with all resolved values. This records the actual configuration used during installation:

* If an operator config existed, preserve all operator-provided values and fill in defaults for omitted fields. When the installer discovers values that differ from the operator's explicit choices (e.g., new capability packs auto-detected), the operator's explicit values win — discovered values are recorded in a separate `_discovered` comment block for the tuner to surface later.
* If no operator config existed, write a complete config with all schema defaults and discovered values
* The resolved config serves as input for future `tune-harness` runs and enables the tuner to detect configuration drift

The installed config includes: `schema_version`, `preset`,
`primary_stack_pack`, `stack_packs`, `install_layers`, `capability_packs`,
`backlog` (tool, directory, suffix_map), `docs` (root, subdirectories),
`continuous_learning`, `model_routing`, and any `overrides` that were applied.

### Phase 4: Verification

#### Step 4.1: Template Variable Sweep

Scan every installed artifact for unresolved template variables:

1. Search all installed `.md` files for `{{` followed by `}}`
2. Exclude occurrences inside fenced code blocks (between ` ``` ` markers) that
   are intentional examples
3. For each match, record the file path, line number, and variable name
4. **FAIL** verification if any unresolved variables are found outside code fences

#### Step 4.2: Cross-Reference Sweep

Verify all installed artifacts are internally consistent:

1. **Agent → Skill references**: For each agent, verify every skill name
   mentioned in the agent body resolves to an installed
   `.github/skills/{name}/SKILL.md` file. Report missing skills.
2. **Agent → Tool references**: For each agent's `tools:` frontmatter field,
   verify referenced tools exist in the workspace or are standard environment
   tools. Report missing tools.
3. **Instruction → File references**: For each instruction file's `applyTo`
   glob pattern, verify the pattern matches at least one file in the workspace.
   Report orphaned patterns.
4. **Policy → Agent references**: For each policy in the registry, verify the
   `Applies To` agents were installed. Report dangling references.
5. **Constitution → Language consistency**: Verify the constitution's
   technology-specific rules reference the same language as the installed
   language instruction file.
6. **Layer → Artifact consistency**: Verify the recorded `install_layers` match
   the artifact classes actually installed:
   * `review` → review personas plus `review` / `plan-review` skills present
   * `runtime` → `runtime-verification` and `operational-closure` skills present
   * `overlays` → at least one pack-specific instruction file present
   * `knowledge` → docs-root directories exist

#### Step 4.3: Overlay Coherence Sweep

For each enabled capability pack:

1. Load the pack's declared overlay targets from the manifest
2. Verify each target artifact exists
3. For each target, verify the artifact contains at least one reference to the
   pack's core behavior keyword (e.g., `agent-intercom` → "heartbeat" or
   "broadcast"; `strict-safety` → "ProposedAction" or "ActionRisk";
   `release-observability` → "monitoring plan" or "rollback trigger")
4. **FAIL** verification if any target artifact is missing or lacks the
   expected behavior reference — this indicates a partially woven overlay

#### Step 4.4: Structural Validation

1. Validate YAML frontmatter in all installed `.md` files (parse as YAML;
   report syntax errors)
2. Verify all Markdown code fences are properly closed (matching ` ``` ` pairs)
3. Verify all Markdown tables have consistent column counts per table
4. Verify file paths in cross-references resolve to actual files

#### Step 4.5: Adversarial Verification

Invoke the **verify-harness** skill to run multi-model adversarial review of the
installed artifacts. This step is mandatory for `standard` and `full` presets and
may be skipped for `starter` or when `--skip-adversarial` is explicitly passed.

Pass:

* `autoharness_home`: The resolved autoharness installation path
* `workspace_path`: The target workspace path
* `manifest_path`: `{workspace_path}/.autoharness/harness-manifest.yaml`
* `auto_remediate`: true (apply HIGH-confidence fixes automatically)
* `scope`: `all`

The verify-harness skill dispatches three independent reviewer subagents — each
using a different model — to audit template fidelity, overlay coherence, and
cross-reference integrity. Findings are assembled into a confidence-weighted
consensus report. HIGH-confidence additive or corrective fixes are applied
automatically; destructive or ambiguous fixes are presented to the operator.

If adversarial verification returns **FAIL** (unresolved HIGH-confidence
CRITICAL/MAJOR findings), halt installation and present the findings. The
operator must resolve them before the installation is considered complete.

If adversarial verification returns **PASS WITH WARNINGS**, present the MEDIUM
findings as advisory and continue.

#### Step 4.6: Report

Present an installation summary:

```text
Harness Installation Complete
─────────────────────────────
Workspace: {{PROJECT_NAME}}
Language:  {{PRIMARY_LANGUAGE}}
Primary stack: {{PRIMARY_STACK_PACK_OR_NONE}}
Stack packs: {{STACK_PACKS_OR_NONE}}
Primitives installed: selected subset / 10
Preset: {{PRESET}}
Install layers: {{INSTALL_LAYERS_OR_NONE}}
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
