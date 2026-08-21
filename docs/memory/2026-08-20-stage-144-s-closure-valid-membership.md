---
title: "Stage session - 144-S manifest restored to closure-valid full-child membership"
date: 2026-08-20
agent: stage
route: "claude-opus-5 / anthropic / high (P-013.5)"
branch: chore/stage-144-s
stash_consumed: []
stash_created: []
features: [136-F]
tasks: []
superseded: [136.001-T]
shipments: [144-S]
execution_order: "146-S -> 144-S -> 145-S"
terminal_state: "144-S queued; manifest closure-valid (classifier: cascade); executable scope still two tasks"
---

# Stage session memory - 2026-08-20 (144-S closure-valid membership)

## Scope

Operator-directed continuation of the same closure-validity review-fix cycle that
corrected `145-S`. Same finding, same contract, same branch, applied to `144-S`.
No deferred entry was created — the whole finding is inside the P-021 C1 contract
this branch already authorizes.

## Degraded-mode declarations

* `TOOL_OK: backlogit` (MCP; registry `.autoharness/backlog-registry.yaml`,
  directory `.backlogit`)
* `INDEX_SYNC_OK` (908 items at session start and at close)
* `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE` — packs
  installed as instructions, no MCP surface available; file-based discovery used
  and phase broadcasts skipped
* Checkpoint scan (`consumer_id: stage`, unfiltered): 5 total, 3 resolved,
  2 abandoned, **0 active**, 0 quarantined -> ZERO-CANDIDATE NORMAL STARTUP.
  No recovery, no cross-role handling.

## Finding, confirmed read-only

`144-S`'s manifest was `[136-F, 136.002-T, 136.003-T]`, dropping the superseded
child `136.001-T` when it was archived. `136-F` has **three** children across
`queue/` + `archive/`, so the reduced manifest could not pass **either** supported
closure path:

* **Cascade refused.** `autoharness.gates.shipment_closure.classify_shipment_close_path`
  enumerates a root feature's children across **both** `.backlogit/queue/` and
  `.backlogit/archive/`. Against the three-item manifest it returned
  `safe_close: feature member '136-F' has children outside the manifest:
  ('136.001-T',)`.
* **Safe-close halted.** P-015 then puts the omitted child in the **protected
  set**, and its baseline integrity gate requires every protected member to be
  present in `queue/`. `136.001-T` is already archived — classified as a
  pre-existing cascade, halting closure before any manifest item is archived. The
  `pre-archived` exemption covers manifest items only; the protected set has none.

Deadlock: neither path could close the shipment. This is the identical
same-contract defect corrected on `145-S`, and it was recorded there as
"observed, not changed" pending this operator decision.

## Correction applied

`136.001-T` was added back to `144-S.custom_fields.items` using the **official**
`backlogit_add_to_shipment` operation (no hand-edit of the manifest). Manifest is
now `[136-F, 136.002-T, 136.003-T, 136.001-T]` — the covering feature first,
then the two executable tasks in dependency order, then the pre-archived member.

Re-running the classifier read-only:

* before: `safe_close` — children outside the manifest
* after: `cascade: every feature member is a verified fully-covered root`
  (qualifying feature `136-F`)

P-015 exception **item 7** is what makes this safe: a pre-archived manifest member
satisfies the coverage/root checks the same as a queued member, does not
disqualify cascade, and the cascade op is idempotent over it — it still returns
the member in `archived_ids`, so shipment-reconcile's exact-match post-condition
holds unchanged.

## Why claim and execution stay safe

Manifest membership is **not** a schedule.

* `136.001-T` remains in `.backlogit/archive/` with `status: archived`, its
  `[SUPERSEDED by 138.001-T]` title, its superseded-by pointer, and **no**
  dependency edges (forward or reverse).
* Ship Step 0.5 item 1a halts only when a `queued` shipment has a manifest task
  that is `active` or `done`; `archived` is neither, so no false
  `SHIPMENT_STATE_INCONSISTENT`.
* Ship Step 2's execution loop has no queued or active record to claim for it.
* `shipment-reconcile` `mode: pre` classifies it `pre-archived`, an explicitly
  **valid** class contributing to `PROCEED`; `mode: post` finds an archive file,
  so the post-check also passes.
* `138.001-T` Scope A (feature `138-F`, shipment `146-S`) retains sole ownership
  of the superseded scope; nothing was re-opened, re-queued, or un-archived.
* `136.002-T` is still the first task of `144-S` and `136.003-T` still depends on
  `136.002-T` alone.

## Verification

* `backlogit_sync_index` -> `INDEX_SYNC_OK` (908) at session start and at close.
* `backlogit_get_shipment 144-S` -> covering feature `136-F`, items list of 4,
  `dependencies: [146-S (blocks)]` unchanged, `status: queued` unchanged.
* `classify_shipment_close_path` read-only, all three shipments after the fix ->
  `144-S: cascade`, `145-S: cascade`, `146-S: cascade`.
* Child enumeration by `parent_id` scan of `queue/` + `archive/` -> exactly three
  children of `136-F` (`136.001-T`, `136.002-T`, `136.003-T`); every one is now a
  manifest member; no extras.
* `backlogit_get_dependencies 136.001-T` forward and `--reverse` -> empty. No edge
  references it, and it declares none. `136.003-T -> 136.002-T (blocks)` is the
  only edge inside `144-S`. Acyclic; no orphans, no dangling references.
* `Test-Path` -> `136.001-T` present only under `.backlogit/archive/`; `136-F`,
  `136.002-T`, `136.003-T` only under `.backlogit/queue/`. No queue/archive
  duplicate of any manifest member.
* `backlogit_doctor` (duplicates + orphans + partial mutations + workspace root
  conflict) -> 9 findings, **all pre-existing and unrelated** (orphaned
  `048.001-T` / `048.002-T` / `048.003-T`; partial commit associations on
  `019-DL`, `040-S`, `041.001-T`, `046-F`, `046.001-T`, `128.002-T`). **Zero
  duplicate IDs. Zero findings against any 136 / 137 / 138 / 144 / 145 / 146
  artifact.**
* `git status` -> the operator's pre-existing unrelated changes (`.gitmodules`,
  `.mcp.json`, `references/*`, `diff_files.txt`) are untouched.

## Coordination with the 145-S correction

Nothing from the already-applied `145-S` closure-membership edits was undone.
`145-S`'s manifest is unchanged at seven items and still classifies `cascade`;
its `144-S (blocks)` dependency, its archived `137.005-T` / `137.006-T` records,
and the `137-F` membership block are all untouched. The prior session's
"observed, not changed" note about `144-S` is superseded by an addendum rather
than rewritten. One coordination repair was made: the `145-S` edit to
`docs/plans/2026-08-20-ship-stash-archive-operation-migration-plan.md` had glued
the following list item onto the end of the corrected bullet
(`... four queued tasks.* Dependency edges removed:`); the missing newline was
restored. No wording was changed.

With both corrections applied, every shipment in the `146-S -> 144-S -> 145-S`
chain classifies `cascade`, and the `8fa8cf67` manifest-hand-removal precedent is
withdrawn workspace-wide with no surviving exception.

## Boundary statement

Stage made **no** source, test, template, schema, or config edit; ran **no**
build, test suite, or linter; made **no** branch switch, commit, push, PR, or
GitHub thread reply/resolve; claimed **no** shipment. The read-only invocations of
`classify_shipment_close_path` / `_enumerate_children` are pure classification
functions that never mutate the backlog. Only backlog artifacts and
planning/memory documents were modified. Publication, the PR reply, and thread
resolution remain the Orchestrator's step.

---

## ADDENDUM 2026-08-20 - execution order SUPERSEDED (B19E9662 / 147-S)

The `execution_order` recorded in this document's frontmatter
(`146-S -> 144-S -> 145-S`) is **superseded**. A newly confirmed prerequisite
blocker was staged after this session: the installed Ship contract
`.github/agents/_ship.agent.md` iterates the shipment manifest unconditionally
in its Step 2 task loop, with no `pre-archived` exclusion, so it would attempt
to reactivate the archived superseded children that the closure-membership
correction deliberately restored to `144-S` and `145-S`.

Current chain:

```text
146-S  ->  147-S  ->  144-S  ->  145-S
```

* New shipment `147-S` (queued, high), covering feature `139-F`, tasks
  `139.001-T` + `139.002-T`. Manifest `[139-F, 139.001-T, 139.002-T]`, all
  queued, **no pre-archived members**, so it executes safely under the current
  unfixed contract.
* **Critical path** (the edges that determine execution order):
  `144-S -> 147-S (blocks)` and `147-S -> 146-S (blocks)`.
* **CORRECTED 2026-08-21 - the direct edge `144-S -> 146-S (blocks)` is
  PRESENT, not removed.** An earlier revision of this addendum recorded it as
  removed; that is superseded. It was restored as a **redundant
  topology-compatibility edge** required by the `pipeline-topology --phase
  pre_claim` gate, whose `_prior_shipment_id` heuristic recognizes only a
  DIRECT lower-numbered dependency and would otherwise infer queued `145-S` as
  `146-S`'s predecessor and block the first claim. The edge is transitively
  implied by the two-hop path, so it does **not** shorten the chain and does
  **not** permit `144-S` to run before `147-S`: `144-S` still blocks on
  `147-S`. Full record:
  `docs/memory/2026-08-21-stage-144-146-topology-compatibility-edge.md`.
* `146-S` remains the chain source and the only claimable shipment.
* **MANDATORY**: reload `main` agent instructions after `147-S` merges and its
  P-020 post-merge closure completes, **before** `144-S` is selected or
  claimed.

Full record: `docs/memory/2026-08-20-stage-b19e9662-ship-pre-archived-execution-contract.md`
(stash `B19E9662`, deliberation `022-DL`, plan
`docs/plans/2026-08-20-ship-pre-archived-manifest-member-execution-plan.md`,
hardening HARDENED H1-H7, review PASS).