# Stage session — EDE3CC2D → 132-F / 141-S (P-015 cascade pre-archived members)

Date: 2026-08-18
Agent: Stage (DARK_MODE_ACTIVE, operator AFK, autonomous within exact scope)
Scope: stash entry `EDE3CC2D` **only**. `1EFDA8EE` and all other stash/queue work untouched.
Route: `claude-opus-5` / `anthropic` / `high`
Staging branch: `chore/stage-141-S` (branched from `main` @ `cf8e70e0`)

## Outcome

| Artifact | ID |
|---|---|
| Covering feature | `132-F` |
| Tasks | `132.001-T`, `132.002-T`, `132.003-T` |
| Shipment | `141-S` (status `queued`, 4 items, `unsized: 0`) |
| Stash disposition | `EDE3CC2D` archived with forward reference |

## What the session established (the decisive part)

The stash entry, and the compound doc behind it, framed this as an unknown:
does the cascade close operation tolerate manifest members archived **before**
shipment-level closure runs? A three-arm spike in isolated throwaway workspaces
(system temp, `--cwd` pinned, live `.backlogit/` never mutated) answered it:

* `backlogit shipment ship` v1.9.0 is **fully idempotent** over pre-archived
  members. Control / partial-pre-archive / full-pre-archive arms all returned
  identical `archived_ids` (task + feature + shipment record), `returned_ids: []`,
  `parent_id` preserved, exit `0`.
* `classify_shipment_close_path` returns a clean `CASCADE` in every arm — it
  already reads both `queue/` and `archive/`.
* Every verification step the Cascade Close Sub-Procedure performs (steps 2, 3,
  4, 6) **passes unchanged** in the pre-archived case.

**Therefore there is no engine-behaviour gap — the gap is purely documentary.**

## Correction to the compound library (important for future sessions)

`docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md`
recommends "adjust the `archived_ids` exact-match post-condition to account for
items that were already archived". **That remedy is wrong and was rejected on
evidence.** The engine already includes pre-archived IDs in `archived_ids`, so
the exact-match check passes today; relaxing it would weaken a live P-005
out-of-scope-mutation detector for no benefit.

Ship is bound by the plan's *Post-merge obligation* section to run
**compound-refresh** on that entry at Step 6 closure. Do not let a future
session re-derive the rejected Option A.

Similarly, `src/autoharness/gates/shipment_closure.py` is **deliberately
unchanged** — the operator scoped code changes to "only if evidence proves code
behavior needs change", and the evidence proves the opposite.

## Decomposition rationale

Contract-only fix, three width-isolated tasks, one file each:

1. `132.001-T` — skill contract (`shipment-reconcile/SKILL.md.tmpl`), S / medium.
   Added as an **unnumbered preamble**, not a numbered step: inserting a step
   would renumber step 4 and falsify the live cross-reference at SKILL line 379.
2. `132.002-T` — policy mirror (`workflow-policies.md.tmpl`), XS / low.
   Appended as item 7 / trailing paragraph so P-015 items 1-6 keep their numbers
   and item 5's "any of the preconditions above" stays accurate.
3. `132.003-T` — regression tests, S / low. Positive **and** negative cases, so
   the suite cannot pass against a classifier that ignores archival state.

Dependencies: `132.001-T` blocks both `132.002-T` and `132.003-T` (wording
dependence). No parallelisation; Ship executes serially.

## Gates

* Spike → deliberation (4 options, D selected) → plan → **plan-harden** (H1-H8,
  required because the change edits a P-015 safety policy) → **plan-review**
  multi-persona adversarial, 6 personas, 7 findings (4×P1, 2×P2, 1×P3).
* **Verdict PASS — 0 unresolved P0, 0 unresolved P1.**
* Notable P1s resolved: incentive attack via deliberate pre-archival (structurally
  impossible — the classifier, not archival state, selects the path); numeric
  cross-reference breakage (H1); spike root-name transferability `.backlog` vs
  legacy `.backlogit` (source-verified: the classifier is parameterised on the
  backlog dir and never branches on root name).

## Deliberate exclusions (scope discipline)

* `templates/agents/_ship.agent.md.tmpl` + its checksum-tracked mirror — its
  close-path section (line 714) **already** states "select the close path from the
  verified check, never from prose alone". Including it would have forced a
  `harness-manifest.yaml` checksum refresh for zero correctness gain.
* No mirrors exist for either edited template (verified).

## Environment findings (not actioned — out of scope)

* **Registry/CLI drift**: `.autoharness/backlog-registry.yaml` declares no
  `features.sizing` and its `update_task` params omit `size`/`complexity`, but
  installed `backlogit v1.9.0` supports `--size`, `--size-source`,
  `--size-ruleset-version`, `--complexity` as mutually exclusive body-preserving
  seams. Structured sizing was used (it is genuinely available); the registry is
  stale. Candidate future stash entry — **not** raised this session to avoid
  scope expansion.

## Checkpoint state

**No active checkpoint left.** Stage's work for `EDE3CC2D` completed within this
session, so leaving an active recovery candidate for completed work is prohibited.
Nothing to resume.

## Handoff

`141-S` is queued and is the handoff token to Ship. Global ordered run is
`EDE3CC2D` → `1EFDA8EE`; `1EFDA8EE` remains unplanned and untouched.
Stage did not open or merge a PR — Orchestrator routes Ship to publication.
