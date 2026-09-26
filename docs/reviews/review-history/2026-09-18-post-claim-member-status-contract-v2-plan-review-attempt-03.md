---
title: "Plan review attempt 03 — Post-claim member-status contract (P-002.7)"
description: "Immutable per-attempt plan-review artifact recording the third and operator-designated terminal independent review of docs/plans/2026-09-18-post-claim-member-status-contract-plan.md at revision 3, against reviewed content HEAD 4b4330b9. Gate result FAIL; decision BLOCKED on zero P0, one P1, zero P2 and one P3 deduplicated finding. All five attempt-02 findings are independently re-derived closed: 169.016-T now emits the plan's three-token vocabulary with the not-observed state evaluated first, the six stale item_deps edges from the retired activation chain are gone and the surviving edge set is exactly PREPARE-RED-ACTIVATE-VERIFY-DOCS, the R5 narrowing rule now returns the unit to Stage with the affected assertion families retired or re-observed red before activation resumes, the retired phase vocabulary is gone from 169.007-T and 169-F, and requires_plan_hardening is true. The new P1 is that the composed-state verdict line has no declared format and no declared destination, so the plan's own absent-line-is-NOT_OBSERVED rule is unevaluable, and the one concrete consumer named for it, .github/workflows/ci.yml, is described with an inverted relation and is modified by no task in the unit. The P3 is that the 177-S and 169-F size_composition rollup reports fourteen members including five archived absorbed tasks while the manifest correctly lists nine tasks plus the covering feature. Dispatch ran in single-agent declared degradation with all seven personas covered inline; engram was circuit-open and not retried, intercom and graphtor-docs were unavailable. No remediation was performed and no PASS is asserted."
doc_type: review
source: docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-03.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 3
attempt_range: "03"
attempt_conformance: conforming
review_terminal: true
terminal_designation: operator-declared
terminal_disposition: TERMINAL-BLOCKED
verdict_manifest: docs/reviews/2026-09-18-post-claim-member-status-contract-v2-plan-review.md
supersedes: null
predecessor_artifact: docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-02.md
plan_path: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
plan_id: post-claim-member-status-contract-v2
reviewed_revision: 3
reviewed_content_head: 4b4330b9
reviewed_content_state: committed
reviewed_branch: chore/stage-176-s-workflow-defects
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 3EF5AAF2
feature_id: 169-F
shipment_id: 177-S
unit_role: reduced-defect-unit
dag_role: root
declared_surface_count: 4
review_cycle: 3
dispatch_mode: single-agent-declared-degradation
anchor_route: absent
anchor_route_note: "No anchor_review key exists in .autoharness/config.yaml model_routing, so no cross-model anchor was dispatchable. The cross-model rubrics ran under same-model declared degradation. This is recorded, not compensated for."
model_route_note: "Stage role route resolved from .autoharness/config.yaml model_routing.stage (claude-opus-5/anthropic/high), re-read fresh at session start per the Session-Start Dynamic Reload contract. The escalation route model_routing.escalation (gpt-5.6-sol/openai/high) is distinct from both the role route and tier3, so the same-route ESCALATION_DEGRADED guard does not fire. No escalation was triggered: no failure threshold was reached during this review."
degraded_capabilities:
  - capability: reviewer-subagent-dispatch
    state: degraded
    note: "TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent inline persona pass. Every selected persona was applied inline with its own finding list, per the Persona Rubric Adapter. Reviewer personas are leaf executors and spawned nothing."
  - capability: agent-engram
    state: circuit-open
    note: "Indexed retrieval circuit open per operator instruction; NOT retried this session. All evidence below comes from bounded direct exact-path reads, git plumbing, and read-only backlogit MCP reads and SQL over a freshly synced index (1430 artifacts)."
  - capability: agent-intercom
    state: unavailable
    note: "No operator broadcast performed; visibility is local-only. No operator choice-presentation step was skipped, because this review presents no choice."
  - capability: graphtor-docs
    state: unavailable
    note: "No graphtor-docs tool surface was exposed to this session. Documentation questions were answered by direct reads under docs/."
backlogit_index_state: "INDEX_SYNC_OK — 1430 artifacts indexed at session start"
gate_result: FAIL
decision: BLOCKED
verdict_at_entry: null
verdict_at_entry_disposition: REMEDIATED-PENDING-REVIEW
verdict_at_entry_plan_revision: 3
remediation_authorization: none-this-cycle
remediation_revision: null
remediation_performed: false
disposition: null
p0_open: 0
p1_open: 1
p2_open: 0
p3_open: 1
hardening_required: true
hardening_present: true
hardening_sufficient: false
hardening_sufficiency_note: "requires_plan_hardening is now correctly true, and H1-H11 answer the structural and vocabulary questions the previous passes omitted. H10 asks whether the plan's token matches the emitting task's token and answers correctly. No hardening question asks where the verdict line is written or who reads it, which is finding L1: a gate output with no address is not observable, and observability is the property the hardening section claims for it."
attempt_02_findings_verified:
  - finding: "G1 — the plan and the only verdict-emitting task declare different, incompatible composed-state vocabularies"
    severity: P1
    state: closed
    evidence: "169.016-T now states it is the sole emitter and emits exactly one of STATUS_CONTRACT_NOT_OBSERVED, STATUS_CONTRACT_DIVERGENT and STATUS_CONTRACT_HELD, evaluated in that order, with the not-observed conditions enumerated first. CONTRACT_ACTIVE and CONTRACT_INCOMPLETE appear in no live record. The smaller producer/consumer seam is also closed: the plan's Producer row now says the module produces the observations and 169.016-T reads them and emits the verdict line, which is what the task record says. 169-F and 177-S both carry the same three tokens."
  - finding: "G2 — item_deps still encodes the retired T1/T2 activation chain"
    severity: P2
    state: closed
    evidence: "A full read of item_deps for 169.% returns exactly twelve edges: five RED tasks on 169.011-T, 169.015-T on all five RED tasks, 169.016-T on 169.015-T, 169.007-T on 169.016-T. All six stale edges involving archived 169.001-T, 169.002-T, 169.003-T, 169.005-T and 169.008-T are gone, including the reverse-dependency edges that made archived activation tasks appear as dependents of live RED tasks. The archived records keep their absorption provenance in prose."
  - finding: "G3 — the R5 narrowing rule conflicts with ACTIVATE's no-authoring invariant and the RED-first rule"
    severity: P2
    state: closed
    evidence: "Both the plan's 2-hour check and 169.015-T now state that narrowing in place is prohibited, that re-deriving an assertion is authoring one, that the unit halts and returns to Stage, that 169.010-T's bidirectional family is retired outright rather than narrowed because dropping the Ship pair removes the reverse half of the cross-reference, and that 169.014-T's closure assertion is re-observed red against the new expectation before activation resumes. Plan and record agree on which families are affected and on re-derive versus re-run."
  - finding: "G4 — retired phase vocabulary in one task title and one feature-description clause"
    severity: P3
    state: closed
    evidence: "169.007-T is retitled 'P-002.7 DOCS: document the contract …' and its body names the PREPARE-RED-ACTIVATE-VERIFY-DOCS order. 169-F now reads 'PHASE SHAPE - THIS UNIT'S ORDER IS PREPARE, RED, ACTIVATE, VERIFY, DOCS' and explains that D2 governs activation atomicity rather than the phase list."
  - finding: "G5 — requires_plan_hardening false on a unit touching two template families"
    severity: P3
    state: closed
    evidence: "requires_plan_hardening is true with a hardening_rationale naming the two template families and their mirrors, and the section is declared a gate rather than a completeness pass. H10 and H11 were added."
persona_coverage:
  - persona: constitution
    status: complete
    mode: inline
    findings: L1
  - persona: python
    status: complete
    mode: inline
    findings: none
  - persona: scope-boundary
    status: complete
    mode: inline
    findings: L2
  - persona: learnings
    status: complete
    mode: inline
    findings: L1
  - persona: architecture
    status: complete
    mode: inline-same-model
    findings: L1
  - persona: agent-native-parity
    status: complete
    mode: inline-same-model
    trigger: "Plan declares a gate token that an agent-facing consumer, Ship's claim sequence, and a CI workflow are both said to read as a pass condition."
    findings: L1
  - persona: security-lens
    status: complete
    mode: inline-same-model
    trigger: "Plan writes a policy clause and an agent-surface note into two installed agent/policy mirrors in a single commit, and defines the gate a claim-time consumer is said to honour."
    findings: none
tags:
  - "plan-review"
  - "defect-unit"
  - "p002-7"
  - "member-status"
  - "dag-root"
  - "portfolio-2026-09-18"
---

# Plan review attempt 03 — Post-claim member-status contract (P-002.7)

This artifact records **one thing**: an independent reviewer's verdict on plan
revision 3 as it stands at content HEAD `4b4330b9` on branch
`chore/stage-176-s-workflow-defects`. It has no Part 2. No remediation
followed it, and none was authorized.

Attempt 02's claimed closures were **independently re-derived** from the plan,
the nine live task records, the archived records, the `177-S` manifest and a
full `item_deps` read — not accepted from the remediation commit message.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-18-post-claim-member-status-contract-plan.md` |
| Reviewed revision | 3 |
| Reviewed content HEAD | `4b4330b9` (committed) |
| Verdict at entry | `null`, disposition `REMEDIATED-PENDING-REVIEW` at plan revision 3 |
| Covering feature / shipment | `169-F` / `177-S` |
| Unit role | reduced defect unit, DAG root |
| Declared surfaces | 4 |
| Governing decision | 2026-09-18 shared-execution-architecture, revision 1 |
| Dispatch mode | `single-agent-declared-degradation` |
| Terminal | yes — operator-declared terminal attempt |
| Gate result | **FAIL** |
| Decision | **BLOCKED** |

```text
dispatch_mode: single-agent-declared-degradation
decision: BLOCKED
```

## Dispatch and coverage

Reviewer subagent dispatch was unavailable, so all seven personas were applied
**inline**, each with its own finding list so coverage is auditable. No persona
was skipped, and no persona spawned a subagent — reviewer personas are leaf
executors in this workflow. Cross-model personas ran under same-model declared
degradation because `.autoharness/config.yaml` declares no `anchor_review`
route.

Both conditional personas were **triggered and ran**. Agent-Native Parity,
because the plan declares a gate token that Ship's claim sequence and a CI
workflow are both said to read as a pass condition. Security Lens, because the
unit writes a policy clause and an agent-surface note into two installed
agent and policy mirrors in one commit.

Engram indexed retrieval was circuit-open and was **not retried** per operator
instruction. Intercom and graphtor-docs were unavailable, so visibility is
local-only and documentation questions were answered by direct reads. Every
claim below cites an exact path, a backlogit record, or a `git` fact, taken
against a freshly synced index.

## Independent verification of attempt-02 closures

**G1 (P1) — divergent composed-state vocabularies. Closed.** `169.016-T`'s
record now states it is "THE SOLE EMITTER OF THE COMPOSED-STATE VERDICT LINE,
AND IT EMITS EXACTLY ONE OF THREE TOKENS - THE SAME THREE THE PLAN DECLARES",
enumerates the not-observed conditions (import raise, non-empty
`loader.errors`, any `_FailedTest`, zero executed assertions, any family with
no per-assertion record), and evaluates them **first**. `STATUS_CONTRACT_HELD`
requires an affirmative per-assertion passing record for all five families,
the surface rule resolving to exactly `declared_surface_count`, and no
never-red assertion in the suite. A search across live and archived records
returns no instance of `CONTRACT_ACTIVE` or `CONTRACT_INCOMPLETE`. `169-F` and
`177-S` both reproduce the three-token vocabulary.

The smaller seam attempt 02 flagged inside G1 is closed too: the plan's
Producer row now says the module produces the **observations** and `169.016-T`
reads them and emits the **verdict line**, and gives the reason for the split.
That matches the task record.

**G2 (P2) — stale `item_deps` edges. Closed, verified exhaustively.** A full
read of every edge touching `169.%` returns exactly twelve, and all twelve are
live:

```text
169.009-T, 169.010-T, 169.012-T, 169.013-T, 169.014-T → 169.011-T
169.015-T → all five RED tasks
169.016-T → 169.015-T
169.007-T → 169.016-T
```

All six stale edges are gone, including `169.001-T` → `169.009-T`/`169.010-T`,
which was the pair that made a reverse-dependency read of the live RED tasks
return an archived activation task as a dependent. The surviving set is
exactly the plan's stated sequence, with no archived record participating.

**G3 (P2) — the R5 narrowing rule. Closed, and closed in both documents.** The
plan's 2-hour check now says `169.015-T` stops, does not split, does not narrow
in place — "re-deriving an assertion is **authoring** one" — and returns the
shipment to **Stage** for explicit scope redesign, with `169.010-T`'s
bidirectional family **retired outright** (because dropping the Ship pair
removes the reverse half of the cross-reference, so the family disappears
rather than narrows) and `169.014-T`'s closure assertion **re-observed red**
against the new expectation before activation resumes. `169.015-T`'s record
states the same rule, with the same two families and the same retire-versus-
re-observe split. The previous plan/record disagreement over scope and over
re-run versus re-derive is gone. R5 and H9 match.

**G4 (P3) — retired phase vocabulary. Closed.** `169.007-T` is now
"P-002.7 DOCS: document the contract …" and its body names the
PREPARE → RED → ACTIVATE → VERIFY → DOCS order. `169-F` now reads "PHASE SHAPE
- THIS UNIT'S ORDER IS PREPARE, RED, ACTIVATE, VERIFY, DOCS" and explains that
D2 governs activation atomicity rather than the phase list.

**G5 (P3) — under-declared hardening flag. Closed.**
`requires_plan_hardening: true`, with a rationale naming
`templates/policies/` and `templates/agents/` plus their mirrors and declaring
the section a gate. H10 and H11 were added.

## Independent verification of plan-to-record correspondence

All nine live tasks match the plan's Tasks table on both axes: `169.011-T`
`S`/`medium`; `169.009-T`, `169.010-T`, `169.012-T` `S`/`low`; `169.013-T`
`XS`/`low`; `169.014-T` `S`/`medium`; `169.015-T` `M`/`low`; `169.016-T`
`S`/`low`; `169.007-T` `S`/`low`. Every task carries `size_source: agent` and
`size_ruleset_version: ah-stage-sizing-v1`. No task carries `complexity:
high`, and the widest is `M`/`low`, for which the plan records a 2-hour
argument and a halt-and-return-to-Stage contingency rather than a narrowing
licence.

The RED-first chain is complete and checkable. Five assertion families, five
RED tasks, one family each, each with a named discriminating near-miss
fixture; ACTIVATE adds none by its own invariant; VERIFY adds none by its own
invariant and by `169.016-T`'s pass condition, which requires that "no
assertion exists in the suite that was not observed red first". The
discriminating-RED rule requires two observations per assertion — absence and
near-miss — which is what distinguishes an assertion that tests the contract
from one that tests a file's existence. Import safety is binding and asserted
directly against `unittest.defaultTestLoader`.

Activation atomicity holds: one task, one commit, four surfaces, with the
rollback argument stated correctly (a single commit reverts as a unit; two
commits joined by an edge do not).

The four declared surfaces were verified to exist:
`templates/policies/workflow-policies.md.tmpl`,
`.github/policies/workflow-policies.md`,
`templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md`. The
exclusion rule was verified rather than accepted: `.gitignore` line 6 is
exactly `.autoharness/staging/`. The claimed **current marker count of 0** was
verified by direct search over the declared scope — `P-002.7` resolves in no
file under `templates/policies/`, `.github/policies/`, `templates/agents/` or
`.github/agents/`. The absence RED observations are therefore real, and
`STATUS_CONTRACT_DIVERGENT` is genuinely reachable today, as the plan claims.

`tests/test_p002_7_member_status_contract.py` correctly does not exist yet:
`169.009-T` creates it.

Provenance holds. `3EF5AAF2` is carried by `169-F`, `177-S` and all nine live
tasks plus the five archived ones; the phantom `3EF5AAF9` appears nowhere.

The root claim is re-confirmed empirically: `item_deps` carries no edge in
either direction for `177-S`, `depends_on_shipments` is empty, and no shipment
in the portfolio depends on `177-S`. R6's claim that root status is "checkable
against the executable records" is true.

## P0 findings

**None.**

## P1 findings (1)

**L1 — the composed-state verdict line has no declared format and no declared
destination, and its one concrete named consumer is described backwards and is
modified by no task in the unit. The gate output is unobservable.**

The plan is precise about *which* token is emitted, *by whom*, and *under what
conditions* — attempt 02's `G1` forced all three, and all three are now right.
It is silent about *where the token goes*.

**No destination.** The Composed-state check's Producer row names the test
module and the emitter; neither names an artifact the verdict line is written
to. `169.016-T` says it "emits the verdict line" and names no path. Both
sibling units in this portfolio do both things: `182-S` names
`docs/spikes/2026-09-18-autoharness-operation-transport-findings.md` "whose
final line is the verdict token", and `183-S` names its findings artifact the
same way.

**No format.** A search for `COMPOSED_STATE` across `docs/plans/` returns two
files — the two spikes, with five worked verdict-line forms between them. This
plan contains none. The emitted line has no specified shape.

**The fail-closed rule is therefore unevaluable.** The plan says:

> an **absent** verdict line is itself `STATUS_CONTRACT_NOT_OBSERVED`: a
> consumer that finds no token has observed nothing and must treat it as such,
> never as a default pass.

`R8` and `H11` restate it. Absence is only decidable relative to a place where
the token would be present. With no declared location, no consumer can
distinguish "the line is absent" from "I am looking in the wrong place", and
the unit's **most specific safety property** — the one H11 calls exactly that
— reduces to an assertion nothing can check.

**The named consumer relation is inverted, and unwired.** The Consumer row
reads:

> `.github/workflows/ci.yml` (the stdlib `unittest` suite, **which reads the
> verdict line as a gate**)

Verified against the file: `ci.yml`'s `test` job runs a `Run unittest suite`
step and consumes a process exit code. The suite is the artifact that produces
the *observations* `169.016-T` reads **before** emitting the line; it cannot
read a line that does not exist until after it has run. The stated direction is
backwards. And no task in `177-S` modifies `ci.yml` — `169.015-T`'s four
surfaces are the two policy copies and the two Ship-agent copies — so nothing
in the unit makes `ci.yml` a reader of anything.

The second named consumer is in the same position for a different reason.
Ship's claim sequence is said to "treat `STATUS_CONTRACT_HELD` as the only pass
token", but what `169.015-T` writes into the two Ship-agent surfaces is "the
intake-reconciliation note and the reverse cross-reference sentence naming the
policy clause" — not a token-consumption rule. Neither declared consumer is
delivered by this unit.

**Graded P1, not P0.** The substantive contract is sound and unchanged from
attempt 02's assessment: activation is atomic, every assertion family has a RED
owner with two observations, the surface list is rule-derived and closed at
four, the marker count is genuinely zero, and the pass condition is reachable
in substance. Nothing here makes the unit unshippable or unsafe. **Graded P1,
not P2**, on the same reasoning attempt 02 applied to `G1` and for the same
artifact: "the gate's whole purpose is to be mechanically checkable by a
consumer that reads the plan." `G1` fixed *which* token. A token with no
address, no shape, and no reader that the unit delivers is not more checkable
than a token with the wrong name — it is the same defect displaced one field
over, which is the third consecutive cycle in which this unit's gate output has
been the finding. It also engages Principle V (Structured Observability)
directly: an emitted verdict that no artifact holds and no consumer reads is
not structured observability, and the hardening section claims observability as
this unit's most specific property without ever asking where the observation
lands.

*Minimum remediation.* Three small edits, no restructuring. (1) Name the
verdict-line artifact and its position on the sibling model — for example, the
line is appended as the final line of a named evidence file under the unit's
closure-evidence path — and state the literal line forms for all three tokens.
(2) Correct the Consumer row: the `unittest` suite is the **observation
producer**, not the verdict reader; state what actually consumes the line in
this unit, or scope the row to say that wiring a CI reader and a Ship
claim-time reader is explicitly out of scope and belongs to a named successor.
(3) Reproduce the destination and the line forms in `169.016-T`, which is
where an executor will look.

*Personas:* Architecture Strategist; Constitution Reviewer (Principle V,
Structured Observability); Agent-Native Parity Reviewer; Learnings Researcher.

## P2 findings

**None.**

## P3 findings (1)

**L2 — the `177-S` and `169-F` size rollup reports fourteen members; the
manifest correctly lists nine tasks plus the covering feature.**

`custom_fields.items` for `177-S` is correct and in phase order: `169-F`,
`169.011-T`, `169.009-T`, `169.010-T`, `169.012-T`, `169.013-T`, `169.014-T`,
`169.015-T`, `169.016-T`, `169.007-T`. The computed-on-read
`size_composition` block on both `177-S` and `169-F`, however, enumerates
fourteen task members, including the five archived absorbed tasks
`169.001-T`, `169.002-T`, `169.003-T`, `169.005-T` and `169.008-T`, with a
histogram of `M`:2, `S`:10, `XS`:2.

This is a backlogit rollup derived from the covering feature's children rather
than from the shipment manifest, so it is tool behaviour rather than a plan or
manifest defect — and it is why the two sibling shipments' rollups match their
manifests exactly: neither has archived children. No plan change is required
and no remediation of the executable records is warranted.

Recorded for two reasons. A reader comparing the rollup's fourteen against the
manifest's nine, on a unit whose review history contains an archived-member
defect (`G2`) and a split-activation defect (`A1`), has no way to tell from the
rollup alone that this instance is benign. And this repository's recorded
defect history includes several cascade-close and topology-gate failures
arising specifically from archived members appearing in derived views.

*Minimum remediation.* One sentence in the `177-S` description noting that the
derived `size_composition` rollup includes the five archived absorbed tasks
while `custom_fields.items` is the authoritative member list. Nothing else.

*Personas:* Scope Boundary Auditor.

## Runtime verification and operational closure

Called out explicitly, as the gate requires.

Rollout and rollback are adequate unconditionally. PREPARE and RED are inert
and change no declared surface; the single ACTIVATE commit reverts as a unit,
returning all four surfaces to their current divergent state simultaneously;
and the guarantee holds because activation is one task in the manifest, with
the split tasks archived and their stale edges now removed.

Closure evidence remains unspecified for the unit. At attempt 02 that was
recorded as acceptable at plan stage for a declaration contract, on the
reasoning that "the composed-state verdict line is the unit's observation
surface". `L1` is the finding that the observation surface has no location, so
that acceptance no longer stands on its own: the unit's only observation
surface and its only closure-evidence candidate are the same unspecified
artifact.

## Disposition

**No remediation.** `remediation_revision` is `null`, `disposition` is `null`,
and the governing revision remains 3 — the revision reviewed and found
BLOCKED.

This plan is **not harvest-ready and not Ship-ready**. No backlog record,
source file, test, template, policy, CI definition or configuration was changed
on the strength of this review; in particular the nine live `169.x` records,
the five archived records, the `177-S` manifest, `item_deps` and the four
declared surfaces were read but **not** mutated, because changing them is
remediation and no remediation is authorized in this cycle.

**On terminality.** The operator designated attempt 03 the terminal review
cycle. Terminality is a designation of the *review* cycle, not a closure of the
*findings*: a P1 remains a P1 and this artifact records FAIL/BLOCKED on its
merits. Severity was not lowered to reach a closable state. Closing `L1`
requires either an operator-authorized bounded remediation cycle followed by an
independent attempt 04 — which requires the operator to lift the terminal
designation — or an explicit, recorded operator waiver accepting `L1` as a
known defect. `L2` is advisory and may be carried. Neither disposition is a
decision this reviewer may take.
