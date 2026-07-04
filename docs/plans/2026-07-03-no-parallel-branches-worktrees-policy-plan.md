---
title: "No Parallel Branches/Worktrees Policy — Implementation Plan"
description: "Plan for CE080560: add a first-class no-parallel-branches/worktrees rule with a narrow Stage spike/research worktree exception and weave it through policy, constitution, agents, concurrency guidance, and verification surfaces."
source_documents:
  - "docs/decisions/2026-07-03-no-parallel-branches-worktrees-deliberation.md"
feature: "060-F"
tasks:
  - "060.001-T"
  - "060.002-T"
  - "060.003-T"
  - "060.004-T"
source_stash_ids:
  - "CE080560"
source_deliberation_ids:
  - "006-DL"
scope: "harness policy/templates/agent guidance only; no CLI/schema changes"
tags:
  - "policy"
  - "branch-management"
  - "worktree"
  - "remote-operator"
  - "primitive-5"
---

## Problem Frame

Agents currently have branch-before-mutation and single-release-unit policies,
but the harness does not state a general rule against parallel agent-owned
branches or worktrees. That leaves room for workflows where one agent works on a
local branch while another agent or worktree carries parallel branch state.

For remote operators, this creates a management problem: the operator must track
which branch/worktree owns which change, which artifacts are safe to commit, and
which state is visible in the active workspace. The rule from stash `CE080560`
should become a first-class harness invariant:

> Agents must not work on parallel branches or maintain one local branch plus
> one or more parallel worktrees. The only exception is a Stage-owned
> spike/research worktree used for staging investigation, not implementation.

## Design

Add a new workflow policy after P-015:

* **Expected ID**: `P-016`
* **Name**: `No Parallel Branch/Worktree Execution`
* **Applies to**: Stage, Ship, Orchestrator, and any skills/agents that create
  branches or worktrees
* **Gate points**:
  * session start / state assessment
  * before Ship claims a shipment or creates a feature/chore branch
  * before any agent creates or uses a worktree
  * before Orchestrator enables pipelined Stage/Ship work
* **Core rule**: one implementation branch/worktree at a time for agent-owned
  execution
* **Exception**: Stage may create/use a separate worktree only for explicit,
  time-boxed spike/research staging, with no implementation, no shipment claim,
  and no Ship execution in that worktree
* **Violation action**: record P-016 through P-005 telemetry and halt; fail
  closed on ambiguous extra worktrees

P-011 should reference P-016 as the branch-creation implementation hook. Ship's
branch gate should inspect `git worktree list --porcelain` before the first
mutation and halt when prohibited extra worktrees are present.

## Task Breakdown

### 060.001-T — Add foundational no-parallel branch/worktree policy

* Add P-016 to `templates/policies/workflow-policies.md.tmpl`, including
  relationship notes for P-001, P-010, and P-011, plus an amendment-log entry.
* Update P-011 to require the worktree gate before branch creation or shipment
  claim.
* Update `templates/foundation/constitution.instructions.md.tmpl` so the
  "branch per release unit" workflow rule becomes a single-active
  implementation branch/worktree rule.
* Update `templates/instructions/concurrency.instructions.md.tmpl` so locks and
  concurrent-access mode cannot be read as permission for parallel
  implementation branches/worktrees.
* **Acceptance**: P-016 is first-class; Stage spike/research is the only
  worktree exception; no new variables are introduced unless documented; changed
  Markdown has valid frontmatter and heading hierarchy.
* **Width**: policy + constitution + concurrency guidance.

### 060.002-T — Enforce no-parallel worktree gate in Ship branch intake

* Update `templates/agents/.ship.agent.md.tmpl` Step 0.5 and the dogfooded
  `.github/agents/.ship.agent.md` mirror.
* Add a `git worktree list --porcelain` check before shipment claim or branch
  creation.
* Ship must not create or use parallel worktrees and must fail closed when an
  extra worktree cannot be confidently classified as an allowed Stage
  spike/research worktree.
* Record P-016/P-005 when prohibited parallel branch/worktree state is found.
* **Acceptance**: Ship cannot claim or execute a shipment with prohibited
  secondary worktrees; P-011 references P-016; template and mirror agree.
* **Width**: Ship agent template + installed mirror.

### 060.003-T — Reframe Stage/Orchestrator pipelining around the research-worktree exception

* Update `templates/agents/.stage.agent.md.tmpl` and
  `.github/agents/.stage.agent.md` so Stage's role boundary explicitly allows a
  separate worktree only for time-boxed spike/research staging and forbids
  implementation/template/source/config mutation in that worktree.
* Update `templates/agents/_orchestrator.agent.md.tmpl` and
  `.github/agents/_orchestrator.agent.md` so pipelined mode no longer requires
  or endorses different implementation branches.
* Orchestrator should sequence Stage/Ship so no concurrent implementation
  branches or worktrees are active; Stage planning may continue only when it
  does not create a parallel implementation branch/worktree, except for the
  explicit research-worktree case.
* **Acceptance**: no Orchestrator guidance tells Stage and Ship to operate on
  different implementation branches; Stage's exception is explicit and narrow;
  templates and mirrors agree.
* **Width**: Stage + Orchestrator agent guidance.

### 060.004-T — Update entry-point docs and verification checks for P-016

* Update `templates/foundation/AGENTS.md.tmpl` and root `AGENTS.md` if needed so
  agents can discover the no-parallel-branches/worktrees rule from the entry
  point.
* Update `.github/skills/install-harness/SKILL.md` and
  `.github/instructions/harness-architecture.instructions.md` where policy
  lists, guardrail mappings, Primitive 4/5/8 text, or verification checks should
  mention P-016 and the Stage spike/research exception.
* Run Ship-appropriate documentation/template validation (for example,
  markdownlint on changed Markdown, unresolved-variable scan, and
  cross-reference checks) and report the results in the PR.
* **Acceptance**: generated-template entry points, installed mirrors, and
  verification guidance agree; P-016 is discoverable; no stale guidance still
  recommends parallel implementation branches/worktrees.
* **Width**: entry-point docs + validation surfaces.

## Sequencing

1. `060.001-T` defines the policy and constitutional rule.
2. `060.002-T` wires the rule into Ship's branch/mutation gate.
3. `060.003-T` reconciles Stage and Orchestrator behavior with the new rule.
4. `060.004-T` finishes discovery and verification surfaces.

`060.002-T` and `060.003-T` depend on `060.001-T`. `060.004-T` depends on all
three implementation tasks.

## Shipment Recommendation

Queue the first shipment with **only `060.001-T`**. This is the safest first
slice because it defines the governing rule before agent templates reference it.
It also avoids partial-feature cascade pitfalls by excluding the parent feature
from the shipment manifest.

Remaining tasks (`060.002-T`, `060.003-T`, `060.004-T`) stay queued under
`060-F` for subsequent shipments.

## Verification

Ship should validate changed Markdown/templates with the smallest relevant
checks available in the repository, including:

* YAML frontmatter validity for changed Markdown/templates
* Markdown heading hierarchy checks
* unresolved `{{VARIABLE}}` scan for rendered/installed output where applicable
* cross-reference checks for policy IDs and file paths
* a targeted search confirming no remaining Stage/Ship/Orchestrator guidance
  endorses parallel implementation branches or worktrees

Stage did not run tests, builds, linters, or template validation as required by
the Stage role boundary for this session.

## Out of Scope

* No CLI, schema, or backlogit binary changes.
* No immediate source/template/config implementation in this Stage session.
* No feature/chore branch or worktree creation during staging.
* No PR creation.
