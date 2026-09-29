---
title: "Ship 177-S / 169-F full lifecycle (compacted)"
description: "Compacted Tier-1 release-unit memory for 177-S / 169-F (P-002.7 post-claim member-status contract, P-020). Covers Stage rollout-shaping sessions, execution, PR #462 merge, contemporaneous CASCADE close, and closure."
doc_type: memory
source: docs/memory/compacted/2026-09-29-ship-177-s-169-f-full-lifecycle-compacted.md
date: 2026-09-29
agent: ship
session_id: ship-2026-09-29-177s-closure
compacted_from:
  - docs/archive/memory/2026-09-29-ship-177-s-169-f-session.md
  - docs/archive/memory/2026-09-19-177-s-rollout-d2-conformance-remediation.md
---

# Ship 177-S / 169-F Full Lifecycle (Compacted)

Verbose originals are listed in `compacted_from`. The Stage memory
`docs/memory/2026-09-19/stage-177-s-n1-n2-mechanization.md` is summarized here
but stays in place because a live Stage memory references it. Closure record:
`docs/closure/177-S-169-F-post-merge-closure.md`. Close evidence:
`.backlogit/reconcile/177-S-cascade-close-20260929-032534.md`.

## Outcome

* Feature 169-F delivered P-002.7, the canonical post-claim member-status
  contract. It changed the policy registry and template, the Ship
  cross-reference (mirror and template), the design doc, and added structural
  tests.
* PR #462 merged as `bd706305`. The reviewed HEAD was `6a5ec1df`
  (`READY_WITH_FOLLOWUPS`, P0=0, P1=0), 2469 tests passed OK, and 4/4 CI
  checks passed. The Copilot thread was captured under P-021 as `62C1E11E`.
  Local review produced `065B0331`.
* Closure used a `CASCADE` close with contemporaneous revalidation, a baseline
  fingerprint, and raw ship output. The recommendation was `CLOSED`, and 177-S
  has `archived_status: shipped`.

## Key Decisions (Stage, 2026-09-19)

* The rollout was reordered for D2 conformance from
  PREPARE-RED-ACTIVATE-VERIFY-DOCS to PREPARE-RED-VERIFY-ACTIVATE-CONFIRM-DOCS.
  That change added the pre-activation gate `169.017-T`, which emits
  `PREACTIVATION_READY`, `PREACTIVATION_BLOCKED`, or
  `PREACTIVATION_NOT_OBSERVED`.
* Readiness verdicts bind to commit identity (`head_commit`) as well as
  surface content. After a `git revert` of an activation, the content is
  byte-identical to the pre-activation state, so a content-only digest cannot
  detect a stale readiness verdict.
* The P-002.7 clause text is frozen as test-owned inert candidate data
  (`169.011-T`) and is transcribed verbatim by the single ACTIVATE commit. As
  a result, later wording fixes are deferred scope (`065B0331`, `62C1E11E`).

## Learnings

* `backlogit shipment ship` can take several minutes while it heartbeats its
  lifecycle locks and rewrites the WAL. Do not interrupt a cascade in flight.
* Script the close-evidence capture, including the snapshot, revalidation,
  fingerprint, raw result, and checks, in one run. This avoids the 175-S
  evidence gap (`008F3BCF`) and saves context.
* In PowerShell, `CP` is an alias for `Copy-Item`, so do not use it as a
  helper name.
