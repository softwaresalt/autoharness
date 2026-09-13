---
title: "Stage session memory — PR #448 review-fix cycle 1 (165-F / 173-S)"
description: "Completion of the partially-applied PR review-fix cycle resolving two Copilot threads on staging PR #448: bootstrap executability and audit purity."
doc_type: memory
source: docs/memory/2026-09-13/stage-165f-173s-pr448-review-fix-cycle-1.md
date: 2026-09-13
agent: stage
branch: chore/stage-173-S
feature: 165-F
shipment: 173-S
pr: 448
---

# Stage — PR #448 review-fix cycle 1 (completion pass)

## Session framing

This session **completed** a cycle already in flight, not a new one. The immediately
preceding Stage attempt left uncommitted, partially-applied corrections in the
working tree (`165-F`, `165.003-T`, `165.009-T`, `173-S`, the plan, the review, and
two new task files `165.011-T`/`165.012-T`). Those changes were inspected and
integrated rather than discarded, and the cycle was carried to a single commit.

No plan-review cycle was consumed. PR review-fix cycles are a separate counter from
the four completed plan-review cycles; plan-review cycle 4 remains the authorized
final plan-review.

## The two findings and how each was resolved

### Thread `PRRT_kwDORzpWpM6h3Tgb` — bootstrap executability (ACCEPTED)

The cycle-2/cycle-3 authorization named three forced `pre_claim` invocations
(U0/U1/U2) performed **by the Orchestrator and Ship**. No installed agent contract
can perform them. Re-verified by direct read this session, not inherited:

* `.github/agents/_orchestrator.agent.md` step 2a and `_ship.agent.md` step 3 invoke
  the gate with no `--force` and halt on exit 1/2 ("never inferred, never fail-open").
* The only agent-visible force provision anywhere is for `copilot-review`.
* `--force` is **stateless**: `_gate_pipeline_topology_command` converts exit 1 → 0
  *in-process* and appends an audit line; it persists no verdict, so an operator
  force does not change what an agent's own later unforced run computes.

Resolution splits the two things that were being conflated:

* **BOOTSTRAP-A** — the one-time, operator-run entry path that actually gets `173-S`
  claimed, using only currently executable mechanisms (the documented operator-only
  `--force` flag). B0/B1 from `main`, B2 from the shipment branch, each
  unforced-verify-then-force; B3 claim; B4 `post_claim` **unforced** (no force is
  authorized there); B5 a version-controlled evidence commit; B6 direct Ship
  invocation against an already-claimed shipment.
* **BOOTSTRAP-B** — the product behaviour `173-S` ships for *future* migrations:
  `165.011-T` (grant surface + full-provenance force audit) and `165.012-T`
  (Orchestrator/Ship consumption). Explicitly barred from authorizing `173-S`'s own
  claim, since neither is installed until `173-S` merges.

### Thread `PRRT_kwDORzpWpM6h3Tgi` — audit purity (ACCEPTED)

`audit_sequencing` was specified as writing nothing at all. That is false by
construction: `_emit_pipeline_topology_telemetry` runs unconditionally on every run
of every phase when telemetry is enabled. Narrowed to **no backlog mutation and no
migration-state/ledger write**, with the ordinary emission explicitly allowed,
observational, and fail-open. Tests must not assert zero filesystem writes.

## Two durable lessons

1. **A retraction is only complete when every coupled artifact carries it.** The
   partial pass corrected the shipment, the plan, and the review, but left the
   *feature* record (`165-F`) still asserting the retracted U0/U1/U2 grant as live
   authorization, and left the deliberation's D6/D3 sections unqualified. A feature
   record contradicting its own shipment record is a P1-class defect. Sweep the
   whole artifact set for the retracted *claim text*, not just the artifact the
   review thread was anchored to.

2. **Check-order short-circuiting makes "vantage" part of a force authorization.**
   `pre_claim` evaluates `branch_ownership` before `shipment_readiness` and
   short-circuits (`topology.py` L795–806), so a run from a Stage branch blocks on
   `BRANCH_MISMATCH` and never reaches `PREDECESSOR_NOT_SHIPPED`. The cycle-3
   conditions named the Stage branch as the required HEAD, which would have forced
   past a block the operator decision never authorized. Any force authorization
   bound to an exact token must also name the vantage from which that token is
   reachable.

## Corrections made this session beyond the partial pass

* `165-F`: BOOTSTRAP section rewritten (retraction + A/B split); absolute "gate owns
  NO write path" claim narrowed.
* `165.006-T` / `165.008-T`: body trailers updated for the two new edges.
* `165.009-T`: body edge recorded; new deliverable 8 (bootstrap grant documentation,
  which the plan required but no task carried); two further absolute no-write claims
  narrowed; size raised `S` → `M` because deliverable 8 pushed it toward the 2-hour
  bound.
* Deliberation raised to rev 5 with supersession banners on D6 and D3; historical
  analysis preserved verbatim rather than rewritten.
* BOOTSTRAP-A handoff precision: B6 now states the entry state to Ship explicitly,
  and the `expected_status` for Ship's step-6 reconcile check is **observed at B3
  and recorded at B5**, not assumed. The installed "Bootstrap exemption" clauses are
  explicitly ruled out — they apply only while the gate is *not installed*, and it
  is installed here.

## State at session end

* Branch `chore/stage-173-S`; one new non-amended commit. Nothing pushed; no PR API
  operation performed; no shipment claimed.
* `173-S` manifest: 11 items, `queued`. Review outcome 0 P0 / 0 P1; 2 P2 and 4 P3
  carried unchanged from cycle 4.
* P-001 preserved: only planning, backlog, and documentation artifacts were written.
  No source, test, template, or config file was modified.

## Next step (operator)

`173-S` is staging-PR ready. Entry is **BOOTSTRAP-A**, which is an operator act, not
a Ship act — Ship cannot enter this shipment on its own until `165.002-T` lands and
`173-S` passes natively as `declared_root`.
