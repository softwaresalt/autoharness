---
title: "Proof C run 3 - one-entry SurfaceSpec and total reason truth table: findings (FAIL, time bound, PE-1.4)"
source: "docs/decisions/2026-09-24-surface-taxonomy-proof-c-run3-spike.md"
doc_type: decision
description: "Stage final adjudication of operator-authorized Proof C run 3 under charter section 6.1/6.2/6.5. Verdict FAIL: the section 6.2 75-minute bound, which section 6.1 says covers Stage analysis and Ship execution together, expired at 19:22:19 local when charged from Stage's run 3 design start at 18:07:19, before this adjudication was complete. Stage does not reset the clock to the 18:21:44 operator authorization. The run 3 fixture result reported by Ship (single native exit 0, failure_count 0, 47/47 branches) is recorded as evidence only and is not converted into PASS. Run 1 FAIL and run 2 BLOCKED are unchanged."
docline:
  type: spike
  date: 2026-09-24
  time_box: "75m"
  conclusion: "fail"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "surface-taxonomy"
    - "proof-c"
    - "time-bound"
---

# Proof C run 3: findings (FAIL, time bound)

## Verdict

**FAIL.** Reason: exceeding the time bound is `FAIL` (charter section 6.1,
"Verdicts"). There is no partial pass. This verdict is not based on the
fixture result.

## Time accounting (explicit, no reset)

| Event | Local time (2026-09-24, -07:00) | Source |
|---|---|---|
| Stage run 3 design (truth table, B1-B6 corrections) began | 18:07:19 | Stage record, as relayed by the operator |
| Operator authorization | 18:21:44 | operator |
| Ship fixture authoring began | 18:50 | Ship report |
| Ship single execution | ~19:19-19:20 | Ship report (10.145 s) |
| Stage adjudication began | 19:21:11 | this session |
| 75 m bound expires (charged from 18:07:19) | **19:22:19** | arithmetic |
| Stage clock read during adjudication | 19:22:04 (charter and run 2 reads still in progress) | `Get-Date` |
| Findings artifact written | after 19:22:19 | this file |

The section 6.1 bound covers "its Stage analysis and its Ship execution
together". The 18:07:19 work was Stage analysis of this proof: truth-table
design, schema branch derivation and freeze inspection. Stage earlier said
that time should be charged. Leaving it out now would be a quiet budget
reset, so Stage charges it. On that basis the bound ran out before Stage
analysis finished, and the verdict is FAIL.

Counterfactual, recorded for the charter owner and not applied here: charged
from the 18:21:44 authorization, the bound would expire at 19:36:44. Even
then, this adjudication would not be a PASS. Stage did not re-hash the
frozen pair or re-derive the section 6.5 conditions against the executed
output, so the result would stay unassessed. The time bound decides the
verdict either way.

## Evidence recorded (Ship-reported; Stage did not re-verify it in this session)

* Frozen pair: `.proof-scratch\C-run3-20260924-185023\c3_verify.py` (44083 B,
  SHA-256 `f7bb8643...19392e3`) and `c3_schema.json` (23483 B, SHA-256
  `a659c4ad...749831b1d3`). These match Stage's earlier FREEZE-OK.
* One execution with no retry: `python -B -X utf8 ...\c3_verify.py`, native
  exit 0 in 10.145 s. stdout was 1052 B (SHA-256 `7da03bd3...2f56c`). stderr
  was empty.
* Report: `failure_count` 0, status `NO_FIXTURE_FAILURE`, schema/surface
  branch counts 47/47.
* Real-surface control: the checksum is reported separately. Render parity is
  `false` (render_reason evaluated, unresolved `[]`) because of the expected
  line reflow at byte 4994, the same as the run 2 observation. This is a
  follow-up need, not a Proof C condition.
* Preflight: sync exit 0. 71 checkpoints: 70 resolved and 1 official valid
  abandoned. 0 anomalies, 0 active `ship`, 0 active task, feature, chore or
  shipment. 173-S closure READY. One clean feature worktree. PE-ACTIVATE-01
  blobs equal `4acba14a` before and after. Only ignored files were touched.
* No source, backlog, claim, PR or push mutation was reported.

Limits: Stage did not run or import the fixture, re-hash files, scan broadly
or read host Temp. The evidence above is as relayed, and none of it changes
the time-bound verdict.

## Matrix rows

| Row | Status after run 3 |
|---|---|
| `PE-INTERFACE-03` | Not advanced (FAIL, time bound) |
| `PE-DATA-01` | Not advanced (FAIL, time bound) |
| `PE-DATA-02` | Not advanced (FAIL, time bound) |

## Prior runs

Run 1 FAIL (`2026-09-24-surface-taxonomy-proof-c-spike.md`) and run 2 BLOCKED
(`2026-09-24-surface-taxonomy-proof-c-run2-spike.md`) are unchanged. Neither
is reclassified.

## Routing

FAIL goes back to architecture or charter (Phase 0), per section 6.1. The
reopened decision is **the charter section 6.2 Proof C 75 m bound and its
start-of-clock rule**. It must say whether Stage design done before operator
authorization counts toward the bound, and whether 75 m is enough for design,
freeze, Ship authoring, execution and adjudication. Any later run needs a new
operator authorization. This artifact does not change backlog, charter, Ship
surfaces, claims or PRs.
