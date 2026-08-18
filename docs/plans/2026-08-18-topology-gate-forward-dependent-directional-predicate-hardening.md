# Plan Hardening (P-006) — Topology gate directional predicate

Date: 2026-08-18
Agent: Stage
Plan: `docs/plans/2026-08-18-topology-gate-forward-dependent-directional-predicate-plan.md`
Trigger: plan declares `Requires plan hardening: yes`
Scope: `131-F` / `131.001-T` / `140-S`

## Why harden a 2-file, 1-function change

The diff is small; the **failure history is not**. This is the *third*
correction to the same predicate:

1. **v1** — disable the fallback only for the *direct violator* → too narrow;
   multi-hop reverse dependency slipped through via an unrelated
   numerically-adjacent shipment.
2. **v2** (`0568f044`, shipped in `139-S`) — disable for *any* shipment
   declaring the target → too broad; normal forward dependents now suppress
   the fallback, silently permitting claims that should block.
3. **v3** (this plan) — disable only for a *numerically lower* shipment
   declaring the target.

Both prior attempts were reviewed and shipped. The recurring defect is not
carelessness but a **reasoning failure mode**: each fix was validated against
the single case that motivated it, and not against the opposite-direction
case simultaneously. Hardening here targets that failure mode directly.

Aggravating factor: the v2 defect was actually **caught by Copilot review on
PR #357** — twice, on `topology.py:1346` — but only as *"Suppressed
comments"* embedded in review bodies, never materialised as
`reviewThreads`. The thread-based review workflow was followed faithfully and
still missed them. This is a **review-surface** hazard independent of the
code.

## Hardening controls

### H1 — Both directional cases must be asserted, in the same test class

The fix is incomplete unless **both** of these hold simultaneously and
permanently:

* lower-numbered declarer → fallback **disabled**
  (`test_multi_hop_reverse_dependency_disables_fallback_entirely_not_just_the_violator`, existing, line ~1677)
* higher-numbered declarer → fallback **active**
  (`test_higher_numbered_forward_dependent_does_not_suppress_targets_own_predecessor_check`, new)

Ship MUST verify the **existing** test still passes, not merely that the new
one does. A green new test with a broken old test is the v1→v2 regression
repeating in reverse. Neither test may be modified, weakened, or deleted to
make the other pass — if they appear to conflict, **halt and escalate**; that
would mean the predicate is still wrong.

### H2 — Equality boundary is explicit and must not drift

The guard uses `if int(other.group(1)) >= target_num: continue`. The `>=`
(not `>`) is load-bearing: it also skips the target's own record, preventing
a self-referential shipment (`N-S` listing `N-S` in its own dependencies,
however malformed) from disabling its own fallback. Ship MUST apply `>=`
exactly as recorded and MUST NOT "simplify" it to `>`.

### H3 — Non-conforming shipment IDs keep failing safe

`re.match(r"^(\d+)-S$", shipment.shipment_id)` returning `None` → `continue`.
A shipment whose ID does not match the numeric shape is skipped as a
*declarer* (it cannot establish direction), exactly as it is already skipped
as a *candidate* in the retained selection loop below. This preserves
existing behaviour for non-numeric IDs; no new token or error path is
introduced.

### H4 — Reuse the recorded diff verbatim; do not re-derive

The compound doc contains the exact, already-verified diff and the exact test
name. Ship MUST apply that recorded fix rather than re-deriving a predicate
from the prose. Re-derivation is precisely how v2 was produced from v1's
lesson. Any deviation from the recorded diff requires halting and escalating,
not improvising.

### H5 — Comment text is part of the deliverable

The stale v2 comment block (lines ~1330–1344) explicitly asserts the
*wrong* rule ("The mere existence of any explicit reverse edge … disables the
entire numeric-adjacency fallback"). Leaving it in place while changing the
code beneath it would leave a booby-trap that actively argues a future
maintainer back into the v2 bug. The comment MUST be replaced with the
corrected directional rationale, including *why* direction matters.

### H6 — Suppressed-comment review sweep is mandatory on this PR

Given H-preamble: on this PR, thread-based Copilot review coverage is
**insufficient on its own**. Ship MUST additionally inspect the raw review
bodies:

```powershell
gh pr view <N> --json reviews
```

and explicitly triage any *"Suppressed comments"* block, not only
`reviewThreads`. This control exists because the exact defect being fixed
here escaped through that gap on PR #357.

### H7 — Fail-closed direction is verified, not assumed

The plan asserts the change can only make the gate block *more*. Ship MUST
sanity-check that no existing test flips from a blocking token to a passing
one. If any previously-blocking assertion becomes passing, the change has
inverted its intended direction — halt and escalate.

### H8 — Sequencing integrity

`140-S` must ship **before** `138-S` is claimed, because abandoning `138-S`
requires `claim`, which executes the `pre_claim` topology gate. The `blocks`
edge (`138-S` depends on `140-S`) enforces this. Ship MUST NOT force past this
edge, and MUST NOT reorder these two shipments.

Note the self-consistency check: with `138-S` (lower) declaring `140-S`
(higher) as a dependency, evaluating target `140-S` hits the
lower-numbered-declarer branch under **both** the old and the new predicate →
`return None` → no implicit predecessor injected → `140-S` remains claimable.
**The hotfix shipment is therefore not blocked by the bug it fixes**, under
either code version. No chicken-and-egg hazard exists.

### H9 — Scope containment

This shipment touches exactly two files. Ship MUST NOT bundle: the `129-F` /
`138-S` cancellation, any storage-root work, any other gate, or any
opportunistic cleanup. The cancelled-migration disposition is Stage-owned
backlog/doc work already committed separately.

## Residual risks accepted

| Risk | Severity | Mitigation | Accepted |
|---|---|---|---|
| A *fourth* directional case exists that neither test covers | low | H1 pins both known directions; the predicate is now total over `<`, `>=` — there is no third numeric relation | yes |
| Numeric-adjacency heuristic is itself the wrong design | medium | out of scope; a heuristic replacement is a separate, larger design question and must not be smuggled into a hotfix | yes — explicitly deferred |
| Suppressed-comment gap recurs on a future PR | medium | H6 covers this PR only; a durable workflow fix is a separate follow-up | yes — flagged for later stash |

## Hardening verdict

**HARDENED — H1–H9.** No control here blocks execution; all are verification
and containment obligations on Ship. Plan may proceed to review.
