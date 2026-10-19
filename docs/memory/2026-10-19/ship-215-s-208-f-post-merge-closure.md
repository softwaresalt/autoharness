---
title: "Ship session 2026-10-19: 215-S / 208-F post-merge closure"
date: 2026-10-19
agent: ship
shipment: 215-S
feature: 208-F
session_id: ship-2026-10-19-215-s-208-f
doc_type: memory
---

# Ship session: 215-S / 208-F (all times UTC)

## Outcome

* PR #539 merged as `8e807a255cd26c502a0d2e184925ccb1dfc9629d` (merge commit, two parents; ancestor of `origin/main`). Reviewed HEAD at merge `e312db3c`.
* Closure via CASCADE (`--classify-only` exit 0, mutating `--detach` exit 9, `--poll` to exit 0 after about 27 minutes; `--timeout 2280`, N = 16, B = ceil(1.5 x (800 + 45 x 16))).
* Evidence: `docs/closure/evidence/215-S-208-F-close-evidence.json` (phase `post_close`, postcondition pass).

## Pipeline events

* `TOOL_DEGRADED`: backlogit MCP not exposed; CLI fallback used for all backlog operations (registry-declared). `INDEX_SYNC_OK (CLI)`.
* Bootstrap grant `215-S` consumed at both Ship sites: `ship_pre_branch` (from `main`) and `ship_pre_claim` (after renaming the branch to carry the shipment id). `forced: true`, token `PREDECESSOR_CLOSURE_INCOMPLETE`, predecessor `214-S`, head `8c13c9a3`. No `--force`.
* Claim verified (`CLAIM_VERIFY_OK`, `post_claim` topology pass). Intake reconcile PROCEED.
* Implementation delegated in seven sequential batches (B1-B2, B3a-B4a, B5, B6-B6a, B7, B8-B9, B10-B11), TDD per task. Review: ten personas (0 P0/P1), five in-scope fixes, delta review clean, then Copilot round 1 finding (fixed `e312db3c`), round 2 clean.
* P-021: four deferred-scope stash entries captured pre-PR: `623963D0`, `81E933B2`, `7FB1D9BF`, `9669DD1E`; post-merge follow-up `B891B448` (Ship template branch naming).
* P-009: merge commit used; squash and rebase are disabled on the repository.

## Learnings

See `docs/compound/2026-10-19-ship-branch-naming-slow-backlogit-cli-and-concurrent-mutation-flakes.md`.
