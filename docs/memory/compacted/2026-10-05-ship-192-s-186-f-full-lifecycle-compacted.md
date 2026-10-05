---
title: "Ship 192-S / 186-F full lifecycle and post-merge closure (compacted)"
description: "Compacted Tier-1 release-unit memory for 192-S / 186-F (ship lifecycle Unit A: P-002/P-004 per-task expected-RED roster and harness-architect per-task semantics). Covers the dark-mode execution (PR #494 merge bf43cc0b), the IM-14 harvest-commit audit, the local and Copilot review dispositions, and the CASCADE close through autoharness shipment cascade-close (P-020)."
doc_type: memory
source: docs/memory/compacted/2026-10-05-ship-192-s-186-f-full-lifecycle-compacted.md
date: 2026-10-05
agent: ship
session_id: ship-2026-10-05-192s-unit-a
compacted_from:
  - docs/archive/memory/2026-10-05-ship-192-s-186-f-closure-session.md
---

# Ship 192-S / 186-F Full Lifecycle and Post-Merge Closure (Compacted)

The verbose original is listed in `compacted_from`; it holds the full IM-14
harvest-commit audit table. Closure record:
`docs/closure/192-S-186-F-post-merge-closure.md`. Close evidence:
`docs/closure/evidence/192-S-186-F-close-evidence.json` and
`.backlogit/reconcile/192-S-cascade-close-20261005-081010.md`.

## Delivery

* A1 `ab4137c5`: P-002/P-004 scope RED to the current task's expected-RED
  roster. The roster excludes characterization tests and no-stub structural
  tests. RED is `ERROR` with the test's own `NotImplementedError` marker,
  attributed under R2. A marker-bearing `AssertionError` is refused.
  `harness-surface:none` is limited to tasks with no Python module under
  `src/`. The Marker Convention is verbatim. History row `1.32.0`.
* A2 plus review fixes `294c30ac`, delta P3s `7c051fe9`: the
  harness-architect works on exactly one caller-supplied task and never
  claims. Step 3 carves out characterization tests; Step 5.2 adds the roster
  rules with a roster-scoped refused list; Step 6 adds the per-task evidence
  record. Parallel hunks only; the installed file was not re-rendered (IM-10).
* IM-12 chains: policy `f8e2a2d1` -> `23077e1d` -> `54108e1d` -> `c8781195`;
  actor `39089629` -> `3fb73113` -> `2d549907`. Each refresh used the raw
  staged blob, and the pre-refresh value equaled `HEAD`.
* Suite: 3170 tests OK (skipped 54). CI green. P-018 `SATISFIED`
  (`required`). Merged with `--merge` as `bf43cc0b` under dark-mode
  pre-authorization; no admin fallback.

## Reviews

* Local review (8 personas, including an adversarial design pass): the P1s
  were a refused list not scoped to the roster, an empty-roster escape, and
  a missing `src/` limit on the actor exemption. All were fixed. The delta
  re-review found 0 P0 and 0 P1.
* Copilot round 1 raised 2 threads, both out of scope: the template Ship
  batch caller (`21CDBC0A`) and template portability under AGENTS.md Core
  Rule 2 (`EC980E56`). Both were declined with their IDs cited and resolved.

## Close

* Lifecycle gate exited 0. Pre-mode returned `PROCEED`. `--classify-only`
  exited 0 (`CASCADE`, `VERIFIED` `1.11.0` / cli). N = 4 and B = 410 s, so
  the default timeout applied.
* The mutating `cascade-close` exited 0; the child took about 196 s. It
  archived 4 IDs, `returned_ids` was empty, and postconditions passed. INV-12
  returned `DISPOSITION_COMPLETE` (empty set). Post-mode returned `PROCEED`.
* There was no `source_stash_id` or `source_deliberation_id`, so nothing was
  archived.

## Learnings

* The global `autoharness` 1.5.0 lacks `shipment`. Use
  `.venv\Scripts\autoharness.exe` for `cascade-close` and `closure-evidence`.
* `READY_WITH_CONDITIONS` needs every `conditions` entry to have
  `satisfied: true` plus evidence. Record a forward release hold as a
  satisfied "recorded and tracked" condition, and let stash entries carry it.
* AGENTS.md Core Rule 2 conflicts with plan wording that writes
  runner-specific RED vocabulary into product templates. Resolving it needs
  deliberation (`EC980E56`).

## Follow-Ups

`EC980E56` (high), `21CDBC0A` (high), `E0136957` (medium), `8BE38096` (low),
`4D600C75` (low), and `808BAB5E` (medium: plan D3 preflight FI-12 blob
drift). The pre-existing MD001 is tracked by `24BA1B8F`.
