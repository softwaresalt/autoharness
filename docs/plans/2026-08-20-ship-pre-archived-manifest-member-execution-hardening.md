---
title: "Plan hardening - Ship pre-archived manifest-member execution exclusion"
date: 2026-08-20
plan: docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-plan.md
stash_id: B19E9662
deliberation: "022-DL (archived 2026-08-20 to .backlogit/archive/022-DL.md)"
status: "HARDENED (H1-H7); H1 and H6 require plan amendments A1 and A2 (applied)"
---

# Plan Hardening - Ship pre-archived manifest-member execution exclusion

Date: 2026-08-20
Agent: Stage (plan-harden gate, P-006)
Plan: `docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-plan.md`
Stash source: `B19E9662`
Deliberation: `022-DL` (archived 2026-08-20 to `.backlogit/archive/022-DL.md`)
Status: **HARDENED (H1-H7)**

Hardening was required because the change edits the **authoritative installed
Ship execution contract** that governs every future shipment in this workspace,
its **template counterpart** shipped to all downstream workspaces, and the
**harness-manifest checksum** that authenticates the installed artifact. A
careless edit here does not fail loudly on one shipment - it silently changes
how every subsequent shipment selects work.

## H1 - The derivation must not suppress the Step 0.5 item 1a early-warning

**Risk.** Step 0.5 item 1a halts with `SHIPMENT_STATE_INCONSISTENT` when a
shipment record is `queued` while any manifest task is already `active` or
`done`. The new derivation in Step 2 keeps only `queued`/`active` records and
drops everything else. If an implementer treats the derivation as the single
place where statuses are interpreted, they can reasonably conclude that `done`
members are simply "filtered out too" and quietly neutralise a fail-closed
integrity guard - converting a detectable torn-state shipment into a silently
partial run.

**Severity.** P1. This is the one way this fix can make the system *less* safe.

**Mitigation (PLAN AMENDMENT A1, applied).** The plan's contract must state
explicitly that:

* the Step 0.5 item 1a scan is unchanged and runs strictly **before** the new
  derivation, exactly where it runs today;
* the derivation is a **work-selection** step, never an integrity-guard step,
  and never suppresses, replaces, softens, or pre-empts item 1a's halt;
* excluding a `done` member from the executable set and skipping a
  `pre-archived` member are **distinct outcomes** and must be reported
  separately (`already_done` vs. `pre_archived_skipped`), so a `done` member
  can never be silently laundered as a tolerated pre-archived skip.

Task 1's acceptance criteria gain a corresponding line, and Task 2 gains
assertion **A6** requiring both files to state the unchanged-item-1a ordering
and the distinct reporting.

## H2 - Checksum computed from the working tree instead of the committed blob

**Risk.** This repository has a recorded CRLF/LF gotcha: hashing the Windows
working-tree file produces a checksum that will never match the LF-normalized
committed blob, and the mismatch surfaces later as a spurious harness-drift
failure in an unrelated shipment.

**Severity.** P2.

**Mitigation.** The plan already names `git cat-file -p :<path>` (staged) /
`HEAD:<path>` (post-commit). Hardening adds the explicit prohibition: **never**
`Get-FileHash` / `sha256sum` a raw working-tree read for this field. The
existing `note` on that manifest artifact already documents the procedure and
must be extended, not replaced.

## H3 - Feature entry in the manifest must not be claimed as a task

**Risk.** 144-S's manifest is `[136-F, 136.002-T, 136.003-T, 136.001-T]`. A
derivation that filters only on status and not on artifact type would hand
`136-F` to the claim step. The existing Step 0.5 item 1a already documents this
exact hazard ("the shipment `items` list is untyped").

**Severity.** P1.

**Mitigation.** Contract item 2 filters to task artifacts (IDs ending `-T`)
**before** any status read, and resolves the covering feature through
`parent_id` per the 097-S task-only-manifest precedent. Task 1's acceptance
criteria state this; Task 2 assertion A1 covers it.

## H4 - Empty executable set must halt, not auto-close

**Risk.** A manifest whose task members are all pre-archived yields an empty
executable set. A "helpfully" permissive contract could treat that as
"nothing to do, proceed to PR/closure", producing an empty PR or an
unwarranted closure attempt.

**Severity.** P2.

**Mitigation.** Contract item 5 halts and reports. Hardening pins the two
prohibitions explicitly: the empty case must **not** advance to build or PR,
and must **not** trigger any closure path. Operator disposition only. Task 2
assertion A4 covers the halt rule.

## H5 - Pre-archived skip must not become an unbounded status escape hatch

**Risk.** Written loosely ("skip members that cannot be claimed"), the rule
becomes a catch-all that swallows genuinely broken members - a missing record,
an unreadable file, a status the contract does not recognise - and Ship runs a
silently truncated shipment.

**Severity.** P1.

**Mitigation.** The exclusion is defined **positively and exhaustively**: keep
`queued`/`active`; skip-and-report `archived` (`pre-archived`); report `done`
separately per H1; **any other or unreadable status is a fail-closed halt**,
not a skip. Task 2 assertion A1 requires the exhaustive form to be present in
both files.

## H6 - Template must not introduce an unresolved variable for the archived state

**Risk.** The template defines exactly three status variables -
`{{STATUS_QUEUED}}`, `{{STATUS_ACTIVE}}`, `{{STATUS_DONE}}`. There is no
`{{STATUS_ARCHIVED}}`. Reaching for one by symmetry would ship an unresolved
`{{...}}` placeholder into every downstream workspace and fail the
variable-completeness quality gate.

**Severity.** P1 (quality-gate breaking).

**Mitigation (PLAN AMENDMENT A2, applied).** The template expresses the
archived state through the **`pre-archived` classification vocabulary already
defined by `shipment-reconcile`** (record archived / archive file present),
never through a new status variable. Task 1's acceptance criteria gain: no new
`{{VARIABLE}}` is introduced, and the template is checked for zero unresolved
placeholders. Task 2 assertion **A7** asserts the template contains no
`{{STATUS_ARCHIVED}}` token.

## H7 - The mandatory post-merge instruction reload is only partly enforced

**Risk.** The fix takes effect only for a Ship session that reads the merged
`.github/agents/_ship.agent.md`. A session holding the pre-merge contract in
context would re-expose the original failure on 144-S.

**Severity.** P2 (process, not artifact).

**Mitigation.** Partly enforced already: the installed Orchestrator's
multi-shipment cursor-advance step mandates "**reload current `main` agent
instructions** - re-read the freshly merged Orchestrator and Ship
templates/instructions - before advancing the cursor or selecting the next
successor shipment", after merge and after P-020 post-merge closure. That
covers the dark-run path from this shipment to 144-S. For an
operator-driven (non-dark) advance the obligation is manual, so it is recorded
redundantly in: the new shipment's title, the shipment-order record, and the
staging handoff memory. No backlog-record mechanism can enforce it, and none is
invented here.

## Hardening verdict

**HARDENED.** Two plan amendments (A1, A2) are required and have been applied to
`docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-plan.md`.
H2-H5 and H7 are satisfied by the plan as written plus the acceptance-criteria
lines named above. No task split is required: the amendments add contract
precision and two assertions, not new work surfaces, and both tasks remain
within the 2-hour rule.
