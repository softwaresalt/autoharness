---
description: "Multi-phase installation workflow that composes harness primitives from templates into a target workspace based on its discovered profile"
---

## Install Harness

Compose and install a complete agent harness into a target workspace. Uses the workspace profile from the workspace-discovery skill to customize universal templates for the target environment's specific technology stack, conventions, and workflow requirements.

autoharness operates as a globally-installed tool. Templates are read from the autoharness home directory; only generated harness artifacts are written to the target workspace. The target workspace never contains autoharness engine files — only the output artifacts it needs to function.

## When to Use

Invoke this skill after workspace-discovery has produced a profile, or let the Auto-MergeInstall agent invoke it automatically. The skill handles template selection, variable substitution, artifact generation, and installation verification.

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

Verify that `workspace_path` is NOT inside `autoharness_home` and vice versa. If `workspace_path` equals `autoharness_home` (same directory), do **not** halt immediately — flag for self-install evaluation and continue to load the workspace profile in Step 1.1 first. The self-install mode decision requires the profile and is evaluated in Step 1.1b.

All template reads in subsequent phases use `{autoharness_home}/templates/` as the base path. All artifact writes use `{workspace_path}` as the base path.

#### Step 1.0c: Enforce Branch Safety for Install Output

If `workspace_path` is a Git repository, determine the current branch and the
repository's default branch before producing any follow-up guidance that
mentions committing or pushing the generated install output.

* Never commit or push autoharness install output directly to the default
   branch (`main`, `master`, `trunk`, or the detected remote default branch).
* If the current branch is the default branch, explicitly recommend creating or
   switching to a feature branch first, for example
   `chore/autoharness-install-<date>`.
* Treat the intended Git workflow as: generate install output on a feature
   branch, review the diff, and open a pull request.
* If the operator declines to create or switch branches, installation may still
   proceed as local uncommitted changes, but do NOT commit or push those changes
   from this workflow.

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

#### Step 1.1b: Evaluate Self-Install Mode (if flagged)

If `workspace_path` equals `autoharness_home` (flagged in Step 1.0), check the now-loaded profile:

* If `distribution.is_global_tool` is `true`, enter self-install mode:
  1. **Agent routing**: Generate workflow agents (stage, ship) and write them to `distribution.local_agents_dir` (default `.github/local-agents`) instead of `.github/agents/`. Template agents, global skills, instructions, policies, and prompts continue to use their standard locations under `.github/`.
  2. **Wheel isolation check**: Verify that `distribution.local_agents_dir` is NOT referenced in `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` mappings (normalize path keys — check both with and without trailing `/`). If it is, halt and report the violation — workflow agents must not leak into the distribution package.
  3. **Operator confirmation required**: Before proceeding, display: "Self-install mode: target is the autoharness installation itself. Workflow agents will be placed in `{distribution.local_agents_dir}` to avoid wheel leakage. Confirm?" Do not proceed until the operator confirms.
  4. In self-install mode, workflow agent writes use `{workspace_path}/{distribution.local_agents_dir}` instead of `{workspace_path}/.github/agents/`.
* If `distribution.is_global_tool` is absent or `false`, halt and report: "Target workspace is the autoharness installation itself and is not configured as a globally-distributed tool. Select a different target workspace."

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
| `{{POLL_INTERVAL}}` | `ci.poll_interval` (seconds, optional) | `30` | `30` | `30` |
| `{{MAX_WAIT}}` | `ci.max_wait` (seconds, optional) | `600` | `600` | `600` |

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
| `{{OP_ARCHIVE_ITEM_MCP}}` | Registry `operations.archive_item.mcp_tool` | `backlogit_archive_item` | `task_archive` |
| `{{OP_CREATE_CLI}}` | Registry `operations.create_task.cli_command` | `backlogit add` | `backlog task create` |
| `{{OP_LIST_CLI}}` | Registry `operations.list_tasks.cli_command` | `backlogit list` | `backlog task list` |
| `{{OP_GET_CLI}}` | Registry `operations.get_task.cli_command` | `backlogit show {id}` | `backlog task view {id}` |
| `{{OP_UPDATE_CLI}}` | Registry `operations.update_task.cli_command` | `backlogit update {id}` | `backlog task edit {id}` |
| `{{OP_MOVE_CLI}}` | Registry `operations.move_task.cli_command` | `backlogit move {id} {status}` | `backlog task move {id}` |
| `{{OP_SEARCH_CLI}}` | Registry `operations.search_tasks.cli_command` | `backlogit search {query}` | `backlog task search` |
| `{{OP_COMPLETE_CLI}}` | Registry `operations.complete_task.cli_command` | `backlogit done {id}` | `backlog task complete {id}` |
| `{{OP_ARCHIVE_ITEM_CLI}}` | Registry `operations.archive_item.cli_command` | `backlogit archive {id}` | `backlog archive {id}` |

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
| `{{OP_SYNC_INDEX_MCP}}` | Registry `operations.sync_index.mcp_tool` | `backlogit_sync_index` | _(empty string)_ |
| `{{OP_SYNC_INDEX_CLI}}` | Registry `operations.sync_index.cli_command` | `backlogit sync` | _(empty string)_ |
| `{{OP_GET_SHIPMENT_MCP}}` | Registry `operations.get_shipment.mcp_tool` | `backlogit_get_shipment` | _(empty string)_ |
| `{{OP_LIST_SHIPMENTS_MCP}}` | Registry `operations.list_shipments.mcp_tool` | `backlogit_list_shipments` | _(empty string)_ |
| `{{OP_CLAIM_SHIPMENT_MCP}}` | Registry `operations.claim_shipment.mcp_tool` | `backlogit_claim_shipment` | _(empty string)_ |
| `{{OP_SHIP_SHIPMENT_MCP}}` | Registry `operations.ship_shipment.mcp_tool` | `backlogit_ship_shipment` | _(empty string)_ |
| `{{OP_ADD_TO_SHIPMENT_MCP}}` | Registry `operations.add_to_shipment.mcp_tool` | `backlogit_add_to_shipment` | _(empty string)_ |
| `{{OP_RETURN_BLOCKED_MCP}}` | Registry `operations.return_blocked.mcp_tool` | `backlogit_return_blocked` | _(empty string)_ |
| `{{OP_CREATE_CHECKPOINT_MCP}}` | Registry `operations.create_checkpoint.mcp_tool` | `backlogit_create_checkpoint` | _(empty string)_ |
| `{{OP_LIST_CHECKPOINTS_MCP}}` | Registry `operations.list_checkpoints.mcp_tool` | `backlogit_list_checkpoints` | _(empty string)_ |
| `{{OP_GET_CHECKPOINT_MCP}}` | Registry `operations.get_checkpoint.mcp_tool` | `backlogit_get_checkpoint` | _(empty string)_ |
| `{{OP_RESOLVE_CHECKPOINT_MCP}}` | Registry `operations.resolve_checkpoint.mcp_tool` | `backlogit_resolve_checkpoint` | _(empty string)_ |
| `{{OP_POLL_HOOK_EVENTS_MCP}}` | Registry `operations.poll_hook_events.mcp_tool` | `backlogit_poll_hook_events` | _(empty string)_ |
| `{{OP_ACK_HOOK_EVENTS_MCP}}` | Registry `operations.ack_hook_events.mcp_tool` | `backlogit_ack_hook_events` | _(empty string)_ |

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

**Security Surface Variables** (synthesized from workspace profile; used by security-audit skill, security-reviewer, security-lens-reviewer, and security-sentinel templates):

| Template Variable | Source | Default | Description |
|---|---|---|---|
| `{{AGENTIC_CONFIG_GLOB}}` | `agentic.config_paths` from workspace profile | `.github/**,.vscode/**` | Glob patterns for agentic config files scanned during security-audit Phase 2/3 |
| `{{SOURCE_GLOB}}` | `source.include_patterns` from workspace profile | `src/**` | Application source file glob for security-audit OWASP scan |
| `{{DOCS_SECURITY}}` | `config.docs.root` + `security` subdirectory | `docs/security` | Output directory for persisted security audit reports |
| `{{SECURITY_CONFIG_RULES}}` | Synthesized from detected agentic environment (Copilot CLI, VS Code, Claude Code, etc.) | See note | Per-environment config rule table for Tier 1 deterministic checks in security-audit Phase 2 |
| `{{SECURITY_OWASP_PATTERNS}}` | Synthesized from `languages.primary` | See note | Language-specific OWASP detection pattern set for security-audit Phase 4 |
| `{{SECURITY_SCAN_PATTERNS}}` | Synthesized from detected technology stack | See note | Full-stack security scan patterns used by security-sentinel for injection, auth, and exposure analysis |
| `{{SECURITY_REVIEW_PATTERNS}}` | Synthesized from `languages.primary` | See note | Language-specific file path and content signals that trigger the security-reviewer conditional persona |

Resolution notes for security surface variables:

* `{{SECURITY_CONFIG_RULES}}`: Derive from detected agentic environment. For GitHub Copilot CLI: check `.github/` for overly permissive allow-lists and missing input validation in instruction files. For VS Code: check `.vscode/settings.json` for terminal auto-approve patterns. Include rules common to all environments: hardcoded credentials, unpinned secrets, debug endpoints.
* `{{SECURITY_OWASP_PATTERNS}}`: Select from language knowledge. Python: SQLAlchemy raw queries, `eval()`, `pickle.loads()`, `subprocess.run(shell=True)`, f-string SQL. Go: `fmt.Sprintf` in SQL, `exec.Command` with user input. Rust: `unsafe` blocks, unchecked deserialization. TypeScript: `eval()`, `innerHTML`, unparameterized queries, `child_process.exec`. Adapt to the detected primary language.
* `{{SECURITY_SCAN_PATTERNS}}`: Combine language-specific OWASP patterns with framework-specific signals (e.g., Express middleware order, Django CSRF, FastAPI auth dependencies). Include auth middleware names, ORM patterns, and framework route decorators for the detected stack.
* `{{SECURITY_REVIEW_PATTERNS}}`: Bullet list of file path globs and content keywords that trigger security review. Example for Python: `auth*.py`, `permission*.py`, `middleware*.py`, `views.py`, `api.py`, pattern keywords `login`, `token`, `password`, `permission`, `role`, `secret`, `key`, `credential`. Adapt to detected stack.

**Browser & Experiment Variables** (used by browser-automation and iterative-experiment skill templates):

| Template Variable | Source | Default | Description |
|---|---|---|---|
| `{{BROWSER_CLI}}` | `config.browser.cli` or tool detection | `agent-browser` | Browser CLI tool invoked by the browser-automation skill |
| `{{BROWSER_HEADLESS_FLAG}}` | `config.browser.headless_flag` | `--headless` | Headless flag passed to `{{BROWSER_CLI}}` during automation runs |
| `{{EXPERIMENT_BRANCH_PREFIX}}` | `config.experiments.branch_prefix` | `experiment/` | Git branch prefix used by the iterative-experiment skill for experiment branches |
| `{{EXPERIMENT_RESULTS_DIR}}` | `config.experiments.results_dir` | `docs/experiments` | Directory for persisted iterative-experiment TSV logs; configurable, not a hardcoded path |

Resolution notes for browser and experiment variables:

* `{{BROWSER_CLI}}`: Override via `config.browser.cli` if set; otherwise detect from `runtime_surfaces.browser_tooling` in the workspace profile (e.g., Playwright, Puppeteer, agent-browser); falls back to the schema default `agent-browser`.
* `{{BROWSER_HEADLESS_FLAG}}`: Defaults to `--headless`, which is correct for `agent-browser` and most browser CLIs. CLIs with non-standard headless conventions (e.g., Playwright, which is headless by default and uses `--headed` to run with a visible browser) must set `config.browser.headless_flag` explicitly.
* `{{EXPERIMENT_BRANCH_PREFIX}}`: Must end with `/`. Validate at resolution time and append `/` if missing.
* `{{EXPERIMENT_RESULTS_DIR}}`: Must be a relative path within the workspace. Validate at resolution time.

**Guardrail Variables** (used by instruction templates):

| Template Variable | Source | Default | Description |
|---|---|---|---|
| `{{CIRCUIT_BREAKER_COOLDOWN}}` | `config.overrides.CIRCUIT_BREAKER_COOLDOWN` or resolved install defaults | `5 minutes` | Cooldown window used by the optional circuit-breaker auto-reset guidance before a single retry is allowed |

Resolution note for guardrail variables:

* `{{CIRCUIT_BREAKER_COOLDOWN}}`: Default to `5 minutes` unless the operator explicitly overrides it. Keep the value human-readable because it is rendered into instruction prose rather than parsed as machine configuration.

**Health-Check Variables** (used by the harness-doctor skill template):

| Template Variable | Source | Default | Description |
|---|---|---|---|
| `{{HARNESS_MANIFEST_PATH}}` | `config.harness.manifest_path` or schema default | `.autoharness/harness-manifest.yaml` | Path to the installed harness manifest; used by harness-doctor to locate the manifest for integrity and version checks |
| `{{AUTOHARNESS_VERSION}}` | `autoharness version` CLI when available, else `autoharness_home` package/plugin metadata (`pyproject.toml` / `src/autoharness/__init__.py` / plugin manifest) | _(resolved at install time)_ | The autoharness version that performed the install; written to the manifest's `autoharness_version` field. harness-doctor resolves the *current* version live and compares it against this recorded value to detect version drift |

Resolution notes for health-check variables:

* `{{HARNESS_MANIFEST_PATH}}`: Defaults to `.autoharness/harness-manifest.yaml` relative to the workspace root. Override via `config.harness.manifest_path` in the workspace config. Must be a relative path.
* `{{AUTOHARNESS_VERSION}}`: Resolve at install time to the **concrete** version of the autoharness distribution performing the install, using the first available source: (1) the `autoharness version` CLI (pip and editable installs); (2) `autoharness_home` package metadata — `autoharness_home/pyproject.toml` (`[project].version`) or `autoharness_home/src/autoharness/__init__.py` (`__version__`), present in source/clone checkouts even though the released wheel data directory omits them; (3) for plugin installs with no Python CLI, the plugin/package manifest version that `autoharness_home` was resolved from. The install MUST resolve one of these to a concrete version and MUST never write a literal `{{AUTOHARNESS_VERSION}}` to the manifest — Step 4.1 fails the install if it does.

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
| `{{MODEL_ROUTING_TIER1}}` | `config.model_routing.tier1.model` (object form) or `config.model_routing.tier1` (legacy string) | `gpt-5.4-mini` | Fast/cheap model identifier for memory, docs, compaction tasks. When `tier1` is a plain string, that string is used as the model value and all other tier sub-fields default to empty. |
| `{{MODEL_ROUTING_TIER2}}` | `config.model_routing.tier2.model` (object form) or `config.model_routing.tier2` (legacy string) | `claude-sonnet-4.6` | Standard model identifier for orchestration, code writing, review. Same string-fallback rule as TIER1. |
| `{{MODEL_ROUTING_TIER3}}` | `config.model_routing.tier3.model` (object form) or `config.model_routing.tier3` (legacy string) | `claude-opus-4.6` | Frontier model identifier for planning, architecture, analysis. Same string-fallback rule as TIER1. |
| `{{TIER_1_REASONING_EFFORT}}` | `config.model_routing.tier1.reasoning_effort` | _(empty)_ | Reasoning effort for Tier 1 agents; leave empty to use model default |
| `{{TIER_1_PROVIDER}}` | `config.model_routing.tier1.model_provider` | _(empty)_ | Model provider for Tier 1 agents (e.g., `openai`, `anthropic`) |
| `{{TIER_1_FAMILY}}` | `config.model_routing.tier1.model_family` | `gpt-5.4-mini` | Model family shorthand resolved into Tier 1 agent frontmatter |
| `{{TIER_2_REASONING_EFFORT}}` | `config.model_routing.tier2.reasoning_effort` | _(empty)_ | Reasoning effort for Tier 2 agents; leave empty to use model default |
| `{{TIER_2_PROVIDER}}` | `config.model_routing.tier2.model_provider` | _(empty)_ | Model provider for Tier 2 agents (e.g., `openai`, `anthropic`) |
| `{{TIER_2_FAMILY}}` | `config.model_routing.tier2.model_family` | `claude-sonnet-4.6` | Model family shorthand resolved into Tier 2 agent frontmatter |
| `{{TIER_3_REASONING_EFFORT}}` | `config.model_routing.tier3.reasoning_effort` | _(empty)_ | Reasoning effort for Tier 3 agents; leave empty to use model default |
| `{{TIER_3_PROVIDER}}` | `config.model_routing.tier3.model_provider` | _(empty)_ | Model provider for Tier 3 agents (e.g., `openai`, `anthropic`) |
| `{{TIER_3_FAMILY}}` | `config.model_routing.tier3.model_family` | `claude-opus-4.6` | Model family shorthand resolved into Tier 3 agent frontmatter |
| `{{ORCHESTRATOR_REASONING_EFFORT}}` | `config.model_routing.orchestrator.reasoning_effort` (object form), fallback `{{TIER_2_REASONING_EFFORT}}` | _(empty)_ | Reasoning effort for the Orchestrator; falls back to Tier 2 default |
| `{{ORCHESTRATOR_PROVIDER}}` | `config.model_routing.orchestrator.model_provider` (object form), fallback `{{TIER_2_PROVIDER}}` | _(empty)_ | Model provider for the Orchestrator; falls back to Tier 2 default |
| `{{ORCHESTRATOR_FAMILY}}` | `config.model_routing.orchestrator.model_family` (object form) or `config.model_routing.orchestrator` (string form), fallback `gpt-5.4` | `gpt-5.4` | Model family for the Orchestrator; defaults to `gpt-5.4` when unset (does NOT fall back to tier2 — the orchestrator has its own default) |

When `config.model_routing.orchestrator` is a plain string (e.g., `orchestrator: "gpt-5.4"`), it is treated as the `model_family` value. The `reasoning_effort` and `model_provider` fields fall back to their tier2 equivalents. When it is an object, each field resolves independently.
| `{{BROWSER_CLI}}` | `config.browser.cli` | `agent-browser` | Written back into `config.browser.cli` in the resolved harness-config.yaml |
| `{{BROWSER_HEADLESS_FLAG}}` | `config.browser.headless_flag` | `--headless` | Written back into `config.browser.headless_flag` |
| `{{EXPERIMENT_BRANCH_PREFIX}}` | `config.experiments.branch_prefix` | `experiment/` | Written back into `config.experiments.branch_prefix` (normalized to end with `/`) |
| `{{EXPERIMENT_RESULTS_DIR}}` | `config.experiments.results_dir` | `docs/experiments` | Written back into `config.experiments.results_dir` (must be a relative workspace path) |
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
| `{{AGENT_INTERCOM_CONFIG_PATHS}}` | `agent_intercom.config_paths[]` | `.mcp.json, .intercom/settings.json` | empty |
| `{{AGENT_ENGRAM_ENABLED}}` | `capability_packs` contains `agent-engram` | `true` | `false` |
| `{{AGENT_ENGRAM_DETECTED}}` | `agent_engram.detected` | `true` | `false` |
| `{{AGENT_ENGRAM_CONFIG_PATHS}}` | `agent_engram.config_paths[]` | `.mcp.json, .engram/config.toml` | empty |
| `{{BROWSER_VERIFICATION_ENABLED}}` | `capability_packs` contains `browser-verification` | `true` | `false` |
| `{{CONTINUOUS_LEARNING_ENABLED}}` | `capability_packs` contains `continuous-learning` | `true` | `false` |
| `{{AGENT_NATIVE_REVIEWER_RECOMMENDED}}` | `agent_native.recommended_reviewer` | `true` | `false` |
| `{{AGENT_ADVERSARIAL_REVIEW_ENABLED}}` | `capability_packs` contains `adversarial-review` | `true` | `false` |
| `{{GRAPHTOR_DOCS_ENABLED}}` | `capability_packs` contains `graphtor-docs` | `true` | `false` |
| `{{GRAPHTOR_DOCS_DETECTED}}` | `graphtor_docs.detected` | `true` | `false` |
| `{{GRAPHTOR_SOURCES_PATH}}` | `graphtor_docs.sources_path` or operator `graphtor_docs.sources_path` | `.graphtor/config/sources.yaml` | `.graphtor/config/sources.yaml` |
| `{{GRAPHTOR_BINARY_PATH}}` | binary path from `graphtor_docs` detection or operator `graphtor_docs.binary_path` | `.graphtor/bin/graphtor-docs` | `.graphtor/bin/graphtor-docs` |

Note: These capability-pack and reviewer-selection variables are used internally by the installer during overlay composition. They drive conditional template selection and pack weaving logic. They are not emitted into installed artifact text — a capability pack's effects appear through the overlay content woven into templates, not through literal variable substitution.

**Runtime validator profile inputs** (consumed structurally — not emitted as literal template variables):

| Profile Path | Primary Consumers | Purpose |
|---|---|---|
| `runtime_validation.validator_manifest` | `.ship.agent.md`, `runtime-verification/SKILL.md` | Surface adapters, probe hints, and manual checkpoints for the runtime validator |
| `runtime_validation.validation_expectations` | `.ship.agent.md`, `runtime-verification/SKILL.md` | Expected surfaces, minimum verdict, invariants, and explicit release blockers |
| `runtime_validation.releasability` | `operational-closure/SKILL.md`, `release-observability.instructions.md` | Required releasability evidence such as monitoring, rollback, owner, and validation-window expectations |

**Alternate Model Variables** (used by `adversarial-review` and `doc-review` templates when alternate provider support is enabled):

| Template Variable | Source | Example (Gemini) | Example (none) |
|---|---|---|---|
| `{{ALT_REVIEW_PROVIDER}}` | `config.model_routing.alt_review.model_provider` or operator override | `google` | _(empty string)_ |
| `{{ALT_REVIEW_FAMILY}}` | `config.model_routing.alt_review.model_family` or operator override | `gemini-2.5-flash` | _(empty string)_ |
| `{{ALT_DOC_REVIEW_PROVIDER}}` | `config.model_routing.alt_doc_review.model_provider` or operator override | `google` | _(empty string)_ |
| `{{ALT_DOC_REVIEW_FAMILY}}` | `config.model_routing.alt_doc_review.model_family` or operator override | `gemini-2.5-pro` | _(empty string)_ |

Resolution notes for alternate model variables:

* When both `*_PROVIDER` and `*_FAMILY` are non-empty, the corresponding skill or agent routes one reviewer/review slot to the alternate provider. When either is empty, standard tier routing applies.
* `{{ALT_REVIEW_PROVIDER}}` / `{{ALT_REVIEW_FAMILY}}` replace Reviewer-B (Tier 2 slot) in the adversarial-review agent's reviewer pool. This ensures cross-provider diversity without requiring additional reviewer count.
* `{{ALT_DOC_REVIEW_PROVIDER}}` / `{{ALT_DOC_REVIEW_FAMILY}}` determine the model used for the entire doc-review skill pass. When empty, doc-review uses Tier 2.
* These variables resolve to the empty string when the operator has not configured an alternate model. Templates that reference them must degrade gracefully to Tier 2 defaults when the variables are empty.

**Community template variables** — used by templates in `templates/community/` when selected during Step 1.3a:

| Variable | Resolved From | Example (Rust) | Example (Go) | Example (Python) |
|---|---|---|---|---|
| `{{ADR_DIRECTORY}}` | operator `community.adr_directory` or default | `docs/adrs` | `docs/adrs` | `docs/adrs` |
| `{{REVIEW_LANGUAGE}}` | operator `community.review_language` or default `English` | `English` | `English` | `English` |
| `{{CODEBASE_DOCS_DIRECTORY}}` | operator `community.codebase_docs_directory` or default `docs/codebase` | `docs/codebase` | `docs/codebase` | `docs/codebase` |
| `{{PLANS_DIRECTORY}}` | operator `community.plans_directory` or default `docs/plans` | `docs/plans` | `docs/plans` | `docs/plans` |
| `{{TEST_COMMAND}}` | `test.command` from workspace profile or operator override | `cargo test` | `go test ./...` | `pytest` |
| `{{COMMIT_PREFIX}}` | operator `community.commit_prefix` or default `feat` | `feat` | `feat` | `feat` |
| `{{CHANGELOG_STYLE_FILE}}` | operator `community.changelog_style_file` or default `CHANGELOG_STYLE.md` | `CHANGELOG_STYLE.md` | `CHANGELOG_STYLE.md` | `CHANGELOG_STYLE.md` |
| `{{CHANGELOG_FILE}}` | operator `community.changelog_file` or default `CHANGELOG.md` | `CHANGELOG.md` | `CHANGELOG.md` | `CHANGELOG.md` |

Note: Community template variables are resolved only when the operator selects the corresponding community template during Step 1.3a. They are not resolved for templates that are not selected.

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
| `agent-intercom` | Installs `agent-intercom.instructions.md` and threads heartbeat, broadcast, approval-routing, and operator-wait expectations through foundation docs, pipeline agents, review / verification / closure workflows, long-running skills, and the ping-loop prompt |
| `agent-engram` | Installs `agent-engram.instructions.md` and threads engram-first indexed search, workspace binding, freshness checks, and code-graph-driven analysis through foundation docs and analysis-heavy workflows |
| `backlogit` | Installs `backlogit.instructions.md`, `backlogit-sql-schema.instructions.md`, and `backlogit-yaml-header-tooling.instructions.md`, and threads backlogit-native query, queue, dependency, memory, checkpoint, comment, commit-trace, and source-artifact-cleanup workflows through backlog-aware artifacts |
| `browser-verification` | Installs `browser-verification.instructions.md` and threads server readiness, route selection, headed/headless choice, and human-checkpoint handling through runtime verification and closure workflows |
| `continuous-learning` | Installs `continuous-learning.instructions.md` and `observe` / `learn` / `evolve` skills so recurring workflow practice can be captured, clustered, and promoted into explicit learned artifacts |
| `strict-safety` | Installs `strict-safety.instructions.md` and threads explicit `ProposedAction` / `ActionRisk` / `ActionResult` guidance through risky planning, safety, review, and closure workflows |
| `release-observability` | Installs `release-observability.instructions.md` and threads monitoring plan, pre-deploy audit, observation window, and rollback trigger expectations through operational closure and runtime verification workflows |
| `adversarial-review` | Enables the standalone multi-model adversarial-review agent and review escalation path for higher-confidence consensus findings |
| `graphtor-docs` | Installs `graphtor-docs.instructions.md` and threads indexed local documentation retrieval — keyword search, semantic search, topic research, doc-graph traversal — through research, planning, and knowledge-retrieval workflows so agents resolve domain concepts and APIs from indexed sources before falling back to broad web or filesystem search |

#### Step 1.3a: Community Template Selection

After resolving the installation shape and before applying capability-pack
overlays, evaluate community templates from the autoharness registry:

1. Read `templates/community/registry.yaml` from `autoharness_home`.
   If the file does not exist or `templates` is empty, skip this step.
2. For each registry entry, evaluate `applicable_profiles` against the
   workspace profile's detected languages, frameworks, and stack packs:
   * An entry with `"any"` in `applicable_profiles` matches all workspaces.
   * An entry listing specific profiles (e.g., `"python"`, `"web-app"`)
     matches when the workspace profile's languages, frameworks, or stack
     packs include at least one of those values.
3. Check `prerequisite_packs` — only propose entries whose prerequisites
   are a subset of the selected `capability_packs`. If `prerequisite_packs`
   is empty, the entry has no pack prerequisites.
4. Produce a ranked list of applicable community templates. Rank by:
   * Number of matching profile tags (more matches = higher rank)
   * Number of `primitives_deepened` that overlap with `primitives_installed`
5. Present the ranked list to the operator for **opt-in selection**.
   Community templates are **never auto-installed**. The operator may
   select all, some, or none.
6. For each selected template:
   * Read the `.tmpl` file from `autoharness_home` at the entry's
     `template_path`.
   * Resolve `{{VARIABLE}}` placeholders using the same variable resolution
     table as first-party templates. If the template introduces new
     variables (listed in `variables_introduced`), prompt the operator for
     values or use defaults from the workspace profile.
   * Place the resolved artifact in the target workspace following the same
     artifact-class placement rules as first-party templates (agents →
     `.github/agents/`, instructions → `.github/instructions/`, skills →
     `.github/skills/`, prompts → `.github/prompts/`).
7. Record selected community templates in the harness manifest under
   `community_templates[]` with both `installed_checksum` (SHA-256 of the
   resolved installed artifact) and `source_checksum` (SHA-256 of the source
   `.tmpl` file at install time). This dual-checksum design enables the tuner
   to distinguish local modifications from upstream template updates. See
   schema at `schemas/harness-manifest.schema.json`.

Community templates are part of the `overlays` install layer. If any
community templates are selected and `install_layers` does not already
include `overlays`, add it automatically.

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
| Schema and tooling reference | backlogit-specific instruction files plus backlog-aware workflows that inspect SQL, frontmatter, or `custom_fields` |
| Source artifact cleanup | `.ship.agent.md`, `operational-closure/SKILL.md`, and closure-facing traceability guidance |

Example overlay target map for `agent-engram`:

| Overlay Element | Required Targets |
|---|---|
| Indexed search routing | foundation docs, `agent-engram.instructions.md`, research / planning / build workflows |
| Workspace binding and freshness | instructions plus workflows that depend on indexed results |
| Code-graph blast radius analysis | harness / build / repair workflows that inspect symbols and callers |

#### Formal Overlay Contract: `agent-engram`

**Eligibility signals** (when to recommend agent-engram):
* `.mcp.json` (root, canonical shared config) references `engram` server or known engram tool names
* legacy editor-local MCP settings still reference Engram tool names (compatibility fallback only)
* `.engram/config.toml`, `.engram/registry.yaml`, or `.engram/code-graph/` present at workspace root
* `AGENTS.md` or `.github/copilot-instructions.md` contains `<!-- engram:start -->` marker or Engram tool names

**Recommendation logic**: Recommend when `agent_engram.mcp_configured: true` OR `agent_engram.detected: true` in the workspace profile.

**Overlay targets**:
* `foundation-docs` — AGENTS.md, copilot-instructions.md (engram:start/end block)
* `agent-engram.instructions.md` — primary instruction file installed at `.github/instructions/`
* `pipeline-agents` — .stage.agent.md, .ship.agent.md: session-start daemon check, pre-planning search, pre-build impact analysis
* `analysis-heavy-workflows` — research/planning/build skills: add `unified_search` / `impact_analysis` guidance

**Behavior deltas**:
* Session start: call `get_workspace_status` to verify daemon readiness and workspace binding; log `ENGRAM_OK` or `ENGRAM_DEGRADED`
* Before planning: run `unified_search` or `impact_analysis` to assess blast radius before invoking impl-plan
* Before build: run `impact_analysis` on the task's primary symbol/file scope before beginning code changes
* Fallback: `ENGRAM_DEGRADED` mode — use file-based tools (grep, glob, view); do not halt session

**Verification checks** (installation-time):
* `agent-engram.instructions.md` installed at `.github/instructions/` with valid YAML frontmatter
* `.stage.agent.md` contains Engram session-start check (`get_workspace_status`) and pre-planning search step
* `.ship.agent.md` contains Engram session-start check (`get_workspace_status`) and pre-build impact-analysis step
* `copilot-instructions.md` engram block cross-references installed instructions (`agent-engram.instructions.md`)
* No unresolved `{{VARIABLE}}` in `agent-engram.instructions.md` (template has none — direct copy)

**Tuning drift checks**:
* `agent-engram.instructions.md` checksum vs. template checksum in harness-manifest
* .stage.agent.md and .ship.agent.md contain `get_workspace_status` reference (text search)
* copilot-instructions.md contains `engram:start` / `engram:end` markers (text search)

#### Formal Overlay Contract: `agent-intercom`

**Eligibility signals** (when to recommend agent-intercom):
* `.mcp.json` (root, canonical shared config) references `agent-intercom`, `intercom`, or known intercom tool names (`ping`, `broadcast`, `standby`, `transmit`)
* legacy editor-local MCP settings still reference intercom tool names (compatibility fallback only)
* `AGENTS.md` or agent files contain intercom tool names or `<!-- intercom:start -->` marker

**Recommendation logic**: Recommend when `agent_intercom.mcp_configured: true` OR `agent_intercom.detected: true` in the workspace profile.

**Overlay targets**:
* `agent-intercom.instructions.md` — primary instruction file installed at `.github/instructions/`
* `pipeline-agents` — .stage.agent.md, .ship.agent.md: startup heartbeat, phase broadcasts, approval routing, operator-choice broadcasts
* `destructive-action-workflows` — anywhere the harness gates destructive operations (file deletion, directory removal)
* `operator-choice-surfaces` — stash triage, plan review, shipment assembly (self-contained broadcast with backlogit item details)

**Behavior deltas**:
* Session start: heartbeat/ping with concise status message; log `INTERCOM_OK` or `INTERCOM_DEGRADED`
* Before operator-facing choices: self-contained broadcast with item ID, priority, type, one-line summary, ordering rationale, and explicit wait-for-confirmation statement
* Before destructive ops: auto-check → request clearance if not auto-approved; block if intercom unavailable
* Phase transitions: broadcast at planning started, build started, task claimed, task completed, review complete, runtime verification, operational closure
* Fallback: `INTERCOM_DEGRADED` — non-destructive work continues; approval-dependent ops blocked until restored

**Combined backlogit+intercom operator-presentation rule**: When both `agent-intercom` and `backlogit` packs are active, operator-facing backlog presentation (stash triage choices, queue items, plan review options) must be broadcast as a self-contained message: include item ID, priority, type, one-line summary, recommended ordering or shortlist rationale, and an explicit statement that operator confirmation is awaited. The operator may be reading remotely and cannot recover context from the chat transcript.

**Verification checks** (installation-time):
* `agent-intercom.instructions.md` installed at `.github/instructions/` with valid YAML frontmatter
* .stage.agent.md contains heartbeat/ping call and `INTERCOM_DEGRADED` reference
* .ship.agent.md contains heartbeat/ping call and `INTERCOM_DEGRADED` reference
* No unresolved `{{VARIABLE}}` in `agent-intercom.instructions.md` (template has none — direct copy)

**Tuning drift checks**:
* `agent-intercom.instructions.md` checksum vs. template checksum in harness-manifest
* .stage.agent.md and .ship.agent.md contain `INTERCOM_DEGRADED` reference (text search)
* MCP config path in manifest should normally resolve to `.mcp.json`; legacy editor-local config paths may still appear when tuning older workspaces

#### Formal Overlay Contract: `graphtor-docs`

**Eligibility signals** (when to recommend graphtor-docs):
* `.mcp.json` (root, canonical shared config) references `graphtor` or `graphtor-docs` server
* legacy editor-local MCP settings still reference graphtor-docs tool names (compatibility fallback only)
* `.graphtor/` directory present at workspace root, OR `.graphtor/config/sources.yaml` or `.graphtor/config/` exists
* `AGENTS.md` or agent files reference graphtor-docs tool names (`search_local_docs`, `search_semantic`, `research_topic`, `get_status`)
* `graphtor-docs` binary present on PATH or at `.graphtor/bin/`

**Recommendation logic**: Recommend when `graphtor_docs.mcp_configured: true` OR `graphtor_docs.detected: true` in the workspace profile.

**Overlay targets**:
* `graphtor-docs.instructions.md` — primary instruction file (two template variables require discovery-first resolution)
* `pipeline-agents` — .stage.agent.md, .ship.agent.md: session-start server check, pre-planning doc research, pre-build doc search, multi-pack routing note
* `research-skills` — any research or learnings-retrieval skill: prefer graphtor-docs for doc lookup over broad grep
* `workspace-profile` — requires `graphtor_docs` section with `sources_path` and `binary_path` (string|null)

**Behavior deltas**:
* Session start: `get_status` check once per session — log `GRAPHTOR_OK` or `GRAPHTOR_UNAVAILABLE`
* Before planning: `research_topic` or `search_local_docs` before impl-plan for domain concepts and API references
* Before build: `search_local_docs` or `search_semantic` for documentation questions
* Routing split when Engram is also active: Engram handles code relationships, impact analysis, and git history; graphtor-docs handles documentation lookup, API references, and concept research
* Fallback: `GRAPHTOR_UNAVAILABLE` — grep/view over `docs/` directory; do not halt session

**Variable resolution for `graphtor-docs.instructions.md`**:

This is the only pack in the current instruction set that produces a workspace-specific installed file — both template variables require discovery before rendering:

| Variable | Resolution Order | Example |
|---|---|---|
| `{{GRAPHTOR_SOURCES_PATH}}` | 1. Check `.graphtor/config/sources.yaml`; 2. Check `.graphtor/sources.yaml`; 3. Default: `.graphtor/config/sources.yaml` | `.graphtor/config/sources.yaml` |
| `{{GRAPHTOR_BINARY_PATH}}` | 1. `graphtor` on PATH (`which graphtor`); 2. `.graphtor/bin/graphtor-docs.exe` or `.graphtor/bin/graphtor-docs`; 3. Default: `graphtor` (assumes PATH) | `.graphtor/bin/graphtor-docs.exe` |

After resolution, verify no `{{...}}` remain in the rendered file before recording the artifact checksum.

**Verification checks** (installation-time):
* `graphtor-docs.instructions.md` installed at `.github/instructions/` with valid YAML frontmatter
* Zero `{{VARIABLE}}` placeholders in installed file (both `GRAPHTOR_SOURCES_PATH` and `GRAPHTOR_BINARY_PATH` must be resolved)
* .stage.agent.md and .ship.agent.md contain `GRAPHTOR_UNAVAILABLE` reference
* workspace-profile.yaml has `graphtor_docs` section with `sources_path` and `binary_path` (string|null)

**Tuning drift checks**:
* `graphtor-docs.instructions.md` checksum comparison: note that because template variables are resolved at install time, the installed checksum is workspace-specific — the tuner should compare the rendered content against a fresh render from the template (re-resolving variables), NOT against the raw template file. If both `GRAPHTOR_SOURCES_PATH` and `GRAPHTOR_BINARY_PATH` are unchanged, checksums will match; if the paths changed, the tuner should flag for re-render.
* .stage.agent.md and .ship.agent.md contain `GRAPHTOR_UNAVAILABLE` reference (text search)
* workspace-profile.yaml contains `graphtor_docs` section (structural check)

Example overlay target map for `browser-verification`:

| Overlay Element | Required Targets |
|---|---|
| Browser workflow rules | foundation docs, `browser-verification.instructions.md` |
| Automation skill | `browser-automation/SKILL.md` — treated as an explicit overlay target, not an optional add-on |
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
| Risky-plan legibility | `.stage.agent.md`, `impl-plan/SKILL.md`, `plan-harden/SKILL.md`, `plan-review/SKILL.md` |
| Approval / rollback visibility | review, runtime-verification, and operational-closure workflows |

Example overlay target map for `release-observability`:

| Overlay Element | Required Targets |
|---|---|
| Monitoring plan discipline | foundation docs, `release-observability.instructions.md`, `operational-closure/SKILL.md` |
| Rollback trigger requirements | `operational-closure/SKILL.md`, `runtime-verification/SKILL.md` |
| Observation windows | closure-facing skills and PR lifecycle handoff sections |

Runtime validator structural contract:

* workspace-profile.yaml contains `runtime_validation.validator_manifest`, `runtime_validation.validation_expectations`, and `runtime_validation.releasability`
* .ship.agent.md references validator evidence and releasability evidence handoff
* runtime-verification/SKILL.md emits validator evidence with surface adapters, probe hints, manual checkpoint evidence, and verdict
* operational-closure/SKILL.md converts validator evidence into releasability evidence

Map primitives to template groups:

| Primitive | Template Groups |
|---|---|
| 1 - State & Context | `agents/stage` (session continuity), `agents/ship` (session continuity), `agents/research/learnings-researcher`, `skills/compact-context`, `skills/compound`, `skills/compound-refresh`, `skills/harness-doctor` (install health baseline and pre-flight context), `instructions/context-efficiency` |
| 2 - Task Granularity | Embedded in `foundation/AGENTS.md`, `agents/stage` |
| 3 - Model Routing | Embedded in `foundation/AGENTS.md`, all agent definitions |
| 4 - Orchestration | `agents/stage`, `agents/ship`, `agents/orchestrator`, `skills/deliberate`, `skills/spike`, `skills/impl-plan`, `skills/plan-harden`, `skills/build-feature`, `skills/fix-ci`, `skills/harvest`, `skills/pr-lifecycle`, `skills/harness-architect`, `skills/shipment-reconcile` (when `{{FEATURE_SHIPMENTS}}` is true), `prompts/feature-flow`, `prompts/feature-flow-parallel` (P-016 planning-overlap alias, not parallel implementation), `prompts/feature-flow-dark` (P-017 exact-trigger shim) |
| 5 - Guardrails | `foundation/constitution`, `policies/workflow-policies`, `foundation/AGENTS.md`, `skills/safety-modes`, `skills/file-lock`, `skills/harness-doctor` (MCP pre-flight, tool availability gate, P-016 topology awareness, and P-017 dark-mode gate awareness), `instructions/circuit-breaker`, `instructions/concurrency`, optional `instructions/strict-safety` |
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
   * `coding-discipline.instructions.md` — Behavioral coding guardrails: think before coding, simplicity first, surgical changes, and goal-driven verification. Universal (install as-is).
   * `git-merge.instructions.md` — Universal (install as-is)
   * `pull-request.instructions.md` — Universal (install as-is)
   * `prompt-builder.instructions.md` — Universal (install as-is)
   * `circuit-breaker.instructions.md` — Anti-spinning protocol with retry thresholds, escalation, error logging, and optional cooldown/auto-reset guidance. Universal (install as-is). Resolve `{{CIRCUIT_BREAKER_COOLDOWN}}` with default `5 minutes`. Referenced by the constitution's Stop Conditions section.
   * `concurrency.instructions.md` — File operation locking protocol for multi-agent and human+agent concurrency control. Universal (install as-is). Requires the `file-lock` skill scripts to be installed alongside.
   * `architecture-doc.instructions.md` — Progressive disclosure and architecture documentation rules (Primitive 9)
   * `context-efficiency.instructions.md` — Context window hygiene: tool result offloading, committed change eviction, and proactive compaction triggers (Primitive 1). Universal (install as-is).
   * `ci-security.instructions.md` — CI/CD security and hygiene conventions. Adapt `{{CI_WORKFLOW_GLOB}}` to match the workspace CI platform (e.g., `**/.github/workflows/*.yml` for GitHub Actions). Install when the workspace uses a CI system detected during discovery.
   * `workflows.instructions.md` — CI/CD workflow structural conventions (job naming, artifacts, caching, matrix, reusable workflows). Install alongside `ci-security.instructions.md` when a CI system is detected.
   * `github-pr-automation.instructions.md` — GitHub-specific PR automation: local-review readiness verification, optional Copilot shadow-review lifecycle during migration, and CI check monitoring with back-off polling. Install when the workspace is hosted on GitHub (git remote contains `github.com` or `{{CI_PLATFORM}}` is `GitHub Actions`). Resolves `{{REPO_OWNER}}` and `{{REPO_NAME}}` from the git remote URL.
   * `mcp-server.instructions.md` — MCP server development conventions. Install when workspace-discovery detects an MCP server project (MCP SDK in dependencies). Resolves `{{MCP_SDK}}`, `{{MCP_TRANSPORT}}`, `{{MCP_PROJECT_STRUCTURE}}`.

3. **Backlog integration instructions** (`backlog-integration.instructions.md`): Generated from the backlog tool registry. Maps abstract operations to the specific tool's MCP names and CLI commands. Only generated when a backlog tool is detected or registered.

4. **Capability-pack instructions**: When `agent-intercom` is enabled, install `agent-intercom.instructions.md` and use it as the authoritative reference for heartbeat, remote approval, operator steering, and standby workflows.
   When `agent-engram` is enabled, install `agent-engram.instructions.md` and use it as the authoritative reference for engram-first search, workspace binding, index freshness, and indexed-search fallback workflows.
   When `backlogit` is enabled, install `backlogit.instructions.md`, `backlogit-sql-schema.instructions.md`, and `backlogit-yaml-header-tooling.instructions.md` and use them as the authoritative references for backlogit-native query, queue, dependency, memory, checkpoint, comment, traceability, SQL lookup, YAML frontmatter coverage, and source-artifact-cleanup workflows.
   When `browser-verification` is enabled, install `browser-verification.instructions.md` and use it as the authoritative reference for browser-ready server checks, route selection, headed/headless choice, and human checkpoints.
   When `continuous-learning` is enabled, install `continuous-learning.instructions.md` and use it as the authoritative reference for observation capture, instinct formation, and learned-artifact promotion.
   When `strict-safety` is enabled, install `strict-safety.instructions.md` and use it as the authoritative reference for `ProposedAction`, `ActionRisk`, `ActionResult`, approval routing, and risky-work legibility.
   When `release-observability` is enabled, install `release-observability.instructions.md` and use it as the authoritative reference for monitoring plans, pre-deploy audits, observation windows, and rollback trigger discipline.
   When `adversarial-review` is enabled, install `adversarial-review.instructions.md` and use it as the authoritative reference for multi-model dispatch, consensus assembly, confidence tiers, and remediation queue structure.
   When `graphtor-docs` is enabled, install `graphtor-docs.instructions.md` and use it as the authoritative reference for indexed local documentation search, semantic retrieval, doc-graph traversal, and server lifecycle workflows. Resolve `{{GRAPHTOR_SOURCES_PATH}}` from the workspace profile's `graphtor_docs.sources_path` (defaulting to `.graphtor/config/sources.yaml`) and `{{GRAPHTOR_BINARY_PATH}}` from `graphtor_docs.binary_path` when present; otherwise fall back to `graphtor` on PATH and then `.graphtor/bin/graphtor-docs.exe` or `.graphtor/bin/graphtor-docs`, with final default `graphtor` (assumes PATH).

5. **Two-agent model instructions** (conditional — auto-detected): When both `.stage.agent.md` and `.ship.agent.md` are being installed (indicating the two-agent Stage/Ship workflow model), install `role-enforcement.instructions.md` from `role-enforcement.instructions.md.tmpl`. This instruction defines the pre-mutation check protocol that teaches each agent to self-check against its own `## Role Boundary (NON-NEGOTIABLE)` table before executing tool calls. Skip this instruction when only one agent (or neither) is installed — role enforcement is only meaningful in the two-agent model.

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

1. **Pipeline agents**: stage, ship, orchestrator
   * Adapt build/test/lint commands throughout
   * Adapt quality gate sequences
    * Adapt model routing tiers (preserve structure, adjust agent assignments if needed)
    * When `agent-intercom` is enabled, add explicit workflow guidance for ping/heartbeat, broadcast milestones, approval routing, and operator clarification waits. If P-017 dark factory guidance is present, ensure dark-mode events (`DARK_MODE_START`, `DARK_MODE_SCOPE`, `BRAINSTORM_HANDOFF_READY`, `LOCAL_REVIEW_READY`, `DARK_MODE_MERGE_AUTHORIZED`, `ADMIN_FALLBACK_ATTEMPTED`, `DARK_MODE_HALTED`, `DARK_MODE_COMPLETE`) are self-contained and include scope, decisions, brainstorm/requirements handoff state, gates, reviewed HEADs, outcomes, and next actions.
    * When `agent-engram` is enabled, add explicit workflow guidance for engram-first search, workspace binding/index verification, and code-graph or impact-analysis style diagnostics
    * When `backlogit` is enabled, add explicit workflow guidance for queue-first work selection, dependency-aware planning, checkpoint persistence, and commit traceability
    * When `strict-safety` is enabled, keep risky planning and approval vocabulary visible through stage, review, verification, and closure handoffs
    * When runtime validation is in scope, ensure Ship, runtime-verification, and operational-closure carry `runtime_validation.validator_manifest`, `runtime_validation.validation_expectations`, validator evidence, and releasability evidence rather than report-oriented runtime notes
    * When `release-observability` is enabled, ensure operational-closure and runtime-verification carry monitoring plan, observation window, rollback trigger expectations, and releasability evidence requirements
    * When `graphtor-docs` is enabled, add explicit workflow guidance for indexed local documentation search using graphtor-docs MCP tools (`search_local_docs`, `search_semantic`, `research_topic`) before falling back to broad filesystem or web search
    * When both stage and ship agents are being installed (two-agent model), ensure both agent definitions contain a `## Role Boundary (NON-NEGOTIABLE)` section with Allowed/Forbidden tables. The role-enforcement instruction (Step 2.2, item 5) references these tables at runtime.

2. **Support agents**: prompt-builder
   * Minimal technology adaptation needed
   * Adapt file path patterns for the workspace structure

3. **Expert agent**: Generate a technology-specific expert agent (equivalent to `rust-engineer.agent.md` but for the target language). Name it `{language}-engineer.agent.md`.

4. **Review personas**: Generate from review persona templates when the `review`
   layer is active
   * `architecture-strategist.agent.md` — Universal with domain adaptation
   * `constitution-reviewer.agent.md` — References local constitution
   * `correctness-reviewer.agent.md` — Always-on behavioral correctness reviewer
   * `maintainability-reviewer.agent.md` — Always-on maintainability and complexity reviewer
   * `scope-boundary-auditor.agent.md` — Universal
    * `technology-reviewer.agent.md` → `{language}-reviewer.agent.md` — Fully technology-specific
    * `concurrency-reviewer.agent.md` — Include only for languages with concurrency primitives
    * `agent-native-parity-reviewer.agent.md` — Include when `agent_native.recommended_reviewer` is true in the workspace profile
    * `security-reviewer.agent.md` — Include when the `review` layer is active; universal security code review persona
    * `security-lens-reviewer.agent.md` — Include when the `review` layer is active; plan-level security review persona
    * `template-integrity-reviewer.agent.md` — Include when the workspace produces template-driven or Markdown-heavy product surfaces so frontmatter, placeholder, markdown, and cross-reference defects are caught before PR submission
    * `schema-cli-docs-coupling-reviewer.agent.md` — Include when diffs commonly span schemas, CLI verification logic, install/tune flows, and operator docs
    * `learnings-researcher.agent.md` — Universal

5. **Orchestrating review skills**: `plan-review/SKILL.md`, `review/SKILL.md` — dispatch persona subagents during plan and code review at subagent depth 1. Install when the `review` layer is active. Ensure `review/SKILL.md` produces a local review readiness outcome (`READY`, `READY_WITH_FOLLOWUPS`, `BLOCKED`) and routes residual P2/P3 findings into explicit follow-up handling. `adversarial-review.agent.md` is a standalone agent at depth 2 (dispatches multiple parallel reviewer instances).
   * Minimal technology adaptation needed
   * Install as skills (not agents)

6. **Security agent**: `security-sentinel.agent.md` — User-invocable security audit agent. Install when Primitive 5 or Primitive 7 is selected.

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
    * `security-audit/SKILL.md` — Install when Primitive 5 or Primitive 7 is selected. Resolves security surface variables: `{{AGENTIC_CONFIG_GLOB}}`, `{{SOURCE_GLOB}}`, `{{PRIMARY_LANGUAGE}}`, `{{DOCS_SECURITY}}`, `{{SECURITY_CONFIG_RULES}}`, `{{SECURITY_OWASP_PATTERNS}}`.
    * `runtime-verification/SKILL.md` — Install when the `runtime` layer is active (normally because Primitive 10 is selected)
    * `operational-closure/SKILL.md` — Install when the `runtime` layer is active (normally because Primitive 10 is selected)
    * `observe/SKILL.md`, `learn/SKILL.md`, `evolve/SKILL.md` — Install when `continuous-learning` is enabled
    * `browser-automation/SKILL.md` — Install when `browser-verification` is enabled. Resolves browser variables: `{{BROWSER_CLI}}`, `{{BROWSER_HEADLESS_FLAG}}`. This is an explicit browser-verification overlay target, not an optional add-on.
    * `iterative-experiment/SKILL.md` — Install when the `workflow` layer is active. Resolves experiment variables: `{{EXPERIMENT_BRANCH_PREFIX}}`, `{{EXPERIMENT_RESULTS_DIR}}`.

3. **Always-installed skills** (install with every preset, regardless of primitive or layer selection):
    * `harness-doctor/SKILL.md` — Universal health diagnostic; install with every preset. Resolves health-check variables: `{{HARNESS_MANIFEST_PATH}}`, `{{AUTOHARNESS_VERSION}}`.

When `agent-intercom` is enabled, weave operator visibility guidance into the long-running and gating skills rather than treating it as a separate isolated instruction.

When `agent-engram` is enabled, weave indexed-search guidance into research, planning, build, and repair skills rather than treating it as a generic footnote.

When `browser-verification` is enabled, install `browser-automation/SKILL.md` as an explicit overlay target and weave browser-specific guidance into runtime verification and operational closure rather than leaving browser work as an implicit manual step.

When `continuous-learning` is enabled, install and reference the observation
lifecycle skills rather than relying on invisible prompt behavior.

When `strict-safety` is enabled, weave the action contract through `plan-harden`,
`safety-modes`, review, and closure skills rather than treating the pack as a
single isolated instruction file.

When `release-observability` is enabled, weave monitoring plan and rollback trigger
expectations through `runtime-verification` and `operational-closure` rather than
treating the pack as a standalone instruction file.

When `graphtor-docs` is enabled, weave indexed documentation retrieval guidance into
research, planning, and knowledge-retrieval workflows. Agents should resolve domain
concepts, API references, and architectural context from graphtor-docs indexed sources
before falling back to broad web search or raw filesystem scan.

#### Step 2.6: Policy Layer

Generate the workflow policy registry from `workflow-policies.md.tmpl`:

* P-001 (Single-Release-Unit Completion) — Universal
* P-002 (TDD Gate) — Adapt test commands and red-phase detection
* P-003 (Decomposition Chain) — Universal
* P-004 (Red Phase Before Implementation) — Adapt compilation and test failure detection
* P-005 (Policy Violation Telemetry) — Universal
* P-006 (Plan Hardening Gate) — Universal
* P-007 through P-015 — Universal backlog, markdown, merge, role, branch, tool, tier, review-readiness, and shipment-closure policies
* P-016 (No Parallel Branch/Worktree Execution) — Universal. Preserve the Stage spike/research worktree exception and ensure generated Stage, Ship, Orchestrator, AGENTS.md, and concurrency guidance do not endorse parallel implementation branches/worktrees.
* P-017 (Dark Factory Autonomy Contract) — Universal when dark-mode prompts or guidance are installed. Preserve the exact trigger, bounded scope, local-review-first readiness, merge/admin fallback fail-closed behavior, telemetry events, and closure evidence requirements.
* Full-build PR gate — Universal. Ensure Ship, pr-lifecycle, and GitHub PR automation guidance require a successful full local build before any code-changing PR is created, updated, or presented, with explicit non-applicability allowed only for documentation-only/backlog-only PRs.

#### Step 2.7: Prompt Layer

Generate prompt files:

* `ping-loop.prompt.md` — Universal
* `feature-flow.prompt.md` — Install when Primitive 4 is selected. User-facing alias to the Orchestrator's standard sequential full-cycle routing.
* `feature-flow-parallel.prompt.md` — Install when Primitive 4 is selected. User-facing alias to the Orchestrator's pipelined full-cycle routing preference, now constrained to P-016-compliant planning overlap; it must degrade to sequential execution when overlap would create parallel implementation branches/worktrees.
* `feature-flow-dark.prompt.md` — Install when Primitive 4 and P-017 are selected. User-facing shim for the exact `Run pipeline in dark mode` trigger; it must route through Orchestrator, record `DARK_MODE_ACTIVE`, preserve P-001/P-009/P-014/P-016/P-017, and never bypass local readiness, required checks, telemetry, or closure gates.

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

If `dry_run` is true, write all artifacts to `.autoharness/staging/`, then run deterministic compatibility verification with:

```text
autoharness verify-workspace --workspace {workspace_path}
```

The command writes JSON and Markdown reports into `.autoharness/staging/` describing schema blockers, unresolved placeholders, staged render output, and targeted overlay checks. Report those paths and halt here without mutating the installed harness.

#### Step 3.2: Write Artifacts

Write generated artifacts to the target workspace. Use the following directory mapping:

| Source Template Group | Target Location |
|---|---|
| Foundation / AGENTS.md | `{workspace}/AGENTS.md` |
| Foundation / copilot-instructions.md | `{workspace}/.github/copilot-instructions.md` |
| Foundation / constitution | `{workspace}/.github/instructions/constitution.instructions.md` |
| Instructions | `{workspace}/.github/instructions/` |
| Agents | `{workspace}/.github/agents/` — top-level agents (Orchestrator, Stage, Ship, Auto-MergeInstall, Auto-Tune) |
| Subagents | `{workspace}/.github/agents/subagents/` — all non-top-level agents: review personas, researchers, language-engineer, prompt-builder, adversarial-review, security-sentinel |
| Skills | `{workspace}/.github/skills/{name}/SKILL.md` |
| Scripts (when Primitive 5 or 6 selected) | `{workspace}/scripts/` — copy all `.ps1` and `.sh` files from `{autoharness_home}/templates/skills/{skill-name}/scripts/` for each skill that includes scripts (file-lock, skill-search) |
| Startup scripts | `{workspace}/start.ps1`, `{workspace}/start.sh` — generated from `{autoharness_home}/templates/scripts/start.ps1.tmpl` and `start.sh.tmpl`; always installed at workspace root regardless of preset |
| Markdownlint config (when `tools.markdownlint` detected or operator opt-in) | `{workspace}/.markdownlint.json` — resolved from `{autoharness_home}/templates/scripts/.markdownlint.json.tmpl` (no variables to resolve; copy as-is) |
| Markdownlint pre-commit hooks (when markdownlint config installed) | `{workspace}/scripts/pre-commit-markdownlint.sh`, `{workspace}/scripts/pre-commit-markdownlint.ps1` — copied from `{autoharness_home}/templates/scripts/pre-commit-markdownlint.sh.tmpl` and `pre-commit-markdownlint.ps1.tmpl`; set execute permission on `.sh` after copy: `chmod +x scripts/pre-commit-markdownlint.sh` |
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
autoharness_version: "{{AUTOHARNESS_VERSION}}"
autoharness_home: "{{AUTOHARNESS_HOME}}"
profile_hash: "{{SHA256_OF_PROFILE}}"
config_hash: "{{SHA256_OF_CONFIG_OR_NULL}}"  # null if no .autoharness/config.yaml was present
install_preset: "{{PRESET}}"
primary_stack_pack: {{PRIMARY_STACK_PACK}}
stack_packs: [{{STACK_PACKS}}]
install_layers: [{{INSTALL_LAYERS}}]
capability_packs: [{{CAPABILITY_PACKS}}]
capability_pack_overlays:
  - pack: "{{PACK_NAME}}"
    overlay_targets: [{{OVERLAY_TARGETS}}]
    verification_checks: [{{OVERLAY_VERIFICATION_CHECKS}}]
  # When agent-engram is enabled, a real (non-commented) overlay entry is required:
  # - pack: "agent-engram"
  #   overlay_targets:
  #     - "foundation-docs"
  #     - "agent-engram.instructions.md"
  #     - "pipeline-agents"
  #     - "analysis-heavy-workflows"
  #   verification_checks:
  #     - "agent-engram.instructions.md installed at .github/instructions/"
  #     - ".stage.agent.md contains Engram session-start check (get_workspace_status)"
  #     - ".ship.agent.md contains Engram session-start check (get_workspace_status)"
  #     - "copilot-instructions.md engram block cross-references installed instructions"
  #     - "No unresolved {{VARIABLE}} in agent-engram.instructions.md"
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

Use `autoharness verify-workspace --workspace {workspace_path}` as the deterministic verification engine for this phase. The command stages renderable artifacts into `.autoharness/staging/`, runs a portability scan to flag hardcoded environment-specific paths in installed artifacts (surfaced as P1 warnings), and produces JSON plus Markdown reports before adversarial review runs.

#### Step 4.1: Template Variable Sweep

Scan every installed artifact for unresolved template variables:

1. Search all installed `.md` files for `{{` followed by `}}`
2. Exclude occurrences inside fenced code blocks (between ` ``` ` markers) that
   are intentional examples
3. For each match, record the file path, line number, and variable name
4. **FAIL** verification if any unresolved variables are found outside code fences
5. Also scan the written harness manifest (`{{HARNESS_MANIFEST_PATH}}`) for unresolved `{{...}}`
   in scalar field values. In particular, `autoharness_version` MUST be a concrete
   version string, never a literal `{{AUTOHARNESS_VERSION}}`. **FAIL** verification if
   the manifest contains an unresolved placeholder — a literal version would silently
   poison harness-doctor's drift check.

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
5. **Markdownlint config verification** (when markdownlint config was installed):
   a. Confirm `.markdownlint.json` is present at workspace root
   b. Confirm it contains `"MD001": true`, `"MD025": true`, `"MD041": true`
   c. Confirm `scripts/pre-commit-markdownlint.sh` and `scripts/pre-commit-markdownlint.ps1`
      are present in `{workspace}/scripts/`
   d. Report FAIL for any missing artifact
6. **Merge policy verification** (universal — applies to all installed harnesses):
   a. Confirm `constitution.instructions.md` contains "Merge Commit History Preservation"
      or equivalent principle text referencing P-009
   b. Confirm `workflow-policies` contains "P-009" and "squash" keyword
   c. Confirm `.ship.agent.md` or the pr-lifecycle skill contains a pre-merge strategy
      guardrail referencing P-009
   d. Confirm `git-merge.instructions.md` contains a squash-merge prohibition section
   e. Report FAIL for any missing artifact — absent merge policy is a P-009 violation risk
 6a. **Full-build PR gate verification** (universal — applies to all installed harnesses):
    a. Confirm `.ship.agent.md` requires a full local build before code-changing PRs
    b. Confirm `pr-lifecycle/SKILL.md` requires successful full local build evidence in PR readiness for code-changing PRs
    c. Confirm `github-pr-automation.instructions.md` includes the `Full local build` readiness field and gate check
    d. Report FAIL for stale guidance that allows code-changing PRs without successful full local build evidence
7. **No-parallel branch/worktree verification** (universal — applies to all installed harnesses):
   a. Confirm `workflow-policies` contains `P-016` and "No Parallel Branch/Worktree Execution"
   b. Confirm `constitution.instructions.md` or root `AGENTS.md` states single active implementation branch/worktree behavior
   c. Confirm `.ship.agent.md` contains a P-016 worktree topology gate before shipment claim or mutation
   d. Confirm `.stage.agent.md` limits extra worktrees to explicit Stage spike/research investigation with no implementation, template/source/config mutation, shipment claim, PR preparation, or Ship execution
   e. Confirm `_orchestrator.agent.md` describes planning overlap without requiring different implementation branches
   f. Report FAIL for stale guidance that endorses parallel implementation branches/worktrees outside the Stage spike/research exception
8. **Dark factory verification** (when P-017 or `feature-flow-dark` is installed):
   a. Confirm `workflow-policies` contains `P-017`, exact trigger `Run pipeline in dark mode`, and `DARK_MODE_ACTIVE`
   b. Confirm `_orchestrator.agent.md` records bounded scope, merge approval authority, admin fallback authority, stop conditions, and `DARK_MODE_START` / `DARK_MODE_COMPLETE`
   c. Confirm `.ship.agent.md` or `pr-lifecycle` requires current-HEAD local readiness, P-009 merge commit strategy, required checks, P-016 topology, and immediate `headRefOid` re-check before merge/admin fallback
   d. Confirm `agent-intercom.instructions.md` contains dark-mode visibility events, including `BRAINSTORM_HANDOFF_READY`, and degraded-visibility halt behavior
   e. Confirm `feature-flow-dark.prompt.md` routes through Orchestrator and does not bypass Stage, Ship, backlog/shipment policy, local readiness, telemetry, or closure
   f. Report FAIL for missing or stale guidance that treats dark mode as a safety bypass, allows vague trigger phrases, or omits closure evidence (decisions, gates, reviewed HEADs, merge/fallback status, closure status, follow-ups)

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
* When the workspace is Git-backed, install output is left as feature-branch work or local uncommitted changes awaiting feature-branch handoff; direct default-branch commit/push is never recommended
