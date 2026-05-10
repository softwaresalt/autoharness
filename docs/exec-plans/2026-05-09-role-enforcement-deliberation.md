# Harness Role Enforcement — Deliberation

**Date**: 2026-05-09
**Shipment**: 023-S
**Status**: complete

---

## Context

The autoharness two-agent workflow (Stage + Ship) relies on instructional role
boundaries defined in agent template markdown. Currently:

- **Stage** has an explicit `## Role Boundary (NON-NEGOTIABLE)` section with an
  Allowed/Forbidden table and P-010 violation language.
- **Ship** has no equivalent explicit role boundary table — its constraints are
  embedded in the step-by-step pipeline instructions.
- **Orchestrator** enforces role isolation through routing ("Stage never gets
  build/PR scope; Ship never gets stash/planning scope") but has no mechanism
  to verify compliance.

The enforcement is entirely instructional — any agent can call any tool. There
is no pre-mutation gate that checks role before executing.

## Decision 1: Role Declaration Schema

**Question**: Where should agents declare their permitted and forbidden operations?

### Option A: YAML frontmatter metadata

```yaml
---
name: Stage
role: stage
permitted_operations: [create_item, create_shipment, update_item, stash, search]
forbidden_operations: [claim_shipment, move_to_active, push, pr_create]
---
```

**Pros**: Machine-parseable, verify_workspace can validate, consistent across environments.
**Cons**: Frontmatter fields are not standardized across environments — VS Code
Copilot reads `name`, `description`, `tools`, `model` but may ignore custom fields.
Agents may not be able to introspect their own frontmatter at runtime.

### Option B: Structured section in agent body (current pattern, enhanced)

```markdown
## Role Boundary (NON-NEGOTIABLE)

| Category | Allowed | Forbidden |
|---|---|---|
| Backlog | create, update, stash | claim_shipment, close_shipment |
| Git | commit to default branch | create feature branches |
| Build | — | run tests, linters |
| PR | — | create, push, merge |
```

**Pros**: Already exists for Stage, agents read their own body at session start,
verify_workspace can parse the table with text matching, environment-agnostic.
**Cons**: Prose-based — harder to parse programmatically than YAML. Table format
must be standardized for automated validation.

### Option C: Separate instruction template

```markdown
# role-enforcement.instructions.md
applyTo: '**'

Before any mutation, check the agent's declared role boundary table...
```

**Pros**: Applies universally via `applyTo`, decoupled from agent definitions,
single source of enforcement logic.
**Cons**: Adds a new artifact; the instruction can only remind, not enforce.

### ✅ Recommendation: Option B + C (hybrid)

- **Option B**: Standardize the Role Boundary table in both Stage and Ship
  agent templates. Ship currently lacks this table — add it.
- **Option C**: Create a `role-enforcement.instructions.md.tmpl` that defines
  the pre-mutation check protocol. The instruction references the agent's own
  Role Boundary table and teaches the agent to self-check before tool calls.

This is the most environment-agnostic approach. The role declarations live where
agents already read them (their own body), and the enforcement instruction adds
a reminder layer that applies to all files.

## Decision 2: Enforcement Mechanism

**Question**: How is the role boundary enforced at runtime?

### Option A: Instruction-based self-check (agent reads its own rules)

The `role-enforcement.instructions.md` instructs every agent to:
1. At session start, read its own Role Boundary table
2. Before any tool call that mutates state, classify the operation
3. If the operation is in the Forbidden column, halt and log P-010

**Pros**: Environment-agnostic, works everywhere, no external dependencies.
**Cons**: Instructional — the agent must follow the instruction. An agent under
pressure (large context, complex task) may skip the check.

### Option B: Environment-level pre-call hook

Some environments may support tool-call interceptors or MCP middleware that
validates the caller's identity before executing a tool.

**Pros**: Deterministic — cannot be skipped by the agent.
**Cons**: No current environment exposes this API. Would require environment-specific
implementations for each of VS Code Copilot, Copilot CLI, Codex, Cursor, Claude Code.

### Option C: Backlogit server-side enforcement (actor parameter)

Add an `actor` field to backlogit MCP tool calls. Backlogit validates the actor
against a permissions table in `hooks.yaml`.

**Pros**: Deterministic for backlogit operations.
**Cons**: Only covers backlogit — doesn't cover git, file system, or other tools.
Requires backlogit Go code changes (not autoharness template work).

### ✅ Recommendation: Option A (instruction-based)

The instruction-based approach is the only one that works across all environments
and all tools without requiring external changes. It is weaker than deterministic
enforcement, but it is the only option available today.

**Mitigation for weakness**: Combine with verify_workspace assertions that check
installed agents have consistent role boundary tables and the role-enforcement
instruction is present. This catches drift at install/tune time even if runtime
enforcement is imperfect.

**Future upgrade path**: When environments add pre-call hooks or MCP middleware,
the instruction can be replaced with a deterministic gate. The role declaration
schema (Decision 1) is designed to be machine-parseable for this future.

## Decision 3: Conditional Weaving

**Question**: How does install-harness decide when to apply role restrictions?

### Option A: Detect presence of both stage.agent.md.tmpl and ship.agent.md.tmpl

If both templates are being installed, the workspace uses the two-agent model.
Weave role enforcement. If only one agent (or neither) is installed, skip.

**Pros**: Automatic detection, no config flag needed.
**Cons**: Could misfire if someone installs both agents for a different purpose.

### Option B: Explicit config flag

```yaml
# .autoharness/config.yaml
workflow_model: "two-agent"  # or "single-agent"
```

**Pros**: Explicit, no ambiguity.
**Cons**: Another config field to manage. Operator must set it correctly.

### Option C: Infer from preset + installed agents

`full` preset with both stage and ship → two-agent model. `starter` or
`standard` without both → single-agent.

**Pros**: Leverages existing preset system.
**Cons**: Doesn't handle custom configurations where someone picks `standard`
but installs both agents.

### ✅ Recommendation: Option A (auto-detect)

Detect the presence of both `stage.agent.md` and `ship.agent.md` in the
installed artifacts. If both exist, weave role enforcement. Simple, automatic,
and correct for the common case.

Edge case: if someone installs both agents but doesn't want role enforcement,
they can add `role_enforcement: false` to config.yaml as an explicit opt-out.
This is the exception, not the rule — don't add config complexity for it unless
needed.

## Decision 4: Verification Contract

**Question**: What does verify_workspace.py check for role consistency?

### Assertions to add:

1. **Role Boundary table presence**: When both `stage.agent.md` and `ship.agent.md`
   exist, both must contain a `## Role Boundary (NON-NEGOTIABLE)` section.

2. **Role Boundary table consistency**: Stage's Forbidden column must include
   operations that Ship's Allowed column includes (and vice versa). No operation
   should be Allowed by both agents in the same category.

3. **Role enforcement instruction**: When two-agent model is detected (both agents
   present), `role-enforcement.instructions.md` must also be present.

4. **No cross-contamination**: Stage agent body should not reference `claim_shipment`,
   `pr_create`, `git push`, or other Ship-only operations outside the Forbidden
   column. Ship agent body should not reference `create_shipment`, `stash`, or
   other Stage-only operations outside its allowed scope.

### Test coverage:

- Pass case: both agents with consistent boundaries + instruction present
- Fail case: Ship missing Role Boundary table
- Fail case: role-enforcement instruction missing when both agents installed
- Fail case: Stage references a Ship-only operation in its workflow steps

## Implementation Plan

Based on these decisions, the follow-up shipment (024-S) should contain:

| Task | Description | Effort |
|---|---|---|
| 024.001-T | Add Role Boundary table to `ship.agent.md.tmpl` (matching Stage's format) | Small |
| 024.002-T | Create `templates/instructions/role-enforcement.instructions.md.tmpl` | Medium |
| 024.003-T | Update `install-harness/SKILL.md` with conditional weaving for role enforcement (auto-detect two-agent model) | Medium |
| 024.004-T | Add verify_workspace.py assertions + tests for role consistency | Medium |
| 024.005-T | Documentation updates | Small |
