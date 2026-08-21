---
title: "Plan review - full-suite test-isolation repair"
date: 2026-08-21
plan: docs/plans/2026-08-21-full-suite-test-isolation-plan.md
hardening: docs/plans/2026-08-21-full-suite-test-isolation-hardening.md
stash_id: E8158860
deliberation: "024-DL"
verdict: PASS
review_fix_cycle: 2
regated: 2026-08-21
---

# Plan Review - full-suite test-isolation repair

Date: 2026-08-21
Agent: Stage (plan-review gate)
Plan hardening: HARDENED (A1-A3 applied pre-review)
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Verdict

**PASS (re-gated after review-fix cycle 2).**

*Original pass:* 2 P1 raised, both RESOLVED by amendments A4 and A5; 1 P2 raised
and accepted with existing mitigation.

*Review-fix cycle 2* (Copilot review on PR #386 at HEAD `c992b2bf`; 5 of the 8
current-head threads landed on this plan/hardening/review triple): a **P0** was
raised - the A2 resolution this review had accepted is UN-EXECUTABLE and deadlocks
the shipment. A2 is **WITHDRAWN** and replaced by **A2R** (shipment boundary +
always-terminating outcomes). A second finding, **P1-5**, records that A4's
correction was never applied to the plan's operative Harvest note. Both RESOLVED.

**0 unresolved P0/P1.** Review-fix cycles used: **2 of 3.**

*Method note:* the P0 was established by reading the INSTALLED Ship contract
(`.github/agents/_ship.agent.md:325-340`) and the backlogit shipment-status
compound record, not by inference from the plan text. The original review accepted
A2's "hand-back path" without checking whether Ship can execute a hand-back - that
omission is the root cause of this cycle.

## P1-1 (RESOLVED by amendment A4) - the structural guard is red across intermediate commits

**Finding.** Task 2's test-first requirement adds an AST guard that is RED with
58 hits, and the plan's own Harvest note says it "is expected to stay RED until
the last subtask completes." But Task 2 is decomposed into per-module subtasks,
and this repository gates EVERY task on a local build/test pass (P-018). A
deliberately-red checked-in test blocks the gate for every intermediate subtask,
which will either stall the shipment or - far more likely - pressure the executing
agent into bypassing the gate. A plan that predictably forces a gate bypass is a
plan defect, not an execution problem.

**Why it is P1.** It makes the plan un-executable as written under the
repository's own merge gate.

**Resolution (A4).** The guard is written from the outset with an EXPLICIT,
SHRINKING ALLOWLIST of known offending files. Each per-module subtask removes its
own module from the allowlist in the same change that fixes that module's call
sites, so the guard is GREEN after every subtask. The final subtask empties the
allowlist and asserts it is empty, so the allowlist cannot survive as a permanent
escape hatch.

**Follow-up (cycle 2, P1-5; thread `PRRT_kwDORzpWpM6bSzOQ`).** A4 was recorded in
the plan's amendment list, but the plan's operative **Harvest note still said the
guard "is expected to stay RED until the last subtask completes"**. The plan
therefore carried two contradicting operative instructions, and the stale one sat
in the more prominent position. The Harvest note has now been REWRITTEN in place to
state the shrinking-allowlist behaviour directly, and A4's cross-reference updated
accordingly. Lesson: an amendment that contradicts operative text must REWRITE that
text, not merely supersede it from an appendix.

## P1-2 (RESOLVED by amendment A5) - the bisect protocol has no runnable mechanism

**Finding.** Task 1 step 2 says "rerun with the three `test_scope_containment_*`
modules excluded" and step 3 says "run only {candidate subset} + {the five
victims}." The canonical gate is `python -m unittest discover -s tests`, which
supports only a filename PATTERN (`-p`) - it has no deselect/exclude facility. As
written the protocol cannot be executed on the canonical runner, and the obvious
workaround (switch to pytest with `--deselect`) silently changes the gate the
bisect is measuring, which is exactly the confound the protocol exists to avoid.

**Why it is P1.** The protocol is the load-bearing part of this plan; a protocol
that cannot be run produces improvisation, and improvisation here produces a
speculative fix.

**Resolution (A5).** The protocol now specifies explicit dotted-name invocation
against the canonical runner, which supports arbitrary subsets:
`$env:PYTHONPATH='src'; python -m unittest tests.test_a tests.test_b
tests.test_repo_root_artifacts.RepoRootTrackedJsonAllowlistTest.test_root_tracked_json_matches_allowlist ...`
Subset selection is by explicit enumeration, never by exclusion. pytest may be
used only as a cross-reference and never as the measurement gate
(`docs/compound/097-S-canonical-unittest-gate.md`).

## P2-1 (ACCEPTED, existing mitigation sufficient) - the 8-round bound may be optimistic

**Finding.** Binary search from three modules down to a single test METHOD across
modules that contain hundreds of tests can exceed eight rounds.

**Assessment (ORIGINAL - superseded in cycle 2).** Accepted. The bound is a time-box
heuristic, and the plan already carries a HARD STOP with a hand-back path (A2) that
fires on time-box exhaustion rather than on round count. No amendment required; the
stop rule is the real control.

**Assessment (CYCLE 2 - operative).** Still ACCEPTED, but the control is no longer
A2's hand-back, because A2 is withdrawn (see P0-1). The real control is A2R: time-box
exhaustion records `VERDICT: INCONCLUSIVE` and closes Task 1 `done`, and the
conditional remediation is not in that shipment at all, so an over-running bisect
cannot bleed into a speculative fix. The 8-round bound remains a heuristic; the
terminal verdict and Task 3b AC13's citation requirement are the enforceable parts.

## Confirmed strengths (no action)

* Putting diagnosis before remediation is the correct response to a root cause
  that Stage provably cannot determine within its role boundary. Most plans in
  this situation guess. (The "hand-back" half of this praise was WITHDRAWN in
  cycle 2: the diagnosis-first ORDERING is sound, but the hand-back MECHANISM was
  not executable. The ordering survives; the mechanism was replaced by A2R.)
* Refuting the entry's own stated hypotheses (cwd, env) with concrete static
  evidence, and recording the refutation, materially shrinks the search space and
  prevents the executing agent from re-treading them.
* Recognising that a Windows-only defect cannot be regression-guarded by Linux CI,
  and therefore choosing a STRUCTURAL guard, is the key insight of this plan.
* The separation of "unconditionally correct hygiene" (Tasks 1-2) from
  "conditional on the finding" (Task 3) means the work retains value even if the
  bisect fails. Cycle 2 STRENGTHENED this: the separation is now a SHIPMENT
  boundary (149-S vs 151-S) rather than an intra-shipment task boundary, which is
  what makes it deliverable - a conditional task inside a shipment Ship must
  complete has no safe non-execution path.

## P0-1 (RAISED in review-fix cycle 2; RESOLVED by amendment A2R) - the accepted hard-stop resolution deadlocks the shipment

**Threads.** `PRRT_kwDORzpWpM6bSzLz` (141.001-T), `PRRT_kwDORzpWpM6bSzMM` (141-F),
`PRRT_kwDORzpWpM6bSzMz` (plan A2), `PRRT_kwDORzpWpM6bSzNF` (hardening H2),
`PRRT_kwDORzpWpM6bSzPW` (141.005-T).

**Finding.** Amendment A2 - which this review ACCEPTED at cycle 1 - required that on
time-box exhaustion Task 1 return `blocked`, Task 3 be "returned blocked via the
official return-blocked operation", and "the shipment closes with Tasks 1-2 only".
Checked against the installed contract, none of that is executable:

1. `.github/agents/_ship.agent.md:325-340` derives the executable task set by
   filtering the manifest to `-T` artifacts and THEN reading status. The rule is
   exhaustive and positive: KEEP `queued`/`active`; SKIP-AND-REPORT pre-archived;
   REPORT `already_done`; **ANY OTHER status is a FAIL-CLOSED HALT, never a skip.**
   A `blocked` member HALTS the shipment.
2. The same passage states the manifest "is never mutated to make execution
   proceed", so the blocked member cannot be removed to unblock the run.
3. There is consequently NO partial-close path. The documented resolution produces a
   deadlock - strictly worse than the failure it was written to prevent.
4. Backlogit 1.8.0 defines no shipment `blocked` status; only `queued -> active`,
   `active -> shipped`, `active -> abandoned`
   (`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`). There is no
   shipment-level fallback either.
5. The installed Ship contract never instructs Ship to use
   `backlogit_return_blocked`. `.github/agents/_ship.agent.md` contains ZERO prose
   references to it, verified across the `return_blocked` / `return-blocked` /
   `return blocked` variants and re-verified in cycle 2 under the degraded-search
   fallback protocol. **Precision note (cycle 2):** Ship does hold tool ACCESS via
   the `'backlogit/*'` wildcard in its frontmatter, so this finding is NOT "the tool
   is unavailable to Ship" - it is that the contract assigns the operation no
   semantics on any step, gate, or failure path, while the Step 2 derivation halts
   fail-closed on a `blocked` member regardless of origin. The operation IS
   enumerated in Stage's own tool allowlist (`.github/agents/_stage.agent.md`),
   reinforcing that it was never a Ship-side lifecycle lever. A2 therefore depended
   on Ship behaviour its contract does not define.

**Why it is P0.** It makes the shipment un-closable on a path the plan itself
declares likely enough to harden for, and it does so silently - nothing in the
backlog would reveal the deadlock until Ship halted mid-run.

**Resolution (A2R).** Separate conditional from unconditional work by a SHIPMENT
BOUNDARY rather than by a task status:

* 149-S (feature 141-F) keeps only unconditionally executable work: 141.001-T
  diagnosis plus 141.002-T/141.003-T/141.004-T decoupling.
* New successor shipment **151-S**, new covering feature **143-F**, carries the
  conditional work. Gated `151-S -> 149-S` and sequenced BEFORE 150-S so H7's
  "test-isolation lands before variable-derivation" constraint still holds; because
  every 151-S task terminates `done`, 151-S always reaches `shipped` and can never
  strand 150-S on an unsatisfied edge.
* 141.001-T now has TWO terminal outcomes, both `done`: `VERDICT: PAIR-ISOLATED` or
  `VERDICT: INCONCLUSIVE`.
* 141.005-T is SPLIT into 143.001-T (unconditional git self-diagnosis) and 143.002-T
  (three dispositions R1/R2/R3, all closing `done`), then archived as SUPERSEDED with
  an explicit AC-to-AC mapping table. It REMAINS a 149-S manifest member as a
  tolerated `pre_archived_skipped` entry, so no manifest was mutated.
* A NEW covering feature was required rather than leaving 141.005-T under 141-F:
  safe-close archives the manifest's item IDs, so an open child under an archived
  141-F would be orphaned, and an open 141-F carried into 150-S would trip Ship's
  P-001 "no other top-level release unit active" gate.
* H2's anti-speculation intent is preserved STRUCTURALLY and more strongly: there is
  no remediation work inside 149-S to slip into, and Task 3b AC13 forbids any source
  edit that does not cite a recorded minimal reproducing pair.

**Verification.** Chain re-read as `148-S -> 149-S -> 151-S -> 150-S`, acyclic, with
**148-S alone claimable**. No task ID, acceptance criterion, or scope was dropped.

## Reviewer lesson (candidate for `docs/compound/`)

A plan-review that accepts a FAILURE-PATH resolution must verify that the EXECUTING
agent can actually perform it, against the installed executor contract - not merely
that the resolution reads as well-reasoned. Cycle 1 accepted "returned blocked via
the official return-blocked operation" because it sounded procedural and cited an
"official operation"; that operation is absent from the Ship contract, and the status
it sets is a fail-closed halt. **The phrase "via the official X operation" is a
verification obligation, not evidence.**
