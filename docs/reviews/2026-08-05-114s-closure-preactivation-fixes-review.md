---
title: "plan-review — 114-S Closure Pre-Activation Fixes"
type: plan-review
doc_type: review
source: docs/reviews/2026-08-05-114s-closure-preactivation-fixes-review.md
date: 2026-08-05
route: claude-opus-4.8 / anthropic / high (Stage role route)
plan: docs/archive/plans/2026-08-05-114s-closure-preactivation-fixes-plan.md
deliberation: docs/decisions/2026-08-05-114s-closure-preactivation-fixes-deliberation.md
closure: docs/archive/closure/114-S-109-F-post-merge-closure.md
scope_reviewed: 3 harvested tasks — 115-S {109.021-T, 109.022-T, 109.023-T} + intra-shipment sequencing over the 115-S activation set; re-reviewed 2026-08-05b for the 109.017-T CLAIM_NOT_OBSERVED consumption P1; re-reviewed 2026-08-05c for the 109.021-T delayed-vs-failed indistinguishability P1
verdict: PASS
p0: 0
p1: 0 (4 raised, all resolved — F-1, F-2 in initial pass; F-4 escalated P2->P1 and resolved in re-review 2026-08-05b; F-5 raised+resolved in re-review 2026-08-05c)
p2: 0 unresolved (4 raised; F-3 resolved/accepted, F-4 re-classified to P1, final authoring findings resolved)
---

## Verdict: PASS

The plan is dependency-correct, width-isolated, non-conflating, each task is
single-family and ≤2h, the two design-decision defects are settled with the
gate's authority boundary as the governing constraint, and plan hardening
reflects the true blast radius (gate module + CLI telemetry + activation
gating). All findings raised below are resolved. Proceed to harvest + shipment
assembly.

## What was checked

- **Detection-vs-mutation authority (P-001/P-016):** the chosen Option C for
  Defect 1 keeps the gate read-only and hands convergence to Ship's external
  loop. Rejecting Option A (inject a claim) is correct and explicitly grounded
  in 109-F's verbatim authority boundary. ✔
- **Fail-closed discipline:** Defect 3's contract requires `READY` by default
  and only accepts `READY_WITH_CONDITIONS` on machine-readable per-condition
  evidence; malformed frontmatter fails closed — consistent with the PR #297
  "silent fail-open" remediation class. ✔
- **Width isolation:** 109.022-T is CLI-surface (`cli.py`); 109.021-T and
  109.023-T are gate-module (`topology.py`). No task mixes CLI + gate + schema
  + template families. ✔
- **2-hour / two-axis granularity gate:** each task is a single function-area
  + its tests. 109.021-T is `complexity: high` but de-risked by the
  deliberation (the sanctioned de-risking step), keeping it a single `size: M`
  unit rather than forcing a further split. ✔
- **Cycle safety:** fix tasks depend on nothing but the single 023→021 edge;
  activation tasks depend only on fix tasks; acyclic. ✔
- **Smallest coherent plan:** no separate prerequisite shipment created — the
  three small same-feature fixes join 115-S ahead of its activation set. ✔

## Findings

### F-1 (P1) — Docs (109.010-T) and tests (109.015-T) appeared to bypass the gating
**Raised:** the plan blocks only 5 activation tasks (007, 008, 013, 017, 018)
and leaves 010/015 unblocked; a naive read suggests documentation and
integration tests could execute *before* the fixes, which for B5 (which
exercises the gate through hooks) would be wrong.
**Resolution (VERIFIED):** 010 and 015 both already declare `depends_on:
[109.013-T]`, and 013 is directly blocked by all three fixes. Therefore 010
and 015 are **transitively** sequenced after 021/022/023 via 013 → they cannot
become eligible until the fixes complete. Coverage of the activation-adjacent
set is thus **complete**: 007/008/013/017/018 directly, 010/015 transitively.
No additional edges required; leaving them unblocked is correct and preserves
their existing intra-115-S ordering. Closed.

### F-2 (P1) — Cross-fix token/exit_code interlock could silently regress
**Raised:** Defect 1 introduces a new retry-required token whose exit_code
must be classified `failed` by Defect 2's mapping; if 109.022-T is written to
only special-case `exit_code == 2` literally, the new token's value could slip
back into `success`.
**Resolution:** the plan's hardening item 2 pins the mapping as *any* non-zero
/ non-`blocked` / non-`forced` → `failed` (not a literal `== 2` special-case),
and requires a cross-reference test in whichever task lands second. Both task
acceptance criteria carry the interlock. Closed.

### F-3 (P2) — closure_complete stricter predicate could retroactively block a legitimate predecessor
**Raised:** requiring `READY` (vs. non-`BLOCKED`) could flip an already-shipped
predecessor whose closure doc used `READY` but with an unusual field shape,
blocking downstream readiness.
**Resolution:** hardening item 4 mandates a backward-compat regression test
over a `READY`+compaction-done fixture so legitimately-complete closures stay
complete. The only intended flip is `READY_WITH_CONDITIONS`-without-evidence →
not-complete, which is the desired fix. Accepted.

### F-4 (P2 → **escalated to P1** in re-review 2026-08-05b) — Ship-side consumption of the retry-required token
**Raised:** the gate returning a retry-required token is inert unless Ship's
claim-retry loop consumes it; if the activation task 109.017-T (Ship wiring)
does not cover that, the contract is half-wired.
**Initial disposition (2026-08-05a):** Accepted as a downstream scope note —
109.017-T is downstream of the fixes in the same shipment, so it "lands in the
correct order." Recorded as a handoff flag; no change to plan scope.
**Re-review (2026-08-05b) — ESCALATED to P1 and RESOLVED:** the "correct order"
argument is necessary but NOT sufficient. On inspection, 109.017-T's acceptance
criteria never defined the consumption path AND one criterion (`each invocation
point halts fail-closed on a non-zero verdict`) directly *contradicted*
109.021-T's contract, under which `CLAIM_NOT_OBSERVED` is non-zero,
non-`blocked`, and retry-required (must NOT halt). A downstream task that would
halt on the very token its upstream produces is a half-wired contract, not a
benign ordering note — hence P1, not P2.
**Resolution (VERIFIED):** 109.017-T amended (backlog-only, Stage-scoped) so the
immediate post_claim invocation consumes `CLAIM_NOT_OBSERVED` via a bounded
Ship-owned reclaim-and-reverify sequence — double-claim status re-read first
(safe if the original claim already succeeded despite the token; no double
claim), then a re-run of full `--phase pre_claim` checks, then the actual
supported claim performed exactly once (`backlogit shipment claim` /
`OP_CLAIM_SHIPMENT_MCP`; no CAS/lock/lease invented), then an immediate
post_claim re-verify; bound = one cycle, reconciled with the Ship template's
existing Step 4a single claim-retry. All other non-zero/invalid verdicts
(exit 1/2, `CLAIM_VERIFY_FAILED`, `SHIPMENT_STATE_INCONSISTENT`) remain terminal;
`CLAIM_NOT_OBSERVED` at post_claim is the only carve-out. Explicit
structural/unit acceptance tests added to 109.017-T prove the generated Ship
instructions contain and order the bounded, token-specific, double-claim-guarded
path. The `109.017-T → 109.021-T` blocks edge already existed (producer precedes
consumer); no new task/dependency; 115-S stays task-only 10 members;
`complexity: medium → high` (de-risked by the fully-specified contract, single
size:M unit). Closed.

## Re-Review (2026-08-05b) — verdict re-affirmed

**Scope:** the single P1 escalated from F-4 above, its repair on 109.017-T, and
the coordinated updates to 109-F DoD, the implementation plan (Re-Review
Addendum), and session memory.

**Checked:**
- **Detection-vs-mutation preserved (P-001/P-016):** the repair adds NO claim to
  the gate. Ship (the caller) performs the single intervening claim between the
  gate's pre_claim detect-before and post_claim detect-after reads — exactly the
  division the deliberation mandates. The gate stays a pure detector. ✔
- **No invented atomicity:** the sequence reuses backlogit's existing unlocked
  claim; no CAS/lock/lease/serialization is asserted, consistent with 109-F's
  verbatim authority boundary. ✔
- **Double-claim safety / ambiguity fail-closed:** the double-claim guard
  re-reads status first and converges without reclaiming when the original claim
  already succeeded; two-or-more-active / mismatched-single / inconsistent
  snapshot / unexpected status all stay terminal `CLAIM_VERIFY_FAILED`. ✔
- **Boundedness:** at most one reclaim-and-reverify cycle, reconciled with the
  existing Step 4a single claim-retry; a second `CLAIM_NOT_OBSERVED` is terminal.
  No unbounded loop. ✔
- **Carve-out is token- and phase-specific:** only `CLAIM_NOT_OBSERVED` at the
  immediate post_claim invocation; never applied to pre_claim/lifecycle/build/
  PR/closure; all other non-zero verdicts terminal. ✔
- **Testability:** structural/unit assertions parse ordering and presence of the
  path (not string counts), and assert terminal verdicts never reclaim and the
  double-claim guard precedes any reclaim. ✔
- **Scope discipline:** backlog + planning + memory artifacts only; no template/
  source/config edit, no shipment claim, no new task/dependency; 115-S unchanged
  at 10 task-only members. ✔

**Verdict: PASS — 0 P0, 0 unresolved P1.** The producer→consumer contract for
`CLAIM_NOT_OBSERVED` is now fully wired and correctly ordered within 115-S.

## Re-Review (2026-08-05c) — F-5 (P1): gate must not classify delayed vs failed on the indistinguishable first snapshot

### F-5 (P1) — Producer required an unsatisfiable "failed-claim → terminal" gate test
**Raised.** `109.021-T` (and the deliberation/plan/memory echoing it) required
the gate to "add delayed-claim (retry-required) **and failed-claim (terminal)**
tests" and to "preserve terminal `CLAIM_VERIFY_FAILED` … for a genuinely failed
claim." This asks the **stateless read-only** gate to **distinguish** a delayed
claim from a failed claim on the post-claim snapshot. It **cannot**: a delayed
claim and a failed claim are identical at that snapshot (target still `queued`,
zero active). A producer acceptance/test that demands terminal
`CLAIM_VERIFY_FAILED` for that indistinguishable first snapshot is unsatisfiable
and directly contradicts the `CLAIM_NOT_OBSERVED` retry-required contract; it
also duplicates terminal-classification responsibility that `109.017-T` already
owns. Half-defined / self-contradictory producer contract → **P1**.

**Resolution (VERIFIED).** Backlog-only, Stage-scoped, CLI-only backlogit — no
template/source/config edit, no claim, no commit/push:

- **`109.021-T` (producer, `backlogit update --description`):** the read-only
  post-claim snapshot `queued` + zero active now **consistently emits
  `CLAIM_NOT_OBSERVED`** (retry-required, non-`blocked`) **without classifying
  delayed vs failed**. Terminal `CLAIM_VERIFY_FAILED` is reserved **only** for
  the discriminable ambiguity cases (`SHIPMENT_STATE_INCONSISTENT`,
  two-or-more-active, mismatched-single-active). The "failed-claim → terminal"
  producer test is **removed**; the producer now tests delayed/failed
  (indistinguishable) → `CLAIM_NOT_OBSERVED` and the ambiguity cases → terminal.
  An explicit criterion forbids any producer test requiring terminal
  `CLAIM_VERIFY_FAILED` for a `queued` + zero-active first snapshot.
- **`109.017-T` (consumer) — NO change required.** Its acceptance criteria
  **already** place all failure/exhaustion classification on the caller: after
  the one bounded double-claim-guarded retry, a **second** `CLAIM_NOT_OBSERVED`
  (bound exhausted) → terminal `CLAIM_VERIFY_FAILED`, and actual ambiguity stays
  terminal immediately. Verified by re-reading `109.017-T`; the producer/consumer
  split is now consistent on both sides.
- **`109-F` DoD (`backlogit update --section dod`):** the Ship-ordering bullet
  now records that the gate emits `CLAIM_NOT_OBSERVED` for the indistinguishable
  snapshot without classifying delayed vs failed, and that all failure/exhaustion
  classification is owned by `109.017-T`.
- **Plan / deliberation / memory** aligned (plan Re-Review Addendum 2026-08-05c;
  deliberation Correction 2026-08-05c; memory addendum).

**Checked:**
- **Detection-vs-mutation preserved (P-001/P-016):** the fix removes a
  classification the gate cannot perform; it adds no claim/mutation. Gate stays a
  pure detector. ✔
- **No responsibility gap:** the terminal side is fully owned by `109.017-T`
  (bounded retry → second `CLAIM_NOT_OBSERVED` terminal; ambiguity terminal
  immediately). No state is left unclassified. ✔
- **Producer/consumer consistency:** `109.021-T` emits, `109.017-T` classifies;
  the `109.017-T → 109.021-T` blocks edge already existed (producer precedes
  consumer). ✔
- **Scope discipline:** backlog + planning + memory artifacts only; no
  template/source/config edit, no claim, no new task/dependency; **115-S remains
  task-only 10 members** (M:7/S:3). ✔

**Verdict: PASS — 0 P0, 0 unresolved P1.** The producer no longer asks the gate
to distinguish delayed vs failed; the indistinguishable first snapshot uniformly
yields `CLAIM_NOT_OBSERVED`, and terminal failure/exhaustion classification lives
solely in `109.017-T`.

## Final Independent Review (2026-08-05d)

**Verdict: READY_WITH_FOLLOWUPS — P0=0, P1=0, P2=2, P3=1.** Both P2 findings
were resolved before publication: the session-memory summary now states that
delayed and failed first snapshots both emit `CLAIM_NOT_OBSERVED`, and the new
decision/plan/review artifacts declare their required `doc_type` and `source`
frontmatter. The P3 obsolete Ship step references were normalized from Step
0.5.5 to the current Step 4a. No implementation blocker remains.

## Audit-log discrepancy (Defect 4) — disposition reviewed

The deliberation classifies the missing `shipment_status_changed: shipped`
event as **external backlogit-owned**, not an autoharness code defect and not
a `115-S` blocker, grounded in the correct persisted state
(`archived_status: shipped`) and the `2026-07-02-cascade-guard` external-bug
precedent. **Concur.** Recording it as a labeled deferred stash entry (no
fabricated autoharness fix, no mutation of the backlogit repo) is the correct,
evidence-bounded action. ✔

## Conclusion

PASS — 0 P0, 0 unresolved P1. Harvest 109.021-T / 109.022-T / 109.023-T with
the stated size/complexity, add them to 115-S (task-only), and wire the
explicit `blocks` edges as specified.
