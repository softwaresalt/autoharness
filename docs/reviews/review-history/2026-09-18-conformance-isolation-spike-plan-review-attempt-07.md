---
title: "Plan review attempt 07 — Conformance isolation spike (S2)"
description: "Immutable per-attempt plan-review artifact recording the seventh and operator-designated terminal independent review of docs/plans/2026-09-18-conformance-isolation-spike-plan.md at revision 7, against reviewed content HEAD 4a28eb4a on branch chore/stage-176-s-workflow-defects. Gate result PASS; decision PASS on zero P0, zero P1, zero P2 and eight P3 deduplicated findings. Attempt 06's two open P2 findings are independently re-derived CLOSED, each on its own terms and each against the repository rather than against a remediation narrative. M1 is closed because the removal proof is now durable rather than positional: 177.007-T derives the removal commit from committed history by the fixed-argv derivation RC1-RC7, which requires existence, an exact-path deletion, no other workflow file touched, absence from the removal commit's own tree, reachability from the current HEAD by ancestor-or-equal merge-base, and the creation commit in ancestry, with a self-reference guard binding the SHA to history read before anything is staged; no surface anywhere still requires the removal commit to be the current tip, 177.006-T re-derives the identical RC1 and requires SHA equality, and re-emission after later unrelated forward commits needs no second removal or deletion commit. This was verified empirically in throwaway repositories: RC1 through RC6 resolve the removal commit after an unrelated bookkeeping commit and after an unrelated merge, and reachability holds in both. M2 is closed because every cleanliness limb is now scoped to the single path .github/workflows/spike-177-isolation-probe.yml by the fixed-argv probes PP1, PP2 and PP3; no live requirement for whole-tree git status --porcelain emptiness survives on any of the nine surfaces, and all remaining whole-tree mentions are historical narration of the defect itself. A five-case control matrix confirms the specified semantics exactly: an unrelated dirty tree passes clean, an untracked exact-path copy and a staged exact-path copy each fail closed as residue, and a tracked-at-tip copy and a tracked-plus-unstaged copy each fail closed as tracked-at-tip, so the tracked-then-residue precedence inside C6 reports a truthful token in every case. Attempt 05's P3 L2 is also independently re-derived CLOSED, on the plan text and 177.006-T's record alone and expressly not on the stash capture that disclaims authority: WORKFLOW_PRESENT_AT_TIP is narrowed to the tracked-at-tip case and is stated on both surfaces never to be raised for a working-tree or index condition, WORKFLOW_PATH_RESIDUE carries exact-path residue, TIP_UNOBSERVABLE carries ambiguity, and the advertised remedy now names the residue case so it is no longer a no-op against the actual cause. Three new P3 findings are raised, all accuracy defects in justification text rather than in mandated behaviour, and all fail-closed or fail-safe in consequence. N1, RC1's stated rationale for --full-history names the wrong trigger; the mandate is load-bearing and must be kept, but its real trigger is merge simplification of a create-and-delete pair living entirely on a merged side branch, not absence of the path at HEAD, which was empirically shown not to prune the deletion commit. N2, PP2's stated rationale for --untracked-files=all names a directory-collapse case that does not occur when an exact-path pathspec is supplied; the flag is nevertheless load-bearing for a stronger reason the text does not give, because omitting it under status.showUntrackedFiles=no silently misses untracked exact-path residue, which is a fail-open. N3, 177.007-T's numbered step contract consumes the creation SHA in RC6 at step 1 while instructing that the value be read at step 4. K5, K6, M3, M4 and M5 are independently re-verified unchanged and carried open. 183-S is cleared of P0, P1 and P2 and becomes publication-eligible, completing the three-root wave alongside 177-S and 182-S. Dispatch ran in single-agent declared degradation with all seven personas covered inline; engram was circuit-open and not retried, intercom was unavailable so visibility is local-only, and graphtor-docs was not exposed. No remediation was performed and none is proposed."
doc_type: review
source: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-07.md
date: 2026-09-19
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 7
attempt_range: "07"
attempt_conformance: conforming
review_terminal: true
terminal_designation: operator-declared
terminal_disposition: TERMINAL-PASS
verdict_manifest: docs/reviews/2026-09-18-conformance-isolation-spike-plan-review.md
supersedes: null
predecessor_artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-06.md
plan_path: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
plan_id: conformance-isolation-spike
reviewed_revision: 7
reviewed_content_head: 4a28eb4a
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
review_cycle: 7
dispatch_mode: single-agent-declared-degradation
anchor_route: absent
anchor_route_note: "No anchor_review key exists in .autoharness/config.yaml model_routing, whose only keys are tier1, tier2, tier3, orchestrator, stage, ship and escalation, so no cross-model anchor was dispatchable. The cross-model rubrics ran under same-model declared degradation. This is recorded, not compensated for."
model_route_note: "Stage role route resolved from .autoharness/config.yaml model_routing.stage (claude-opus-5/anthropic/high), re-read fresh at session start per the Session-Start Dynamic Reload contract. The escalation route model_routing.escalation (gpt-5.6-sol/openai/high) is distinct from both the role route and tier3 (claude-opus-5), so the same-route ESCALATION_DEGRADED guard does not fire. No escalation was triggered: no failure threshold was reached during this review."
degraded_capabilities:
  - capability: reviewer-subagent-dispatch
    state: degraded
    note: "TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent inline persona pass. Every selected persona was applied inline with its own finding list, per the Persona Rubric Adapter. Reviewer personas are leaf executors and spawned nothing."
  - capability: agent-engram
    state: circuit-open
    note: "Indexed retrieval circuit open per operator instruction; NOT retried this session. All evidence below comes from bounded direct exact-path reads, git plumbing, read-only backlogit MCP reads over a freshly synced index (1435 artifacts), and bounded throwaway-repository controls run outside the repository under TEMP."
  - capability: agent-intercom
    state: unavailable
    note: "No operator broadcast performed; visibility is local-only. No operator choice-presentation step was skipped, because this review presents no choice."
  - capability: graphtor-docs
    state: unavailable
    note: "No graphtor-docs tool surface was exposed to this session. Documentation questions were answered by direct reads under docs/ and docs/compound/."
backlogit_index_state: "INDEX_SYNC_OK — 1435 artifacts indexed at session start"
gate_result: PASS
decision: PASS
verdict_is_pass: true
verdict_at_entry: null
verdict_at_entry_disposition: REMEDIATED-PENDING-REVIEW
verdict_at_entry_plan_revision: 7
remediation_authorization: none-this-cycle
remediation_revision: null
remediation_performed: false
disposition: null
p0_open: 0
p1_open: 0
p2_open: 0
p3_open: 8
open_findings: [K5, K6, M3, M4, M5, N1, N2, N3]
findings_closed_at_this_attempt: [M1, M2, L2]
findings_raised_at_this_attempt: [N1, N2, N3]
hardening_required: true
hardening_present: true
hardening_sufficient: true
hardening_sufficiency_note: "The hardening pass now carries H1-H18. Attempt 06 recorded the pass insufficient for exactly two absences: no question asked whether a writer's precondition is consistent with the checks of the predicate it feeds, and none asked whether the observation moment a record mandates survives the execution environment that runs it. Revision 7 adds H17 for the first and H18 for the second, each stating the generalisable question rather than only the instance, and each answered against the revised text rather than asserted. The three new P3 findings raised at this attempt are accuracy defects in justification prose for commands whose mandated argv is correct, not gaps in the question set, so they do not reopen sufficiency."
attempt_06_findings_verified:
  - finding: "M1 — 177.007-T could write only after confirming the removal commit was the CURRENT TIP, a precondition strictly stronger than C4's reachability requirement and C5's removal-commit-or-descendant tolerance, so one intervening commit forbade the write under the atomic all-or-nothing rule, and because the path was already deleted no second removal commit could ever exist, leaving the pass state unrecoverable in-unit"
    severity: P2
    state: closed
    evidence: "Re-derived from the revision-7 text and from git behaviour, not accepted from the remediation narrative. (a) NO CURRENT-TIP REQUIREMENT SURVIVES. The plan's Probe workflow lifecycle row, its RC5 row, its CLEANUP_REMOVED_COMMIT field table, its C4 and C5 rows, 177.007-T step (1), 177.003-T's owed-obligations paragraph, 177-F and 183-S each state that the removal commit is never required to be the tip; RC5 is ancestor-or-equal, so a removal commit that happens still to be the tip also passes. A full-text audit of all nine surfaces found no remaining tip-identity precondition. (b) THE DERIVATION IS DETERMINISTIC AND REJECTS AMBIGUITY. RC1 requires exactly one line carrying one 40-character lowercase hex SHA and fails closed on empty or multi-line output; RC2 requires exactly one D line for the exact path; RC3 requires that same single line over .github/workflows/ so no other workflow file is touched; RC4 requires the path absent from the removal commit's own tree; RC5 requires reachability from the current HEAD; RC6 requires the creation commit in ancestry AND created-sha != sha; RC7 binds the SHA to committed history read before anything is staged, so it can never name the evidence commit. Nothing guesses, invents or pre-computes a SHA, and the atomic all-or-nothing rule forbids a partial or placeholder block. (c) IT IS ONE COMMIT, NOT A CLASS. RC1 with --max-count=1 yields the most recent commit touching the path; RC2 then requires that commit to be a deletion, so a later re-add resolves to fail-closed rather than to a second candidate. (d) IT SURVIVES FORWARD COMMITS, VERIFIED EMPIRICALLY. In a throwaway repository, after create, remove, then an unrelated bookkeeping commit, RC1 returned the removal commit, RC2 returned exactly one D line, RC3 returned that same single line, RC4 was empty, and RC5 and RC6 each exited 0. Repeated with an unrelated --no-ff merge landed on the branch after the removal, RC1 still returned the removal commit and RC5 still exited 0. (e) RE-EMISSION NEEDS NO SECOND REMOVAL. Because RC5 asks only for reachability and C5 accepts observed_tip as the removal commit or a descendant, a later re-run re-derives the same commit and records a later observed_tip; the plan, 177.007-T, 177.006-T, 177.003-T, 177-F and 183-S all state that no second deletion or removal commit is ever required, which is what makes the advertised in-unit ISOLATION_CLEANUP_FAILED remedy executable. (f) WRITER AND EVALUATOR CANNOT DIVERGE. C4 re-runs RC1 independently and requires the recorded SHA to equal what it yields, failing to EVIDENCE_INCONSISTENT otherwise, so the writer's precondition can no longer exceed the predicate. (g) C6 REMAINS INDEPENDENT. C6 is evaluated first, observes the current state directly, is forbidden to take that state from CLEANUP_TIP_OBSERVATION or CLEANUP_REMOVED_COMMIT, and is named on every surface as the final branch-state authority, so making the historical proof durable did not weaken the present-state check. M1 is closed on its own terms."
  - finding: "M2 — 177.007-T step (3) and 177.006-T check C6 both required a whole-tree empty git status --porcelain, in a repository whose backlog records under .backlogit are tracked and whose agents emit untracked checkpoint and memory files in normal operation, so the cleanliness premise of revision 6's one-normal-run derivation was falsified on a normal run"
    severity: P2
    state: closed
    evidence: "Re-derived from the revision-7 text and from git behaviour. (a) NO LIVE WHOLE-TREE REQUIREMENT SURVIVES. Every occurrence of 'git status --porcelain' across the plan, 177-F, 183-S and the seven task records was enumerated and classified: the live occurrences are PP2 on 177.006-T, 177.007-T and the plan's PP2 row, all carrying the exact-path pathspec; every other occurrence is historical narration of the defect in the frontmatter verdict note, the L1 explanation table, the M1/M2 remediation table, H18 and 183-S's history paragraph. The plan, 177.003-T, 177.006-T and 177.007-T each state affirmatively that whole-tree cleanliness is never observed, required or recorded anywhere in the unit. (b) THE PROBES ARE FIXED-ARGV AND EXACT-PATH. PP1 reads tracked-at-tip by ls-tree at HEAD; PP2 reads staged, unstaged and untracked residue by status with --porcelain=v1 --untracked-files=all and the exact pathspec; PP3 reads index residue by ls-files --cached --error-unmatch. Byte-identical path containment is required, a reported path that is not byte-identical or any directory form ending in / is ambiguous, and ambiguity raises TIP_UNOBSERVABLE rather than resolving in the passing direction. (c) THE FIVE-STATE CONTROL MATRIX BEHAVES EXACTLY AS SPECIFIED, VERIFIED EMPIRICALLY. In a throwaway repository with the path created, removed and committed: with an unrelated dirty tree (untracked note, untracked checkpoint under .backlogit/checkpoints, modified tracked README) PP1 was empty, PP2 was empty and PP3 exited non-zero, so cleanup passes; with an untracked copy at the exact path PP2 reported '?? <path>' so residue fails closed; with that copy staged PP3 exited 0 and PP2 reported 'A  <path>', so residue fails closed; with the path tracked at the tip PP1 returned exactly the one byte-identical line, so tracked-at-tip fails closed; with the path tracked and additionally modified PP1 still returned that line, and because C6 evaluates tracked-at-tip before residue the reported token is WORKFLOW_PRESENT_AT_TIP, which is the truthful fact in that case. (d) UNRELATED WORK CANNOT BLOCK A PASS AND EXACT-PATH RESIDUE CANNOT REACH ONE. The first control is precisely the condition that falsified revision 6, and it now passes; the remaining four all fail closed, still force ISOLATION_CLEANUP_FAILED, and still block 181-S harvest. (e) THE COMPOUND RECORD IS NOW CITED. R14 cites docs/compound/2026-08-16-multiple-implementation-worktrees-blocks-topology-gate-globally.md, the prior record of a whole-tree cleanliness gate misfiring on unrelated content, which attempt 06 recorded as cited by neither the plan nor any 177.x record. M2 is closed on its own terms."
attempt_05_findings_verified:
  - finding: "L2 — the C6 reason token WORKFLOW_PRESENT_AT_TIP was raised on a dirty working tree as well as on a present path, so a verdict line could assert the workflow is present at the tip when it was absent, while the line form carried workflow_path alongside that token and the advertised remedy was a no-op against the actual cause"
    severity: P3
    state: closed
    evidence: "Closed by independent derivation from the plan text and 177.006-T's record, and expressly NOT from the stash capture, which disclaims authority on finding state and which explicitly leaves the judgement to this attempt. The reason table on both surfaces now reads WORKFLOW_PRESENT_AT_TIP as raised when PP1 reports the exact path tracked at the current branch tip, adding in terms that this token means that and nothing else and is never raised for a working-tree or index condition. The two facts L2 named are now separated: exact-path index or worktree residue raises the distinct token WORKFLOW_PATH_RESIDUE, and an unobservable tip or any probe output outside its accepted shape raises TIP_UNOBSERVABLE. The dirty-tree case L2 was raised against no longer reaches the predicate at all when the dirt is unrelated, because no limb observes anything but the one path. The ISOLATION_CLEANUP_FAILED line form still carries workflow_path, and that field is now truthful under every token that can accompany it: under WORKFLOW_PRESENT_AT_TIP the path is tracked at the tip, and under WORKFLOW_PATH_RESIDUE the path carries residue. The advertised remedy is correspondingly no longer a no-op: the plan, 177.003-T, 177.006-T and 177-F each instruct removing the workflow if it is still tracked AND clearing any exact-path staged, unstaged or untracked residue. The empirical control matrix under M2 confirms that no input produces WORKFLOW_PRESENT_AT_TIP while the path is absent at the tip. L2 is closed as raised; its severity was not lowered and no count was moved to reach that result."
  - finding: "K5 — the FLOOR_INVOKED verdict-line literal differs by a dash between the plan (em dash) and its sole writer 177.004-T (hyphen-minus)"
    severity: P3
    state: open
    evidence: "Independently re-verified unchanged at revision 7 by byte comparison. The plan still prints 'I1_GATE: FLOOR_INVOKED | verdict=NOT DETERMINED — FLOOR INVOKED | blocked_by=<short-reason> | checked=2026-09-DD' with an em dash; 177.004-T still prints the same line with a hyphen-minus. The OPEN/CLOSED predicate keys on the first field's token only and both surfaces agree that token is FLOOR_INVOKED, so no gate decision turns on it. The revision-7 cycle did not touch 177.004-T. Carried, not invalidated."
  - finding: "K6 — the plan does not record that I2's evidence is observed in a job that performs no acquisition, so the after-acquisition relation is task-level across two hosted-runner jobs rather than in-job"
    severity: P3
    state: open
    evidence: "Independently re-verified unchanged at revision 7. 177.001-T still dispatches its own i2-i3-egress probe and still carries no gate read precisely because it touches nothing untrusted, which remains the correct security posture; the plan's only occurrence of a weakening word is in the M1 discussion about the present-state check, not about I2. Carried, not invalidated."
attempt_06_p3_findings_verified:
  - finding: "M3 — four of seven task records still cite plan revision 5"
    severity: P3
    state: open
    evidence: "Independently re-verified at revision 7 and, as predicted by the bounded cycle, unchanged in substance. 177.001-T, 177.002-T, 177.004-T and 177.005-T each still close with 'revision 5, awaiting independent attempt 05', while 177.003-T, 177.006-T and 177.007-T now close with 'revision 7, awaiting independent attempt 07'. The divergence is now two revisions wide rather than one. No executable behaviour keys on the label; graded P3 for provenance only. Carried."
  - finding: "M4 — the date placeholder literal differs between the plan and the emitting records"
    severity: P3
    state: open
    evidence: "Independently re-verified unchanged at revision 7. The plan still prints checked=2026-09-DD in the I1_GATE and COMPOSED_STATE forms and observed_at=2026-09-DD in the CLEANUP_ block; 177.004-T and 177.006-T still print checked=<date>, and 177.007-T and C5 in 177.006-T still print observed_at=<date>. The revision-7 cycle renamed the adjacent third field on both surfaces and deliberately left the placeholder untouched. Carried."
  - finding: "M5 — one of the four dispatch identifiers has no recorded capture owner"
    severity: P3
    state: open
    evidence: "Independently re-verified unchanged at revision 7. 177.001-T, 177.002-T and 177.005-T each still carry the instruction to record their dispatch's workflow-run ID and URL; a full-text scan of 177.004-T found no occurrence of 'run ID', 'run_id' or 'workflow-run'. The plan-level obligation in Probe workflow lifecycle is unchanged, which is why this stays P3, and the failure mode remains fail-closed EVIDENCE_MISSING rather than a false pass. Carried."
persona_coverage:
  - persona: constitution
    status: complete
    mode: inline
    trigger: "Plan-review gate on a queued shipment with an immutable attempt roster, a mutable verdict manifest, operator-declared terminality and per-state successor-eligibility authority."
    findings: none
  - persona: python
    status: complete
    mode: inline
    trigger: "Repository ships a Python CLI under src/autoharness. Checked for scope overlap only; this unit ships no production code and touches no Python surface."
    findings: none
  - persona: scope-boundary
    status: complete
    mode: inline
    trigger: "Spike unit with a declared floor, an external tracker held blocked, a successor plan gated on a composed-state token, and a bounded remediation cycle scoped to two named findings."
    findings: none
  - persona: learnings
    status: complete
    mode: inline
    trigger: "Compound library carries prior records on porcelain-based cleanliness gates and on review-loop convergence for novel safety-critical work."
    findings: none
  - persona: architecture
    status: complete
    mode: inline-same-model
    trigger: "Plan defines a two-step evidence lifecycle, a seven-step removal derivation, a three-probe cleanliness contract, a six-check predicate with a declared first-failure order, a six-token reason vocabulary and a five-state precedence gating a successor shipment."
    findings: N3
  - persona: agent-native-parity
    status: complete
    mode: inline-same-model
    trigger: "Every limb of this plan is executed and evaluated by agents reading task records as their execution contract, using fixed-argv git plumbing whose stated rationale an agent may rely on when maintaining the contract."
    findings: N1, N2, N3
  - persona: security-lens
    status: complete
    mode: inline-same-model
    trigger: "Plan defines credential-absence determination, untrusted external asset acquisition, adversarial containment probing, egress denial, and the removal of a committed CI surface that runs on hosted runners."
    findings: none
tags:
  - "plan-review"
  - "spike"
  - "ci-isolation"
  - "supply-chain"
  - "safe-close"
  - "portfolio-2026-09-18"
---

# Plan review attempt 07 — Conformance isolation spike (S2)

Attempt 06's eight open findings were **independently re-derived from the plan,
the seven `177.x` task records, `177-F`, the `183-S` shipment record, backlogit
`item_deps`, the shipment manifest, the governing decision, the compound library
and the working tree**, and — where the claim was about git behaviour rather
than about text — from **bounded controls run in throwaway repositories outside
this repository**. No closure summary was trusted. The P3 follow-up stash entry
`5E45691A` was read only to verify capture and scope, never as an authority on
finding state.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` |
| Reviewed revision | 7 |
| Reviewed content HEAD | `4a28eb4a` (committed) |
| Verdict at entry | `null`, disposition `REMEDIATED-PENDING-REVIEW` at plan revision 7 |
| Covering feature / shipment | `177-F` / `183-S` (queued, 8 members) |
| Unit role | precursor spike, DAG root |
| External tracker | `002-C`, `blocked`, outside every manifest |
| Governing decision | 2026-09-18 shared-execution-architecture, revision 1 |
| Dispatch mode | `single-agent-declared-degradation` |
| Terminal | yes — operator-declared terminal attempt 07 |
| Gate result | **PASS** |
| Decision | **PASS** |

## Dispatch and coverage

All seven personas were applied inline, each with its own finding list.
Reviewer personas are **leaf executors** and spawned nothing. Engram remained
**circuit-open** and was **not** retried; intercom and graphtor-docs were
unavailable, so operator visibility is local-only. No remediation was performed
and none is proposed. No anchor route exists in `model_routing`, so the
cross-model rubrics ran same-model; that is recorded, not compensated for.

## `M1` is closed — the removal proof is durable, and it was tested against real git

`M1` said the writer's precondition was stronger than the predicate it feeds and
that, once it failed, it could never be satisfied again. Revision 7 removes the
precondition rather than weakening the predicate.

### No surface still requires the removal commit to be the tip

A full-text audit of the plan, `177-F`, `183-S` and all seven task records found
**no remaining tip-identity precondition**. What replaced it is stated
identically on the writer's surface (`177.007-T` step 1), the evaluator's (`C4`,
`RC1`–`RC7`), the remover's (`177.003-T`, "it does not owe the predicate a tip
position"), and both rollup records: the removal commit must **exist**, **delete
exactly** the probe-workflow path, **touch no other workflow file**, be **absent
from its own tree**, be **reachable from the current `HEAD`**, and carry the
**creation commit in its ancestry**. `RC5` is ancestor-**or-equal**, so a removal
commit that happens still to be the tip is accepted — accepted, never required.

### The derivation identifies exactly one commit and rejects ambiguity

`RC1` demands exactly one line carrying one 40-character lowercase hex SHA and
fails closed on empty output, multiple lines or any other shape. `RC2` demands
exactly one `D` line for the exact path, so a candidate that is *not* a deletion
cannot be adopted; `RC3` demands that same single line over `.github/workflows/`,
so a commit that also touched another workflow file cannot be adopted; `RC4`
demands the path absent from the candidate's own tree. `RC6` requires the
creation commit in ancestry **and** `<created-sha> ≠ <sha>`, which forbids a
degenerate identity. `RC7` binds the SHA to history read **before** anything is
staged, so no field can name the evidence commit. The atomic all-or-nothing rule
forbids a partial block, a placeholder line, and a guessed, invented or
pre-computed SHA outright.

### It was verified against git, not only against the text

Two bounded controls were run in throwaway repositories under `TEMP`:

| Control | Result |
|---|---|
| create → remove → **unrelated bookkeeping commit** | `RC1` returned the removal commit; `RC2` returned exactly one `D` line for the exact path; `RC3` returned that same single line; `RC4` was empty; `RC5` exit `0`; `RC6` exit `0` |
| create → remove → **unrelated `--no-ff` merge landed on the branch** | `RC1` still returned the removal commit; `RC5` still exit `0` |

So a later unrelated forward commit — including the tracked-`.backlogit`
bookkeeping commits that produced `M1` — does not disturb the derivation, and
neither does a merge.

### Re-emission is reachable, and writer and evaluator cannot diverge

Because `RC5` asks only for reachability and `C5` accepts `observed_tip` as the
removal commit **or a descendant**, a re-run at any later point re-derives the
**same** removal commit and records a later `observed_tip`. Every carrying
surface states that **no second deletion or removal commit is ever required**,
which is exactly what `M1` found missing: the advertised in-unit
`ISOLATION_CLEANUP_FAILED` remedy is now executable rather than advertised.
`C4` re-runs `RC1` itself and requires SHA equality, failing to
`EVIDENCE_INCONSISTENT` on a mismatch, so the writer's precondition can no
longer exceed what the predicate checks.

### The independent current-state check is untouched

`C6` is still evaluated **first**, still observes the current state **directly**
before the evaluator stages anything, is still forbidden to take that state from
`CLEANUP_TIP_OBSERVATION` or `CLEANUP_REMOVED_COMMIT`, and is still named on
every surface as the **final branch-state authority**. Making the historical
proof durable did not make the present-state check weaker. `M1` is **closed**.

## `M2` is closed — cleanliness is exact-path-scoped, and the five states were exercised

### No live whole-tree requirement survives

Every occurrence of `git status --porcelain` across the plan, `177-F`, `183-S`
and the seven task records was enumerated and classified. The **live** ones are
the three `PP2` specifications, each carrying the exact-path pathspec. Every
other occurrence is **historical narration** of the defect itself — the
frontmatter note, the `L1` explanation table, the `M1`/`M2` remediation table,
`H18`, and `183-S`'s history paragraph. The plan, `177.003-T`, `177.006-T` and
`177.007-T` each state affirmatively that whole-tree cleanliness is **never**
observed, required or recorded anywhere in the unit.

### The controls behave exactly as specified

Run in a throwaway repository with the probe path created, removed and
committed:

| Control | `PP1` | `PP2` | `PP3` exit | Specified outcome | Observed outcome |
|---|---|---|---|---|---|
| Unrelated dirty tree (untracked note, untracked `.backlogit/checkpoints/` file, modified tracked file) | empty | empty | non-zero | clean — cleanup may pass | **clean** |
| Untracked copy at the exact path | empty | `?? <path>` | non-zero | `WORKFLOW_PATH_RESIDUE` | **residue** |
| Staged copy at the exact path | empty | `A  <path>` | `0` | `WORKFLOW_PATH_RESIDUE` | **residue** |
| Path tracked at the tip | one byte-identical line | empty | `0` | `WORKFLOW_PRESENT_AT_TIP` | **tracked at tip** |
| Path tracked **and** modified in the worktree | one byte-identical line | ` M <path>` | `0` | `WORKFLOW_PRESENT_AT_TIP` (tracked-at-tip evaluated first) | **tracked at tip** |

The first row is precisely the condition that falsified revision 6, and it now
passes. The other four all fail closed, still force `ISOLATION_CLEANUP_FAILED`,
and still block `181-S` harvest outright. **Fail-closed was narrowed, not
loosened.**

### Ambiguity resolves against the pass

A non-zero exit, a reported path that is not byte-identical, a directory form
ending in `/`, or an unresolvable tip each raise `TIP_UNOBSERVABLE`. A staged
rename would present an `old -> new` path field, which is not byte-identical and
therefore also fails closed. No probe outcome resolves an unrecognised shape in
the passing direction.

### The prior learning is now cited

`R14` cites
`docs/compound/2026-08-16-multiple-implementation-worktrees-blocks-topology-gate-globally.md`,
the compound record of a whole-tree cleanliness gate misfiring on unrelated
content — which attempt 06 recorded as cited by neither the plan nor any
`177.x` record. `M2` is **closed**.

## `L2` is closed — and closed on derivation, not on its stash capture

`L2` was re-evaluated **only** because the token split touches the exact clause
it names, and it is judged on the plan text and `177.006-T`'s record alone. The
stash entry that carries `L2` disclaims authority and defers the judgement to
this attempt; that deferral was honoured, and the entry was not used as
evidence.

`L2`'s defect had three limbs, and each is now addressed:

1. **One token, two facts.** `WORKFLOW_PRESENT_AT_TIP` is narrowed to the
   tracked-at-tip case, with both surfaces adding that the token *means that and
   nothing else and is never raised for a working-tree or index condition*.
   Exact-path residue raises `WORKFLOW_PATH_RESIDUE`; unobservable or
   out-of-shape probe output raises `TIP_UNOBSERVABLE`.
2. **A line that named a path it was wrong about.** The
   `ISOLATION_CLEANUP_FAILED` form still carries `workflow_path=`, and that field
   is now truthful under every token that can accompany it — tracked at the tip
   under the first, carrying residue under the second.
3. **A remedy that was a no-op against the actual cause.** The remedy now reads
   *remove the workflow if it is still tracked there, **clear any exact-path
   staged, unstaged or untracked residue**, re-emit, re-run*, on the plan,
   `177.003-T`, `177.006-T` and `177-F`.

The empirical matrix above confirms no input yields `WORKFLOW_PRESENT_AT_TIP`
while the path is absent at the tip. `L2` is **closed as raised**. Its severity
was not lowered and no count was moved to reach that result.

## New finding `N1` (P3) — `RC1`'s stated rationale for `--full-history` names the wrong trigger

`RC1` mandates `--full-history` and justifies it on all three carrying surfaces
(the plan's `RC1` row, `177.007-T`, `177.006-T`) with:

> `--full-history` **is mandatory**: default history simplification prunes the
> deletion commit once the path is absent at `HEAD` and the command returns
> empty.

The stated mechanism is **not what git does**. Verified in throwaway
repositories:

| Topology | `git rev-list --max-count=1 HEAD -- <path>` | with `--full-history` |
|---|---|---|
| create → remove → later commit (linear, path absent at `HEAD`) | **returns the removal commit** | returns the removal commit |
| create → remove → unrelated `--no-ff` merge onto the same branch | **returns the removal commit** | returns the removal commit |
| create **and** remove on a side branch, then `--no-ff` merge into `main`, read from `main` | **returns empty** | **returns the removal commit** |

So absence of the path at `HEAD` does **not** prune the deletion commit; what
prunes it is **merge simplification** when the create-and-delete pair lives
entirely on a merged side branch whose merge is TREESAME to the first parent —
which is exactly the topology this branch enters if it is ever merged and the
derivation is re-run from the merge target.

**The mandate is correct and must be kept.** The finding is that its
justification names a trigger that is demonstrably false on the topology an
executor is most likely to test, and a maintainer who tests the claim, finds it
false, and drops the flag would reintroduce a real failure mode. Graded **P3**
because the consequence is **fail-closed**: an empty `RC1` produces no block,
which resolves `CLEANUP_FAILED | cleanup=EVIDENCE_MISSING`, a non-pass,
harvest-blocking state — never a false pass, and never an unsafe execution.

*Plain-language scope, recorded as scope and not as a proposal:* the rationale
sentence on the three surfaces would state the merge-simplification trigger
rather than the path-absent-at-`HEAD` trigger; the argv would not change.

## New finding `N2` (P3) — `PP2`'s stated rationale for `--untracked-files=all` names a case that cannot arise under its own pathspec

`PP2` mandates `--untracked-files=all` and justifies it on all three carrying
surfaces with:

> `--untracked-files=all` is mandatory so an untracked copy inside an
> otherwise-untracked directory is reported as the file rather than collapsed
> into a directory entry.

With the mandated **exact-path pathspec**, that collapse does not occur.
Verified: with `.github/` entirely untracked, `git status --porcelain=v1 --
<exact path>` reports `?? .github/workflows/spike-177-isolation-probe.yml`
**without** the flag; the directory form `?? .github/` appears only when **no**
pathspec is given.

**The flag is nevertheless load-bearing — for a stronger reason the text does
not give.** Untracked reporting is configurable, and the configuration can
suppress it. Verified: with `status.showUntrackedFiles=no`, `git status
--porcelain=v1 -- <exact path>` returns **empty** while an untracked copy sits at
that exact path, and adding `--untracked-files=all` restores the `?? <path>`
line. Omitting the flag is therefore a **fail-open** under a repository-level or
global setting the executing agent does not control, which is strictly more
serious than the collapse case the text names.

Graded **P3**, not P2: the flag **is** mandated on every surface, so the
fail-open is not reachable by an executor that follows the contract as written.
The defect is that the contract's own reasoning would not survive
inspection, and an editor who verified the stated case and found it vacuous
could remove the one thing preventing a fail-open.

*Plain-language scope:* the rationale would name configuration independence —
`status.showUntrackedFiles` — as the reason the flag is mandatory, and state
that omitting it can silently miss untracked residue; the argv would not change.

## New finding `N3` (P3) — `177.007-T` consumes the creation SHA in step (1) while instructing it be read in step (4)

`177.007-T`'s numbered contract runs `RC1`–`RC7` as **step (1)**. `RC6` requires
`git merge-base --is-ancestor <created-sha> <sha>` and `<created-sha> ≠ <sha>`,
so it consumes `177.004-T`'s creation SHA. The record instructs that value to be
read at **step (4)**: *Read `177.004-T`'s creation commit SHA and the four
dispatch run IDs and URLs from the records already produced*. The plan's binding
observation-order paragraph has the same shape, placing the creation-SHA read
after the `RC1`–`RC7` confirmation.

Nothing is unsatisfiable: the creation SHA exists in `177.004-T`'s record long
before this task starts, so an executor simply reads it earlier. The finding is
that a **numbered execution contract consumes a value one step before the step
that acquires it**, in a record whose whole purpose is to be followed literally
by an agent, and in a unit whose two most recent P2 findings were both about a
contract being unsatisfiable at the moment it was mandated.

Graded **P3**: no value is unavailable, no check is weakened, nothing fails
open, and the atomic all-or-nothing rule already covers the case where the value
cannot be read at all.

*Plain-language scope:* the creation-SHA read would be named as a step (0)
input, or `RC6` would state that it consumes the value read in step (4); the
checks themselves would not change.

## Verified safe — recorded so a later attempt does not re-raise them

* **The `I1` verdict gate is intact and unchanged.** `177.004-T` remains the
  sole writer of a single non-secret `I1_GATE:` line; `177.005-T` and
  `177.002-T` each carry the gate read as their **first action** and fail closed
  to `NOT DETERMINED — FLOOR INVOKED` naming `I1` on anything but `ACHIEVABLE`,
  including missing, unreadable, multi-line and unrecognised-token cases;
  `177.001-T` carries no gate read and inherits the precedence through
  `177.005-T`, with `I3` ungated. `177.007-T` correctly carries **no** gate read
  and states why. The revision-7 cycle widened no gated surface.
* **No-secret and no-credential evidence rules are intact.** The `CLEANUP_`
  block carries paths, commit identities, run identifiers, URLs and a date only,
  under the same binding R6 rule as the `I1` inventory and the gate line. The
  renamed field `path_clean_at_observation` carries `yes` and no content. No new
  field can carry a value.
* **Network isolation is intact.** `177.007-T` and `177.006-T` are each local,
  offline and credential-free; `RC1`–`RC7` and `PP1`–`PP3` read only the local
  repository. Acquisition-then-no-network is unchanged.
* **Workflow rollback is intact.** One creation owner, one exact path, one
  removal owner and point, rollback by `git revert` of the single creation
  commit or deletion of the single added path. `git ls-files .github/workflows`
  at the reviewed HEAD returns only `ci.yml` and `release.yml`, so no probe
  workflow exists yet — the pre-execution state the plan describes.
* **Removal → evidence → evaluation ordering is enforced in `item_deps`.**
  `177.007-T` depends on `177.003-T`; `177.006-T` depends on both `177.003-T`
  and `177.007-T`. The `183-S` manifest order is `177-F`, `177.004-T`,
  `177.005-T`, `177.001-T`, `177.002-T`, `177.003-T`, `177.007-T`, `177.006-T` —
  parent first, then dependency order.
* **Sizing is within the 2-hour rule on both axes.** All seven tasks carry
  `size` and `complexity` with `size_source: agent` and
  `size_ruleset_version: v1`; the shipment rollup reports four `S`, three `XS`,
  zero unsized. Elapsed bounds are 90, 90, 120, 120, 45, 30 and 30 minutes.
  `177.002-T`'s `complexity: high` still carries its declared de-risking
  rationale. The three closing tasks are `XS`/`low` at 30–45 minutes, so
  splitting the lifecycle across three tasks did not push any task past the
  rule.
* **`183-S` is a DAG root with no incoming edge**, `depends_on_shipments: []`,
  and `181-S` reads only the composed-state token — never the block or its
  checks. Per-state successor eligibility is unchanged: `ISOLATION_CLEANUP_FAILED`
  authorises nothing, `ISOLATION_FLOOR_ONLY` floor-only, `002-C` blocked under
  all five states.
* **The five-state precedence remains a total function**, re-derived by case
  analysis over `{DETERMINED, FLOOR_INVOKED, ABSENT}` × `{PROVEN, FAILED}`, with
  the cleanup test above both harvest-eligible states.
* **Cross-references resolve.** The decision, the `181-S` plan, both cited
  compound records and `docs/spikes/` all exist. The plan carries no unresolved
  `{{...}}` placeholder; `2026-09-DD` and `<date>` are declared line-form
  placeholders, and their divergence is already `M4`.
* **Not graded — an ignored copy at the exact path is outside `PP2`.** `PP2`
  does not pass `--ignored`, so an *ignored* untracked copy would not be
  reported. Followed to the end: the path is not ignored in this repository
  (`git check-ignore` exits non-zero for it), an untracked file is not on the
  branch and cannot be executed by GitHub, and `C6`'s subject is branch state.
  No eligibility leak. Recorded, not graded.
* **Not graded — step 5 of the plan's reachability derivation names the
  evidence commit as the tip at evaluation time.** That is an illustrative
  instance of the general case step 4 already declares immaterial, and `C6`'s
  own definition carries no tip-identity requirement, so a bookkeeping commit
  between the evidence commit and the evaluation changes nothing. Narrative
  only. Recorded, not graded.
* **Not graded — `C3` checks set membership while the writer mandates order.**
  Re-verified unchanged; the writer is stricter than the evaluator, which is
  harmless. Recorded at attempts 05 and 06 and still not graded.
* **Not graded — the `ISOLATION_UNDETERMINED` line form carries no cleanup
  field**, so an `ABSENT` row masks the cleanup result. Both states block
  harvest outright, so this is not an eligibility leak. As at attempts 05 and 06.

## P3 follow-up stash verification

`5E45691A` was read **read-only** and holds **exactly** the six P3 findings open
against `183-S` at entry to this attempt — `K5`, `K6`, `L2`, `M3`, `M4`, `M5` —
at `priority: low`, `kind: task`, explicitly marked as not for the current
shipment scope and as blocking nothing. It is **not triaged, not harvested, not
parented, and in no manifest**: the `183-S` manifest carries exactly `177-F` and
the seven `177.x` tasks, and no backlog item references the entry. The two P2
findings `M1` and `M2` are correctly **absent** from it. The entry states in
terms that it has never been an authority on finding state and that `L2`'s
judgement belongs to this attempt; both were honoured.

The revision-7 cycle's only stash mutation was a single-line in-place edit of
`5E45691A`. Entries `711CA657` and `8DE3047F` are present and unchanged, and the
finding labelled `M4` in `8DE3047F` belongs to a different review series and is
**not** this `M4`.

**`N1`, `N2` and `N3` were raised by this review and are NOT stashed by it.** A
review does not triage, harvest or capture its own findings; they are available
for explicit operator disposition, and the entry above is left exactly as found.

## Finding summary

| ID | Severity | State | One line |
|---|---|---|---|
| `M1` | P2 | **closed at this attempt** | Removal proof is durable, not positional: `RC1`–`RC7` derive one reachable removal commit from content and ancestry, never from tip position |
| `M2` | P2 | **closed at this attempt** | Every cleanliness limb is exact-path-scoped via `PP1`–`PP3`; no live whole-tree requirement survives, and unrelated work cannot block a pass |
| `L2` | P3 | **closed at this attempt** | Reason vocabulary split; `WORKFLOW_PRESENT_AT_TIP` narrowed to tracked-at-tip, residue and ambiguity carry their own truthful tokens |
| `K5` | P3 | open, carried | Gate-line dash literal differs between the plan and `177.004-T` |
| `K6` | P3 | open, carried | The plan does not note that `I2`'s after-acquisition relation is task-level across two jobs |
| `M3` | P3 | open, carried | Four determining-task records still cite plan revision 5 — now two revisions stale |
| `M4` | P3 | open, carried | Date placeholder literal differs between the plan and the emitting records |
| `M5` | P3 | open, carried | `177.004-T` alone lacks the dispatch run-ID and URL capture instruction |
| `N1` | P3 | **raised at this attempt** | `RC1`'s `--full-history` rationale names the wrong trigger; the mandate is correct and must be kept |
| `N2` | P3 | **raised at this attempt** | `PP2`'s `--untracked-files=all` rationale names a vacuous case; the flag's real justification is configuration independence |
| `N3` | P3 | **raised at this attempt** | `177.007-T` consumes the creation SHA in step (1) while instructing it be read in step (4) |

Counts: **0 P0, 0 P1, 0 P2, 8 P3**. No severity was lowered, no count
decremented, and no finding folded into another.

## Decision

**Gate result `PASS`. Decision `PASS`.** Zero P0, zero P1 and zero P2 findings
remain open against plan revision 7 at content HEAD `4a28eb4a`. The eight open
findings are all **P3**, and no policy in
`.github/policies/workflow-policies.md` makes a P3 blocking — the blocking
predicate there is *unresolved P0/P1 findings*.

**`183-S` is publication-eligible.** Both P2 findings that held it back were
re-derived closed by this attempt from the repository, not from a narrative, and
the pass state `ISOLATION_CHARACTERIZED` is now reachable on a **first, normal,
spec-conformant execution** in this repository's actual execution environment —
with agent checkpoints, session notes and tracked-backlog bookkeeping present —
and equally reachable on any later re-emission, without a waiver, a guessed SHA,
a corrective cycle, a second removal commit or a whole-tree cleanliness claim.
It remains **structurally unreachable** while the probe workflow is tracked at
`HEAD` or present as exact-path residue.

**This attempt is terminal.** No remediation was performed, **none is proposed**,
and no remediation cycle is authorized by this artifact. The eight open P3
findings are available for explicit operator disposition; they block nothing.

**`PASS` is a judgement on the plan, not an authorization to Ship.** It clears
`183-S` for staging publication and makes `181-S` harvestable **only** through
the composed-state token the spike will emit — never in advance of it. `002-C`
stays `blocked`, outside every manifest, under all five composed states.

## Root-wave position

`183-S` is one of the portfolio's three DAG roots. With this attempt the wave is
complete:

| Root | Feature | Latest independent attempt | Verdict | Open P2 | Open P3 |
|---|---|---|---|---|---|
| `177-S` | `169-F` | 07, terminal | **PASS** | 0 | 6 |
| `182-S` | `176-F` | 04, terminal | **PASS** | 0 | 3 |
| `183-S` | `177-F` | **07, terminal** | **PASS** | **0** | **8** |

All three roots are now cleared of P0, P1 and P2 and are collectively eligible
for staging publication. No successor shipment is unblocked by this artifact:
successors remain gated on their own reviews and, for `181-S`, on the spike's
emitted composed-state token.
