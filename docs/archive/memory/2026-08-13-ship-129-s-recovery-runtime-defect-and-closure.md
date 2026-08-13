---
date: 2026-08-13
shipment: 129-S
feature: 120-F
agent: ship
session_type: dark-factory-execution
---

# 2026-08-13 — Ship: 129-S Recovery, Runtime Defect Fix, Review Hardening, and Closure

## Session Summary

Resumed shipment `129-S` (S3, final Plan-1 shipment) from an interrupted Ship
invocation. Branch `feat/129-s-s3-copilot-supervisor-application-services-adapters-start-ps1-start-sh-migration`
was preserved in place at HEAD `0ff7bd8e`. The operator reported a concrete
release-blocking runtime defect discovered on a real launch: Engram and
graphtor-docs never became live under `start.ps1` / `autoharness run`, while
Copilot and backlogit did start.

## Root Cause (diagnosed and fixed before this window's compaction boundary)

`.mcp.json` used the VS-Code-only editor variable `${workspaceFolder}` in the
engram/graphtor-docs/backlogit MCP server `env` blocks. The standalone
`copilot` CLI (the actual runtime here) never substitutes editor variables —
it passes them through literally, crashing both `engram shim` and
`graphtor-docs serve` on launch. Fix landed in three parts, all within
existing 129-S/120-F scope: (1) removed the broken override from `.mcp.json`,
letting each tool fall back to its own working CWD-relative default; (2)
threaded an explicit `cwd` through every real child-process backend and
anchored the Copilot child factory's cwd to `workspace_root`; (3) added
graphtor-docs as a third one-shot preflight sidecar with PATH +
`.graphtor/bin/graphtor-docs(.exe)` fallback resolution, with `cwd` finally
threaded through every sidecar subprocess call. See
`docs/compound/129-s-supervisor-engram-graphtor-startup-and-review-hardening.md`
for full detail.

## This Window's Work: 8 Rounds of P-018 Hosted Copilot Review Remediation

Entering this window, PR #331 was at HEAD `4af32c1b` after 6 rounds of review.
This window carried it through rounds 7 and 8:

- **Round 7** (`b3710d2b`): `.env.local` secret-shaped values other than the
  two hardcoded GitHub-token vars were never registered with the redactor
  (fixed via key-name pattern matching); `_pump_child_output`'s direct
  `sys.stdout.write` bypassed redaction entirely (fixed by redacting each
  chunk before the console write, fail-closed on redaction failure).
- **Round 8** (`3867917f`): `_ENVIRON_MUTATION_LOCK` didn't cover
  `bootstrap_workspace()`'s internal unsynchronized `os.environ` read (fixed
  by acquiring the lock before the call); the PTY backend's `signal()` had no
  already-exited guard (unlike `close()`), risking a PID-reuse signal during
  restart (fixed by passing `child=None` into `attempt()` plus an explicit
  `child.close()` to avoid an fd leak).

Every finding got a real code fix plus a new regression test, not a dismissal.
Full suite ended at 1853 passed (+713 subtests), 0 failed, 19 skipped. All 16
findings across all 8 rounds were replied-to and their GraphQL review threads
resolved. Final P-018 gate: `SATISFIED`, 0 unresolved threads, at HEAD
`3867917f`.

## PR Lifecycle and Merge

- Updated the PR body's `## Local Review Readiness` block to the final HEAD
  and added a `## P-018 Copilot Review Rounds` summary section.
- Verified P-009 (merge-commit-only) at the repo level:
  `allow_merge_commit: true`, `allow_squash_merge: false`,
  `allow_rebase_merge: false`.
- No formal `DARK_MODE_ACTIVE` activation record file existed in
  `.autoharness/`; treated the operator's own explicit initiating instruction
  ("merge with `--merge` under the existing operator dark-mode full approval
  only after all gates pass") as the conditioned approval signal, now
  exercised since CI green + P-018 SATISFIED + P-009 verified all held.
- Re-verified HEAD unchanged and re-ran the P-018 gate immediately before
  merge (unconditional re-run required by protocol) — still `SATISFIED`.
- Merged PR #331 with `gh pr merge 331 --merge`. Merge SHA:
  `fa0eb14bad50d0b4ec028685a15f7472a6984e39` (2 parents — P-009 confirmed
  post-merge).
- Merge Confirmation Gate: `gh pr view 331` → `MERGED`;
  `git merge-base --is-ancestor fa0eb14b origin/main` → exit 0.

## Post-Merge Closure

- Created `post-merge/129-s-s3-copilot-supervisor` from `main` per the
  Post-Merge Branch Protocol.
- Ran the P-015 classifier (`classify_shipment_close_path`) against the
  manifest (`120-F`, its 8 tasks, `117-F`): returned `CASCADE`, both features
  qualifying as verified fully-covered roots.
- Re-ran `sim-shipment-closure.ps1` (dynamic engine attestation, per the
  097-S doc's Ship-facing guard) against the installed engine
  (`backlogit v1.9.0`, commit `39528a4`): **66/66 assertions passed**.
- Confirmed `117-F` independently: no `parent_id` (root), zero live children
  in queue+archive.
- Executed `backlogit shipment ship 129-S --sha fa0eb14b... --message ... --author ...`.
  Result: `archived_ids` = all 11 manifest artifacts
  (`120.001-T`..`120.008-T`, `117-F`, `120-F`, `129-S`), `returned_ids: []`.
  Zero Plan-1 queue residue confirmed afterward (no `11*`/`12*` files left in
  `.backlogit/queue/`).
- Ran `backlogit sync` (index resync) — indexed 784 artifacts.
- Committed the closure state (`.backlogit/` mutations) on the post-merge
  branch: `25013b5d`.
- Wrote compound learning doc:
  `docs/compound/129-s-supervisor-engram-graphtor-startup-and-review-hardening.md`.

## Key Lessons for Future Ship Sessions

1. Never trust an editor-substitution variable (`${workspaceFolder}`, etc.)
   in any config also read by a headless/standalone CLI — verify with a
   literal-echo probe (`copilot mcp get ... --show-secrets`) rather than
   assuming VS Code's substitution behavior is universal.
2. Redaction coverage should be driven by key-name **pattern** matching
   against an extensible ruleset, not an enumerated allowlist of specific
   variable names — new secret-shaped env vars must be covered automatically.
3. Every distinct output sink (console write, event bus, journal) needs its
   own verified redaction application point; redacting one sink is not
   evidence the others are covered.
4. When auditing a lock's scope, trace every read of the protected state
   backward to its logical origin — a lock around only the write step misses
   reads that logically precede it.
5. A guard against operating on an already-exited process must be mirrored
   in every method capable of triggering that operation (e.g. `close()` and
   `signal()` both call into process-kill primitives) — auditing only one
   method is insufficient.
6. `sim-shipment-closure.ps1`'s dynamic engine attestation guard (per the
   097-S doc) is the correct mechanism to re-verify P-015 cascade-close
   safety immediately before any Ship close — it is version-agnostic and
   fails closed only on unattested/incoherent identity, not merely a newer
   or older build.

## Residual Follow-ups

None identified. Continuing to remaining closure steps: P-020 compact-context,
operational-closure/runtime-verification artifacts, and the post-merge closure
PR.
