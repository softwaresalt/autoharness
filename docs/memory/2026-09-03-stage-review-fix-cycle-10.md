---
title: Stage session memory — SHIP-10 review-fix cycle 10 (root-cause consolidation)
date: 2026-09-03
agent: stage
feature: 160-F
shipment: 168-S
branch: chore/stage-159-167-publication
---

# Cycle 10 — root-cause consolidation of the SHIP-10 plan

## Why this cycle existed

Cycle 9 independent review was **blocked**, not by a defect in the current
contract, but by the accumulated form of the document. Nine consecutive review
cycles had each been applied as an *appended amendment*. The plan reached
**3,784 lines / 355,752 bytes**, and superseded operational clauses were still
readable as if current. A reviewer could not tell which of several statements
about the same subject was binding.

The remedy was structural, not incremental: rewrite the plan as one canonical
*current* execution contract and relocate all history to a single artifact.

## What changed

| Artifact | Change |
|---|---|
| `docs/plans/2026-09-03-minimal-copilot-plugin-payload-plan.md` | Rewritten. **3,784 -> 850 lines**, **355,752 -> 41,014 bytes** (-78% lines, -89% bytes) |
| `docs/reviews/2026-09-03-minimal-copilot-plugin-payload-plan-review-history.md` | **New.** 229 lines. Cycle summaries (staging, 1–10), memory-pointer table, cycle-10 correction table, withdrawn-clause index |
| `.backlogit/queue/160.001-T.md` (T2a) | E3 rewritten (no OS tempfile, no baseline rebuild feeding T10, hermetic case withdrawn); consumption contract, scratch text, sizing rationale; **size S → M** |
| `.backlogit/queue/160.003-T.md` (T4) | `install_root` corrected — plugin `install_root` is `""`; `plugin-payload/**` is an output root, never an install-root prefix |
| `.backlogit/queue/160.017-T.md` (T16) | `observation_phase` added; `artifact_ref` made phase-selected; `owner_task` verification added; stale "T14 corrects CI" attribution → `160.020-T` |
| `.backlogit/queue/160.008/009/010/012/013-T.md` | Stale "the four pre-change byte captures" → "the pre-change byte captures (SIX …)" |

Verified already correct without change: `160.020-T`, `160.015-T`,
`160.006-T`, `160.007-T`, `160.014-T`, `160-F`, `168-S`.

## Authoritative current metrics

* 19 live tasks; DAG **19 nodes / 51 edges**, acyclic; roots T0/T1/T2a; sink T15
* Case ledger **46 unique = 32 RED-FIRST + 14 CHARACTERIZATION**
* **52** case-owner assignments (six two-owner rows)
* **34** RED-FIRST author→owner ordering paths, **zero** reachability violations
* `168-S` manifest **20 entries** (`160-F` + 19 tasks); `160.019-T` absent
* Live size histogram **S 9 / M 10**
* **Six** pre-change captures across four tasks (T0×3, T7, T8, T14)
* Eight-class write partition; one scratch root `dist/.autoharness-scratch/<run-id>/`

## Decisions worth carrying forward

1. **Amendment-by-append does not scale.** Nine cycles of appending produced a
   document that blocked the very review it was written for. Consolidate on a
   cadence, not on a crisis.
2. **History belongs in one artifact, not in the contract.** Traceability is
   preserved by relocation, not duplication. Cycle memory files remain pointers.
3. **A withdrawn-clause index is the cheap half of consolidation.** Removing a
   clause without recording what replaced it makes legacy wording unresolvable.
4. **One statement per subject.** Every definitional subject (scratch root,
   aggregate digest, AC11 selection, install roots) is defined exactly once and
   referenced everywhere else.

## Open follow-up (P2, non-blocking)

`backlogit shipment get 168-S` derives `size_composition` by resolving `160-F`
into every child with `parent_id: 160-F`, including the archived, retired
`160.019-T` (M). The derived rollup reads `M:11, S:9` over 20 members while the
live 19-task histogram is `M:10, S:9`. The manifest itself is correct. This is
backlogit rollup behaviour, not a plan/manifest/task defect. Never quote
`M:11, S:9` as the live task histogram.

## Next steps

* `168-S` remains **queued**. Ship claims it; Stage does not.
* T0 (`160.020-T`) is the execution entry point — every other task except the
  T1/T2a roots is downstream of it.
* Heading stability warning: 34 task-record cross-references resolve to four
  exact plan heading strings (`Evidence-verification contract for 160.017-T`,
  `Plan Hardening`, `H2`, `Test strategy`). Renaming any of them breaks all of
  them.
