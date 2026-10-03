---
title: "Automatic, fail-closed CASCADE close-evidence capture"
description: "Replace the agent-discretionary CASCADE close audit trail with an autoharness-owned command that captures the fresh classifier verdict, the out-of-manifest snapshot, and the raw bounded, redacted backlogit close output into a committed evidence record, plus a closure-evidence gate that refuses CASCADE closure without that record."
doc_type: plan
status: replanned-reviewed
review_record: docs/reviews/2026-09-27-cascade-close-evidence-capture-plan-review.md
created: 2026-09-27
amended: 2026-10-02
source_stash: 008F3BCF
replan_stash: 1263B218
source_deliberation: docs/decisions/2026-09-27-close-evidence-frontmatter-context-tier-staging-deliberation.md
replan_deliberation: docs/decisions/2026-10-02-198-s-flat-cascade-replan-deliberation.md
replan_contract: "201-S / 195-F (038-DL D2, D3a, D4a; docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md), verified on main at 654b143d"
requires_plan_rereview: "no - re-reviewed 2026-10-02 (cycles 1-2), PASS_WITH_FOLLOWUPS; see review record"
provenance: "175-S / 167-F, PR #458 (merge 985e3990), closure PR #459, close commit 5cc5371a, condition operator-accepts-175s-cascade-evidence-deviation"
requires_plan_hardening: "yes"
post_review_operator_amendment: "2026-09-27T22:50-07:00 - D-A1..D-A6 (including the review-cycle-1 D-A3 SAFE_CLOSE fail-closed amendment) operator-confirmed; shipment 198-S is an operator-declared dag-root. No design change; the PASS review is not reopened. See section Operator Rulings (2026-09-27T22:50-07:00). Superseded by the 2026-10-02 re-plan: dag-root removal recommended (198-S now has an explicit blocks edge to 201-S)."
---

# Automatic, fail-closed CASCADE close-evidence capture

## Re-plan amendment (2026-10-02, stash 1263B218)

This plan was reviewed on 2026-09-27 against the backlogit 1.10.x cascade
contract. In that contract, `validated_linked_deliberations(S)` belonged to both
`allowed_ids` and `required_ids`, and no engine-semantics gate existed.
`201-S` / `195-F` has since shipped the flat 1.11.x contract on `main`
(`654b143d`). This amendment re-plans every affected unit onto that contract. The
decisions are recorded in
`docs/decisions/2026-10-02-198-s-flat-cascade-replan-deliberation.md` (amends
035-DL). They come from 038-DL D2, D3a, and D4a, and the amendment introduces no
new design. Where this section and any unit text written before 2026-10-02
disagree, this section and the revised unit text win.

**Merged contract consumed** (`src/autoharness/gates/shipment_closure.py`):

* `assess_cascade_engine_semantics(probed_version, *, probe_surface, invocation_surface, probed_commit=None) -> EngineSemanticsDecision`;
* `select_close_path(classifier: ClosePathDecision, engine: EngineSemanticsDecision) -> tuple[ClosePath, str]`;
* `compute_linked_deliberation_disposition(manifest_items, shipment_id, workspace_backlog_dir, *, engine, stash_path=None) -> LinkedDeliberationDispositionPlan`;
* `classify_shipment_close_path`, unchanged;
* `closure_scope(S)`, which exists only as the private `_closure_scope_ids`. No
  public `allowed_ids` / `required_ids` helper exists. This plan computes the
  flat sets locally in A3b and pins them by a parity test (M1 in the
  deliberation).

**Private-name rule (re-plan cycle-2 C2-4).** One rule governs every private
`shipment_closure` name this plan uses:

* `_closure_scope_ids` and `_is_engine_inert` are never imported by
  production code. A3b re-derives the flat sets locally, and its parity test
  pins them to these two helpers (M1).
* `_RELEASE_VERSION_PATTERN` (A2a), `_scan_backlog` and
  `_enumerate_descendants` (A2b), `_read_artifact_record` (A2b, A4b), and
  `_check_path_containment` (A4b) are reused rather than restated. Each is
  imported **lazily**, inside
  the function that uses it, and never at module top level in `cli.py` or in
  any `shipment_close/` module. An upstream rename therefore cannot break
  `cli.py` import or any unrelated command. It fails only the call that
  needs the name.
* The A3b parity test module, which is test-only, also pins that each of
  these five names exists with the signature (or, for the pattern, the
  type) this plan relies on. A rename fails the tests, not the CLI import.

**Alignment items to units:**

| # | Stash 1263B218 item | Settled by | Units |
|---|---|---|---|
| 1 | Evidence gains `engine_semantics` from `assess_cascade_engine_semantics` on the invocation surface (CLI) | D4a | A2a (new), A1, A2 |
| 2 | Close path from `select_close_path`. A `safe_close` record may carry `classifier_verdict: CASCADE` when the engine is UNVERIFIED | D4a | A1, A2, A4 |
| 3 | `cascade-close` never runs the cascade without the engine gate. It fails closed to SAFE_CLOSE (exit 3). A re-probe difference, or any difference from a `cascade`-selected `--classify-only` record, halts (exit 4) and never overwrites that record | D4a | A3, A1b, A5 |
| 4 | Flat `allowed_ids` / `required_ids`. A disposition-set deliberation in `archived_ids`, or modified, is engine drift | D2 | A3b, A3c, A3, A1c |
| 5 | Evidence records `linked_deliberation_disposition` from the planner. `retained_*` never halts. The command never archives. The A4 gate does not re-check disposition-set deliberations (re-plan cycle-1 R2), except on a `safe_close` record with an UNVERIFIED engine, where no archive is planned (re-plan cycle-2 C2-1) | D3a, U5a | A2, A2b, A1c, A4b, A5 |
| 6 | Stale `dag-root` on 198-S | D8a, topology | Recommendation only: remove the label (see the deliberation) |

**Removed from the plan:** every linked-deliberation term in `allowed_ids` and
`required_ids`, in fixtures, and in tests. This includes the A2 "linked
deliberations of each qualifying feature" collection and the record key
`pre_close.linked_deliberations`. The replacement is the disposition snapshot,
which the planner produces over every explicit manifest member with the H10
exclusions.

**Harvest delta for 198-S** (Stage re-harvest; this chunk does not mutate the
backlog):

| Unit | Task | Change |
|---|---|---|
| A1 | `192.001-T` | **Changed.** Record shape, path, and selection consistency (R1, R2, R4). Disposition and set-term rules move to A1c (cycle-1 R4). Owns `redact` and the `*_to_record` / `*_from_record` helpers (cycle-1 R6, R8). Size M / low. **Superseded by Copilot PR #481 T8:** the ten helpers moved to A1d/A1e/A1f (`192.017-T`..`192.019-T`); A1 is size S |
| A1c | *new* | **New task (cycle-1 R4).** Disposition and set-term rules (R5, D2), with pre-mutation outcomes only and two-way engine/outcome consistency (cycle-1 R13). S / low |
| A1b | `192.002-T` | **Changed (minor).** Existing-record check hands a `cascade`-selected `pre_close` record to A3 (cycle-1 R1). Uses the A1 `redact`; `engine_semantics.reason` and `close_path_selection.reason` are not redacted (cycle-1 R6). Owns the `EXIT_*` constants in `shipment_close/__init__.py` (cycle-1 R15). M / medium |
| A3a | `192.004-T` | **Changed.** Now precedes A2. Bare-name `cli.binary`, basename match, probe `cwd` in an empty, workspace-contained, Git-ignored probe directory that is never deleted automatically (cycle-1 R3; Copilot PR #481 T3). S / medium |
| A2a | *new* | **New task.** CLI engine-semantics probe (`shipment_close/engine_probe.py`). S / low |
| A2b | *new* | **New task (cycle-1 R4).** Safe-close observation set (`shipment_close/observation.py`). It holds no disposition-set deliberation (cycle-1 R2) unless the engine is UNVERIFIED (cycle-2 C2-1). A missing member is recorded, not raised (cycle-2 C2-2). S / medium |
| A2 | `192.003-T` | **Changed.** Planner-based disposition snapshot, `select_close_path`, observation set from A2b. M / medium |
| A3b | `192.005-T` | **Changed.** Parser, flat sets, and INV-10 (cycle-1 R4 moved drift to A3c). M / medium |
| A3c | *new* | **New task (cycle-1 R4).** `linked_deliberation_drift` evaluator. S / medium |
| A3 | `192.006-T` | **Changed.** Engine re-probe in revalidation, the `--classify-only` record hand-off (cycle-1 R1), exit 3 and exit 4 semantics, post-close re-collection. CLI wiring moves to A3d. M / medium |
| A3d | *new* | **New task (cycle-1 R4).** `cli.py` wiring, USAGE, and `--json` output. S / low |
| A4 | `192.007-T` | **Changed.** Selected-path validation and the `close_evidence` checks. The observation-set re-check moves to A4b. M / medium |
| A4b | *new* | **New task (cycle-1 R4).** SAFE_CLOSE observation-set re-check. No planned-`archive` exemption and no `stranded_linked_deliberation` warning (cycle-1 R2). Disposition-set deliberation records are re-checked only on an UNVERIFIED-engine record (cycle-2 C2-1). S / medium |
| A5 | `192.008-T` | **Changed.** Step 0(c) points to the command. The disposition step takes its inputs from the evidence. The mutating-mode exit-3 routing row is revised (cycle-1 R1). M / low |
| A6 | `192.009-T` | **Changed (minor).** The pointer names the engine gate and the disposition step. S / low |
| A7 | `192.010-T` | **Changed (minor).** Docs gain the new fields and exit semantics. S / low |

No unit is removed. Six tasks are new: A1c, A2a, A2b, A3c, A3d, and A4b.
The re-harvest sets each task's `dependencies` to exactly the following
(re-plan cycle-1 R5):

| Task | Unit | Dependencies after re-harvest | Change from the current backlog |
|---|---|---|---|
| `192.001-T` | A1 | none | unchanged |
| *new* | A1c | `192.001-T` | new |
| `192.002-T` | A1b | A1c | was `192.001-T` |
| `192.004-T` | A3a | `192.002-T` | **remove `192.003-T`**, add `192.002-T` |
| *new* | A2a | `192.004-T` | new |
| *new* | A2b | A1c | new |
| `192.003-T` | A2 | A2a, A2b | was `192.002-T` |
| `192.005-T` | A3b | `192.003-T` | was `192.004-T` |
| *new* | A3c | `192.005-T` | new |
| `192.006-T` | A3 | A3c | was `192.005-T` |
| *new* | A3d | `192.006-T` | new |
| `192.007-T` | A4 | A3d | was `192.006-T` |
| *new* | A4b | `192.007-T` | new |
| `192.008-T` | A5 | A4b | was `192.007-T` |
| `192.009-T` | A6 | `192.008-T` | unchanged |
| `192.010-T` | A7 | A3d | was `192.006-T` |

* The existing edge `192.004-T depends on 192.003-T` (verified in
  `.backlogit/queue/192.004-T.md`) **must be removed** before `192.003-T`
  gains its dependency on A2a, which depends on `192.004-T`. Keeping both
  would form the cycle `192.003-T` → A2a → `192.004-T` → `192.003-T`.
* Every new task gets `parent_id: 192-F`, the size and complexity above, and
  `harness-surface:harness-architect` (A1c, A2a, A2b, A3c, A3d, A4b are all
  code-bearing).
* Every new task is added to 198-S `custom_fields.items`, and the full
  manifest is rewritten in this dependency order (covering feature first,
  17 items): `192-F`, `192.001-T` (A1), A1c, `192.002-T` (A1b), `192.004-T`
  (A3a), A2a, A2b, `192.003-T` (A2), `192.005-T` (A3b), A3c, `192.006-T`
  (A3), A3d, `192.007-T` (A4), A4b, `192.008-T` (A5), `192.009-T` (A6),
  `192.010-T` (A7). The current manifest lists `192.003-T` before
  `192.004-T`, so the existing order changes too. Every item appears after
  each of its dependencies in the table above.
* The rows above, each unit's **Depends on** line, and the edge list in
  `## Dependency Graph` stated the same 16 task edges at re-harvest. The
  Copilot PR #481 cycle-1 amendment below supersedes this table, the
  17-item manifest, and the one-PR list: its table is the current one (22
  task edges, 23 manifest items).
* `192.007-T`, A4b, `192.008-T`, and `192.009-T` carry the one-PR constraint
  (extended by the Copilot PR #481 amendment to A5b, A5c, and A6b).

**Review state.** The plan-review PASS below predates this amendment. Under
P-021 C6, this plan was re-reviewed on 2026-10-02 (cycles 1-2) with verdict
PASS_WITH_FOLLOWUPS and no open P0/P1; the follow-up is the Stage re-harvest
above, before 198-S is claimed. Plan hardening is extended with INV-P8 and
INV-P9 (see Plan Hardening).

## Copilot cycle 1 amendment (PR #481, 2026-10-02)

Copilot's first review of the 198-S re-plan PR (#481) raised ten threads
(T1-T10) on one contract surface. All ten are fixed in this plan, in the
task bodies, and in the backlog; none is deferred. The dispositions are in
the review record, section "Copilot cycle 1 (PR #481)". Where this section
and earlier text disagree, this section and the revised unit text win. In
Copilot cycle 2 (thread `PRRT_kwDORzpWpM6oh0SP`) the unit sections under
`## Implementation Units` (including the new A1d, A1e, A1f, A5b, A5c, and
A6b sections), the granularity table, and `## Dependency Graph` were brought
into agreement with this section, so they no longer disagree.

* **T1, T2, T5 (tuple comparison).** `redact()` returns `(text,
  redaction_applied)`, so every redaction-neutrality check is now written
  `redact(x)[0] == x` (A1 validator, A1b, A2a sanitizer, A2 reason check).
* **T3, T4 (workspace containment, constitution IV).** The engine-probe
  `cwd` is a fresh, empty, trust-checked directory under the Git-ignored
  `.autoharness/gates/cascade-close/probe/`, inside the workspace, and the
  command never deletes it (removal is an operator action, constitution
  VII). See A3a and A2a. The runtime-proof scratch workspace likewise moves
  under the Git-ignored `.proof-scratch/`.
* **T6 (`run_id` ownership).** A `pre_close` record written by a
  `--classify-only` run is replaced by a different run only through the A1b
  **pre_close takeover**: an atomic compare-and-swap that requires the
  expected prior `run_id`. A3 step 4 uses it only after step 3's exact-match
  check passes. See A1b and A3.
* **T7 (A7 ordering).** A7 documents the gate's new `failed_check` values
  and `warnings[]`, so it depends on A4b (`192.016-T`), not on A3d.
* **T8, T9, T10 (granularity, Primitive 2: fewer than 3 files, 5
  functions, 4 test scenarios).**
  * A1 kept `build_evidence_path`, `validate_evidence_record`, and `redact`.
    Its ten serializer functions moved into three new codec units: A1d
    (`declared_status_*`, `observation_entry_*`; `192.017-T`), A1e
    (`engine_semantics_*`, `close_path_selection_*`; `192.018-T`), and A1f
    (`disposition_plan_*`; `192.019-T`). Each has at most four functions,
    two files, and three test scenarios. A1 drops to three scenarios and
    size S.
  * A5 split into A5 (shipment-reconcile, `192.008-T`), A5b
    (operational-closure, `192.020-T`), and A5c (doc assertions,
    `192.021-T`). A6 split into A6 (Ship template and mirror, `192.009-T`)
    and A6b (pointer assertions, `192.022-T`).
  * **Rendered-surface triple.** A template, its installed mirror, and the
    mirror's checksum line in `.autoharness/harness-manifest.yaml` must
    change in one commit. Existing tests compare template with mirror, and
    `tests/test_crash_resumption_protocol.py` and
    `tests/test_checkpoint_payload_contract.py` assert the `_ship.agent.md`
    mirror checksum. A5, A5b, and A6 therefore each edit that atomic triple
    and nothing else, and their new assertions are separate one-file test
    tasks (A5c, A6b). A split that separated the triple would leave a task
    whose verifiable outcome is a failing suite, which Primitive 2's atomic
    milestone rule forbids. The residual (three files) is recorded in the
    review record.

The backlog now sets each task's `dependencies` to exactly the following.
This table, each unit's **Depends on** line, and the edge list in
`## Dependency Graph` state the same 22 task edges:

| Task | Unit | Dependencies | Change in Copilot cycle 1 |
|---|---|---|---|
| `192.001-T` | A1 | none | unchanged (size M → S) |
| `192.017-T` | A1d | `192.001-T` | new (T8) |
| `192.018-T` | A1e | `192.017-T` | new (T8) |
| `192.019-T` | A1f | `192.018-T` | new (T8) |
| `192.011-T` | A1c | `192.019-T` | was `192.001-T` (T8) |
| `192.002-T` | A1b | `192.011-T` | unchanged |
| `192.004-T` | A3a | `192.002-T` | unchanged |
| `192.012-T` | A2a | `192.004-T` | unchanged |
| `192.013-T` | A2b | `192.011-T` | unchanged |
| `192.003-T` | A2 | `192.012-T`, `192.013-T` | unchanged |
| `192.005-T` | A3b | `192.003-T` | unchanged |
| `192.014-T` | A3c | `192.005-T` | unchanged |
| `192.006-T` | A3 | `192.014-T` | unchanged |
| `192.015-T` | A3d | `192.006-T` | unchanged |
| `192.007-T` | A4 | `192.015-T` | unchanged |
| `192.016-T` | A4b | `192.007-T` | unchanged |
| `192.008-T` | A5 | `192.016-T` | unchanged (scope narrowed, T9) |
| `192.020-T` | A5b | `192.008-T` | new (T9) |
| `192.021-T` | A5c | `192.020-T` | new (T9) |
| `192.009-T` | A6 | `192.021-T` | was `192.008-T` (T9/T10) |
| `192.022-T` | A6b | `192.009-T` | new (T10) |
| `192.010-T` | A7 | `192.016-T` | was `192.015-T` (T7) |

* The 198-S manifest is rewritten in this dependency order (covering
  feature first, 23 items): `192-F`, `192.001-T` (A1), `192.017-T` (A1d),
  `192.018-T` (A1e), `192.019-T` (A1f), `192.011-T` (A1c), `192.002-T`
  (A1b), `192.004-T` (A3a), `192.012-T` (A2a), `192.013-T` (A2b),
  `192.003-T` (A2), `192.005-T` (A3b), `192.014-T` (A3c), `192.006-T` (A3),
  `192.015-T` (A3d), `192.007-T` (A4), `192.016-T` (A4b), `192.008-T` (A5),
  `192.020-T` (A5b), `192.021-T` (A5c), `192.009-T` (A6), `192.022-T`
  (A6b), `192.010-T` (A7).
* A6 depends on A5c, not on A5, so that the three `harness-manifest.yaml`
  checksum edits (A5, A5b, A6) stay serial and A6 follows the whole A5
  family.
* A4, A4b, A5, A5b, A5c, A6, and A6b (`192.007-T`, `192.016-T`,
  `192.008-T`, `192.020-T`, `192.021-T`, `192.009-T`, `192.022-T`) carry the
  one-PR constraint (label `release-unit-a4-a6`).
* The new code-bearing tasks A1d, A1e, and A1f carry
  `harness-surface:harness-architect`. A5b, A5c, and A6b carry
  `harness-surface:none`.

## Problem Frame

P-015 permits the destructive `backlogit shipment ship` cascade only when
`classify_shipment_close_path` (`src/autoharness/gates/shipment_closure.py`) returns
`CASCADE`. The Cascade Close Sub-Procedure in
`templates/skills/shipment-reconcile/SKILL.md.tmpl` (mirrored at
`.github/skills/shipment-reconcile/SKILL.md`) tells the agent to do five things:

* re-run the classifier immediately before the call;
* fingerprint the out-of-manifest descendants;
* invoke the cascade;
* check `returned_ids`, the two-set `allowed_ids` / `required_ids` gate, `parent_id`
  preservation, and baseline invariance;
* write a report.

All of it is prose. During the 175-S close (commit `5cc5371a`), Ship kept none of
the raw evidence. Closure PR #459 halted `BLOCKED` and needed an operator deviation.
The evidence cannot be reproduced after a cascade, because the cascade mutates the
very `status` fields the snapshot records. Nothing in the write-time
`closure-evidence` gate (`src/autoharness/cli.py`,
`src/autoharness/gates/closure_contract.py`) knows which close path ran, so a
missing record is never refused.

## Requirements Trace

| # | Requirement (stash `008F3BCF` / deliberation D-A*) | Unit(s) |
|---|---|---|
| R1 | Record the pre-close classifier verdict automatically, from a fresh re-run | A2 |
| R2 | Record the out-of-manifest snapshot (IDs, locations, content hashes, declared statuses) and the linked-deliberation **disposition snapshot** before the close (re-plan 2026-10-02: the disposition snapshot replaces the 1.10.x qualifying-feature linked-deliberation collection) | A2, A2b |
| R3 | Record the raw close stdout, stderr, and exit code, bounded and redacted | A1b, A3a, A3 |
| R4 | The evidence file is written before and after the close; if the pre-close write fails, nothing is invoked | A1b, A2, A3 |
| R4a | An interrupted, concurrent, or ambiguous close is detectable and never silently retried (hardening H-B1/H-B2, review cycle 1) | A1b, A3 |
| R5 | The closure-evidence gate refuses a closure whose close path lacks a valid record | A1, A1d, A1e, A1f, A1c, A4, A4b |
| R6 | SAFE_CLOSE (D-A3, amended by review cycle 1 — Stage-recommended, pending operator confirmation): verdict record via `--classify-only`, required by the gate | A2, A2b, A3d, A4, A4b |
| R7 | Surfaces updated: shipment-reconcile (template and mirror), operational-closure (template and mirror), Ship agent (template and mirror), docs | A5, A5b, A5c, A6, A6b, A7 |
| R8 | Upstream half as a portable, non-blocking backlogit request (D-A1) | A7 |
| R9 | Retention and location (D-A2): committed at `docs/closure/evidence/`, and closure discovery is unaffected | A1, A4 |
| R10 | Re-plan item 1 (D4a): the evidence records `engine_semantics` from `assess_cascade_engine_semantics`, probed on the CLI surface the command invokes, for released builds only | A2a, A1, A2 |
| R11 | Re-plan items 2-3 (D4a): the close path comes from `select_close_path`. No cascade runs unless it selects `CASCADE`. A re-probe difference halts with no mutation | A1, A2, A3, A3d, A4, A5 |
| R12 | Re-plan item 4 (D2): flat `allowed_ids` / `required_ids`. A disposition-set deliberation that is archived or modified is engine drift | A3b, A3c, A3 |
| R13 | Re-plan item 5 (D3a): the evidence records the planned `linked_deliberation_disposition`. `retained_*` is non-halting. The command never archives a deliberation | A2, A1c, A5 |

## Implementation Units

Harness-surface labels: code-bearing units carry `harness-surface:harness-architect`
(P-004 per-task harness generation applies), and docs- or template-only units carry
`harness-surface:none`.

Layering (review cycle 1, AS-F07): the read-only, gate-facing contract and validator
live in `src/autoharness/gates/cascade_evidence.py`. Every write and every subprocess
lives in the new command package `src/autoharness/shipment_close/`, which the gate
never imports. New modules must not restate a closure filename (`*closure.md`,
`post-merge-closure`) outside the contract-derived form, so
`tests/test_closure_contract_nondrift.py` stays green.

Granularity (re-plan cycle-1 R4, 2-hour rule): every unit touches at most two
files (a module and its test), except where noted, and has at most four test
scenarios. A scenario is one table-driven test whose rows are cases.

| Unit | Files | Test scenarios | Size / complexity |
|---|---|---|---|
| A1 | 2 | 3 | S / low |
| A1d | 2 | 3 | S / low |
| A1e | 2 | 3 | S / low |
| A1f | 2 | 2 | S / low |
| A1c | 2 | 4 | S / low |
| A1b | 2, plus `shipment_close/__init__.py`, which holds only the `EXIT_*` constants (re-plan cycle-1 R15) | 4 | M / medium |
| A3a | 2 | 3 | S / medium |
| A2a | 2 | 4 | S / low |
| A2b | 2 | 4 | S / medium |
| A2 | 2 | 4 | M / medium |
| A3b | 2 | 4 | M / medium |
| A3c | 2 | 4 | S / medium |
| A3 | 2 | 4 | M / medium |
| A3d | 2 | 3 | S / low |
| A4 | 2 | 4 | M / medium |
| A4b | 2 | 2 | S / medium |
| A5 | 1 rendered-surface triple (shipment-reconcile template, mirror, and manifest checksum line); no new test file | 0 (existing doc tests stay green) | M / low |
| A5b | 1 rendered-surface triple (operational-closure template, mirror, and manifest checksum line); no new test file | 0 (existing doc tests stay green) | S / low |
| A5c | 1 test file | 3 | S / low |
| A6 | 1 rendered-surface triple (Ship template, mirror, and manifest checksum line); no new test file | 0 (existing Ship tests stay green) | S / low |
| A6b | 1 test file | 2 | XS / low |
| A7 | 2 | 2 checks (no new test) | S / low |

### A1 — Evidence record contract: shape, path, and selection consistency (read-only)

Re-plan cycle-1 R4 split the former A1 into this unit and A1c (disposition and
set-term rules), so each satisfies the 2-hour rule. Copilot PR #481 T8 then
moved the ten record-serialization functions into three codec units, A1d,
A1e, and A1f, because A1 held three public functions plus ten serializer
functions (Primitive 2: fewer than 3 files, 5 functions, 4 test scenarios).

* **Goal:** the single read-only evidence contract and validator that the
  A4/A4b gate and the `shipment_close` command both use.
* **Functions (3 public):** `build_evidence_path`,
  `validate_evidence_record`, and `redact`, plus private validator helpers.
  The `*_to_record` / `*_from_record` codec is **not** this unit (A1d, A1e,
  A1f).
* **Files:** `src/autoharness/gates/cascade_evidence.py` (new), and
  `tests/test_cascade_evidence_contract.py` (new).
* **Changes:**
  * `EVIDENCE_SCHEMA_VERSION = 1`.
  * `build_evidence_path(workspace_root, shipment_id, feature_id)` builds
    `docs/closure/evidence/{S}-{F}-close-evidence.json` (one record per pair, for
    either close path), using `closure_contract.validate_closure_id` and
    `assert_path_within_workspace`.
  * `validate_evidence_record(record: Mapping[str, object], *, shipment_id: str,
    feature_id: str, close_path: Literal["cascade", "safe_close"]) -> list[str]`
    is the single validator. The gate and the command both use it.
    `close_path` is the **selected** close path (re-plan R2), not the classifier
    verdict.
  * **Selection consistency (re-plan R1/R2; D4a).** For both close paths:
    * The validator rebuilds an `EngineSemanticsDecision` by calling
      `shipment_closure.assess_cascade_engine_semantics(probed_version, probe_surface=..., invocation_surface=..., probed_commit=...)`
      on the recorded raw `engine_semantics` inputs. The recorded `verdict`,
      `reason`, and `minor_line` must equal the result, so a hand-edited
      `VERIFIED` fails.
    * It rebuilds a `ClosePathDecision` from `classifier_verdict` and
      `classifier_reason`. Record values are `CASCADE` / `SAFE_CLOSE`, mapped to
      `ClosePath.CASCADE` / `ClosePath.SAFE_CLOSE`.
    * It calls `shipment_closure.select_close_path(classifier, engine)`. The
      recorded `close_path_selection.selected_close_path` and `reason` must equal
      the result.
    * `invocation_surface` must be `"cli"`, because the command invokes only
      through the CLI.
    * **Sanitized inputs, unredacted outputs (re-plan cycle-1 R6).** The
      validator asserts `redact(x)[0] == x` for `engine_semantics.probed_version`,
      `engine_semantics.probed_commit`, `engine_semantics.reason`, and
      `close_path_selection.reason` (each when non-null). It compares the
      text element of the `(text, redaction_applied)` tuple, never the tuple
      itself (Copilot PR #481 T1). Any difference rejects the record. These four fields are never redacted on output:
      A2a sanitizes the probe inputs instead, so the recorded values are the
      exact inputs and outputs of the merged functions, and re-assessment
      reproduces them.
  * **Path fields (re-plan cycle-1 R12).** Every record path field
    (`observation_set[].path`, `linked_deliberation_disposition.dispositions[].path`,
    `dispositions[].records[].path`, and `read_failures[].path`) must be a
    relative POSIX path under the backlog root: its first segment is
    `.backlog` or `.backlogit` (one root for every path in a record), and it
    has no `..` segment, no leading `/` or `\`, no drive prefix, and no UNC
    prefix. The check is textual and runs before anything else reads the
    path. `path: null` is accepted only on a `retained_read_error`
    disposition and a `read_failures[]` entry, where the planner reported a
    path outside the backlog root and A2 kept only the `reason_code`, and on
    an `observation_set` entry with `location: missing` (re-plan cycle-2
    C2-2). Any other value rejects the record.
  * **Redaction function (re-plan cycle-1 R6).** `redact(text) -> tuple[str,
    bool]` is defined here, not in `shipment_close/`, because the validator
    needs it and the gate never imports the command package. A1b's
    `StreamCapture` and every A1b free-text redaction call this one function.
    Its pattern set is the one listed under A1b. Because it returns a tuple,
    every "is this value redaction-neutral?" check in this plan is written
    `redact(x)[0] == x` (or `redact(x)[0] != x` for the negation). A bare
    `redact(x) == x` compares a tuple with a string and is always false
    (Copilot PR #481 T1, T2, T5).
  * **Record serialization codec (re-plan cycle-1 R8; Copilot PR #481 T8).**
    This module owns the pure `*_to_record` / `*_from_record` pairs, and A2a,
    A2, A2b, A3, A3b, and A3c use them both to write the record and to
    compare a fresh value against it. No other module encodes a record
    field. This unit does **not** implement them: `declared_status_*` and
    `observation_entry_*` are A1d (`192.017-T`), `engine_semantics_*` and
    `close_path_selection_*` are A1e (`192.018-T`), and `disposition_plan_*`
    is A1f (`192.019-T`). This unit's validator reads the plain JSON record
    fields directly; A1d and A1e later route the well-typed and
    selection-consistency checks through their decoders, so one decoder
    exists per field.
  * `cascade` requires `phase: post_close`,
    `close_path_selection.selected_close_path: cascade`,
    `classifier_verdict: CASCADE`, `engine_semantics.verdict: VERIFIED`, and
    `postcondition_verdict: pass`, **and** internal consistency (AS-F11):
    `invocation.exit_code == 0`, `timed_out: false`, `mutation_state: completed`,
    no `parse_error`, empty `parsed_result.returned_ids`, empty
    `unexpected_archived`, `missing_required`, `linked_deliberation_drift`, and
    `failures[]`, and `parent_id_preserved`, `baseline_invariant`,
    `disposition_byte_identical`, and `shipment_archived_shipped` all `true`.
    A `pass` verdict that contradicts any of these is rejected.
  * `safe_close` requires `phase: pre_close` and
    `close_path_selection.selected_close_path: safe_close`. `classifier_verdict`
    is `SAFE_CLOSE`, **or** it is `CASCADE` together with
    `engine_semantics.verdict: UNVERIFIED`. That is the `select_close_path` row
    "CASCADE × UNVERIFIED → SAFE_CLOSE", and the selection-consistency check
    enforces it. A `safe_close` record with `classifier_verdict: CASCADE` and a
    `VERIFIED` engine is rejected, because `select_close_path` would have
    selected `cascade`.
  * Both require the pair to match and every required key to be present and
    well-typed.
  * The disposition and set-term rules are A1c. They extend this same
    `validate_evidence_record`, so the gate and the command keep one
    validator.
  * `CascadeEvidenceError(Exception)` is the single error type. This
    read-only gate module defines no exit codes. The command's `EXIT_*`
    constants live in `shipment_close/__init__.py` (A1b; re-plan cycle-1
    R15).
* **Record shape:**
  * `schema_version`, `shipment_id`, `feature_id`, `merge_commit_sha`, `run_id`
    (uuid4 hex, fixed by the owning run), and `phase: pre_close | invoking | post_close`;
  * `tool{binary_path, binary_sha256, version_excerpt}` (path and hash from
    A3a; `version_excerpt` from the single A2a probe spawn, re-plan cycle-1
    R7);
  * `pre_close{classifier_verdict, classifier_reason, qualifying_feature_ids, engine_semantics{verdict, reason, probed_version, minor_line, probed_commit, probe_surface, invocation_surface}, close_path_selection{selected_close_path, reason}, shipment_record{location, sha256, declared_status}, manifest_members[{id, artifact_type, location, sha256, declared_status, parent_id}], out_of_manifest_descendants[{id, location, sha256, declared_status}], linked_deliberation_disposition{dispositions[{deliberation_id, outcome, reason_code, path, link_kinds[], linking_member_ids[], referrer_ids[], declared_status, records[{path, declared_status, sha256}]}], unresolved_references[{id, reason_code}],   read_failures[{path, reason_code}], planning_error}, observation_set[{id, path, location, sha256, declared_status}] (selected SAFE_CLOSE only), captured_at}`.
    Every `declared_status` uses the canonical encoding defined in A1d
    (re-plan cycle-1 R8).
    `engine_semantics` mirrors `EngineSemanticsDecision`, plus the
    `invocation_surface` input. There is no probe excerpt in
    `engine_semantics` (re-plan cycle-1 R7).
    `linked_deliberation_disposition` carries four of the six
    `LinkedDeliberationDispositionPlan` fields: `dispositions`,
    `unresolved_references`, `read_failures`, and `planning_error`, with the
    planned outcomes. Each `dispositions[]` entry mirrors
    `LinkedDeliberationDisposition` field for field. The plan's other two
    fields are intentionally omitted (re-plan cycle-1 R14): `shipment_id`
    always equals the top-level `shipment_id` that A2 passes to the planner,
    and `engine` is the A2a decision already recorded as
    `pre_close.engine_semantics` (the in-memory object is not JSON-safe).
    `disposition_plan_to_record` (A1f) drops both, and
    `disposition_plan_from_record(r, *, shipment_id, engine)` restores them
    from those two record fields. It is also the **disposition snapshot**
    that A3c compares against. The observation set contains no
    disposition-set deliberation (re-plan cycle-1 R2), except on a
    `safe_close` record with an UNVERIFIED engine (re-plan cycle-2 C2-1; see
    A1c, A2b, and H-C2). An `observation_set` entry for an expected member
    that is missing at baseline records `location: missing`, `path: null`,
    `sha256: null`, and `declared_status: null` (re-plan cycle-2 C2-2). The
    1.10.x key `linked_deliberations` is removed (re-plan);
  * `invocation{argv_redacted, started_at, finished_at, exit_code, timed_out, mutation_state: none | completed | indeterminate, stdout{total_bytes, total_lines, sha256, capture_truncated, excerpt, redaction_applied}, stderr{...same}}`
    (both excerpts are always persisted, bounded and redacted, on success and on
    failure, because R3 requires the raw close output — AS-F09);
  * `post_close{parsed_result{shipment_status, archived_ids, returned_ids, commit_sha} | parse_error, shipment_record_status, shipment_record_archived_status, allowed_ids, required_ids, unexpected_archived, missing_required, linked_deliberation_drift[], disposition_byte_identical, parent_id_preserved, baseline_invariant, shipment_archived_shipped, postcondition_verdict: pass | fail, failures[]}`.
    `allowed_ids` and `required_ids` are the flat sets (re-plan R4, A3b).
  * Serialization (Principle IX): `json.dumps(sort_keys=True, indent=2,
    ensure_ascii=False)`, LF line endings, one trailing newline, and every ID list
    sorted.
* **Tests (test-first, three scenarios; each scenario is one table-driven test
  whose rows are cases, matching the table-driven precedent in
  `docs/plans/2026-08-31-ship1-v1_5_0-guardrail-contract-restoration-plan.md`
  and `docs/plans/2026-09-27-agent-skill-frontmatter-conformity-plan.md`):**
  1. **Shape and pair table:** a well-formed record for each close path is
     accepted; a missing `post_close` for `cascade`, a mismatched shipment or
     feature ID, an unknown `schema_version`, and a `SAFE_CLOSE` record offered
     for `cascade` (and the reverse) are rejected; a path field that is
     absolute, contains `..`, carries a drive or UNC prefix, or lies outside
     the backlog root is rejected, and `path: null` on a
     `retained_read_error` disposition, or on an `observation_set` entry
     with `location: missing` and a null `sha256`, is accepted (re-plan
     cycle-1 R12; cycle-2 C2-2); two serializations of the same record are
     byte-stable (LF, one trailing newline, sorted ID lists).
  2. **Cascade internal-consistency table (AS-F11):** `postcondition_verdict:
     fail`, a non-zero `exit_code`, a non-empty `linked_deliberation_drift`,
     and `disposition_byte_identical: false` under a `pass` verdict are each
     rejected.
  3. **Selection-consistency table (re-plan R1/R2):** a `safe_close` record
     with `classifier_verdict: CASCADE` and an UNVERIFIED engine
     (`probed_version` `1.10.1` or `1.11.1-rc1`) is **accepted**; the same
     record with a `VERIFIED` engine (`1.11.0`, `cli`/`cli`) is rejected; a
     `cascade` record whose engine is UNVERIFIED is rejected; a hand-edited
     `engine_semantics.verdict: VERIFIED` over `1.10.0` is rejected; a
     `selected_close_path` or reason that disagrees with `select_close_path`
     is rejected; an `invocation_surface` other than `cli` is rejected; a
     `probed_commit` or `close_path_selection.reason` containing `token=...`
     (so `redact(x)[0] != x`) is rejected (re-plan cycle-1 R6).

  Every fixture builds `engine_semantics` by calling
  `assess_cascade_engine_semantics`. No fixture hard-codes a
  `validated_linked_deliberations` set. The former fourth scenario
  (serialization and the `declared_status` date encoding) moved: byte
  stability is now part of scenario 1, and the date encoding is A1d
  scenario 1 (Copilot PR #481 T8).
* **Depends on:** none (first task). **Harness surface:**
  `harness-surface:harness-architect`.
* **Posture:** test-first. **Size:** S (re-plan cycle-1 R4 split it to S;
  R6 and R8 raised it to M; Copilot PR #481 T8 moved the ten serializer
  functions into A1d, A1e, and A1f and returned it to S). **Complexity:**
  low.

### A1d — Evidence record codec: declared_status and observation_entry helpers

* **Goal:** the canonical `declared_status` encoding and the
  observation-set entry codec, split out of A1 by Copilot PR #481 T8.
* **Functions (4):** `declared_status_to_record`,
  `declared_status_from_record`, `observation_entry_to_record`, and
  `observation_entry_from_record`.
* **Files:** `src/autoharness/gates/cascade_evidence.py` (extended), and
  `tests/test_cascade_evidence_codec_status.py` (new).
* **Changes:**
  * **Canonical `declared_status` encoding (re-plan cycle-1 R8).** The same
    encoding covers every other parsed frontmatter scalar the record keeps.
    An exact `str` is stored as the JSON string. Every other value is stored
    as a tagged object `{"type": <tag>, "value": <canonical text or null>}`,
    with the tags `missing` (no `status` key; `value: null`), `null`,
    `bool`, `int`, `float`, `date`, `datetime` (ISO 8601 text), `list` and
    `mapping` (canonical JSON text of the recursively encoded items,
    `sort_keys=True`), and `other` (the type name only). A YAML
    `status: 2026-01-01` is therefore
    `{"type": "date", "value": "2026-01-01"}`, never the string
    `"2026-01-01"`, so it cannot compare equal to a quoted date string.
  * `declared_status_from_record` decodes a record value (an `other` tag
    decodes to an opaque marker that keeps only the type name) and rejects
    an unknown tag or a malformed tagged object with `CascadeEvidenceError`.
    Round trips are stable: `x_to_record(x_from_record(r)) == r` for every
    valid `r`.
  * `observation_entry_*` encode and decode
    `{id, path, location, sha256, declared_status}`. `location` is `queue`,
    `archive`, or `missing`. A `location: missing` entry has `path`,
    `sha256`, and `declared_status` all `null` (re-plan cycle-2 C2-2).
    `declared_status` goes through `declared_status_to_record`.
  * `validate_evidence_record`'s well-typed check decodes every
    `declared_status` field and every `observation_set` entry through these
    helpers, so one decoder exists and a malformed tagged object rejects the
    record.
  * A comparison always compares the `*_to_record` encodings of both sides,
    never a parsed YAML value against JSON.
* **Tests (test-first, three table-driven scenarios):**
  1. **`declared_status` tag table:** an exact `str` encodes as the JSON
     string; each tag (`missing`, `null`, `bool`, `int`, `float`, `date`,
     `datetime`, `list`, `mapping`, `other`) encodes and round-trips; YAML
     `status: 2026-01-01` encodes as `{"type": "date", "value":
     "2026-01-01"}`, round-trips, and does not compare equal to the string
     `"2026-01-01"` (re-plan cycle-1 R8).
  2. **Malformed-tag table:** an unknown tag, a tagged object without
     `value`, and a non-object, non-string value each raise
     `CascadeEvidenceError`, and a record carrying one is rejected by
     `validate_evidence_record`.
  3. **Observation-entry table:** a `queue` entry and a `location: missing`
     entry (null `path`, `sha256`, and `declared_status`) round-trip; two
     serializations of a record carrying both are byte-identical under the
     A1 serialization rule.
* **Depends on:** A1 (`192.001-T`). **Harness surface:**
  `harness-surface:harness-architect`.
* **Posture:** test-first. Pure functions, no I/O. **Size:** S.
  **Complexity:** low.

### A1e — Evidence record codec: engine_semantics and close_path_selection helpers

* **Goal:** the engine-semantics and close-path-selection record codec,
  split out of A1 by Copilot PR #481 T8.
* **Functions (4):** `engine_semantics_to_record`,
  `engine_semantics_from_record`, `close_path_selection_to_record`, and
  `close_path_selection_from_record`.
* **Files:** `src/autoharness/gates/cascade_evidence.py` (extended), and
  `tests/test_cascade_evidence_codec_selection.py` (new).
* **Changes:**
  * `engine_semantics_*` encode an `EngineSemanticsDecision` plus the
    `invocation_surface` input as `{verdict, reason, probed_version,
    minor_line, probed_commit, probe_surface, invocation_surface}`, where
    `minor_line` is `[major, minor]` or `null`. There is no probe excerpt
    (re-plan cycle-1 R7; the probe stdout excerpt is
    `tool.version_excerpt`). No field is redacted (re-plan cycle-1 R6):
    values are stored verbatim, so re-assessment reproduces them.
  * `engine_semantics_from_record` rebuilds the decision fields and
    `invocation_surface`. A missing key, a `minor_line` that is neither
    `null` nor a two-integer list, or an unknown `verdict` raises
    `CascadeEvidenceError`.
  * `close_path_selection_*` encode the `(ClosePath, reason)` result of
    `select_close_path` as `{selected_close_path: cascade | safe_close,
    reason}`. An unknown `selected_close_path` raises
    `CascadeEvidenceError`.
  * A1's selection-consistency check decodes the recorded `engine_semantics`
    and `close_path_selection` through these helpers (one decoder) before it
    re-assesses with `assess_cascade_engine_semantics` and
    `select_close_path`.
  * Round trips are stable, and a comparison always compares `*_to_record`
    encodings.
* **Tests (test-first, three table-driven scenarios):**
  1. **Engine round-trip table:** a `VERIFIED` `1.11.0` `cli`/`cli` decision
     and `UNVERIFIED` decisions (`probed_version` `None`; `1.10.1`), each
     built by `assess_cascade_engine_semantics`, round-trip with
     `minor_line` `[1, 11]` or `null` and every value stored verbatim
     (re-plan cycle-1 R6).
  2. **Close-path round-trip table:** both selections returned by
     `select_close_path` round-trip; an unknown `selected_close_path` raises
     `CascadeEvidenceError`.
  3. **Malformed-engine table:** a missing key, a `minor_line` of length 3
     or of type `str`, and an unknown `verdict` each raise
     `CascadeEvidenceError`, and `validate_evidence_record` rejects a record
     carrying one.
* **Depends on:** A1d (`192.017-T`). **Harness surface:**
  `harness-surface:harness-architect`.
* **Posture:** test-first. Pure functions, no I/O. **Size:** S.
  **Complexity:** low.

### A1f — Evidence record codec: disposition_plan helpers

* **Goal:** the linked-deliberation disposition snapshot codec, split out of
  A1 by Copilot PR #481 T8.
* **Functions (2):** `disposition_plan_to_record` and
  `disposition_plan_from_record`.
* **Files:** `src/autoharness/gates/cascade_evidence.py` (extended), and
  `tests/test_cascade_evidence_codec_disposition.py` (new).
* **Changes:**
  * `disposition_plan_to_record(plan)` encodes four of the six
    `LinkedDeliberationDispositionPlan` fields: `dispositions`,
    `unresolved_references`, `read_failures`, and `planning_error`. Each
    `dispositions[]` entry mirrors `LinkedDeliberationDisposition` field for
    field: `{deliberation_id, outcome, reason_code, path, link_kinds[],
    linking_member_ids[], referrer_ids[], declared_status, records[{path,
    declared_status, sha256}]}`. Every `declared_status` goes through A1d's
    `declared_status_to_record`, and ID lists are sorted.
  * `shipment_id` and `engine` are intentionally dropped (re-plan cycle-1
    R14). `disposition_plan_from_record(r, *, shipment_id, engine)` restores
    them from the top-level `shipment_id` and the decoded
    `pre_close.engine_semantics`.
  * A malformed record (a missing key, an unknown field, or a malformed
    tagged `declared_status`) raises `CascadeEvidenceError`. Round trips are
    stable.
  * The outcome vocabulary and the engine/outcome consistency rules belong
    to the A1c validator (`192.011-T`), not to this codec, which round-trips
    any outcome string.
* **Tests (test-first, two table-driven scenarios):**
  1. **Round-trip table** over plans built from `LinkedDeliberationOutcome`
     values and `PLANNED_ARCHIVE` (`archive`, `already-archived`, and each
     `retained_*` outcome): `to_record` drops `shipment_id` and `engine`;
     `from_record(r, shipment_id=..., engine=...)` restores them; and
     `x_to_record(x_from_record(r)) == r`. No fixture hard-codes a
     `validated_linked_deliberations` set.
  2. **Malformed-plan table:** a missing `dispositions` key, an unknown
     disposition field, and a malformed tagged `declared_status` inside
     `records[]` each raise `CascadeEvidenceError`.
* **Depends on:** A1e (`192.018-T`). **Harness surface:**
  `harness-surface:harness-architect`.
* **Posture:** test-first. Pure functions, no I/O. **Size:** S.
  **Complexity:** low.

### A1c — Evidence record contract: disposition and set-term rules (read-only)

* **Goal:** the disposition and set-term half of the A1 validator (re-plan R5,
  D2, D3a), split out of A1 by re-plan cycle-1 R4.
* **Files:** `src/autoharness/gates/cascade_evidence.py` (extended), and
  `tests/test_cascade_evidence_disposition.py` (new).
* **Changes:** `validate_evidence_record` gains these rules, as private
  helpers it calls:
  * **Disposition (re-plan R5).** `pre_close.linked_deliberation_disposition`
    must be present on both paths. `planning_error` must be `null`, because the
    command never writes a record when the planner fails.
    * Each `outcome` must be a **pre-mutation** outcome (re-plan cycle-1
      R13): the planned `"archive"` (`shipment_closure.PLANNED_ARCHIVE`),
      `"already-archived"` (`LinkedDeliberationOutcome.ALREADY_ARCHIVED`), or
      one of the six `retained_*` values `"retained_read_error"`,
      `"retained_ambiguous"`, `"retained_engine_unverified"`,
      `"retained_live_status"`, `"retained_shared_reference"`, and
      `"retained_description_mention"`. `"archived"`
      (`LinkedDeliberationOutcome.ARCHIVED`) is rejected: only the skill's
      disposition step assigns it, after verify-after-each, and the command
      never archives. Any other value is rejected.
    * `reason_code` must be a non-empty string. Unknown reason codes are
      accepted, because that vocabulary is extensible.
    * A `retained_*` outcome never halts by itself (non-halting). Only the
      engine-consistency rule below can reject one.
    * **Engine/outcome consistency, both ways (D3a; re-plan cycle-1 R13).**
      The planner's INV-12 precedence applies the engine rule after
      `retained_read_error`, `retained_ambiguous`, and `already-archived`,
      and before every other rule. Therefore:
      * under `engine_semantics.verdict: UNVERIFIED`, an outcome must be
        `retained_read_error`, `retained_ambiguous`, `already-archived`, or
        `retained_engine_unverified`. `archive`, `retained_live_status`,
        `retained_shared_reference`, and `retained_description_mention` are
        rejected, because the engine rule decides those deliberations first;
      * under `VERIFIED`, `retained_engine_unverified` is rejected.

      So `retained_engine_unverified` is present if and only if the engine is
      UNVERIFIED, on exactly the deliberations that would otherwise reach
      `archive` or a later retain rule.
  * **No linked-deliberation set terms.** The validator never treats a
    disposition-set ID as a member of `allowed_ids` or `required_ids`. A
    recorded `allowed_ids` or `required_ids` that contains a disposition-set
    deliberation ID is rejected (D2; the H10 explicit-member carve-out does not
    apply, because H10 IDs are excluded from the disposition set).
  * **Deliberations in the observation set (re-plan cycle-1 R2; cycle-2
    C2-1).** An `observation_set` entry whose ID is in the disposition
    snapshot is rejected, with one exception: on a `safe_close` record whose
    `engine_semantics.verdict` is `UNVERIFIED`. There, the observation set
    must contain exactly one entry for each `records[]` path of every
    disposition whose outcome is not `already-archived`, with that
    deliberation's ID and the snapshot's `path` and `sha256`. A missing,
    extra, or mismatched entry is rejected. This exception is safe because
    the outcome rule above forbids a planned `archive` under an UNVERIFIED
    engine, so the disposition step archives nothing. Under a `VERIFIED`
    engine, and on every `cascade` record, the rejection still applies.
* **Tests (test-first, four table-driven scenarios):**
  1. **Outcome and engine-consistency table:** every `retained_*` outcome
     under its matching engine verdict, including `retained_read_error` with
     an unknown `reason_code`, is accepted; `archive` and `already-archived`
     under a VERIFIED engine are accepted; `"archived"` and an unknown
     `outcome` are rejected under either engine; `archive` and
     `retained_live_status` under an UNVERIFIED engine are rejected;
     `retained_engine_unverified` under a VERIFIED engine is rejected
     (re-plan cycle-1 R13).
  2. **Planner-state table:** a missing disposition snapshot and a non-null
     `planning_error` are rejected.
  3. **Set-term table:** a recorded `required_ids` or `allowed_ids` containing
     a disposition-set deliberation ID is rejected; an explicit-member
     deliberation (H10) in `allowed_ids` is accepted.
  4. **Observation-set table:** a `safe_close` record with a `VERIFIED`
     engine whose observation set contains a disposition-set deliberation ID
     is rejected; a `safe_close` record with an UNVERIFIED engine whose
     observation set holds exactly the `records[]` paths and hashes of its
     non-`already-archived` dispositions is accepted, and the same record
     with one such path omitted, with a changed `sha256`, or with an
     `already-archived` deliberation's path added is rejected (re-plan
     cycle-2 C2-1).

  Fixtures build dispositions from `LinkedDeliberationOutcome` values and
  `PLANNED_ARCHIVE`, and never hard-code a linked deliberation in either set.
* **Depends on:** A1f (`192.019-T`; was A1 `192.001-T` before Copilot PR #481
  T8 inserted the A1d-A1f codec chain). **Harness surface:**
  `harness-surface:harness-architect`.
* **Posture:** test-first. **Size:** S. **Complexity:** low.

### A1b — Evidence persistence: streaming capture, redaction, lock, atomic write

* **Files:** `src/autoharness/shipment_close/__init__.py`,
  `src/autoharness/shipment_close/persist.py` (new), and
  `tests/test_shipment_close_persist.py` (new).
* **Changes:**
  * **Exit codes (re-plan cycle-1 R15):** `shipment_close/__init__.py` holds
    only the command's `EXIT_*` constants (the codes of the A3 table). It is
    their single definition. A1b, A3a, A3, and A3d import them from there,
    and the read-only `gates/cascade_evidence.py` never defines or imports
    them.
  * **Streaming capture:** `StreamCapture` counts bytes and lines and folds every
    byte into a SHA-256. It retains (a) a tail window of the final 64 KiB / 500
    lines plus a 4 KiB leading margin, and (b) for stdout only, an in-memory
    parse buffer of at most 1 MiB that is never persisted. Bytes past 1 MiB /
    10,000 lines are drained and hashed but not retained
    (`capture_truncated: true`). A stdout overflow makes the result unparseable
    (`parse_error: stdout exceeded capture cap`), never silently truncated JSON
    (AS-F03).
  * **Redaction:** `redact(text)` (defined in A1 `cascade_evidence.py`, re-plan
    cycle-1 R6) covers bearer or basic `Authorization` values; credential
    pairs over one shared, case-insensitive key set (`token`, `password`,
    `secret`, `api_key`, `apikey`, `access_token`, `refresh_token`, and
    `client_secret`), both as `key=value` and as a quoted JSON key with a `:`
    separator and optional whitespace (`"token": "..."`, `"api_key":"..."`;
    the quoted value is redacted through its closing quote and the key is
    kept, re-plan cycle-1 R17); GitHub `gh[pousr]_` and `github_pat_` tokens;
    and `sk-` style keys. It returns
    the text and a `redaction_applied` flag. It runs over the retained tail window
    **before** the excerpt is sliced (H-B4), and over **every** persisted
    free-text field: argv, `tool.version_excerpt`, `parse_error`, both
    excerpts, and `failures[]` (SL-F04). It never runs over
    `engine_semantics.reason`, `close_path_selection.reason`,
    `probed_version`, or `probed_commit` (re-plan cycle-1 R6): those are
    stored verbatim, because the validator re-assesses them, and they are
    safe by construction because A2a sanitizes the probe inputs and the A1
    validator asserts `redact(x)[0] == x` for all four.
  * **Per-pair lock (SL-F01):** `acquire_pair_lock(workspace, S, F, run_id)`
    creates `.autoharness/gates/cascade-close/{S}-{F}.lock` (a gitignored
    runtime directory) with `O_CREAT | O_EXCL` (plus `O_NOFOLLOW` where
    available, following the `gates/bootstrap_grant.py` precedent), holding
    `run_id`, the PID, and `started_at`. Before creating anything, every path
    component from the workspace root to the lock directory, and to
    `docs/closure/evidence/`, is checked: it must be contained in the workspace
    and be a real directory (no symlink, junction, or reparse point). Missing
    components are created one at a time with `mkdir` and re-checked after each
    creation (SL-F06). It is held from the first
    existing-record check through the final write and released in `finally`. An
    existing lock is never broken automatically: it returns exit 7. Removing a
    stale lock is an operator action.
  * **Existing-record check** (the first action under the lock, in every mode):
    an `invoking` record → exit 7; a `post_close` record → exit 2
    (`evidence already finalized`). A `pre_close` record is handled by mode:
    * Plain `--classify-only` is no-clobber: an existing `pre_close` record →
      exit 2 (`evidence already exists`), nothing written (PR #460 review).
    * `--classify-only --replace-pre-close` may replace it. That is an
      overwrite, and therefore destructive, and needs operator approval
      (Principle VII). The overwrite is an A1b pre_close takeover (below).
    * The mutating mode (itself destructive-approved) **never overwrites a
      `pre_close` record whose `close_path_selection.selected_close_path` is
      `cascade`** (re-plan cycle-1 R1). It hands that record to A3 as the
      Step 0(c) record. A3 step 3 compares the fresh selection against it,
      and on any difference exits 4 and leaves the record byte-identical. The
      mutating mode never writes a `safe_close` record over a
      `cascade`-selected one. The only write it may make over such a record is
      A3 step 4's re-stamp after an exact match (same selection, compared
      content identical; only `run_id` and `captured_at` change), made
      through the **pre_close takeover** below. A `pre_close`
      record whose selected path is `safe_close` may be replaced by the
      mutating mode, as before, also through the takeover.
    The check returns the existing `pre_close` record (or `None`) to its
    caller, so A3 never re-reads it outside the lock.
  * **Owner transition (AS-F01):** `write_evidence_atomic(path, record, *,
    owner_run_id, takeover_from_run_id=None)` permits the owning run (the
    same `run_id`, holding the lock) to move its own record `pre_close →
    invoking → post_close`. It refuses any other writer, and it refuses any
    transition out of `post_close`.
  * **Pre_close takeover (Copilot PR #481 T6).** A `pre_close` record
    written by a `--classify-only` run carries that run's `run_id`, so a
    later mutating run is a foreign writer to it. The one narrowly
    authorized exception is an atomic compare-and-swap of a `pre_close`
    record, requested with `takeover_from_run_id`:
    * `write_evidence_atomic` re-reads the on-disk record under the pair
      lock and proceeds only when it is `phase: pre_close` **and** its
      `run_id` equals `takeover_from_run_id`. The new record must also be
      `phase: pre_close` and carry `run_id == owner_run_id`. Otherwise it
      raises `CascadeEvidenceError` and leaves the on-disk record
      byte-identical. A takeover never applies to an `invoking` or
      `post_close` record, and a write without `takeover_from_run_id` over a
      record with a different `run_id` is still refused.
    * `takeover_from_run_id` is the `run_id` of the record the
      existing-record check returned under the same lock hold. It is never
      read from anywhere else.
    * Exactly three callers may pass it: (1) A3 step 4, re-stamping a
      `cascade`-selected record, **only after** A3 step 3's exact-match
      comparison passes and A3 has confirmed that the new record's
      `*_to_record` encoding equals the handed-off record's except for
      `run_id` and `captured_at`; (2) the mutating mode replacing a
      `safe_close`-selected `pre_close` record; and (3) the
      operator-approved `--classify-only --replace-pre-close`. No other
      code path passes it.
    * After the takeover, the record carries the mutating run's `run_id`,
      so A3's later `invoking` and `post_close` writes are ordinary owner
      transitions.
  * **Atomic write:** a same-directory temp file, flushed and fsynced, then
    `os.replace`. It refuses symlinked or reparse-point targets and parent
    directories (reusing the shipment_closure helpers). On Windows the directory
    fsync is skipped (unsupported), and `os.replace` retries a sharing-violation
    `PermissionError` at most 3 times with bounded backoff. The temp file is
    removed in `finally`.
* **Tests (test-first, four table-driven scenarios):**
  1. **Capture and redaction:** a truncation boundary at 64 KiB and at 500
     lines; a 2 MiB stream with bounded retained memory; a stdout overflow
     producing `parse_error`; a redaction case, plus a secret split across the
     excerpt boundary; a quoted JSON key case where `"token": "abc"`,
     `"api_key":"abc"`, and `"Access_Token" : "abc"` each have the value
     redacted and the key kept (re-plan cycle-1 R17); redaction of
     `failures[]` and `parse_error`.
  2. **Lock and directory trust:** two concurrent acquirers where exactly one
     wins and the other gets exit 7; a symlinked or junctioned lock-directory
     or evidence-directory component is refused before any file is created.
  3. **Existing-record check table:** an `invoking` record gives exit 7; a
     `post_close` record gives exit 2; plain `--classify-only` over an
     existing `pre_close` record exits 2 and leaves it byte-identical, while
     `--replace-pre-close` replaces it (PR #460 review); the mutating mode
     receives an existing `cascade`-selected `pre_close` record back from the
     check instead of replacing it (re-plan cycle-1 R1).
  4. **Owner transition, takeover, and atomic write:** the transition
     succeeds for the owning `run_id` and fails for a foreign one; a
     `pre_close` takeover with the correct `takeover_from_run_id` replaces
     the record and binds it to the new `run_id`, while a takeover with a
     wrong `takeover_from_run_id`, over an `invoking` or `post_close`
     record, or writing a non-`pre_close` record is refused with the
     on-disk record byte-identical (Copilot PR #481 T6); an atomic write
     leaves no partial file on a simulated failure and refuses a symlink
     target.
* **Depends on:** A1c. **Harness surface:** `harness-surface:harness-architect`.
* **Posture:** test-first. **Size:** M. **Complexity:** medium.

### A3a — Bounded backlogit subprocess runner

* **Files:** `src/autoharness/shipment_close/runner.py` (new), and
  `tests/test_shipment_close_runner.py` (new).
* **Changes:**
  * `resolve_backlogit_binary(workspace) -> ResolvedBinary` reads `cli.binary` from
    `.autoharness/backlog-registry.yaml` and resolves it with `shutil.which`. It
    refuses (exit 2) when:
    * `cli.binary` is not a bare name matching `^[A-Za-z0-9_-]+$` (re-plan
      cycle-1 R3). A path separator, a drive or UNC prefix, an absolute path
      such as `/bin/sh`, a `.`, or an extension is refused before any lookup;
    * the binary is unresolved;
    * the resolved file's basename, minus a trailing `.exe` on Windows, does
      not equal `cli.binary` (case-insensitive on Windows, exact elsewhere), so
      `which` cannot substitute a differently named program;
    * the resolved path lies inside the workspace root (a working-directory hijack
      on Windows);
    * it is a symlink or reparse point;
    * on Windows, its suffix is not `.exe`. A `.cmd`, `.bat`, or other script
      shim is refused, because batch argument parsing can reinterpret
      metacharacters even with `shell=False` (SL-F02).
  * Every version probe of the resolved binary runs with `cwd` set to a fresh,
    empty probe directory **inside the workspace** (Copilot PR #481 T3;
    constitution IV, CLI workspace containment), never the workspace root
    (re-plan cycle-1 R3). A trusted-looking name such as `python` therefore
    cannot pick up a planted `version` file from the workspace root. The
    probe directory rule (owned by A2a, the only probe spawner):
    * it lives under `.autoharness/gates/cascade-close/probe/`, the Git-ignored
      runtime directory that already holds the A1b pair lock
      (`.autoharness/gates/` is in `.gitignore`), so the command adds no new
      ignore assumption;
    * every path component from the workspace root down to `probe/` passes
      the same containment and directory-trust check as the A1b lock
      directory (contained in the workspace, a real directory, no symlink,
      junction, or reparse point; missing components created one at a time
      with `mkdir` and re-checked, SL-F06);
    * each probe gets its own directory, created exclusively with
      `tempfile.mkdtemp(prefix="probe-", dir=<probe root>)` and confirmed empty
      and contained (`assert_path_within_workspace`) immediately before the
      spawn;
    * the command **never deletes** a probe directory, in `finally` or
      anywhere else. An empty probe directory is left in place, and removing
      accumulated probe directories is an operator action under the
      destructive-command approval path (constitution VII), exactly like
      removing a stale lock.
  * It records the absolute path and the file's SHA-256 as `tool{binary_path,
    binary_sha256}`. A3a never spawns `--version` itself (re-plan cycle-1 R7):
    `tool.version_excerpt` is taken from the output of the single A2a probe
    spawn. The spawn always uses that absolute path,
    never the bare name, and A3 re-hashes the file immediately before spawning
    (SL-F03, in-scope part). The trust model equals today's: the current skill
    already runs the first `backlogit` on PATH. Pinning a trusted absolute path
    in the registry would be a new configuration contract. It is out of scope
    under P-021 C1 and is carried as a follow-up.
  * `run_bounded(argv, *, cwd, timeout) -> BoundedRunResult` (a frozen
    dataclass) uses `subprocess.Popen` with `shell=False`, `stdin=DEVNULL`, and
    one reader thread per stream feeding A1b `StreamCapture`. The child starts in
    a new process group (`start_new_session=True` on POSIX, and
    `CREATE_NEW_PROCESS_GROUP` on Windows). On timeout it kills the group
    (`os.killpg` on POSIX; on Windows, the absolute
    `%SystemRoot%\System32\taskkill.exe /T /F /PID <pid>`, by PID only), then
    does a bounded `wait(10)`.
  * `timeout` defaults to 120 s. `--timeout` accepts 30-900 s; out-of-range values
    exit 2.
* **Tests (test-first, three table-driven scenarios):**
  1. **Binary trust table:** a fake binary inside the workspace root is
     refused; a `.cmd` shim is refused on Windows (skipped elsewhere);
     `cli.binary` values `/bin/sh`, an absolute path (`C:\Tools\backlogit.exe`
     or `/usr/local/bin/backlogit`), and `tools/backlogit` are refused before
     any lookup; a bare name whose resolved basename differs is refused
     (re-plan cycle-1 R3).
  2. **Timeout:** a fake that sleeps past a 1 s test timeout is killed with
     `timed_out: true`.
  3. **Drain:** a fake emitting 2 MiB of stdout is drained.

  Test fakes are real executables outside the test's fixture workspace root
  (both created by the test itself, never by the command), for example a
  tiny compiled or `sys.executable`-launched shim whose resolution is injected
  through the `ResolvedBinary` seam, never a `.cmd`. `ResolvedBinary` carries
  `argv_prefix: tuple[str, ...]`, which is `(absolute_path,)` in production and
  `(sys.executable, fake_script)` in tests. The `.exe` and containment checks
  apply to `argv_prefix[0]`. Reader threads are joined with a bounded timeout
  after the process exits.
* **Depends on:** A1b (`192.002-T`), for `StreamCapture`. **Harness surface:**
  `harness-surface:harness-architect`.
* **Posture:** test-first. **Size:** S. **Complexity:** medium.

### A2a — CLI engine-semantics probe

* **Goal:** produce the `pre_close.engine_semantics` decision (re-plan R1,
  038-DL D4a) by probing the backlogit build the command will invoke, on the
  same CLI surface, through the same resolved absolute binary. The probe never
  halts. Every failure is `UNVERIFIED`, and `select_close_path` then selects
  SAFE_CLOSE.
* **Files:** `src/autoharness/shipment_close/engine_probe.py` (new), and
  `tests/test_shipment_close_engine_probe.py` (new).
* **Changes:**
  * `probe_engine_semantics(resolved: ResolvedBinary, *, workspace) -> EngineProbe`
    runs A3a `run_bounded` with the fixed argv
    `[*resolved.argv_prefix, "version", "--no-update-check", "--format", "json"]`
    (the shipment-reconcile Step 0(c) CLI probe), `cwd` set to a fresh, empty,
    workspace-contained probe directory under the Git-ignored
    `.autoharness/gates/cascade-close/probe/` (re-plan cycle-1 R3; Copilot
    PR #481 T4, constitution IV; the probe directory rule is stated under
    A3a: trusted components, exclusive `mkdtemp` creation, emptiness and
    containment re-checked before the spawn, and **no automatic deletion**,
    removal being an operator action under constitution VII), and a fixed
    30 s timeout. If the probe directory cannot be established (a
    containment or trust failure, or an I/O error), the probe spawns nothing
    and the result is `UNVERIFIED` with `probed_version=None`. It never spawns through a bare name and
    never uses a different binary from the one A3 later invokes. A3 step 6
    re-hashes that binary right before the spawn.
  * It parses **stdout only** as one JSON object and reads the raw `version`
    and `commit` values. It sanitizes the inputs, never the outputs (re-plan
    cycle-1 R6):
    * `version` is passed unchanged only when it is a `str` of at most 64
      characters that fully matches the merged release-version pattern
      (`re.fullmatch(shipment_closure._RELEASE_VERSION_PATTERN, version,
      flags=re.ASCII)`, reused rather than restated, and imported lazily
      inside `probe_engine_semantics` under the private-name rule, re-plan
      cycle-2 C2-4) **and**
      `redact(version)[0] == version` (the text element of the tuple;
      Copilot PR #481 T5). Otherwise `None` is passed.
    * `commit` is passed unchanged only when it is a `str` that fully matches
      `^[0-9a-f]{7,64}$`. Otherwise `None` is passed.
    * A `None` commit does not by itself make the engine `UNVERIFIED`. The
      merged function records `probed_commit` and never decides on it. Since
      two `None` commits compare equal, the A3 re-probe comparison does not
      rely on the commit to prove build identity: it relies on the
      `tool.binary_sha256` re-hash (A3 steps 3 and 6).
  * It calls
    `shipment_closure.assess_cascade_engine_semantics(version, probe_surface="cli", invocation_surface="cli", probed_commit=commit)`.
    A non-zero exit, a timeout, a stdout overflow, or unparseable JSON passes
    `probed_version=None`, so the result is `UNVERIFIED`. Released builds only
    and the verified minor lines are enforced by the merged function. The probe
    never restates them.
  * `EngineProbe` is a frozen dataclass: the `EngineSemanticsDecision`,
    `invocation_surface: "cli"`, and `version_excerpt`. `version_excerpt` is
    the A1b `StreamCapture` excerpt of this probe's stdout (bounded, and
    redacted before the slice, H-B4). It becomes `tool.version_excerpt`, so
    the probe is the only version spawn (re-plan cycle-1 R7). It is audit
    context only, and the validator never re-assesses it.
  * Serialization into `pre_close.engine_semantics` (A1 shape) goes through
    A1e `engine_semantics_to_record` (re-plan cycle-1 R8): `verdict`,
    `reason`, `probed_version`, `minor_line` (`[major, minor]` or `null`),
    `probed_commit`, `probe_surface`, and `invocation_surface`. None of these
    is redacted (re-plan cycle-1 R6).
  * The function never raises. An unexpected exception becomes an
    `UNVERIFIED` decision built by the same merged function with
    `probed_version=None`.
* **Acceptance criteria:**
  * A released `1.11.x` probe on `cli`/`cli` yields `VERIFIED`. Every other
    outcome yields `UNVERIFIED`, with the `ENGINE_SEMANTICS_UNVERIFIED:` reason
    prefix, and no exception and no exit code of its own.
  * The recorded sanitized `probed_version` and `probed_commit`, re-assessed
    by the A1 validator, reproduce the recorded `verdict`, `reason`, and
    `minor_line`.
  * The spawned argv is exactly the fixed probe argv on `resolved.argv_prefix`.
* **Tests (test-first, four table-driven scenarios, using the A3a
  `ResolvedBinary` test seam):**
  1. **Verified probe:** a fake emitting
     `{"version": "1.11.0", "commit": "131577c"}` yields `VERIFIED`,
     `minor_line` `[1, 11]`, the raw commit, and the exact argv; a planted
     `token=...` in stdout is redacted in `version_excerpt`; a `commit` of
     `"xyz"` or `"token=abc"`, a non-string `commit` (`131577` or
     `["131577c"]`), and a 65-character hex `commit` are each passed as
     `null`, and the verdict stays `VERIFIED` (re-plan cycle-1 R6, R18).
  2. **Unverified-version table:** `1.10.1` and `1.11.1-rc1` yield
     `UNVERIFIED` with the reason prefix; a 65-character `version`, a
     `version` of `"1.11.0 token=abc"`, and one with a trailing newline each
     yield `probed_version: null`, and the recorded `reason` equals
     `redact(reason)[0]` (re-plan cycle-1 R6; Copilot PR #481 T5).
  3. **Probe-failure table:** a fake that exits 1, one that sleeps past the
     timeout, one that emits non-JSON, one that exits 0 with empty stdout,
     and an injected `run_bounded` that raises an unexpected exception all
     yield `probed_version: null` and `UNVERIFIED` with the
     `ENGINE_SEMANTICS_UNVERIFIED:` reason prefix, and nothing raises
     (re-plan cycle-1 R18).
  4. **Working-directory isolation and containment:** `cli.binary: python` (a
     bare name that passes A3a) with a planted `version` script in the
     workspace root: the probe runs in a fresh, empty probe directory under
     `.autoharness/gates/cascade-close/probe/` inside the fixture workspace,
     the planted script never executes (its sentinel file is never written),
     and the result is `UNVERIFIED` (re-plan cycle-1 R3); after the probe
     returns, the probe directory still exists (no automatic deletion) and
     nothing was created outside the fixture workspace; a junctioned or
     symlinked `probe/` component makes the probe spawn nothing and return
     `UNVERIFIED` (Copilot PR #481 T4; constitution IV and VII).
* **Depends on:** A3a (`192.004-T`) directly; A1b and A1c are reached
  through it. **Harness surface:** `harness-surface:harness-architect`.
* **Posture:** test-first. **Size:** S. **Complexity:** low (risk low).

### A2b — Safe-close observation set

* **Goal:** compute the path-keyed safe-close observation set that A2 records
  for a selected SAFE_CLOSE and that A4b re-checks. Split out of A2 by re-plan
  cycle-1 R4.
* **Files:** `src/autoharness/shipment_close/observation.py` (new), and
  `tests/test_shipment_close_observation.py` (new).
* **Changes:**
  * `compute_observation_set(manifest_items, shipment_id, backlog_dir, *, excluded_ids, deliberation_records=()) -> tuple[ObservationEntry, ...]`
    is read-only and returns one entry per record path, with its
    workspace-relative `path`, location (queue or archive), SHA-256, and
    declared status, each encoded with A1d `observation_entry_to_record`
    (re-plan cycle-1 R8). The set is the union of:
    * the shipment-reconcile `mode: safe-close` observation set: the parent
      feature of each manifest task, plus every unshipped sibling task;
    * every out-of-manifest descendant of each manifest feature member (the
      classifier's traversal, `shipment_closure._scan_backlog` and
      `_enumerate_descendants`);
    * the entries built from `deliberation_records` (re-plan cycle-2 C2-1,
      below).
  * **Private helpers (re-plan cycle-2 C2-4).** `_scan_backlog`,
    `_enumerate_descendants`, and `_read_artifact_record` are imported
    lazily inside `compute_observation_set`, under the private-name rule in
    the re-plan amendment.
  * **Per-ID resolution and missing members (re-plan cycle-2 C2-2).** Each
    expected traversal ID is first resolved with
    `shipment_closure._read_artifact_record` (`queue/` and `archive/`, with a
    frontmatter `id` match). This matches the skill's safe-close step 3,
    which fingerprints each member's baseline location as `queue`,
    `archive`, or `missing`, and treats a member that is "already archived,
    descoped, or missing **at baseline**" as baseline state that is
    "explicitly **NOT** a halt":
    * no match records `location: missing`, `path: null`, `sha256: null`,
      and `declared_status: null`, and does not raise;
    * one match is located and fingerprinted;
    * more than one match (torn), a `BacklogUnavailableError`, a `None`
      traversal scan, or a resolved path that cannot be fingerprinted raises
      `CascadeEvidenceError`, which A2 turns into exit 2 with no record. That
      matches the skill, which halts only when a member "resolves to more
      than one record, cannot be fingerprinted, or otherwise cannot be read
      consistently".
  * **Closure-scope exclusion (re-plan cycle-1 R11).** Every ID in
    `closure_scope(S)` (`items(S) ∪ {S}`, computed locally exactly as A3b
    computes `allowed_ids`) is excluded, matching the skill's safe-close
    step 2 ("every unshipped sibling task outside `closure_scope(S)`"). For
    example, the covering feature of the manifest tasks is excluded when it
    is itself a manifest member (a whole-feature manifest), because
    safe-close archives it.
  * `excluded_ids` is supplied by A2: every ID in the disposition snapshot.
    It removes those IDs from the traversal entries, so under a `VERIFIED`
    engine the set holds no disposition-set deliberation (re-plan cycle-1
    R2; see H-C2).
  * **UNVERIFIED-engine deliberation records (re-plan cycle-2 C2-1).**
    When the engine verdict is `UNVERIFIED`, A2 passes as
    `deliberation_records` every `records[]` entry of each disposition
    whose outcome is not `already-archived`. Each becomes one entry with
    the deliberation ID, the snapshot's `path` and `sha256`, the location
    taken from the path's `queue/` or `archive/` segment, and the snapshot's
    `declared_status`. The entries are copied from the disposition snapshot
    and never re-read, so a deliberation's `retained_*` outcome never makes
    the set fail. A `retained_read_error` path has no `records[]` entry and
    is not included. Under a `VERIFIED` engine, A2 passes nothing. This
    closes the residual of AN-F07: an unauthorized direct cascade on a
    1.10.x engine that archives a linked deliberation. Under an UNVERIFIED
    engine, A1c forbids a planned `archive`, so the disposition step
    archives nothing and the A4b re-check of these paths cannot misfire.
* **Tests (test-first, four scenarios):**
  1. a task-only, partial-feature manifest yields the parent feature and the
     unshipped siblings, including a sibling already archived at baseline;
  2. an out-of-manifest descendant of a manifest feature member is included;
  3. **Exclusion table:** an ID in `excluded_ids` is absent even when it is
     a descendant; in a whole-feature manifest, the covering feature (a
     manifest member, so inside `closure_scope(S)`) is absent while its
     archived out-of-manifest descendants are present (re-plan cycle-1 R11);
     the `records[]` paths of a non-`already-archived` disposition passed as
     `deliberation_records` are present with the snapshot's `sha256`, and an
     `already-archived` disposition's paths, which A2 never passes, are
     absent (re-plan cycle-2 C2-1);
  4. **Torn versus missing table:** a torn observation-set member raises,
     and nothing is returned; a missing parent feature is recorded as
     `location: missing` with a null `path` and `sha256`, and nothing raises
     (re-plan cycle-2 C2-2).
* **Depends on:** A1c. **Harness surface:** `harness-surface:harness-architect`.
* **Posture:** test-first. **Size:** S. **Complexity:** medium.

### A2 — Pre-close snapshot and `--classify-only`

* **Files:** `src/autoharness/shipment_close/preclose.py` (new), and
  `tests/test_shipment_cascade_close_preclose.py` (new).
* **Depends on:** A2a (re-plan) and A2b (re-plan cycle-1 R4). The engine
  decision feeds both `select_close_path` and the disposition planner, and A2b
  supplies the observation set.
* **Changes:**
  * Input validation happens before any read: `shipment_id` / `feature_id` through
    `closure_contract.validate_closure_id`, and `--sha` as a full 40-character
    lowercase hex SHA. Invalid input exits 2 and writes nothing.
  * The lock and existing-record check (A1b) run **before** classification, in
    both modes, so an `invoking` record always wins with exit 7 and can never be
    reclassified into SAFE_CLOSE (AN-F02).
  * `run_preclose(workspace, shipment_id, feature_id, *, resolved) -> PreCloseSnapshot`:
    * it loads the manifest from the shipment record under the detected backlog
      root (`backlog_root.py`; `.backlog/` and `.backlogit/` both present fails
      closed);
    * a shipment that is no longer open (already archived or shipped) exits 2 and
      writes no record, so a verdict record cannot be produced after the fact
      (AN-F01);
    * it runs `classify_shipment_close_path` **fresh**;
    * it runs the A2a probe on `resolved` and records `engine_semantics`
      (re-plan R1). It assembles `tool{}` from the A3a `ResolvedBinary` path
      and hash and the A2a `version_excerpt` (re-plan cycle-1 R7);
    * it calls `select_close_path(classifier, engine)` and records
      `close_path_selection{selected_close_path, reason}` (re-plan R2). Every
      later branch keys on the **selected** path, never on the classifier
      verdict alone. If `redact(reason)[0] != reason` (Copilot PR #481 T2;
      the classifier reason
      quotes backlog-declared statuses), it exits 2 and writes no record,
      because the A1 validator would reject it (re-plan cycle-1 R6);
    * when the selected path is CASCADE, `feature_id` must be in the
      classifier's `qualifying_feature_ids`. When it is SAFE_CLOSE (including
      classifier CASCADE with an UNVERIFIED engine), `feature_id` must be a
      manifest member or the `parent_id` of one. Otherwise it exits 2 (AS-F08);
    * it captures location, SHA-256, declared status, and `parent_id` for the
      shipment record and for every manifest member (AS-F05). Every field is
      encoded with the A1d-A1f `*_to_record` helpers (re-plan cycle-1 R8);
    * it records the **disposition snapshot** (re-plan R5):
      `compute_linked_deliberation_disposition(manifest_ids, shipment_id, backlog_dir, engine=<the A2a decision>)`,
      with no `stash_path`, exactly as the skill's Linked-Deliberation
      Disposition step calls it. The planner covers every explicit manifest
      member, regardless of `artifact_type`, and applies the H10 exclusions
      (self-reference and every ID in `closure_scope(S)`). Its output is
      serialized with A1f `disposition_plan_to_record` into
      `pre_close.linked_deliberation_disposition`, with the planned outcomes.
      A planner path that is not a workspace-relative path under the backlog
      root (for example the out-of-workspace path the planner reports for a
      `path_escape` read error) is stored as `path: null` with its
      `reason_code` only, never as an absolute path (re-plan cycle-1 R12). This is a read-only call. The command never
      archives a deliberation. A non-null `planning_error` exits 2 and writes
      no record. Every `retained_*` outcome, unresolved reference, and read
      failure is recorded and never halts;
    * it fingerprints `out_of_manifest_descendant_ids` (location plus SHA-256);
    * when the **selected** path is SAFE_CLOSE, it also records the
      **safe-close observation set** by calling A2b
      `compute_observation_set(..., excluded_ids=<every disposition-snapshot ID>, deliberation_records=<see below>)`.
      The set is path-keyed. Under a `VERIFIED` engine (classifier
      SAFE_CLOSE), A2 passes no `deliberation_records`, so the set holds no
      disposition-set deliberation (re-plan cycle-1 R2): the skill's
      Linked-Deliberation Disposition step may archive those records after
      the close, so the A4b write-time re-check cannot key on them (see
      H-C2). Under an UNVERIFIED engine, A2 passes every `records[]` entry of
      each disposition whose outcome is not `already-archived` (re-plan
      cycle-2 C2-1), because no archive is planned and the A4b re-check
      cannot misfire. The disposition snapshot itself stays in
      `pre_close.linked_deliberation_disposition` for A3c drift detection.
      This covers task-only, partial-feature manifests, which have no manifest
      feature to traverse (AN-F07/AN-F09/AN-F01). If the observation set cannot be established
      (a torn or unreadable member; a missing member is recorded as
      `location: missing`, re-plan cycle-2 C2-2),
      `--classify-only` exits 2 and writes no record. That is fail-closed, and
      it matches the skill's own safe-close, which halts on the same
      conditions;
    * a torn or missing manifest member, or a torn observation-set member,
      fails closed. Disposition-set deliberations follow the planner's
      non-halting `retained_*` outcomes instead (`RECONCILE_FAIL_SNAPSHOT_*`
      applies to manifest members only).
  * The 1.10.x collection of "linked deliberations of each qualifying feature"
    and the `pre_close.linked_deliberations` key are removed (re-plan).
  * `--classify-only` writes a `phase: pre_close` record (for either selected
    path) and exits 0 when the selected path is CASCADE, or 3 when it is
    SAFE_CLOSE. That includes classifier CASCADE with an UNVERIFIED engine. It
    never mutates backlog state.
* **Tests (test-first, four table-driven scenarios):**
  1. **Selection table:** a CASCADE fixture with a fake `1.11.0` probe writes
     a pre-close record with every fingerprint,
     `engine_semantics.verdict: VERIFIED`, `selected_close_path: cascade`, and
     the disposition snapshot, and exits 0; the same fixture with a fake
     `1.10.1` probe records `classifier_verdict: CASCADE`,
     `engine_semantics.verdict: UNVERIFIED`, and
     `selected_close_path: safe_close`, records the A2b observation set,
     including the record paths of the fixture's linked deliberation, now
     planned `retained_engine_unverified` (re-plan cycle-2 C2-1), and exits 3.
  2. **Disposition-snapshot table:** a manifest member linking a live
     deliberation records it with a planned outcome, and under a `VERIFIED`
     engine the deliberation is absent from the observation set (re-plan
     cycle-1 R2); a deliberation
     that is itself an explicit manifest member is absent from the snapshot
     (H10); a torn deliberation records `retained_ambiguous` and does not
     halt; an injected planner `planning_error` exits 2 with no record.
  3. **Fail-closed input table:** a torn or duplicate manifest member, an
     already-shipped shipment, and a `feature_id` outside the qualifying set
     each exit 2 with no record.
  4. **Lock precedence:** an existing `invoking` record returns exit 7 even
     when the fixture now classifies SAFE_CLOSE.

  No fixture builds a `validated_linked_deliberations` set or asserts a
  linked deliberation in `allowed_ids` or `required_ids`.
* **Harness surface:** `harness-surface:harness-architect`.
* **Posture:** test-first, using the fixture builders in
  `tests/test_shipment_closure_classification.py`. **Size:** M. **Complexity:** medium.

### A3b — Response parser, flat sets, and INV-10 evaluator

* **Files:** `src/autoharness/shipment_close/postclose.py` (new), and
  `tests/test_shipment_close_postconditions.py` (new).
* **Changes:**
  * `parse_ship_response(stdout_bytes) -> ParsedResult | ParseError` parses the
    JSON-RPC 2.0 envelope from **stdout only** (backlogit logs to stderr). The
    envelope shape is characterized first: the first test step records
    `backlogit --jsonrpc shipment ship --help` and a canned envelope captured from
    a scratch fixture workspace, and both are committed as test fixtures.
  * `evaluate_postconditions(snapshot, parsed, reread) -> PostCloseResult` is
    pure, with no I/O. `reread` is supplied by A3. It holds a post-close read
    of the shipment record and of every fingerprinted file, plus the
    post-cascade **re-collection** of the disposition snapshot, which A3c
    evaluates (re-plan R4).
  * **Flat sets (re-plan R4; 038-DL D2).** It computes both sets locally, from
    the pre-close snapshot only (INV-P2), over every manifest item regardless of
    `artifact_type`:
    * `allowed_ids = items(S) ∪ {S}`, which is `closure_scope(S)`;
    * `required_ids = {S} ∪ qualifying_feature_ids ∪ {x ∈ items(S): the pre-close declared status of x is not exactly archived}`.
      `qualifying_feature_ids` is the classifier's set from Step 0(c), never a
      re-derivation. The declared status is decoded from the record with A1
      `declared_status_from_record` (re-plan cycle-1 R8), and only an exact
      `str` equal to `"archived"` counts as archived.

    No linked-deliberation term appears in either set. There is no
    `validated_linked_deliberations` term (re-plan, removed). A deliberation
    that is an explicit manifest member is an ordinary member of
    `allowed_ids` (H10). A disposition-set deliberation is in neither set. No
    public set helper exists on `main`, so production code does not import the
    private `_closure_scope_ids`. A parity test pins `allowed_ids` to it
    instead (M1, INV-P8; see the private-name rule in the re-plan amendment).
  * It evaluates INV-10 in full:
    * `returned_ids == []`;
    * the unexpected-artifact check and the missing-required check, each
      separately labelled and failing independently (INV-P3);
    * `parent_id` preservation for **every** manifest member, including each
      archived task, whose post-close `parent_id` (read from its archive
      location) must equal the pre-close snapshot (AS-F10);
    * byte-identical baseline invariance for every fingerprinted artifact outside
      `allowed_ids`;
    * the re-read shipment record declares `status: archived` and
      `archived_status: shipped` (AS-F04).
  * `linked_deliberation_drift[]` and `disposition_byte_identical` are
    computed by A3c and merged into the `PostCloseResult`; any drift entry
    makes `postcondition_verdict: fail`.
  * `mutation_state` is derived here: `completed` for a parsed success envelope;
    `none` only when every fingerprinted file's SHA-256 is unchanged and no
    fingerprinted ID has gained an archive-location file; otherwise
    `indeterminate`. A timeout or a non-zero exit is never read as "no mutation"
    (compound `2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md`).
* **Tests (test-first, four table-driven scenarios):**
  1. **Envelope and `mutation_state`:** the characterized envelope parses; a
     malformed envelope yields `ParseError`; `mutation_state` for unchanged,
     changed, and unparsed inputs.
  2. **Flat-set table:** a table-driven pass case; the two set checks failing
     independently (with both failing at once, both are reported); a
     pre-close archived manifest task is absent from `required_ids` (compound
     `2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md`);
     an explicit-member deliberation that is archived passes as an ordinary
     `allowed_ids` member (H10); a disposition-set deliberation in
     `archived_ids` is reported as an unexpected artifact.
  3. **INV-10 table:** a non-empty `returned_ids`; a moved `parent_id` on an
     archived manifest task and on an out-of-manifest artifact; a modified
     descendant giving `baseline_invariant: false`; a shipment record lacking
     `archived_status: shipped`.
  4. **Parity test** (M1, INV-P8): for a table of manifest fixtures,
     including an empty manifest and a manifest containing a deliberation,
     `allowed_ids` equals `shipment_closure._closure_scope_ids(manifest_ids, S)`.
     The same test pins the local "truly archived" check used for
     `required_ids` against `shipment_closure._is_engine_inert` (re-plan
     cycle-1 R9): for declared statuses `"archived"`, `"Archived"`,
     `" archived "`, `True`, `None`, and a missing `status` key, the local
     check over the A1-encoded and decoded status equals `_is_engine_inert`
     over the raw parsed value (`None` for the missing key), so only the
     first is archived. This test module is the only importer of these two
     private helpers. It also pins the existence and signature (for the
     pattern, a `str`) of the five lazily imported private names
     (`_RELEASE_VERSION_PATTERN`, `_scan_backlog`, `_enumerate_descendants`,
     `_read_artifact_record`, `_check_path_containment`), so an upstream
     rename fails this test rather than `cli.py` import (re-plan cycle-2
     C2-4).

  Fixtures build dispositions from `LinkedDeliberationOutcome` values, and
  none hard-codes a linked deliberation in either set.
* **Depends on:** A2 (`192.003-T`), for the snapshot type. **Harness surface:**
  `harness-surface:harness-architect`.
* **Posture:** test-first. **Size:** M. **Complexity:** medium (the high-risk
  envelope uncertainty is de-risked by the characterization step, and the
  function is pure).

### A3c — Linked-deliberation drift evaluator

* **Goal:** detect engine drift on disposition-set deliberations at close
  time (re-plan item 4, R4; 038-DL D2). Split out of A3b by re-plan cycle-1
  R4. This is the authoritative drift check: the A4b gate does not re-check
  disposition-set deliberations (H-C2).
* **Files:** `src/autoharness/shipment_close/postclose.py` (extended), and
  `tests/test_shipment_close_deliberation_drift.py` (new).
* **Changes:**
  * `evaluate_linked_deliberation_drift(snapshot, archived_ids, recollected) -> tuple[DriftEntry, ...]`
    is pure. Engine drift is any of the following, and each is recorded as
    `{deliberation_id, kind, detail}`:
    * `archived`: a disposition-set deliberation ID appears in `archived_ids`.
      It also fails the A3b unexpected-artifact check, because it is outside
      `allowed_ids`;
    * `modified`: the SHA-256 of any `records[]` path differs from the
      pre-close snapshot, or the path moved. Then
      `disposition_byte_identical` is `false`;
    * `snapshot_drift`: the re-collected snapshot differs from the pre-close
      snapshot in deliberation IDs, link kinds, linking members, declared
      status, record paths, SHA-256, unresolved references, or
      `read_failures` (each `{path, reason_code}`). That is the field set the
      skill's Cascade Close Sub-Procedure step 5 compares. The planned
      `outcome` is compared only when the pre-close or the re-collected
      outcome is a settled outcome (`retained_read_error`,
      `retained_ambiguous`, or `already-archived`), and for a
      `retained_read_error` disposition its `path` and `reason_code` are
      compared too (re-plan cycle-1 R10). This matches the settled-outcome
      comparison in the skill's Linked-Deliberation Disposition step 1.
      Any other outcome change is not drift (re-plan cycle-2 C2-3). For
      example, `retained_shared_reference` and the planned `archive` can
      swap when a live referrer outside `closure_scope(S)` changes, and the
      disposition step re-plans those outcomes itself;
    * `planning_error`: the post-close re-collection returned a non-null
      `planning_error`. That is drift, never a skipped comparison, so it
      makes `postcondition_verdict: fail` (exit 5) (re-plan cycle-1 R10).

    The re-collected plan is encoded with A1f `disposition_plan_to_record`,
    and every comparison is between that encoding and the recorded one,
    never between a parsed YAML value and JSON (re-plan cycle-1 R8).
    Any drift entry makes `postcondition_verdict: fail` (exit 5 in A3).
    `retained_*` outcomes are never drift by themselves.
* **Tests (test-first, four scenarios):**
  1. **Flat-contract pass:** a manifest member links a live deliberation, the
     cascade leaves it in `queue/` and unchanged, and the result has no drift.
     This pins the 190-S halt shape as a non-failure.
  2. **`archived` drift:** a disposition-set deliberation in `archived_ids` is
     reported as `linked_deliberation_drift` (`archived`).
  3. **`modified` drift:** a modified deliberation record yields `modified`
     drift and `disposition_byte_identical: false`.
  4. **`snapshot_drift` and `planning_error` table:** a re-collected
     snapshot with a new link kind, a changed settled outcome, a
     `retained_read_error` whose `path` or `reason_code` changed, or a
     changed `read_failures` entry yields `snapshot_drift`; a re-collection
     with a non-null `planning_error` yields `planning_error` drift; each
     row makes `postcondition_verdict: fail` (re-plan cycle-1 R10); a
     planned `archive` that became `retained_shared_reference` from a new
     live referrer, with every compared field unchanged, yields no drift
     (re-plan cycle-2 C2-3).
* **Depends on:** A3b (`192.005-T`). **Harness surface:**
  `harness-surface:harness-architect`.
* **Posture:** test-first. **Size:** S. **Complexity:** medium.

### A3 — `cascade-close` orchestration

Re-plan cycle-1 R4 moved the CLI wiring and `--json` rendering into A3d.

* **Files:** `src/autoharness/shipment_close/command.py` (new), and
  `tests/test_shipment_cascade_close_invoke.py` (new).
* **Changes:**
  * `run_cascade_close(...)` steps, all under the A1b pair lock:
    1. Acquire the lock and run the existing-record check (exit 7 or 2), before
       any classification.
    2. Validate `--message` and `--author`: each must be non-empty, contain no NUL
       or newline, and be at most 1,024 characters. Failure exits 2.
    3. Call `run_preclose`, which includes the A2a engine probe and
       `select_close_path`.
       * **No prior `cascade`-selected record** (none exists, or the existing
         `pre_close` record selected `safe_close`): if the **selected** path is
         not CASCADE, the command writes the `pre_close` verdict record and
         exits 3 without invoking anything. This covers a SAFE_CLOSE classifier
         verdict, and it covers a CASCADE classifier verdict with an UNVERIFIED
         engine. That is the engine gate, failing closed to SAFE_CLOSE (re-plan
         R3; D4a). The cascade never runs without a `VERIFIED` engine on the
         CLI surface it invokes.
       * **A `--classify-only` record that selected `cascade` exists** (re-plan
         cycle-1 R1; D4a "a re-probe difference halts"): the command treats it
         as the Step 0(c) record and compares the fresh result against it:
         the classifier verdict, reason, and qualifying set; the engine probe
         (`verdict`, `reason`, raw `probed_version`, raw `probed_commit`,
         `probe_surface`, `invocation_surface`, and the re-hashed
         `tool.binary_sha256`); the close-path selection; and the disposition
         snapshot. **Any** difference, including a fresh selection of
         SAFE_CLOSE, exits 4 and leaves the record byte-identical. Every
         compared field is compared as its A1d-A1f `*_to_record` encoding (re-plan
         cycle-1 R8). The command
         never writes a `safe_close` record over a `cascade`-selected one and
         never substitutes SAFE_CLOSE (INV-P4). An exact match continues to
         step 4.
    4. Write the `pre_close` record. Over a matched `cascade`-selected record,
       this is a re-stamp that changes only `run_id` and `captured_at`. It is
       made only after step 3's exact-match comparison passes, as an A1b
       **pre_close takeover**: `write_evidence_atomic(path, restamped,
       owner_run_id=<this run>, takeover_from_run_id=<run_id of the record
       the existing-record check returned>)`, after A3 confirms that the
       `*_to_record` encodings of `restamped` and the handed-off record differ
       only in `run_id` and `captured_at` (Copilot PR #481 T6). The takeover
       binds the record to this run, so steps 7 and 10 are ordinary owner
       transitions. Over a `safe_close`-selected record, the replacement uses
       the same takeover. A refused takeover (the on-disk record no longer
       matches the expected prior `run_id` or phase) exits 4 with the record
       byte-identical and nothing invoked. If the write fails for any other
       reason, exit 2 without invoking anything.
    5. Revalidate (AS-F02): recompute the **entire** pre-close snapshot and
       compare it with the durable record, ignoring only `captured_at`. The
       snapshot covers the classifier verdict, the qualifying set, every
       declared status, every `parent_id`, every SHA-256, and the disposition
       snapshot (deliberation IDs, link kinds, linking members, declared
       statuses, record paths, SHA-256 values, and unresolved references). Any
       difference exits 4 (`HALT — cascade pre-invocation revalidation drift detected`).
       **Engine re-probe** (re-plan R3; D4a), alongside the snapshot
       recomputation: re-run the A2a probe fresh, through the same resolved
       binary on the same CLI surface. Compare the raw `probed_version`,
       `probed_commit`, and `probe_surface` values and the verdict with the
       record by exact string equality, never by minor line only. Any
       difference, or a re-probe failure of any kind, exits 4. It never
       substitutes SAFE_CLOSE, because after a CASCADE selection that would be
       the prohibited substitution (INV-P4). A `None` `probed_commit` on both
       sides compares equal and proves nothing about build identity, so the
       comparison relies on the step 6 `tool.binary_sha256` re-hash for that
       (re-plan cycle-1 R6).
    6. Re-hash the resolved binary. A mismatch with `tool.binary_sha256` exits 4
       without invoking anything, leaving only the replaceable `pre_close`
       record (AN-F08).
    7. Write the owner-bound `phase: invoking` record (`run_id`,
       `argv_redacted`, `started_at`). If that write fails, exit 2 without
       invoking anything (INV-P1, INV-P7).
    8. Invoke through A3a with the fixed argv
       `[<absolute binary>, "--no-update-check", "--jsonrpc", "--cwd", <workspace root>, "shipment", "ship", S, "--sha", X, "--message", M, "--author", A]`.
    9. Re-read the fingerprinted files and the shipment record. Re-collect the
       disposition snapshot with `compute_linked_deliberation_disposition`,
       passing the **pre-close** manifest IDs and the recorded pre-close engine
       decision. Then call A3b `parse_ship_response` and
       `evaluate_postconditions`.
    10. Write the owner-bound `post_close` record. This happens **even when the
        invocation or the parse fails**, so the evidence of a failure is preserved.
        If this write fails, exit 8.
  * The command spawns exactly two kinds of process: the A2a probe (at
    step 3 and its step 5 re-probe) and `shipment ship`. There is no
    separate `--version` spawn, because `tool.version_excerpt` comes from the
    A2a probe (re-plan cycle-1 R7). It never
    archives, moves, or edits a deliberation or any other artifact. The skill's
    Linked-Deliberation Disposition step is the only archiver (038-DL D3a,
    one archiver).
  * Exit codes (one table for the command, including `--classify-only`). Each
    code is an `EXIT_*` constant from `shipment_close/__init__.py` (A1b;
    re-plan cycle-1 R15):

    | Code | Meaning | Mutation possible? | Ship action |
    |---|---|---|---|
    | 0 | Mutating mode: all postconditions passed. `--classify-only`: CASCADE selected (classifier CASCADE, engine VERIFIED), verdict recorded | mutating: yes (completed); classify-only: no | See the A5 routing table |
    | 2 | Input, I/O, no-clobber refusal (`already finalized`), a disposition `planning_error`, or a pre-invocation write failure | no | HALT; fix the input or ask the operator |
    | 3 | The selected path is not CASCADE: the classifier said SAFE_CLOSE, or the engine is UNVERIFIED. A verdict record is written and nothing is invoked. Mutating mode exits 3 only when no `cascade`-selected `--classify-only` record existed | no | See the A5 routing table |
    | 4 | Pre-invocation revalidation drift: snapshot drift, an engine re-probe difference or failure, a binary hash change, or any difference from a `cascade`-selected `--classify-only` record (the record is left byte-identical). Nothing invoked | no | HALT; operator. Never SAFE_CLOSE |
    | 5 | A postcondition failed, including `linked_deliberation_drift`; the record names every failure | yes | HALT; operator review |
    | 6 | backlogit exited non-zero, timed out, or stdout did not parse | indeterminate | HALT; operator review |
    | 7 | An existing lock or `invoking` record; nothing invoked | unknown (prior run) | HALT; operator review |
    | 8 | The post-close evidence write failed after invocation | yes | HALT; operator review |

  * Exits 5, 6, 7, and 8 forbid committing the backlog root, re-running
    `cascade-close`, calling `backlogit shipment ship` directly, or substituting
    SAFE_CLOSE (INV-P4) until an operator reviews the backlog state and the record.
  * `run_cascade_close` returns a frozen `CascadeCloseOutcome` (exit code,
    evidence path, phase written, and the fields A3d renders). The CLI wiring
    and the `--json` rendering are A3d.
* **Tests (test-first, four table-driven scenarios).** A fake `backlogit` (A3a
  seam) emits a canned envelope, answers the `version` probe from a per-call
  script, and writes a sentinel file when `shipment ship` runs:
  1. **Pass and argv log:** a pass case; the argv log holds exactly the two
     A2a probe argvs (step 3 and the step 5 re-probe) and one fixed ship
     argv (including `--cwd`), with no `--version` argv and no archive call
     (re-plan cycle-1 R7).
  2. **Pre-spawn fail-closed table:** a classifier CASCADE with a fake
     `1.10.1` probe exits 3, the `shipment ship` sentinel is never written,
     and the record selects `safe_close`; the fake's `commit` changes between
     the step 3 probe and the step 5 re-probe: exit 4, no spawn; the step 5
     re-probe times out: exit 4, never 3; drift injected between steps 4 and 5
     exits 4 with no spawn; a pre-existing `invoking` record exits 7 and the
     fake is never spawned.
  3. **`--classify-only` record hand-off (re-plan cycle-1 R1):** a
     `--classify-only` run records a `cascade` selection, then the fake's
     probe answers `1.10.1` (or the disposition snapshot changes) before the
     mutating run: exit 4, the `pre_close` record is byte-identical, no
     `safe_close` record is written, and `shipment ship` is never spawned.
     With nothing changed, the mutating run re-stamps only `run_id` and
     `captured_at` through the A1b pre_close takeover (the record now carries
     the mutating run's `run_id`) and proceeds; a takeover attempted with a
     stale expected `run_id` exits 4 with the record byte-identical (Copilot
     PR #481 T6).
  4. **Post-spawn failure table:** a non-empty `returned_ids` exits 5 with the
     record written; the fake modifies a disposition-set deliberation during
     the ship call: exit 5 with `linked_deliberation_drift` recorded;
     backlogit exiting 1 with stderr keeps redacted stderr in the record and
     exits 6; a simulated post-close write failure exits 8.
* **Depends on:** A3c. **Harness surface:** `harness-surface:harness-architect`.
* **Posture:** test-first. **Size:** M. **Complexity:** medium.

### A3d — `cascade-close` CLI wiring and `--json` output

* **Goal:** expose `run_cascade_close` as `autoharness shipment cascade-close`.
  Split out of A3 by re-plan cycle-1 R4.
* **Files:** `src/autoharness/cli.py` (dispatch and usage only), and
  `tests/test_cli_shipment_cascade_close.py` (new).
* **Changes:**
  * `--json` output (AN-F06) is one object:
    `{mode, exit_code, evidence_path, phase_written, classifier_verdict,
    engine_verdict, selected_close_path, mutation_possible: no | yes | indeterminate | unknown,
    postcondition_verdict, failures[], operator_action: none | review_required}`.
    The exit-2 cases always report `mutation_possible: no`, because every
    post-invocation write failure uses exit 8.
  * `cli.py` gains the `shipment` group, the `cascade-close` subcommand, and USAGE
    lines. The USAGE text labels the mutating mode and
    `--classify-only --replace-pre-close` **destructive**, and plain
    `--classify-only` no-clobber and read-only apart from creating a new
    evidence record (Principle VII).
  * Argument parsing: `--timeout` accepts 30-900 s (out of range exits 2), and
    `--replace-pre-close` is accepted only together with `--classify-only`.
* **Tests (test-first, three scenarios, with `run_cascade_close` stubbed):**
  1. `--json` fields for every exit code in the A3 table, including
     `mutation_possible` per code;
  2. the USAGE text carries the destructive and no-clobber labels;
  3. argument-parsing table: an out-of-range `--timeout`, a lone
     `--replace-pre-close`, and a missing `--sha` each exit 2.
* **Depends on:** A3 (`192.006-T`). **Harness surface:**
  `harness-surface:harness-architect`.
* **Posture:** test-first. **Size:** S. **Complexity:** low.

### A4 — Closure-evidence gate: `close_path` and the close-evidence requirement

* **Files:** `src/autoharness/cli.py` (the `_evaluate_closure_evidence` path only),
  and `tests/test_cli_gate_closure_evidence.py` (extended).
* **Changes:**
  * The gate is write-time only: no workflow, script, or CI job re-gates committed
    closure artifacts (verified 2026-09-27: no `.github/workflows/` or `scripts/`
    invocation of `closure-evidence`). The new checks therefore apply to every
    invocation, and committed artifacts are unaffected because they are never
    re-gated and the topology reader is unchanged (INV-P5).
  * Check order: the new checks run only **after** the existing
    `frontmatter_predicate` and `discoverability` checks pass. A `BLOCKED`
    artifact therefore still fails at `frontmatter_predicate` exactly as today,
    and the new checks never mask or reorder an existing `failed_check`.
  * Every artifact must carry `close_path: cascade | safe_close`. A missing or
    other value fails as `failed_check: close_path`.
  * Every artifact must carry `close_evidence: <path>`, checked in this order, each
    failure reported as `failed_check: close_evidence`:
    1. textual containment first (a relative POSIX path, no `..`, no drive or UNC
       prefix, under `docs/closure/evidence/`), before any filesystem call
       (compound `2026-09-27-175-s-closure-evidence-gate-hardening-lessons.md`);
    2. it equals `build_evidence_path(S, F)` for the artifact's declared pair;
    3. the entry is a regular file (no symlink or reparse point) of at most
       512 KiB. It is opened with `O_NOFOLLOW` where available. **Before any
       byte is read**, its `fstat` identity must equal the pre-open `lstat`, and
       the resolved path of the file and of each parent component is re-checked
       for containment (SL-F05/SL-F07). It is then read once and parsed as JSON.
       The remaining parent-swap race window needs a local attacker with write
       access to the working tree, which is outside this gate's threat model.
       This is accepted and recorded;
    4. `validate_evidence_record(..., close_path=<declared>)` passes. The
       declared `close_path` is checked against the record's **selected** close
       path (re-plan R2), never against the classifier verdict alone. A
       `safe_close` record whose `classifier_verdict` is `CASCADE` is valid
       exactly when its engine is UNVERIFIED, because the validator re-runs
       `assess_cascade_engine_semantics` and `select_close_path` over the
       recorded inputs (A1);
    5. when the closure artifact carries the `merge_commit` frontmatter key (the
       key committed artifacts already use, for example
       `docs/closure/175-S-167-F-post-merge-closure.md`), the record's
       `merge_commit_sha` must equal it. When the key is absent the gate adds a
       `warnings[]` entry instead: the operational-closure template does not yet
       mandate `merge_commit`, and mandating it is outside this plan's scope.
  * SAFE_CLOSE is fail-closed too (AN-F01, amending D-A3 — Stage-recommended,
    pending operator confirmation). A `safe_close` artifact without a valid
    verdict record whose selected close path is `safe_close` fails.
  * The SAFE_CLOSE observation-set re-check is A4b (re-plan cycle-1 R4). It
    runs as the last `close_evidence` sub-check, after step 5.
  * `close_path` and `close_evidence` are added to the `failed_check` vocabulary in
    the gate USAGE text and the `--json` description. `warnings[]` is
    documented there, including the vacuous-check (A4b) and
    absent-`merge_commit` warnings.
  * The pipeline-topology closure reader is **not** modified.
* **Tests (test-first, four table-driven scenarios):**
  1. **Per-path verdict table:** CASCADE with no record, with a `fail`
     verdict record, or with a record whose engine is UNVERIFIED → FAIL;
     CASCADE with a valid record → PASS; SAFE_CLOSE with no record or with a
     CASCADE record → FAIL; SAFE_CLOSE with a valid verdict record, including
     one whose `classifier_verdict` is `CASCADE` and whose engine is
     UNVERIFIED → PASS; a mismatched shipment ID in the record → FAIL.
  2. **Evidence-path containment table:** a `..` path, an absolute path, a
     path other than `build_evidence_path(S, F)`, an oversize file, and a
     symlinked record → FAIL with no read outside the workspace.
  3. **`merge_commit` cross-check:** a mismatched `merge_commit_sha` → FAIL;
     an absent `merge_commit` key → PASS with the warning.
  4. **Non-regression pins:** a `BLOCKED` artifact still reports
     `failed_check: frontmatter_predicate`; the topology gate still accepts a
     committed fixture artifact that has no `close_path` (INV-P5 pin);
     `classify_closure_candidates` ignores a `docs/closure/evidence/`
     subdirectory.
* **Depends on:** A3d (`192.015-T`). A4, A4b, A5, A5b, A5c, A6, and A6b ship
  in one PR (label `release-unit-a4-a6`). **Harness
  surface:** `harness-surface:harness-architect`.
* **Posture:** test-first. **Size:** M. **Complexity:** medium.

### A4b — Closure-evidence gate: SAFE_CLOSE observation-set re-check

* **Goal:** the write-time SAFE_CLOSE direct-cascade detection, split out of
  A4 by re-plan cycle-1 R4.
* **Files:** `src/autoharness/cli.py` (the `_evaluate_closure_evidence` path
  only), and `tests/test_cli_gate_closure_evidence_observation.py` (new).
* **Changes:**
  * SAFE_CLOSE direct-cascade detection (AN-F07/AN-F09): for a `safe_close`
    record, the gate requires every `observation_set` entry to still be at
    exactly its recorded location, with its recorded SHA-256. An entry that was
    already archived at baseline therefore stays valid, and only a change
    relative to the baseline fails. An entry recorded `location: missing`
    (re-plan cycle-2 C2-2) must still be missing:
    `shipment_closure._read_artifact_record(backlog_dir, id)`, imported
    lazily under the private-name rule, must return `None`. A record that now
    resolves, or a torn or unsafe resolution (`BacklogUnavailableError`),
    fails. Any difference fails as
    `failed_check: close_evidence`. This is the same baseline invariance that
    safe-close itself asserts, re-checked at write time. An empty observation
    set (when no manifest task has a parent outside `closure_scope(S)` and no
    manifest feature has an out-of-manifest descendant) passes with a
    `warnings[]` entry saying the check was vacuous.
  * **Path containment (re-plan cycle-1 R12).** Every non-null
    observation-set path
    is read through the same containment discipline as `close_evidence`
    (A4 steps 1 and 3), before any byte is read: the A1 textual check (the
    validator has already run), then the first segment must equal the
    detected backlog root, then
    `shipment_closure._check_path_containment(workspace_root / path,
    backlog_dir)`, imported lazily inside the re-check function under the
    private-name rule (re-plan cycle-2 C2-4) (verified on `main`: lexical containment, no symlink,
    junction, or reparse point on any component from the backlog root down,
    and canonical containment; it returns a read-error reason code or
    `None`). A non-`None` result fails as `failed_check: close_evidence`
    with that reason code, and nothing is read. The file is then opened and
    read exactly as A4 step 3 reads the evidence record (`O_NOFOLLOW` where
    available, regular file, `fstat` equal to the pre-open `lstat`, bounded
    size). Reusing the planner's own containment helper, rather than
    restating it, keeps one containment rule for every backlog path the
    plan reads; the A4b tests and the A3b private-name pin cover the
    behavior, so a change to the private helper surfaces there.
  * **Disposition-set deliberations (re-plan cycle-1 R2; cycle-2 C2-1,
    C2-5).** The gate has no planned-`archive` exemption, never reads a
    disposition outcome, and emits no `stranded_linked_deliberation`
    warning. It re-checks a disposition-set deliberation only through the
    observation set, and only where A2b put one there:
    * **`VERIFIED` engine (classifier SAFE_CLOSE).** The observation set
      holds no disposition-set deliberation (A2b, A1c), so the gate does not
      re-check them. The skill's Linked-Deliberation Disposition step runs
      after the close and before the closure artifact is written, and it is
      the sole archiver. It takes its inputs from Step 0(c) (from the
      evidence record after A5), then re-runs the planner with the recorded
      engine decision. That plan must match the snapshot on IDs, link kinds,
      linking members, record paths, hashes, settled outcomes, and
      unresolved references, but the archive-or-retain outcome of every
      other deliberation comes from the live referrers at that moment, and
      step 3 re-checks the shared-reference guard before each archive. A
      gate rule keyed on the pre-close planned outcome would therefore
      misfire. Engine drift on those deliberations under the CASCADE path is
      detected at close time by A3c's post-close re-collection, which is the
      authoritative point.
    * **UNVERIFIED engine (classifier SAFE_CLOSE or CASCADE).** The
      observation set holds every `records[]` path of each disposition
      whose outcome is not `already-archived` (A2b), and the gate re-checks
      each one byte-identical (location and SHA-256), like any other entry.
      The re-check cannot misfire: A1c forbids a planned `archive` under an
      UNVERIFIED engine, and the skill's disposition step mutates nothing
      ("Engine UNVERIFIED means no mutation").

    Stranded advisories are surfaced by the skill's own disposition report;
    gate-level surfacing stays in the deferred stash scope `3B43CE5A` /
    `D79EA53A`.
  * **Guarantee:** a direct cascade can never be accepted under
    `close_path: cascade`. Under `close_path: safe_close`, it is detected whenever
    it changed anything in the observation set, which is exactly the corruption
    SAFE_CLOSE exists to prevent. The set includes every out-of-manifest
    descendant a cascade could reach and, under an UNVERIFIED engine (for
    example backlogit 1.10.x, whose cascade can archive linked
    deliberations), every hashed record path of each disposition-set
    deliberation that was not already archived pre-close (re-plan cycle-2
    C2-1). Under a `VERIFIED` (1.11.x) engine, the flat cascade does not
    archive disposition-set deliberations, so they are not re-checked. Two
    residuals stay undetected. The first is a direct cascade whose effect
    equals the
    safe-close outcome, which by construction left nothing outside closure
    scope changed. The second is a `retained_read_error` deliberation path,
    which has no hash and is never read. Both remain P-005 deviations by
    skill contract, and upstream enforcement is requested in A7. Accepting
    the first, benign residual is a Stage-recommended decision, pending
    operator confirmation.
* **Tests (test-first, two scenarios):**
  1. **Observation-set table:** on a task-only, partial-feature fixture, an
     observation-set parent feature or sibling now archived or modified →
     FAIL; a sibling that was already archived at baseline and is unchanged
     → PASS; an empty observation set → PASS with the vacuous-check warning.
     On a whole-feature manifest whose classifier verdict is CASCADE and
     whose engine is UNVERIFIED (so the record selects `safe_close`), the
     closure artifact passes A4 and A4b after safe-close archives the
     manifest feature and its tasks, because the feature is inside
     `closure_scope(S)` and never in the observation set (re-plan cycle-1
     R11). An observation-set entry whose path has a junctioned or
     symlinked component, or whose first segment is not the detected backlog
     root, → FAIL with no read (re-plan cycle-1 R12). An entry recorded
     `location: missing` that is still missing → PASS, and one that now
     resolves to a record → FAIL (re-plan cycle-2 C2-2).
  2. **Disposition table (re-plan cycle-1 R2 regression pin; cycle-2
     C2-1):** on a `VERIFIED`-engine `safe_close` record, the disposition
     step archives a planned-`archive` deliberation after safe-close →
     PASS, because no disposition-set deliberation is in the observation
     set, and no `stranded_linked_deliberation` warning is emitted for a
     `retained_*` disposition. On an UNVERIFIED-engine `safe_close` record,
     a `retained_engine_unverified` deliberation whose recorded record path
     is unchanged → PASS, and one that a direct cascade archived or
     modified → FAIL as `failed_check: close_evidence`.
* **Depends on:** A4 (`192.007-T`). **Harness surface:**
  `harness-surface:harness-architect`.
* **Posture:** test-first. **Size:** S. **Complexity:** medium.

### A5 — shipment-reconcile skill routes CASCADE through the command (template and mirror)

Copilot PR #481 T9 split the former six-file A5 into this unit (the
shipment-reconcile skill), A5b (the operational-closure skill), and A5c (the
doc assertions for both).

* **Goal:** route every shipment close through `autoharness shipment
  cascade-close` in the shipment-reconcile skill (template and mirror).
* **Files:** `templates/skills/shipment-reconcile/SKILL.md.tmpl`,
  `.github/skills/shipment-reconcile/SKILL.md`, and that entry's checksum
  and note line in `.autoharness/harness-manifest.yaml`. The template, its
  installed mirror, and the mirror's manifest checksum are one atomic
  rendered-surface triple: existing parity and checksum-coherence tests fail
  if any one changes without the other two, so they cannot be split further.
* **Changes:**
  * shipment-reconcile:
    * Step 0(c) (the engine-semantics gate, close-path selection, and the
      linked-deliberation disposition snapshot) now points at
      `autoharness shipment cascade-close --classify-only`. Its record carries
      `pre_close.engine_semantics`, `pre_close.close_path_selection`, and
      `pre_close.linked_deliberation_disposition` (re-plan R1, R2, R5);
    * the Cascade Close Sub-Procedure pre-invocation revalidation (including
      the engine-semantics re-probe), baseline capture, step 1 invocation, and
      steps 2-6 now point at the mutating `autoharness shipment cascade-close`;
    * the Linked-Deliberation Disposition step takes its step 0 inputs from the
      evidence record instead of from in-session Step 0(c) state, and never
      recomputes them: the selected close path and
      reason from `pre_close.close_path_selection`, the engine decision from
      `pre_close.engine_semantics` (rebuilt with A1e
      `engine_semantics_from_record`), the disposition snapshot from
      `pre_close.linked_deliberation_disposition`, and the path baseline from
      `observation_set` (SAFE_CLOSE) or `out_of_manifest_descendants`
      (CASCADE). That input source is the only change to the step (re-plan
      cycle-2 C2-5). Steps 1-6 are unchanged: step 1 still re-runs the
      planner after the close with that recorded engine decision and halts
      unless the fresh plan matches the snapshot on IDs, link kinds, linking
      members, record paths, hashes, settled outcomes, and unresolved
      references, while every other deliberation's archive-or-retain outcome
      still comes from live referrers; step 3 still re-checks the
      shared-reference guard before each single-artifact archive. Under an
      UNVERIFIED engine the step still mutates nothing. The step stays the only archiver of a disposition-set
      deliberation. The command never archives one (038-DL D3a, one archiver);
    * every close runs `autoharness shipment cascade-close --classify-only` first;
    * the mutating `cascade-close` invocation **is** the destructive command.
      It needs the same operator approval that the direct `backlogit shipment
      ship` call needs today (intercom auto-check or operator clearance;
      Principle VII). Plain `--classify-only` needs none, because it is
      no-clobber and only creates a new record; `--classify-only
      --replace-pre-close` overwrites an existing record and needs the same
      approval;
    * a direct `backlogit_ship_shipment` MCP or `backlogit shipment ship` CLI call
      is a **P-005 deviation** on either path (the A4 gate also refuses its
      closure);
    * the prose invariants stay as the specification the command implements.
  * The routing table in the skill (AN-F03/AN-F04):

    | Mode | Exit | Skill action |
    |---|---|---|
    | `--classify-only` | 0 (CASCADE) | Obtain destructive-command approval, then run mutating `cascade-close` |
    | `--classify-only` | 3 (SAFE_CLOSE selected: classifier SAFE_CLOSE, or engine UNVERIFIED) | Safe-close steps 1-10, then the Linked-Deliberation Disposition step, citing the verdict record as `close_evidence` |
    | mutating | 0 | Run the Linked-Deliberation Disposition step with its inputs from the evidence record, then write the closure artifact with `close_path: cascade` and `close_evidence` |
    | mutating | 3 | Reached only when no `cascade`-selected `--classify-only` record preceded the run, which the routing above never does. Nothing was mutated: HALT, operator review, and never SAFE_CLOSE on this result (INV-P4). A selected-path change after a CASCADE `--classify-only` selection is exit 4, never 3 |
    | either | 2, 4 | HALT. Nothing was mutated. Exit 4 includes an engine re-probe difference and any difference from the `cascade`-selected `--classify-only` record, and is never answered with SAFE_CLOSE. Fix the input, or ask the operator |
    | either | 5, 6, 7, 8 | HALT. Operator review. No commit of the backlog root, no retry, no direct call |

  * No edited surface places a linked deliberation in `allowed_ids` or
    `required_ids`.
  * The operational-closure frontmatter change (`close_path`,
    `close_evidence`) is A5b (`192.020-T`), not this unit.
* **Verifiable outcome (characterization-first, no new test file).** The
  existing doc tests (`tests/test_flat_manifest_closure_docs.py`,
  `tests/test_shipment_reconcile_*.py`,
  `tests/test_linked_deliberation_disposition_consumers.py`, and
  `tests/test_closure_contract_nondrift.py`) pass before the edit and after
  it, every wording they pin is preserved, and the full unittest suite is
  green with the refreshed checksum. The new structural, parity, and
  nondrift assertions are A5c (`192.021-T`; Copilot PR #481 T9).
* **Depends on:** A4b (`192.016-T`). **Harness surface:**
  `harness-surface:none`.
* **Posture:** characterization-first (run the existing doc tests before
  editing). **Size:** M. **Complexity:** low.

### A5b — operational-closure skill (template and mirror)

* **Goal:** the operational-closure half of the former A5, split out by
  Copilot PR #481 T9 (A5 spanned six files).
* **Files:** `templates/skills/operational-closure/SKILL.md.tmpl`,
  `.github/skills/operational-closure/SKILL.md`, and that entry's checksum
  and note line in `.autoharness/harness-manifest.yaml`. This is one atomic
  rendered-surface triple, like A5's. Test assertions are A5c.
* **Changes:**
  * The closure artifact frontmatter gains `close_path` (`cascade` |
    `safe_close`) and `close_evidence` (the
    `docs/closure/evidence/{S}-{F}-close-evidence.json` path built by
    `build_evidence_path`), and the evidence JSON is committed with the
    closure artifact.
  * The `### Step 3a: Validate the Closure Artifact with the
    Closure-Evidence Gate` heading is kept verbatim, and no closure filename
    is restated outside the contract-derived form.
  * No edited surface places a linked deliberation in `allowed_ids` or
    `required_ids`.
  * Every wording pinned by an existing test is preserved; new assertions
    land in A5c.
* **Verifiable outcome (characterization-first, no new test file).** The
  existing doc tests (`tests/test_flat_manifest_closure_docs.py` and
  `tests/test_closure_contract_nondrift.py`) pass before the edit and after
  it, and the full unittest suite is green with the refreshed checksum.
* **Depends on:** A5 (`192.008-T`). **Harness surface:**
  `harness-surface:none`.
* **Posture:** characterization-first (run the existing doc tests before
  editing). **Size:** S. **Complexity:** low.

### A5c — Closure-routing doc assertions

* **Goal:** the test half of the former A5, split out by Copilot PR #481 T9.
  It pins the A5 (shipment-reconcile) and A5b (operational-closure) edits.
* **Files:** `tests/test_flat_manifest_closure_docs.py` (extended). One
  file.
* **Tests (three scenarios):**
  1. **Structural assertions:** in both the template and the mirror, the
     `cascade-close` command, the routing table, the destructive-approval
     sentence, and the P-005 wording appear; Step 0(c) names
     `--classify-only` and the three `pre_close` fields
     (`engine_semantics`, `close_path_selection`, and
     `linked_deliberation_disposition`); the Linked-Deliberation Disposition
     step's input sentence names the evidence record as its source; and no
     edited surface places a linked deliberation in `allowed_ids` or
     `required_ids`.
  2. **Rendered parity (AN-F05):** a new parity assertion pins LF-normalized
     equality between the rendered template and the installed mirror for
     each edited section (the Step 0(c) block, the Cascade Close
     Sub-Procedure, and the operational-closure frontmatter block). Existing
     tests cover only the Output bullet, Step 3a, and the Ship paragraph.
  3. **Nondrift pin:** `tests/test_closure_contract_nondrift.py` stays green
     unchanged. The operational-closure Step 3a heading is kept verbatim, and
     no edited surface restates a closure filename outside the
     contract-derived form.

  The new assertions pass against the A5 and A5b edits and fail if any
  pinned phrase is removed from either the template or the mirror.
* **Depends on:** A5b (`192.020-T`). **Harness surface:**
  `harness-surface:none`.
* **Posture:** test-after-edit (assertions over the A5 and A5b edits).
  **Size:** S. **Complexity:** low.

### A6 — Ship agent P-015 pointer (template and mirror)

Copilot PR #481 T10 split the former four-file A6: the test assertions are
A6b.

* **Goal:** the Ship agent P-015 post-merge step 2c pointer to
  `autoharness shipment cascade-close` (template and mirror).
* **Files:** `templates/agents/_ship.agent.md.tmpl`,
  `.github/agents/_ship.agent.md`, and that entry's checksum line in
  `.autoharness/harness-manifest.yaml`. This is one atomic rendered-surface
  triple: `tests/test_crash_resumption_protocol.py` and
  `tests/test_checkpoint_payload_contract.py` assert the mirror's manifest
  checksum, and parity tests compare template and mirror, so the three
  cannot be split further.
* **Changes:**
  * In post-merge step 2c, every close starts with `--classify-only`. CASCADE is
    executed only through `autoharness shipment cascade-close`, with the same
    destructive-command approval, and the closure artifact needs `close_path` plus
    `close_evidence`.
  * Re-plan: the pointer names the command's engine-semantics gate (no cascade
    unless `select_close_path` selects CASCADE on a VERIFIED engine probed on
    the CLI surface; otherwise exit 3, and a re-probe difference is exit 4).
    It also names the skill's Linked-Deliberation Disposition step, which runs
    after the close with its inputs from the evidence record and remains the
    only archiver.
  * The closure-evidence contract sentence names the new frontmatter keys.
  * Pointer-level only. The routing table lives in the skill, not here.
  * Frontmatter is **not** touched (C owns it).
* **Verifiable outcome (characterization-first, no new test file).** The
  existing Ship tests (`tests/test_ship_safe_close_pointer.py`,
  `tests/test_closure_contract_nondrift.py`, the manifest-checksum coherence
  checks in `tests/test_crash_resumption_protocol.py` and
  `tests/test_checkpoint_payload_contract.py`, and
  `tests/test_telemetry_ship_lifecycle.py`) pass before the edit and after
  it, every wording they pin is preserved, and the full unittest suite is
  green with the refreshed checksum. The `**Closure-evidence contract**`
  paragraph stays a single line in each file, with the new keys inside it,
  because
  `tests/test_closure_contract_nondrift.py::test_template_and_installed_mirror_parity`
  asserts exactly one such line. The new pointer assertions are A6b
  (`192.022-T`; Copilot PR #481 T10).
* **Depends on:** A5c (`192.021-T`; was A5 `192.008-T` before Copilot PR
  #481 T9/T10). A6 follows the whole A5 family, so the three
  `harness-manifest.yaml` checksum edits of A5, A5b, and A6 stay serial.
  **Harness surface:** `harness-surface:none`.
* **Posture:** characterization-first. **Size:** S. **Complexity:** low.

### A6b — Ship agent step 2c pointer assertions

* **Goal:** the test half of the former A6, split out by Copilot PR #481 T10
  (A6 spanned four files).
* **Files:** `tests/test_ship_safe_close_pointer.py` (extended; the existing
  Ship structural P-015 pointer test). One file.
* **Tests (two scenarios):**
  1. **Pointer assertions:** in both `templates/agents/_ship.agent.md.tmpl`
     and `.github/agents/_ship.agent.md`, step 2c starts every close with
     `--classify-only`, executes CASCADE only through `autoharness shipment
     cascade-close`, names the command's engine-semantics gate and the
     skill's Linked-Deliberation Disposition step, and requires
     `close_path` plus `close_evidence`.
  2. **Rendered parity (AN-F05):** a rendered-section parity assertion for
     step 2c. The Ship `**Closure-evidence contract**` paragraph stays a
     single line in each file, with template/mirror parity and the new keys
     inside it.

  The new assertions pass against the A6 edit and fail if a pinned phrase is
  removed from either file.
* **Depends on:** A6 (`192.009-T`). **Harness surface:**
  `harness-surface:none`.
* **Posture:** test-after-edit (assertions over the A6 edit). **Size:** XS.
  **Complexity:** low.

### A7 — Docs: command reference and the portable upstream backlogit request

* **Files:** `docs/gates-reference.md` (a "Shipment close commands" section that
  explains why it is not a gate, including the A3 exit-code table and `--json`
  fields, and the closure-evidence gate's new `failed_check` values and
  `warnings[]`), and
  `docs/bugs/2026-09-27-backlogit-shipment-ship-structured-evidence-request.md` (new).
* **Changes:**
  * The upstream request is self-contained and copy-ready for the backlogit
    workspace. It asks for:
    * a native `--json` result on `shipment ship`;
    * an optional `--evidence-out <path>` that emits the engine's own pre-close
      candidate set (`collectArchiveCandidateIDs`) and the post-close result;
    * a documented envelope;
    * an opt-in workspace setting that refuses a direct `shipment ship` or
      `backlogit_ship_shipment` unless an evidence path is supplied. This is the
      mutation-boundary enforcement AN-F01 asks for, and autoharness cannot
      implement it itself.
  * It states explicitly that autoharness does not depend on it.
  * Re-plan: the command reference documents the record fields
    `pre_close.engine_semantics` (including `invocation_surface`, with no
    probe excerpt; the probe's stdout excerpt is `tool.version_excerpt`),
    `pre_close.close_path_selection`,
    `pre_close.linked_deliberation_disposition`, and
    `post_close.linked_deliberation_drift`; the flat `allowed_ids` /
    `required_ids` definitions; the `--json` fields `engine_verdict` and
    `selected_close_path`; exit 3 (selected path not CASCADE, including an
    UNVERIFIED engine, nothing invoked) and exit 4 (an engine re-probe
    difference or failure, or a difference from a `cascade`-selected
    `--classify-only` record, halts and never SAFE_CLOSE); and that the gate
    does not re-check disposition-set deliberations (re-plan cycle-1 R2). The
    1.10.x `pre_close.linked_deliberations` key is not documented.
* **Tests (two checks, no new test scenario):** markdownlint, and
  `tests/test_docs_frontmatter_decodes.py`.
* **Depends on:** A4b (`192.016-T`; was A3d `192.015-T` before Copilot PR
  #481 T7, because A7 documents the gate's new `failed_check` values and
  `warnings[]`). **Harness surface:** `harness-surface:none`.
* **Posture:** docs-only. **Size:** S. **Complexity:** low.

## Dependency Graph

Re-plan cycle-1 R4/R5 (2026-10-02), revised by Copilot PR #481 cycle 1
(T7-T10). Direct edges (`X → Y` means Y depends on X). These 22 edges match
each unit's **Depends on** line, the dependency table in the Copilot cycle 1
amendment, and each task's backlog `dependencies`:

| # | Edge | Tasks |
|---|---|---|
| 1 | A1 → A1d | `192.001-T` → `192.017-T` |
| 2 | A1d → A1e | `192.017-T` → `192.018-T` |
| 3 | A1e → A1f | `192.018-T` → `192.019-T` |
| 4 | A1f → A1c | `192.019-T` → `192.011-T` |
| 5 | A1c → A1b | `192.011-T` → `192.002-T` |
| 6 | A1c → A2b | `192.011-T` → `192.013-T` |
| 7 | A1b → A3a | `192.002-T` → `192.004-T` |
| 8 | A3a → A2a | `192.004-T` → `192.012-T` |
| 9 | A2a → A2 | `192.012-T` → `192.003-T` |
| 10 | A2b → A2 | `192.013-T` → `192.003-T` |
| 11 | A2 → A3b | `192.003-T` → `192.005-T` |
| 12 | A3b → A3c | `192.005-T` → `192.014-T` |
| 13 | A3c → A3 | `192.014-T` → `192.006-T` |
| 14 | A3 → A3d | `192.006-T` → `192.015-T` |
| 15 | A3d → A4 | `192.015-T` → `192.007-T` |
| 16 | A4 → A4b | `192.007-T` → `192.016-T` |
| 17 | A4b → A5 | `192.016-T` → `192.008-T` |
| 18 | A4b → A7 | `192.016-T` → `192.010-T` |
| 19 | A5 → A5b | `192.008-T` → `192.020-T` |
| 20 | A5b → A5c | `192.020-T` → `192.021-T` |
| 21 | A5c → A6 | `192.021-T` → `192.009-T` |
| 22 | A6 → A6b | `192.009-T` → `192.022-T` |

```text
A1 → A1d → A1e → A1f → A1c ─┬─→ A1b → A3a → A2a ─┐
                            └─→ A2b ─────────────┴─→ A2 → A3b → A3c → A3 → A3d → A4 → A4b ─┬─→ A5 → A5b → A5c → A6 → A6b
                                                                                           └─→ A7
```

Manifest (linear topological) order: A1, A1d, A1e, A1f, A1c, A1b, A3a, A2a,
A2b, A2, A3b, A3c, A3, A3d, A4, A4b, A5, A5b, A5c, A6, A6b, A7 (22 tasks;
the 198-S manifest is 23 items with the covering feature `192-F` first).
A2b sits after A2a in the manifest only to keep the order linear. It has no
edge from A2a. The removed task edge "`192.004-T` depends on `192.003-T`"
(A3a on A2) is not in this graph, because A2 now depends on A3a through A2a.

(Earlier forms: before Copilot PR #481 cycle 1, 16 edges with A1 → A1c,
A5 → A6, and A3d → A7; before the cycle-1 splits, A1 → A1b → A3a → A2a → A2
→ A3b → A3 → A4 → A5 → A6, and A3 → A7; before the 2026-10-02 re-plan, A1 →
A1b → A2 → A3a → A3b.)

* A1d, A1e, and A1f implement the A1 record codec, and A1c extends A1's
  validator (its fixtures build dispositions with A1f
  `disposition_plan_to_record`). A1b, A2b, A2, A3b, A3c, A4, and A4b consume
  the A1-A1f contract, codec, and validator.
* A3a depends only on A1b's `StreamCapture`. It precedes A2, because the CLI
  engine probe needs its runner.
* A2a depends on A3a's `run_bounded` and `ResolvedBinary` seam (and, through
  A3a, on A1b and A1c).
* A2b depends only on A1c's record shape.
* A2 depends on A2a (the engine decision feeds both `select_close_path` and
  the disposition planner) and on A2b (the observation set).
* A3b depends on A2's snapshot type. A3c depends on A3b's `PostCloseResult`.
* A3 composes A1b, A2a (the step 5 engine re-probe), A2, A3a, A3b, and A3c. A3d
  wires A3 into `cli.py`.
* A4 follows A3d so the gate and the command land against one settled record
  shape. A4b extends A4's `close_evidence` check. A4 and A4b both edit
  `_evaluate_closure_evidence`, so they stay serial.
* A5, A5b, and A6 each touch `.autoharness/harness-manifest.yaml`, so they
  stay serial (A6 depends on A5c, which follows A5b).
* A4, A4b, A5, A5b, A5c, A6, and A6b must ship in the same release unit (one
  PR; label `release-unit-a4-a6`). The stricter gate must never land ahead of
  the skill and agent routing that produces its evidence.
* A7 documents the shipped command behavior and the closure-evidence gate's
  new `failed_check` values and `warnings[]`, so it follows A4b (Copilot PR
  #481 T7).
* The task-level edges are the 22 rows above and the dependency table in the
  Copilot cycle 1 amendment.

## Decisions and Rationale

See deliberation D-A1 through D-A6 (all Stage-recommended, pending operator
confirmation).
*Superseded: the operator confirmed D-A1 through D-A6 on 2026-09-27T22:50-07:00,
including the D-A3 amendment below. Every inline "Stage-recommended, pending operator
confirmation" qualifier on D-A1 to D-A6 or on the D-A3 amendment in this plan (R6,
A4, and this section) is superseded. See
[Operator Rulings](#operator-rulings-2026-09-27t2250-0700--post-review-amendment).*

* The command lives in autoharness, and the upstream request does not block.
* The evidence is committed under `docs/closure/evidence/` and kept permanently.
* SAFE_CLOSE gets a verdict record, and (review cycle 1, amending D-A3 — Stage-recommended,
  pending operator confirmation) the gate requires that record rather than only
  warning. Without it, a self-declared `safe_close` would bypass R5 (AN-F01).
* A machine-readable `close_path` key is added.
* The contract stays in code, not in `schemas/`.
* Re-plan (2026-10-02): the 201-S flat-cascade contract (038-DL D2, D3a, D4a)
  is adopted in every affected unit. See
  `docs/decisions/2026-10-02-198-s-flat-cascade-replan-deliberation.md` and the
  Re-plan amendment section at the top of this plan.

The command does not depend on 179-F / 185-S, which is unclaimable by construction.
It implements minimal local fixed-argv, bounded-read, and atomic-write helpers. When
179-F eventually lands, the follow-up is to converge these onto its primitives, and
that follow-up is recorded here.

## Risks and Caveats

* **The JSON-RPC envelope shape is uncharacterized.** Mitigation: A3b's
  characterization-first step. An unparseable result is written to evidence and
  exits 6. It never passes silently.
* **A CASCADE mutation happened but the post-close write failed** (disk full).
  Mitigation: the `invoking` record already exists. The command exits 8 with
  `HALT — cascade evidence post-close write failed`, and any later run halts with
  exit 7 on that record. The skill forbids committing the backlog state until an
  operator reviews it.
* **An evidence file in the repository could carry secrets.** Mitigation:
  redaction of every persisted free-text field, and bounded excerpts. backlogit's result carries IDs and
  SHAs only, `--no-update-check` removes the only network call, and the evidence
  JSON is part of the reviewed closure PR diff. Residual: a finite redactor cannot
  prove arbitrary stderr is secret-free. This is accepted, because backlogit is a
  local file-backed tool with no credential inputs (SL-F04).
* **A hand-forged evidence record would pass the gate.** The record is an audit
  trail, not an attestation. Forging it is a P-005 violation. Mutation-boundary
  enforcement is requested upstream in A7.
* **PATH trust is unchanged from today** (SL-F03). Pinning a trusted absolute
  binary path in the registry is a follow-up, out of scope under P-021 C1.
* **Windows:** the atomic replace over an open file is covered in A1b's tests, and
  test-fixture directories are cleaned up with bounded retry (compound 034-DL
  pattern). The command itself never deletes its probe directories (A3a/A2a;
  Copilot PR #481 T3/T4, constitution VII).
* **Merge overlap** with 192-S / 197-S on `_ship.agent.md*`. They touch different
  sections, and Ship rebases.
* **Private `shipment_closure` names are reused in production** (re-plan
  cycle-1 R6, R12; cycle-2 C2-2, C2-4): A2a's sanitizer matches
  `_RELEASE_VERSION_PATTERN`; A2b traverses with `_scan_backlog`,
  `_enumerate_descendants`, and `_read_artifact_record`; and A4b's
  observation-set re-check calls `_check_path_containment` and
  `_read_artifact_record`. They are reused, not restated, so the probe,
  the observation set, and the gate apply the merged rules exactly. Under
  the private-name rule in the re-plan amendment, each is imported lazily
  inside the function that uses it, never at module top level of `cli.py`
  or a `shipment_close/` module, so an upstream rename cannot break CLI
  import. The A3b parity test module pins their existence and signatures,
  so a rename fails the tests first. M1 still governs the flat sets, which
  are re-derived locally and parity-pinned (A3b), and `_closure_scope_ids`
  and `_is_engine_inert` stay test-only imports.

## Plan Hardening Signals

* Public API, schema, or contract change — **present** (new CLI command group, new
  closure frontmatter keys, a stricter gate).
* Security or compliance-sensitive behavior — **present** (persisting subprocess
  output; redaction).
* Migration or destructive action — **present** (it wraps the destructive cascade;
  the gate tightens for new artifacts).
* External integration — **present** (backlogit CLI subprocess).
* High runtime or rollback risk — **present** (the closure path used by every
  shipment).

Requires plan hardening: yes

## Runtime Verification and Closure

* A3 and A4 change runtime CLI surfaces.
* Environment precheck: `backlogit --version` resolves outside the workspace root
  and reports the version recorded in A3's characterization step. `git status` of
  the scratch workspace is clean before the run.
* Runtime proof: in a scratch copy of a fixture workspace created under the
  Git-ignored `.proof-scratch/` directory of this repository (constitution IV:
  never outside the workspace; confirm the ignore rule with `git check-ignore`
  first, NOROW-F18; never the live `.backlogit/`; the scratch copy is removed
  only through the operator-approval path, constitution VII),
  run `autoharness shipment cascade-close` against the real `backlogit` binary on
  a CASCADE-eligible fixture. Confirm that the record is written,
  `postcondition_verdict: pass` holds, and `autoharness gate closure-evidence`
  returns PASS for an artifact that cites it. Then delete the record and confirm
  the gate FAILs with `failed_check: close_evidence`. Re-run `cascade-close` on
  the same pair and confirm exit 2 (`evidence already finalized`) with no second
  backlogit spawn. Re-plan: also confirm the record carries
  `engine_semantics.verdict: VERIFIED` with `probe_surface` and
  `invocation_surface` both `cli`, a `close_path_selection` of `cascade`, and a
  `linked_deliberation_disposition` whose `planning_error` is `null`.
* Blocked path: if the real binary is unavailable or its version differs from the
  characterized one, the runtime proof is recorded as `BLOCKED` with the reason
  (P-012), never as PASS on the fake-binary tests alone.
* Closure: this feature's own closure artifact records `close_path`. If its closure
  is itself a CASCADE, it is the first dogfood use of the command.

## Plan Hardening

* **Hardening required:** yes. All five signals are present.
* **Learnings consulted:**
  * `docs/compound/2026-09-27-175-s-closure-evidence-gate-hardening-lessons.md`
    (textual containment before any filesystem call; regular entries only; truthful
    negative records);
  * `docs/compound/2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md`
    (`archived_ids` is a transition log, so the two-set gate is keyed on the
    pre-close snapshot);
  * `docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md` (a
    classifier verdict is final, with no substitution).
* **Instructions consulted:** `circuit-breaker.instructions.md` (log bounds and
  redaction), `backlogit.instructions.md`, and `constitution.instructions.md`.
* **Protected invariants:**
  * INV-P1: no CASCADE invocation without a durable pre-close record.
  * INV-P2: `allowed_ids` / `required_ids` are computed only from the pre-close
    snapshot, never from a post-close re-read.
  * INV-P3: the two set checks stay separately labelled and fail independently
    (B57F9E24).
  * INV-P4: no fallback to SAFE_CLOSE after a CASCADE verdict. Refusing to run is a
    halt, not a substitution.
  * INV-P5: already-committed closure artifacts and the pipeline-topology consumer
    are unchanged.
  * INV-P6: evidence content is bounded and redacted, and the raw capture beyond the
    excerpt is never persisted.
* **ProposedAction / ActionRisk:**

  | ProposedAction | ActionRisk | Approval |
  |---|---|---|
  | The wrapper invokes the destructive `shipment ship` | high | Same as today (the P-015 classifier authorizes it); no new authority |
  | Tighten the closure-evidence gate for every write-time invocation (CASCADE and, per review cycle 1, SAFE_CLOSE) | medium | Plan-review PASS; the operator can revert with a one-commit rollback of A4 |
  | Persist subprocess output into the repository | medium | Redaction tests in A1 are a merge prerequisite |
  | Edit the skill and agent templates plus mirrors and manifest checksums | low | Checksums refreshed from the raw staged blob (IM-12) |

* **Rollback:** each unit is a separate commit. Reverting A5, A5b, and A6
  (with their assertion units A5c and A6b) restores the
  prose path. Reverting A4 restores the old gate. The command itself is additive.
  Rollback trigger: any closure that the new gate FAILs incorrectly, or any wrapper
  crash during a real closure. In that case Ship halts and records a P-005 deviation
  rather than falling back silently.
* **Monitoring and validation window:** the next three CASCADE closures after the
  merge record `close_path: cascade` with a PASSing gate. Ship reports any exit 5 or
  6 as a residual-risk record.
* **Review-gate capability risk:** no reviewer subagent tool is exposed in this
  Stage runtime. The review must declare its `dispatch_mode:` and literal
  `decision:` marker. An external-CLI reviewer on the anchor route is preferred.
* **Unresolved operator decisions:** D-A1 through D-A4 (Stage-recommended). None
  blocks safe execution.

### Hardening Pass 2 (2026-09-27, Stage resumption)

The first pass above (written with the plan) recorded triggers and invariants but
left operational gaps. This pass closed them in the unit text. Each item names the
unit it changed.

* **Additional learnings consulted:**
  * `docs/compound/2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md`
    (a timeout is not a clean negative signal, so a timed-out cascade is
    `indeterminate`, not "no mutation");
  * `docs/compound/2026-07-01-subprocess-validation-gating.md` (argv-array only,
    no `shell=True`, runtime state out of the tracked tree).
* **Code facts verified for this pass:** the closure-evidence gate
  (`src/autoharness/cli.py` `_evaluate_closure_evidence`) runs
  `frontmatter_predicate` before `discoverability`, and `BLOCKED` already fails
  `topology._closure_artifact_complete`; no workflow or script re-gates committed
  closure artifacts; `backlogit shipment ship` accepts `--sha`, `--message`,
  `--author`, and the global `--cwd`, `--jsonrpc`, `--no-update-check` flags;
  committed closure artifacts use the `merge_commit` frontmatter key;
  `tests/test_closure_contract_nondrift.py` pins the single-line Ship contract
  paragraph and the Step 3a heading.
* **Hardening items:**
  * **H-B1 (A3):** an `invoking` phase is written atomically before spawn, so a
    crash or kill between spawn and the post-close write leaves a detectable
    in-flight record. `mutation_state` is recorded, and a timeout or non-zero
    exit is `indeterminate` unless a byte-level re-read proves otherwise.
  * **H-B2 (A1, A2, A3):** no-clobber. A `post_close` record is never replaced
    (exit 2). An `invoking` record halts with exit 7. Only a `pre_close` record
    may be replaced, and only by the mutating mode or by the approval-gated
    `--classify-only --replace-pre-close`; plain `--classify-only` refuses to
    overwrite it (exit 2). Re-plan cycle-1 R1: the mutating mode never
    overwrites a `cascade`-selected `pre_close` record except by the exact-match
    re-stamp of A3 step 4; any difference exits 4. Copilot PR #481 T6: every
    `pre_close` replacement by a different run (that re-stamp, the mutating
    mode over a `safe_close`-selected record, and `--replace-pre-close`) is an
    A1b pre_close takeover, an atomic compare-and-swap that requires the
    expected prior `run_id` returned by the existing-record check.
  * **H-B3 (A3):** one exit-code table covering 0/2/3/4/5/6/7 (and 8 after review cycle 1), each with its
    mutation possibility, and a single HALT rule: no retry, no direct
    `backlogit shipment ship`, no SAFE_CLOSE substitution, and no commit of the
    backlog root after 5/6/7 until an operator review.
  * **H-B4 (A1):** redaction runs before the excerpt is sliced, over a margin
    window, so a boundary-split secret cannot leak. The capture is streamed, so
    memory stays bounded.
  * **H-B5 (A2, A3):** input validation (IDs, a 40-hex SHA, message and author
    length with no NUL or newline) happens before any write. backlogit is pinned
    to the workspace with `--cwd`. Only stdout is parsed.
  * **H-B6 (A3a):** the binary is resolved with `shutil.which`. A binary inside
    the workspace root, or a symlinked or reparse-point binary, is refused. The
    resolved path and version are recorded. Timeout kills the process tree by
    PID, and the timeout is bounded to 30-900 s. Re-plan cycle-1 R3:
    `cli.binary` must be a bare name (`^[A-Za-z0-9_-]+$`), the resolved
    basename must equal it, and every version probe runs in a fresh, empty
    probe directory inside the workspace (under the Git-ignored
    `.autoharness/gates/cascade-close/probe/`), never the workspace root, and
    never deleted automatically (Copilot PR #481 T3/T4; constitution IV, VII).
  * **H-B7 (decomposition):** the subprocess runner was split out of A3 as A3a, and
    review cycle 1 split further into A1/A1b and A3b/A3. Re-plan cycle-1 R4
    split again: A1c out of A1, A2b out of A2, A3c out of A3b, A3d out of A3,
    and A4b out of A4. Every unit now touches at most two files (the A1b
    package marker and the A5/A6 rendered template/mirror surfaces are noted
    in the Implementation Units granularity table), has at most four test
    scenarios, and is size S or M, inside the 2-hour rule.
  * **H-B8 (A4):** new checks run after the existing checks, so no existing
    `failed_check` is reordered. Evidence-path textual containment runs before any
    filesystem call, followed by a regular-file check and a 512 KiB size cap.
    `merge_commit` is cross-checked when present. The `failed_check` vocabulary
    and `warnings[]` are documented. "New artifacts" is replaced by the verified
    write-time-only fact.
  * **H-B9 (A5, A6):** nondrift constraints are stated explicitly (the single-line
    Ship contract paragraph, the Step 3a heading, and no restated closure
    filenames). The skill's exit-code mapping is spelled out.
  * **H-B10 (runtime verification):** an environment precheck, an OS-temp scratch
    workspace, a re-run no-clobber proof, and an explicit `BLOCKED` path (P-012).
* **Added protected invariant:**
  * INV-P7: a CASCADE invocation leaves exactly one durable record whose phase
    shows how far it got (`pre_close`, `invoking`, or `post_close`). No path
    overwrites a record that reached `invoking` or `post_close`.
* **Additional ProposedAction / ActionRisk:**

  | ProposedAction | ActionRisk | Approval |
  |---|---|---|
  | Kill a timed-out backlogit process tree mid-cascade | high | No new authority: the result is always `indeterminate` and exit 6, followed by an operator review before any further close action |
  | Refuse to run on an existing `invoking` record (exit 7) | low | None. This is a halt, not a mutation |

* **Residual risk (accepted, carried to review):** the evidence record is an audit
  trail, not a cryptographic attestation. A hand-forged record would pass the gate.
  Forging it is a P-005 violation, and detection is left to review and to the
  record's hashes. Cross-checking the live archive state at gate time is out of
  this plan's scope under P-021 C1.
* **Review-gate capability (restated):** reviewer subagent dispatch is not exposed
  in this Stage runtime. Cross-model personas go through the external Copilot CLI
  on the anchor route (`gpt-6-sol`), and the always-on personas are applied inline
  by Stage (`dispatch_mode: same-model-declared-degradation` for inline passes,
  declared in the review record).

### Hardening Pass 3 (2026-10-02, re-plan onto the 201-S contract)

This pass extends the protected invariants for the stash `1263B218` re-plan.
It introduces no new design. Each invariant restates a decision of
`docs/decisions/2026-10-02-198-s-flat-cascade-replan-deliberation.md` (038-DL
D2, D3a, D4a) as a testable plan invariant.

* **Additional sources consulted:**
  * `docs/decisions/2026-09-29-backlogit-1-11-cascade-linked-deliberation-alignment-deliberation.md`
    (038-DL);
  * `docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md` (201-S);
  * `src/autoharness/gates/shipment_closure.py` on `main` (`654b143d`):
    `assess_cascade_engine_semantics`, `select_close_path`,
    `compute_linked_deliberation_disposition`, and the private
    `_closure_scope_ids`, `_is_engine_inert`, `_check_path_containment`,
    `_RELEASE_VERSION_PATTERN`, `_read_artifact_record`, `_scan_backlog`, and
    `_enumerate_descendants` (re-plan cycle-1 R6, R9, R12; cycle-2 C2-2,
    C2-4).
* **Added protected invariants:**
  * INV-P8: `allowed_ids` and `required_ids` are flat (038-DL D2).
    `allowed_ids = closure_scope(S) = items(S) ∪ {S}`, and the A3b parity test
    pins it to `_closure_scope_ids` (M1). `required_ids = {S} ∪ qualifying feature members ∪ {x ∈ items(S): not truly archived pre-close}`,
    and the same parity test pins the "truly archived" check to
    `_is_engine_inert` (exact `str` `"archived"` only; re-plan cycle-1 R9).
    Neither set ever holds a disposition-set deliberation. No record,
    fixture, or test reintroduces a `validated_linked_deliberations` term.
    A disposition-set deliberation that is archived or modified by the
    cascade is `linked_deliberation_drift` (exit 5), never a set member.
  * INV-P9: no cascade without a `VERIFIED` engine on the same surface (038-DL
    D4a). `shipment ship` is spawned only when `select_close_path` selects
    CASCADE over an `EngineSemanticsDecision` that A2a probed on the CLI
    surface, through the same resolved absolute binary the command invokes.
    Every UNVERIFIED decision, including a probe failure, fails closed to
    SAFE_CLOSE (exit 3, nothing invoked) when no `cascade`-selected
    `--classify-only` record exists. A pre-invocation re-probe difference or
    failure, or any difference from a `cascade`-selected `--classify-only`
    record, halts with exit 4, leaves that record byte-identical, and never
    substitutes SAFE_CLOSE (INV-P4).
    The command never archives a deliberation. The skill's Linked-Deliberation
    Disposition step is the only archiver (038-DL D3a).
* **Hardening items:**
  * **H-C1 (A2a, A1):** the validator re-runs the merged
    `assess_cascade_engine_semantics` and `select_close_path` over the recorded
    raw inputs, so a hand-edited verdict or selection is rejected, and a later
    widening of the verified minor lines needs no record-shape change.
  * **H-C2 (A1c, A2, A2b, A4b; re-plan cycle-1 R2 and cycle-2 C2-1, C2-5;
    amends R5a of the re-plan deliberation):** the observation set is
    path-keyed. The A4 gate has no planned-`archive` exemption and no
    `stranded_linked_deliberation` warning.
    * Under a `VERIFIED` engine, the observation set never contains a
      disposition-set deliberation. Rationale: the skill's
      Linked-Deliberation Disposition step is the sole archiver. After the
      close, it re-runs the planner with the recorded engine decision. The
      fresh plan must match the snapshot on IDs, link kinds, linking
      members, record paths, hashes, settled outcomes, and unresolved
      references, but every other deliberation's archive-or-retain outcome
      comes from live referrers. A gate exemption or check keyed on the
      pre-close planned outcome would therefore misfire (the executed
      outcome may legitimately differ from the recorded planned outcome).
      Engine drift on those deliberations (re-plan item 4) is detected at
      close time by A3c's post-close re-collection, which is the
      authoritative point.
    * Under an UNVERIFIED engine (a `safe_close` record only), the
      observation set contains every `records[]` path of each disposition
      whose outcome is not `already-archived`, and A4b re-checks each one
      byte-identical. A1c forbids a planned `archive` under an UNVERIFIED
      engine, and the skill's disposition step mutates nothing, so the
      re-check cannot misfire. It closes the AN-F07 residual: an
      unauthorized direct cascade on a 1.10.x engine that archives linked
      deliberations. This narrows R5a's "never contains one" to the
      `VERIFIED` case. Under this plan's amendment rule, the plan text wins
      over the deliberation.
    * Stranded-advisory surfacing at the gate stays in the deferred stash
      scope `3B43CE5A` / `D79EA53A`. The pre-close disposition snapshot stays
      in the record (item 5) for A3c drift detection.
  * **H-C3 (decomposition; re-plan cycle-1 R4):** A2a is a separate S / low
    unit, and A2b (S / medium) takes the observation set out of A2, so A2
    stays inside the 2-hour rule. The other re-plan units are also split:
    A1c, A3c, A3d, and A4b. The granularity table under Implementation Units
    records files and test-scenario counts for all 16 units (22 after
    Copilot PR #481 cycle 1 added A1d, A1e, A1f, A5b, A5c, and A6b). None
    exceeds four scenarios.
* **Additional ProposedAction / ActionRisk:**

  | ProposedAction | ActionRisk | Approval |
  |---|---|---|
  | Run the read-only `backlogit version` probe twice per mutating run | low | None. It is read-only and passes `--no-update-check` |

* **Review state:** the 2026-09-27 plan-review PASS below predates this pass.
  The re-plan was re-reviewed on 2026-10-02 (cycles 1-2, P-021 C6):
  PASS_WITH_FOLLOWUPS. See the review record.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

* Review record: `docs/reviews/2026-09-27-cascade-close-evidence-capture-plan-review.md`.
  It is authoritative for findings, dispositions, and persona coverage.
* Re-review (2026-10-02, P-021 C6, stash `1263B218`): cycles 1-2 over the
  re-plan, verdict **PASS_WITH_FOLLOWUPS** (no open P0/P1). The follow-up is
  the Stage re-harvest of 198-S. See the review record's re-review sections.
* Gate: **PASS** under severity rule C4, with 0 open P0 and 0 open P1, after three
  review-fix cycles and a bounded fix-verification loop confined to the cycle-3
  fixes.
* Plan hardening was required and is satisfied (the original record plus
  Hardening Pass 2).
* Persona coverage, all seven selected personas:
  * inline passes: Constitution, Python, Scope Boundary, and Learnings;
  * independent anchor-route passes (`gpt-6-sol`, external Copilot CLI):
    Architecture Strategist, Security Lens, and Agent-Native Parity.
  * Declared degradation: `TOOL_DEGRADED: reviewer-subagent-dispatch — declared
    fallback: single-agent persona pass`.
* Stage-recommended decisions pending operator confirmation: the D-A3 amendment
  (SAFE_CLOSE fails closed), acceptance of the benign direct-cascade residual, and
  acceptance of the SL-F04 and SL-F07 residuals.
  *Partly superseded (2026-09-27T22:50-07:00): the D-A3 amendment is
  operator-confirmed. See Operator Rulings below for the residual acceptances.*

## Operator Rulings (2026-09-27T22:50-07:00) — post-review amendment

The operator ruled on the staging deliberation's open items. Verbatim:

> "Confirm 1-4. 5. Set Ship's context_tier to long_context in the template. Set Ship's max_subagent_tier to 3 in its template."

For this plan (192-F / 198-S), the effects are:

* **Ruling 2:** D-A1 to D-A6 are confirmed, including the review-cycle-1 D-A3
  amendment. The `closure-evidence` gate fails closed for SAFE_CLOSE without a valid
  `--classify-only` verdict record, as well as for CASCADE without a valid evidence
  record. The D-A3 decline fallback (revert A4's SAFE_CLOSE branch to a warning) is
  therefore moot.
* **Ruling 1:** D-P2's `dag-root` recommendation is confirmed. Shipment 198-S carries
  the `dag-root` label, and the ordering-only placeholder edge 198-S ← 189-S is
  removed. 199-S still blocks on 198-S.
  *Superseded by the 2026-10-02 re-plan: dag-root removal recommended (198-S
  now has an explicit blocks edge to 201-S). See the re-plan amendment, item
  6, and `docs/decisions/2026-10-02-198-s-flat-cascade-replan-deliberation.md`
  (re-plan cycle-1 R16).*
* **Not named in the ruling:** the acceptance of the benign direct-cascade residual
  (AN-F01 / AN-F07) and of the SL-F04 and SL-F07 residuals. These are the review's
  accepted residuals. Under the original harvest terms, they stand unless the
  operator overrides them before Ship claims 198-S.
* Ruling 5 does not touch this plan.
* **Review state:** this amendment applies operator rulings and is not new design. It
  comes after the review's PASS, it reopens no finding, and it needs no re-review.
  The review record carries a matching note, and the deliberation holds the full
  mapping in its section "Operator rulings (2026-09-27T22:50-07:00)".

