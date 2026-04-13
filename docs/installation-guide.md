---
title: Installation Guide
description: Step-by-step guide for setting up autoharness globally and installing a harness into a target workspace
---

## Overview

autoharness is installed once to a global location and invoked against target workspaces. The target workspace receives only the generated harness artifacts — never autoharness engine files, templates, or schemas.

```text
┌──────────────────────────┐       ┌──────────────────────────┐
│  autoharness (global)    │       │  target workspace        │
│  ~/.autoharness/         │       │  ~/projects/my-app/      │
│                          │       │                          │
│  templates/              │──────▶│  AGENTS.md               │
│  schemas/                │ reads │  .github/agents/         │
│  .github/agents/         │ tmpl, │  .github/skills/         │
│  .github/skills/         │ writes│  .github/instructions/   │
│                          │ output│  .github/policies/       │
│                          │       │  .backlog/               │
│                          │       │  .autoharness/           │
└──────────────────────────┘       └──────────────────────────┘
```

## Step 1: Install autoharness Globally

### With uv (recommended)

```bash
uv tool install git+https://github.com/softwaresalt/autoharness.git
```

This installs `autoharness` as a global CLI tool. Agents resolve the installation path by running `autoharness home`.

Update when improvements are available:

```bash
uv tool upgrade autoharness
```

### With git clone (alternative)

Clone the repository to your preferred global location:

```bash
git clone https://github.com/softwaresalt/autoharness.git ~/.autoharness
```

Update: `cd ~/.autoharness && git pull`

Or use a custom location and set the environment variable:

```bash
git clone https://github.com/softwaresalt/autoharness.git ~/tools/autoharness
export AUTOHARNESS_HOME=~/tools/autoharness   # bash/zsh
$env:AUTOHARNESS_HOME = "$HOME\tools\autoharness"  # PowerShell
```

### Verify the installation

```bash
autoharness home      # prints the installation path
autoharness version   # prints the version
```

### How agents find autoharness

The `autoharness_home` path is resolved by agents in this order:

1. `AUTOHARNESS_HOME` environment variable
2. Output of `autoharness home` CLI command (if on PATH)
3. Directory traversal from the agent definition file
4. `~/.autoharness/` default

## Step 2: Configure Your Workspace (Optional)

Before running the installer, you can create an operator configuration file to tell autoharness how you want your harness set up. This is optional — autoharness auto-detects most settings — but it gives you explicit control over preferences that you want to persist across installations and tuning runs.

```bash
mkdir -p .autoharness
cat > .autoharness/config.yaml <<'EOF'
schema_version: "1.0.0"
preset: standard
primary_stack_pack: api-service
stack_packs:
  - api-service
  - deployable-service
install_layers:
  - foundation
  - instructions
  - workflow
  - review
  - runtime
  - backlog
  - knowledge
capability_packs:
  - backlogit
  - agent-engram
  - continuous-learning
backlog:
  tool: backlogit
  suffix_map:
    feature: "F"
    chore: "C"
    task: "T"
    spike: "S"
    deliberation: "D"
    bug: "B"
    epic: "E"
    subtask: "ST"
    shipment: "S"
docs:
  root: docs
continuous_learning:
  directory: .autoharness/continuous-learning
  capture_hooks: false
  environment_adapter: none
  promotion_threshold: 3
model_routing:
  tier1: gpt-5.4-mini
overrides:
  PROJECT_NAME: my-app
EOF
# Edit to your preferences:
$EDITOR .autoharness/config.yaml
```

The config file controls:

| Setting | Example | Purpose |
|---|---|---|
| `preset` | `standard` | Installation shape (starter, standard, full) |
| `primary_stack_pack` | `api-service` | Preferred primary stack classification when multiple additive stack packs are present |
| `stack_packs` | `[api-service, deployable-service]` | Additive workspace-shape signals used for composition |
| `install_layers` | `[foundation, instructions, workflow, review, runtime, backlog, knowledge]` | Explicit artifact-class composition derived from the chosen preset and overlays |
| `capability_packs` | `[backlogit, agent-engram]` | Which packs to enable |
| `backlog.tool` | `backlogit` | Override backlog tool auto-detection |
| `backlog.suffix_map` | `{feature: "F", chore: "C", task: "T", shipment: "S"}` | Work item type suffixes |
| `docs.root` | `docs` | Where durable knowledge artifacts live |
| `continuous_learning` | `{directory: ".autoharness/continuous-learning"}` | Repo-local observation and learned-artifact settings for the optional continuous-learning pack |
| `model_routing` | `{tier1: "gpt-5.4-mini"}` | Model preferences per tier |
| `overrides` | `{PROJECT_NAME: "my-app"}` | Explicit template variable overrides |

The installer and tuner both read this file. When tuning, changes to `config.yaml` are treated as intentional configuration updates (not drift) and are prioritized in the tuning report.

## Step 3: Register with Your AI Coding Environment

autoharness is environment-agnostic. Register it once in whichever environment(s) you use.

### VS Code with GitHub Copilot

The harness installer writes the agent and prompt discovery settings to your **VS Code user settings** (`%APPDATA%\Code\User\settings.json` on Windows; `~/Library/Application Support/Code/User/settings.json` on macOS; `~/.config/Code/User/settings.json` on Linux). These are user-scoped settings so the Harness Installer agent is available from every workspace, not just the one it was installed into.

After the first-time setup described below, entries like these will be present in your user settings without any manual editing:

```jsonc
// VS Code user settings — written automatically by autoharness install
// The exact path is the output of: autoharness home
{
  "chat.agentFilesLocations":  { "C:\\Users\\you\\AppData\\Roaming\\uv\\tools\\autoharness\\Lib\\site-packages\\autoharness\\data\\.github\\agents":  true },
  "chat.agentSkillsLocations": { "C:\\Users\\you\\AppData\\Roaming\\uv\\tools\\autoharness\\Lib\\site-packages\\autoharness\\data\\.github\\skills":  true },
  "chat.promptFilesLocations": { "C:\\Users\\you\\AppData\\Roaming\\uv\\tools\\autoharness\\Lib\\site-packages\\autoharness\\data\\.github\\prompts": true }
}
```

The installer resolves the path by running `autoharness home` — tilde shorthand (`~`) is not expanded in VS Code JSON settings on Windows and is never used. Existing settings are preserved; only the autoharness-specific entries are added.

Once those settings are in place, the **Harness Installer** agent appears in the **agents dropdown** at the top of the Chat view. Select it there before typing your prompt. The `/install-harness` slash command (from the autoharness prompt file) is also available in chat.

> **First-time setup:** Run this command once after installing autoharness (cwd does not matter):
> ```bash
> autoharness setup-vscode
> ```
> This writes the three `chat.*` entries into your VS Code user settings using the fully-resolved path from `autoharness home`. Then reload the VS Code window (`Ctrl+Shift+P` → **Reload Window**) and the **Harness Installer** agent will appear in the agents dropdown.

### GitHub Copilot CLI — VS Code background sessions

VS Code integrates with the Copilot CLI as **background agent sessions** that run autonomously while you continue other work. VS Code installs and configures the Copilot CLI agent runtime automatically.

For the **Harness Installer** and **Harness Tuner** agents to appear in Copilot CLI sessions, run this command once after installing autoharness:

```bash
autoharness setup-copilot-cli
```

This copies the agent `.md` files and skill `SKILL.md` files from the autoharness installation into your Copilot CLI global config directory (`~/.copilot/agents/` and `~/.copilot/skills/`). Re-run it after upgrading autoharness to pick up updated files.

To run the harness installer as a background session:

1. Open the Chat view (`Ctrl+Alt+I`)
2. Select **Copilot CLI** from the **Session Target** dropdown (or run **Chat: New Copilot CLI** from the Command Palette)
3. Optionally select **Harness Installer** from the **Agents** dropdown in the session (requires `github.copilot.chat.cli.customAgents.enabled` — experimental)
4. Type your install request in the session:

```text
Install a standard harness into this workspace
```

### GitHub Copilot CLI — terminal

VS Code registers a **GitHub Copilot CLI** terminal profile. To open a session:

- Select the **+** dropdown in the Terminal panel and choose **GitHub Copilot CLI**, or
- Run **Terminal: Create New Terminal (With Profile)** from the Command Palette and select **GitHub Copilot CLI**, or
- Type `copilot` in any VS Code integrated terminal

VS Code handles authentication automatically. Once the session is open, type `/install-harness` to run the install prompt, or describe the task naturally.

For standalone Copilot CLI sessions outside VS Code, run `autoharness setup-copilot-cli` first so agents and skills are registered globally, then use the generated `start.ps1` (or `start.sh`) at the workspace root to set workspace-local state before launching.

> **First install (before `start.ps1` exists):** The startup scripts are generated *by* the installer, so they do not exist yet. Use the VS Code terminal approach above — VS Code handles auth. The `start.ps1` / `start.sh` scripts are for subsequent sessions outside VS Code.

### Claude Code

Run once after installing autoharness:

```bash
autoharness setup-claude
```

This copies agent `.md` files into `~/.claude/agents/` and skill `SKILL.md` files into `~/.claude/skills/`. Claude Code discovers agents and skills from those directories at startup. The `CLAUDE_CONFIG_DIR` environment variable overrides the default `~/.claude/` path. Restart Claude Code after running, and again after upgrading autoharness.

### Codex

Run once after installing autoharness:

```bash
autoharness setup-codex
```

This copies skill `SKILL.md` files into `~/.codex/skills/`. Codex uses a unified skills model — the `install-harness` and `tune-harness` skills serve as the agent entry points. The `CODEX_HOME` environment variable overrides the default `~/.codex/` path. Restart Codex after running, and again after upgrading autoharness.

### Startup Scripts

The harness installer generates `start.ps1` (PowerShell) and `start.sh` (bash) at your workspace root. These scripts set workspace-local directories for AI agent state before launching your AI CLI tool:

```powershell
# start.ps1 — generated by autoharness
$env:COPILOT_HOME = ".\.copilot"   # workspace-local Copilot database and memories
$env:GITHUB_TOKEN = (gh auth token)
& "copilot"                        # or the full path configured in .autoharness/config.yaml
```

```bash
# start.sh — generated by autoharness
export COPILOT_HOME="./.copilot"
export GITHUB_TOKEN="$(gh auth token)"
"copilot"
```

By redirecting `COPILOT_HOME` (and optionally `ENGRAM_DATA_DIR` for agent-engram) to a workspace-local directory, the agent's memories, checkpoints, and database are stored inside the project and become visible to git. This keeps agent state isolated per project rather than shared across all workspaces.

Sections for Claude Code and OpenAI Codex are included in each script as commented-out blocks; activate the one you need.

To configure the Copilot CLI path (when it is not on PATH), set it in `.autoharness/config.yaml` before running install or tune:

```yaml
ai_tools:
  copilot_cli:
    exe_path: "C:\\Tools\\ghcpcli\\copilot.exe"   # Windows example
    # exe_path: "/usr/local/bin/copilot"           # macOS/Linux example
```

## Step 4: Install a Harness into a Target Workspace

Open the Chat view in VS Code (`Ctrl+Alt+I`), select **Harness Installer** from the agents dropdown, then describe what you want. Alternatively, type `/install-harness` as a slash command to run the guided install prompt.

### Full Installation (Recommended)

Select the **Harness Installer** agent from the agents dropdown, then ask:

```text
Install a standard harness into this workspace
```

or run the prompt directly:

```text
/install-harness preset=standard
```

The installer will:

1. **Resolve autoharness home** — locate templates and schemas
2. **Discover** the target workspace profile (languages, frameworks, build tools, test runners, CI/CD)
3. **Present** a proposed harness configuration for your review, including stack packs, install layers, and why the preset/packs were recommended
4. **Generate** customized agents, skills, instructions, policies, and constitutional docs
5. **Install** the artifacts into the target workspace
6. **Verify** the installation is coherent and all cross-references resolve

### Preset-Based Installation

Choose the installation shape before fine-tuning primitives manually:

```text
/install-harness preset=starter
/install-harness preset=full capability_packs=agent-intercom,browser-verification,continuous-learning,strict-safety,release-observability,adversarial-review
```

| Preset | Installs | Best For |
|---|---|---|
| `starter` | Core planning, execution, safety, workflow policy, and repository knowledge | First adoption, libraries, smaller repos |
| `standard` | Full 10-primitive harness | Most repos |
| `full` | Full 10-primitive harness plus recommended capability packs | Web apps, services, and higher-operational-maturity teams |

Discovery also proposes additive `stack_packs` and explicit `install_layers` so
the installer can explain why a repo is being treated as a `web-app`,
`api-service`, `mcp-server`, `library`, or similar shape, and which artifact
classes (`foundation`, `review`, `runtime`, `overlays`, and so on) should be
present in the final harness.

### Capability Packs

Capability packs deepen the harness without redefining the primitive model:

| Pack | Adds |
|---|---|
| `agent-intercom` | Remote operator visibility, heartbeat, approval routing, and steering guidance woven through the installed harness |
| `agent-engram` | Engram-first indexed search, code graph lookup, workspace binding, and query-driven context retrieval woven through analysis-heavy workflows |
| `backlogit` | backlogit-native query, queue, dependency, memory, checkpoint, comment, and commit-trace guidance layered over generic backlog integration |
| `browser-verification` | Browser-aware runtime verification and closure guidance for web UIs |
| `continuous-learning` | Observation capture, instinct formation, and promotion into explicit learned instructions or skills |
| `strict-safety` | Stronger default use of careful / freeze-scope / investigate-first modes plus explicit `ProposedAction` / `ActionRisk` / `ActionResult` tracking |
| `release-observability` | Richer operational closure and monitoring artifacts |
| `adversarial-review` | Multi-model consensus review and escalation for higher-confidence review gates |

`agent-intercom` is intentionally different from a narrow add-on. When enabled, autoharness should thread its workflow expectations into `AGENTS.md`, `copilot-instructions.md`, intercom-specific instructions, pipeline agents, long-running skills, and heartbeat prompts so operator visibility and approval routing become part of the normal harness behavior.

`agent-engram` is also an overlay rather than a single search toggle. When enabled, autoharness should keep the generic search guidance in place while additionally teaching the harness to use Engram's higher-leverage indexed capabilities such as unified search, code graph lookup, workspace memory queries, lifecycle checks, and index freshness workflows.

`backlogit` is also an overlay rather than a simple tool toggle. When enabled, autoharness should keep the generic backlog abstraction in place while additionally teaching the harness to use backlogit's higher-leverage features such as SQL query access, prioritized queue retrieval, dependency traversal, agent memory, checkpoints, comments, and commit traceability.

`browser-verification` is also an overlay rather than a one-off test note. When enabled, autoharness should teach the harness to verify server readiness, choose headed vs headless runs deliberately, select routes from changed surfaces, and record human checkpoints for external flows.

`continuous-learning` is also an overlay rather than a hidden prompt behavior. When enabled, autoharness should install an explicit observation lifecycle (`observe`, `learn`, `evolve`) and persist recurring-practice state under `.autoharness/continuous-learning/`.

`strict-safety` is also an overlay rather than a generic caution toggle. When
enabled, autoharness should install explicit action-risk/result guidance and
keep risky planning, review, verification, and closure states legible instead
of leaving them implicit.

Use [Backlogit Operating Model](backlogit-operating-model.md) as the contract for
what `autoharness` should consume today. If backlogit evolves a new internal
workflow, promote only the validated external contract into `autoharness`, not
the in-progress implementation details.

All packs follow the formal overlay pattern documented in [Capability Packs](capability-packs.md). Packs are applied after the base primitive composition is chosen and before installation verification completes.

Separately, discovery may recommend the `agent-native-parity-reviewer` persona
when the workspace exposes MCP-heavy or agent-facing product surfaces that need
user/agent parity review.

### Selective Installation

Install only specific primitives:

```text
/install-harness primitives=1,4,5,8,10
```

**Primitive numbers:**

1. State & Context Management
2. Task Granularity & Horizon Scoping
3. Model Routing & Escalation
4. Orchestration & Delegation
5. Tool Execution & Guardrails
6. Injection Points & Dynamic Reminders
7. Observability & Evaluation
8. Workflow Policy
9. Repository Knowledge & Agent Legibility
10. Operational Closure & Feedback

### Dry Run (Preview)

Generate artifacts to a staging directory without installing:

```text
/install-harness dry_run=true
```

## What Gets Installed in the Target

The target workspace receives only generated harness artifacts:

```text
target-workspace/
  AGENTS.md                              # Root agent instructions (adapted to tech stack)
  .github/
    copilot-instructions.md              # Shared development guidelines
    agents/                              # Agent definitions
      stage.agent.md
      ship.agent.md
      prompt-builder.agent.md
      {language}-engineer.agent.md       # Technology-specific expert
      deprecated/                        # Superseded agents kept for reference
      review/                            # Review personas
        architecture-strategist.agent.md
        constitution-reviewer.agent.md
        scope-boundary-auditor.agent.md
        {language}-reviewer.agent.md     # Technology-specific reviewer
        concurrency-reviewer.agent.md    # If applicable
      research/
        learnings-researcher.agent.md
    skills/
      deliberate/SKILL.md
      spike/SKILL.md
      build-feature/SKILL.md
      compact-context/SKILL.md
      compound/SKILL.md
      compound-refresh/SKILL.md
      fix-ci/SKILL.md
      harness-architect/SKILL.md
      harvest/SKILL.md
      impl-plan/SKILL.md
      plan-harden/SKILL.md
      operational-closure/SKILL.md
      plan-review/SKILL.md
      pr-lifecycle/SKILL.md
      review/SKILL.md
      runtime-verification/SKILL.md
      safety-modes/SKILL.md
      observe/SKILL.md                    # Optional: continuous-learning pack
      learn/SKILL.md                      # Optional: continuous-learning pack
      evolve/SKILL.md                     # Optional: continuous-learning pack
    instructions/
      constitution.instructions.md
      {language}.instructions.md          # Language-specific conventions
      commit-message.instructions.md      # Conventional commits scoping
      markdown.instructions.md            # Markdown conventions
      writing-style.instructions.md       # Prose style rules
      git-merge.instructions.md           # Merge practices
      pull-request.instructions.md        # PR conventions
      prompt-builder.instructions.md      # Prompt authoring conventions
      architecture-doc.instructions.md    # Architecture documentation rules
      ci-security.instructions.md         # CI/CD security (when CI detected)
      workflows.instructions.md           # CI/CD workflow structure (when CI detected)
      mcp-server.instructions.md          # MCP server conventions (when MCP detected)
      backlog-integration.instructions.md # Backlog tool mapping (when backlog detected)
      agent-intercom.instructions.md      # Optional: agent-intercom pack
      agent-engram.instructions.md        # Optional: agent-engram pack
      backlogit.instructions.md           # Optional: backlogit pack
      browser-verification.instructions.md # Optional: browser-verification pack
      continuous-learning.instructions.md # Optional: continuous-learning pack
      strict-safety.instructions.md       # Optional: strict-safety pack
      release-observability.instructions.md # Optional: release-observability pack
      adversarial-review.instructions.md  # Optional: adversarial-review pack
    policies/
      workflow-policies.md
    prompts/
      ping-loop.prompt.md
  .backlog/
    config.yml
    queue/
      .stash.md
    archive/
  docs/
    compound/
    plans/
    decisions/
    memory/
    closure/
  .autoharness/
    config.yaml                          # Operator configuration (optional, created before install)
    workspace-profile.yaml               # Discovered workspace profile
    harness-manifest.yaml                # Installation tracking (includes autoharness_home)
```

**Not installed in the target**: autoharness templates, schemas, installer/tuner agents, documentation, or any engine files.

### Review Personas

Review personas are specialized subagents spawned by the `review` and
`plan-review` skills. They are not invoked directly.

**Always-on (every review)**:

| Persona | Focus |
|---|---|
| Constitution Reviewer | Map changes against constitutional principles |
| {Language} Reviewer | Language-specific safety, correctness, and idiom checks |
| Learnings Researcher | Search compound library for related past issues |

**Conditional (activated by diff content)**:

| Persona | Trigger | Focus |
|---|---|---|
| Architecture Strategist | Module boundaries, dependency changes | Cohesion, coupling, layering |
| Concurrency Reviewer | Concurrent/async patterns (if applicable) | Race conditions, deadlocks |
| Scope Boundary Auditor | Changes spanning multiple domains | Scope creep, YAGNI |
| Agent-Native Parity Reviewer | MCP tools, agent-facing actions | User/agent workflow symmetry |

Cross-model diversity is preferred (different models for different personas)
but not blocking.

### Support Agents

| Agent | Purpose |
|---|---|
| `{language}-engineer.agent.md` | Technology-specific implementation expert |
| `prompt-builder.agent.md` | Prompt authoring assistant |
| `learnings-researcher.agent.md` | Compound library search and retrieval |

## Post-Installation

### Verify the Installation

The installer runs automatic verification. You can also manually check:

1. Open any installed `.agent.md` file and verify it references correct paths
2. Check that the constitution mentions your project's technology stack
3. Verify `AGENTS.md` has the correct build/test/lint commands
4. Confirm instruction file `applyTo` patterns match your file extensions
5. Confirm the selected preset and capability packs are recorded in `.autoharness/harness-manifest.yaml`
6. Ensure no `{{VARIABLE}}` placeholders remain in any generated file
7. If `agent-intercom` is enabled, verify `.github/instructions/agent-intercom.instructions.md` exists and the installed agents/skills reference intercom heartbeat, broadcast, and approval usage where expected
8. If `agent-engram` is enabled, verify `.github/instructions/agent-engram.instructions.md` exists and the installed agents/skills reference engram-first search, workspace binding, or indexed-fallback behaviors where expected
9. If `backlogit` is enabled, verify `.github/instructions/backlogit.instructions.md` exists and the installed agents reference backlogit query / queue / memory / traceability behaviors where expected

### First Use

1. Select the **Stage** agent from the agents dropdown and describe your feature or chore idea
2. The stage agent determines whether this needs a decision (deliberate) or investigation (spike)
3. Review the decision or findings artifact and promote to a plan or queue
4. If promoted to plan, the stage agent decomposes it into tasks via the harvest skill
5. Select the **Ship** agent from the agents dropdown to implement the feature or chore
6. The ship agent handles harness generation, build, review, CI, and PR lifecycle
7. If the feature or chore changes runtime behavior, ship runs `runtime-verification`
8. Ship captures release readiness and follow-up monitoring with `operational-closure`
9. After merge, ship can invoke `compound-refresh` when shipped work supersedes, duplicates, or invalidates existing learnings in `docs/compound/`
10. If the workspace enabled `agent-intercom`, confirm the server is reachable before relying on remote approval or operator steering flows
11. If the workspace enabled `agent-engram`, confirm the engram MCP / daemon path is reachable and the workspace is bound (or auto-bound) before relying on indexed search results
12. If the workspace enabled `backlogit`, confirm the backlogit MCP or CLI path is available before relying on queue, SQL query, or checkpoint workflows

### Ongoing Maintenance

Run the tuner from the global autoharness installation against the target workspace. Select the **Harness Tuner** agent from the agents dropdown, or run the prompt:

```text
/tune-harness
```

The tuner reads updated templates from the global installation, re-runs
workspace discovery, and compares manifest-tracked artifact checksums to the
installed harness. Use `.autoharness/drift-ignore` for intentional local
customizations you do not want surfaced as drift.

Recommended tuning schedule:

* After every major release
* After adding new languages or frameworks
* After changing CI/CD pipelines
* Monthly for actively developed projects

## Updating autoharness Itself

To get new templates, improved agents, and updated schemas:

```bash
# If installed with uv
uv tool upgrade autoharness

# If installed with git clone
cd ~/.autoharness && git pull
```

Existing target workspace harnesses are not affected until you run the tuner against them. The tuner will detect template improvements and propose updates.
