# Consolidate Non-Top-Level Agent Install Paths to `subagents/` — Implementation Plan

**Date**: 2026-05-22
**Source stash**: `0EBC97D5` (recovered — was absent from active and archived stash state)
**Covering feature**: 048-F
**Risk level**: Low — mechanical string substitutions in skill/template files; no schema changes, no CLI code changes
**Requires plan hardening**: yes (touches multiple template families: install-harness SKILL, verify-harness SKILL, foundation AGENTS template)

---

## Objective

Update the autoharness harness install workflow so that **all non-Orchestrator/Stage/Ship agents**
are installed into a single `.github/agents/subagents/` directory in the target workspace,
instead of the current categorized subdirectory layout (`agents/review/`, `agents/research/`).

This completes an intent that was captured in stash entry `6AB4534F` → feature `031-F`
but archived as `harness_status: pending` (never executed). Entry `0EBC97D5` restates the
same requirement with tighter scope: install-output paths only, no source template moves.

## Background: Current vs. Target State

### Current install-output layout (target workspace)

```
.github/agents/
  orchestrator.agent.md     ← top-level
  stage.agent.md            ← top-level
  ship.agent.md             ← top-level
  auto-mergeinstall.agent.md ← top-level
  auto-tune.agent.md        ← top-level
  adversarial-review.agent.md
  language-engineer.agent.md
  prompt-builder.agent.md
  security-sentinel.agent.md
  review/                   ← categorized subdir
    agent-native-parity-reviewer.agent.md
    architecture-strategist.agent.md
    concurrency-reviewer.agent.md
    constitution-reviewer.agent.md
    scope-boundary-auditor.agent.md
    security-lens-reviewer.agent.md
    security-reviewer.agent.md
    technology-reviewer.agent.md
  research/                 ← categorized subdir
    learnings-researcher.agent.md
```

### Target install-output layout

```
.github/agents/
  orchestrator.agent.md     ← top-level (unchanged)
  stage.agent.md            ← top-level (unchanged)
  ship.agent.md             ← top-level (unchanged)
  auto-mergeinstall.agent.md ← top-level (unchanged)
  auto-tune.agent.md        ← top-level (unchanged)
  subagents/                ← single flat subdir for ALL non-top-level agents
    adversarial-review.agent.md
    language-engineer.agent.md
    prompt-builder.agent.md
    security-sentinel.agent.md
    agent-native-parity-reviewer.agent.md
    architecture-strategist.agent.md
    concurrency-reviewer.agent.md
    constitution-reviewer.agent.md
    scope-boundary-auditor.agent.md
    security-lens-reviewer.agent.md
    security-reviewer.agent.md
    technology-reviewer.agent.md
    learnings-researcher.agent.md
```

Source template files in `templates/agents/review/` and `templates/agents/research/`
**remain in place** — only the install OUTPUT paths change.

## Blast Radius

| Surface | Change | Risk |
|---|---|---|
| `.github/skills/install-harness/SKILL.md` | Update primitive map table + install paths table | Low — text substitution |
| `.github/skills/verify-harness/SKILL.md` | Update review payload build step | Low — 1 line |
| `templates/foundation/AGENTS.md.tmpl` | Update legacy-agent migration table | Low — 2 lines |
| `src/autoharness/verify_workspace.py` | No change needed — no hardcoded `review/` or `research/` path assertions | None |
| `templates/agents/review/*.tmpl` | No change — source template location unchanged | None |
| `templates/agents/research/*.tmpl` | No change — source template location unchanged | None |
| Target workspace migration | Existing installs keep stale `review/`/`research/` dirs; `tune-harness` will detect and propose cleanup on next run | Low — no breakage, cosmetic drift |

## Plan Harden: Risk Assessment

**Scope confirmation**: All three files contain only documentation-level path references.
No runtime logic depends on these strings at harness-install time (the agent following the
SKILL.md reads these as instructions). No test fixtures validate `review/` or `research/`
subdirectory paths. No schema fields constrain agent install output paths.

**Migration safety**: Existing harness installs that used the old layout will continue to
function; agents in `agents/review/` and `agents/research/` remain discoverable to VS Code
(which scans `chat.agentFilesLocations` recursively). On next `tune-harness` run, the tuner
will detect the drift and propose removing the stale subdirs and re-installing to `subagents/`.

**Consistency note**: Two non-review non-research agents (`language-engineer`, `prompt-builder`)
were already mapped to `subagents/` in earlier partial work. This plan completes the migration
for the remaining agents. After this plan, `adversarial-review` and `security-sentinel` also
move to `subagents/` (they are top-level templates but non-Orchestrator/Stage/Ship agents).

**Finding**: No hardening actions required beyond documentation of migration safety. Plan
proceeds to review.

## Plan Review Gate: Findings

**Reviewer**: Stage (self-review — low-risk mechanical change)

| Finding | Severity | Disposition |
|---|---|---|
| Verify no `agents/review/` references remain after 048.001-T/048.002-T/048.003-T | P2 | Ship verifies — add to task acceptance criteria |
| Confirm `adversarial-review` and `security-sentinel` are included in subagents/ layout (not left as top-level flat) | P2 | Captured in 048.001-T scope |
| Note migration guidance for existing workspaces in SKILL.md tune-harness section | P3 | Advisory — tune-harness drift detection handles this automatically |

**Plan review verdict**: PASS — proceed to harvest.

---

## Task 1: Update install-harness/SKILL.md agent path references

**File**: `.github/skills/install-harness/SKILL.md`
**Scope**: Update three locations:

1. **Primitive map table** (line 753): Change `agents/research/learnings-researcher`
   → `agents/subagents/learnings-researcher`

2. **Primitive map table** (line 759): Change `agents/review/*`
   → `agents/subagents/*`

3. **Install paths table** (lines 1080-1082): Consolidate `Review Personas` and
   `Research Agents` rows into a single `Subagents` row:

   Before:
   ```
   | Agents | `{workspace}/.github/agents/` |
   | Review Personas | `{workspace}/.github/agents/review/` |
   | Research Agents | `{workspace}/.github/agents/research/` |
   ```

   After:
   ```
   | Agents | `{workspace}/.github/agents/` — top-level agents (Orchestrator, Stage, Ship, Auto-MergeInstall, Auto-Tune) |
   | Subagents | `{workspace}/.github/agents/subagents/` — all non-top-level agents: review personas, researchers, language-engineer, prompt-builder, adversarial-review, security-sentinel |
   ```

**Acceptance criteria**:
- No remaining `agents/review/` or `agents/research/` install-path references in this file
- Primitive map table updated for both row 1 (State/Context) and row 7 (Observability)
- Install paths table has single `Subagents` row

---

## Task 2: Update verify-harness/SKILL.md review payload build step

**File**: `.github/skills/verify-harness/SKILL.md`
**Scope**: Line 60 — update review payload build step

Before:
```
   * The actual agent files in `.github/agents/` and `.github/agents/review/`
```

After:
```
   * The actual agent files in `.github/agents/` and `.github/agents/subagents/`
```

**Acceptance criteria**:
- No remaining `agents/review/` reference in this file

---

## Task 3: Update templates/foundation/AGENTS.md.tmpl legacy-agent migration table

**File**: `templates/foundation/AGENTS.md.tmpl`
**Scope**: Lines 340-341 — update the legacy-agent migration table entries for `review` and `plan-review` skills

Before:
```
| `review` (agent) | `review` skill | Converted from agent to skill; dispatches persona subagents from `.github/agents/review/` |
| `plan-review` (agent) | `plan-review` skill | Converted from agent to skill; dispatches persona subagents from `.github/agents/review/` |
```

After:
```
| `review` (agent) | `review` skill | Converted from agent to skill; dispatches persona subagents from `.github/agents/subagents/` |
| `plan-review` (agent) | `plan-review` skill | Converted from agent to skill; dispatches persona subagents from `.github/agents/subagents/` |
```

**Acceptance criteria**:
- No remaining `agents/review/` reference in this file
- Legacy migration table accurately reflects the `subagents/` install layout

---

## Verification Checklist (Ship)

After all three tasks are complete:

- [ ] `grep -r "agents/review" .github/skills/ templates/foundation/` returns no results
- [ ] `grep -r "agents/research" .github/skills/ templates/foundation/` returns no results
- [ ] Install paths table in `install-harness/SKILL.md` has a `Subagents` row referencing `subagents/`
- [ ] Primitive map table rows 1 and 7 reference `subagents/`
- [ ] `verify-harness/SKILL.md` references `subagents/` not `review/`
- [ ] `AGENTS.md.tmpl` legacy migration table references `subagents/`
