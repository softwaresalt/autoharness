---
title: "Stage session memory — 165-F / 173-S review-fix cycle 2"
description: "Cycle-2 (final normal) correction pass over the DAG-authoritative predecessor-derivation plan, decision, backlog records, and shipment manifest, resolving nine operator P1 findings and three P2 findings."
doc_type: memory
source: docs/memory/2026-09-12/stage-165f-173s-review-fix-cycle-2.md
date: 2026-09-12
agent: stage
feature_id: 165-F
shipment_id: 173-S
review_cycle: 3
---

# Stage Session Memory — 165-F / 173-S Review-Fix Cycle 2

**Scope.** Second and final normal correction cycle before the 3-cycle stop
condition. Twelve operator findings (nine P1, three P2) raised against the
cycle-1 output, all resolved in-cycle. No P1 deferred; no same-contract-surface
completion postponed.

**Role posture.** Stage-owned artefacts only: planning documents, backlog
records, shipment manifest, stash, memory. No product source, template, test, or
config file was written. One previously-untracked **documentation** file — the
intake bug report — was added **byte-for-byte unmodified** under explicit operator
authorization. No shipment claim, no branch, no PR.

## What changed and why

### P1 corrections

| # | Change | Reason it mattered |
|---|---|---|
| 1 | Committed `docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md` verbatim | Three committed artefacts (archived stash `AF2890B7`, cycle-1 memory, plan provenance) forward-referenced a file absent from the repository, so the intake chain did not resolve at HEAD. |
| 2 | Narrow genesis rule G1–G4 replacing "no shipped history" | The old rule was a *has-not-shipped-yet* test, not a bootstrap test: in a workspace of N queued shipments **every** edge-less candidate passed `genesis` at once — the exact unearned-pass failure the feature exists to remove, reintroduced in the state meant to be safe. |
| 3 | Exactly **two** audited forced `pre_claim` invocations (U1 pre-branch, U2 pre-claim) | Verified against `.github/agents/_ship.agent.md` L227–229 / L254–258: Ship runs `pre_claim` twice before claiming. A single-use grant was literally unsatisfiable, which is worse than a two-use grant — it pressures the executor to stretch one grant across two invocations, unaudited. |
| 4 | Added edge `165.006-T <- 165.003-T` | 165.006-T renders the `audit_sequencing` output that 165.003-T produces; without the edge the two were orderable in the wrong sequence. |
| 5 | Retracted `_tuple_of_str` reuse; mandated a labels-specific validator | **Near-P0.** `_tuple_of_str` validates members against `_ARTIFACT_ID_PATTERN = ^\d+(?:\.\d+)*-[A-Z]+$` and raises on failure. `dag-root` fails it, so literal compliance would have made **every labelled shipment record** — including `173-S` — a hard read failure. |
| 6 | Re-expressed historical directional cases as raw `audit_sequencing` candidate expectations | The cycle-1 wording would have pinned the *retired suppression behaviour* of `_prior_shipment_id` as a live tested contract, contradicting D3/F6 which require the audit to report the raw candidate unsuppressed. |
| 7 | Removed the F6 deferral escape hatch in 165.002-T | It permitted the task to close with claim-path numeric residue given a follow-up stash entry — i.e. shipping a shipment whose own stated contract was false at merge. |
| 8 | Merged 165.010-T into 165.008-T (one atomic task/commit) | A dependency edge orders work; it does not prevent drift. Between the two tasks, template sources would hold the new contract while the installed `.github/agents/` mirrors the dogfooded agents actually read held the retired one. |
| 9 | Verified `FD0CCB42` live; flipped `9AA34143` to `requires deliberation: yes` | Archived `165.007-T` must forward-reference a real durable item, and P-021 C6 requires the flag on deferred scope expansions. |

### P2 corrections

| # | Change | Reason |
|---|---|---|
| 10 | Closure-evidence variants narrowed to the `explicit` state; `declared_root` / `genesis` / `unsequenced` tested once each | Closure evidence is evaluated per explicit predecessor; the other three states have no predecessor for it to apply to, so those cells were vacuous. |
| 11 | Documented that code rollback alone does not undo migrated edges or root labels; added a migration ledger and data-first rollback ordering | Reverting the engine while migrated data persists yields a state that existed neither before nor after — the most confusing possible failure mode. |
| 12 | Reconciled `AF2890B7`'s archival summary via an append-only comment event on `165-F` | backlogit exposes **no** edit/append path for an archived stash entry (`backlogit_stash_get AF2890B7` → `not_found`), so the archived record is left intact and the reconciliation lives on the item it forward-references. |

## Final state

**Active task set (8 tasks + feature, = the `173-S` manifest, 9 items):**
`165-F`, `165.001-T`, `165.002-T`, `165.003-T`, `165.004-T`, `165.005-T`,
`165.006-T`, `165.008-T`, `165.009-T`.
**Archived:** `165.007-T` (descoped → stash `FD0CCB42`),
`165.010-T` (merged → `165.008-T`).

**Edges:** `165.001-T → 165.002-T`;
`165.002-T → {165.003-T, 165.004-T, 165.006-T}`; `165.003-T → 165.006-T`;
`165.004-T → 165.005-T`; `{165.005-T, 165.006-T} → {165.008-T, 165.009-T}`.
Verified acyclic, no dangling edges, manifest stored in topological order.

**Sizing:** 001 M/medium · 002 M/high · 003 M/medium · 004 S/medium ·
005 M/high · 006 S/low · 008 M/medium · 009 S/low. All carry
`size_source: agent` and `size_ruleset_version: ah-stage-sizing-v1`.

**Review:** cycle 3, plan revision 3 → **PASS**, 0 P0 / 0 P1 / 2 P2 / 4 P3.
Cycles used **3 of 3**.

## Decisions worth carrying forward

* **Genesis must be a cardinality-1 property.** Any "bootstrap" predicate that two
  candidates can satisfy simultaneously is not a bootstrap predicate. Sole-extancy
  is what makes it un-spoofable by a later-numbered candidate; shipped-history
  absence is not.
* **An unsatisfiable authorization is more dangerous than a wider one.** Grants
  must be written against the executor's *actual* protocol, with the invocation
  count named and the out-of-scope invocation (here, the `CLAIM_NOT_OBSERVED`
  retry) explicitly excluded.
* **Fail-closed discipline transfers; syntax does not.** Reusing a validator for
  its posture while inheriting its unrelated format rule is a reliable way to
  brick a reader.
* **A dependency edge is not an atomicity guarantee.** When two artefacts are
  copies of each other, order them into the same commit, not into the same DAG.
* **backlogit archived-stash entries are immutable.** Plan reconciliation onto a
  live item's append-only event log from the start.

## Known non-blocking residue

* **P2-A** — shipment `size_composition.members` derives from `parent_id`
  children rather than the manifest, so it still lists archived `165.007-T` and
  `165.010-T`. Tool artefact; **second recorded occurrence**; externalized to
  stash `9AA34143`. The `173-S` record carries a note so a future reader does not
  "reconcile" it by re-adding an archived task.
* **P2-B** — `dag-root` has no mechanical enforcement; it is a durable, diffable,
  attributable declaration governed by agent contract. Mechanical enforcement
  needs a backlogit permission model, outside this shipment.
* **MCP gotcha** — a `backlogit_update_item` call on `165-F` returned
  `MCP error -32001: Request timed out` while the write **succeeded**. Verify
  against the queue file before retrying, or risk a double-apply.

## Next steps

1. Operator reviews and opens the staging PR for the Stage artefacts.
2. Ship executes `173-S` in dependency order from `165.001-T` (RED tests),
   using **exactly two** audited forced `pre_claim` invocations per D6.
3. `165.002-T` self-liquidates the bootstrap grant by giving `173-S` a
   `dag-root` label; no further force authority exists after the claim.
4. After `173-S`: deliberate `86498B64` (branch naming) — sequence rather than
   parallelize, since both touch `src/autoharness/gates/topology.py`.
5. Deliberate `9AA34143` (rollup member set) and `FD0CCB42` (closure-evidence
   defect), both flagged `requires deliberation: yes`.
