---
title: "Compacted — PR #411 adversarial review substitution and merge"
date: 2026-08-26
source: docs/memory/compacted/2026-08-26-pr411-adversarial-review-merge-compacted.md
doc_type: memory
release_unit: "PR #411 (no shipment)"
compacted_from:
  - docs/archive/memory/2026-08-26-orchestrator-pr411-adversarial-review-merge.md
---

# Compacted — PR #411 adversarial review substitution and merge

Post-merge floor compaction for the release unit closed by PR **#411**
(merge commit `be97deb4`). The verbose original lives at
`docs/archive/memory/2026-08-26-orchestrator-pr411-adversarial-review-merge.md`.

## Outcome

Copilot's shadow reviewer stalled on PR #411 and could not resume. The operator
authorized an **independent adversarial review in its place**, with merge
authority conditional on everything checking out. Real P0/P1 findings came back,
so the merge precondition **initially failed**; all findings were verified,
remediated, and re-verified, then the PR merged as a true merge commit
(two parents — P-009 satisfied).

## Transferable learning — verify the reviewer, not just the code

The highest-leverage technique was a **fairness test** applied to every finding:
*is this a regression this PR introduces, or the repository's pre-existing
ambient state?* It materially reduced three findings, two of them headline:

| Claim | Verified reality |
|---|---|
| "25 of 26 decided-plans assert false status" | Joined all 32 plans against the backlog (957 items): **15 provably shipped**, 2 mixed, **9 already correct** |
| "73 new lint violations with invented `doc_type` values" | **40** genuine missing required fields; the other **33** are `unknown_doc_type` against a **closed vocabulary already stale relative to `main`** |
| "127 dangling references" | **14** on live surfaces; the rest were immutable append-only history, correctly excluded |

**A reviewer's severity and count are themselves claims requiring
verification.** Accepting them uncritically would have produced three wrong
fixes — including renaming `decided-plan`, which has 6 precedents on `main` and
is *prescribed by the compact-context skill itself*, so the "fix" would have
created the inconsistency it claimed to remove.

## Root causes (distinct per finding — not one shared cause)

* **Dangling references** — compaction flattened dated subdirectories
  (`docs/memory/<date>/x.md` → `docs/archive/memory/x.md`), which a naive
  `docs/X` → `docs/archive/X` substitution cannot express.
* **False delivery statuses** — status was asserted at compaction time without
  joining against the authoritative backlog.
* **Missing docline fields** — new summaries omitted the `source`/`title`
  fields the authoring profile requires.

## Self-review caught what external reviewers missed

Reviewing the *fix commits themselves* surfaced three dangling references in
stash entry `34D50F2D`. The fairness test showed `main=1, head=1` — they exist
identically on `origin/main` and this PR never touched those lines, so they were
prior-quarantine fallout on a different contract surface. Captured as
`99E4CF94` under **P-021 C1** (genuine ambiguity resolves OUT of scope) rather
than fixed in flight.

## Failed approaches

* **Re-engaging the stalled Copilot reviewer** — REST re-request plus the full
  §1.2 back-off (2/2/3/3/5 min) left its review pinned at an old HEAD while HEAD
  advanced, so the gate could not self-clear. Exit was the audited `--force`
  (precedent: PR #337, same verdict).

  **The deadlock is intermittent, not structural — do not generalize it.** This
  memory originally inferred that a post-review push never re-triggers review.
  PR #412 disproved that within the hour: it re-reviewed automatically after
  *two* successive post-review fix pushes (`a0d96d01`, then `2793c297`),
  clearing the gate each time with no force. An unreviewed HEAD is therefore
  **not** by itself evidence of a stall. Force only after observing a real stall
  across the full §1.2 back-off — treating the deadlock as the default would
  convert an audited exception into routine bypass of a fail-closed gate.
* **`--json` on `backlogit docs lint`** — suppresses output entirely and reads
  as a false "0 findings"; the bare command already emits JSON.
* **Default `subprocess` encoding on Windows** — `cp1252` raises
  `UnicodeDecodeError` on `git diff` output.

## Final verification (HEAD `10cc65b0`)

False plan status **0 remaining**; required-field lint gaps on new files
**0 remaining** (73 → 33 findings, all residual being the stale-vocabulary class
shared with `main`); dangling refs on live surfaces **0 remaining**; both
content-fidelity losses restored; CI green; **0** unresolved review threads.

## Follow-ups

`11BCE865`, `1BDBD08B`, `99E4CF94`.
