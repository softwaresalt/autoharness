---
title: "Proof D reopened decisions: admitted-member bound, read budget and read-limit exhaustion mapping"
source: "docs/decisions/2026-09-24-read-budget-admitted-bound-and-exhaustion-decision.md"
doc_type: decision
description: "Architecture/charter decision closing the two decisions Proof D (FAIL, PE-1.1) reopened. Decision 1: lower the admitted shipment membership maximum from 512 to 48, keep max_files=256 and the plan revision 12 read plan unchanged, so C(N,U,rho)=4(N+1)+3U(1+rho) peaks at C(48,1,1)=202 with 54 spare slots, and also absorbs one unmodeled extra claim per record (251 <= 256). This is a recorded public-contract change, not a hidden technical fix. Byte budget: a worst-case 32 MiB total cannot be guaranteed for any meaningful admitted membership under the frozen 4 MiB per-file cap (416 MiB worst case at N=48), so no byte-fit guarantee is claimed and byte exhaustion is a bounded failure. Decision 2: any read-limit error (FILE_COUNT_LIMIT, TOTAL_SIZE_LIMIT, FILE_SIZE_LIMIT) at any read or recheck stage reduces to UNRESOLVED / 2, never NO_HARNESS / 1 or HARNESS_READY / 0, reusing existing closed codes. Proof D is re-chartered under PE-1.2; it is not marked PASS here."
date: 2026-09-24
status: decided
decision_status: decided
deciders: operator (bounded delegation), Stage
operator_authorization: "2026-09-24 - operator instruction to act on Proof D's reopened decisions, authorizing a Stage-selected, proportionate remedy recorded as a versioned PE-1.2 charter change plus this decision; operator may veto before the Proof D run 2 handoff"
resolves:
  - "Proof D reopened decision 1 (admitted membership bound, file budget, read plan)"
  - "Proof D reopened decision 2 (explicit closed reducer class for budget exhaustion)"
reopened_by: docs/decisions/2026-09-23-read-budget-proof-d-spike.md
parent_decision: docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version_introduced: "1.2"
matrix_id: PE-1.2
feature_id: 181-F
shipment_id: 187-S
shipment_claim_ready: false
proof_d_verdict: FAIL
proof_d_rerun_required: true
backlog_item_created: false
plan_changed: false
public_contract_change: true
promoted_to: none
tags:
  - read-budget
  - file-count-limit
  - reducer
  - proof-entry
  - ship-lifecycle
---

# Proof D reopened decisions: admitted bound, read budget, exhaustion mapping

## Context

Proof D (charter PE-1.1 section 6.6) ended `FAIL`. The file-slot claim count
derived from frozen plan revision 12 is:

```text
C(N, U, rho) = 4(N+1) + 3U(1+rho)
  N   = admitted shipment members (plan revision 12: 1..512)
  U   = surface union size (one-entry SurfaceSpec: 0 or 1)
  rho = 1 if the ledger recheck re-reads manifest, template and installed
```

With `max_files=256`, the first over-budget admitted case is `N=62, U=1, rho=1`
(`C=258`), and `C(512,1,1)=2058`. The plan also has no closed reducer class for
read-limit exhaustion, and the nearest rules (for example "Missing installed
bytes are `MISSING`") could turn exhaustion into `NO_HARNESS / 1`.

Plan revision 12 stays frozen and is diagnostic only. This decision does not
edit it, and does not open plan revision 13 or review attempt 12. Its choices
bind the rebaselined plan and the implementation matrix drafted after proof exit.

## Decision 1 - admitted bound, file budget and read plan

**Chosen: option (a). Lower the admitted membership maximum to `N_max = 48`.
Keep `max_files = 256` and the revision 12 read plan (both candidates charged,
stable absence charged, every recheck a new non-refundable claim) unchanged.**

| Case | `C` | Spare of 256 |
|---|---|---|
| `187-S` today, `N=17`, `U=1`, `rho=1` | 78 | 178 |
| `N=48`, `U=0` | 196 | 60 |
| `N=48`, `U=1`, `rho=0` | 199 | 57 |
| `N=48`, `U=1`, `rho=1` (`C_max`) | **202** | **54 (21.1%)** |
| `N=48`, one unmodeled extra claim per record, `5(N+1)+6` | 251 | 5 |
| Over-limit membership `N >= 49` (rejected before any member lookup) | at most 4 (`C(0,0,0)`: shipment candidates and their recheck) | at least 252 |

**Margin rule (binding on any later change).** The admitted maximum must satisfy
`C(N_max, U_max, 1) + (N_max + 1) <= max_files`: every admitted shipment still
fits if the model has missed one claim per record. At 48 this is
`202 + 49 = 251 <= 256`. The largest `N` meeting this rule is 49; 48 leaves 5
slots beyond it. With `N=48`, the surface union could grow to `U=10` before
`C_max` exceeds 256 (`196 + 6U`). A change to `max_files`, the read plan, the
recheck scope or the `SurfaceSpec` size requires recomputing `C` and a new
decision.

**Why 48.** It is about 2.8 times the real `187-S` (17 items). The governance
default for future shipments (charter `PE-TASK-02`: at most 6 tasks) makes a
membership near 48 unusual. It keeps a real margin rather than the zero or
near-zero margins at `N=61` to `N=63`.

**Rejected alternatives.**

| Option | Why rejected |
|---|---|
| Keep `N_max = 61` (largest that fits every variant) | Spare is 2 slots (`C=254`); it has no margin for model error, and the charter pass criterion asks for a recorded margin |
| (b) Raise `max_files` to at least 2058 plus margin | Changes a frozen `ReadLimits` default by about 8 times to protect memberships nobody uses; it multiplies worst-case byte demand too (see below) and weakens the bounded-read obligation (charter section 5) |
| (c) Replan reads (stop charging absence, narrow rechecks, pool claims) | Changes ledger and mutation-detection semantics that other frozen rules depend on (`inputs_sha256` binds both candidates, including stable absence). That is more new production design than the fault needs |

**Public contract change (recorded, not hidden).** Revision 12 admits
`custom_fields.items` of `1..512`. The admitted range becomes `1..48`. A list
longer than 48 is rejected by the **existing** closed reason `MEMBERS_TOO_MANY`,
which already reduces through class 2 to `UNRESOLVED / 2`. No new code is
created. A shipment with 49 to 512 members that would have been admitted under
revision 12 now fails closed with exit 2. It never fails with `NO_HARNESS`, and
it never passes silently. No such shipment was checked (see Residual risks).

## Byte budget - accounted for, not guaranteed

Frozen limits: `max_file_bytes = 4 MiB`, `max_total_bytes = 32 MiB`. Each
regular-file read reserves its advertised size, and the reservation is never
refunded. Absent candidates reserve no bytes. Let `P` be the number of
byte-reserving reads:

```text
P_min(N,U)      = (N+1) + 3U                 present records and surfaces, no byte re-reservation on recheck
P_max(N,U,rho)  = 2(N+1) + 3U(1+rho)         rechecks re-read present files (conservative)
worst-case bytes = P * max_file_bytes
```

| Case | Worst-case bytes | Against 32 MiB |
|---|---|---|
| `N=48, U=1, rho=1`, `P_max=104` | 416 MiB | Exceeds by 13 times |
| `N=17, U=1, rho=1`, `P_max=42` | 168 MiB | Exceeds |
| Largest `N` with a guaranteed fit, `P_max`, `U=1, rho=1` | none (`2N+8 <= 8` requires `N=0`) | - |
| Largest `N` with a guaranteed fit, `P_min`, `U=1` | 4 | - |

A worst-case byte fit **cannot be guaranteed** for the admitted range under the
frozen per-file cap. For a uniform cap to guarantee a fit at
`N=48, U=1, rho=1` it would have to be `floor(32 MiB / 104) = 322,638` bytes.
That was rejected: the installed `.autoharness/harness-manifest.yaml` is
already 158,091 bytes (about 49% of that cap) and grows with every entry.
Raising `max_total_bytes` to 416 MiB was also rejected, because it defeats the
memory bound.

**Decided.** The byte limits stay as frozen. No artifact claims a byte fit for
every admitted member. Byte exhaustion (`TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT`)
is a **bounded failure** that yields `UNRESOLVED / 2` under Decision 2. It is
never success and never `NO_HARNESS`. For scale only (not a guarantee): the
three current surface files total 341,722 bytes, or 683,444 bytes when they are
re-read, far below 32 MiB.

## Decision 2 - closed read-limit exhaustion mapping

A **read-limit error** is a `ReadErrorCode` of `FILE_COUNT_LIMIT`,
`TOTAL_SIZE_LIMIT` or `FILE_SIZE_LIMIT`, all of which already exist in plan
revision 12.

1. **Every stage.** A read-limit error at any read or recheck stage reduces the
   invocation to `UNRESOLVED / 2`. The stages are: shipment queue or archive
   candidate, member queue or archive candidate, manifest read, template read,
   installed-file read, candidate ledger recheck, and surface recheck.
2. **Precedence.** One reducer class is inserted directly after the frozen
   class 1 (mutation) and before class 2:
   `1b. read-limit error at any stage -> UNRESOLVED / 2 / <the ReadErrorCode that occurred first>`.
   A disagreement already observed on a completed recheck still dominates as
   `INPUT_CHANGED_DURING_RESOLUTION`, unchanged. Class 1b dominates classes
   2 to 8, so exhaustion can never produce `NO_SURFACES_REQUIRED`,
   `ALL_SURFACES_PRESENT` or `NO_HARNESS`.
3. **Not an observation.** A read-limit error is never recorded as stable
   absence (so never `MEMBER_NOT_FOUND`), never classifies a surface as
   `MISSING`, `STALE` or `PRESENT`, and a recheck that could not complete is
   never treated as agreement.
4. **Reason code.** The result's `reason_code` is the existing `ReadErrorCode`
   value that occurred first, in deterministic generation order. The diagnostics
   record the `ReadStage`. **No new reason code or taxonomy is created.**
5. **Out of scope.** Whether the resolver issues further requests after the
   first read-limit error is not decided here, except that it cannot change
   the class, the exit code or the reason code. No other production behavior is
   decided.

**Change request for Proof C (not a PE-1.2 change to Proof C).** Proof C's
reason truth table and schema parity must include these three values as
`UNRESOLVED` reasons. This is recorded as a change request under charter section 3.
Proof C's question, bounds and rows are unchanged.

## Consequences for the charter

* Charter version **1.2** (matrix **PE-1.2**) revises section 6.6 and rows
  `PE-DATA-03` and `PE-SAFETY-04` only. Every other row, the threat model and
  Proofs A, B, C, E, F and G are unchanged. The recorded verdicts for Proof A
  (`BLOCKED`) and Proof F (`PASS`) stand as recorded under PE-1.1.
* Proof D stays **`FAIL`** under PE-1.1. A new run ("Proof D run 2") is
  chartered under PE-1.2 section 6.6 (`PE-FLOW-04`). This decision does not
  mark Proof D `PASS`.
* The rebaselined plan and the implementation-matrix draft after proof exit
  must carry the bound, the margin rule and the class 1b mapping.

## Residual risks

* **Model risk.** The count assumes revision 12's claim model. An unmodeled
  source of more than one extra claim per record would breach the margin rule.
  Proof D run 2 tests the model, not production code (none exists).
* **Migration.** No existing shipment was measured for 49 or more members,
  because no semantic backlog read was made during the frozen proof phase.
  Such a shipment would fail closed with `MEMBERS_TOO_MANY`. The check belongs
  to Phase 2, decision C3.
* **Byte non-guarantee.** An admitted shipment with unusually large records or
  surfaces can end `UNRESOLVED / 2` on byte limits. This is accepted as a bounded,
  explicit failure. Proof G owns the reader-level bound cases.
* **Delegated approval.** The concrete bound was selected by Stage under the
  operator's bounded delegation. The operator may veto it before the Proof D
  run 2 handoff.

## References

* `docs/decisions/2026-09-23-read-budget-proof-d-spike.md` (Proof D FAIL,
  reopened decisions)
* `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (version 1.2:
  sections 3, 6.2, 6.6, 7.6, 7.7, 10)
* `docs/decisions/2026-09-23-lifecycle-review-convergence-reset-deliberation.md`
  (B+D; `S71`)
* `docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` (revision
  12, frozen, diagnostic: `ReadLimits`, Session budgets, lookup, ledger,
  Reducer precedence)
* `docs/compound/093-S-review-loop-convergence.md` (failures reopen
  architecture, not prose)
* `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`
  (contract changes carry a version bump)
