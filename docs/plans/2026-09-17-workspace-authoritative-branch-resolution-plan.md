---
title: "Workspace-authoritative implementation-branch resolution for the pipeline-topology gate"
description: "Implementation plan routing every pipeline-topology branch decision through one shared resolve_expected_branches() applying strict precedence — explicit custom_fields.implementation_branch, then a reserved-but-empty workspace-convention rung, then title-derived aliases as fallback only — with a present-but-malformed explicit value failing closed as IMPLEMENTATION_BRANCH_MALFORMED and never falling back, gate JSON emitting resolution_source, selected_branch, and ordered expected_branches, and the seven-row regression matrix from stash 14F4D6F3 pinned alongside the 018-S/020-S/025-S field regressions."
doc_type: plan
source: docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md
date: 2026-09-17
status: reviewed
revision: 2
revision_note: "Revision 2 is the canonical statement of the intended design. Review findings were remediated in place; this document states exactly one binding requirement per topic. The bounded audit trail lives in `linked_review`."
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 1
source_prior_deliberation: docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md
source_prior_review: docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md
source_bug_report: docs/bugs/2026-09-16-autoharness-pipeline-topology-explicit-branch-contract-bug.md
source_stash_id: 86498B64
stash_ids:
  - 86498B64
  - 14F4D6F3
merged_stash_ids:
  - 14F4D6F3
prior_learnings:
  - docs/compound/2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md
  - docs/compound/2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
  - docs/compound/2026-08-17-branch-rename-after-pr-open-auto-closes-pr.md
linked_review: docs/reviews/2026-09-17-workspace-authoritative-branch-resolution-plan-review.md
covering_feature: 170-F
shipment: 178-S
requires_plan_hardening: "yes"
plan_hardening_status: complete
tags:
  - "pipeline-topology"
  - "branch-ownership"
  - "p-022"
  - "fail-closed-design"
  - "merged-stash"
---

# Workspace-authoritative implementation-branch resolution

## Provenance and merge

This plan covers **two stash entries merged on evidence** (decision **D1**):

* `86498B64` — the covering feature (workspace-driven branch
  resolution), carrying the open decision about declarative workspace templates.
  Its intake declares a source design document at
  `docs/design-docs/2026-09-10-autoharness-workspace-driven-branch-resolution-design.md`,
  which is **absent from this repository** as of 2026-09-17. The operative
  design record is the design summary preserved verbatim inside the `86498B64`
  stash entry; every requirement it states is restated in full in this plan, so
  no requirement below depends on the missing file. Recorded as an advisory
  provenance gap in the deliberation.
* `14F4D6F3` — the same defect observed in the field, carrying a seven-row
  regression matrix, acceptance criteria, and the
  `IMPLEMENTATION_BRANCH_MALFORMED` token name.

Both name `src/autoharness/gates/topology.py`, the same authority question
(what is the release unit's implementation branch called), and the same
mechanism. They are one contract. Both IDs are carried on this plan, on the
covering feature, on every task, and on the review; neither entry is destroyed.

`86498B64`'s recorded sequencing precondition — harvest immediately after
`173-S` is executed — is **satisfied**: `173-S` and `174-S` both report
`status: archived`.

## Problem

`_branch_aliases()` / `_resolve_shipment_from_branch()` in
`src/autoharness/gates/topology.py` build `expected_branches` only from
title-derived slug aliases. The authoritative P-022 branch contract recorded on
the shipment as `custom_fields.implementation_branch` is never read.

A shipment checked out on exactly the branch named in its own
`implementation_branch` is therefore false-blocked with `BRANCH_MISMATCH`
(`blocked: true`, exit 1) whenever its descriptive title does not slugify to
that branch. The block is fail-closed with no honored explicit-contract path,
so the only escapes are an unsafe `--force` or renaming the branch off its
authoritative contract — and renaming after a PR is open auto-closes the PR
(`docs/compound/2026-08-17-branch-rename-after-pr-open-auto-closes-pr.md`).

Observed on `025-S` and `020-S`, currently masked by temporary title-alias
workarounds; blocks downstream release unit `018-S`, whose explicit branch
cannot be renamed without violating P-016/P-022.

## Design

### Single resolver, strict precedence

One `resolve_expected_branches()` is the sole branch authority, used by **all
four phases** — `pre_claim`, `post_claim`, `lifecycle`, `ambient`. No phase may
compute branches by any other path.

| Rung | Source | `resolution_source` |
|---|---|---|
| 1 | Explicit `custom_fields.implementation_branch` on the shipment record | `explicit_contract` |
| 2 | Configured workspace naming convention — **reserved, empty in this release unit** | `workspace_convention` |
| 3 | Title-derived slug aliases (`_branch_aliases()`) | `title_alias` |

Rung 2 ships **present, tested, and empty**: a wired precedence position with
a test asserting it is currently never selected. This makes the deferred
declarative-template tier additive rather than a later restructuring. Per
decision **D1**, no `.autoharness/config.yaml` key is added by this release
unit; adjacency to `165-F`'s `gates.pipeline_topology.unsequenced_shipment`
key is noted and avoided.

### Fail-closed on malformed explicit value

A **present-but-malformed** `implementation_branch` — blank, whitespace-only,
not a valid Git branch short name, or otherwise unparseable — fails closed with
`IMPLEMENTATION_BRANCH_MALFORMED` and **never falls back to rung 2 or 3**.

This is the load-bearing asymmetry: *absent* means "no contract, fall back";
*present-but-invalid* means "a contract was declared and is broken, halt". The
design doc's `BRANCH_POLICY_INVALID` is recorded as a synonym so the design doc
remains readable; `IMPLEMENTATION_BRANCH_MALFORMED` is the emitted token
because it names the field rather than an abstract policy.

Validation is a Git branch **short name** check: non-empty, no leading/trailing
`/`, no `..`, no ASCII control characters, no space, no `~^:?*[\`, not ending
`.lock`, not exactly `@`.

### Gate output

Every phase's JSON gains, unconditionally:

* `resolution_source` — one of `explicit_contract`, `workspace_convention`,
  `title_alias`
* `selected_branch` — the single branch the gate considers authoritative
* `expected_branches` — the **ordered** list actually evaluated

These are emitted on both the pass and the block path, so a `BRANCH_MISMATCH`
report says which authority produced the expectation it is enforcing.

### Reader change

`FilesystemTopologyReaders.list_shipments()` parses `custom_fields.implementation_branch`
from the nested map, validates it, and surfaces it on `ShipmentState`.
Shipments without the field behave **exactly** as before — this is the
compatibility invariant, and it has its own regression case.

## Work Breakdown

| # | Task | Scope |
|---|---|---|
| T1 | Parse and validate `custom_fields.implementation_branch` in `list_shipments()`; add the field to `ShipmentState` | `src/autoharness/gates/topology.py` |
| T2 | Implement `resolve_expected_branches()` with the three-rung precedence and the empty reserved rung 2 | `src/autoharness/gates/topology.py` |
| T3 | Route all four phases through the single resolver; remove every other branch-derivation path | `src/autoharness/gates/topology.py` |
| T4 | Emit `resolution_source`, `selected_branch`, ordered `expected_branches` on pass and block paths | `src/autoharness/gates/topology.py` |
| T5 | Seven-row regression matrix from `14F4D6F3` | `tests/test_gates_topology.py` |
| T6 | Field regressions for `018-S`, `020-S`, `025-S`, plus the no-field compatibility invariant | `tests/test_gates_topology.py` |
| T7 | CLI-surface tests for the new JSON fields and the malformed-value exit path | `tests/test_gate_pipeline_topology_cli.py` |
| T8 | Retire the temporary title-alias workarounds on `025-S`/`020-S` | backlog data + docs |
| T9 | Gate documentation: precedence table, token table, migration note | `docs/` |

## Verification

* `PYTHONPATH=src python -m unittest discover -s tests` exits 0.
* All seven matrix rows pass, including both malformed-value rows.
* A shipment with no `implementation_branch` produces byte-identical gate JSON
  to `main` except for the three additive fields.
* `autoharness gate check` passes on every modified file.
* No `--force` invocation appears anywhere in the new tests or docs.

## Risks

| ID | Risk | Mitigation |
|---|---|---|
| R1 | Malformed explicit value silently falls back, re-creating the defect inverted | Dedicated matrix rows assert `IMPLEMENTATION_BRANCH_MALFORMED` and assert rungs 2/3 were **not** consulted |
| R2 | One of the four phases keeps a private branch-derivation path | T3 removes every other path; a structural test asserts exactly one call site computes branches |
| R3 | Rung 2 is dead code that rots | It ships with an explicit test asserting it is currently never selected, so its behaviour is pinned rather than unobserved |
| R4 | Merge contention with `165-F`'s `_shipment_readiness_check` work | `165-F`/`173-S` is **archived**; the recorded contention window is closed |
| R5 | Retiring the title-alias workarounds breaks a shipment mid-flight | T8 is sequenced last and touches only backlog data for shipments whose explicit contract the resolver now honors |

## Out of scope

* Declarative workspace-level branch templates in `.autoharness/config.yaml`
  (deferred per decision **D1** and the design doc's own recommendation).
* Any vendor identifier (ADO, Jira) in the engine.
* Repository-supplied executable branch rules — workspace policy stays
  declarative data only.
* Sequencing authority (`_shipment_readiness_check`, `dag-root`,
  `UNSEQUENCED_SHIPMENT`), which is a different contract surface.
* Any `--force` path.
