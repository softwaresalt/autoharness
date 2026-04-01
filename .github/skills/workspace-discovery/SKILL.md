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

### Phase 1: File System Scan

Scan the workspace root to build an inventory of project characteristics.

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

### Phase 2: Convention Extraction

#### Step 2.1: Code Style Discovery

Detect existing code style enforcement:

* Linter configurations (`.eslintrc`, `clippy.toml`, `.pylintrc`, `rustfmt.toml`, `.prettierrc`)
* Editor configurations (`.editorconfig`, `.vscode/settings.json`)
* Pre-commit hooks (`.husky/`, `.pre-commit-config.yaml`)

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
* Existing harness artifacts that reference stale paths, removed tools, or outdated conventions

Record: `drift_report{}` with categorized changes.

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

frameworks: []

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

conventions:
  code_style: {}
  git: {}
  documentation: {}

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

drift_report: null
```

#### Step 4.2: Present for Review

Display the profile summary to the user and wait for confirmation or corrections before the installer proceeds to template composition.

## Quality Criteria

* Every field in the profile schema is populated or explicitly set to null with a reason
* Language detection is verified against at least 2 signals (file extensions alone are insufficient)
* Build and test commands are verified to exist in configuration files, not assumed
* The profile is valid YAML and conforms to `schemas/workspace-profile.schema.json`
