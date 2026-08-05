---
title: "114-S Closure Pre-Activation Fixes — Implementation Plan"
description: "Decomposes the three mandatory 114-S closure follow-up code defects into three width-isolated, two-axis-sized tasks under feature 109-F, sequenced BEFORE the 115-S topology-gate activation tasks via explicit intra-shipment blocks dependencies. Covers the post-claim retry outcome-contract fix, the cli.py telemetry outcome mapping fix, and the closure_complete() releasability enforcement fix, plus the external disposition of the 114-S audit-log discrepancy."
doc_type: plan
source: docs/plans/2026-08-05-114s-closure-preactivation-fixes-plan.md
source_documents:
  - "docs/decisions/2026-08-05-114s-closure-preactivation-fixes-deliberation.md"
  - "docs/closure/114-S-109-F-post-merge-closure.md"
  - "docs/compound/114-S-109-F-copilot-review-fix-patterns.md"
feature: "109-F"
tasks:
  - "109.021-T"
  - "109.022-T"
  - "109.023-T"
shipment: "115-S"
scope: "src/autoharness/gates/topology.py + src/autoharness/cli.py + their tests (no template, schema, or CLI-subcommand-surface additions)"
requires_plan_hardening: "yes"
tags:
  - "topology-gate"
  - "fail-closed"
  - "detection-vs-mutation"
  - "P-001"
  - "P-016"
  - "closure"
  - "pre-activation"
---

## Problem Frame

The `114-S`/`109-F` post-merge closure is `READY_WITH_CONDITIONS`. Its
Releasability condition requires three pre-existing correctness defects in
merged `main` code to be **fixed and verified before `115-S` wires the
topology gate into any hook or automated caller** (before the gate becomes a
live enforcement point). This plan decomposes those three fixes and sequences
them ahead of the `115-S` activation tasks. Design decisions for the two
non-mechanical defects are settled in the linked deliberation.

## Design Decisions (from deliberation — fixed, not re-opened)

1. **Post-claim retry** → replace the illusory internal self-retry with an
   explicit **retry-required outcome contract** (`CLAIM_NOT_OBSERVED`, exit
   non-zero and non-`blocked`); the gate stays a read-only detector and never
   claims (P-001/P-016 preserved); Ship's external claim-retry-and-recall loop
   drives convergence.
2. **`closure_complete()`** → require `closure_status: READY` by default;
   accept `READY_WITH_CONDITIONS` only with machine-readable per-condition
   `satisfied: true` + `evidence`; everything else fails closed.
3. **cli.py telemetry** → non-zero, non-`blocked`, non-`forced` outcome →
   `failed` (mechanical).
4. **Audit-log discrepancy** → external backlogit-owned; deferred tracking
   stash entry only; no autoharness fix; not a blocker.

## Task Decomposition (three width-isolated, ≤2h tasks under 109-F)

### 109.021-T — Gate: post-claim retry becomes a read-only retry-required contract
- **Family/width:** gate module (`src/autoharness/gates/topology.py`) + its unit tests. No CLI-surface, template, or schema change.
- **Scope:**
  - Remove the second internal `list_shipments()` "retry" read that pretends to converge with no intervening mutation.
  - When pre-claim revalidation passes but the target is still `queued` with zero active, return a distinct **retry-required** result (`CLAIM_NOT_OBSERVED`; exit_code non-zero and **not** `blocked`) whose message directs the caller to (re)claim and re-invoke `post_claim`. This holds whether the claim is merely **delayed** or genuinely **failed** — the two are **indistinguishable** to a stateless read-only detector (both present as target `queued` + zero active), so both MUST yield the same `CLAIM_NOT_OBSERVED` token. The gate never tries to classify delayed vs failed on that first snapshot.
  - Preserve terminal `CLAIM_VERIFY_FAILED` **only** for the snapshots the gate can genuinely discriminate: inconsistent snapshots (`SHIPMENT_STATE_INCONSISTENT`) and two-or-more-active / mismatched-single-active. A `queued` + zero-active snapshot is **never** classified terminal by the gate.
  - **Repair the misleading unit test** whose fake reader silently advances its snapshot to mask the gap.
  - Add tests: genuinely delayed claim → retry-required (not a false pass, not premature terminal). A genuinely **failed** claim is **indistinguishable** from a delayed one at the first read-only post-claim snapshot (both `queued` + zero active) → it **too** returns `CLAIM_NOT_OBSERVED`; the producer MUST NOT assert terminal `CLAIM_VERIFY_FAILED` for that indistinguishable first snapshot. Terminal classification on **retry-exhaustion** (a second `CLAIM_NOT_OBSERVED` after the one bounded retry → terminal `CLAIM_VERIFY_FAILED`) is owned and tested by **109.017-T**, not this task. The gate's terminal tests cover only the discriminable ambiguity cases (inconsistent snapshot / two-or-more-active / mismatched-single-active).
- **Acceptance criteria:**
  - The gate performs **no** backlogit transition/claim (grep proof: no claim/mutation call added on the post_claim path); P-001/P-016 preserved.
  - Any `queued` + zero-active post-claim snapshot (delayed **or** failed — indistinguishable) returns the retry-required token, not `success` and not immediate `CLAIM_VERIFY_FAILED`. No producer test requires terminal `CLAIM_VERIFY_FAILED` for a `queued` + zero-active first snapshot.
  - The repaired test fails against the *old* illusory-loop code and passes against the new contract.
  - Offline `pytest` for the topology gate module passes.
- **Interlock:** the retry-required exit_code must be classified by 109.022-T's mapping as `failed` (non-zero, non-`blocked`), never `success`.
- **size: M · complexity: high** (design uncertainty de-risked by the deliberation; single function + tests keeps it ≤2h).

### 109.022-T — CLI: telemetry outcome mapping classifies invalid/error results as failed
- **Family/width:** CLI surface (`src/autoharness/cli.py`) + its tests. **Width-isolated** from the gate-module tasks.
- **Scope:**
  - Replace the `success`-default fall-through (`cli.py:735–739`) so mapping is: `forced` → `operator_required`; `exit_code == 1` → `blocked`; **any other non-zero (incl. `exit_code == 2`)** → `failed`; `exit_code == 0` → `success`.
  - Keep the existing `result.message` exclusion from the telemetry fingerprint (do not regress PR #297's round-7 fix).
- **Acceptance criteria:**
  - Tests assert the mapping for exit_code 0 → success, 1 → blocked, 2 → failed, forced → operator_required, and an arbitrary other non-zero → failed.
  - Test asserting the new `CLAIM_NOT_OBSERVED` retry-required exit_code maps to `failed` (cross-fix guard), or an equivalent parametrized non-zero case if 109.021-T's token value is finalized after this task starts.
  - Offline `pytest` for the CLI telemetry mapping passes.
- **size: S · complexity: low.**

### 109.023-T — Gate: closure_complete() enforces closure_status/releasability
- **Family/width:** gate module (`src/autoharness/gates/topology.py`) + its unit tests. No CLI-surface, template, or schema change.
- **Scope:**
  - `closure_complete()` returns `True` only when BOTH `compaction_status ∈ {done, degraded}` AND (`closure_status == READY` OR a valid machine-readable verified-conditions block).
  - Implement the structured `conditions:` contract: `READY_WITH_CONDITIONS` counts as complete only if the block exists, is well-formed, non-empty, and every entry has `satisfied: true` with a non-empty `evidence` ref.
  - Fail closed on: `BLOCKED`, missing `closure_status`, `READY_WITH_CONDITIONS` with no/empty conditions block, any `satisfied: false`/missing-evidence entry, malformed frontmatter (reuse the fail-closed `_frontmatter` discipline; never `{}`-swallow).
- **Acceptance criteria (negative tests mandatory):** `BLOCKED` → not complete; missing `closure_status` → not complete; `READY_WITH_CONDITIONS` without conditions → not complete; `READY_WITH_CONDITIONS` with an unverified/`satisfied: false` or evidence-less condition → not complete; malformed frontmatter → not complete; `READY` (+ compaction done) → complete; `READY_WITH_CONDITIONS` with a fully-verified conditions block → complete.
  - Offline `pytest` for the closure_complete path passes.
- **size: M · complexity: medium.**

## Dependency Sequencing (intra-shipment, executable under backlogit 1.8.0 queued+blocks)

New fix tasks join **115-S** (task-only manifest; the smallest coherent plan —
no separate prerequisite shipment is needed because all three fixes are small,
same-feature, and belong ahead of the same activation set).

**Same-file serialization:** 109.021-T and 109.023-T both edit
`topology.py`; serialize to avoid concurrent-edit friction:
- `109.023-T` **blocks-depends-on** `109.021-T`.

**Activation-after-fixes** (the core condition). The `115-S` activation /
wiring tasks — those that make the gate a live enforcement point — each
**block-depend-on all three fix tasks**:
- Activation set = `109.007-T` (B1 pre-push hook), `109.008-T` (B2 pre-commit hook), `109.013-T` (B3 install/activation + verify assertion), `109.017-T` (B6 Ship wiring), `109.018-T` (B7 Orchestrator wiring).
- Each of the 5 activation tasks depends_on `109.021-T`, `109.022-T`, `109.023-T`.
- **Not blocked:** `109.010-T` (B4 docs) and `109.015-T` (B5 tests) are *not* activation points (they document/test, they do not wire the gate into a caller), so they are intentionally left unblocked to preserve parallelism. Rationale recorded so the omission is deliberate, not accidental.

**Cycle safety:** fix tasks depend on nothing except the single 023→021 edge;
activation tasks depend only on fix tasks; no fix task depends on any
activation task. Acyclic. Existing edges (e.g. 013→{007,008}, 017/018→002,
015→013) are preserved and do not conflict.

**Shipment dependency edges** (`115-S`→`114-S`, `116-S`→`115-S`) are unchanged;
no new shipment needed, so serial shipment ordering is untouched.

## Feature 109-F planning / handoff updates

- Append a **Pre-activation conditions** planning note to `109-F` recording
  that 109.021/022/023-T gate the 115-S activation set, referencing this plan
  and the closure doc.
- Record the closure handoff reference: `114-S`'s `READY_WITH_CONDITIONS`
  conditions are now tracked as these three tasks; amending the `114-S`
  closure doc to `READY` (or to a verified `conditions:` block) is a
  **follow-up handoff note**, not part of any fix task's scope.

## Out of scope / non-goals

- No change to the gate's CLI subcommand surface, argument parsing, or the
  four topology invariants themselves.
- No mutation of `C:\Source\GitHub\backlogit`; no synthetic audit-log entry.
- No claiming of `115-S`/`116-S`; no build/PR/branch/worktree; Stage-only.

## Validation strategy

- Offline `uv run python -m pytest tests -q` for the touched modules (sandbox
  has no PyPI network; offline suite is the available evidence, per 114-S
  precedent).
- `uv run autoharness --help` smoke (CLI import/parse intact) after 109.022-T.
- Each task's negative/positive tests as enumerated above.

## Plan Hardening (P-006)

**Hardening required: YES.** Blast radius is elevated — the changes touch the
topology **gate module** (the mechanical enforcement core of P-001/P-016), the
**CLI telemetry** surface, and they gate the entire `115-S` activation set.
This is not a single-template edit, so hardening is mandatory before review.

### Blast-radius analysis

| Change | Direct surface | Downstream / hidden dependents | Risk |
| ------ | -------------- | ------------------------------ | ---- |
| 109.021-T retry contract | `topology.py` post_claim path | Ship's Step 4a external claim-retry loop (must consume the new token); the four topology invariants (must be untouched); telemetry mapping (109.022-T interlock) | **High** — an incorrect token or an accidental mutation would breach the authority boundary or leave Ship unable to converge |
| 109.022-T telemetry mapping | `cli.py:735–739` | outcome-metrics consumers; must not regress the round-7 `result.message` exclusion | **Medium** — mis-mapping corrupts metrics silently (the exact defect class being fixed) |
| 109.023-T closure_complete | `topology.py` dependency-readiness invariant | every caller relying on closure completeness as a `shipped`-readiness signal; the `114-S` closure doc's own evaluation flips to not-complete until amended | **Medium-High** — over-strictness could block a legitimately-complete predecessor; under-strictness reproduces the fail-open bug |

### Hardening decisions (fold into task acceptance)

1. **Authority-boundary guard (109.021-T):** acceptance MUST include a
   proof that no claim/mutation call is added on the post_claim path (grep/AST
   check) — the gate stays a pure detector. A reviewer checklist item, not
   just prose.
2. **Token/exit_code interlock (109.021-T ↔ 109.022-T):** the retry-required
   token's exit_code is chosen so 109.022-T maps it to `failed` (non-zero,
   non-`blocked`). Both tasks carry a cross-reference test. If 109.021-T lands
   first, 109.022-T's test pins the concrete value; if 109.022-T lands first,
   it uses a parametrized non-zero case and 109.021-T adds the concrete-value
   assertion. Either order is safe because 109.023-T→109.021-T is the only
   intra-fix ordering edge and 109.022-T is width-isolated.
3. **No behavior change to the four invariants (109.021-T, 109.023-T):**
   acceptance requires the existing invariant tests to remain green unchanged
   — the fixes only change the *retry outcome* and the *closure-completeness*
   predicate, never invariant logic.
4. **Backward-compatibility of closure contract (109.023-T):** existing
   closure docs with `closure_status: READY` (and compaction done) MUST still
   evaluate complete; a regression test over a representative prior closure
   (e.g. a `READY` fixture) is required so the stricter predicate does not
   retroactively block already-shipped predecessors.
5. **Fail-closed on malformed input (109.023-T):** reuse the PR #297
   fail-closed `_frontmatter` discipline; malformed/missing frontmatter →
   `False`, never `{}`-swallow → `True`.
6. **Amend-114S-closure is a separate handoff note**, not code scope — so the
   fix tasks cannot be gamed into "passing" by editing the closure doc.

### Residual risk after hardening

- **Ship-side token consumption** is realized in the activation task
  `109.017-T` (Ship wiring), which is *downstream* of these fixes in the same
  shipment — so the gate contract and its consumer land in the correct order.
  **RESOLVED (re-review 2026-08-05b):** the earlier "scope note … flagged for
  review" was escalated to a P1 because `109.017-T`'s acceptance criteria did
  NOT define the token-consumption path and one criterion (`each invocation
  point halts fail-closed on a non-zero verdict`) actively contradicted
  `109.021-T`'s retry-required contract. `109.017-T` has now been amended (see
  the Re-Review Addendum below) to consume `CLAIM_NOT_OBSERVED` through a
  bounded Ship-owned reclaim-and-reverify sequence, with explicit
  structural/unit assertions and a double-claim guard; all other non-zero/
  invalid verdicts remain terminal. The `109.017-T → 109.021-T` blocks edge
  already existed, so producer precedes consumer in `115-S`. No new task and
  no new dependency were required; `115-S` remains task-only 10 members.
- No schema or template family is touched by the three fix tasks, so the wider
  harness-manifest / installed-mirror blast radius is **not** in play here.

## Re-Review Addendum (2026-08-05b) — P1 fix: 109.017-T consumes CLAIM_NOT_OBSERVED

**Trigger.** Post-harvest review of the *activation* set surfaced a single P1:
`109.021-T` defines `CLAIM_NOT_OBSERVED` as a read-only retry-required contract
(non-zero, non-`blocked`, caller-drives-reclaim), but `109.017-T` still stated
every non-zero gate verdict halts fail-closed and its acceptance criteria/tests
never defined the consumption path. The plan *claimed* `109.017-T` would consume
the token; the task did not. Half-wired contract → P1.

**Repair (backlog-only; Stage-scoped; no template/source/config edits).**
`109.017-T` acceptance criteria now specify, at the **immediate post_claim**
invocation only:

1. **Two-outcome split.** `CLAIM_NOT_OBSERVED` (pre_claim topology valid, target
   still `queued`, zero active) is NOT terminal → drives the bounded sequence.
   Genuine ambiguity (any other active, mismatched single active,
   `SHIPMENT_STATE_INCONSISTENT`) stays terminal `CLAIM_VERIFY_FAILED`.
2. **Bounded Ship-owned reclaim-and-reverify (≤1 cycle), in order:**
   (a) *double-claim guard first* — re-read shipment status via CLI; if already
   `active` and the post_claim GLOBAL re-verify shows sole-active-target, the
   original claim succeeded despite the token → converged, **do not reclaim**;
   ambiguity → terminal. (b) only if still `queued`/zero-active, re-run full
   `--phase pre_claim` GLOBAL checks (non-zero → terminal). (c) perform the
   *actual supported* claim exactly once (`backlogit shipment claim` /
   `OP_CLAIM_SHIPMENT_MCP`; backlogit's existing unlocked read/check/write — **no
   CAS/lock/lease invented**). (d) re-run immediate `--phase post_claim`; exit 0/
   sole-active-target → converge; a second `CLAIM_NOT_OBSERVED` (bound exhausted)
   or any ambiguity → terminal `CLAIM_VERIFY_FAILED`. Bound reconciled with the
   Ship template's existing Step 4a single claim-retry.
3. **All other verdicts terminal.** exit 1/2, `CLAIM_VERIFY_FAILED`,
   `SHIPMENT_STATE_INCONSISTENT` remain fail-closed at every invocation;
   `CLAIM_NOT_OBSERVED` is the ONLY carve-out and only at post_claim.
4. **Structural/unit acceptance tests** (added to `109.017-T`, which owns the
   Ship-wiring `_ship.agent.md.tmpl` + scoped assertion files) prove the
   generated Ship instructions CONTAIN and ORDER the path (double-claim re-read →
   pre_claim re-check → single claim → post_claim re-verify → converge-or-
   terminal), that it is bounded to one cycle, token-specific, double-claim
   guarded, and that terminal verdicts never reclaim. Assertions parse ordering,
   not string counts.

**Coordination with 109.021-T (detection-only).** The gate never claims; Ship
supplies the single intervening claim between the gate's pre_claim detect-before
and post_claim detect-after reads — exactly the "intervening mutation the gate is
forbidden to perform" from the deliberation. No atomic-exclusion guarantee is
asserted anywhere.

**Sizing.** `109.017-T` bumped `complexity: medium → high` (genuine token-
consumption/double-claim/ambiguity reasoning), de-risked by this fully-specified
acceptance contract so it stays a single `size: M` unit in the same template
family — no split, mirroring `109.021-T`'s M/high de-risking precedent.

**Dependency/scope.** No new dependency (the `109.017-T → 109.021-T` blocks edge
already existed) and no new task; `115-S` remains task-only 10 members. Feature
`109-F` DoD Ship-ordering bullet amended to record the bounded consumption.

**Verdict after re-review: PASS — 0 P0, 0 unresolved P1.**

## Re-Review Addendum (2026-08-05c) — P1 fix: gate must not classify delayed vs failed on the indistinguishable first snapshot

**Trigger.** A single P1 was found in the *producer* task and its supporting
artifacts: `109.021-T` (and the deliberation/plan/memory echoing it) required the
gate to "add delayed-claim (retry-required) **and failed-claim (terminal)**
tests" — i.e. it asked the stateless read-only gate to **distinguish a delayed
claim from a failed claim** on the post-claim snapshot and emit terminal
`CLAIM_VERIFY_FAILED` for the failed case. It **cannot**: a delayed claim and a
failed claim are byte-for-byte identical at that snapshot (target still `queued`,
zero active). Requiring a terminal producer test for that indistinguishable first
snapshot is unsatisfiable and contradicts the retry-required contract; terminal
failure/exhaustion classification already belongs to `109.017-T`.

**Repair (backlog-only; Stage-scoped; CLI-only backlogit; no template/source/config
edit, no claim, no commit/push).**

1. **Producer contract clarified (`109.021-T`).** The read-only post-claim snapshot
   `queued` + zero active now **consistently emits `CLAIM_NOT_OBSERVED`**
   (retry-required, non-`blocked`) **without classifying delayed vs failed**. The
   gate reserves terminal `CLAIM_VERIFY_FAILED` **only** for the snapshots it can
   genuinely discriminate: inconsistent snapshot (`SHIPMENT_STATE_INCONSISTENT`),
   two-or-more-active, and mismatched-single-active.
2. **Producer test removed.** The "failed-claim → terminal" producer
   acceptance/test is **removed**; a genuinely failed claim at the first snapshot
   returns `CLAIM_NOT_OBSERVED` like a delayed one. The producer tests now cover:
   delayed/failed (indistinguishable) `queued`+zero-active → `CLAIM_NOT_OBSERVED`,
   and the discriminable ambiguity cases → terminal.
3. **Failure/exhaustion classification consolidated in `109.017-T`.** After its
   one bounded double-claim-guarded retry, a **second** `CLAIM_NOT_OBSERVED`
   becomes terminal `CLAIM_VERIFY_FAILED`; actual ambiguous states remain terminal
   immediately. `109.017-T`'s acceptance criteria **already** specify exactly this
   (a SECOND `CLAIM_NOT_OBSERVED` bound-exhausted or any ambiguity → terminal), so
   **no change to `109.017-T` was required** — it already owns the terminal side.

**Coordination.** Producer (`109.021-T`, detection-only, never classifies
delayed/failed and never claims) → consumer (`109.017-T`, owns bounded retry +
terminal exhaustion). The `109.017-T → 109.021-T` blocks edge already existed
(producer precedes consumer).

**Dependency/scope.** No new task, no new dependency; `115-S` remains task-only
**10 members** (M:7/S:3 unchanged). Feature `109-F` DoD Ship-ordering bullet
amended to record that the gate emits `CLAIM_NOT_OBSERVED` for the indistinguishable
snapshot and that terminal classification is owned by `109.017-T`.

**Verdict after re-review: PASS — 0 P0, 0 unresolved P1.**
