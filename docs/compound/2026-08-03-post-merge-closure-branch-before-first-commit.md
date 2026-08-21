---
title: Post-merge closure branch must exist before the first archival commit
date: 2026-08-03
tags: [ship, post-merge-closure, backlog, P-014]
source: docs/compound/2026-08-03-post-merge-closure-branch-before-first-commit.md
doc_type: learning
---

# Post-merge closure branch must exist before the first archival commit

## Problem

During `111-S` / `085-F` post-merge closure, the shipment-archival mutation
(`backlogit archive 111-S`) was run and committed while local `main` was
still checked out — immediately after `git pull` fast-forwarded it to the
merge commit, but **before** `git checkout -b post-merge/{slug}` was run.
This landed a `chore: archive ...` commit directly on `main`, violating the
Post-Merge Branch Protocol (closure commits must never land on `main`
directly).

## Root cause

The Post-Merge Closure sequence in the Ship instructions lists "sync clean
local main" before the backlog reconciliation steps, but the branch-creation
step is documented separately under "Post-Merge Branch Protocol." It is easy
to read the two sections as sequential-but-independent and start archival
work right after `git pull`, skipping the intermediate `git checkout -b
post-merge/{slug}` step.

## Fix / detection

Caught immediately via `git log --oneline` review before pushing anything.
Recovery was cheap only because the bad commit had not yet been pushed:

```powershell
git rev-list origin/main..main --count   # confirm nothing pushed yet
git reset --hard <merge-commit-sha>      # drop the bad commit, restore working tree
git checkout -b post-merge/{slug}        # create closure branch NOW
# redo the archival work on the closure branch
```

Note: `git reset --hard` to the merge commit also physically reverted the
`backlogit archive` file-move side effect (the queue file was restored),
which is expected and safe to redo on the closure branch.

## Preventive rule for future Ship sessions

**Never run any `.backlogit/` mutation (archive/move) or any other
closure-work file edit between `git pull` (syncing local `main`) and `git
checkout -b post-merge/{slug}`.** Treat branch creation as blocking the
start of any closure work, not merely a step documented nearby. A one-line
self-check before the first closure-related mutation: `git branch
--show-current` must already read `post-merge/...`, never `main`.
