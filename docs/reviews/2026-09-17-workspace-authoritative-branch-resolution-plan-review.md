---
title: "Plan review — Workspace-authoritative implementation-branch resolution"
description: "Multi-persona plan review of docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md, gating harvest. Covers the evidence-backed merge of stash 14F4D6F3 into 86498B64. Inline persona coverage under declared subagent-dispatch degradation. Plan hardening confirmed complete before review. Gate decision: PASS, 0 P0 / 0 P1 open."
doc_type: review
source: docs/reviews/2026-09-17-workspace-authoritative-branch-resolution-plan-review.md
date: 2026-09-17
plan_path: docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md
plan_revision: 2
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 1
source_stash_id: 86498B64
stash_ids:
  - 86498B64
  - 14F4D6F3
review_cycle: 2
review_cycles_remaining: 1
dispatch_mode: declared-degradation
decision: PASS
p0_open: 0
p1_open: 0
tags:
  - "plan-review"
  - "pipeline-topology"
  - "branch-ownership"
  - "merged-stash"
---

# Plan review — Workspace-authoritative implementation-branch resolution

## Dispatch mode

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent
persona pass`. Every selected persona rubric applied inline with a separate
finding list. No persona skipped.

Personas applied: Constitution Reviewer, Python Reviewer, Scope Boundary
Auditor, Learnings Researcher (always-on); Architecture Strategist and
**Security Lens Reviewer** (cross-model, inline — triggered because the plan
parses externally-supplied workspace data into a value used for branch
selection, an external trust boundary).

## Plan hardening (P-006)

Declares `requires_plan_hardening: "yes"`, `plan_hardening_status: complete`.
Warranted: the change is on the sole claim-authority gate engine, alters
fail-closed behaviour, and changes gate JSON consumed by two agent templates.
Hardening outputs visible in the reviewed plan: the absent-versus-malformed
asymmetry stated as the load-bearing invariant, the explicit Git short-name
validation character set, and R2's structural single-call-site test.

## Merge review (decision D1)

The Scope Boundary Auditor specifically examined the merge of `14F4D6F3` into
`86498B64` against this repository's own recorded precedent — the `86498B64`
annotation and the Scope Boundary Auditor verdict in
`docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md`,
which held that same-file adjacency is not same-contract necessity.

**Merge upheld.** That precedent separated *sequencing* authority from
*branch-naming* authority — two different contracts. `14F4D6F3` and `86498B64`
are both branch-naming authority: same file, same authority question, same
precedence mechanism, same output fields. The precedent does not separate them;
it is the test they pass. Both stash IDs are carried on the plan, the feature,
every task, and this review, and neither entry is destroyed.

## Final Reviewed Contract

One `resolve_expected_branches()` used by all four phases with strict
precedence `explicit_contract` > `workspace_convention` (reserved, empty,
tested-never-selected) > `title_alias`; present-but-malformed explicit value
fails closed as `IMPLEMENTATION_BRANCH_MALFORMED` with **no** fallback;
`resolution_source` / `selected_branch` / ordered `expected_branches` emitted on
both pass and block paths; the seven-row matrix from `14F4D6F3` plus `018-S` /
`020-S` / `025-S` field regressions plus a no-field compatibility invariant.
Nine tasks. Declarative config templates deferred.

## Findings

### Cycle 1 — findings raised and remediated in place

| ID | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| F1 | Constitution Reviewer | **P0** | Cycle-1 draft let a malformed explicit value fall back to title aliases, which inverts the defect: a broken declared contract would silently resolve to a wrong branch. | **Resolved.** Absent-versus-malformed asymmetry is now the stated load-bearing invariant; R1 asserts rungs 2/3 were **not** consulted. |
| F2 | Security Lens Reviewer | **P0** | Branch short-name validation was unspecified, admitting path traversal (`..`), option injection (leading `-`), and control characters from externally-supplied workspace data. | **Resolved.** Explicit character-set validation enumerated in the plan: non-empty, no leading/trailing `/`, no `..`, no ASCII control characters, no space, no ``~^:?*[\``, not ending `.lock`, not exactly `@`. |
| F3 | Scope Boundary Auditor | **P1** | Cycle-1 draft included the declarative `.autoharness/config.yaml` branch-template tier, which the source design doc itself recommends deferring and which collides with `165-F`'s adjacent `gates.pipeline_topology.unsequenced_shipment` key. | **Resolved.** Deferred per D1. Rung 2 ships reserved and empty so the later addition is additive, and no config key is added. |
| F4 | Architecture Strategist | **P1** | Nothing prevented a phase retaining a private branch-derivation path, which is how the original defect survived. | **Resolved.** T3 removes every other path; R2 adds a structural test asserting exactly one call site computes branches. |
| F5 | Learnings Researcher | **P1** | Plan did not acknowledge `docs/compound/2026-08-17-branch-rename-after-pr-open-auto-closes-pr.md`, which makes the "rename the branch" workaround actively destructive. | **Resolved.** Cited in the Problem section as the reason the workaround is not merely inelegant. |
| F6 | Python Reviewer | P2 | The two token names (`IMPLEMENTATION_BRANCH_MALFORMED`, `BRANCH_POLICY_INVALID`) were both in play with no precedence. | **Resolved.** D1 picks the field-naming token as emitted and records the other as the design-doc synonym. |
| F7 | Scope Boundary Auditor | P2 | Retiring the `025-S`/`020-S` title-alias workarounds could disturb a shipment mid-flight. | **Resolved.** T8 sequenced last; R5 bounds it to backlog data for shipments whose explicit contract the resolver now honors. |

### Cycle 2 — verification pass

No new P0 or P1. Two P3 observations, **accepted without change**:

* **P3-1** (Architecture Strategist): rung 2 is deliberately dead in this
  release. Accepted — it ships with a test pinning that it is never selected,
  so its behaviour is observed rather than unobserved.
* **P3-2** (Python Reviewer): `018-S` is a downstream workspace's shipment and
  its regression must be expressed as a fixture, not a live lookup. Accepted;
  T6 is fixture-based.

## Sequencing precondition

`86498B64`'s recorded precondition — harvest immediately after `173-S` is
executed — was verified directly: `backlogit shipment get 173-S` and `174-S`
both report `status: archived`. The recorded merge-contention window on
`topology.py` with `165-F`'s `_shipment_readiness_check` work is **closed**
(R4). No blocker.

## Persona coverage

| Persona | Findings | Open P0/P1 |
|---|---|---|
| Constitution Reviewer | F1 | 0 |
| Python Reviewer | F6, P3-2 | 0 |
| Scope Boundary Auditor | F3, F7, merge review | 0 |
| Learnings Researcher | F5 | 0 |
| Architecture Strategist | F4, P3-1 | 0 |
| Security Lens Reviewer | F2 | 0 |

## Gate decision

**PASS.** 0 P0 open, 0 P1 open. Cleared for harvest.

Explicitly verified: no `--force` path appears anywhere in the plan or its
tests; no vendor identifier enters the engine; workspace policy remains
declarative data only; sequencing authority is untouched.
