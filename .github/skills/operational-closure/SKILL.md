---
description: "Produce release-readiness, releasability evidence, monitoring, rollback, and feedback artifacts that close the loop after implementation and verification"
---

# Operational Closure

Turn “implemented” into “safely absorbed by the running system”. This skill creates the artifacts and decisions that close the loop after code review, CI, and runtime verification.

## When to Use

Invoke when a feature, fix, or risky change is ready to hand off into merge, deployment, or post-deploy monitoring.

## Inputs

* `mode`: (Required) One of `pre-merge`, `post-merge`, or `post-deploy`.
* `context`: (Required) PR, task, feature, or release context.
* `verification_report`: (Optional) Path to the runtime verification report.
* `validator_evidence`: (Optional) Structured handoff from runtime-verification describing surface adapters, probe outcomes, manual checkpoint evidence, and verdict.
* `releasability_expectations`: (Optional) Structured requirements from `runtime_validation.releasability`.

## Output

* Closure artifact at `docs/closure/{shipment_id}-{feature_id}-post-merge-closure.md`
  * **Required frontmatter keys**: `closure_status` (`READY`, `READY_WITH_CONDITIONS`, or `BLOCKED`) and `compaction_status` (`pending`, `done`, or `degraded`). New artifacts always write `compaction_status`; the legacy `compaction` alias is accepted on read only for already-committed history. Both keys are gate-relevant. The consumer's acceptance requirement, quoted from the closure-evidence contract: "a closure artifact is accepted only when its frontmatter carries a compaction_status (or legacy compaction) of done or degraded AND a closure_status of READY, or of READY_WITH_CONDITIONS with a non-empty conditions list in which every entry is a mapping with satisfied: true (the literal boolean) and a non-empty evidence reference".
  * **Naming note**: the closure date is carried in frontmatter, never in the filename. Legacy date-prefixed names (`{YYYY-MM-DD}-{shipment_id}-{slug}-closure.md`) remain readable for already-committed history but are never written; recognition on read is not permission to write.
* Structured releasability evidence summarizing whether the change is `READY`, `READY_WITH_CONDITIONS`, or `BLOCKED`
* A **compaction status** field (`pending` → `done` / `degraded`) recording P-020 post-merge context compaction state
* Follow-up tasks or compound-learnings triggers when needed

## Required Protocol

When the `agent-intercom` capability pack is installed, follow
`.github/instructions/agent-intercom.instructions.md`: broadcast closure readiness, blocked states,
monitoring handoff details, and any rollback trigger that the operator should be aware of during
the validation window.

When the `browser-verification` capability pack is installed, also follow
`.github/instructions/browser-verification.instructions.md`: carry browser
verification evidence, human-checkpoint outcomes, and browser-specific post-deploy
checks into the closure artifact instead of treating them as side notes.

When the `strict-safety` capability pack is installed, also follow
`.github/instructions/strict-safety.instructions.md`: carry the risky
`ProposedAction` entries, their `ActionRisk`, approval path, and final
`ActionResult` into closure artifacts when those details matter to rollout,
monitoring, or rollback.

When the `release-observability` capability pack is installed, also follow
`.github/instructions/release-observability.instructions.md`: integrate the
monitoring plan (SLIs, dashboards, alert thresholds), pre-deploy audit results,
post-deploy observation window (owner, duration), and rollback triggers into
the closure artifact as structured sections rather than ad hoc notes.

### Step 1: Gather Closure Context

Collect:

* Summary of the change
* CI status and unresolved review items
* Runtime verification report or validator evidence (required when runtime surfaces were changed) — including verdict (`PASS`, `PASS_WITH_FOLLOW_UP`, `FAIL`, or `BLOCKED`), evidence, manual checkpoint evidence, and follow-up recommendations. If verification was BLOCKED, record the blocked status and the missing prerequisite as a closure condition.
* Any risky actions that required approval, rollback planning, or explicit containment
* Affected runtime surfaces
* Deployment or release path, if applicable
* Invariants that must remain true after release
* Data, migration, or rollout-sensitive behavior that could require extra monitoring

### Step 2: Build the Closure Checklist

The closure artifact MUST include:

* **Invariants to preserve** — the behaviors or guarantees that cannot regress
* **Validator evidence** — the structured summary of probes, manual checkpoints, verdict, and blocked prerequisites received from runtime-verification
* **Pre-deploy audits** — migrations, flags, config, access, or rollout prerequisites that must be checked before release
* **Deployment or rollout path** — merge-only, deploy, canary, phased rollout, maintenance window, or handoff path
* **Post-deploy checks** — the first concrete observations or smoke checks to run after release
* **Risky action record** — the `ProposedAction` entries that materially affected rollout or rollback, their `ActionRisk`, and final `ActionResult`
* **Healthy signals** — what success should look like
* **Failure signals** — what indicates rollback or intervention is needed
* **Monitoring plan** — logs, dashboards, alerts, or smoke checks to watch
* **Rollback trigger** — the condition that should halt or reverse the rollout
* **Rollback procedure** — the actual rollback or mitigation action to take when the trigger fires
* **Validation window** — how long the change should be watched
* **Owner** — who is responsible for observing or acting
* **Source artifact cleanup** — the traceable record of which source artifacts feeding the shipped scope were retired. For every shipped top-level item (feature or chore), record the `custom_fields.source_stash_id` and `custom_fields.source_deliberation_id` values, each with its outcome. A `source_stash_id` outcome is one of: archived, skipped because it was already archived, skipped because it was not found, or `none` when the item declares no such field. A `source_deliberation_id` outcome is `none` when the item declares no such field; otherwise it is the report's literal outcome — `archived`, `already-archived`, `retained_read_error`, `retained_engine_unverified`, `retained_ambiguous`, `retained_live_status`, `retained_shared_reference`, or `retained_description_mention` — or `skipped_not_in_disposition_report` (the deliberation is absent from the report). The `source_deliberation_id` outcome and its `reason_code` (and `path`, when present) are copied from the shipment's `linked_deliberation_disposition` report (the `shipment-reconcile` Linked-Deliberation Disposition step, P-015 INV-12), never re-derived; an unknown `reason_code` is recorded verbatim, and neither Ship nor the disposition step archives a `retained_*` or `skipped_not_in_disposition_report` deliberation (an explicit manifest member is archived by the close path itself, H10). Ship retires the source stash entries and records these outcomes (only the INV-12 disposition step archives a deliberation) against the backlog artifacts under `.backlogit/` during post-merge closure and reports the resulting IDs here, so this section — not the tool's own logs — is the closure artifact's system of record for source-artifact retirement.
* **Compaction status (P-020)** — the post-merge context compaction state, one of `pending`, `done`, or `degraded`. operational-closure initializes this field to `pending` when it creates the closure artifact; the Ship post-merge closure finalizes it to `done` after compact-context completes, or `degraded` if compact-context was invoked but failed (non-blocking). Allowed transitions are `pending` → `done` and `pending` → `degraded` only. The Orchestrator's next-shipment routing (P-001 + P-020) treats `pending`, unset, or missing as an incomplete post-merge closure that blocks routing, and `done` or `degraded` as satisfied.
* **Releasability evidence** — the final structured record showing which required evidence from `runtime_validation.releasability` is satisfied, conditional, or still blocked

### Step 3: Record Readiness Status

Return one of:

* **READY** / `READY` — merge/deploy can proceed with the recorded monitoring plan
* **READY WITH CONDITIONS** / `READY_WITH_CONDITIONS` — proceed only if named conditions are satisfied
* **BLOCKED** / `BLOCKED` — missing verification, unclear rollback path, or unresolved runtime risk

The closure artifact is the canonical releasability evidence record. Do not
collapse validator outcomes back into free-form prose after they have been
structured.

### Step 3a: Validate the Closure Artifact with the Closure-Evidence Gate

Run the write-time closure-evidence gate against the artifact:

```text
autoharness gate closure-evidence --path docs/closure/{shipment_id}-{feature_id}-post-merge-closure.md --shipment {shipment_id} --json
```

* **Before every commit of the artifact**, including the first commit while
  `compaction_status` is still `pending`: a `failed_check` of
  `workspace_containment`, `input`, `filename`, or `discoverability` blocks the
  commit. Fix the path, filename, or frontmatter syntax and re-run; never
  rename the artifact to a legacy date-prefixed form. A `frontmatter_predicate`
  failure is expected while `compaction_status` is `pending` or
  `closure_status` is `BLOCKED`, and does not block committing that truthful
  record. Because the gate stops at the first failed check, this run confirms
  containment, readability, and the canonical filename; discoverability is
  confirmed by the final run.
* **Before the closure is declared complete**, after the compaction status is
  finalized to `done` or `degraded`: the gate MUST exit `0` before the closure
  is declared complete. Only an artifact that passes is predecessor-closure
  evidence. A finalized `BLOCKED` closure (or a `READY_WITH_CONDITIONS` closure
  with an unsatisfied condition) never passes: it may still be committed as a
  truthful record when the gate's reported `failed_check` is
  `frontmatter_predicate`, but the closure is not declared complete and the
  successor shipment stays blocked, as intended.

### Step 4: Feed Back into the Harness

When the closure process reveals durable knowledge:

* Invoke `compound` for new runtime, deployment, or workflow learnings
* Update documentation if the release process or architecture knowledge changed
* Add tuning proposals if the harness lacked a needed safety mode, verification pattern, or reviewer

## Why This Skill Exists

Operational closure is the compositional bridge from code production to safe absorption. It makes runtime verification actionable, keeps PRs honest about monitoring expectations, and turns release outcomes into future harness improvements.

## Quality Criteria

* Closure artifacts include concrete release and monitoring signals, not generic advice
* Validator evidence and releasability evidence remain structured rather than turning back into report-oriented runtime notes
* Pre-deploy and post-deploy checks are explicit when the change has runtime or rollout risk
* Risky actions and their outcomes are visible when they affect release safety
* Rollback triggers and rollback procedures are explicit and actionable
* Ownership and validation windows are recorded
* Durable runtime learnings are fed back into the harness when appropriate


## Model Routing

This skill operates at **Tier 2 (Standard)** — closure artifact assembly from defined inputs.

Generated by autoharness | Template: operational-closure/SKILL.md.tmpl
