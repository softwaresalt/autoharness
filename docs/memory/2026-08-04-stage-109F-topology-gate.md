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

- backlogit = authoritative shipment claim/status store; its ClaimShipment is NOT
  a CAS, lock, or lease — it is an UNLOCKED read/check/write with PER-SHIPMENT
  ALL-OR-NOTHING PERSISTENCE + rollback and NO serialization at any scope (local
  same-checkout + cross-machine TOCTOU). The gate is a fail-closed READER/VALIDATOR
  providing pre/post DETECTION + fail-closed remediation (never atomic exclusion),
  and never mutates backlogit internal transitions (external-guard pattern). Do not
  mutate C:/Source/GitHub/backlogit.
- Race/TOCTOU via detect-before (`SHIPMENT_STATE_INCONSISTENT`) + post-claim GLOBAL
  re-verify-after (`CLAIM_VERIFY_FAILED`: exactly-one-active-and-target; pre-retry
  zero-active revalidation) DETECTION (106-S); no bespoke locking, no claimed atomic
  exclusion.
- Active-shipment invariant scope: PHASE-AWARE via the explicit `--phase` flag
  (pre_claim ZERO-active vs post_claim/lifecycle exactly-one-same-target), DETECTION-only,
  NOT serialized by backlogit at any scope — best-effort + fail-closed-on-ambiguity
  (documented limitation — detect-at-sync/CI, no invented lock/lease); exactly-one
  WORKTREE = machine-local.
- Bypass: audited `--force` log + telemetry on every GATE RUN (an operator
  `--force` is auditable whenever the gate executes); a `git --no-verify` hook
  skip runs no gate code and is inherently UNOBSERVABLE locally — required CI is
  the INDEPENDENT non-bypassable backstop, NOT proof the local hook ran
  (Git has no pre-worktree-add hook).
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

## P-013.6 terminal reasoning-escalation repair (2026-08-04)

- Escalation route: `gpt-5.6-sol/openai/high` (distinct from the normal Stage route).
- Reviewed base HEAD: `171c8c97ef9a5aba818831eb662639b397476332`.
- Terminal review/hardening record: **109.004-R — PASS (P0=0, P1=0)**.
- Checkpoint: `.backlogit/checkpoints/checkpoint-20260805-004752.json` (valid v1; supersedes the schema-invalid legacy checkpoint referenced by the escalation payload).

### P1 resolution

`109.003-T` is now the **branch-to-target-shipment** ownership check. Shipment-scoped mode consumes `target_shipment_id` from the shared domain input, loads that explicit shipment read-only before claim, derives the expected branch from that target title, and evaluates the P-011 three cases against that target even when no shipment is currently claimed. It cannot substitute a different currently claimed shipment.

Missing or unresolvable shipment-scoped targets remain INVALID (exit 2). Existence-guarded no-target behavior is reserved strictly for ambient hook/CI mode when central target resolution yields no target; target-independent A2/A3b checks still run fail-closed. This reconciles 109.003-T with 109.002-T, 109.004-T, 109.006-T, 109.017-T, and 109.018-T. Existing dependency `109.003-T -> 109.002-T` remains sufficient.

### Scope and continuity

- P2 stale `blocked -> queued` prose follow-up was already captured by **109.019-T**; no implementation or new task was added.
- No shipment membership, ordering, status, or dependency changes: 114-S=9, 115-S=7, 116-S=3; all queued; task-only manifests preserved.
- Handoff token remains **114-S**.
- Only backlog/planning/memory artifacts changed. No source, templates, config, build, branch/worktree, shipment claim, PR, or merge activity. The two untracked GraphQL files remained untouched.

## PR #296 review-fix cycle 1 (2026-08-04, HEAD 6e3d3b5)

Bounded review-fix of nine Copilot review threads on staging PR #296. Route
claude-opus-4.8/anthropic/high, DARK_MODE_ACTIVE. Only `.backlogit/**`, this
memory doc, and scoped planning/review artifacts touched — no source/templates/
config/build/branch/worktree/shipment-claim/PR/merge activity; `.backlogit/config.yaml`
and the two untracked GraphQL files untouched; C:/Source/GitHub/backlogit read-only.

### Thread 1 — safe-close protected set must not treat every archived shipment as shipped
`109.016-T` (acceptance + description + implementation-notes) now excludes a
predecessor sibling from the protected set ONLY when its owning archived shipment
record has a successful terminal `archived_status: shipped` (or normalized legacy
`done`). Siblings of not-yet-shipped shipments AND siblings whose owning shipment
is archived in any non-shipped terminal state (e.g. `abandoned`) stay protected;
a genuine cascade still halts (P-005, no P-001 bypass). Added a NEGATIVE test
requirement (abandoned archived predecessor -> siblings remain protected) and an
`abandoned` fixture. Coherence propagated to feature DoD (109-F) and review
109.002-R P1-1 finding. Evidence that archived != shipped: `.backlogit/archive/110-S.md`
carries `archived_status: active`, confirming archived records hold varied terminal
statuses.

### Threads 2-4 — remove impossible "gate telemetry observes `git --no-verify`" claim
`012-DL` (BYPASS AUDITING), `109.001-T` (description + a new acceptance bullet),
and archived review `109.001-R` (H4) now distinguish: (a) an AUDITED gate `--force`
RUNS the gate and is observable via force-audit log + per-run telemetry; (b) a
`git --no-verify` hook skip runs NO gate code and emits NO telemetry, so it is
inherently unobservable locally (no local observer at skip time; the gate cannot
record its own non-execution). CI is INDEPENDENT server-side enforcement, NOT proof
the local hook ran. No planning artifact now claims `--no-verify` itself is locally
observable. (012-DL point 3's "hooks are bypassable by design (git --no-verify)" is
a correct capability statement, not an observability claim, and was left intact.
109.007-T/109.008-T only document the bypass NOTE — no observability claim — left intact.)

### Thread 5 — record the cycle-3 109.019-T move in the shipment logs
Appended (history-preserving, no rewrite) paired trace events: `115-S.jsonl`
`shipment_item_removed`(109.019-T) and `114-S.jsonl` `shipment_item_added`(109.019-T),
both timestamped 2026-08-04T17:28:15/16-07:00 with cycle-3 rationale + `items_after`.
Replay verification: 114-S reconstructs to 9 tasks and 115-S to 7 tasks (set-match
against live manifests). Task-only manifests unchanged (9/7/3); no status/dependency
change.

### Threads 6-9 — checkpoint directory hygiene
Removed four malformed ad-hoc (non-v1) checkpoint files that failed
`CheckpointV1` validation. All context they held is already captured above in the
cycle-1/2/3 sections; for the record their unique payloads were:
- `checkpoint-20260804-234452.json` — initial topology-gate session: tasks 001-015,
  shipments A/B/C, stash disposition (E3C25E6D archived; 33CC445C retained;
  34D50F2D/936C68F3 untouched). (See "Stash disposition" + "Artifacts created".)
- `checkpoint-20260804-235504.json` — cycle-1 P1 repair: 109-F removed from 114-S,
  task-only 7/5/3. (See "P1 repair".)
- `checkpoint-20260805-001958.json` — cycle-2: defects P1-1/2/3, backlogit 1.8.0,
  manifests 8/8/3, artifacts created 109.016-019-T + 109.002-R. (See "P1 repair cycle 2".)
- `checkpoint-20260805-003901.json` — cycle-3 final: manifests 9/7/3, 109.019-T moved
  to 114-S, deps 109.017-T->109.002-T & 109.018-T->109.002-T, review 109.003-R PASS.
  (See "P1 repair cycle 3 — FINAL".)
Kept the valid v1 `checkpoint-20260805-004752.json` (terminal shipment-ready). A new
valid v1 checkpoint was written for THIS review-fix session via the supported
backlogit tool. NOTE (out of scope): two additional pre-existing malformed checkpoints
(`checkpoint-20260802-045420.json` = 105-F work, `checkpoint-20260802-192655.json` =
106-F/110-S work) also fail v1 validation but are NOT part of this PR's 109-F scope
and were deliberately left untouched per the operator's exact-file enumeration.

### Validation (cycle 1)
- Shipment manifests remain task-only 9/7/3; dependencies/statuses unchanged (all queued).
- 114/115 logs reconstruct the current manifests (109.019-T move recorded).
- No planning artifact claims `git --no-verify` is locally observable.
- `backlogit checkpoint list` succeeds; the 109-F-scoped live records are all valid v1.
- Boundary preserved: backlog/planning/memory artifacts only; no commit/push (Orchestrator commits).

## PR #296 review-fix cycle 2 (2026-08-04, HEAD f82ead6)

Bounded review-fix of four Copilot round-2 threads on staging PR #296. Route
claude-opus-4.8/anthropic/high, DARK_MODE_ACTIVE. Only `.backlogit/**`, this memory
doc, and scoped planning artifacts touched — no source/templates/config/build/
branch/worktree/shipment-claim/PR/merge activity; `.backlogit/config.yaml` and the two
untracked GraphQL files untouched; C:/Source/GitHub/backlogit read-only. Manifests
remain task-only 9/7/3; no membership/dependency/status change.

### Thread 1 — `109.005-T`: pre-claim ZERO-active, phase-aware invariant
A2 rewritten from "zero or one active -> pass" to a PHASE-AWARE invariant on an
EXPLICIT gate domain-input `phase`: PRE-CLAIM requires ZERO active shipments (any
active -> blocked); POST-CLAIM/later-lifecycle allows EXACTLY ONE active and only
when it is the resolved target. Added a deterministic phase x count matrix
(acceptance + description + impl-notes). Coherence: phase field added to the
`109.002-T` domain-input contract {mode, phase, target_shipment_id, json, force};
tests added to `109.006-T`.

### Thread 2 — `109.001-T`: post-claim GLOBAL re-verify + pre-retry revalidation
A5 post-claim re-verify now re-runs the FULL workspace-global active-shipment
invariant (all shipment records, not just target state): exactly-one-active-and-target
-> proceed; target-still-queued -> ONE retry ONLY after re-running full topology +
the A2 pre-claim ZERO-active precondition + detect-before scan; target blocked / any
other active / inconsistency -> CLAIM_VERIFY_FAILED, no reclaim. Race/rollback +
pre-retry-revalidation test cases added to `109.006-T`. 012-DL RACE/ATOMICITY (point 2)
updated to match.

### Thread 3 — `012-DL`: backlogit atomicity is one-checkout-local, not cross-machine
**[SUPERSEDED by PR #296 review-fix cycle 3 (below): the "atomic CAS within one
synchronized checkout / local filesystem CAS" framing was itself an overclaim and
was fully removed in cycle 3 — backlogit ClaimShipment is an unlocked read/check/write
with per-shipment all-or-nothing persistence + rollback and NO serialization at any
scope (local + cross-machine TOCTOU).]**
Corrected the cross-machine OVERCLAIM everywhere it appeared: backlogit ClaimShipment
is an atomic CAS WITHIN ONE SYNCHRONIZED CHECKOUT (local filesystem CAS), NOT a
real-time cross-machine lease; the active-shipment invariant is checkout-scoped and
best-effort + fail-closed across machines (detect-at-sync/CI), and a centralized remote
lease is explicit out-of-scope future work (no speculative infra invented). Edited
`012-DL` (authority-boundary pt 1, race/atomicity pt 2, rollout pt 6, open-question 1),
`109-F` (description authority boundary + invariant 1, DoD scope-limitation bullet,
goals 2/3/5), `109.011-T` (CI = server-side detect-at-sync, not cross-machine lease),
and this memory's Key-design-decisions bullets. Fail-closed-on-ambiguity preserved.

### Thread 4 — `109.016-T`: verified terminal marker BEFORE archive
**[SUPERSEDED by PR #296 review-fix cycle 3 (below): a pre-archive `archived_status`
check is IMPOSSIBLE — backlogit_ship_shipment transitions AND archives internally and
stamps `archived_status` DURING archive. Cycle 3 replaced this with a SHIP-THEN-VERIFY
contract: ship via the supported op (current shipment only), then verify the archived
record's `archived_status: shipped` AFTER the call returns.]**
Extended the Ship safe-close closure contract: a SUCCESSFUL close MUST transition/
record and VERIFY a successful terminal marker (`archived_status: shipped` via
backlogit_ship_shipment, or normalized legacy `done`) BEFORE archiving — never
archiving a still-`active` record (evidence: archived `110-S.md` carries
`archived_status: active`). The sequence-aware protected-set exclusion now relies on
that VERIFIED marker. Added deterministic 114->115->116 tests + negatives (abandoned
predecessor stays protected; archiving a still-`active` record is rejected). P-015
no-cascade preserved (terminal marker set only for the shipment being closed). 109-F
DoD safe-close bullet updated.

### Validation (cycle 2)
- Contracts coherent across 109-F, 109.001/002/005/006/011/016-T, 012-DL, and memory.
- No artifact claims local backlogit is a cross-machine atomic lease; all such claims
  scoped to one synchronized checkout with documented degraded cross-machine behavior.
- Pre-claim ZERO-active, post-claim exactly-one-same-target, retry full revalidation
  expressed and testable.
- Successful terminal marker established+verified BEFORE archive; protected-set relies on it.
- Shipment manifests/dependencies unchanged: task-only 9/7/3, all `queued`; no size change.
- New valid v1 checkpoint appended via backlogit (not ad-hoc JSON).
- Boundary preserved: backlog/planning/memory artifacts only; no commit/push (Orchestrator commits).

## PR #296 review-fix cycle 3 — FINAL (2026-08-04, HEAD 71ff1b8)

Final bounded review-fix cycle (cycle 3 of 3) of three P1 findings from current-HEAD
local review of staging PR #296 (HEAD 71ff1b8f8bb7411fbc7bda983bdc28e5eccdbc6f). Route
claude-opus-4.8/anthropic/high, DARK_MODE_ACTIVE. Backlogit 1.8.0 source read as
read-only evidence (C:/Source/GitHub/backlogit). Only `.backlogit/**`, this memory doc,
and scoped review artifacts touched — no source/templates/config; no commit/push.

### P1-1 — claim is NOT a checkout-local CAS (remove every CAS/serialization overclaim)
Evidence (backlogit `internal/core/shipment_lifecycle.go` `ClaimShipment`): an UNLOCKED
read -> MoveShipmentStatus(active) -> re-read -> activate-items sequence. Its only
guarantee is PER-SHIPMENT ALL-OR-NOTHING PERSISTENCE with rollback (torn-write avoidance
for a single claim). There is NO lock/lease/CAS and NO serialization at ANY scope: two
concurrent claims in the SAME checkout can both read zero-active and both proceed (LOCAL
TOCTOU), and divergent checkouts race cross-machine. Removed the residual cycle-2
"atomic CAS WITHIN ONE SYNCHRONIZED CHECKOUT / local filesystem CAS" framing everywhere;
described ClaimShipment as per-shipment all-or-nothing PERSISTENCE with rollback + local
AND cross-machine TOCTOU; the gate provides pre/post DETECTION + fail-closed remediation,
NOT atomic exclusion. A workspace-global lock / central lease is explicit out-of-scope
future work. Edited `012-DL` (authority-boundary pt1, race/atomicity pt2, rollout pt6,
DAG note, open-Q1, notes), `109-F` (description authority boundary + invariant 1, DoD
scope-limitation bullet, goals 2/3/5), `109.001-T`, `109.005-T`, `109.011-T`, archived
review `109.001-R` (H1/H2), and this memory's Key-design-decisions bullets.

### P1-2 — callers cannot supply required phase (add explicit `--phase` CLI flag)
The domain-input carried a `phase` field but there was no CLI surface to supply it and
mode alone cannot determine pre_claim vs post_claim (prohibited inference). Added an
explicit required `--phase pre_claim|post_claim|lifecycle` flag for agent shipment-scoped
mode (missing/invalid -> exit 2, never inferred); pre_claim=ZERO-active,
post_claim/lifecycle=exactly-one-same-target; hook/CI ambient resolves deterministically
(default lifecycle). Every agent shipment-scoped invocation now passes the correct phase:
Ship (`109.017-T`) claim=pre_claim, build/worktree/PR/closure=post_claim/lifecycle;
Orchestrator (`109.018-T`) route-to-Ship + cursor-advance=pre_claim. Updated CLI/domain
task `109.002-T`, A2 `109.005-T`, post-claim re-verify `109.001-T`, tests `109.006-T`
(missing `--phase` -> exit 2; phase-driven matrix; post_claim==lifecycle equivalence),
docs `109.010-T`, and feature DoD `109-F`.

### P1-3 — pre-archive `archived_status` verification is impossible (ship-then-verify)
Evidence (backlogit `archive.go` L215 `fm["archived_status"] = oldStatus`): `archived_status`
is stamped DURING archive; `ShipShipment` requires status==active then internally transitions
active->shipped AND archives in one call. A pre-archive field check cannot exist. Corrected
`109.016-T` (A7): Ship uses the SUPPORTED ship op (backlogit_ship_shipment) for the CURRENT
shipment only (P-015 no cascade), then AFTER the call returns verifies the archived
record/provenance reads `archived_status: shipped` (or normalized legacy `done`); absent/
`active`/`abandoned` -> FAIL closure + remediation. Removed the impossible
"terminal-marker-before-archive gate" and the "archive rejected when still active" negative;
replaced with a post-operation `archived_status: active` -> non-shipped -> siblings stay
protected + verification fails. Deterministic 114->115->116 tests and abnormal-archived-state
protection (abandoned predecessor stays protected) preserved. Feature DoD `109-F` safe-close
+ protected-set bullets updated to match.

### Revised topology (unchanged manifests/dependencies)
Task-only shipment manifests unchanged: 114-S=9, 115-S=7, 116-S=3; all tasks `queued`; no
sizes/complexity/dependencies changed. Handoff token to Ship unchanged (shipment sequence
114-S -> 115-S -> 116-S via blocks edges).

### Validation (cycle 3)
- No artifact claims the shipment claim is CAS/locked/atomic serialization; ClaimShipment
  described as per-shipment ALL-OR-NOTHING PERSISTENCE with rollback + local AND cross-machine
  TOCTOU; residual cycle-2 "local filesystem CAS" framing removed.
- Explicit `--phase pre_claim|post_claim|lifecycle` flag exists (109.002-T) and every agent
  shipment-scoped invocation passes it (Ship 109.017-T, Orchestrator 109.018-T; tests 109.006-T;
  docs 109.010-T; consumed by 109.005-T/109.001-T).
- Safe-close ship+archive THEN post-verify provenance contract is executable with backlogit
  1.8.0 (ShipShipment active->shipped+archive; archived_status stamped at ArchiveItem; verified
  after return). No impossible pre-archive verification remains.
- Task-only 9/7/3 manifests and dependencies unchanged.
- Hardening/review (109.001-R H1/H2) + this memory updated coherently; valid v1 checkpoint
  appended via backlogit (not ad-hoc JSON).
- Boundary preserved: backlog/planning/memory artifacts only; no source/template/config;
  no commit/push (Orchestrator commits/pushes).
