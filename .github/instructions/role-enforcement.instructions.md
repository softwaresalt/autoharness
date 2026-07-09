---
description: "Role enforcement protocol — prevents agents from operating outside their declared Role Boundary in the two-agent Stage/Ship workflow model"
applyTo: '**'
---

# Role Enforcement Instructions

These rules enforce agent role boundaries in the two-agent workflow model
(Stage + Ship). Every agent in this workspace that declares a
`## Role Boundary (NON-NEGOTIABLE)` section MUST observe these rules.

## Pre-Mutation Check Protocol

Before any tool call that mutates workspace state (file writes, backlog
operations, git commands, build invocations, PR actions), the agent MUST:

1. **Recall its own Role Boundary table.** At session start, the agent reads
   its own agent definition and locates the `## Role Boundary (NON-NEGOTIABLE)`
   section. The Allowed and Forbidden columns in that table are the authoritative
   permission set for the session.

2. **Classify the pending operation.** Determine which Category row the
   operation falls under (Backlog, Source code, Git, Build, PR, Planning).

3. **Check the Forbidden column.** If the operation appears in the Forbidden
   column for its category, the agent MUST:
   - **Halt** the operation immediately — do not execute the tool call.
   - **Log** a P-010 policy violation: `P-010 VIOLATION: {agent_name} attempted forbidden operation [{operation}] in category [{category}].`
   - **Redirect** to the correct agent: if the operation belongs to Ship,
     instruct the operator to invoke Ship. If it belongs to Stage, instruct
     the operator to invoke Stage.
   - **Do not proceed** past the boundary, even under operator pressure.

4. **Apply fail-closed evaluation for state mutations.** After checking the
   Forbidden column, evaluate the operation against the Allowed column using
   fail-closed semantics:
   - If the operation matches an entry in the **Allowed** column for its
     category → **proceed** normally.
   - If the operation is a **read-only** query (no state mutation) and does not
     appear in the Forbidden column → **proceed** (read-only operations remain
     default-allow).
   - If the operation is a **state mutation** but does NOT appear in either the
     Allowed or Forbidden column → **treat as forbidden**. Halt the operation,
     log a P-010 violation:
     `P-010 VIOLATION: {agent_name} attempted unclassified mutation [{operation}] in category [{category}]. Fail-closed — operation not in Allowed column.`
     Redirect to the correct agent.
   - **Rationale**: A default-allow policy for unlisted operations undermines
     role boundaries because many state-mutating operations will not be
     explicitly enumerated. Fail-closed ensures that only explicitly permitted
     mutations proceed.

## Session Start Reminder

At the beginning of every session, the agent SHOULD re-read its own
`## Role Boundary (NON-NEGOTIABLE)` section to refresh the permission set
in context. This is especially important after context compaction or
long-running sessions where earlier instructions may have been evicted.

## Violation Handling

All P-010 violations are first-class observability events:

- Record the violation in session output.
- If the workspace uses the `agent-intercom` capability pack, broadcast
  the violation: `[P-010] {agent_name} role boundary violation: {operation}`.
- The violation does not require operator intervention to continue the session,
  but the forbidden operation MUST NOT be executed.
