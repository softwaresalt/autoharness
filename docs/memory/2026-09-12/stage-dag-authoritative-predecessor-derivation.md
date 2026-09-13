---
title: "Stage session — DAG-authoritative predecessor derivation (165-F / 173-S)"
description: "Stage stash-to-backlog session consuming stash AF2890B7 into feature 165-F, tasks 165.001-T..165.009-T, and shipment 173-S, with a material correction to the triggering framing."
doc_type: memory
source: docs/memory/2026-09-12/stage-dag-authoritative-predecessor-derivation.md
date: 2026-09-12
agent: stage
---

# Stage Session — 2026-09-12 — DAG-Authoritative Predecessor Derivation

> **SUPERSEDED in part (review-fix cycle 1).** This record describes plan
> **revision 1** (commit `4c09e50b`), whose review was later overturned to
> **BLOCKED** by the operator. The `unsequenced_shipment` config key described
> below was removed, 165.003-T was repurposed, 165.007-T was descoped and
> archived, and 165.010-T was added. See
> `docs/memory/2026-09-12/stage-165f-173s-review-fix-cycle-1.md` for the current
> state.

## Outcome

Consumed stash `AF2890B7` into feature **`165-F`**, tasks **`165.001-T` … `165.009-T`**,
and queued shipment **`173-S`** (SHIP-15, priority `critical`).

Route: `claude-opus-5` / `anthropic` / `high`. Non-dark run. Single worktree on
`main`; no spike worktree created.

## Capability status

```text
TOOL_OK: backlogit
DEGRADED_MODE: agent-engram (ENGRAM_DEGRADED), agent-intercom (INTERCOM_DEGRADED),
               graphtor-docs (GRAPHTOR_UNAVAILABLE)
INDEX_SYNC_OK
```

Instruction packs for engram/intercom/graphtor are installed, but no corresponding
MCP servers were reachable this session. File-based exploration used throughout.

Checkpoint recovery: zero active `stage`-owned checkpoints (36 enumerated, all
`resolved`). Two on-disk checkpoint files not returned by the `consumer_id: stage`
scope were inspected and confirmed `agent: ship` / `status: resolved` — correctly
out of scope, not quarantined. Zero-candidate normal startup.

## Most important finding (carry forward)

**The triggering framing was factually wrong, and the plan was corrected before
harvest.**

The orchestrator stated the gate blocked `163-S` by *inferring* archived `162-S`
as a numeric predecessor. Direct reproduction disproved this:

* `backlogit dep list 163-S` → `163-S → 162-S (blocks)` — an **explicit** edge
* `.backlogit/queue/163-S.md` → `dependencies: [162-S]`
* gate token is `PREDECESSOR_CLOSURE_INCOMPLETE` with `closure_complete: null`,
  **not** `PREDECESSOR_NOT_SHIPPED`
* `docs/closure/` has `160-S-…` and `161-S-…` closure artifacts but **no**
  `162-S-*-post-merge-closure.md`

Because `_prior_shipment_id` only appends when the inferred ID is not already
present, and the numerically adjacent shipment *is* `162-S`, the heuristic is a
**no-op** for `163-S`. Retiring numeric adjacency would **not** unblock it.

The real `163-S` cause is a missing closure-evidence artifact, tracked separately
as `165.007-T` with an explicit prohibition on weakening the closure gate.

## Second finding — the advisory divergence is on the closure dimension

`dag-readiness` reports `163-S` ready; `pre_claim` blocks it. Both gates **agree**
on the DAG edge. They diverge because `_dag_all_predecessors_finished` models only
shipped-terminal status and does not model closure evidence at all. Alignment
therefore requires a **shared** closure helper (task `165.005-T`), not merely
deleting the heuristic.

## Third finding — live bootstrap paradox (ACTION REQUIRED BY OPERATOR)

`173-S` declares **no** explicit `blocks` dependency (correct: it is a DAG root),
yet the current gate blocks it:

```text
PREDECESSOR_NOT_SHIPPED: predecessor 172-S is not in a shipped terminal state
```

The shipment that retires the numeric fallback is itself blocked *by* the numeric
fallback. Stage did **not** issue `--force` — per the source bug doc, `--force` must
be human-authorized for a specific named shipment and audited, and must never be
issued by an agent on its own authority.

## Decision recorded

Adopted **Option C** — DAG-authoritative derivation with explicit fail-closed
migration — over hard removal (Option B, rejected as a silent fail-open) and
presentation-only (Option A, rejected as not satisfying operator direction).

Supporting evidence: `docs/compound/` records **three successive defects** in
`_prior_shipment_id`, one of which is still marked unfixed on `main`. Task
`165.002-T` must *prove* retirement renders it moot rather than assume it.

The bug report's presentation-only recommendation was **superseded, not
rewritten** — `docs/bugs/2026-09-11-…` is unmodified.

## Artifacts

| Kind | Path |
|---|---|
| Deliberation | `docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md` |
| Plan (hardened) | `docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md` |
| Review (PASS) | `docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md` |

Plan review: 0 P0, 0 P1, 4 P2, 1 P3 → `PASS`, 1 of 3 cycles used. Reviewer
dispatch degraded (no subagent surface); all personas applied inline.

## Stash dispositions

| ID | Disposition |
|---|---|
| `AF2890B7` | **Consumed** → `165-F` / `173-S`; archived with forward reference |
| `86498B64` | Left in stash, annotated; **recommended next unit**; kept separate (branch-naming ≠ sequencing contract) |
| `9B582824` | Left separate — broad cost epic |
| `97B28746`, `50434138` | Left separate — related follow-ups |
| `58A85283` | Excluded — unrelated |

## Publication note

Only Stage-owned artifacts were committed. Operator work-in-progress left
untouched and uncommitted: `.gitignore`, `.backlogit/checkpoints/checkpoint-20260908-195611.json`,
`docs/bugs/2026-09-11-…`, both `docs/design-docs/…` files, `docs/diagrams/`, and
`scripts/check_eraser_diagrams.py`. Consequence: this session's artifacts reference
`docs/bugs/2026-09-11-…`, which is not yet committed — that cross-reference does not
resolve at HEAD until the operator commits it.

## Next steps

1. Operator decides how `173-S` is claimed given the bootstrap paradox.
2. Ship executes `173-S` in dependency order starting at `165.001-T` (RED tests).
3. After `173-S`, deliberate `86498B64`; sequence rather than parallelize, since
   both touch `src/autoharness/gates/topology.py`.

---

## Correction note (appended cycle 2, 2026-09-12) — do not rewrite the above

This note is **appended, not merged**. Everything above records the state as it
stood at the end of cycle 1 and is left byte-for-byte intact as intake history;
the three statements below were true when written and are no longer true at the
current HEAD.

1. **"Review (PASS) … 1 of 3 cycles used" (line 110).** Superseded twice. The
   review document at that path is now **cycle 3** against plan revision 3, and
   **3 of 3** correction cycles are used. Its counts are 0 P0 / 0 P1 / 2 P2 /
   4 P3. The cycle-1 and cycle-2 review texts remain in git history at their
   respective commits.
2. **"Publication note" (lines 125–130).** `docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md`
   is **no longer uncommitted**. It was committed **byte-for-byte unmodified** in
   the cycle-2 correction commit under explicit operator authorization, as the
   durable intake artefact that `AF2890B7`, this memory, the decision, and the
   plan all forward-reference. The stated consequence — "that cross-reference
   does not resolve at HEAD" — is therefore **resolved**. The rest of that
   paragraph still holds: `.gitignore`, both `docs/design-docs/…` files,
   `docs/diagrams/`, `scripts/check_eraser_diagrams.py`, and the
   `.backlogit/checkpoints/*.json` files remain untouched and uncommitted
   operator work-in-progress.
3. **"Next steps" item 1 (line 134).** The bootstrap paradox is no longer an open
   operator decision. It is resolved by decision D6: **exactly two** audited
   forced `pre_claim` invocations for `173-S` only (pre-branch and immediately
   pre-claim), each under enumerated validity conditions, expiring on successful
   claim or any mismatch, with the post-claim `CLAIM_NOT_OBSERVED` retry
   invocation explicitly **unauthorized**.

Unchanged by this note: the Option A/B analysis, the `_prior_shipment_id`
compound-library evidence, and the stash dispositions table — except that
`AF2890B7`'s archival summary has since been reconciled through an **append-only**
comment event on `165-F` (backlogit exposes no edit path for an archived stash
entry), and the closure-defect disposition moved from `165.007-T` to stash
`FD0CCB42`.

Full cycle detail: `docs/memory/2026-09-12/stage-165f-173s-review-fix-cycle-1.md`
and `docs/memory/2026-09-12/stage-165f-173s-review-fix-cycle-2.md`.
