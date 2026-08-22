---
problem_type: claim-integrity
category: ship-workflow
root_cause: backlogit-queued-with-active-work-inconsistency-unmitigated-in-claim-flow
tags: [backlogit, shipment, claim, status, blocked, queued, active, ship-agent, guard-token, p-018, telemetry]
shipment: 106-S
feature: 102-F
pr: 270
tokens: [CLAIM_VERIFY_FAILED, SHIPMENT_STATE_INCONSISTENT]
source: docs/compound/106-S-claim-integrity-guards.md
doc_type: learning
title: "106-S / 102-F: Ship Claim-Integrity Guards (queued/blocked-with-active-work)"
---

# 106-S / 102-F: Ship Claim-Integrity Guards (queued/blocked-with-active-work)

Shipment `106-S` added an in-repo mitigation for the backlogit
*queued-with-active-work* inconsistency, where a shipment record can read
`queued`/`blocked` while its manifest tasks are already `active`/`done`. The
backlogit-internal transition guard that would prevent this at the source is
**external** and was routed upstream — the mitigation here lives entirely in the
Ship agent's claim flow (template + dogfood mirror), never in backlogit source.

Two guard tokens now anchor the Ship claim flow:

- **`SHIPMENT_STATE_INCONSISTENT`** — Unit B intake early-warning (detect-and-report).
- **`CLAIM_VERIFY_FAILED`** — Unit A post-claim status verification (fail-closed).

## Problem

The backlogit claim transition (`queued → active`) is not always atomic/consistent
against the manifest task states. Two failure shapes were observed / reasoned:

1. **Pre-claim inconsistency** — the loaded shipment record is `queued`/`blocked`
   while a manifest task is already `active`/`done`. A *successful* `queued → active`
   claim would silently **mask** this (the record just becomes `active` and looks
   healthy), and the existing Step 0.5.1 status validation — which accepts only
   `queued`/`active` — would reject a `blocked` record *earlier* than any late-stage
   warning could fire. So the diagnostic must run **before both** the status
   validation and the claim.
2. **Post-claim non-arrival** — after `shipment claim`, the record may not actually
   reach `active` (MCP is the flaky surface). A claim that "returns" without the
   record transitioning leaves the pipeline operating on an unclaimed/mis-stated
   release unit.

## Durable Rule

### Unit B — intake early-warning (`SHIPMENT_STATE_INCONSISTENT`)

- Run the consistency scan **immediately after the shipment record is loaded**,
  **before** the Step 0.5.1 status validation and **before** the Step 0.5.4 claim.
  Placement before *both* is mandatory: status validation rejects `blocked` too
  early, and a successful `queued → active` claim masks the inconsistency.
- If the record is `queued`/`blocked` **and** any manifest task is `active`/`done`,
  halt with `SHIPMENT_STATE_INCONSISTENT`. Detect-and-report only — do not mutate.
- Scan **task artifacts only** (filter by artifact type); never let a feature/shipment
  artifact leak into the task-state check.
- In the generic (dogfood) intake, guard the scan so it **applies only when a
  shipment exists** — the "no shipment / task-selection" intake path must not
  dereference an unset `shipment_id`.

### Unit A — post-claim verification (`CLAIM_VERIFY_FAILED`)

- **After** `shipment claim`, re-read the shipment record's **own** status. Prefer
  the backlogit **CLI** re-read — MCP is the flaky surface this whole shipment
  mitigates.
- Assert the record reached `active`.
- **Retry-once ONLY when the re-read status is `queued`.** A genuinely `queued`
  record may be re-claimed directly.
- **For `blocked`: halt immediately with `CLAIM_VERIFY_FAILED` — no retry, no
  re-claim.** `blocked` is the repository's claim-prevention state; remediation must
  resolve the blocking gate and transition `blocked → queued` **before** any claim.
  **Never** "re-claim to active" on a `blocked` record — that bypasses the gate.
- Guard the verification so it **applies only when a shipment was claimed**.

## The blocked-vs-queued asymmetry (the crux)

| Re-read status | Action | Rationale |
| --- | --- | --- |
| `active` | proceed | claim landed |
| `queued` | **retry-once** (direct re-claim OK) | queued is a legal claim source |
| `blocked` | **halt `CLAIM_VERIFY_FAILED`, no retry/claim** | blocked must clear its gate and go `blocked → queued` first; direct re-claim bypasses the gate |

Cite `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md:32-44`
(blocked → queued before claim; never re-claim-to-active on blocked).

## Why It Matters

Claim integrity is the first mutation of a release unit. If the claim silently
masks a queued-with-active-work inconsistency, or "succeeds" without the record
actually going `active`, every downstream gate operates on a mis-stated unit.
The two tokens make both failure shapes **loud and fail-closed**: Unit B surfaces
the inconsistency before any mutation; Unit A refuses to proceed on an
unconfirmed claim and refuses the illegal `blocked` re-claim path.

## Verification Pattern

1. Load shipment → **before** validation/claim, if `queued`/`blocked` record ×
   `active`/`done` task → `SHIPMENT_STATE_INCONSISTENT` (task-artifact-filtered).
2. After claim → CLI re-read status: `active` proceeds; `queued` retries once;
   `blocked` halts `CLAIM_VERIFY_FAILED` (no retry/claim).
3. Both scans are shipment-existence / claim-existence guarded in the generic
   intake path.
4. Template (`templates/agents/_ship.agent.md.tmpl`) and dogfood mirror
   (`.github/agents/_ship.agent.md`) stay in sync; the mirror checksum in
   `.autoharness/harness-manifest.yaml` is regenerated so
   `test_manifest_tracks_dogfood_ship_agent_checksum` passes on the end state.

## Deferred (out of 106-S scope)

- **C11 / P3-3** — a narrower pre-claim shipment-record-status classification gate
  (`shipment-reconcile` pre-mode) is deferred to stash `2970FA4E` to keep the
  single-family blast radius.
- **R3 (upstream)** — the illegal backlogit-internal `blocked → active` flip during
  claim is a backlogit-internal transition guard; routed upstream, not patched here.
