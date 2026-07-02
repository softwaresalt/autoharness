---
type: session-memory
agent: Ship
date: 2026-07-02
session: post-merge closure — headless eval runner + deterministic reviewer matrix (055-F Shipment B)
shipment: 056-S
tags: [eval, reviewer, deterministic, ship, closure, backlogit, shipment-ship, cascade-bug, backlog-integrity]
---

# Ship Session — Eval Runner + Reviewer Matrix (055-F Shipment B)

## Summary

Post-merge closure of shipment **056-S** — the headless evaluation runner plus
deterministic reviewer matrix for feature **055-F** (Phase-2 evaluation,
Shipment B). Delivered via PR
[#126](https://github.com/softwaresalt/autoharness/pull/126), merged into `main`
as merge commit `1b1ef42cf201457d781602098ee71e278245de54` on 2026-07-02.

## What shipped

New `src/autoharness/eval/` package — an **injectable / replay** execution runner
(`runner.py`, no live model runtime), a rule-based **line-cited diff grader**
(`reviewer.py`), a model-config matrix loader (`matrix.py`), and a comparative
baseline summary (`summary.py`), wired through the `eval` CLI. Evaluation emits
telemetry **one-way** (fail-open); a hermetic boundary test locks in the
"no live model call" invariant.

## Re-decomposition (055.001 → 055.004/005/006)

055-F's Shipment-B scope was re-decomposed from the umbrella task **055.001-T**
into three delivered tasks:

- **055.004-T** — eval model-config matrix loader (`63bbaa1`)
- **055.005-T** — frozen-state execution loop (`a98fe16`)
- **055.006-T** — comparative baseline summary + `eval run` CLI wiring (`b970e1b`)

plus the reviewer matrix grader **055.002-T** (`74f62d6`). These four tasks
(`055.002/004/005/006-T`) are the shipment's `items`. The umbrella **055.001-T**
was closed `done` at closure since its children shipped.

## Review

Two review-fix commits landed on the branch:

- `fd12160` — validate eval matrix baseline sub-blocks; expand eval public API
  (056-S review gate).
- `46db958` — two P3 correctness fixes from PR-#126 review:
  1. `reviewer.py` `parse_unified_diff` misread an added line whose content
     starts with `+++ ` as a new-file header (reset hunk state, dropped
     remaining lines). Fixed by gating header detection on hunk state and
     tracking the `@@ +c,d @@` declared new-line count.
  2. `cli.py` `_eval_command` scanned *all* remaining tokens for `help`, so a git
     ref literally named `help` could not be a `--base`/`--head`. Fixed to only
     treat the leading token as a help request.

Two residual P3 diff-parser/CLI stash bugs (`635F74A0`, `B423FDD7`) were folded
into the fix and archived out of the active stash during closure.

## backlogit cascade-bug incident + remediation

**Hazard.** `backlogit shipment ship 056-S` walks to parent **055-F** and
archives it, cascading/orphaning siblings — including `055.003-T` (Shipment C,
still blocked on an external backlogit `--size` dependency) and umbrella
`055.001-T`. `backlogit archive` is suspected of the same walk. A **prior 056-S
closure attempt hit this cascade and was git-reverted** wholesale.

**Remediation (this session).** Closed 056-S with **single-artifact operations
only**, verifying invariants after every mutation:

1. `backlogit move 056-S --status done` (active → done).
2. `backlogit move 055.001-T --status active` then `--status done`
   (queued → active → done; direct queued → done is rejected by the transition
   pre-hook).
3. `backlogit update 056-S --commit 1b1ef42… --description ...` to record the
   release.
4. `backlogit sync` to rehydrate the index.

After each step, re-read invariants — **055-F stayed `blocked`**, **055.003-T
stayed `blocked` with `parent_id: 055-F`**, **055.001-T kept `parent_id:
055-F`**. No cascade occurred; the only file moves were the expected
queue → archive relocations of `056-S.md` and `055.001-T.md`. A follow-up chore
was stashed to upgrade/patch backlogit past the cascade bug.

## Closure

056-S = `done`, merge commit `1b1ef42…` recorded via `backlogit update`.
Legitimate stash drift (`C414C5C6` retained; `635F74A0`/`B423FDD7` archived)
folded into the closure commit. Delivered as closure PR from
`chore/close-056s` — **not merged** (P-014: separate operator approval required).

## Next step

**Shipment C (055.003-T)** — the sizing gate — remains **blocked** on the
external backlogit `--size` capability. 055-F stays `blocked` (parent
harness_status pending) until its final task ships. No release obligations
(feature; no tag/publish).
