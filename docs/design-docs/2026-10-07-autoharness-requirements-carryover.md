---
title: "autoharness requirements carryover from backlogit"
description: "Requirements to carry manually from backlogit into the autoharness workspace"
doc_type: scratch
created_at: 2026-10-07T04:19:39Z
source_workspace: softwaresalt/backlogit (main @ a960cd54)
autoharness_reference: origin/main @ 698590f8 (v1.5.0 + 990 commits)
---

# autoharness requirements carryover from backlogit

This doc lists requirements that originated in backlogit and belong in
autoharness. Carry it to the autoharness workspace by hand, then stash or plan
each requirement there. It is local-only: `docs/scratch/` is not committed.

All dates and times here are UTC.

## Context

The backlogit dark-factory run on 153-S halted with
`PREDECESSOR_CLOSURE_INCOMPLETE`. The predecessor, 154-S, closed as
`READY_WITH_CONDITIONS`, and its condition (b) is still unattested.

Condition (b) requires that the `scheduler_baseline_claim` marker written at
shipment claim is actually consumed. Under convergence Model M2 there are two
consumers:

| Consumer | Location | State |
|---|---|---|
| Ship agent Step 4.0 wave admission | backlogit `.github/agents/_ship.agent.md` (about lines 544–575) | Present, proven by 195-S fixture proof |
| External P-002.6 wave scheduler | autoharness templates | Absent: 0 hits for `scheduler_baseline`, `baseline_claim`, or `claim-assigned` in `templates/` |

Decision 074-DL sets the interim unblock signal as an operator-only
`CONDITION_B_ATTESTED: <evidence>` comment in the 154-S item log. No agent may
originate it. Twenty-one queued backlogit shipments depend on 154-S, so this gap
blocks most of the backlogit DAG.

Source references in backlogit:

* `docs/decisions/2026-09-20-shipment-claim-wave-scheduler-convergence-deliberation.md` (Model M2, about lines 204–252; risk "marker never consumed", about line 423)
* `docs/decisions/2026-09-28-513e62ab-condition-b-enforcement-deliberation.md` (074-DL operator decisions, about lines 240–285)
* `docs/exec-plans/2026-09-30-af1e5075-condition-b-preclaim-harness-contract-plan.md` (Attestation Rule R6, about lines 159–190)
* `docs/closure/154-S-173-F-scheduler-baseline-marker-post-merge-closure.md`
* `docs/closure/195-S-claim-start-proof-positive.md`

## R1 — External scheduler consumes the claim marker (blocks 153-S)

**Priority**: critical for backlogit throughput.

**Requirement**: Make the autoharness P-002.6 wave scheduler and Ship template
consume the `scheduler_baseline_claim` marker, following Model M2.

* Read the active shipment, its exact ordered `custom_fields.items`, each
  member's status, each member's `scheduler_baseline_claim` marker, and each
  member's `logs/<id>.jsonl`.
* Classify each `active` member exactly as backlogit Ship Step 4.0 does. A
  member is **claim-assigned** only when it is `active`, its marker equals the
  live shipment `S`, it is listed in `S`'s live `custom_fields.items`, and its
  current start epoch has no valid `WORK_STARTED:` record. Every other `active`
  member is an **active residual** (`WAVE_NO_PROGRESS`, detail
  `active residual`), including a missing or non-`S` marker or a member absent
  from the live manifest.
* Admit claim-assigned members to wave 1 without treating them as residual
  active work.
* Fail closed with `WAVE_CLAIM_STATE_INDETERMINATE` when the active-shipment
  count is not exactly one, the manifest drifts between two reads, an item read
  is stale or errors, or the marker equals `S` but the member log is missing,
  unparseable, or lacks a claim event. Indeterminate takes precedence over
  residuals.

**Single-source contract**: Publish one versioned marker-consumption contract,
for example `marker_contract_version: 1`. Both backlogit Ship Step 4.0 and the
autoharness scheduler cite it so the two consumers cannot drift.

**Target files** (autoharness):

* `templates/agents/_ship.agent.md.tmpl` (Step 4.0 wave admission)
* `templates/policies/workflow-policies.md.tmpl` (P-002.6 wave semantics)
* `src/autoharness/gates/topology.py` (optional: marker check in `pre_claim`, the long-term L3 enforcement per 074-DL)

**Acceptance criteria**:

* A fixture with a claimed shipment whose members are `active` and
  marker-stamped admits the dependency-ready member in wave 1 and reports the
  rest as claim-assigned waiting, with zero active residuals.
* A member with a missing or non-`S` marker is classified as an active
  residual, never as claim-assigned. A member whose marker equals `S` but whose
  log lacks a claim event is indeterminate.
* After release and install into backlogit, the operator can truthfully post
  `CONDITION_B_ATTESTED: <evidence>` on 154-S, citing the autoharness release
  and fixture proof.

## R2 — Prevention rows from the 153-S halt

These seven rows are stashed in backlogit (PR #482) and target autoharness
templates. Rows P1 and P3 are operator-approved to proceed first.

| Row | backlogit stash | Priority | Requirement | Target autoharness files |
|---|---|---|---|---|
| P1 | 6AB5E7FC | high, approved | Gate-aware eligibility. Orchestrator Step 0 runs `autoharness gate pipeline-topology --mode agent --shipment {id} --phase pre_claim --json` for each DAG-ready candidate. Report gate-blocked candidates as ineligible with the gate token. | `templates/agents/_orchestrator.agent.md.tmpl` |
| P2 | 23D47703 | high, operator-emphasized | Model closure conditions as backlog items. Ship closure creates one item per condition, with owner, UTC due date, and attestation evidence, plus `blocks` edges from successors. DAG readiness then reflects open conditions. | `templates/agents/_ship.agent.md.tmpl`, `templates/skills/operational-closure/SKILL.md.tmpl` |
| P3 | AC530DE2 | high, approved | Dark-mode activation preflight. Gate the scope head before recording `DARK_MODE_ACTIVE`. Report later in-scope sequencing waits as `PENDING` and surface external blockers at activation. | `templates/agents/_orchestrator.agent.md.tmpl`, `templates/prompts/feature-flow-dark.prompt.md.tmpl` |
| P4 | EB95F5F7 | medium | Session-start surfacing of `READY_WITH_CONDITIONS` closures, with owner, UTC age, and blocked successors. | `templates/agents/_orchestrator.agent.md.tmpl` |
| P5 | 43BB6B88 | medium | Stage Step 5.5 checks predecessors' open closure conditions before assembling a shipment. | `templates/agents/_stage.agent.md.tmpl` |
| P6 | 8664E2A1 | medium | Every closure condition carries an owner, UTC due date, attestation evidence, and escalation path. Add a lint check. | `templates/skills/operational-closure/SKILL.md.tmpl`, `src/autoharness/gates/topology.py` or a doc lint |
| P7 | A42A17B8 | high | UTC is mandatory for all recorded dates and times: memory folder names, frontmatter, comments, logs, and output stamps. Add a lint check. | `templates/instructions/output-timestamps.instructions.md.tmpl`, `templates/foundation/copilot-instructions.md.tmpl`, `templates/foundation/AGENTS.md.tmpl`, `templates/skills/compact-context/SKILL.md.tmpl` |

**Acceptance criteria (shared)**:

* P1: a candidate whose predecessor closure is `READY_WITH_CONDITIONS` with an
  unsatisfied condition appears as ineligible in the eligibility report, not as
  DAG-ready.
* P3: activating dark mode on a gate-blocked scope head halts before
  `DARK_MODE_ACTIVE` is recorded.
* P7: no generated artifact records local-offset times; date-named folders use
  the UTC date.

## Already implemented in autoharness (no action)

* The `pipeline-topology` gate accepts `READY_WITH_CONDITIONS` when the closure
  frontmatter has a `conditions:` list whose entries are `satisfied: true` with
  evidence (v1.5.0, commit `e446f73b`).

## Related autoharness stash IDs

Check these for overlap before creating new items: 34AAF1C7, 808BAB5E,
3B67029C, 2940EA5F, C327A8DE.

## Release-cut guidance

* origin/main is 990 commits past v1.5.0.
* P1 and P3 do not depend on R1. Cutting a release once P1 and P3 land improves
  backlogit eligibility reporting without waiting on R1.
* 153-S and the other 154-S successors unblock only after R1 ships and is
  installed in backlogit, followed by the operator attestation. The alternative
  is a recorded operator decision that in-repo Ship Step 4.0 consumption alone
  satisfies condition (b).
* Recommendation: do not hold a release for R1 alone. Cut one release for P1,
  P3, and P7, then a follow-up release for R1.

## backlogit follow-up after autoharness release

1. Install the release and run `autoharness verify-workspace`.
2. Operator posts the attestation (operator only; no agent may originate it):

   ```text
   backlogit comment add 154-S --actor operator --comment "CONDITION_B_ATTESTED: <evidence citing autoharness release and fixture proof>"
   ```

3. Ship or Stage copies the attestation's timestamp, actor, and leading line
   into the 154-S closure frontmatter as a `conditions:` entry with
   `satisfied: true`.
4. Rerun the `pipeline-topology` `pre_claim` gate for 153-S.
