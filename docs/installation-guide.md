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

Clone the repository to your preferred global location:

```bash
git clone https://github.com/softwaresalt/autoharness.git ~/.autoharness
```

Or use a custom location and set the environment variable:

```bash
git clone https://github.com/softwaresalt/autoharness.git ~/tools/autoharness
export AUTOHARNESS_HOME=~/tools/autoharness   # bash/zsh
$env:AUTOHARNESS_HOME = "$HOME\tools\autoharness"  # PowerShell
```

The `autoharness_home` path is resolved by agents in this order:

1. `AUTOHARNESS_HOME` environment variable
2. Directory traversal from the agent definition file
3. `~/.autoharness/` default

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
@harness-installer workspace=/path/to/target
```

The installer will:

1. **Resolve autoharness home** — locate templates and schemas
2. **Discover** the target workspace profile (languages, frameworks, build tools, test runners, CI/CD)
3. **Present** a proposed harness configuration for your review
4. **Generate** customized agents, skills, instructions, policies, and constitutional docs
5. **Install** the artifacts into the target workspace
6. **Verify** the installation is coherent and all cross-references resolve

### Selective Installation

Install only specific primitives:

```text
@harness-installer workspace=/path/to/target primitives=1,4,5,8
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
      brainstorm/SKILL.md
      build-feature/SKILL.md
      compact-context/SKILL.md
      compound/SKILL.md
      fix-ci/SKILL.md
      impl-plan/SKILL.md
      plan-review/SKILL.md
      review/SKILL.md
    instructions/
      constitution.instructions.md
      {language}.instructions.md
      commit-message.instructions.md
      markdown.instructions.md
      writing-style.instructions.md
      git-merge.instructions.md
      pull-request.instructions.md
      prompt-builder.instructions.md
    policies/
      workflow-policies.md
    prompts/
      ping-loop.prompt.md
  .backlog/
    config.yml
    queue.md
    tasks/
    plans/
    brainstorm/
    compound/
    reviews/
    memory/
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
5. Ensure no `{{VARIABLE}}` placeholders remain in any generated file

### First Use

1. Create a feature idea in `.backlog/brainstorm/my-feature.md`
2. Invoke the backlog-harvester: `@backlog-harvester source=.backlog/brainstorm/my-feature.md`
3. Review the generated plan and task decomposition
4. Invoke the harness-architect for the feature
5. Invoke the build-orchestrator to implement

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
cd ~/.autoharness
git pull
```

Existing target workspace harnesses are not affected until you run the tuner against them. The tuner will detect template improvements and propose updates.
