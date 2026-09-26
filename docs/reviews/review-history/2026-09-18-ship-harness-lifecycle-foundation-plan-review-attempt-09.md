---
title: "Plan review attempt 09 - SHIP-HARNESS-LIFECYCLE-FOUNDATION (187-S)"
description: "Immutable per-attempt plan-review artifact recording the NINTH independent review of docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md, the FIRST independent review of revision 10, dispatched under the continuing operator authorization that also permitted the revision-10 remediation cycle. GATE RESULT FAIL/BLOCK at P0 2 / P1 22 / P2 13 / P3 2. Revision 10 correctly retires the circular 191-S prerequisite, restores 187-S as a root and states a far more complete resolver contract. It is STILL NOT SHIPPABLE. The new blocking defect is that the ACTIVATE contract names Ship surfaces THAT DO NOT EXIST - templates/agents/ship.md.tmpl and .github/agents/ship.md, where the real artifacts are templates/agents/_ship.agent.md.tmpl and .github/agents/_ship.agent.md - so the single atomic activation the whole unit converges on cannot be performed as written. A second structural defect is that the plan reads manifest variables_used as a PER-ARTIFACT field when it is a SINGLE TOP-LEVEL MAPPING, which invalidates the render rule and the PAR-6b parity criterion. S14 remains CLOSED on external Ship evidence. NO OTHER FINDING IS CLOSED."
doc_type: review
source: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-09.md
date: 2026-09-20
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 9
attempt_range: "09"
attempt_conformance: conforming
review_terminal: false
terminal_designation: not-terminal-remediation-authorized
terminal_disposition: FAIL-BLOCKING-P0-AND-P1
terminal_note: "Attempt 09 CONSUMES attempt number 9 and is NOT terminal. The operator directive that dispatched it authorizes a further remediation cycle after recording. This is a FAIL, not a convergence terminal and not a terminal PASS."
verdict_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
supersedes: null
predecessor_artifact: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-08.md
plan_path: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
plan_id: ship-harness-lifecycle-foundation
reviewed_revision: 10
reviewed_content_head: 844cee9c
reviewed_content_state: committed
reviewed_branch: chore/stage-176-s-workflow-defects
plan_mutated_by_this_attempt: false
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 7
feature_id: 181-F
shipment_id: 187-S
prerequisite_shipment_id: null
declared_surface_count: 1
review_cycle: 9
dispatch_mode: multi-agent
degraded_capabilities: []
security_lens_triggered: false
security_lens_note: "No Security Lens trigger fired. The containment findings S38 and S50 are recorded on the ARCHITECTURE and PYTHON axes as robustness-contract gaps in a planning document, not as live exploitable vulnerabilities: no resolver code exists yet to attack."
gate_result: FAIL
decision: BLOCK
verdict_is_pass: false
verdict_at_entry: null
verdict_at_entry_disposition: PENDING-INDEPENDENT-REVIEW
verdict_at_entry_plan_revision: 10
verdict_at_entry_manifest_revision: 17
verdict_at_entry_publication_eligible: false
remediation_authorization: authorized-by-operator-directive-after-recording
remediation_performed: false
remediation_cycle_proposed: true
disposition: FAIL-BLOCKING-P0-AND-P1
p0_open: 2
p1_open: 22
p2_open: 13
p3_open: 2
open_findings_count: 39
blocking_findings_count: 24
open_findings: [S13, S15, S16, S17, S18, S19, S20, S21, S22, S23, S24, S25, S26, S27, S28, S29, S30, S31, S32, S33, S34, S35, S36, S37, S38, S39, S40, S41, S42, S43, S44, S45, S46, S47, S48, S49, S50, S51, S52]
blocking_findings: [S15, S16, S17, S18, S19, S20, S26, S27, S28, S29, S30, S31, S35, S36, S37, S38, S39, S40, S41, S42, S43, S44, S45, S46]
closed_predecessor_findings: []
carried_predecessor_findings: [S13, S15, S16, S17, S18, S19, S20, S21, S22, S23, S24, S25, S26, S27, S28, S29, S30, S31, S32, S33, S34]
findings_raised_at_this_attempt: [S35, S36, S37, S38, S39, S40, S41, S42, S43, S44, S45, S46, S47, S48, S49, S50, S51, S52]
revision_10_addressed_pending_review_not_closed: [S13, S15, S16, S17, S18, S19, S20, S21, S22, S23, S24, S25, S26, S27, S28, S29, S30, S31, S32, S33, S34]
previously_closed_findings_unchanged:
  - finding: S14
    state: CLOSED
    closed_at_attempt: 8
    closed_by: external-ship-review-remediation
    closing_commits:
      - 1cb0dc8140a809d63c3193d58431cd14408788b7
      - b8ac632a93751fb29c51a8e5bf0f5e036b65cfb3
    reaffirmed_at_this_attempt: true
    note: "S14 remains CLOSED on external Ship evidence alone. It was NOT closed by any Stage artifact and NOT by shipment 191-S, which is retired and never executed. This attempt neither reopens it nor extends its closure to any other finding."
hardening_required: true
hardening_present: true
hardening_sufficient: false
hardening_note: "Revision 10 hardening is again materially stronger - one classification table, separated trust roots, an approval-gated rollback with an explicit dark/AFK halt - but it remains INSUFFICIENT because it hardens a contract whose central activation target does not exist (S35) and whose render rule is grounded in a misreading of the manifest schema (S36). Hardening cannot be assessed as adequate for surfaces that have not been correctly identified."
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
  - "revision-10"
  - "nonexistent-activation-target"
  - "portfolio-2026-09-18"
---

# Plan review attempt 09 — Ship pre-task harness-generation lifecycle

## Reviewed subject

`docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` at **revision
10**, committed base `844cee9c` on branch
`chore/stage-176-s-workflow-defects`, together with the live carriers `181-F`,
`181.001-T`–`181.005-T` and `187-S`, the governing decision at revision 7, and
the mutable verdict manifest at manifest revision 17.

This is the **first** independent review of revision 10.

## What revision 10 got right

The structural corrections are real and are recorded as such:

* Retiring `191-S` / `185-F` dissolves the `S26` circularity at its root rather
  than re-scoping it, and the retirement is honest about never having executed.
* Restoring `187-S` as a `dag-root` with an empty dependency set is correct,
  and the record distinguishes root status from claim authority.
* Structural installation (`07b4be79`) and behavioural conformance (`1cb0dc81`,
  `b8ac632a`) are kept rigorously distinct throughout.
* A single classification table now governs surface adjudication, and the
  carriers no longer restate mutable review state.
* The rollback contract — fresh, live, SHA-bound approval with an explicit halt
  when the operator is dark or AFK — matches the settled `P-007` `G1`–`G9`
  pattern.

**None of this makes the plan executable**, for the reasons below.

## Findings

### `S35` — the ACTIVATE contract names Ship surfaces that do not exist (P0, BLOCKING)

The plan's ACTIVATE contract, `181.005-T`, `181-F` and `187-S` all name
**exactly three files**, of which two are:

* `templates/agents/ship.md.tmpl`
* `.github/agents/ship.md`

**Neither path exists in this repository.** The actual artifacts are:

* `templates/agents/_ship.agent.md.tmpl`
* `.github/agents/_ship.agent.md`

The manifest entry for the installed Ship agent records
`path: .github/agents/_ship.agent.md`. The entire unit converges on one atomic
activation commit, and that commit is specified against paths that cannot be
opened. This is not a typo to be fixed in passing: the plan's three-file /
one-manifest-entry count, its `PAR-1`–`PAR-6b` parity criteria and its rollback
unit are all defined over these paths, so every one of them is currently
unverifiable.

### `S36` — manifest `variables_used` is top-level, not per-artifact (P1, BLOCKING)

The render rule states that placeholder values come **"solely from the matched
manifest entry's `variables_used`"**, and `PAR-6b` requires the manifest entry
to name the authoritative template it was rendered from.

`.autoharness/harness-manifest.yaml` does not have that shape. `variables_used`
is a **single top-level mapping** of 41 keys. **Zero** of the 73 `artifacts`
entries carries a `variables_used` key; artifact entries carry only `path`,
`primitive`, `template`, `checksum` and an optional `note`.

Two consequences follow. First, "the matched manifest entry's `variables_used`"
resolves to nothing, so the render rule as written can never produce a value
and every surface would adjudicate `UNRESOLVED`. Second, the installed Ship
agent's entry records `template: global agent definition` — a descriptive
string, **not** a `.tmpl` path — so `PAR-6b` is unsatisfiable for the very
artifact this unit activates. The `skills/<id>/SKILL.md.tmpl` mapping rule is
correct for skill artifacts and incorrect as a general rule.

### `S37` — state aggregation, `none` and `INVALID` are incomplete (P1, BLOCKING)

Three gaps in the state model:

* **Aggregation is undefined.** A shipment may declare several surfaces across
  several tasks. The plan gives a per-surface `SurfaceStatus` and a single
  top-level `HarnessState`, and never says how many surfaces combine into one
  state. Is one `STALE` surface among four `PRESENT` ones `NO_HARNESS`? The
  classification table answers only the one-surface case.
* **`harness-surface:none` has no state mapping.** The grammar admits it, but
  no row of the classification table says what a shipment all of whose tasks
  declare `none` resolves to. `HARNESS_READY` and `NO_HARNESS` are both
  defensible and the plan picks neither.
* **`SurfaceStatus.INVALID` is declared and unreachable.** No row of the
  classification table produces it. Either it is dead, or a case is missing.

### `S38` — the no-follow check is itself a race (P1, BLOCKING)

The containment contract orders the checks as: lexical rejection, canonical
containment, **then** a prohibition on reparse components, **then** a single
opened handle with pre/post identity validation.

Checking for a reparse point and *then* opening is the classic check-then-use
race the pre/post validation is meant to eliminate, and it does not eliminate
it: a component can be replaced with a junction between the check and the open,
and the post-open identity comparison compares the substituted target to
itself. The prohibition must be enforced **at open time** — `O_NOFOLLOW` /
`FILE_FLAG_OPEN_REPARSE_POINT` semantics, or an `openat`-style descent — not by
a preceding `lstat` sweep. Attempt 08's `S30` identified the conflated trust
roots; revision 10 separated the roots but preserved the racing sequence.

### `S39` — `<resolved-or-default>` is a literal, not a command (P1, BLOCKING)

The CLI is quoted throughout the plan, `181-F`, `187-S` and `181.002-T`, and is
required as a **literal** in `181.003-T`'s fixtures, as:

```
autoharness harness resolve --workspace . --autoharness-home <resolved-or-default> --shipment <id> --json
```

`<resolved-or-default>` is placeholder prose. A fixture that carries this
string carries something that cannot be executed, and `181.003-T` is explicitly
required to carry the invocation literally so that it is *exercised rather than
described*. Either the flag has a real default and should be omitted from the
canonical invocation, or the canonical invocation must show a real value.

### `S40` — the RED task cannot be import-safe as sequenced (P1, BLOCKING)

`181.001-T` requires tests that fail by **assertion**, not by `ImportError`,
and explicitly forbids import failure as RED evidence. But `181.001-T` is first
in the chain and `181.002-T` — which creates
`src/autoharness/harness_surfaces.py` — comes after it. At the moment
`181.001-T` is verified RED, the module does not exist, so
`import autoharness.harness_surfaces` raises `ModuleNotFoundError` and the task
fails its own acceptance criterion.

The same task's coverage list requires fixtures for containment, race and
manifest-match cases, but the fixture corpus is owned by `181.003-T`, two
positions later in the declared chain. The plan's own dependency order
contradicts its own task contents.

### `S41` — the two Ship sections lack exact anchors and may install duplicate gates (P1, BLOCKING)

`181.005-T` updates "the harness-generation section" and "the crash-recovery
section" of the template and the mirror. Neither is identified by exact heading
text, heading level or ordinal position, and `PAR-1`/`PAR-2` are stated as
parity criteria **between** template and mirror rather than as anchors for
insertion. Two independent insertions that each halt before task partition can
produce a duplicated gate whose second evaluation is either redundant or
contradictory, and nothing in the contract forbids it.

### `S42` — the checkpoint promise names Stage but Stage has no such surface, and the ordering is not implementable (P1, BLOCKING)

The plan states that "after the operator selects a checkpoint and **Stage or
Ship** restores it, the resolver is re-invoked before the task cursor and phase
execution are restored."

Two problems. **Stage does not execute tasks**, has no task cursor and never
performs harness generation; naming Stage as a consumer of this rule describes
a surface that does not exist and will not be built by `181.005-T`, which
touches Ship only. And the ordering "after checkpoint restore, before cursor
restore" names **no integration point**: the crash-recovery protocol does not
expose a seam between those two acts, so the rule cannot be wired even in Ship.
Attempt 08's `S28` is carried and is now more precisely located.

### `S43` — activation is verified before it happens (P1, BLOCKING)

`181.004-T` (VERIFY) precedes `181.005-T` (ACTIVATE) in the declared chain, and
the plan describes `181.004-T` as producing evidence "with the actor installed
and the lifecycle **not yet wired** into Ship." Yet the verification floor and
the `PAR-1`–`PAR-6b` parity criteria describe checks over the **activated**
mirror and the **refreshed** manifest entry. As sequenced, nothing verifies the
activation after it occurs; `181.005-T` carries no verification step of its own.

### `S44` — governing decision `D10` is stale (P1, BLOCKING)

`D10` describes the conditional-withholding regime in terms of a portfolio
shape that revision 7 of the decision has since changed. It continues to
reason about the withheld set and its verdict emitters without accounting for
the retirement of `176-S`, and it is cited by the archived `184-S` restoration
clause that this plan's carriers now depend on for their no-revival guarantee.
A governing decision section that contradicts its own portfolio table cannot
be relied on as the authority the plan cites it as.

### `S45` — the archived `176`/`168` records carry contradictory rationale (P1, BLOCKING)

The retirement clauses copied onto the thirteen archived `176`/`168` records
assert both that the unit is retired because its **design** was superseded and
that the requirement survives for a **fresh** re-harvest gated on `185-S` and
`187-S`. Those two statements are individually defensible and are placed
without reconciliation, so a future reader cannot determine whether a
restoration is forbidden because the design is wrong or merely deferred because
the sequence is not ready. The `NOREVIVE` clause and the `REHARVEST` clause
state different things about the same records.

### `S46` — direct carriers, task sizes and the review note are stale (P1, BLOCKING)

* `181.005-T`, `181-F` and `187-S` all repeat the nonexistent Ship paths of
  `S35`, so the defect is present in four places, not one.
* The plan's frontmatter still carries `latest_attempt: 8` and
  `awaiting_attempt: 9` while the manifest is authoritative for both; the plan
  says its own fields are pointers, and they now point at a superseded state.
* `181.002-T` is sized `L` while the plan's own granularity rule caps a task at
  roughly two hours of human-equivalent effort; see `S48`.

### `S47` — reason codes, JSON, digest and redaction are named but not specified (P2)

The plan requires "a closed, documented set" of reason codes, "canonical JSON
with domain separation", and "root-relative and redacted" paths. **None of the
three is enumerated.** There is no reason-code list, no canonical-JSON
serialization rule (key ordering, separators, unicode escaping), no domain
separation scheme, and no definition of what redaction removes beyond the
examples. A downstream implementer would have to invent all three, and two
implementations would produce different `inputs_sha256` values for the same
inputs.

### `S48` — the `L`/`high` resolver task should be split (P2)

`181.002-T` owns the whole resolver module *and* the CLI routing, and is sized
`L`/`high`. The plan's own task-granularity rule and the 2-hour constraint both
point to splitting it — module and CLI are separable, and the CLI has a
distinct acceptance surface (argument parsing, exit codes, stream discipline).
Attempt 08's `S27` was that the CLI had no owner; revision 10 fixed ownership by
enlarging one task past the limit rather than by adding one.

### `S49` — input bounds are undefined (P2)

The resolver reads backlog records, a manifest and two file trees with no
stated bound on file size, entry count, declaration count or directory depth. A
pathological input is neither rejected nor bounded, and there is no `UNRESOLVED`
row for "input exceeds bounds."

### `S50` — the ambient `BACKLOGIT_WORKSPACE_DIR` override is not neutralized (P2)

The plan requires the resolver to use the existing `resolve_backlog_root`
helper and forbids a backlog-path argument, both of which are correct for
consistency. But `resolve_backlog_root` honours the ambient environment
variable `BACKLOGIT_WORKSPACE_DIR`, so the backlog root — an input the
containment contract treats as anchored to `workspace_root` — can be redirected
by the caller's environment without violating any stated rule. The containment
contract and the root-resolution helper disagree, and the plan does not say
which wins.

### `S51` — reparse-point tests are nondeterministic (P2)

`181.003-T` constructs reparse-point cases at test time and "skips cleanly
where the platform forbids their creation." On a developer workstation without
the required privilege, the entire symlink and junction escape corpus silently
skips, and the suite reports green over untested containment. A skip in a
containment corpus is indistinguishable from a pass.

### `S52` — the manifest count and note are stale (P2)

Carriers and the decision refer to the manifest's shape in terms that no longer
match: the live manifest carries **73** `artifacts` entries. `D11` is correct
to state membership as a rule rather than a count, and the surrounding prose
does not consistently follow it.

## Carried open without re-argument

`S13` (P3); `S15`–`S20` (P1); `S21`–`S24` (P2); `S25` (P3); `S26` (P0);
`S27`–`S31` (P1); `S32`–`S34` (P2) are all **carried OPEN**.

Revision 10 lists every one of them as `findings_addressed_pending_review`, and
much of that remediation is substantive — `S26`'s subject is retired, `S27`'s
CLI now has a named owner, `S30`'s trust roots are separated. **Addressed is not
closed, and partially-addressed is not closed.** This attempt closes none of
them, for the reason attempt 08 gave and this attempt reaffirms: remediation is
not independently verifiable while structural defects stand. A resolver
contract cannot be verified closed when its activation target does not exist
(`S35`) and its render rule misreads the schema it reads from (`S36`); a
containment contract cannot be verified closed while its no-follow enforcement
races (`S38`); and a task chain cannot be verified closed while it contradicts
its own ordering (`S40`, `S43`).

`S26` specifically is **carried, not closed**, even though `191-S` is now
retired. The reviewers record that the retirement removes the circularity as
described; they decline to close the finding because the restructure it is part
of introduced a new `P0` in the same area, and closure would assert a
verification this attempt could not perform.

## Persona coverage

| Persona | Applied | Principal contributions |
|---|---|---|
| Constitution | yes | `S43` (verify-before-activate), `S45` (contradictory retirement rationale), `S46` |
| Python | yes | `S38` (no-follow open race), `S49` (input bounds), `S50` (ambient override), `S47` |
| Scope boundary | yes | `S35` (nonexistent activation target), `S46` (carrier staleness), `S48` |
| Learnings | yes | Cited `P-007` `G1`–`G9` as the approval pattern revision 10 correctly retained; cited the `188-S` retirement as the precedent revision 10 correctly followed for `191-S` |
| Architecture | yes | `S37` (aggregation and `none`), `S41` (anchors and duplicate gates), `S42` (checkpoint surface), `S44` (`D10`) |
| Agent-Native Parity | yes | `S39` (unrunnable literal), `S42` — both are rules stated in prose with no machine-enforced consumer |
| Security Lens | no | Not triggered; see `security_lens_note` |

`dispatch_mode: multi-agent`. No capability ran degraded at this attempt.

## Gate result

**FAIL / BLOCK**, under the standing decision rule (`P0` or `P1` present is
`FAIL`; `P2`-only is `ADVISORY`; `P3`-or-none is `PASS`).

Counts: `P0` 2, `P1` 22, `P2` 13, `P3` 2 — **39 findings open**, 24 blocking.

**No finding was closed at this attempt.** No severity was lowered, and no
finding was deferred or waived. `S14` remains closed from attempt 08 on
external Ship evidence; that closure is reaffirmed and is **not** extended to
any other finding.

`SM-2` `HARVEST_ADMITTED` remains **SHUT**. The plan is **not
publication-eligible**.

The execution axis is separately shut: `187-S` is a genuine root, but its
activation task cannot be performed against the paths it names.

## Authorization boundary

This attempt **consumed attempt number 9** and is **not terminal**. The
operator directive that dispatched it authorizes a further remediation cycle
after recording.

This review **performed no remediation**: no plan, source, template, skill,
manifest, test, backlog carrier, stash entry, checkpoint or GitHub object was
mutated. Only this immutable artifact and the mutable verdict manifest were
written.

## Scope statement

Reviewed: the plan at revision 10; the live carriers `181-F`,
`181.001-T`–`181.005-T` and `187-S`; the governing decision at revision 7; the
archived `176`/`168` and `191`/`185` retirement records as they bear on this
unit; `.autoharness/harness-manifest.yaml` and the on-disk Ship agent artifacts
as ground truth for `S35`, `S36` and `S52`; and `src/autoharness/backlog_root.py`
as ground truth for `S50`.

Not reviewed: the harness-architect actor's content; the `184-S` / `185-S`
operation substrate; any plan outside this `plan_id`.
