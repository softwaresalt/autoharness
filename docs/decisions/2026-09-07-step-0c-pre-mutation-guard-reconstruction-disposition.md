---
title: "Disposition of the reconstructed Step 0(c) linked-deliberation pre-mutation guard for the 159-S cascade close"
description: "Focused deliberation on whether a post-hoc reconstruction of shipment-reconcile Step 0(c)'s three-source linked-deliberation collection can satisfy the step's pre-mutation safety purpose, or only its outcome-correctness purpose, and what disposition the already-executed irreversible 159-S cascade close therefore requires"
topic: "shipment-reconcile Step 0(c) live pre-mutation gate vs post-hoc reconstructed evidence"
depth: "deep"
decision_status: "decided"
decided_date: 2026-09-08
decided_by: "operator"
decision_summary: "DECIDED (operator, 2026-09-08) — Option A: accepted-with-remediation P-005 process deviation. Step 0(c)'s linked-deliberation collection for 151-F is recorded as NOT executed as a live pre-mutation gate before the 159-S cascade; the mechanical archival outcome stands as verified and FINAL; the systemic fix is tracked as a SEPARATE follow-up shipment (171-S / feature 163-F), NOT folded into 169-S or 170-S. NO retroactive compliance is claimed and NO merge authorization is given or implied."
promoted_to: "163-F"
plan_path: "docs/plans/2026-09-08-shipment-reconcile-step-0c-live-pre-mutation-evidence-plan.md"
harvested_feature: "163-F"
harvested_tasks: "163.001-T, 163.002-T, 163.003-T, 163.004-T, 163.005-T, 163.006-T, 163.007-T"
shipment: "171-S"
date: 2026-09-07
stash_entry: "856B6770"
reconciled_source_refs: "task N/A (no late identifier found; not attributable to any single 159-S task); feature 151-F; shipment 159-S; PR 436; review threads RECONCILED from N/A -> PRRT_kwDORzpWpM6gGfcV, PRRT_kwDORzpWpM6gGfcv, PRRT_kwDORzpWpM6gGfc_, PRRT_kwDORzpWpM6gGfdU (all unresolved at HEAD 094bd157)"
duplicate_scan: "CLEAN - unconditional P-021 C5 duplicate scan over all 57 stash.jsonl entries found exactly one entry describing this expansion (856B6770). No duplicates merged, none archived."
closed_shipment: "159-S"
covering_feature: "151-F"
pull_request: 436
pr_head: "094bd157d61df3d32d88f5c3566496cd3cddf549"
cascade_commit: "cb474a0a7d1fdfe2bbfe0dd3e2a6110aefb533ab"
preserved_evidence_commit: "1b758a16"
related_but_distinct:
  - "2026-09-06-shipment-reconcile-cascade-pre-mode-contract-deliberation (stash 15A02E21; cited by title only — not yet committed to any branch, pending publication tracked by follow-up 1CD92B69) - RELATED, DISTINCT: the Pre-Mode member-class status-mismatch/HALT deviation, already dispositioned accepted-with-remediation P-005, remediated by shipment 169-S / feature 161-F. This deliberation concerns a SECOND, separate deviation in a different sub-step (Step 0(c) linked-deliberation collection ordering), and MUST NOT be folded into that disposition."
tags:
  - shipment-reconcile
  - pre-mutation-gate
  - P-005
  - P-021
  - process-deviation
  - historical-disposition
---

# Step 0(c) pre-mutation guard reconstruction — disposition deliberation

**Status: DECIDED (operator, 2026-09-08). Option A adopted. Harvested to feature
`163-F`, tasks `163.001-T`–`163.007-T`, shipment `171-S` (queued, `blocks` dependency
on `169-S`). The body below is preserved as authored; see the Disposition section at
the end for the recorded decision and its consequences.**

## Question

Shipment-reconcile Step 0(c) requires, for each qualifying feature member, that the
three engine-defined linked-deliberation sources be collected and validated
**before** the destructive cascade invocation. For the 159-S close of qualifying
feature `151-F`, that scan was **reconstructed after** the cascade from preserved
pre-close evidence (commit `1b758a16`), not executed live as a pre-mutation gate.

Does that reconstruction satisfy Step 0(c), or only prove the outcome was correct?

## Authoritative protocol text

`.github/skills/shipment-reconcile/SKILL.md`:

* L473–475 — "extend Step 0(c)'s classification here, still **before** the cascade
  invocation: for each qualifying feature member, independently collect its linked
  deliberation IDs using exactly those same three engine-defined sources".
* L487–492 — on ambiguous/torn or missing record location, "halt immediately with
  `RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS` or `RECONCILE_FAIL_SNAPSHOT_MISSING`
  respectively — never guess which copy or location is authoritative, and never
  compute `required_ids` from an arbitrary copy **before the destructive cascade
  invocation**".
* L747–749 — snapshot values are "all captured **before** this step 1 invocation,
  never a freshly-read or assumed post-close value".

The ordering requirement is explicit and load-bearing, stated three times.

## Step 0(c) serves two separable purposes

This is the crux of the disposition.

**Purpose 1 — data supply (outcome correctness).** Produce the validated
linked-deliberation ID set that feeds `allowed_ids` / `required_ids` in the
Cascade Close Sub-Procedure's step-3 two-set gate.

**Purpose 2 — pre-mutation halt (decision optionality).** Detect ambiguous/torn or
missing records and halt *while not mutating is still possible*, preserving the
operator's option to decline the irreversible cascade.

A post-hoc reconstruction can satisfy **Purpose 1 if and only if the inputs are
provably unchanged by the mutation**. It can **never** satisfy Purpose 2, because
the value of a pre-mutation gate is the preserved opportunity to halt. Once the
irreversible cascade executed, that opportunity was destroyed. No evidence
produced afterwards can retroactively create a choice that was never offered.
This is a category difference, not an evidentiary shortfall.

## Stage's independent verification of Purpose 1

Stage did not accept the report's byte-identity assertion on its own authority. It
was re-verified directly:

```
git show 1b758a16:.backlogit/queue/151-F.md   vs   .backlogit/archive/151-F.md
```

The only differences are archival bookkeeping fields added by the archive
operation: `archived_from`, `archived_status`, `commit`, `status`, `updated_at`.
`custom_fields`, the description body, and `references` — **the three and only
three Step 0(c) sources** — are unchanged.

Therefore the reconstructed scan's inputs are provably identical to what a live
scan would have read, and its result (validated linked-deliberation set for
`151-F` = `{}`, empty) is what a live scan would have produced. **Purpose 1 is
genuinely satisfied, with high confidence.**

## Four-axis separation

| Axis | Finding | Confidence |
|---|---|---|
| **Mechanical outcome** | **CORRECT.** Empty linked-deliberation set correctly omitted from both ID sets; `returned_ids` empty; `archived_ids` == `allowed_ids` == `required_ids`; all `parent_id` values preserved. Independently re-verified. Irreversible but harmless. **Nothing to remediate mechanically.** | High |
| **Process compliance** | **NOT COMPLIANT.** The scan ran after the mutation; the protocol requires it before, three times over. Disclosure is not compliance — as the review threads correctly state, "merely disclosing that execution continued does not resolve the gate". A genuine second deviation, distinct from 15A02E21. | High |
| **Authorization** | **ABSENT.** The sole recorded operator authorization covers stale-lock removal ("I Authorize removal of the stale .159-S.md.lock and continue 159-S closure"). It does not reach a skipped pre-mutation safety gate. The 15A02E21 disposition covers a different deviation. Stage cannot self-authorize (P-001/P-009). **Operator-only.** | High |
| **Future precedent** | **HIGHEST STAKES.** Ratifying reconstruction as equivalent completion would establish that any pre-mutation gate may be skipped and back-filled whenever inputs happen to be immutable — converting gates into post-hoc audits and inverting the burden of proof. It is also self-defeating: Step 0(c) resolves ambiguous/missing states before mutation precisely for the case where inputs are *not* recoverable. Ratifying the easy case (inputs preserved) creates the precedent that will be cited in the hard case (inputs destroyed). | High |

## Options evaluated

### Option A — Accepted-with-remediation P-005 deviation (RECOMMENDED)

Keep the mechanical archive as final and verified. Record Step 0(c) as **not
executed live** — a real process deviation, permanently disclosed. Remediate
systemically so the skill cannot execute this way again.

* **Concrete remediation:** amend the shipment-reconcile Step 0(c) contract to
  require the linked-deliberation collection to emit a durable, timestamped
  pre-mutation evidence record *before* the cascade invocation, and to fail closed
  when that record is absent at close time — i.e. make live execution *provable*,
  not merely *required*. Add a replay/regression test over the 159-S shape that
  fails if the collection is reconstructible after mutation.
* **Can `READY` be unconditional after disposition?** **Yes.** `READY` asserts the
  shipment's artifacts are releasable, not that the process was flawless. Once the
  operator dispositions the deviation, the residual risk is closed: the outcome is
  verified correct and the systemic fix is tracked. The closure record must
  permanently retain the deviation disclosure. This is exactly the shape the
  operator already accepted for 15A02E21 — consistency is a strong argument.

### Option B — Ratify reconstructed evidence as equivalent completion

* **Burden of proof:** the proponent must show equivalence on *both* purposes. It
  holds only for Purpose 1. Purpose 2 fails categorically.
* **Precedent risk:** severe and self-defeating (see the four-axis table).
* **Verdict: REJECT.** Accepting B would make the harness's fail-closed posture
  unenforceable in exactly the situations it exists for.

### Option C — Mark closure conditional/halted until additional remediation

* **What evidence could change a historical non-execution?** **None.** No future
  artifact can make a step that did not run at time T have run at time T.
* **Does this produce an indefinite block?** **Yes, in its natural form.** If the
  condition is "until Step 0(c) is proven to have run live", it is unsatisfiable in
  principle — a permanent block.
* **And if narrowed to "until the remediation ships"?** It **deadlocks.** The
  remediation shipment 169-S is queued and execution-blocked on PR #436's own
  closure under P-001. Gating #436's closure on remediation shipping creates a
  circular dependency: #436 waits on 169-S, 169-S waits on #436.
* **Verdict: REJECT as primary.** Its legitimate instinct — that `READY` must not
  silently unblock successors via `topology.py`'s `closure_complete == True` — is
  fully absorbed into Option A by requiring explicit disposition first.

## Recommendation

**Option A**, high confidence.

It is the only option that simultaneously tells the truth on all four axes: it
keeps the verified-correct mechanical outcome, refuses to launder a process
deviation into compliance, respects that authorization is operator-only, and
protects the precedent by fixing the gate systemically rather than excusing it.
It also avoids Option C's circular deadlock and matches the disposition shape the
operator already chose for the sibling deviation 15A02E21.

### Shared shipment 169-S, or separate follow-up?

**Separate follow-up shipment. Not 169-S.** Reasons:

1. **169-S is a sealed, reviewed decomposition.** Its plan passed plan-review
   (cycle 2 of 3) and was harvested into 161-F with `161.003-T` explicitly marked
   *"U1 ATOMIC CORE ... (R-4 INDIVISIBLE)"*. Expanding its scope reopens a reviewed
   plan and would require a re-review that cannot currently run — PR #436 has hit
   its hard 3-cycle limit and P-018 is blocked.
2. **Different defect class (width isolation).** 161-F fixes *what* Pre-Mode
   compares (member-class status contract). 856B6770 concerns *whether Step 0(c)
   executed live and is evidenced as pre-mutation*. Different contract surface,
   different failure mode, different tests.
3. **Critical-path hygiene.** 169-S is already blocked behind #436; loading a
   second, separately-authorized deviation onto it lengthens an
   already-blocked path and couples two independent dispositions.

**However**, the two share a root cause — *pre-mutation gates that are required but
not evidenced*. The follow-up should be recorded as a sibling of 161-F, may reuse
its test scaffolding, and should carry a **sequencing dependency on 169-S** so the
two do not make conflicting edits to the same `SKILL.md` Step 0 region.

## What the operator's disposition must cover

Two separate grants are required. A single sentence covering only one is
insufficient.

**(a)** Disposition of `856B6770` itself — the historical safety question, which is
operator-only and which Stage cannot decide.

**(b)** Authorization for **one bounded fourth** PR #436 review-fix round, since the
hard 3-cycle limit is reached and P-018 is blocked. Without (b), the closure
records and the four open threads cannot be brought into agreement even after (a)
is decided.

### Proposed exact operator authorization sentence

> I disposition 856B6770 as an accepted-with-remediation P-005 process deviation —
> the Step 0(c) linked-deliberation collection for 151-F is recorded as not
> executed as a live pre-mutation gate before the 159-S cascade, the mechanical
> archival outcome stands as verified and final, and the systemic fix is tracked
> as a separate follow-up shipment, not folded into 169-S; and I separately
> authorize exactly one bounded fourth PR #436 review-fix round, limited to
> aligning the closure_status/releasability fields, replying to and resolving the
> four open Copilot threads, and re-running the local review and Copilot gates at
> the new HEAD. This authorizes neither any further review cycle beyond that one
> round nor merge of PR #436.

## Scope of open threads this disposition would close

All four unresolved threads at HEAD `094bd157` reduce to this one question:

| Thread | Asks for |
|---|---|
| `PRRT_kwDORzpWpM6gGfcV` | `closure_status` non-ready until 856B6770 dispositioned (`topology.py` unblocks successors on `READY` + done compaction) |
| `PRRT_kwDORzpWpM6gGfcv` | Cascade report to record halted/process-deviation rather than protocol-compliant `CLOSED` |
| `PRRT_kwDORzpWpM6gGfc_` | Operational closure to record the condition, not unconditional releasability |
| `PRRT_kwDORzpWpM6gGfdU` | Durable compacted memory to carry the round-12 finding |

Under Option A they are answered by an explicit recorded disposition plus the
bounded fourth round in (b) — not by weakening the mechanical verdict.

## Stage constraints observed

PR #436, its body, threads, branch commits, closure-status fields, the
implementation, and shipment 169-S were **read only**. Nothing was merged,
promoted, or harvested. `decision_status` remains `exploring` pending the
operator's decision.

---

## Disposition (operator, 2026-09-08) — RECORDED, FINAL

**Option A adopted.** The operator's recorded decision, in full:

> `856B6770` is an **accepted-with-remediation P-005 process deviation**. Step 0(c)'s
> linked-deliberation collection for `151-F` was **not executed as a live pre-mutation
> gate** before the 159-S cascade. The **mechanical archival outcome stands as verified
> and final.** The systemic fix is a **separate follow-up shipment**, not folded into
> `169-S`. **No merge authorization** is given or implied.

### What this disposition does and does not assert

| Axis | Recorded outcome |
|---|---|
| **Mechanical outcome** | **CORRECT and FINAL.** Independently re-verified. Nothing to remediate mechanically. Not re-opened |
| **Process compliance** | **NOT COMPLIANT, permanently disclosed.** Step 0(c) is recorded as not executed live. **No retroactive compliance is claimed** and none is available |
| **Authorization** | **GRANTED (2026-09-08)** for the deviation's disposition only. It authorizes no merge, no further review round, and no other deviation |
| **Future precedent** | **PROTECTED by remediation, not by excuse.** The gate is fixed systemically in `163-F`/`171-S` so this cannot recur — per lesson 7 of the composed-state-machine learning: fix the contract, label the deviation, do not build a deviation ritual around it |

### Remediation identity (closes the AF-06 auditability gap)

The remediation now has a durable, trackable identity. Before this session it existed
only as the prose phrase *"a separate follow-up shipment (not 169-S)"*, which stash
`9E22BFC6` (adversarial finding AF-06) correctly flagged: *the deviation was
searchable, its remedy was not, and nothing would ever have marked the deviation
closed because nothing identified what must ship.*

| Artifact | Identity |
|---|---|
| Plan | `docs/plans/2026-09-08-shipment-reconcile-step-0c-live-pre-mutation-evidence-plan.md` (hardened; plan-review **PASS** cycle 1, zero P0/P1) |
| Covering feature | **`163-F`** — Shipment-reconcile Step 0(c): provable live pre-mutation evidence gate |
| Tasks | **`163.001-T` … `163.007-T`** (U1a, U1b, U1c, U2 ATOMIC CORE, U3, U4, U5) |
| Shipment | **`171-S`** — SHIP-13, `status: queued`, `priority: high` |
| Dependency | `171-S` **blocks**-depends on `169-S` — sequencing only, so the two do not make conflicting edits to the same `SKILL.md` Step 0 / Cascade Sub-Procedure region |

The remediation content is exactly the three requirements this deliberation's Option A
clause specified, and nothing more:

1. a **durable, timestamped pre-mutation evidence record** emitted before the cascade
   invocation (`RQ-1` → `163.004-T`);
2. a **fail-closed live-execution check** on that record's **pre-existence** —
   `RECONCILE_FAIL_PRECASCADE_EVIDENCE_MISSING` / `_STALE` (`RQ-2` → `163.004-T`);
3. a **159-S-pattern replay regression test** that fails if the collection is
   reconstructible after mutation (`RQ-3` → `163.001-T`/`163.002-T`/`163.003-T`).

The load-bearing detail carried from this deliberation into the plan: the replay test
must reject post-hoc reconstruction **on the ordering axis, not the content axis**,
because 159-S's reconstruction *was* byte-identical and would pass any content
comparison. That is the Purpose-1/Purpose-2 distinction made executable.

### Routing confirmed

* **NOT folded into `169-S`/`161-F`** — sealed, plan-reviewed decomposition; `161.003-T`
  is marked *R-4 INDIVISIBLE ATOMIC CORE*; different contract surface (*what* Pre-Mode
  compares vs *whether* Step 0(c) ran live).
* **NOT folded into `170-S`/`162-F`** — hosted-review learning methodology; its scope is
  unaltered by this disposition.

### What remains open

**Nothing in this deliberation.** Part (b) of the earlier "what the operator's
disposition must cover" section — authorization of a bounded fourth PR #436 review-fix
round — was **not** granted and is **not** requested by this disposition. This record
carries no merge authorization and no review-round authorization.

## Stage constraints observed

PR #436, its body, threads, branch commits, closure-status fields, the
implementation, shipment `169-S` and shipment `170-S` were **read only** throughout
both the deliberation and this disposition session. No source, template, config, or
test file was written; no branch was created or checked out; no commit, push, or PR
operation was performed (P-010).
