---
title: autoharness Agent Instructions
description: Authoritative rules for all agents operating in the autoharness repository
---

# Agent Instructions

This file defines the authoritative rules for working in the autoharness repository.

## Core Rules

1. **Templates are the product.** This project produces template files, not application code. All templates must be technology-agnostic with `{{VARIABLE}}` placeholders for customization points.

2. **Discovery before generation.** Never generate harness artifacts without first running workspace discovery. The workspace profile drives all template composition.

3. **Verify after installation.** Every installation must end with a verification pass that confirms no unresolved template variables remain and all cross-references resolve.

4. **Preserve existing work.** When installing into a workspace that already has harness artifacts, back up originals before overwriting. Offer merge install as an alternative.

5. **Tuning is non-destructive.** The tuner proposes changes for review. Auto-apply is opt-in, not default. Backups are mandatory before any modification.

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
