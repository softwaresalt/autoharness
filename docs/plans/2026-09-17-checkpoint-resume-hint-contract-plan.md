---
title: "Checkpoint resume_hint: producer guarantee, deterministic validation, and historical-record migration"
description: "Implementation plan closing the autoharness-owned half of the checkpoint resume_hint gap: a historical-record policy for pre-existing resolved checkpoints lacking the field, a producer guarantee that every harness checkpoint author emits a specific top-level resume_hint including the minimal end-of-session shape, and deterministic author-time validation with regression tests — ordered policy-first so the validator cannot deadlock startup on an unrepairable historical record. The upstream backlogit validator, schema, and CLI-help change is explicitly excluded."
doc_type: plan
source: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
date: 2026-09-17
status: reviewed
revision: 2
revision_note: "Revision 2 is the canonical statement of the intended design. Review findings were remediated in place; this document states exactly one binding requirement per topic. The bounded audit trail lives in `linked_review`."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 1
source_stash_id: 71200CBB
stash_ids:
  - 71200CBB
deferred_scope_expansions:
  - 71200CBB
excluded_upstream_report: docs/scratch/bugs/2026-09-17-backlogit-checkpoint-v1-resume-hint-validation-gap.md
prior_learnings:
  - docs/compound/2026-08-18-stage-agent-checkpoint-index-sync-ordering-self-contradiction.md
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
linked_review: docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
covering_feature: 172-F
shipment: 180-S
requires_plan_hardening: "no"
source_refs:
  originating_pr: 452
  originating_review_thread: PRRT_kwDORzpWpM6i_UrE
  originating_task_id: "N/A"
  originating_feature_id: "N/A"
  originating_shipment_id: "N/A"
tags:
  - "checkpoint"
  - "recovery-contract"
  - "migration"
  - "fail-closed-design"
---

# Checkpoint `resume_hint` contract

## Provenance

Deferred scope expansion `71200CBB`, discovered via hosted Copilot review of
PR 452, thread `PRRT_kwDORzpWpM6i_UrE`. Task, feature, and shipment IDs were
recorded `N/A` at capture; the P-021 C6 late-identifier reconciliation was run
this session over the Ship-owned residual-risk records and **no late identifier
surfaced**. The `N/A` values stand as truthful terminal records. Non-blocking.

Unconditional P-021 C5 duplicate detection: **clean scan, no duplicate.**
`904C47BC` (top-level `progress` context-nesting) is a different defect class
on a different field; `445C1DFB` / `032-DL` is a distinct, already-repaired
earlier instance on a different file. Not merged.

## Ownership boundary

**In scope (autoharness-owned).** The producer guarantee, autoharness-side
deterministic validation and tests, and the historical-record policy.

**Excluded (backlogit-owned, upstream).** Any change to backlogit's CheckpointV1
validator or schema requiredness for `resume_hint`, and any change to the
`checkpoint create` CLI help text or its example payload. That half is written
up separately at
`docs/scratch/bugs/2026-09-17-backlogit-checkpoint-v1-resume-hint-validation-gap.md`
for parallel work in the backlogit workspace. This release unit is **not
blocked** on that report landing.

## Problem

`.github/instructions/backlogit.instructions.md` lines 147–151 require every
checkpoint to carry a specific resume hint **even when the record is
immediately resolved**. backlogit does not auto-populate the field — only
`created_at`, `updated_at`, and `status` are auto-populated — so the producer
is the only place it can originate. backlogit also does not consider the
omission an error: `backlogit checkpoint get` returns `"valid": true` with no
warning and no quarantine flag, and `checkpoint create --help` lists
`resume_hint` among the modeled top-level keys without stating it is required,
with an example payload that omits it entirely.

The startup recovery protocol fails closed on missing or malformed required
fields **without exempting resolved records**, and a resolved checkpoint cannot
be repaired through the official create operation. Therefore shipping
validation ahead of a historical-record policy converts a latent gap into a
hard, self-inflicted startup block.

## Ordering hazard (binding)

Work lands in the order **(3) policy → (1) producer → (2) validation**. The
validator is the last thing enabled. This is a correctness constraint, not a
preference: it is the difference between closing a gap and manufacturing a
deadlock.

## Design

### Part 3 first — historical-record policy

Define how a pre-existing `schema_version: 1` record lacking `resume_hint` is
treated by the fail-closed startup scan:

* A record with `status: resolved` **and** no `resume_hint` is classified
  `LEGACY_HINTLESS_RESOLVED`. It is enumerated, reported, and **excluded from
  the candidate set** — it can never be an active recovery candidate by
  definition, so excluding it removes no recovery capability.
* A record with `status: active` and no `resume_hint` is **not** exempt. It
  fails closed to operator handoff exactly as today. No active record is ever
  grandfathered.
* `LEGACY_HINTLESS_RESOLVED` is a **closed, enumerable** classification, not an
  open-ended tolerance: the scan reports the count and the filenames so the
  exemption is visible rather than silent.
* An operator may repair a historical record out-of-band; the policy neither
  requires nor performs such a repair.

### Part 1 — producer guarantee

Every harness checkpoint producer — Stage, Ship, and any other — emits a
top-level `resume_hint` specific enough to support a later recovery decision.
This explicitly includes the **minimal end-of-session completion checkpoint**,
which is the shape `checkpoint-20260916-064310.json` appears to be. A hint must
name the next actionable step or state explicitly that no re-entry is required;
a generic or empty string does not satisfy the guarantee.

### Part 2 last — deterministic validation

Autoharness-side validation plus regression tests that fail deterministically
when a **harness-authored** `schema_version: 1` payload omits `resume_hint`, so
the gap is caught at author time rather than at recovery time.

| Token | Condition |
|---|---|
| `CHECKPOINT_RESUME_HINT_MISSING` | Harness-authored V1 payload with no top-level `resume_hint` |
| `CHECKPOINT_RESUME_HINT_EMPTY` | Present but blank or whitespace-only |
| `CHECKPOINT_LEGACY_HINTLESS_RESOLVED` | Pre-existing resolved record, reported and excluded |

Validation applies at **author time** on payloads this harness produces. It
does not retroactively invalidate records it did not author, which is precisely
what Part 3 makes safe.

## Evidence recorded this session (read-only)

* `checkpoint-20260916-064310.json` in the working tree **now carries** a
  populated top-level `resume_hint`, added by operator/session repair. It is a
  worked example of a migrated historical record and is **not modified** by
  this plan or this session.
* Full unfiltered checkpoint enumeration: 51 records, 50 `resolved`, 1
  `abandoned` (`ship`-owned), zero anomalies, zero active `stage`-owned.
* backlogit version `1.10.1-0.20260823032255-b07729386a31+dirty`.

## Work Breakdown

| # | Task | Scope |
|---|---|---|
| T1 | Author the historical-record policy and the `LEGACY_HINTLESS_RESOLVED` classification | `.github/instructions/backlogit.instructions.md` + `templates/instructions/` |
| T2 | Wire the classification into the startup recovery scan contract in the agent templates and installed mirrors | `templates/agents/` + `.github/agents/` |
| T3 | Producer guarantee for the Stage checkpoint author, including the minimal completion shape | `templates/agents/_stage.agent.md.tmpl` + installed mirror |
| T4 | Producer guarantee for the Ship checkpoint author, including the minimal completion shape | `templates/agents/_ship.agent.md.tmpl` + installed mirror |
| T5 | Implement the three validation tokens at author time | `src/autoharness/` |
| T6 | Regression suite: one passing and one failing concrete state per token, plus an active-record-not-exempt case | `tests/` |
| T7 | Inventory test asserting every currently-committed checkpoint classifies cleanly under the new policy | `tests/` |

T5 declares `blocks` dependencies on T1 and T2 so the validator cannot land
before the policy.

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* The startup scan over this repository's 51 committed records produces zero
  fail-closed handoffs and reports its `LEGACY_HINTLESS_RESOLVED` set explicitly.
* No committed checkpoint file is modified by this release unit.
* `autoharness gate check` passes on every modified file.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Validator lands before policy and deadlocks startup | T5 declares `blocks` on T1 and T2; this is the entry's own recorded escalation trigger (b) |
| R2 | The legacy exemption silently grows into a permanent tolerance | The classification is enumerated and reported by count and filename at every scan, and T7 pins the current inventory |
| R3 | An `active` record is accidentally grandfathered | T6 carries an explicit active-record-not-exempt case |
| R4 | Someone pulls the upstream validator change into this scope | Stated as excluded in frontmatter, in the Ownership boundary section, and in Out of scope |

## Priority

Remains `medium`. Neither of the entry's own escalation triggers has fired: no
Orchestrator/Stage/Ship startup has been observed halting on this record, and
item (2) has not landed ahead of item (3) — this plan's ordering is what
guarantees the latter.

## Out of scope

* backlogit CheckpointV1 validator/schema requiredness for `resume_hint`.
* `checkpoint create` CLI help text and example payload.
* Repairing, recreating, or resolving `checkpoint-20260916-064310.json` or any
  other existing record.
* Stash entry `904C47BC` (top-level `progress` hoisting) — confirmed distinct,
  not merged, untouched.
