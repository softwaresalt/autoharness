# Stage session memory — SHIP-10 review-fix cycle 9

**Date:** 2026-09-03
**Agent:** Stage
**Branch:** `chore/stage-159-167-publication`
**Base commit at session start:** `1c50b0a8be6ca71dfeacf8cf15b6514b11d988da`
**Working tree at session start:** cycles 5–8 edits present, uncommitted
**Feature:** `160-F` — Minimal Copilot plugin installation payload
**Shipment:** `168-S` — SHIP-10

## Operator authorization

Add **exactly one** bounded prerequisite task to `160-F`/`168-S` implementing
test-toolchain alignment, plus verify/fix thirteen enumerated review items, then
re-run all exact consistency checks and a fresh Stage plan review requiring zero
P0/P1. Explicitly authorized as **same-contract completion**: the task is required
to execute the already-authorized test harness under the repository's
non-negotiable Constitution. **No other new task, channel, case, engine, schema,
or dependency.**

## What was created

**`160.020-T`** — *Test-toolchain alignment prerequisite: declare and lock pytest,
move CI to the canonical runner* (`T0`).

* parent `160-F`, status `queued`, priority `high`
* `size: S`, `complexity: medium`, `size_source: agent`,
  `size_ruleset_version: ah-stage-sizing-v1`
* labels: `ci`, `toolchain`, `dependencies`, `prerequisite`, `fail-closed`
* **ID allocation:** next valid non-retired ID. `160.019-T` (retired sdist-wiring
  tombstone) was **not** reused.

### Measured evidence that justified it

* Constitution declares the Test gate as `pytest`; PR-automation instruction gives
  `uv run python -m pytest`; `pyproject.toml` already has a live
  `[tool.pytest.ini_options]` with `pythonpath = ["src"]`.
* `uv.lock` locks exactly eight distributions and **`pytest` is not among them**;
  `pyproject.toml` declared no `dependency-groups` and no test extra;
  `ci.yml` ran `PYTHONPATH=src python -m unittest discover -s tests`.
* Conclusion: pytest is **configured and mandated but not locked**, and CI has
  drifted off the mandated runner.

### Scope of `T0` (three files, nothing else)

1. `pyproject.toml` **test-dependency section only** — one pinned `pytest`
   declaration via `[dependency-groups]`.
2. `uv.lock` — regenerated, bounded reviewable diff.
3. `.github/workflows/ci.yml` **`test` job only** — pinned `setup-uv` at the same
   SHA `release.yml` uses, canonical `uv run python -m pytest`, retained
   fail-closed `--version` preflight.

Authors no payload behaviour test, no case, no channel, no schema. All three files
are **AC11 Exclude in both channels**, so the task cannot invalidate `T2a`'s
baseline inventories or aggregate digests. Produces **no AC3e partition record**
(runs no generator) — only pre-change byte captures.

## Graph placement

`T0` is a **third DAG root** (no prerequisites). Three edges added:

* `160.020-T → 160.005-T` (`T3a`, RED-FIRST harness)
* `160.020-T → 160.016-T` (`T3b`, CHARACTERIZATION harness)
* `160.020-T → 160.015-T` (`T14`) — transitively implied, recorded explicitly
  because `T14` is the task cycle 8 left knowingly blocked

`T3a`/`T3b` are the earliest nodes that must **execute** a test, so blocking them
places `T0` before every SHIP-10 test author and consumer requiring pytest.

**`pyproject.toml` now has two editors in disjoint regions** — `T7` owns the build
tables, `T0` owns `[dependency-groups]`. Serialization is guaranteed by the DAG
(`T0 → T3a → … → T7`), so **no extra edge** was added. `T7`'s "sole editor of
`pyproject.toml`" claim was narrowed to "sole editor of the build tables".

## Revised counts (recomputed after the last edit)

| Quantity | Before | After |
|---|---|---|
| Live tasks | 18 | **19** |
| DAG nodes / edges | 18 / 48 | **19 / 51** |
| DAG roots | 2 (`T1`, `T2a`) | **3 (`T0`, `T1`, `T2a`)** |
| DAG sink | `T15` | `T15` (unchanged) |
| Live size histogram | `S 9, M 9` | **`S 10, M 9`** |
| Derived `size_composition` | 19 members, `M:10, S:9` | **20 members, `M:10, S:10`** |
| `168-S` manifest entries | 19 | **20** |
| Case ledger | 46 / 32R / 14C | **unchanged** |
| Green/preservation owner edges | 52 | **unchanged** |
| RED-FIRST author-before-owner paths | 34 | **unchanged** |

The derived rollup traverses the **feature's children**, not the manifest, so it
includes the archived `160.019-T` (`M`) tombstone. Subtracting it from
`M:10, S:10` yields exactly the 19-task live histogram `S 10, M 9`.

`160.020-T` was **appended as manifest entry 20** — backlogit's add-to-shipment
operation takes no position argument. Manifest order is not execution order; the
DAG is authoritative.

## The one live defect found

**P1 — surviving "hermetic actual upgrade" claim.** The mandatory-durable-outputs
table still described `T10`'s baseline consumption as a *hermetic actual upgrade …
rebuild and verify the baseline wheel locally*, the exact form cycle 8 item 8
withdrew from AC6, V3 and `160.012-T`. Rewritten to **"local-artifact upgrade
orphan/behaviour guarantee"** with an explicit cycle-9 withdrawal note (no baseline
rebuild, no network, no venv, no export dir, no worktree). The real gap stays
**live residual risk** as deferred entry `60C207F1` — narrowed and honest, not
falsely closed.

The other twelve operator items were verified **already correct** in the cycle 5–8
tree and are recorded as re-verified rather than silently omitted.

## Secondary defect corrected

The **cycle-8 plan-review section was never written**, so the cycle-7 gate's
*"Cycle 8 superseded this verdict — see below"* pointed at nothing. A `## Plan
Review — review-fix cycle 8` section was reconstructed **from the dated
`(cycle 8, item N)` annotations cycle 8 actually wrote into the artifacts**, not
from memory, and its gate verdict recorded.

## Case rename (operator item 10)

`test_target_workspace_prefix_derivation_predicate_holds` →
**`test_target_workspace_prefix_derivation_is_centralized`**, atomically across
AC2d prose, the 46-row ledger, and `160.003-T`, `160.004-T`, `160.005-T`,
`160.017-T`, `160.018-T`. **Count unchanged at 46.** The old name was a tautology;
the case is RED-FIRST and not yet authored, so no shipped suite desynchronizes and
`T16`'s bijection is re-established in the same cycle.

## Backlog records edited

* `160.020-T` — created
* `160.015-T` (`T14`) — **all `ci.yml` ownership stripped**; `T0` prerequisite
  added; knowingly-blocked record closed; rollback narrowed to one file;
  acceptance and size rationale recomputed (**stays `M`**)
* `160.005-T` (`T3a`) — `T0` prerequisite prose; case rename + withdrawal note
* `160.016-T` (`T3b`) — `T0` prerequisite prose
* `160.006-T` (`T7`) — "sole editor" narrowed to the build tables (two places)
* `160.003-T`, `160.004-T`, `160.017-T`, `160.018-T` — case rename
* `160-F` — live-task cardinal 18 → 19; new **SOURCE-TRACEABILITY FORWARD
  CORRECTION (CYCLE 9)** comment enumerating the nineteen live tasks
* `168-S` — `160.020-T` added to the manifest

## Gate

**PASS — zero P0 and zero P1.** Publication diff verified as **only
`.backlogit/**` and `docs/**`**. Encoding sweep over all 47 changed files: 0
control characters outside tab/LF/CR, 0 U+FFFD, 0 BOM, 0 unbalanced fences, all
frontmatter parses. 36 table blocks, 0 column-count mismatches.

## Open P2 follow-up

**`T14` (`160.015-T`) sizing is near-boundary.** Cycle 6 raised it `S` → `M` on
two grounds: (a) the two asymmetric `release.yml` gate steps, (b) the third step in
`ci.yml`. Cycle 9 moved (b) entirely to `T0`. Ground (a) alone still carries `M` —
Gate B's digest-identity discipline is the expensive part and did not move.
Recorded rather than silently inherited or speculatively downsized; **re-measure at
execution time**. Blocks nothing; `M` is the conservative direction.

## Carried-forward residual risk (unchanged)

* `99818C6D` — deferred sdist channel (high)
* `60C207F1` — reproducible offline end-to-end upgrade testing (high) — **live**
* SHIP-8 — no runtime predicate for the sizing budget

## Next steps for Ship

Execute `168-S` starting from the three DAG roots. **`160.020-T` must run first**
among them for any task that executes a test. Stage performed no Git commit, no
source/config/workflow edit, no PR, no shipment claim, and no worktree creation.
