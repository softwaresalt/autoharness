---
description: "Discover target workspace technology stack, conventions, build tools, test runners, CI/CD pipelines, and project structure to generate a workspace profile for harness composition"
---

## Workspace Discovery

Scan a target workspace to produce a structured workspace profile that drives harness template composition. The profile captures everything the installer needs to customize agents, skills, instructions, and policies for the target environment.

This skill is invoked from the globally-installed autoharness tool and operates read-only against the target workspace (aside from writing the profile output). It does not require autoharness to be installed in the target workspace.

## When to Use

Invoke this skill as the first phase of harness installation or tuning. The workspace profile is the single source of truth that downstream template composition uses to generate workspace-specific artifacts.

## Inputs

* `workspace_path`: (Required) Absolute path to the target workspace root.
* `existing_profile`: (Optional) Path to a previously generated profile for delta comparison during tuning.

## Output

A YAML file at `.autoharness/workspace-profile.yaml` in the target workspace containing the structured profile.

## Required Protocol

### Phase 0: Load Operator Configuration

Check for an operator-authored configuration file at `{workspace_path}/.autoharness/config.yaml`. If present:

1. Validate against `schemas/harness-config.schema.json`
2. Extract operator preferences: preset, primary stack pack, stack packs, install layers, capability packs, backlog tool/directory, prefix map, docs directory structure, model routing, template variable overrides
3. These preferences take precedence over auto-detected values in subsequent phases — when the operator has explicitly specified a value, use it instead of detecting

If the file does not exist, proceed with pure auto-detection. All fields are optional; the operator may specify only the settings they want to control.

### Phase 1: File System Scan

Scan the workspace root to build an inventory of project characteristics. When `.autoharness/config.yaml` provides explicit values, record those directly and skip detection for the corresponding field.

#### Step 1.1: Language Detection

Identify primary and secondary languages by file extension distribution:

| Signal | Detection Method |
|--------|-----------------|
| Rust | `Cargo.toml`, `*.rs` files, `rust-toolchain.toml` |
| TypeScript/JavaScript | `package.json`, `tsconfig.json`, `*.ts`, `*.tsx`, `*.js` |
| Python | `pyproject.toml`, `setup.py`, `requirements.txt`, `*.py`, `Pipfile` |
| Go | `go.mod`, `go.sum`, `*.go` |
| C# / .NET | `*.csproj`, `*.sln`, `global.json`, `*.cs` |
| Java / Kotlin | `pom.xml`, `build.gradle`, `*.java`, `*.kt` |
| Ruby | `Gemfile`, `*.rb`, `Rakefile` |
| Swift | `Package.swift`, `*.swift` |
| PHP | `composer.json`, `*.php` |
| C/C++ | `CMakeLists.txt`, `Makefile`, `*.c`, `*.cpp`, `*.h` |

Record: `primary_language`, `secondary_languages[]`, `file_counts{}`.

#### Step 1.2: Framework Detection

Identify frameworks from configuration files and dependency declarations:

| Signal | Framework |
|--------|-----------|
| `next.config.js` / `next.config.mjs` | Next.js |
| `angular.json` | Angular |
| `vite.config.*` | Vite |
| `django` in requirements | Django |
| `flask` in requirements | Flask |
| `fastapi` in requirements | FastAPI |
| `spring` in pom.xml/gradle | Spring Boot |
| `axum` / `actix` / `rocket` in Cargo.toml | Rust web framework |
| `rails` in Gemfile | Ruby on Rails |
| `laravel` in composer.json | Laravel |

Record: `frameworks[]`.

#### Step 1.3: Build & Test Tool Detection

| Signal | Tool |
|--------|------|
| `Cargo.toml` | cargo (build, test, clippy, fmt) |
| `package.json` scripts | npm/yarn/pnpm (build, test, lint) |
| `Makefile` | make |
| `CMakeLists.txt` | cmake |
| `pyproject.toml` [tool.pytest] | pytest |
| `jest.config.*` | jest |
| `vitest.config.*` | vitest |
| `.mocharc.*` | mocha |
| `go test` convention | go test |
| `*.csproj` | dotnet build/test |
| `build.gradle` | gradle |
| `pom.xml` | maven |

Record: `build_tool`, `test_runner`, `linter`, `formatter`, `package_manager`.

#### Step 1.4: CI/CD Detection

| Signal | Platform |
|--------|----------|
| `.github/workflows/*.yml` | GitHub Actions |
| `.gitlab-ci.yml` | GitLab CI |
| `Jenkinsfile` | Jenkins |
| `.circleci/config.yml` | CircleCI |
| `azure-pipelines.yml` | Azure DevOps |
| `.travis.yml` | Travis CI |
| `bitbucket-pipelines.yml` | Bitbucket Pipelines |

Record: `ci_platform`, `ci_pipeline_steps[]`, `ci_quality_gates[]`.

#### Step 1.5: Project Structure Analysis

Identify the project's organizational patterns:

* Source directory layout (`src/`, `lib/`, `app/`, `pkg/`, monorepo with `packages/`)
* Test directory layout (`tests/`, `__tests__/`, `test/`, `spec/`, inline tests)
* Documentation directory (`docs/`, `doc/`, `wiki/`)
* Configuration files present (`.editorconfig`, `prettier`, `eslint`, linter configs)
* Existing agent harness artifacts (`.github/agents/`, `.github/skills/`, `.github/instructions/`)

Record: `source_layout`, `test_layout`, `doc_layout`, `existing_harness_artifacts[]`.

#### Step 1.5b: Runtime Surface Detection

Detect whether the workspace has runtime surfaces that need post-build verification or operational closure:

| Signal | Surface |
|--------|---------|
| Next.js / Vite / Angular / Rails views / templates / `public/` frontend assets | Web UI |
| OpenAPI files, route declarations, controllers, `api/` or `routes/` directories | Public API |
| Queue libraries, job workers, cron config, message consumers | Background jobs |
| Dockerfile, Helm charts, Terraform, deployment workflows | Deployment manifests |

Also detect browser-verification tooling from package dependencies or config files
such as Playwright, Cypress, Puppeteer, Selenium, or equivalent browser runners.

Record: `runtime_surfaces{}` with booleans for `web_ui`, `public_api`, and
`background_jobs`, `browser_tooling[]`, plus `deployment_manifests[]` for
discovered paths.

#### Step 1.5c: Agent-Intercom Detection

Detect whether the workspace is already configured for agent-intercom or a closely related remote-operator workflow:

| Signal | Meaning |
|--------|---------|
| `.intercom/settings.json` exists | Workspace has explicit intercom policy/configuration markers |
| `.vscode/mcp.json` or `.vscode/settings.json` references `agent-intercom`, `intercom`, or known intercom tool names (`ping`, `broadcast`, `standby`, `transmit`) | MCP server likely configured for the workspace |
| Existing `AGENTS.md` / `.github/copilot-instructions.md` references intercom heartbeat, remote approval, or Slack-mediated workflows | Harness may already be partially woven for intercom |

Record: `agent_intercom{}` with the following structure:

```yaml
agent_intercom:
  detected: true|false
  mcp_configured: true|false
  config_paths: []
  instruction_markers: []
  recommended: true|false
```

#### Step 1.5d: Agent-Engram Detection

Detect whether the workspace is already configured for agent-engram or a closely related indexed-search workflow:

| Signal | Meaning |
|--------|---------|
| `.engram/config.toml`, `.engram/registry.yaml`, or `.engram/code-graph/` exists | Workspace has engram installation or persisted state markers |
| `.vscode/mcp.json` or `.vscode/settings.json` references `agent-engram`, `engram`, or known engram tool names (`unified_search`, `query_memory`, `map_code`, `list_symbols`, `impact_analysis`, `query_graph`) | MCP server likely configured for the workspace |
| Existing `AGENTS.md` / `.github/copilot-instructions.md` references Engram-first search, `.engram/`, or workspace binding / status checks | Harness may already be partially woven for engram |

Record: `agent_engram{}` with the following structure:

```yaml
agent_engram:
  detected: true|false
  mcp_configured: true|false
  config_paths: []
  instruction_markers: []
  recommended: true|false
```

#### Step 1.5e: Agent-Native Surface Detection

Detect whether the workspace exposes agent-facing product surfaces that justify a
parity-focused reviewer:

| Signal | Meaning |
|--------|---------|
| `frameworks.mcp_sdk` or MCP transport dependencies are present | Workspace likely exposes MCP or agent-facing tool surfaces |
| `mcp-server.instructions.md`, tool handler directories, or tool schemas are present | Explicit agent tooling surface exists |
| Existing docs describe parity between UI actions and agent actions, or agent-only workflow concerns | Product likely requires user/agent parity review |
| Tool manifests, capability schemas, or action handlers suggest users and agents must share the same business operation surface | Parity-sensitive design likely matters |

Record: `agent_native{}` with the following structure:

```yaml
agent_native:
  detected: true|false
  mcp_sdk_present: true|false
  mcp_transport: "stdio"|"sse"|"streamable-http"|null
  agent_tooling_markers: []
  user_agent_parity_required: true|false
  recommended_reviewer: true|false
```

#### Step 1.5f: Stack-Pack Normalization

Normalize discovered signals into additive stack packs so the installer and tuner
can reason about composition more explicitly than a preset name alone.

Suggested normalization:

| Signal | Stack Pack |
|--------|------------|
| `runtime_surfaces.web_ui == true` | `web-app` |
| `runtime_surfaces.public_api == true` | `api-service` |
| `runtime_surfaces.background_jobs == true` | `background-worker` |
| `runtime_surfaces.deployment_manifests[]` not empty | `deployable-service` |
| `frameworks.mcp_sdk` present or `agent_native.detected == true` | `mcp-server` |
| CLI frameworks / layouts detected (for example Cobra, Clap, Click, Typer, Commander, `cmd/`, `bin/`) | `cli-tool` |
| No stronger runtime signal and the workspace looks package-like or reusable | `library` |

Choose `primary_stack_pack` deterministically:

1. Use the operator-configured `primary_stack_pack` when present.
2. Otherwise prefer the strongest detected runtime-facing stack in this order:
   `web-app` -> `api-service` -> `mcp-server` -> `background-worker` -> `cli-tool` -> `library`.
3. If no normalized stack pack is justified, leave it `null` and explain why in
   the recommendation summary.

Record:

```yaml
primary_stack_pack: "web-app"|null
stack_packs: []
```

#### Step 1.5g: Capability Pack Signal Detection

Scan for signals that indicate specific capability packs should be recommended.
This step covers packs whose eligibility depends on workspace characteristics
beyond what earlier steps already detect (agent-intercom, agent-engram, and
backlogit are detected through their tool markers; browser-verification is
detected through `runtime_surfaces.browser_tooling`).

**strict-safety signals**:

* public API surface present (`runtime_surfaces.public_api == true`)
* migration or schema management files detected (Alembic, Flyway, Prisma, ActiveRecord migrations, etc.)
* security-sensitive patterns present (auth modules, crypto usage, PII handling, payment integration)
* deployment infrastructure suggests rollout-critical surfaces (Kubernetes manifests, Helm charts, Docker Compose with production profiles)

Record: `strict_safety_signals: []` (list of detected signal descriptions)

**release-observability signals**:

* deployment manifests detected (Dockerfiles, Helm charts, Terraform, CloudFormation, Kubernetes YAML)
* runtime surfaces exist (`runtime_surfaces.public_api`, `runtime_surfaces.web_ui`, `runtime_surfaces.background_jobs`)
* monitoring or alerting configuration present (Prometheus rules, Grafana dashboards, Datadog config, PagerDuty integration)
* CI/CD pipelines include deployment steps (deploy jobs, release workflows, canary configurations)

Record: `release_observability_signals: []` (list of detected signal descriptions)

#### Step 1.6: Backlog Tool Detection

Detect installed backlog management tools by scanning for their workspace markers and configuration:

| Signal | Tool | Directory |
|--------|------|-----------|
| `.backlogit/` directory with `config.yaml` | backlogit | `.backlogit/` |
| `backlog/` directory with `config.yml` | backlog-md | `backlog/` |
| `backlog/` directory with `config.yaml` | backlog-md (alt) | `backlog/` |
| `backlog.config.yml` at root | backlog-md (project-root config) | `backlog/` |
| `.backlog/` directory (no tool config) | Manual/custom backlog | `.backlog/` |

For each detected tool, also check:

* MCP server configuration in VS Code settings (`.vscode/settings.json` → `mcpServers`)
* CLI binary availability (run `which backlogit` or `which backlog` or `npx backlog-md --version`)
* Package dependencies (`go.mod` for backlogit, `package.json` for backlog-md)

If no backlog tool is detected, check for manual backlog structures:

* `.backlog/` with task markdown files
* `TODO.md`, `BACKLOG.md`, or similar files at root

Record: `backlog_tool{}` with the following structure:

```yaml
backlog_tool:
  detected: true|false
  tool_name: "backlogit"|"backlog-md"|"manual"|null
  directory: ".backlogit"|"backlog"|".backlog"|null
  tool_type: "mcp"|"cli"|"both"|null
  mcp_registered: true|false
  cli_available: true|false
  config_path: "path/to/config"|null
  status_values: ["queued", "active", "done"]  # from tool config
  features:
    sql_query: true|false
    milestones: true|false
    documents: true|false
    telemetry: true|false
    # ... other feature flags
```

When a known tool is detected (backlogit or backlog-md), load the matching pre-built registry from `templates/backlog/registries/` for use during harness composition. When an unknown or manual backlog structure is detected, generate a minimal registry that the user can customize.

#### Step 1.7: AI Coding Environment Detection

Detect which AI coding environments are present in the workspace so the installer can apply environment-specific configuration automatically.

**VS Code detection signals** (any one is sufficient):

| Signal | Meaning |
|--------|---------|
| `.vscode/` directory exists | VS Code workspace likely in use |
| `*.code-workspace` file at the workspace root | Explicit VS Code multi-root workspace |
| `.vscode/settings.json` exists | VS Code settings already configured |
| `.vscode/extensions.json` exists | VS Code extension recommendations present |

When VS Code is detected:

1. Determine the platform-appropriate **user settings path**:
   - Windows: resolve `%APPDATA%` and append `\Code\User\settings.json`
   - macOS: `$HOME/Library/Application Support/Code/User/settings.json`
   - Linux: `$HOME/.config/Code/User/settings.json`
2. Check whether that user settings file already contains `chat.agentFilesLocations`,
   `chat.agentSkillsLocations`, or `chat.promptFilesLocations` entries pointing
   to paths under the resolved `autoharness home`
3. Record the resolved user settings path and findings for the installer

Record: `vscode{}` with the following structure:

```yaml
vscode:
  detected: true|false
  user_settings_path: "C:\\Users\\alice\\AppData\\Roaming\\Code\\User\\settings.json"  # resolved absolute path; null if OS unrecognised
  has_agent_settings: true|false   # true when autoharness agent entries already present in user settings
```

### Phase 2: Convention Extraction

#### Step 2.1: Code Style Discovery

Detect existing code style enforcement:

* Linter configurations (`.eslintrc`, `clippy.toml`, `.pylintrc`, `rustfmt.toml`, `.prettierrc`)
* Editor configurations (`.editorconfig`, `.vscode/settings.json`)
* Pre-commit hooks (`.husky/`, `.pre-commit-config.yaml`)
* Markdown linting: detect `markdownlint-cli` via `which markdownlint` (bash) or
  `Get-Command markdownlint` (PowerShell), and check for existing `.markdownlint.json` or
  `.markdownlint.yaml` config files. Record `tools.markdownlint: true|false` and
  `tools.markdownlint_config: {path}|null` in the workspace profile.
* Global distribution detection: check whether this workspace is a globally-distributed
  tool that ships agent definitions in its package. Detection signals:
  1. `pyproject.toml` exists and its `[tool.hatch.build.targets.wheel.force-include]`
     section maps `.github/agents` into the wheel (value contains `src/` or any package path)
  2. `.github/local-agents/` directory exists
  3. The force-include section does NOT map `.github/local-agents/`
  When all three signals are present, record:
  `distribution.is_global_tool: true`
  `distribution.global_agents_dir: .github/agents`
  `distribution.local_agents_dir: .github/local-agents/`
  Otherwise omit the `distribution` field from the profile.

Record: `code_style{}` with detected rules.

#### Step 2.2: Git Convention Discovery

Detect Git workflow conventions:

* Branch naming patterns (from recent `git branch` or `.github/workflows/` triggers)
* Commit message patterns (conventional commits, other standards)
* PR templates (`.github/PULL_REQUEST_TEMPLATE.md`)
* Issue templates (`.github/ISSUE_TEMPLATE/`)
* Protected branches, required reviewers (from branch protection rules if accessible)

Record: `git_conventions{}`.

#### Step 2.3: Documentation Convention Discovery

Detect documentation patterns:

* README structure and sections
* API documentation tools (rustdoc, JSDoc, Sphinx, Javadoc, Swagger/OpenAPI)
* Architecture Decision Records (ADRs)
* Changelog conventions (`CHANGELOG.md`, conventional changelog)

Record: `doc_conventions{}`.

### Phase 3: Existing Harness Assessment

If the workspace already has agent harness artifacts (from a previous autoharness installation or manual setup):

#### Step 3.1: Inventory Existing Artifacts

Scan for and catalog:

* `.github/agents/*.agent.md`
* `.github/skills/*/SKILL.md`
* `.github/instructions/*.instructions.md`
* `.github/prompts/*.prompt.md`
* `.github/policies/*.md`
* `.github/copilot-instructions.md`
* `AGENTS.md`
* `.backlog/` directory structure
* `.autoharness/` marker files

Record: `existing_harness{}` with file paths, descriptions, and modification dates.

#### Step 3.2: Drift Detection (Tuning Mode Only)

When `existing_profile` is provided, compare the current scan against the previous profile:

* New languages or frameworks added
* Build/test tools changed
* CI pipeline modified
* New source directories created
* Primary stack or additive stack-pack composition changed
* Existing harness artifacts that reference stale paths, removed tools, or outdated conventions
* Manifest-tracked harness artifacts that are missing or checksum-divergent, excluding any paths matched by `.autoharness/drift-ignore`

Record: `drift_report{}` with categorized changes, optional checksum-scan
results, and initial recommendations.

### Phase 4: Profile Assembly

#### Step 4.1: Compose the Profile

Assemble all discovered data into the workspace profile YAML:

```yaml
# .autoharness/workspace-profile.yaml
schema_version: "1.0.0"
generated_at: "{{ISO_8601_TIMESTAMP}}"
workspace_path: "{{WORKSPACE_PATH}}"

languages:
  primary: "{{PRIMARY_LANGUAGE}}"
  secondary: []

frameworks:
  list: []
  mcp_sdk: null
  mcp_transport: null

primary_stack_pack: null
stack_packs: []

build:
  tool: "{{BUILD_TOOL}}"
  command: "{{BUILD_COMMAND}}"

test:
  runner: "{{TEST_RUNNER}}"
  command: "{{TEST_COMMAND}}"
  directory: "{{TEST_DIR}}"

lint:
  tool: "{{LINTER}}"
  command: "{{LINT_COMMAND}}"

format:
  tool: "{{FORMATTER}}"
  command: "{{FORMAT_COMMAND}}"

ci:
  platform: "{{CI_PLATFORM}}"
  pipeline_steps: []
  quality_gates: []

structure:
  source_layout: "{{SOURCE_LAYOUT}}"
  test_layout: "{{TEST_LAYOUT}}"
  doc_layout: "{{DOC_LAYOUT}}"

runtime_surfaces:
  web_ui: false
  public_api: false
  background_jobs: false
  browser_tooling: []
  deployment_manifests: []

conventions:
  code_style: {}
  git: {}
  documentation: {}

distribution:               # omit this section when is_global_tool is false
  is_global_tool: true      # true when workspace ships agents in its distribution package
  global_agents_dir: .github/agents        # agents included in the package
  local_agents_dir: .github/local-agents/  # workflow agents excluded from the package

tools:
  markdownlint: false        # true when markdownlint-cli is installed
  markdownlint_config: null  # path to existing config file, or null

harness_recommendations:
  preset: "{{RECOMMENDED_PRESET}}"
  capability_packs: []
  install_layers: []
  recommendation_reasons:
    preset: []
    capability_packs: []
    install_layers: []
  # Example when Engram is detected and recommended:
  # capability_packs: ["agent-engram"]

agent_intercom:
  detected: false
  mcp_configured: false
  config_paths: []
  instruction_markers: []
  recommended: false

agent_engram:
  detected: false
  mcp_configured: false
  config_paths: []
  instruction_markers: []
  recommended: false
  # Example when Engram is present:
  # detected: true
  # mcp_configured: true
  # config_paths: [".vscode/mcp.json", ".engram/config.toml"]
  # recommended: true

agent_native:
  detected: false
  mcp_sdk_present: false
  mcp_transport: null
  agent_tooling_markers: []
  user_agent_parity_required: false
  recommended_reviewer: false

existing_harness:
  has_harness: false
  artifacts: []

backlog_tool:
  detected: false
  tool_name: null
  directory: null
  tool_type: null
  mcp_registered: false
  cli_available: false
  config_path: null
  registry_path: null
  status_values: []
  features: {}

vscode:
  detected: false
  user_settings_path: null
  has_agent_settings: false

drift_report: null
# Example in tuning mode:
# drift_report:
#   changes: []
#   checksum_scan:
#     manifest_present: true
#     ignore_file: ".autoharness/drift-ignore"
#     checked_artifacts: 12
#     missing_count: 0
#     user_modified_count: 1
#     ignored_count: 0
#     artifacts: []
#   recommendations: []
```

#### Step 4.2: Present for Review

Display the profile summary to the user and wait for confirmation or corrections before the installer proceeds to template composition.

The summary MUST include:

* Primary stack pack and additive stack packs detected from the workspace
* Recommended preset (`starter`, `standard`, or `full`)
* Recommended install layers derived from preset, stack packs, runtime surfaces, and overlays
* Recommended capability packs based on runtime surfaces (for example `browser-verification` when `web_ui: true` and browser tooling is present)
* Whether the `agent-intercom` pack is recommended because intercom markers or remote-operator workflow signals were detected
* Whether the `agent-engram` pack is recommended because engram markers or indexed-search workflow signals were detected
* Whether the `backlogit` pack is recommended because backlogit was detected and its advanced workflow features are available
* Whether the `strict-safety` pack is recommended because security-sensitive, migration, or high-blast-radius signals were detected
* Whether the `release-observability` pack is recommended because deployment infrastructure and runtime surfaces were detected
* Whether the conditional agent-native parity reviewer is recommended because MCP or parity-sensitive agent tooling surfaces were detected
* Whether Primitive 10 should be emphasized because deployment or runtime surfaces were detected
* Plain-language reasons for the recommended preset, packs, and install layers rather than only the final names

## Quality Criteria

* Every field in the profile schema is populated or explicitly set to null with a reason
* Language detection is verified against at least 2 signals (file extensions alone are insufficient)
* Build and test commands are verified to exist in configuration files, not assumed
* The profile is valid YAML and conforms to `schemas/workspace-profile.schema.json`
* When tuning mode is active and a manifest exists, checksum-scan results are captured or explicitly omitted with a reason
