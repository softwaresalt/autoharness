---
title: "Proof D run 2 - admitted-bound budget equation and read-limit exhaustion: findings (PASS, synthetic contract only)"
source: "docs/decisions/2026-09-24-read-budget-proof-d-run2-spike.md"
doc_type: decision
description: "Stage-authored findings for Proof D run 2 under charter PE-1.2 section 6.6. Ship ran one disposable synthetic scratch fixture that modelled the decided contract (admitted membership 1..48, max_files=256, revision 12 read plan, byte non-guarantee, class 1b read-limit mapping). The first execution exited 1 because of a defect in the fixture's own off-by-one negative-control assertion; Ship corrected the disposable script and ran it once more, exiting 0. All four section 6.6 pass parts were reported met: 192 admitted cases equal the closed form with C_max=202 (margin 54) and the margin rule held (remainder 5 at N=48); 187-S gives 78; N in {49,512,513} yields MEMBERS_TOO_MANY -> UNRESOLVED / 2 with at most 4 claims and no member lookup; worst-case bytes 416 MiB exceed 32 MiB so no byte fit is claimed, and synthetic N=17 total-size and oversize-file cases yield UNRESOLVED / 2 with the correct reason; 240 read-limit combinations over 12 stages yield UNRESOLVED / 2 with the injected code, a prior completed-recheck mutation keeps precedence, and an incomplete recheck is never agreement; the four run 1 controls and the five PE-1.2 controls were all caught. The 45m time bound is met by a conservative upper bound (under 45m from the operator directive to authoring), and the one-disposable-file bound is met. Verdict PASS for the synthetic contract only. Run 1 stays FAIL. PE-DATA-03 is satisfied for proof entry; the Proof D half of PE-SAFETY-04 is satisfied and the row still awaits Proof G. No production code exists or was exercised, the decision is not implemented in any source or plan, and 187-S stays queued with no claim authority."
docline:
  type: spike
  date: 2026-09-24
  time_box: "45m"
  conclusion: "proceed"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "read-budget"
    - "file-count-limit"
    - "reducer"
    - "proof-entry"
    - "ship-lifecycle"
proof: D
proof_run: 2
proof_verdict: PASS
proof_verdict_scope: synthetic-contract-only
prior_run_artifact: docs/decisions/2026-09-23-read-budget-proof-d-spike.md
prior_run_verdict: FAIL
prior_run_verdict_changed: false
decision: docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md
decision_implemented: false
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.2"
matrix_id: PE-1.2
matrix_rows: [PE-DATA-03, PE-SAFETY-04]
branch: chore/stage-176-s-workflow-defects
head_at_ship_dispatch: 286aa4af
head_at_authoring: 286aa4af
feature_id: 181-F
shipment_id: 187-S
shipment_status_at_authoring: queued
shipment_claim_ready: false
publication_eligible: false
actor_invoked: false
review_scheduled: false
backlog_item_created: false
plan_changed: false
fail_route: none
time_bound_status: met-by-conservative-upper-bound
file_bound_status: met
scratch_cleanup_status: removed-by-parent-after-verification
---

# Proof D run 2 findings - admitted-bound budget equation

## Verdict

| Field | Value |
|---|---|
| Verdict | **`PASS` (synthetic contract only)** |
| What passed | The decided contract in `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`, as modelled by one disposable synthetic fixture. No production code exists, and none was exercised |
| Pass criterion (charter section 6.6, PE-1.2) | All four parts reported met by Ship's second execution: file-slot guarantee, byte distinction, exhaustion at every stage, negative controls (see Findings) |
| Fail criteria (charter section 6.6) | None reported: no admitted case over 256 or breaking the margin rule, no closed-form/simulation disagreement, no exhaustion case with exit 0 or exit 1 or the wrong reason, no uncaught control, no byte-fit claim, time and file bounds met |
| Time bound (45m, Stage plus Ship) | **Met** by a conservative upper bound: under 45m from the operator directive to this authoring (see Time and File Bounds) |
| File bound (1 disposable) | **Met**: one script |
| Run 1 | Stays **`FAIL`** under PE-1.1 (`docs/decisions/2026-09-23-read-budget-proof-d-spike.md`). It is not re-labelled or edited |
| Matrix rows | `PE-DATA-03`: **satisfied for proof entry**. `PE-SAFETY-04`: **Proof D half satisfied**; the row still awaits Proof G |
| Implementation status | The PE-1.2 decision is **not implemented** in any source, template, schema or plan. Plan revision 12 stays frozen |
| Shipment | `187-S` stays `queued`. This verdict grants no claim authority. `publication_eligible: false` |

## Goal

Answer charter PE-1.2 section 6.6: with admitted membership `1..48`, does the
claim count fit `max_files=256` with the recorded margin for every admitted
input, and does every read-limit error at every read or recheck stage,
including byte exhaustion that is explicitly not guaranteed to fit, reduce to
`UNRESOLVED / 2`, never `NO_HARNESS / 1` or `HARNESS_READY / 0`?

## Success Criteria

* **Pass**: all four section 6.6 parts hold, and the time and file bounds are
  met.
* **Fail**: any section 6.6 fail criterion, or the time or file bound is
  exceeded (charter section 6.1).
* **Blocked**: a per-invocation gate rejected Ship's verification-only
  execution, or a required environment was not available.

## Scope Constraints

* Stage did read-only analysis and authored this artifact only. It ran no
  fixture command, test, build or linter, and did not re-run the fixture
  (P-010; charter section 6.1).
* This findings artifact is the only tracked change, committed as a new
  commit. No source, template, schema, backlog, review, plan, charter,
  verdict manifest or run 1 artifact was changed. No amend took place.
* No claim, push, pull request or additional worktree. The P-016 exception
  was not used.
* Nothing is in scope beyond Proof D run 2.

## Inputs (Decided Parameters, Stage Read-Only)

From the decision and charter PE-1.2 section 6.6, not from diagnostic values:

```text
C(N, U, rho) = 4(N+1) + 3U(1+rho)
  N in 1..48, U in {0,1}, rho in {0,1}      192 admitted cases
  max_files = 256, max_file_bytes = 4 MiB, max_total_bytes = 32 MiB
margin rule:  C(N, U, 1) + (N+1) <= 256
class 1b:     read-limit error at any stage -> UNRESOLVED / 2 / <first ReadErrorCode>
              (after class 1 mutation, before class 2)
read-limit codes: FILE_COUNT_LIMIT, TOTAL_SIZE_LIMIT, FILE_SIZE_LIMIT
```

Stage derived this model read-only while authoring the decision. Expected
values: `C(48,1,1) = 202` (margin 54), `C(48,1,1) + 49 = 251` (remainder 5),
`C(17,1,1) = 78`, worst-case bytes at `N=48, U=1, rho=1` =
`104 * 4 MiB = 416 MiB`.

## Evidence Provenance (Ship Verification-Only Invocation)

Ship produced all execution evidence under charter section 6.1. Stage records
it as reported and did not re-run it.

| Gate / fact | Result |
|---|---|
| P-001 | Satisfied before the write (Ship-reported, read-only): active shipments, tasks, features and chores all `[]` |
| P-002 | No claim, no `harness-ready` consumption |
| P-011 | Clean (Ship-reported) |
| P-016 | One worktree (Ship-reported; Stage confirmed one worktree at authoring) |
| HEAD at Ship dispatch | `286aa4af` |
| Host | Windows 11; Python 3.14.3 |
| Scratch | `.proof-scratch\proof-d2-20260924-004200\` inside the current worktree |
| Fixture | One file, `d_budget2.py`, 12,847 bytes, SHA-256 `5a5fbb838bf70262745ce7702e5d31b1cb9965436a42efe657f7717168710c91` (as reported by Ship; the handoff gives one size and hash and no separate hash for the pre-correction content) |
| Worktree after scratch | Only the untracked fixture (Ship-reported) |
| Raw stdout / stderr | Not included verbatim in the handoff; key values were reported |

### Executions (Disclosed Candidly)

| Execution | Exit | Cause / meaning |
|---|---|---|
| 1 | **1** | Defect in the fixture itself: a malformed off-by-one negative-control assertion. This was a scratch-script error, not a contract counterexample |
| 2 | **0** | Ship corrected the disposable script and ran it once more. All assertions held |

There was no third attempt. Two executions stay below the universal retry
threshold of 3. Stage treats execution 1 as a fixture defect rather than a
`FAIL`, because it did not show any section 6.6 fail criterion and the bounds
still hold. The correction was to the disposable fixture only.

| Timing | Value |
|---|---|
| Passing execution runtime | 0.265 s |
| Both executions | 0.487 s |
| Ship segment | About 4m20s |

### Stage Read-Only Confirmation Limits

* The scratch was removed before this authoring, so Stage could not re-hash
  or read the fixture source, unlike run 1. The parent session removed only
  that verified scratch after size, hash and path checks at
  2026-09-24T00:43:30-07:00.
* At authoring Stage observed read-only: `git status --short` empty,
  `.proof-scratch` absent, one worktree, branch
  `chore/stage-176-s-workflow-defects`, HEAD `286aa4af`, and `187-S` recorded
  as `status: queued`.
* The findings below therefore rest on Ship's reported values and exit
  status, checked against the model Stage derived independently.

## Findings

### Part 1 - File-slot guarantee: met

* All 192 admitted `(N, U, rho)` combinations (`N` in `1..48`) were simulated
  claim by claim and equal the closed form.
* `C_max = C(48,1,1) = 202`, margin 54.
* Margin rule held for every admitted `N`; the remainder at `N=48` is 5
  (`202 + 49 = 251 <= 256`).
* `187-S`: `C(17,1,1) = 78`.
* `N` in `{49, 512, 513}` was rejected before any member lookup as
  `MEMBERS_TOO_MANY -> UNRESOLVED / 2`, with at most 4 claims each.

### Part 2 - Byte distinction: met, no byte fit claimed

* Worst-case byte demand at `N=48, U=1, rho=1` is 416 MiB against a 32 MiB
  total limit. It exceeds the limit, so **no byte fit is claimed** for any
  admitted membership.
* Synthetic `N=17` cases whose reservations exceed 32 MiB yield
  `UNRESOLVED / 2 / TOTAL_SIZE_LIMIT`, and a file over `max_file_bytes`
  yields `UNRESOLVED / 2 / FILE_SIZE_LIMIT`. Neither yields success.

### Part 3 - Exhaustion at every stage: met

* 240 read-limit combinations over 12 stages (as reported by Ship) each
  yielded `UNRESOLVED / 2` with the injected code as `reason_code`.
* A disagreement already observed on a completed recheck keeps precedence as
  `INPUT_CHANGED_DURING_RESOLUTION`.
* An incomplete recheck is never treated as agreement.
* Stage cannot itemize how the 12 fixture stages map to the charter's named
  stages, because the source was removed before authoring. Ship reported the
  part met.

### Part 4 - Negative controls: all caught

| Control set | Controls | Caught |
|---|---|---|
| Run 1 (4) | Stable-absent candidates not charged; ledger rechecks skipped; all three surface files re-read per task; off-by-one (+1 / -1) | Yes (Ship-reported) |
| PE-1.2 (5) | Admitted maximum 512 must be over budget; installed-read exhaustion mapped to `MISSING` (exit 1); exhausted candidate recorded as stable absence; incomplete recheck treated as agreement; success reported when reservations exceed 32 MiB | Yes (Ship-reported) |

Mutant counts were not reported in the handoff, and Stage does not supply any.

### Matrix Row Status (Proof D Only; Not a Proof-Exit Audit)

| Row | PE-1.2 criterion | Status |
|---|---|---|
| `PE-DATA-03` | Admitted range `1..48`; `C <= 256` and margin rule; no byte-fit claim; byte and every-stage exhaustion yield `UNRESOLVED / 2` | **Satisfied for proof entry** (synthetic contract) |
| `PE-SAFETY-04` | Proof D run 2 passes under section 6.6, and the Proof G bound cases pass | **Proof D half satisfied**; the row stays open until Proof G |

No reason code beyond `MEMBERS_TOO_MANY`, `FILE_COUNT_LIMIT`,
`TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT` and `INPUT_CHANGED_DURING_RESOLUTION`
is used or created here.

## Time and File Bounds

| Item | Value |
|---|---|
| Upper-bound start | Operator directive, 2026-09-24T00:27:37.827-07:00. This is before both Stage's decision work and Ship's proof |
| Upper-bound end | This artifact's authoring, host clock 2026-09-24T00:47:03-07:00, before the commit |
| Upper bound | About 19m25s, under 45m |
| Result | **Met** by that upper bound. Stage does not state exact Stage and Ship minutes. Components: Ship segment about 4m20s; Stage's current session under 10m |

File bound: one disposable file, as Ship reported. Not exceeded.

## Scratch Hygiene

* Run 2 scratch (`.proof-scratch\proof-d2-20260924-004200\d_budget2.py`) was
  removed by the parent session only after size, hash and path checks, at
  2026-09-24T00:43:30-07:00. Stage deleted nothing.
* At authoring, `.proof-scratch` does not exist and `git status --short` was
  empty before this artifact was written. This read-only observation does not
  edit or re-label the run 1 artifact's hygiene record.

## Consequences

* Proof D run 2 is `PASS` for the synthetic contract only. It proves the
  decided model, not production behavior.
* The PE-1.2 decision is not implemented in source or plan. The rebaselined
  plan and the implementation matrix drafted after proof exit must carry the
  48-member bound, the margin rule, the byte non-guarantee and class 1b.
* The Proof C change request recorded in the decision (the three read-limit
  values as `UNRESOLVED` reasons) stays open for Proof C.
* `187-S` stays `queued`, not claim-ready, and `publication_eligible: false`.
  No backlog, label or shipment change follows from this artifact.

## Recommendation

**Proceed** to the remaining proofs under PE-1.2. Record run 1 `FAIL` and
run 2 `PASS` in the proof-exit report (charter section 8). Proof G still owns
the reader-level bound cases for `PE-SAFETY-04`.

## References

* `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (version 1.2:
  sections 3.1, 6.1, 6.2, 6.6, 7.6 row `PE-SAFETY-04`, 7.7 row `PE-DATA-03`, 8)
* `docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md`
  (Decisions 1 and 2, byte budget, margin rule)
* `docs/decisions/2026-09-23-read-budget-proof-d-spike.md` (run 1, `FAIL`,
  PE-1.1)
* `docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` (revision
  12, frozen, diagnostic only)
* `.github/skills/spike/SKILL.md`
* `.github/agents/_stage.agent.md`
* `.github/agents/_ship.agent.md`
