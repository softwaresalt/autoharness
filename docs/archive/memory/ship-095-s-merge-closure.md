---
type: ship-session
date: "2026-07-27"
agent: Ship
shipment: "095-S"
feature: "090-F"
pr: 235
merge_commit: c6d712b25d52635a3961fc3426091e2bcb106101
status: shipped
---

# Ship Session — 095-S / 090-F Merge and Post-Merge Closure

## Summary

Merged PR #235 (feature 090-F, "PR #227 telemetry hardening" — 8 file-disjoint
TDD tasks 090.001-T through 090.008-T) with operator-approved P-014 sign-off.
Merge commit `c6d712b25d52635a3961fc3426091e2bcb106101` (2 parents confirmed:
`75f645ae` main tip + `2d0bb75` feature HEAD — genuine merge commit, P-009
satisfied). Attended (non-dark) mode; feature-source merge held for explicit
operator approval and not auto-merged.

## Pre-merge state

- HEAD `2d0bb75` at merge time.
  `autoharness gate copilot-review 235 --repo softwaresalt/autoharness
  --enforcement auto` → `SATISFIED: PASS` (re-verified immediately before merge).
- All 3 CI checks green (`ci gate`, `detect code changes`, `test`).
- mergeable=MERGEABLE, mergeStateStatus=CLEAN, 0 unresolved review threads,
  reviewDecision=null (no required human review).
- §1.9 readiness gate: all 5 checks PASS; PR body `## Local Review Readiness`
  block = `READY`, P0/P1=0, full local build 701 tests OK.

## Copilot review remediation (P-018) — 5 rounds, all threads resolved

Each round: fix → commit → push → reply to thread → `resolveReviewThread`
(GraphQL). Rounds converged 3→1→2→1→1→0 threads; each finding was a genuinely
new, valid issue on newly-introduced code (not a re-raise), so the P-018
"unresolved Copilot threads block merge" rule left no "accept as backlog"
option. See `docs/compound/095-S-derived-metric-provenance-additive-map.md`.

| Round | Commit | Fix |
|---|---|---|
| 1 | `d32bcfa` | report `_quality` skips zero-valued unlabeled metrics; `record` rejects tz-naive timestamps; documented `_field_quality` asymmetry |
| 2 | `98a2b99` | numeric-only derived ratios + additive `derived_quality` provenance map (aggregation + eval/summary + report + docs) |
| 3 | `fd52cb3` | `_normalize_quality` fail-closes malformed `metric_quality` (fixes unhashable `_QUALITY_RANK` crash + undocumented-marker leak) |
| 4 | `117ada7` | `derived_quality` made additive/optional on exported `ConfigSummary`/`BaselineSummary` (backward-compat) |
| 5 | `2d0bb75` | same normalization applied to report `_quality` (2nd site of the round-3 issue) |

## Post-merge closure work

1. Verified merge commit has exactly 2 parents (P-009). Fast-forwarded local
   `main` to `c6d712b`.
2. Created post-merge branch `post-merge/090-telemetry-hardening` from `main`.
3. **Single-artifact safe-close** (NOT the forbidden `backlogit shipment ship`
   cascade, P-015): archived the 8 manifest tasks individually
   (`backlogit move <id> --status done` → `backlogit archive <id>`) and the
   shipment record `095-S`; **preserved feature 090-F in queue** (status
   `active`, matching the committed 089-F precedent). Protected-set (090-F)
   verified present after every archival.
4. **Pitfall hit and recovered**: `backlogit move 090-F --status done` on the
   feature *relocated it to archive* (registry routing sends terminal statuses
   to `archive/`). Caught immediately (nothing staged/committed yet), restored
   090-F to `.backlogit/queue/` and set `status: active`. Lesson: never run
   `move --status done` on the protected feature — leave it untouched or set a
   non-terminal status; only manifest task IDs get the move→archive treatment.
5. Ran `backlogit sync` → exit 0 (CLOSURE_INDEX_SYNC_OK).
6. Committed archival (`b47564e`) with surgically-staged paths only (never
   `git add .backlogit/` — that would grab pre-existing untracked logs and
   checkpoints).
7. Wrote `docs/compound/095-S-derived-metric-provenance-additive-map.md` and
   this session memory.

## Follow-ups (Ship-reported, not backlog items — Role Boundary)

None from the merged feature. Out of scope and untouched: 5 left-stashed
telemetry entries and the broader other-domain stash (12+ items) remain for a
later Orchestrator → Stage cycle.
