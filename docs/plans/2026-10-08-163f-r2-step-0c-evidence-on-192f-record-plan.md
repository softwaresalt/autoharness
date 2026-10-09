---
title: "163-F R2: Step 0(c) pre-mutation evidence on the 192-F record — temporal-ordering gate, agreement-check input channel"
description: "Superseding re-plan of 171-S / 163-F after 169-S (161-F) and 192-F shipped. RQ-1 discharged by the 192-F pre_close record; RQ-2 completed by fail-closed temporal-ordering checks in the closure-evidence validator; RQ-3 by a 159-S-shape replay test; folds D6502107 and E1E31E6A into the Step 0(c)/(d) surface"
date: 2026-10-08
status: reviewed
supersedes_units_of: "docs/plans/2026-09-08-shipment-reconcile-step-0c-live-pre-mutation-evidence-plan.md (R1 units U1a-U6)"
deliberation: "docs/decisions/2026-10-08-171s-regrounding-and-reconcile-hygiene-deliberation.md (D-1..D-4, D-6)"
feature: 163-F
shipment: 171-S
stash_entries: [856B6770, A9BABC8B, D6502107, E1E31E6A]
requires_plan_hardening: "yes"
plan_hardening_status: "hardened"
plan_review_verdict: "PASS"
plan_review_cycles: 1
tags: [plan, shipment-reconcile, pre-mutation-gate, closure-evidence, p-015, dogfood-parity]
---

## Problem Frame (re-grounded 2026-10-08)

The R1 plan's requirements stand unchanged (RQ-1 durable timestamped pre-mutation
record; RQ-2 fail closed when absent or not provably pre-mutation; RQ-3 a 159-S-shape
replay test that fails when the collection is reconstructible after mutation). Its
**mechanism** is stale:

* 192-F's `autoharness shipment cascade-close --classify-only` now performs the
  Step 0(c) collection itself and writes `pre_close` (with `captured_at`) to
  `docs/closure/evidence/{S}-{F}-close-evidence.json` before any mutation. The
  mutating run writes `pre_close`, revalidates, writes `invocation.started_at`, then
  spawns `backlogit shipment ship` (`src/autoharness/shipment_close/command.py`
  module docstring steps 3-8). RQ-1 is met (deliberation D-1). Authoring the R1
  agent-written `.backlogit/reconcile/` record would duplicate it.
* `validate_evidence_record` (`src/autoharness/gates/cascade_evidence.py` L1450) and
  `_check_pre_close` (L1125, `captured_at` checked at L1138 as a non-empty string
  only) and the invocation checks (L1190) never **compare** timestamps. A post-hoc
  `--classify-only` run after the members were already archived — the 159-S shape —
  passes `autoharness gate closure-evidence` today. That is the RQ-2 residual.
* 169-S added the "Pre-Mode step 2b agreement check" paragraph to Step 0(c) with no
  declared input and an unenforced recording duty (D6502107), plus two generic-template
  wording defects (E1E31E6A).

### Re-grounded anchors (both copies identical, 1992 lines; verified 2026-10-08)

| Surface | `.github/skills/shipment-reconcile/SKILL.md` = `templates/skills/shipment-reconcile/SKILL.md.tmpl` |
|---|---|
| Inputs table | `## Inputs` L58 |
| Safe-Close Step 0 (a)/(b)/(c) | L546 / L549 / L555 / L590 |
| Agreement-check paragraph (`**Pre-Mode step 2b agreement check.**`) | L757-L779; "(Ship Step 5)" at L776 |
| `<!-- cascade-close-routing:BEGIN step-0c -->` | L780 (END at L832) |
| Cascade Close Sub-Procedure | L964 |
| Linked-Deliberation Disposition (INV-12) | L1334 |
| Scenario Matrix / Quality Criteria | L1890 / L1915 |
| Ship agent recording duty | `templates/agents/_ship.agent.md.tmpl` L820 (step 1.a, wrong step); `.github/agents/_ship.agent.md` L698 |
| Gate help text | `src/autoharness/cli.py` L276-L305 (`closure-evidence` paragraph); check wiring `_check_close_path_requirement` (L1830) |
| Manifest | `.autoharness/harness-manifest.yaml`: the one entry whose `path:` is `.github/skills/shipment-reconcile/SKILL.md` (locate by path; R1-14 rule kept) plus the entry for `.github/agents/_ship.agent.md` |

Line numbers are a starting point; implementers locate by the quoted text.

## Requirements Trace

| ID | Requirement | Discharged by |
|---|---|---|
| RQ-1 | durable, timestamped pre-mutation record before the cascade | 192-F `pre_close` record (no new artifact); U3 states this once in Step 0(c) |
| RQ-2 | fail closed when the record is absent or not provably pre-mutation | absent: already enforced by closure-evidence (`failed_check close_evidence`); not provably pre-mutation: U2a + U2b |
| RQ-3 | 159-S-shape replay test fails when the collection is reconstructible after mutation | U1 |
| D6502107 | declared input channel + recorded outcome for the agreement check | U3 (skill) + U5 (Ship copies) |
| E1E31E6A | "(Ship Step 5)" wording; generic Ship template recording duty in 1.a instead of 1.b | U3 + U5 |
| A9BABC8B / A-14 | re-ground; no duplicate record; agreement check as labelled sub-step | this plan; U3 (Step 0(d)) |

## Ordering contract (the RQ-2 rule, stated once)

All timestamps are parsed as RFC 3339 and compared as UTC instants (engine logs use
local offsets such as `-07:00`; the evidence record uses `Z`). An unparseable
timestamp fails.

1. **In-record ordering (cascade records).** `pre_close.captured_at` <
   `invocation.started_at` <= `invocation.finished_at`. Violation:
   `record.pre_close.captured_at: must precede invocation.started_at`
   (resp. `record.invocation.finished_at: must not precede started_at`).
2. **Engine-anchored window (both close paths).** Let `M` = committer time of
   `merge_commit_sha` (`git log -1 --format=%cI <sha>` in the workspace) and
   `C` = `pre_close.captured_at`. For the shipment and every manifest member in
   `pre_close`, read its engine log `<backlog root>/logs/<id>.jsonl`. A **close-mutation
   event** is `event_type: archived`, or a `status_changed` / `artifact_mutation` whose
   new status is `archived` or `shipped`. Any close-mutation event with `M <= t < C`
   fails closed (`failed_check close_evidence`, message names the id, event and
   timestamps). `commit_tracked`, `comment` and `status: done` events are not
   close-mutation events.
3. **Fail-closed inputs.** `M` unresolvable (unknown sha, git unavailable) fails.
   A missing or unreadable log fails for a member whose `pre_close` snapshot records
   it **not** archived; it is tolerated (warning) for a member recorded archived at
   capture, since such a member has no in-window event to compare. A malformed log
   line fails.

**Passing state:** the 169-S evidence record against the 169-S logs (C =
05:02:03Z, started 05:02:17Z, finished 05:21:30Z; 161.003-T archived 22:14:25-07:00 =
05:14:25Z > C; M = 04:48:32Z). **Failing state:** the same record with `captured_at`
moved to 05:30:00Z (post-hoc `--classify-only`): rule 1 fails, and rule 2 fails on
161.003-T's `archived` event at 05:14:25Z in `[M, C)`.

Threat model (R1-8 kept): tamper-evident and out-of-protocol, not tamper-proof. A
forger must hand-edit engine-owned JSONL or the tool-written record — itself a P-005
violation. Clock skew between GitHub (M) and the local engine clock only widens or
narrows the window's lower edge by seconds; no legitimate close mutates between merge
and `--classify-only`.

## Implementation Units

### U1 — RED: 159-S-shape replay tests (task 163.001-T, amended)

New `tests/test_cascade_evidence_temporal_ordering.py` (stdlib `unittest`, temp-dir
fixtures; reuse existing evidence fixture builders where present, e.g. in
`tests/test_cli_gate_closure_evidence.py`). Cases: rule-1 positive and both
negatives; unparseable timestamp; rule-2 negative (member `archived` inside `[M, C)`),
positive late-but-legit (member archived before `M`), non-mutation event inside the
window passes, mixed offsets compared as instants; rule-3 unresolvable `M`, missing log
for a non-archived member fails, missing log for an archived member warns. Git
committer time is injected through a seam (function parameter) so tests do not need a
real repo. Must fail before U2a/U2b. **Size M, complexity medium.**

### U2a — GREEN: in-record ordering (task 163.002-T, amended)

Add rule 1 to `cascade_evidence.py` cascade checks (pure function; no I/O).
**Size S, complexity low.**

### U2b — GREEN: engine-anchored window in closure-evidence (task 163.004-T, amended)

Implement rules 2-3 in the closure-evidence check path (`cli.py`
`_check_close_path_requirement` or a helper in `cascade_evidence.py`), with path containment before any log
read (same helpers 192-F uses), and update the `closure-evidence` help paragraph
(`cli.py` L276-L305) to name the ordering checks. **Size M, complexity medium.**
No change to `shipment_close/command.py` (it already writes in the required order).

### U3 — Skill text: Step 0(c) record statement, Step 0(d) agreement check, matrix (task 163.005-T, amended)

Both copies, byte-identical except template placeholders:

1. In Step 0(c), one sentence: the `--classify-only` `pre_close` record is the Step 0(c)
   pre-mutation evidence record, and closure-evidence rejects it when it is not
   provably pre-mutation (cite the ordering contract by reference to the gate). Do not
   restate the "before the cascade" requirement a fourth time (R1 H-1).
2. Promote the agreement-check paragraph to **Step 0(d)** (label only; content kept),
   add `pre_report_path` to `## Inputs` (`safe-close` only, optional; REQUIRED when a
   pre-close Pre-Mode run returned a report within this lock hold). The comparison
   reads exactly that path. Not-applicable is restated as "`pre_report_path` absent".
   `pre_report_path` present but unreadable = difference → `RECONCILE_FAIL_PREMODE_CLASSIFIER_DRIFT`.
3. Replace "(Ship Step 5)" with "(Ship's post-merge closure)" in both copies.
4. Scenario Matrix + Quality Criteria: add rows for the ordering rejection and for
   `pre_report_path` absent / present-agreeing / present-differing.

**Size M, complexity medium.**

### U4 — Section-scoped contract and parity guard (task 163.003-T, amended)

Extend or add a test asserting, within the Safe-Close section of both copies: Step 0(d)
label, `pre_report_path` in Inputs, the "parameter absent" not-applicable wording, no
"(Ship Step 5)", and template/mirror parity for the edited region. Written RED before
U3 lands. **Size S, complexity low.**

### U5 — Ship agent copies: pass `pre_report_path`, record the outcome (NEW task)

`templates/agents/_ship.agent.md.tmpl` and `.github/agents/_ship.agent.md`: the
safe-close invocation (step 1.b) passes the path Pre-Mode step 6 returned; the
agreement-check outcome (`agreed` / `not-applicable`) is named in the post-merge
closure-artifact writing step; the generic template's duty moves from 1.a to 1.b.
No gate enforcement of the outcome (D6502107 (2)). **Size S, complexity low.**

### U6 — Checksums and GREEN (task 163.007-T, amended)

Recompute the manifest checksums for the edited dogfood files located by `path:`
(skill and Ship agent); no other entry touched. Run
`PYTHONPATH=src python -m unittest discover -s tests`; confirm templates/ ↔ .github/
parity. **Size XS, complexity low.**

### Obsolete R1 units

* 163.006-T (U4 diagram) — obsolete (deliberation D-4): `docs/diagrams/` is not in the
  repository; diagram currency stays with 675EA40E.
* 163.008-T (U6 L2 publication) — obsolete (D-1): no anchor event to publish; engine
  logs and the evidence record are already committed by Ship's closure commit.

## Dependency Graph

U1 → U2a → U2b; U4 → U3 → U5; {U2b, U5} → U6. U1 and U4 can start independently.

## Sequencing and shared files

171-S blocks on 169-S (kept) and 212-S (new). U5 edits the Ship agent files that
208-S/210-S/212-S also edit; U3/U6 touch the skill copies and the harness manifest.
Ship rebases 171-S onto merged predecessors before U5/U6 and recomputes checksums
after the rebase.

## Non-Goals

No change to `shipment_close/command.py`, the Pre-Mode member-class contract, Safe-Close
steps 1-10 (D16452D7 is Part B), the diagram set, or gate enforcement of the
agreement-check outcome. No new evidence artifact.

## Plan Hardening Signals

Python validator change on a fail-closed closure gate (blast radius: every future
closure); Ship agent contract edit; dogfood parity. **Requires plan hardening: yes.**

## Plan Hardening (2026-10-08)

* **H1 — unsatisfiable-gate check (15A02E21 lesson).** Passing state named above uses
  real 169-S data; rule 3 tolerates missing logs for archived-at-capture members so
  legitimately pre-archived history without logs cannot block a close. Legacy closures
  are not re-validated retroactively: the gate runs on the closure being written.
* **H2 — false positives.** Only `archived`/`shipped` transitions count; `done`
  transitions (normal pre-merge task completion) and `commit_tracked` (the merge
  commit is tracked after `C`, as in 169-S) are excluded.
* **H3 — protected invariants.** `command.py` ordering, no-clobber `--classify-only`,
  INV-12 disposition inputs from the record, R1-14 path-keyed checksum rule.
* **H4 — timezone.** Instant comparison is mandatory; a string comparison would pass
  the 169-S record by accident and fail others. U1 includes a mixed-offset case.
* **H5 — risky actions.** None destructive; all edits are text/validator. Rebase risk
  on the Ship agent files is handled by the sequencing edge.
* **H6 — unresolved decisions.** None; gate enforcement of the agreement outcome is an
  explicit non-goal.

## Plan Review (cycle 1, 2026-10-08)

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`
(no subagent dispatch surface in this Stage invocation; every selected persona applied
inline). Personas: Architecture Strategist, Security/Threat, Template Integrity, Test
Strategy. R-5 verified: `tests/test_shipment_reconcile_member_class_contract.py` and
`tests/test_shipment_reconcile_contract_single_source.py` pin the affected wording.

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

| # | Sev | Finding | Disposition |
|---|---|---|---|
| R-1 | P1 | Rule 2 must not reject the standard flow where the merge `commit_tracked` lands after `C`. | Fixed: `commit_tracked` explicitly excluded (Ordering contract 2, H2). |
| R-2 | P1 | Engine log paths must be containment-checked before read (192-F precedent). | Fixed: U2b requires the same containment helpers. |
| R-3 | P2 | U5 shares files with 208-S/210-S/212-S. | Fixed: sequencing section; checksum recompute after rebase. |
| R-4 | P2 | Tests must not depend on a real git repo for `M`. | Fixed: injected seam (U1). |
| R-5 | P3 | Step 0(d) relabel could break existing guard tests that quote "Pre-Mode step 2b agreement check". | Accepted: U4 updates any such pin in the same task; label text retained inside the step. |

**Gate decision: PASS** — zero P0, P1s fixed in-plan. Every task ≤ 2 h human-equivalent; no
`complexity: high` remains (163.004-T lowered from high to medium because the R1
atomic core is replaced by a bounded validator rule).
