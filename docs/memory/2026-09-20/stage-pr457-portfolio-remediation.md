---
title: "Stage — PR #457 portfolio remediation (2026-09-20)"
date: "2026-09-20"
agent: stage
---

# Stage — PR #457 portfolio remediation (2026-09-20)

**Commits:** `84c68e4e` (remediation), `989712bf` (checkpoint). Branch
`chore/stage-176-s-workflow-defects`, from `a55bd5a6`. Not pushed — Orchestrator owns PR actions.

## What the 11 threads actually were

Four defect families on one contract surface, not eleven separate bugs:

1. **Bootstrap deadlock** (1 thread). Two axes, and the reviewer was right that
   edge reversal alone was insufficient — it only repairs axis 2.
2. **Unclaimable declared roots** (3 threads). `dag-root` is the *only* reachable
   root provenance in a multi-shipment workspace; `genesis` needs exactly one
   shipment record. A root stated in prose is not a root.
3. **Premature successor harvest** (2 threads). A `blocks` edge clears on
   predecessor *completion*; both spike emitters complete on every token they
   can emit, most non-authorizing. Ordering ≠ authorization.
4. **Stale current-state prose** (5 threads).

## Judgement calls worth remembering

* **The bootstrap is not a waiver.** P-004's precondition is mechanical and
  actor-independent. The skill file is the *procedure spec*; `py_compile` +
  `unittest discover` are the *evidence*. Executing the complete template
  procedure directly produces the **full** evidence — strictly more than a
  waiver, which produces none. This is what made a narrow one-time authority
  defensible without touching the operator-authored `pre_claim` grant mechanism.
* **Withholding = archival.** The live shipment status vocabulary is exactly
  `queued|active|shipped|abandoned`; a live `blocked` shipment is malformed data
  that fails closed at read time. Archival is the only repository-supported
  fail-closed withholding, and it preserves all evidence.
* **Scope expanded deliberately, twice.** The stale-prose defect hit 27 records,
  not the 4 flagged; fixing only the flagged ones would leave siblings
  incoherent. `176-S` carried a stale `dag-root` while declaring itself not a
  root — an ambiguous root on the same surface.
* **Scope withheld deliberately, once.** `169-S` has the identical root defect
  but belongs to the 2026-09-08 chain and is not in this PR's diff. Deferred
  under P-021 C2 as stash `DDADD3AD` rather than silently widening blast radius.
* **J5 left alone.** The transport manifest's Provenance section retains a wrong
  parenthetical *as evidence* for a closed finding, and that retention is itself
  open P3 finding J5. Stage cannot self-close it, so only the `## Current
  verdict` section was rewritten.

## Open / next

* Two plans await their **first** independent review:
  `2026-09-20-harness-architect-bootstrap-plan.md` (new) and
  `2026-09-18-ship-harness-lifecycle-foundation-plan.md` (revision 2).
* Re-harvest of `184-S`/`181-S` is conditional and unscheduled — a new staging
  session must read the findings artifact first.
* 17 P3 follow-ups untouched in `711CA657`, `5E45691A`, `8DE3047F`.
