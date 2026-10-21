---
title: "Ship session memory: 221-S / 214-F post-merge closure"
date: 2026-10-21
agent: ship
shipment: 221-S
feature: 214-F
---

# Ship session: 221-S / 214-F (G2 backlog CLI first-class peer of MCP), dark mode P-017

Release 1.6.0 chain 3/6.

## Decisions

* PR #548 merged as `114625743ebbd9c5583a1d3b754ad33ed8a5bea5` (merge commit, two parents, in origin/main). Tasks 214.001-T..214.005-T.
* Reviewed HEADs: `4ffbbea3` (local review READY), `275b52ab`, `da218a62` (final, merged). Two Copilot review rounds (6 findings): 5 fixed (stash add flag/option termination, link `--type`, unfiltered shipment listing wording, hook poll payload-less output), 1 deferred to stash `3D06D419` (P-021 C1).
* Closure via cascade (engine VERIFIED on backlogit 1.11.0); 221-S archived `shipped`.

## Failed approaches and slips

* The branch name must be `feat/<shipment-number>-s-...` (`feat/221-s-...`) or `pre_claim` blocks `BRANCH_MISMATCH`. A first branch name lacked the `-s-` form, and a chained `backlogit shipment claim` ran despite the blocked gate; the branch was renamed before any work and `post_claim` / `pre_claim` then passed. Never chain the claim after the gate with `;`.
* `backlogit shipment claim` on this workspace takes minutes and cascades queued tasks to `active`.
* CI flake once in `test_telemetry_jsonl_sink` two-writer interleave (passed on rerun and locally).

## Learnings

* Copilot checks registry CLI mappings against backlogit source flags; the command-path inventory test cannot catch invalid flags, so argument-level assertions are needed.
* `backlogit stash add` and `link add/remove` take positional arguments; use `--` before free text.
* Pre-push hook runs the full unittest suite (about 20 min).

## Follow-ups

* Stash `3D06D419` (package pinned backlogit inventory into verify_workspace; requires deliberation), stash `89948730` (hook CLI template variables; remaining "CLI fallback" wording).
