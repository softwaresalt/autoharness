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

## H4 — Schema changes are additive; the version bump is conditional

**Revised (PR #339 Copilot review, comment 3788712399; PR #342 follow-up).** The
original wording mandated widening plus a version bump unconditionally. Verified
against current `main`, there is nothing to widen: `harness-config.schema.json:107-114`
and `backlog-tool-registry.schema.json:22-26` both declare `directory` as an
unconstrained `"type": "string"` (no `enum`, no `pattern`), and
`workspace-profile.schema.json:224` mentions `.backlogit/**` only as prose inside a
`description`. `.backlog` documents already validate.

H4 therefore now reads:

1. **Additive only** — removing `.backlogit` from any enum or example set in this
   shipment stays **forbidden**. Legacy workspaces remain supported upstream and MUST
   remain supported here. This half of H4 is unchanged and remains mandatory.
2. **No version bump for descriptive/default edits** — T3 as rescoped changes only
   examples, descriptions, and stated defaults. It MUST NOT carry a schema version
   identifier bump, because a bump that leaves the accepted-document set unchanged is
   pure migration and compatibility churn.
3. **Conditional escalation** — if and only if T1 (`126.001-T`) discovers a genuine
   validation constraint on the storage root, the widening becomes real. It MUST then
   be additive, MUST carry a version identifier bump, MUST add the versioned schema
   mirror, and MUST update `src/autoharness/schema_contracts.py`, per
   `docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`.

This matches the rescoped T3 in the plan and the reclassified `126.003-T`, so
implementation receives one consistent instruction rather than contradictory
mandatory directives.

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
