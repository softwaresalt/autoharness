---
title: "A failed cascade-close record with mutation_state none cannot be superseded by --replace-pre-close; recovery needs an authorized move-aside (observed in 223-S)"
problem_type: tooling-pitfall
category: workflow
root_cause: "`autoharness shipment cascade-close` finalizes a post_close evidence record even when the run failed before any mutation (exit 6 invocation_failed, mutation_state none). `--replace-pre-close` only supersedes a pre_close record, so it refuses the finalized failure with 'evidence already finalized'. The failure itself was a transient ~10 s internal backlogit lineage-check deadline on one member under host load; it is not configurable through --timeout."
tags: [cascade-close, replace-pre-close, evidence, lineage-deadline, host-load, ship, shipment-reconcile]
shipment: 223-S
date: 2026-10-23
source: docs/compound/2026-10-23-cascade-close-failed-record-needs-authorized-move-aside.md
doc_type: learning
---

## What was observed

* Attempt 1 of the mutating cascade close failed with exit 6 `invocation_failed`; the cause was the internal backlogit lineage-check deadline on member `216.006-T`. `mutation_state` was `none` and nothing was archived.
* `--replace-pre-close` refused the record: 'evidence already finalized'.
* Operator-authorized recovery under dark mode: hash-verify the failed record (SHA-256), keep a preserved copy in `docs/closure/evidence/`, move (never edit) the record out of the active path, redo `--classify-only`, re-verify ancestry of every member head, then run one mutating re-run (attempt 2 of 3). It succeeded.

## Guidance

Treat a finalized record with `mutation_state: none` as a counted failure of the same operation. Do not edit it. Recover only with an explicit operator authorization and a hash-verified preserved copy committed with the closure PR. Tracked as a stash follow-up: `--replace-pre-close` should supersede such records.

Related: the Copilot review of the docs-only checker needed 12 fix cycles, and the Windows pre-push hook flaked and was retried; neither changed the closure path.
