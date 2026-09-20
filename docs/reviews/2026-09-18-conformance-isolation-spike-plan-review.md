---
title: "Plan review verdict manifest — Conformance isolation spike (S2)"
description: "Mutable verdict manifest for docs/plans/2026-09-18-conformance-isolation-spike-plan.md. This file is a selection surface, not a review: it names which immutable attempt artifact is authoritative right now, and nothing else. The reviews live one per attempt under docs/reviews/review-history/ and are never edited after they are written. Latest attempt: 05, terminal, which judged plan revision 5 at content HEAD 24e19050 and returned gate result ADVISORY, decision ADVISORY, on zero P0, zero P1, one P2 and three P3. Attempt 05 independently re-derived K3 CLOSED and K4 CLOSED, carried K5 and K6 open, and raised one new P2 L1 and one new P3 L2. Plan revision: 5. Independent attempt 01 reviewed revision 1 at content HEAD db39553a and returned FAIL/BLOCKED on one P0, one P1, two P2 and one P3. A Stage remediation cycle produced revision 2, and independent attempt 02 reviewed that revision at content HEAD 5aa8643f, verified all five attempt-01 findings closed and returned FAIL/BLOCKED on zero P0, one P1, one P2 and one P3. A second Stage remediation cycle produced revision 3, and independent attempt 03 reviewed that revision at content HEAD 4b4330b9 and returned gate result FAIL, decision BLOCKED, on zero P0, one P1, one P2 and zero P3. Attempt 03 verified F1, F2 and F3 all genuinely closed, and found a new defect in the mechanism that closes F1: a blocks edge gates on predecessor completion, not on an achievable I1 verdict, so both the 90-minute floor-invoked outcome and an explicit NOT ACHIEVABLE verdict clear the edge and permit the untrusted-credential acquisition and probe tasks to run in a job whose credential absence is unverified or affirmatively falsified, which blast radius, H7, H9, R8 and the 177.004-T record all forbid. No stop condition exists anywhere in the plan or the six task records. That is the open P1, K1. The open P2, K2, is that four determining tasks require GitHub-hosted-runner jobs, which requires committing a probe workflow to the branch, while blast radius said no tracked surface outside docs/spikes/ is mutated and no task owned the workflow's creation or removal. The operator then lifted the terminal designation and authorized a third and final bounded remediation cycle, which produced revision 4: K1 was addressed by separating ordering from safety, retaining the blocks edges as ordering and adding an executable verdict predicate - 177.004-T emits a single non-secret I1_GATE line and 177.005-T and 177.002-T read it as their first action, failing closed to NOT DETERMINED - FLOOR INVOKED naming I1 on anything but ACHIEVABLE, which forces ISOLATION_FLOOR_ONLY and makes ISOLATION_CHARACTERIZED structurally unreachable; K2 was addressed by stating that the probe workflow is committed and giving it an owning task, one exact path, a dispatch model, a removal owner and point, a rollback and branch-cleanliness evidence, with blast radius and rollback reconciled truthfully. Both findings are recorded as addressed pending review, not closed, and the plan now awaits independent attempt 04. Independent terminal attempt 04 then reviewed revision 4 at content HEAD 42f2f8ec and returned gate result ADVISORY, decision ADVISORY, on zero P0, zero P1, one P2 and three P3. Attempt 04 verified K1 and K2 genuinely closed by re-derivation from the plan, the six task records, 177-F, 183-S and the working tree, and raised one new P2, K3: 177.006-T's record mandates a fourth branch-cleanliness check that must emit no pass on a dirty branch, but the plan defines its four composed states exhaustively as functions of the seven-entry coverage ledger, so an all-DETERMINED ledger on a branch still carrying the probe workflow forces the passing state and no token can express unclosed spike. K3 is graded P2 on consequence - a leftover workflow_dispatch-only workflow with minimal permissions and no secrets, reverted in one commit, with no untrusted execution and no credential exposure - and no severity was lowered to reach a closable state. K4, K5 and K6 are advisory P3. Attempt 04 is terminal, so no further remediation cycle is authorized; K3 is available for operator disposition. The plan is cleared of P0/P1 and eligible for staging publication, but ADVISORY is not a PASS, the plan is not Ship-ready, and 181-S becomes reviewable as a plan without becoming harvestable. No PASS exists anywhere in this record and none is asserted. Independent terminal attempt 05 then reviewed revision 5 at content HEAD 24e19050 and returned gate result ADVISORY, decision ADVISORY, on zero P0, zero P1, one P2 and three P3. It re-derived K3 closed - the final state is no longer ledger-only because ISOLATION_CHARACTERIZED now requires the seven-entry ledger AND CLEANUP_PROVEN, C6 independently re-observes the branch tip and is evaluated first, C2 and C4 check creation and removal evidence against the repository, the five-state precedence was re-derived total and deterministic by case analysis, ISOLATION_CLEANUP_FAILED sits above both harvest-eligible states, absence of the block is EVIDENCE_MISSING and never ISOLATION_NOT_OBSERVED, and the block format, sole writer, sole evaluator, C1-C6 semantics, reason vocabulary and successor eligibility agree across the plan, 177.003-T, 177.006-T, 177-F and 183-S, with I1 gating, the no-credential evidence rule, no-network-after-acquisition and rollback intact and reachable - and re-derived K4 closed on the rewritten four-check enumeration, on re-derivation and expressly not on its stash capture. It carried K5 and K6 open and raised one new P2, L1: the eight-line CLEANUP_ block is mandated to be written in the same commit that removes the workflow, while CLEANUP_REMOVED_COMMIT must name that commit's own SHA and CLEANUP_TIP_OBSERVATION must record a clean working tree and a tip SHA, so no spec-conformant first emission exists, C4 and C5 cannot be satisfied on a first pass, and at least one spurious ISOLATION_CLEANUP_FAILED cycle is forced. L1 is graded P2 rather than P1 because the failure is fail-closed and the plan's own in-unit remedy reaches the pass state on a second emission without a waiver or a determining re-run, and P2 rather than P3 because it is a mechanical impossibility in a machine-evaluated predicate's input contract agreed across two surfaces. It also raised one new P3, L2: the C6 reason token WORKFLOW_PRESENT_AT_TIP is raised on a dirty working tree as well as on a present path, so a verdict line can assert the workflow is present at the tip when it is absent. No severity was lowered and no count decremented. Attempt 05's terminal designation was subsequently lifted by the operator for one bounded remediation cycle scoped to the single open P2, L1. That cycle produced plan revision 6: the cleanup lifecycle is split into a removal step (177.003-T, which now writes no CLEANUP_ line) and a separate bounded cleanup-evidence step (a new task 177.007-T, the sole writer of the eight-line block, which observes the already-existing removal commit and writes the block in its own evidence commit), the tip-observation field is renamed to name the tip that was observed rather than the commit that records it, C4 and C5 are restated against values that exist before they are recorded, and C6 remains the evaluator's independent observation of the CURRENT tip and the final branch-state authority. The five-state vocabulary, ISOLATION_CLEANUP_FAILED and its five-token reason vocabulary, the I1 verdict gate, the no-credential and no-secret evidence rule, the acquisition-then-no-network model, the workflow rollback and the per-state 181-S eligibility rules are preserved unchanged. L1 is recorded as ADDRESSED PENDING REVIEW, not closed; K5, K6 and L2 were out of scope and remain open and unaddressed. No count is decremented and no PASS is asserted. Independent terminal attempt 06 then reviewed revision 6 at content HEAD 7768c5d5 and returned gate result ADVISORY, decision ADVISORY, on zero P0, zero P1, two P2 and six P3. It re-derived L1 CLOSED on its own terms - the eight-line block's every field now names a value that exists before the write, no field names the commit that records it, the removal and evidence commits are separate and separately owned, and writer, evaluator, check order, reason vocabulary, precedence and dependency edges agree across the plan, 177.003-T, 177.007-T, 177.006-T, 177-F and 183-S - and raised two new P2 findings against revision 6's new one-normal-run reachability derivation. M1: 177.007-T may write only after confirming the removal commit is the CURRENT TIP, which is stronger than C4's reachability requirement and C5's explicit removal-commit-or-descendant tolerance, so any intervening commit forbids the write under the atomic rule, and because the path is already deleted no second removal commit can exist, making the pass state unrecoverable by the in-unit remedy the plan advertises. M2: 177.007-T step 3 and 177.006-T check C6 both require a whole-tree empty git status --porcelain in a repository whose backlog records under .backlogit are tracked and whose agents emit untracked checkpoint and memory files in normal operation, so the derivation's cleanliness premise is falsified on a normal run; this is distinct from L2, which judges only what the reason token says, and closes nothing of L2. Three new P3 findings were raised - M3, four of seven task records still cite plan revision 5 and attempt 05; M4, the date placeholder literal differs between the plan and the emitting records on all three machine-read line forms; M5, 177.004-T alone lacks the dispatch run-ID and URL capture instruction its three peer determining tasks carry - and K5, K6 and L2 were independently re-verified unchanged and carried open. No severity was lowered and no count decremented. 183-S remains not publication-eligible while M1 and M2 are open. Attempt 06 is terminal: no remediation was performed, none is proposed, and every open finding requires explicit operator disposition."
doc_type: review-manifest
source: docs/reviews/2026-09-18-conformance-isolation-spike-plan-review.md
date: 2026-09-18
manifest_shape: attempt-roster
plan_id: conformance-isolation-spike
plan_path: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
plan_revision: 6
feature_id: 177-F
shipment_id: 183-S
latest_attempt: 6
review_terminal: true
terminal_designation: operator-declared
terminal_disposition: TERMINAL-ADVISORY
terminal_note: "Attempt 03 was designated terminal by the operator, who subsequently lifted that designation and authorized a third and final bounded remediation cycle producing revision 4. Attempt 04 is the operator-declared terminal attempt against revision 4 and returned ADVISORY; its designation was then lifted for one bounded K3-only remediation cycle producing revision 5. Attempt 05 returned ADVISORY against revision 5 and was designated terminal; that designation was then lifted for one bounded L1-only remediation cycle producing revision 6. Attempt 06 is the operator-declared terminal attempt against revision 6 and returned ADVISORY, so review_terminal is true, awaiting_attempt is null and no further remediation cycle is authorized. Terminality never closed a finding and no severity was lowered to reach a closable state."
awaiting_attempt: null
reviewed_content_head: 7768c5d5
gate_result: ADVISORY
verdict: ADVISORY
verdict_is_pass: false
verdict_note: "verdict is ADVISORY because independent terminal attempt 06 judged plan revision 6 at content HEAD 7768c5d5 and found zero P0 and zero P1 findings, with two P2 and six P3 remaining open. Attempt 05's L1 was independently re-derived CLOSED from the plan, the seven task records, 177-F, 183-S, item_deps and the working tree, never from a closure summary and expressly not from the P3 follow-up stash capture. The open P2 findings are M1 and M2, both raised at attempt 06 against revision 6's new one-normal-run reachability derivation. ADVISORY is not a PASS: it records that nothing blocking was found, and the two P2 and six P3 findings remain available for operator disposition."
p0_open: 0
p1_open: 0
p2_open: 2
p3_open: 6
open_findings: [M1, M2, K5, K6, L2, M3, M4, M5]
findings_addressed_pending_review: []
findings_closed_at_attempt_05: [K3, K4]
findings_raised_at_attempt_05: [L1, L2]
findings_closed_at_attempt_06: [L1]
findings_raised_at_attempt_06: [M1, M2, M3, M4, M5]
open_counts_note: "Counts are attempt 06's, derived independently at content HEAD 7768c5d5. K1 (P1) and K2 (P2) were closed at attempt 04; K3 (P2) and K4 (P3) at attempt 05. L1 (P2) is CLOSED at attempt 06 by independent re-derivation from the plan text and the executable records alone: the cleanup lifecycle is split across two tasks and two commits, every field of the eight-line block names a value that exists before the write, and no field names the commit that records it. Closing L1 did not establish first-pass reachability in general. Two new P2 findings judge revision 6's new derivation and are raised rather than folded into the closed finding. M1: 177.007-T's binding step (1) requires the removal commit to be the CURRENT TIP, while C4 requires only reachability and C5 explicitly accepts observed_tip as the removal commit OR A DESCENDANT, so any intervening commit - including the bookkeeping commits this repository's tracked .backlogit records produce - forbids the write under the atomic all-or-nothing rule, and no second removal commit can ever exist because the path is already deleted, so the in-unit remedy the plan advertises cannot restore the pass state. M2: 177.007-T step (3) and 177.006-T check C6 both require a whole-tree empty git status --porcelain, and at the reviewed HEAD the tree carries five unrelated untracked agent-produced entries under .backlogit/checkpoints and docs/memory, so the cleanliness premise fails on a normal run; M2 is distinct from L2 and closes no part of it. Three new P3 findings were raised: M3 (four of seven task records still cite plan revision 5 and attempt 05), M4 (date placeholder literal differs between the plan and the emitting records) and M5 (177.004-T alone lacks the dispatch run-ID and URL capture instruction). K5, K6 and L2 were independently re-verified unchanged and are CARRIED open, not invalidated. No severity was lowered and no count decremented anywhere, and no finding was folded into another to reduce a count. M1, M2, M3, M4 and M5 were NOT added to any stash by attempt 06 and were not triaged or harvested. The P3 follow-up stash entry 5E45691A was re-read read-only and holds exactly K5, K6 and L2; it is expressly NOT treated as an authority on finding state. 183-S is not publication-eligible while M1 and M2 are open."
remediation_authorization: none-this-cycle
latest_remediation_revision: 6
judged_revision: 6
latest_disposition: null
latest_artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-06.md
attempts:
  - attempt: 1
    artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-01.md
    reviewed_revision: 1
    reviewed_content_head: db39553a
    verdict: BLOCKED
    p0_open: 1
    p1_open: 1
    p2_open: 2
    p3_open: 1
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: 2
    disposition: REMEDIATED-PENDING-REVIEW
    terminal: false
    findings_state: closed-at-attempt-02
  - attempt: 2
    artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-02.md
    reviewed_revision: 2
    reviewed_content_head: 5aa8643f
    reviewed_branch: chore/stage-176-s-workflow-defects
    verdict: BLOCKED
    p0_open: 0
    p1_open: 1
    p2_open: 1
    p3_open: 1
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: 3
    disposition: REMEDIATED-PENDING-REVIEW
    terminal: false
    closed_predecessor_findings: [A1, A2, B1, B2, C1]
  - attempt: 3
    artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-03.md
    reviewed_revision: 3
    reviewed_content_head: 4b4330b9
    reviewed_branch: chore/stage-176-s-workflow-defects
    verdict: BLOCKED
    gate_result: FAIL
    p0_open: 0
    p1_open: 1
    p2_open: 1
    p3_open: 0
    open_findings: [K1, K2]
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: 4
    disposition: REMEDIATED-PENDING-REVIEW
    terminal: false
    terminal_designation: lifted-by-operator
    closed_predecessor_findings: [F1, F2, F3]
  - attempt: 4
    artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-04.md
    reviewed_revision: 4
    reviewed_content_head: 42f2f8ec
    reviewed_branch: chore/stage-176-s-workflow-defects
    verdict: ADVISORY
    gate_result: ADVISORY
    p0_open: 0
    p1_open: 0
    p2_open: 1
    p3_open: 3
    open_findings: [K3, K4, K5, K6]
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: null
    disposition: null
    terminal: true
    terminal_designation: operator-declared
    closed_predecessor_findings: [K1, K2]
  - attempt: 5
    artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-05.md
    reviewed_revision: 5
    reviewed_content_head: 24e19050
    reviewed_branch: chore/stage-176-s-workflow-defects
    verdict: ADVISORY
    gate_result: ADVISORY
    p0_open: 0
    p1_open: 0
    p2_open: 1
    p3_open: 3
    open_findings: [L1, K5, K6, L2]
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: 6
    disposition: REMEDIATED-PENDING-REVIEW
    terminal: true
    terminal_designation: lifted-by-operator
    closed_predecessor_findings: [K3, K4]
    carried_predecessor_findings: [K5, K6]
    findings_raised: [L1, L2]
    remediation_scope: "L1 only. K5, K6 and L2 were not in scope and remain open and unaddressed; they are carried as non-blocking follow-ups in the backlogit stash. No finding is claimed closed by this cycle and no count was decremented."
  - attempt: 6
    artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-06.md
    reviewed_revision: 6
    reviewed_content_head: 7768c5d5
    reviewed_branch: chore/stage-176-s-workflow-defects
    verdict: ADVISORY
    gate_result: ADVISORY
    p0_open: 0
    p1_open: 0
    p2_open: 2
    p3_open: 6
    open_findings: [M1, M2, K5, K6, L2, M3, M4, M5]
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: null
    disposition: null
    terminal: true
    terminal_designation: operator-declared
    closed_predecessor_findings: [L1]
    carried_predecessor_findings: [K5, K6, L2]
    findings_raised: [M1, M2, M3, M4, M5]
    remediation_scope: "None. Attempt 06 is a terminal review-only attempt: no remediation was performed, none is proposed, and no finding was stashed, triaged or harvested by it."
carried_forward_context: []
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
external_tracker: 002-C
external_tracker_state: blocked-outside-shipment
tags:
  - "plan-review"
  - "verdict-manifest"
  - "portfolio-2026-09-18"
---

# Verdict manifest — Conformance isolation spike (S2)

This file is a **selection surface**, not a review. It names which immutable
attempt artifact is authoritative right now, and nothing else.

## Current verdict

| Field | Value |
|---|---|
| `plan_id` | `conformance-isolation-spike` |
| `plan_path` | `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` |
| `plan_revision` | 6 |
| `latest_attempt` | **06** (operator-declared **terminal**; no further remediation cycle authorized) |
| `latest_artifact` | `docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-06.md` |
| `reviewed_content_head` | `7768c5d5` (what attempt 06 judged — plan revision 6) |
| `gate_result` (attempt 06, immutable) | **ADVISORY** |
| `verdict` | **ADVISORY** (attempt 06's judgement of revision 6) |
| `verdict_is_pass` | **false** |
| `latest_remediation_revision` | **6** (produced after attempt 05, scoped to `L1`; now judged) |
| `latest_disposition` | `null` — revision 6 has been independently judged |
| `awaiting_attempt` | `null` |
| `p0_open` | **0** |
| `p1_open` | **0** (`K1` closed at attempt 04) |
| `p2_open` | **2** (`M1`, `M2` — raised at attempt 06; `L1` **closed**, `K3` **closed**) |
| `p3_open` | **6** (`K5`, `K6`, `L2` carried; `M3`, `M4`, `M5` raised at attempt 06; `K4` **closed**) |
| `findings_closed_at_attempt_06` | `[L1]` — by independent re-derivation |
| `findings_raised_at_attempt_06` | `[M1, M2, M3, M4, M5]` — **not** stashed by the review |
| `findings_addressed_pending_review` | `[]` |
| `p3_followup_stash` | `5E45691A` (`K5`, `K6`, `L2`) — outside this shipment's scope; `M3`, `M4` and `M5` are **not** in it |

**The top-level `verdict` is attempt 06's own judgement, not a carried value.**
Independent terminal attempt 06 read revision 6 at content HEAD `7768c5d5` and
returned **ADVISORY** on zero P0, zero P1, two P2 and six P3.

**ADVISORY is not a PASS.** `verdict_is_pass` is **false**. ADVISORY records
that an independent reviewer found nothing blocking — zero P0 and zero P1 — on
the content it read, while two P2 remained open. No policy in
`.github/policies/workflow-policies.md` makes a P2 blocking for this unit — the
blocking predicate there is *unresolved P0/P1 findings* — so `M1` and `M2` do
not gate as FAIL/BLOCK. They are not findings Stage may close.

**`183-S` is not publication-eligible while `M1` and `M2` are open.** Both make
the plan's pass state `ISOLATION_CHARACTERIZED` unreachable on a first,
spec-conformant execution in this repository's actual execution environment,
and under `M1` unrecoverable by the in-unit remedy the plan advertises. That is
a different and stronger statement than "not blocking". Publication eligibility
requires explicit operator disposition of `M1` and `M2`.

**Attempt 04's terminal designation was lifted by the operator on
2026-09-19T21:41:26.916-07:00**, authorizing one bounded remediation cycle
scoped to `K3`, judged by independent attempt 05. Lifting terminality bounded
the *review loop*, never a *finding*: **no severity was lowered and no count
was decremented** to permit that cycle, and none was lowered or decremented to
reach attempt 05's result either.

**Attempt 05's terminal designation was likewise lifted**, authorizing one
bounded remediation cycle scoped to `L1`, judged by independent attempt 06.
That cycle produced **plan revision 6** — see *What follows attempt 05*.
**Attempt 06 is the operator-declared terminal attempt against revision 6**: it
closed `L1` by independent re-derivation and raised `M1`, `M2`, `M3`, `M4` and
`M5`. No further remediation cycle is authorized, `awaiting_attempt` is `null`,
and every open finding requires explicit operator disposition. The same rule
applied throughout: **no severity was lowered and no count decremented** to
permit any cycle or to reach any result.

**No `PASS` is asserted.** This manifest has never reported `PASS` and does not
report one now, so harvest remains closed and no Ship work is authorized
against `183-S` or anything downstream of it.

**`L1` is closed by the only authority that can close it**, as were `K3` and
`K4` before it. Each was re-derived by the *next independent attempt* from the
plan, the `177.x` task records, `177-F`, `183-S`, `item_deps` and the working
tree, rather than accepted from a remediation narrative. The P3 follow-up stash
entry `5E45691A` is expressly **not** treated as closure for anything. `K5`,
`K6` and `L2` were re-verified unchanged at attempt 06 and are carried.

**The attempt-01 through attempt-05 counts are closed, and by the same
authority.** Attempt 03 verified `F1`, `F2` and `F3` genuinely closed; attempt
04 closed `K1` and `K2`; attempt 05 closed `K3` and `K4`; attempt 06 closed
`L1`. The open counts above are attempt 06's own set: three carried P3 findings
and five findings it raised.

**Remediation has not converged across five cycles, and `M1`/`M2` are the sixth
layer of the same seam.** Revision 2 closed every attempt-01 finding and
introduced a new P1 doing it. Revision 3 closed all three attempt-02 findings
and introduced a new P1 **inside the very mechanism that closed `F1`**.
Revision 4 separated ordering from safety and introduced `K3` in the composed
vocabulary. Revision 5 made cleanup an executable predicate and introduced
`L1` **inside the very evidence block that closes `K3`** — the block's declared
write point cannot supply two of the block's own fields. Revision 6 split that
write point in two and genuinely closed `L1`, and introduced `M1` and `M2`
**inside the observation preconditions that make the split work** — the writer
must see the removal commit as the current tip, and two limbs must see a clean
whole tree, in a repository whose own agents move the tip and dirty the tree.
This is the non-convergence pattern recorded in
`docs/compound/093-S-review-loop-convergence.md` for novel safety-critical
work: each cycle is a genuine improvement and each cycle exposes the next layer
of the same seam. No Ship work is authorized against `183-S` or anything
downstream of it.

## What attempt 01 records

Independent first review opened against plan revision 1 at content HEAD
`db39553a`; gate result FAIL, decision BLOCKED, one P0, one P1, two P2 and one
P3 open.

Persona coverage was complete across all seven personas (Constitution, Python,
Scope Boundary, Learnings, Architecture, Agent-Native Parity, Security Lens).
Reviewer subagent dispatch was unavailable, so every persona ran as a declared
inline pass with its own finding list; `.autoharness/config.yaml` declares no
`anchor_review` route, so the cross-model rubrics ran same-model. Engram
indexed retrieval was circuit-open and was not retried, and intercom was
unavailable, so visibility was local-only. All evidence was gathered by bounded
direct exact-path reads, `git` plumbing, and read-only backlogit SQL.

**The P0 (`A1`)** is that the plan's declared pass state is unreachable under
its own decomposition. The plan states every property `I1`–`I7` "is classified
ACHIEVABLE or NOT ACHIEVABLE by this spike. None is assumed", and defines
`ISOLATION_UNDETERMINED` as any property left unclassified, adding that a
partially-classified result "is a **fail**, not a partial pass". But
`177.001-T` determines `I2`/`I3`, `177.002-T` determines `I4`/`I5`/`I6`, and
`177.003-T` is an authoring task — **no task determines `I1`**, "No credentials
of any kind in the job environment". The plan's own `R3` and `H2` forbid a
verdict resting on assertion rather than an observed mechanism, so the
authoring task cannot absorb it. Executed as decomposed, the spike terminates
in its own fail state. This is the defect class recorded in
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`
and the one decision D6 exists to catch before harvest; it is graded P0 both
because the contract is broken rather than incomplete and because `I1` is the
security-critical property deciding whether an untrusted binary shares an
environment with a readable token.

**The P1 (`A2`)** is the same structural gap on `I7`: the redirect rule must be
"derived from observed acquisition behaviour", but no task performs an
acquisition, so the rule replacing attempt-08 `B6`'s unsatisfiable rule would
itself be derived from assumption.

The two P2s are the `verdict`-key enum defect (`B1`, graded P2 only because the
manifest-reading consumer does not yet exist) and `177.002-T` carrying
`complexity: high` with neither a split nor a declared de-risking rationale
(`B2`). The P3 is that the composed-state check names producer and consumer in
prose rather than by path.

Attempt 01 also recorded, positively, that the plan's attempt-08 citations of
`B3`, `B4` and `B6` are exact; that the `002-C` boundary is stated exactly as
D5 requires and is confirmed in `item_deps` (no edge in either direction);
that the degradation floor is correctly one-directional; that hardening is
declared and present; and that the three `177.x` task records in `183-S` match
the plan's task table on both size and complexity.

## What follows attempt 01

A Stage remediation cycle, authorized by the operator as a single bounded
cycle, produced **plan revision 2**. What the revision changed, per finding:

* **A1 (P0)** — `I1` now has a determining task. New `177.004-T` inspects the
  **actual job/container environment** and records objective evidence:
  environment-variable **names only**, mount and path presence or absence, and
  the identity the job runs as. It does not read values, so the observation
  cannot itself leak the credential it is looking for. The property is
  determined by observation, not by assertion, which is what `R3` and `H2`
  require and what the authoring task could never supply.
* **A2 (P1)** — new `177.005-T` performs **one real release-asset
  acquisition** and records the redirect chain it actually follows. The `I7`
  allowlist and pinning rule is then **read off that recorded chain** by
  `177.003-T`, which may not invent one. No assumption-derived redirect policy
  can enter, which is the defect attempt-08 `B6` first recorded. `I2` was also
  redefined to be evaluated **after** the observed acquisition, so the
  acquisition and the egress denial no longer contradict each other.
* **A1 and A2, structurally** — a new `## Property coverage` table assigns
  every property `I1`–`I7` a determining task and a named evidence shape, and
  states explicitly that `177.003-T` **transcribes only**. New `177.006-T`
  runs the coverage and composed-state check: first that every property *has*
  a determining task, then that every ledger row is `DETERMINED`, emitting
  `ISOLATION_CHARACTERIZED` or `ISOLATION_UNDETERMINED`. The structural check
  runs first on purpose — it is what would have caught `A1` before harvest.
  A third `ISOLATION_NOT_OBSERVED` state prevents an unrun spike from being
  scored as a determined one.
* **B1 (P2)** — the plan's `verdict` frontmatter key is now `null`, with the
  disposition value moved to a `disposition` key where it belongs.
* **B2 (P2)** — `177.002-T` retains `complexity: high` and now carries the
  **declared de-risking rationale** attempt 01 named as an acceptable answer:
  the three properties `I4`/`I5`/`I6` share one container harness, so splitting
  them would triple setup cost without reducing uncertainty, and the
  uncertainty is concentrated in a single question the task states up front.
* **C1 (P3)** — the composed-state check now names producer and consumer **by
  path** rather than in prose.

The **security model is preserved exactly** and is now stated as a constraint
rather than a question: isolated Linux container, no credentials, restricted
and disposable mounts, post-acquisition network denial, containment over
verification. A property that proves unachievable moves `181-S` to the
evidence-and-documentation floor; it never relaxes the requirement. The
degradation floor remains one-directional.

`002-C` is unchanged: still `blocked`, still outside every manifest, still with
no dependency edge in either direction.

The plan was rewritten as a single coherent current-state document. It carries
no correction log and no review addendum: the remediation narrative lives here,
in the mutable manifest, which is the surface designed to hold it.

**The findings were not closed by that remediation.** Closing them required an
independent attempt 02 against revision 2, which is recorded below.

## What attempt 02 records

Independent second review opened against plan revision 2 at content HEAD
`5aa8643f` on branch `chore/stage-176-s-workflow-defects`; gate result
**FAIL**, decision **BLOCKED**, zero P0, one P1, one P2 and one P3 open.

Persona coverage was complete across all seven personas, with Agent-Native
Parity and Security Lens both triggered and run. Dispatch was again
`single-agent-declared-degradation` with no `anchor_review` route; engram
indexed retrieval was circuit-open and not retried; intercom was unavailable,
so visibility was local-only. Evidence came from bounded direct exact-path
reads, `git` plumbing, and read-only backlogit SQL over a freshly synced index.

**All five attempt-01 findings are verified closed**, each re-derived from the
executable surface rather than accepted from the remediation narrative:

* **A1 (P0)** — `177.004-T` exists, is a member of `183-S`, and determines
  `I1` by enumerating the job environment from a running job rather than
  asserting it; `I1` now has a determining task and the pass state
  `ISOLATION_CHARACTERIZED` is reachable.
* **A2 (P1)** — `177.005-T` exists and performs a real acquisition, so the
  `I7` redirect rule is derived from observed behaviour, not assumption.
* **B1 (P2)** — `verdict: null` with the disposition on its own key.
* **B2 (P2)** — `complexity: high` now carries explicit de-risking: the unit
  is a spike, every task is time-boxed, and `177.006-T` validates coverage and
  composed state before any verdict is emitted.
* **C1 (P3)** — producer/consumer relationships are tabulated rather than
  left in prose.

Correspondence was re-verified independently: all six `177.x` tasks match the
plan's table on both size and complexity; `183-S` has no incoming edge and
`181-S` depends on it, in the direction the plan asserts; `002-C` remains
`blocked`, outside every manifest, with no dependency edge in either direction.

**The open P1 (`F1`) is new and was introduced by the remediation.** The plan's
`### Blast radius` and hardening answer `H7` rest the probe-safety argument on
a claim of ordering — that `I1` "is determined before any probe job is trusted
to be safe". Four independent records deny it: the plan's own task sequence,
`177.004-T`'s body (which says it "may run in any order relative to them"
immediately before the contradicting sentence), `177.002-T`'s and `177.005-T`'s
bodies, and `item_deps`, which carries no edge from either probe task to
`177.004-T`. It is graded P1 rather than P0 because the pass state is still
reachable, the security model is not weakened, and no task executes an
untrusted binary — but a safety argument the executable record contradicts is
not a safety argument. The remedy is a choice of two: add `blocks` edges from
`177.004-T` to `177.002-T` and `177.005-T`, **or** withdraw the ordering claim
from the blast radius, `H7` and `177.004-T`.

**The P2 (`F2`)** is that `ISOLATION_UNDETERMINED` is asserted to block `181-S`
harvest *and* to leave the degradation floor standing, in both the plan and
`177.006-T`, with no `NOT-DETERMINED-FALLBACK` pass value to carry the second
reading; the sibling `182-S` plan solves the identical shape with
`NOT-ANSWERED-FALLBACK`. Decision `R2`/`D5` are not contradicted, because
`R2`'s trigger is a *conclusion* rather than a non-conclusion, so the floor
stays reachable — hence P2. **The P3 (`F3`)** is that the `183-S` manifest
`items` array is not in dependency order; `item_deps` is correct, so this is
presentational.

## What follows attempt 02

A second Stage remediation cycle, authorized by the operator as a single
bounded cycle, produced **plan revision 3**. What the revision changed, per
finding:

* **F1 (P1)** — resolved by **enforcing the ordering, not withdrawing the
  claim**. `177.004-T` is now a real prerequisite of both untrusted-work tasks:
  `item_deps` carries `177.002-T → 177.004-T` and `177.005-T → 177.004-T`, and
  the two task records carry the matching `dependencies` frontmatter. The
  plan's task-sequence paragraph, `177.004-T`'s body (the "may run in any order
  relative to them" sentence is gone), `177.002-T`'s and `177.005-T`'s bodies,
  hardening answer `H7`, the `### Blast radius` paragraph and the `183-S`
  manifest ordering now all state the same thing: the credential-environment
  inspection is observed **before** any acquisition or probe job runs. The
  safety claim is stronger than it was, and the executable record now carries
  it rather than contradicting it. Hardening answers `H9` and `H10` and risk
  `R8` were added to state the enforced edge and what happens if `I1` comes
  back adverse.
* **F2 (P2)** — resolved by **defining the missing transition rather than
  copying the sibling's pass value**. `182-S`'s `NOT-ANSWERED-FALLBACK` is a
  *pass* value, and importing it here would assert a proven isolation floor
  that nothing observed. The composed-state check is now a **four-state
  machine**: `ISOLATION_CHARACTERIZED` (the only pass — every property
  `DETERMINED`), `ISOLATION_FLOOR_ONLY` (every property determined, at least
  one determined **NOT ACHIEVABLE** — explicitly **not a pass**, permits only
  the evidence-and-documentation floor harvest of `181-S`),
  `ISOLATION_UNDETERMINED` (any row `ABSENT` — blocks `181-S` harvest entirely
  and names the absent rows) and `ISOLATION_NOT_OBSERVED` (evaluated first,
  covers an unrun spike and an absent verdict line, never a pass). A
  "Successor eligibility, stated per state" table makes successor eligibility
  unambiguous for each of the four; a fail-closed default states that silence
  never produces eligibility; and three explicit verdict-line forms remove the
  formatting ambiguity. The ledger gained a third value, `NOT DETERMINED —
  FLOOR INVOKED`, which requires all three of what was attempted, what blocked
  it, and a written statement that the property is unproven and the floor is
  invoked — anything less is `ABSENT`. No state presents the floor as proven
  and no PASS is fabricated. Risks `R1` and `R9` and hardening `H4` were
  reworded to match.
* **F3 (P3)** — the `183-S` manifest `items` array is now in dependency order:
  `177-F`, `177.004-T`, `177.005-T`, `177.001-T`, `177.002-T`, `177.003-T`,
  `177.006-T`. No dependency edge changed; the DAG is identical and the
  reordering only makes it readable top to bottom. `183-S` gained a description
  stating that the manifest order **is** dependency order and why `177.004-T`
  leads it.

`002-C` is unchanged under all four composed states: still `blocked`, still
outside every manifest, still with no dependency edge in either direction. The
degradation floor remains one-directional, and `183-S` remains a DAG root with
no incoming edge and `181-S` still depending on it.

The plan was rewritten as a single coherent current-state document. It carries
no correction log and no review addendum: the remediation narrative lives here,
in the mutable manifest, which is the surface designed to hold it.

**The findings are not closed by this remediation.** Closing them requires an
independent attempt 03 against revision 3, which is recorded below.

## What attempt 03 records

Independent third review opened against plan revision 3 at content HEAD
`4b4330b9` on branch `chore/stage-176-s-workflow-defects`; gate result
**FAIL**, decision **BLOCKED**, zero P0, one P1, one P2 and zero P3 open. The
operator designated this the terminal review cycle.

Persona coverage was complete across all seven personas, with Agent-Native
Parity and Security Lens both triggered and run. Dispatch was again
`single-agent-declared-degradation` with no `anchor_review` route; engram
indexed retrieval was circuit-open and not retried; intercom and graphtor-docs
were unavailable, so visibility was local-only. Evidence came from bounded
direct exact-path reads, `git` plumbing, and read-only backlogit MCP reads and
SQL over a freshly synced index.

**All three attempt-02 findings are verified closed**, each re-derived from the
executable surface rather than accepted from the remediation narrative:

* **F1 (P1) — closed.** The precedence is now enforced by real `blocks` edges
  (`177.004-T` → `177.005-T` and `177.004-T` → `177.002-T`) in `item_deps`, not
  by narrative alone, and the three task records reproduce it. The safety claim
  was strengthened rather than withdrawn, which is the correct direction.
* **F2 (P1 coupled) — closed.** The single `ISOLATION_UNDETERMINED` reading is
  replaced by a four-state machine — `ISOLATION_CONFORMANT`,
  `ISOLATION_FLOOR_ONLY`, `ISOLATION_NONCONFORMANT`,
  `ISOLATION_NOT_DETERMINED` — in which the floor-only state is explicitly not
  a pass and no successor eligibility is asserted from it.
* **F3 (P3) — closed.** `custom_fields.items` reads `177-F`, `177.004-T`,
  `177.005-T`, `177.001-T`, `177.002-T`, `177.003-T`, `177.006-T`, matching
  `item_deps` exactly. No edge changed.

Correspondence was re-verified independently: all six `177.x` tasks match the
plan's table on size and complexity and carry `size_source: agent` with a
non-empty ruleset version; `177.002-T` is the only `complexity: high` task and
carries declared de-risking; every property `I1`–`I7` has a determining task;
the full edge set was read back (`177.005←177.004`, `177.002←177.004`,
`177.001←177.005`, `177.003←{001,002,004,005}`, `177.006←177.003`) and is
acyclic; `183-S` has no incoming edge and `181-S` depends on it; and `002-C` is
still `blocked`, still outside every manifest, still with no edge in either
direction.

**The open P1 is `K1`, and it lives inside the mechanism that closed `F1`.**
A `blocks` edge gates on predecessor **completion**, not on an **achievable
`I1` verdict**. The plan declares two outcomes reachable that complete
`177.004-T` and therefore clear the edge while credential absence is *unverified
or affirmatively falsified*: `NOT DETERMINED — FLOOR INVOKED` at the 90-minute
bound (`R9`), and `DETERMINED` carrying a `NOT ACHIEVABLE` verdict (`R6`). Both
then permit `177.005-T` (untrusted-credential acquisition) and `177.002-T`
(probe) to run — exactly what blast radius, `H7`, `H9`, `R8` and the
`177.004-T` record all state must never happen. A search for a halt, stop,
abort or `NOT ACHIEVABLE` branch found **no stop condition** in the plan or in
any of the six task records, so nothing else catches it.

**The open P2 is `K2`:** four determining tasks require GitHub-hosted-runner
jobs, which in practice requires committing and pushing a probe workflow to the
branch, while blast radius states the spike "mutates no tracked surface outside
`docs/spikes/`" and rollback describes a "throwaway probe, not a committed
workflow". No task declares the probe workflow's creation, ownership or
removal. The `## Prototype lifecycle` treatment that `182-S` received for the
same class of problem was not propagated here.

## What follows attempt 03

The operator **lifted the terminal designation** and authorized a third and
final bounded remediation cycle. It produced **plan revision 4**. What the
revision changed, per finding:

* **`K1` (P1)** — addressed by **separating ordering from safety instead of
  adding a third ordering mechanism**. The `blocks` edges are retained and
  unchanged; they are simply no longer offered as the guarantee, because a
  `blocks` edge is a predicate over predecessor *completion* and `177.004-T`
  completes on three outcomes, two of which leave credential absence unverified
  or falsified. The guarantee is now an **executable verdict predicate**.
  `177.004-T` writes exactly one non-secret `I1_GATE:` line — `ACHIEVABLE`,
  `NOT_ACHIEVABLE` or `FLOOR_INVOKED` — to
  `docs/spikes/2026-09-18-conformance-isolation-i1-gate.md` as its last action,
  and is the sole writer. `177.005-T` and `177.002-T` **read that line as their
  first action**, before any acquisition, download, handle creation or
  substitution attempt. The gate is **OPEN** only on a readable file carrying
  exactly one `I1_GATE:` line whose token is `ACHIEVABLE`; **CLOSED** covers
  everything else, including a missing file, an unreadable file, no line, more
  than one line, an unrecognised token, `NOT_ACHIEVABLE` and `FLOOR_INVOKED`.
  On CLOSED neither task runs the untrusted acquisition or the probe **at
  all** — not deferred, not retried, not narrowed — and each records its
  properties `NOT DETERMINED — FLOOR INVOKED` **naming `I1` as the blocker**
  with the three parts the ledger requires. `177.001-T` records `I2` the same
  way, via the acquisition that never ran; `I3` is explicitly **not** gated,
  because repository absence is observable without touching anything untrusted.
  The forced composed state is **`ISOLATION_FLOOR_ONLY`**, never
  `ISOLATION_CHARACTERIZED` — structurally, since the only pass state requires
  all seven properties `DETERMINED`. The rule is stated in a new `## I1 gate`
  section and reproduced in the Security model, the Tasks ordering text, the
  Composed-state table, blast radius, `H7`, new `H12` and `H13`, `R8`, new
  `R10`, and in the `177.004-T`, `177.005-T`, `177.002-T`, `177.001-T`,
  `177.003-T` and `177.006-T` records. `177.006-T` additionally treats a
  `DETERMINED` verdict on a gated property under a CLOSED gate as **itself a
  fail**, and is told explicitly not to read the `blocks` edge as evidence the
  gate was open.
* **`K2` (P2)** — addressed by **telling the truth about the committed
  workflow and giving it the `182-S` treatment**. GitHub executes only
  workflows that exist on a branch, so the plan now states that the probe
  workflow **is committed** rather than calling it a throwaway. A new
  `## Probe workflow lifecycle` section names the owning task (`177.004-T`,
  creation, in its own commit), the exact bounded path
  (`.github/workflows/spike-177-isolation-probe.yml`, one file, no existing
  workflow modified), the dispatch model (all four determining tasks reuse the
  single workflow by `workflow_dispatch` input), the removal owner and point
  (`177.003-T`, at spike close, in the same commit that lands the findings
  artifact, and anyway if the spike aborts), the rollback (`git revert` of the
  single creation commit), and the evidence (creation commit SHA and path, four
  dispatch run IDs and URLs, removal commit SHA, and a
  `git status --porcelain` observation showing the workflow absent from the
  branch tip). **Blast radius and rollback were reconciled truthfully**: both
  previously said the spike mutates no tracked surface and that any CI
  definition is uncommitted. Blast radius now names the one tracked path and
  its transient lifetime; rollback now has two entries with declared owners.
  `181-S` still owns every **durable** committed CI surface — this one is
  dispatch-only, minimally permissioned, secret-free, and does not survive its
  unit. `177.006-T` records a branch still carrying the workflow at spike close
  as an unclosed spike.

**The no-credentials and no-network-after-acquisition model is intact and the
invariant evidence stays non-secret.** The `I1_GATE:` line carries a token, a
verdict, a short non-secret mechanism or reason identifier and a date — a
reader learns *whether* credential absence was established, never *what* any
credential is. The names-only evidence rule (`R6`) was extended to bind the
gate artifact explicitly. The probe workflow declares a minimal `permissions:`
block, is passed no secrets, and fires only on `workflow_dispatch`; acquisition
happens only in `177.005-T`'s dispatch and every containment probe runs after
egress is denied.

Task topology, sizing, complexity and the edge set are unchanged: six tasks,
the same `177.005←177.004`, `177.002←177.004`, `177.001←177.005`,
`177.003←{001,002,004,005}`, `177.006←177.003` edges, acyclic, `183-S` still a
DAG root with no incoming edge and `181-S` still depending on it. `002-C`
remains `blocked`, outside every manifest, with no edge in either direction.

The plan was rewritten as a single coherent current-state document. It carries
no correction log and no review addendum: the remediation narrative lives here,
in the mutable manifest, which is the surface designed to hold it.

**The findings are not closed by this remediation.** `K1` and `K2` are recorded
as *addressed, pending review*. Closing them requires an independent **attempt
04** against revision 4. The plan remains **not harvest-ready and not
Ship-ready**, and `181-S` does not become reviewable, because its predecessor
gate has not passed.

## What attempt 04 records

Independent fourth review, **operator-declared terminal**, opened against plan
revision 4 at content HEAD `42f2f8ec` on branch
`chore/stage-176-s-workflow-defects`; gate result **ADVISORY**, decision
**ADVISORY**, zero P0, zero P1, one P2 and three P3 open.

Persona coverage was complete across all seven personas, with Agent-Native
Parity and Security Lens both triggered and run. Dispatch was
`single-agent-declared-degradation` with no `anchor_review` route; engram
indexed retrieval was circuit-open and not retried; intercom and graphtor-docs
were unavailable, so visibility was local-only. Evidence came from bounded
direct exact-path reads, `git` plumbing over the working tree, and read-only
backlogit structured queries against a freshly synced index.

**Both attempt-03 findings are verified closed, by re-derivation rather than by
closure summary:**

* **`K1` (P1) — closed.** `I1_GATE` is now a genuine fail-closed **verdict
  predicate**, not merely an ordering statement. The plan defines `I1_OPEN` and
  `I1_CLOSED` as named states with an explicit emitter, and every acquisition
  and probe task that would touch untrusted material is conditioned on
  `I1_OPEN`. On the closed path the tasks are forced to a floor-only,
  non-passing state and the composed verdict cannot reach a pass. The `177-F`
  record and the `183-S` description agree with the plan, and the conditioning
  appears in the individual `177.x` task records rather than only in the plan
  prose.
* **`K2` (P2) — closed.** The committed probe workflow now has a complete
  lifecycle in the plan and in the owning task records: a named owner, a create
  step, a remove step and a rollback path expressed as a single-commit revert.
  `.github/workflows/spike-177-isolation-probe.yml` is confirmed **absent** from
  the tree, which is correct — it is created at execution time, not at plan
  time.

Attempt 04 verified independently that acquisition and probe tasks cannot touch
untrusted material unless `I1` is `OPEN`; that closed paths force floor-only,
non-pass state with no token that can be mistaken for a pass; that the declared
invariants and evidence remain non-secret and reachable with no credential,
secret or token exposure in any probe surface; and that sizing, complexity,
`item_deps`, DAG root status, source IDs, manifest closure and every
cross-reference correspond. `002-C` was confirmed intact, `status: blocked`,
carrying no dependency edges and sitting outside every shipment manifest.

**The one open P2** is `K3`: `177.006-T`'s record mandates a fourth
branch-cleanliness check whose failure must "emit no pass", but the plan defines
the four composed states **exhaustively as functions of the seven-entry coverage
ledger**, so an all-`DETERMINED` ledger on a branch still carrying the probe
workflow forces the passing state and no token can express "unclosed spike".
This is a plan-to-record divergence *and* an unexpressible verdict — the same
defect class as `K1` — but its consequence is bounded: a leftover
`workflow_dispatch`-only workflow with minimal `permissions` and no secrets,
reverted in one commit. No untrusted execution, no credential exposure and no
change to successor eligibility. The load-bearing safety mechanism (`I1`
predicate to forced floor-only) is intact, which is why this is graded P2 and
not P1. **The severity was not lowered to reach a closable state**; it was
graded on consequence from the outset.

`K4`, `K5` and `K6` are P3 and advisory.

## What follows attempt 04

At **2026-09-19T21:41:26.916-07:00** the operator **lifted attempt 04's
terminal designation** and authorized one bounded Stage remediation cycle
scoped to `K3` alone, plus mechanically necessary consistency edits, followed
by an independent attempt 05. `review_terminal` is therefore `false`,
`terminal_designation` is `operator-lifted`, and `awaiting_attempt` is `5`.
**Lifting terminality closes no finding, decrements no count and changes no
verdict.** The manifest verdict remains attempt 04's `ADVISORY`.

That cycle produced **plan revision 5**, disposition
`REMEDIATED-PENDING-REVIEW`. `K3` is recorded as **addressed pending review**,
not closed: it is still counted in `p2_open` and still listed in
`open_findings`, and only an independent attempt 05 may close it.

**What revision 5 did about `K3`.** It made branch cleanup an executable limb
of the final predicate rather than a prose expectation:

* `177.003-T` becomes the **sole writer** of a fixed **eight-line `CLEANUP_`
  evidence block** in the findings artifact, written in the same commit that
  removes the workflow, carrying paths, commit identities, run IDs and URLs
  only under the same non-secret evidence rule as `R6`.
* `177.006-T` becomes the **sole evaluator**, resolving cleanup to
  `CLEANUP_PROVEN` or `CLEANUP_FAILED` through six checks `C1`–`C6`, with
  **`C6` evaluated first** because it independently re-observes the branch tip
  rather than trusting the artifact's own recorded observation.
* A **fifth composed state `ISOLATION_CLEANUP_FAILED`** carries its own verdict
  line form and a five-token reason vocabulary
  (`WORKFLOW_PRESENT_AT_TIP`, `TIP_UNOBSERVABLE`, `EVIDENCE_MISSING`,
  `EVIDENCE_MALFORMED`, `EVIDENCE_INCONSISTENT`).
* A **declared precedence** — `ISOLATION_NOT_OBSERVED`,
  `ISOLATION_UNDETERMINED`, `ISOLATION_CLEANUP_FAILED`,
  `ISOLATION_FLOOR_ONLY`, `ISOLATION_CHARACTERIZED` — makes state resolution a
  total function and places the cleanup test **above** the pass state, so
  `ISOLATION_CHARACTERIZED` is structurally unreachable while the exact
  workflow path survives at the branch tip or its lifecycle evidence is
  missing, malformed or inconsistent.
* A **per-state successor-eligibility row** blocks `181-S` harvest outright on
  `ISOLATION_CLEANUP_FAILED`, with an in-unit remedy that needs no further
  determining run and no waiver.
* Absence of the whole block resolves to
  `CLEANUP_FAILED | cleanup=EVIDENCE_MISSING`, never `ISOLATION_NOT_OBSERVED`.
* `I1` gating and the no-credentials / no-network-after-acquisition model are
  **preserved unchanged**; the cleanup check is local, offline and
  credential-free.

Aligned surfaces: the plan's state table, precedence, verdict line forms,
transition-check enumeration, *Probe workflow lifecycle*, `H10`, `H13`, `H14`,
new `H15`, `R11`, blast radius and rollback; task records `177.003-T` and
`177.006-T`; `177-F`; `183-S`; and this manifest. Plan-revision references were
bumped in all six `177.x` records and `177-F`.

**`K4`, `K5` and `K6` were out of scope** for this cycle, remain open and
unaddressed, and are carried as non-blocking follow-ups in backlogit stash
entry `5E45691A`. The revision-5 edits to the transition-check enumeration
necessarily touch text `K4` also concerns, because making cleanup an executable
check required enumerating it; **no claim of `K4` closure is made or implied**.

This unit remains **cleared of P0/P1**. `ADVISORY` is still not a `PASS`, the
plan is not Ship-ready, and `181-S` remains reviewable as a plan without
becoming harvestable. No `PASS` exists anywhere in this record and none is
asserted.

## What attempt 05 records

Independent terminal **attempt 05** read **plan revision 5** at content HEAD
`24e19050` on branch `chore/stage-176-s-workflow-defects` and returned gate
result **ADVISORY**, decision **ADVISORY**, on **zero P0, zero P1, one P2 and
three P3**. Dispatch ran in `single-agent-declared-degradation` with all seven
personas applied inline; engram was circuit-open and **not** retried, and
intercom and graphtor-docs were unavailable.

**`K3` (P2) is closed.** Re-derived, not accepted:

* the final state is **not ledger-only** — `ISOLATION_CHARACTERIZED` requires
  all seven ledger rows `DETERMINED` **and** cleanup `CLEANUP_PROVEN`, and the
  conjunction appears on every surface;
* **`C6` is evaluated first and re-observes the branch tip itself**
  (`git ls-files --error-unmatch` non-zero plus empty `git status --porcelain`),
  explicitly *not* taking the fact from `CLEANUP_TIP_OBSERVATION`, and `C2` and
  `C4` check creation and removal evidence against the repository, so the
  predicate inputs are executable rather than asserted;
* the five-state precedence was re-derived **total and deterministic** by case
  analysis over `{DETERMINED, FLOOR_INVOKED, ABSENT}` × `{PROVEN, FAILED}`;
* `ISOLATION_CLEANUP_FAILED` sits **above both** harvest-eligible states, and
  the one reason-masking case (`ISOLATION_UNDETERMINED` on a dirty branch with
  an `ABSENT` row) was followed to the end: its waiver path still requires a
  `177.006-T` re-run that reaches the cleanup limb, so it is **not an
  eligibility leak**;
* the eight-line block format, sole writer `177.003-T`, sole evaluator
  `177.006-T`, `181-S`'s token-only read, `C1`–`C6` semantics, the first-failure
  order `C6, C1, C2, C3, C4, C5`, the five-token reason vocabulary, the
  absence rule (`EVIDENCE_MISSING`, never `ISOLATION_NOT_OBSERVED`) and
  per-state successor eligibility **agree across the plan, `177.003-T`,
  `177.006-T`, `177-F` and `183-S`**;
* `I1` gating, the no-credential/no-secret evidence rule, the
  no-network-after-acquisition invariant and rollback are **intact and
  reachable**; the cleanup check is local, offline and credential-free.

**`K4` (P3) is closed**, on the rewritten enumeration alone: the plan now says
`177.006-T` performs the transition "in four checks" — Coverage, Evidence, I1
gate, Cleanup — matching `177.006-T`'s **FOUR CHECKS, IN ORDER**. The stash
capture `5E45691A` is expressly **not** treated as closure.

**`K5` and `K6` (P3) are carried**, independently re-verified unchanged: the
`FLOOR_INVOKED` verdict-line separator still differs between the plan (em dash)
and `177.004-T` (hyphen-minus); and the plan still does not record that `I2`'s
evidence is observed in a job that performs no acquisition.

**`L1` (P2) is raised.** The plan and `177.003-T` both mandate that the
`CLEANUP_` block be written **in the same commit that removes the workflow**,
while `CLEANUP_REMOVED_COMMIT` must carry "this task's removal commit" SHA and
`CLEANUP_TIP_OBSERVATION` must carry a tip SHA and `porcelain_empty=yes`. A
commit cannot contain its own SHA and a clean-tree observation cannot be made
from inside the change that cleans it, so **no spec-conformant first emission
of the block exists**: `C4` and `C5` fail, the unit composes to
`ISOLATION_CLEANUP_FAILED`, and at least one spurious cycle is forced. This is
not a plan-to-record divergence — both surfaces state the same impossible
mandate. Graded **P2**: not P1 because the failure is fail-closed and the
plan's own in-unit remedy reaches the pass state on a second emission without a
waiver or a determining re-run; not P3 because it is a mechanical impossibility
in a machine-evaluated predicate's input contract.

**`L2` (P3) is raised.** `WORKFLOW_PRESENT_AT_TIP` is the `C6` reason token for
*either* "the exact path is present at the branch tip" *or* "the working tree
is dirty", so an unrelated uncommitted edit emits a verdict line asserting the
workflow is present when `git ls-files` has already shown it absent, and the
stated remedy is a no-op against the actual cause. Diagnostic-only; still
fail-closed and harvest-blocking.

**`L1` and `L2` were not added to any stash**, were not triaged and were not
harvested. They require explicit operator disposition.

## What follows attempt 05

**The operator lifted attempt 05's terminal designation** and authorized one
bounded Stage remediation cycle scoped to the single open P2, `L1`, to be judged
by an independent attempt 06. `review_terminal` is therefore `false`,
`terminal_designation` is `lifted-by-operator`, and `awaiting_attempt` is `6`.
**Lifting terminality closes no finding, decrements no count and changes no
severity.** `L1` remains open in this manifest until an independent reviewer
judges it.

That cycle produced **plan revision 6**, disposition
`REMEDIATED-PENDING-REVIEW`, which is a statement about what Stage produced and
never about what a reviewer found.

**What revision 6 did about `L1`.** It split the cleanup lifecycle into two
tasks and two commits so that every value the evidence block records already
exists when it is recorded. `177.003-T` removes
`.github/workflows/spike-177-isolation-probe.yml` and lands the findings
artifact in one commit — the **removal commit** — and writes no `CLEANUP_`
line. A new bounded task `177.007-T` (XS, low, 30 min) then runs against that
already-existing commit, observes it, and is the **sole writer** of the
eight-line block, which it lands in its own separate **evidence commit**. The
tip-observation field is restated as
`observed_tip` / `porcelain_empty_at_observation` / `observed_at`, so it names
the tip that was actually observed — the removal commit, the **parent** of the
evidence commit — rather than pretending the record contains its own final
commit SHA. `C4` now requires the removal commit to be already reachable from
the current tip; `C5` checks `observed_tip` against the repository; and `C6`
remains `177.006-T`'s **independent observation of the current tip**, evaluated
first and before the evaluator stages its own edit, which is the final
branch-state authority. Manifest order and edges become `177.003-T` →
`177.007-T` → `177.006-T`, with the pre-existing `177.003-T` → `177.006-T` edge
retained.

**What revision 6 deliberately did not do.** The five composed states including
`ISOLATION_CLEANUP_FAILED`, its five-token fail-closed reason vocabulary, the
declared precedence, the `I1` verdict gate, the no-credential and no-secret
evidence rule, the acquisition-then-no-network model, the workflow rollback and
the per-state `181-S` successor-eligibility rules are all preserved unchanged.
`K5`, `K6` and `L2` were **out of scope** and remain open and unaddressed. In
particular the `C6` reason token `WORKFLOW_PRESENT_AT_TIP` is still raised on a
dirty working tree as well as on a present path, which is `L2` exactly; no
claim of `L2` closure is made or implied.

`183-S` is **cleared of P0/P1** and **not publication-eligible** while `L1` is
open. The open findings `L1`, `L2`, `K5` and `K6` are available for explicit
operator disposition. `ADVISORY` is still not a `PASS`, the plan is not
Ship-ready, and `181-S` remains reviewable as a plan without becoming
harvestable. No `PASS` exists anywhere in this record and none is asserted.

## What attempt 06 records

Independent terminal **attempt 06** read **plan revision 6** at content HEAD
`7768c5d5` on branch `chore/stage-176-s-workflow-defects` and returned gate
result **ADVISORY**, decision **ADVISORY**, on **zero P0, zero P1, two P2 and
six P3**. Dispatch ran in `single-agent-declared-degradation` with all seven
personas applied inline; engram was circuit-open and **not** retried, and
intercom and graphtor-docs were unavailable.

**`L1` (P2) is closed.** Re-derived field by field, not accepted:

* the removal happens first and in its own commit — `177.003-T` deletes
  `.github/workflows/spike-177-isolation-probe.yml` in the commit that lands
  the findings artifact, that commit is its **terminal action**, and it writes
  **no** `CLEANUP_` line;
* every one of the eight fields names a value that exists **before** the write:
  a constant path, `177.004-T`'s creation commit, four completed run IDs and
  URLs, `177.003-T`'s already-existing removal commit, and an observation taken
  before `177.007-T` stages anything;
* **no field names the commit that records it**, no SHA may be guessed,
  invented or pre-computed, and the renamed
  `porcelain_empty_at_observation` field makes and needs no claim about the
  tree after the block is written;
* sole writer `177.007-T`, sole evaluator `177.006-T`, `181-S`'s token-only
  read, the `C6`-first order, the five reason tokens and the five-state
  precedence agree across the plan, `177.003-T`, `177.007-T`, `177.006-T`,
  `177-F` and `183-S`;
* `item_deps` carries `177.003-T` → `177.007-T` → `177.006-T` with the
  pre-existing `177.003-T` → `177.006-T` edge retained, and the `183-S`
  manifest order is that dependency order, so removal → evidence → evaluation
  is unavoidable.

**`M1` (P2) is raised.** `177.007-T` may write only after confirming the
removal commit **is the current tip**, while `C4` requires only reachability
and `C5` explicitly accepts `observed_tip` as the removal commit **or a
descendant** and states it is never required to equal the current tip. The
writer's precondition is therefore stronger than the predicate it feeds. Under
the atomic all-or-nothing rule, one intervening commit forbids the write — and
`.backlogit/` is tracked (2476 paths, including `.backlogit/queue/177.007-T.md`),
so ordinary status bookkeeping moves the tip. Because the path is already
deleted, **no second removal commit can ever exist**, so re-emission can never
satisfy step (1) again and the advertised in-unit remedy cannot restore the
pass state. Graded P2: fail-closed, no false pass, no safety impact — but it
defeats the property the revision-6 cycle was authorized to establish and is
unrecoverable in-unit.

**`M2` (P2) is raised.** `177.007-T` step (3) and `177.006-T` check `C6` both
require a **whole-tree** empty `git status --porcelain`, and `C6` is evaluated
first so its failure short-circuits the predicate. At the reviewed HEAD the
tree carries five unrelated untracked entries produced by the agents that run
this pipeline — two under `.backlogit/checkpoints/`, three under
`docs/memory/`. Revision 6's new one-normal-run derivation assumes both
observations see a clean tree, and they do not. Distinct from `L2`, which
judges only what the reason token *says* when a dirty tree raises it; neither
closes the other.

**`M3`, `M4` and `M5` (P3) are raised.** Four of seven task records still cite
plan revision 5 and attempt 05; the date placeholder literal differs between
the plan (`2026-09-DD`) and the emitting records (`<date>`) on all three
machine-read line forms; and `177.004-T` alone lacks the dispatch run-ID and
URL capture instruction its three peer determining tasks carry, while `C3`
requires an `i1-credentials` line and the sole writer is offline.

**`K5`, `K6` and `L2` (P3) are carried**, independently re-verified unchanged
and expressly not claimed closed.

**`M1`, `M2`, `M3`, `M4` and `M5` were not added to any stash**, were not
triaged and were not harvested. They require explicit operator disposition.

## What follows attempt 06

**Nothing automatic.** Attempt 06 is the operator-declared terminal attempt
against revision 6. **No remediation was performed and none is proposed**, no
remediation cycle is authorized, and `awaiting_attempt` is `null`.

`183-S` is **cleared of P0/P1** and **not publication-eligible** while `M1` and
`M2` are open. The eight open findings — `M1`, `M2`, `K5`, `K6`, `L2`, `M3`,
`M4`, `M5` — are available for explicit operator disposition. `ADVISORY` is
still not a `PASS`, the plan is not Ship-ready, and `181-S` remains reviewable
as a plan without becoming harvestable. No `PASS` exists anywhere in this
record and none is asserted.

## Attempt roster

`reviewed_revision` + `verdict` are what an **independent reviewer** judged.
`remediation_revision` + `disposition` are what **Stage** produced in response.
They are separate columns because merging them is how a fabricated PASS enters
the record. `REMEDIATED-PENDING-REVIEW` is never a `verdict` value; it is only
ever a `disposition`.

| Attempt | Artifact | Reviewed rev | Reviewer verdict | Remediation rev | Disposition |
|---|---|---|---|---|---|
| 1 | `...-plan-review-attempt-01.md` | 1 @ `db39553a` | **BLOCKED** (1 P0, 1 P1, 2 P2, 1 P3) | 2 | `REMEDIATED-PENDING-REVIEW` |
| 2 | `...-plan-review-attempt-02.md` | 2 @ `5aa8643f` | **BLOCKED** (0 P0, 1 P1, 1 P2, 1 P3) | 3 | `REMEDIATED-PENDING-REVIEW` |
| **3** (terminal designation lifted) | `...-plan-review-attempt-03.md` | 3 @ `4b4330b9` | **BLOCKED** (0 P0, 1 P1, 1 P2, 0 P3) | 4 | `REMEDIATED-PENDING-REVIEW` |
| **4** (terminal designation lifted 2026-09-19) | `...-plan-review-attempt-04.md` | 4 @ `42f2f8ec` | **ADVISORY** (0 P0, 0 P1, 1 P2, 3 P3) | 5 | `REMEDIATED-PENDING-REVIEW` |
| **5** (terminal designation lifted 2026-09-19) | `...-plan-review-attempt-05.md` | 5 @ `24e19050` | **ADVISORY** (0 P0, 0 P1, 1 P2, 3 P3) | 6 | `REMEDIATED-PENDING-REVIEW` |
| **6** (operator-declared terminal) | `...-plan-review-attempt-06.md` | 6 @ `7768c5d5` | **ADVISORY** (0 P0, 0 P1, 2 P2, 6 P3) | — | — |

## Provenance

* Plan: `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` at revision 6
* Feature: `177-F` — Shipment: `183-S` (queued, DAG root, no incoming edge)
* Shipment members after remediation, in manifest (dependency) order: `177-F`,
  `177.004-T` (determines `I1`; enforced prerequisite of the two untrusted-work
  tasks), `177.005-T` (observes the acquisition that `I7` is read off),
  `177.001-T`, `177.002-T`, `177.003-T` (transcribes only; removes the probe
  workflow in the removal commit; writes no `CLEANUP_` line), `177.007-T`
  (observes the committed removal; sole writer of the `CLEANUP_` evidence block,
  in its own evidence commit), `177.006-T`
  (coverage, `I1`-gate, cleanup and five-state composed-state validation; sole
  evaluator of the block; independently re-observes the current branch tip)
* Non-blocking P3 follow-ups for this root: backlogit stash entry `5E45691A`
  (`K5`, `K6`, `L2`) — not in this shipment's scope. `K4` was independently
  closed at attempt 05 and has been **removed** from that entry; `L2`, raised at
  attempt 05, has been **added** to it. Neither edit was made by a review: the
  entry was corrected by Stage during the revision-6 remediation cycle, and no
  severity was lowered and no count decremented to do so. Attempt 06 re-read the
  entry **read-only** and confirms it holds exactly `K5`, `K6` and `L2`. `L1` is
  **not** in that entry — it was addressed at revision 6 and closed at attempt
  06. `M1`, `M2`, `M3`, `M4` and `M5` are **not** in that entry either: attempt
  06 stashed nothing.
* External tracker: `002-C`, `blocked`, outside every manifest, no dependency
  edge in either direction — unchanged by this review
* Governing decision: the 2026-09-18 shared-execution-architecture and
  portfolio-reslicing decision, revision 1

## Authority

Latest attempt and verdict are read from this manifest, never from the plan
body. Per-attempt reviews live one per attempt under
`docs/reviews/review-history/` and are never edited afterwards. A disagreement
between `latest_attempt`/`latest_artifact` and the roster derivation above is
`REVIEW_VERDICT_AMBIGUOUS`, not a matter of narrative.
