---
title: "Chore worktree carry-forward / PR #502 (compacted)"
date: 2026-10-07
doc_type: memory
pr: 502
---

# Chore worktree carry-forward: PR #502 (compacted)

**Outcome.** The P-011 backlog-state carry-forward and the `pipeline-topology`
`pre_claim` `worktree_cleanliness` check shipped in PR #502, merged as
`40b9ca9f` with `--merge` (parents `698590f8` + `79c17ad0`). No shipment was
claimed; this was a standalone chore branch. The check reports
`WORKTREE_CLEAN` / `CARRY_FORWARD_ELIGIBLE` (pass) and `WORKTREE_DIRTY` /
`WORKTREE_STATUS_UNAVAILABLE` (block). It runs after `worktree_uniqueness`,
before `shipment_readiness`, in `pre_claim` only, and is a visible `skipped`
result for readers without the capability. `.gitattributes` gained
`.backlogit/** text eol=lf`; `docs/pipeline-topology-gate.md` documents the
check.

## Decisions

* **Gate, not git stash.** The gate never runs `git stash` or
  `update-index --refresh`; it reads `git diff --name-only -z` (worktree and
  index, no renames) and `git ls-files --others -z`, refuses a
  workspace that is not the repository top level, and fails closed on git
  timeout, OS, or decode errors.
* **Carry-forward is reclassified before staging.** Ship and P-011 stage and
  commit only the exact Stage-written backlog paths (pathspec commit with
  `--literal-pathspecs`) and verify with `git show -z --name-only HEAD`.
* **Divergent staged content blocks.** Round 4 added
  `worktree_divergent_paths()` (index ∩ (unstaged ∪ untracked)); a match is
  `WORKTREE_DIRTY` with `details.divergent_paths`.
* **Scope.** The operator-authored `.gitmodules` commit `3ac3f75e` (toon
  submodule) landed on the branch; the PR body recorded the scope expansion.

## Evidence

* Local review: six personas, 0 P0; all P1/P2 fixed in `73926ce9`.
* Copilot rounds 1–4 fixed in `61f513e3`, `99f4f1a4`, `18fb41a4`,
  `79c17ad0`; every thread replied to and resolved. P-018 gate `SATISFIED` at
  `79c17ad0`; CI green; pre-push hook full suite 3425 OK.

## Learnings

* Copilot desktop prewarm worktrees under `.worktrees/` trip P-016
  (`MULTIPLE_IMPLEMENTATION_WORKTREES`) and fail two pre-push tests; the
  operator must remove them, agents must not.
* `git push --delete` runs the full pre-push hook; delete a remote branch
  through `gh api -X DELETE repos/{owner}/{repo}/git/refs/heads/{branch}`.
* Git output without `-z` C-quotes non-ASCII and special paths; use `-z` for
  any path that is later fed back to git.

## Follow-ups

`BB0D15AB` (upstream backlogit no-op rewrite), `E547CB70` (deferred scope
expansion: catalog references for backlog-md; its provenance was narrowed
with `stash edit`, which is Stage-only under P-021 C5 — `stash correct` was
the right operation), and the legacy `docs/memory` backlog over the P-020
thresholds (104 files, 937 KB), captured at this closure as `3A3C72D0`.
