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

> **SUPERSEDED by cycle-2 repair (see "P1 repair cycle 2" below).** 115-S/116-S are
> now `status: queued` (not `blocked`); serial order is enforced purely by `blocks`
> edges. Counts changed: A=8, B=8, C=3 (19 tasks). The list below is the cycle-1 state.

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

> **SUPERSEDED by cycle-2 repair.** The `blocked -> queued` transition below is
> UNSUPPORTED by backlogit 1.8.0 and must NOT be attempted. See the corrected
> handoff in "P1 repair cycle 2".

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

## P1 repair cycle 2 (2026-08-04, reviewed HEAD fa6858e BLOCKED, P0=0 / P1=3)

Reviewed HEAD fa6858e (prior feature-in-first-manifest defect already fixed). Three
high-severity contract defects repaired. Route claude-opus-4.8/anthropic/high,
DARK_MODE_ACTIVE. Review evidence: **109.002-R** (PASS). No source/template/config
mutated by Stage; only backlog + planning + memory artifacts.

### P1-1 — safe-close reconcile falsely protects archived predecessor siblings
The installed Ship `shipment-reconcile` safe-close contract (`_ship.agent.md`
closure tasks b/c, L484-522) computes the protected set as the covering feature +
every sibling task NOT in the manifest, scanning both `.backlogit/queue/` and
`.backlogit/archive/`, and requires every protected-set member to remain in
`queue/`. For a feature split across serial shipments (109-F -> 114/115/116-S), a
predecessor shipment's LEGITIMATELY archived tasks trip the baseline/verify cascade
halt, so 115-S/116-S can never safe-close.
**Fix:** added **109.016-T (A7)** to **114-S** — make protected-set computation
multi-shipment-per-feature sequence-aware (exclude siblings whose owning shipment
already shipped/archived; still halt on genuine cascades — NO P-001 bypass). Placed
in 114-S so the corrected contract is installed BEFORE 115-S/116-S close (114-S
itself closes cleanly under the current contract — no predecessor archived yet).

### P1-2 — impossible blocked -> queued handoff
VERIFIED against `C:/Source/GitHub/backlogit/internal/core/shipment.go`
`isValidShipmentTransition` (L336-345): supported transitions are ONLY
`queued->active`, `active->shipped`, `active->abandoned`. `blocked` is not a valid
`ShipmentStatus` constant; a blocked shipment is a dead end. The prior handoff
required `blocked -> queued` (impossible).
**Fix (data):** 115-S and 116-S corrected `blocked -> queued`; `blocks` edges
retained (115-S->114-S, 116-S->115-S). Serial eligibility is now enforced by the
orchestrator hard blocks-eligibility gate — a `queued` successor with an unshipped
blocking predecessor is never eligible (verified: 114-S no predecessor = ELIGIBLE;
115-S/116-S suppressed). **Fix (durable):** added **109.019-T (B8)** to correct the
Orchestrator/Ship sequencing prose (remove blocked->queued; queued-from-start +
blocks-edge suppression). Stale compound doc
`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md` corrected inline.

### P1-3 — missing Ship/Orchestrator gate-invocation integration
The feature promised gate enforcement before claim, branch/worktree creation, build,
push, PR, closure, but no task wired the AGENT-orchestrated invocation points (git
hooks only cover commit/push).
**Fix:** added **109.017-T (B6)** — Ship agent invocation at claim / worktree /
build / PR / closure; **109.018-T (B7)** — Orchestrator invocation at route-to-Ship
eligibility + cursor-advance. Both carry structural acceptance assertions. Feature
DoD updated with the two new invocation-coverage + sequence-aware-reconcile bullets.

### Revised topology (task-only manifests, 19 tasks, each exactly once)
- **114-S (A — core)** — `queued`, **ELIGIBLE (cursor / next)**. 8 tasks:
  109.001-T, 109.002-T, 109.003-T, 109.004-T, 109.005-T, 109.006-T, 109.009-T,
  **109.016-T (A7, reconcile sequence-awareness — new)**.
- **115-S (B — hooks/install/integration)** — `queued`, blocks-on 114-S (suppressed).
  8 tasks: 109.007-T, 109.008-T, 109.010-T, 109.013-T, 109.015-T,
  **109.017-T (B6)**, **109.018-T (B7)**, **109.019-T (B8)** — all new B6/B7/B8.
- **116-S (C — CI backstop)** — `queued`, blocks-on 115-S (suppressed).
  3 tasks: 109.011-T, 109.012-T, 109.014-T.

### Corrected handoff to Ship (supersedes the stale section above)
Handoff token = **shipment 114-S** (single eligible cursor). All three shipments are
`status: queued`; 115-S/116-S are dependency-gated by `blocks` edges and are NOT
eligible until their predecessor reaches `shipped`. **Do NOT attempt any
`blocked -> queued` transition** — it is unsupported. Ship claims a successor
(`queued -> active`) only after its predecessor is shipped AND post-merge closure
(incl. P-020 compaction) is complete. Ordered cursor: 114-S -> 115-S -> 116-S.

Artifacts touched this cycle: created 109.016-T / 109.017-T / 109.018-T / 109.019-T
(sized size+complexity); added to manifests 114-S (016) and 115-S (017/018/019);
115-S & 116-S status blocked->queued; 109-F DoD updated; review 109.002-R (PASS);
compound status-constraints doc corrected; this memory. Index re-synced (686).

## P1 repair cycle 3 — FINAL (2026-08-04, reviewed HEAD b2efcf3 BLOCKED, P0=0 / P1=2)

Third and final bounded review-fix cycle. Both P1s RESOLVED (not deferred). Route
claude-opus-4.8/anthropic/high, DARK_MODE_ACTIVE. Review evidence: **109.003-R** (PASS).
No source/template/config mutated by Stage; only backlog + planning + memory artifacts.

### P1-1 — sequencing repair ships too late (109.019-T was in 115-S)
The installed Orchestrator attempts the invalid `blocked -> queued` cursor-advance
immediately AFTER 114-S closes (when advancing to 115-S) — before 115-S could ever run
the durable correction (109.019-T, B8). **Fix:** MOVED 109.019-T from 115-S to 114-S so
the corrected queued-from-start + blocks-suppression contract is installed by shipment A,
before the 114 -> 115 transition. Added a MANDATORY post-predecessor-closure CONTEXT
RELOAD requirement to 109.019-T acceptance + 109-F DoD: after 114-S merges and P-020
closure completes, the Orchestrator RELOADS current `main` agent instructions before
cursor-advance / 115-S selection, so the freshly-installed corrected prose is the version
in effect (never a stale in-context copy). 114-S now holds BOTH 114->115 prerequisites:
109.016-T (safe-close sequence-awareness) + 109.019-T (sequencing correction + reload).

### P1-2 — pre-claim gate not bound to a selected shipment
109.002-T's CLI contract lacked a required shipment identifier while
109.004-T/109.017-T/109.018-T needed shipment-scoped validation. **Fix:** added a
`--shipment <SHIPMENT_ID>` target flag: REQUIRED and fail-closed in agent shipment-scoped
modes (pre-claim / route / cursor-advance; missing -> exit 2, never fail-open), carried on
the gate domain-input {mode, target_shipment_id, json, force}. 109.004-T readiness evaluated
against the explicit target; 109.017-T (Ship) passes the shipment being claimed/operated on
at each of the five lifecycle points; 109.018-T (Orchestrator) passes the candidate/successor
shipment at route + cursor-advance (both now carry an explicit `blocks` dep on 109.002-T).
Non-shipment hook/ci contexts (109.007-T/109.008-T/109.011-T) use a DETERMINISTIC implicit
target-resolution contract (currently-claimed shipment / current-branch slug), running
ambient-only invariants fail-closed + existence-guarded when no target resolves — a
deliberately non-shipment-scoped mode that does NOT weaken fail-closed agent mode. Tests
(109.006-T) and docs (109.010-T) + feature DoD updated accordingly.

### Revised topology (task-only manifests, 19 tasks, each exactly once)
- **114-S (A — core)** — `queued`, **ELIGIBLE (cursor / next)**. **9 tasks:** 109.001-T,
  109.002-T, 109.003-T, 109.004-T, 109.005-T, 109.006-T, 109.009-T, 109.016-T,
  **109.019-T (B8, MOVED from 115-S this cycle)**.
- **115-S (B — hooks/install/integration)** — `queued`, blocks-on 114-S (suppressed).
  **7 tasks:** 109.007-T, 109.008-T, 109.010-T, 109.013-T, 109.015-T, 109.017-T, 109.018-T.
- **116-S (C — CI backstop)** — `queued`, blocks-on 115-S (suppressed). 3 tasks:
  109.011-T, 109.012-T, 109.014-T.

### Corrected handoff to Ship (unchanged token)
Handoff token = **shipment 114-S** (single eligible cursor). All three shipments `queued`;
115-S/116-S dependency-gated by blocks edges — NOT eligible until the predecessor is
`shipped` AND post-merge closure (incl. P-020 compaction) completes. Do NOT attempt any
`blocked -> queued` transition. After 114-S closes, the Orchestrator must RELOAD current
main instructions before advancing to 115-S. Ordered cursor: 114-S -> 115-S -> 116-S.

Artifacts touched cycle 3: moved 109.019-T (115-S->114-S manifests); amended 109.002-T,
109.004-T, 109.006-T, 109.007-T, 109.008-T, 109.010-T, 109.011-T, 109.017-T, 109.018-T,
109.019-T; added deps 109.017-T->109.002-T and 109.018-T->109.002-T; 109-F DoD updated;
review 109.003-R (PASS); this memory. Index re-synced (687). No sizes changed (all tasks
remain two-axis sized).
