---
title: Stage session — Copilot PR #322 review-fix cycle 2 (115-F / 123-S)
date: 2026-08-09
agent: stage
route: claude-opus-5/anthropic/high
feature: 115-F
shipment: 123-S
review: 115.001-R
phase: review-fix
status: complete
---

# Stage session — PR #322 review-fix cycle 2

Bounded Stage review-fix cycle addressing all five valid Copilot review findings on
PR #322. Scope was strictly limited to 115-F / 123-S and the referenced in-scope
stash tracker text. No implementation, no branch/worktree, no commit/push/PR, no
GitHub thread reply or resolution, no shipment claim or status mutation.

## Session start state

* Branch `chore/stage-123-s-20260809`, clean tree, HEAD `c8d95207`, merge-base
  `efeba82b`.
* `TOOL_OK: backlogit` v1.8.0. `INDEX_SYNC_OK` (746 artifacts).
* Engram / intercom / graphtor MCP tools not exposed this session →
  `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`; file-based
  fallback used. Non-blocking.
* Checkpoint scan (unfiltered, consumer `stage`): 22 total, **0 quarantined, 0
  validation errors, 0 active** → zero-candidate normal startup, no recovery.

## The corrected contract

The central defect was an **impossible analyzer signature**. The plan claimed a
7-branch analyzer whose first branch was `degraded`, but `BacklogUnavailableError`
is raised by `readers.list_shipments()` — before the `shipments` tuple exists and
before `compute_dag_readiness` is ever called. Both analyzer inputs are absent on
exactly the path that would signal degradation, so the branch was **unreachable by
construction**: dead, untestable code, and an acceptance criterion that could not
be honestly satisfied.

Resolved by **separation, not by adding an input**:

| | Owner | Outcomes |
|---|---|---|
| `degraded` (outcome 1) | CLI — 115.002-T | Synthesized deterministically in the `BacklogUnavailableError` handler, **before** the analyzer is invoked |
| Outcomes 2–7 | Analyzer — 115.001-T | `cycle_detected`, `ambiguous_provenance`, `multi_active_anomaly`, `resume_active`, `ready_set_head`, `no_candidates` |

The canonical 1–7 gate numbering was **retained** so every cross-reference in the
plan, feature, tasks, and future docs stays stable. The analyzer must never emit
`degraded` and must not take an `is_degraded` sentinel input (rejected: it would
let a caller assert degradation while passing successfully-read data).

Other contract corrections:

* **Tie-break belongs to branch 6** (`ready_set_head`) — the only branch selecting
  among multiple candidates. Never branch 5 (`resume_active`), which has exactly
  one active shipment and nothing to tie-break.
* **`next_eligible_detail` is always two arrays.** On the degraded path it is
  exactly `{"candidate_ids": [], "offending_ids": []}` — never `{}`, never null.
  This preserves the always-indexable invariant and keeps the degraded key set
  identical to ok/empty.
* **backlogit 1.8.0 shipment status enum is exactly `{queued, active, shipped,
  abandoned}`.** `blocked` is an *item* status (`models.StatusBlocked`, set by
  `ReturnBlockedItem`) on a different artifact. A `blocked` value in a shipment
  status field is malformed legacy data that must fail closed to report/operator
  handoff — never normalized, coerced, or treated as a valid lifecycle state.

## Artifacts changed

* `docs/plans/2026-08-09-dag-next-eligible-resumption-advisory-plan.md` —
  resolution-order ownership split + reachability proof, tie-break heading
  corrected to branch 6, detail-shape row tightened, new hardening item **H4b**.
* `.backlogit/queue/115-F.md` — description + DoD reconciled.
* `.backlogit/queue/115.001-T.md` — title, AC2/AC3/AC7/AC9, new AC10, description.
* `.backlogit/queue/115.002-T.md` — AC1/AC5, new AC9/AC10, description.
* `.backlogit/queue/115.003-T.md` — AC3/AC4/AC5, description (docs coherence).
* `.backlogit/stash.jsonl` — 936C68F3 enum corrected in place plus an appended
  `ENUM CORRECTION` annotation, applied via the supported `backlogit stash edit`
  so the stash log and index stay coherent. Entry **remains ACTIVE**.
* `.backlogit/archive/115.001-R-*.md` — cycle-2 findings, re-review, structural
  checks, decisions, summary, title.
* `docs/memory/2026-08-09-stage-pr322-review-fix-cycle2.md` — this file.

## Verdict and validation

* **Plan review: PASS. P0 = 0, P1 = 0.** 2 of 3 fix cycles used; cap not reached.
* `gate dag-readiness --json` → `status: ok`, `ready_set == ["123-S"]` (sole
  eligible), no cycle, no degraded reason.
* `gate pipeline-topology --json` (ambient) → PASS, `active_shipment_ids == []`,
  `WORKTREE_TOPOLOGY_OK`, single implementation worktree, no spike worktree.
* `gate pipeline-topology --shipment 123-S` → `BRANCH_MISMATCH`, **expected**: the
  Stage chore branch is correctly refused as 123-S's execution branch, confirming
  Ship's branch/claim authority is intact and unexercised.
* `git diff --check` (worktree and vs merge-base `efeba82b`) → exit 0; only
  informational CRLF notices.
* `backlogit sync` → 746 artifacts indexed.
* 123-S: `queued`, task-only manifest (115.001-T/115.002-T/115.003-T), covering
  feature 115-F. Unmutated.

## Next steps

1. **Orchestrator**: publish the UNCOMMITTED artifact set above. Nothing is
   committed — this was left deliberately for Orchestrator per the operator.
2. **Ship** (after publication and an explicit operator handoff): claim 123-S and
   execute 115.001-T → 115.002-T → 115.003-T in dependency order.
3. Do **not** archive stash 936C68F3 — it remains the living tracker for the
   deferred true-auto-repair portion, and 112-F's provenance deliberately uses
   `source_stash_tracker_id` so automated cleanup will not retire it.

## Reusable lesson (candidate compound learning, not yet promoted)

A fail-closed branch must be sited where its triggering condition is actually
**observable**. An anomaly branch placed behind inputs that cannot exist on the
anomaly path is dead code masquerading as a safety guarantee. This is the dual of
the existing `2026-08-07-copilot-review-fix-introduces-new-filter-bug` learning:
that one warns against a filter that *hides* an anomaly; this one warns against a
guard positioned where the anomaly can never *arrive*.
