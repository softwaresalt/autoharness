---
title: "Stage session — 109-F mechanical serial Stage->Ship topology enforcement"
date: 2026-08-04
agent: stage
route: claude-opus-4.8/anthropic/high
mode: DARK_MODE_ACTIVE (P-017, operator-authorized)
stash_scope: E3C25E6D (primary) + 33CC445C (informing spike)
---

# Stage Session: Topology Gate Enforcement (109-F)

Dark-factory Stage run. Own path = stash-to-backlog only (no implementation,
build, branch/worktree creation, shipment claim, PR, or merge).

## Tool status

- `TOOL_OK: backlogit` (MCP + CLI 1.8.0 @ fd8d2c9d)
- `INDEX_SYNC_OK` (661 indexed at start)
- `ENGRAM_DEGRADED` — no engram MCP surface exposed; file-based exploration fallback
- `GRAPHTOR_UNAVAILABLE` — no graphtor MCP surface; file-based doc search fallback
- `INTERCOM_DEGRADED` — operator-declared; local self-contained summaries only

## Artifacts created

| Kind | ID | Note |
|---|---|---|
| Spike | `001-SP` | DAG bounded-adoption investigation (stash 33CC445C); informs 109-F; distinct |
| Deliberation | `012-DL` | Authority boundary / atomicity / manual-dev / bypass / recovery / rollout |
| Feature | `109-F` | Covering feature — `gate pipeline-topology` mechanical enforcement |
| Review | `109.001-R` | plan-harden (P-006) + plan-review = PASS, no P0/P1 |
| Tasks | `109.001-T` … `109.015-T` | 15 tasks, two-axis sized (size + complexity) |
| Shipments | `114-S` / `115-S` / `116-S` | Serial A -> B -> C |

Links: `001-SP --informs--> 109-F`, `012-DL --informs--> 109-F`.

## Serial shipment sequence + cursor

- **114-S (A — deterministic gate core)** — `queued`, ELIGIBLE (cursor / next).
  Items (task-only): 109.002-T(A1), 109.005-T(A2), 109.003-T(A3a), 109.009-T(A3b),
  109.004-T(A4), 109.001-T(A5), 109.006-T(A6).
- **115-S (B — hooks + install adapters)** — `blocked`, blocks-on 114-S.
  Items: 109.007-T(B1), 109.008-T(B2), 109.013-T(B3), 109.010-T(B4), 109.015-T(B5).
- **116-S (C — remote CI validation)** — `blocked`, blocks-on 115-S.
  Items: 109.011-T(C1), 109.014-T(C2), 109.012-T(C3).

## Key design decisions (from 012-DL / 109.001-R)

- backlogit = authoritative cross-machine claim/status lease; the gate is a
  fail-closed READER/VALIDATOR, never mutates backlogit internal transitions
  (external-guard pattern). Do not mutate C:/Source/GitHub/backlogit.
- Atomicity via detect-before (`SHIPMENT_STATE_INCONSISTENT`) + re-verify-after
  (`CLAIM_VERIFY_FAILED`) reuse (106-S); no bespoke locking.
- Cross-machine scope split: at-most-one-ACTIVE-shipment = global; exactly-one
  WORKTREE = machine-local (documented limitation).
- Bypass: audited `--force` log + telemetry-on-every-run; required CI backstop
  is the non-bypassable enforcement point (Git has no pre-worktree-add hook).
- Rollout: staged advisory -> required, matching serial A -> B -> C.
- DAG parallel/multi-worktree execution = permanent NON-GOAL under P-001/P-016.

## Stash disposition

- `E3C25E6D` — ARCHIVED (fully consumed -> 012-DL / 109-F / 114-116-S).
- `33CC445C` — RETAINED as living tracker for DEFERRED DAG-visibility follow-up
  (investigation done as 001-SP; Phase 1/2 adoption need own plan->review->harvest).
- `34D50F2D`, `936C68F3` — UNTOUCHED (out of this turn's scope).

## Handoff to Ship

Handoff token = **shipment 114-S** (single eligible cursor). Successors 115-S/116-S
are dependency-gated (`blocked`). Ship transitions each `blocked -> queued` only
after its upstream shipment closes. Planning artifacts are NOT git-committed
(operator decision — see summary).

## P1 repair (2026-08-04, reviewed HEAD 8d6f83c BLOCKED, P0=0/P1=1)

Reviewer P1: covering feature `109-F` was incorrectly present in shipment 114-S's
manifest even though 114-S is only the FIRST of three partial-feature shipments.
A Ship safe-close of 114-S would archive 109-F before downstream task shipments
115-S/116-S run, breaking parentage. Repository contract for this multi-shipment
sequence requires **task-only manifests** (precedent: 105-S — feature derived via
`parent_id`, not manifest membership). No verified terminal-shipment-includes-feature
pattern exists, so the reviewer-requested task-only shape is used for all three.

Repair applied:
- Removed `109-F` from 114-S manifest. All three shipments are now **task-only**:
  114-S = 7 tasks, 115-S = 5 tasks, 116-S = 3 tasks (15 total = full 109-F scope).
- `covering_feature` render-time projection is now omitted for all three (was only
  on 114-S). Feature parentage stays intact via task `parent_id`, not manifest.
- Sequencing unchanged/verified: 114-S `queued`, 115-S `blocked`-on 114-S,
  116-S `blocked`-on 115-S.

Feature-closure contract (explicit, post-116-S):
- `109-F` stays **open (`queued`)** through 114-S and 115-S — and through 116-S.
- No shipment manifest contains 109-F, so Ship safe-close of 114-S/115-S/116-S
  archives ONLY tasks, never the feature.
- 109-F is closed **separately, only after 116-S completes** (all 15 tasks done).
  Stage/operator performs the feature transition to done/archive as the terminal
  step of the sequence — it is NOT delegated to any shipment safe-close.

## Operator-only decisions remaining

1. Whether to git-commit the .backlogit planning artifacts (Stage left worktree
   unchanged beyond backlogit's own writes; untracked graphql files untouched).
2. CI hard-fail vs warn in required mode (default advisory-first; flip after bake-in).
3. Optional backlogit-recorded worktree-owner token for cross-machine worktree
   observability (deferred; out of current bounded scope).
4. Prioritize the deferred DAG-visibility follow-up (33CC445C) in a future turn.
