---
title: "Plan review attempt 08 - SHIP-HARNESS-LIFECYCLE-FOUNDATION (187-S)"
description: "Immutable per-attempt plan-review artifact recording the EIGHTH independent review of docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md, the FIRST independent review of revision 9, dispatched under the fresh operator authorization that also permitted the revision-9 remediation cycle. GATE RESULT FAIL/BLOCK at P0 1 / P1 11 / P2 7 / P3 2. Revision 9 is a genuine structural advance - it splits actor conformance out as a prerequisite unit, specifies the resolver as an executable boundary, makes recomputation the freshness carrier, approval-gates rollback and rewrites the problem frame as current state - and it is STILL NOT SHIPPABLE. The new blocking defect is that the prerequisite unit 191-S cannot execute under the ordinary P-002/P-004 gates it is itself meant to unblock, which reintroduces the self-bootstrap deadlock at one remove. S14 is CLOSED at this attempt, but NOT by 191-S and NOT by any Stage artifact: it was closed by external Ship review-remediation commits 1cb0dc81 and b8ac632a. No other finding is closed."
doc_type: review
source: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-08.md
date: 2026-09-20
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 8
attempt_range: "08"
attempt_conformance: conforming
review_terminal: false
terminal_designation: not-terminal-remediation-authorized
terminal_disposition: FAIL-BLOCKING-P0-AND-P1
terminal_note: "Attempt 08 CONSUMES attempt number 8 and is NOT terminal. The operator directive that dispatched it explicitly authorizes continued remediation after recording. This is a FAIL, not a convergence terminal and not a terminal PASS."
verdict_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
supersedes: null
predecessor_artifact: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-07.md
plan_path: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
plan_id: ship-harness-lifecycle-foundation
reviewed_revision: 9
reviewed_content_head: b11d6555
reviewed_content_state: committed
reviewed_branch: chore/stage-176-s-workflow-defects
plan_mutated_by_this_attempt: false
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 6
feature_id: 181-F
shipment_id: 187-S
prerequisite_shipment_id: 191-S
declared_surface_count: 2
review_cycle: 8
dispatch_mode: multi-agent
degraded_capabilities: []
security_lens_triggered: false
security_lens_note: "No Security Lens trigger fired for this revision. S30 (trust-root conflation and path TOCTOU / no-follow identity) is recorded on the ARCHITECTURE and PYTHON axes as a robustness-contract gap in a planning document, not as a live exploitable vulnerability: no resolver code exists yet to attack."
gate_result: FAIL
decision: BLOCK
verdict_is_pass: false
verdict_at_entry: null
verdict_at_entry_disposition: PENDING-INDEPENDENT-REVIEW
verdict_at_entry_plan_revision: 9
verdict_at_entry_manifest_revision: 15
verdict_at_entry_publication_eligible: false
remediation_authorization: authorized-by-fresh-operator-directive-after-recording
remediation_performed: false
remediation_cycle_proposed: true
disposition: FAIL-BLOCKING-P0-AND-P1
p0_open: 1
p1_open: 11
p2_open: 7
p3_open: 2
open_findings: [S13, S15, S16, S17, S18, S19, S20, S21, S22, S23, S24, S25, S26, S27, S28, S29, S30, S31, S32, S33, S34]
blocking_findings: [S15, S16, S17, S18, S19, S20, S26, S27, S28, S29, S30, S31]
closed_predecessor_findings: [S14]
closed_findings_evidence:
  - finding: S14
    closed_by: external-ship-review-remediation
    closing_commits:
      - 1cb0dc8140a809d63c3193d58431cd14408788b7
      - b8ac632a93751fb29c51a8e5bf0f5e036b65cfb3
    closed_by_this_plan: false
    closed_by_191_s: false
    note: "S14 is CLOSED. It was NOT closed by plan revision 9, NOT by feature 185-F and NOT by shipment 191-S, none of which has executed. It was closed by external Ship review-remediation commits landed directly on this branch: 1cb0dc81 corrected Step 5.2 of .github/skills/harness-architect/SKILL.md from pytest to the canonical PYTHONPATH=src python -m unittest discover -s tests, mirrored the correction into templates/skills/harness-architect/SKILL.md.tmpl while KEEPING the {{TEST_COMMAND}} and {{UNIMPLEMENTED_MARKER}} placeholders so the template stays ecosystem-agnostic, strengthened the red-phase guardrail prose to require per-test marker correlation and to reject zero-discovery, wrong-reason, collection/import/syntax failures, skips, xfails and passes as red-phase evidence, added tests/test_harness_architect_p004_contract.py, and refreshed the manifest checksum; b8ac632a then added variables_used.UNIMPLEMENTED_MARKER, which had been absent from the derivation output entirely. Canonical suite reported 2358 passed / 0 failed / 54 skipped with manifest parity holding."
carried_predecessor_findings: [S13, S15, S16, S17, S18, S19, S20, S21, S22, S23, S24, S25]
findings_raised_at_this_attempt: [S26, S27, S28, S29, S30, S31, S32, S33, S34]
revision_9_addressed_pending_review_not_closed: [S15, S16, S17, S18, S19, S20, S21, S22, S23, S24, S25]
hardening_required: true
hardening_present: true
hardening_sufficient: false
hardening_note: "Revision 9 hardening is materially stronger than revision 8 - it adds fail-closed containment, an exhaustive adjudication table and an approval-gated rollback - but it remains INSUFFICIENT because it hardens a contract whose executability is not established: the CLI it activates is unbuilt and unowned (S27), the prerequisite unit that must run first cannot pass its own gates (S26), and the trust boundary it contains against is not identified (S30)."
personas_applied:
  - constitution
  - python
  - scope-boundary
  - learnings
  - architecture
  - agent-native-parity
personas_not_applied:
  - security-lens
tags:
  - "plan-review"
  - "attempt"
  - "fail"
  - "revision-9"
  - "self-bootstrap-deadlock"
  - "portfolio-2026-09-18"
---

# Plan review attempt 08 - SHIP-HARNESS-LIFECYCLE-FOUNDATION (187-S)

## Reviewed subject

`docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` at **revision
9**, at committed base `b11d6555` on branch `chore/stage-176-s-workflow-defects`.
Revision 9 is a full rewrite, not an append, authored by Stage under the fresh
operator authorization that permitted exactly one remediation cycle and this
attempt to judge it.

The plan was **not mutated by this attempt**. Revision 9 stands unchanged.

## What revision 9 got right

This is recorded because a review that lists only defects misrepresents the
distance travelled, and because the next remediation must not undo the parts
that are sound.

* The actor-conformance correction is correctly **split out** of the lifecycle
  unit rather than smuggled into it (`185-F` / `191-S`).
* Commit `07b4be79` is correctly recorded as **structural installation only**,
  never behavioural satisfaction. That distinction was the heart of `S14` and
  revision 9 states it plainly.
* The resolver is specified as an **executable boundary** with a named module,
  typed output and exit codes, rather than as agent prose.
* **Recomputation as the freshness carrier**, with no persisted readiness
  state and an explicit "a token never authorizes" rule, is the right
  architecture and resolves the state-staleness class of defect at its root.
* Rollback is **approval-gated** under this workspace's own `P-007` `G1`-`G9`
  precedent.
* The duplicated review prose in live carriers is replaced with **pointer-only**
  authority to the manifest.

None of this is sufficient to pass, for the reasons below.

## Findings

Findings are merged and de-duplicated conservatively: where two personas
reported the same underlying defect through different symptoms, one finding is
recorded and both symptoms are named inside it. Where a symptom could plausibly
be a distinct defect, it is recorded separately rather than absorbed.

### S14 - CLOSED at this attempt, by external evidence only

`S14` was the `P0` of attempt 07: revision 8 treated the installed
harness-architect actor as satisfying the `P-004` behavioural prerequisite when
the installed `SKILL.md` prescribed `pytest`.

**It is now closed.** The installed `.github/skills/harness-architect/SKILL.md`
reads `PYTHONPATH=src python -m unittest discover -s tests`, the manifest
carries both `variables_used.TEST_COMMAND` and `variables_used.UNIMPLEMENTED_MARKER`,
manifest parity holds, and the canonical suite reports **2358 passed / 0 failed
/ 54 skipped**.

**The closure is attributed precisely, because attribution is the whole point.**
`S14` was closed by **external Ship review-remediation commits `1cb0dc81` and
`b8ac632a`**, landed directly on this branch. It was **not** closed by plan
revision 9, **not** by feature `185-F`, and **not** by shipment `191-S` - none
of which has executed. Nothing in this record may be read as implying `191-S`
shipped. It did not; it remains queued.

This closure is also the origin of several findings below, because it changes
the facts that `185-F` was built on.

### S26 - `191-S` cannot execute under the gates it exists to unblock (P0, BLOCKING)

Revision 9 makes `191-S` a hard prerequisite of `187-S` and a declared
`dag-root`. `191-S`'s tasks write Python under `src/` and under `tests/`.
Therefore, at claim time, `191-S` is subject to ordinary `P-002` and `P-004`,
which require a harness-ready state whose declared producer is the
harness-architect actor operating through the lifecycle that `187-S` builds.

`187-S` is downstream of `191-S`. So `191-S` must satisfy a gate whose
machinery does not exist until after `191-S` completes.

**This is the self-bootstrap deadlock of `188-S`, reintroduced one level up.**
Revision 9 dissolved the old deadlock by observing that the actor already
existed; it created a new one by making a code-bearing unit the root of the
chain that builds the lifecycle. The plan does not address this anywhere: it
asserts `191-S` is "a genuine root" on the grounds that its *inputs* exist,
which is a statement about data availability and not about gate satisfiability.

The plan's own `185-F` record explicitly acknowledges the adjacent problem -
that harness-surface declaration labels would be circular on these tasks - and
then does not draw the obvious conclusion that the *gate* is circular for the
same reason.

Compounding this: `S14`'s closure by external commits means the substantive
work `191-S` was created to perform **has largely already been done outside the
backlog**. `185.002-T` in particular is premised on an install-time *precedence*
defect, and the manifest note added by `1cb0dc81` records that
`_derive_template_variables` **already** treats manifest `variables_used` as
authoritative (profile-derived defaults use `.setdefault`, a no-op once the
manifest key exists), so the defect was a **stale-render** defect, not a
precedence defect. `191-S` therefore carries at least one task whose stated
root cause is now known to be wrong, while blocking the entire lifecycle chain.

### S27 - the plan activates a CLI that nothing owns (P1, BLOCKING)

Revision 9 specifies `autoharness harness resolve --workspace . --shipment <id>
--json` with exit codes `0` / `1` / `2`, and makes Ship and checkpoint resume
invoke it. The plan then **explicitly defers** wiring it, in its own Tasks
section, on the grounds that adding `src/autoharness/cli.py` would make
`181.002-T` a four-file task, and carries it as "the first task of the follow-on
unit".

There is no follow-on unit. No feature, task or shipment owns the CLI
subcommand, its argument parsing, its exit-code contract or its tests. A
contract that is specified, activated by two consumers, and owned by nobody is
not deferred - it is **unbuilt and unassigned**. The three-file bound is a
legitimate granularity rule, and the correct response is to split the task, not
to drop the surface out of the backlog.

### S28 - checkpoint-resume recomputation is not wired to the recovery surface (P1, BLOCKING)

The plan states that checkpoint resume re-invokes the resolver freshly rather
than trusting a persisted token. This is the right rule. But the actual
crash-recovery surface in this workspace is the checkpoint protocol - 
`backlogit_get_checkpoint`, the `CheckpointV1` payload and the restore path -
and revision 9 names no integration point in it, no field that carries the
recomputed digest, and no task that modifies the recovery path.

The rule is therefore stated where nothing enforces it. On resume, the existing
recovery path will restore recorded phase and context exactly as before and will
not recompute anything, because nothing tells it to.

### S29 - surface-ID mapping and canonical lookup are ambiguous, and the zero-match rule contradicts the table (P1, BLOCKING)

Three related ambiguities, recorded as one finding because they share a root -
the plan never defines the *mapping function* from a declaration to a manifest
entry.

1. `harness-surface:<id>` is matched against "exactly one manifest entry", but
   the manifest is keyed by installed path, and `<id>` is a short symbolic name
   (`harness-architect`). The plan never states how `harness-architect` resolves
   to `.github/skills/harness-architect/SKILL.md`.
2. The canonical lookup order for shipment and task records is unstated. Items
   are declared "authoritative" from the shipment, but tasks may be read from
   the queue, the archive or the index, and these can disagree.
3. **The zero-match case is self-contradictory.** The adjudication table maps
   "a declared surface has **no** manifest entry" to `NO_HARNESS` (terminal),
   while the resolver narrative treats a declaration matching no entry as an
   unresolvable input. One of these is wrong. Given that "more than one match"
   is `UNRESOLVED`, a reader cannot tell whether zero matches is an orderly
   negative adjudication or an input defect.

### S30 - trust roots are conflated and path identity is insufficient (P1, BLOCKING)

`resolve_harness_surfaces(*, workspace_root, autoharness_home, shipment_id)`
takes **two** roots, and the containment section constrains paths against
"the workspace root" as though there were one. The plan never says which root
each class of input is contained against, nor whether `autoharness_home` is
trusted, semi-trusted or untrusted relative to the workspace.

This matters because the two roots have genuinely different trust properties:
`autoharness_home` is global, shared across workspaces, and not under the
reviewed branch's control.

Separately, the containment mechanism itself is insufficient. Lexical plus
canonical comparison performed **before** the read is a TOCTOU pattern: the path
can be replaced between the check and the open. The plan mentions rejecting
symlinks and junctions but specifies no **no-follow open** and no post-open
identity re-verification (file-descriptor identity, or device/inode equivalence
on Windows). "Canonicalize then open" is exactly the sequence this class of
defect exploits.

### S31 - the executable `181` carriers remain stale against revision 9 (P1, BLOCKING)

Revision 9 rewrote the plan and repointed the carriers' review prose, but the
`181.001-T`-`181.005-T` records that an executor will actually read still
describe the revision-8 world. Specifically, they retain: dependency and
review text that does not match the plan's current chain; the older
lifecycle state model rather than the `UNRESOLVED` / `NO_HARNESS` /
`HARNESS_READY` adjudication; test surfaces that do not match the plan's named
test module; no approval-gated revert obligation; no CLI invocation contract;
and sizing that was synchronized in the plan's table but not consistently
reflected in the task bodies.

The pointer-only change fixed *review-state* duplication. It did not
synchronize *executable content*, which is what these carriers are for. An
executor following `181.003-T` today would build against a superseded contract.

### S32 - `184-S` restoration text and the governing decision retain stale claims (P2)

`.backlogit/archive/184-S.md` and
`docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md`
still carry prerequisite and root claims that revision 9 superseded - in
particular the description of `187-S` as a root and the prerequisite framing
that predates the `191-S` edge. These are current-state surfaces, not immutable
histories, so the staleness is a live contradiction rather than preserved
history.

### S33 - the review manifest retains stale revision-7 PASS prose (P2)

The mutable lifecycle review manifest still carries revision-7 PASS narrative in
several places. The attempt roster is correctly scoped as historical by the
`attempts_roster_note` added at manifest revision 15, but PASS prose outside the
roster is not covered by that scoping and reads as current-state.

### S34 - the JSON, dataclass and digest contracts are incomplete (P2)

The plan names `HarnessResolution`, `SurfaceStatus`, `Readiness` and
`inputs_sha256`, and specifies `--json`, without pinning: the JSON schema or key
set; whether the JSON is stable across versions; the dataclass field names,
types and optionality; the digest's canonical input ordering and separator
discipline; or the encoding. Two conforming implementations could produce
mutually unreadable output, and two digest implementations could disagree while
both following the prose.

### Carried open without re-argument

`S15`, `S16`, `S17`, `S18`, `S19`, `S20` (`P1`, blocking), `S21`, `S22`, `S23`,
`S24` (`P2`), `S25` (`P3`) and `S13` (`P3`) are **carried OPEN**.

Revision 9 lists `S15`-`S25` as `findings_addressed_pending_review`, and much of
that remediation is substantive. **Addressed is not closed.** This attempt does
not close them because the remediation is not independently verifiable while the
defects above stand: a containment contract cannot be verified closed when its
trust boundary is undefined (`S30` bears directly on `S17`), and an executable
boundary cannot be verified closed when its CLI is unowned (`S27` bears directly
on `S15`).

## Persona coverage

| Persona | Applied | Principal contributions |
|---|---|---|
| Constitution | yes | `S26` (gate circularity), `S14` closure attribution discipline, `S33` |
| Python | yes | `S30` (TOCTOU / no-follow identity), `S34` (dataclass and digest contracts) |
| Scope boundary | yes | `S27` (unowned CLI surface), `S31` (carrier staleness), `S32` |
| Learnings | yes | Cited the `188-S` self-bootstrap retirement as direct precedent for `S26`; cited `P-007` `G1`-`G9` as the settled approval pattern revision 9 correctly adopted |
| Architecture | yes | `S26`, `S28` (recovery-surface wiring), `S29` (mapping and lookup ambiguity) |
| Agent-Native Parity | yes | `S27`, `S28` - both are cases of a rule stated in prose with no machine-enforced consumer |
| Security Lens | no | Not triggered; see `security_lens_note` |

`dispatch_mode: multi-agent`. No capability ran degraded at this attempt.

## Gate result

**FAIL / BLOCK**, under the standing decision rule (`P0` or `P1` present is
`FAIL`; `P2`-only is `ADVISORY`; `P3`-or-none is `PASS`).

Counts: `P0` 1, `P1` 11, `P2` 7, `P3` 2 - **21 findings open**, 12 blocking.

One finding was closed at this attempt: `S14`, on external evidence, as
recorded above. **No severity was lowered, no finding was deferred or waived,
and no other finding was closed.**

`SM-2` `HARVEST_ADMITTED` remains **SHUT**. The plan is **not
publication-eligible**.

The execution axis is separately and independently shut, and is now shut in a
new way: `187-S` depends on `191-S`, and `S26` finds `191-S` itself unable to
clear its own gates.

## Authorization boundary

This attempt **consumed attempt number 8** and is **not terminal**. The operator
directive that dispatched it explicitly authorizes continued remediation after
recording.

This review **performed no remediation**: no plan, source, template, skill,
manifest, test, backlog carrier, stash entry, checkpoint or GitHub surface was
mutated. It wrote only this immutable artifact and the mutable verdict manifest,
plus the current-state pointer fields the established carrier pattern requires.

## Scope statement

Verdicts are asserted by independent attempts and never by Stage. Stage authored
revision 9; Stage did not judge it, and Stage closes no finding. The `S14`
closure recorded here rests on external commits and the observed state of the
installed artifact and manifest, not on any Stage assertion.
