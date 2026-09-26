---
title: "Plan review attempt 08 (terminal) — Workspace-authoritative branch resolution"
description: "Immutable per-attempt plan-review artifact recording the independent attempt-08 review of docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md at revision 7, against reviewed content HEAD f142173c. Gate result FAIL; decision BLOCKED on one P0, two P1 and two P2 deduplicated findings: selected_branch crosses no executable fixed-argv boundary because the consuming site is a Markdown agent that interpolates it into prose, the normative creation command 'git checkout -b -- <selected_branch>' is not valid git argv, and comparison-then-creation needs one atomic branch-ensure operation. The authorized remediation cycle is exhausted: no remediation was performed, no finding is closed, and no PASS is asserted."
doc_type: review
source: docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-08.md
date: 2026-09-18
review_artifact_role: attempt
review_artifact_immutable: true
attempt: 8
attempt_range: "08"
attempt_conformance: conforming
review_terminal: true
verdict_manifest: docs/reviews/2026-09-17-workspace-authoritative-branch-resolution-plan-review.md
supersedes: docs/reviews/review-history/2026-09-17-workspace-authoritative-branch-resolution-plan-review-attempt-07.md
plan_path: docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md
plan_id: workspace-authoritative-branch-resolution
reviewed_revision: 7
reviewed_content_head: f142173c
reviewed_content_state: committed
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 3
source_stash_id: 86498B64
source_stash_id_recorded_in_backlog: 86498B64
source_stash_id_conflict: false
merged_stash_ids:
  - 14F4D6F3
feature_id: 170-F
shipment_id: 178-S
review_cycle: 8
dispatch_mode: declared-degradation
anchor_route: absent
anchor_route_note: "No cross-model anchor was available. The cross-model rubrics ran under same-model declared degradation; this is recorded, not compensated for."
gate_result: FAIL
decision: BLOCKED
verdict_at_entry: REMEDIATED-PENDING-REVIEW
verdict_at_entry_plan_revision: 7
remediation_authorization: none-exhausted
remediation_revision: null
remediation_performed: false
disposition: null
p0_open: 1
p1_open: 2
p2_open: 2
severity_basis: "Severities are the dispatch-recorded severities. The fixed-argv boundary finding was dispatched with an explicit P0 label; the invalid creation command and the missing atomic branch-ensure operation were dispatched P1. Findings dispatched on the portfolio P2 list are recorded P2 against the plan surface they land on."
persona_coverage:
  - persona: constitution
    status: complete
  - persona: python
    status: complete
  - persona: scope-boundary
    status: complete
    findings: none
  - persona: learnings
    status: degraded
    note: "Not-ready/degraded: could not inspect the diff. Relevant prior lessons were retrieved and applied."
  - persona: architecture
    status: complete
  - persona: agent-native-parity
    status: complete
  - persona: security-lens
    status: complete
tags:
  - "plan-review"
  - "terminal-review"
  - "pipeline-topology"
  - "branch-ownership"
  - "argv-injection"
---

# Plan review attempt 08 (terminal) — Workspace-authoritative branch resolution

This artifact records **one thing**: the independent reviewer's verdict on plan
revision 7 as it stands at content HEAD `f142173c`. It has no Part 2. The
authorized remediation budget is **exhausted**, so no remediation followed this
review, no finding below is closed, and Stage asserts no `PASS`.

## Reviewed subject

| Field | Value |
|---|---|
| Plan | `docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md` |
| Reviewed revision | 7 |
| Reviewed content HEAD | `f142173c` (committed) |
| Verdict at entry | `REMEDIATED-PENDING-REVIEW` at plan revision 7 |
| Covering feature / shipment | `170-F` / `178-S` |
| Source stash | `86498B64` (merged with `14F4D6F3`); plan and backlog agree |
| Dispatch mode | `declared-degradation` |
| Gate result | **FAIL** |
| Decision | **BLOCKED** |

## Dispatch and coverage

All **seven** required personas ran: Constitution, Python, Scope Boundary,
Learnings, Architecture, Agent-Native Parity, Security Lens.

* **Anchor route absent.** No cross-model anchor was reachable; the cross-model
  rubrics executed under *same-model declared degradation*.
* **Learnings degraded / not-ready.** Could not inspect the diff; prior lessons
  were retrieved and applied, diff-grounded checks did not run.
* **Scope Boundary returned no finding for this plan.** Its `source_stash_id`
  and the executable records both name `86498B64`, which exists.

## P0 findings (1)

**A1 — `selected_branch` never crosses an executable fixed-argv boundary.**
The plan's safety argument rests on a `--`-terminated fixed-argv boundary
(asserted by `T8a`, implemented by `T8b`). But the consuming site is
`templates/agents/_ship.agent.md.tmpl` and its installed mirror — a **Markdown
agent document**. A Markdown agent does not execute argv; it **interpolates the
value into prose** that a model then composes into a shell command. There is no
`execve`, no argument vector, and therefore no boundary for `--` to terminate.
The leading-hyphen and option-like rejection rules are a **validator-side
mitigation only**, and the plan's claim that a leading-hyphen-adjacent value
`survives the --terminated fixed-argv boundary` is not testable against the
surface the plan actually changes. The control the plan relies on for its
highest-risk path does not exist where the plan places it; an executable
boundary — a real callable that receives `selected_branch` as a positional
argument — is required.

## P1 findings (2, deduplicated)

**B1 — the normative creation command is not valid `git` argv.**
The plan specifies the creation site as `git checkout -b -- <selected_branch>`.
That is **not a valid invocation**: in `git checkout -b <new-branch>`, `--`
separates revisions from *pathspecs*, and placing it before the new-branch
operand makes the branch name parse as a pathspec rather than as the name of the
branch to create. The normative command as written fails. This is the wrong
command, and it is recorded P1 independently of A1 — fixing the boundary does
not fix the argv, and fixing the argv does not create the boundary.

**B2 — comparison and creation need one atomic branch-ensure operation.**
`selected_branch` is consumed at two separate sites — a **comparison** site and a
**creation** site — with no operation that makes the pair atomic. Between the
two, the branch may be created, renamed, or deleted by another actor, so the
branch Ship compares against is not provably the branch Ship creates or checks
out. The plan needs a single atomic *ensure-branch* operation whose postcondition
is `the working tree is on exactly selected_branch`, rather than a check followed
by an unguarded create.

## P2 findings (2)

**C1 — the verdict manifest's `description` asserts a falsehood.**
The mutable verdict manifest's `description` claims `No PASS exists anywhere in
this record` while its own roster carries `verdict: PASS` at attempts 2 and 3.
The truthful statement is narrower: no `PASS` exists at or after attempt 4, and
none exists against the governing revision. Recorded against the manifest
wording **as observed at `f142173c`**; one defect class, six instances across the
portfolio, counted once per manifest surface.

**C2 — branch rollback details are underspecified.**
The plan does not state what happens to a branch that was created from a
`selected_branch` later found invalid, nor what the rollback leaves behind when
an ensure/create step partially succeeds. Given the recorded prior lesson that a
branch rename after a PR is opened auto-closes the PR, the rollback path needs
to be stated explicitly rather than left to the executing agent's judgement.

## Disposition

**No remediation.** The authorized remediation budget is exhausted.
`remediation_revision` is `null`, `disposition` is `null`, and the governing
revision remains 7 — the revision that was reviewed and found BLOCKED.

This plan is **not harvest-ready and not Ship-ready**. No backlog executable
record, source file, test or configuration was changed on the strength of this
review.
