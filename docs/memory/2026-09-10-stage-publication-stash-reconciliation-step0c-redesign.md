---
title: "Stage session — publish SHIP-11/SHIP-12 staging records, reconcile eight stash entries, redesign the Step 0(c) evidence anchor"
date: 2026-09-10
agent: stage
session_id: "8964a988-6f32-4605-a2dc-b6a0bb66f9f9"
route: "claude-opus-5 / anthropic / high"
branch: main
tags: [memory, stage, publication, stash-reconciliation, shipment-reconcile, p-021, fail-closed-design]
---

# Stage session 2026-09-10 — staging publication, stash reconciliation, Step 0(c) redesign

## Gate state at session start

* `backlogit` MCP **available** — `TOOL_OK`, `INDEX_SYNC_OK`.
* `agent-intercom` configured but **no callable surface** — `INTERCOM_DEGRADED`,
  operator visibility reduced. The operator's message was treated as explicit
  authorization for the specifically named archival operations, and destructive
  scope was not broadened beyond them.
* `agent-engram` / `graphtor-docs` not exposed — `ENGRAM_DEGRADED`,
  `GRAPHTOR_UNAVAILABLE`; file-based exploration used throughout.
* Crash-resumption scan: 35 checkpoints enumerated with **no** status/agent filter,
  anomaly-scanned **before** partitioning. 33 `stage` + 2 `ship`, **all resolved**,
  zero quarantined, zero malformed. **Zero-candidate normal startup** — not a
  failure, not an operator handoff.
* One worktree, `main`, `HEAD fef4e4a3`. No worktree created; no branch created.

## What was done

### A — published the SHIP-11 / SHIP-12 staging records

Two focused commits on `main`. Both artifact sets were already `status: reviewed`
with `plan_review_verdict: PASS`; **publication only, no implementation scope was
touched to publish them.**

* `5171ace1` — 161-F + 161.001-T..161.007-T, the 15A02E21 decision/plan/two memory
  records/compound learning, and three referenced bug records (published for
  cross-reference integrity, not as manifest members).
* `922f99bf` — 162-F + 162.001-T..162.013-T + 170-S, the review-pattern-learning
  decision/plan/memory, and the harvest's `resolved` session checkpoint.

`169-S`'s own shipment record was already on `origin/main` (`a601696e`, PR 437), so
only its manifest members were missing.

### B — reconciled and archived exactly eight stash entries

Every archival was **evidence-first**: the postcondition was re-verified against
current state before the entry was touched, and the verification is recorded inside
the archived entry's own text. `archive`, never delete — a duplicate entry is itself
evidence that the same expansion was captured twice.

| Entry | Evidence that closed it |
|---|---|
| `6B627A50` | all 8 member records present at `HEAD` after `5171ace1` |
| `1CD92B69` | both halves: 169-S on `origin/main`, and 15A02E21 reconciled+archived here |
| `15A02E21` | deliberated, plan PASS, harvested into 161-F/169-S, now published |
| `2B68F9D6` | all **21** enumerated paths verified on `origin/main` via `git ls-tree` |
| `8F2BC28D` | `checkpoint-20260904-220151.json` is `resolved`; 35/35 checkpoints resolved |
| `EE1AB6DB` | the defective wording is gone **and** the publication condition is discharged |
| `4C2D4E69` | duplicate of consumed intake `8F2FD1F6`; explicit **ADOPT** decision for 164-F/172-S |
| `7AD60E4F` | strict subset of `904C47BC`; supersession recorded both directions |

### C — Step 0(c) evidence-anchor redesign (`DDBF283E`, `EB23D1B9`)

`DDBF283E`'s finding was **upheld**. The planned gate proved pre-existence with
`collection_completed_at`, the `HEAD` SHA and the manifest list — *all three written
by the agent whose compliance is checked*. A backdated byte-identical reconstruction
satisfied every clause. `15A02E21` was a gate no legitimate state could satisfy;
this was its dual — **a gate no illegitimate state could fail.**

**Decision:** an engine-written append-only ordering proof. Step 0(c) appends a
`PRECASCADE_EVIDENCE_ANCHOR` event carrying the record's `sha256` to
`.backlogit/logs/{shipment_id}.jsonl`; the *engine* writes the timestamp, actor and
append position, and the cascade mutation later appends its own events to the same
file. Ordering is proved by **relative append position in an engine-owned file**.
`collection_completed_at` is demoted to corroborating metadata, with the demotion
asserted by a guard so it cannot be silently re-promoted.

Artifacts: `docs/decisions/2026-09-10-step-0c-evidence-anchor-mechanism-redesign-deliberation.md`,
deliberation item `033-DL`, plan revision **R1**, and amended tasks
`163.001-T`/`163.002-T`/`163.003-T`/`163.004-T`/`163.005-T`.

## Decisions worth remembering

**The mechanism was verified against live data, not assumed.** Engine authorship
(`150-S`/`151-S`/`152-S` logs), engine-timestamped comment events, **log retention
after archival** (a proof that vanished with the archival would be useless), and —
decisively — `.backlogit/logs/159-S.jsonl` contains **no** anchor before `archived`.
The real failure case is mechanically detectable under the new mechanism and was not
under the old one.

**The claim is deliberately bounded.** Tamper-*evident* and out-of-protocol, not
tamper-*proof*. No local mechanism resists an operator with shell access. The threat
is the 159-S failure mode — a good-faith agent reconstructing equivalent-looking
evidence — and the fix makes that path unreachable through the agent's normal tool
surface.

**Contained in 171-S rather than split into a predecessor shipment.** A predecessor
would edit the *identical* Step 0(c) paragraphs, adding a third contender to a region
already contended by 169-S and reproducing the two-independent-restatements drift
that *produced* `15A02E21`. Splitting would have imported the defect class this
feature exists to remove.

**A shipment-level `blocks` edge onto a non-shipment is impossible — and would have
been a bug if it were not.** `backlogit` rejected `171-S -> 033-DL` ("both endpoints
must be shipments"). Shipment eligibility requires every predecessor to reach
`shipped`, which only a shipment can reach, so such an edge would be permanently
unsatisfiable — and `dep_type` collapses to `blocks` on sync, so even a `relates_to`
edge would have degraded into that unsatisfiable gate. Encoded at feature/task level
instead, where it *is* satisfiable.

**`163.004-T` rose to `complexity: high` and was NOT split.** It is INDIVISIBLE, and
R1 *strengthens* that argument — the anchor is the record's proof. The two-axis gate
was discharged by de-risking instead: this deliberation, RED-first ordering, and a
fresh review cycle.

## New finding raised this session

The checkpoint context-nesting defect tracked by `904C47BC` is **not historical**.
All 35 checkpoints were parsed: **26** carry a top-level `progress` key, not the 22
recorded at capture. Four were written *after* that capture, by **both** agent roles,
across four sessions — so the **writer path is still emitting non-conforming
payloads** and a one-time bulk repair would not stop recurrence. `904C47BC` was
annotated and **left ACTIVE**; its "requires deliberation: yes" and its need for a
fresh operator disposition are unmet and carried forward. Disclosed: one affected
file (`checkpoint-20260908-071321.json`) was published as-is in `922f99bf` because it
is that harvest's durable session record.

## State at session end

* `171-S`: `status: queued`, `blocks 169-S` **unsatisfied** (169-S is queued, not
  shipped) ⇒ **not claimable**. Its acceptance criteria are now correct.
* `033-DL`: `done`, held `active` for the whole revision and closed only after
  plan-review cycle 2 returned PASS.
* Eight publication/reconciliation entries archived; `DDBF283E` and `EB23D1B9`
  archived after the reviewed backlog reflected the decision.
* Left **active** on purpose: `904C47BC` (needs operator disposition), `9B582824`
  (untouched, outside authorized scope).

## Next steps

1. Orchestrator owns the remote publication gate. Nothing was pushed; no PR opened.
2. Operator disposition needed on `904C47BC` — and it should now consider the
   **writer fix** as the primary remedy, not a bulk file repair.
3. `169-S` must ship before `171-S` becomes claimable.
