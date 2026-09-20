---
title: "Plan review attempt 05 — Conformance isolation spike (S2)"
description: "Immutable per-attempt plan-review artifact recording the fifth and operator-designated terminal independent review of docs/plans/2026-09-18-conformance-isolation-spike-plan.md at revision 5, against reviewed content HEAD 24e19050. Gate result ADVISORY; decision ADVISORY on zero P0, zero P1, one P2 and three P3 deduplicated findings. Attempt 04's open P2 K3 is independently re-derived CLOSED: branch cleanup is now an executable limb of the final predicate rather than a prose claim, with a sole writer, a sole evaluator, a six-check cleanup predicate whose first limb independently re-observes the branch tip, a fifth composed state ISOLATION_CLEANUP_FAILED carrying its own verdict line form and closed reason vocabulary, a declared precedence making state resolution a total function over the five states, and a per-state successor-eligibility row that blocks 181-S harvest outright. Attempt 04's P3 K4 is independently re-derived CLOSED on the rewritten four-check enumeration, on re-derivation and not on its stash capture; K5 and K6 are carried open and unaddressed. One new P2 L1 is raised: the cleanup evidence block is mandated to be written in the same commit that removes the workflow while two of its eight lines carry values that commit's own creation defines, so a spec-conformant first emission is impossible and at least one spurious CLEANUP_FAILED cycle is forced. One new P3 L2 is raised: the C6 reason token WORKFLOW_PRESENT_AT_TIP is also raised on a dirty working tree, so a verdict line can assert the workflow is present at the tip when it is absent. Dispatch ran in single-agent declared degradation with all seven personas covered inline; engram was circuit-open and not retried, intercom and graphtor-docs were unavailable. No remediation was performed and no remediation cycle is proposed."
doc_type: review
source: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-05.md
date: 2026-09-19
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 5
attempt_range: "05"
attempt_conformance: conforming
review_terminal: true
terminal_designation: operator-declared
terminal_disposition: TERMINAL-ADVISORY
verdict_manifest: docs/reviews/2026-09-18-conformance-isolation-spike-plan-review.md
supersedes: null
predecessor_artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-04.md
plan_path: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
plan_id: conformance-isolation-spike
reviewed_revision: 5
reviewed_content_head: 24e19050
reviewed_content_state: committed
reviewed_branch: chore/stage-176-s-workflow-defects
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 7F9CB5E9
feature_id: 177-F
shipment_id: 183-S
unit_role: precursor-spike
dag_role: root
external_tracker: 002-C
external_tracker_state: blocked-outside-shipment
review_cycle: 5
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
    note: "Indexed retrieval circuit open per operator instruction; NOT retried this session. All evidence below comes from bounded direct exact-path reads, git plumbing, and read-only backlogit MCP reads over a freshly synced index (1434 artifacts)."
  - capability: agent-intercom
    state: unavailable
    note: "No operator broadcast performed; visibility is local-only. No operator choice-presentation step was skipped, because this review presents no choice."
  - capability: graphtor-docs
    state: unavailable
    note: "No graphtor-docs tool surface was exposed to this session. Documentation questions were answered by direct reads under docs/."
backlogit_index_state: "INDEX_SYNC_OK — 1434 artifacts indexed at session start"
gate_result: ADVISORY
decision: ADVISORY
verdict_at_entry: null
verdict_at_entry_disposition: REMEDIATED-PENDING-REVIEW
verdict_at_entry_plan_revision: 5
remediation_authorization: none-this-cycle
remediation_revision: null
remediation_performed: false
disposition: null
p0_open: 0
p1_open: 0
p2_open: 1
p3_open: 3
open_findings: [L1, K5, K6, L2]
findings_closed_at_this_attempt: [K3, K4]
findings_raised_at_this_attempt: [L1, L2]
hardening_required: true
hardening_present: true
hardening_sufficient: false
hardening_sufficiency_note: "The hardening pass carries H1-H15, and H15 now answers the branch-cleanliness question as a predicate rather than a claim, which is what closes K3. It is nevertheless recorded insufficient at this attempt: no hardening question asks whether a fixed-shape evidence block's declared write point can supply the values that block's own fields require, which is exactly the seam L1 occupies. H15 asserts the cleanup evidence is producible without deriving that it is."
attempt_04_findings_verified:
  - finding: "K3 — the branch-cleanliness check 177.006-T's record mandates has no expressible verdict: the composed-state vocabulary is defined exhaustively over the seven-entry coverage ledger, in which branch state appears nowhere, so an all-DETERMINED ledger on a branch still carrying the probe workflow forces the pass state and no token can express an unclosed spike"
    severity: P2
    state: closed
    evidence: "Revision 5 makes cleanup a conjunct of the final predicate rather than a ledger function. ISOLATION_CHARACTERIZED now requires all seven ledger rows DETERMINED AND cleanup resolved CLEANUP_PROVEN, and the plan, 177.003-T, 177.006-T, 177-F and the 183-S description all carry that conjunction. The final state is therefore not ledger-only. The cleanup predicate is six checks; C6 is evaluated FIRST and re-observes the branch tip directly - git ls-files --error-unmatch on the exact path exiting non-zero plus an empty git status --porcelain - and the plan states explicitly that the task does NOT take this from CLEANUP_TIP_OBSERVATION, so the executable predicate input is an independent observation and not the artifact's own word. Creation, dispatch and removal evidence are separately checked for internal consistency against the repository by C2, C3 and C4, including that the removal commit deletes exactly that path and is a descendant of the creation commit. A fifth state ISOLATION_CLEANUP_FAILED exists with its own verdict line form and a five-token closed reason vocabulary. Precedence is declared 1 ISOLATION_NOT_OBSERVED, 2 ISOLATION_UNDETERMINED, 3 ISOLATION_CLEANUP_FAILED, 4 ISOLATION_FLOOR_ONLY, 5 ISOLATION_CHARACTERIZED, emit-first-match, which was re-derived total and deterministic by case analysis over row states {DETERMINED, FLOOR_INVOKED, ABSENT} crossed with cleanup {PROVEN, FAILED}. Cleanup sits above BOTH harvest-eligible states, so no harvest-eligible state is reachable while cleanup is absent, malformed, inconsistent or the exact path remains at the tip. Absence of the whole block resolves to CLEANUP_FAILED | cleanup=EVIDENCE_MISSING and explicitly never to ISOLATION_NOT_OBSERVED. Successor eligibility is stated per state and 181-S reads only the composed-state token. I1 gating, the no-credential/no-secret evidence rule, no-network-after-acquisition and the rollback path were each re-read and are intact and reachable; the cleanup check is local, offline and credential-free and does not interact with them."
  - finding: "K4 — the plan describes 177.006-T's transition as mechanical in two checks while 177.006-T's own record mandates a third, so the enumeration and the record disagree on how many checks the gate performs"
    severity: P3
    state: closed
    evidence: "Revision 5 rewrites the enumeration to four checks in a stated order - 1 Coverage, 2 Evidence, 3 I1 gate, 4 Cleanup - and 177.006-T's record now reads FOUR CHECKS, IN ORDER with the same four subjects in the same order. No two-check or three-check text remains anywhere in the plan. Closed on independent re-derivation from the plan text and the task record only. The P3 stash capture 5E45691A is expressly NOT treated as closure, and that entry's own NOTE FOR THE FUTURE REVIEWER disclaims closure."
  - finding: "K5 — the ISOLATION_FLOOR_ONLY verdict-line form printed in the plan and the form 177.004-T's record mandates differ in the separator inside the verdict field"
    severity: P3
    state: open
    evidence: "Independently re-verified unchanged at revision 5. The plan prints verdict=NOT DETERMINED — FLOOR INVOKED with an em dash; 177.004-T's record prints verdict=NOT DETERMINED - FLOOR INVOKED with a hyphen-minus. A byte-comparing consumer distinguishes them. Carried, not invalidated."
  - finding: "K6 — the plan does not record that I2's evidence is observed in a job that performs no acquisition, so the after-acquisition relation is task-level across two hosted-runner jobs rather than in-job"
    severity: P3
    state: open
    evidence: "Independently re-verified unchanged at revision 5. The no-network-after-acquisition invariant remains stated at the unit level; the plan still does not note that 177.001-T observes I2 in a job that acquires nothing, so the temporal relation the invariant names holds across jobs rather than inside one. Carried, not invalidated."
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
    findings: none
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
    trigger: "Plan defines a fixed-shape machine-written evidence block, a six-check machine-evaluated cleanup predicate, a five-state composed vocabulary with declared precedence, and a successor-eligibility table a successor agent reads at 181-S harvest time."
    findings: L1, L2, K5
  - persona: security-lens
    status: complete
    mode: inline-same-model
    trigger: "Plan defines credential-absence determination, untrusted external asset acquisition, adversarial containment probing, egress denial, and the removal of a committed CI surface that runs on hosted runners."
    findings: K6
tags:
  - "plan-review"
  - "spike"
  - "ci-isolation"
  - "supply-chain"
  - "safe-close"
  - "portfolio-2026-09-18"
---

# Plan review attempt 05 — Conformance isolation spike (S2)

Attempt 04's four findings were **independently re-derived from the plan, the
six `177.x` task records, `177-F`, the `183-S` shipment record, `item_deps`,
the governing decision and the working tree**. No closure summary was trusted,
and the three P3 follow-up stash entries were read only to verify capture.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` |
| Reviewed revision | 5 |
| Reviewed content HEAD | `24e19050` (committed) |
| Verdict at entry | `null`, disposition `REMEDIATED-PENDING-REVIEW` at plan revision 5 |
| Covering feature / shipment | `177-F` / `183-S` |
| Unit role | precursor spike, DAG root |
| External tracker | `002-C`, `blocked`, outside every manifest |
| Governing decision | 2026-09-18 shared-execution-architecture, revision 1 |
| Dispatch mode | `single-agent-declared-degradation` |
| Terminal | yes — operator-declared terminal attempt 05 |
| Gate result | **ADVISORY** |
| Decision | **ADVISORY** |

## Dispatch and coverage

All seven personas were applied inline, each with its own finding list.
Reviewer personas are leaf executors and spawned nothing. Engram remained
circuit-open and was **not** retried; intercom and graphtor-docs were
unavailable, so operator visibility was local-only. No remediation was
performed and none is proposed.

## `K3` is closed — cleanup is a predicate, not a claim

### The final state is not ledger-only

Through revision 4 the five — then four — composed states were defined
exhaustively as a function of the seven-entry coverage ledger. Revision 5
breaks that by conjunction:

> `ISOLATION_CHARACTERIZED` — all seven ledger rows `DETERMINED` **and**
> cleanup resolved `CLEANUP_PROVEN`.

The conjunction appears in the plan's *Composed-state check*, in
`177.006-T`'s record, in `177-F`, and in the `183-S` description. An
all-`DETERMINED` ledger on a branch still carrying the probe workflow can no
longer force the pass state, because the pass state now has a second conjunct
the ledger does not supply.

### The executable predicate inputs are observations, not assertions

`C6` is evaluated **first**, and the plan states the reason: it is the only
limb that does not depend on the artifact's own word.

| Limb | Input | Independent of the artifact? |
|---|---|---|
| `C6` | `git ls-files --error-unmatch <exact path>` exits non-zero **and** `git status --porcelain` is empty | **yes** — the plan states `177.006-T` does *not* take this from `CLEANUP_TIP_OBSERVATION` |
| `C2` | the named creation commit **adds exactly that path** and adds or modifies no other workflow file | yes — checked against the repository |
| `C3` | exactly four `CLEANUP_DISPATCH:` lines whose input fields are exactly the declared set, each with non-empty `run_id` and `url` | internal consistency |
| `C4` | the named removal commit **deletes exactly that path** and is a **descendant** of the `C2` commit | yes — checked against the repository |

So creation, dispatch and removal evidence are checked for internal
consistency *and* against the repository, and the branch-tip fact is
re-observed rather than transcribed. `K3`'s complaint — that the check was a
claim — no longer holds.

### Precedence is one total, deterministic relation over five states

Declared order, emit-first-match:

```text
1  ISOLATION_NOT_OBSERVED
2  ISOLATION_UNDETERMINED
3  ISOLATION_CLEANUP_FAILED
4  ISOLATION_FLOOR_ONLY
5  ISOLATION_CHARACTERIZED
```

I re-derived totality by case analysis over row states
`{DETERMINED, FLOOR_INVOKED, ABSENT}` crossed with cleanup
`{PROVEN, FAILED}`. Every input maps to exactly one state; no input maps to
none, and the emit-first-match rule makes the map single-valued even where two
conditions hold. The relation is total and deterministic.

**No harvest-eligible state can appear while cleanup is unproven.** State 3
sits **above both** harvest-eligible states — `ISOLATION_FLOOR_ONLY` (floor-only
harvest) and `ISOLATION_CHARACTERIZED` (full harvest). The only state above 3
that is not itself a cleanup verdict is `ISOLATION_UNDETERMINED`, which blocks
harvest outright; a dirty branch with an `ABSENT` row therefore emits
`ISOLATION_UNDETERMINED` and masks the *reason*, but it does not leak
eligibility. I checked the masking case to the end: the
`ISOLATION_UNDETERMINED` waiver path resolves `ABSENT` rows only and still
requires `177.006-T` to be re-run, which then reaches the cleanup limb and
emits `ISOLATION_CLEANUP_FAILED`. **Not a leak.**

### The evidence block, writer, evaluator and vocabularies agree everywhere

Re-derived across the plan, `177.003-T`, `177.006-T`, `177.004-T`, `177-F` and
the `183-S` description:

* exactly eight lines, in the declared order, each at column zero, with the
  literal prefixes shown;
* **sole writer** `177.003-T`; **sole evaluator** `177.006-T`; `181-S` reads
  neither the block nor its checks and reads only the composed-state token;
* `C1`–`C6` semantics identical on every surface, including the first-failure
  order `C6, C1, C2, C3, C4, C5`;
* five-token reason vocabulary — `WORKFLOW_PRESENT_AT_TIP`,
  `TIP_UNOBSERVABLE`, `EVIDENCE_MISSING`, `EVIDENCE_MALFORMED`,
  `EVIDENCE_INCONSISTENT` — closed and identical;
* **absence of the whole block is `CLEANUP_FAILED | cleanup=EVIDENCE_MISSING`,
  never `ISOLATION_NOT_OBSERVED`**, stated in the plan and the evaluator's
  record;
* successor eligibility stated per state, with `181-S` blocked outright on
  states 1, 2 and 3;
* the block carries paths, commit identities, run identifiers and URLs only —
  no environment-variable value, token, key fragment or credential content,
  which is the same binding evidence rule `R6` applies to the I1 inventory.

### The safety envelope is intact and reachable

Re-read directly, not inferred: the `I1_GATE` predicate, its OPEN/CLOSED
totality, both gated tasks' first-action reads, the no-credential/no-secret
evidence rule, the no-network-after-acquisition invariant and the rollback path
are all unchanged by revision 5 and all reachable. The cleanup check is local,
offline and credential-free, so it neither weakens nor interacts with `I1`.

**`K3` is closed.**

## `K4` is closed — on re-derivation, not on its stash capture

The plan now reads: `177.006-T` performs the transition mechanically, **in four
checks**, in this order — 1 Coverage, 2 Evidence, 3 I1 gate, 4 Cleanup.
`177.006-T`'s record reads **FOUR CHECKS, IN ORDER** with the same four
subjects in the same order. No two-check or three-check text survives anywhere
in the plan.

This closure rests on the plan text and the task record alone. The P3 follow-up
stash entry `5E45691A` is **not** treated as closure, and that entry's own
*NOTE FOR THE FUTURE REVIEWER* explicitly disclaims closure. No severity was
lowered and no count decremented to reach this result.

## `K5` and `K6` are carried

Both were independently re-verified and neither is invalidated.

* **`K5` (P3)** — the plan prints `verdict=NOT DETERMINED — FLOOR INVOKED`
  (em dash); `177.004-T` prints `verdict=NOT DETERMINED - FLOOR INVOKED`
  (hyphen-minus). A byte-comparing consumer distinguishes them.
* **`K6` (P3)** — the plan still does not record that `I2`'s evidence is
  observed in a job (`177.001-T`) that performs no acquisition, so the
  "after acquisition" relation is task-level across two hosted-runner jobs.

## New finding `L1` (P2) — the cleanup block cannot be written where it is mandated to be written

**Both surfaces agree on an instruction that cannot be followed.**

The plan:

> `177.003-T` is the **sole writer** of this block and writes it into
> `docs/spikes/2026-09-18-conformance-isolation-findings.md` **in the same
> commit that removes the workflow**.

`177.003-T`'s record:

> THIS TASK IS THE SOLE WRITER of the cleanup evidence block and writes it **IN
> THE SAME COMMIT** that removes the workflow.

Two of the block's eight lines carry values that only exist **after** that
commit is created:

| Line | Value required | Available when? |
|---|---|---|
| `CLEANUP_REMOVED_COMMIT: <40-lowercase-hex>` | the record annotates it "(this task's removal commit)" | only after the removal commit exists — a commit's content cannot contain its own SHA |
| `CLEANUP_TIP_OBSERVATION: WORKFLOW_ABSENT \| tip=<40-lowercase-hex> \| porcelain_empty=yes` | the record requires "a `git status --porcelain` observation showing the working tree **clean**" and a tip SHA | only after the removal commit exists — the tree is dirty until it is committed, and the tip is that commit |

A commit's identity is a function of its content, so a commit whose content
names its own SHA is not constructible. A `porcelain_empty=yes` observation
likewise cannot be made from inside the staged change that makes the tree
clean. **The declared write point and the declared field contents are mutually
unsatisfiable**, so no spec-conformant first emission of the block exists.

**This is not a plan-to-record divergence.** The plan and the record state the
same impossible mandate. It is an internal contradiction in the predicate's own
input contract — the same class as `K3`, one layer in.

**Consequence, derived rather than assumed.** `C6` would pass (the path *is*
absent at the tip after the removal commit). `C1`–`C3` would pass. `C4` and
`C5` cannot be satisfied by a conformant first emission, so cleanup resolves
`CLEANUP_FAILED | cleanup=EVIDENCE_MISSING` or `EVIDENCE_MALFORMED`, the unit
composes to `ISOLATION_CLEANUP_FAILED`, and `181-S` harvest is blocked. The
failure is **fail-closed**: no unsafe state, no falsely-passing state and no
harvest-eligible state is reachable through it.

**Severity `P2`, argued both ways.** It is not `P1`: the plan's own declared
in-unit remedy — "remove the workflow from the branch tip, have `177.003-T`
re-emit a complete and consistent cleanup evidence block, and re-run
`177.006-T`" — is not constrained to the removal commit, so a conformant block
is producible on the **second** emission without a waiver, without a
determining re-run and without a Stage return; the pass state is reachable, and
decision `D6`'s reachability criterion is therefore met, if only after a
mandatory spurious cycle. It is not `P3`: it is a mechanical impossibility in a
machine-evaluated predicate's input contract, agreed across two surfaces, that
forces at least one false `ISOLATION_CLEANUP_FAILED` on every execution of the
unit as written.

**No remediation is proposed.** This finding requires explicit operator
disposition. It was **not** added to any stash this session.

## New finding `L2` (P3) — `WORKFLOW_PRESENT_AT_TIP` is raised on a clean-but-dirty distinction it does not make

The reason table maps one token to two different facts:

> `WORKFLOW_PRESENT_AT_TIP` — `C6` — the exact path is present at the branch
> tip, **or the working tree is dirty**.

An unrelated uncommitted edit — a backlog record, a memory note — therefore
emits a verdict line whose reason token asserts the probe workflow is present
at the tip when `git ls-files --error-unmatch` has already established it is
absent. The `ISOLATION_CLEANUP_FAILED` line form carries `workflow_path=`
alongside that token, so the line actively names a path it is wrong about, and
the plan's stated remedy — remove the workflow from the branch tip — is a
no-op against the actual cause.

The plan and `177.006-T` **agree** on this wording, so it is an accuracy defect
rather than a divergence. The consequence is diagnostic only: the state is
still `CLEANUP_FAILED`, still non-pass, still harvest-blocking, and the remedy
is in-unit. Graded **P3**, non-blocking, requiring explicit operator
disposition. It was **not** added to any stash this session.

## Verified safe — recorded so a later attempt does not re-raise them

* **`ISOLATION_NOT_OBSERVED` has no declared verdict-line form.** This is
  correct, not a gap: that state is reachable precisely when the artifact is
  missing or ledger-less, so no line could have been written. The consumer-side
  fail-closed default under *Successor eligibility* covers it. Pre-existing
  since revision 3 and not a `K3` regression.
* **`C3` checks set membership, not line order**, while the plan declares the
  block "exactly eight lines, in this order" and `177.003-T` mandates the four
  dispatch lines "one each, in that order"; no check rejects an unrecognised
  extra `CLEANUP_` line. The block is machine-read only by `177.006-T`, which
  is order-insensitive, so nothing turns on it. Recorded as an observation, not
  graded.
* **The `ISOLATION_NOT_OBSERVED` definition now includes "carries more than one
  `COMPOSED_STATE:` line"**, and the emitter's instruction changed from append
  to whole-line replace. Plan and `177.006-T` agree; this is a mechanically
  necessary consequence of the `K3` remedy and is consistent.
* **`177.006-T`'s elapsed bound moved 20 → 30 minutes** to accommodate `C1`–`C6`.
  The plan's Tasks table and the task record agree. Within the 2-hour rule.

## Finding summary

| ID | Severity | State | Subject |
|---|---|---|---|
| `K3` | P2 | **closed** | branch-cleanliness check had no expressible verdict |
| `K4` | P3 | **closed** | check-count enumeration disagreed with the evaluator's record |
| `K5` | P3 | open | `FLOOR_INVOKED` verdict-line separator differs between plan and `177.004-T` |
| `K6` | P3 | open | after-acquisition relation is task-level across two jobs, unrecorded |
| `L1` | **P2** | **new** | cleanup block's mandated write point cannot supply two of its own fields |
| `L2` | P3 | **new** | `WORKFLOW_PRESENT_AT_TIP` also raised on an unrelated dirty tree |

**Counts:** P0 = 0, P1 = 0, P2 = 1, P3 = 3.

## Decision

**ADVISORY.** One P2 remains open. No policy in
`.github/policies/workflow-policies.md` elevates a P2 to blocking for this
unit, so the decision is advisory rather than FAIL/BLOCK. No severity was
lowered to force closure, and no count was decremented.

`183-S` is **not** publication-eligible while `L1` is open: the plan's pass
state `ISOLATION_CHARACTERIZED` is unreachable on a first, spec-conformant
execution.

This is the terminal review for this authorized cycle. No remediation is
proposed and none was performed. `L1`, `L2`, `K5` and `K6` require explicit
operator disposition.
