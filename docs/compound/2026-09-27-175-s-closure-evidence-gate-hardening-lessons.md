---
title: "175-S closure-evidence gate: textual containment before resolve, regular-entry discovery, and gate-timing wording for truthful negative closures"
problem_type: security-hardening
category: gate-implementation-learning
root_cause: "The first closure-evidence gate draft resolved the caller's --path before checking containment. On Windows that opens UNC/device paths, including an SMB connection that can leak NetNTLM, before rejecting them. It also treated symlinked docs/closure entries as discovery evidence and assumed Path.resolve() returns on-disk casing, which is false on APFS. The producer docs also required exit 0 before committing any closure artifact, which a truthful pending or BLOCKED record can never reach."
resolution_type: code+docs
severity: medium
component: "autoharness gate closure-evidence (src/autoharness/cli.py) / closure_contract.classify_closure_candidates / operational-closure skill / Ship agent"
related_pr: 458
related_shipment: 175-S
related_feature: 167-F
doc_type: learning
source: docs/compound/2026-09-27-175-s-closure-evidence-gate-hardening-lessons.md
tags:
  - closure-evidence
  - path-containment
  - windows
  - symlink
  - gate-timing
---

# 175-S Closure-Evidence Gate Hardening Lessons

## 1. Check containment textually before any filesystem call

`Path.resolve()` and `is_file()` touch the filesystem. On Windows, touching a
UNC path such as `\\host\share\x` opens an SMB session before any containment
check runs.

**Fix**: run a textual check first:
`os.path.commonpath` over `normcase(normpath(...))`, where a `ValueError`
means a different drive or anchor. Accept both the resolved workspace root and
the caller's own `os.path.abspath(workspace)` spelling. This keeps symlinked or
junctioned workspaces, `/var` vs `/private/var`, and 8.3 short names working.
Only after this check passes do you call resolve and the resolved-containment
check.

## 2. Discovery evidence comes from regular entries only

If a canonically named symlink in `docs/closure/` points to a file stored
elsewhere, `resolve()`-based set membership lets that file be "discovered"
under a different canonical name.

**Fix**: skip symlink candidates. Compare directory identity with
`os.path.samefile(parent, closure_dir)`; directories cannot be hard-linked, so
this is safe. Also compare the exact on-disk entry name.

## 3. The on-disk name comes from the directory listing, not from `resolve()`

APFS keeps the caller's casing in `resolve()`, while Windows returns the
on-disk casing. To get the true name, read `os.listdir(parent)`: use an exact
match if there is one, else a unique `casefold` match, else fail closed.

## 4. Gate-timing wording must allow truthful negative records

A gate that stops at its first failed check cannot certify "only failure".
Key the allowance to the reported `failed_check`:

* `frontmatter_predicate` is tolerated before finalization.
* It is also tolerated for a finalized `BLOCKED` or unmet-conditions record,
  which may be committed.
* Exit 0 is required only before closure is *declared complete*.

## 5. `is_dir()` hides real failures

`Path.is_dir()` returns `False` on permission errors and symlink loops, so a
broken directory looks like an absent one. Call `iterdir()` directly and
suppress only `FileNotFoundError`. The reader then maps other `OSError`s to
`BACKLOG_UNAVAILABLE`.

## 6. Operational pitfall: stale local `main` plus dirty checkpoint files

`git checkout main` from the feature branch aborted because the local `main`
ref predated the merge and lacked a modified checkpoint file. The next
`git checkout -b` then silently branched from the feature HEAD.

**Fix**: before switching, move session-owned checkpoint files aside. Then
`git checkout main` and `git pull`, verify `git log -1` shows the merge commit,
create the branch, and restore the files. Never use `git stash` while an
operator stash exists.
