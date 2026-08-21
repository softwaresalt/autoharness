---
title: "git stash/pop mid-shipment can desync backlogit's on-disk .md status from its authoritative internal state"
description: "A git stash/pop cycle performed mid-shipment while backlogit .backlogit/queue/*.md bookkeeping files sit uncommitted can revert those files to their pre-mutation state even though backlogit's own internal state (and the CLI's claim/move conflict checks) still reflects the correct, later status."
problem_type: "tool-state-desync"
category: "workflow-issues"
component: "backlogit-cli"
root_cause: "git stash/pop operates purely on the git working tree and index; it has no awareness of backlogit's own internal state tracking. When uncommitted .backlogit/queue/*.md mutations (shipment claim, task move-to-done) are stashed and later popped, the round-trip itself was verified to correctly restore file contents, but a subsequent backlogit CLI mutation call issued afterward observed and/or persisted the pre-mutation (reverted) status for four task files, producing a file-vs-internal-state disagreement that the CLI's own claim command surfaced as a status conflict."
resolution_type: "workaround"
severity: "medium"
message: "shipment status conflict / LIFECYCLE_NO_ACTIVE_SHIPMENT"
file_path: ".backlogit/queue/145-S.md"
citations:
  - "PR #384"
  - "PR #385"
  - "docs/closure/145-S-137-F-post-merge-closure.md"
date: 2026-08-21
shipment: 145-S
feature: 137-F
tags:
    - backlogit
    - git
    - bookkeeping
    - process
source: docs/compound/2026-08-21-backlogit-shipment-status-file-desync-after-git-stash.md
doc_type: learning
---

# git stash/pop mid-shipment can desync backlogit's on-disk status

## Finding

During shipment `145-S`, a `git stash` / `git stash pop` cycle was used to
isolate whether a set of full-suite test failures was pre-existing (they
were -- the known `E8158860` test-isolation-pollution finding). The stash
included uncommitted `.backlogit/queue/*.md` mutations for the active
shipment and its already-completed tasks (backlogit rewrites these files
in place on every `move`/`claim`, and Ship's per-task commits intentionally
do not stage `.backlogit/` bookkeeping files alongside deliverables).

After the stash/pop round-trip, and one subsequent `backlogit move <task>
--status done` call for an unrelated task, the on-disk
`.backlogit/queue/145-S.md` file and all four `.backlogit/queue/137.00{1..4}-T.md`
files had reverted to their **pre-claim** state (`status: queued`), even
though:

* the shipment's actual deliverables (source, templates, tests, docs) were
  already correctly committed to git across four separate task commits, and
* `backlogit`'s own claim command refused to re-claim the shipment
  (`move shipment 145-S from active to active: backlogit: shipment status
  conflict`), proving its **internal** state (not reflected in the reverted
  file) still correctly considered the shipment `active`.

This is a **file/internal-state desync**, not a real competing claim or a
genuine "queued record with active work underneath it" (the Step 0.5 item
1a scenario). The desync was invisible to normal `backlogit get`/`shipment
get` reads for the SHIPMENT (which reported the correct `active` status,
apparently from internal state) but was reflected exactly in the raw
`.backlogit/queue/*.md` files that `git` tracks and that the
filesystem-based `pipeline-topology` gate reads directly. For the four
TASKS, however, `backlogit get` reported the reverted (`queued`) status,
matching the file -- suggesting task-level reads are more file-driven than
shipment-level reads, or that the specific sequence of stash/pop plus a
subsequent `move` command amplified the desync differently at each
artifact level. The exact internal mechanism was not root-caused.

## Detection signal

The Step 4 `pipeline-topology --phase lifecycle` gate (which reads
`.backlogit/queue/*.md` directly via `FilesystemTopologyReadersTests`-style
readers) reported `LIFECYCLE_NO_ACTIVE_SHIPMENT: expected exactly one active
shipment` with an empty `active_shipment_ids` list, despite the shipment
having been claimed and worked on for the entire session. Attempting to
re-claim via `backlogit shipment claim <id>` surfaced the `active to active:
shipment status conflict` error, which is the decisive signal that the
desync is file-only, not a real inconsistency requiring the Step 0.5 item
1a `SHIPMENT_STATE_INCONSISTENT` halt-and-report path.

## Repair procedure (verified effective)

1. Do not treat the topology gate's `LIFECYCLE_NO_ACTIVE_SHIPMENT` as
   automatically fatal; first attempt `backlogit shipment claim <id>` (or
   `backlogit move <task> --status active`) to probe whether the CLI's own
   internal state disagrees with the file.
2. If the CLI refuses with a `status conflict` error (i.e. it believes the
   target status is already reached), the file is the stale side. For a
   shipment, directly correct the `status:` field in the tracked `.md` file
   to match the value the conflict error implies, then run `backlogit
   sync`.
3. For tasks that show the same file/CLI disagreement (where the CLI
   itself also reports the reverted status, not just the file), re-run the
   full `queued -> active -> done` transition sequence through the normal
   CLI commands rather than hand-editing task files -- this is safe because
   `move --status done` correctly re-archives the file with the right
   `status: done` and preserves `parent_id`, commit-tracking metadata, and
   sizing fields, none of which hand-editing would reconstruct.
4. After repair, re-run the `pipeline-topology --phase lifecycle` gate and
   confirm `exit_code: 0` before proceeding to any further gated step.
5. Commit the bookkeeping repair as its own commit, separate from any
   deliverable commit, so the repair is auditable and does not get
   conflated with task-scope work.

## Process guidance

* **Do NOT use a separate `git worktree` as a workaround for this.** Ship
  operates under a strict single-worktree constraint (P-016;
  `templates/policies/workflow-policies.md.tmpl` -- an extra worktree during
  an in-progress Ship shipment is permitted only for Stage-owned
  spike/research work and is explicitly forbidden for Ship execution).
  Recommending a worktree-based baseline here would trip the
  `pipeline-topology` worktree-uniqueness check for any Ship agent following
  this learning literally. Retain a single-worktree method instead: prefer
  running the suspected-pre-existing tests against a `git show
  <ref>:<path>` snapshot (e.g. `git show main:tests/some_test.py` piped to a
  temporary file, or `git worktree`-free `git diff`/`git log -p` inspection)
  rather than `git stash`, when the working tree contains uncommitted
  backlogit bookkeeping mutations for an in-progress shipment. `git
  stash`/`pop` is safe for ordinary source edits but interacts poorly with
  backlogit's live, frequently-rewritten `.backlogit/queue/` and
  `.backlogit/archive/` files sitting alongside a long-running session's
  uncommitted bookkeeping state.
* If `git stash` is unavoidable mid-shipment, re-verify shipment AND task
  status (`backlogit get`/`shipment get` for every manifest member) via the
  Step 0.5 item 1a style check immediately after `git stash pop`, before any
  further task-loop or lifecycle-gate work, rather than assuming the pop
  fully restored intended state.

## Related

* `docs/closure/145-S-137-F-post-merge-closure.md` -- the shipment where
  this was found and repaired.
* `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md` --
  the related, distinct finding about backlogit 1.8.0's shipment status
  enum not including `blocked`.
* `docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`
  -- a different backlogit 1.10.0 behavior finding from the immediately
  preceding shipment (`144-S`).
