---
title: "187-S retirement mechanics (C3): archived from queued, never claimed; abandoned is reachable only through a claim and was not used"
source: "docs/decisions/2026-09-25-187-s-retirement-mechanics-c3-record.md"
doc_type: decision
description: "Stage record of the C3 retirement of shipment 187-S, executed in Phase 2 under the operator's C3 ruling 'Retire 187-S' (2634bac2) and the Phase 2 'Go' (2ca9d9a5). Mechanics were checked against the installed backlogit 1.10.1-0.20260823032255-b07729386a31+dirty: .backlogit/hooks.yaml permits queued -> active or blocked only, and abandoned only from active; 'backlogit shipment' has no abandon command. So 'abandoned' is reachable only through 'active', which is a claim. Stage did not use that path. Instead Stage retired 187-S by archival from queued, the repository-supported non-claim operation already used for 176-S and 181-S, after removing the dag-root label and recording the retirement in the title, labels and description. 181-F and its 16 live tasks were archived from queued with the same disposition; each has a successor pointer into the C2 release units of docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md. Nothing was deleted, claimed, moved to active, or marked done, shipped or abandoned. The index was synced after the mutations."
date: 2026-09-25
created: 2026-09-25
status: recorded
decision_status: executed
deciders: operator (C3 ruling); Stage (mechanism, within P-010)
recorded_by: Stage
docline:
  type: decision
  date: 2026-09-25
  conclusion: "187-s-retired-by-archival-from-queued-no-claim-abandoned-path-requires-claim-not-used"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md"]
  tags:
    - "c3"
    - "shipment-retirement"
    - "ship-lifecycle"
    - "phase-2"
relates:
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-2.md, commit: 2634bac2, relation: "C3 'Retire 187-S'; mechanics deferred to Phase 2; retirement must not be a Ship claim"}
  - {path: docs/decisions/2026-09-25-lifecycle-proof-exit-operator-rulings-5.md, commit: 2ca9d9a5, relation: "Phase 2 'Go'"}
  - {path: docs/compound/2026-05-07-backlogit-shipment-status-constraints.md, relation: "shipment status and transition constraints"}
backlogit_version: "1.10.1-0.20260823032255-b07729386a31+dirty"
mechanism: archive-from-queued
claim_performed: false
status_active_entered: false
status_abandoned_set: false
items_deleted: 0
items_archived: 18
index_synced: true
---

# 187-S retirement mechanics (C3)

## Bottom Line

| Question | Answer |
|---|---|
| Can a queued shipment go straight to `abandoned`? | **No.** `.backlogit/hooks.yaml` allows `queued` to `active` or `blocked` only, and `abandoned` only from `active`. `backlogit shipment --help` lists no abandon command |
| Was the `active` path used? | **No.** Entering `active` is a claim. Stage may not claim (P-010), and a retirement must never be a Ship claim or execution (`2634bac2`, `PE-SCOPE-04`, IM-15) |
| How was `187-S` retired? | **By archival from `queued`**, the repository-supported non-claim operation already used for `176-S` and `181-S`. The `dag-root` label was removed first, and the title, labels and description record the retirement. The archived record keeps `archived_status: queued` |
| What happened to `181-F` and its items? | All 16 live tasks and `181-F` were archived from `queued` with the same disposition (table below). `181.001-T` was already archived as superseded. Nothing was deleted |
| Is anything orphaned? | No. Every archived task keeps `parent_id: 181-F`, and `181-F` is archived with them. `backlogit doctor` reports no finding for any `181`/`187` ID (its four findings are the pre-existing `048.001-T` to `048.003-T` and `155.006-T`) |
| Does anything depend on `187-S`? | No live item. A text scan of `.backlogit/queue/` found `187-S` only in `181-F`, `181.007-T` and `187-S` itself, all now archived. The archived `176-S` keeps its historical edge |

## Mechanics Check

| Check | Result |
|---|---|
| Version | `backlogit --version` and MCP `get_version`: `1.10.1-0.20260823032255-b07729386a31+dirty` |
| `backlogit shipment --help` | Commands: `add`, `claim`, `create`, `get`, `list`, `return-blocked`, `ship`. No abandon |
| `.backlogit/hooks.yaml` `lifecycle.transitions` | `queued: [active, blocked]`; `active: [done, blocked, review, shipped, abandoned]`; `blocked: [active]` |
| `.backlogit/header-def.yaml` shipment `status` | `queued`, `blocked`, `active`, `shipped`, `abandoned` |
| Eligibility rule (`backlogit.instructions.md`) | A shipment is eligible when `status == queued` and every `blocks` predecessor is `shipped`. A label alone does not make a queued shipment ineligible, so leaving `187-S` queued with a label would have left it technically claimable |
| Precedent | `176-S` (retired, never executed) and `181-S` (withheld) were archived from `queued` (`archived_status: queued`) |

**Why not `blocked`.** `queued` to `blocked` is permitted, but the backlogit
instructions say not to model gating with a shipment `blocked` status, and
`181-S`'s record notes that the pre-claim topology gate treats a live
`blocked` shipment as malformed legacy data.

**If `abandoned` is wanted on record.** That needs either an
operator-performed action or a backlogit transition change (`queued` to
`abandoned`). It must never be done by Stage or Ship claiming `187-S`.

## Mutations Performed

In order, all through backlogit MCP, all by Stage:

1. For each of the 16 live tasks and `181-F`: `update_item` (title prefixed
   `RETIRED (C3, never executed):`; labels `retired`, `superseded` and
   `never-executed` added; body kept), `append_comment` (the successor
   pointer below), then `archive_item`.
2. `187-S`: `update_item` (title prefixed `RETIRED (C3, never claimed, never
   executed):`; `dag-root` removed; `retired`, `superseded` and
   `never-executed` added; description prefixed with the retirement record
   and the original kept verbatim), `append_comment`, then `archive_item`.
3. `sync_index` (1474 indexed) and `doctor`.

The item comment logs are Git-ignored (`.gitignore:16`), so this table is the
tracked record of each successor pointer.

## Disposition of the 17 Manifest Items

"Successor" names the concern in the rebaselined plan's release units. The
successor backlog items are created only by harvest after a `LIFECYCLE-E2`
review `PASS`, and they carry a back-reference to these IDs.

| Item | Concern (revision 12) | Disposition | Successor |
|---|---|---|---|
| `181-F` | Feature | Archived, retired | One feature per unit A, B, C and D |
| `181.002-T` | Reader contracts and lexical validation | Archived, retired | Unit C, C1 |
| `181.008-T` | Budgets and bounded reads | Archived, retired | Unit C, C3 (snapshot, `RACE` and `IDENTITY_MISMATCH` semantics retired by Option D) |
| `181.009-T` | POSIX handle-relative adapter | Archived, retired | **None.** Retired by Option D. Containment moves to C2, C4 and C5 |
| `181.010-T` | Windows `NtCreateFile` bindings | Archived, retired | **None.** Retired by Option D. Windows containment moves to C2 |
| `181.011-T` | Windows parent-handle traversal | Archived, retired | **None.** Retired by Option D. Bounded reads move to C3 |
| `181.012-T` | Integration, error mapping, cleanup | Archived, retired | Unit C, C2 and C3 (error mapping); adapter cleanup retired |
| `181.006-T` | Resolver contracts and reason registry | Archived, retired | Unit B, B1 |
| `181.013-T` | Records, membership, declarations | Archived, retired | Unit B, B2 (`1..48`, not `1..512`) |
| `181.014-T` | Manifest snapshot and classification | Archived, retired | Unit B, B3 |
| `181.015-T` | Ledger, recheck, digest | Archived, retired | Unit B, B4 |
| `181.016-T` | Resolver and reducer | Archived, retired | Unit B, B4 (early return, IM-16) |
| `181.017-T` | Schema mirrors and registration | Archived, retired | Unit B, B1 |
| `181.007-T` | CLI adapter | Archived, retired | Unit B, B5. The Ship-side consumer (IM-07) is D1 |
| `181.003-T` | Ship text fixtures and structural tests | Archived, retired | Unit D, D2 |
| `181.004-T` | Pre-activation evidence | Archived, retired | Folded into D3's preflight. Its "marker-bearing assertion failure" rule is superseded by Proof A run 5 (R2) |
| `181.005-T` | Three-file activation | Archived, retired | Unit D, D3 |

## What This Record Does Not Do

It does not claim, activate, execute or ship anything. It does not set any
record to `active`, `done`, `shipped` or `abandoned`. It does not delete any
record. It does not edit the P-004 plan, its review or its lock file.
