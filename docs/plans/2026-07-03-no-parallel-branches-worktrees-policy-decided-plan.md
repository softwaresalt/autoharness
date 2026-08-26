---
title: "No Parallel Branches/Worktrees Policy — decided plan"
doc_type: decided-plan
status: planned
created: 2026-07-03
feature: "060-F"
tasks: ["060.001-T", "060.002-T", "060.003-T", "060.004-T"]
supersedes:
  - docs/archive/plans/2026-07-03-no-parallel-branches-worktrees-policy-plan.md
---

# Decided Plan: No Parallel Branches/Worktrees Policy

**Outcome:** Planned, not shipped. The source plan turns stash `CE080560` into first-class policy `P-016`: agents must not execute across parallel implementation branches/worktrees. The only allowed exception is a narrow Stage-owned spike/research worktree. The recommended first shipment is `060.001-T` only, so the governing rule exists before agent templates and entry-point docs depend on it.

## Decisions

1. Add `P-016` as a workflow policy covering Stage, Ship, Orchestrator, and any skill/agent that creates or uses branches/worktrees.
2. Enforce a single active implementation branch/worktree at a time for agent-owned execution.
3. Allow a separate worktree only for explicit, time-boxed Stage spike/research staging, with no implementation, no shipment claim, no Ship execution, and no template/source/config mutation in that worktree.
4. Make `P-011` and Ship intake enforce the rule: Ship must inspect `git worktree list --porcelain` before claim/branch creation and fail closed on ambiguous extra worktrees.
5. Reframe Stage/Orchestrator pipelining so planning may continue only when it does not create a parallel implementation branch/worktree.

## Implementation (4 tasks)

- **060.001-T** — add `P-016`, update constitutional wording, and update concurrency guidance so file locks cannot be misread as permission for parallel implementation branches/worktrees.
- **060.002-T** — wire the worktree gate into the Ship template and installed Ship mirror before shipment claim or branch creation.
- **060.003-T** — make Stage's exception explicit and narrow, and remove any Orchestrator guidance that endorses concurrent implementation branches/worktrees.
- **060.004-T** — update entry-point docs and verification surfaces so `P-016` is discoverable and stale guidance is caught.

Dependencies remain intentionally simple: `060.001-T` defines the rule, `060.002-T` and `060.003-T` depend on it, and `060.004-T` closes the loop across docs and verification.

## Key constraints preserved

- Fail closed whenever an extra worktree cannot be confidently classified as the narrow Stage spike/research exception.
- Introduce no new template variables unless explicitly documented.
- Keep the first shipment to `060.001-T` only so policy precedes agent/template references and partial-feature closure risk stays low.
- Validation must cover frontmatter, markdown hierarchy, unresolved `{{VARIABLE}}` scans, cross-reference integrity, and a search for any remaining guidance that endorses parallel execution.
- Stage did not create branches/worktrees or run builds/tests/linters/template validation in the planning session.

## Rejected alternatives

- **One local branch plus parallel worktrees** — rejected because it forces operators to track ambiguous ownership and safe commit state.
- **Pipelined Stage/Ship on different implementation branches/worktrees** — rejected because `P-016` keeps implementation execution single-threaded even when planning continues.
- **A broad research-worktree carve-out** — rejected; only explicit, time-boxed Stage spike/research worktrees are allowed.

## Out of scope preserved

- No CLI, schema, or backlogit binary changes.
- No immediate source/template/config implementation in the Stage session.
- No feature/chore branch or worktree creation during staging.
- No PR creation.