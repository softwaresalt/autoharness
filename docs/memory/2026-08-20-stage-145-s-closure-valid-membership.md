---
title: "Stage session - 145-S manifest restored to closure-valid full-child membership"
date: 2026-08-20
agent: stage
route: "claude-opus-5 / anthropic / high (P-013.5)"
branch: chore/stage-144-s
stash_consumed: []
stash_created: []
features: [137-F]
tasks: []
superseded: [137.005-T, 137.006-T]
shipments: [145-S]
execution_order: "146-S -> 144-S -> 145-S"
terminal_state: "145-S queued; manifest closure-valid (classifier: cascade); executable scope still four tasks"
---

# Stage session memory - 2026-08-20 (145-S closure-valid membership)

## Scope

Operator-directed bounded, same-contract (P-021 C1) correction of the remaining
Copilot review thread on PR #375 - thread `PRRT_kwDORzpWpM6bB9OQ`, comment
`3827155258`, against `.backlogit/queue/145-S.md`. No deferred item was created;
the whole finding is inside the contract this branch already authorizes.

## Finding, confirmed read-only

`145-S`'s manifest had been reduced to `[137-F, 137.002-T, 137.001-T,
137.003-T, 137.004-T]`, dropping the two superseded children `137.005-T` and
`137.006-T` when they were archived. `137-F` still has **six** children across
`queue/` + `archive/`, so the reduced manifest could not pass **either**
supported closure path:

* **Cascade refused.** `autoharness.gates.shipment_closure.classify_shipment_close_path`
  enumerates a root feature's children across **both** `.backlogit/queue/` and
  `.backlogit/archive/`. Against the five-item manifest it returned
  `safe_close: feature member '137-F' has children outside the manifest
  ('137.005-T', '137.006-T')`.
* **Safe-close halted.** P-015 then puts each omitted child in the **protected
  set**, and its baseline integrity gate requires every protected member to be
  present in `queue/`. Both were already archived - classified as a pre-existing
  cascade, halting closure before any manifest item is archived. The
  `pre-archived` exemption covers manifest items only; the protected set has no
  such exemption.

Deadlock: neither path could close the shipment.

## Correction applied

`137.005-T` and `137.006-T` were added back to `145-S.custom_fields.items` using
the **official** `backlogit_add_to_shipment` operation (no hand-edit of the
manifest was needed). Manifest is now
`[137-F, 137.002-T, 137.001-T, 137.003-T, 137.004-T, 137.005-T, 137.006-T]` -
the covering feature first, then the four executable tasks in dependency order,
then the two pre-archived members.

Re-running the classifier read-only:

* before: `safe_close` - children outside the manifest
* after: `cascade: every feature member is a verified fully-covered root`
  (qualifying feature `137-F`)

P-015 exception **item 7** is what makes this safe: a pre-archived manifest
member satisfies the coverage/root checks the same as a queued member, does not
disqualify cascade, and the cascade op is idempotent over it - it still returns
the member in `archived_ids`, so shipment-reconcile's exact-match post-condition
holds unchanged.

## Why claim and execution stay safe

Manifest membership is **not** a schedule.

* `137.005-T` / `137.006-T` remain in `.backlogit/archive/` with
  `status: archived` (`archived_status: queued`), their `[SUPERSEDED by
  137.003-T]` titles, their superseded-by pointers, and **no** dependency edges.
* Ship Step 0.5 item 1a halts only when a `queued` shipment has a manifest task
  that is `active` or `done`; `archived` is neither, so no false
  `SHIPMENT_STATE_INCONSISTENT`.
* Ship Step 2's execution loop has no queued or active record to claim for
  either id.
* `shipment-reconcile` `mode: pre` classifies each as `pre-archived`, which is
  an explicitly **valid** class contributing to `PROCEED`; `mode: post` finds an
  archive file for each, so the post-check also passes.
* `137.003-T` retains sole atomic ownership of the superseded scope; nothing was
  re-opened, re-queued, or un-archived.

## Verification

* `backlogit_sync_index` -> `INDEX_SYNC_OK` at session start and at close.
* `backlogit_get_shipment 145-S` -> covering feature `137-F`, items list of 7,
  `dependencies: [144-S (blocks)]` unchanged, `status: queued` unchanged.
* Child enumeration by `parent_id` scan of `queue/` + `archive/` -> exactly six
  children of `137-F`; every one is now a manifest member; no extras.
* Dependency graph unchanged and acyclic - `137.001-T -> 137.002-T`,
  `137.003-T -> 137.002-T`; `137.004-T` order-independent; `137.005-T` /
  `137.006-T` declare none and none reference them. No cycles, no orphans, no
  dangling references.
* `git status` -> the operator's pre-existing unrelated changes
  (`.gitmodules`, `.mcp.json`, `references/*`, `diff_files.txt`) are untouched.

## Observed, not changed

`144-S` carries the **same** defect: its manifest `[136-F, 136.002-T,
136.003-T]` omits archived `136.001-T`, so the classifier returns
`safe_close: feature member '136-F' has children outside the manifest
('136.001-T',)` and safe-close would then halt on the protected-set baseline.
`144-S` was **not** modified - it is outside the bounded scope of the `145-S`
review thread and needs a separate operator decision. `146-S` was also checked
and is already `cascade`-valid.

The manifest-reduction precedent recorded in
`docs/memory/2026-08-20-stage-gate-cycle-correction.md` (commit `8fa8cf67`) is
**withdrawn** in an addendum there: the absence of a member-removal operation is
the contract, not a gap to hand-edit around.

## Boundary statement

Stage made **no** source, test, template, schema, or config edit; ran **no**
build, test suite, or linter; made **no** branch switch, commit, push, PR, or
GitHub thread reply/resolve; claimed **no** shipment. The single read-only
invocation of `classify_shipment_close_path` is a pure classification function
that never mutates the backlog. Only backlog artifacts and planning/memory
documents were modified. Publication, the PR reply, and thread resolution remain
the Orchestrator's step.

## Addendum — the "Observed, not changed" note on `144-S` is superseded (2026-08-20)

The `144-S` defect recorded above under **Observed, not changed** was
subsequently authorized by the operator and **fixed in the same way**, on this
branch, in a follow-on session. `136.001-T` was added back to
`144-S.custom_fields.items` with the official `backlogit_add_to_shipment`
operation; the classifier moved from
`safe_close: feature member '136-F' has children outside the manifest
('136.001-T',)` to
`cascade: every feature member is a verified fully-covered root`.

Nothing in the `145-S` correction recorded above was undone: `145-S`'s manifest
is unchanged at seven items, still classifies `cascade`, and its
`144-S (blocks)` dependency is untouched. All three shipments in the chain
(`146-S`, `144-S`, `145-S`) now classify `cascade`. Full record:
`docs/memory/2026-08-20-stage-144-s-closure-valid-membership.md`.
