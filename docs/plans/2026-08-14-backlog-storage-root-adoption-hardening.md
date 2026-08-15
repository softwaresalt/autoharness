---
title: "Plan Hardening — Adopt the backlogit `.backlog` storage root (P-006)"
date: "2026-08-14"
description: "P-006 hardening pass over the .backlog storage-root adoption plan. Verdict HARDENED. Covers precedence fidelity, fail-closed ambiguity, schema legacy preservation, dark-mode exclusion of the live repository rename, and detect-only tune behavior."
doc_type: plan
source: docs/plans/2026-08-14-backlog-storage-root-adoption-hardening.md
plan_id: "PLAN-BACKLOG-ROOT-H"
verdict: "HARDENED"
stash_ids: ["BED0DDED"]
model_route:
  model_family: claude-opus-5
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "docs/plans/2026-08-14-backlog-storage-root-adoption-plan.md"
  - "docs/reviews/2026-08-14-backlog-storage-root-adoption-review.md"
  - ".backlogit/queue/018-DL.md"
---

# Plan Hardening — `.backlog` storage-root adoption

**Trigger:** the plan declares `Requires plan hardening: yes` (schemas + CLI +
multiple template families + CI scripts, all touching backlog-state resolution).

**Verdict: HARDENED.** H1-H8 below are binding constraints on harvest and on Ship.

---

## H1 — No literal flip before classification (gating)

No `.backlogit` literal may be changed until T1's inventory has classified that
occurrence as *resolver-routable* or *literal-required*. T3 and T5 are dependency-
blocked on T1. Rationale: an unclassified flip is exactly the failure the two
prior deferrals were protecting against.

## H2 — Precedence fidelity is a P0 invariant

The autoharness resolver MUST reproduce upstream ordering exactly:

1. `BACKLOGIT_WORKSPACE_DIR` (validated; empty or NUL-containing values rejected)
2. `.backlog`
3. `.backlogit`

Any divergence — including "helpfully" preferring the legacy root, or silently
defaulting when the override names a missing directory — is a P0 defect. Upstream
returns `os.ErrNotExist` when an explicit override is absent rather than falling
through to the candidate scan; the follower MUST NOT fall through either.

## H3 — Ambiguity fails closed, always

When both `.backlog` and `.backlogit` are present, autoharness MUST report and
halt, mirroring upstream `AmbiguousWorkspaceRootError`. It MUST NOT:

* pick either root,
* merge, copy, or reconcile content between them,
* delete or rename either directory,
* or treat the condition as a warning that execution may continue past.

This is a report-and-halt boundary identical in spirit to the shipment-reconcile
default preserved by stash `936C68F3`.

## H4 — Schema changes are additive with a version bump

The three schema updates MUST widen the accepted set (add `.backlog`, keep
`.backlogit` valid) and MUST carry a version identifier bump. In-place semantic
mutation of a validation contract without a version bump is a recorded prior
failure: `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`.
Removing `.backlogit` from any enum or example set in this shipment is forbidden —
legacy workspaces remain supported upstream and MUST remain supported here.

## H5 — The live repository rename is excluded from automation (dark-mode guard)

No task in this plan may execute `backlogit migrate --workspace-dir`, rename
`.backlogit`, or edit `.autoharness/backlog-registry.yaml`'s `directory:` value
for this repository. This exclusion MUST appear verbatim in the acceptance
criteria of every harvested task, so it survives task-level context isolation.

Rationale: the storage root is live state that the Orchestrator, Stage and Ship
are concurrently reading and writing during a dark-factory run. Renaming it
mid-run relocates the shipment manifests, the queue, the index and the checkpoint
store simultaneously, and `migrate --rollback` cannot recover work that other
agents wrote to the old path after the move began.

## H6 — Tune is detect-and-report only

The tune-harness rule (T6) MUST NOT invoke migration, MUST NOT write to a target
workspace's storage root, and MUST surface an operator proposal citing
`backlogit migrate --workspace-dir --dry-run`. This matches the non-destructive
proposal discipline already established for tune's script-artifact rules.

## H7 — External repository stays read-only

`C:\Source\GitHub\backlogit` MUST NOT be mutated. All upstream facts in the plan
were established by read-only inspection and are reproducible from v1.9.0 /
HEAD 39528a41. Per the 2026-07-02 cascade-guard external-bug precedent, no
upstream change may be fabricated or assumed.

## H8 — Anti-drift: no directory-name configuration invention

Autoharness MUST NOT invent its own directory-name configuration key, env var, or
config field. `BACKLOGIT_WORKSPACE_DIR` is upstream's contract and is the only
override honored. Adding a competing autoharness-side setting would recreate the
two-sources-of-truth split this plan exists to close.
