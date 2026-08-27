---
title: "Compacted memory — Dark-factory bounded sessions (082-F/113-F/114-F, 120-S/121-S/122-S) + 33CC445C Phase 2 DAG-readiness advisory (115-F/123-S) + PR #322 review-fix"
doc_type: memory
memory_class: compacted
created: 2026-08-08
scope: stage-session-batch
shipment: [120-S, 121-S, 122-S, 123-S]
feature: [082-F, 113-F, 114-F, 115-F]
pr: [322]
consolidates:
  - docs/archive/memory/2026-08-08-stage-p017-dark-factory-session.md
  - docs/archive/memory/2026-08-09-stage-dark-factory-33cc445c-phase2.md
  - docs/archive/memory/2026-08-09-stage-pr322-review-fix-cycle2.md
---

# Compacted: Dark-factory bounded Stage sessions (2026-08-08 → 2026-08-09)

## Session 1 — P-017 dark-factory activation, four frozen scope units (2026-08-08)

AFK dark-factory session (route `claude-opus-4.8`/`anthropic`/`high`, `visibility_mode=
local-only/degraded`). Zero active crash-resumption candidates at start (21 checkpoints,
0 quarantined) — correctly treated as **normal steady-state startup**, not a failure.

**Frozen scope, 4 units triaged**:
1. `082-F` (mandated first cursor) → 3 tasks → shipment **`120-S`** (first eligible, no
   predecessor).
2. `F02FD596` + `E8B5B3C5` (routing group, archived — fully consumed) → feature **`113-F`**,
   5 tasks (high-complexity items de-risked by hardening docs, sizes held ≤M) → shipment
   **`121-S`** (`depends_on 120-S`).
3. `BED0DDED` → **deferred, external-blocked, no shipment created**. Root cause: the external
   `backlogit` binary hardcodes `.backlogit` as its workspace storage root
   (`WorkspaceStorageRoot`, `internal/core/workspace.go:56`, ~31 literal occurrences at the
   time) with no directory-override env/config knob (only `BACKLOGIT_LOG_LEVEL`/`_FORMAT`
   exist). An autoharness-side-first `.backlogit`→`.backlog` rename would silently split state
   between the two tools. Fail-closed defer; kept as an active living tracker.
4. `47971057` (bounded increment) → feature **`114-F`**, 3 tasks → shipment **`122-S`**
   (`depends_on 121-S`). Full runtime-provisioning execution and open supply-chain/OS-matrix/
   version-channel/elevation/offline/rollback design questions explicitly deferred pending
   operator input — **not** something an agent should design by guesswork.

All 4 reviews PASS, no unresolved P0/P1. Serial chain `120-S → 121-S → 122-S`. Living trackers
left untouched/active: `34D50F2D`, `33CC445C`, `936C68F3`, `84D8E6AB`.

## Session 2 — 33CC445C Phase 2: DAG-readiness advisory resumption cursor (2026-08-09)

Bounded dark-factory session (route `claude-opus-5`/`anthropic`/`high`) re-triaging exactly 6
previously-deferred stash entries with fresh evidence:

| Stash | Disposition | Evidence |
|---|---|---|
| `84D8E6AB` | Stays active | Repo-wide search for `shipment_status_changed` = 0 hits; re-triage condition unmet |
| `BED0DDED` | Still external-blocked, stays active | Re-verified against `backlogit` HEAD `fd8d2c9d` (v1.8.0): hardcoded `.backlogit` literals **grew to 245**; still no override |
| `47971057` | Bounded increment already shipped (114-F/122-S); provisioning still deferred, stays active | Design questions still operator-unanswered |
| `34D50F2D` | Candidate (d) shipped (111-F/119-S); (a)/(c) deferred, stays active | Stale in-flight claims/checkpoint pointers superseded and re-verified resolved |
| `936C68F3` | Report-only slice shipped (112-F/118-S); auto-repair still unsupported, stays active | Re-confirmed no `active→queued` edge, single-shot `ClaimShipment`, no record-only repair transition |
| `33CC445C` | **Fully consumed → archived** | Phase 1 already shipped (110-F/117-S); Phase 2 re-validated as useful and non-duplicative, then harvested |

**Decision (014-DL, Option C)**: build an **advisory-only** deterministic "next eligible
shipment" resumption cursor. Harvested feature `115-F` + 3 tasks (`115.001-T` analyzer M/medium,
`115.002-T` CLI S/low, `115.003-T` docs S/medium) → shipment **`123-S`** (task-only, sole
eligible — the handoff token).

**Key design decision — advisory-only is load-bearing, not incidental**: the already-shipped
Phase 1 DAG-readiness tool declared a permanent non-goal that the gate will never "select or
execute a 'next' shipment automatically." Phase 2 preserves that: the prohibited behavior is
automatic selection-**for-execution**; a read-only recommendation a human must still act on is
categorically different. Deleting or softening that non-goal was flagged as a P0 defect class.

**Resolution order** (resumption-first, anomaly-first): `degraded` → `cycle_detected` →
`ambiguous_provenance` → `multi_active_anomaly` → `resume_active` (one active shipment is
always the cursor — never recommend starting new work) → `ready_set_head` → `no_candidates`.
Tie-break: descending downstream-dependent fan-out, then ascending id.

**Review finding (root-caused during first review pass)**: the first draft's 6-branch design
buried "ambiguous provenance" in prose rather than giving it its own branch, so a single active
shipment with **corrupt** provenance had no matching branch and would have silently fallen
through to `resume_active` — recommending resumption of a corrupt record. This is the same
shape of defect as the compound learning `2026-08-07-copilot-review-fix-introduces-new-filter-
bug.md` (a filter that hides an anomaly instead of surfacing it). Fixed by promoting
`ambiguous_provenance` to its own anomaly-first branch with a distinct reason code.

Cross-validated against the already-shipped Phase 1 tool: `autoharness gate dag-readiness
--json` independently reported `ready_set: ["123-S"]`, confirming the cursor.

## Session 3 — Copilot PR #322 review-fix cycle 2 (115-F / 123-S, 2026-08-09)

**Central defect (found and fixed)**: the plan's analyzer signature was **unreachable by
construction**. It specified a 7-branch analyzer whose first branch was `degraded`, but
`BacklogUnavailableError` is actually raised by `readers.list_shipments()` — **before** the
`shipments` tuple exists and before the analyzer function is ever invoked. Both analyzer
inputs are absent on exactly the path meant to signal degradation, making that branch dead,
untestable code with an acceptance criterion that could never be honestly satisfied.

**Fix — resolved by ownership separation, not by adding an input**: `degraded` (outcome 1)
moved to the **CLI** (`115.002-T`), synthesized deterministically in the
`BacklogUnavailableError` exception handler *before* the analyzer is invoked. Outcomes 2–7
(`cycle_detected`, `ambiguous_provenance`, `multi_active_anomaly`, `resume_active`,
`ready_set_head`, `no_candidates`) remain owned by the **analyzer** (`115.001-T`). The
canonical 1–7 numbering was retained for cross-reference stability. An alternative fix
(passing an `is_degraded` sentinel input to the analyzer) was **rejected** — it would let a
caller assert degradation while still passing successfully-read data, defeating the point of
the guard.

**Other contract corrections in the same cycle**:
* Tie-break logic belongs only to branch 6 (`ready_set_head`, the only branch selecting among
  multiple candidates) — never branch 5 (`resume_active`, which has exactly one active
  shipment and nothing to tie-break).
* `next_eligible_detail` must always be exactly two arrays (`candidate_ids`, `offending_ids`),
  even on the degraded path (`{[], []}`, never `{}` or null) — preserves an always-indexable
  response shape across all outcomes.
* **backlogit 1.8.0's shipment status enum is exactly `{queued, active, shipped, abandoned}`**
  — `blocked` is an **item**-level status (`models.StatusBlocked`), not a valid shipment
  status; a `blocked` value found in a shipment status field is malformed legacy data that
  must fail closed to report/operator handoff, never be normalized or coerced.

Plan review: PASS, P0=0/P1=0, 2 of 3 fix cycles used (cap not reached). `gate dag-readiness
--json` confirmed `ready_set == ["123-S"]`; `gate pipeline-topology` confirmed the Stage chore
branch correctly refuses to be treated as 123-S's execution branch (`BRANCH_MISMATCH`,
expected — Ship's claim authority is intact and unexercised).

**Reusable lesson (flagged as a compound-learning candidate, not yet promoted)**: a
fail-closed anomaly branch must be sited where its triggering condition is actually
**observable**. A branch placed behind inputs that cannot exist on that path is dead code
masquerading as a safety guarantee — the **dual** of the earlier filter-hides-anomaly lesson
(that one warns against hiding an anomaly that arrives; this one warns against a guard the
anomaly can never reach).

## Cross-cutting learnings (this batch)

1. **Zero active recovery/resumption candidates at session start is normal, not degraded** —
   both sessions 1 and 2 treat this explicitly as steady-state, distinct from an actual crash-
   recovery scenario.
2. **Re-verify externally-blocked deferrals with fresh evidence each cycle rather than
   carrying forward a stale disposition** — session 2 re-checked `BED0DDED` and `936C68F3`
   against the live upstream `backlogit` source rather than trusting the prior session's
   findings, and found the blocking literal count had grown (31→245), reinforcing rather than
   weakening the defer decision.
3. **Advisory-only vs. auto-select is a permanent, explicit non-goal that must be re-affirmed
   whenever a "next" recommendation feature is extended** — never let convenience erode it into
   automatic selection-for-execution.
4. **Ownership separation prevents "unreachable by construction" dead branches** — when a
   condition can only be true before a component's inputs exist, that component cannot be the
   one to detect it; move detection to the actual boundary (here: CLI's exception handler, not
   the pure-function analyzer).
5. **Anomaly branches and hidden-anomaly filters are dual failure modes** — one hides an
   anomaly that arrives; the other guards a place the anomaly can never arrive. Both must be
   checked for when reviewing gate/analyzer logic.

## Outcome

All four shipments (`120-S`, `121-S`, `122-S`, `123-S`) staged and left uncommitted for the
Orchestrator to publish; `123-S` is the sole eligible handoff token to Ship at batch end (its
predecessors from session 1, `120-S`/`121-S`/`122-S`, form an independent serial chain staged
the day before). No implementation, build, branch, commit/push, PR, or shipment claim was
performed in any of the three sessions.
