---
title: "Shipping a 14-task shipment under a bootstrap grant: topology branch naming, slow backlogit CLI calls, and concurrent-mutation test flakes (observed in 215-S)"
problem_type: workflow-pitfall
category: workflow
root_cause: "Several independent frictions appeared while shipping 215-S end to end. (1) The Ship template tells the agent to create `feat/{feature-slug}`, but the pipeline-topology branch_ownership check only recognizes a branch whose slug equals one of the shipment's title aliases or starts with `{shipment-id}-`, so a feature-slug branch fails the second pre_claim run with BRANCH_MISMATCH. (2) With a ~1950-artifact backlog the backlogit CLI takes minutes per mutation (shipment claim about 7 min, each `move --status done` about 3.5 min), which makes per-task backlog bookkeeping the long pole unless it runs in a background shell while implementation continues. (3) Backlog mutations running concurrently with the unit-test suite flake the tests that assert a read-only tree (poll/close tests)."
tags: [ship, pipeline-topology, branch-ownership, bootstrap-grant, backlogit-cli, test-flake, p-017]
shipment: 215-S
date: 2026-10-19
source: docs/compound/2026-10-19-ship-branch-naming-slow-backlogit-cli-and-concurrent-mutation-flakes.md
doc_type: learning
---

## Problem

Shipment 215-S (feature 208-F, 14 tasks) was shipped end to end under an operator-delegated
bootstrap grant. Three frictions cost time and are worth recording.

## What happened and what works

### Branch naming must carry the shipment id

The first `pre_claim` run (the `ship_pre_branch` grant site, from `main`) consumed the grant and
passed. After the branch was created as `feat/model-routing-catalog-bindings` the second run (the
`ship_pre_claim` site) returned `BRANCH_MISMATCH: current branch ... does not match target 215-S`
with `forced: false`, so the grant was not consumed there. `_resolve_shipment_from_branch` in
`src/autoharness/gates/topology.py` accepts a slug equal to a title alias or starting with
`{shipment_id.lower()}-`. Renaming the (still empty) branch to
`feat/215-s-model-routing-catalog-bindings` fixed it. Name Ship branches
`feat/{shipment-id-lowercase}-{slug}` (the existing repository convention). The Ship template's
`feat/{feature-slug}` wording does not say this; it is captured as a follow-up.

A grant consumed at the first site does not block the second site: each authorized invocation
label is consumed independently, and the two consumption records are written under
`.autoharness/gates/bootstrap-grant-consumption/{shipment_id}/`.

### Backlog bookkeeping is slow; run it in a background shell

`backlogit shipment claim` took about 7 minutes and each `backlogit move <task> --status done`
about 3.5 minutes on this workspace. Keep one background shell that loops over completed tasks
(`move --status done`, then `comment add <id> --actor ship --comment ... --commit-sha <sha>`) while the
next implementation batch runs. `backlogit comment add` takes `<item-id>` plus `--actor`,
`--comment`, `--commit-sha` flags (not positional text). A `done` move relocates the task record
to `.backlogit/archive/`; the queue/archive state must be committed before the PR.

### Do not run backlog mutations during the suite

Tests that assert a tree is unchanged during a poll (for example
`test_a_running_supervisor_is_exit_9_and_wait_resolves_it`) flake while a background `backlogit`
process rewrites `.backlogit/`. Re-run such a test alone to confirm, and sequence backlog
bookkeeping around the canonical full-suite gate rather than alongside it.

### Smaller points

* The pre-push hook runs the whole unit-test suite (about 30 to 40 minutes serial). Treat the push
  as a long call: run it async and read it with long delays.
* A delegated implementer once ran `git stash` and `git stash pop` to check a flake; with
  background backlog writes that is risky. Tell implementers never to run `git stash`.
* The ambient `.worktrees/copilot-prewarm-*` worktree (a Copilot app artifact) reappears and trips
  `MULTIPLE_IMPLEMENTATION_WORKTREES` in the topology tests and gate; verify it is clean and detached,
  then `git worktree remove` it.
* Requesting a Copilot review without GitHub MCP used the GraphQL `requestReviews` mutation with
  `botIds` (see `docs/compound/2026-10-12-requesting-copilot-review-via-graphql-bot-id.md`); the
  review arrived in about 4 minutes both rounds.
* Review findings that touch your own earlier review fix are worth a second look: Copilot caught a
  legacy-schema re-render case introduced by the first round of local fixes.
