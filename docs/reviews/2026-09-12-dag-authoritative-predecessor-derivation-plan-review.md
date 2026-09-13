---
title: "Plan review — DAG-authoritative predecessor derivation (cycle 2)"
description: "Multi-persona adversarial plan review of docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md revision 2, gating harvest."
doc_type: review
source: docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md
date: 2026-09-12
plan_path: docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md
plan_revision: 2
review_cycle: 2
decision: PASS
---

# Plan Review — DAG-Authoritative Predecessor Derivation (cycle 2)

Review cycles used: **2 of 3**.

This review supersedes the cycle-1 review of plan revision 1 (commit `4c09e50b`).
That cycle-1 verdict was **overturned by the operator to BLOCKED** with eleven
numbered findings. Cycle 2 reviews **plan revision 2**, which was rewritten to
resolve them. Section "Operator Findings Verification" below checks each of the
eleven individually; the persona passes below are an independent re-review, not a
re-statement of that checklist.

## Dispatch Capability and Declared Degradation

```text
dispatch_mode: single-agent-declared-degradation
TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass
TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass
TOOL_DEGRADED: agent-engram (unified_search / impact_analysis) — declared fallback: file-based grep/view over src/ and tests/
TOOL_DEGRADED: agent-intercom — declared fallback: no phase broadcast; operator visibility via session report only
TOOL_DEGRADED: graphtor-docs — declared fallback: direct read of docs/compound/ and docs/decisions/
```

No subagent dispatch surface and no alternate model route are available in this
session, so this is a **declared** degradation, not a silent one (P-012). Every
persona below was still applied inline against its rubric — **no persona was
skipped**, and no finding was downgraded because of the degradation. Reviewer
route: `claude-opus-5`/`anthropic`/`high` (same as caller; a genuine cross-model
adversarial pass was not available).

Claims in this review that depend on current source behaviour were verified by
direct read of `src/autoharness/gates/topology.py`,
`tests/test_gates_topology.py`, `.github/skills/operational-closure/SKILL.md`,
`.github/instructions/workflows.instructions.md`, and the live `.backlogit`
records — not from memory of the prior cycle.

## Severity Scale

| Sev | Meaning | Gate effect |
|---|---|---|
| P0 | Plan cannot be executed as written; would produce incorrect or unsafe behaviour | BLOCK |
| P1 | Material defect; execution would produce a known-wrong intermediate state or violate a policy | BLOCK |
| P2 | Should be corrected; does not prevent execution | Record + handle |
| P3 | Advisory / stylistic | Record |

## Persona Findings

### Constitution Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | Principle II (Test-First, NON-NEGOTIABLE): satisfied, and materially stronger than revision 1. 165.001-T/165.004-T author expectations before 165.002-T/165.005-T implement, dependency edges enforce the ordering, and revision 2 now distinguishes **characterization** tests (C1–C4, describing behaviour that already exists) from genuinely **new** expectations (N1–N6), so no impossible RED observation is demanded. | OK |
| — | Principle VIII (Explicit Safety Modes for Elevated Risk): satisfied without a new config switch. The four-state contract is fail-closed by default (`unsequenced` blocks), and the only escape is an explicit, recorded, per-shipment declaration. | OK |
| — | Principle V (Structured Observability): `predecessor_source` on **both** blocked and passed payloads (F1) gives every claim decision a machine-readable provenance value. | OK |
| — | Principle VI (Single Responsibility): derivation (165.002-T), audit (165.003-T), and advisory parity (165.005-T) are separated; the closure-evidence naming defect is descoped entirely rather than conflated. | OK |
| — | Principle IV (CLI Workspace Containment): revision 1's open P2 here is **moot** — it was raised against the new config read path, and revision 2 has no config surface at all (D2). The root declaration is read from a backlog record the reader already opens. | RESOLVED by design change |
| — | P-001 role separation: the plan assigns no implementation to Stage; every code-touching task is a Ship-executed backlog item. | OK |

### Python Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| P2-1 | **Genesis probe must consider archived history.** `genesis` is defined as "no shipped-terminal shipment exists in the workspace". If the probe reads only live queue records, archiving shipped history would silently re-enter genesis and convert a correct block into an unearned pass. This is a fail-*open* direction and therefore the highest-risk detail in the contract. | **Resolved in-cycle.** 165.001-T gains assertion N5b (a workspace whose only shipped history is archived is NOT genesis), and 165.002-T now requires the probe to consult `archived_status`/`archived_record_present` alongside live status. |
| P2-2 | **`labels` parsing must fail closed.** The reader at `topology.py` L560-600 already applies `_tuple_of_str` fail-closed discipline to `custom_fields.items` and `dependencies`, raising `BacklogUnavailableError` on a present-but-wrong-shaped block. A new `labels` parse that silently degrades to "no declaration" would be inconsistent with that established rule, and would turn a malformed record into an unexplained block. | **Resolved in-cycle.** 165.002-T now names the pattern, the line range, and the required exception. |
| — | No numeric comparison survives on the claim path in any of the four states. Given three prior defects in this file all originated in the *direction* of a numeric predicate, removing the predicate rather than re-tuning it is the correct fix. | OK |
| — | `_prior_shipment_id` is explicitly **retained** (re-homed into the audit path by 165.003-T) rather than deleted, so 165.002-T cannot leave a dangling reference. | OK |
| P3-1 | The shared derivation/closure helper's module location is unspecified — `topology.py` or a new module. | Advisory. 165.005-T now requires the executor to *state* the choice in the task record; either is acceptable. |
| P3-3 | Expected-failure tests should be **strict** xfail so that an early accidental pass fails the suite rather than silently reporting as expected. | Already required by 165.001-T. No change needed. |

### Scope Boundary Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | The closure producer/consumer naming defect is fully removed from 165-F/173-S: 165.007-T is archived and off the manifest, and the defect is captured as stash `FD0CCB42`. The plan does not weaken the closure gate anywhere to compensate. | OK |
| — | Scope fences are explicit and match the operator's boundary list: `86498B64` (explicit branch contracts), `9B582824` (cost epic), `97B28746`/`50434138` (follow-ups) remain separate; `58A85283` excluded. | OK |
| — | Revision 1's "optional follow-up outside 173-S" escape hatch in 165.008-T is removed. Template and installed-mirror work is now mandatory and split into two explicit dependent tasks (165.008-T → 165.010-T), both **inside** 173-S. | OK |
| — | The `.github/instructions/workflows.instructions.md` mapping is removed. Verified by direct search: that file contains no `pre_claim`, `PREDECESSOR_`, or `dag-readiness` token, so it genuinely needs no change. | OK |
| P2-5 | The shipment `size_composition.members` rollup still lists archived, descoped `165.007-T`, because the rollup derives members from `parent_id` children rather than from the manifest. The manifest itself (`custom_fields.items`) is correct. | **Externalized**, not absorbed: stash `9AA34143` (low). Fixing it would require modifying backlogit, which is outside this shipment's scope. Recorded here so a future reader does not "reconcile" the discrepancy by re-adding a descoped task. |
| — | No source, template, or config file was modified by Stage in this cycle; only planning artifacts and backlog records. | OK |

### Learnings Researcher

| Sev | Finding | Disposition |
|---|---|---|
| — | All six directed learnings are mapped to concrete plan constraints in the revision-2 prior-learnings table, and each maps to a *testable* constraint rather than a slogan: directional numeric-fallback → no numeric predicate on the claim path at all; explicit queued+blocks sequencing → the declared-root/explicit-edge contract; closure producer/consumer composed-state-machine testing → the total P1–P7 parity matrix; immutable schema mirror versioning → moot, since D2 removes the schema surface; lifecycle-gate-before-close ordering → audit phase is advisory and non-authorizing; non-vacuous DAG ordering tests → the fixture gate in 165.001-T. | OK |
| — | The non-vacuity requirement is the right defence for this change specifically: a parity matrix that silently constructed states no fixture could reach would "pass" while proving nothing. | OK |
| P3-2 | `audit_sequencing` as a phase name sits alongside `pre_claim`/`post_claim`/`lifecycle`/`ambient`, which are lifecycle *positions* rather than activities. | Advisory only. Accepted: the phase is registered in `VALID_PHASES` only, never in `SCOPED_PHASES`, so it cannot acquire an active-target requirement and cannot disturb `lifecycle`'s invariant. |

### Architecture Strategist

| Sev | Finding | Disposition |
|---|---|---|
| — | **The central revision-2 correction is sound.** Legacy behaviour blocked a shipment only when a numerically lower *unshipped* shipment existed; a genuine DAG root passed. A flat `block` mode therefore could never be "legacy compatibility" — it is strictly more restrictive and deadlocks every root permanently. The four-state contract restores the property that actually mattered (roots are claimable) while removing the property that caused the defects (numeric inference). | OK — resolves operator finding 1 |
| — | Removing the config key (D2) removes an entire coupled surface: root schema, a new immutable versioned schema, `schema_contracts.py`, `templates/harness-config.yaml.tmpl`, install/tune preservation, dogfood config, and parity tests. Simplifying the design away from the surface is strictly preferable to adding a task to manage it (operator finding 7 offered both; the simpler branch is taken). | OK |
| P2-3 | **One snapshot, one answer.** `genesis` is a workspace-level fact. If `pre_claim` and `dag-readiness` probe it independently, they can observe different snapshots mid-mutation and re-diverge on exactly the dimension the shared helper exists to unify — the original defect reproduced one abstraction level up. | **Resolved in-cycle.** 165.005-T now requires the workspace-level fact to be computed once inside the shared helper and handed to both gates. |
| P2-4 | The `dag-root` label has **no mechanical enforcement**: any actor who can edit a shipment record can declare a root and bypass the unsequenced block. | **Accepted with handling**, and this is a deliberate contract boundary rather than an oversight. Mitigations: (a) the declaration is durable, diffable, and attributable in the record; (b) `predecessor_source: declared_root` makes every such claim auditable after the fact; (c) the agent contract (165.008-T/165.010-T) prohibits self-declaration to escape a block. Mechanical enforcement would require a backlogit-side permission model — outside this shipment. Fenced and recorded rather than silently assumed away. |
| — | F3's single-shared-helper requirement is correctly stated as **review-blocking** rather than advisory. A parallel reimplementation is the architectural root cause of the original divergence. | OK |

### Agent-Native Parity Reviewer

| Sev | Finding | Disposition |
|---|---|---|
| — | Template sources (165.008-T) and installed dogfood mirrors (165.010-T) are both mandatory members of 173-S, with an explicit dependency edge and a recorded parity check. Revision 1's drift risk (template updated, installed mirror deferred) is closed. | OK |
| — | The two agent surfaces named are the ones that actually carry claim-path guidance; no speculative file was added to pad parity. | OK |
| — | Documentation (165.009-T) cross-references only committed artifacts. | OK |

### Security / Safety Lens

| Sev | Finding | Disposition |
|---|---|---|
| — | The default posture is fail-closed: an edge-less shipment in a workspace with shipping history blocks. Every pass state is either explicit (edges), declared (recorded), or genuinely bootstrap (no history anywhere). | OK |
| — | `pre_claim` remains the sole claim authority in all four states. `dag-readiness` is explicitly non-authorizing and now excludes policy-blocked shipments from `ready_set`/`next_eligible`, so it cannot advertise something `pre_claim` will refuse (operator finding 4). | OK |
| — | The closure-evidence check is **not** weakened anywhere to achieve parity; parity is reached by making the advisory side model the same requirement. Explicitly prohibited in 165.005-T. | OK |
| — | The D6 bootstrap disposition for `173-S` is bounded: one shipment, one claim, audited, recorded in the shipment record, and granting no broader force authority. | OK |
| — | `--force` semantics are unchanged by this plan; no new bypass is introduced. | OK |

## Operator Findings Verification (cycle-1 BLOCK, eleven findings)

| # | Operator finding | Resolution | Where |
|---|---|---|---|
| 1 | Migration mode deadlock — `block` is not legacy behaviour | Replaced with the four-state declared-root contract; roots remain representable *and* claimable; blocks name two self-service remedies; no fail-open | Decision D1/D3; plan §3; 165.001-T, 165.002-T, 165.003-T |
| 2 | 173-S bootstrap | Durable, shipment-specific disposition recorded with five explicit bounds, authorized by the operator directive | Decision D6; `173-S` record; plan H6 |
| 3 | Test ordering / impossible RED | Legacy `ImplicitNumericPredecessorTests` re-expression made **atomic** with the removal in 165.002-T (per-case disposition for all five, bulk deletion forbidden); characterization vs new expectations separated so every task ends green | 165.001-T (C1–C4 vs N1–N6), 165.002-T; plan §4 |
| 4 | Advisory parity | Total P1–P7 matrix across all four states; policy-blocked shipments excluded from `ready_set`/`next_eligible`; parity required in both directions; `pre_claim` remains sole authority | 165.004-T, 165.005-T; decision D5 |
| 5 | Closure issue scope | Removed from 165-F/173-S. 165.007-T archived and off the manifest; captured as `DEFERRED SCOPE EXPANSION` stash `FD0CCB42` with full source refs and a clean duplicate scan. Closure gate not weakened; authoring a competing closure artifact explicitly prohibited (the real defect is a naming-contract drift, not a missing file) | Decision D4; `FD0CCB42`; `.backlogit/archive/165.007-T.md` |
| 6 | Source provenance | All references to the uncommitted bug doc removed, including the ellipsized path; `bug_source`/`supersedes_recommendation_in` frontmatter removed; historical context preserved as prose; plan and decision are self-contained against committed sources only. The untracked operator file was neither modified nor committed | Decision + plan revision 2 |
| 7 | Config/schema coupling | **Simplified away.** No config key, therefore no root-schema change, no new versioned schema mirror, no `schema_contracts.py` change, no template/install/tune/dogfood config surface, no parity tests for them. Validated empirically that `labels` persists on a shipment record | Decision D2 |
| 8 | Template/installed parity | No optional follow-up. Split into mandatory dependent tasks 165.008-T → 165.010-T, both in 173-S. Incorrect `workflows.instructions.md` mapping removed after verifying the file carries no relevant token | 165.008-T, 165.010-T |
| 9 | Placeholder hygiene | No literal unfenced double-brace tokens remain in plan or task prose | plan, all 165.* records |
| 10 | Learnings incorporated | All six mapped to concrete, testable constraints | plan §2 prior-learnings table |
| 11 | Scope boundaries | Restated and honoured | decision scope fences; plan §2 "Surfaces deliberately NOT touched" |

## Backlog Integrity Verification

Verified directly against `.backlogit` after all mutations and a successful
`backlogit_sync_index`:

* **Manifest of `173-S`** (order): `165-F`, `165.001-T`, `165.002-T`,
  `165.003-T`, `165.004-T`, `165.005-T`, `165.006-T`, `165.008-T`,
  `165.009-T`, `165.010-T` — covering feature first, then tasks in dependency
  order. `165.007-T` absent.
* **Dependency edges** (acyclic, consistent with manifest order):
  `165.001-T → 165.002-T`; `165.002-T → {165.003-T, 165.004-T, 165.006-T}`;
  `165.004-T → 165.005-T`; `{165.005-T, 165.006-T} → {165.008-T, 165.009-T}`;
  `165.008-T → 165.010-T`.
* **Sizing**: all nine tasks carry both `size` and `complexity`. No task exceeds
  the 2-hour bound at `size: M`; the two `complexity: high` tasks
  (165.002-T, 165.005-T) are de-risked by a preceding test-authoring task
  (165.001-T and 165.004-T respectively) rather than split further, since
  splitting them would break the atomicity the plan requires.
  Recorded values: 165.001-T M/medium, 165.002-T M/high, 165.003-T M/medium,
  165.004-T S/medium, 165.005-T M/high, 165.006-T S/low, 165.008-T S/medium,
  165.009-T S/low, 165.010-T S/medium.
* **No orphaned references**: 165.007-T's dependency edge was removed before
  archival; its archived record carries the forward reference to `FD0CCB42`;
  165.010-T fills the vacated slot as a genuine new member rather than a
  renumbering.

## Merged Finding Counts

| Severity | Count | Status |
|---|---|---|
| P0 | **0** | — |
| P1 | **0** | — |
| P2 | 5 | 3 resolved in-cycle (P2-1, P2-2, P2-3); 1 accepted with recorded handling (P2-4); 1 externalized to stash `9AA34143` (P2-5) |
| P3 | 3 | Advisory; P3-1 requires a recorded choice at execution, P3-2 accepted, P3-3 already satisfied |

## Gate Decision

**decision: PASS**

Zero P0 and zero P1 findings. All five P2 findings have an explicit disposition —
none is deferred silently. All eleven operator findings from the cycle-1 BLOCK are
resolved in plan revision 2 and the corresponding backlog records.

Harvest may proceed. `173-S` is staging-PR ready, contingent on Ship using the
single audited `pre_claim --force` authorized by decision D6 for `173-S` only.
