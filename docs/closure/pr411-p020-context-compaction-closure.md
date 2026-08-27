---
title: "PR #411 post-merge closure — P-020 context compaction"
merged_pr: 411
shipment: none
shipment_claimed: false
merge_commit: be97deb4993ba1ffda999c67e5149db4537f0fc0
merged_at: "2026-08-27T00:54:23Z"
reviewed_head: 10cc65b030e1c11508abb58689393bf2708733a9
merge_strategy: merge-commit
admin_fallback_used: false
copilot_review_forced: true
closure_status: READY
compaction_status: done
terminal_closure: true
source: docs/closure/pr411-p020-context-compaction-closure.md
doc_type: closure
follow_ups:
  - 11BCE865: "10 docs/ files have silently truncated frontmatter (pre-existing; unquoted scalar containing space-hash truncates with no parse error)"
  - 1BDBD08B: "circuit-breaker checkpoint frontmatter template gap"
  - 99E4CF94: "three dangling refs in stash entry 34D50F2D left by the earlier deprecated-supervisor-design quarantine"
---

# PR #411 Post-Merge Closure — P-020 context compaction

PR **#411** merged to `main` as merge commit `be97deb4` (two parents —
P-009 merge-commit-only satisfied).

**No backlog shipment or feature covers this PR.** No shipment was claimed,
created, mutated, or shipped for this closure. At merge time the backlog held
**0 active** and **0 queued** shipments.

## Review disposition — operator-directed review substitution

The Copilot shadow reviewer stalled and could not resume. The operator
explicitly authorized an independent adversarial review in its place, with
merge authority conditional on everything checking out.

Two independent hostile reviewers plus a separate non-overlapping pass produced
P0/P1 findings, so the merge precondition initially **failed**. Every finding
was then verified against evidence and fairness-tested (regression introduced by
*this* PR, versus the repository's pre-existing ambient state). Three findings
proved materially over-called; the genuine defects were remediated in four
commits and independently re-verified before merge.

| Finding | Disposition |
|---|---|
| Decided-plans assert false delivery status | 17 corrected against the authoritative backlog (957 items); 9 left unchanged because their status was already correct. **0 remaining.** |
| Missing required docline fields | 40 genuine gaps fixed. **0 required-rule gaps** remain on new files. The residual 33 are `unknown_doc_type` against a closed vocabulary already stale relative to `main`. |
| Dangling references to relocated artifacts | 14 repointed. **0 remaining on live surfaces**; the 413 residual occurrences are immutable append-only history that must not be rewritten. |
| Dropped operator-decisions block | Restored from the archived original. |
| Missing deprecation marker on a superseded design | Marker added. |
| Overstated "moved verbatim" claim | Corrected — 44 of 80 archived files are pure renames; 36 carry this PR's own archive-path link repointing. |

## Gate outcomes

| Gate | Result |
|---|---|
| Local review readiness (§1.9 Checks 1–4) | **PASS** for reviewed HEAD `10cc65b0` |
| Full local build | **PASS** — `pytest tests/` 1881 passed / 20 skipped / 1422 subtests; `markdownlint "**/*.md"` exit 0; pre-push hook (1901 tests) all gates passed |
| CI | **PASS** — `ci gate`, `test`, `detect code changes`, `pipeline-topology (ambient)` |
| Unresolved review threads | **0** |
| P-009 merge-commit-only | **PASS** — merge commit has two parents |
| P-018 copilot-review (Check 5) | **FORCED** — `WAITING_FOR_REVIEW` deadlock; audited `--force` recorded in `.autoharness/gates/copilot-review-force-audit.log` (precedent: PR #337, same verdict) |

## P-020 compaction

`compact-context` was invoked at closure as required, and the **post-merge floor
consolidation was performed**.

**Candidate (completed-work rule, Phase 2).** The just-closed release unit's
session memory —
`docs/memory/2026-08-26-orchestrator-pr411-adversarial-review-merge.md` —
qualifies as completed feature/chore memory. That rule is **independent of the
14-day age threshold**, so this candidate is eligible despite being fresh.

**Action taken (Phase 3, bounded Tier-1 consolidation):**

* Dense summary written to
  `docs/memory/compacted/2026-08-26-pr411-adversarial-review-merge-compacted.md`
* Verbose original archived to
  `docs/archive/memory/2026-08-26-orchestrator-pr411-adversarial-review-merge.md`
* Traceable path preserved in both directions via the summary's
  `compacted_from` field

**Directory assessment after consolidation:**

| Directory | Files | Size | Further candidates |
|---|---|---|---|
| `docs/memory` | 91 (50 of them compacted summaries, preserved by rule) | 725 KB | 0 |
| `docs/plans` | 65 | 642 KB | 0 |
| `docs/closure` | 32 | 405 KB | 0 |
| `docs/compound` | 76 | 427 KB | 0 |

Beyond the completed-work candidate above, **no further file qualifies**. PR
#411 was itself the historical compaction and consumed the entire pre-2026-08-10
backlog in one pass, so every remaining non-compacted memory file dates from
2026-08-18 or later, inside the 14-day threshold. `docs/memory` and `docs/plans`
remain above the raw file-count and size triggers only because the compacted
summaries and recent working memory both live there; compacting recent working
memory would be premature.

## Residual risk

* `docs/memory` and `docs/plans` remain above the raw `max_files` / `max_size_kb`
  triggers. This is expected immediately after a large compaction and will
  resolve naturally as the recent files age past the threshold. Re-assess at the
  next post-merge closure.
* The docline closed vocabulary rejects four `doc_type` values already in
  established use across `main` (`audit`, `deliberation`, `plan-hardening`,
  `plan-review`) plus `decided-plan`, which the compact-context skill itself
  prescribes. 41 repo-wide `unknown_doc_type` findings stem from this. Widening
  the vocabulary is the correct fix; renaming the documents is not.
