---
title: "114-S Closure Pre-Activation Fixes: Deliberation and Direction"
description: "Resolves the two design-decision defects among the three mandatory 114-S closure follow-ups that MUST land before 115-S activates the topology gate: (1) the bounded post-claim retry in topology.py that re-reads state but never converges, and (3) closure_complete() validating only compaction_status. Also records the disposition of the 114-S audit-log completeness discrepancy as external backlogit-owned. Fix (2), the cli.py telemetry outcome mapping, is mechanical and needs no deliberation."
doc_type: decision
source: docs/decisions/2026-08-05-114s-closure-preactivation-fixes-deliberation.md
topic: "For the two topology.py defects flagged by 114-S closure, what bounded contract preserves the gate's read-only detection authority (P-001/P-016) while making the post-claim retry and closure_complete() actually correct?"
depth: "deep"
decision_status: "accepted"
promoted_to: "docs/plans/2026-08-05-114s-closure-preactivation-fixes-plan.md"
linked_artifacts:
  - "src/autoharness/gates/topology.py"
  - "src/autoharness/cli.py"
  - "docs/closure/114-S-109-F-post-merge-closure.md"
source_documents:
  - "docs/closure/114-S-109-F-post-merge-closure.md"
  - "docs/compound/114-S-109-F-copilot-review-fix-patterns.md"
  - "docs/decisions/2026-07-02-shipment-closure-cascade-guard-deliberation.md"
feature: "109-F"
backlog_items:
  - "109-F"
  - "109.021-T"
  - "109.022-T"
  - "109.023-T"
shipment: "115-S"
tags:
  - "topology-gate"
  - "fail-closed"
  - "detection-vs-mutation"
  - "P-001"
  - "P-016"
  - "closure"
  - "backlogit"
---

## Problem Frame

Shipment `114-S` (gate A of feature `109-F`'s staged A→B→C topology-gate
rollout) shipped and closed `READY_WITH_CONDITIONS`. Its post-merge closure
(`docs/closure/114-S-109-F-post-merge-closure.md`) surfaced **three
pre-existing correctness defects** in already-merged `main` code, plus **one
audit-log completeness discrepancy**. The closure's Releasability verdict
makes fixing the three code defects a hard **condition that must be satisfied
before `115-S` wires the gate into any hook or automated caller** — i.e.
before the gate becomes a live enforcement point.

Two of the three code defects carry a genuine design decision and are
deliberated here. The third (telemetry outcome mapping) is mechanical and is
planned directly. The audit-log discrepancy's disposition is also recorded
here because it turns on a repository-ownership judgment, not a code choice.

The governing constraint for both topology.py defects is `109-F`'s own
**AUTHORITY BOUNDARY** (verbatim from the feature description):

> The gate is a read-only detector/validator of persisted state plus local
> git branch/worktree topology; it provides pre/post detection and
> fail-closed remediation, never atomic exclusion, and **never mutates
> backlogit transitions**. … ClaimShipment is an unlocked read/check/write
> … but no CAS, lock, lease, or serialization exists at any local or
> cross-machine scope.

Any fix that has the gate itself perform a claim/mutation to "make the retry
work" would **violate P-001** (detection-vs-mutation separation) and the
feature's stated authority boundary. This single constraint drives both
decisions below.

## Prior Learnings Applied

- `docs/compound/114-S-109-F-copilot-review-fix-patterns.md` — the "silent
  fail-open" defect class exhausted across 12 Copilot rounds on PR #297. Both
  defects deliberated here are **new instances of the same class**: code that
  *appears* to check something but silently accepts an unconverged/unverified
  state. The remedy is the same discipline: fail closed, and never let an
  unverified value register as success.
- `docs/decisions/2026-07-02-shipment-closure-cascade-guard-deliberation.md`
  — precedent that defects living in the **external backlogit Go binary**
  are out of scope for this repository and must be handled harness-side or
  tracked externally, never by fabricating a patch to a binary autoharness
  does not own. This precedent governs the audit-log disposition below.

---

## Decision 1 — Bounded post-claim retry (`topology.py`, ~L658–690)

### What is actually wrong

`_evaluate_post_claim_with_retry` (the `post_claim` wrap path) does this when
the target is still `queued` with zero active shipments:

1. `revalidation = list_shipments()` → re-run `pre_claim` core (a **read**).
2. `retry = list_shipments()` → re-run `post_claim` core (a **read**).
3. If the target still is not the sole active shipment → `CLAIM_VERIFY_FAILED`.

There is **no operation between the two reads that could transition the
target from `queued` to `active`.** In production nothing claims the target
between reads, so a genuinely delayed or failed claim **deterministically**
ends in `CLAIM_VERIFY_FAILED`. The existing unit test only passes because its
fake reader advances its own snapshot on each call — masking the gap. The
retry, as written, is an **illusory convergence loop**: it re-reads and hopes,
but by the authority boundary it must never itself claim.

### Options considered

- **Option A — Inject a real claim operation** (callback/injected claimer)
  that the gate invokes between the reads. *Rejected.* This makes the gate a
  mutator of backlogit transitions, directly violating the `109-F` authority
  boundary and P-001. It also re-introduces the exact TOCTOU/atomicity
  illusion the feature description explicitly disclaims ("never atomic
  exclusion").

- **Option B — Remove the retry semantics entirely**; on a non-converged
  `post_claim` return `CLAIM_VERIFY_FAILED` immediately. *Rejected as the
  sole fix.* It is honest (no illusory loop) but discards the legitimate
  purpose: a *caller-driven* retry where an external actor (Ship) performs
  the claim and asks the gate to re-verify. Collapsing straight to a terminal
  failure removes Ship's ability to converge a slow-but-valid claim.

- **Option C (CHOSEN) — Replace the illusory self-retry with an explicit,
  bounded "retry-required / verification-pending" outcome contract** that
  hands convergence back to the caller. The gate detects that the target is
  still `queued` with zero active and the pre-claim topology is otherwise
  valid, and returns a **distinct, non-zero, non-`blocked` "claim not yet
  observed — re-invoke after (re)claim"** result (a `CLAIM_NOT_OBSERVED` /
  retry-required token), rather than pretending to loop internally. Ship's
  own external claim-retry-and-recall loop (its Step 4a) performs the
  actual claim and re-invokes the gate; the gate stays a pure detector. The
  bound is expressed as the **caller's** retry budget, not a fake internal
  loop. Where the current code genuinely has fresh state to check without a
  mutation (e.g. an inconsistent snapshot), it still returns
  `CLAIM_VERIFY_FAILED` as today.

### Chosen direction

**Option C.** Preserve detection-vs-mutation authority (P-001) and P-016 by
making the gate *report* the unconverged-but-valid condition with an explicit
retry-required outcome instead of simulating a claim it is forbidden to
perform. Concretely:

- Remove the second internal `list_shipments()` "retry" read that pretends to
  converge without any intervening mutation.
- When the pre-claim revalidation passes but the target is still `queued`
  with zero active, return a distinct retry-required result
  (`CLAIM_NOT_OBSERVED`, exit_code non-zero and **not** `blocked`) whose
  message states the caller must (re)claim and re-invoke `post_claim`.
- Keep the genuine terminal `CLAIM_VERIFY_FAILED` for inconsistent snapshots
  and for the two-or-more-active / mismatched-single-active cases.
- **Repair the misleading unit test** (its fake reader must not silently
  advance to mask the gap) and add tests for a genuinely delayed claim
  (returns retry-required, not a false pass and not a premature terminal
  failure). A genuinely failed claim is **indistinguishable** from a delayed
  one at the first read-only snapshot (both `queued` + zero active), so it
  **too** returns retry-required; terminal classification on retry-exhaustion
  is owned by the caller (`109.017-T`), while the gate keeps terminal
  `CLAIM_VERIFY_FAILED` only for discriminable ambiguity. (See Correction
  2026-08-05c below.)

> **Correction (2026-08-05c).** The bullet above originally read "…and a
> genuinely failed claim (still terminal)." That was wrong: a stateless
> read-only detector **cannot** tell a delayed claim apart from a failed one on
> the post-claim snapshot — both are target `queued` + zero active. So the
> indistinguishable first snapshot MUST **consistently emit `CLAIM_NOT_OBSERVED`
> (retry-required) without classifying delayed vs failed**, and the producer
> (`109.021-T`) MUST NOT assert a terminal `CLAIM_VERIFY_FAILED` for it.
> **All** failure/exhaustion classification lives in the caller `109.017-T`:
> after its one bounded double-claim-guarded retry, a **second**
> `CLAIM_NOT_OBSERVED` becomes terminal `CLAIM_VERIFY_FAILED`; actual ambiguous
> states (inconsistent snapshot, two-or-more-active, mismatched-single-active)
> remain terminal immediately. The gate's own terminal path covers only those
> discriminable ambiguity cases. This correction does not change the accepted
> Option C direction — it removes an unsatisfiable producer-test requirement
> that contradicted the read-only contract.

This is a de-risking of a `complexity: high` change: the deliberation itself
is the required de-risking step so the harvested task stays a single, bounded
`size: M` unit.

### Open questions / risks

- Exact token name (`CLAIM_NOT_OBSERVED` vs. reusing an existing
  retry-required token) and its exit_code value are an implementation detail
  for `impl-plan`; the contract (distinct, non-zero, non-`blocked`,
  caller-drives-reclaim) is fixed here. **Note the interlock with Decision 3
  / Defect 2:** whatever exit_code this token uses, `cli.py`'s telemetry
  mapping (Fix 2) must classify it correctly — it must NOT fall through to
  `success`. This is called out as a cross-fix acceptance criterion in the
  plan.
- Ship's Step 4a loop already exists (referenced in the 114-S closure);
  this change assumes it, and the plan must verify the token it expects. If
  Ship does not yet consume a retry-required token, the plan scopes the gate
  contract only and flags the Ship-side consumption as covered by the
  existing activation task `109.017-T` (Ship wiring), not silently assumed.

---

## Decision 2 — `closure_complete()` must validate closure_status/releasability (`topology.py`, ~L505–518)

### What is actually wrong

`closure_complete()` returns `True` as soon as any matching closure doc has
`compaction_status ∈ {done, degraded}`. It **never inspects `closure_status`
or releasability.** So the `114-S` closure — `closure_status:
READY_WITH_CONDITIONS` with three still-unmet conditions — already registers
as "complete" purely because `compaction_status: done`. This is the fail-open
class again: a `READY_WITH_CONDITIONS`/`BLOCKED`/missing closure passes the
dependency-readiness invariant it should gate.

### Options considered for accepted closure states

- **Option A — Accept any non-`BLOCKED` value.** *Rejected.* This is exactly
  the naive fix the closure doc warns against: it lets
  `READY_WITH_CONDITIONS` with unmet conditions register as complete.

- **Option B (CHOSEN) — Default require `closure_status: READY`.** A closure
  is complete only when BOTH `compaction_status ∈ {done, degraded}` AND
  `closure_status == READY`. `READY_WITH_CONDITIONS` is accepted **only** when
  accompanied by **machine-readable, structured evidence that every listed
  condition is independently verified satisfied** — not a free-text string.
  Anything else (`BLOCKED`, missing `closure_status`, `READY_WITH_CONDITIONS`
  without verified-condition evidence) → **not complete** (fail closed).

### Machine-readable condition-evidence contract

For `READY_WITH_CONDITIONS` to count as complete, the closure frontmatter must
carry a structured block (shape finalized in `impl-plan`, e.g.):

```yaml
closure_status: READY_WITH_CONDITIONS
conditions:
  - id: <stable-id>
    satisfied: true
    evidence: <verifiable ref — commit sha, task id, or artifact path>
```

`closure_complete()` returns `True` for this state **only if the block exists,
is well-formed, is non-empty, and every entry has `satisfied: true` with a
non-empty `evidence` ref.** A bare string value, a missing block, an empty
block, or any `satisfied: false`/absent → `False` (fail closed). Malformed
frontmatter → `False` (reuse the fail-closed `_frontmatter` discipline from
PR #297, never `{}`-swallow).

Deliberate note on **this very closure**: `114-S`'s closure doc records its
three conditions only as **prose**, not as a structured `conditions:` block —
so under this contract it correctly evaluates to **not complete** until either
(a) the three fixes land and the closure doc is amended to `READY` (or to a
verified `conditions:` block), or (b) both happen. That is the intended,
fail-closed behavior and is the mechanical backstop the closure doc's addendum
said was missing.

### Chosen direction

**Option B.** Require `READY` by default; accept `READY_WITH_CONDITIONS` only
with machine-readable, per-condition `satisfied: true` + `evidence` proof;
everything else fails closed. Add **negative tests** for: `BLOCKED`, missing
`closure_status`, `READY_WITH_CONDITIONS` with no `conditions:` block,
`READY_WITH_CONDITIONS` with a `conditions:` entry that is `satisfied: false`
or missing `evidence`, and malformed frontmatter. `complexity: medium`,
`size: M`.

### Open questions / risks

- Final field names (`conditions`, `satisfied`, `evidence`) and whether to
  additionally require a top-level `releasability:` echo are an `impl-plan`
  detail; the **semantics** (READY default; conditional acceptance only on
  verified structured evidence; fail-closed otherwise) are fixed here.
- Amending the existing `114-S` closure doc to satisfy the new contract is
  **out of scope for this fix task** and is instead handled as a closure
  handoff-reference update (see plan §Handoff); the fix task only implements
  and tests the gate contract.

---

## Decision 3 — Defect 2 (cli.py telemetry mapping) needs no deliberation

`cli.py:735–739` maps outcome `success` by default and only special-cases
`forced` and `exit_code == 1` (`blocked`). `exit_code == 2` (invalid gate
evaluation — unknown shipment, invalid mode/phase) and **any** other
non-zero/non-`blocked`/non-`forced` result fall through to `success`,
corrupting outcome metrics. The correct mapping is mechanical: non-zero,
non-`blocked`, non-`forced` → `failed`. Planned directly as `109.022-T`
(`size: S`, `complexity: low`) with explicit tests for exit_code 0/1/2 and the
`forced` case. It is width-isolated (CLI surface) from the two gate-module
fixes. **Cross-fix interlock:** it must correctly classify the new
retry-required token from Decision 1 (non-zero, non-`blocked` → `failed`, not
`success`).

---

## Decision 4 — Audit-log completeness discrepancy disposition (Defect 4)

`.backlogit/logs/114-S.jsonl` jumps from `shipment_status_changed: active`
directly to `archived`, omitting the intermediate
`shipment_status_changed: shipped` event that comparable prior closures
(`093-S`, `096-S`) record. The **data is correct** — the archived record's
`archived_status: shipped` confirms the transition genuinely happened and was
independently verified during safe-close.

**Disposition: EXTERNAL / backlogit-owned; NOT an autoharness code defect;
NOT a `115-S` activation blocker.** The append-only JSONL audit log is written
by the **backlogit Go binary** during `backlogit move --status shipped` /
`backlogit archive`, not by any autoharness code. Per the
`2026-07-02-shipment-closure-cascade-guard` precedent, defects in the external
backlogit binary are out of scope for this repository; autoharness must not
mutate `C:\Source\GitHub\backlogit` and must not hand-author a synthetic log
entry (doing so would itself corrupt the append-only trail's integrity).

The evidence does **not** support classifying this as in-repo contract work:
no autoharness code path is responsible for emitting that event, and the final
persisted state is correct. It is therefore recorded as a **deferred external
follow-up** (a backlogit-repo tracking item), captured as a clearly-labeled
stash entry in this workspace for visibility only, with **no autoharness fix
fabricated**. If future evidence shows an autoharness caller *should* be
asserting on that intermediate event's presence, it can be re-triaged then —
but on current evidence it is neither an autoharness bug nor a blocker.

---

## Summary of Accepted Directions

| # | Defect | Decision | Task | size / complexity |
| - | ------ | -------- | ---- | ----------------- |
| 1 | post-claim retry never converges | Option C — retry-required outcome contract; gate stays read-only; caller (Ship) drives reclaim | 109.021-T | M / high |
| 2 | telemetry maps exit_code==2 → success | Mechanical — non-zero/non-blocked/non-forced → failed | 109.022-T | S / low |
| 3 | closure_complete ignores closure_status | Option B — require READY; conditional acceptance only on machine-readable per-condition evidence; else fail closed | 109.023-T | M / medium |
| 4 | 114-S audit log missing shipped event | EXTERNAL backlogit-owned; deferred tracking only; no autoharness fix; not a blocker | (stash) | n/a |

All three code fixes MUST complete before the `115-S` activation tasks wire
the gate into any hook or automated caller (enforced via explicit
intra-shipment `blocks` dependencies — see the plan).
