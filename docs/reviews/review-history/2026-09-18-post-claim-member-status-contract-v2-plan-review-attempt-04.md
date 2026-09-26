---
title: "Plan review attempt 04 — Post-claim member-status contract (P-002.7)"
description: "Immutable per-attempt plan-review artifact recording the fourth and operator-designated terminal independent review of docs/plans/2026-09-18-post-claim-member-status-contract-plan.md at revision 4, against reviewed content HEAD 42f2f8ec. Gate result FAIL; decision BLOCKED on zero P0, one P1, zero P2 and three P3 deduplicated findings. Attempt 03's P1 is independently re-derived closed: the composed-state verdict line now has one declared destination at .autoharness/gates/p002-7-status-contract-verdict.txt, verified gitignored, three literal line forms, a sole writer, an atomic whole-file-replace rule, a closed absence vocabulary and an exit-code consumer contract, and the false CI consumer is corrected in the right direction against the verified ci.yml test job. The new P1 is that the plan's rollout phase order contradicts the binding decision's D2 rollout invariant without recording the deviation: D2 states PREPARE then VERIFY then ACTIVATE with the complete evidence set produced before any activation, while the plan declares PREPARE then RED then ACTIVATE then VERIFY then DOCS and places its sole gate emitter after the commit that mutates all four declared surfaces. Every other plan in the portfolio follows D2's ordering, and the unit cites D2 by name for its atomicity rule while dropping the ordering rule from the same section. Because this is the terminal attempt, the finding is halted for operator disposition rather than remediated. Dispatch ran in single-agent declared degradation with all seven personas covered inline; engram was circuit-open and not retried, intercom and graphtor-docs were unavailable."
doc_type: review
source: docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-04.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 4
attempt_range: "04"
attempt_conformance: conforming
review_terminal: true
terminal_designation: operator-declared
terminal_disposition: TERMINAL-BLOCKED
verdict_manifest: docs/reviews/2026-09-18-post-claim-member-status-contract-v2-plan-review.md
supersedes: null
predecessor_artifact: docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-03.md
plan_path: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
plan_id: post-claim-member-status-contract-v2
reviewed_revision: 4
reviewed_content_head: 42f2f8ec
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
review_cycle: 4
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
    note: "Indexed retrieval circuit open per operator instruction; NOT retried this session. All evidence below comes from bounded direct exact-path reads, git plumbing, and read-only backlogit MCP reads over a freshly synced index (1430 artifacts)."
  - capability: agent-intercom
    state: unavailable
    note: "No operator broadcast performed; visibility is local-only. The blocking finding is surfaced in the session return and in the mutable verdict manifest instead."
  - capability: graphtor-docs
    state: unavailable
    note: "No graphtor-docs tool surface was exposed to this session. Documentation questions were answered by direct reads under docs/."
backlogit_index_state: "INDEX_SYNC_OK — 1430 artifacts indexed at session start"
gate_result: FAIL
decision: BLOCKED
verdict_at_entry: null
verdict_at_entry_disposition: REMEDIATED-PENDING-REVIEW
verdict_at_entry_plan_revision: 4
remediation_authorization: none-this-cycle
remediation_revision: null
remediation_performed: false
remediation_cycle_proposed: false
disposition: HALTED-FOR-OPERATOR-DISPOSITION
p0_open: 0
p1_open: 1
p2_open: 0
p3_open: 3
open_findings: [M1, M2, M3, M4]
blocking_findings: [M1]
hardening_required: true
hardening_present: true
hardening_sufficient: false
hardening_sufficiency_note: "The hardening pass carries H1-H11, H15 and H16 and is substantively thorough on the unit's internal coherence. It is insufficient in one respect and that insufficiency is the blocking finding: the section explicitly exists because 'a plan invariant and its own manifest were previously able to contradict each other', yet no question asks whether the plan's rollout ordering conforms to the binding decision that governs it. H6 defends one-task-one-commit by citing D2's atomicity rule while the same D2 section's ordering rule is not addressed anywhere."
attempt_03_findings_verified:
  - finding: "L1 — the composed-state verdict line has no declared destination artifact and no declared line format, and the one named consumer, .github/workflows/ci.yml, is described with an inverted relation and is modified by no task"
    severity: P1
    state: closed
    evidence: "The plan carries a ## Verdict artifact and line format section. Destination: exactly one path, .autoharness/gates/p002-7-status-contract-verdict.txt, verified gitignored by git check-ignore -v, which resolves to .gitignore:7 (.autoharness/gates/) - so the verdict is never committed and cannot leave the tree dirty. Format: exactly one line, one of three literal forms, prefix COMPOSED_STATE: with the token as first field and fields separated by pipe-space, with closed vocabularies for reason= and divergence=. Ownership: 169.016-T is sole writer; the write is atomic via same-directory temp file plus rename; each run replaces the whole file and never appends. Absence: a closed six-item list - missing, unreadable, empty, no COMPOSED_STATE line, more than one such line, unrecognised token - all resolve to STATUS_CONTRACT_NOT_OBSERVED. Exit code: zero only on STATUS_CONTRACT_HELD. The CI direction is corrected and independently verified: .github/workflows/ci.yml line 112 runs PYTHONPATH=src python -m unittest discover -s tests and consumes an exit code, and the plan, 169.016-T, 169.007-T and the 177-S description all now name it a producer and explicitly not a consumer, with no task in the unit modifying it. The same contract is reproduced verbatim across the plan, 169.016-T, 169.007-T and 177-S."
  - finding: "L2 — the tool-derived size_composition rollup counts archived absorbed tasks"
    severity: P3
    state: open-unchanged
    evidence: "177-S size_composition.members still reports fourteen entries including the five archived absorbed tasks 169.001-T, 169.002-T, 169.003-T, 169.005-T and 169.008-T, while custom_fields.items correctly lists nine tasks plus the covering feature 169-F. The archived records themselves were verified to carry no live item_deps edges, so the executable graph is correct and only the tool-derived rollup is affected. Recorded as advisory and explicitly not addressed in the revision-4 cycle. Carried forward unchanged as M4."
persona_coverage:
  - persona: constitution
    status: complete
    mode: inline
    findings: none
  - persona: python
    status: complete
    mode: inline
    findings: none
  - persona: scope-boundary
    status: complete
    mode: inline
    findings: M3
  - persona: learnings
    status: complete
    mode: inline
    findings: M1
  - persona: architecture
    status: complete
    mode: inline-same-model
    findings: M1, M2
  - persona: agent-native-parity
    status: complete
    mode: inline-same-model
    trigger: "Plan defines a machine-written verdict artifact with a literal line format, a sole-writer atomicity rule, a closed absence vocabulary and an exit-code gate an agent evaluates."
    findings: M2
  - persona: security-lens
    status: complete
    mode: inline-same-model
    trigger: "Plan writes a generated verdict artifact into .autoharness/ and mutates two policy and two agent declaration surfaces including the Ship claim sequence."
    findings: none
tags:
  - "plan-review"
  - "defect-unit"
  - "p002-7"
  - "member-status"
  - "dag-root"
  - "portfolio-2026-09-18"
---

# Plan review attempt 04 — Post-claim member-status contract (P-002.7)

Attempt 03's findings were **independently re-derived from plan, task, feature
and shipment records and from the repository itself**. No closure summary was
trusted. One new P1 was found that attempts 01–03 did not raise.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-18-post-claim-member-status-contract-plan.md` |
| Reviewed revision | 4 |
| Reviewed content HEAD | `42f2f8ec` (committed) |
| Verdict at entry | `null`, disposition `REMEDIATED-PENDING-REVIEW` at plan revision 4 |
| Covering feature / shipment | `169-F` / `177-S` |
| Unit role | reduced defect unit, DAG root |
| Governing decision | 2026-09-18 shared-execution-architecture, revision 1 |
| Dispatch mode | `single-agent-declared-degradation` |
| Terminal | yes — operator-declared terminal attempt 04 |
| Gate result | **FAIL** |
| Decision | **BLOCKED** |

## Dispatch and coverage

All seven personas were applied inline, each with its own finding list.
Reviewer personas are leaf executors and spawned nothing. Engram remained
circuit-open and was not retried; intercom and graphtor-docs were unavailable,
so operator visibility was local-only.

## Independent verification of attempt-03's P1 closure

**`L1` — closed, on every sub-claim, verified against the repository rather
than against the plan's assertion about the repository.**

| Sub-claim | Verification |
|---|---|
| Exact path declared | `.autoharness/gates/p002-7-status-contract-verdict.txt`, stated identically in the plan, `169.016-T`, `169.007-T` and the `177-S` description |
| Path is gitignored | `git check-ignore -v` resolves it to `.gitignore:7` → `.autoharness/gates/`. The claim is true, so "never committed, never leaves the tree dirty" holds |
| Literal whole-file line format | Three forms, prefix `COMPOSED_STATE: `, token as first field, ` \| ` separators, closed `reason=` and `divergence=` vocabularies, multi-surface `DIVERGENT` repeats `surface=` on the one line |
| Atomic ownership | `169.016-T` is sole writer; same-directory temp file plus rename; whole-file replace; never appended; exactly one `COMPOSED_STATE:` line at all times |
| Absence semantics | Closed six-item list — missing, unreadable, empty, no `COMPOSED_STATE:` line, more than one such line, unrecognised token — all resolve to `STATUS_CONTRACT_NOT_OBSERVED` |
| Exit-code consumer contract | `169.016-T` exits zero **only** on `STATUS_CONTRACT_HELD`; non-zero on `DIVERGENT` and `NOT_OBSERVED`; exit code and artifact carry the same verdict because one step produces both |

**The false CI consumer is closed, and closed in the correct direction.**
`.github/workflows/ci.yml` line 112 was read directly: the `test` job runs
`PYTHONPATH=src python -m unittest discover -s tests`. It consumes an exit code
and *produces* the observations the verdict is derived from — the reverse of a
verdict-line consumer. The plan, `169.016-T`, `169.007-T` and the `177-S`
description now all state this, and no task in the unit modifies `ci.yml`. The
only remaining declared consumer of contract *text* is Ship's claim sequence at
`.github/agents/_ship.agent.md` item 4, correctly distinguished from a gate
consumer.

**The three-state vocabulary is coherent and the ordering is load-bearing.**
`169.016-T` is the sole emitter; `STATUS_CONTRACT_NOT_OBSERVED` is evaluated
first and absorbs import failure, `loader.errors`, `_FailedTest` placeholders,
zero executed assertions, a family with no per-assertion record and an absent
verdict line; `STATUS_CONTRACT_HELD` requires an affirmative per-assertion
passing record for all five families. A green aggregate exit cannot reach the
pass token. The plan's `H10`/`H11` and the task record reproduce this verbatim.

## Independent verification of plan-to-record correspondence

* Sizing and complexity match the plan's Tasks table on all nine tasks
  (`169.011-T` S/medium; `169.009-T`, `169.010-T`, `169.012-T` S/low;
  `169.013-T` XS/low; `169.014-T` S/medium; `169.015-T` M/low; `169.016-T`
  S/low; `169.007-T` S/low), each with `size_source: agent` and a non-empty
  `size_ruleset_version`.
* `item_deps` encodes exactly one topology: `169.011-T` → the five RED tasks →
  `169.015-T` → `169.016-T` → `169.007-T`. The five archived absorbed tasks
  carry **no** live edges, so attempt 02's `G2` remains closed.
* `177-S` manifest order is phase order and leads with `169-F`; nine tasks plus
  the covering feature.
* `declared_surface_count: 4` matches the four enumerated paths, and the
  `P-002.7` marker count in the declared search scope
  (`templates/policies/`, `.github/policies/`, `templates/agents/`,
  `.github/agents/`) was independently counted as **0**, which is what makes
  the absence RED observations real.
* Every assertion family in the Assertion-to-task map has exactly one RED owner
  and a named discriminating near-miss fixture; `169.016-T` introduces none.
* Source ID provenance: `3EF5AAF2` is carried by every live executable record.
  `3EF5AAF9` survives only as an explicit historical narrative reference in
  `169-F`, the decision's `F10`, this plan's root section and a memory record,
  each naming it as the closed phantom ID. Attempt-08 `B1` remains closed.
* `177-S` is a DAG root: `depends_on_shipments` is empty and no shipment in the
  queued set carries an edge to or from it.
* The superseded revision-7 plan carries `plan_role: superseded` and
  `superseded_by` pointing at this plan. Every cross-referenced path resolves.

## P0 findings

None.

## P1 findings (1)

### `M1` — the plan's rollout phase order contradicts the binding decision's `D2` rollout invariant, and the deviation is nowhere recorded

**What the binding decision says.** `D2` of
`docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md`
(revision 1) is titled *"The rollout invariant is PREPARE → VERIFY →
ACTIVATE"* and opens: **"Every contract in this portfolio rolls out in three
phases."** It then defines them:

* **PREPARE** — author the implementation and its tests **inert**. "Tests go
  RED first, then GREEN, entirely within the inert surface."
* **VERIFY** — "produce the complete evidence set **before any activation**:
  RED evidence …, GREEN evidence (the same assertions observed passing), and
  compatibility evidence … VERIFY produces an evidence record; it changes no
  behaviour."
* **ACTIVATE** — "one task, one commit", flipping every surface simultaneously.

**What the plan says.** The *Rollout* section declares **PREPARE → RED →
ACTIVATE → VERIFY → DOCS**, and the Tasks table and `item_deps` implement it:
`169.015-T` (ACTIVATE) precedes `169.016-T` (VERIFY). VERIFY is placed *after*
activation — the reverse of the invariant.

**This is not a portfolio convention.** Every other plan in the portfolio uses
`D2`'s ordering — `branch-ensure-operation`, `checkpoint-authority`,
`operation-substrate-transport`, `p004-observation-gate`,
`review-authority-foundation`, `safe-close-conformance`,
`safe-operation-primitives` and `ship-harness-lifecycle-foundation`, eight of
eight. `177-S` is the sole outlier.

**The deviation is selective, not accidental.** The plan cites the decision's
`F7`, `F10`, `D6` and `R5` by clause. `169.015-T`'s record cites **`D2` by
name** — "ACTIVATE PHASE - ONE TASK, ONE COMMIT, ALL FOUR DECLARED SURFACES
(decision D2)". So `D2`'s atomicity rule is adopted while the ordering rule
stated in the same section, two paragraphs above it, is dropped. Neither the
plan, its hardening section (`H1`–`H11`, `H15`, `H16`), its risks (`R1`–`R8`),
`169-F`, the `177-S` description nor any of the nine task records mentions
`D2`'s ordering, argues that it does not apply, or records a deviation.

**The consequence is material, not cosmetic.** `169.016-T` is the unit's **sole
gate emitter**. Under the plan's ordering, the single ACTIVATE commit mutates
and lands all four declared surfaces — two authoritative templates and two
installed mirrors, including the Ship agent's claim sequence — **before any
verdict exists**. A `STATUS_CONTRACT_DIVERGENT` or
`STATUS_CONTRACT_NOT_OBSERVED` verdict is then reachable only by reverting a
landed commit. `D2`'s ordering exists precisely to make activation the last
step after a complete evidence set, so the plan relocates the gate to the far
side of the mutation `D2` positions it to guard.

**A conformant framing was available, so the deviation is not compelled.** The
unit already authors inert test-owned data and near-miss fixtures in
`169.011-T`, and the discriminating-RED rule already runs assertions against
those fixtures. GREEN is therefore observable against the canonical definition
*as inert fixture data* before any declared surface changes — which is exactly
`D2`'s "tests go RED first, then GREEN, entirely within the inert surface". The
plan never considers this, so the reviewer cannot close the finding on
reasoning the artifact does not contain.

**Why P1 and not P2.** A governing plan and the binding decision that governs
it assert incompatible orderings for the same unit, unreconciled, on the one
unit that is a DAG root and therefore the first thing Ship would execute. That
leaves Ship choosing between two authorities on when its gate runs relative to
its only irreversible commit. This is the same defect class attempts 01–03
graded P1 throughout this portfolio — `F1`, `G1`, `J1`, `K1` and `L1` were each
an unreconciled contradiction between a plan and the records or authorities
around it — and it is not lowered here to reach a closable state.

**Note on `P-004`.** `P-004` (Red Phase Before Implementation) is satisfied by
the plan and is *not* in tension with `D2`: `D2` already sequences RED before
GREEN inside PREPARE. `P-004` therefore does not license the reordering, and no
policy in `.github/policies/workflow-policies.md` was found that overrides a
binding decision's rollout invariant.

## P2 findings

None.

## P3 findings (3)

### `M2` — the Tasks table entry for `169.016-T` omits its verdict-emitting role

The Tasks table describes `169.016-T` as "Observe every RED assertion passing
against the shipped text; add no assertion", phase VERIFY. The *Composed-state
check* makes the same task the sole emitter of the verdict line, the sole
writer of the verdict artifact and the authoritative gate evaluator by exit
code. The task record carries both roles; the Tasks table carries only the
first. A reader sizing the task from the Tasks table alone would under-scope
it. Advisory.

### `M3` — the marker-provenance sentence overstates where `P-002.7` appears

*Declared surfaces* states that `P-002.7` "appears only in this plan, its
review artifacts and the deliberation record". It also appears in `169-F`,
`177-S` and nine `169.x` backlog task records. The load-bearing claim — "`P-002.7`
appears in no file in the search scope today", count **0** — was independently
verified true, and backlog records are outside the declared search scope, so
nothing in the contract or the assertions depends on the overstatement.
Advisory.

### `M4` — the `size_composition` rollup still counts five archived absorbed tasks (carried forward from `L2`)

`177-S` and `169-F` report fourteen `size_composition.members` including
`169.001-T`, `169.002-T`, `169.003-T`, `169.005-T` and `169.008-T`, while
`custom_fields.items` correctly lists nine tasks plus the covering feature. The
archived records carry no live `item_deps` edges, so the executable graph is
correct and only the tool-derived rollup is affected. Unchanged since attempt
03, where it was recorded as advisory and explicitly not addressed. Advisory.

## Runtime verification and operational closure

Nothing in this unit was executed. No test module was created or run, no
declared surface was touched, no verdict artifact was written. The review
performed no build, no test run and no linting, and created, claimed and closed
no shipment.

## Disposition

Gate result **FAIL**; decision **BLOCKED**. Zero P0, one P1, zero P2, three P3.

Attempt 04 is the operator-designated terminal attempt. **No remediation was
performed and no further remediation cycle is proposed or executed.** `M1` is
an in-scope P1 and is **halted for operator disposition**: the operator decides
whether to authorize a further remediation cycle, to record an explicit waiver
reconciling the plan with `D2`, or to amend `D2` itself. Until one of those
happens, `177-S` is **not harvest-ready and not Ship-ready**.

`M2`, `M3` and `M4` are advisory follow-up candidates and are not blocking.

No severity was lowered to force a closure and none was raised to force a
block. `L1` was closed on independently re-derived repository evidence, not on
a closure summary, and `M1` was derived independently rather than inherited
from any prior attempt.
