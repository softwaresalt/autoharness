---
title: "Agent Role Boundaries: P-010 Stage vs Ship Enforcement"
date: 2026-05-06
problem_type: agent-workflow
category: harness-design
root_cause: Stage agent was observed executing code, running builds, or creating PRs — work that belongs to Ship
tags: [p-010, role-boundary, stage-agent, ship-agent, allow-deny-table]
shipment: 009-S
---

# Agent Role Boundaries: P-010 Stage vs Ship Enforcement

## Problem

Without an explicit role boundary, Stage agents would sometimes drift into Ship territory: writing implementation code, running `pytest`, or creating PRs. This blurs the two-agent contract and makes the pipeline harder to reason about and debug.

## Solution

P-010 (Agent Role Boundary) was added to the workflow policy registry. The Stage template received a `## Role Boundary (NON-NEGOTIABLE)` section with an explicit allow/deny table placed prominently before the Step Sequence Contract.

### Allow/Deny Table Pattern

An allow/deny table is more durable than a paragraph prohibition because:
1. It forces the author to enumerate every scoped activity explicitly
2. It is scannable by both agents and humans without reading dense prose
3. It makes the boundary verifiable: verify_workspace can check for the presence of both the heading and the "Forbidden" column

### Key Stage Boundary Nuance

"Stage MUST NOT create git branches" was wrong. Stage legitimately commits backlog, planning, and administrative artifacts directly to `main` or an admin branch. The correct boundary is: **Stage MUST NOT create _feature/chore implementation_ branches or write implementation code**.

The allow/deny table was updated to reflect this nuance: commits to `main` for backlog artifacts are allowed; implementation feature branches are forbidden.

## Artifacts

- `templates/policies/workflow-policies.md.tmpl` — P-010 policy definition
- `templates/agents/stage.agent.md.tmpl` — `## Role Boundary (NON-NEGOTIABLE)` table
- `src/autoharness/verify_workspace.py` — `stage_role_boundary` assertion
