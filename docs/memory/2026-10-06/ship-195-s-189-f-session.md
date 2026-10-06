---
type: session-memory
agent: ship
shipment: 195-S
feature: 189-F
date: 2026-10-06
mode: dark (P-017)
---

# Ship session: 195-S / 189-F (S(B-entry))

## Startup (2026-10-06T05:51Z to 06:01Z)

* Preflight by the Orchestrator at 05:51Z: backlogit 1.11.0 CLI, index
  synced, 99 checkpoints with 0 active and 0 quarantined (no recovery).
* Intercom, engram and graphtor tools are not exposed in this runtime
  (degraded visibility; milestones are reported with UTC timestamps).
* `uv run autoharness` cannot build here (no network for `hatchling`), and
  the global `autoharness.exe` is a stale non-editable 1.5.0 install. Every
  `autoharness` command in this session runs the checkout's own CLI:
  `python .proof-scratch/195-S/ah.py ...`, a git-ignored wrapper that puts
  `src` on `sys.path` and calls `autoharness.cli:main`.
* Temp reroute (Principle IV, stash `B99B661D`): every test run, hook and
  `git push` sets `TEMP`/`TMP`/`TMPDIR` and `GIT_CEILING_DIRECTORIES` to the
  git-ignored `.proof-scratch/195-S/tmp`.

## IM-14 harvest-commit audit (before the first claim, 05:57Z)

The plan's detector (`DETECTOR`, `normalize`, `_spanning` from
`tests/test_harness_noclaim_audit.py`) ran over every added line of each
non-merge harvest commit's own diff, including adjacent-line joins, plus a
camelCase scan:

| Commit | Content | Files | Added lines | Hits | Disposition |
|---|---|---:|---:|---:|---|
| `90f23361` | harvest S(B-entry) (195-S, 189-F, 189.001-T to 189.003-T) | 5 | 231 | 3 | All three are the AC "IM-14: no added text claims race, TOCTOU or hardlink-alias resistance." (non-claim) |
| `d633cd58` | AC bullet fix in S(B-core) tasks | 3 | 15 | 0 | none |
| `7ca13f66` | harvest S(IM-10) (190-F, 190.001-T, 190.002-T) | 6 | 168 | 3 | 190-F DoD and the 190.001-T / 190.002-T ACs, each the same IM-14 disclaimer (non-claim) |

No join hit and no camelCase hit. The harvest merge that brought these
commits to `main` is `e38ac305` (PR #457), conflict-free and audited at
193-S (IM-14-F67).

## Pre-claim decisions

* Working tree on `main` before branching: the uncommitted stash line
  `A34432A2` (left by a prior Orchestrator run) is carried unchanged into the
  first backlog commit on the feature branch. The operator-local
  `.github/copilot/settings.local.json` (modified) and
  `.github/copilot/settings.json` (untracked) are known out-of-scope operator
  state: never modified, stashed, discarded, staged or committed. The P-011
  clean-tree check is read as "no uncommitted work of this shipment"; these
  three paths are recorded here as the only exceptions.
* Stash `672A3F27` (B-entry design inputs from the 194-S review) is still
  untriaged by Stage. Ship reads it only as non-binding implementation
  guidance consistent with the frozen task ACs; it is neither triaged nor
  mutated (P-010).

## Claim (06:00Z)

* `pre_claim` on `main`: exit 0 (`BRANCH_CREATE_ELIGIBLE`, predecessor
  `194-S` explicit). Branch
  `feat/195-s-s-ship-lifecycle-unit-b-entry-ledger-and-digest-reducer-with-early-return-resolve-shipment-and-harness-resolve-cli`
  created from `main` at `1a6648de`. `pre_claim` again on the branch: exit 0
  (`BRANCH_OK`, `WORKTREE_TOPOLOGY_OK`). No bootstrap grant.
* `backlogit shipment claim 195-S` wrote the claim (195-S, 189-F and the
  three tasks all `active`, the P-002.7 post-claim state) but its process did
  not return; it was stopped after the write was confirmed.
* `post_claim`: exit 0, sole active shipment. CLI re-read: `status: active`.
  `CLAIM_VERIFY_OK: shipment 195-S reached active and is the sole active
  shipment`.
* Intake reconcile (`mode: pre`, `expected_status: active`): 4 items matched,
  0 orphans, record-consistent -> `PROCEED`.
