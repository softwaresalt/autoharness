---
title: "R1 claim-marker consumption: scope, priority, and L3 topology deferral"
date: 2026-10-08
status: decided
stash_id: 21F8C04A
paired_stash: F2D11D61
source: docs/design-docs/2026-10-07-autoharness-requirements-carryover.md
---

# R1 claim-marker consumption: scope, priority, and L3 topology deferral

## Problem Frame

Stash `21F8C04A` (CARRYOVER R1) asks autoharness to make "the autoharness P-002.6 wave
scheduler and Ship template" consume backlogit's `scheduler_baseline_claim` marker (Model
M2). It also asks for one versioned marker-consumption contract (`marker_contract_version: 1`)
that both backlogit Ship Step 4.0 and autoharness cite. The entry says R1 blocks backlogit
`153-S` and the `154-S` successor DAG.

Triage found that two premises of the entry no longer hold. This deliberation decides what R1
means for this repository.

## Research Findings

1. **There is no autoharness P-002.6.** `git grep` across `templates/`, `src/`, `.github/`,
   and `schemas/` finds no `P-002.6`, `WAVE_NO_PROGRESS`, `WAVE_CLAIM_STATE_INDETERMINATE`, or
   `scheduler_baseline_claim`. The autoharness Ship template has no Step 4.0. The dependency-aware
   wave scheduler (P-002.6, Ship Step 4.0 Wave Admission) is a backlogit-local customization.
   It is drift-ignored in backlogit's `.autoharness/drift-ignore` ("a template adoption that keeps
   P-002.6 MUST carry ...") and was never adopted upstream.
2. **The autoharness claim-to-admission seam is P-002.7 plus Ship Step 3 item 1.**
   P-002.7 (`templates/policies/workflow-policies.md.tmpl`, marker block `P-002.7:BEGIN/END`)
   defines exactly three rows, T1–T3. Ship Step 3 item 1 keeps every `queued` and `active`
   manifest task in the executable set. Today autoharness admits every active member and has no
   active-residual concept. `tests/test_p002_7_member_status_contract.py` pins the P-002.7 block
   byte-for-byte. Its near-miss fixture uses a fourth row `**halt** WAVE_NO_PROGRESS` as a
   forbidden mutation, so new consumption text must sit in its own block.
3. **The producer contract already exists.** backlogit publishes
   `docs/design-docs/scheduler-baseline-marker-contract.md` (`scheduler-baseline-marker/v1`). It
   covers the key and value shape at `custom_fields.scheduler_baseline_claim`, a read recipe
   with exact JSON paths, the normative three-part option-A predicate, the active-shipment
   cardinality guard, and residuals R1–R3. The autoharness consumer contract must cite it rather
   than restate it.
4. **R1 no longer gates 153-S.** `docs/closure/154-S-173-F-scheduler-baseline-marker-post-merge-closure.md`
   (backlogit) records `condition-b-scheduler-marker-consumption` as `satisfied: true`,
   attested by the operator at `2026-10-07T06:31:36Z`. The attestation substitutes in-workspace
   Ship consumption. The closure says: "R1 stays open so upstream consumption can replace the
   substitution, but it does not re-gate `154-S` successors unless this attestation is
   revoked." The carryover doc was cut at `2026-10-07T04:19:39Z`, before the attestation.
5. **The start record is a backlogit Ship convention.** backlogit Ship writes
   `WORK_STARTED: <S>` as an item comment. It defines the start epoch from the latest
   `status_changed` event with `delta.to: active` and `delta.reason: shipment claimed`. The
   autoharness Ship Step 4.1 writes no start record, so "claim-assigned versus started" cannot
   be decided in autoharness today.
6. **L3 (074-DL).** backlogit `docs/decisions/2026-09-28-513e62ab-condition-b-enforcement-deliberation.md`
   (~L167, ~L215, ~L283) names the `pipeline-topology` `pre_claim` gate as the long-term
   deterministic home of predicate (C), which is condition attestation. It is contingent on
   backlogit stash `A592FC1C`, under which the topology gate mis-derives predecessors.
7. **Learnings.** `docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`
   explains why the post-claim cascade state is the claim's own and not a residual (the P-002.7
   basis). `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md` covers the
   mirror and manifest checksum discipline.

## Options Evaluated

### Option A: Upstream the full backlogit P-002.6 wave scheduler plus marker consumption

Port waves, red-deliverable execution, wave green semantics, the snapshot or frozen-M machinery,
and the simulation fixture (150 assertions, 21 scenarios) into the templates, then add marker
consumption. This is very large: several features and more than 20 tasks. Much of it is
backlogit-specific. It is not required to consume the marker.

### Option B: Publish the consumer contract as P-002.8 and wire Ship Step 3 and Step 4.1, capability-gated (chosen)

* Add a new policy block, P-002.8 "Claim-Marker Consumption Contract"
  (`marker_contract_version: 1`), alongside P-002.7. It cites the producer contract
  `scheduler-baseline-marker/v1` and defines:
  * the claim-assigned, active-residual, and indeterminate classification;
  * the start-record and epoch rule;
  * indeterminate precedence;
  * the admission outcomes (admitted, claim-assigned waiting, active residual).
* Ship Step 3 applies the contract. Ship Step 4.1 writes the start record.
* All of this is gated by a new registry capability, `features.scheduler_baseline_claim`.
  It defaults to `false`, so existing workspaces keep P-002.7 behavior unchanged.
* Fixture proof (tests) backs acceptance (1) and (2).

### Option C: Defer R1 entirely

Option C is justified by finding 4. The operator directed staging R1, though, and the
closure keeps R1 open so upstream consumption can replace the substitution.

## Trade-off Comparison

| Criterion | A | B | C |
|---|---|---|---|
| Satisfies R1 acceptance (1)(2) | yes | yes | no |
| Single versioned consumer contract | yes | yes | no |
| Blast radius on generic workspaces | high | low (opt-in flag) | none |
| Fits one shipment under the 2-hour rule | no | yes (7 tasks) | n/a |
| Preserves the P-002.7 byte-stable block | at risk | yes (separate block) | yes |

## Decision

* **D1 — Scope: Option B.** Wave terminology maps as follows. In autoharness, "wave 1" is the
  initial Step 3 ready-queue admission. `ready_1 = { t in queued or claim-assigned : every
  dependency of t is terminal_success }`. Claim-assigned members with unfinished dependencies are
  reported as `claim-assigned waiting`. The status tokens `WAVE_NO_PROGRESS` (detail
  `active residual`) and `WAVE_CLAIM_STATE_INDETERMINATE` are shared verbatim with backlogit, so
  the two consumers cannot drift.
* **D2 — Priority: high, not critical.** The blocking claim is superseded by the
  `2026-10-07T06:31:36Z` substitution attestation (finding 4). The shipment is still sequenced
  after `211-S` as the operator directed. That matches the release-cut guidance: R1 ships in the
  follow-up release after P1, P3, and P7.
* **D3 — L3 topology `pre_claim` marker check: DEFERRED** (P-021 C1, captured as a new stash
  entry). Reasons:
  1. `ClaimShipment` writes the marker at claim time, so a `pre_claim` phase has no marker for
     the shipment being claimed. Marker consumption is a post-claim concern.
  2. 074-DL assigns L3 to the attestation predicate (C), not to marker consumption, and makes it
     contingent on `A592FC1C`.
  3. Width isolation: Python gate work is a different domain from the template contract.
  4. Acceptance (1)–(3) are satisfiable without it.
* **D4 — Start record.** Under the capability, Ship Step 4.1 appends `WORK_STARTED: <S>` once
  per start epoch, idempotently: it re-reads before appending. The epoch rule is copied from the
  backlogit convention into P-002.8 so both consumers share it.
* **D5 — Residual action and crash resume.** Classification is identical to backlogit. In
  autoharness, an active residual halts with `WAVE_NO_PROGRESS` (detail `active residual`) at
  Step 3. There is one carve-out: under the Ship Crash-Resumption Protocol, the
  operator-confirmed restore of a `ship`-owned checkpoint is the operator's disposition of the
  single residual whose ID equals the checkpoint's recorded in-flight task. That member is
  reported as `active residual (operator-resumed)` and admitted. Any other residual still halts.
  `WAVE_CLAIM_STATE_INDETERMINATE` always takes precedence.
* **D6 — Capability gate.** `features.scheduler_baseline_claim` is added to
  `schemas/backlog-tool-registry.schema.json` (boolean, default `false`). It is also added to the
  backlogit registry template and the dogfood registry as `false`, with an opt-in comment. When
  the flag is false or absent, Step 3 and Step 4.1 behave exactly as today and P-002.7 governs.
  A workspace whose installed backlogit writes the marker (backlogit after `154-S`) opts in.
* **D7 — Fixture proof is test-side.** JSON fixtures plus a reference evaluator under `tests/`
  encode the P-002.8 decision table. Contract-text tests assert that the policy and the Ship
  template carry the contract version, rule IDs, and tokens. No `src/` production module is
  added.
* **D8 — Cross-workspace follow-up (P-017, not harvestable here).** After the follow-up
  release is installed:
  * backlogit Ship Step 4.0 cites `P-002.8 marker_contract_version: 1`;
  * the operator alone may post a refreshed `CONDITION_B_ATTESTED` on `154-S` that cites the
    release and the fixture proof, replacing the substitution. No agent may originate it.

## Rejected Alternatives

* **Option A.** Disproportionate and backlogit-specific. A future template adoption of P-002.6
  is not requested and is not pursued.
* **Option C.** It contradicts the operator directive and leaves the substitution permanent.
* **Auto-detect the marker capability from the backlogit version.** Rejected for now because it
  adds CLI detection scope. The opt-in flag is sufficient and fails closed.
* **Restate the backlogit producer predicate in P-002.8.** Rejected because it violates single
  sourcing. P-002.8 cites `scheduler-baseline-marker/v1` and adds only the consumer rules.

## Unresolved Questions

* None blocking. If backlogit later exposes the item event stream through MCP, raw
  `logs/<id>.jsonl` reads can be replaced. Until then P-002.8 requires a scoped P-012
  declaration for raw log reads, mirroring backlogit.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Flag enabled on a backend that does not write the marker, so every claimed member reads as a residual and Ship halts | Fail-closed halt, not silent mis-admission. The flag defaults to `false`, and its documentation names the minimum producer contract. |
| The P-002.7 byte-stable block is disturbed | P-002.8 lives in its own `P-002.8:BEGIN/END` block. The plan forbids edits inside the P-002.7 block. |
| Merge conflicts with 208-S, 210-S, and 211-S on the shared Ship and policy files and the manifest | Rebase onto the merged predecessors and anchor by heading and marker, not line number. |
| Divergence from backlogit Step 4.0 | Shared verbatim tokens, a contract version, and a cross-workspace citation follow-up |

## Stash Traceability

* `21F8C04A`: consumed by this deliberation and the plan
  `docs/plans/2026-10-08-r1-claim-marker-consumption-plan.md`.
* `F2D11D61`: paired carryover-doc entry. It stays live for P2, P4, P5, and P6.
* New stash: L3 topology `pre_claim` deferral (D3).
