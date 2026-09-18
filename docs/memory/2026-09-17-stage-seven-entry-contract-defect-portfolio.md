---
title: "Stage session — seven-entry contract-defect staging portfolio (3EF5AAF2, 14F4D6F3, 86498B64, 76EBDE6D, C9CD24F3, 7F9CB5E9, 71200CBB)"
description: "Current-state Stage handoff for an exact operator-selected seven-entry stash scope. Records the per-entry disposition, the single evidence-based merge (14F4D6F3 into 86498B64), the one consolidated deliberation and one read-only spike, six reviewed implementation plans, six covering features with forty-eight two-hour-bounded tasks, and six serially-sequenced queued shipments rooted at declared dag-root 176-S. Also records two pre-existing DAG blockers surfaced rather than repaired, one provenance gap, one backlog-registry drift, one stale installed-CLI divergence, and the session degradation set (Engram circuit open, intercom unavailable)."
doc_type: memory
source: docs/memory/2026-09-17-stage-seven-entry-contract-defect-portfolio.md
date: 2026-09-17
updated: 2026-09-17
agent: stage
doc_status: superseded
superseded_by: docs/memory/2026-09-19-stage-remediation-cycle-3-current-state.md
superseded_note: "EXPLICITLY SUPERSEDED as a CURRENT-STATE surface. Preserved verbatim for provenance: it is an accurate record of what was true on 2026-09-17. It is NOT operative current-state input - its task count (48), serial shipment sequencing, decision_revision (1) and review state are all stale, and it predates the 168-S -> 176-S edge. Read docs/memory/2026-09-19-stage-remediation-cycle-3-current-state.md instead."
status: complete
scope_kind: portfolio
feature_ids:
  - 168-F
  - 169-F
  - 170-F
  - 171-F
  - 172-F
  - 173-F
shipment_ids:
  - 176-S
  - 177-S
  - 178-S
  - 179-S
  - 180-S
  - 181-S
source_stash_ids:
  - 76EBDE6D
  - 3EF5AAF2
  - 86498B64
  - 14F4D6F3
  - C9CD24F3
  - 71200CBB
  - 7F9CB5E9
merged_stash_ids:
  - 14F4D6F3
deferred_scope_expansions:
  - 7F9CB5E9
  - 71200CBB
source_decision: docs/decisions/2026-09-17-seven-entry-contract-defect-staging-portfolio-deliberation.md
decision_revision: 1
source_spike: docs/spikes/2026-09-17-post-claim-member-status-contract-spike.md
plan_sources:
  - docs/plans/2026-09-17-p004-red-phase-precondition-scoping-plan.md
  - docs/plans/2026-09-17-post-claim-member-status-contract-plan.md
  - docs/plans/2026-09-17-workspace-authoritative-branch-resolution-plan.md
  - docs/plans/2026-09-17-single-governing-plan-contract-plan.md
  - docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
  - docs/plans/2026-09-17-safe-close-record-transition-disposition-plan.md
review_sources:
  - docs/reviews/2026-09-17-p004-red-phase-precondition-scoping-plan-review.md
  - docs/reviews/2026-09-17-post-claim-member-status-contract-plan-review.md
  - docs/reviews/2026-09-17-workspace-authoritative-branch-resolution-plan-review.md
  - docs/reviews/2026-09-17-single-governing-plan-contract-plan-review.md
  - docs/reviews/2026-09-17-checkpoint-resume-hint-contract-plan-review.md
  - docs/reviews/2026-09-17-safe-close-record-transition-disposition-plan-review.md
degradations:
  - "engram unified_search / query_memory circuit OPEN (error-5001, content_record lacks chunk_id, 3 identical failures) — pack-routing deviation signal emitted; degraded evidence path was exact-path reads plus git grep / git log -S plus backlogit get/stash operations"
  - "agent-intercom unavailable in this CLI session — INTERCOM_DEGRADED, local operator visibility only, no phase broadcasts"
  - "reviewer-subagent-dispatch unavailable — declared fallback: single-agent inline persona pass (dispatch_mode: declared-degradation on all six reviews)"
---

# Stage session — seven-entry contract-defect staging portfolio

## Scope

Exact operator-selected stash scope, seven entries, every one given an explicit
disposition. No unrelated stash entry was pulled into implementation scope. The
session stopped at reviewed/harvested **queued** shipment artifacts: no claim, no
implementation, no build, no PR, no merge, no closure.

## Per-entry disposition

| Stash | Disposition | Feature | Shipment |
|---|---|---|---|
| `76EBDE6D` | Consumed as-is | `168-F` | `176-S` |
| `3EF5AAF2` | Consumed, **re-scoped** on evidence (D3) | `169-F` | `177-S` |
| `86498B64` | Consumed as **surviving identity** of merge D1 | `170-F` | `178-S` |
| `14F4D6F3` | **Merged into `86498B64`** on evidence (D1); both IDs preserved | `170-F` | `178-S` |
| `C9CD24F3` | Consumed as-is, with a recorded scope ceiling (D5) | `171-F` | `179-S` |
| `71200CBB` | Deliberated (P-021 C6); autoharness-owned half only (D6) | `172-F` | `180-S` |
| `7F9CB5E9` | Deliberated (P-021 C6); **not discarded**; owned half retained, upstream half escalated (D7) | `173-F` | `181-S` |

All seven were annotated with a forward reference and then **archived**
non-destructively via `backlogit stash archive`. Zero of the seven remain active;
103 unrelated stash entries were left untouched.

## Key evidence that changed the outcome

* **F1 — `P-002.6` does not exist in autoharness.** `git grep` over `*.md`/`*.tmpl`
  for `WAVE_NO_PROGRESS|ready_k` returns only the bug report itself;
  `git log -S "P-002.6" --all` and `git log -S "WAVE_NO_PROGRESS" --all` each
  return exactly one commit — `187526c0`, the commit that added the report.
  `.github/policies/workflow-policies.md` has `P-002` with no `.6` sub-clause, and
  the report's frontmatter carries
  `external_provenance.origin_repository: softwaresalt/backlogit`. The wave-admission
  contract is **downstream-authored**, so `3EF5AAF2` is not an autoharness policy
  conflict.
* **F2 — the canonical Ship contract already tolerates post-claim all-active.**
  `templates/agents/_ship.agent.md.tmpl:274` and its installed mirror
  `.github/agents/_ship.agent.md:322` both accept the all-active state
  immediately after this session's own claim. The template source reads, with
  its **unrendered template variable** left deliberately intact rather than
  substituted:

  ```text
  all {{STATUS_ACTIVE}} immediately after this session's own claim
  ```

  (`{{STATUS_ACTIVE}}` renders to `active` in this workspace; it is quoted here
  as template source, not as a leaked placeholder.) The adjacent
  `SHIPMENT_STATE_INCONSISTENT` early warning fires on the inverse condition.
  Corroborated by `docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`.
  The real defect is that this tolerance is **unnamed, unversioned and unenforced** —
  which is what `169-F` fixes, with no upstream backlogit change required.
* **D1 merge evidence.** `86498B64` and `14F4D6F3` name the same file
  (`src/autoharness/gates/topology.py`), the same authority question (what the
  release unit's implementation branch is called), and the same mechanism (one
  shared resolver, precedence `explicit custom_fields.implementation_branch` >
  configured convention > title-derived aliases, fail-closed on malformed explicit
  values). They differ only in token spelling. One contract, one feature, both
  source IDs carried on the feature, on the plan, and on every `170.*-T` task.

## Shipment sequence (all `queued`, none claimed)

```text
176-S  (dag-root)  ->  177-S  ->  178-S  ->  179-S  ->  180-S  ->  181-S
```

Each `blocks` edge was written on the **new** shipment only; no existing shipment
record was mutated. `176-S` is a **declared** root (`dag-root` label on backlog
data, version-controlled and review-gated) and **not** a bootstrap grant — no file
was created under `.autoharness/bootstrap-grants/`.

Root justification (D8): `176-S` removes the P-004 red-phase precondition that
currently blocks `168-S`, and `168-S` sits inside existing chain A. Attaching
`176-S` behind chain A's leaf `167-S` would place the fix *behind* the shipment it
unblocks — an unreachable-fix deadlock. A declared root is the only sequencing that
is both honest and reachable without mutating unrelated scope.

## Blockers surfaced, not repaired

* **BLOCKER-1 — `169-S` is `UNSEQUENCED_SHIPMENT`.** Confirmed by the working-tree
  topology gate: `predecessor_source: unsequenced`, remediation options
  `['record the real blocks edge', 'declare the shipment a root']`. `169-S` and its
  dependents `170-S`/`171-S`/`172-S` cannot be claimed. Out of the selected scope;
  the honest remedy (`169-S` blocked by `167-S`) mutates unrelated scope and needs
  operator authorization.
* **BLOCKER-2 — `168-S` is blocked at harness-ready by the P-004 defect.** The
  honest edge would be `168-S` blocked by `176-S`, which mutates `168-S` — out of
  scope. This is precisely why `176-S` is a declared root.
* **BLOCKER-3 (advisory) — the installed `autoharness` CLI is stale.**
  `C:\Python\Python314\Scripts\autoharness.exe` resolves to site-packages
  **1.5.0**, whose topology gate reports a false `PREDECESSOR_NOT_SHIPPED:
  predecessor 175-S` for `176-S`. The working-tree source at `src/` correctly
  reports `predecessor_source: declared_root`, `blocked: false`. Ship must
  reinstall from the working tree before relying on `autoharness gate
  pipeline-topology`.
* **Provenance gap (advisory).** `86498B64`'s intake declares an exact
  repository-relative design document at
  `docs/design-docs/2026-09-10-autoharness-workspace-driven-branch-resolution-design.md`,
  which is absent from the repository and appears in no commit. The operative
  design record is the design summary preserved verbatim inside the stash entry;
  every requirement is restated in full in the plan. Recorded in the deliberation
  and the plan.
* **Registry drift (advisory).** `.autoharness/backlog-registry.yaml` declares no
  `features.sizing` key and no size/complexity params on `create_task`/`update_task`,
  yet the live `backlogit_update_item` MCP tool and `backlogit update` CLI both
  accept `--size` / `--size-source` / `--size-ruleset-version` / `--complexity`.
  Structured fields were used; the registry should be reconciled.

## Validation performed

* Doc validation over all 14 new artifacts: frontmatter parses, required fields
  present, `source` matches path, single H1, zero unresolved `{{...}}` placeholders,
  all cross-referenced repository paths resolve (one allow-listed declared-missing
  path, documented above). **PASS 14/14.**
* Backlog hierarchy: 48/48 tasks parent to the correct feature. **PASS.**
* Two-axis sizing: 48/48 tasks carry a valid `size` and an independent valid
  `complexity`, with `size_source: agent` and
  `size_ruleset_version: autoharness-2h-v1`. No task exceeds `M`, so the 2-hour rule
  holds on the size axis; every `complexity: high` task is size-capped at `M` and
  cites its reviewed plan as its de-risking record. **PASS.**
* Manifest coverage: 54 manifest entries across six shipments, 54 unique, zero
  duplicates, zero harvested items uncovered. **PASS.**
* DAG: `autoharness gate dag-readiness` reports `cycle_detected: false`,
  `status: ok`. **PASS.**
* Dependency readiness semantics: `176-S` passes `pre_claim` as `declared_root`;
  `177-S` correctly blocks with `PREDECESSOR_NOT_SHIPPED: 176-S`. **PASS.**
* Plan-review closure: all six reviews `decision: PASS`, `p0_open: 0`,
  `p1_open: 0`, `review_cycle: 2`, one cycle remaining. **PASS.**
* Full test suite: `Ran 2344 tests ... OK (skipped=54)`. **PASS.**

## Next action for Orchestrator

Globally, `175-S` remains the existing eligible head of chain A. Within the newly
staged sequence, `176-S` is independently claimable now (declared root, predecessor
set empty, `pre_claim` passes on working-tree source). Nothing here was claimed.

---

## Remediation cycle 2 (final permitted fix cycle) — HEAD 6dfb2755

Local review cycle 2 returned **BLOCKED** on one root cause: the revision-3 plan
changes had never been propagated into the executable backlog records. Thirteen
operator P1 findings were raised (A1–A3, B4–B10, C11–C13). All thirteen are
closed at the record level; none was deferred.

### Provenance correction that matters most

The verification block above is **cycle-1 evidence**, including the
`Ran 2344 tests ... OK (skipped=54)` line. That test run was performed by Stage,
which Stage's role boundary categorically forbids — a **P-005 / P-010
violation**, now recorded as stash `750A7863`. Remediation cycle 2 executed **no**
test, linter, or build. The cycle-1 evidence is cited as cycle-1-sourced and was
neither re-run nor re-validated, because re-running it would repeat the identical
violation in order to verify it.

The `Plan-review closure: all six reviews decision: PASS` line above is likewise
superseded. The six verdict manifests now read **REMEDIATED-PENDING-REVIEW** at
plan revision 4: Stage authored this remediation and cannot review it, so the
next reviewer pass is attempt 05.

### Design decisions worth carrying forward

* **`relates_to` is what makes a reference edge onto a never-closing item safe.**
  `002-C` tracks an upstream backlogit defect and will not close during this
  portfolio. A `blocks` edge from `173.007-T`/`173.010-T` onto it would have made
  both tasks permanently unstartable and `181-S` permanently unclosable — the
  exact partial-closure deadlock finding B10 exists to remove — and for
  `173.010-T` it would have demanded the very terminal state that regression
  forbids. This trap was caught after the edges were first added as `blocks`, and
  corrected.
* **Re-homing beats exclusion.** A shipment whose covering feature retains live
  blocked children while excluding them from the manifest cannot close without a
  SAFE_CLOSE disposition that no agent can execute. `backlogit adopt` moves the
  child out of the covering feature, renumbers it into the new parent's namespace,
  and auto-preserves `custom_fields.origin_feature` — no deletion, no hand-editing.
  New deferred features `174-F` (2 tasks) and `175-F` (4 tasks) are the homes.
* **A false equivalence claim is worse than an approximate one.** The branch
  validator was documented as having an accept/reject set identical to
  `git check-ref-format --branch`. Git **accepts and resolves** `@{-N}`; rule V10
  rejects it. Restated as a strict superset of rejections with divergence set **D**
  enumerated as a frozen literal. Normalization was considered and rejected: a
  value whose meaning depends on the invoking checkout's reflog is not a stable
  identifier for a workspace-**authoritative** contract, and `selected_branch`
  builds filesystem paths.
* **Leading-hyphen rejection cannot be derived from git at all.** Git's CLI cannot
  unambiguously receive such an argument, so V2/V3 are asserted as a standalone
  workspace invariant and excluded from the git-driven corpus arm.
* **A volatile count is the wrong assertion.** The checkpoint corpus read 51, then
  52, then 53 across three sessions. Three readings, three values — which is itself
  the argument for invariant-based assertion over a cardinality literal.
* **Red-phase tasks must not depend on the implementation.** Revision 3 encoded
  several "red" tasks as blocking *on* the implementation, which is test-after
  wearing a red-phase label. Every TDD triple is now machine-encoded as `blocks`
  edges with the asymmetry preserved.

### Known residual risk

The installed backlogit writer omits the `# {title}` H1 and `## Description`
headings its own templates declare; 189 of 191 queue records lack an H1. Hand-writing
tool-owned bodies is outside the supported operation set, so this is captured as
stash `2D70D556` rather than worked around.

Two separate incidents this session confirmed a related hazard: `backlogit update
--description` **destroys** sibling sections unless they are re-supplied in the same
call. `179-S` and `173-F` each lost sections that way and were restored. Always pass
`--section` for every existing section alongside `--description`.

### Next action

Reviewer re-review at attempt 05. If it passes, Ship claims `176-S` first (single
DAG root), then the five fan-out successors one at a time under P-016. Every
shipment manifest now exactly equals its covering feature's live descendant set.
Nothing was claimed, committed, or pushed.
