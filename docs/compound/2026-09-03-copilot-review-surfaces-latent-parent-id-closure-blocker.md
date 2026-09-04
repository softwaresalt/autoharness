---
title: "Hosted Copilot review, cross-checked against actual gate/skill code, surfaced a latent shipment-closure blocker that six local review personas missed"
description: "PR #430 (a docs/backlog-only publication of 10 shipment manifests) passed a seven-persona local adversarial review with zero P0/P1, then Copilot's hosted review found that an archived, retired task's retained parent_id makes it a member of shipment-reconcile's safe-close protected set, which will halt 168-S's eventual closure. Verifying the claim against src/autoharness/gates/shipment_closure.py and the shipment-reconcile skill before acting distinguished a genuine future blocker from what the plan had mischaracterized as a cosmetic backlogit rollup quirk."
problem_type: "latent-defect-discovery"
category: "review-coverage-gap"
component: "shipment-reconcile safe-close protected set / backlog parent_id hygiene"
root_cause: "160.019-T was retired via a P-021 C1 de-scope capture (99818C6D) and archived, but its parent_id: 160-F field was never cleared, and it was correctly excluded from 168-S's shipment manifest per that same de-scope decision. shipment-reconcile's safe-close protected-set computation (SKILL.md steps 2-3) enumerates every sibling sharing a manifest feature's hierarchy prefix across BOTH queue/ and archive/ as protected unless a verified-shipped/-done predecessor-shipment exclusion applies; 160.019-T's archived_status is blocked, not shipped/done, so it stays protected. Because it is already archived (missing from queue/), the baseline integrity gate in step 3 will find a protected-set member outside queue/ and halt with 'HALT - cascade detected, revert required' the first time 168-S is safe-closed. The plan and review-history documents had classified this same parent_id relationship as only a cosmetic backlogit size_composition rollup discrepancy (M:12,S:8 derived vs M:11,S:8 live) - true but incomplete, since the identical parent_id fact also drives the safe-close protected-set computation, a different consumer of the same field with a much higher-severity consequence."
resolution_type: "process"
severity: "medium"
tags:
  - "shipment-closure"
  - "safe-close"
  - "protected-set"
  - "parent_id"
  - "copilot-review"
  - "p-021"
  - "review-coverage"
citations:
  - "PR #430 (chore(stage): publish SHIP-1..SHIP-10 shipment portfolio)"
  - "src/autoharness/gates/shipment_closure.py classify_shipment_close_path / _build_children_index / _enumerate_descendants"
  - ".github/skills/shipment-reconcile/SKILL.md steps 2-3 (protected set, baseline integrity gate)"
  - "Deferred entry 3CA122AC (168-S future closure blocker)"
  - "Deferred entry 99818C6D (original 160.019-T retirement, sdist channel de-scope)"
  - "Deferred entry 7AD60E4F (checkpoint schema-nesting defect, partial scope)"
  - "Deferred entry 904C47BC (checkpoint schema-nesting defect, full 22-file scope, found during post-merge closure review)"
source: docs/compound/2026-09-03-copilot-review-surfaces-latent-parent-id-closure-blocker.md
doc_type: learning
---

# Hosted review found what local review missed, because it checked the actual gate code

## The pitfall

A seven-persona local adversarial review (Constitution, Python, Correctness,
Maintainability, Learnings, Scope Boundary Auditor, Template Integrity) ran
against PR #430 before it was pushed and returned zero unresolved P0/P1. The
PR's own plan document already *knew about* the fact in question — it had an
"Open P2" note stating that `backlogit shipment get 168-S` derives a
`size_composition` rollup that includes the archived `160.019-T` because that
task's `parent_id` still points at `160-F`. Every reviewer, including the
Correctness Reviewer who explicitly recomputed the size histograms, treated
this as a fully-explained, non-blocking rollup arithmetic quirk and moved on.

Hosted Copilot review, running against the same diff after push, flagged the
same `parent_id` fact but drew a different, more consequential conclusion —
because it (or its underlying analysis) traced the fact through to a
*different consumer*: `shipment-reconcile`'s safe-close protected-set
computation, which scans both `queue/` and `archive/` for every sibling of a
manifest's covering feature and requires each to still be live in `queue/` at
closure time. An archived sibling with a retained `parent_id` is invisible to
a review that only checks the manifest's own declared items and the rollup
command's arithmetic; it is fully visible to a review — human or AI — that
asks "what else reads this field, and under what condition does it fail?"

## Why local review missed it

Both the plan author (Stage) and every local review persona reasoned about
`160.019-T`'s `parent_id` **exclusively through the lens of the artifact that
was already flagged as touching it** (`backlogit shipment get`'s rollup). No
persona's brief included "enumerate every other consumer of this field
in the codebase before accepting the first explanation as complete." A
single-hypothesis review — even a multi-persona one — inherits the blind
spot of whichever artifact/finding it starts from if nothing forces a second
pass over *other* readers of the same data.

## Durable rule

When a review (local or hosted) or a plan document offers a **complete-sounding
explanation** for a data anomaly (a stray field, an unusual relationship, a
"just a display quirk" classification), before accepting it:

1. **Grep for every other place that reads the same field/relationship** in
   the actual enforcement code (gates, skills, CLI commands) — not just the
   place the anomaly was first observed. `parent_id` here was read by both a
   read-only display command (`backlogit shipment get`, harmless) and a
   destructive-path classifier (`shipment_closure.py` / `shipment-reconcile`,
   consequential). The same fact, two consumers, two entirely different
   severities.
2. **Verify a "this is just X" classification by reading the actual gate/skill
   source**, not by trusting the plan's own prose, before republishing that
   classification as settled. In this case reading
   `src/autoharness/gates/shipment_closure.py`'s `classify_shipment_close_path`
   and `.github/skills/shipment-reconcile/SKILL.md`'s protected-set steps took
   under a minute and definitively confirmed the more severe reading.
3. **Do not fix the artifact yourself if the fix requires a planning or
   backlog-structural decision** (here: clearing `parent_id` on retirement,
   changing the shipment-reconcile exemption logic, or re-including the
   retired task in the manifest against its own deliberate exclusion). Capture
   it (P-021 C2) with the verified evidence attached, so the next agent that
   picks it up does not have to re-derive the code-reading proof from
   scratch.
4. **When a hosted reviewer's finding conflicts with your own prior local
   review's classification of the same fact, re-verify before dismissing
   either one** — the disagreement itself is a signal that at least one
   review stopped at the first plausible explanation.

## Related but distinct pattern from the same PR

The same PR's Copilot review also surfaced, across two review rounds, eight
resolved historical backlogit checkpoints whose `progress` object was hoisted
to the top level instead of nested under `context`, violating the checkpoint
payload contract (`.github/instructions/backlogit.instructions.md` rule 4).
These were captured as a single P-021 entry (`7AD60E4F`) rather than
quarantined, because the session's only standing operator authorization to
quarantine covered one specific, unrelated checkpoint defect — a reminder
that **discovering more instances of an already-authorized action does not
extend that authorization to the new instances** without a fresh, explicit
operator decision. This same PR's own post-merge closure review then
independently re-scanned every checkpoint and found the true scope was
**22** resolved checkpoints with the identical defect, not 8 — a second
reminder that **a P-021 capture's own file list should not be trusted as
exhaustive without independently re-deriving it**, and that supplementing an
incomplete capture is a NEW capture (`904C47BC`), never an edit to the
original (`7AD60E4F`), per the single-write invariant.
