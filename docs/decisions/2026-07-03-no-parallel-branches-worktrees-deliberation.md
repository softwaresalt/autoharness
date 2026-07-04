---
title: "No Parallel Branches or Worktrees: Deliberation and Direction"
description: "Decision for stash CE080560: make single-branch/single-worktree execution a first-class autoharness rule, with only Stage-owned spike/research worktrees exempt."
topic: "How should autoharness prevent agents from operating across parallel branches or worktrees while preserving a narrow Stage research exception?"
depth: "deep"
decision_status: "accepted"
promoted_to: "docs/plans/2026-07-03-no-parallel-branches-worktrees-policy-plan.md"
linked_artifacts:
  - "templates/foundation/constitution.instructions.md.tmpl"
  - "templates/policies/workflow-policies.md.tmpl"
  - "templates/instructions/concurrency.instructions.md.tmpl"
  - "templates/agents/.ship.agent.md.tmpl"
  - "templates/agents/.stage.agent.md.tmpl"
  - "templates/agents/_orchestrator.agent.md.tmpl"
  - ".github/agents/.ship.agent.md"
  - ".github/agents/.stage.agent.md"
  - ".github/agents/_orchestrator.agent.md"
source_stash_ids:
  - "CE080560"
backlog_items:
  - "060-F"
  - "060.001-T"
  - "060.002-T"
  - "060.003-T"
  - "060.004-T"
tags:
  - "policy"
  - "branch-management"
  - "worktree"
  - "remote-operator"
  - "primitive-5"
---

## Problem Frame

Stash `CE080560` asks autoharness to adopt a fundamental rule: agents must
not work on parallel branches, including one local branch plus one or more
parallel worktrees. The reason is operational, not Git capability: remote
operators cannot reliably manage branch-change state when multiple agent-owned
branches or worktrees are active at once.

The stash also defines the only intended exception: worktrees focused
specifically on spike/research operations as part of staging. That exception
must stay Stage-owned, time-boxed, and non-implementation-focused.

## Options

### Option A — Fold the rule into P-011 only

Add worktree checks to the existing Ship branch-before-mutation policy.

* **Pros:** Smallest change and directly touches Ship branch creation.
* **Cons:** Misses Orchestrator pipelining, Stage spike exceptions, and
  workspace-level constitutional guidance.

### Option B — Add a first-class policy and weave it through branch/worktree surfaces

Add a new workflow policy after P-015 and update the constitution,
concurrency instruction, Ship branch gate, Stage guidance, and Orchestrator
pipelining guidance.

* **Pros:** Makes the rule discoverable and enforceable at every relevant gate.
* **Cons:** Larger template/mirror weave; needs careful task isolation.

### Option C — Add a detached instruction only

Create one instruction file for branch/worktree discipline.

* **Pros:** Easy to install and review.
* **Cons:** Risks drift from the existing policy registry and branch gate; may
  not be loaded at the moment of mutation.

### Option D — Disable all Stage/Ship pipelining

Remove pipelined mode entirely.

* **Pros:** Simple mental model.
* **Cons:** Overcorrects. Stage may still do safe planning when it does not
  create a parallel implementation branch, and the stash explicitly preserves
  the spike/research worktree exception.

## Decision

Adopt **Option B**. Create a first-class workflow policy (expected next ID:
**P-016 — No Parallel Branch/Worktree Execution**) and weave it through the
constitution, workflow policy registry, concurrency guidance, Ship branch gate,
Stage exception guidance, and Orchestrator pipelining constraints.

P-011 remains the concrete Ship branch-creation hook, but the new policy should
be broader than P-011 because it governs all agent branch/worktree behavior and
the remote-operator management model.

## Current Surface Findings

* `templates/foundation/constitution.instructions.md.tmpl` says each
  feature/chore gets a dedicated branch, but does not prohibit parallel
  branches or worktrees.
* `templates/policies/workflow-policies.md.tmpl` currently ends at P-015, so
  P-016 is the next available policy slot.
* `templates/agents/.ship.agent.md.tmpl` and `.github/agents/.ship.agent.md`
  implement branch creation gates, but do not inspect `git worktree list`.
* `templates/agents/_orchestrator.agent.md.tmpl` and
  `.github/agents/_orchestrator.agent.md` still describe pipelined mode as
  requiring Stage and Ship on different branches, which conflicts with this
  decision.
* `templates/agents/.stage.agent.md.tmpl` references concurrency control for
  multiple agents but does not bound the spike/research worktree exception.
* `templates/instructions/concurrency.instructions.md.tmpl` needs to clarify
  that locks do not authorize parallel implementation branches or worktrees.

## Guardrails

This section describes the original staging deliberation constraints: during
deliberation, Stage did not create implementation branches or worktrees and did
not perform the policy/template implementation. Execution is owned by Ship via
feature `060-F` and its child tasks.
