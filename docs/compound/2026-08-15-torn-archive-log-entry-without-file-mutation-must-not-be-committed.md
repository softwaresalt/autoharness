---
title: "A logged \"archived\" event without a corresponding file mutation is torn state — never commit it into a closure"
source: docs/compound/2026-08-15-torn-archive-log-entry-without-file-mutation-must-not-be-committed.md
doc_type: learning
---

# A logged "archived" event without a corresponding file mutation is torn state — never commit it into a closure

**Date**: 2026-08-15
**Context**: Post-merge closure of shipment `135-S` / feature `126-F`
(adopt the backlogit `.backlog` storage root).

## Finding

While inspecting the dirty worktree left behind by the (already-completed)
`135-S` safe-close/cascade-archive operation, an **untracked**
`.backlogit/logs/018-DL.jsonl` was found containing two events for
deliberation record `018-DL` (referenced by `126-F`'s body as "Deliberation:
018-DL", but **not** a member of `135-S`'s manifest `items` list):

```json
{"event_type":"commit_tracked","delta":{"commit_sha":"9851cc3d..."}}
{"event_type":"archived","delta":{"archive_path":".backlogit/archive/018-DL.md"}}
```

The log claims `018-DL` was archived. But:

- `.backlogit/archive/018-DL.md` does **not** exist.
- `.backlogit/queue/018-DL.md` is unchanged (`status: queued`), byte-identical
  to the last committed version — `git status` shows no diff for it.

The log entries describe a mutation that never actually happened to the
artifact file. This is **torn state**: a JSONL log write succeeded (or was
attempted) while the corresponding file move/frontmatter update did not.

## Why this matters

A closure workflow that trusts logs at face value (e.g. "the log says X was
archived, so let's include/reconcile X") can launder an out-of-scope,
never-actually-applied mutation into git history — creating a permanent,
misleading provenance record for an artifact untouched by the actual
shipment. `018-DL` is also outside `135-S`'s manifest, so even a *completed*
archive of it here would have been a protected-set/cascade violation under
the shipment-reconcile safe-close contract.

## Rule

Before including any backlog log file in a shipment closure commit:

1. Cross-check every claimed mutation in the log against the **actual current
   file state** (existence, path, frontmatter fields) — never trust the log
   text alone as proof a mutation completed.
2. If a log claims an event for an artifact **not in the shipment's own
   manifest**, exclude it regardless of whether the underlying mutation
   completed — manifest scope is the boundary, not "did something happen to
   it."
3. If a log claims a mutation that did **not** actually complete on disk,
   do not commit that log file as part of the closure; leave it untracked
   and record the anomaly as an explicit follow-up rather than silently
   discarding or "fixing" it (fixing a deliberation-record artifact's state
   is Stage's domain, not Ship's, per role boundary — triage/deliberate
   fields are out of scope for Ship).

## Generalizes to

Any workflow (not just shipment-reconcile) that reconciles/verifies backlog
or telemetry state from append-only log files: an append succeeding does not
prove the paired file-system mutation it describes also succeeded. Verify
both independently.
