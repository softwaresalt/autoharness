---
date: 2026-08-05
agent: stage
mode: DARK_MODE_ACTIVE (Stage-only planning; CLI-only backlogit; MCP/Engram/Graphtor/Intercom declared degraded)
feature: 109-F
shipment: 115-S
route: claude-opus-4.8 / anthropic / high
handoff: Stage -> Orchestrator (publish staging artifacts to main), then Ship
---

# Stage session — 114-S closure pre-activation fixes for 115-S

## Objective

Stage the three mandatory 114-S post-merge-closure code defects so they land in
shipment `115-S` **before** its topology-gate activation tasks, plus disposition
the 114-S audit-log discrepancy. No implementation, no shipment claim, no
build/branch/PR; serial cursor held at Stage handoff.

## What was created / changed

### Backlog (all under feature 109-F, added to shipment 115-S)
- **109.021-T** — Gate: post-claim retry becomes a read-only retry-required
  contract (`topology.py`). size **M**, complexity **high**. Design: Option C
  from deliberation — gate never claims (P-001/P-016); returns
  `CLAIM_NOT_OBSERVED` (non-zero, non-blocked); Ship's external
  claim-retry-and-recall loop drives convergence; repair the misleading
  self-advancing-fake-reader test; add delayed and failed first-snapshot tests
  that both expect `CLAIM_NOT_OBSERVED` because those states are
  indistinguishable to the read-only producer.
- **109.022-T** — CLI: telemetry outcome mapping (`cli.py:735-739`) maps any
  non-zero/non-blocked/non-forced (incl. `exit_code==2` and the new
  retry-required token) to `failed`, not `success`. size **S**, complexity
  **low**. Width-isolated CLI surface.
- **109.023-T** — Gate: `closure_complete()` (`topology.py`) enforces
  `closure_status`/releasability — require READY; accept READY_WITH_CONDITIONS
  only with machine-readable per-condition `satisfied:true`+`evidence`; else
  fail closed. Mandatory negative tests + READY backward-compat test. size
  **M**, complexity **medium**. Serialized after 021-T (same file).

### Shipment 115-S manifest (now 10 task-only items, unsized:0, M:7/S:3)
`109.007-T, 109.008-T, 109.013-T, 109.010-T, 109.017-T, 109.018-T, 109.015-T,
109.021-T, 109.022-T, 109.023-T`. No duplicate membership; 116-S unchanged (3).

### Intra-115-S blocks dependency edges added (16 total, acyclic)
- Serialize: `109.023-T -> 109.021-T`.
- Activation-after-fixes: `109.007-T`, `109.008-T`, `109.013-T`, `109.017-T`,
  `109.018-T` each depend on `109.021-T`, `109.022-T`, `109.023-T` (15 edges).
- `109.010-T` (docs) and `109.015-T` (tests) are transitively gated via their
  existing `-> 109.013-T` edge — intentionally not directly blocked (preserves
  parallelism; they are not activation points).

### Feature 109-F
- Appended a DoD bullet recording the pre-activation condition + edges + doc refs.
- Appended a planning/handoff comment (actor `stage`) with the full task list,
  edge map, plan-review PASS, and closure-handoff note.

### Audit-log discrepancy (Defect 4)
- Dispositioned **EXTERNAL / backlogit-owned**, not an autoharness defect, not a
  115-S blocker. Recorded as labeled deferred stash **84D8E6AB** (kind bug,
  priority low). No autoharness fix fabricated; no mutation of
  `C:\Source\GitHub\backlogit`; no synthetic log entry.

## Staging artifacts (committed by Orchestrator to main; Stage did NOT commit/push)
- `docs/decisions/2026-08-05-114s-closure-preactivation-fixes-deliberation.md`
- `docs/plans/2026-08-05-114s-closure-preactivation-fixes-plan.md` (incl. P-006 hardening)
- `docs/reviews/2026-08-05-114s-closure-preactivation-fixes-review.md` (verdict PASS)
- Backlog files: `.backlogit/queue/109.021-T.md|109.022-T.md|109.023-T.md`,
  updated `.backlogit/queue/109-F.md` and `115-S.md`, `.backlogit/stash.jsonl`,
  `.backlogit/logs/109-F.jsonl`.

## Gates / verdicts
- plan-review: **PASS**, 0 P0, 0 unresolved P1 (F-1/F-2 resolved, F-3/F-4 accepted).
- P-006 plan hardening: done (blast radius = gate module + CLI + activation gating).
- Step 3.0 Gate Bypass Guard: not triggered (plan + review both executed).
- doctor: no findings on new artifacts; pre-existing legacy `archived_from_self_ref`
  (62) and `048.00x-T` orphans (3) are unrelated/out-of-scope.

## Handoff / next steps (for Orchestrator -> Ship)
1. Orchestrator publishes the staging docs + backlog changes to `main`.
2. Ship (when routed) claims 115-S and executes 021/022/023-T FIRST (eligibility:
   021 & 022 immediately eligible; 023 after 021; activation set unlocks after all
   three). **Ship scope (RESOLVED 2026-08-05b):** `109.017-T` (Ship wiring) now
   explicitly consumes the `CLAIM_NOT_OBSERVED` retry-required token via a bounded
   reclaim-and-reverify sequence — no longer a handoff caveat.
3. After the three fixes land, amend `docs/closure/114-S-109-F-post-merge-closure.md`
   to `READY` (or add a verified machine-readable `conditions:` block) — a handoff
   note, not part of any fix task's scope.
4. External follow-up 84D8E6AB (backlogit audit-log event emission) tracked in stash
   only; re-triage only on new evidence.

Serial cursor held at Stage handoff. Ship NOT started. No shipment claimed.

---

## Re-Review Addendum (2026-08-05b) — P1 fix: 109.017-T consumes CLAIM_NOT_OBSERVED

**Trigger.** A single P1 was found in the staged 115-S artifacts: `109.021-T`
defines `CLAIM_NOT_OBSERVED` as a read-only retry-required contract, but
`109.017-T` still said every non-zero gate verdict halts and never defined the
consumption path — a half-wired producer/consumer contract (the earlier F-4,
previously a P2 "accepted" handoff note, escalated to P1).

**Repair (backlog-only, CLI; Stage-scoped — no template/source/config edit, no
claim, no commit/push).**
- `109.017-T` acceptance criteria amended: immediate post_claim invocation now
  splits `CLAIM_NOT_OBSERVED` (retry-required, bounded reclaim) from genuine
  ambiguity (terminal `CLAIM_VERIFY_FAILED`). Added the bounded Ship-owned
  reclaim-and-reverify sequence — **double-claim guard first** (re-read status;
  converge without reclaim if the original claim already succeeded despite the
  token), re-run `--phase pre_claim`, perform the actual supported claim exactly
  once (`backlogit shipment claim` / `OP_CLAIM_SHIPMENT_MCP`; **no CAS/lease
  invented**), re-run immediate post_claim; **bound = one cycle** (reconciled
  with the Ship template's existing Step 4a single claim-retry). All other
  non-zero/invalid verdicts stay terminal.
- Added explicit **structural/unit acceptance tests** to `109.017-T` (owner of
  the `_ship.agent.md.tmpl` wiring + scoped assertion files) proving the
  generated Ship instructions contain and order the bounded, token-specific,
  double-claim-guarded path and that terminal verdicts never reclaim.
- `109.017-T` `complexity: medium → high` (de-risked by the fully-specified
  contract → single `size: M` unit; mirrors 109.021-T's M/high precedent).
- Updated description + implementation-notes on `109.017-T` (coordination with
  109.021-T detection-only contract; reuse Step 4a as the guard/bound).
- `109-F` DoD Ship-ordering bullet amended to record the bounded consumption
  (all 13 DoD bullets preserved).

**Dependency/scope.** `109.017-T → 109.021-T` blocks edge already existed
(producer precedes consumer). **No new task, no new dependency.** 115-S remains
task-only **10 members** (M:7/S:3 unchanged).

**Gates.** Plan re-review + P-006 hardening re-run → **PASS, 0 P0, 0 unresolved
P1** (F-4 escalated P2→P1 and resolved). Plan doc gained a Re-Review Addendum;
review doc gained a Re-Review (2026-08-05b) section; both re-affirm PASS.

**Exact files touched this re-review:**
- `.backlogit/queue/109.017-T.md` (acceptance-criteria, description,
  implementation-notes, complexity — via `backlogit update --section` /
  `--complexity`)
- `.backlogit/queue/109-F.md` (DoD bullet — via `backlogit update --section`)
- `.backlogit/logs/109.017-T.jsonl`, `.backlogit/logs/109-F.jsonl` (CLI event log)
- `docs/plans/2026-08-05-114s-closure-preactivation-fixes-plan.md` (Re-Review Addendum)
- `docs/reviews/2026-08-05-114s-closure-preactivation-fixes-review.md` (F-4 escalation + Re-Review section + frontmatter counts)
- `docs/memory/2026-08-05-stage-114s-closure-preactivation-fixes.md` (this addendum)

Stage-only, CLI-only backlogit. No commit/push. Serial cursor still at Stage handoff.

---

## Re-Review Addendum (2026-08-05c) — P1 fix: gate must not classify delayed vs failed on the indistinguishable first snapshot

**Trigger.** A single P1 (F-5) was found in the *producer* artifacts:
`109.021-T` (echoed by the deliberation/plan/memory) required the gate to add a
"failed-claim (**terminal**)" test and to "preserve terminal
`CLAIM_VERIFY_FAILED` for a genuinely failed claim" — i.e. it asked the
**stateless read-only** gate to **distinguish** a delayed claim from a failed
claim on the post-claim snapshot. It cannot: both present identically as target
`queued` + zero active. That producer requirement is unsatisfiable and
contradicts the `CLAIM_NOT_OBSERVED` retry-required contract; `109.017-T` already
owns terminal failure/exhaustion classification.

**Repair (backlog-only, CLI; Stage-scoped — no template/source/config edit, no
claim, no commit/push).**
- `109.021-T` (`backlogit update --description`): the read-only post-claim
  snapshot `queued` + zero active now **consistently emits `CLAIM_NOT_OBSERVED`**
  (retry-required, non-blocked) **without classifying delayed vs failed**. Gate
  reserves terminal `CLAIM_VERIFY_FAILED` only for discriminable ambiguity
  (inconsistent snapshot / two-or-more-active / mismatched-single-active). The
  "failed-claim → terminal" producer test is **removed**; an explicit criterion
  now forbids any producer test requiring terminal `CLAIM_VERIFY_FAILED` for a
  `queued`+zero-active first snapshot.
- `109.017-T`: **NO change required** — its acceptance criteria already put all
  failure/exhaustion classification on the caller (after the one bounded
  double-claim-guarded retry, a **second** `CLAIM_NOT_OBSERVED` → terminal
  `CLAIM_VERIFY_FAILED`; actual ambiguity terminal immediately). Verified by
  re-read.
- `109-F` DoD (`backlogit update --section dod`): Ship-ordering bullet amended to
  record the gate emits `CLAIM_NOT_OBSERVED` for the indistinguishable snapshot
  without classifying delayed vs failed, and that terminal classification is owned
  by `109.017-T`. All 13 DoD bullets preserved (diff confirmed single-bullet
  change).
- Plan / deliberation / review aligned (plan Re-Review Addendum 2026-08-05c;
  deliberation Correction 2026-08-05c; review Re-Review 2026-08-05c + frontmatter
  P1 count 3→4-raised-all-resolved).

**Dependency/scope.** No new task, no new dependency; the `109.017-T → 109.021-T`
blocks edge already existed. **115-S remains task-only 10 members** (M:7/S:3
unchanged).

**Gates.** Plan re-review re-run → **PASS, 0 P0, 0 unresolved P1** (F-5 raised +
resolved 2026-08-05c).

**Exact files touched this re-review:**
- `.backlogit/queue/109.021-T.md` (description — via `backlogit update --description`)
- `.backlogit/queue/109-F.md` (DoD Ship-ordering bullet — via `backlogit update --section dod`)
- `.backlogit/logs/109.021-T.jsonl`, `.backlogit/logs/109-F.jsonl` (CLI event log)
- `docs/plans/2026-08-05-114s-closure-preactivation-fixes-plan.md` (109.021-T section + Re-Review Addendum 2026-08-05c)
- `docs/decisions/2026-08-05-114s-closure-preactivation-fixes-deliberation.md` (Decision 1 Correction 2026-08-05c)
- `docs/reviews/2026-08-05-114s-closure-preactivation-fixes-review.md` (F-5 Re-Review 2026-08-05c + frontmatter counts)
- `docs/memory/2026-08-05-stage-114s-closure-preactivation-fixes.md` (this addendum)

`109.017-T` unchanged (already owned the terminal side). Stage-only, CLI-only
backlogit. No commit/push. Serial cursor still at Stage handoff.
