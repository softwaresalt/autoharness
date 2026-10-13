---
title: "Ship session memory: 209-S / 202-F gate-aware Orchestrator eligibility and dark-mode activation preflight"
date: 2026-10-12
shipment: 209-S
feature: 202-F
pr: 514
merge_commit: e8693423d0a472745ee67cbfa7da21079c9bb963
---

# Ship session 2026-10-12: shipment 209-S

## Outcome

Shipment 209-S (feature 202-F, tasks 202.001-T to 202.004-T) merged through PR #514
(`--merge`, parents `6227fc09` and `8faa1f86`, merged 2026-10-12T23:20:10Z) and was
closed through the P-015 CASCADE path (`autoharness shipment cascade-close`, postconditions
pass, 6 of 6 IDs archived, shipment `archived_status: shipped`).

## What changed

* Orchestrator Step 0 step 2b: read-only per-DAG-ready-candidate
  `pipeline-topology --phase pre_claim` probe that never carries
  `--bootstrap-grant-invocation` or `--force`; `ELIGIBLE` / `INELIGIBLE: {token}` /
  `GLOBAL_GATE_BLOCK` / `ELIGIBILITY_GATE_SKIPPED` reporting; fail-closed
  `GATE_PROBE_ERROR` and `GATE_INVALID`; new ORCHESTRATOR STATE fields.
* Orchestrator Step 2: advisory "Gate-blocked first-pass skip" with three carve-outs
  (grant-annotated candidates stay selectable; in-scope-only during a dark run; an
  operator-named `ship {id}` is never substituted). Step 2a stays the only bootstrap-grant
  consumption site.
* Dark Factory Mode: activation preflight on the scope head before `DARK_MODE_ACTIVE` is
  recorded (`DARK_MODE_PREFLIGHT_BLOCKED`, `PENDING`, `EXTERNAL_BLOCKER`, optional
  `preflight` field, `head: active (resume)`, stash-only `not_applicable`).
* feature-flow-dark prompt item 1; contract test
  `tests/test_orchestrator_gate_aware_eligibility_contract.py` (4 scenarios).

## Decisions and judgement calls

* A grant-annotated gate-blocked dark-run head fails closed at the preflight (the
  preflight never applies a grant); the operator can route it through a non-dark
  `ship {id}` where Step 2a evaluates the grant.
* The P-017 policy text and `docs/pipeline-topology-gate.md` were not touched (plan units
  A1-A4 do not authorize them). Captured as deferred stash `635D7BAC` (P-021 C2).
* Stash `F2D11D61` (paired carryover doc) was deliberately NOT retired: Stage's triage
  note says to keep it until R1 and the deferred P2/P4/P5/P6 rows are staged. Stashes
  `50DCCBED` and `8675D546` were already archived by Stage's harvest.

## Review history

* Local review: round 1 (Constitution, Correctness, Maintainability, Template Integrity,
  Scope Boundary, Python, Learnings): no P0/P1; the P2 findings were fixed in `e7d41b30`.
  Round 2 (Correctness, Template Integrity): no P0-P2; P3 wording and test pins fixed in
  `825f5489`.
* Copilot: round 1 on `428336c6` produced 4 inline findings (activation condition omitted
  the resume and skipped paths; prompt scope head), fixed in `8faa1f86`, replied and
  resolved; round 2 on `8faa1f86` was "Approval recommended, 0 open findings". P-018 gate
  `SATISFIED`.

## Learnings

* `backlogit move <task> --status done` relocates the task record under `.backlogit/archive/` but
  the record still declares `status: done`. Under P-015 that is NOT truly archived or engine-inert
  (only a declared `status: archived` counts); location is descriptive only. The pre-close contract
  matches those members by declared `done` status, and the later CASCADE close set the final
  `archived` status.
* Observed in 209-S (not a configured fallback; the policy question is stash `1AD61D32`): a
  GraphQL `requestReviews` mutation with `botIds` registered the Copilot reviewer when `gh` and REST
  did not; see `docs/compound/2026-10-12-requesting-copilot-review-via-graphql-bot-id.md`.
* Each push runs the full unittest suite and markdownlint through the pre-push hook
  (about 10 minutes); batch fixes per Copilot round.
