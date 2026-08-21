---
title: "Stage staging handoff - Ship pre-archived manifest-member execution contract (B19E9662)"
date: 2026-08-20
agent: stage
route: "claude-opus-5 / anthropic / high (P-013.5)"
branch: chore/stage-144-s
head: e88a8d62
pr: 375
stash: B19E9662
deliberation: "022-DL (archived 2026-08-20 to .backlogit/archive/022-DL.md)"
feature: 139-F
tasks: [139.001-T, 139.002-T]
shipments: [147-S]
execution_order: "146-S -> 147-S -> 144-S -> 145-S"
terminal_state: "queued; 146-S remains the only claimable shipment"
supersedes_execution_order: "146-S -> 144-S -> 145-S (recorded in docs/memory/2026-08-20-stage-7852ce0d-baseline-red-prerequisite.md and docs/memory/2026-08-20-stage-144-s-closure-valid-membership.md)"
---

# Stage handoff - Ship pre-archived manifest-member execution contract

## The blocker

The closure-membership correction at `e88a8d62` (this branch, PR #375) is
correct: manifests `144-S` and `145-S` now include their superseded, archived
children so `classify_shipment_close_path` returns **CASCADE** for P-015.

But the **installed** Ship contract `.github/agents/_ship.agent.md` still says,
at "Step 2: Task Execution Loop":

> For each task in the shipment/feature:
> 1. **Claim**: Move the task to active via `backlogit_move_item`.

That iterates the manifest unconditionally - no status filter, no
`pre-archived` classification, and no `shipment-reconcile mode: pre` intake
step (the template carries that intake step at Step 0.5 item 6; the installed
dogfood mirror does not). Running `144-S` under that contract would drive Ship
to claim archived `136.001-T`, which is stamped
`*** SUPERSEDED - NOT EXECUTABLE - DO NOT SCHEDULE ***`.

The Step 0.5 item 1a early-warning does not catch it: it halts only on
`active`/`done`, and an archived task carries `status: archived`.

Template-only guidance is insufficient - `144-S` executes under the INSTALLED
dogfood contract.

## P-021 classification

**C1 FAILS.** `e88a8d62` is a shipment-membership / closure-classifier surface.
This is the agent-instruction execution contract plus its regression-test
surface. Different contract, different test surface - so capture-first normal
intake applied, not an in-place fix.

Duplicate scan (unconditional): **CLEAN**. Active stash (12) and archived stash
(172) both scanned. Nearest neighbour `EDE3CC2D` is the P-015 cascade-**close**
path gap, already harvested as `132-F` / `141-S` and shipped. Different surface,
not a duplicate, nothing merged, nothing archived as a duplicate.

Late-identifier reconciliation: performed, **no result**. `review-thread ID:
N/A` because the finding came from a local Stage review of the working tree,
not a PR review comment. The `N/A` stands as a truthful terminal record.
Non-blocking.

## Pipeline outcome

| Artifact | ID / path |
|---|---|
| Stash | `B19E9662` (archived with forward refs) |
| Deliberation | `022-DL` (archived to `.backlogit/archive/022-DL.md`) |
| Plan | `docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-plan.md` |
| Hardening | `docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-hardening.md` |
| Review | `docs/reviews/2026-08-20-ship-pre-archived-manifest-member-execution-review.md` |
| Feature | `139-F` (queued, high) |
| Tasks | `139.001-T` (S / medium), `139.002-T` (S / low) |
| Shipment | `147-S` (queued, high, covering feature `139-F`) |

P-006 hardening: **required and performed** (H1-H7). Two plan amendments
applied: **A1** (the derivation is work-selection, never an integrity guard -
it must not suppress the item 1a `SHIPMENT_STATE_INCONSISTENT` halt, and
`already_done` must be reported distinctly from `pre_archived_skipped`) and
**A2** (no new template status variable - there is no `{{STATUS_ARCHIVED}}`).

plan-review: **PASS**, 0 unresolved P0/P1, 1 review-fix cycle of 3.
The P1 was real: the plan's originally-proposed closure-classifier regression
test **already exists and is green** as
`tests/test_shipment_closure_classification.py::test_mixed_pre_archived_and_queued_manifest_members_still_selects_cascade`
(plus four siblings), shipped by `132-F` / `141-S`. Amendment **A3** dropped the
duplicate and replaced it with a named cross-reference in the new module's
docstring.

## Execution chain (CHANGED this session)

```text
146-S  ->  147-S  ->  144-S  ->  145-S
```

Dependency edges (direction = "depends on"):

**Critical path** - these edges determine execution order:

* `145-S -> 144-S (blocks)` - pre-existing, unchanged
* `144-S -> 147-S (blocks)` - **NEW**
* `147-S -> 146-S (blocks)` - **NEW**

**Redundant topology-compatibility edge** - carries no scheduling meaning of
its own:

* `144-S -> 146-S (blocks)` - **PRESENT (restored 2026-08-21).** An earlier
  revision of this record described this edge as **REMOVED**; that statement is
  **superseded**. See the correction addendum at the end of this document.

`146-S` has no outbound edge and remains the chain source and the only
claimable shipment.

`147-S`'s manifest is `[139-F, 139.001-T, 139.002-T]` - all newly created,
all in `.backlogit/queue/`, **zero pre-archived members** - so it is safely
executable under the current, still-unfixed contract.

## MANDATORY post-merge instruction reload before 144-S

The fix only takes effect for a Ship session that reads the **merged**
`.github/agents/_ship.agent.md`. After `147-S` merges and its P-020 post-merge
closure completes, `main` agent instructions MUST be reloaded before `144-S` is
selected or claimed.

This is already contractually enforced on the dark-run path: the installed
Orchestrator's multi-shipment cursor-advance step mandates "**reload current
`main` agent instructions** - re-read the freshly merged Orchestrator and Ship
templates/instructions - before advancing the cursor or selecting the next
successor shipment". On an operator-driven advance the obligation is manual,
so it is recorded redundantly here, in `147-S`'s title, and in the plan.

## Verification performed (read-only; no build, test, or linter run)

* `backlogit_sync_index` -> 908 at session start, **913** at close.
* Closure classification, all four shipments -> **CASCADE**:
  `146-S` (`138-F`), `147-S` (`139-F`), `144-S` (`136-F`), `145-S` (`137-F`).
* Manifests unchanged for `144-S` `[136-F, 136.002-T, 136.003-T, 136.001-T]`,
  `145-S` (seven items), `146-S` `[138-F, 138.001-T]`. Only `147-S` is new.
* `backlogit dep list` -> `145-S -> 144-S`, `144-S -> 147-S`, `147-S -> 146-S`,
  `146-S` no outbound edge. Linear, acyclic, no dangling edge to `146-S`.
* `backlogit queue view --type shipment` -> **`146-S` alone** claimable.
* `147-S` covering feature derived as `139-F`; `size_composition` `S:2`,
  `unsized: 0`.
* Sizing persisted through the separate priority write:
  `139.001-T` = `size S / size_source agent / size_ruleset_version 2h-rule-v1
  / complexity medium`; `139.002-T` = `size S / ... / complexity low`.
* `backlogit doctor` -> 64 findings, **zero** touching `136`/`137`/`138`/`139`/
  `144`-`147`/`022-DL`/`B19E9662`. All are pre-existing `archived_from_self_ref`
  entries on the `003`-`009` series plus three `048` orphans, unrelated to this
  session.
* All three planning artifacts exist at the paths referenced by `139-F`,
  `139.001-T`, and `139.002-T`. No dangling reference.
* `022-DL` archive record carries `archived_from: .backlogit/queue/022-DL.md`
  (not self-referential).
* `.backlogit/stash.jsonl` is byte-unchanged (entry added then archived);
  `.backlogit/archive/stash.jsonl` gained `B19E9662` -> 173 entries.

## Boundary statement

Stage created planning artifacts, backlog records, and memory only. **No**
source, test, template, config, or instruction file was modified. **No** build,
test, or linter was run. **No** branch switch, commit, push, or PR. **No**
shipment claimed. **No** GitHub thread mutated. `.backlogit` bookkeeping and
`docs/` artifacts are left uncommitted in the working tree for Orchestrator
publication.

## Open follow-ups (recorded, not opened this session)

* `022-DL` open question 1: executable enforcement of the derivation via an
  `autoharness gate` subcommand or a `shipment_execution` module, replacing the
  prose contract with fail-closed logic. Deferred for blast radius and the
  2-hour rule while `144-S` is blocked.
* `docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`
  still records a Stage-owned follow-up with **no backlog ID** (cascade close
  archiving a `custom_fields.source_deliberation_id`-linked deliberation). It
  does not affect `147-S` - `139-F` carries no `source_deliberation_id` - and
  was deliberately not expanded into this bounded session.

---

## ADDENDUM 2026-08-21 - direct `144-S -> 146-S` edge RESTORED (topology-compatibility)

**Supersedes** the "REMOVED" line in the Execution chain section above. The
direct edge `144-S -> 146-S (blocks)` is **present**.

### Why the two-hop-only graph was wrong

The mandatory `pipeline-topology --phase pre_claim` gate blocks the intended
first shipment `146-S`. Its `_prior_shipment_id` helper
(`src/autoharness/gates/topology.py`) infers an implicit predecessor by NUMERIC
ADJACENCY, and suppresses that inference only when a NUMERICALLY LOWER shipment
declares the target **directly** in its own `dependencies`.

With edges `144-S -> 147-S`, `147-S -> 146-S`, `145-S -> 144-S`, no
lower-numbered shipment declared `146-S` directly. The heuristic therefore fell
through to numeric adjacency and selected queued `145-S` as `146-S`'s
predecessor, producing:

```text
PREDECESSOR_NOT_SHIPPED: predecessor 145-S is not in a shipped terminal state
```

The explicit chain is **transitively** correct but the heuristic does not walk
transitive paths - it matches only a direct edge.

### Correction applied

Added the redundant `blocks` edge `144-S -> 146-S` via
`backlogit_add_dependency`. `144-S` (numerically lower than `146-S`) now
declares `146-S` directly, so `_prior_shipment_id("146-S")` returns `None` and
the erroneous numeric-predecessor inference is suppressed.

### Final edge set

| Edge (direction = "depends on") | Role |
|---|---|
| `147-S -> 146-S (blocks)` | **critical path** |
| `144-S -> 147-S (blocks)` | **critical path** |
| `145-S -> 144-S (blocks)` | **critical path** |
| `144-S -> 146-S (blocks)` | **redundant topology-compatibility edge** |

**The redundant edge changes no ordering.** It is transitively implied by
`144-S -> 147-S -> 146-S`. `144-S` still blocks on `147-S` and **can never run
before `147-S`**. Effective execution order is unchanged:

```text
146-S  ->  147-S  ->  144-S  ->  145-S
```

The mandatory post-merge instruction reload before `144-S` (see above) is
**unaffected and still required**.

### Verification (read-only; no build, test, or linter run)

* Acyclic: `compute_dag_readiness` -> `cycle_detected: False`.
* `critical_path` -> `('146-S', '147-S', '144-S', '145-S')` - the redundant edge
  does not shorten it.
* `ready_set` -> `('146-S',)` - `146-S` is the ONLY eligible shipment.
* `_prior_shipment_id("146-S")` -> `None` (was `145-S` before the fix).
* `_shipment_readiness_check("pre_claim", "146-S", ...)` -> **passed**,
  `predecessor_ids: []` (was `blocked / PREDECESSOR_NOT_SHIPPED`).
* Readiness for `147-S`, `144-S`, `145-S` -> all still
  `blocked / PREDECESSOR_NOT_SHIPPED`, as intended.
* Full `topology.evaluate(mode=agent, phase=pre_claim, target=146-S)` on
  `146-S`'s own branch -> `blocked: False`, `exit_code: 0`, all five checks
  passed (`detect_before_consistency`, `active_shipment_invariant`,
  `branch_ownership`, `worktree_topology`, `shipment_readiness`).
* The `autoharness gate pipeline-topology ... --json` CLI could not itself
  return PASS from this session: it short-circuits on `branch_ownership`
  because Stage is on `chore/stage-144-s`, and branch switching is prohibited.
  Equivalent direct gate-function evidence is recorded above.
* Backlog delta: exactly one file, `.backlogit/queue/144-S.md` (one added
  `dependencies` entry). No shipment membership, task, or manifest change.
