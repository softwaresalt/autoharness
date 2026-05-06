# Browser Automation & Iterative Experimentation Skills - Implementation Plan

**Date**: 2026-05-05
**Source stash entries**: `759380C6` (agent-browser skill), `F6794713` (autoresearch)
**Covering feature**: Browser & Experimentation Skill Templates
**Risk level**: Low - additive skill templates only
**Requires plan hardening**: no

---

## Objective

Add two new optional skill templates that expand autoharness's leaf skill catalog:

1. **Browser automation skill** - strengthens the existing `browser-verification`
   capability pack with concrete browser interaction recipes
2. **Iterative experimentation skill** - adds an autonomous goal->measure->keep/revert
   experimentation loop for performance tuning and optimization tasks

Both are pure template additions with no schema, CLI, or foundation changes.

## Source Material

- `atv-starterkit/.github/skills/agent-browser/SKILL.md` (with references/ and templates/)
- `atv-starterkit/pkg/scaffold/templates/skills/autoresearch/SKILL.md`

---

## Task 1: Create browser-automation skill template

**Files**: `templates/skills/browser-automation/SKILL.md.tmpl` (new)
**Scope**: Create a browser automation skill template providing concrete recipes
for agent-driven browser interaction. The skill covers:

- Core workflow pattern: navigate -> snapshot -> interact -> re-snapshot
- Authentication handling (state import, explicit login, token-based)
- Form automation patterns
- Screenshot and visual verification
- Session management
- Human verification checkpoints for OAuth, payments, external flows

Design requirements:

- Uses `{{BROWSER_CLI}}` for tool-agnostic browser CLI reference
- Uses `{{BROWSER_HEADLESS_FLAG}}` for headless/headed mode
- Integrates with `browser-verification` capability pack overlay targets
- Environment-agnostic: no hardcoded tool names
- References: may include a `references/` subdirectory for auth patterns

**Acceptance**: Template produces coherent browser automation workflow when
variables resolved. Valid YAML frontmatter.

## Task 2: Create iterative-experiment skill template

**Files**: `templates/skills/iterative-experiment/SKILL.md.tmpl` (new)
**Scope**: Create an autonomous experimentation skill template. The skill:

- Phase 1: Setup (define goal, metric command, direction, scope constraints)
- Phase 2: Baseline (establish measurement before changes)
- Phase 3: Loop (modify -> commit -> measure -> keep/revert, track in TSV)
- Phase 4: Summary (report best result, experiments tried, improvements)

Design requirements:

- Uses `{{EXPERIMENT_BRANCH_PREFIX}}` for branch naming
- Uses `{{EXPERIMENT_RESULTS_DIR}}` for results output
- Persists experiment history under the configured `{{EXPERIMENT_RESULTS_DIR}}` using collision-resistant filenames (for example: timestamp or run slug + timestamp)
- Treats `docs/experiments` as the default output directory, not as a hardcoded path in frontmatter or workflow text
- Requires git (commits each experiment for clean revert)
- Never modifies files marked out-of-scope
- Autonomous once loop starts (no pause to ask "should I continue?")

**Acceptance**: Template produces coherent experimentation workflow, uses configurable collision-resistant result paths, and has valid YAML frontmatter.

## Task 3: Register new skill variables and browser-verification overlay wiring in install-harness

**Files**: `.github/skills/install-harness/SKILL.md` (modify)
**Scope**: Add variables:

- `{{BROWSER_CLI}}` - resolved from workspace profile tool detection
- `{{BROWSER_HEADLESS_FLAG}}` - default: `--headless`
- `{{EXPERIMENT_BRANCH_PREFIX}}` - default: `experiment/`
- `{{EXPERIMENT_RESULTS_DIR}}` - default: `docs/experiments`

Also add `browser-automation` and `iterative-experiment` to the skill installation manifest, and update the `browser-verification` overlay contract / weaving guidance so `browser-automation/SKILL.md` is treated as an explicit overlay target.

**Acceptance**: Variables are in the resolution table with defaults, the skill manifest references the new skills explicitly, and the browser-verification overlay contract names `browser-automation/SKILL.md`.

## Task 4: Add focused verification for browser and experiment skill wiring

**Files**: `src/autoharness/verify_workspace.py`, `tests/test_verify_workspace.py` (modify)
**Scope**: Add focused verification covering template existence for `browser-automation/SKILL.md.tmpl` and `iterative-experiment/SKILL.md.tmpl`, install-harness references to `browser-automation/SKILL.md` and `iterative-experiment/SKILL.md`, and browser-verification overlay wiring that names `browser-automation/SKILL.md`.

**Acceptance**: Verification covers template presence plus install-harness/overlay wiring, and any string-based checks use skill filenames rather than display-name labels.

---

## Dependency Graph

```
Task 1 (browser-automation)     ->
                                   Task 3 (install-harness wiring) -> Task 4 (verification)
Task 2 (iterative-experiment)   ->
```

Tasks 1 and 2 are independent and can proceed in parallel. Task 3 updates install-harness once the new skill surfaces are settled. Task 4 runs after Tasks 1-3 and verifies the completed template and wiring surfaces together.
