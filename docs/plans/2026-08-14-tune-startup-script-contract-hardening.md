---
title: "Plan Hardening — Tune target-workspace startup-script contract migration (P-006)"
date: "2026-08-14"
description: "P-006 hardening pass over the 125-F Tune startup-script contract migration plan, which declared 'Requires plan hardening: yes' but had no hardening artifact. Verdict HARDENED. Covers destructive-rewrite discipline, classification fail-closed behavior, and scope exclusions."
doc_type: plan
source: docs/plans/2026-08-14-tune-startup-script-contract-hardening.md
plan_id: "PLAN-TUNE-STARTUP-H"
verdict: "HARDENED"
stash_ids: ["015B2914"]
model_route:
  model_family: claude-opus-5
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - ".backlogit/archive/125-F.md"
  - ".backlogit/queue/017-DL.md"
  - "docs/reviews/2026-08-14-tune-startup-script-contract-review.md"
---

# Plan Hardening — Tune startup-script contract migration (125-F / 134-S)

**Gate-gap origin.** Feature `125-F` records *"Plan Hardening conclusion:
Requires plan hardening: yes"*, but no hardening artifact and no plan-review
artifact existed for it. Shipment `134-S` was nevertheless left queued as the
next claim cursor. Under P-006 a plan that declares a hardening signal must be
hardened before plan-review, and under the Stage step contract a shipment must
not enter execution ungated. This artifact and its sibling review close that gap.
No decomposition change was required.

**Verdict: HARDENED.** H1-H6 are binding on Ship.

## H1 — Back up before any mutation, without exception

Any accepted refresh of an installed `start.ps1` / `start.sh` MUST copy the
original into the target workspace's dated autoharness backup area **before** the
new content is written. A refresh that cannot back up MUST abort rather than
proceed. Precedent: `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`.

## H2 — Classification failure fails closed to operator review

The five-way classification (missing / current / known-legacy pre-shim /
user-modified / ambiguous-unknown) MUST resolve to an operator-review proposal
whenever content cannot be confidently classified. Silent overwrite of an
unclassified or ambiguous file is forbidden. "Ambiguous" is a terminal outcome
that halts auto-apply — it is never coerced into "legacy" to enable a refresh.

## H3 — Contract version is additive and legacy-tolerant

The named startup-script contract/version MUST be introduced with a
backward-compatible default for manifests that predate the metadata. A manifest
without the field MUST be interpreted as legacy, never as invalid, and never as
current. This mirrors the versioned-identifier lesson in
`docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`.

## H4 — Manifest metadata updates strictly follow accepted file changes

Contract/checksum metadata MUST be written only **after** the file change is
accepted and applied. Writing metadata first would leave a workspace whose
manifest claims the current contract while the file on disk is still legacy —
a state that permanently suppresses future drift detection.

## H5 — Custom-section preservation is deterministic or it halts

Extraction and reattachment of supported operator-added sections (Claude Code,
Codex, and other safe blocks) MUST be deterministic and round-trip verifiable.
If reattachment cannot be verified, the run MUST produce an operator-review
proposal instead of writing the file. Losing an operator's customization is a
worse outcome than leaving a script stale.

## H6 — Scope exclusions are binding

Target workspaces only. This work MUST NOT modify autoharness's own repository
`start.ps1` / `start.sh` (already migrated to thin shims by shipped Plan 1),
MUST NOT re-plan Plan 1, and MUST NOT resurrect Plan 3 remote UI work.
`install-harness` and the current startup templates change only if implementation
evidence proves shared contract metadata or generation wiring is missing.
