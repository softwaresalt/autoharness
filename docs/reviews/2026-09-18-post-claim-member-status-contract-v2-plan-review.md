---
title: "Plan review verdict manifest — Canonical post-claim member-status contract (P-002.7), v2"
description: "Mutable verdict manifest for docs/plans/2026-09-18-post-claim-member-status-contract-plan.md. This file is a selection surface, not a review: it names which immutable attempt artifact is authoritative right now, and nothing else. The reviews live one per attempt under docs/reviews/review-history/ and are never edited after they are written. Latest attempt: 04, operator-designated terminal. Plan revision: 4. Independent attempt 01 reviewed revision 1 at content HEAD db39553a and returned FAIL/BLOCKED on two P0, three P1, two P2 and one P3. A Stage remediation cycle produced revision 2 and re-derived the executable task set from it, archiving five superseded tasks and creating one atomic ACTIVATE task plus five RED-owning tasks. Independent attempt 02 reviewed revision 2 at content HEAD 5aa8643f, verified both P0s and all three P1s closed, and returned FAIL/BLOCKED on zero P0, one P1, two P2 and two P3. A second Stage remediation cycle produced revision 3, and independent attempt 03 reviewed that revision at content HEAD 4b4330b9 and returned gate result FAIL, decision BLOCKED, on zero P0, one P1, zero P2 and one P3. Attempt 03 verified G1, G2, G3, G4 and G5 all genuinely closed, and found that the composed-state verdict line the plan gates on has no declared destination artifact and no declared line format anywhere in the plan or the six task records, which makes the plan's own rule that an absent verdict line is STATUS_CONTRACT_NOT_OBSERVED unevaluable, and that the plan names .github/workflows/ci.yml as a consumer that reads the verdict line as a gate when ci.yml consumes a unittest exit code and no task in 177-S modifies it. That is the open P1, L1. The open P3, L2, is that the computed size_composition rollup for 177-S and 169-F counts fourteen task members including the five archived absorbed tasks while custom_fields.items correctly lists nine tasks and the feature. The operator then lifted the terminal designation and authorized a third and final bounded remediation cycle, which produced revision 4: L1 was addressed by declaring one destination artifact (.autoharness/gates/p002-7-status-contract-verdict.txt, gitignored so it is never committed and never leaves the tree dirty), one literal line format per token, a single-writer atomic whole-file-replace rule, and a closed list of read outcomes that resolve to STATUS_CONTRACT_NOT_OBSERVED so absence is decidable; and by correcting the consumer direction so ci.yml is described as a producer of the unittest observations, with 169.016-T's own invocation made the authoritative evaluator via process exit code and verdict artifact, keeping the unit self-contained and adding no CI task. L2 is advisory, tool-derived, and was deliberately carried unaddressed. L1 is recorded as addressed pending review and L2 as carried; neither is closed, and the plan now awaits independent attempt 04. Independent terminal attempt 04 then reviewed revision 4 at content HEAD 42f2f8ec and returned gate result FAIL, decision BLOCKED, on zero P0, one P1, zero P2 and three P3. Attempt 04 verified L1 genuinely closed by re-derivation against the repository itself - git check-ignore resolves the verdict artifact to .gitignore:7 and ci.yml line 112 runs PYTHONPATH=src python -m unittest discover -s tests, confirming it is an exit-code producer and not a verdict-line consumer - and carried L2 forward as M4. The new blocking P1 is M1: the plan's declared rollout order PREPARE to RED to ACTIVATE to VERIFY to DOCS contradicts binding decision D2, whose rollout invariant is PREPARE to VERIFY to ACTIVATE with the complete RED, GREEN and compatibility evidence set produced before any activation, so the plan places its sole gate emitter 169.016-T after the single irreversible ACTIVATE commit 169.015-T that mutates all four declared surfaces. The deviation is unreconciled - the plan cites F7, F10, D6 and R5 and never cites D2 - and selective, because 169.015-T's record cites decision D2 by name for one-task-one-commit atomicity while dropping the ordering rule from the same section; eight of eight other portfolio plans use PREPARE VERIFY ACTIVATE, and a conformant framing was available because GREEN is observable against 169.011-T's inert near-miss fixtures before activation. M2, M3 and M4 are advisory P3. Because attempt 04 is the operator-declared terminal attempt, no fourth remediation cycle was proposed or executed: M1 is halted for operator disposition, whose options are authorizing a further bounded cycle, recording an explicit waiver reconciling the plan against D2, or amending D2 itself. The plan is BLOCKED, not publication-eligible, not harvest-ready and not Ship-ready; the block is confined to this unit because 177-S is a DAG root with no successor shipment. No PASS exists anywhere in this record and none is asserted."
doc_type: review-manifest
source: docs/reviews/2026-09-18-post-claim-member-status-contract-v2-plan-review.md
date: 2026-09-18
manifest_shape: attempt-roster
plan_id: post-claim-member-status-contract-v2
plan_path: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
plan_revision: 4
feature_id: 169-F
shipment_id: 177-S
predecessor_manifest: docs/reviews/2026-09-17-post-claim-member-status-contract-plan-review.md
latest_attempt: 4
review_terminal: true
terminal_designation: operator-declared
terminal_disposition: HALTED-FOR-OPERATOR-DISPOSITION
terminal_note: "Attempt 03 was designated terminal by the operator, who subsequently lifted that designation and authorized a third and final bounded remediation cycle producing revision 4. Attempt 04 is the operator-declared terminal attempt against revision 4 and returned FAIL/BLOCKED on a newly derived P1. Because attempt 04 is terminal, no fourth remediation cycle is authorized, proposed or executed: the blocking finding is halted for operator disposition. Terminality never closed a finding and no severity was lowered to reach a closable state."
awaiting_attempt: null
reviewed_content_head: 42f2f8ec
gate_result: FAIL
verdict: BLOCKED
verdict_is_pass: false
verdict_note: "verdict is BLOCKED because independent terminal attempt 04 judged plan revision 4 at content HEAD 42f2f8ec and derived one open P1, M1, against binding decision D2. Attempt 03's L1 was independently re-derived closed from the plan, the task records and the repository itself, not from a closure summary. L2 was carried unaddressed by design and is re-raised as M4. Stage asserts no PASS and has performed no self-review."
p0_open: 0
p1_open: 1
p2_open: 0
p3_open: 3
open_findings: [M1, M2, M3, M4]
blocking_findings: [M1]
findings_addressed_pending_review: []
findings_carried_unaddressed: []
remediation_cycle_proposed: false
disposition: HALTED-FOR-OPERATOR-DISPOSITION
open_counts_note: "Counts are attempt 04's. L1 (P1) is closed by independent re-derivation at attempt 04. M1 is a new P1 and is blocking: the plan's declared rollout order PREPARE to RED to ACTIVATE to VERIFY to DOCS contradicts binding decision D2, whose rollout invariant is PREPARE to VERIFY to ACTIVATE with the complete evidence set produced before any activation. M2, M3 and M4 are advisory P3. No severity was lowered to reach a closable state."
remediation_authorization: none-this-cycle
latest_remediation_revision: 4
latest_disposition: HALTED-FOR-OPERATOR-DISPOSITION
latest_artifact: docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-04.md
attempts:
  - attempt: 1
    artifact: docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-01.md
    reviewed_revision: 1
    reviewed_content_head: db39553a
    verdict: BLOCKED
    p0_open: 2
    p1_open: 3
    p2_open: 2
    p3_open: 1
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: 2
    disposition: REMEDIATED-PENDING-REVIEW
    terminal: false
    findings_state: closed-at-attempt-02
  - attempt: 2
    artifact: docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-02.md
    reviewed_revision: 2
    reviewed_content_head: 5aa8643f
    reviewed_branch: chore/stage-176-s-workflow-defects
    verdict: BLOCKED
    p0_open: 0
    p1_open: 1
    p2_open: 2
    p3_open: 2
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: 3
    disposition: REMEDIATED-PENDING-REVIEW
    terminal: false
    closed_predecessor_findings: [A1, A2, B1, B2, B3, C1, C2, D1]
  - attempt: 3
    artifact: docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-03.md
    reviewed_revision: 3
    reviewed_content_head: 4b4330b9
    reviewed_branch: chore/stage-176-s-workflow-defects
    verdict: BLOCKED
    gate_result: FAIL
    p0_open: 0
    p1_open: 1
    p2_open: 0
    p3_open: 1
    open_findings: [L1, L2]
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: 4
    disposition: REMEDIATED-PENDING-REVIEW
    terminal: false
    terminal_designation: lifted-by-operator
    closed_predecessor_findings: [G1, G2, G3, G4, G5]
  - attempt: 4
    artifact: docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-04.md
    reviewed_revision: 4
    reviewed_content_head: 42f2f8ec
    reviewed_branch: chore/stage-176-s-workflow-defects
    verdict: BLOCKED
    gate_result: FAIL
    p0_open: 0
    p1_open: 1
    p2_open: 0
    p3_open: 3
    open_findings: [M1, M2, M3, M4]
    blocking_findings: [M1]
    dispatch_mode: single-agent-declared-degradation
    anchor_route: absent
    remediation_revision: null
    disposition: HALTED-FOR-OPERATOR-DISPOSITION
    terminal: true
    terminal_designation: operator-declared
    closed_predecessor_findings: [L1]
carried_forward_context:
  - artifact: docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-08.md
    reason: "Terminal attempt against the superseded revision-7 plan. Its B1 (phantom source stash 3EF5AAF9) was verified closed at db39553a and re-verified closed at 5aa8643f: every live record carries 3EF5AAF2, and the sole 3EF5AAF9 occurrence is an explicit historical citation in 169-F's description recording that the phantom ID is closed. Its B2 (GREEN-only assertions) was recorded as A2 of attempt 01 and is verified CLOSED at attempt 02: five RED-owning tasks exist and every GREEN task has a RED predecessor."
    state: closed-at-attempt-02
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
tags:
  - "plan-review"
  - "verdict-manifest"
  - "portfolio-2026-09-18"
---

# Verdict manifest — Canonical post-claim member-status contract (P-002.7), v2

This file is a **selection surface**, not a review. It names which immutable
attempt artifact is authoritative right now, and nothing else.

## Current verdict

| Field | Value |
|---|---|
| `plan_id` | `post-claim-member-status-contract-v2` |
| `plan_path` | `docs/plans/2026-09-18-post-claim-member-status-contract-plan.md` |
| `plan_revision` | 4 |
| `latest_attempt` | **04** (operator-declared terminal) |
| `latest_artifact` | `docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-04.md` |
| `reviewed_content_head` | `42f2f8ec` |
| `gate_result` (attempt 04, immutable) | **FAIL** |
| `verdict` | **BLOCKED** (derived — the judged content is current) |
| `verdict_is_pass` | **false** |
| `latest_remediation_revision` | **4** |
| `latest_disposition` | **HALTED-FOR-OPERATOR-DISPOSITION** |
| `awaiting_attempt` | **null** (terminal — no attempt 05 is authorized) |
| `p0_open` | **0** |
| `p1_open` | **1** (`M1` — new at attempt 04, **blocking**) |
| `p2_open` | **0** |
| `p3_open` | **3** (`M2`, `M3`, `M4` — advisory; `M4` carries forward `L2`) |

**The top-level `verdict` is derived, not authored.** Take the highest-numbered
roster entry — attempt 04. Its `remediation_revision` is **null**, so the
content attempt 04 judged (revision 4 at `42f2f8ec`) is **still current**: the
reviewer's verdict describes the plan text as it stands, so it is carried up
unchanged. `verdict` is **BLOCKED** and `gate_result` is **FAIL**, the immutable
record of what attempt 04 read.

`disposition` is **HALTED-FOR-OPERATOR-DISPOSITION**, which states what Stage
did — *nothing* — and never what a reviewer found. Attempt 04 is the
**operator-declared terminal** attempt, so the open P1 `M1` was **not**
remediated and **no fourth cycle was proposed**. `remediation_cycle_proposed`
is `false`. The finding is handed to the operator intact, at its derived
severity; no severity was lowered to reach a closable state.

This plan is **not publication-eligible, not harvest-ready and not Ship-ready**
until `M1` is disposed of. `177-S` is a DAG root with **no successor
shipment**, so the block is confined to this unit.

**No `PASS` is asserted.** Under the plan-review severity table one P1 returns
FAIL. This manifest has never reported `PASS` and does not report one now, so
harvest remains closed and no Ship work is authorized against `177-S`. The
operator lifted the terminal designation and authorized one bounded remediation
cycle, the third and final permitted; terminality bounded the *review loop*,
never a *finding*, and no severity was lowered.

**`p1_open` and `p3_open` above are attempt 03's counts and they still stand.**
`L1` was *addressed* by revision 4; `L2` is advisory, tool-derived, and was
deliberately left unaddressed. Both are *decremented* only by a further
independent attempt — attempt 04 — or by an explicit recorded operator waiver.
Neither has happened.

**The attempt-01 and attempt-02 counts are closed, and by the only authority
that can close them.** Attempt 01's two P0, three P1, two P2 and one P3 were
closed because an *independent* attempt 02 re-derived each from plan, task and
manifest state; attempt 02's `G1`–`G5` are closed because an *independent*
attempt 03 did the same. Attempt-08 `B2`, carried forward as attempt-01 `A2`,
is closed with them. The open counts above are attempt 03's **own, new**
findings.

**Remediation has not converged across three cycles, and revision 4 closes the
last structural gap rather than adding a mechanism.** Revision 2 closed every
attempt-01 finding, including both P0s, and left a new P1 behind. Revision 3
closed all five attempt-02 findings — including a genuinely difficult
three-token vocabulary alignment and a stale-edge cleanup — and left a new P1
behind: the verdict line that the whole composed-state gate depends on was
required, was gated on, and was never given a destination or a format.
Revision 4 supplies exactly that — one path, one literal line form per token,
one writer, one atomicity rule, one closed absence vocabulary — and corrects the
inverted consumer claim instead of building a CI gate around it.

## What attempt 01 records

Independent first review opened against plan revision 1 at content HEAD
`db39553a`; gate result FAIL, decision BLOCKED, two P0, three P1, two P2 and
one P3 open.

Persona coverage was complete across all seven personas (Constitution, Python,
Scope Boundary, Learnings, Architecture, Agent-Native Parity, Security Lens).
Security Lens returned a nil result — the unit changes declarations only and
exposes no execution boundary, credential surface or external trust boundary —
recorded as a covered persona, not a skipped one. Reviewer subagent dispatch
was unavailable, so every persona ran as a declared inline pass with its own
finding list; `.autoharness/config.yaml` declares no `anchor_review` route, so
the cross-model rubrics ran same-model. Engram indexed retrieval was
circuit-open and was not retried, and intercom was unavailable, so visibility
was local-only. All evidence was gathered by bounded direct exact-path reads,
`git` plumbing, and read-only backlogit SQL.

**Both P0s are contradictions between the plan and the shipment it governs**,
not defects in the plan's reasoning.

`A1` — the plan's Rollout states "ACTIVATE. One task, one commit updating every
declared surface — template and installed mirror together", and decision D2
declares "the `T1`/`T2` shape on `177-S`" retired "by construction". It is not
retired: `177-S` carries `169.001-T` ("author the canonical clause in the
policy **template**", S) and `169.002-T` ("apply the identical clause to the
installed policy **mirror**", XS), joined by a `blocks` edge in `item_deps`.
That is precisely the two-tasks-joined-by-an-edge shape D2 forbids, on
precisely the pair the plan names as the pair that must never disagree, in a
`queued` shipment that is claimable today.

`A2` — the plan's central claim is that "Every assertion in this unit is
observed failing … before it is observed passing", closing attempt-08 `B2`.
That defect is still encoded: `169.008-T` is a GREEN task adding
**mirror-divergence** and **version-attribution** assertions, `169.005-T` is a
GREEN task for the composed state-machine suite, and the only RED tasks
(`169.009-T`, `169.010-T`) cover the three transition states and
wiring/cross-reference — not mirror-divergence, not version-attribution, not
the negative state-machine rows. No task records a per-assertion RED
observation, so `R2`'s mitigation has no implementing task.

The three P1s are: `B1`, the plan enumerates no implementation units at all
while its shipment carries eight, so no surface exists on which either P0 could
be caught; `B2`, the surface list the whole contract asserts over is never
enumerated and its "fixed count" never stated, so `R1`'s mitigation and
decision `R5`'s two-hour activation-width rule are both unverifiable; and `B3`,
the composed-state check names producer and consumer in prose rather than as
identified artifacts, leaving the conformance test's assertion target
undetermined.

The two P2s are `C1`, the plan's claim that attempt 08 "was blocked on a single
evidence defect" when the record shows two P1s and one P2 — the provenance P1
was genuinely closed out of band by F10, verified at `db39553a`, but the
sentence as written is false about the record and is replicated in `169-F`'s
description — and `C2`, the `verdict`-key enum defect. The P3 is that the
manifest's item order places the RED tasks last and the T-labels are
non-monotonic against the IDs; `item_deps` nonetheless enforces RED-first, so
execution order is correct.

Attempt 01 also recorded, positively, that the DAG-root claim is empirically
confirmed (`177-S` has no edge in either direction while every other queued
defect unit has one, and the old false-star edge `177-S → 176-S` is gone), that
the diagnosis of the attempt-08 evidence defect is exactly right, that the
out-of-scope boundary is disciplined, and that attempt-08 `B1` is genuinely
closed.

## What follows attempt 01

A Stage remediation cycle, authorized by the operator as a single bounded
cycle, produced **plan revision 2** and **re-derived the executable task set
from it**, rather than retaining the superseded plan's task shape. What
changed, per finding:

* **A1 (P0)** — the split activation is gone. `169.001-T` (policy template),
  `169.002-T` (installed policy mirror) and `169.003-T` (Ship agent pair) were
  **archived with absorption provenance** and replaced by a single
  **`169.015-T`**, "ACTIVATE: transcribe the clause into all four declared
  surfaces in one commit". One task, one commit, every declared surface —
  which is the only shape that keeps each template/mirror pair consistent at
  every commit boundary, because a `blocks` edge orders two commits without
  fusing them. The archived records state truthfully that they were absorbed
  and never executed; no deletion history was fabricated.
* **A2 (P0)** — every assertion now enters in a RED task that individually
  records the observed pre-implementation failure. Mirror-divergence moved to
  new **`169.012-T`**, version-attribution to new **`169.013-T`**, and the
  negative state-machine rows plus four-surface closure to new
  **`169.014-T`**. The two GREEN tasks that had been introducing them,
  `169.005-T` and `169.008-T`, were archived with absorption provenance; their
  observation role is absorbed by new **`169.016-T`**, which is explicitly
  forbidden from adding any assertion. The plan also now carries a
  **discriminating RED rule**: each assertion records two observations — an
  absence RED against current surfaces, failing individually with its own
  marker, and a RED against a deliberately near-miss fixture. The second is
  what proves the assertion tests the contract rather than a file's existence.
  Aggregate suite exit codes are stated to be insufficient evidence.
* **B1 (P1)** — the plan now carries a **`## Tasks` table** with nine rows
  (ID, task, phase, size, complexity), plus an **assertion-to-task map**
  binding each of the five assertion families to its RED owner and its
  discriminating fixture.
* **B2 (P1)** — a new **`## Declared surfaces`** section states the marker
  set, the search scope, the exclusion rule (`.autoharness/staging/`,
  gitignored at `.gitignore:6` as generated verify-workspace output rather than
  a mirror), the enumerated four-path list, and the current marker count,
  which is **0**. `declared_surface_count: 4` is now a checkable number.
* **B3 (P1)** — the composed-state check names producer and consumer **by
  exact path**: producer `tests/test_p002_7_member_status_contract.py`;
  consumers `.github/workflows/ci.yml` and `.github/agents/_ship.agent.md`
  item 4 together with its template.
* **C1 (P2)** — the attempt-08 narrative is corrected wherever it appeared.
  The plan and `169-F` now state that attempt 08 recorded **two P1s and one
  P2**, that `B1` (phantom stash `3EF5AAF9`) was closed by decision F10's
  correction to `3EF5AAF2`, and that `B2` remained open. The false "single
  evidence defect" sentence is gone from both.
* **C2 (P2)** — the plan's `verdict` frontmatter key is now `null`, with the
  disposition value moved to a `disposition` key where it belongs.
* **D1 (P3)** — the `177-S` manifest is rebuilt in **phase order** — PREPARE,
  RED, ACTIVATE, VERIFY, DOCS — so reading it top to bottom shows RED before
  GREEN, and the shipment description states that the order is phase order.

A new **`169.011-T`** PREPARE task was added ahead of the RED tasks. It authors
the canonical vocabulary, the surface-enumeration rule and the near-miss
fixtures as **inert test-owned data**, changing no declared surface. This is
what makes the atomic `169.015-T` survive the **2-hour re-check**: with every
word already authored, the four-surface commit is mechanical transcription
rather than composition. The plan records the pre-specified fallback decision
`R5` requires — if the bound is ever threatened, **narrow the contract** by
dropping the Ship-agent pair (`declared_surface_count` 4 → 2), **never split
the activation commit**.

Source defect ID **`3EF5AAF2`** is carried throughout; the phantom `3EF5AAF9`
appears nowhere in live or archived records.

The plan was rewritten as a single coherent current-state document. It carries
no correction log and no review addendum: the remediation narrative lives here,
in the mutable manifest, which is the surface designed to hold it.

**The findings were not closed by that remediation.** Closing them required an
independent attempt 02 against revision 2, which is recorded below.

## What attempt 02 records

Independent second review opened against plan revision 2 at content HEAD
`5aa8643f` on branch `chore/stage-176-s-workflow-defects`; gate result
**FAIL**, decision **BLOCKED**, zero P0, one P1, two P2 and two P3 open.

Persona coverage was complete across all seven personas, with Agent-Native
Parity and Security Lens both triggered and run. Dispatch was again
`single-agent-declared-degradation` with no `anchor_review` route; engram
indexed retrieval was circuit-open and not retried; intercom was unavailable,
so visibility was local-only. Evidence came from bounded direct exact-path
reads, `git` plumbing, read-only backlogit SQL over a freshly synced index,
and direct reads of `.backlogit/queue/*.md` for task bodies.

**Both P0s and all three P1s are verified closed**, each re-derived from the
executable surface rather than accepted from the remediation narrative:

* **A1 (P0)** — activation is a single task. `169.015-T` is the only ACTIVATE
  task in `177-S`; the split template/mirror pair is archived; no `blocks` edge
  divides activation; the task record carries an explicit
  `TRANSCRIPTION ONLY - NO AUTHORING` invariant and a single-commit rule.
* **A2 (P0, = attempt-08 `B2`)** — every assertion family now has a RED owner.
  Five RED-owning tasks exist, `169.005-T` and `169.008-T` are archived, and
  no GREEN task in the manifest lacks a RED predecessor in `item_deps`.
* **B1 (P1)** — the plan carries a full task table with per-task size,
  complexity and phase; all nine live `169.x` tasks match it on **both** axes,
  and all carry `size_source: agent` with a non-empty `size_ruleset_version`.
* **B2 (P1)** — the affected surfaces are enumerated exactly rather than
  gestured at, and the `P-002.7` marker count across the declared search scope
  was independently re-counted at **0**, confirming the plan's claim.
* **B3 (P1)** — producer/consumer relationships are tabulated rather than
  left in prose.
* **C1, C2 (P2)** and **D1 (P3)** are likewise closed: the attempt-08 record
  is stated correctly, `verdict: null` was used with a separate disposition
  key, and the `177-S` `items` array is in phase order.

Consumer anchors were re-verified in source: `backlogit_claim_shipment` is
item 4 at `.github/agents/_ship.agent.md:267`, with the intake-reconciliation
note at line 311. Source defect ID `3EF5AAF2` is carried by `169-F`, `177-S`
and all nine live `169.x` tasks; the sole `3EF5AAF9` occurrence is an explicit
*historical* citation in `169-F`'s description recording that the phantom ID is
closed, which is correct rather than a defect.

**The open P1 (`G1`) is a composed-state token seam.** The plan declares the
verdict vocabulary `STATUS_CONTRACT_HELD` / `STATUS_CONTRACT_DIVERGENT` /
`STATUS_CONTRACT_NOT_OBSERVED`. `169.016-T`, the **only** verdict-emitting
task, emits `CONTRACT_ACTIVE` / `CONTRACT_INCOMPLETE`. Exhaustive search
confirms zero overlap: `STATUS_CONTRACT` appears in no backlogit record, and
`CONTRACT_ACTIVE|CONTRACT_INCOMPLETE` appears in no plan. The two-token task
vocabulary also *deletes* the not-observed state, collapsing decision `D6`'s
mandated three states to two — the precise failure mode
`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`
records. A secondary seam sits alongside it: the plan's Producer row says the
test module emits the observation, while the task record makes `169.016-T` the
emitter.

**The two P2s** are `G2`, five stale `item_deps` edges preserving the retired
T1/T2 chain (all five predecessors are archived and out of the manifest, so no
live task has an archived predecessor and `A1` is substantively closed, but the
forbidden shape is still queryable and two edges originate in live RED tasks —
`backlogit_remove_dependency` exists, so they are removable); and `G3`, the
`R5` narrowing rule conflicting with ACTIVATE's own no-authoring invariant and
with RED-first, plus the observation that dropping the Ship-agent pair *deletes*
`169.010-T`'s bidirectional assertion family rather than narrowing it.

**The two P3s** are `G4`, residual naming from the retired shape (`169.007-T`
still titled "P-002.7 **T6**: …", `169-F`'s description listing only PREPARE,
VERIFY, ACTIVATE with no RED); and `G5`, `requires_plan_hardening: false`
despite two template families — noted only because the hardening *content* is
present and materially complete, so the plan-review FAIL condition for missing
hardening is not met.

## What follows attempt 02

A second Stage remediation cycle, authorized by the operator as a single
bounded cycle, produced **plan revision 3**. What the revision changed, per
finding:

* **G1 (P1)** — resolved by **collapsing the seam onto the D6 vocabulary**,
  not by inventing a third. `169.016-T` now emits exactly
  `STATUS_CONTRACT_HELD`, `STATUS_CONTRACT_DIVERGENT` and
  `STATUS_CONTRACT_NOT_OBSERVED`; `CONTRACT_ACTIVE` and `CONTRACT_INCOMPLETE`
  are gone from every record. The plan's Producer/Consumer table was split so
  the two roles no longer contradict each other: the **test module produces
  per-assertion observations**, and `169.016-T` is the **sole emitter** of the
  single verdict line derived from them. A new `### Emission conditions`
  subsection gives objective, **ordered** conditions rather than a prose
  description: `STATUS_CONTRACT_NOT_OBSERVED` is evaluated **first** and fires
  on an import raise, a non-empty `loader.errors`, any `_FailedTest`, zero
  executed assertions, or any assertion family lacking a per-assertion record;
  then `STATUS_CONTRACT_DIVERGENT` on any failing assertion, naming the
  offending surface; then `STATUS_CONTRACT_HELD`, which requires every
  RED-proven assertion to have an individual passing record. **An absent
  verdict line is itself `STATUS_CONTRACT_NOT_OBSERVED`**, so silence cannot be
  read as a pass, and `STATUS_CONTRACT_HELD` is stated as the only pass token.
  `169-F`, `177-S` and `169.007-T` carry the same three tokens, so plan, task
  and manifest now agree. Hardening answers `H9`–`H11` and risk `R7` were added
  to record the vocabulary and the fail-closed default.
* **G2 (P2)** — the stale edges are **removed**, not documented. Enumerating
  `item_deps` over the five archived tasks returned **six** edges (attempt 02
  named five): `169.001-T → 169.009-T`, `169.001-T → 169.010-T`,
  `169.002-T → 169.001-T`, `169.003-T → 169.002-T`, `169.005-T → 169.003-T`
  and `169.008-T → 169.003-T`. All six were removed with
  `backlogit_remove_dependency`, and the archived records' `dependencies`
  frontmatter was cleared with them. No archived task now appears in any live
  task's dependency closure. The surviving edge set expresses exactly the
  PREPARE → RED → ACTIVATE → VERIFY → DOCS ordering: the five RED tasks depend
  on `169.011-T`, `169.015-T` depends on all five RED tasks, `169.016-T`
  depends on `169.015-T`, and `169.007-T` depends on `169.016-T`. The
  absorption provenance the archived records carry in prose is untouched —
  only the executable edges were retired, and `177-S`'s description now records
  what was removed and why.
* **G3 (P2)** — resolved **in favour of the atomic activation contract**. The
  old `R5` rule let Ship narrow the contract in place if `169.015-T` threatened
  the 2-hour rule; that required re-deriving an assertion inside a
  transcription-only task, which is authoring, and would admit a never-red
  assertion after the production text existed. It also *deleted* `169.010-T`'s
  bidirectional family rather than narrowing it. The plan's "2-hour check on
  ACTIVATE" is now a four-step **halt and return to Stage**: `169.015-T` halts,
  the shipment stops, Stage — not Ship — decides any reduction of
  `declared_surface_count`, and Stage re-plans the consequences (retiring
  `169.010-T`'s family outright and re-observing `169.014-T`'s closure
  assertion RED) before activation resumes. The task may not silently narrow
  or author assertions during Ship. `R5` was rewritten and `R8` added;
  `169-F`, `169.015-T` and `177-S` state the same rule.
* **G4 (P3)** — residual naming from the retired shape is corrected.
  `169.007-T` is retitled `P-002.7 DOCS: …` in place of `P-002.7 T6: …`, and
  `169-F`'s description now states this unit's actual order as **PREPARE, RED,
  ACTIVATE, VERIFY, DOCS**, noting that decision `D2` governs the *atomicity*
  of the activation rather than the phase list — which is how a phase list with
  no RED phase in it came to be written down.
* **G5 (P3)** — `requires_plan_hardening` is now **`true`**, with a rationale
  naming the elevated blast-radius signal: the four declared surfaces span two
  template families, `templates/policies/` and `templates/agents/`. The
  hardening section's preamble was reframed from a completeness pass into a
  **gate**, which is what P-006 requires once the flag is `true`. Attempt 02
  already recorded the hardening content as present and materially complete, so
  the flag change records what was already true rather than demanding new work.

`177-S` remains a DAG root with no incoming edge, and its `items` array remains
in phase order — no manifest reordering was needed here. Source defect ID
`3EF5AAF2` is unchanged throughout, and the sole `3EF5AAF9` occurrence remains
the explicit historical citation in `169-F` recording that the phantom ID is
closed.

The plan was rewritten as a single coherent current-state document. It carries
no correction log and no review addendum: the remediation narrative lives here,
in the mutable manifest, which is the surface designed to hold it.

**The findings are not closed by this remediation.** Closing them requires an
independent attempt 03 against revision 3, which is recorded below.

## What attempt 03 records

Independent third review opened against plan revision 3 at content HEAD
`4b4330b9` on branch `chore/stage-176-s-workflow-defects`; gate result
**FAIL**, decision **BLOCKED**, zero P0, one P1, zero P2 and one P3 open. The
operator designated this the terminal review cycle.

Persona coverage was complete across all seven personas, with Agent-Native
Parity and Security Lens both triggered and run. Dispatch was again
`single-agent-declared-degradation` with no `anchor_review` route; engram
indexed retrieval was circuit-open and not retried; intercom and graphtor-docs
were unavailable, so visibility was local-only. Evidence came from bounded
direct exact-path reads, `git` plumbing, and read-only backlogit MCP reads and
SQL over a freshly synced index.

**All five attempt-02 findings are verified closed**, each re-derived from the
executable surface rather than accepted from the remediation narrative:

* **G1 (P1) — closed.** The plan's Producer row, `169.016-T` and every
  consumer now carry exactly the `D6` three-token vocabulary with ordered,
  objective emission conditions. The vocabulary is identical in plan text and
  in the task record; no fourth token and no silent-default path survives.
* **G2 (P2) — closed.** `item_deps` for `169.%` is now exactly **12 live
  edges** — five RED tasks each gated on `169.011-T`, `169.015-T` gated on all
  five RED tasks, `169.016-T` on `169.015-T`, and `169.007-T` on `169.016-T`.
  All six stale edges left by the retired chain are gone, the
  PREPARE→RED→ACTIVATE→VERIFY→DOCS ordering is preserved, and the graph is
  acyclic with a single entry point.
* **G3 (P2) — closed.** The mid-flight narrowing path is replaced by a halt and
  return to Stage, stated identically in the plan, `169-F`, `169.015-T` and
  `177-S`. Ship can no longer reduce `declared_surface_count` or author an
  assertion during execution.
* **G4 (P3) — closed.** `169.007-T` is retitled to the DOCS phase and `169-F`
  states the actual PREPARE/RED/ACTIVATE/VERIFY/DOCS order.
* **G5 (P3) — closed.** `requires_plan_hardening` is `true` and the hardening
  section reads as a gate rather than a completeness pass.

Correspondence was re-verified independently: all nine live `169.x` tasks carry
`size`, `complexity`, `size_source: agent` and a non-empty
`size_ruleset_version`, matching the plan's table on both axes with the 2-hour
rule holding; every assertion has a RED-owning task preceding its GREEN; the
activation is a single atomic commit owned by `169.015-T`; the `P-002.7` marker
count across the four declared surfaces is **0**, and
`tests/test_p002_7_member_status_contract.py` correctly does not yet exist, so
the RED phase is genuinely red; all four declared surfaces exist; provenance
`3EF5AAF2` is on `169-F`, `177-S` and every `169.x` record with the phantom
`3EF5AAF9` appearing only as the historical citation; and `177-S` is a true DAG
root with no successor depending on it.

**The open P1 is `L1`:** the composed-state **verdict line has no declared
destination artifact and no declared line format**. A repository-wide search
for the token finds worked forms only in the two spike plans; this plan has
none, in the plan body or in any of the six task records. Because the plan's
own rule is that an *absent* verdict line is itself
`STATUS_CONTRACT_NOT_OBSERVED` (`R8`/`H11`), a reader cannot tell absence from
presence-elsewhere, and the gate is unevaluable as written. Compounding it, the
Consumer row names `.github/workflows/ci.yml` as reading the verdict line as a
gate; `ci.yml`'s `test` job in fact runs the stdlib unittest suite and consumes
an **exit code**, and the suite *produces* the observations that `169.016-T`
reads *before* emitting the line — the direction is inverted. No task in
`177-S` modifies `ci.yml`, and `169.015-T` writes only the clause, note and
cross-reference into the four declared surfaces, so neither declared consumer
is delivered by this unit. This engages Principle V (Structured Observability):
an observation with no destination is not an observation.

**The open P3 is `L2`:** the computed `size_composition` rollup on `177-S` and
`169-F` counts **14** task members, including the five archived absorbed tasks
(`169.001/002/003/005/008-T`), while `custom_fields.items` correctly lists the
nine live tasks plus `169-F`. This is tool-derived — the rollup runs over
feature children rather than the manifest — so no plan change is warranted; one
clarifying sentence in the `177-S` description would close it.

## What follows attempt 03

The operator **lifted the terminal designation** and authorized a third and
final bounded remediation cycle. It produced **plan revision 4**. What the
revision changed, per finding:

* **`L1` (P1)** — addressed by **naming the destination and the format, and by
  correcting the consumer direction rather than building a CI gate around it**.
  The verdict now has **one destination**,
  `.autoharness/gates/p002-7-status-contract-verdict.txt`, and **one literal
  line form per token** — `COMPOSED_STATE: ` prefix, token as the first field,
  ` | `-separated fields, with `families`/`assertions_passed`/
  `declared_surface_count`/`resolved_surface_count` for `STATUS_CONTRACT_HELD`,
  `families`/`failed`/`surface`/`divergence` for `STATUS_CONTRACT_DIVERGENT`,
  and a closed `reason=` vocabulary (`import_error`, `loader_errors`,
  `failed_test_placeholder`, `zero_assertions`, `family_unrecorded`) for
  `STATUS_CONTRACT_NOT_OBSERVED`. **Ownership and write behaviour are
  specified**: `169.016-T` is the sole writer, the write is atomic via a
  same-directory temporary file and a rename, and each run replaces the whole
  file so the artifact holds exactly one `COMPOSED_STATE:` line and is never
  appended to. **Absence is now decidable**: missing, unreadable, empty, no
  `COMPOSED_STATE:` line, *more than one* such line, or an unrecognised token
  all resolve to `STATUS_CONTRACT_NOT_OBSERVED`. That is what makes the plan's
  pre-existing rule — an absent verdict line *is* `STATUS_CONTRACT_NOT_OBSERVED`
  (`R8`, `H11`) — evaluable instead of ambiguous, and it is fully compatible
  with the unit's no-observation semantics: absence is a *reading*, never an
  error and never a default pass. The contract is mirrored into `169.016-T`,
  into the DOCS task `169.007-T`, into `169-F` and into the `177-S` manifest,
  and stated in the Composed-state table's Producer/Verdict-artifact/Consumer
  rows plus new hardening answers `H15` and `H16`.
* **The false `ci.yml` consumer claim is corrected, and the unit stays
  self-contained.** `.github/workflows/ci.yml` is now described as a
  **producer** — its `test` job runs
  `PYTHONPATH=src python -m unittest discover -s tests` and consumes an *exit
  code*, and that suite produces the observations the verdict is derived
  *from*. **No CI consumer task was added**, because none is necessary:
  `169.016-T`'s own invocation is the authoritative evaluator, exiting zero
  **only** on `STATUS_CONTRACT_HELD` and non-zero on the other two tokens, so
  the exit code and the artifact carry the same verdict by construction. No
  task in `177-S` modifies `ci.yml`, no workflow is added, and the scope was
  not broadened into CI redesign. Ship's claim sequence is reclassified as a
  consumer of the **`P-002.7` contract text** that `169.015-T` writes into that
  declared surface — which this unit *does* deliver — rather than of the
  verdict line.
* **The artifact cannot be left dirty.** `.autoharness/gates/` is gitignored,
  so the verdict is a generated observation *about* the tracked surfaces rather
  than a tracked surface itself: never committed, never in a diff, never a
  stray working-tree change after `169.016-T` runs. `169.007-T` documents the
  artifact; it does not commit one.
* **`L2` (P3)** — **carried unaddressed, deliberately.** It is tool-derived:
  the computed `size_composition` rollup runs over feature children rather than
  the manifest, so it counts the five archived absorbed tasks. `custom_fields.
  items` remains correct at nine live tasks plus `169-F`. No plan change is
  warranted and none was made this cycle.

Phase order, task topology, sizing, complexity and the edge set are unchanged:
the same nine live tasks, the same 12 live `item_deps` edges expressing
PREPARE → RED → ACTIVATE → VERIFY → DOCS, acyclic with a single entry point,
and `177-S` still a DAG root with no successor depending on it.

The plan was rewritten as a single coherent current-state document. It carries
no correction log and no review addendum: the remediation narrative lives here,
in the mutable manifest, which is the surface designed to hold it.

**The findings are not closed by this remediation.** `L1` is recorded as
*addressed, pending review*; `L2` is carried. Closing either requires an
independent **attempt 04** against revision 4. The plan remains **not
harvest-ready and not Ship-ready**.

## What attempt 04 records

Independent fourth review, **operator-declared terminal**, opened against plan
revision 4 at content HEAD `42f2f8ec` on branch
`chore/stage-176-s-workflow-defects`; gate result **FAIL**, decision
**BLOCKED**, zero P0, **one P1**, zero P2 and three P3 open.

Persona coverage was complete across all seven personas, with Agent-Native
Parity and Security Lens both triggered and run. Dispatch was
`single-agent-declared-degradation` with no `anchor_review` route; engram
indexed retrieval was circuit-open and not retried; intercom and graphtor-docs
were unavailable, so visibility was local-only. Evidence came from bounded
direct exact-path reads, `git` plumbing, and read-only backlogit structured
queries against a freshly synced index.

**`L1` (P1) is verified closed, by re-derivation against the repository rather
than by closure summary.** The verdict artifact's exact path, its literal
whole-file single-line format, its atomic ownership by a single emitting task,
its absence semantics and its exit-code consumer contract now agree across the
plan, the owning task records and the shipment manifest, and — critically — the
plan no longer claims a CI consumer that does not exist. Both claims were
checked empirically: `git check-ignore -v` resolves the verdict artifact to
`.gitignore:7` (`.autoharness/gates/`), so it is untracked by construction; and
`.github/workflows/ci.yml` line 112 runs `PYTHONPATH=src python -m unittest
discover -s tests`, which is an exit-code **producer** and not a verdict-line
consumer, exactly as the revised plan now states. The PREPARE / RED / ACTIVATE /
VERIFY / DOCS phase vocabulary and the three-state status vocabulary are
internally coherent, every transition is reachable, `P-002.7` marker count in
the declared scope is **0** as asserted, `3EF5AAF2` is the live source ID with
`3EF5AAF9` surviving only as historical narrative, sizes and complexity are
assigned on all nine live tasks, and the five archived absorbed tasks carry no
live dependency edges, so `G2` stays closed.

**The new blocking finding is `M1` (P1).** Binding decision
`docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md`
§`D2` is titled *"The rollout invariant is PREPARE → VERIFY → ACTIVATE"* and
states that every contract in this portfolio rolls out in three phases, with
VERIFY producing the complete evidence set — RED, GREEN and compatibility —
**before any activation**, and with RED-then-GREEN sequenced *inside* PREPARE on
the inert surface. This plan instead declares **PREPARE → RED → ACTIVATE →
VERIFY → DOCS**, which places its sole gate emitter, `169.016-T`, *after* the
single irreversible ACTIVATE commit, `169.015-T`, that mutates all four declared
surfaces. The evidence that `D2` requires before activation is therefore
produced after it.

Three things make this P1 rather than advisory. First, the deviation is
unreconciled: the plan cites `F7`, `F10`, `D6` and `R5` and never cites `D2` at
all, so no recorded justification exists for departing from a binding authority.
Second, it is *selective*: `169.015-T`'s record cites "decision D2" by name for
the one-task-one-commit atomicity rule drawn from the same section, while
silently dropping that section's ordering rule. Third, it is materially
consequential and was not compelled — a `D2`-conformant framing was available,
because GREEN is observable against `169.011-T`'s inert near-miss fixtures
before activation. A regex scan of the portfolio corroborates the outlier
status: **8 of 8** other `2026-09-18` portfolio plans use `PREPARE/VERIFY/
ACTIVATE`; this plan is the only one that does not. `P-004` does not license the
reordering, because `D2` already sequences RED before GREEN within PREPARE.

`M2`, `M3` and `M4` are advisory P3; `M4` carries forward attempt-03's `L2`.

## What follows attempt 04

**Nothing automatic. This is halted for operator disposition.** Attempt 04 is
the operator-declared terminal attempt, so **no fourth remediation cycle is
proposed and none has been executed**. `M1` is an in-scope P1 that remains open,
and per the terminal instruction it is handed to the operator rather than
remediated.

The operator has three dispositions available for `M1`, and this manifest takes
no position among them: authorize a further bounded cycle that reorders the
rollout to `D2`'s invariant; record an explicit waiver that reconciles this
plan's ordering against `D2` on the record; or amend `D2` itself if the
portfolio invariant is judged wrong. Until one of those happens, the plan is
**BLOCKED**: not publication-eligible, **not harvest-ready and not Ship-ready**.

The block is **confined to this unit**. `177-S` is a DAG root with no successor
shipment — nothing in the portfolio depends on it — so no downstream plan is
gated by this verdict.

## Attempt roster

`reviewed_revision` + `verdict` are what an **independent reviewer** judged.
`remediation_revision` + `disposition` are what **Stage** produced in response.
They are separate columns because merging them is how a fabricated PASS enters
the record. `REMEDIATED-PENDING-REVIEW` is never a `verdict` value; it is only
ever a `disposition`.

| Attempt | Artifact | Reviewed rev | Reviewer verdict | Remediation rev | Disposition |
|---|---|---|---|---|---|
| 1 | `...-v2-plan-review-attempt-01.md` | 1 @ `db39553a` | **BLOCKED** (2 P0, 3 P1, 2 P2, 1 P3) | 2 | `REMEDIATED-PENDING-REVIEW` |
| **2** | `...-v2-plan-review-attempt-02.md` | 2 @ `5aa8643f` | **BLOCKED** (0 P0, 1 P1, 2 P2, 2 P3) | 3 | `REMEDIATED-PENDING-REVIEW` |
| **3** (terminal designation lifted) | `...-v2-plan-review-attempt-03.md` | 3 @ `4b4330b9` | **BLOCKED** (0 P0, 1 P1, 0 P2, 1 P3) | 4 | `REMEDIATED-PENDING-REVIEW` |
| **4** (terminal) | `...-v2-plan-review-attempt-04.md` | 4 @ `42f2f8ec` | **BLOCKED** (0 P0, 1 P1, 0 P2, 3 P3) | — | `HALTED-FOR-OPERATOR-DISPOSITION` |

This roster covers the **v2 plan only**. Attempts 1–8 against the superseded
`2026-09-17` plan remain in that plan's own manifest,
`docs/reviews/2026-09-17-post-claim-member-status-contract-plan-review.md`,
which is terminal and is not re-opened. Attempt numbering restarts at 1 here
because this is a different plan document, not a ninth attempt against the old
one.

## Carried-forward context

Context, never operative input.

* `docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-08.md`
  — terminal attempt against the superseded revision-7 plan. Its `B1` (phantom
  source stash `3EF5AAF9`) is verified **closed** at `db39553a` and re-verified
  **closed** at `5aa8643f`. Its `B2` (GREEN-only assertions) was verified still
  open at the time of attempt 01 and was recorded as `A2` of that attempt; the
  revision-2 remediation moved every affected assertion into a RED task and
  archived the two GREEN tasks that had been introducing them, and independent
  attempt 02 verified that in the executable record. `B2` is therefore
  **closed at attempt 02**. No item of carried-forward context remains open.

## Provenance

* Plan: `docs/plans/2026-09-18-post-claim-member-status-contract-plan.md` at revision 4
* Supersedes: `docs/plans/2026-09-17-post-claim-member-status-contract-plan.md`
  (revision 7, terminal at attempt 08)
* Feature: `169-F` — Shipment: `177-S` (queued, DAG root, no incoming edge)
* Shipment members after remediation, in phase order: `169-F`, `169.011-T`
  (PREPARE, new), `169.009-T`, `169.010-T`, `169.012-T` (new), `169.013-T`
  (new), `169.014-T` (new) — the five RED tasks — `169.015-T` (ACTIVATE, new,
  atomic), `169.016-T` (VERIFY, new), `169.007-T` (DOCS)
* Archived with absorption provenance, no longer manifest members:
  `169.001-T`, `169.002-T`, `169.003-T` (absorbed into `169.015-T` under `A1`);
  `169.005-T`, `169.008-T` (assertions absorbed into `169.012-T`/`169.013-T`/
  `169.014-T`, observation into `169.016-T`, under `A2`). The six stale
  `item_deps` edges these five carried were removed under `G2` in the
  attempt-02 remediation cycle; their prose provenance is retained.
* Source stash: `3EF5AAF2` — verified present in the stash record and cited by
  `169-F`, `177-S` and every live and archived `169.x` task record
* Governing decision: the 2026-09-18 shared-execution-architecture and
  portfolio-reslicing decision, revision 1

## Authority

Latest attempt and verdict are read from this manifest, never from the plan
body. Per-attempt reviews live one per attempt under
`docs/reviews/review-history/` and are never edited afterwards. A disagreement
between `latest_attempt`/`latest_artifact` and the roster derivation above is
`REVIEW_VERDICT_AMBIGUOUS`, not a matter of narrative.
