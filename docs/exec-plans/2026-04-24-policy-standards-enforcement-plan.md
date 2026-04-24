# Policy & Standards Enforcement — Implementation Plan

**Date**: 2026-04-24
**Source stash entries**: `F4373F02` (markdownlint), `3ABAEF80` (git merge policy)
**Covering feature**: Policy & Standards Enforcement
**Risk level**: Moderate — additive changes to foundation templates
**Requires plan hardening**: no

---

## Objective

Introduce two new standards enforcement mechanisms into the autoharness template system:

1. **Markdown heading hierarchy enforcement** via markdownlint-cli with pre-commit hooks
2. **Git merge-commit-only policy** forbidding squash merge at multiple enforcement layers

Both follow the same enforcement pattern: workflow policy → constitution/foundation → generated config/hooks → agent guardrails → install/tune verification.

## Sub-Epic 1: Markdownlint Heading Hierarchy Enforcement

### Task 1.1: Create markdownlint config template

**Files**: `templates/scripts/.markdownlint.json.tmpl` (new)
**Scope**: Generate a `.markdownlint.json` config enforcing:

- MD001 (heading increment — no skipped levels)
- MD025 (single H1 per file)
- MD041 (first line in file should be a top-level heading)

**Acceptance**: Template resolves to valid JSON with no `{{...}}` placeholders remaining.

### Task 1.2: Create pre-commit hook template for markdownlint

**Files**: `templates/scripts/pre-commit-markdownlint.sh.tmpl` (new), `templates/scripts/pre-commit-markdownlint.ps1.tmpl` (new)
**Scope**: Generate pre-commit hooks (bash + PowerShell) that run `markdownlint` on staged `.md` files and exit non-zero on violations. The hook must be environment-agnostic (work in any git environment with markdownlint-cli installed).
**Acceptance**: Hook scripts lint only staged Markdown files; non-zero exit on violation.

### Task 1.3: Add markdownlint-cli detection to workspace discovery

**Files**: `.github/skills/workspace-discovery/SKILL.md`
**Scope**: Add markdownlint-cli to the list of detected tools during workspace discovery. Record presence/absence in the workspace profile under a `tools.markdownlint` field.
**Acceptance**: Workspace discovery detects markdownlint-cli when installed and records it in the profile.

### Task 1.4: Add P-008 Markdown Conformance policy

**Files**: `templates/policies/workflow-policies.md.tmpl`
**Scope**: New P-008 policy entry requiring all generated and committed Markdown files to pass markdownlint heading hierarchy rules. Gate point: Ship pre-commit (Step 5). Violation action: halt and fix.
**Acceptance**: P-008 section present in template with proper field table, statement, pre/postconditions, and violation action. Amendment log row added.

### Task 1.5: Register markdownlint templates in install-harness

**Files**: `.github/skills/install-harness/SKILL.md`
**Scope**: Add `.markdownlint.json` config and pre-commit hook scripts to the installation workflow. Conditional on markdownlint-cli detection or operator opt-in. Add verification step confirming config was installed.
**Acceptance**: Install-harness references the new templates and includes a verification checkpoint.

### Task 1.6: Add markdownlint verification to tune-harness

**Files**: `.github/skills/tune-harness/SKILL.md`
**Scope**: Add a drift check for `.markdownlint.json` presence and config correctness. Flag if config is missing or rules have been weakened.
**Acceptance**: Tune-harness detects missing or weakened markdownlint config.

## Sub-Epic 2: Git Merge-Commit-Only Policy

### Task 2.1: Add Constitution principle for merge commit history preservation

**Files**: `templates/foundation/constitution.instructions.md.tmpl`
**Scope**: New principle (after current VIII or as IX): "Merge Commit History Preservation (NON-NEGOTIABLE)" — all merges must use merge commits; squash merge is forbidden. Rationale: merge commits preserve full development history, individual commit attribution, and bisect-friendly history.
**Acceptance**: New principle present in constitution template with rationale block.

### Task 2.2: Add P-009 Merge-Commit-Only policy

**Files**: `templates/policies/workflow-policies.md.tmpl`
**Scope**: New P-009 policy entry forbidding squash merge. Applies to `ship`. Gate point: Ship Step 5 pre-merge. Precondition: merge strategy is `merge commit` (not squash or rebase). Violation action: halt, do not merge.
**Acceptance**: P-009 section present with proper field table and amendment log row.

### Task 2.3: Add pre-merge guardrail in Ship agent template

**Files**: `templates/agents/ship.agent.md.tmpl`
**Scope**: Insert a verification step before any merge operation in Ship's PR lifecycle that checks the merge strategy is set to merge-commit. If squash merge is detected (e.g., via GitHub API or PR settings), halt and report a P-009 violation.
**Acceptance**: Ship agent template contains pre-merge strategy check referencing P-009.

### Task 2.4: Create GitHub repo settings recommendation template

**Files**: `templates/instructions/git-merge.instructions.md.tmpl` (update existing if present)
**Scope**: Update the git-merge instructions template to include explicit recommendation to disable squash merge in GitHub repository settings. Include the specific GitHub settings path and the rationale.
**Acceptance**: git-merge instructions template includes squash-merge-disable recommendation.

### Task 2.5: Register merge policy in install-harness

**Files**: `.github/skills/install-harness/SKILL.md`
**Scope**: Ensure install-harness references the updated constitution principle and P-009 policy. Add verification check confirming merge policy is documented.
**Acceptance**: Install-harness includes merge policy in its verification checklist.

## Dependency Graph

```text
Sub-Epic 1 (Markdownlint):
  1.1 (.markdownlint.json.tmpl)
    → 1.2 (pre-commit hooks) [depends: config exists]
    → 1.4 (P-008 policy) [independent]
  1.3 (workspace discovery) [independent]
  1.5 (install-harness) [depends: 1.1, 1.2, 1.4]
  1.6 (tune-harness) [depends: 1.1]

Sub-Epic 2 (Git Merge Policy):
  2.1 (constitution principle) [independent]
  2.2 (P-009 policy) [independent]
  2.3 (ship guardrail) [depends: 2.2]
  2.4 (git-merge instructions) [independent]
  2.5 (install-harness) [depends: 2.1, 2.2]

Cross-epic: 1.5 and 2.5 both touch install-harness — execute 2.5 after 1.5 to avoid conflict.
```

## Execution Order

1. 1.1, 1.3, 1.4, 2.1, 2.2, 2.4 (all independent — can execute in parallel)
2. 1.2 (after 1.1)
3. 2.3 (after 2.2)
4. 1.5 (after 1.1, 1.2, 1.4)
5. 1.6 (after 1.1)
6. 2.5 (after 2.1, 2.2, and after 1.5 to avoid install-harness conflict)

## Estimated Scope

11 tasks × 2 hours = ~22 hours human-equivalent effort
