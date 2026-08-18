---
shipment: 140-S
feature: 131-F
feature_pr: 360
merge_commit: 57b5af38008905ea47ce01887c1680205b75350e
merged_at: "2026-08-18T06:02:02Z"
reviewed_head: 14c32ef8
closure_pr: null
closure_reviewed_head: null
closure_status: PENDING_CLOSURE_PR
compaction_status: done
conditions: []
---

# 140-S / 131-F Post-Merge Closure — Topology Gate Directional-Predicate Reliability Hotfix

Shipment 140-S fixed a P1 gate-correctness defect in
`src/autoharness/gates/topology.py::_prior_shipment_id`: the reverse-edge
suppression check was direction-blind, so a numerically **higher** shipment
declaring a normal forward dependency on the target silently suppressed the
target's own numeric-predecessor fallback — a fail-open condition in a
safety gate. The fix restricts suppression to numerically **lower**
declaring shipments only, matching the directional semantics the fallback
exists to support. This shipment satisfies the outstanding
`topology-forward-dependent-suppression-fix` condition recorded in
`docs/closure/139-S-130-F-post-merge-closure.md` (updated separately, this
same session, to `satisfied: true`).

## Merge Confirmation

- PR #360 merged to `main` at `2026-08-18T06:02:02Z` with merge commit
  `57b5af38008905ea47ce01887c1680205b75350e`.
- The merge commit has two parents, preserving the P-009 merge-commit
  strategy.
- `git merge-base --is-ancestor 57b5af38... origin/main` confirmed exit 0.
- Closure began from synced `main` at `57b5af38...`.

## Runtime Verification

**Surface**: `cli` (per `.autoharness/workspace-profile.yaml`
`runtime_validation.validator_manifest.surfaces`) — the topology-gate fix is
exercised through the `autoharness` CLI's `gate pipeline-topology` command
and the pytest-driven gate test suite.

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | `command` (CLI) |
| Runtime probe | `autoharness --help` — exits 0, prints CLI help text |
| Canonical gate | `pytest tests/test_gates_topology.py -q` plus full repo suite `pytest tests/ -q` |
| Result | Targeted: 94/94 tests, 113/113 subtests pass (93 pre-existing + 1 new regression test). Full suite: 1550 passed, 1 pre-existing unrelated flaky failure (`test_checklist_report_prints_non_interactively`, confirmed reproducing with or without this fix), 20 skipped. |
| Live gate exercise | `autoharness gate pipeline-topology --mode agent --shipment 140-S --phase lifecycle --json` returned `exit_code: 0`, confirming the fixed predicate operates correctly against this session's own live shipment/branch topology (140-S active on `feat/topology-gate-directional-predicate-reliability-hotfix` at the time of the check, one active shipment matching target). |
| Verdict | **PASS** |

`releasability.required` is `false` in the workspace profile with
`required_evidence: []`, so no additional structured releasability artifact
beyond the evidence above is mandated; `status_when_satisfied: READY`
applies.

## Backlog Reconciliation

The shipment manifest (`131-F` + `131.001-T`) includes the covering feature
itself as a root member with its only child present, so
`classify_shipment_close_path` returned **CASCADE** — the P-015 verified
fully-covered-root exception would ordinarily apply. However, at the time
closure ran, both manifest items (`131-F`, `131.001-T`) had already been
individually archived via the standard Step 2 task-completion sequence
(`backlogit move --status done`, which the registry's routing rules
auto-relocate to `archive/`) during task execution, before the closure step
began. Rather than invoke the cascade `backlogit shipment ship` command
against an already-partially-archived state — which the cascade
sub-procedure's post-condition checks (`archived_ids` must match exactly)
have no documented tolerance for — this closure used the **manual
safe-close** procedure instead, treating the pre-archived manifest state as
an unresolved precondition that falls back to safe-close per the P-015
fallback language.

Verified post-conditions (manual safe-close):

| Check | Result |
| --- | --- |
| `131-F` | already in `archive/` at closure time → classified `pre-archived`, not re-archived |
| `131.001-T` | already in `archive/` at closure time → classified `pre-archived`, not re-archived |
| Protected set | empty (covering feature `131-F` is itself a manifest member with no other siblings) — trivially intact throughout |
| `140-S` live status | moved to `shipped` via `backlogit move 140-S --status shipped`, re-read and verified `status: shipped` |
| `140-S` archive record | archived via `backlogit archive 140-S`, re-read and verified `archived_status: shipped` |

**Process note (see compound doc
`docs/compound/2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md`)**:
the safe-close mutation was initially run before the mandatory pre-closure
`lifecycle` topology gate check, which then correctly failed
(`LIFECYCLE_NO_ACTIVE_SHIPMENT`) because the target was no longer active.
Since nothing had been committed yet, this was corrected by restoring the
pre-close `queue/140-S.md` state from the feature-branch merge commit,
re-running the lifecycle gate (`exit_code: 0`, confirmed above), and then
redoing the safe-close mutation in the correct order.

`backlogit sync` completed after the safe-close (re-indexed artifacts). No
active or queued artifacts remain for the `131-F`/`131.001-T`/`140-S`
lineage; `138-S` (which declares `140-S` as a blocking predecessor) remains
`queued`, unmodified by this session per explicit operator instruction.

## Operational Closure

- **Healthy signals**:
  - Feature PR #360 merged with a verified 2-parent merge commit.
  - Targeted and full-suite canonical tests passed (94/94 + 113/113
    subtests targeted; 1550/1551 full suite, 1 pre-existing unrelated
    flake).
  - CI was green at the feature PR merge gate.
  - P-018 copilot-review gate `SATISFIED` — Copilot review returned **zero
    threads** (clean pass, confirmed via GraphQL `reviewThreads` empty
    query).
  - Multi-persona adversarial review (Stage-authored,
    `docs/reviews/2026-08-18-topology-gate-forward-dependent-directional-predicate-review.md`)
    PASS, 0 unresolved P0/P1 (6 findings; 2 P1 resolved, 3 P2 resolved, 1 P3
    accepted+deferred) — independently re-verified by Ship (H1/H2/H5/H7)
    before merge.
  - Manual safe-close post-conditions verified (protected set intact,
    shipment record status/provenance verified at each step).
- **Failure signals to watch**:
  - Any future shipment whose manifest items are individually archived
    (via ordinary task-completion routing) before the shipment-level
    closure step runs will hit the same pre-archived-vs-cascade tension
    documented above; default to manual safe-close in that situation
    rather than invoking the cascade command against an already-mutated
    state.
  - Any future closure session must run the `lifecycle` topology gate
    strictly before any shipment-status-mutating step — see the new
    compound doc for the recovery procedure if this order is
    inadvertently reversed and not yet committed.
  - The topology gate's numeric-adjacency fallback: this is now the
    **third** correction to the same predicate (skip-violator → any-direction
    → directional); any future shipment-numbering scheme change should be
    checked against `tests/test_gates_topology.py::ImplicitNumericPredecessorTests`
    before being relied upon.
- **Validation window**: immediate post-merge closure on 2026-08-18 after
  `main` synced to merge commit `57b5af38...`, merged at
  `2026-08-18T06:02:02Z`.
- **Rollback trigger**: revert merge commit `57b5af38...` if the directional
  predicate begins misclassifying shipment predecessors with **live,
  observed** impact (a false `PRECLAIM_ACTIVE_SHIPMENT_PRESENT`/
  `BRANCH_MISMATCH` block, or a missed genuine predecessor block that lets
  an ineligible shipment claim proceed). No such impact has been observed;
  the fix is verified via reproduction plus the full targeted and full-suite
  regression evidence above.
- **Owner**: Ship agent for closure evidence; operator `@softwaresalt` for
  merge approval and release follow-up routing.
- **Residual follow-up**: none — Copilot review returned zero threads on
  the feature PR; the three Copilot threads on the staging PR (#359) were
  documentation-accuracy findings in Stage-owned artifacts, replied to and
  resolved per
  `docs/compound/2026-08-18-ship-role-boundary-copilot-findings-in-forbidden-artifacts.md`,
  and require no further action.
- **Predecessor unblock**: `140-S`'s own closure condition on `139-S` is now
  satisfied (see `docs/closure/139-S-130-F-post-merge-closure.md`'s
  Addendum). `138-S` declares both `139-S` and `140-S` as blocking
  predecessors; both are now `shipped`/`archived`, so `138-S` is
  gate-eligible for a **future** session's mechanical abandonment. This
  session does not abandon `138-S` per explicit operator instruction.

## Compaction (P-020)

`compact-context --target all` invoked per the mandatory per-merge trigger.
Scanned `docs/memory/`, `docs/plans/`, `docs/closure/`. The just-closed
release unit's own session memory (originally written to
`docs/memory/2026-08-18-ship-140-s-topology-hotfix-full-lifecycle.md`)
qualified under the completed-work rule (Phase 2) regardless of age;
compacted to
`docs/memory/compacted/2026-08-18-140S-131F-compacted.md` and the verbose
original archived to
`docs/archive/memory/2026-08-18-ship-140-s-topology-hotfix-full-lifecycle.md`.
No plan consolidation was performed: the `131-F` plan/hardening/review docs
are Stage-authored artifacts, and Ship's Role Boundary forbids creating or
modifying plan/review artifacts — consolidating them into a decided-plan is
left to a future Stage session. No closure-record compaction candidates
existed (both `139-S` and `140-S` closure docs are same-day, under the
`threshold_days` age gate). `compaction_status: done` recorded in this
document's frontmatter.

**Closure verdict (interim): PENDING_CLOSURE_PR.** Runtime verification
passed and backlog reconciliation (manual safe-close) completed with all
post-conditions verified. This document's `closure_status` will be updated
to `READY` once the post-merge closure PR (backlog archival + doc updates
committed on `post-merge/131-f-topology-gate-directional-predicate-hotfix`)
has completed local review, the §1.9 readiness gate, and received explicit
operator approval and merge.
