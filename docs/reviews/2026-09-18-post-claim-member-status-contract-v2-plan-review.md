---
title: "Plan review verdict manifest — Canonical post-claim member-status contract (P-002.7), v2"
description: "Mutable verdict manifest for docs/plans/2026-09-18-post-claim-member-status-contract-plan.md. This file is a selection surface, not a review: it names which immutable attempt artifact is authoritative right now, and nothing else. The reviews live one per attempt under docs/reviews/review-history/ and are never edited after they are written. Latest attempt: 01. Plan revision: 2. Independent attempt 01 reviewed revision 1 at content HEAD db39553a and returned gate result FAIL and verdict BLOCKED on two P0, three P1, two P2 and one P3 deduplicated finding. Both P0s are plan-versus-manifest contradictions in shipment 177-S: the policy template and installed mirror are two tasks joined by a blocks edge, which the plan's own ACTIVATE invariant and decision D2 forbid; and the GREEN-phase assertion defect the plan exists to close, attempt-08 B2, is still encoded in 169.005-T and 169.008-T with no RED task covering mirror-divergence or version-attribution assertions. A Stage remediation cycle then produced plan revision 2 and re-derived the executable task set from it: five superseded tasks were archived with absorption provenance, one atomic ACTIVATE task and five RED-owning tasks were created, and the 177-S manifest was rebuilt in phase order. latest_remediation_revision is 2 and latest_disposition is REMEDIATED-PENDING-REVIEW. The top-level verdict is null: a remediation revision supersedes the content attempt 01 judged, and no independent reviewer has judged revision 2. The findings remain counted open because only an independent attempt 02 can close them. The plan is not harvest-ready and not Ship-ready. No PASS exists anywhere in this record and none is asserted."
doc_type: review-manifest
source: docs/reviews/2026-09-18-post-claim-member-status-contract-v2-plan-review.md
date: 2026-09-18
manifest_shape: attempt-roster
plan_id: post-claim-member-status-contract-v2
plan_path: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
plan_revision: 2
feature_id: 169-F
shipment_id: 177-S
predecessor_manifest: docs/reviews/2026-09-17-post-claim-member-status-contract-plan-review.md
latest_attempt: 1
review_terminal: false
awaiting_attempt: 2
reviewed_content_head: db39553a
gate_result: FAIL
verdict: null
p0_open: 2
p1_open: 3
p2_open: 2
p3_open: 1
remediation_authorization: operator-authorized-single-cycle
latest_remediation_revision: 2
latest_disposition: REMEDIATED-PENDING-REVIEW
latest_artifact: docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-01.md
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
carried_forward_context:
  - artifact: docs/reviews/review-history/2026-09-17-post-claim-member-status-contract-plan-review-attempt-08.md
    reason: "Terminal attempt against the superseded revision-7 plan. Its B1 (phantom source stash 3EF5AAF9) is verified closed at db39553a; its B2 (GREEN-only assertions) is verified still open in the 177-S manifest and is recorded as A2 of attempt 01."
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
| `plan_revision` | 2 |
| `latest_attempt` | **01** |
| `latest_artifact` | `docs/reviews/review-history/2026-09-18-post-claim-member-status-contract-v2-plan-review-attempt-01.md` |
| `reviewed_content_head` | `db39553a` |
| `gate_result` (attempt 01, immutable) | **FAIL** |
| `verdict` | **null** (derived — see below) |
| `latest_remediation_revision` | **2** |
| `latest_disposition` | **REMEDIATED-PENDING-REVIEW** |
| `awaiting_attempt` | **02** |
| `p0_open` | **2** |
| `p1_open` | **3** |
| `p2_open` | **2** |
| `p3_open` | **1** |

**The top-level `verdict` is derived, not authored.** Take the highest-numbered
roster entry — attempt 01. Its `remediation_revision` is now `2`, so a
Stage-produced revision **supersedes** the content the reviewer judged. The
reviewer's `BLOCKED` was returned against revision 1 and cannot be carried
forward as a judgement of revision 2, and no reviewer has judged revision 2.
The derived `verdict` is therefore **null**, and `latest_disposition` carries
what Stage actually produced: `REMEDIATED-PENDING-REVIEW`.

`REMEDIATED-PENDING-REVIEW` is a `disposition`, never a `verdict`, for the
reason this plan's own predecessor manifest states. Writing it into the
`verdict` key would assert that a review concluded, which is precisely the
fabrication this two-column shape exists to prevent.

**The finding counts remain open.** Two P0, three P1, two P2 and one P3 are
still counted open even though each was remediated. Stage remediating a
finding is not the same event as a reviewer confirming it closed, and only the
latter retires a finding. The counts drop when attempt 02 says they drop.

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

**The findings are not closed.** Closing them requires an independent attempt
02 against revision 2. This manifest asserts remediation and nothing more.

## Attempt roster

`reviewed_revision` + `verdict` are what an **independent reviewer** judged.
`remediation_revision` + `disposition` are what **Stage** produced in response.
They are separate columns because merging them is how a fabricated PASS enters
the record. `REMEDIATED-PENDING-REVIEW` is never a `verdict` value; it is only
ever a `disposition`.

| Attempt | Artifact | Reviewed rev | Reviewer verdict | Remediation rev | Disposition |
|---|---|---|---|---|---|
| **1** | `...-v2-plan-review-attempt-01.md` | 1 @ `db39553a` | **BLOCKED** (2 P0, 3 P1, 2 P2, 1 P3) | 2 | `REMEDIATED-PENDING-REVIEW` |

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
  source stash `3EF5AAF9`) is verified **closed** at `db39553a`; its `B2`
  (GREEN-only assertions) was verified **still open** in the `177-S` manifest
  at the time of attempt 01 and was recorded as `A2` of that attempt. The
  revision-2 remediation moved every affected assertion into a RED task and
  archived the two GREEN tasks that had been introducing them; whether `B2` is
  thereby closed is for independent attempt 02 to judge, not for this manifest
  to assert.

## Provenance

* Plan: `docs/plans/2026-09-18-post-claim-member-status-contract-plan.md` at revision 2
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
  `169.014-T`, observation into `169.016-T`, under `A2`)
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
