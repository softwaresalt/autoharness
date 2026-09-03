# Stage session — extended review-fix cycle 4 (SHIP-4 / SHIP-8 / SHIP-10)

- **Date**: 2026-09-03
- **Branch**: `chore/stage-159-167-publication`
- **HEAD at session start**: `a03a6ff05b1faedfd13b66984933a76f59d1b338` (clean)
- **Routing**: claude-opus-5 / anthropic / high
- **Budget**: operator explicitly extended the Stage review-fix budget beyond the
  normal 3-cycle limit and directed autonomous continuation to a genuine gate.

## Scope

Fifteen post-cycle-3 findings across three shipments, all confirmed legitimate
and remediated with official backlogit operations only. No Git commit, no
source/test/config implementation, no PR, no shipment claim, no worktree.

## Degraded capabilities

`ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE` — instruction files
present but no MCP tools exposed. Proceeded with file-based exploration per the
documented fallback; no halt required. `TOOL_OK: backlogit` (1.10.1). Storage root
is the legacy `.backlogit/`.

## Findings closed

| # | Surface | Class |
|---|---|---|
| 1 | `154.003-T` asymmetric amended-artifact set | P0 |
| 2 | `158.002-T` owns all B1–B11 (Class R 8 / Class C 3) | P0 |
| 3 | Principle VII destructive-generation approval | P0 |
| 4 | `160.014-T ← 160.002-T` spike edge | P1 |
| 5 | `test_plugin_source_path_is_tracked_and_fetchable` → CHARACTERIZATION | P1 |
| 6 | `test_plugin_payload_conforms_to_the_selected_strategy` branch-parametric | P1 |
| 7 | Observation destinations for T3a/T3b/T9–T13 | P0 |
| 8 | `tests/**` write grants removed from T2b/T6 | P0 |
| 9 | AC2d fixture carve-out + derivation assertion + new named case | P1 |
| 10 | H2 writable-surface audit | P1 |
| 11 | wheel + sdist + plugin channel language | P2 |
| 12 | `160.010-T` bare template token | P2 |
| 13 | Commit-qualified blob reference on `160-F` | P2 |
| 14 | `154.004-T` five outcomes / three under A | P2 |
| 15 | Terminal PASS after recalculation | P1 |

## Key decisions

- **Destructive generation (3)**: planned writes partitioned CREATE / NO-OP /
  OVERWRITE / REMOVE. Non-empty OVERWRITE ∪ REMOVE ⇒ fresh live non-synthesizable
  operator approval, else HALT — regardless of generator trust or directory.
  Empty set ⇒ no approval, and branch (a) must **not** demand one (false gates
  prohibited). `--check` is read-only and never gated. Enforcement lives in the
  generator (T6) so all callers inherit it.
- **Unachievable reds (5, 6)**: a red that cannot exist at baseline is not a
  test-first case. One was reclassified; the other was made branch-parametric so
  the red survives in both branches via a conjunction with file-set equality.
- **Single evidence store (7, 10)**: extended the existing bounded audit surface
  with an `observations/` subdirectory rather than inventing a second store.
  Authorization stated in the operative SAFETY MODE clause, because a destination
  named only in prose still reads as unauthorized under freeze-scope.
- **Green owners cannot write tests (8)**: a green owner able to edit its own
  tests can make them pass by weakening them.
- **Fixture carve-out (9)**: the guarantee is preserved by a derivation assertion,
  not by textual absence. A fixture literal is inert data; a fixture literal that
  something executable *reads* is a second source of truth.

## Measured verification (post-edit)

19 tasks · `168-S` 20 members, unsized 0 · sequencing `159-S→…→166-S→168-S→167-S`
all queued · DAG acyclic 19/19 · 52 cases · 35 RED-FIRST / 17 CHARACTERIZATION ·
author edges 52/52 miss 0 · owner edges 69/69 miss 0 · RED-FIRST ordering 39/39
violations 0 · observation destinations 7/7 · bare tokens outside fences 0 ·
append seams 0.

**Gate after cycle 4: PASS.**

## Next steps for Ship

`168-S` (SHIP-10) is queued and unclaimed, blocked by `166-S` (SHIP-8). Ship owns
claim and execution. Stage took no claim action. Recommended execution order is
the plan's topological order, beginning `160.001-T` / `160.002-T`.
