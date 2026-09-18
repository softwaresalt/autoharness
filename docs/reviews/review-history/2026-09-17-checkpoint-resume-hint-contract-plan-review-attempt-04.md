---
title: "Plan review attempt 04 — Checkpoint resume-hint / payload-shape contract (plan revision 4)"
description: "Immutable per-attempt plan-review artifact. Records local review cycle 2 against docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md at revision 3 — verdict BLOCKED, because the revision-3 design had not been propagated into the executable backlog records — together with the Stage remediation-cycle-2 response that raises the plan to revision 4 and propagates it. Replaces a volatile record-count pin with invariant-based corpus assertions, machine-encodes the policy-then-producers-then-validator ordering so the validator cannot be enabled before both producers are updated, corrects the work provenance from 24D4E0F8 to 71200CBB, and retitles away from migration language that no shipped mechanism supports. Disposition: REMEDIATED-PENDING-REVIEW. Stage does not review its own remediation."
doc_type: review
source: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-04.md
date: 2026-09-19
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 4
attempt_range: "04"
attempt_conformance: conforming
verdict_manifest: docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-03.md
plan_path: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
plan_revision: 4
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 71200CBB
feature_id: 172-F
shipment_id: 180-S
review_cycle: 4
review_cycles_remaining: 0
dispatch_mode: declared-degradation
decision: REMEDIATED-PENDING-REVIEW
verdict_at_entry: BLOCKED
verdict_at_entry_plan_revision: 3
p0_open: 0
p1_open: 0
tags:
  - "plan-review"
  - "checkpoint-contract"
  - "provenance"
  - "compatibility-policy"
  - "remediation-cycle-2"
---

# Plan review attempt 04 — Checkpoint resume-hint / payload-shape contract

## Scope of this attempt

Local review cycle 2 opened against **plan revision 3** and returned
**BLOCKED** with one root cause: revision 3's design was never propagated into
the executable backlog records, so the plan and the records described different
systems. No finding disputed the revision-3 design itself.

Operative input set: plan revision 3, its verdict manifest, and the live
`172-F` / `180-S` backlog records. Attempts 01–02 and attempt 03 are
preserved in `review-history/` and are excluded from the operative set as
superseded history.

dispatch_mode: `declared-degradation`

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent
persona pass`. No reviewer subagent was dispatched for this attempt; the
cycle-2 findings were operator-supplied and are recorded here as received.

## Findings raised at revision 3, and their closure at revision 4

| ID | Finding (local review cycle 2) | Closure evidence |
|---|---|---|
| B8.1 | `172.007-T` pinned the historical corpus at **51 records**, a value that had already moved to 52 and is now 53 — three readings, three values | Count pin removed and replaced with four **invariants** asserted over whatever the corpus contains at run time. `172.007-T` retitled to "invariant-based live-corpus audit" |
| B8.2 | The ordering was contradictory prose: the validator's enablement was described as gated on producers it did not depend on | Split into real dependency semantics with two new tasks. `172.008-T` (**T5a RED**) authors the validator contract tests against a missing boundary; `172.005-T` retitled `(IMPLEMENTATION)` and delivers the boundary **without wiring it in**; `172.006-T` retitled `(GREEN)`; new `172.009-T` (**T5c ENABLE**) is the only task that turns enforcement on and blocks on **both producers** (`172.003-T`, `172.004-T`) **and** the implementation and its green proof. The validator therefore cannot be enabled before both producers are updated |
| B8.3 | Task bodies cited superseded revisions | All nine task bodies rewritten to cite plan revision 4 and decision revision 3, with reconciled source refs |
| A2.1 | The `180-S` body attributed this work to stash `24D4E0F8`; the canonical selected ID is `71200CBB` | Corrected in the `180-S` description and in this manifest's `source_stash_id`. Attempt-03 is immutable and carries the wrong value; it is corrected by the errata note below rather than by editing the artifact |
| A2.2 | `172-F`, `172.001-T` and `172.007-T` used "historical migration" language, but no migration mechanism ships in this unit | Retitled to **compatibility / policy** language; the `migration` label replaced with `compatibility-policy`; the plan title, description and Work Breakdown de-migrated |

## Errata against immutable attempt 03

`docs/reviews/review-history/2026-09-17-checkpoint-resume-hint-contract-plan-review-attempt-03.md`
records `source_stash_id: 24D4E0F8`. That value is **wrong**. The canonical
selected stash ID for this work is **`71200CBB`**.

Attempt artifacts are immutable and are never edited after they are written, so
attempt 03 is left byte-unchanged and this errata note is the correction of
record. Any consumer resolving provenance for this plan must read `71200CBB`
from this artifact or from the verdict manifest, and must treat the
`24D4E0F8` occurrence in attempt 03 as a known, corrected transcription error.

## Dependency graph as propagated

```text
`172.002-T → 172.001-T`; `172.003-T → 172.001-T`; `172.004-T → 172.001-T`;
`172.008-T → 172.001-T, 172.002-T`; `172.005-T → 172.008-T`; `172.006-T → 172.005-T`;
`172.009-T → 172.003-T, 172.004-T, 172.005-T, 172.006-T`; `172.007-T → 172.009-T`.
Ten members in `180-S`.
```

## Portfolio-wide findings closed in this attempt

These findings were raised against the portfolio as a whole and are recorded
identically in all six attempt-04 artifacts. Each is closed at the record
level, not merely in prose.

| ID | Finding (local review cycle 2) | Closure evidence |
|---|---|---|
| A1 | The portfolio decision still governed a superseded design: serial shipment chain, three-rung branch resolver, unreduced 171-F scope, and a live post-claim detector | Decision revised to **revision 3** with four binding amendments — D1 (two-rung ladder; `workspace_convention` withdrawn), D3 (detector formally withdrawn, spike question closed), D5 (four surfaces moved out of the release unit), D8 (fan-out shipment DAG replacing the serial encoding, with the three-reason rejection recorded). Every plan's `source_decision` reference now carries `decision_revision: 3` |
| A2 | Checkpoint work provenance cited the wrong stash ID `24D4E0F8` instead of the canonical selected ID `71200CBB`; several surfaces used "historical migration" language for work that ships no migration mechanism | `180-S` body corrected; the checkpoint verdict manifest's `source_stash_id` corrected; attempt-03 is immutable and is corrected by the errata note in the attempt-04 artifact rather than by edit. `172-F`, `172.001-T` and `172.007-T` retitled to compatibility/policy language; the `migration` label replaced with `compatibility-policy` |
| A3 | The five remediation-created deferred stash entries were not P-021 C2 conformant | `E770139B`, `95575B96`, `4003E0B8`, `0F26AA6C`, `7C7A4C96` rewritten to full C2 payloads: literal `DEFERRED SCOPE EXPANSION` first field, one-sentence expansion statement, C1 rationale, four independently explicit source refs each carrying an ID or `N/A`, `requires deliberation`, kind, and provisional priority |
| A3b | The previous Stage cycle executed the test suite, which Stage's role boundary forbids | Recorded as a **P-005 / P-010 policy violation** in the stash record. The earlier test evidence is attributed truthfully to that out-of-boundary run and is **not** re-run in this cycle; no test, linter, or build was executed at any point in remediation cycle 2 |
| B10 | `177-S` and `179-S` carried parent features whose live blocked children were excluded from the shipment manifest, forcing SAFE_CLOSE with no agent-executable transition | Every descoped or blocked child was re-homed **out of** the covering feature through the supported backlog lifecycle (`adopt`), never by deletion or hand-editing. Two new deferred features created: **`174-F`** (post-claim detector surfaces) and **`175-F`** (single-governing-plan follow-on surfaces). Provenance and P-021 linkage preserved on every moved record via auto-retained `origin_feature` plus explicit body provenance. All six manifests now exactly equal their covering feature's live descendant set |
| C11 | `{{STATUS_QUEUED}}` / `{{STATUS_ACTIVE}}` placeholder leaks in a spike and a memory document | Both excerpts fenced as verbatim template source with an explicit note that the tokens are unrendered by design |
| C12 | Backlog record bodies do not carry the `# {title}` H1 and `## Description` headings declared by the installed `.backlogit/templates/*.md` | Empirically confirmed to be a **writer defect**, not an authoring omission: a live `backlogit_update_item` call emits neither heading, and 189 of 191 queue records lack an H1. Hand-writing tool-owned bodies is out of the supported operation set, so the residual risk is captured as a compliant P-021 deferred entry with full C2 fields rather than worked around. Substantive sections already added are preserved |
| C13 | Session required a compliant terminal checkpoint | Final Stage checkpoint created through the official create operation with `schema_version: 1`, a non-empty `resume_hint`, and all progress/domain data nested under `context`; then resolved. No active checkpoint remains. `checkpoint-20260916-064310.json` is preserved byte-unchanged |

## What this attempt is, and is not

This artifact records **local review cycle 2** and the Stage remediation
response to it. The cycle-2 verdict against plan revision 3 was **BLOCKED**:
the revision-3 design was sound, but it had never been propagated into the
executable backlog records, so the records and the plans disagreed.

The remediation raises the plan to **revision 4** and propagates the design
into the records. It does **not** assert a reviewer PASS at revision 4. Stage
does not review its own remediation; the manifest verdict is therefore
`REMEDIATED-PENDING-REVIEW`, and the next reviewer pass is attempt 05.

No test suite, linter, or build was executed during this remediation. Stage's
role boundary forbids it, and the prior cycle's boundary violation is recorded
above rather than repeated.

## Disposition

* Plan raised to **revision 4**; `source_decision` now resolves at
  **decision revision 3**.
* All cycle-2 P1 findings scoped to this plan are closed at the record level.
* Verdict carried forward to the manifest: **REMEDIATED-PENDING-REVIEW**. The
  next reviewer pass is attempt 05.
