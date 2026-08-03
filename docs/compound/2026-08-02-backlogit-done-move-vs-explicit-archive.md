---
problem_type: backlogit_done_move_vs_explicit_archive
category: backlogit
root_cause: "backlogit move <id> --status done relocates the artifact file from .backlogit/queue/ into .backlogit/archive/ as a side effect of this backlogit version's file layout (terminal-status items are stored under archive/ regardless of whether the explicit archive command has run), but it does NOT set status:\"archived\" or the archived_status/archived_from metadata fields. Only the explicit `backlogit archive <id>` command does that."
tags: [backlogit, archive, safe-close, P-007, P-015]
shipment: 110-S
date: 2026-08-02
---

# backlogit: `move --status done` Is Not `archive`

## Problem

During post-merge safe-close of a shipment, it is easy to assume that once a
task/feature/shipment record shows `status: done` and its file already lives
under `.backlogit/archive/` (both true immediately after
`backlogit move <id> --status done` during the task loop), the artifact is
already "archived" in the P-007 archive-integrity sense and the explicit
archive step can be skipped.

This is incorrect. `109-S`'s post-merge closure (see
`docs/closure/109-S-105-F-post-merge-closure.md`) discovered — via the
closure PR's own Copilot review — that three artifacts had only ever been
`move --status done`'d and never explicitly archived, so none carried
`archived_status`/`archived_from` metadata or the terminal
`status: archived` value.

## Root Cause

This backlogit version physically relocates a `done`-status artifact's file
into `.backlogit/archive/` as a side effect of `move --status done` — this is
purely a file-layout choice, not a semantic "this item is archived" marker.
The artifact's own `status` field remains `done` after this move. Only
running `backlogit archive <id>` explicitly:

1. sets `status: archived`,
2. records `archived_status: <previous status, e.g. done/active>`, and
3. records `archived_from: <original queue path>`.

Running `backlogit archive <id>` on a file that already physically resides
in `archive/` (because of a prior `move --status done`) is **not a no-op** —
it performs this real metadata transition and must still be run.

## Fix / Convention

During the Step 5 Closure Tasks single-artifact safe-close, always run the
explicit `backlogit archive <id>` command for **every** manifest task, the
shipment record, and the covering feature (once its children are confirmed
all archived) — never treat "file already under `.backlogit/archive/`" as
evidence that the explicit archive step already happened. Verify by
inspecting the artifact's `status` field: `done` (even if the file path is
already `archive/...`) means the explicit archive step is still outstanding;
`archived` (with `archived_status`/`archived_from` present) means it is
complete.

```powershell
backlogit get <id>   # check: status: archived (not done) + archived_status/archived_from present
```

This was correctly applied proactively during `110-S`'s closure (all 9
manifest tasks + the shipment + the covering feature were explicitly
archived one at a time, each verified to still carry the protected-set
invariant — see `docs/closure/110-S-106-F-post-merge-closure.md`).

## Second occurrence (111-S / 085-F)

The gap recurred during `111-S`'s closure: the 8 manifest tasks had already
been physically relocated to `.backlogit/archive/` by the feature branch's
own task-loop commits (via `move --status done`), and this was
misread as "already archived" (the pre-archived-item skip rule was
misapplied — that rule is for items already carrying `status: archived`,
not merely items whose *file* lives under `archive/`). The same
misclassification then repeated for the covering feature `085-F`
(archived via `move --status done` only). A Copilot review thread on the
`111-S` post-merge closure PR caught the task-level gap; the symmetric
feature-level gap was found proactively in the same fix pass. See
`docs/closure/111-S-085-F-post-merge-closure.md`.

**This compound-doc reminder alone was insufficient to prevent recurrence.**
Recorded follow-up: add an explicit pre-flight status check as a hard step
in the Step 5 Closure Tasks safe-close procedure — for every candidate
"pre-archived" item, run `backlogit get <id>` (or read the file's `status`
field) and treat `status: done` (even under `archive/` on disk) as **not
archived**; only `status: archived` with `archived_status`/`archived_from`
present may be skipped. Do not infer archived-ness from file location.
