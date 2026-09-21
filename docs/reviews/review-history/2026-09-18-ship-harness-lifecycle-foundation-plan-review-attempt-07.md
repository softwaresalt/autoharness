---
title: "Plan review attempt 07 - SHIP-HARNESS-LIFECYCLE-FOUNDATION (187-S)"
description: "Immutable per-attempt plan-review artifact recording the SEVENTH independent review of docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md at revision 8, the first independent review of revision 8 and the first after the external retirement of 188-S/182-F. GATE FAIL: one P0 and six P1 blocking findings, four P2 and two P3 non-blocking. The central defect is that revision 8 treats the externally installed harness-architect actor as satisfying a BEHAVIORAL prerequisite when the installed SKILL.md prescribes a test runner this workspace does not use and P-004 does not accept. Attempt 07 is CONSUMED and TERMINAL under the current authorization; no remediation was performed and none is authorized without a fresh explicit operator instruction."
doc_type: review
source: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-07.md
date: 2026-09-20
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 7
attempt_range: "07"
attempt_conformance: conforming
review_terminal: true
terminal_designation: terminal-under-current-authorization
terminal_disposition: FAIL-BLOCKING-P0-AND-P1
terminal_note: "Attempt 07 is TERMINAL in the sense that it CONSUMES the attempt number and that no further review or remediation cycle is authorized after it under the instruction that dispatched it. This is NOT a terminal PASS and NOT a convergence terminal: the gate FAILED. Any subsequent remediation of the findings recorded here, and any attempt 08 to judge that remediation, requires a FRESH EXPLICIT OPERATOR AUTHORIZATION."
verdict_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
supersedes: null
predecessor_artifact: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-06.md
plan_path: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
plan_id: ship-harness-lifecycle-foundation
reviewed_revision: 8
reviewed_content_head: be9542a5
reviewed_content_state: committed
reviewed_branch: chore/stage-176-s-workflow-defects
plan_mutated_by_this_attempt: false
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 6
feature_id: 181-F
shipment_id: 187-S
declared_surface_count: 2
review_cycle: 7
dispatch_mode: multi-agent
degraded_capabilities:
  - capability: learnings
    state: bounded
    note: "Learnings persona ran under a bounded docs-only scope. It returned NO revision-specific finding and is recorded as raising none; it supplied relevant citations only. Its silence is a SCOPE ARTIFACT and MUST NOT be read as a clean bill of health on the learnings axis."
security_lens_triggered: false
security_lens_note: "No Security Lens trigger fired for this revision. Note that S17 (containment/traversal/symlink fail-closed) is recorded on the ARCHITECTURE and PYTHON axes as a robustness-contract gap, not as a Security Lens finding; had the Security Lens triggered it would have been evaluated there as well."
gate_result: FAIL
decision: BLOCK
verdict_is_pass: false
verdict_at_entry: null
verdict_at_entry_disposition: PENDING-INDEPENDENT-REVIEW
verdict_at_entry_plan_revision: 8
verdict_at_entry_manifest_revision: 13
verdict_at_entry_publication_eligible: false
remediation_authorization: none-after-this-review
remediation_performed: false
remediation_cycle_proposed: false
disposition: FAIL-BLOCKING-P0-AND-P1
p0_open: 1
p1_open: 6
p2_open: 4
p3_open: 2
open_findings: [S13, S14, S15, S16, S17, S18, S19, S20, S21, S22, S23, S24, S25]
blocking_findings: [S14, S15, S16, S17, S18, S19, S20]
closed_predecessor_findings: []
carried_predecessor_findings: [S13]
findings_raised_at_this_attempt: [S14, S15, S16, S17, S18, S19, S20, S21, S22, S23, S24, S25]
hardening_required: true
hardening_present: true
hardening_sufficient: false
hardening_note: "Hardening is present but INSUFFICIENT at revision 8: the hardening section does not reach the executable-boundary, durable-state, containment or approval-gated-rollback gaps recorded as S15-S18."
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
  - "terminal"
  - "fail"
  - "bootstrap-retirement"
  - "portfolio-2026-09-18"
---

# Plan review attempt 07 - SHIP-HARNESS-LIFECYCLE-FOUNDATION (187-S)

## Reviewed subject

`docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` at **revision
8**, read at committed base `be9542a5` on branch
`chore/stage-176-s-workflow-defects`.

This is the **first independent review of revision 8**, and the first review of
any revision after shipment `188-S` and feature `182-F` were retired as
externally satisfied. Revision 8 was authored as a graph-fact synchronization
after the harness-architect actor arrived in the publication baseline through
harness-maintenance commit `07b4be79263252b1820701fd123d0aed85c1db2a`.

The plan was **not modified by this attempt**. No remediation was performed and
none is authorized.

## Why this attempt exists

Attempt 06 returned PASS against **revision 7**. That verdict was briefly
carried forward onto revision 8 and then withdrawn at manifest revision 13,
because a verdict belongs to the revision an independent attempt actually
judged and is not extensible by the authoring agent. Revision 8 therefore
entered this attempt holding a **null verdict**, `awaiting_attempt: 7`, and
`publication_eligible: false`.

Revision 8's own claim is that nothing the terminal review judged has changed -
that `D1`-`D3`, `G1`-`G8`, `P1`-`P6`, the class partition, the addressing rule
and the ACTIVATE contract are all unchanged in substance, and that only graph
facts moved. **That claim is the principal thing this attempt tested, and it
does not hold.** The retirement of `188-S` did not merely remove a graph edge;
it silently replaced a *planned, contract-bound* actor installation with an
*externally authored* artifact that this plan never specified and never
verified. Revision 8 inherited the conclusion of the bootstrap work without
inheriting its obligations.

## Findings

Findings are merged and deduplicated conservatively across the six personas.
Where two personas raised the same defect at different severities, the finding
is recorded at the **higher** severity and the disagreement is stated; no
severity was lowered to reconcile a split.

### S14 - the installed actor does not satisfy the behavioral prerequisite revision 8 says it satisfies (P0, BLOCKING)

Raised by: Constitution, Python, Architecture. Severity split P0/P1; recorded
at **P0** as the higher of the two, because the defect makes the plan assert a
falsehood about a precondition rather than merely leave one under-specified.

The installed actor at `.github/skills/harness-architect/SKILL.md:126` instructs:

> Run `pytest` for the harness tests. ALL tests MUST fail with ...

`P-004` in `.github/policies/workflow-policies.md:88` requires:

> **Precondition**: `python -m py_compile src/autoharness/cli.py` exits 0 AND
> `PYTHONPATH=src python -m unittest discover -s tests` exits non-zero with
> expected failure markers in the output for every test function.

`.autoharness/harness-manifest.yaml` agrees with P-004 and not with the actor:
`TEST_COMMAND` at L471 and `QUALITY_GATE_2` at L508 are both
`PYTHONPATH=src python -m unittest discover -s tests`. The manifest goes
further and records at L495-L497 that **this workspace has no pytest
configured at all**, and that a `profile.test.command` of `"pytest"` is a
stale field deliberately overridden.

So the actor prescribes a runner that (a) is not the runner P-004 accepts as
evidence, and (b) is not installed in this workspace. An actor invocation that
followed its own instructions would produce no P-004-admissible RED evidence.

Revision 8's defect is not that it caused this - the artifact is external - but
that it **treats mere installation as prerequisite satisfaction**. The plan
records `actor_installed_in_baseline: true` and reasons from there, with no
behavioral conformance criterion anywhere: nothing in revision 8 requires the
installed actor to emit the P-004 command, nothing detects that it does not,
and nothing halts if it does not. The self-bootstrap axis is declared closed on
the strength of a file existing.

**Installation is a presence fact. P-004 satisfaction is a behavioral fact.**
Revision 8 conflates them, and the conflation is false on live evidence.

### S15 - the resolver has no executable boundary, no authoritative declaration, no typed output and no wired consumer (P1, BLOCKING)

Raised by: Architecture, Python, Agent-Native Parity.

The lifecycle resolver is specified as behavior without being specified as a
*thing that can be run*. The plan does not fix:

* a **stable executable boundary and invocation** - no module path, entry
  point, CLI subcommand or callable signature by which the resolver is invoked,
  and therefore no surface a test can bind to;
* an **authoritative task-to-surface declaration** - no single named source of
  truth stating which surfaces a given task requires, so the mapping the
  resolver is supposed to resolve has no canonical input;
* a **structured typed output** - the result is described in prose
  (`HARNESS_READY` / `NO_HARNESS` and a report of missing templates) but has no
  declared schema, field set or types, so no consumer can depend on its shape;
* a **mechanically wired consumer** - nothing in the plan makes any Ship step,
  gate or policy path actually call it as a matter of mechanism.

The compound risk is specific and it is the one this unit exists to avoid: the
resolver lands as **agent prose that no machine executes, or as dead code that
nothing invokes**. `181.002-T` already concedes the inert state ("the resolver
is implemented and unit-tested but NOTHING invokes it"), and `181.005-T`'s
ACTIVATE commit wires *documentation sections* into two Ship surfaces rather
than wiring an executable into a call path. Without a boundary, the activation
cannot be distinguished from documentation.

### S16 - no durable, freshness-bound state carrier (P1, BLOCKING)

Raised by: Architecture, Agent-Native Parity.

Harness state is computed and then discarded. The plan provides no durable
carrier readable by all four declared consumers:

1. Ship, at pre-task time within a run;
2. the `P-004` gate, which must consume the state as a precondition;
3. CLI / MCP / human invocation outside a Ship run;
4. **checkpoint recovery**, which must re-establish harness state after a
   crash without silently assuming the pre-crash result still holds.

Nor is there any **freshness binding**: no declared inputs digest, no staleness
predicate, no invalidation rule. A `HARNESS_READY` determined before a template
or manifest change remains nominally true afterwards. Consumer 4 is the sharpest
case - recovery is precisely the moment a stale readiness claim is most
dangerous and least likely to be re-derived.

### S17 - the resolver contract lacks fail-closed containment requirements (P1, BLOCKING)

Raised by: Python, Architecture.

The resolver reads templates and surfaces by path, but its contract states no
requirement for:

* **workspace containment** - resolution confined to the workspace root;
* **traversal rejection** - `..` segments and absolute-path escapes refused;
* **symlink discipline** - symlinks that leave the workspace refused rather
  than followed.

All three must be **fail-closed**: refusal on violation, never best-effort
resolution and never silent skip. Absent these, a crafted or merely careless
surface declaration can direct reads outside the workspace, and the resolver
has no stated obligation to stop. Recorded on the architecture and robustness
axes; the Security Lens did not trigger for this revision and did not evaluate
it.

### S18 - rollback prescribes `git revert` without fresh operator approval (P1, BLOCKING)

Raised by: Constitution, Scope.

The rollback path directs a `git revert` without requiring a fresh, live
operator approval at the moment of execution. This is the same class of defect
that `P-007` was amended to close for `git restore`: the workspace's own
governing precedent (recorded in `.autoharness/harness-manifest.yaml` at the
P-007 checksum-refresh note for `162-S/154.002-T`, decisions G1-G9) establishes
that a destructive history operation requires a **fresh, live,
non-synthesizable operator approval** before it may run, that a backlog comment
is audit evidence and never authorization, and that the absence of an approval
channel is a fail-closed halt in **all** modes including dark/AFK.

Revision 8's rollback inherits none of that. As written it authorizes an
unattended destructive operation.

### S19 - stale current-state contradictions in live review-state carriers (P1, BLOCKING)

Raised by: Constitution, Scope.

Three live surfaces contradicted the frontmatter state they are supposed to
report, at the moment this attempt began (revision 8, manifest revision 13,
decision revision 6, verdict null, `awaiting_attempt: 7`, publication
ineligible):

1. `docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md`
   **description** still read "MANIFEST REVISION 11", "THE VERDICT OF RECORD IS
   PASS ... against plan REVISION 7", and "awaiting_attempt is NULL" - directly
   contradicting its own frontmatter two lines below.
2. The same file's **`open_counts_note`** still asserted counts "asserted by
   independent attempt 04", stale by three attempts.
3. `.backlogit/queue/187-S.md` **footer** still read "REVISION 7, verdict PASS
   as determined by TERMINAL independent attempt 06 ... awaiting_attempt NULL.
   Verdict manifest revision 10".

The manifest-revision-13 update corrected the *body* prose of 187-S but left
its footer, and rewrote the frontmatter of the review manifest but left its
description and counts note. The pattern - current-state facts duplicated into
free prose in several places, then refreshed in some and not others - is the
defect; the three instances are its symptoms.

**Note on disposition.** Recording attempt 07 necessarily writes current review
state into exactly these surfaces, so their specific stale strings do not
survive this commit. **S19 is nevertheless recorded OPEN.** A finding is closed
by an independent attempt that verifies the closure, never by the agent whose
own edit happened to overwrite the offending text, and the underlying
duplication pattern is untouched.

### S20 - the problem frame still authorizes actor installation (P1, BLOCKING)

Raised by: Scope, Constitution, Architecture.

The plan's current problem framing continues to present installing the
harness-architect actor as work this portfolio performs and this plan
coordinates. That authorization is void: the actor was installed externally by
`07b4be79`, `188-S` and `182-F` are retired and archived without ever having
been claimed, executed or shipped, and no unit in this portfolio holds an
installation obligation for that artifact.

Revision 8 corrected the *graph* (dependencies, root status, retirement status)
but not the *frame*. The result is a plan whose frontmatter says the actor is
already installed and whose problem statement still reasons about installing
it. This is the frame-level counterpart of S14: both stem from revision 8
updating the facts around the bootstrap without re-deriving what the plan is
now for.

### S21 - the exact P-004 command is never quoted (P2)

Raised by: Python, Agent-Native Parity.

The plan refers to P-004's precondition without ever quoting the literal
command string. An executor cannot derive
`PYTHONPATH=src python -m unittest discover -s tests` from the plan alone, and
the absence of the literal is precisely what let S14's mismatch go unnoticed.

### S22 - `NO_HARNESS` transition-table contradiction (P2)

Raised by: Architecture, Python.

The `NO_HARNESS` state is described inconsistently across the plan. The
step sequence at L237-L238 treats it as a transition that halts before the task
partition runs; the state table at L465 defines it as a terminal fail state
("an explicit failed precondition, never silent success"); L476 and L616 add
further framings. These are not obviously reconcilable as written, and the
plan's own hardening question H2 ("Could `NO_HARNESS` be silently treated as a
pass?") is answered by appeal to the `176-S` gate rather than by the table.

### S23 - no executable RED / GREEN / full-suite commands (P2)

Raised by: Python.

The verification floor does not state runnable commands for the RED phase, the
GREEN phase or the full-suite run. Combined with S21, the plan's test-first
obligations are stated as intentions with no literal by which compliance could
be demonstrated or checked.

### S24 - stale `176-S` P-004 plan actor ownership (P2)

Raised by: Scope.

The `176-S` P-004 plan surface still attributes ownership of the actor to the
retired bootstrap unit. It is out of this plan's edit scope and is recorded
here as a cross-carrier staleness of the same family as S19 and S20, to be
routed to its owning unit rather than fixed here.

### S25 - ambiguous `P4` naming (P3)

Raised by: Agent-Native Parity.

The plan uses `P1`-`P6` for parity criteria (for example the `P4` row of the
parity table at L393) while the same document discusses policies `P-002` and
`P-004` and severities `P0`-`P3`. A bare `P4` is ambiguous between a parity
criterion and a policy on first reading. Naming only; no criterion is wrong.

### S13 - carried open, P3

`S13` is re-verified as still true and is **carried OPEN at P3 without being
lowered**. It remains a non-blocking follow-up held in stash `703B6FAF`, Item
4, outside this shipment's scope, under the operator's standing disposition.
It was not remediated and was not closed.

## Persona coverage

| Persona | Applied | Findings raised |
|---|---|---|
| Constitution | yes | S14, S18, S19, S20 |
| Python | yes | S14, S17, S21, S22, S23 |
| Scope boundary | yes | S18, S19, S20, S24 |
| Learnings | yes (bounded) | none - see note |
| Architecture | yes | S14, S15, S16, S17, S20, S22 |
| Agent-Native Parity | yes | S15, S16, S21, S25 |
| Security Lens | **not triggered** | n/a |

**Learnings note.** The Learnings persona ran under a **bounded docs-only
scope** and returned **no revision-specific finding**. It supplied relevant
citations only. Its silence is an artifact of that bound and is explicitly
**not** evidence that the learnings axis is clean.

**Security Lens note.** No Security Lens trigger fired for this revision, so
the lens was not applied. S17 is recorded on the architecture and robustness
axes instead.

## Gate result

**FAIL / BLOCK.**

Under the standing decision rule (P0 or P1 present -> FAIL; P2-only ->
ADVISORY; P3-or-none -> PASS), one P0 (`S14`) and six P1s (`S15`-`S20`) are
open and blocking. `p0_open: 1`, `p1_open: 6`, `p2_open: 4`, `p3_open: 2`.

No finding was lowered, deferred, waived or closed at this attempt. No
predecessor finding was closed. `S13` was carried at its recorded severity.

Plan **revision 8 is preserved unchanged** by this attempt, and
`publication_eligible` remains **false**. The plan was not edited and no review
log was appended to it.

## Authorization boundary

**Attempt 07 is CONSUMED and is TERMINAL under the authorization that
dispatched it.** No remediation was performed and none is authorized by this
artifact.

This is a terminal **FAIL**, not a terminal PASS and not a convergence
terminal. It closes the current authorization with the review gate **shut**.
Remediating any finding recorded here, and any attempt 08 to judge such a
remediation, requires a **fresh, explicit operator authorization**. Absent
that, this unit remains blocked on the review axis.

## Scope statement

This attempt read the plan, its carriers, the installed actor, the policy file
and the harness manifest. It **wrote** only this immutable artifact, the
mutable verdict manifest, and the current review-state pointers on `187-S`,
`181-F` and `181.001-T`-`181.005-T`. It did **not** modify the plan, any
source, template, skill, installed artifact, manifest, test or stash entry; it
ran no tests, created no checkpoint, touched no GitHub surface and pushed
nothing.
