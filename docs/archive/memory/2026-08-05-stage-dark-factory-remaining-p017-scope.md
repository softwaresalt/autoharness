---
session: stage
date: 2026-08-05
route: claude-opus-4.8/anthropic/high
mode: dark-factory (serial Stage->Ship, "with all approvals" = deliberate-not-bypass)
baseline_commit: 56376db9f943ce9e85fd11dc5877556cdbb5d1b6
tools: backlogit MCP (TOOL_OK); engram/intercom/graphtor operator-declared DEGRADED (not probed)
---

# Stage session — remaining approved dark-factory P-017 scope

> [!WARNING]
> **SUPERSEDED — DO NOT RELY ON THE FACTS BELOW.** This dark-factory scope memory ends
> with **stale pre-P1-7 semantics** and predates the final publication-review repair and
> the P1-8 owner-exclusive-routing alignment. For the authoritative state, read the
> **final publication memory**
> [`2026-08-05-stage-publication-review-repair-p017.md`](./2026-08-05-stage-publication-review-repair-p017.md)
> (durable key `2026-08-05-stage-publication-review-repair-p017-final`) and the single
> **active Stage checkpoint `checkpoint-20260806-072043.json`** (the current sole active
> valid Stage checkpoint, created 2026-08-06 via the supported checkpoint create/resolve
> lifecycle; the earlier chain `023057 → 034020 → 053524 → 062506` is RESOLVED history — `053524`
> was improperly amended in place after creation and was rolled forward to `062506`, which in turn
> carried the stale F3 DAG ready-set wording that mislabeled `active` as a terminal/non-blocking
> predecessor state and was therefore RESOLVED and rolled forward to `062506`'s successor
> `checkpoint-20260806-072043.json`, which carries the corrected predecessor-finished predicate:
> a `queued` OR `active` predecessor is UNFINISHED and BLOCKS its dependent, only a valid
> `shipped`/`done` closure is no-longer-blocking, and `abandoned`/malformed/unknown fails closed).
> Corrections that supersede this file:
>
> - **13 tasks / 16 task-blocks edges** (110×3, 111×6, 112×4; edges 110:2, 111:10,
>   112:4, no cycles) — this file's "11 tasks / 12 edges" is STALE, and the earlier
>   supersession figure of "12 tasks / 14 edges" is ALSO now STALE (111.005-T AND the
>   owner-agent fail-closed lifecycle task **111.006-T** were both added; 119-S includes
>   111.005-T and 111.006-T). Only 117-S is eligible (serial chain 117-S→118-S→119-S).
> - **Zero-candidate normal startup** — at session start, ZERO active recovery candidates
>   = **no recovery needed ⇒ the Orchestrator continues normal orchestration** (NOT a
>   failure, NOT an operator handoff). The recovery gate engages ONLY when one or more
>   valid candidates exist.
> - **Owner-exclusive recovery routing over ALL THREE operations** — on an explicit,
>   unique operator checkpoint selection + CheckpointV1 `agent`-ownership validation
>   (`stage`/`ship`), the Orchestrator **routes restore/resume/prune EXCLUSIVELY to the
>   owning agent and NEVER restores/resumes/prunes Stage/Ship-owned state directly**; it
>   fails closed AMONG EXISTING CANDIDATES on missing/invalid/ambiguous ownership or a
>   non-unique selection (zero candidates never fails closed).
> - **Overlay** `.github/instructions/backlogit.instructions.md` is **currently ABSENT**
>   and is **installed by 111.005-T** (standard single `artifacts[].checksum`).
>
> Original text is preserved below for append-only provenance.

Staged the exactly-three bounded in-scope items into a strictly serial Stage->Ship
sequence. No source/template/config mutated, no commit/push, no shipment claim,
no branch/worktree created. P-001/P-016 preserved throughout.

## Serial shipment chain (dependency cursor = 117-S)

```
117-S (110-F, DAG readiness reporting)   <- ELIGIBLE (no blocks)
   ^ blocks
118-S (112-F, constrained repair mode)   <- blocked by 117-S
   ^ blocks
119-S (111-F, crash-resumption)          <- blocked by 118-S
```

Ship consumes exactly one at a time, in order: 117-S -> 118-S -> 119-S.

## Features / tasks (all tasks size+complexity assigned; each <=2h, width-isolated)

- 110-F (33CC445C Phase 1, DAG readiness) / 117-S
  - 110.001-T reader in gates/topology.py (S/medium)
  - 110.003-T CLI `gate dag-readiness` (S/low)
  - 110.002-T docs (XS/trivial)
  - Hardening: NOT-REQUIRED (read-only/additive). Review 110.001-R: PASS (P0/P1 clear).
- 112-F (936C68F3 pt2, constrained repair) / 118-S
  - 112.001-T repair-record-status mode (S/high, de-risked)
  - 112.004-T audit+telemetry (S/medium)
  - 112.002-T regression guard + verify + tests (S/medium)
  - 112.003-T docs (XS/low)
  - Hardening: REQUIRED+done (H1-H6). Review 112.001-R: PASS after 1 fix cycle.
- 111-F (34D50F2D candidate d, crash-resumption) / 119-S
  - 111.001-T orchestrator crash-resumption protocol (S/high, de-risked)
  - 111.004-T prune-on-restore instruction (S/medium)
  - 111.002-T degraded fallbacks (S/medium)
  - 111.003-T verify + docs (S/low)
  - Hardening: REQUIRED+done (H1-H5). Review 111.001-R: PASS after 1 fix cycle.

## Decision artifacts

- 013-DL — self-repair lift: Option C CONSTRAINED lift (operator-invoked,
  topology-gated, forward-only queued->active, atomic via existing ClaimShipment,
  audited). Full/silent/backward auto-repair permanently rejected; no locks/CAS.
- 002-SP — crash-resumption boundary spike: PROCEED (orchestration prose over
  existing checkpoint/engram substrate; no external binary change).
- 001-SP (pre-existing) — informed 110-F Phase 1 scope.

## Stash dispositions

- 33CC445C: Phase 1 CONSUMED -> 110-F/117-S; Phase 2 (next-eligible resumption
  helper) OPERATOR-GATED + deferred. Stays ACTIVE (tracker for Phase 2).
- 34D50F2D: candidate (d) CONSUMED -> 111-F/119-S; candidates (a)/(c) DEFERRED.
  Stays ACTIVE (living tracker for a/c).
- 936C68F3: part (2) fully dispositioned via 013-DL -> 112-F/118-S. ARCHIVED.
- 84D8E6AB: OUT OF SCOPE (external backlogit audit-log). UNTOUCHED.

## Reconciliations

- 012-DL: stale queued deliberation from shipped 109-F (exact title match,
  informs->109-F). Terminalized queued->active->done->archived. No scope impact.

## Next steps (Ship)

Claim 117-S first (only eligible). After each shipment ships+closes, the next
unblocks. Do NOT expand scope beyond these three shipments. Candidates (a)/(c)
and 33CC445C Phase 2 remain operator-gated/deferred.

## Repair addendum — 2026-08-06 independent BLOCKED-review repair

An independent review returned BLOCKED on the uncommitted staging set. Repaired
Stage-only, CLI-only (backlogit + read-only git), no source/template/config
mutation, no commit/push/PR/shipment-claim. Re-reviewed until P0/P1 clear
(operator removed the 3-cycle cap). Boundary re-verified clean (only `.backlogit/`
and `docs/memory/` changed).

Findings resolved:

1. **P1 — task-only manifests.** 117-S/118-S/119-S manifests included covering
   feature IDs (110-F/112-F/111-F). Reassembled to task-only:
   117-S={110.001-T,110.003-T,110.002-T}; 118-S={112.001-T,112.004-T,112.002-T,112.003-T};
   119-S={111.001-T,111.004-T,111.002-T,111.003-T}. No duplicate membership.
   Appended a `PROVENANCE RECONCILIATION` comment event to each shipment log
   (append-only integrity preserved; original shipment_created event not rewritten).
2. **P1 — persisted dependencies.** 12 real `blocks` edges added via `backlogit dep add`
   (persist to frontmatter, survive sync): 110.003→110.001, 110.002→110.003;
   111.004→111.001, 111.002→{111.001,111.004}, 111.003→{111.001,111.004,111.002};
   112.004→112.001, 112.002→{112.001,112.004}, 112.003→112.001. No cycles.
   Shipment chain 118-S→117-S, 119-S→118-S intact; only 117-S eligible.
3. **P1 — 112.001-T unreachable precondition.** `gate pipeline-topology`
   early-halts on the target's own SHIPMENT_STATE_INCONSISTENT (topology.py
   `_evaluate_core`: `_detect_before_consistency` before `_active_invariant_check`),
   so precondition (i) could never be observed. Re-deliberated (013-DL Addendum A):
   replaced with a TARGET-AWARE READ-ONLY inspection over EXISTING backlogit reads
   (zero active shipments AND target is the SOLE inconsistency; fail closed on all
   non-target ambiguity), forward-only via existing ClaimShipment, no locks/CAS.
   SKILL-prose (single template family) — width isolation did NOT require a new
   task; 118-S membership unchanged. Added hardening H7; folded into 112.001-T,
   112.002-T (refuse-when-not-sole-inconsistency test), 112-F; review 112.001-R P1-3.
4. **P1 — 111.004-T never-installed instruction.** Standalone checkpoint-recovery
   template had no capability-pack install path. Re-hosted the protocol inside the
   ALREADY-INSTALLED backlogit-pack overlay `backlogit.instructions.md.tmpl` (which
   already threads the checkpoint workflow; backlogit pack is a hard precondition of
   crash-resumption) with harness-manifest installed_checksum/source_checksum +
   verify-harness presence+checksum, install-time variable resolution, technology
   agnostic (engram-degraded fallback). Added hardening H6; folded into 111.004-T,
   111.003-T (verify+checksum AC), 111-F DoD/IMPL-PLAN; review 111.001-R P1-3.
5. **P2 — invalid checkpoint.** `checkpoint-20260805-235555.json` was ad-hoc
   (non-V1, failed validation). Replaced via `backlogit checkpoint create` with a
   valid resumable V1 checkpoint (`checkpoint-20260806-002356.json`, verified by
   `checkpoint get`); removed the invalid untracked Stage-authored file.

Hardening counts now: 110-F none; 112-F H1-H7; 111-F H1-H6. Reviews: 110.001-R PASS;
112.001-R PASS (+2026-08-06 re-review, P1-3 resolved); 111.001-R PASS (+re-review,
P1-3 resolved). No outstanding P0/P1. Serial chain + cursor (117-S) unchanged.

## Repair addendum — 2026-08-05 SECOND independent BLOCKED-review repair

A second independent review returned BLOCKED on the (still-uncommitted) staging set.
Repaired Stage-only, CLI/MCP + read-only file/git surfaces, no source/template/config
mutation, no commit/push/PR/shipment-claim. Re-reviewed until P0/P1 clear (operator
removed the 3-cycle cap). This addendum is append-only and CORRECTS two decisions the
FIRST addendum recorded (items 3 and 4 below supersede the first addendum's items 3/4).
Boundary re-verified clean (only `.backlogit/` and `docs/memory/` changed).

Findings resolved:

1. **P1 — self-repair TOCTOU overstated (112-F).** The prior design described the
   forward re-claim as "provably-safe" / "topology-gated". CORRECTED: the target-aware
   read-only inspection and the ClaimShipment are SEPARATE, UNLOCKED operations — a
   concurrent claim can race between them; the post-condition can only DETECT a second
   active AFTER target activation; and active->queued rollback is FORBIDDEN (backlogit
   1.8.0). Retained the TOCTOU limitation EXPLICITLY (same as 109-F: best-effort
   DETECTION, not prevention; never "provably safe"/serialization/atomic exclusion).
   The GLOBAL post-condition DETECTS post-claim two-active and FAILS CLOSED (audit +
   halt + operator remediation via backlogit's sanctioned lifecycle) with NO forbidden
   active->queued rollback. Required a concurrent-claim/post-condition-failure test.
   Honest ACCEPTABILITY DECISION: the constrained operator-invoked FORWARD repair
   REMAINS ACCEPTABLE (operator-invoked/single-shot; same risk class as 109-F; detect +
   fail-closed bounds blast radius); report-only considered and REJECTED (no safety gain).
   Added H8; folded into 112-F, 112.001-T, 112.002-T (test), 112.003-T (docs),
   112.004-T (audit), 013-DL Addendum B, review 112.001-R (P1-4).
2. **P1 — overlay checksum/install contract (111-F).** CORRECTED the first addendum's
   item 4: `.autoharness/harness-manifest.yaml` uses a SINGLE `artifacts[].checksum`
   field (there is NO `installed_checksum`/`source_checksum` dual-checksum surface), and
   `.github/instructions/backlogit.instructions.md` is NOT installed (no manifest
   artifact, not on disk) — the overlay was falsely assumed "already-installed" and the
   community dual-checksum was wrong. Replanned on the standard first-party contract:
   single `artifacts[].checksum` + targeted SECTION-PRESENCE verification, and added a
   NEW install/tune task **111.005-T** that actually installs the overlay to
   `.github/instructions/backlogit.instructions.md` when the backlogit pack is active and
   records it as a first-party manifest artifact (no source-vs-installed drift assertion).
   DECOMPOSITION CHANGED: 119-S membership now {111.001,111.004,111.002,111.003,111.005};
   deps 111.005->111.004 and 111.003->111.005; no cycles. Folded into 111-F, 111.004-T
   (host-authoring only), 111.003-T (verify), review 111.001-R (P1-4).
3. **P1 — dead-session predicate (111-F).** CORRECTED the first addendum's item 3
   (live-session disambiguation via "checkpoint age threshold AND no heartbeat/lock"):
   checkpoint schema V1 has NO heartbeat/session-lock/lease (only created_at/updated_at)
   and spike 002-SP excluded new checkpoint-schema/runtime plumbing, so "no live
   heartbeat/lock" is UNVERIFIABLE and age alone cannot prove a session dead — automatic
   dead-session recovery is unsafe/unreachable. Replanned: recovery is EXPLICITLY
   OPERATOR-CONFIRMED before ANY restore/prune; no automatic resume, no live-session
   hijack. Candidate (d) stays useful (operator confirmation is sufficient). Folded into
   111.001-T (AC 1/3), 111.003-T (verify gate + docs), 111-F H1, spike 002-SP correction
   addendum, review 111.001-R (P1-5).
4. **P3 — stale provenance normalized.** Removed "topology-gated"/"provably-safe" from
   013-DL Option C + net summary (added Addendum B) and from the archived 936C68F3 stash
   record; updated hardening counts (112-F H1-H8, 111-F H1-H6) in the 936C68F3 and
   34D50F2D stash records and here; append-only shipment logs untouched.

Hardening counts now: 110-F none; 112-F **H1-H8** (H2/H4 clarified detection-not-
prevention; +H8 TOCTOU-explicit); 111-F **H1-H6** (H1 revised operator-confirmed; H6
revised standard single-checksum overlay install via 111.005-T). Reviews: 110.001-R
PASS; 112.001-R PASS (+2 re-reviews, P1-3/P1-4 resolved); 111.001-R PASS (+2 re-reviews,
P1-3/P1-4/P1-5 resolved). No outstanding P0/P1. Task-only manifests:
117-S={110.001,110.003,110.002}; 118-S={112.001,112.004,112.002,112.003};
119-S={111.001,111.004,111.002,111.003,111.005}. Serial chain 117-S->118-S->119-S,
cursor 117-S (only eligible) unchanged. No source/template/config mutated; no
commit/push/PR/claim.

## Repair addendum — 2026-08-05 THIRD independent BLOCKED-review repair

A third independent review returned BLOCKED on the (still-uncommitted) staging set:
one P1 role-ownership defect + three P2 factual defects. Repaired Stage-only,
backlogit MCP/CLI + read-only file/git (incl. read-only inspection of backlogit 1.8.0
source @ fd8d2c9d — NOT mutated); no source/template/config mutation, no
commit/push/PR/shipment-claim. Re-reviewed until P0/P1 clear. Append-only; boundary
re-verified clean (only `.backlogit/` + `docs/memory/` changed).

Findings resolved:

1. **P1 — role-ownership recovery contract (111-F/111.001-T).** The crash-resumption
   recovery drove restore/resume over "the recorded single-active cursor" without
   establishing WHICH checkpoint is chosen when several are unresolved or WHO may
   restore. Verified live: MULTIPLE checkpoints can be ACTIVE concurrently across
   agents (this workspace has a `stage`-owned active checkpoint AND two `ship`-owned
   active checkpoints). CORRECTED: recovery now (a) REQUIRES explicit operator
   selection of a SINGLE checkpoint by filename (Orchestrator never auto-picks);
   (b) VALIDATES the selected checkpoint's CheckpointV1 `agent` ownership
   (`required,oneof=ship stage`, verified in backlogit `internal/events/checkpoint_schema.go`);
   (c) the Orchestrator ROUTES restore/resume/prune EXCLUSIVELY to that owning agent
   (stage-owned => Stage only; ship-owned => Ship only) and NEVER executes
   Stage/Ship-owned restore work itself directly (P-001 role separation); (d) FAILS
   CLOSED (operator handoff) on missing/invalid/ambiguous ownership OR a non-unique
   selection. Uses only the existing `agent` field (no new schema). Added hardening
   H7; folded into 111.001-T (AC 1/2), 111.003-T (verify+docs), 111-F IMPL-PLAN/DoD,
   spike 002-SP correction addendum, review 111.001-R (P1-6).
2. **P2 — checkpoint edge miscount.** `checkpoint-20260806-011931.json` recorded
   "13 blocks edges"; the actual total is 14 (110 group 2 + 111 group 8 + 112 group 4),
   verified via `item_deps`. Corrected through the supported checkpoint lifecycle:
   created a fresh valid V1 checkpoint recording 14 edges + all third-review
   corrections, then resolved the stale 011931 checkpoint (no hand-edit of
   tool-managed state).
3. **P2 — ClaimShipment miscalled "idempotent" (013-DL).** Verified against
   `internal/core/shipment.go::isValidShipmentTransition`: `active->active` is invalid
   and returns `ErrShipmentConflict`, so a repeat claim is REJECTED, not a no-op.
   CORRECTED to STRICTLY SINGLE-SHOT (NOT idempotent) — the rejection IS the
   double-claim guard and preserves the TOCTOU fail-closed behavior. Folded into
   013-DL Addendum C + chosen-direction (iv), 112-F, 112.002-T, 112.003-T,
   review 112.001-R (P2-1).
4. **P2 — nonexistent `blocked` shipment lifecycle (112-F/013-DL/tasks).** Verified:
   backlogit 1.8.0 `ShipmentStatus` is only `queued|active|shipped|abandoned` and
   `isValidShipmentTransition` has no blocked state / no blocked->queued edge. REMOVED
   `blocked` from all supported repair paths; the re-claimable status is `queued` only;
   a legacy/malformed `blocked` record is classified as MALFORMED LEGACY DATA and
   HALTED for operator manual remediation (no fabricated transition). Hardening H3
   recast BLOCKED-HARD-EXCLUSION -> MALFORMED-STATUS-HARD-EXCLUSION. Folded into
   013-DL Addendum C + chosen-direction (i)(b)/(ii)/problem-frame/notes-citation,
   112-F IMPL-PLAN/H3/DoD, 112.001-T, 112.002-T, 112.003-T, review 112.001-R (P2-2).

Hardening counts now: 110-F none; 112-F **H1-H8** (H3 recast to malformed-status
hard-exclusion); 111-F **H1-H7** (H7 role-ownership recovery routing added).
Reviews: 110.001-R PASS; 112.001-R PASS (+3 re-reviews, P1-3/P1-4/P2-1/P2-2 resolved);
111.001-R PASS (+3 re-reviews, P1-3/P1-4/P1-5/P1-6 resolved). No outstanding P0/P1.
Revalidated: task-only manifests unchanged; 14 blocks edges (2+8+4), no cycles; serial
chain 117-S->118-S->119-S with only 117-S eligible; 119-S includes 111.005-T; single
valid active Stage checkpoint (the two pre-existing `ship`-owned 093-S active
checkpoints are unrelated legacy Ship sessions, outside Stage scope); stash + 012-DL
provenance intact. No source/template/config mutated; no commit/push/PR/claim.

> **[SUPERSEDED 2026-08-06 — active-checkpoint roll to `checkpoint-20260806-083118.json`]** Every "current / sole active valid Stage checkpoint is `checkpoint-20260806-072043.json`" statement in this document is SUPERSEDED. The Copilot PR #304 repair rolled the sole active Stage checkpoint forward to **`checkpoint-20260806-083118.json`** (`072043` RESOLVED; full chain `020353 → 023057 → 034020 → 053524 → 062506 → 072043` is RESOLVED history) and the decomposition to **14 tasks** (110×3, 111×7 incl new **111.007-T**, 112×4) / **19 task-blocks edges** (110:2, 111:13, 112:4); 112-F is RE-SCOPED report-only; **936C68F3 stays ACTIVE** (cleanup-triggering `source_stash_id` replaced with the non-cleanup `source_stash_tracker_id` — Ship must leave 936C68F3 active). See `docs/archive/memory/2026-08-06-stage-copilot-pr304-five-finding-repair.md` and memory `2026-08-06-stage-copilot-pr304-provenance-cleanup-083118`.


> **[FURTHER ROLL 2026-08-06 — active-checkpoint roll to `checkpoint-20260806-150505.json`]** The `checkpoint-20260806-083118.json` named in the superseded note above is itself now RESOLVED/superseded via the supported `backlogit checkpoint create`+`resolve` lifecycle. The current SOLE active valid Stage checkpoint is **`checkpoint-20260806-150505.json`**, which corrects the F3 112-F provenance from the cleanup-triggering `custom_fields.source_stash_id` to the NON-cleanup `custom_fields.source_stash_tracker_id: 936C68F3` (936C68F3 stays ACTIVE; Ship MUST NOT archive it). Structural state (14 tasks / 19 task-blocks edges / manifests / review verdicts) UNCHANGED. `checkpoint-20260806-083118.json` preserved as RESOLVED history.
