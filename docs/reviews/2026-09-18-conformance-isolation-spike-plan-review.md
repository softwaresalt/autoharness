---
title: "Plan review verdict manifest — Conformance isolation spike (S2)"
description: "Mutable verdict manifest for docs/plans/2026-09-18-conformance-isolation-spike-plan.md. This file is a selection surface, not a review: it names which immutable attempt artifact is authoritative right now, and nothing else. The reviews live one per attempt under docs/reviews/review-history/ and are never edited after they are written. Latest attempt: 05, terminal, which judged plan revision 5 at content HEAD 24e19050 and returned gate result ADVISORY, decision ADVISORY, on zero P0, zero P1, one P2 and three P3. Attempt 05 independently re-derived K3 CLOSED and K4 CLOSED, carried K5 and K6 open, and raised one new P2 L1 and one new P3 L2. Plan revision: 5. Independent attempt 01 reviewed revision 1 at content HEAD db39553a and returned FAIL/BLOCKED on one P0, one P1, two P2 and one P3. A Stage remediation cycle produced revision 2, and independent attempt 02 reviewed that revision at content HEAD 5aa8643f, verified all five attempt-01 findings closed and returned FAIL/BLOCKED on zero P0, one P1, one P2 and one P3. A second Stage remediation cycle produced revision 3, and independent attempt 03 reviewed that revision at content HEAD 4b4330b9 and returned gate result FAIL, decision BLOCKED, on zero P0, one P1, one P2 and zero P3. Attempt 03 verified F1, F2 and F3 all genuinely closed, and found a new defect in the mechanism that closes F1: a blocks edge gates on predecessor completion, not on an achievable I1 verdict, so both the 90-minute floor-invoked outcome and an explicit NOT ACHIEVABLE verdict clear the edge and permit the untrusted-credential acquisition and probe tasks to run in a job whose credential absence is unverified or affirmatively falsified, which blast radius, H7, H9, R8 and the 177.004-T record all forbid. No stop condition exists anywhere in the plan or the six task records. That is the open P1, K1. The open P2, K2, is that four determining tasks require GitHub-hosted-runner jobs, which requires committing a probe workflow to the branch, while blast radius said no tracked surface outside docs/spikes/ is mutated and no task owned the workflow's creation or removal. The operator then lifted the terminal designation and authorized a third and final bounded remediation cycle, which produced revision 4: K1 was addressed by separating ordering from safety, retaining the blocks edges as ordering and adding an executable verdict predicate - 177.004-T emits a single non-secret I1_GATE line and 177.005-T and 177.002-T read it as their first action, failing closed to NOT DETERMINED - FLOOR INVOKED naming I1 on anything but ACHIEVABLE, which forces ISOLATION_FLOOR_ONLY and makes ISOLATION_CHARACTERIZED structurally unreachable; K2 was addressed by stating that the probe workflow is committed and giving it an owning task, one exact path, a dispatch model, a removal owner and point, a rollback and branch-cleanliness evidence, with blast radius and rollback reconciled truthfully. Both findings are recorded as addressed pending review, not closed, and the plan now awaits independent attempt 04. Independent terminal attempt 04 then reviewed revision 4 at content HEAD 42f2f8ec and returned gate result ADVISORY, decision ADVISORY, on zero P0, zero P1, one P2 and three P3. Attempt 04 verified K1 and K2 genuinely closed by re-derivation from the plan, the six task records, 177-F, 183-S and the working tree, and raised one new P2, K3: 177.006-T's record mandates a fourth branch-cleanliness check that must emit no pass on a dirty branch, but the plan defines its four composed states exhaustively as functions of the seven-entry coverage ledger, so an all-DETERMINED ledger on a branch still carrying the probe workflow forces the passing state and no token can express unclosed spike. K3 is graded P2 on consequence - a leftover workflow_dispatch-only workflow with minimal permissions and no secrets, reverted in one commit, with no untrusted execution and no credential exposure - and no severity was lowered to reach a closable state. K4, K5 and K6 are advisory P3. Attempt 04 is terminal, so no further remediation cycle is authorized; K3 is available for operator disposition. The plan is cleared of P0/P1 and eligible for staging publication, but ADVISORY is not a PASS, the plan is not Ship-ready, and 181-S becomes reviewable as a plan without becoming harvestable. No PASS exists anywhere in this record and none is asserted. Independent terminal attempt 05 then reviewed revision 5 at content HEAD 24e19050 and returned gate result ADVISORY, decision ADVISORY, on zero P0, zero P1, one P2 and three P3. It re-derived K3 closed - the final state is no longer ledger-only because ISOLATION_CHARACTERIZED now requires the seven-entry ledger AND CLEANUP_PROVEN, C6 independently re-observes the branch tip and is evaluated first, C2 and C4 check creation and removal evidence against the repository, the five-state precedence was re-derived total and deterministic by case analysis, ISOLATION_CLEANUP_FAILED sits above both harvest-eligible states, absence of the block is EVIDENCE_MISSING and never ISOLATION_NOT_OBSERVED, and the block format, sole writer, sole evaluator, C1-C6 semantics, reason vocabulary and successor eligibility agree across the plan, 177.003-T, 177.006-T, 177-F and 183-S, with I1 gating, the no-credential evidence rule, no-network-after-acquisition and rollback intact and reachable - and re-derived K4 closed on the rewritten four-check enumeration, on re-derivation and expressly not on its stash capture. It carried K5 and K6 open and raised one new P2, L1: the eight-line CLEANUP_ block is mandated to be written in the same commit that removes the workflow, while CLEANUP_REMOVED_COMMIT must name that commit's own SHA and CLEANUP_TIP_OBSERVATION must record a clean working tree and a tip SHA, so no spec-conformant first emission exists, C4 and C5 cannot be satisfied on a first pass, and at least one spurious ISOLATION_CLEANUP_FAILED cycle is forced. L1 is graded P2 rather than P1 because the failure is fail-closed and the plan's own in-unit remedy reaches the pass state on a second emission without a waiver or a determining re-run, and P2 rather than P3 because it is a mechanical impossibility in a machine-evaluated predicate's input contract agreed across two surfaces. It also raised one new P3, L2: the C6 reason token WORKFLOW_PRESENT_AT_TIP is raised on a dirty working tree as well as on a present path, so a verdict line can assert the workflow is present at the tip when it is absent. No severity was lowered and no count decremented. Attempt 05's terminal designation was subsequently lifted by the operator for one bounded remediation cycle scoped to the single open P2, L1. That cycle produced plan revision 6: the cleanup lifecycle is split into a removal step (177.003-T, which now writes no CLEANUP_ line) and a separate bounded cleanup-evidence step (a new task 177.007-T, the sole writer of the eight-line block, which observes the already-existing removal commit and writes the block in its own evidence commit), the tip-observation field is renamed to name the tip that was observed rather than the commit that records it, C4 and C5 are restated against values that exist before they are recorded, and C6 remains the evaluator's independent observation of the CURRENT tip and the final branch-state authority. The five-state vocabulary, ISOLATION_CLEANUP_FAILED and its five-token reason vocabulary, the I1 verdict gate, the no-credential and no-secret evidence rule, the acquisition-then-no-network model, the workflow rollback and the per-state 181-S eligibility rules are preserved unchanged. L1 is recorded as ADDRESSED PENDING REVIEW, not closed; K5, K6 and L2 were out of scope and remain open and unaddressed. No count is decremented and no PASS is asserted. Independent terminal attempt 06 then reviewed revision 6 at content HEAD 7768c5d5 and returned gate result ADVISORY, decision ADVISORY, on zero P0, zero P1, two P2 and six P3. It re-derived L1 CLOSED on its own terms - the eight-line block's every field now names a value that exists before the write, no field names the commit that records it, the removal and evidence commits are separate and separately owned, and writer, evaluator, check order, reason vocabulary, precedence and dependency edges agree across the plan, 177.003-T, 177.007-T, 177.006-T, 177-F and 183-S - and raised two new P2 findings against revision 6's new one-normal-run reachability derivation. M1: 177.007-T may write only after confirming the removal commit is the CURRENT TIP, which is stronger than C4's reachability requirement and C5's explicit removal-commit-or-descendant tolerance, so any intervening commit forbids the write under the atomic rule, and because the path is already deleted no second removal commit can exist, making the pass state unrecoverable by the in-unit remedy the plan advertises. M2: 177.007-T step 3 and 177.006-T check C6 both require a whole-tree empty git status --porcelain in a repository whose backlog records under .backlogit are tracked and whose agents emit untracked checkpoint and memory files in normal operation, so the derivation's cleanliness premise is falsified on a normal run; this is distinct from L2, which judges only what the reason token says, and closes nothing of L2. Three new P3 findings were raised - M3, four of seven task records still cite plan revision 5 and attempt 05; M4, the date placeholder literal differs between the plan and the emitting records on all three machine-read line forms; M5, 177.004-T alone lacks the dispatch run-ID and URL capture instruction its three peer determining tasks carry - and K5, K6 and L2 were independently re-verified unchanged and carried open. No severity was lowered and no count decremented. 183-S remains not publication-eligible while M1 and M2 are open. Attempt 06 is terminal: no remediation was performed, none is proposed, and every open finding requires explicit operator disposition. Attempt 06's terminal designation was subsequently lifted by the operator for one bounded remediation cycle scoped to the two open P2 findings, M1 and M2. That cycle produced plan revision 7. M1 is addressed by replacing the positional removal proof with a durable one: 177.007-T no longer requires the removal commit to be the current tip, and instead derives it deterministically from committed history by a fixed-argv derivation RC1-RC7 that requires the named commit to exist, to delete exactly the probe-workflow path and no other workflow file, to be absent from its own tree, to be reachable from the current HEAD by merge-base ancestor-or-equal, and to carry 177.004-T's creation commit in its ancestry, with a self-reference guard binding the SHA to committed history read before anything is staged. Later unrelated forward commits therefore cannot invalidate the proof, the block is re-emittable from the same reachable removal commit, and no second deletion or removal commit is ever required, which makes the in-unit ISOLATION_CLEANUP_FAILED remedy executable rather than advertised. M2 is addressed by replacing every whole-tree git status --porcelain emptiness requirement with exact-path-scoped probes PP1-PP3 over .github/workflows/spike-177-isolation-probe.yml alone: PP1 answers whether the path is tracked at the current tip, PP2 and PP3 answer whether a staged, unstaged or untracked copy exists at that exact path, ambiguous output in any probe is rejected rather than interpreted, and unrelated tracked files, untracked files, agent checkpoints, session memory notes and operator work are outside every limb. Because a truthful diagnostic cannot report two different facts under one token, the C6 reason vocabulary is split from five tokens to six: WORKFLOW_PRESENT_AT_TIP is narrowed to the tracked-at-tip case only and a new WORKFLOW_PATH_RESIDUE covers exact-path worktree or index residue, with TIP_UNOBSERVABLE extended to any ambiguous probe output. The five composed states, ISOLATION_CHARACTERIZED's unreachability while the workflow is tracked at HEAD or present as exact-path residue, the I1 verdict gate, the no-credential and no-secret evidence rule, the acquisition-then-no-network model, the workflow rollback and the per-state 181-S eligibility rules are all preserved unchanged, and fail-closed semantics are narrowed rather than loosened. M1 and M2 are recorded as ADDRESSED PENDING REVIEW, not closed. L2's subject matter is mechanically reconciled by the token split as a by-product and is expressly NOT claimed closed; K5, K6, M3, M4 and M5 were out of scope and remain open and unaddressed. No count is decremented, no severity is lowered and no PASS is asserted. Independent terminal attempt 07 then reviewed revision 7 at content HEAD 4a28eb4a and returned gate result PASS, decision PASS, on zero P0, zero P1, zero P2 and eight P3. It re-derived M1 CLOSED - no surface anywhere still requires the removal commit to be the current tip, RC1-RC7 identify exactly one reachable removal commit by content and ancestry and reject ambiguity, empty output, a non-deletion candidate, another touched workflow file, a degenerate self-identity and any guessed SHA, 177.006-T re-derives RC1 independently and requires SHA equality, and bounded throwaway-repository controls confirmed the derivation survives both an unrelated bookkeeping commit and an unrelated merge, so re-emission from the same removal commit needs no second deletion - and re-derived M2 CLOSED - every live cleanliness limb is exact-path-scoped through PP1-PP3, no live whole-tree porcelain requirement survives on any of the nine surfaces, and a five-case control matrix confirmed that an unrelated dirty tree passes clean while untracked, staged, tracked-at-tip and tracked-plus-unstaged exact-path states each fail closed under a truthful token. It also re-derived attempt 05's P3 L2 CLOSED, on the plan text and 177.006-T's record alone and expressly not on the stash capture that deferred the judgement to this attempt: WORKFLOW_PRESENT_AT_TIP is narrowed to tracked-at-tip and stated never to be raised for a working-tree or index condition, WORKFLOW_PATH_RESIDUE carries exact-path residue, TIP_UNOBSERVABLE carries ambiguity, the workflow_path field is now truthful under every token that can accompany it, and the advertised remedy names the residue case so it is no longer a no-op. Three new P3 findings were raised, all accuracy defects in justification prose for commands whose mandated argv is correct and must be kept: N1, RC1's stated rationale for --full-history names absence of the path at HEAD as the pruning trigger, which was empirically shown false on linear history and after a merge, while the real trigger is merge simplification of a create-and-delete pair living entirely on a merged side branch; N2, PP2's stated rationale for --untracked-files=all names a directory-collapse case that cannot arise under an exact-path pathspec, while the flag is in fact load-bearing because omitting it under status.showUntrackedFiles=no silently misses untracked exact-path residue, a fail-open; N3, 177.007-T's numbered contract consumes the creation SHA in RC6 at step 1 while instructing that value be read at step 4. K5, K6, M3, M4 and M5 were independently re-verified unchanged and carried open. No severity was lowered and no count decremented. 183-S is cleared of P0, P1 and P2 and is publication-eligible, completing the three-root wave alongside 177-S and 182-S. Attempt 07 is terminal: no remediation was performed, none is proposed, and the eight open P3 findings block nothing and are available for explicit operator disposition."
doc_type: review-manifest
source: docs/reviews/2026-09-18-conformance-isolation-spike-plan-review.md
date: 2026-09-18
manifest_shape: attempt-roster
plan_id: conformance-isolation-spike
plan_path: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
plan_revision: 7
feature_id: 177-F
shipment_id: 183-S
latest_attempt: 7
review_terminal: true
terminal_designation: operator-declared
terminal_disposition: TERMINAL-PASS
terminal_note: "Attempt 03 was designated terminal by the operator, who subsequently lifted that designation and authorized a third and final bounded remediation cycle producing revision 4. Attempt 04 is the operator-declared terminal attempt against revision 4 and returned ADVISORY; its designation was then lifted for one bounded K3-only remediation cycle producing revision 5. Attempt 05 returned ADVISORY against revision 5 and was designated terminal; that designation was then lifted for one bounded L1-only remediation cycle producing revision 6. Attempt 06 is the operator-declared terminal attempt against revision 6 and returned ADVISORY; that designation was then lifted by the operator for one bounded remediation cycle scoped to the two open P2 findings M1 and M2, producing revision 7. Attempt 07 is the operator-declared terminal attempt against revision 7 and returned PASS on zero P0, zero P1, zero P2 and eight P3, so review_terminal is true and no further attempt is awaited. Terminality never closed a finding and no severity was lowered to reach a closable state: M1, M2 and L2 were closed at attempt 07 by independent re-derivation, never by terminality."
awaiting_attempt: null
reviewed_content_head: 4a28eb4a
gate_result: PASS
verdict: PASS
verdict_is_pass: true
verdict_note: "verdict is PASS because independent terminal attempt 07 judged plan revision 7 at content HEAD 4a28eb4a and found zero P0, zero P1 and zero P2 findings, with eight P3 remaining open. Attempt 06's two open P2 findings M1 and M2 were independently re-derived CLOSED from the plan, the seven task records, 177-F, 183-S, item_deps, the shipment manifest and the working tree, plus bounded git controls run in throwaway repositories outside this repository - never from a closure summary and expressly not from the P3 follow-up stash capture. Attempt 05's P3 L2 was likewise re-derived CLOSED on the plan text and 177.006-T's record alone. Three new P3 findings N1, N2 and N3 were raised, all accuracy defects in justification prose for commands whose mandated argv is correct and must be kept; none is blocking, and none was stashed by the review. PASS is a judgement on the plan, not an authorization to Ship: it clears 183-S for staging publication, and 181-S becomes harvestable only through the composed-state token the spike will emit, never in advance of it. No severity was lowered and no count decremented."
p0_open: 0
p1_open: 0
p2_open: 0
p3_open: 8
open_findings: [K5, K6, M3, M4, M5, N1, N2, N3]
findings_addressed_pending_review: []
findings_closed_at_attempt_05: [K3, K4]
findings_raised_at_attempt_05: [L1, L2]
findings_closed_at_attempt_06: [L1]
findings_raised_at_attempt_06: [M1, M2, M3, M4, M5]
findings_closed_at_attempt_07: [M1, M2, L2]
findings_raised_at_attempt_07: [N1, N2, N3]
open_counts_note: "Counts are attempt 07's, derived independently at content HEAD 4a28eb4a against plan revision 7. K1 (P1) and K2 (P2) were closed at attempt 04; K3 (P2) and K4 (P3) at attempt 05; L1 (P2) at attempt 06. M1 (P2), M2 (P2) and L2 (P3) are CLOSED at attempt 07 by independent re-derivation. M1 closes because no surface still requires the removal commit to be the current tip: RC1-RC7 identify exactly one removal commit by content and ancestry, requiring an exact-path deletion that touches no other workflow file, absence from the removal commit's own tree, ancestor-or-equal reachability from the current HEAD and the creation commit in ancestry, with a self-reference guard and an explicit ban on guessed, invented or pre-computed SHAs; 177.006-T re-derives RC1 independently and requires SHA equality, so writer and evaluator cannot diverge; and bounded controls in throwaway repositories confirmed the derivation resolves the same removal commit after an unrelated bookkeeping commit and after an unrelated merge, so re-emission needs no second deletion or removal commit. M2 closes because every live cleanliness limb is exact-path-scoped through PP1-PP3 while every remaining whole-tree porcelain mention across the nine surfaces is historical narration; a five-case control matrix confirmed that an unrelated dirty tree passes clean while untracked, staged, tracked-at-tip and tracked-plus-unstaged exact-path states each fail closed, with tracked-at-tip evaluated before residue so the reported token is truthful in every case. L2 closes because the reason vocabulary was split, WORKFLOW_PRESENT_AT_TIP is narrowed to tracked-at-tip on both surfaces and stated never to be raised for a working-tree or index condition, workflow_path is truthful under every token that can accompany it, and the advertised remedy now names the residue case so it is no longer a no-op. Three new P3 findings were raised and are counted open: N1, RC1's --full-history rationale names the wrong pruning trigger while the mandate itself is correct and load-bearing for the merge-simplification topology; N2, PP2's --untracked-files=all rationale names a case that cannot arise under an exact-path pathspec while the flag is load-bearing against a fail-open under status.showUntrackedFiles=no; N3, 177.007-T consumes the creation SHA in RC6 at step 1 while instructing that it be read at step 4. K5, K6, M3, M4 and M5 were independently re-verified unchanged and are CARRIED open, not invalidated. No severity was lowered and no count decremented anywhere, and no finding was folded into another. N1, N2 and N3 were NOT added to any stash by attempt 07 and were not triaged or harvested. The P3 follow-up stash entry 5E45691A was re-read read-only and holds exactly K5, K6, L2, M3, M4 and M5; it is expressly NOT an authority on finding state, and L2's closure was derived without it. Stash entries 711CA657 and 8DE3047F are unchanged. 183-S is publication-eligible: it is cleared of P0, P1 and P2, and the three-root wave 177-S, 182-S and 183-S is complete. PASS authorizes no Ship work by itself, and 002-C stays blocked under all five composed states."
remediation_authorization: none-this-cycle
latest_remediation_revision: 7
judged_revision: 7
latest_disposition: null
latest_artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-07.md
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
    remediation_revision: 7
    disposition: REMEDIATED-PENDING-REVIEW
    terminal: false
    terminal_designation: lifted-by-operator
    closed_predecessor_findings: [L1]
    carried_predecessor_findings: [K5, K6, L2]
    findings_raised: [M1, M2, M3, M4, M5]
    remediation_scope: "Attempt 06 was itself a terminal review-only attempt: it performed no remediation, proposed none, and stashed, triaged or harvested nothing. Its terminal designation was subsequently lifted by the operator for one bounded Stage remediation cycle scoped to the two open P2 findings M1 and M2, producing plan revision 7 awaiting independent attempt 07. That cycle replaced M1's current-tip requirement with a durable reachability-based removal derivation RC1-RC7, replaced M2's whole-tree porcelain requirements with exact-path probes PP1-PP3 over .github/workflows/spike-177-isolation-probe.yml alone, and split the C6 reason vocabulary from five tokens to six by narrowing WORKFLOW_PRESENT_AT_TIP to tracked-at-tip and adding WORKFLOW_PATH_RESIDUE. It touched exactly five records - 177-F, 183-S, 177.003-T, 177.006-T, 177.007-T - plus the plan and this manifest, and added M3, M4 and M5 to the P3 follow-up stash entry 5E45691A alongside the preserved K5, K6 and L2. M1 and M2 are ADDRESSED PENDING REVIEW and remain counted open; L2 is mechanically reconciled and expressly not claimed closed; K5, K6, M3, M4 and M5 remain open and unaddressed. No severity was lowered and no count decremented."
  - attempt: 7
    artifact: docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-07.md
    reviewed_revision: 7
    reviewed_content_head: 4a28eb4a
    reviewed_branch: chore/stage-176-s-workflow-defects
    verdict: PASS
    gate_result: PASS
    p0_open: 0
    p1_open: 0
    p2_open: 0
    p3_open: 8
    open_findings: [K5, K6, M3, M4, M5, N1, N2, N3]
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: null
    disposition: null
    terminal: true
    terminal_designation: operator-declared
    closed_predecessor_findings: [M1, M2, L2]
    carried_predecessor_findings: [K5, K6, M3, M4, M5]
    findings_raised: [N1, N2, N3]
    remediation_scope: "None. Attempt 07 is a terminal review-only attempt: it performed no remediation, proposed none, and stashed, triaged or harvested nothing. M1, M2 and L2 were closed by independent re-derivation from the plan, the seven task records, 177-F, 183-S, item_deps, the shipment manifest and the working tree, plus bounded git controls executed in throwaway repositories outside this repository; the P3 follow-up stash entry 5E45691A was read read-only and was expressly not used as an authority on finding state. The three findings raised at this attempt, N1, N2 and N3, were deliberately NOT added to any stash, because a review-only attempt creates no backlog or stash state. The five carried P3 findings K5, K6, M3, M4 and M5 remain in 5E45691A at low priority, untriaged, unharvested, unparented and outside the current shipment scope. Remaining P3 findings require explicit operator disposition; no automatic remediation follows a terminal review."
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
| `plan_revision` | 7 |
| `latest_attempt` | **07** (operator-declared **terminal**; no further attempt awaited) |
| `latest_artifact` | `docs/reviews/review-history/2026-09-18-conformance-isolation-spike-plan-review-attempt-07.md` |
| `reviewed_content_head` | `4a28eb4a` (what attempt 07 judged — plan revision 7) |
| `gate_result` (attempt 07, immutable) | **PASS** |
| `verdict` | **PASS** (attempt 07's judgement of revision 7) |
| `verdict_is_pass` | **true** |
| `judged_revision` | **7** |
| `latest_remediation_revision` | **7** (produced after attempt 06, scoped to `M1` and `M2`; judged at this attempt) |
| `latest_disposition` | `null` — attempt 07 is review-only; no remediation was performed or proposed |
| `awaiting_attempt` | `null` |
| `p0_open` | **0** |
| `p1_open` | **0** (`K1` closed at attempt 04) |
| `p2_open` | **0** (`M1` and `M2` **closed** at attempt 07 by independent re-derivation; `L1`, `K3`, `K2` closed earlier) |
| `p3_open` | **8** (`K5`, `K6`, `M3`, `M4`, `M5` carried; `N1`, `N2`, `N3` raised at attempt 07; `L2` and `K4` **closed**) |
| `findings_closed_at_attempt_07` | `[M1, M2, L2]` — by independent re-derivation |
| `findings_raised_at_attempt_07` | `[N1, N2, N3]` — **not** stashed by the review |
| `findings_addressed_pending_review` | `[]` — nothing is addressed-but-unjudged |
| `p3_followup_stash` | `5E45691A` (`K5`, `K6`, `L2`, `M3`, `M4`, `M5`) — outside this shipment's scope; `N1`–`N3` deliberately not added |

**The top-level `verdict` is attempt 07's own judgement, not a carried value.**
Independent terminal attempt 07 read revision 7 at content HEAD `4a28eb4a` and
returned **PASS** on zero P0, zero P1, zero P2 and eight P3.

**PASS is a judgement on the plan, not an authorization to Ship.** It records
that an independent reviewer found no blocking defect — zero P0, zero P1 — and
also no P2, on the content it read. The blocking predicate in
`.github/policies/workflow-policies.md` is *unresolved P0/P1 findings*, so the
eight open P3 findings do not gate. They are genuine open findings and remain
available for explicit operator disposition; PASS does not close them and no
severity was lowered to reach it.

**`183-S` is publication-eligible.** Both attempt-06 P2 findings are closed on
their own terms, not by narrowing:

- **`M1` is closed.** No surface any longer requires the removal commit to be
  the current tip. `RC1`–`RC7` identify exactly one removal commit by content
  and ancestry — a single deletion of the exact path, touching no other
  workflow file, absent from the removal commit's own tree, ancestor-or-equal
  to the current `HEAD`, with the creation commit in its ancestry, a
  self-reference guard, and an explicit ban on guessed, invented or
  pre-computed SHAs. `177.006-T` re-derives `RC1` independently and requires
  SHA equality, so the writer and the evaluator cannot silently diverge.
  Unrelated forward commits no longer invalidate the proof, and `177.007-T`
  can re-emit the evidence from the **same** removal commit without a second
  removal — which is what made `M1` unrecoverable before. `C6` remains an
  independent current-state authority, evaluated on its own evidence.
- **`M2` is closed.** Every live cleanliness limb is scoped to the exact probe
  path through `PP1`–`PP3`; every remaining whole-tree `git status --porcelain`
  mention across the nine surfaces is historical narration, not a live
  requirement. Unrelated tracked or untracked work no longer blocks a pass,
  while tracked-at-tip, staged, unstaged and untracked residue at the exact
  path each fail closed with distinct, truthful reasons — tracked-at-tip is
  evaluated first and reports `WORKFLOW_PRESENT_AT_TIP`; index or worktree
  residue reports `WORKFLOW_PATH_RESIDUE`. Ambiguity and command error resolve
  to `TIP_UNOBSERVABLE`, never to clean.

**A first normal execution and a later re-emission are both reachable** without
self-reference, a guessed SHA, a corrective deletion, or whole-tree
cleanliness. The five composed states, the six-token reason vocabulary, the
precedence order and successor eligibility remain total, mutually exclusive and
consistent across the plan, `177-F`, `183-S` and all seven task records.

**`L2` is closed** — re-evaluated only because the token split actually touches
its subject, and derived from the plan text and `177.006-T`'s record alone.
`WORKFLOW_PRESENT_AT_TIP` is now narrowed to tracked-at-tip on both surfaces
and is stated never to be raised for an index or worktree condition, so the
diagnostic mismatch that `L2` described no longer exists. The stash capture was
**not** used as closure for it, or for anything else.

**Three new P3 findings were raised** and are counted open. All three are
accuracy defects in *justification prose* for commands whose mandated argv is
correct and must be kept: `N1` (the `--full-history` rationale names the wrong
pruning trigger), `N2` (the `--untracked-files=all` rationale names a case that
cannot arise under an exact-path pathspec, while the flag is load-bearing
against a genuine fail-open) and `N3` (`177.007-T` consumes the creation SHA at
step 1 while instructing that it be read at step 4). None is blocking; each is
trivially satisfiable by an executor following the mandated commands.

**Five P3 findings are carried unchanged**, each independently re-verified
rather than assumed: `K5`, `K6`, `M3`, `M4` and `M5`. None was invalidated and
none was folded into another.

**Attempt 07 is terminal and review-only.** It performed no remediation,
proposed none, and stashed, triaged or harvested nothing. Remaining P3 findings
require explicit operator disposition; no automatic remediation follows.

**Terminality never closed a finding, in any cycle.** Attempt 04's designation
was lifted on 2026-09-19T21:41:26.916-07:00 for a bounded `K3` cycle; attempt
05's for a bounded `L1` cycle; attempt 06's for a bounded `M1`/`M2` cycle
producing revision 7. Each time, the loop was bounded, never a finding: **no
severity was lowered and no count decremented** to permit a cycle or to reach a
result — including this one.

**Every closure was made by the only authority that can make it.** `F1`–`F3`
were verified closed at attempt 03; `K1` and `K2` at attempt 04; `K3` and `K4`
at attempt 05; `L1` at attempt 06; `M1`, `M2` and `L2` at attempt 07. In each
case the *next independent attempt* re-derived closure from the plan, the
`177.x` task records, `177-F`, `183-S`, `item_deps`, the shipment manifest and
the working tree, rather than accepting a remediation narrative. Attempt 07
additionally ran bounded git controls in throwaway repositories outside this
repository to test the behaviours `RC1`–`RC7` and `PP1`–`PP3` depend on.

**Remediation converged at the sixth cycle.** Revision 2 closed every
attempt-01 finding and introduced a new P1 doing it. Revision 3 closed all
three attempt-02 findings and introduced a new P1 **inside the very mechanism
that closed `F1`**. Revision 4 separated ordering from safety and introduced
`K3` in the composed vocabulary. Revision 5 made cleanup an executable
predicate and introduced `L1` **inside the very evidence block that closes
`K3`**. Revision 6 split that write point in two, genuinely closed `L1`, and
introduced `M1` and `M2` **inside the observation preconditions that make the
split work**. Revision 7 replaced both preconditions with ones the environment
cannot falsify — a durable reachability-based removal proof and exact-path
cleanliness — and independent attempt 07 derives that this is the layer at
which the seam closes: the three findings it raised are prose-accuracy defects
outside the safety mechanism, not a seventh layer of it. This is the
convergence tail of the pattern recorded in
`docs/compound/093-S-review-loop-convergence.md` for novel safety-critical
work.

**What PASS does and does not authorize.** It clears `183-S` for staging
publication as review-cleared, completing the three-root wave alongside `177-S`
and `182-S`. It does **not** by itself start Ship work, and it does not
pre-clear anything downstream: `181-S` remains gated on the composed-state
token the spike will actually emit, and `002-C` stays blocked under all five
composed states.

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

**The operator lifted attempt 06's terminal designation** and authorized one
bounded Stage remediation cycle scoped to the two open P2 findings, `M1` and
`M2`, to be judged by an independent attempt 07. `review_terminal` is therefore
`false`, `terminal_designation` is `lifted-by-operator`, and `awaiting_attempt`
is `7`. **Lifting terminality closes no finding, decrements no count and
changes no severity.** `M1` and `M2` remain open in this manifest until an
independent reviewer judges them.

That cycle produced **plan revision 7**, disposition
`REMEDIATED-PENDING-REVIEW`, which is a statement about what Stage produced and
never about what a reviewer found.

**What revision 7 did about `M1`.** It replaced a *positional* removal proof
with a *durable* one. `177.007-T` no longer requires the removal commit to be
the current branch tip. It instead **derives** that commit from committed
history by a fixed-argv derivation `RC1`–`RC7`, which requires the named commit
to exist, to delete **exactly** `.github/workflows/spike-177-isolation-probe.yml`
and no other workflow file, to be absent from its own tree, to be **reachable
from the current HEAD** (`git merge-base --is-ancestor`, ancestor-or-equal), and
to carry `177.004-T`'s creation commit in its ancestry — with a self-reference
guard binding the SHA to history read **before** anything is staged, so it can
never be the evidence commit. `RC1` mandates `--full-history`, because default
history simplification prunes the deletion commit once the path is absent at
`HEAD` and would otherwise read as *no removal commit exists*. The consequences
are stated rather than inferred: later unrelated forward commits **never
invalidate** the proof; the block is **re-emittable from the same reachable
removal commit** after any number of them; and **no second deletion or removal
commit is ever required**, which is what makes the in-unit
`ISOLATION_CLEANUP_FAILED` remedy executable rather than advertised. `C4` now
re-derives `RC1`–`RC7` independently and requires SHA equality, failing to
`EVIDENCE_INCONSISTENT` on a mismatch, and is **never** required to equal the
tip — `C6` remains the current-state authority.

**What revision 7 did about `M2`.** It replaced every whole-tree
`git status --porcelain` emptiness requirement with **exact-path-scoped** probes
`PP1`–`PP3` over `.github/workflows/spike-177-isolation-probe.yml` and nothing
else. `PP1` (`git ls-tree --full-tree -r --name-only HEAD -- <path>`) answers
whether the path is **tracked at the current tip**; `PP2`
(`git status --porcelain=v1 --untracked-files=all -- <path>`) and `PP3`
(`git ls-files --cached --error-unmatch -- <path>`) answer whether a **staged,
unstaged or untracked copy exists at that exact path**. All three use fixed
argv and byte-identical path containment, and **ambiguous output is rejected
rather than interpreted**, raising `TIP_UNOBSERVABLE` — ambiguity is never
resolved in the passing direction. Unrelated tracked files, untracked files,
agent checkpoints, session memory notes and operator work are outside every
limb and can no longer prevent the evidence write or fail the evaluation. The
eighth line's third field is renamed accordingly, from
`porcelain_empty_at_observation` to `path_clean_at_observation`, on both the
writer's and the evaluator's surface, so the recorded value cannot be read as a
whole-tree claim. The adjacent date placeholder was deliberately left
untouched, so `M4` is neither silently closed nor silently altered.

**Why the reason vocabulary went from five tokens to six.** `PP1` and `PP2`/`PP3`
report **different facts**, and one token cannot carry both truthfully.
`WORKFLOW_PRESENT_AT_TIP` is therefore **narrowed** to the tracked-at-tip case
only, and a new sixth token `WORKFLOW_PATH_RESIDUE` reports an exact-path
staged, unstaged or untracked copy. A diagnostic can no longer claim the
workflow is present at the tip when only worktree or index residue exists.

**Fail-closed is preserved and narrowed, not loosened.** A staged, unstaged or
untracked copy of the exact probe path still fails cleanup, still forces
`ISOLATION_CLEANUP_FAILED`, and still blocks `181-S` harvest outright — now
under a truthful reason. `ISOLATION_CHARACTERIZED` **remains impossible** while
the workflow is tracked at the current HEAD or exists as exact-path residue.

**What revision 7 deliberately did not do.** The **five** composed states, the
declared precedence, the `I1` verdict gate, the no-credential and no-secret
evidence rule, the acquisition-then-no-network model, the workflow rollback,
the per-state `181-S` successor-eligibility rules, the two-step no-self-reference
lifecycle (`177.003-T` removal commit → `177.007-T` evidence → `177.006-T`
evaluation) and the `item_deps` edges are all preserved unchanged. Only the
reason-token **count** changed, from five to six; the state count did not.

**`L2` is reconciled, not closed.** The token split necessarily touches `L2`'s
subject matter — `L2` names exactly the one-token-two-facts defect that `M2`'s
scoping forced open. Every surface that carries the vocabulary states
explicitly that **no claim of `L2` closure is made or implied**. `L2` remains
listed open, at unchanged severity, for independent attempt 07 to derive.

**`K5`, `K6`, `M3`, `M4` and `M5` were out of scope** and remain open and
unaddressed. The cycle was kept bounded deliberately: only the five records
mechanically touched by `M1`/`M2` — `177-F`, `183-S`, `177.003-T`, `177.006-T`,
`177.007-T` — were bumped to revision 7, so the four determining-task records
still carry the stale label `M3` names; the date placeholder literal was left
divergent (`2026-09-DD` in the plan, `<date>` in the records) even on the lines
edited for the field rename, so `M4` is neither silently closed nor silently
altered; and `177.004-T` was not touched at all, so `M5` is untouched. `M3`,
`M4` and `M5` were **added by Stage** to the existing P3 follow-up stash entry
`5E45691A`, alongside the preserved `K5`, `K6` and `L2`, at `low` priority and
expressly excluded from the current shipment scope — not triaged, not
harvested, not parented, and in no manifest.

**`M1` and `M2` are recorded ADDRESSED PENDING REVIEW, not closed.** No count
is decremented, no severity is lowered, and `p2_open` remains **2**.

`183-S` is **cleared of P0/P1** and **not publication-eligible** while `M1` and
`M2` are open. The eight open findings — `M1`, `M2`, `K5`, `K6`, `L2`, `M3`,
`M4`, `M5` — remain available for explicit operator disposition. `ADVISORY` is
still not a `PASS`, the plan is not Ship-ready, and `181-S` remains reviewable
as a plan without becoming harvestable. No `PASS` exists anywhere in this
record and none is asserted.

> **Superseded by attempt 07.** Every statement in this section, including the
> counts, the `ADDRESSED PENDING REVIEW` status of `M1` and `M2`, and the
> "no `PASS` exists anywhere in this record" claim, describes the state of the
> record **as of the close of the revision-7 remediation cycle, before
> independent attempt 07 judged it**. It is preserved verbatim as history. The
> authoritative current state is *Current verdict* and *What attempt 07
> records*: `M1`, `M2` and `L2` are **closed**, `p2_open` is **0**, and the
> verdict is **PASS**.

## What attempt 07 records

Independent terminal attempt 07 read plan **revision 7** at content HEAD
`4a28eb4a` on branch `chore/stage-176-s-workflow-defects` and returned
**PASS** on **zero P0, zero P1, zero P2 and eight P3**. It was a **review-only**
attempt: it performed no remediation, proposed none, and stashed, triaged or
harvested nothing.

**Independence.** Every judgement below was re-derived from primary sources —
the plan body, all seven `177.00x-T` task records, `177-F`, `183-S`,
`item_deps`, the `183-S` shipment manifest, the binding decision document and
the actual working tree — not from the revision-7 remediation narrative, and
expressly not from the P3 follow-up stash entry. Attempt 07 additionally ran
**bounded git controls in throwaway repositories outside this repository** to
test the real behaviour of the commands `RC1`–`RC7` and `PP1`–`PP3` mandate,
rather than accepting the plan's claims about them. Nothing in this repository
was mutated to perform the review.

**`M1` is closed.** The attempt-06 defect was that `177.007-T`'s binding
precondition required the removal commit to be the *current tip*, which the
repository's own bookkeeping commits routinely falsify and which no second
removal could ever restore. Revision 7 removes that requirement from every
surface. `RC1` derives the removal commit from committed history with a fixed
argv and requires exactly one 40-hex SHA; `RC2` requires exactly one deletion
line for the exact path; `RC3` requires that commit to touch no other file
under `.github/workflows/`; `RC4` requires the path to be absent from the
removal commit's own tree; `RC5` requires ancestor-or-equal reachability from
the current `HEAD`; `RC6` requires the creation commit in ancestry and
distinct from the removal commit; `RC7` binds the SHA to history read before
anything is staged, so the evidence commit can never be its own proof. Guessed,
invented and pre-computed SHAs are explicitly rejected, and ambiguity in any
limb fails closed rather than being resolved by choice. `177.006-T` re-derives
`RC1` independently and requires SHA equality, failing to
`EVIDENCE_INCONSISTENT` on mismatch, so the writer and the evaluator cannot
diverge. Controls confirmed the derivation resolves the **same** removal commit
after an unrelated bookkeeping commit and after an unrelated merge, so
`177.007-T` can re-emit the evidence block from that same commit with **no
second removal**. `C6` remains an independent current-state authority evaluated
on its own evidence, unaffected by the removal proof.

**`M2` is closed.** Every live cleanliness limb is scoped to
`.github/workflows/spike-177-isolation-probe.yml` alone, through `PP1`
(tracked-at-tip), `PP2` (index/worktree status) and `PP3` (index membership),
each with fixed arguments and byte-identical path containment. Attempt 07
audited **every** `git status --porcelain` occurrence across all nine surfaces
and confirmed that only the three `PP2` specifications are live requirements;
the rest is historical narration. A five-case control matrix confirmed the
semantics: an unrelated dirty tree — including untracked agent checkpoints and
memory notes of exactly the kind present at the reviewed HEAD — passes clean;
an untracked, a staged, a tracked-at-tip and a tracked-plus-unstaged copy at
the exact path each fail closed; and tracked-at-tip is evaluated **before**
residue, so `WORKFLOW_PRESENT_AT_TIP` and `WORKFLOW_PATH_RESIDUE` are each
raised only on the condition they truthfully describe. Non-zero exit,
non-byte-identical output and directory-form output all resolve to
`TIP_UNOBSERVABLE`; no ambiguity resolves in the passing direction.

**A first normal execution and a later re-emission are both reachable** without
self-reference, a guessed SHA, a corrective deletion or whole-tree cleanliness.
The removal → evidence → evaluation ordering across `177.003-T` → `177.007-T`
→ `177.006-T` is preserved and matches `item_deps`; task sizing remains within
the granularity bound, with every task carrying both `size` and `complexity`.
The `I1` verdict gate, the no-secret and no-credential evidence rule, the
acquisition-then-no-network isolation model, the workflow rollback, `183-S`'s
DAG-root status and the `181-S` successor-eligibility rules were each
re-verified and are unchanged. The five composed states, the six-token reason
vocabulary, the declared precedence and successor eligibility remain **total,
mutually exclusive and consistent** across all nine surfaces.

**`L2` is closed.** It was re-evaluated only because the token split genuinely
touches its subject, and closure was derived from the plan text and
`177.006-T`'s record alone — the stash capture was **not** used as closure.
`WORKFLOW_PRESENT_AT_TIP` is narrowed to the tracked-at-tip case on both
surfaces and is stated never to be raised for an index or worktree condition;
`WORKFLOW_PATH_RESIDUE` carries the residue case; the recorded `workflow_path`
field is truthful under every token that can accompany it; and the advertised
remedy now names the residue case instead of being a no-op for it. The
one-token-two-facts mismatch `L2` described no longer exists.

**Three P3 findings were raised.** `N1`: `RC1`'s stated rationale for
`--full-history` names the wrong pruning trigger — controls showed the default
simplification still returns the deletion commit on linear history and after an
unrelated merge onto the same branch, and prunes it only when the create/delete
pair lives on a merged side branch read from the merge target; the **flag is
correct and load-bearing** and must be kept, only its justification is
inaccurate, and the failure mode it guards is fail-closed. `N2`: `PP2`'s
rationale for `--untracked-files=all` names directory collapse, which cannot
occur under an exact-path pathspec; the flag is nonetheless **load-bearing**
because omitting it under `status.showUntrackedFiles=no` returns empty output
while untracked residue exists — a genuine **fail-open** the stated rationale
does not name. `N3`: `177.007-T`'s numbered contract consumes the creation SHA
in `RC6` at step (1) while instructing that it be read at step (4). All three
are prose or ordering defects outside the safety mechanism, trivially
satisfiable by an executor following the mandated commands, and none is
blocking.

**Five P3 findings are carried**, each independently re-verified unchanged
rather than assumed: `K5` (em-dash/hyphen divergence in the `I1_GATE`
line form), `K6` (no note preventing an `I2`-weakening reading), `M3` (four
determining-task records still cite plan revision 5, now two revisions stale),
`M4` (date placeholder literal divergence between plan and records) and `M5`
(`177.004-T` alone lacks the dispatch run-ID and URL capture instruction). None
was invalidated and none was folded into another.

**Nothing was decremented or downgraded.** No severity was lowered, no count
reduced, and no finding merged into another to reach `PASS`. The eight open P3
findings are counted open in this manifest.

**Stash verification.** The P3 follow-up stash entry `5E45691A` was re-read
**read-only** and holds exactly the current P3 follow-ups `K5`, `K6`, `L2`,
`M3`, `M4` and `M5`, at `low` priority, non-blocking, outside the current
shipment scope, untriaged, unharvested, unparented and in no manifest. `M1` and
`M2` are correctly absent from it. `N1`, `N2` and `N3` were **deliberately not
added** — a review-only attempt creates no stash state. Stash entries
`711CA657` and `8DE3047F` are unchanged.

**Root-wave position.** `183-S` is one of exactly three DAG roots in the
2026-09-17 portfolio wave. `177-S` passed at its attempt 07 and `182-S` at its
attempt 04; `183-S` passes here, so the three-root wave is complete and `183-S`
is publication-eligible. That root status is now **mechanically effective**:
PR #457 review thread `PRRT_kwDORzpWpM6kHrxc` found `183-S` declaring itself a
root in prose while carrying no `dag-root` label, which leaves it
`unsequenced` and unclaimable — `genesis` provenance is unreachable in a
workspace holding many shipment records. The label is now recorded. (`177-S`
and `182-S` carried the same defect, threads `PRRT_kwDORzpWpM6kHrxD` and
`PRRT_kwDORzpWpM6kHrxY`.) A fourth root, `188-S`, was added later under
decision D9 and is unrelated to this wave.

**The successor's records have since been withdrawn from the executable
queue.** PR #457 review thread `PRRT_kwDORzpWpM6kHrxK` found that `181-S`,
covering feature `173-F` and tasks `173.001-T`–`173.011-T` had already been
harvested, and that the `depends_on 183-S` edge could enforce **neither** the
per-state token **nor** the per-state allowed task set: a `blocks` edge clears
on predecessor **completion**, and `177.006-T` completes on all five of its
tokens. No installed shipment-claim predicate reads
`docs/spikes/2026-09-18-conformance-isolation-findings.md`. Those thirteen
records are therefore **archived** under `.backlogit/archive/` as a conditional
future unit (decision D10), with
`docs/plans/2026-09-18-safe-close-conformance-plan.md` preserved intact and
marked `plan_role: conditional-future`. Nothing is deleted. Stage restores them
only in a **new staging session**, applying the per-state rules `177.006-T`
already declares: `ISOLATION_CHARACTERIZED` admits every task the findings
support; `ISOLATION_FLOOR_ONLY` admits **only** the evidence-and-documentation
floor subset and **only** after a new recorded Stage decision enumerating it
task by task; `ISOLATION_CLEANUP_FAILED`, `ISOLATION_UNDETERMINED` and
`ISOLATION_NOT_OBSERVED` admit **nothing**. This changes nothing about attempt
07's verdict, which stands as recorded: it is a statement about the
successor's records, not about this plan.

**What this does not authorize.** `PASS` is a judgement on the plan. It starts
no Ship work by itself, and it pre-clears nothing downstream: `181-S` becomes
harvestable only through the composed-state token the spike actually emits, and
`002-C` stays blocked under all five composed states. Attempt 07 is terminal:
there is no automatic remediation proposal or execution, and the eight
remaining P3 findings require **explicit operator disposition**.

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
| **6** (terminal designation lifted 2026-09-20) | `...-plan-review-attempt-06.md` | 6 @ `7768c5d5` | **ADVISORY** (0 P0, 0 P1, 2 P2, 6 P3) | 7 | `REMEDIATED-PENDING-REVIEW` |
| **7** (operator-declared terminal) | `...-plan-review-attempt-07.md` | 7 @ `4a28eb4a` | **PASS** (0 P0, 0 P1, 0 P2, 8 P3) | — | — |

## Provenance

* Plan: `docs/plans/2026-09-18-conformance-isolation-spike-plan.md` at revision 7
  (judged revision: **7**, by independent terminal attempt 07 at content HEAD
  `4a28eb4a`)
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
  (`K5`, `K6`, `L2`, `M3`, `M4`, `M5`) — not in this shipment's scope. `K4` was
  independently closed at attempt 05 and has been **removed** from that entry;
  `L2`, raised at attempt 05, was **added** to it during the revision-6 cycle;
  `M3`, `M4` and `M5`, raised at attempt 06, were **added** to it during the
  revision-7 cycle, with `K5`, `K6` and `L2` preserved. None of these edits was
  made by a review: the entry is corrected by Stage between attempts, and no
  severity was lowered and no count decremented to do so. Attempt 07 re-read the
  entry **read-only** and verified it holds exactly the current P3 follow-ups at
  `low` priority, untriaged, unharvested, unparented and in no manifest; the
  entry is expressly **not** an authority on finding state, and `L2`'s closure
  was derived without it. `L1` is **not** in that entry — it was addressed at
  revision 6 and closed at attempt 06. `M1` and `M2` are **not** in that entry
  either: they are P2, were addressed at revision 7, and were **closed** at
  attempt 07. `L2` is now closed but is still listed in the entry, which is a
  Stage bookkeeping correction for a later authorized pass, not a review action.
  `N1`, `N2` and `N3`, raised at attempt 07, are **not** in any stash: a
  review-only attempt creates no stash state. Stash entries `711CA657` and
  `8DE3047F` are unrelated and unchanged; the finding labelled `M4` in
  `8DE3047F` belongs to a different review series and is **not** this `M4`.
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
