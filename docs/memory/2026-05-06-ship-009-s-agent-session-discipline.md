---
title: "Ship 009-S: Agent Session Discipline and Workflow Boundaries"
date: 2026-05-06
shipment: 009-S
pr: 36
merge_sha: ee3828a
branch: feat/agent-session-discipline
status: shipped
---

# Ship Session Memory: 009-S

## What Was Shipped

Three interrelated workflow discipline policies (P-010, P-011, P-012) and a new dispatch coordinator agent.

### Tasks

| Task | Title |
|---|---|
| 009.001-T | Enforce Stage/Ship workflow boundary compliance (P-010 + Role Boundary table) |
| 009.002-T | Add pre-flight MCP tool availability gate at session start (P-012 + Step 0.0) |
| 009.003-T | Mandatory branch creation gate (P-011) + dispatch agent template |

## Key Technical Decisions

**P-005 is telemetry, not enforcement.** Early plan referenced P-005 as the violated policy for role boundary and branch issues. P-005 only records violations. P-010/P-011/P-012 are the actual behavioral policies; P-005 is the recording mechanism for all of them.

**Branch gate ordering**: Branch slug derives from shipment title → shipment must be loaded (read-only) before branch can be created → claim (first mutation) must come after branch creation. Step 0.5 ordering: load → validate → branch gate → claim.

**Stage's branch behavior is nuanced**: Stage commits backlog artifacts to main directly. "Stage MUST NOT create git branches" was wrong. Correct: "Stage MUST NOT create feature/chore implementation branches." The allow/deny table handles this precisely.

**MCP gate is registry-driven**: Read `cli_command` from `.autoharness/backlog-registry.yaml` per tool. Do not hardcode tool names or JSONL paths. Stash JSONL (`.autoharness/stash.jsonl`) is incubating — dispatch reads stash via configured backlog tool only.

**Dispatch must be wired into install-harness**: Adding a template to `templates/agents/` is not enough. Must also add to Step 2.4 and Primitive 4 mapping in `install-harness/SKILL.md` or target workspaces won't receive it.

## Copilot Review Fixes (commit babf336)

After PR #36 opened, 4 review comments required fixes:
1. Claim appeared before branch gate in Step 0.5 (item 1 mentioned claim; branch gate was item 3) — reordered
2. "If on `main` or any other non-shipment branch" was ambiguous — tightened to `main` only
3. Same issue in `ship.agent.md.tmpl` with `{{DEFAULT_BRANCH}}`
4. `dispatch.agent.md.tmpl` referenced hardcoded `.autoharness/stash.jsonl` — replaced with registry-driven stash read

## Verification

- 30 tests pass (4 new foundation assertions)
- `stage_role_boundary`, `stage_tool_availability_gate`, `ship_branch_creation_gate`, `ship_tool_availability_gate`

## Compound Learnings Written

- `docs/compound/2026-05-06-p011-branch-before-mutation-design.md`
- `docs/compound/2026-05-06-p010-agent-role-boundaries.md`
- `docs/compound/2026-05-06-p012-tool-availability-gate-and-dispatch.md`
