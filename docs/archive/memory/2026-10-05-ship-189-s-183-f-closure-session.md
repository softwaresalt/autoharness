# Ship session checkpoint: 189-S / 183-F full lifecycle and post-merge closure (2026-10-05)

## Context

* 189-S (SHIP-23) closed out already-merged test-only work. Commit
  `622a41a1` reached `main` through PR #457 (merge `e38ac305`). On operator
  instruction the backlog lifecycle had been left `queued`.
* The session was not in dark mode. Merge needed explicit operator approval.
  Agent-intercom was unavailable, so all reporting went in final outputs. The
  Orchestrator ran the merge and the mutating `cascade-close`; Ship ran
  everything else.

## What ran

1. Startup: the checkpoint scan found 98 records, 0 quarantined, and 0
   active Ship candidates. The backlogit MCP tools were not exposed in this
   session, so the CLI was used (degraded mode). `uv run` failed on a TLS
   handshake to PyPI, so `.venv\Scripts\autoharness.exe` was used instead.
2. `pre_claim` passed from `main` and again from
   `chore/189-s-ship-23-graphtor-mcp-shim-test-synchronization-repair`
   (predecessor `190-S` explicit). The claim succeeded and `post_claim`
   exited 0. Members became `active` (P-002.7). Commit `68f39530`.
3. Re-verification on `c23c8bd3`: the targeted test passed, and 10 repeats
   were 10/10 green (Node v24.12.0).
4. `backlogit_track_commit` (622a41a1 → 183.001-T) was called through a
   `backlogit mcp` stdio script, because the CLI has no track-commit
   command. Comments were added, and 183.001-T and 183-F moved to `done`
   (relocated to `archive/`). Commit `4e8ad8bb`.
5. Local review: `READY_WITH_FOLLOWUPS` (P3 × 4 advisory). Pre-push suite:
   3143 tests OK (skipped 54). PR #492: CI green; Copilot recommended
   approval with no threads; P-018 `SATISFIED: PASS`. The operator approved,
   and the Orchestrator merged it as `a28fb797`.
6. Closure on `chore/189-s-closure`:
   * Lifecycle gate: exit 0.
   * Lock acquired at `03:31:49Z`.
   * Pre-mode: `PROCEED`.
   * Classify-only: `CASCADE` / `VERIFIED`; N = 3, B = 357 s.
   * Orchestrator cascade-close: exit 0, pass. The child ran about 156 s.
     The whole-tree check covered 1896 files and found 4 changes, all in
     scope.
   * INV-12: `DISPOSITION_COMPLETE` (empty).
   * Post-mode: `PROCEED`. Lock released at `03:38:37Z`.
7. Source cleanup: 183-F has no `source_stash_id` or
   `source_deliberation_id`. Its description-only sources, `24A85BF8` and
   `AD3D41FA`, were already archived at harvest on 2026-09-20, so nothing
   was archived. Stash entry `D15F6A93` (the operator-supplied
   compound-learning text block, copied verbatim) was captured. `C9E87CE9`
   was captured in error: Ship read the archived `stash.jsonl` as if it were
   the active one. It stays active for Stage to dismiss.

## Learnings

* The `cascade-close` child for 3 artifacts took about 156 s. The model
  predicted 238 s unmargined. The fixed cost is lower than 133 s when only
  the shipment and two members change.
* The lock token is reusable by a later process; the release step requires
  that. What does not persist is a shell variable or environment binding,
  because each tool call is a new process. Carry the captured token in
  memory or in conversation and bind it again for the release call; never
  write it to a file. The phase-C script received it through `LOCK_TOKEN`.
* Two files are named `stash.jsonl`: `.backlogit/stash.jsonl` (active) and
  `.backlogit/archive/stash.jsonl` (archived). Select-String's `Filename`
  output cannot tell them apart; check the full path before deciding a
  stash entry is still active.
* A `git add` whose pathspec names a removed path (`.backlogit/queue/189-S.md`)
  fails the whole add. Stage only the existing archive paths; the staged
  rename carries the deletion.
* The 200-S `run_c.py` worked again with only the IDs and the token source
  changed.
* An already-merged lifecycle closure needs no code change. The re-run of
  the targeted test plus 10 repeats is the runtime evidence.
