---
title: "Re-grounding 171-S/163-F after 169-S and 192-F, and triage of the post-169-S shipment-reconcile follow-ups"
description: "Stage deliberation (P-021 C6) for deferred-scope-expansion entries A9BABC8B, D6502107, E1E31E6A, D16452D7, 814BB949, 675EA40E, B5AB7D95, F0F8916F and follow-up 4CB6A1E0"
date: 2026-10-08
status: decided
agent: stage
stash_entries: [A9BABC8B, D6502107, E1E31E6A, D16452D7, 814BB949, 675EA40E, B5AB7D95, F0F8916F, 4CB6A1E0]
related_features: [163-F, 161-F, 192-F]
related_shipments: [171-S, 169-S]
---

## Context

171-S (feature 163-F, stash origin 856B6770) was planned on 2026-09-08/10
(`docs/plans/2026-09-08-shipment-reconcile-step-0c-live-pre-mutation-evidence-plan.md`,
revision R1, review PASS after 5 cycles). Since then two shipments changed the
surface it targets:

* **192-F** (`autoharness shipment cascade-close`): every close now starts with
  `--classify-only`, which writes a tool-authored evidence record at
  `docs/closure/evidence/{S}-{F}-close-evidence.json`. Its `pre_close` block carries
  the Step 0(b) snapshot, classifier verdict, engine-semantics decision, close-path
  selection and the linked-deliberation disposition snapshot, stamped
  `pre_close.captured_at`. The mutating run writes `pre_close`, revalidates, writes
  the owner-bound `invocation` record (`started_at`), then spawns
  `backlogit shipment ship` (`src/autoharness/shipment_close/command.py` steps 3-8).
  `autoharness gate closure-evidence` refuses a closure artifact without a valid
  record for its declared `close_path`.
* **169-S / 161-F** (PR #506): Pre-Mode member-class status contract, plus the
  Step 0(c) "Pre-Mode step 2b agreement check" paragraph immediately before
  `<!-- cascade-close-routing:BEGIN step-0c -->` (both copies, L757-L780 of 1992).

Learnings consulted: `docs/compound/2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md`,
`2026-09-27-175-s-closure-evidence-gate-hardening-lessons.md`,
`2026-08-02-backlogit-done-move-vs-explicit-archive.md`,
`096-S-template-vs-global-skill-placeholders.md` (confidence: medium).

## Duplicate scan and late-identifier reconciliation (P-021 C5/C6)

* **Clean duplicate scan** over the 233-entry stash for all nine entries. Adjacent but
  distinct: `A5FA81C4` (effective `--timeout` not recorded — different field from
  4CB6A1E0's reference costs), `218DF163` (path literals, not status literals —
  different from 814BB949), `16128302` (161-F decision-record bookkeeping). No merge.
* **Late identifiers**: every entry except 4CB6A1E0 records `PR N/A` and
  `review thread N/A` (pre-PR local adversarial review). The Ship-owned 169-S
  closure record (`docs/closure/169-S-161-F-post-merge-closure.md`) identifies the
  shipping PR as **#506** (merge `489e7c3b`). Recovered: originating shipment PR #506
  for all eight. Review thread: **no late identifier found** — the findings were
  raised before the PR existed; `N/A` stands as a truthful terminal record.

## Decisions

### D-1 — RQ-1 is discharged by the 192-F `pre_close` record; do not author a second record (A9BABC8B)

163-F R1 designed an agent-authored record under `.backlogit/reconcile/` plus an
engine-log anchor event (`PRECASCADE_EVIDENCE_ANCHOR`), an L1/L2 durability split and
an L2 publication executor (U6). 192-F now supplies a durable, timestamped,
**tool-written** pre-mutation record on every close, which is exactly RQ-1. A second
record would create two sources of truth for the same Step 0(c) facts. **Decided:**
the 192-F `pre_close` record IS the Step 0(c) pre-mutation evidence record. The R1
anchor event, the `.backlogit/reconcile/` record, the four U2(b) tokens, and U6 are
superseded.

### D-2 — RQ-2 residual is a temporal-ordering gap in the closure-evidence validator

`validate_evidence_record` (`src/autoharness/gates/cascade_evidence.py`) checks that
`pre_close.captured_at`, `invocation.started_at` and `invocation.finished_at` are
non-empty strings, but never compares them. A post-hoc `--classify-only` run (the
159-S shape: the collection reconstructed after mutation) is therefore "valid" when
its timestamps postdate the mutation. **Decided:** RQ-2 is completed by fail-closed
ordering checks in the validator — no new artifact:

* **cascade**: `pre_close.captured_at` < `invocation.started_at` <= `invocation.finished_at`,
  all RFC 3339 UTC; unparseable = fail.
* **both paths (engine-anchored, R1-8 threat model kept)**: no engine-written
  close-mutation event for the shipment or any manifest member (backlogit item JSONL
  log under the backlog root's `logs/`) may carry a timestamp in the window
  `[merge commit committer time, pre_close.captured_at)`. Members archived before the
  merge commit remain legitimately pre-archived. A missing or unreadable log for a
  member whose `pre_close` snapshot shows it **not** archived fails closed; a missing
  log for an already-archived member is tolerated (no event to compare).

The claim stays bounded as in R1-8: tamper-evident and out-of-protocol, not
tamper-proof. This is a Python change in the validator (unlike the R1 plan's
"no Python source change" posture), which is why the plan requires hardening.

### D-3 — D6502107 and E1E31E6A fold into 171-S (same Step 0(c) contract surface)

Both edit the agreement-check paragraph (L757-L779) and its Ship-side recording
duty. **Decided:** add safe-close input `pre_report_path` (optional; required when a
pre-close Pre-Mode run preceded the safe-close in the same lock hold); both Ship
copies pass the path returned by Pre-Mode step 6; restate not-applicable as
"`pre_report_path` absent"; Ship names the agreement-check outcome in its post-merge
closure-artifact writing step. Replace "(Ship Step 5)" with the phase name ("Ship's
post-merge closure") in both skill copies, and move the generic Ship template's
recording duty from step 1.a (`mode: pre`) to 1.b (`mode: safe-close`). Gate
enforcement of the agreement-check outcome through closure-evidence stays out of
scope (D6502107 (2) says so).

A-14 (promote the agreement check to its own labelled sub-step): **adopted** as
Step 0(d) since the paragraph now has an input, an outcome token and a halt token.

### D-4 — 163.006-T (diagram) and 163.008-T (L2 publication) are obsolete

`docs/diagrams/` is not in the repository (operator WIP in `git stash@{1}`, per
675EA40E). Creating diagram 05 at the canonical path would publish over unpublished
operator content. U6 existed only to publish the R1 anchor; D-1 removes the anchor.

### D-5 — Part B scope (new shipment, chained after 171-S)

| Entry | Disposition | Reason |
|---|---|---|
| D16452D7 | **include** | Safe-Close step 4 (L887-888) keys `pre-archived` on location; aligns it with the shipped Pre-Mode declared-status rule. Real bug (2026-08-02 learning). |
| 814BB949 | **include** | Template portability; template L579, L643, L1040, L1113 carry literal `status: done`. 147-F tests pin wording. |
| B5AB7D95 | **include** | Two cross-references; cheap disambiguation of adjacent contracts. |
| 4CB6A1E0 | **include** | Reference values understate wall time by ~1.7x (169-S: 1153 s vs B=672 s). Refresh F/P and point calibration at `invocation.started_at/finished_at` of prior evidence records (already recorded — the entry's "record child duration" ask is satisfied by 192-F). |
| F0F8916F | **leave in stash** | Design decision, not mechanical: a second discriminator beside `expected_status` creates two sources of truth that can disagree and needs its own disagreement rule. Low value while `expected_status: done` is the documented MUST. Revisit if a third Pre-Mode invocation kind appears. |
| 675EA40E | **leave in stash** | Blocked: target file is not under version control. Actionable only after the operator publishes the diagram set. |

### D-6 — Sequencing

171-S `blocks` on 169-S (kept) and 212-S (new, operator order). The Part B shipment
`blocks` on 171-S. Both touch `templates/skills/shipment-reconcile/SKILL.md.tmpl`
+ mirror + `.autoharness/harness-manifest.yaml`; 171-S also touches the two Ship agent
files that 208-S/210-S/212-S edit. Each must rebase on merged predecessors.
