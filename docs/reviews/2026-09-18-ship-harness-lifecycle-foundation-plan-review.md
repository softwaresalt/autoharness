---
title: "Plan review verdict manifest — Ship pre-task harness-generation lifecycle"
description: "Mutable verdict manifest for docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md. This file is a selection surface, not a review: it names which immutable attempt artifact is authoritative right now, and nothing else. MANIFEST REVISION 5. INDEPENDENT ATTEMPT 03 HAS RUN against plan revision 4 at content HEAD c52e8403 and returned gate_result ADVISORY / decision PROCEED-WITH-ADVISORY on two P2 findings, with no P0, no P1 and no P3. All three attempt-02 findings are CONFIRMED CLOSED: S7's blocking premise inversion is repaired against live file content re-derived exactly, S8's 181.003-T is an explicitly inert procedure-design task with guards propagated and sizes coherently re-derived, and S9's provenance is corrected to 76EBDE6D and verified against decision line 993 and archive line 234. S1 through S6 remain closed. Two new non-blocking P2 findings were raised: S10, the ten-cross-reference characterization is inaccurate for four of its ten cited lines and renders parity criterion P6's second clause unsatisfiable as literally written; and S11, the D/G/P label space diverges between the plan and 181.005-T while three records cross-reference each other by label. Both err in the safe direction and leave no failure mode undetected. ADVISORY IS NOT PASS: 187-S remains NOT publication-eligible, its tasks remain NOT claimable, and it remains gated on 188-S."
doc_type: review-manifest
source: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
date: 2026-09-18
manifest_shape: attempt-roster
manifest_revision: 5
plan_id: ship-harness-lifecycle-foundation
plan_path: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
plan_revision: 4
feature_id: 181-F
shipment_id: 187-S
latest_attempt: 3
review_terminal: true
terminal_designation: terminal-for-cycle
terminal_disposition: ADVISORY-NO-REMEDIATION-THIS-CYCLE
terminal_note: "Attempt 03 is terminal for this cycle. It returned ADVISORY on two P2 findings with no P0, no P1 and no P3, and performed no remediation. S10 and S11 are recorded open and non-blocking. Whether a further remediation cycle is opened against them is an operator decision; the gate does not compel one, and ADVISORY does not become PASS by the absence of one."
awaiting_attempt: null
reviewed_content_head: c52e8403
gate_result: ADVISORY
verdict: ADVISORY
verdict_is_pass: false
verdict_note: "ADVISORY as independently determined by attempt 03 against plan revision 4 at HEAD c52e8403, on the stated decision rule (P0/P1 FAIL, P2-only ADVISORY, P3/none PASS). ADVISORY IS NOT PASS. SM-2's HARVEST_ADMITTED state is defined against verdict: PASS, so harvest on the strength of this manifest remains CLOSED and no Ship work is authorized from it. 187-S is additionally gated on 188-S, which must reach shipped first. No severity was lowered to reach this verdict and no finding was downgraded."
p0_open: 0
p1_open: 0
p2_open: 2
p3_open: 0
open_findings: [S10, S11]
blocking_findings: []
findings_closed_at_attempt_02: [S1, S2, S3, S4, S5, S6]
findings_closed_at_attempt_03: [S7, S8, S9]
findings_addressed_pending_review: []
open_counts_note: "Counts are now REAL, asserted by independent attempt 03 rather than by Stage. S7 (P1, was blocking) is CLOSED on re-derived live evidence: the template's '### Step 2: Harness Generation (P-002 / P-004)' is at line 326 and the mirror has zero harness-generation headings and zero occurrences of harness-ready or harness-architect; both files are byte-identical to the da8f890a state the plan says it read; G1 evaluates to 1, G2 to 0 and G3 to 1-and-1 against live content. S8 is CLOSED: 181.003-T is explicitly an inert agent-template/procedure design task producing no Python at two named fixture paths, the plan's Composed-state check and Blast radius agree, guards and citations are propagated to 181.001-T/181.003-T/181.004-T, and sizes are coherently re-derived (181.003-T S/medium as a re-derivation against changed scope, 181.005-T HELD at M/high with three named de-risking steps). S9 is CLOSED: decision line 993 assigns 76EBDE6D to P4/187-S/181-F, archive stash.jsonl line 234 resolves it, and line 995 assigns 3EF5AAF2 to 177-S/169-F, which is also the declared source of the post-claim plan. S10 (P2, new): four of the ten cited mirror lines (184, 214, 377, 748) are lowercase references to local numbered sub-steps of other procedures rather than to the Task Execution Loop, so parity criterion P6's second clause cannot be satisfied as literally written even by a correct commit. S11 (P2, new): D2/D3 are swapped between the plan and 181.005-T, and the record's G5/G6/G7 and P1-P6 differ in referent from the plan's, while 181.003-T and 181.004-T cross-reference the plan's numbering. Coverage was checked failure-mode by failure-mode and is complete under either set, so neither finding is blocking."
remediation_authorization: none-this-cycle
latest_remediation_revision: 4
latest_disposition: ADVISORY-P2-ONLY
latest_artifact: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-03.md
attempts:
  - attempt: 1
    artifact: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-01.md
    reviewed_revision: 2
    reviewed_content_head: 989712bf
    gate_result: FAIL
    verdict: FAIL
    verdict_is_pass: false
    p0: 0
    p1: 3
    p2: 3
    p3: 0
    blocking: [S1, S2, S3]
    remediation_revision: 3
    disposition: FAIL-BLOCKING-P1
    dispatch_mode: single-agent-declared-degradation
  - attempt: 2
    artifact: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-02.md
    reviewed_revision: 3
    reviewed_content_head: 38d23f53
    gate_result: FAIL
    verdict: FAIL
    verdict_is_pass: false
    p0: 0
    p1: 1
    p2: 2
    p3: 0
    blocking: [S7]
    closed_predecessor_findings: [S1, S2, S3, S4, S5, S6]
    remediation_revision: 4
    disposition: FAIL-BLOCKING-P1
    dispatch_mode: single-agent-declared-degradation
  - attempt: 3
    artifact: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-03.md
    reviewed_revision: 4
    reviewed_content_head: c52e8403
    gate_result: ADVISORY
    verdict: ADVISORY
    verdict_is_pass: false
    p0: 0
    p1: 0
    p2: 2
    p3: 0
    blocking: []
    closed_predecessor_findings: [S7, S8, S9]
    findings_raised: [S10, S11]
    remediation_revision: null
    disposition: ADVISORY-P2-ONLY
    dispatch_mode: single-agent-declared-degradation
carried_forward_context:
  - "S1 (P1, was blocking) — CLOSED AT ATTEMPT 02. Verified on nine live carriers that no task generates, installs, modifies or deletes 188-S's deliverable and that rollback is unit-scoped: plan Rollout, Blast radius, Rollback and Tasks; the 187-S and 181-F records; and the 181.002-T, 181.004-T and 181.005-T records. The hardening pass is genuinely re-derived rather than re-dated - H1 is rewritten and H7/H8 are new questions that did not exist at revision 2."
  - "S2 (P1, was blocking) — CLOSED AT ATTEMPT 02. 181.002-T is titled and bodied as the harness-surface requirement resolver, states it GENERATES NO SKILL AND INSTALLS NO SKILL, MUST NOT write/modify/delete anything under .github/skills/, MUST NOT generate any file from any template, and consumes the harness-architect surface READ-ONLY as an already-satisfied precondition installed by 188-S/182-F/182.003-T. It DETERMINES nothing else and DECIDES nothing else."
  - "S3 (P1, was blocking) — CLOSED AT ATTEMPT 02. 181.005-T carries no P-004 cross-reference, names templates/agents/_ship.agent.md.tmpl and .github/agents/_ship.agent.md as THE ONLY SURFACES THIS COMMIT MAY CHANGE, forbids any policy-text edit INCLUDING a cross-reference, and routes a wanted cross-reference to a separate plan revision with its own hardening. The stale actor-existence sentence is corrected. Plan H3 independently forbids the same edit."
  - "S4 (P2) — CLOSED AT ATTEMPT 02. Neither the 181-F nor the 187-S title carries the 'and installed harness-architect' claim."
  - "S5 (P2) — CLOSED AT ATTEMPT 02. 181-F cites decision revision 3, D9, matching the plan and 187-S; the decision file's own frontmatter reads revision: 3."
  - "S6 (P2) — CLOSED AT ATTEMPT 02. The entry manifest tracked plan revision 3 and decision revision 3, carried manifest_revision 2, held a NULL verdict, and confined REMEDIATED-PENDING-REVIEW to latest_disposition. Schema-valid and self-consistent; the S6 misuse was not repeated."
  - "S7 (P1, was blocking) — ADDRESSED AT PLAN REVISION 4, NOT CLOSED, PENDING INDEPENDENT ATTEMPT 03. The finding was correct on live state: templates/agents/_ship.agent.md.tmpl:326 already declares '### Step 2: Harness Generation (P-002 / P-004)' while .github/agents/_ship.agent.md contains ZERO occurrences of harness-ready or harness-architect. Remediation re-grounds the unit in that state rather than defending the old premise. The plan gains a 'Live state of the two ACTIVATE targets' section recording the evidence, and a 'The ACTIVATE contract, stated mechanically' section fixing four things the executor previously had to choose: DETECTION (D1-D3 exact whole-line case-sensitive literals, loose/substring/heading-level-agnostic matching forbidden); DUPLICATE PREVENTION (G1-G3 pre-commit, G4-G7 post-commit, where G4's 'exactly one D1' makes an appended second section an immediate revert); the MIRROR HEADING '### Step 1.5: Harness Generation (P-002 / P-004)', fractional because the mirror's own Step 2 is Task Execution Loop and ten passages reference it, so renumbering is forbidden; and PARITY CRITERIA P1-P6. The atomicity argument is rewritten: the drift runs template-ahead-of-mirror, so a split commit WIDENS or REVERSES it rather than creating it. 181.005-T now UPDATES the existing template section IN PLACE and INSERTS the mirror section, in one commit; 181.004-T pre-asserts G1-G3 against live file content; rollback is a single-commit revert whose post-revert state is the known pre-existing drift, not a novel broken state."
  - "S8 (P2) — ADDRESSED AT PLAN REVISION 4, NOT CLOSED, PENDING INDEPENDENT ATTEMPT 03. Both halves are answered. (a) The 181.003-T contradiction is resolved in favour of the live record: it is an INERT AGENT-TEMPLATE / PROCEDURE DESIGN TASK that produces NO Python and adds NO src/ module. The plan's Composed-state check now names 181.002-T's resolver as the producer and Blast radius no longer attributes a src/ module to 181.003-T. Its output is made exact - the canonical phase text as test-owned fixture data at two named paths under tests/fixtures/ship_harness_phase/, following the workspace's own 169.011-T precedent - which also keeps 'inert' literally true, since editing the template's already-executed Step 2 early would both break inertness and destroy 181.005-T's atomicity. Size/complexity are re-derived against the CHANGED scope, M/high to S/medium, with the reasoning recorded in the plan and on the task; 181.005-T is re-derived and HELD at M/high with three named de-risking steps. (b) The re-scope guards and plan/verdict-manifest/source citations are propagated to the three task records that lacked them: 181.001-T, 181.003-T and 181.004-T."
  - "S9 (P2) — ADDRESSED AT PLAN REVISION 4, NOT CLOSED, PENDING INDEPENDENT ATTEMPT 03. Corrected in favour of the live carriers, not the plan frontmatter: source_stash_ids is now [76EBDE6D]. This was verified as a SINGLE-SOURCE correction rather than a multi-source relation - the governing decision's portfolio table assigns 76EBDE6D to P4 / 187-S / 181-F at line 993 and assigns 3EF5AAF2 to 177-S / 169-F at line 995, so 3EF5AAF2 was simply the wrong unit's ID. 76EBDE6D is an archived stash entry at .backlogit/archive/stash.jsonl line 234; every citation now records that location so the ID is resolvable rather than dangling. A source_stash_note in the plan frontmatter records the correction and its evidence, and the ID is cited consistently across the plan, 181-F, 187-S and all five task records."
  - "CONFIRMED CORRECT at attempt 02 and not to be re-litigated: the 184-S edge is genuinely removed and 187-S's live dependency list is exactly [188-S]; the graph is acyclic; 187-S is NOT stranded by 184-S's conditional withholding; the actor/automation split is real on every carrier; the single-commit ACTIVATE atomicity principle and its 174-S citation are sound in principle (though applied to an inverted premise, per S7); NO_HARNESS is a genuine failed precondition; sizing and the 2-hour rule hold (S/S/M/XS/M, unsized 0); no policy edit exists anywhere in template or installed form."
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 3
tags:
  - "plan-review"
  - "verdict-manifest"
  - "portfolio-2026-09-18"
  - "ship-lifecycle"
---

# Verdict manifest — Ship pre-task harness-generation lifecycle

This file is a **selection surface**, not a review. It names which immutable
attempt artifact is authoritative right now, and nothing else.

## Current verdict

| Field | Value |
|---|---|
| `plan_id` | `ship-harness-lifecycle-foundation` |
| `manifest_revision` | 5 |
| `plan_revision` | **4** |
| `latest_attempt` | **03** (against plan revision **4**) |
| `latest_artifact` | `docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-03.md` |
| `gate_result` | **ADVISORY** |
| `verdict` | **ADVISORY** |
| `verdict_is_pass` | **false** |
| `latest_remediation_revision` | 4 |
| `latest_disposition` | `ADVISORY-P2-ONLY` |
| `awaiting_attempt` | **null** — terminal |
| `p0_open` / `p1_open` / `p2_open` / `p3_open` | **0 / 0 / 2 / 0** |
| `findings_closed_at_attempt_02` | `S1`–`S6` (all six) |
| `findings_closed_at_attempt_03` | `S7`, `S8`, `S9` |
| `open_findings` | `S10` (P2), `S11` (P2) — non-blocking |

**`ADVISORY` is not `PASS`.** Attempt 03 applied the decision rule P0/P1 →
`FAIL`, P2-only → `ADVISORY`, P3-or-none → `PASS`, and landed on `ADVISORY`
because two P2 findings remain open. SM-2's `HARVEST_ADMITTED` state is defined
against `verdict: PASS`, so harvest on the strength of this manifest remains
**closed**.

**This unit is still not executable.** `187-S` is not publication-eligible, its
tasks are not claimable, and no Ship work is authorized from this manifest. It
is additionally gated on `188-S`, which must reach `shipped` first.

**Counts are now real**, asserted by an independent reviewer rather than by
Stage. No severity was lowered and no finding was downgraded to reach them.

**`S1`–`S6` remain closed**, re-checked at attempt 03 against the revision-4
plan and task records to confirm the edits did not regress them.

## What attempt 03 closed

* **`S7` (P1, was blocking) — CLOSED.** The plan is genuinely re-grounded in
  live state, and every fact it asserts about the two ACTIVATE targets was
  re-derived independently: the template carries
  `### Step 2: Harness Generation (P-002 / P-004)` at line 326; the mirror
  carries no harness-generation heading and zero occurrences of `harness-ready`
  or `harness-architect`; the step sequences are as stated (template 319/326/
  345/383/567/693, mirror 329/336/417/481/594); fractional numbering is already
  the mirror's own convention; and `Harness Generation` does occur in template
  prose (lines 4, 23, 379, 1062), so exact whole-line matching is justified.
  Both files are byte-identical to the `da8f890a` state the plan says it read,
  so its pinned line numbers hold. The counted gates are satisfiable today:
  `G1` = 1, `G2` = 0, `G3` = 1 and 1. The instruction is unambiguously *update
  in place* on the template and *insert at a fixed anchor* on the mirror, with
  nothing renumbered and rollback confined to a single-commit revert whose
  post-revert state is named plainly as the known pre-existing drift.
* **`S8` (P2) — CLOSED.** `181.003-T` is explicitly an inert agent-template /
  procedure-design task producing no Python, with two named fixture paths; the
  plan's Composed-state check and Blast radius agree; `181-F` states only
  `181.002-T` adds Python. Guards and plan/manifest/source citations are
  propagated to `181.001-T`, `181.003-T` and `181.004-T`. Sizes are coherent
  and honestly labelled — `181.003-T` re-derived to `S`/`medium` against a
  changed scope, `181.005-T` **held** at `M`/`high` with three named de-risking
  steps rather than downgraded.
* **`S9` (P2) — CLOSED.** Decision line 993 assigns `76EBDE6D` to
  `P4`/`187-S`/`181-F`; archive `stash.jsonl` line 234 resolves it; line 995
  assigns `3EF5AAF2` to `177-S`/`169-F`, which is also the declared
  `source_stash_ids` of the post-claim member-status plan. The single-source
  claim is correctly scoped to this unit and does not assert exclusivity.

## Findings open after attempt 03

* **`S10` (P2) — non-blocking.** The claim that "ten passages inside the mirror
  refer to 'Step 2' **meaning that loop**" is inaccurate for four of its ten
  cited lines. The citations themselves are exact and complete — lines 184, 214,
  275, 283, 302, 305, 326, 336, 377 and 748 are precisely the case-insensitive
  `step 2` occurrences — but lines 184, 214, 377 and 748 are lowercase
  references to local numbered sub-steps of *other* procedures (crash-resumption,
  Work Intake, the loop's own internals, Post-Merge Closure), not to
  `### Step 2: Task Execution Loop`. Parity criterion `P6`'s second clause
  therefore states an invariant that never held and cannot be satisfied even by
  a correct commit, and `181.004-T` asks the executor to record a set whose
  stated predicate does not match the supplied list. Held at P2 because the
  instruction it supports — renumber nothing, use `Step 1.5` — is correct and
  strictly conservative, `P6`'s first clause is unaffected, and every failure
  path is a halt in the safe direction.
* **`S11` (P2) — non-blocking.** The `D`/`G`/`P` label space diverges between
  the plan and `181.005-T`. `D2` and `D3` are swapped; the record's `G5` is the
  plan's `G6`; the record's `G6` has no plan counterpart; the record's `G7`
  means parity while the plan's `G7` is the renumbering detector that `R5`
  names; and the record's `P1`–`P6` are shifted relative to the plan's.
  Meanwhile `181.003-T` is directed to "plan parity criteria `P3`, `P4` and
  `P5`" and `181.004-T` to "the plan's `G1`-`G3`", so three records in one unit
  use one label space for different referents. Coverage was checked failure-mode
  by failure-mode and is complete under either set — the only loss is the
  redundant detection of a renumbered **non-anchor** mirror heading, which the
  record's scope contract already forbids — so it is not blocking. It is above
  P3 because `181.005-T` is the activation commit on the one file every future
  shipment execution passes through, and an auditor verifying a labelled gate
  cannot have two authoritative surfaces answering differently.

## What the preceding remediation did — and did not — do

| Did | Did not |
|---|---|
| Rewrote the plan to revision 4, grounded in re-verified live file state | Assert any verdict, or claim `PASS` |
| Recorded `S7`/`S8`/`S9` as *addressed, pending review* | Close, downgrade or defer any finding |
| Withdrew attempt 02's terminal-for-cycle designation, since remediation is now authorized | Alter attempt 02's `FAIL`, its counts, or its immutable artifact |
| Propagated scope guards and citations to `181.001-T`, `181.003-T`, `181.004-T` | Touch either live Ship surface — Stage writes no source or template |
| Re-derived `181.003-T` to `S`/`medium` against a changed scope, and held `181.005-T` at `M`/`high` | Lower any severity, or shrink a task to dodge the 2-hour rule |
| Corrected `source_stash_ids` to `[76EBDE6D]` on decision-table evidence | Invent a multi-source relation to reconcile the divergence |

## What attempt 02 closed — all six

* **`S1`** — verified on nine live carriers that no task generates, installs,
  modifies or deletes `188-S`'s deliverable, and that rollback is unit-scoped.
  The hardening pass is genuinely re-derived: `H1` rewritten, `H7`/`H8` new.
* **`S2`** — `181.002-T` is exactly the resolver: generates and installs no
  skill, writes nothing under `.github/skills/`, generates no file from any
  template, and consumes the actor read-only as an already-satisfied
  precondition.
* **`S3`** — `181.005-T` carries no P-004 cross-reference, names only the two
  authorized integration surfaces, forbids any policy-text edit including a
  cross-reference, and corrects the stale actor-existence sentence.
* **`S4`** — neither title carries the `and installed harness-architect` claim.
* **`S5`** — `181-F` cites decision revision 3, `D9`.
* **`S6`** — the entry manifest was schema-valid and self-consistent, with
  `REMEDIATED-PENDING-REVIEW` confined to `latest_disposition`.

## What attempt 02 raised — and how revision 4 answers it

Attempt 02's findings are **not closed** by anything below. Each entry states
the reviewer's observation, then what Stage changed. Attempt 03 judges whether
the answer holds.

* **`S7` (was P1, blocking) — addressed.** The observation was correct on live
  state: `templates/agents/_ship.agent.md.tmpl:326` already declares
  `### Step 2: Harness Generation (P-002 / P-004)`, while
  `.github/agents/_ship.agent.md` contains **no** harness-generation content at
  all — zero occurrences of `harness-ready` or `harness-architect`. Revision 4
  re-grounds the unit rather than defending the old premise. A **Live state of
  the two ACTIVATE targets** section records the evidence. A **The ACTIVATE
  contract, stated mechanically** section fixes the four things the executor
  was previously left to choose: exact whole-line case-sensitive **detection**
  literals `D1`–`D3`; **duplicate prevention** `G1`–`G3` pre-commit and
  `G4`–`G7` post-commit, where `G4`'s *exactly one* `D1` makes an appended
  second section an immediate revert; the **mirror heading**
  `### Step 1.5: Harness Generation (P-002 / P-004)`, fractional because the
  mirror's own Step 2 is the Task Execution Loop and ten passages reference it,
  so renumbering is forbidden; and **parity criteria** `P1`–`P6`. The atomicity
  argument is rewritten in the correct direction — the drift runs
  template-ahead-of-mirror, so a split commit *widens* or *reverses* it rather
  than creating it. `181.005-T` now **updates the existing template section in
  place** and **inserts** the mirror section, in one commit.
* **`S8` (P2) — addressed.** `181.003-T` is resolved in favour of the live
  record: an **inert agent-template / procedure design task** producing no
  Python and no `src/` module. Its output is made exact — the canonical phase
  text as test-owned fixture data at two named paths, following the workspace's
  own `169.011-T` precedent. The plan's Composed-state check and Blast radius
  no longer attribute a `src/` module to it. Size/complexity are re-derived
  against the *changed* scope (`M`/`high` → `S`/`medium`), and `181.005-T` is
  re-derived and **held** at `M`/`high` with three named de-risking steps.
  Scope guards and citations are propagated to `181.001-T`, `181.003-T` and
  `181.004-T`.
* **`S9` (P2) — addressed.** `source_stash_ids` is corrected to `[76EBDE6D]`,
  in favour of the live carriers rather than the plan frontmatter. This is a
  **single-source** correction, not a multi-source relation: the governing
  decision's portfolio table assigns `76EBDE6D` to `P4` / `187-S` / `181-F` at
  line 993 and assigns `3EF5AAF2` to `177-S` / `169-F` at line 995, so
  `3EF5AAF2` was simply another unit's ID. `76EBDE6D` is an **archived** entry
  at `.backlogit/archive/stash.jsonl` line 234; every citation now records that
  location so the ID resolves rather than dangles.

Nothing was downgraded, and no finding was deferred into the stash.

## What was re-verified and confirmed correct

Confirmed at attempt 02 and **re-checked after the revision-4 rewrite** to
ensure the remediation did not regress them:

* The `184-S` edge is **genuinely removed**; `187-S`'s live dependency list is
  exactly `[188-S]`, and the `188-S` bootstrap edge is intact.
* The graph is **acyclic**, and `187-S` is **not stranded** by the conditional
  withholding of `184-S`.
* The **actor/automation split is genuine** on every carrier, and the plan
  states the reviewer's point back correctly — axis 2 is fixed *in addition to*
  axis 1.
* `NO_HARNESS` is a genuine failed precondition; no waiver, bootstrap grant,
  `--force` or force-audit entry exists anywhere on this path.
* **`S1`–`S6` hold after the rewrite**: no task generates or installs `188-S`'s
  deliverable; `181.002-T` remains exactly the resolver; `181.005-T` still
  carries no policy cross-reference and names exactly two permitted surfaces;
  neither title carries the actor-install claim; decision revision 3 / `D9` is
  cited consistently; and this manifest still holds a `null` verdict with
  `REMEDIATED-PENDING-REVIEW` confined to `latest_disposition`.
* Sizing and the 2-hour rule still hold across all five tasks:
  `S`/`S`/`S`/`XS`/`M`, `unsized: 0`. The one change is `181.003-T`'s `M` → `S`
  re-derivation under `S8`.

## Attempt roster

`reviewed_revision` + `verdict` are what an **independent reviewer** judged.
`remediation_revision` + `disposition` are what **Stage** produced in response.
They are separate columns because merging them is how a fabricated PASS enters
the record. `REMEDIATED-PENDING-REVIEW` is never a `verdict` value; it is only
ever a `disposition`.

| Attempt | Artifact | Reviewed rev | Reviewer verdict | Remediation rev | Disposition |
|---|---|---|---|---|---|
| 01 | `…-attempt-01.md` | 2 | **FAIL** (P0 0 / P1 3 / P2 3 / P3 0) | 3 | `FAIL-BLOCKING-P1` |
| 02 | `…-attempt-02.md` | 3 | **FAIL** (P0 0 / P1 1 / P2 2 / P3 0) | 4 | `FAIL-BLOCKING-P1` |
| 03 | `…-attempt-03.md` | 4 | **ADVISORY** (P0 0 / P1 0 / P2 2 / P3 0) | — | `ADVISORY-P2-ONLY` |

The attempt-03 row asserts no verdict and confers no eligibility. It exists so
the roster shows an **outstanding obligation** rather than an apparently
complete history.

## Provenance

* Plan: `docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md` at revision 4
* Feature: `181-F` — Shipment: `187-S` (queued, depends on `188-S`)
* Source stash: `76EBDE6D` (archived — `.backlogit/archive/stash.jsonl` line 234)
* Bootstrap precursor: `docs/plans/2026-09-20-harness-architect-bootstrap-plan.md` (`188-S`)
* Governing decision: the 2026-09-18 shared-execution-architecture and
  portfolio-reslicing decision, revision 3, `D9`
* Origin of revision 2: PR-457 Copilot review thread `PRRT_kwDORzpWpM6kHrw5`

## Authority

Latest attempt and verdict are read from this manifest, never from the plan
body. Per-attempt reviews live one per attempt under
`docs/reviews/review-history/` and are never edited afterwards. A disagreement
between `latest_attempt`/`latest_artifact` and the roster derivation above is
`REVIEW_VERDICT_AMBIGUOUS`, not a matter of narrative.