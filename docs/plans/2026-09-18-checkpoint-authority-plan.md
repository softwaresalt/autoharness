---
title: "Checkpoint authority: guarded create operation, bounded corpus classification, narrowed tool permission"
description: "Reduced current-state contract for the checkpoint defect. Replaces raw checkpoint creation reached through the backlogit/* tool wildcard with a guarded safe operation that validates resume_hint at author time, classifies the full 134-record historical corpus totally through the 185-S bounded reader including the two observed torn records, and narrows the Ship agent's tool wildcard to an enumerated set in the same activation commit that lands the guarded operation. Historical records are classified and never rewritten."
doc_type: plan
source: docs/plans/2026-09-18-checkpoint-authority-plan.md
date: 2026-09-18
plan_id: checkpoint-authority
plan_path: docs/plans/2026-09-18-checkpoint-authority-plan.md
plan_role: active
revision: 1
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 is a fresh document replacing the eight-attempt append history of checkpoint-resume-hint-contract at architecture level. It awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-18-checkpoint-authority-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 71200CBB
feature_id: 172-F
shipment_id: 180-S
unit_role: reduced-defect-unit
supersedes_plan: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
depends_on_shipments:
  - 185-S
task_reharvest_gate: 185-S
requires_plan_hardening: true
hardening_rationale: "Narrows an agent tool permission and introduces a guarded write path over a 134-record live corpus containing known-torn records. A defect either re-opens the bypass or breaks recovery for historical records."
tags:
  - defect-unit
  - checkpoint
  - resume-hint
  - tool-permission
  - reduced-scope
---

# Checkpoint authority

## The P0: the guard is bypassable

Attempt-08 `A1` (P0): the plan adds a guarded checkpoint-creation path, but
`.github/agents/_ship.agent.md` frontmatter grants `'backlogit/*'`, which
matches the raw `backlogit_create_checkpoint` tool. `.mcp.json` additionally
grants `"tools": ["*"]` to the backlogit server.

A guard reachable only when the agent chooses not to use the unguarded tool
sitting beside it is a **convention**, not a guard.

Narrowing needs no research: the same frontmatter file already demonstrates
per-tool enumeration for another server (`ms-python.python/...` listed tool by
tool). The pattern exists; it simply was not applied to `backlogit`.

The narrowing and the guarded operation therefore land in the **same activation
commit**. Any ordering that lands one without the other produces a reachable
state that is either a bypassable guard or a removed capability with no
replacement.

## The corpus is real and already broken

134 checkpoint records exist (60 live, 74 archived, plus one operator-authored
record preserved untouched). Two are **torn mid-write**:

```text
checkpoint-20260821-203531.json   4975 B   truncates mid-'context'
checkpoint-20260901-002917.json   5445 B   truncates mid-'progress'
```

Both truncate at exactly their file length — partial writes from a non-atomic
writer, preserved in the record. Attempt-08 `B4` recorded the consequence: a
scanner that raises cannot complete a corpus scan, and one that skips silently
under-reports.

## Contract

1. **Guarded create operation.** A registered safe operation validates
   `resume_hint` at author time — non-empty, and sufficient to resume without
   reading any other record — and writes through the `185-S` atomic writer.
   Raw creation is not reachable from the agent surface.
2. **Total classification.** Every record in the corpus resolves to exactly one
   of `VALID`, `LEGACY_NO_SCHEMA_VERSION`, or `QUARANTINED` with a reason. No
   record is skipped and no record is silently dropped. Classification runs
   through the `185-S` bounded reader, so a torn record yields a typed
   quarantine record rather than an exception.
3. **Historical compatibility.** Records predating the contract are classified,
   reported, and **never rewritten**. The two torn records stay torn; they are
   evidence.
4. **Narrowed permission.** `'backlogit/*'` is replaced by an enumerated tool
   list that excludes raw checkpoint creation, in the activation commit.

## Composed-state check

| Field | Value |
|---|---|
| Pass state | `CHECKPOINT_RECORDED` — `resume_hint` validated at author time and the record committed atomically |
| Fail state | `CHECKPOINT_REFUSED` — validation failed; nothing written, previous state intact |
| Scan states | `VALID` / `LEGACY_NO_SCHEMA_VERSION` / `QUARANTINED` — total over the corpus |
| Producer | `185-S` PR-1 atomic write and PR-4 bounded reader; `184-S` registry |
| Consumer | Ship and Stage checkpoint steps; the crash-resumption scan |
| Activation commit | one task: guarded operation registered **and** wildcard narrowed **and** both agent mirrors updated |

`CHECKPOINT_RECORDED` is reachable for any record with a valid `resume_hint`;
`QUARANTINED` is reachable today, demonstrated by the two torn records.

## Known constraint: the closed create namespace

`backlogit_create_checkpoint` at `schema_version: 1` treats the top level and
`progress` as a **closed** namespace — legal top-level keys are
`schema_version`, `agent`, `session_id`, `phase`, `status`, `created_at`,
`updated_at`, `context`, `progress`, `resume_hint`, and `progress` admits only
`tasks_completed`, `tasks_remaining`, `files_modified`, `decisions`. `context`
is open. Disposition fields are reserved to the abandon operation.

The guarded operation therefore nests **all** domain data under `context` and
adds no top-level key. A design that carried validated fields at the top level
would be rejected by the very tool it wraps.

## Rollout

**PREPARE (inert).** Validator, classifier and guarded operation built and
tested against the pinned corpus while the wildcard remains in place and no
agent surface calls the operation. Live behaviour is unchanged.

**VERIFY.** Full corpus classified with zero unhandled exceptions and zero
unclassified records; both torn records observed as `QUARANTINED` with reasons;
`CHECKPOINT_REFUSED` observed leaving prior state intact.

**ACTIVATE.** One task, one commit: register the operation, narrow the
frontmatter permission, and update the checkpoint procedure in the Ship and
Stage templates and both installed mirrors — together.

## Task re-harvest gate

Deferred until `185-S` fixes PR-1 and PR-4 signatures. Existing tasks under
`172-F` remain queued and are re-sliced against the delivered primitives.

## Out of scope

* Repairing, migrating or deleting any historical checkpoint. **Immutable
  history is never rewritten.**
* The operator-authored `checkpoint-20260916-064310.json`, which is preserved
  untouched and is read only as a classification fixture.
* Broad `.mcp.json` permission redesign. Only the tool grant this guard depends
  on is narrowed.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Narrowing the wildcard removes a tool Ship needs elsewhere | The enumerated list is derived from tools actually invoked in the Ship surfaces, and the VERIFY step records that inventory before activation. |
| R2 | Author-time `resume_hint` validation is too strict and blocks checkpointing | `CHECKPOINT_REFUSED` names the failing rule; a refusal never destroys prior state, so recovery is always possible. |
| R3 | Quarantine hides a record from recovery | Quarantined records are reported in the scan output with their reason, so they are visible rather than absent. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Is a guarded operation a control while `backlogit/*` is granted? | No. A guard reachable only when the agent declines to use the unguarded tool beside it is a convention. That is why narrowing and the guarded operation land in the **same** commit. |
| H2 | Does narrowing require research? | No. The same frontmatter file already enumerates tools per server for another provider. The pattern exists and was simply not applied to `backlogit`. |
| H3 | Could narrowing remove a tool Ship needs? | The enumerated list is derived from tools actually invoked across the Ship surfaces, and that inventory is recorded in VERIFY before activation rather than discovered after it. |
| H4 | Can a torn record break the corpus scan? | No. The `185-S` bounded reader returns a typed quarantine record. A scanner that raised could not complete the scan, and one that skipped silently would under-report — both were attempt-08 `B4`. |
| H5 | Should the two torn records be repaired? | No. Immutable history is never rewritten. They are classified, reported, and retained as the evidence that motivated the atomic writer. |
| H6 | Why nest everything under `context`? | Because `backlogit_create_checkpoint` treats the top level and `progress` as a closed namespace at `schema_version: 1`. A design carrying validated fields at the top level would be rejected by the tool it wraps. |
| H7 | Is the operator-authored checkpoint at risk? | No. `checkpoint-20260916-064310.json` is read only as a classification fixture and is never written. |

### Blast radius

An agent tool permission, a guarded write path over a 134-record live corpus,
and the checkpoint procedure in two agent templates and two installed mirrors.
A defect either re-opens the bypass or breaks crash recovery.

### Rollback

PREPARE is inert; the wildcard stays and no surface calls the operation. The
ACTIVATE commit reverts as a unit, restoring the wildcard **and** removing the
operation together — the only revert that cannot leave the capability removed
with no replacement.

### Verification floor

Full corpus classified with zero unhandled exceptions and zero unclassified
records; both torn records observed `QUARANTINED` with reasons; and
`CHECKPOINT_REFUSED` observed leaving prior state intact.
