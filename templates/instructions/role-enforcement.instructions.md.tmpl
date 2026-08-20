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
   - **Log** a P-010 policy violation: `P-010 VIOLATION: {agent_name} attempted
     forbidden operation [{operation}] in category [{category}].`
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
   - **P-021 capture-only carve-out**: A capture-only stash write performed
     under P-021 C2 (mandatory deferred-scope-expansion capture) matches the
     acting agent's Allowed column via P-021 C5 (Ship's capture-only
     carve-out) and does NOT trigger the fail-closed unclassified-mutation
     halt above. This is an enumeration in the Allowed column, not a
     weakening of fail-closed semantics. Any OTHER stash operation by Ship —
     triage, prioritize, re-classify, edit, harvest, deliberate, or
     discretionary removal/archival — remains a P-010 violation and MUST
     halt.

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

## Skill-Delegation Model Inheritance (P-013.5)

Skills are leaf executors: they do not declare their own `model_family` /
`model_provider` / `reasoning_effort` frontmatter and they do not spawn
subagents. A skill invoked by an agent (Stage, Ship, Orchestrator, or an
elective agent) runs **inside the invoking agent's already-routed session** —
it inherits whatever model that agent resolved and declared per its own
invocation directive (P-013.5). This applies uniformly when invoking agents
**and** their skill workflows: the routing decision is made once, at
agent-invocation time, not re-resolved per skill call.

Before invoking any skill, the invoking agent MUST confirm and propagate its
own current routing state for the session — either "resolved" or explicitly
"`ROUTING_DEGRADED`" — rather than requiring a non-degraded state as a
precondition (a degraded session must still be able to invoke its skills; it
just carries the degradation forward, per step 3 below):

1. **Confirm own routing first.** If the agent's own model route was resolved
   via an explicit invocation directive (Orchestrator Steps 1/2 for Stage/Ship;
   an equivalent directive for elective agents) and no `ROUTING_DEGRADED`
   condition was declared for this session, proceed — the skill inherits that
   resolved session model with no further action.
2. **Do not re-resolve per skill.** A skill is not a separate routing target;
   introducing a per-skill `model_family` field would duplicate P-013.5 routing
   at the wrong granularity and is explicitly out of scope (skills remain leaf
   executors — see also P-013.4 tier annotation, which applies to agent
   definitions only).
3. **Carry a degraded state forward, do not clear it.** If the invoking agent's
   own session is already in a `ROUTING_DEGRADED` state (its resolved role route
   could not be honored by the runtime), that degradation applies to every skill
   the agent invokes during the session. Do not silently treat a skill invocation
   as a fresh, non-degraded routing context.

**Rationale**: this closes the gap between "the desired role→model mapping
exists in config" and "every unit of work — agent turn and skill call alike —
actually runs on the resolved model." Cross-reference P-013.5 (invocation-time
model-routing enforcement) in `workflow-policies.md` for the fail-closed
verification and `ROUTING_DEGRADED` semantics this contract depends on.
