# Stage session — closure-evidence producer/consumer naming contract (FD0CCB42)

- **Date**: 2026-09-17
- **Agent**: Stage
- **Operation**: `stage next`, scoped to a single stash entry
- **Branch**: `main` (single worktree; P-016 preserved — no spike/research worktree was created)
- **Outcome**: reviewed plan harvested into `167-F` + 9 tasks, assembled as queued shipment `175-S`

## Scope

Operator restricted this session to stash `FD0CCB42` — "Align closure-artifact producer
naming with topology-gate lookup" — identified as the highest-value direct unblocker for
queued shipment `163-S`.

Explicitly **not** consumed, archived, edited, triaged, deliberated, or harvested:
stash `3EF5AAF2` (shipment-claim vs wave-admission contract conflict). Verified still
active at end of session.

Explicitly **not** absorbed (adjacent closure-hygiene entries left in stash):
`24E3E464`, `C395CFE3`, `0C094AED`, `63C5C305`, `5A537510`, `9E404C49`, `4702E1F6`,
`71200CBB`.

## Capability posture

| Gate | Result |
|---|---|
| Step 0.0 Tool availability | backlogit `ALL_TOOLS_OK`; `DEGRADED_MODE: agent-engram, agent-intercom, graphtor-docs` |
| Step 0.1 Index sync | `INDEX_SYNC_OK` (1256 indexed at start) |
| Step 0.1b Engram | `ENGRAM_DEGRADED` — fell back to grep/glob/view |
| Step 0.1c Intercom | `INTERCOM_DEGRADED` — phase broadcasts skipped, non-destructive work continued |
| Step 0.1d Graphtor-docs | `GRAPHTOR_UNAVAILABLE` — file-based doc search |
| Step 0 Crash resumption | ZERO-CANDIDATE NORMAL STARTUP — 47 checkpoints enumerated unfiltered, 0 anomalies, 0 quarantined, 0 active `stage`-owned |

## Triage obligations (P-021 C5/C6)

`FD0CCB42` carries the literal `DEFERRED SCOPE EXPANSION` marker, which **forced** the
`deliberate` route regardless of shape or size, and barred Step 3 planning until the
deliberation artifact existed.

- **(A) Duplicate detection — UNCONDITIONAL**: scanned all 110 active stash entries on
  six keys. Also specifically checked `7F93FA0C` (the tracking identity the compound
  learning assigns to this defect class) — not present in this workspace's active stash;
  it belongs to the sibling harness. **DISCOVERY-STATUS: CLEAN — no duplicate.**
- **(B) Late-identifier reconciliation — triggered** by `pr_number: N/A` and
  `review_thread_id: N/A`. Searched all Ship-owned residual-risk records citing
  `FD0CCB42`. The expansion originated in a pre-PR Stage staging session from an
  operator-delivered plan-review finding, so no PR and no hosted thread ever existed.
  **Reconciliation = NO-OP; the `N/A` values STAND as truthful terminal records.**
  This is not a C3 or C6 shortfall.

Step 1.5 grouping was **skipped** (single entry; deferred-expansion entries are excluded
from grouping pre-deliberation). Step 1.8 learnings retrieval returned a **HIGH**
confidence direct hit.

## The defect (verified, reproducible, read-only)

Producer and consumer specify the closure filename incompatibly, so valid closure
evidence is never opened.

- **Consumer**: `src/autoharness/gates/topology.py:718` globs
  `docs/closure/{shipment_id}-*-post-merge-closure.md`, returns `None` on no match.
- **Producer**: `.github/skills/operational-closure/SKILL.md:23` and
  `templates/skills/operational-closure/SKILL.md.tmpl:23` specify
  `{DOCS_CLOSURE}/{YYYY-MM-DD}-{slug}-closure.md`.

No string satisfies both. Discovery is filename-first, so a conforming artifact is never
read; the silent `None` collapses into `PREDECESSOR_CLOSURE_INCOMPLETE`.

Live probes on the committed tree:

```
closure_complete('162-S') -> None   # artifact EXISTS and is valid
closure_complete('174-S') -> None   # same shape
closure_complete('173-S') -> True   # only because an ID-anchored artifact was hand-authored
closure_complete('161-S') -> True
closure_complete('160-S') -> True

autoharness gate pipeline-topology --mode manual --shipment 163-S --phase pre_claim --json
  -> exit_code 1, token PREDECESSOR_CLOSURE_INCOMPLETE,
     details.predecessor_source "explicit", details.closure_complete null
```

Predecessor derivation for `163-S` is **correct and explicit**; the sole failing condition
is closure-artifact discovery. This is the direct and only unblocker.

## Decision

Adopted **Option C** (contract module) over A (widen the glob) and B (revert the
producer). Binding decisions `D1`–`D9` in the deliberation. Key points:

- `D1` single authoritative definition in a **new** module
  `src/autoharness/gates/closure_contract.py` — deliberately not inside `topology.py`,
  which is a *consumer*; co-locating the definition with one consumer is the generative
  cause of this defect class.
- `D2` canonical **write** pattern `{shipment_id}-{feature_id}-post-merge-closure.md`
  (29/30 shipment-scoped records already conform; the repo converged here de facto when
  repairing `173-S`). Date moves to frontmatter.
- `D3` recognized **read** set is **permanent, closed, exactly two** anchored regexes.
  Read tolerance of immutable history; never write permission.
- `D4` new **blocking** token `PREDECESSOR_CLOSURE_UNRECOGNIZED`.
- `D7` composed test must build the filename through the contract module's path builder —
  a hand-written fixture is a **defect**, since such a test would have passed through all
  six historical occurrences.
- `D8` **zero** files under `docs/closure/` created, renamed, edited, or deleted.

## Sequencing decision (D9) — why `dag-root` is truthful, not convenience

The gate enumerates exactly two remediations (`_SEQUENCING_REMEDIATION_OPTIONS`,
`topology.py:1543-1546`): record a real `blocks` edge, or declare the shipment a root.

There is **no real blocking edge**: this work depends on no queued shipment. Manufacturing
an edge on `174-S` would be **self-defeating** — `closure_complete('174-S')` returns `None`
*because of the very defect under repair*, producing a bootstrap deadlock. Leaving the
shipment unlabelled yields `unsequenced` (19 live shipment records, so `genesis` cannot
apply), which is excluded from `ready_set` and blocked with `UNSEQUENCED_SHIPMENT`.

Therefore `dag-root` is the accurate declaration. Precedent: `173-S`, `174-S`.

## Artifacts created

| Path | Purpose |
|---|---|
| `docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md` | Mandatory P-021 C6 deliberation; D1–D9, OQ-1…OQ-5, R1–R9, both triage obligations recorded |
| `docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md` | Reviewed plan, revision 2: RQ-1…RQ-14, units U1–U9, `## Plan Hardening` H1–H7, `## Plan Review` cycle 1 PASS |
| `docs/reviews/2026-09-17-closure-evidence-naming-contract-plan-review.md` | Standalone review record: PASS, 0 P0 / 0 P1 open, 2 cycles remaining |

Plan hardening was **required** (`Requires plan hardening: yes`, 3/5 signals present) and
ran before review, per P-006.

## Backlog produced

- Feature **`167-F`** — Closure-evidence producer/consumer naming contract reconciliation
- Tasks **`167.001-T` … `167.009-T`** (one per plan unit U1–U9), all `queued`, all carrying
  both `size` and `complexity`

| Task | Unit | Domain | Size | Complexity |
|---|---|---|---|---|
| 167.001-T | U1 contract module | Python src | M | medium |
| 167.002-T | U2 reader rewire | Python src | M | high |
| 167.003-T | U3 gate diagnostics | Python src | S | medium |
| 167.004-T | U4 validation CLI | Python CLI | M | medium |
| 167.005-T | U5 producer spec (atomic pair) | skill docs | S | low |
| 167.006-T | U6 Ship agent alignment (atomic pair) | agent docs | S | low |
| 167.007-T | U7 composed test | tests | M | high |
| 167.008-T | U8 adversarial regression | tests | S | medium |
| 167.009-T | U9 non-drift guard | tests | S | medium |

Width isolation holds: no task mixes Python source with template work, and none touches
`schemas/`.

## Shipment

**`175-S`** — "SHIP-17 - Closure-evidence producer/consumer naming contract reconciliation
(FD0CCB42, unblocks 163-S)", status `queued`, labels
`dag-root, topology-gate, closure, contract-drift, p-021`.

Manifest is exactly the 10 harvested IDs — `167-F` first, then the 9 tasks in dependency
order. No pre-existing queue item was pulled in.

Human SHIP-number is **17** because `173-S` already holds "SHIP-15" and `174-S` holds
"SHIP-16"; the initially created title said SHIP-15 and was corrected.

## DAG edges added

Intra-feature (transitive reduction of the plan's graph; the full declared set is recorded
in each task description):

```
167.002-T <- 167.001-T
167.003-T <- 167.002-T
167.004-T <- 167.001-T
167.005-T <- 167.001-T
167.006-T <- 167.005-T
167.007-T <- 167.003-T, 167.004-T
167.008-T <- 167.002-T
167.009-T <- 167.006-T
```

Cross-shipment: **`163-S` now depends on `175-S`** (in addition to its pre-existing
`162-S`). `163-S` remains `queued` — no `blocked` shipment status was invented.

## Validation evidence

```
gate dag-readiness --json
  cycle_detected: false, cycle_nodes: []
  ready_set: ["175-S"]
  next_eligible: "175-S" (ready_set_head)
  downstream_dependents["175-S"]: [163-S, 164-S, 165-S, 166-S, 167-S, 168-S]

gate pipeline-topology --mode manual --shipment 175-S --phase pre_claim --json
  exit_code: 0, blocked: false, "topology gate pass"
  shipment_readiness.predecessor_source: "declared_root"
  predecessor_ids: []

gate pipeline-topology --mode manual --shipment 163-S --phase pre_claim --json
  exit_code: 1, PREDECESSOR_CLOSURE_INCOMPLETE  (expected — the defect is not yet fixed;
  Stage does not implement. The 175-S edge is additive and did not mask this.)
```

Stash: active count 110 → 109. `FD0CCB42` archived non-destructively (present in
`.backlogit/archive/stash.jsonl`); `3EF5AAF2` verified still active, unmodified.

## Notes / follow-ups

- **Registry drift**: `.autoharness/backlog-registry.yaml` does not declare
  `features.sizing`, and its `create_task`/`update_task` params omit size/complexity — yet
  the live `backlogit_update_item` tool *does* accept `size`, `size_source`,
  `size_ruleset_version`, and `complexity`, and shipments render `size_composition`. The
  structured path was used (it works) and prose was mirrored in descriptions. The registry
  should be reconciled with the live tool surface.
- **`backlogit_stash_archive` MCP tool is not exposed** in this workspace; only the
  deprecated `backlogit_stash_remove`. Used the canonical CLI `backlogit stash archive`
  as the P-012 fallback.
- **`create_shipment --items` takes a comma-separated string**, not a JSON array. A JSON
  array is silently split on commas and fails with a confusing `not_found` naming
  `["167-F"` as the missing ID.
- Deferred to future sessions (out of scope, recorded as OQ-1…OQ-3): a full canonical
  closure *writer*; promoting closure frontmatter into `schemas/`; the
  dag-readiness/pre_claim closure-awareness divergence.

## Next step

Orchestrator performs the staging-artifact publication gate. Stage did **not** commit,
push, merge, claim `175-S`, build, run tests, create a PR, or invoke Ship. No source,
template, or schema file was modified.
