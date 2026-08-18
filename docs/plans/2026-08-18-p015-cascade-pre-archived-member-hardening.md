# Plan Hardening — P-015 cascade pre-archived manifest-member handling

Date: 2026-08-18
Agent: Stage (plan-harden gate, P-006)
Plan: `docs/plans/2026-08-18-p015-cascade-pre-archived-member-plan.md`
Scope: `132-F` / `132.001-T`-`132.003-T` / `141-S`
Status: **HARDENED (H1-H8)**

Hardening was required because the change edits a P-015 safety policy and its
implementing skill contract; a mis-worded clause could authorise the exact class
of unsafe close the policy exists to prevent.

---

## H1 (P1) — Inserting a numbered step breaks a live cross-reference

The plan's `132.001-T` says to add a new numbered step "before the existing
step 1". The Cascade Close Sub-Procedure's steps are cross-referenced **by
number from outside the sub-procedure**:

`templates/skills/shipment-reconcile/SKILL.md.tmpl:379` (inside Step 0(b) of
Safe-Close Mode):

> "...it is the baseline the Cascade Close Sub-Procedure's **step 4**
> parent-preservation check compares against..."

Inserting a new step 1 renumbers `4 -> 5` and silently falsifies that reference.
The reference points at the `parent_id` snapshot contract — the very invariant
that detects a cascade clearing parentage — so a stale pointer here is a real
safety-documentation defect, not cosmetic.

**Hardening**: the pre-archived-member branch MUST be added as an **unnumbered
preamble block** (a short bolded sub-heading plus body) placed between the
sub-procedure's intro paragraph and its existing step 1. Existing steps 1-6 keep
their numbers, and every existing cross-reference (`step 4` at line 379,
`Step 0(b)` at lines 543/552/555, and the contract summary at lines 736-740)
stays valid.

If a future author instead prefers a numbered step, renumbering is only
permitted together with a same-commit update of line 379 and every other numeric
cross-reference — but the preamble form is the required approach here.

---

## H2 (P1) — The tolerance clause must not be placed in Step 0's classification block

Placing "pre-archived members are tolerated" inside Step 0(c) would read as a
**classifier precondition**, implying the classifier must itself test archival
state. It must not: the classifier's verdict is already correct and archival-
state-agnostic by design.

**Hardening**: the clause lives **only** in the Cascade Close Sub-Procedure
(execution-time guidance), never in Step 0(c)'s precondition list. Step 0(c)'s
precondition wording is unchanged.

---

## H3 (P1) — Must not leak a pre-archived exemption into the protected set

Safe-close deliberately grants `pre-archived` tolerance to **manifest items only**
and explicitly denies it to the **protected set** (SKILL lines 446-447, 471-473;
P-015 line 424). Introducing cascade-side pre-archived language risks a future
reader generalising the exemption.

**Hardening**: the new text MUST state that it applies to **manifest members
only**, and MUST NOT restate, weaken, or cross-apply the protected-set rule. It
should note that a qualifying cascade manifest has no unshipped siblings *by
construction* (full-coverage is a precondition), so no protected set arises on
this path — rather than implying the protected-set exemption changed.

---

## H4 (P1) — The no-substitution rule must be directional and must not contradict step 2

The sub-procedure's existing step 2 already forbids falling back to safe-close
**after** a cascade has executed ("do NOT retry, do NOT fall back to safe-close
after a cascade has already executed"). The new rule addresses the **pre-execution**
window: a clean `CASCADE` verdict must not be discarded *before* invoking the
cascade op.

**Hardening**: the new clause MUST be scoped to the window between Step 0's
verdict and step 1's invocation, and MUST be phrased so it complements rather
than restates or contradicts step 2. The asymmetry must be explicit: this clause
forbids `CASCADE -> manual safe-close` substitution; it grants **no** licence in
the other direction (a `SAFE_CLOSE` verdict never permits cascade — that remains
governed by the P-015 default prohibition).

---

## H5 (P2) — Do not authorise a manual archive loop on the cascade path

A reader could take "pre-archived members are tolerated" as licence to
pre-archive remaining members manually before invoking the cascade op, blending
the two paths. The sub-procedure already forbids partial mixing.

**Hardening**: state that the cascade operation performs all remaining archival
itself; Ship performs **no** manual per-item archive loop on this path. Cite the
existing "no partial mixing of the two paths" rule rather than duplicating it.

---

## H6 (P2) — Evidence provenance must be recorded in-contract

The tolerance claim rests on observed `backlogit v1.9.0` behaviour, not on a
published API guarantee. A future engine change could invalidate it silently.

**Hardening**: the new text MUST cite the spike
(`docs/spikes/2026-08-18-cascade-close-pre-archived-member-behavior.md`) as the
provenance of the idempotency claim, and MUST make clear that step 3's
exact-match check is the live guard that would catch any future engine
regression — i.e. the contract stays fail-closed even if the engine changes.
This is why step 3 must not be relaxed.

---

## H7 (P2) — Policy edit must not renumber P-015's preconditions

`132.002-T` adds to the exception block whose items 1-6 are referenced as an
all-or-nothing set, and item 5 explicitly governs items "above".

**Hardening**: add the clarification as a **new item 7** (or as a trailing
clarifying paragraph after item 6), never inserted among items 1-5. Items 1-6
keep their numbers and meaning, and item 5's "any of the preconditions above"
semantics must remain accurate.

---

## H8 (P2) — Regression tests must be hermetic and must prove the negative cases

Tests that only assert "pre-archived still yields CASCADE" would pass trivially
against a classifier that ignored archival state entirely, and would not detect a
future over-grant.

**Hardening**: `132.003-T` MUST include the negative cases already named in the
plan (out-of-manifest child discovered in `archive/`; pre-archived non-root
feature member) so the tests constrain the grant from **both** sides. Fixtures
MUST be constructed under `tmp_path`; no test may read or write the live
`.backlogit/` tree.

---

## Hardening verdict

**HARDENED.** H1-H4 (P1) are binding acceptance constraints on `132.001-T` and
`132.002-T`; H5-H8 (P2) are binding acceptance constraints on their respective
tasks. All are mechanically checkable at review time.
