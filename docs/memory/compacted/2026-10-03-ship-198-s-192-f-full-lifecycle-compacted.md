---
title: "Ship 198-S / 192-F post-merge closure (compacted)"
description: "Compacted Tier-1 release-unit memory for 198-S / 192-F (cascade-close evidence capture). Covers the halted first closure, the timeout-cap remediation (PRs #483-#485), and the successful resumed CASCADE close through autoharness shipment cascade-close (P-020)."
doc_type: memory
source: docs/memory/compacted/2026-10-03-ship-198-s-192-f-full-lifecycle-compacted.md
date: 2026-10-03
agent: ship
session_id: ship-2026-10-03-198s-closure
compacted_from:
  - docs/archive/memory/2026-10-02-ship-198-s-192-f-closure-halt.md
  - docs/archive/memory/2026-10-03-ship-198-s-192-f-closure-session.md
---

# Ship 198-S / 192-F Post-Merge Closure (Compacted)

The verbose originals are listed in `compacted_from`. Closure record:
`docs/closure/198-S-192-F-post-merge-closure.md`. Close evidence:
`docs/closure/evidence/198-S-192-F-close-evidence.json` and
`.backlogit/reconcile/198-S-cascade-close-20261003-080830.md`.

## Delivery

* PR #482 merged as `eb8b7811`. It delivered the `cascade-close` command
  (`192.001-T` .. `192.022-T`).
* The first closure halted before mutation. The predicted runtime of about
  973–1020 s exceeded the 900 s `--timeout` cap. PR #483 recorded the halt
  and stash `F50BD40F`.
* Operator Option 1: Stage added `192.023-T` .. `192.026-T` (PR #484). PR
  #485 merged as `829ab5e1`, setting `--timeout` to 30–3600 s with a 1800 s
  default and a `--timeout + 600 s` supervision budget.

## Close

* Pre-mode returned `PROCEED` for 27 items.
  `--classify-only --replace-pre-close` exited 0 (`CASCADE`, `VERIFIED`
  `1.11.0` / cli).
* Sizing: N = 28 and B = 1670 s, so the default timeout was used.
* The mutating `cascade-close` exited 0 after 1006 s (child about 985 s). It
  archived 28 IDs, `returned_ids` was `[]`, and postconditions passed. This
  was the first live end-to-end run of the command.
* INV-12: `035-DL` and `038-DL` were `retained_shared_reference`, giving
  `DISPOSITION_COMPLETE`. Post-mode returned `PROCEED`.
* Source cleanup: `008F3BCF` was already archived. The `035-DL` outcome was
  copied from the report.
* `backlogit sync` reported `Indexed 1696 artifacts`
  (`CLOSURE_INDEX_SYNC_OK`).

## Learnings

* The duration model (133 s + 35 s per artifact, with a 1.5× margin) is
  safe. The 28-artifact actual (985 s) came in below the unmargined
  prediction (1113 s).
* Run long closures attached and async, and poll with long delays. Do not
  change the stash between classify-only and the mutating run.
* The queue lock token can be persisted across processes. Releasing after
  the target moves to the archive only prints a warning.

## Follow-Ups

`A5FA81C4` (new: the effective `--timeout` is not recorded in the evidence
record), `E01BA307`, `320499CC`, `8C88A1DB`, and `9869AA32`.
