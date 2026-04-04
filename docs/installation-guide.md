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

## Step 2: Register with Your AI Coding Environment

autoharness is environment-agnostic. Register it once in whichever environment(s) you use.

### VS Code with GitHub Copilot

Add autoharness as a workspace folder in a multi-root workspace alongside your target project. The agents, skills, and prompts are automatically discovered from the `.github/` directory.

Alternatively, reference it in your VS Code settings:

```jsonc
// .vscode/settings.json (in your target workspace)
{
  "github.copilot.chat.agentWorkspaceFolders": ["~/.autoharness"]
}
```

### GitHub Copilot CLI

Invoke with the workspace argument:

```bash
ghcp agent @harness-installer workspace=/path/to/target
```

### Claude Code

Reference the autoharness agent directly:

```bash
claude --agent ~/.autoharness/.github/agents/harness-installer.agent.md
```

### Cursor

Add autoharness as an agent source in Cursor settings, pointing to `~/.autoharness/.github/agents/`.

### Codex

Reference the autoharness agents directory or pass the AGENTS.md as system context.

## Step 3: Install a Harness into a Target Workspace

### Full Installation (Recommended)

```text
@harness-installer workspace=/path/to/target preset=standard
```

The installer will:

1. **Resolve autoharness home** — locate templates and schemas
2. **Discover** the target workspace profile (languages, frameworks, build tools, test runners, CI/CD)
3. **Present** a proposed harness configuration for your review
4. **Generate** customized agents, skills, instructions, policies, and constitutional docs
5. **Install** the artifacts into the target workspace
6. **Verify** the installation is coherent and all cross-references resolve

### Preset-Based Installation

Choose the installation shape before fine-tuning primitives manually:

```text
@harness-installer workspace=/path/to/target preset=starter
@harness-installer workspace=/path/to/target preset=full capability_packs=agent-intercom,browser-verification,release-observability
```

| Preset | Installs | Best For |
|---|---|---|
| `starter` | Core planning, execution, safety, workflow policy, and repository knowledge | First adoption, libraries, smaller repos |
| `standard` | Full 10-primitive harness | Most repos |
| `full` | Full 10-primitive harness plus recommended capability packs | Web apps, services, and higher-operational-maturity teams |

### Capability Packs

Capability packs deepen the harness without redefining the primitive model:

| Pack | Adds |
|---|---|
| `agent-intercom` | Remote operator visibility, heartbeat, approval routing, and steering guidance woven through the installed harness |
| `agent-engram` | Engram-first indexed search, code graph lookup, workspace binding, and query-driven context retrieval woven through analysis-heavy workflows |
| `backlogit` | backlogit-native query, queue, dependency, memory, checkpoint, comment, and commit-trace guidance layered over generic backlog integration |
| `browser-verification` | Browser-aware runtime verification guidance for web UIs |
| `strict-safety` | Stronger default use of careful / freeze-scope / investigate-first modes |
| `release-observability` | Richer operational closure and monitoring artifacts |

`agent-intercom` is intentionally different from a narrow add-on. When enabled, autoharness should thread its workflow expectations into `AGENTS.md`, `copilot-instructions.md`, intercom-specific instructions, pipeline agents, long-running skills, and heartbeat prompts so operator visibility and approval routing become part of the normal harness behavior.

`agent-engram` is also an overlay rather than a single search toggle. When enabled, autoharness should keep the generic search guidance in place while additionally teaching the harness to use Engram's higher-leverage indexed capabilities such as unified search, code graph lookup, workspace memory queries, lifecycle checks, and index freshness workflows.

`backlogit` is also an overlay rather than a simple tool toggle. When enabled, autoharness should keep the generic backlog abstraction in place while additionally teaching the harness to use backlogit's higher-leverage features such as SQL query access, prioritized queue retrieval, dependency traversal, agent memory, checkpoints, comments, and commit traceability.

All packs follow the formal overlay pattern documented in [Capability Packs](capability-packs.md). Packs are applied after the base primitive composition is chosen and before installation verification completes.

### Selective Installation

Install only specific primitives:

```text
@harness-installer workspace=/path/to/target primitives=1,4,5,8,10
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
@harness-installer workspace=/path/to/target dry_run=true
```

## What Gets Installed in the Target

The target workspace receives only generated harness artifacts:

```text
target-workspace/
  AGENTS.md                              # Root agent instructions (adapted to tech stack)
  .github/
    copilot-instructions.md              # Shared development guidelines
    agents/                              # Agent definitions
      deliberator.agent.md
      backlog-harvester.agent.md
      build-orchestrator.agent.md
      harness-architect.agent.md
      pr-review.agent.md
      memory.agent.md
      doc-ops.agent.md
      prompt-builder.agent.md
      {language}-engineer.agent.md       # Technology-specific expert
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
      fix-ci/SKILL.md
      impl-plan/SKILL.md
      operational-closure/SKILL.md
      plan-review/SKILL.md
      review/SKILL.md
      runtime-verification/SKILL.md
      safety-modes/SKILL.md
    instructions/
      constitution.instructions.md
      agent-intercom.instructions.md      # Optional: installed when the pack is enabled
      agent-engram.instructions.md        # Optional: installed when the agent-engram pack is enabled
      backlogit.instructions.md           # Optional: installed when the backlogit pack is enabled
      {language}.instructions.md
      commit-message.instructions.md
      markdown.instructions.md
      writing-style.instructions.md
      git-merge.instructions.md
      pull-request.instructions.md
      prompt-builder.instructions.md
      architecture-doc.instructions.md
    policies/
      workflow-policies.md
    prompts/
      ping-loop.prompt.md
  .backlog/
    config.yml
    queue/
      queue.md
    tasks/
    plans/
    deliberate/
    spike/
    compound/
    reviews/
    memory/
    closure/
    completed/
  .autoharness/
    workspace-profile.yaml               # Discovered workspace profile
    harness-manifest.yaml                # Installation tracking (includes autoharness_home)
```

**Not installed in the target**: autoharness templates, schemas, installer/tuner agents, documentation, or any engine files.

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

1. Invoke the deliberator: `@deliberator topic="my feature idea"`
2. The deliberator determines whether this needs a decision (deliberate) or investigation (spike)
3. Review the decision or findings artifact and promote to a plan or queue
4. If promoted to plan, the backlog-harvester decomposes it into tasks
4. Invoke the harness-architect for the feature
5. Invoke the build-orchestrator to implement
6. If the feature changes runtime behavior, run `runtime-verification`
7. Capture release readiness and follow-up monitoring with `operational-closure`
8. If the workspace enabled `agent-intercom`, confirm the server is reachable before relying on remote approval or operator steering flows
9. If the workspace enabled `agent-engram`, confirm the engram MCP / daemon path is reachable and the workspace is bound (or auto-bound) before relying on indexed search results
10. If the workspace enabled `backlogit`, confirm the backlogit MCP or CLI path is available before relying on queue, SQL query, or checkpoint workflows

### Ongoing Maintenance

Run the tuner from the global autoharness installation against the target workspace:

```text
@harness-tuner workspace=/path/to/target
```

The tuner reads updated templates from the global installation and proposes changes to the target workspace's harness artifacts.

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
