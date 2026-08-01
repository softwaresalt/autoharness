---
title: "Ship claim-integrity verification (queued-with-active-work mitigation) — DECIDED"
type: decided-plan
date: 2026-07-30
decided_at: 2026-08-01
supersedes: docs/archive/plans/2026-07-30-ship-claim-integrity-preflight-plan.md
source: docs/decisions/2026-07-30-ship-claim-integrity-preflight-spike.md
shipment: 106-S
feature: 102-F
decision: PASS
stash_ref: "6D6CACC1"
tags:
  - "ship-agent"
  - "claim-integrity"
  - "backlogit-shipment"
---

# Decided Plan — 102-F Ship claim-integrity verification

Consolidated from the reviewed plan (plan-review **PASS**, `Requires plan
hardening: no`, Revision Log r1 = PR #269 review fixes). This decided-plan keeps
only the actionable decisions and rationale; the verbose original is archived at
`docs/archive/plans/2026-07-30-ship-claim-integrity-preflight-plan.md`.

## Scope

In-repo mitigation for the backlogit *queued-with-active-work* inconsistency,
implemented entirely in the Ship agent's claim flow. The backlogit-internal
transition guard is **external** (routed upstream — R3/R4); no backlogit source,
schema, or CLI-distribution change.

## Surviving Implementation Units (both shipped)

### Unit A — Post-claim shipment-status verification (`102.001-T`)

- **After** the Step 0.5 claim, re-read the shipment record's **own** status,
  **preferring the backlogit CLI** (`backlogit shipment get`) — MCP is the flaky
  surface this guard exists to catch, so the verify must not be defeated by the
  same transient.
- Assert `status == active`.
- **Retry-once ONLY when the re-read is `queued`** (CLI `backlogit shipment claim`,
  re-read); if still not `active`, halt fail-closed
  `CLAIM_VERIFY_FAILED: shipment {id} did not reach active after claim` + P-005 event.
- **`blocked` → halt immediately `CLAIM_VERIFY_FAILED`, no retry / no claim.**
  Remediation: resolve the blocking gate and transition `blocked → queued` before
  any claim — never re-claim-to-`active` on a `blocked` record. Cite
  `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md:32-44`.
- Both halts fire **before** the first task→`active` transition — template
  **Step 4.1 Claim Task** (`templates/agents/_ship.agent.md.tmpl:264,297`; the
  template's Step 2 is *Harness Generation*, not the task loop), which in the
  dogfood mirror is **Step 2 Task Execution Loop**.

### Unit B — Queued/blocked-with-active-work intake early-warning (`102.002-T`, depends on A)

- Runs **immediately after the shipment record is loaded, BEFORE the Step 0.5.1
  status validation and BEFORE the Step 0.5.4 claim** (placement before *both* is
  mandatory — validation rejects `blocked` earlier, and a `queued → active` claim
  masks the inconsistency).
- If the record is `queued`/`blocked` **and** any manifest task is `active`/`done`,
  halt `SHIPMENT_STATE_INCONSISTENT` (detect-and-report only, no auto-repair).
- Scans **manifest task IDs only** (task-only manifest, 097-S contract; covering
  feature derived via `parent_id`, not scanned), via the CLI fallback path.
- Applied in **both** the template (`templates/agents/_ship.agent.md.tmpl`) and the
  dogfood (`.github/agents/_ship.agent.md`) — the dogfood addition also closes the
  template↔dogfood drift (dogfood Step 0.5 lacked the intake reconcile step).

## Key Decisions

1. **Prevent + detect, not auto-repair** — honors `shipment-reconcile`'s reserved
   auto-mutation; true self-repair is a deferred follow-up.
2. **Edit both template and dogfood** — the dogfood must dogfood the guard.
3. **Fail-closed before the task loop** — the inconsistency can never be created.
4. **Two atomic units A → B** — A independently shippable; A→B avoids same-file
   conflicts and makes Unit B the last mirror edit that writes the end-state
   `.autoharness/harness-manifest.yaml` checksum.
5. **Scope excludes** `shipment-reconcile` pre-mode status classification and any
   backlogit-internal change (recorded as follow-ups: one deferred stash, one
   upstream referral).
6. **Consistency scan precedes validation and claim** (masking rationale above).
7. **Never re-claim a `blocked` shipment** — retry applies only to `queued`.

## Constraints / Gates

- Affected files per unit (3): template + dogfood mirror + `harness-manifest.yaml`
  checksum. Canonical gate: `test_manifest_tracks_dogfood_ship_agent_checksum`
  (`tests/test_telemetry_ship_lifecycle.py:46-53`) — the mirror sha256 must match.
  Unit B lands the final mirror bytes + authoritative end-state checksum
  (`bf56d28b8f5951c9a3d656d578aa883f883556e723deae84245b5c53ee888833`).
- Fixed greppable halt tokens: `CLAIM_VERIFY_FAILED` (A), `SHIPMENT_STATE_INCONSISTENT` (B).
- Frontmatter validity, no unresolved `{{VAR}}` in the dogfood output, markdownlint
  structure preserved.

## Deferred / Rejected Alternatives

- **Auto-repair (self-heal re-claim)** — deferred; `shipment-reconcile` reserves
  auto-mutation for a future version.
- **`shipment-reconcile` pre-mode shipment-record-status classification (P3-3 / C11)**
  — deferred to stash `2970FA4E` to keep single-family blast radius.
- **Backlogit-internal `blocked → active` transition guard (R3)** — external;
  routed upstream, not patched here.

## Rollback

Revert the merge commit (documentation/template text + mirror + manifest checksum
only; no schema, CLI distribution, data migration, or runtime state). Trivially
revertible; blast radius = single template family (agents), additive, reversible.

## Revision Log (r1 — PR #269 Copilot review, 2026-07-30)

8 valid Copilot comments on the plan/task artifacts applied in 3 themes (marker
`decision: PASS` unchanged): **A** — relocate Unit B before validation + claim;
**B** — add `harness-manifest.yaml` checksum to both units' affected files + the
`test_manifest_tracks_dogfood_ship_agent_checksum` gate (Unit B writes end-state);
**C** — Unit A retry only on `queued`, `blocked` halts with no retry/claim
(`blocked → queued` before any claim). Dependency `102.001-T → 102.002-T` unchanged.
