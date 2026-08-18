# Plan Review — Topology gate directional predicate (multi-persona adversarial)

Date: 2026-08-18
Agent: Stage (plan-review gate)
Plan: `docs/plans/2026-08-18-topology-gate-forward-dependent-directional-predicate-plan.md`
Hardening: `docs/plans/2026-08-18-topology-gate-forward-dependent-directional-predicate-hardening.md` (HARDENED, H1–H9)
Scope: `131-F` / `131.001-T` / `140-S`
Review rounds: 1 (six personas)

## Summary

A single-function directional-predicate correction in the topology gate, plus
one regression test, applying a diff that was already authored and verified
during `139-S` post-merge closure but deliberately left uncommitted for scope
reasons.

**Verdict: PASS — 0 unresolved P0, 0 unresolved P1.**
Six findings raised (2×P1, 3×P2, 1×P3). Both P1s resolved in the plan and
hardening artifacts before this verdict. P2s: two resolved, one accepted with
explicit deferral. P3 accepted.

---

## Persona 1 — Gate-correctness adversary

*"Show me the case where the new predicate is still wrong."*

The predicate partitions all declaring shipments by numeric relation to the
target. Over `{lower, equal-or-higher}` this partition is **total** — there is
no third relation — so no unhandled numeric case exists. Non-numeric IDs are
handled by H3 (`continue`, preserving prior behaviour).

Attempted counter-example: *a lower-numbered shipment that declares the target
but is itself abandoned/shipped.* The guard does not consult declarer status.
Is that wrong? **No** — and this is pre-existing, unchanged behaviour: the
guard's purpose is to detect that *the target's ordering is explicitly
declared somewhere*, which remains true regardless of the declarer's status.
An explicit declaration by a shipped predecessor still means the ordering was
never implicit. Not a regression; not introduced here.

### F1 (P1) — Was the existing multi-hop test actually re-verified, or assumed?

The original defect (v2) was itself produced by a fix that satisfied its own
new test. A plan that only asserts "the new test passes" would repeat that
exact failure.

**Resolved.** The plan now carries an explicit regression-safety table
tracing the existing test (target `139-S`, declarer `138-S`, `138 < 139`)
through the *new* predicate to the same `return None` branch, and H1 makes
re-verifying the **existing** test a mandatory Ship obligation with a
halt-and-escalate clause if the two tests appear to conflict.

---

## Persona 2 — Regression archaeologist

*"This predicate has been wrong twice. Why is the third attempt different?"*

v1 and v2 were each validated against the single motivating case. v3 is the
first version validated against **both** directional cases simultaneously,
and the first to pin both in tests that must pass together (H1).

### F2 (P1) — The stale comment block encodes the wrong rule

Lines ~1330–1344 assert in prose exactly the over-broad v2 rule. Changing the
code while leaving that comment would leave an authoritative-looking argument
in-tree for reverting to the bug — a genuine v4 hazard, given this predicate's
history.

**Resolved.** H5 makes replacing the comment (with rationale for *why*
direction matters, not merely *that* it does) part of the deliverable, and the
plan's Step 1 states it explicitly.

---

## Persona 3 — Sequencing / deadlock analyst

*"Can the hotfix be blocked by the bug it fixes?"*

Checked directly. With `138-S` (lower) declaring `140-S` (higher), evaluating
target `140-S` enters the lower-numbered-declarer branch under **both** the
old and new predicate → `return None` → no implicit predecessor injected →
`140-S` claimable. Additionally `139-S`, the numerically adjacent prior
shipment, is already `shipped`, so even an active fallback would not block.

**No chicken-and-egg hazard.** Recorded as H8. Double-independent-reason
safety: the gate does not block `140-S` under either code version, for two
unrelated reasons.

### F3 (P2) — Ordering is asserted but was not mechanically enforced

An intended ordering held only in prose is not an ordering.

**Resolved.** An explicit `blocks` edge (`138-S` depends on `140-S`) is created
in the backlog, and H8 forbids forcing past it. Eligibility is then computed
by backlogit as `status == queued` AND all `blocks` predecessors `shipped`.

---

## Persona 4 — Blast-radius / safety reviewer

*"What does this break if it is wrong?"*

The change can only **add** suppression-of-suppression, i.e. re-enable a
blocking check. Its failure mode is a spurious `PREDECESSOR_NOT_SHIPPED` —
loud, immediate, non-destructive, trivially diagnosable. It cannot cause data
loss, cannot mutate backlog state, and cannot silently mis-permit (that is the
*current* behaviour being removed).

Contrast with the failure mode being fixed: a **silent fail-open** in a gate
whose entire purpose is to prevent out-of-order claims. Fixing it strictly
improves the safety posture.

### F4 (P2) — "Fail-closed direction" was asserted, not verified

**Resolved.** H7 requires Ship to confirm no existing test flips from a
blocking token to a passing one, with halt-and-escalate if it does.

---

## Persona 5 — Review-process adversary

*"The last fix passed review and was still wrong. Why trust review now?"*

The sharpest finding in this cycle. The v2 defect **was** detected by Copilot
on PR #357 — twice, on the exact line — but surfaced only inside "Suppressed
comments" blocks in review bodies, never as `reviewThreads`. The session
followed the thread-based workflow correctly and still missed it. Process
compliance was not the problem; the **review surface** was.

### F5 (P2) — Thread-based review is insufficient for this PR

**Resolved for this shipment.** H6 mandates a raw-body sweep
(`gh pr view <N> --json reviews`) with explicit triage of any "Suppressed
comments" block, in addition to normal thread handling.

### F6 (P3) — The suppressed-comment gap is repo-wide, not PR-specific

H6 covers only this PR. Every future PR retains the same blind spot.

**Accepted with deferral.** A durable fix (making suppressed-comment triage a
standing obligation in the review workflow instruction surface) is a separate
change to the review workflow and must not be smuggled into a two-file
reliability hotfix (H9 scope containment). Flagged for a follow-up stash entry
rather than silently dropped.

---

## Persona 6 — Scope-discipline reviewer

*"Is this shipment doing exactly one thing?"*

Two files, one function, one new test. The plan's non-goals explicitly exclude
redesigning the heuristic, touching other gates, and touching the cancelled
`129-F`/`138-S` migration scope. H9 enforces containment.

One genuine temptation identified and correctly refused: the numeric-adjacency
heuristic is arguably the *wrong design* — inferring ordering from ID numbering
is inherently fragile, which is why this predicate has needed three
corrections. Replacing it with declared-dependencies-only would be a real
improvement.

**Correctly deferred.** That is a design change requiring its own
deliberation, migration of existing implicit orderings, and a much larger blast
radius. Bundling it into a hotfix for a live fail-open defect would delay the
fix and multiply risk. Recorded in the hardening doc's residual-risk table as
explicitly accepted and deferred.

---

## Findings ledger

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| F1 | P1 | Existing multi-hop test re-verification assumed, not proven | **Resolved** — regression table in plan + H1 |
| F2 | P1 | Stale comment encodes the superseded over-broad rule | **Resolved** — H5 makes comment replacement a deliverable |
| F3 | P2 | Ordering asserted in prose only | **Resolved** — explicit `blocks` edge + H8 |
| F4 | P2 | Fail-closed direction unverified | **Resolved** — H7 |
| F5 | P2 | Thread-based review insufficient (suppressed comments) | **Resolved for this PR** — H6 |
| F6 | P3 | Suppressed-comment gap is repo-wide | **Accepted, deferred** — separate follow-up, H9 forbids bundling |

## Verdict

**PASS — 0 unresolved P0, 0 unresolved P1.**

The plan reuses a fix that is already verified (94/94 topology tests, 1550
full-suite passes with the fix applied locally), is directionally
fail-closed, is scope-contained to two files, has both directional cases
pinned by tests that must pass together, and is mechanically sequenced ahead of
`138-S` by a `blocks` edge.

Approved for harvest and shipment assembly. `140-S` is the next eligible
shipment.

## Closure condition

`topology-forward-dependent-suppression-fix` — **UNSATISFIED at review time
and MUST remain so.** It is satisfied only when Ship merges the fix to `main`
and the merge confirmation gate passes. Neither this review's PASS verdict,
nor shipment assembly, nor the `blocks` edge satisfies it. The defect remains
live on `main` until then.
