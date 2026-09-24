---
title: "Stage session — 183-S attempt-05 `L1` remediation (cleanup lifecycle split)"
date: "2026-09-19"
agent: stage
---

# Stage session — 183-S attempt-05 `L1` remediation (cleanup lifecycle split)

- **Date**: 2026-09-19
- **Agent**: Stage
- **Branch**: `chore/stage-176-s-workflow-defects` (base HEAD `5a2c5112`)
- **Authorization**: operator-bounded — attempt-05 `L1` (P2) only, plus
  mechanically necessary follow-up-stash accuracy
- **Degraded capabilities**: engram circuit-open (not retried, per operator);
  intercom unavailable/local-only; graphtor-docs not exposed

## The defect

`L1` was a constructibility contradiction, not a logic error. Plan revision 5
and `177.003-T`'s record both mandated that the eight-line `CLEANUP_` evidence
block be written **in the same commit that removes**
`.github/workflows/spike-177-isolation-probe.yml`. Two of its fields carried
values that only that commit's own creation defines:

| Field | Required value | Why unsatisfiable at the mandated write point |
|---|---|---|
| `CLEANUP_REMOVED_COMMIT` | the removal commit's SHA | a commit's identity is a function of its content, so it cannot contain its own SHA |
| `CLEANUP_TIP_OBSERVATION` | tip SHA + clean-tree observation | the tree is dirty while the block is being authored; it cannot be observed clean from inside the change that cleans it |

Consequence: `C4` and `C5` were unsatisfiable on a **first** emission, cleanup
resolved `CLEANUP_FAILED | EVIDENCE_MISSING|EVIDENCE_MALFORMED`, and the unit
composed to `ISOLATION_CLEANUP_FAILED` on every correct execution — a spurious
cycle that blocked `181-S` harvest. Fail-closed, hence P2 rather than P1.

## The fix — ordering, not relaxation

Split the cleanup lifecycle into two tasks and two commits:

1. **`177.003-T`** lands the findings artifact and deletes the workflow in one
   commit (**the removal commit**). It now writes **no `CLEANUP_` line at all**.
   It must not amend or rebase that commit after `177.007-T` observes it.
2. **`177.007-T`** (new, XS / low, 30 min) is the **sole writer** of the block.
   It observes the *already existing* removal commit, confirms the path absent
   and `git status --porcelain` empty **before staging its own edit**, then
   writes all eight lines atomically in its own evidence commit.
3. **`177.006-T`** (sole evaluator) checks `C1`–`C6`; `C6` independently
   re-observes the **current** tip and remains the final branch-state authority.

Key naming decision: the eighth line is now
`CLEANUP_TIP_OBSERVATION: WORKFLOW_ABSENT | observed_tip=<sha> |
porcelain_empty_at_observation=yes | observed_at=<date>`. `observed_tip` names
**the tip that was observed** — on a normal run the removal commit, i.e. the
*parent* of the evidence commit. It is never required to equal the current tip
and never names the commit that records it. No field is self-referential.

`C5` requires `observed_tip` to be reachable, to be the `C4` removal commit or
a descendant, and to have the path absent from its tree. Guessing or
pre-computing a SHA is forbidden and resolves `EVIDENCE_INCONSISTENT`; if any
value cannot be observed, **no block is written** (atomic, all-or-nothing),
which resolves `EVIDENCE_MISSING` and stays fail-closed.

## Preserved invariants

Five states and their precedence; five-token reason vocabulary
(`WORKFLOW_PRESENT_AT_TIP`, `TIP_UNOBSERVABLE`, `EVIDENCE_MISSING`,
`EVIDENCE_MALFORMED`, `EVIDENCE_INCONSISTENT`); the I1 verdict gate;
no-credential/no-secret evidence; acquisition-then-no-network; `git revert`
rollback of the single creation commit; per-state `181-S` successor
eligibility; `183-S` as DAG root with `181-S depends_on 183-S`.

`ISOLATION_CHARACTERIZED` is now **derived** reachable on one normal run (a
five-step walk-through in the plan), and remains unreachable when cleanup
evidence is absent, malformed or inconsistent, or the workflow is still tracked.

## Deliberately NOT done

- **`L2` (P3) was not fixed.** The dirty-tree clause in the
  `WORKFLOW_PRESENT_AT_TIP` row was left byte-identical so `L2` is neither
  silently closed nor silently altered. Stated explicitly in the plan's
  `verdict_note`, the manifest, and stash `5E45691A`.
- **No count decremented, no severity lowered, no closure claimed.** The
  manifest still reads `p2_open 1`, `p3_open 3`,
  `open_findings: [L1, K5, K6, L2]`; `L1` is `addressed pending review`.

## Backlog changes

- Created `177.007-T` (parent `177-F`, `dependencies: [177.003-T]`, XS / low).
  Sizing required three separate `update_item` calls (create → `size` +
  `size_source` + `size_ruleset_version` → `complexity`).
- Added edge `177.006-T` ← `177.007-T`; retained `177.006-T` ← `177.003-T`.
- `183-S` manifest now 8 items in dependency order; `backlogit_add_to_shipment`
  appends only, so the `custom_fields.items` reorder was a file-level edit.
- Rewrote descriptions of `177.003-T`, `177.006-T`, `177-F`, `183-S`.

## Follow-up stash corrections

- `5E45691A` → exactly `K5`, `K6`, `L2` (`K4` removed, independently closed at
  attempt 05; `L2` added).
- `8DE3047F` → exactly `O4`, `O5`, `N3`, `N4`, `N5`, `M4` (`O2` removed,
  independently closed at 177-S attempt 07).
- `711CA657` untouched (182-S `J3`/`J4`/`J5`).

All three remain kind `task`, priority `low`, non-blocking, and explicitly
excluded from triage, harvest, parenting and shipment membership.

## Next step

Independent **attempt 06** of `plan-review` against plan revision 6. Stage
claims no closure. `181-S` remains blocked on `183-S`.
