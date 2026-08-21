---
title: "Stage session - restore direct 144-S -> 146-S edge for pipeline-topology pre_claim compatibility"
date: 2026-08-21
agent: stage
route: "claude-opus-5 / anthropic / high (P-013.5)"
branch: chore/stage-144-s
head: 3cbc55e8
stash_consumed: []
stash_created: []
deliberations_archived: []
features: []
tasks: []
shipments: [144-S, 145-S, 146-S, 147-S]
execution_order: "146-S -> 147-S -> 144-S -> 145-S"
terminal_state: "queued; 146-S is the only claimable shipment and now passes the pre_claim topology gate"
---

# Stage session memory - 2026-08-21 (topology-compatibility edge)

## Scope

Bounded, Stage-owned, same-contract correction. One dependency edge added, plus
the Stage-owned narrative surfaces that described the graph as a simple linear
chain or claimed the direct `144-S -> 146-S` edge had been removed.

**P-021 C1: PASSES.** Same contract and same surface as the `B19E9662` staging
session that created the chain - this corrects that session's own dependency
wiring. No deferred stash entry created.

## The defect

The mandatory `pipeline-topology --phase pre_claim` gate blocked the intended
first shipment `146-S`.

`_prior_shipment_id` in `src/autoharness/gates/topology.py` infers an implicit
predecessor by NUMERIC ADJACENCY. It suppresses that inference only when a
numerically LOWER shipment names the target **directly** in its own
`dependencies` list - it does not walk transitive paths.

Pre-correction edges were `144-S -> 147-S`, `147-S -> 146-S`, `145-S -> 144-S`.
No lower-numbered shipment named `146-S` directly, so the heuristic fell through
to numeric adjacency, selected queued `145-S` as `146-S`'s predecessor, and the
gate returned:

```text
PREDECESSOR_NOT_SHIPPED: predecessor 145-S is not in a shipped terminal state
```

The chain was transitively correct; the heuristic simply could not see it.

## Correction

Added the redundant `blocks` edge `144-S -> 146-S` with the official
`backlogit_add_dependency` operation, followed by `backlogit_sync_index`.

`144-S` is numerically lower than `146-S` and now declares it directly, so
`_prior_shipment_id("146-S")` returns `None` and the false inference is
suppressed.

## Final edge set

| Edge (direction = "depends on") | Role |
|---|---|
| `147-S -> 146-S (blocks)` | **critical path** |
| `144-S -> 147-S (blocks)` | **critical path** |
| `145-S -> 144-S (blocks)` | **critical path** |
| `144-S -> 146-S (blocks)` | **redundant topology-compatibility edge** |

### Critical path vs. redundant edge

The distinction matters and must not be collapsed in any downstream record:

* The **critical path** `146-S -> 147-S -> 144-S -> 145-S` is what orders
  execution.
* The **redundant edge** `144-S -> 146-S` exists solely to satisfy the gate's
  direct-edge heuristic. It is transitively implied by
  `144-S -> 147-S -> 146-S`, so it adds no ordering constraint that was not
  already present.
* **`144-S` still blocks on `147-S` and can NEVER run before it.** The redundant
  edge does not make `144-S` eligible any earlier, and any reading that suggests
  `144-S` may precede `147-S` is wrong.

The mandatory post-merge instruction reload after `147-S` merges, before `144-S`
is selected or claimed, is **unaffected and still required**.

## Verification (read-only; no build, test, or linter run)

| Check | Before | After |
|---|---|---|
| `_prior_shipment_id("146-S")` | `145-S` | `None` |
| `_shipment_readiness_check(pre_claim, 146-S)` | `blocked / PREDECESSOR_NOT_SHIPPED` | **`passed`**, `predecessor_ids: []` |
| `compute_dag_readiness().cycle_detected` | `False` | `False` |
| `compute_dag_readiness().ready_set` | `('146-S',)` | `('146-S',)` |
| `compute_dag_readiness().critical_path` | - | `('146-S', '147-S', '144-S', '145-S')` |

* Readiness for `147-S`, `144-S`, `145-S` remains
  `blocked / PREDECESSOR_NOT_SHIPPED` - queue eligibility is `146-S` alone.
* Full `topology.evaluate(mode=agent, phase=pre_claim, target=146-S)` evaluated
  against `146-S`'s own canonical branch -> `blocked: False`, `exit_code: 0`,
  all five checks passed (`detect_before_consistency`,
  `active_shipment_invariant`, `branch_ownership`, `worktree_topology`,
  `shipment_readiness`).
* **Why not the raw CLI:** `autoharness gate pipeline-topology --mode agent
  --shipment 146-S --phase pre_claim --json` cannot return PASS from this
  session - it short-circuits on `branch_ownership` with `BRANCH_MISMATCH`
  because Stage is on `chore/stage-144-s`, and branch switching is prohibited
  for this task. Equivalent direct gate-function evidence is recorded above; the
  branch check is Ship's to satisfy when it claims `146-S` on the correct
  branch.
* `backlogit_sync_index` -> 913 items, unchanged before and after.

## Files changed

| File | Change |
|---|---|
| `.backlogit/queue/144-S.md` | one added `dependencies` entry: `- 146-S` |
| `docs/memory/2026-08-20-stage-b19e9662-ship-pre-archived-execution-contract.md` | edge list split into critical path vs. redundant edge; correction addendum appended |
| `docs/memory/2026-08-20-stage-144-s-closure-valid-membership.md` | "edge removed" claim corrected |
| `docs/memory/2026-08-20-stage-145-s-closure-valid-membership.md` | "edge removed" claim corrected |
| `docs/memory/2026-08-20-stage-7852ce0d-baseline-red-prerequisite.md` | "edge removed" claim corrected; "three-node linear chain" verification line marked superseded |
| `docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-plan.md` | sequencing bullet corrected |
| `docs/reviews/2026-08-20-ship-pre-archived-manifest-member-execution-review.md` | acceptance row added for the retained edge |
| `docs/memory/2026-08-21-stage-144-146-topology-compatibility-edge.md` | this record (new) |

`.backlogit/queue/144-S.md` also had a spurious trailing blank line removed:
the backlogit writer appended one, leaving the file ending `---\n\n` while its
sibling manifests `145-S`, `146-S`, `147-S` all end `---\n`. Normalized to match,
consistent with the prior `normalize shipment manifest endings` corrections.

## Boundary statement

Stage made **no** source, test, template, or config edit; ran **no** build,
test, or linter; made **no** commit, push, PR, or branch switch; claimed **no**
shipment; created **no** worktree. The only backlog mutation is the single
dependency edge. No shipment membership, manifest, task, or size/complexity
field was touched. The operator's pre-existing uncommitted changes
(`.gitmodules`, `.mcp.json`, `references/*`, `diff_files.txt`) were not touched.

## Next step

`146-S` is claimable and passes the pre_claim topology gate. Ship claims `146-S`
on its own branch, then proceeds `147-S` -> (mandatory instruction reload) ->
`144-S` -> `145-S`.
