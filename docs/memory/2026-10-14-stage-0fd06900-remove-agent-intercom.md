---
title: "Stage session 2026-10-14 - 0FD06900 remove the agent-intercom capability pack: plan, review, feature 209-F, shipment 216-S"
date: 2026-10-14
agent: stage
session_id: stage-2026-10-14-0fd06900-remove-agent-intercom
source_stash: 0FD06900
---

# Stage session 2026-10-14: 0FD06900 remove the agent-intercom capability pack

All times are UTC (session started 2026-10-14T03:51Z).

## Outcomes

* **Scope (operator decision relayed by the Orchestrator):** full removal of the pack from the
  autoharness product and from the dogfood installed mirrors; no replacement. No deliberation
  artifact: the only open question (dogfood-only vs full) was decided by the operator; every other
  question was answered with repo evidence and recorded as decisions D-1..D-15 in the plan.
* **Plan:** `docs/plans/2026-10-14-remove-agent-intercom-pack-plan.md` (hardened, plan-review PASS,
  `dispatch_mode: single-agent-declared-degradation`, 2 cycles). Standalone review record:
  `docs/reviews/2026-10-14-remove-agent-intercom-pack-plan-review.md`. Cycle 1 failed on one P1
  (constitution Governance requires a version bump, rationale and sync-impact report for an
  amendment); fixed in U10.
* **Harvest:** feature `209-F`, 23 tasks `209.001-T`..`209.023-T`, linear dependency chain, every
  task with `size` and `complexity` (`ah-stage-sizing-v1`, `size_source: agent`) and a
  `harness-surface` label. Totals S:6 M:17.
* **Shipment:** `216-S` (queued) holding `209-F` first, then the 23 tasks in order; `blocks` edge
  on `215-S`. 211-S..215-S were not modified.
* **Stash:** `0FD06900` forward-referenced to 209-F/216-S and archived (content fully consumed).

## Key decisions

1. **Schema versioning (D-2):** profile and manifest 1.0.0 -> 1.1.0, config = then-current + 1
   (expected 1.3.0 after 215-S, derived at claim time); published mirrors byte-pinned; registry
   schema edited in place (no versioned mirror set).
2. **Legacy tolerance (D-3):** extend `LEGACY_UNSUPPORTED_PACKS`-style handling with a version
   independent `removed-capability-pack` warning plus a `remove-retired-capability-pack` migration
   proposal; tune offers cleanup (never auto-deleting a modified overlay file); install/discover/
   deploy wrappers warn-and-skip `agent-intercom` (`RETIRED_PACK`).
3. **Normative text (D-4):** Dark Factory Visibility Protocol relocated into P-017 of
   workflow-policies; Combined Rule becomes the Operator Choice Presentation Rule; circuit-breaker
   stall item 4 deleted; violation reports go to session output + P-005 telemetry;
   clarification/wait = state the question and STOP; output-timestamps instruction unchanged.
4. **Deferred doc (D-5):** delete `docs/deferred/agent-intercom-opt-in-nonmcp.{md,patch}`.
5. **Retained on purpose:** telemetry `route_kind: "intercom"` vocabulary (D-6) and the
   `## Remote Operator Integration` heading (D-8).
6. **Sequencing (D-11):** shipment waits for 215-S (config 1.2.0 slot, shared verify/tune/install/
   policy files).

## Deviations and environment notes

* Backlogit MCP unavailable -> CLI fallback (`DEGRADED_MODE`); engram search degraded and not
  needed. Reviewer subagent dispatch unavailable -> declared single-agent persona pass.
* The crash-recovery checkpoint scan (Step 0) was run after harvest rather than before triage;
  result: 112 checkpoints, 0 active stage candidates, 0 anomalies, so no behavior difference.
* Mid-session the system Git for Windows install (`C:\Program Files\Git`) was left broken by an
  external installer run (mingw64 emptied; `git` exits "error launching git"). Not caused by this
  session. Git operations for the staging commit used the Visual Studio-bundled git
  (`...\Team Explorer\Git\cmd\git.exe`, 2.55.0) invoked by explicit path. The operator may need to
  repair/reinstall Git for Windows.
* Two PowerShell one-liners appended a trailing newline to the plan via `Add-Content` before
  tooling was corrected; no content impact.

* The staging commit was created locally with that substitute git, but `git push origin main`
  was blocked: the repo's opt-in `core.hooksPath=.githooks` pre-push gate (P-019) executes
  `#!/usr/bin/env bash` and the substitute git ships no bash ("No such file or directory"), so the
  hook could not run. Stage did NOT bypass the gate (`--no-verify`) and did not publish through an
  alternate channel. The commit is local on `main` (ahead of `origin/main` by one commit) and is
  ready to push once a working Git for Windows (with bash) is restored.

## Publication update (Orchestrator, after Stage)

The Orchestrator later published the staging commit without bypassing the gate: a hash-verified
PortableGit (inside the ignored session directory) supplied the bash that the pre-push hook needs,
the hook passed, `git push origin main` was rejected by the repository rule (changes must go through
a pull request), so the commit was pushed on `chore/stage-216-S` and opened as PR 518.

## Next steps

* **Publication (blocking Ship routing - Orchestrator Step 1.5):** merge PR 518 with a merge commit
  once the hosted review is clean, then verify `git show origin/main:.backlogit/queue/216-S.md`.
* Ship: claim `216-S` only after `215-S` ships (pre-claim gate enforces the `blocks` edge).
  At claim time re-read the post-215-S baseline for shared files, derive U4's `<N+1>` config
  version from `SCHEMA_CONTRACTS["config"]`, and re-confirm operator authorization for U8
  (quoted in 209.008-T).
* Operator: repair the system Git install if it remains broken.
