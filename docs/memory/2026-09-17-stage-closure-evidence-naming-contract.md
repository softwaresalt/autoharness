---
title: "Stage session — closure-evidence producer/consumer naming contract (FD0CCB42)"
description: "Current-state Stage handoff for stash FD0CCB42: the closure-evidence producer/consumer naming contract, deliberated, planned, hardened, reviewed and harvested into covering feature 167-F plus twelve bounded tasks, assembled as queued dag-root shipment 175-S — the direct and only unblocker for 163-S. Records the staged artifact set, the backlog hierarchy with sizes and dependencies, the eligibility and dependency evidence as observed, the checkpoint payload shape, and the open handoff to Ship."
doc_type: memory
source: docs/memory/2026-09-17-stage-closure-evidence-naming-contract.md
date: 2026-09-17
updated: 2026-09-17
agent: stage
feature_id: 167-F
shipment_id: 175-S
source_stash_id: FD0CCB42
deferred_scope_expansions:
  - AE612665
source_decision: docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md
decision_revision: 4
plan_source: docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md
plan_revision: 5
linked_review: docs/reviews/2026-09-17-closure-evidence-naming-contract-plan-review.md
review_cycle: 4
decision: PASS
dispatch_mode: single-agent-declared-degradation
revision: 4
revision_note: >-
  This memory is maintained as a rewritten current-state handoff, not as an
  accreting session log. It describes the staged package exactly as it stands
  now; superseded narrative has been removed rather than appended to. Review
  history is preserved in the review artifact's clearly segregated audit trail,
  which is the single place it lives.
---

# Stage session — closure-evidence producer/consumer naming contract

## Purpose of this document

This is the **current-state handoff** from Stage to Ship for stash `FD0CCB42`.
It states what exists now, what it means, and what the next owner must do. It
deliberately does **not** narrate how the package evolved: that belongs to the
review artifact's audit trail.

## Outcome

| Field | Value |
|---|---|
| Source stash | `FD0CCB42` (archived as consumed) |
| Covering feature | `167-F` |
| Tasks | 12 (`167.001-T` … `167.012-T`) |
| Shipment | `175-S`, status `queued`, `dag-root: true`, 13 manifest items |
| Plan | `docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md` (revision 5) |
| Decision | `docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md` (revision 4) |
| Review | `docs/reviews/2026-09-17-closure-evidence-naming-contract-plan-review.md` (cycle 4, **PASS**, 0 P0, 0 P1 open) |
| Deferred expansion captured | `AE612665` (canonical closure-artifact *writer*, OQ-1) |
| Next owner | **Ship** |

## Scope and boundary compliance

Stage authored planning and backlog artifacts only. Within this session Stage
did **not**:

* write, modify, or delete any source, test, template, schema, or config file;
* run build systems, test suites, or linters;
* commit, push, create a branch, or open a pull request;
* claim, close, or advance any shipment;
* create or use an implementation worktree (no P-016 spike worktree was needed);
* consume or edit stash `3EF5AAF2`, or triage/harvest stash `AE612665`;
* touch unrelated untracked bug reports present in the working tree.

Branch `chore/stage-175-S` carries the staged artifacts as **uncommitted
working-tree changes**. `git rev-parse HEAD` is unchanged for the whole session.

All source inspection (`src/autoharness/gates/topology.py`, the producer
template and its installed mirror, the `tests/` naming conventions) was
**read-only**, for planning fidelity.

## Capability posture

| Capability | Status |
|---|---|
| backlogit MCP | `TOOL_OK` — all backlog, shipment, dependency, stash and checkpoint mutations went through official operations |
| Index sync | `INDEX_SYNC_OK` at session start and at session end |
| agent-engram | not installed — file-based exploration used throughout |
| agent-intercom | not installed — `dispatch_mode: single-agent-declared-degradation`; operator interaction was direct |
| graphtor-docs | not installed — `docs/` searched with grep/view |

`backlogit_stash_archive` is not exposed as an MCP tool in this workspace; the
CLI `backlogit stash archive` is the canonical non-destructive fallback and is
what was used. `backlogit_stash_remove` (deprecated) was not used.

## The defect being staged

The closure-evidence **producer** and **consumer** name the same artifact
differently, and nothing in the repository holds them together.

* Producer skill template `templates/skills/operational-closure/SKILL.md.tmpl:23`
  documents `{{DOCS_CLOSURE}}/{YYYY-MM-DD}-{slug}-closure.md`; its installed
  dogfood mirror `.github/skills/operational-closure/SKILL.md:23` renders the
  same shape with the literal `docs/closure`.
* The Ship agent template `templates/agents/_ship.agent.md.tmpl:863` names the
  output **directory** only — no filename contract — and lists `compaction
  status` without `closure_status`.
* The consumer `FilesystemTopologyReaders.closure_complete`
  (`src/autoharness/gates/topology.py:718`) globs
  `docs/closure/{shipment_id}-*-post-merge-closure.md`.

The two shapes cannot intersect, so conforming producer output is invisible to
the gate, which then emits `PREDECESSOR_CLOSURE_INCOMPLETE`. This has recurred
six times and has been repaired per-artifact every time. The staged work
replaces per-artifact repair with **one shared contract module** that both sides
consume, a **write-time validator gate**, and a **composed producer→consumer
test** that fails if either side drifts again.

Observed live consumer state (read-only probes of
`topology._shipment_readiness_check` and `closure_complete`):

| Shipment | `closure_complete` | Note |
|---|---|---|
| `162-S` | `None` | legacy date-prefixed name, unrecognized |
| `174-S` | `None` | legacy date-prefixed name, unrecognized |
| `173-S` | `True` | canonical name, recognized |

## Decision summary (binding — D1…D9)

* **D1** One shared contract module owns the grammar; producer docs and consumer
  reader both consume it. No second definition anywhere.
* **D2** The canonical **write** name is
  `{shipment_id}-{feature_id}-post-merge-closure.md`, uppercase kind letters,
  case-sensitive.
* **D3** The **read** set is a permanent, closed enumeration of two anchored
  regexes: **R1** canonical (uppercase-only, exact case-sensitive comparison)
  and **R2** legacy date-prefixed (`[Ss]` kind letter, case-folded comparison).
  Lowercase tolerance is confined to R2. R1's accepted domain and the path
  builder's accepted domain are identical in **both** directions; for R2 only
  the one-directional, structurally provable property is asserted — no builder
  output can ever match R2.
* **D4** Attribution **parses** the shipment identifier from the position the
  anchored grammar reserves for it (after the date prefix for R2, leading for
  R1) and compares that single parsed group. A requested token is never searched
  for elsewhere in a filename, and never inside an R2 free-form suffix.
* **D5** `PREDECESSOR_CLOSURE_UNRECOGNIZED` is emitted only when no recognized
  candidate exists, so it is unambiguously blocking.
* **D6** A write-time `autoharness gate closure-evidence` reuses the consumer's
  **complete** acceptance predicate by import. Because that predicate is
  **boolean**, the frontmatter rejection diagnostic is a **generic
  authoritative-predicate rejection** (path + deciding predicate + one
  contract-owned requirements summary). Field/reason-specific diagnostics exist
  only for gate-owned checks: filename pattern, discoverability, and
  absent/unreadable input.
* **D7** The composed test must build the **canonical** filename through the
  contract module's path builder. Because the builder cannot emit R2 by
  construction, **legacy** fixture names come from exactly one dedicated,
  test-only legacy filename helper. All durable fixtures are **temporary**; no
  durable test reads `docs/closure/`.
* **D8** Path construction resolves `workspace_root` **first**, anchors a
  relative `closure_dir` as `workspace_root / closure_dir`, and never resolves
  it against the process CWD; absolute/out-of-root inputs and symlink/junction
  escapes are rejected.
* **D9** The real-corpus proof that `162-S` and `174-S` become recognized is
  **one-time publication/runtime evidence** captured into this work's own
  post-merge closure artifact — not a durable test assertion.

## Backlog hierarchy

Twelve tasks, 1:1 with the plan's twelve implementation units, each ≤ 4 named
scenarios and each within the 2-hour rule.

| Task | Plan unit | Size | Complexity | Concern |
|---|---|---|---|---|
| `167.001-T` | U1 | M | medium | Contract module — grammars, read set, attribution, constants |
| `167.010-T` | U10 | M | medium | Path builder — root-first resolution, anchoring, containment |
| `167.002-T` | U2 | M | medium | Consumer reader rewired onto the contract module |
| `167.003-T` | U3 | S | medium | Gate diagnostics — `UNRECOGNIZED` vs `INCOMPLETE`, attribution |
| `167.004-T` | U4 | M | medium | `gate closure-evidence` CLI surface and `--json` shape |
| `167.011-T` | U11 | S | medium | Write/read parity battery and diagnostic-ownership proof |
| `167.005-T` | U5 | S | low | Producer skill template updated to the canonical contract |
| `167.006-T` | U6 | S | low | Ship agent template — filename contract and `closure_status` |
| `167.007-T` | U7 | S | medium | Composed producer→consumer test + legacy filename helper |
| `167.008-T` | U8 | S | medium | Regression battery for the six historical failure shapes |
| `167.012-T` | U12 | XS | low | Fixture-provenance guard (temporary fixtures; helper exception) |
| `167.009-T` | U9 | S | medium | Documentation and cross-reference reconciliation |

`size_composition`: `M × 4`, `S × 7`, `XS × 1`.

**Shipment `175-S` manifest order** (topological, 13 items):

```text
167-F, 167.001-T, 167.010-T, 167.002-T, 167.003-T, 167.004-T,
167.011-T, 167.005-T, 167.006-T, 167.007-T, 167.008-T, 167.012-T, 167.009-T
```

**Live dependency edges** (task ← its predecessors):

```text
167.002-T ← 167.001-T
167.003-T ← 167.002-T
167.004-T ← 167.001-T, 167.010-T
167.005-T ← 167.001-T
167.006-T ← 167.005-T
167.007-T ← 167.001-T, 167.002-T, 167.003-T, 167.004-T, 167.010-T
167.008-T ← 167.002-T, 167.007-T
167.009-T ← 167.001-T, 167.005-T, 167.006-T
167.010-T ← 167.001-T
167.011-T ← 167.004-T
167.012-T ← 167.002-T, 167.008-T
```

Cross-shipment: `163-S` depends on `175-S`. `dag-readiness` reports
`cycle_detected: false`.

### Dependency-edit statement (precise)

The live dependency edges **match the plan-declared predecessor sets for every
task**. Two edits produced that state, and they are the only edits:

* the edge `167.008-T → 167.001-T` was **removed**. It was **not declared** by
  the plan's dependency sets — it was redundant relative to the declared set,
  which already reaches `167.001-T` through `167.002-T`;
* the edge `167.008-T → 167.007-T` was **added**, because the plan makes
  `167.008-T` consume the dedicated legacy filename helper that `167.007-T`
  creates.

This is **not** a transitive reduction of the graph and must not be described as
one. No general redundancy-elimination pass was run, and no other edge was
removed. The manifest's topological order is unchanged by these edits.

## Eligibility evidence (as observed — read-only)

`autoharness gate dag-readiness --json` reports:

* `ready_set: ["169-S", "175-S"]`
* `candidate_ids: ["169-S", "175-S"]`
* `next_eligible: "175-S"`, `next_eligible_reason: "ready_set_head"`
* `cycle_detected: false`

**Stage's claim is narrower than that gate output.** Stage asserts only that
`175-S` is **eligible and claimable under its declared `dag-root` and scope**:
a read-only probe of `topology._shipment_readiness_check("pre_claim", "175-S", …)`
returns `passed` with `predecessor_ids: []`.

Stage does **not** claim `175-S` is the global `ready_set` head. `169-S`
precedes `175-S` in the global `ready_set`, and global queue ordering may select
a different head. The `ready_set_head` token above is the gate's own emitted
reason string, reproduced verbatim as observed output — it is not Stage's
characterisation of `175-S`.

For completeness, and **without acting on it**: a read-only probe shows `169-S`
currently blocked with `PREDECESSOR_NOT_SHIPPED` (predecessor `168-S` is
`queued`). `169-S` was not altered in any way by this session.

**CLI caveat for the next owner:** `autoharness gate pipeline-topology`
short-circuits at `branch_ownership` with `BRANCH_MISMATCH` while the working
tree is on `chore/stage-175-S`, before `shipment_readiness` is ever evaluated.
All readiness evidence above therefore comes from direct read-only Python probes
of `topology`, not from that CLI path. Ship should re-derive readiness from its
own claim branch.

## Checkpoint contract

`backlogit_create_checkpoint` `schema_version: 1` exposes a **closed** top-level
namespace (`schema_version`, `agent`, `session_id`, `phase`, `status`,
`created_at`, `updated_at`, `context`, `progress`, `resume_hint`) and an **open**
`context` object whose arbitrary keys survive round-trip.

The binding rule for this workspace is that **progress data belongs inside
`context`**. The final checkpoint of this session was therefore created through
the official operation with top-level keys limited to `schema_version`, `agent`,
`session_id`, `phase`, `resume_hint` (plus engine-populated lifecycle fields),
and **all** domain, progress and supersession data nested under `context`,
including `context.progress`.

The persisted JSON was retrieved back through `backlogit_get_checkpoint` and
verified to contain **no top-level `progress` key** and a present
`context.progress`. It supersedes `checkpoint-20260917-213419.json` by reference
in `context.supersession`. Superseded checkpoint records were **never**
hand-edited or deleted; supersession is recorded in the new record only, and the
new checkpoint was resolved through `backlogit_resolve_checkpoint` before session
end so no active recovery candidate is left behind for completed work.

## Artifact inventory

| Artifact | State |
|---|---|
| `docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md` | revision 4 — binding D1…D9 and risks stated once, in current form; option analysis explicitly labelled non-binding historical |
| `docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md` | revision 5 — single canonical document; no correction log, revision delta, or reviewer chronology in the body |
| `docs/reviews/2026-09-17-closure-evidence-naming-contract-plan-review.md` | cycle 4, **PASS** — consolidated final reviewed contract above a divider, bounded historical audit trail below it, explicitly non-binding |
| `docs/memory/2026-09-17-stage-closure-evidence-naming-contract.md` | this file, revision 4 — current-state handoff |
| `.backlogit/queue/167-F.md` + 12 task files | current-state descriptions and acceptance criteria matching plan revision 5 exactly |
| `.backlogit/queue/175-S.md` | `queued`, `dag-root: true`, 13 items in topological order |
| `.backlogit/stash.jsonl` | `FD0CCB42` archived as consumed; `AE612665` appended as a deferred expansion (1 insertion, 0 deletions); `3EF5AAF2` untouched |

**Maintenance policy for these artifacts:** they are **rewritten**, not appended
to. Corrections are folded into the canonical body so each document states its
contract once. Only the review artifact retains history, and only below an
explicit `SUPERSEDED — NON-BINDING` divider.

## Deferred expansion

`AE612665` — a full canonical closure-artifact **writer** (path *and* body *and*
frontmatter generated from the shared definition), recorded as OQ-1 and captured
under P-021 C1 with `REQUIRES DELIBERATION: yes`. An unconditional duplicate scan
returned `DISCOVERY-STATUS: CLEAN`. All source refs were available at capture, so
no late-identifier reconciliation is outstanding. **It has not been triaged or
harvested** and must not be, by this session's scope fence.

## Files the plan expects Ship to create

These paths do not exist yet and are expected non-resolving cross-references in
the plan and review. They are the exhaustive list of new files the 12 tasks
introduce:

| Path | Created by |
|---|---|
| `src/autoharness/gates/closure_contract.py` | `167.001-T` (extended by `167.010-T`) |
| `tests/test_closure_contract.py` | `167.001-T` |
| `tests/test_closure_contract_path.py` | `167.010-T` |
| `tests/test_cli_gate_closure_evidence.py` | `167.004-T` (extended by `167.011-T`) |
| `tests/test_closure_contract_compose.py` | `167.007-T` |
| `tests/_closure_legacy_names.py` | `167.007-T` |
| `tests/test_closure_contract_nondrift.py` | `167.009-T` |

`tests/test_closure_contract_compose.py` follows this repository's existing
`_compose` convention for composed-behaviour tests
(`tests/test_telemetry_record_compose.py`,
`tests/test_telemetry_tool_event_compose.py`).
`tests/_closure_legacy_names.py` follows the existing `tests/_*.py` shared
test-helper convention (`tests/_assertion_render.py`, `tests/_env_patch.py`,
`tests/_git_env.py`). This repository has no `tests/conftest.py` and no
`tests/__init__.py`; the helper is imported directly.

## Handoff to Ship

1. Claim `175-S` on its own implementation branch. Re-derive readiness there —
   the `BRANCH_MISMATCH` caveat above makes readiness CLI output unusable from
   `chore/stage-175-S`.
2. Execute the 12 tasks in the manifest's topological order, honouring the live
   dependency edges.
3. Plan revision 5's `## Contract Specification` (C1–C6) is the normative source
   for identifier grammars, the recognized read set, attribution, path
   construction and containment, the diagnostic contract, and the durable-test
   fixture policy. Where a task body and the plan appear to differ, the plan
   governs and the divergence is a defect to report.
4. Capture the one-time real-corpus proof (D9) — that `closure_complete("162-S")`
   and `closure_complete("174-S")` return `True` against the committed corpus —
   into this work's post-merge closure artifact at execution time.
5. `163-S` unblocks on `175-S` shipping with complete closure evidence. Do not
   alter `169-S`.

## Open items for the next session

* Nothing is blocked on Stage. The package is review-PASS with 0 P0 and 0 P1
  open.
* The staged changes remain **uncommitted** on `chore/stage-175-S`; publication
  is Ship's, or the operator's, to perform.
