---
title: "Safe-Close step 4: engine archives an archive/-resident done record (probe)"
date: 2026-10-16
problem_type: workflow
category: closure
root_cause: assumption-drift
tags: [safe-close, shipment-reconcile, probe, backlogit, 206-F, D16452D7]
source: docs/compound/2026-10-16-safe-close-archive-resident-done-probe.md
doc_type: learning
---

# Safe-Close step 4: engine archives an archive/-resident done record (probe)

## Problem

Safe-Close step 4 skipped any manifest item whose file sat in `archive/`, keying on location instead of declared `status`. A record in `archive/` that still declares `done` (or `active`) was never archived. Making step 4 status-keyed assumes the engine will archive such a record. 206.001-T required proving that first.

## Probe (2026-10-16, backlogit 1.11.0, scratch root `.proof-scratch/probe`, git-ignored, removed afterwards)

1. `backlogit init`, then `backlogit add --type feature` created 002-F in `queue/` as `queued`.
2. `move 002-F --status active`, then `move 002-F --status done`. The terminal move relocated the record to `archive/002-F.md` with `status: done`. A direct `queued` to `done` move is refused as an invalid transition.
3. `backlogit archive 002-F` exited 0 on that `archive/`-resident `done` record. Frontmatter became `status: archived`, `archived_status: done`.
4. A second `backlogit archive 002-F` on the already-archived record also exited 0.

## Result

The engine accepts an explicit single-artifact archive of an `archive/`-resident `done` record. No halt is needed for the normal path. The skill keeps a fail-closed rule: if the engine refuses, HALT for operator review and never skip.

## Learnings

* Location (`queue/` or `archive/`) is a label. Declared `status` decides the step 4 action.
* A record declaring `archived` is `pre-archived` and skipped. Any other declared status is moved to `done` if needed, then archived explicitly.
