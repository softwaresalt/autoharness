---
title: "cascade-close --detach ended never_started twice under heavy host load; the attached mode with --caller-wait closed the shipment (observed in 216-S)"
problem_type: tooling-pitfall
category: workflow
root_cause: "On a Windows host under heavy antivirus I/O (Defender real-time scanning) the detached supervisor of `autoharness shipment cascade-close` stalled about 40 s between signalling ready and its spawn gate. The foreground writes `authorize.json` with a 30 s validity (AUTHORIZE_VALIDITY_SECONDS), so the supervisor found the authorization expired, refused to spawn, and wrote a `never_started` outcome (exit 2 from `--poll`). Nothing was mutated and the evidence record rolled back to `pre_close`. Both detached attempts failed identically; the attached mutating run (with `--caller-wait` at least `--timeout` + 600 s) has no authorization handshake and succeeded."
tags: [cascade-close, never-started, authorize-window, detach, poll, host-load, ship, shipment-reconcile]
shipment: 216-S
date: 2026-10-19
source: docs/compound/2026-10-19-cascade-close-never-started-under-host-load.md
doc_type: learning
---

## What was observed

Closing 216-S (N = 25 artifacts, `--timeout 2888`):

* `--classify-only` exit 0 (CASCADE, engine VERIFIED); the evidence record was `pre_close`.
* `--detach` returned exit 9 (started), but `--poll` returned exit 2 with the failure `the supervised run ended: never_started`. The journal (`.autoharness/gates/cascade-close/<shipment>-<feature>.journal/`) showed `exit.json` state `never_started`, `outcome.json` detail "the child was not spawned (no descendant group, stream, or authorization); nothing ran", and `authorize.json` written at T+4 s with `valid_until` at T+34 s while the supervisor's outcome was written at T+45 s.
* `--recover --dry-run` reported exit 2 "no invoking evidence record to recover (the record is pre_close)": the failed run left the record at `pre_close`, so no recovery was applicable.
* A second `--detach` attempt failed the same way.
* The mutating command run attached (`--caller-wait 3488`, async shell) started the child immediately and closed the shipment: exit 0, `phase_written: post_close`, postcondition `pass`.

## Routing used

`--poll` exit 2 is not a documented final result for a detached run; the table says `either 2, 4 -> HALT, nothing was mutated`. The evidence was unambiguous (journal `never_started` proof, `pre_close` record, clean `git status` of `.backlogit/`), so after one detached retry the run used the documented attached run mode. No `--recover` was needed and no lock was removed. If the same failure recurs in a shipment with real mutation risk, treat it as a harness error: write a checkpoint and report to the operator.

## Calibration notes (follow-up, not fixed here)

* The attached run took 2814 s for N = 25 (about 112 s per artifact), only 74 s inside `B = ceil(1.5 x (800 + 45 x 25)) = 2888`. The reference per-artifact cost P = 45 s under-covers this host while the antivirus is busy; recompute F and P from recent evidence and add margin, or a timeout expiry would kill the engine mid-cascade (exit 6, indeterminate).
* The 30 s authorization validity and 60 s window are too tight for a loaded host; captured as a closure follow-up stash entry.
