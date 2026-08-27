---
title: "Compacted — PR #412 merge and post-merge P-020 assessment"
date: 2026-08-27
source: docs/memory/compacted/2026-08-27-pr412-closure-p020-assessment-compacted.md
doc_type: memory
release_unit: "PR #412 (no shipment) — terminal closure of PR #411"
agent: orchestrator
---

# Compacted — PR #412 merge and post-merge P-020 assessment

Bounded Tier-1 floor artifact for the release unit closed by PR **#412**
(merge commit `3233030e`, two parents — P-009 satisfied). PR #412 was itself the
terminal post-merge closure of PR #411, so this record closes the chain; it does
not spawn a further closure PR.

## Outcome

PR #412 merged after **four** Copilot review rounds and one independent
self-review round. Four findings were raised and fixed; a fifth was found by
self-review after three Copilot rounds had passed over it.

| Round | Findings | Fixed in |
|---|---|---|
| Copilot @ `309fb1ec` | P-020 floor consolidation skipped; over-broad root-cause heading | `a0d96d01` |
| Copilot @ `a0d96d01` | traceability claimed bidirectional; PR description stale | `2793c297` |
| Copilot @ `2793c297` | none | — |
| Self-review | overgeneralized P-018 deadlock claim | `e4cbe0c2` |
| Copilot @ `e4cbe0c2` | none — gate SATISFIED for the merged HEAD | — |

## Transferable learning — the P-018 deadlock is intermittent, not structural

Both #411 memory artifacts had inferred that once a Copilot review request is
satisfied, a review-fix push triggers no new review, so the gate "can never
self-clear". **PR #412 disproved this three times**: Copilot re-reviewed and
cleared the gate after each of `a0d96d01`, `2793c297`, and `e4cbe0c2`, with no
force used anywhere on that PR.

This mattered for safety, not just accuracy. As written the claim implied that
an unreviewed HEAD is by itself sufficient evidence of a stall — which would
convert the audited `--force` override into a routine bypass of a fail-closed
gate. Both files now require an *observed* stall across the full §1.2 back-off
before forcing. The correction was left visible rather than silently rewritten:
the #411 observation still stands; only the inference drawn from it was wrong.

## The same counting error recurred three more times — in my own analysis

The fairness test carried over from #411 (*is this a regression this change
introduces, or pre-existing ambient state?*) generalizes to a second discipline:
**verify your own counts before asserting them.**

* First heuristic pass over `docs/plans` reported **19** consolidation
  candidates. Inspecting actual headings showed the regex conflated three
  distinct classes: plans with a genuine appended `## Plan Review` section,
  separate `-hardening.md` artifacts, and plans carrying only amendments.
  Precise count: **3**.
* The #411 closure record asserted `docs/plans | 65 | 642 KB | 0` further
  candidates and "no further file qualifies". That is **wrong** — see below.
* This artifact's own first draft reported `docs/memory | 36 | 430 KB | no |
  0 files older than 14d`. Two errors: it counted the root only (recursively it
  is **92 files / 730 KB**, over both thresholds), and its date heuristic keyed
  on a `YYYY-MM-DD` filename prefix — so it silently skipped
  `098-S-closure.md`, which has an **undated filename** and is 29 days old.
  Caught by Copilot review, not by me.

Over-calling and under-calling are the same failure. **A heuristic that cannot
parse an item must report it, not skip it** — a filter that silently drops
unparseable entries yields a confident, wrong zero. That is precisely how both
the `0 candidates` claims in this chain were produced. Note the 2026-07-30
compaction had already flagged this exact file as awkward ("despite its undated
filename"), so the signal existed in the repo and the heuristic still missed it.

## P-020 assessment for this merge (honest result)

Invocation is mandatory per merge; candidate selection stays threshold-gated.
Assessment performed against each target directory on its own criterion:

| Directory | Files | Size | Over threshold? | Candidates |
|---|---|---|---|---|
| `docs/memory` (recursive) | 92 | 730 KB | **both** | **1** — `098-S-closure.md` |
| ├ root only | 36 | 430 KB | no | 1 (the file above) |
| ├ `compacted/` | 51 | 281 KB | file count only | 0 — compacted outputs, preserved by rule |
| └ dated subdirs | 5 | 19 KB | no | 0 (all within 14d) |
| `docs/plans` | 65 | 642 KB | **both** | **3** with appended `## Plan Review` |
| `docs/closure` | 32 | 405 KB | no | 0 |

`docs/memory/098-S-closure.md` (shipment 098-S, `closed_at: 2026-07-29`) is a
genuine eligible candidate, not an exclusion. The 2026-07-30 compaction preserved
it on an explicitly **time-conditional** ground — "within the 14-day threshold, so
preserved despite its undated filename". That condition lapsed on 2026-08-12; at
29 days old with no active work referencing it, it now satisfies the Phase 2
memory criterion. Captured for action rather than compacted here, to keep this
floor artifact bounded.

**Per-merge floor**: no separate completed-work memory existed for the #412 unit
(its "work" was writing #411's closure), so the floor action is this record.

**Correction to the merged #411 closure record**: its claim of 0 further
candidates in `docs/plans` was produced by assessing `docs/memory` age and
generalizing that no-op to the other directories. Each directory has its own
Phase 2 criterion and must be evaluated separately. Captured forward as
`7645AE19` rather than rewriting the merged artifact.

## Follow-ups captured

* `91CE2B66` (chore) — P-020 compaction backlog: consolidate the 3 plan-review
  candidates and `docs/memory/098-S-closure.md`; decide whether `-hardening.md`
  artifacts are in scope for compaction at all (**requires deliberation**)
* `7645AE19` (bug) — correct the closure record's candidate claim forward; add a
  regression guard so assessments evaluate each directory on its own criterion,
  count recursively, and never silently skip an item the date heuristic cannot
  parse
* Carried from #411: `11BCE865`, `1BDBD08B`, `99E4CF94`

## Verified state at close

`main` @ `3233030e` · 0 active / 0 queued shipments · worktree clean · single
worktree (P-016) · P-009 satisfied · P-018 gate SATISFIED with no force on #412.
