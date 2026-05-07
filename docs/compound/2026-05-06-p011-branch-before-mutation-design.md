---
title: "Branch-Before-Mutation: P-011 Design and Ordering Constraint"
date: 2026-05-06
problem_type: agent-workflow
category: harness-design
root_cause: Ship agent created or mutated the workspace before verifying a feature branch existed, risking commits directly to main
tags: [p-011, branch-creation, ship-agent, workflow-gates, ordering]
shipment: 009-S
---

# Branch-Before-Mutation: P-011 Design and Ordering Constraint

## Problem

The Ship agent was not enforcing a feature branch before performing workspace mutations. This created risk of commits landing directly on `main`. Additionally, even after adding the branch gate, the ordering constraint within `Step 0.5` was subtle and error-prone: the shipment ID needed to be known (from a read-only load) before the branch slug could be derived, but the claim (first mutation) had to come _after_ the branch was created.

## Solution

P-011 (Branch-Before-Mutation) was added to the workflow policy registry and wired into `ship.agent.md.tmpl` as a NON-NEGOTIABLE gate in Step 0.5 between validation steps and the first mutation.

The correct ordering in Step 0.5 is:
1. Load shipment (read-only) — needed to derive the branch slug
2. Validate membership and coverage (read-only)
3. **Branch gate** — git status, checkout default branch, pull, create branch (all separate sequential steps)
4. **Claim shipment** — first mutation, only after branch is confirmed active

A critical lesson: the branch slug comes from the shipment title, so the shipment must be loaded (step 1) before the branch can be created (step 3). The gate cannot be the very first action.

## Branch Condition Precision

The branch gate has three mutually exclusive cases:
- **Matching shipment branch already active** (`feat/{slug}` or `chore/{slug}`) → `BRANCH_OK`, proceed
- **On the default branch** (`main` / `{{DEFAULT_BRANCH}}`) → create the shipment branch
- **On any other branch** → halt with `BRANCH_MISMATCH`

Early drafts used "If on `main` or any other non-shipment branch" for the second case, which conflated the create-branch path with the halt path. Tighten to "If on `{{DEFAULT_BRANCH}}` (the default branch)" to make the three cases unambiguous.

## Artifacts

- `templates/policies/workflow-policies.md.tmpl` — P-011 policy definition
- `templates/agents/ship.agent.md.tmpl` — Step 0.5, step 3a (Branch Creation Gate)
- `src/autoharness/verify_workspace.py` — `ship_branch_creation_gate` assertion
