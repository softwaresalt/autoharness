---
title: Installation Guide
description: Step-by-step guide for installing an agent harness into a target workspace
---

## Prerequisites

* VS Code with GitHub Copilot Chat enabled
* autoharness repository available in a multi-root workspace alongside the target workspace
* The target workspace should be a Git repository with at least basic project structure

## Installation Methods

### Method 1: Prompt-Based (Recommended)

Open the target workspace alongside autoharness in a multi-root VS Code workspace.

1. Open Copilot Chat
2. Use the install prompt: `@harness-installer Install a harness for this workspace`
3. Follow the interactive workflow:
   * Confirm the target workspace
   * Review the discovered profile
   * Approve the installation plan
   * Verify the installed artifacts

### Method 2: Agent-Based (Programmatic)

Invoke the harness-installer agent directly with specific parameters:

```text
@harness-installer workspace=/path/to/target primitives=1,2,3,4,5,6,7,8
```

### Method 3: Selective Installation

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

## What Gets Installed

### Directory Structure

```text
target-workspace/
  AGENTS.md                              # Root agent instructions
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
    harness-manifest.yaml                # Installation tracking
```

## Post-Installation

### Verify the Installation

The installer runs automatic verification. You can also manually check:

1. Open any installed `.agent.md` file and verify it references correct paths
2. Check that the constitution mentions your project's technology stack
3. Verify `AGENTS.md` has the correct build/test/lint commands
4. Confirm instruction file `applyTo` patterns match your file extensions

### First Use

1. Create a feature idea in `.backlog/brainstorm/my-feature.md`
2. Invoke the backlog-harvester: `@backlog-harvester source=.backlog/brainstorm/my-feature.md`
3. Review the generated plan and task decomposition
4. Invoke the harness-architect for the feature
5. Invoke the build-orchestrator to implement

### Ongoing Maintenance

Run the tuner periodically:

```text
@harness-tuner Tune the harness for current workspace state
```

Recommended tuning schedule:

* After every major release
* After adding new languages or frameworks
* After changing CI/CD pipelines
* Monthly for actively developed projects
