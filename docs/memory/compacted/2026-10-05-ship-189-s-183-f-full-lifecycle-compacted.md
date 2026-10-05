---
title: "Ship 189-S / 183-F full lifecycle and post-merge closure (compacted)"
description: "Compacted Tier-1 release-unit memory for 189-S / 183-F (Graphtor MCP shim test synchronization repair). Covers the backlog-only lifecycle closure of already-merged test work (PR #492 merge) and the CASCADE close through autoharness shipment cascade-close (P-020)."
doc_type: memory
source: docs/memory/compacted/2026-10-05-ship-189-s-183-f-full-lifecycle-compacted.md
date: 2026-10-05
agent: ship
session_id: ship-2026-10-05-189s-lifecycle-closure
compacted_from:
  - docs/archive/memory/2026-10-05-ship-189-s-183-f-closure-session.md
---

# Ship 189-S / 183-F Full Lifecycle and Post-Merge Closure (Compacted)

The verbose original is listed in `compacted_from`. Closure record:
`docs/closure/189-S-183-F-post-merge-closure.md`. Close evidence:
`docs/closure/evidence/189-S-183-F-close-evidence.json` and
`.backlogit/reconcile/189-S-cascade-close-20261005-033820.md`.

## Delivery

* The implementation `622a41a1` (deterministic child-stdin-close sync in
  the graphtor-mcp-shim stdin write-error test; test-only) was already on
  `main` through PR #457 (`e38ac305`).
* PR #492 (backlog-only) claimed 189-S, linked `622a41a1` to 183.001-T, and
  moved 183.001-T and 183-F to `done`. It merged as `a28fb797` with reviewed
  HEAD `4e8ad8bb`.
* Re-verification on `c23c8bd3`: the targeted test passed and 10 repeats
  were 10/10. Pre-push suite: 3143 OK (skipped 54).

## Close

* The lifecycle gate exited 0. Pre-mode returned `PROCEED` for 2 items.
  `--classify-only` exited 0 (`CASCADE`, `VERIFIED` `1.11.0` / cli).
* Sizing: N = 3 and B = 357 s, so the default timeout was used.
* The Orchestrator's mutating `cascade-close` exited 0; the child took
  about 156 s. It archived 3 IDs and postconditions passed. The whole-tree
  check covered 1896 files and found only 4 changes, all in closure scope.
* INV-12 returned `DISPOSITION_COMPLETE` (empty set). Post-mode returned
  `PROCEED`. The lock was released.
* Source cleanup: there was no `source_stash_id` or
  `source_deliberation_id`. The description-only sources `24A85BF8` and
  `AD3D41FA` were already archived at harvest (2026-09-20), so nothing was
  archived.

## Learnings

* For 3 artifacts the cascade child took about 156 s against a 238 s
  unmargined prediction, so the fixed cost is lower for small closures.
* The lock token is reusable by a later process (release requires it), but
  shell and environment bindings do not persist between tool calls. Carry
  the token in memory or in conversation, bind it again for release, and
  never write it to a file.
* `.backlogit/stash.jsonl` (active) and `.backlogit/archive/stash.jsonl`
  (archived) share a file name. Check the full path before treating a stash
  entry as active.
* The backlogit CLI has no track-commit command. Call
  `backlogit_track_commit` through a `backlogit mcp` stdio client.
* `uv run` can fail on a TLS handshake to PyPI. `.venv\Scripts\autoharness.exe`
  is a working fallback.

## Follow-Ups

New: `D15F6A93` (operator question: should compound learning run at every
closure). `C9E87CE9` was captured in error, because its targets were
already archived; Stage should dismiss it. No other follow-ups are pending.
