---
title: autoharness Agent Instructions
description: Authoritative rules for all agents operating in the autoharness repository
doc_type: guide
source: AGENTS.md
---

# Agent Instructions

This file defines the authoritative rules for working in the autoharness repository.

## Core Rules

1. **Global tool, local output.** autoharness is installed globally and operated against target workspaces. Templates are read from `autoharness_home`; only generated artifacts are written to the target. Never mix autoharness engine files with target workspace output.

2. **Templates are the product.** This project produces template files, not application code. All templates must be technology-agnostic with `{{VARIABLE}}` placeholders for customization points.

3. **Environment agnostic.** All agents, skills, and generated artifacts must work across VS Code with GitHub Copilot, GitHub Copilot CLI, Codex, Cursor, Claude Code, and any environment supporting agent conventions. Do not use environment-specific APIs or assume a specific IDE.

4. **Discovery before generation.** Never generate harness artifacts without first running workspace discovery. The workspace profile drives all template composition.

5. **Verify after installation.** Every installation must end with a verification pass that confirms no unresolved template variables remain, all cross-references resolve, and multi-model adversarial review confirms template fidelity, overlay coherence, and cross-reference integrity.

6. **Preserve existing work.** When installing into a workspace that already has harness artifacts, back up originals before overwriting. Offer merge install as an alternative.

7. **Tuning is non-destructive.** The tuner proposes changes for review. Auto-apply is opt-in, not default. Backups are mandatory before any modification.

## Quality Gates

```text
# All template files must have valid YAML frontmatter
# All Markdown must pass markdownlint heading hierarchy rules (MD001, MD025, MD041) — P-008
# No {{VARIABLE}} placeholders may remain in installed output
# All cross-references between installed artifacts must resolve
# All PR merges must use merge commits — squash and rebase are forbidden (P-009, Principle XI)
# When both stage and ship agents are installed (two-agent model), both must declare Role Boundary tables — P-010
# Agents must not work across parallel implementation branches or worktrees — P-016
# Dark factory mode must be explicit, bounded, local-review-first, telemetry-visible, and policy-preserving — P-017
```

## Development Workflow

1. Identify the template to create or modify
2. Ensure the template works for at least 3 different technology profiles
3. Update the variable resolution table in install-harness SKILL.md
4. Test the template produces valid output when all variables are resolved
5. Keep one active implementation branch/worktree; only explicit Stage spike/research worktrees are exempt, and they cannot perform implementation, template/source/config mutation, shipment claim, PR preparation, or Ship execution (P-016)
6. Use dark factory mode only through the exact P-017 trigger (`Run pipeline in dark mode`) or its prompt shim (`/feature-flow-dark`); preserve P-001, P-009, P-014, P-016, local review readiness, CI/check handling, telemetry events, and post-merge closure

## Available Agents

| Agent | Purpose |
|---|---|
| `auto-mergeinstall` | Discover workspace and install a customized harness |
| `auto-tune` | Detect drift and propose harness updates |

## Available Skills

| Skill | Purpose |
|---|---|
| `workspace-discovery` | Scan target workspace and produce a profile |
| `install-harness` | Compose and install harness from templates |
| `tune-harness` | Detect drift and propose updates |
| `verify-harness` | Multi-model adversarial verification of installed artifacts |
| `doc-review` | Documentation quality review: cross-reference integrity, frontmatter, markdown structure, template variable drift; supports alternate model provider |

## Enabled Capability Packs

This dogfood harness has the following capability packs enabled. Each is woven through the workflow per its overlay instruction — see the linked file and the overlay blocks in `.github/copilot-instructions.md`. This is a pointer, not a manual.

| Pack | Overlay Reference |
|---|---|
| `agent-intercom` | `.github/instructions/agent-intercom.instructions.md` |
| `backlogit` | `.autoharness/backlog-registry.yaml` |
| `agent-engram` | `.github/instructions/agent-engram.instructions.md` |
| `graphtor-docs` | `.github/instructions/graphtor-docs.instructions.md` |
