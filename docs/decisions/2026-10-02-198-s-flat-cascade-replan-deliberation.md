---
title: "Re-plan 198-S / 192-F close-evidence capture onto the 201-S flat-cascade contract"
description: "Amendment to 035-DL (D-A1..D-A6). Shipment 198-S was planned against the withdrawn backlogit 1.10.x linked-deliberation cascade sets. This deliberation records the decision to adopt the 201-S / 195-F contract (038-DL D2, D3a, D4a) for the cascade-close command, the evidence record, and the closure-evidence gate, and it records the dag-root disposition for 198-S."
topic: "Stash 1263B218 — DEFERRED SCOPE EXPANSION: align 198-S with 201-S flat-cascade semantics"
depth: "standard"
decision_status: "decided"
promoted_to: "plan"
source_stash: 1263B218
amends_deliberation: 035-DL
constrained_by:
  - "038-DL D2 (flat postcondition sets)"
  - "038-DL D3a (disposition set, planner, one archiver, two layers)"
  - "038-DL D4a (engine-semantics gate, same surface, re-probe halts)"
linked_artifacts:
  - "docs/decisions/2026-09-27-close-evidence-frontmatter-context-tier-staging-deliberation.md"
  - "docs/decisions/2026-09-29-backlogit-1-11-cascade-linked-deliberation-alignment-deliberation.md"
  - "docs/plans/2026-09-27-cascade-close-evidence-capture-plan.md"
  - "docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md"
  - "src/autoharness/gates/shipment_closure.py"
tags:
  - "P-015"
  - "P-021"
  - "cascade-close"
  - "close-evidence"
  - "re-plan"
---

# Re-plan 198-S / 192-F onto the 201-S flat-cascade contract

## Problem Frame

Shipment `198-S` (feature `192-F`, tasks `192.001-T`..`192.010-T`) adds the
`autoharness shipment cascade-close` command, a committed close-evidence record,
and a stricter `closure-evidence` gate. It was planned and reviewed on
2026-09-27 against the backlogit 1.10.x cascade contract. Under that contract
`validated_linked_deliberations(S)` was part of both `allowed_ids` and
`required_ids`. backlogit 1.11.x withdrew that behavior. `201-S` / `195-F`
(deliberation `038-DL`, plan `docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md`)
has since realigned P-015, the shipment-reconcile skill, the Ship agent,
operational-closure, and `src/autoharness/gates/shipment_closure.py` to flat
semantics. It is shipped and closed on `main` (`654b143d`).

Stash `1263B218` is a P-021 `DEFERRED SCOPE EXPANSION`. It requires 198-S to be
deliberated and re-planned before it is claimed (P-021 C6). It lists six
required alignment items. This document is non-interactive. Every decision below
is already settled by `038-DL` D2, D3a, or D4a, or by the 201-S plan. No new
design is introduced.

## Research Findings

### The 201-S contract as merged on `main` (`654b143d`)

Verified by reading `src/autoharness/gates/shipment_closure.py`:

| Stash citation | On `main` | Signature / shape |
|---|---|---|
| `assess_cascade_engine_semantics` | present (L669) | `(probed_version: object, *, probe_surface: object, invocation_surface: object, probed_commit: object = None) -> EngineSemanticsDecision`. It never raises. |
| `EngineSemanticsDecision` | present (L578) | frozen: `verdict`, `reason`, `probed_version`, `minor_line`, `probe_surface`, `probed_commit` |
| `EngineSemanticsVerdict` | present (L570) | `VERIFIED`, `UNVERIFIED`; every UNVERIFIED reason starts `ENGINE_SEMANTICS_UNVERIFIED:` |
| `VERIFIED_CASCADE_ENGINE_MINOR_LINES` | present | `frozenset({(1, 11)})` |
| `select_close_path(classifier, engine)` | present (L747) | `(ClosePathDecision, EngineSemanticsDecision) -> tuple[ClosePath, str]`; 2×2 table plus `CLOSE_PATH_SELECTION_INVALID_INPUT`. It never raises. |
| `classify_shipment_close_path` | present (L381), unchanged | `(manifest_items, workspace_backlog_dir) -> ClosePathDecision` |
| `compute_linked_deliberation_disposition` | present (L1546) | `(manifest_items, shipment_id, workspace_backlog_dir, *, engine: EngineSemanticsDecision, stash_path=None) -> LinkedDeliberationDispositionPlan`. It is read-only and never raises. |
| `LinkedDeliberationDispositionPlan` | present (L899) | `shipment_id`, `engine`, `dispositions`, `unresolved_references`, `read_failures`, `planning_error` |
| `LinkedDeliberationDisposition` | present (L861) | `deliberation_id`, `outcome`, `reason_code`, `link_kinds`, `linking_member_ids`, `records[{path, declared_status, sha256}]`, `declared_status`, `referrer_ids`, `path` |
| `LinkedDeliberationOutcome` | present (L799) | closed enum of 8 values; planned form `PLANNED_ARCHIVE = "archive"` |
| `closure_scope(S)` | **private only**: `_closure_scope_ids(manifest_ids, shipment_id)` (L1276) | `items(S) ∪ {S}` |
| `allowed_ids` / `required_ids` helpers | **not present as functions** | defined in prose: the module docstring, P-015 D2, and shipment-reconcile Cascade Close Sub-Procedure step 3 |

Mismatches against the stash wording. None needs a design decision:

* **M1.** No public `closure_scope`, `allowed_ids`, or `required_ids` function
  exists. The stash cites them as set definitions, not as callables. 198-S
  computes the flat sets locally in its pure evaluator, from its own pre-close
  snapshot (INV-P2). A parity test pins `allowed_ids` to `_closure_scope_ids`.
  Production code does not import the private helper, and 198-S does not promote
  it to a public API. Promoting it would change the 201-S module surface, which is
  outside this re-plan (P-021 C1).
* **M2.** `assess_cascade_engine_semantics` also needs `invocation_surface`.
  The command invokes backlogit only through the CLI, so it probes on the CLI and
  records `probe_surface: "cli"` and `invocation_surface: "cli"`.
* **M3.** The CLI probe `backlogit version --no-update-check --format json` returns
  `{"version": "1.11.0", "commit": "131577c", ...}` (live, 2026-10-02). The commit
  is a short hash. It is recorded raw and compared raw, as the skill does.
* **M4.** The stash says "probed version". The dataclass field is
  `probed_version`. It also carries `minor_line`, which the evidence records.
* **M5.** The `compute_linked_deliberation_disposition` docstring still says
  that it "has no runtime caller". 206-S wired the skill step since then. 198-S
  calls it **read-only**, which is consistent with that docstring. Refreshing the
  docstring is out of scope.

### Settled design sources

* **038-DL D2:** `allowed_ids(S) = closure_scope(S)`.
  `required_ids(S) = {S} ∪ qualifying feature members ∪ {x ∈ items(S): x not truly archived pre-close}`.
  Linked deliberations are in neither set. A disposition-set deliberation that
  appears in `archived_ids`, or that the cascade modifies, is engine drift.
* **038-DL D3a:** this decision supplies:
  * the disposition set (every explicit member, H10 exclusions);
  * the pure planner;
  * the eight outcomes and the reason codes;
  * the engine gate, under which an UNVERIFIED engine mutates nothing;
  * **two layers:** the close-path gate is evaluated before disposition, and
    INV-12 is a separately sanctioned post-gate mutation with its own
    invariance check;
  * **one archiver:** the skill's Linked-Deliberation Disposition step is the
    only path that archives a disposition-set deliberation.
* **038-DL D4a:** this decision supplies:
  * released builds only;
  * the probe runs on the same surface that the close path invokes;
  * `select_close_path` is the single composition point;
  * a pre-invocation re-probe failure or difference **halts, non-mutating**. It
    never substitutes SAFE_CLOSE for a CASCADE verdict.
* **Topology (`src/autoharness/gates/topology.py` `_predecessor_source`):**
  explicit `blocks` predecessors are checked before the `dag-root` label. An
  explicit edge therefore always yields `explicit` provenance, and the label is
  inert while the edge exists.

## Options Evaluated

### Option A: Adopt the 201-S contract in every affected 198-S unit (chosen)

Rewrite A1, A2, A3b, A3, A4, A5, A6, and A7 so they consume the merged
functions and the flat sets. Add one small unit for the CLI engine probe.

### Option B: Ship 198-S as planned (rejected)

The validator, evaluator, and fixtures would freeze `validated_linked_deliberations(S)`
into `allowed_ids` and `required_ids`. On every verified 1.11.x close with a live
linked deliberation, the missing-required check would fail, which is the 190-S
halt. Under 1.11.x the command would also run the cascade with no
engine-semantics gate. The command would contradict the shipped P-015 contract
and the skill it implements.

### Option C: Re-open the 198-S design, for example by having the command archive deliberations (rejected)

The command could execute the INV-12 disposition itself. That would create a
second archiver, which 038-DL D3a forbids ("one archiver"). It would also add a
new destructive operation inside the command, which is new design that the
P-021 C6 re-plan scope does not authorize.

## Decision

Adopt Option A. Each stash item maps to a settled source:

* **R1 — `engine_semantics` in the evidence (item 1; D4a).**
  * `pre_close.engine_semantics` records:
    * `verdict` and `reason`;
    * `probed_version`, `minor_line`, and `probed_commit`;
    * `probe_surface` and `invocation_surface`.
  * The record comes from `assess_cascade_engine_semantics`, applied to a CLI
    probe that the command runs through the same resolved absolute binary it
    later invokes (new unit A2a).
  * A probe that fails, times out, or does not parse is passed as `None`, so the
    result is `UNVERIFIED` and never a halt.
  * Released builds only, as the function enforces.
* **R2 — Close-path selection (item 2; D4a).**
  * `pre_close.close_path_selection{selected_close_path, reason}` records the
    result of `select_close_path(classifier, engine)`.
  * The A1 validator keys on the **selected** close path:
    * It accepts a `safe_close` record whose `classifier_verdict` is `CASCADE`
      exactly when `engine_semantics.verdict` is `UNVERIFIED`.
    * It rebuilds the two decisions from the record, re-runs
      `assess_cascade_engine_semantics` and `select_close_path`, and rejects
      any record whose recorded verdict, selected path, or reason disagrees.
* **R3 — No cascade without the gate (item 3; D4a).**
  * `cascade-close` invokes `shipment ship` only when the selected path is
    `CASCADE`. Any other selection writes the verdict record and exits 3 with
    nothing invoked. That is fail-closed to SAFE_CLOSE outside the verified line.
  * Pre-invocation revalidation re-probes on the same surface and compares the
    raw `version`, `commit`, `probe_surface`, and verdict. Any difference or
    re-probe failure exits 4 (halt, non-mutating) and never substitutes
    SAFE_CLOSE.
  * Plan-review cycle 1 (R1): when a `--classify-only` record that selected
    `cascade` exists, the mutating run treats it as the Step 0(c) record and
    compares the fresh classifier verdict, engine probe (verdict, raw version
    and commit, binary hash), selection, and disposition snapshot against it.
    Any difference exits 4 and leaves the record byte-identical. The mutating
    run never writes a `safe_close` record over a `cascade`-selected one. This
    is the D4a "re-probe difference halts" rule applied to the Step 0(c)
    record, not new design.
* **R4 — Flat sets (item 4; D2).**
  * The A3b evaluator computes `allowed_ids = items(S) ∪ {S}`.
  * It computes `required_ids = {S} ∪ qualifying feature members ∪ {x ∈ items(S): declared status in the pre-close snapshot is not exactly archived}`.
    Both sets range over every manifest item regardless of `artifact_type`.
  * No linked-deliberation term appears in either set.
  * A disposition-set deliberation in `archived_ids` fails the
    unexpected-artifact check and is also labelled `linked_deliberation_drift`.
  * A post-cascade re-collection of the disposition snapshot that differs from
    the pre-close snapshot (IDs, link kinds, linking members, declared status,
    record paths, SHA-256, or unresolved references) fails as
    `linked_deliberation_drift`.
  * The H10 carve-out holds: a deliberation that is an explicit manifest member
    is an ordinary `allowed_ids` member.
* **R5 — Disposition in the evidence (item 5; D3a, U5a).**
  * `pre_close.linked_deliberation_disposition` records the planner's output
    verbatim: the planned outcome per deliberation, `reason_code`, `path`,
    `link_kinds`, `linking_member_ids`, `referrer_ids`, and `records[]`, plus
    `unresolved_references`, `read_failures`, and `planning_error`. The planner
    is `compute_linked_deliberation_disposition(manifest, S, backlog_dir, engine=<R1 decision>)`.
  * This record is also the disposition snapshot that R4 compares against.
  * Every `retained_*` outcome is non-halting for the command, the validator,
    and the gate. The gate does not surface them (re-plan cycle-1 R2, see
    R5a); the skill's disposition report carries the
    `stranded_linked_deliberation` advisory.
  * The command never archives a deliberation (one archiver). The executed
    outcomes, including `archived`, are recorded by the skill's
    Linked-Deliberation Disposition report in the closure artifact. That step
    takes `engine_semantics` and the disposition snapshot from this evidence
    record as its Step 0(c) inputs and never recomputes them.
  * A `planning_error` at pre-close means the disposition snapshot cannot be
    established. The command exits 2 and writes no record. This is the same
    fail-closed rule as the existing "observation set cannot be established".
* **R5a — Gate layering (consequence of D3a "two layers"; revised by
  plan-review cycle 1, R2).**
  * The A4 write-time SAFE_CLOSE observation-set re-check does **not** cover
    disposition-set deliberations at all. The observation set never contains
    one, the gate has no planned-`archive` exemption, and it emits no
    `stranded_linked_deliberation` warning.
  * Rationale: the skill's Linked-Deliberation Disposition step is the sole
    archiver (one archiver, U6b) and re-plans after the close from live
    referrers. The executed outcome can therefore legitimately differ from the
    pre-close planned outcome, and any gate exemption or check keyed on the
    pre-close plan mis-fires. INV-12's verify-after-each, reported in the
    closure artifact, owns every disposition mutation.
  * Engine drift on those deliberations (item 4) is detected at close time by
    the A3b post-close re-collection, which is the authoritative point.
    Gate-level stranded-advisory surfacing stays in the deferred stash scope
    `3B43CE5A` / `D79EA53A`.
  * The pre-close disposition snapshot stays in the evidence record (item 5)
    for A3b drift detection.
  * The earlier R5a text (exempt planned `archive`, re-check every other
    deliberation entry) is withdrawn.
* **R6 — `dag-root` hygiene (item 6; D8a, topology).** See the next section.
* **R7 — Decomposition consequence.**
  * The CLI probe needs the A3a runner. The order therefore becomes A1 → A1b →
    A3a → A2a → A2 → A3b → A3 → A4 → A5 → A6, and A3 → A7.
  * A2a is new and needs a new task at harvest.
  * This reorders work inside the plan. It is not a design change.

### `dag-root` disposition (item 6)

Recommendation: **remove the `dag-root` label from 198-S.**

* 198-S has the explicit edge `198-S blocks-on 201-S`. The operator added it on
  2026-09-29 (038-DL D8a). Under the Orchestrator and Ship sequencing contract,
  `explicit` derives only from explicit `blocks` edges, and `declared_root`
  derives only from a recorded `dag-root` label. `topology._predecessor_source`
  checks explicit predecessors first. While the edge exists, the label has no
  effect.
* The stale label is not harmless. If the edge were ever removed, the label
  would silently turn 198-S back into a declared root and bypass the 201-S
  ordering that the operator chose. The operator ruling of 2026-09-27 that
  declared the root (035-DL ruling 1) was made before 201-S existed, and D8a
  superseded it.
* Applying or removing `dag-root` is an operator or Stage act on backlog data.
  Ship never does it. This chunk records the recommendation and does not mutate
  the label. The removal is a one-line, review-gated backlog edit for the Stage
  session that re-harvests 198-S, or for the operator. The 198-S body text that
  says "operator-declared dag-root" is refreshed in the same edit.

## Rejected Alternatives

* **Ship 198-S as planned (Option B).** Rejected. It contradicts the shipped
  P-015 contract and reproduces the 190-S halt.
* **The command executes the INV-12 disposition (Option C).** Rejected. It
  violates 038-DL D3a "one archiver" and adds new destructive scope.
* **Keep `dag-root` and document it.** Rejected in favor of removal. The label
  is inert today, but it is a latent bypass of the operator-chosen edge.

## Unresolved Questions

* None requires `REPLAN_DECISION_REQUIRED`. Every item is settled by 038-DL D2,
  D3a, or D4a, by the 201-S plan, or by the topology contract.
* **Procedural (P-021 C6):** the revised 198-S plan must be re-reviewed before
  198-S is claimed. The 2026-09-27 PASS predates this re-plan.
* **Procedural:** the 198-S task set must be re-harvested. The plan section
  "Re-plan amendment (2026-10-02, stash 1263B218)" holds the delta: the new task
  A2a, changed tasks, and dependency edges.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| A future 1.11.x patch changes cascade semantics inside the verified line | The post-cascade disposition re-collection and the unexpected-artifact check fail as `linked_deliberation_drift` (exit 5) |
| The probe runs on a different build than the invocation | The probe and the invocation use the same resolved absolute binary, whose hash is checked right before the spawn (A3 step 6) |
| A disposition-set deliberation is mis-archived by the disposition step | INV-12 verify-after-each owns that mutation and halts with P-005. Its report is part of the same closure artifact. The A4 gate does not re-check it (plan-review cycle 1, R2) |
| The verified engine line is widened later | `8928EC67` must be deliberated first (038-DL D8a). The validator re-runs `assess_cascade_engine_semantics`, so a widened constant is picked up without changing the record shape |
