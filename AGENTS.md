---
title: autoharness Agent Instructions
description: Authoritative rules for all agents operating in the autoharness repository
---

# Agent Instructions

This file defines the authoritative rules for working in the autoharness repository.

## Core Rules

1. **Global tool, local output.** autoharness is installed globally and operated against target workspaces. Templates are read from `autoharness_home`; only generated artifacts are written to the target. Never mix autoharness engine files with target workspace output.

2. **Templates are the product.** This project produces template files, not application code. All templates must be technology-agnostic with `{{VARIABLE}}` placeholders for customization points.

3. **Environment agnostic.** All agents, skills, and generated artifacts must work across VS Code with GitHub Copilot, GitHub Copilot CLI, Codex, Cursor, Claude Code, and any environment supporting agent conventions. Do not use environment-specific APIs or assume a specific IDE.

4. **Discovery before generation.** Never generate harness artifacts without first running workspace discovery. The workspace profile drives all template composition.

5. **Verify after installation.** Every installation must end with a verification pass that confirms no unresolved template variables remain and all cross-references resolve.

6. **Preserve existing work.** When installing into a workspace that already has harness artifacts, back up originals before overwriting. Offer merge install as an alternative.

7. **Tuning is non-destructive.** The tuner proposes changes for review. Auto-apply is opt-in, not default. Backups are mandatory before any modification.

## Quality Gates

```text
# All template files must have valid YAML frontmatter
# All Markdown must pass structural checks
# No {{VARIABLE}} placeholders may remain in installed output
# All cross-references between installed artifacts must resolve
```

## Development Workflow

1. Identify the template to create or modify
2. Ensure the template works for at least 3 different technology profiles
3. Update the variable resolution table in install-harness SKILL.md
4. Test the template produces valid output when all variables are resolved

## Available Agents

| Agent | Purpose |
|---|---|
| `harness-installer` | Discover workspace and install a customized harness |
| `harness-tuner` | Detect drift and propose harness updates |

## Available Skills

| Skill | Purpose |
|---|---|
| `workspace-discovery` | Scan target workspace and produce a profile |
| `install-harness` | Compose and install harness from templates |
| `tune-harness` | Detect drift and propose updates |
