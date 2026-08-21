---
title: "Plan review - full-suite test-isolation repair"
date: 2026-08-21
plan: docs/plans/2026-08-21-full-suite-test-isolation-plan.md
hardening: docs/plans/2026-08-21-full-suite-test-isolation-hardening.md
stash_id: E8158860
deliberation: "024-DL"
verdict: PASS
---

# Plan Review - full-suite test-isolation repair

Date: 2026-08-21
Agent: Stage (plan-review gate)
Plan hardening: HARDENED (A1-A3 applied pre-review)
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Verdict

**PASS** - 2 P1 raised, both RESOLVED by amendments A4 and A5; 1 P2 raised and
accepted with existing mitigation. **0 unresolved P0/P1.** Review-fix cycles
used: 1 of 3.

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

**Assessment.** Accepted. The bound is a time-box heuristic, and the plan already
carries a HARD STOP with a hand-back path (A2) that fires on time-box exhaustion
rather than on round count. No amendment required; the stop rule is the real
control.

## Confirmed strengths (no action)

* Putting diagnosis before remediation, with a hard stop and hand-back, is the
  correct response to a root cause that Stage provably cannot determine within
  its role boundary. Most plans in this situation guess.
* Refuting the entry's own stated hypotheses (cwd, env) with concrete static
  evidence, and recording the refutation, materially shrinks the search space and
  prevents the executing agent from re-treading them.
* Recognising that a Windows-only defect cannot be regression-guarded by Linux CI,
  and therefore choosing a STRUCTURAL guard, is the key insight of this plan.
* The separation of "unconditionally correct hygiene" (Tasks 1-2) from
  "conditional on the finding" (Task 3) means the shipment retains value even if
  the bisect fails.
