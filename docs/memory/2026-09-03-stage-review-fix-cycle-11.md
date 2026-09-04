---
title: "Stage session memory — SHIP-10 review-fix cycle 11"
date: 2026-09-03
agent: stage
shipment: 168-S
feature: 160-F
plan: docs/plans/2026-09-03-minimal-copilot-plugin-payload-plan.md
review_history: docs/reviews/2026-09-03-minimal-copilot-plugin-payload-plan-review-history.md
verdict: PASS
---

# Stage session memory — SHIP-10 review-fix cycle 11

Bounded correction pass over the canonical SHIP-10 plan and its 19 task records.
Stage/backlog/docs only. No Git, source, test, config or workflow implementation;
no PR, no shipment claim, no worktree. No new task, channel, schema, engine or
dependency. One new test case was explicitly authorized as same-contract
completion.

## The decision that shaped the cycle

`P-004` states its red-phase precondition literally as
`PYTHONPATH=src python -m unittest discover -s tests`; the Constitution names
`pytest`. Verified against `.github/policies/workflow-policies.md` before acting.

The reconciliation costs no policy change and no schema field:

1. Every case this shipment authors is a `unittest.TestCase` method, so both
   runners collect it.
2. P-004's confirmation is **whole-suite and gate-scoped** and is always taken
   with its exact unittest command, before and after T0. `unittest` is stdlib —
   no lock, no dependency group, no network.
3. Per-case ledger observations use `uv run python -m pytest` once locked, with
   exactly one pre-lock exception: T0's own red on the committed pre-change tree.
4. `test_node_id` needs no runner field. A node ID is a property of a case's file
   and class location, fixed at authoring time; T16 verifies every node ID against
   a **terminal** `--collect-only` run, by which time pytest is locked.
5. `artifact_ref` for a case that builds nothing stays phase-selected, with a
   **source-tree** identity source (`baseline` → T2a's E2 commit SHA;
   `post-change` → the observation's own `source_commit`). Inventing an artifact
   digest for a case producing no artifact would have been a fabricated value.

## Defects worth remembering

* **The plan's own rollups were internally inconsistent.** The per-author line
  read `Totals 32 R` and omitted T0; the per-owner itemization summed to 52 while
  its bolded total claimed 53. Both survived because nothing recomputed them from
  the ledger table. Lesson: parse the ledger and re-derive every stated rollup —
  never trust a summary line that sits next to the table it summarizes.
* **The truncation contradiction spanned eight records.** T16 was fixed to reject
  over-bound logs, but all seven producer records still instructed producers to
  truncate head-and-tail. A producer following its own record would have complied
  and still failed the shipment. Lesson: when a rule is enforced by one task and
  obeyed by seven, fixing the enforcer is half the edit.
* **The T10 phantom-orphan defect.** The old U1/U4 compared a baseline
  *install-output* listing (workspace / `site-packages` destination paths) against
  the trimmed wheel's `RECORD` (archive-relative member paths). Two different path
  universes, so nearly every path differs even when nothing moved. Fixed to
  `RECORD`-vs-`RECORD` with a **closed** allowed-metadata-difference list.
* **Generator scope ≠ approval scope.** The withdrawn T0 clause conflated AC3e's
  classification machinery (generator-scoped) with the Layer-2 approval obligation
  over a tracked `OVERWRITE` (not generator-scoped). Left as written, "author the
  edit by hand" became a silent bypass of Principle VII — strictly worse than
  running the generator.
* **Naive stale-token greps flag withdrawal text.** Every `46` / `52` /
  `single-occurrence` hit needed context inspection; most hits were the very
  clauses that withdrew the stale wording. Three genuine live stale figures hid
  among them (`160.005-T`, `160.017-T`, `160.020-T`).

## Metrics after the cycle

| Metric | Value |
|---|---|
| Ledger cases | **47** unique — 33 RED-FIRST + 14 CHARACTERIZATION |
| Owner assignments | **53** (six two-owner cases; case 47 author = owner) |
| RED-FIRST ordering paths | **34**, zero reachability violations |
| Live tasks / DAG edges | **19 / 51**, acyclic, no dangling deps |
| Live size histogram | **S 8 / M 11**; complexity trivial 1 / low 2 / medium 14 / high 2 |
| `168-S` manifest | 20 entries, `160-F` first, `160.019-T` absent |
| Derived `size_composition` | **M 12 / S 8** (includes archived `160.019-T`) — known P2 |
| Pre-change captures | **6** across 4 tasks (T0×3, T7, T8, T14) |
| Plan size | 850 → **979 lines**, 41,014 → **49,734 bytes** |
| Publication diff | `.backlogit/**` and `docs/**` only |

## Carried forward

* `0B83AC8F` — T3a (`160.005-T`) 22-case sizing against the 2-hour bound.
  Deferred; disposition required before or during execution.
* `60C207F1` — real offline installed-upgrade execution. Deferred, open residual
  risk. V3 ships in local-artifact / `RECORD` form only.
* `99818C6D` — sdist channel remains ungated.
* `168-S` rollup anomaly: never quote the derived histogram as the live one.

Publication readiness: **`READY_WITH_FOLLOWUPS`**.

## Next step

Ship executes `168-S` from `160.020-T` (T0). T0's tracked writes to
`pyproject.toml`, `uv.lock` and `ci.yml` require fresh live operator approval over
the exact reviewed OVERWRITE partition — that gate binds at implementation, not at
Stage publication.
