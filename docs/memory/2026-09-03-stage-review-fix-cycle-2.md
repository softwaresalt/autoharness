# Stage session memory — review-fix cycle 2 (SHIP-2/3/4/6/7/8/10)

* **Date:** 2026-09-03
* **Branch:** `chore/stage-159-167-publication`
* **HEAD at session start and end:** `73cb51e6e6d177dd111b2cd987070757cdbc30fc` (no commits made)
* **Routing:** claude-opus-5 / anthropic / high
* **Trigger:** current-head seven-persona re-review returned **BLOCKED** with 17 findings

## Outcome

**READY for re-review.** All 17 findings dispositioned: 15 legitimate and
remediated, 1 accepted as a constraint (17), 1 half-rejected as a false positive
(13). One additional defect was found and fixed during self-review that the
reviewer did not report.

## Verdicts worth remembering

* **Finding 3 (sdist) was the most consequential.** `[tool.hatch.build.targets.sdist]`
  declared *only* `core-metadata-version`, so hatchling's default sweep packaged
  the whole project, and `uv build` publishes that sdist to PyPI and the GitHub
  release next to the wheel. A wheel-only trim removed **nothing** from the real
  disclosure surface. Added AC3b, `160.019-T` (T7b), an sdist manifest overlay,
  and three-channel release-gate coverage.
* **Finding 1 was right in both directions, and cycle 1 was wrong in both.**
  Cycle 1 demanded *every* case be observed red. Several correctly start green —
  the wheel's `force-include` table already lists only the runtime set, so
  `.backlogit/`, `tests/`, `experiments/` are already absent, and both metadata
  pins already exist. Forcing red there means fabricating a failure, which
  destroys the signal where red is real. Meanwhile T9–T13 had *no* red owner at
  all and were authored after the wiring they verify. Resolved with a two-class
  contract (RED-FIRST / CHARACTERIZATION), each requiring a **pair** of recorded
  observations, and by reversing the T9–T13 → T7/T8 edges.
* **Finding 13 is half a false positive.** `E9E5E6CC` **is** durable and tracked
  at HEAD in `.backlogit/archive/stash.jsonl` (blob `aef5f126`). The reviewer
  looked only at the *active* stash, which is empty by design because harvest
  archives consumed entries. `AB387F16` has no durable record and **must not be
  fabricated** — it was a pre-persistence temporary ID. A fabricated record is
  worse than an absent one because it is indistinguishable from a real one later.
* **Archived stash entries are immutable and that is correct.** `stash edit`
  addresses active entries only. The stale `HARVESTED 160.001-T..160.011-T`
  annotation was therefore **not** rewritten; the forward repair is a comment on
  the live feature `160-F` recording the current 19-task scope.
* **Findings 7, 10, 12 were narrow.** In each case the *binding decision body*
  was already correct and only a trailing acceptance line (7), a task **title**
  (10b), or a vector clause (12) was stale. Titles are executed, so a stale title
  is not a documentation nit.

## Self-caught defect (not reviewer-reported)

Ten rows of the new case table named **T16 (the transition ledger)** as
`Green/preservation owner`. T16 verifies and implements nothing, so those
RED-FIRST cases had no implementing task and those CHARACTERIZATION cases named a
task that could not break them. All ten were repointed to `T7`/`T7b`/`T8`.

## Artifacts

* **Plans edited (5):** SHIP-10, SHIP-2, SHIP-3, SHIP-4, SHIP-7.
* **Tasks created (4):** `160.016-T` (T3b), `160.017-T` (T16), `160.018-T` (T2b),
  `160.019-T` (T7b) — each with `size` + `complexity` via the registry's two
  separate mutation-seam calls.
* **Tasks updated (22):** all 15 pre-existing SHIP-10 tasks, plus `152.002-T`,
  `153.004-T`, `154.002-T`, `154.004-T`, `156.002-T`, `157.002-T`, `158.003-T`.
* **DAG rewired:** 10 edges removed, 27 added. Acyclic, 19 nodes, 2 roots
  (`T1`, `T2a`), 1 sink (`T15`).
* **Shipment `168-S`:** 20 members (1 feature + 19 tasks).

## Verification results

| Check | Result |
|---|---|
| `backlogit doctor` | 63 issues — **all pre-existing**, zero overlap with touched records; already captured as an active P-021 deferred entry |
| DAG acyclicity / topological sort | PASS — 19 nodes ordered, 0 cycles |
| Test-first ordering across 45 cases | PASS — 0 violations |
| Plan ↔ queue ↔ shipment bijection | PASS — 19 / 19 / 19 |
| `Tn` back-reference consistency | PASS — 19 / 19 both directions |
| Size + complexity enum validity | PASS — 26 / 26 tasks; none above `M` |
| Plan-table vs queue size/complexity parity | PASS — 19 rows, 0 mismatches |
| Cross-reference integrity | PASS — all flagged paths are forward references, explicit-absence statements, or a checker artifact |
| Placeholder scan | PASS — every `{{...}}` is a quoted template-variable name |
| Policy boundary | PASS — no source/test/config edits, no commits, no claims, no worktrees |

## Preserved prior decisions

* `167-S` still `queued` and still blocked by `168-S`.
* Workspace-wide doctor hygiene remains captured separately, not normalized only
  on new records.
* Cycle-1 P-021 captures `00C2B1F9` and `F73A04A2` intact in the active stash
  (40 active entries).

## Next steps

1. Operator re-runs the seven-persona review against the remediated head.
2. One review-fix cycle remains of the three available.
3. Ship owns execution; Stage made no claim.
