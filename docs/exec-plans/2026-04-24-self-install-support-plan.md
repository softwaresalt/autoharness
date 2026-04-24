# Self-Install Support — Implementation Plan

**Date**: 2026-04-24
**Source stash entry**: `389C83E0`
**Covering feature**: `004-F` Self-Install Support
**Risk level**: Elevated — touches schema, 2 skills (install-harness, workspace-discovery), and 1 agent (auto-mergeinstall)
**Requires plan hardening**: yes

---

## Objective

Teach auto-mergeinstall to handle the autoharness workspace itself. autoharness is a globally-distributed tool that ships agent definitions in its wheel package via `pyproject.toml` force-include mappings. When install-harness targets the autoharness workspace, generated workflow agents (stage, ship) must be routed to `.github/local-agents/` instead of `.github/agents/` to prevent leaking non-distributable workflow agents into the wheel.

Infrastructure already partially implemented:
- `pyproject.toml` force-includes `.github/agents/` but NOT `.github/local-agents/`
- `.vscode/settings.json` `chat.agentFilesLocations` includes both directories
- `.github/local-agents/` created with placeholder stage/ship agents

## Blast Radius Assessment

| Surface | Impact | Reversibility |
|---|---|---|
| `schemas/workspace-profile.schema.json` | New optional `distribution` property — additive, no breaking change | Fully reversible (remove property) |
| `.github/skills/workspace-discovery/SKILL.md` | New detection logic — additive, existing detection unchanged | Fully reversible (remove section) |
| `.github/skills/install-harness/SKILL.md` | Conditional branch in Step 1.0 guard — existing behavior preserved for all non-self-install cases | Fully reversible (remove conditional) |
| `.github/agents/auto-mergeinstall.agent.md` | Relaxed guard with operator confirmation — existing flow unchanged when target != autoharness | Fully reversible (revert step text) |
| `pyproject.toml` | Version bump only | Trivial |

**Key invariant**: The existing guard (`workspace_path` must not equal `autoharness_home`) must remain the default behavior. The relaxation is opt-in, gated on `distribution.is_global_tool == true`, and requires explicit operator confirmation.

## Task 1: Add `distribution` property to workspace-profile schema

**Files**: `schemas/workspace-profile.schema.json`
**Scope**: Add a new optional `distribution` object alongside existing `vscode` and `tools` properties with three fields:
- `is_global_tool` (boolean) — true when the workspace is a globally-distributed tool that ships agents in its package
- `global_agents_dir` (string, nullable) — the directory where globally-distributed agents live (default `.github/agents`)
- `local_agents_dir` (string, nullable) — override directory for local-only workflow agents (default `.github/local-agents/`)

**Acceptance**: Schema validates. Property is optional. Defaults documented in field descriptions.
**Dependencies**: None

## Task 2: Add distribution detection to workspace-discovery skill

**Files**: `.github/skills/workspace-discovery/SKILL.md`
**Scope**: Detect the global-distribution pattern using these signals:
1. `pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` entries that map `.github/agents` into a wheel package
2. `.github/local-agents/` directory existence
3. Force-include does NOT map `.github/local-agents/`

When signals 1 and 2 are present, set `distribution.is_global_tool=true`, `distribution.global_agents_dir=.github/agents`, `distribution.local_agents_dir=.github/local-agents/`.

**Acceptance**: Workspace discovery detects the pattern in autoharness's own workspace.
**Dependencies**: Task 1 (schema must define the property)

## Task 3: Relax install-harness Step 1.0 self-guard for global tools

**Files**: `.github/skills/install-harness/SKILL.md`
**Scope**: Add conditional branch in Step 1.0:
- When `workspace_path == autoharness_home` AND `distribution.is_global_tool == true`:
  - Allow the install instead of halting
  - Route generated workflow agents (stage, ship) to `distribution.local_agents_dir` (default `.github/local-agents/`)
  - Continue placing template agents and global skills in `.github/agents/` and `.github/skills/` as normal
  - Verify `local_agents_dir` is NOT in pyproject.toml force-include mappings

**Protected invariant**: The default guard (`workspace_path` must differ from `autoharness_home`) remains in effect for all workspaces that do NOT have `distribution.is_global_tool == true`.

**Acceptance**: install-harness allows self-install with correct agent routing; default guard unchanged.
**Dependencies**: Task 1 (schema field must exist)

## Task 4: Update auto-mergeinstall agent for self-install flow

**Files**: `.github/agents/auto-mergeinstall.agent.md`
**Scope**:
- Step 1 (Identify the Target Workspace): Relax "target workspace MUST be a different directory" when self-install detected. Add operator confirmation: "Target is the autoharness installation itself. Workflow agents will be placed in `.github/local-agents/` to avoid leaking into the wheel. Confirm?"
- Step 2 (Check for Existing Harness): When self-installing, skip backup for `.github/agents/` (source-controlled global agents) and only back up `.github/local-agents/` contents.

**Acceptance**: auto-mergeinstall can target its own workspace with operator confirmation.
**Dependencies**: Task 3 (install-harness must support the routing)

## Task 5: Bump version to 1.2.0

**Files**: `pyproject.toml`
**Scope**: Update `version = "1.1.6"` to `version = "1.2.0"`. Minor version bump for backward-compatible feature addition.
**Acceptance**: `pyproject.toml` shows `version = "1.2.0"`.
**Dependencies**: Task 4 (executes last)

## Dependency Graph

```text
T1 (schema) ──→ T2 (discovery)  ──┐
       │                           │
       └──→ T3 (install-harness) ──→ T4 (agent) ──→ T5 (version bump)
```

## Rollback Plan

All changes are additive. Rollback is a single `git revert` of the merge commit. No data migrations, no state changes, no external system dependencies.

## Verification

- Schema validates against JSON Schema draft-07
- All existing install-harness behavior unchanged when `distribution.is_global_tool` is absent or false
- `uv run autoharness --help` succeeds after version bump
- Manual self-install test: invoke auto-mergeinstall targeting autoharness workspace → workflow agents appear in `.github/local-agents/`, NOT in `.github/agents/`

## Plan Hardening

**Hardening required**: Yes
**Triggers**: Guard relaxation (weakening a safety boundary), schema contract change, 4 artifact classes touched

### Risk Triggers and Protected Invariants

| Risk | Protected Invariant | Enforcement |
|---|---|---|
| Self-guard relaxation could allow arbitrary same-dir installs | Relaxation ONLY activates when `distribution.is_global_tool == true` AND operator confirms | Conditional check in install-harness Step 1.0 |
| Workflow agents could leak into the wheel package | `.github/local-agents/` MUST NOT appear in `pyproject.toml` force-include | Verification check in install-harness self-install mode |
| Self-install could overwrite source-controlled distributable agents in `.github/agents/` | In self-install mode, install-harness MUST NOT write workflow agents (stage, ship) to `.github/agents/` | Routing logic forces workflow agents to `distribution.local_agents_dir` |
| Schema change could break existing profiles that lack `distribution` | The `distribution` property MUST be optional with no required sub-fields | Schema definition uses `"type": "object"` without `"required"` |

### ProposedAction Classification

| Action | Risk | Approval |
|---|---|---|
| Add optional `distribution` property to schema | Low — additive, no existing field touched | safe_auto |
| Add detection logic to workspace-discovery | Low — new section, existing detection unchanged | safe_auto |
| Relax Step 1.0 guard in install-harness | **Medium** — weakens safety boundary | gated_auto (operator confirmation at runtime) |
| Update auto-mergeinstall to allow self-targeting | **Medium** — changes agent behavior boundary | gated_auto (explicit operator prompt before proceeding) |
| Version bump | Low — metadata only | safe_auto |

### Reinforced Verification Requirements

1. **Negative test**: When `distribution.is_global_tool` is absent or false, confirm install-harness Step 1.0 STILL halts on `workspace_path == autoharness_home` — the default guard is not weakened
2. **Routing test**: In self-install mode, confirm only workflow agents (stage, ship) go to `local_agents_dir`; template agents, skills, instructions, policies go to standard locations
3. **Wheel isolation test**: After self-install, confirm `.github/local-agents/` is not referenced in pyproject.toml force-include
4. **Schema backward compatibility**: An existing workspace profile YAML without a `distribution` field must still validate against the updated schema

### Rollback Procedure

Single `git revert` of the merge commit. No data migrations, no persistent state changes, no external system dependencies. All changes are file-level additions or edits in version-controlled artifacts.

### Operator Checkpoint

Self-install mode requires explicit operator confirmation at two points:
1. auto-mergeinstall Step 1: "Target is the autoharness installation itself — confirm?"
2. install-harness Step 1.0: Runtime verification that `distribution.is_global_tool == true` in profile

### Learnings and Instructions Consulted

- Constitution Principle III (Workspace Isolation) — relaxation must preserve isolation semantics
- Constitution Principle VII (Destructive Command Approval) — overwriting agents is destructive
- Repository memory: "Wheel packaging force-includes .github/{agents,skills,instructions,prompts} but excludes .github/local-agents" — confirms the packaging split already exists
- Repository memory: "Two-agent model: stage and ship replace noun-based agents" — confirms workflow agents are stage/ship only

### Unresolved Decisions

None — all operator decisions are deferred to runtime confirmation prompts.

## Plan Review

**Gate decision**: ADVISORY (PASS)
**Date**: 2026-04-24
**Personas invoked**: Constitution Reviewer, Template/Skill Reviewer, Scope Boundary Auditor, Learnings Researcher

### Plan Hardening Check

Plan hardening was required (guard relaxation, schema contract change, 4 artifact classes). Hardening section is present and complete with ProposedAction/ActionRisk classification, protected invariants, reinforced verification, rollback procedure, and operator checkpoints. **Satisfied.**

### Findings

| # | Severity | Persona | Finding | Recommendation |
|---|---|---|---|---|
| 1 | P2 | Constitution | No formal template test harness for variable resolution exists (pre-existing gap) | Record as follow-up stash entry; not blocking for this plan |
| 2 | P2 | Template/Skill | tune-harness routing follow-up mentioned but not formally tracked | Create stash entry after execution |
| 3 | P3 | Template/Skill | Schema `distribution` object could use `additionalProperties: false` | Optional — apply if desired |
| 4 | P3 | Template/Skill | Detection is hatch-specific; other backends not covered | Acceptable for current scope |
| 5 | P3 | Constitution | Plan correctly preserves default guard, gates on `is_global_tool` | No action |
| 6 | P3 | Constitution | Operator confirmation prompt covers destructive approval | No action |
| 7 | P3 | Scope Boundary | `global_agents_dir` schema field may be YAGNI but costs nothing | No action |
| 8 | P3 | Learnings | Plan consistent with packaging architecture memory | No action |

### Gate Rationale

No P0 or P1 findings. Two P2 items are pre-existing or deferred follow-ups, not blockers. Plan is well-structured with clear dependency graph, acceptance criteria, and hardening detail. Proceed to harvest and execution.
