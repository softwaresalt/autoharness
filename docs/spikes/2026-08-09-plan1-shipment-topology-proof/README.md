---
title: "Plan-1 Shipment Topology Proof — Executable Staging Evidence"
date: "2026-08-09"
description: "Stage-authored, disposable-fixture executable evidence proving the Plan-1 shipment topology redesign structurally eliminates the F14 cross-shipment orphaning defect against the real backlogit 1.8.0 ShipShipment engine. Planning evidence only — not product tooling, not CI-wired, not shipped."
doc_type: spike
status: complete
source: docs/spikes/2026-08-09-plan1-shipment-topology-proof/README.md
---

# Plan-1 Shipment Topology Proof — Executable Staging Evidence

## What this is

Two PowerShell proof harnesses produced by the **Stage** agent while gating the
Plan-1 decomposition for the Copilot CLI supervisor control-plane program
(features `118-F` / `119-F` / `120-F`, shipments `127-S` -> `128-S` -> `129-S`).

They exist to discharge a **P1 review finding (F14-R)** in
`docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md`, which
required the cross-shipment orphaning defect to be *structurally eliminated*
rather than mitigated by a forbidden post-close repair step.

## Role-boundary classification (P-010) — why these live under `docs/`

These files are **planning/verification evidence, not product implementation**.

Stage's role boundary permits creating deliberation/spike/plan/review artifacts
and committing them; it forbids writing product source, test, or config files.
The repository's `scripts/` directory is a **product and CI tooling surface** —
it holds the shipped `deploy-harness.ps1` / `deploy-harness.sh` installers and
`ci-topology-check.sh`, which is invoked directly by `.github/workflows/ci.yml`.
Its history consists exclusively of task-ID-tagged Ship execution commits.

Placing Stage-authored executables there would have added to the product/CI
surface under a Stage commit — a **P-010 role-boundary violation**. The evidence
was therefore *preserved and relocated* into this spike directory rather than
committed to `scripts/` or silently deleted. Nothing in CI, packaging
(`pyproject.toml`), or the deploy wrappers references these files, and moving
them changes no product behavior.

## Safety properties

* **Never mutates the live workspace.** Every closure assertion runs against
  throwaway backlogit workspaces created under `$env:TEMP`.
* `verify-plan1-shipment-topology.ps1` Part 1 issues **read-only** `SELECT`
  queries and `backlogit get` reads against the real `.backlogit` workspace.
* The real `ClaimShipment` / `ShipShipment` engine (backlogit **1.8.0**) is
  exercised — these are not mocks or re-implementations.

## The harnesses

### `sim-shipment-closure.ps1` — controlled two-arm experiment

| Arm | Topology | Purpose |
|---|---|---|
| **ARM A** (control) | Pre-redesign: one shared covering feature, task-only manifests | Demonstrates the defect is **real**, not theoretical |
| **ARM B** (redesign) | Per-shipment **root** covering feature, fully covered, explicit manifest member | Demonstrates the redesign **removes** it |

**Result: 60/60 assertions passed.** ARM A orphans 14/14 downstream tasks on the
first close. ARM B closes all three shipments with `returned_ids: []`, zero
`parent_id` clearing, zero cross-shipment cascade, and a clean terminal
`doctor`.

### `verify-plan1-shipment-topology.ps1` — live verification + isomorphic replay

Part 1 verifies the **live** workspace (V1–V11): covering-feature validity,
size/complexity enum validity and the 2-hour rule, `origin_feature` provenance,
root placement, full coverage, parent-first manifest ordering, umbrella
childlessness, cross-shipment reachability, DAG acyclicity, the 27 retained
task-level `blocks` edges, serial-chain eligibility, archival-not-deletion of the
superseded `124-S`/`125-S`/`126-S`, doctor cleanliness scoped to Plan-1
artifacts, and checkpoint integrity.

Part 2 rebuilds an **isomorphic copy of the exact live topology** — including the
real 27-edge dependency DAG — in `$env:TEMP` and closes all three shipments for
real.

**Result: 194/194 assertions passed**, `returned_ids: []` on every close, zero
non-archived residue in the terminal state.

## Reproducing

Requires `backlogit` 1.8.0 on `PATH`.

```powershell
pwsh docs/spikes/2026-08-09-plan1-shipment-topology-proof/sim-shipment-closure.ps1
pwsh docs/spikes/2026-08-09-plan1-shipment-topology-proof/verify-plan1-shipment-topology.ps1
```

`verify-plan1-shipment-topology.ps1` resolves the workspace under verification
from its own location (`$PSScriptRoot` ascended three levels), so it works in any
clone; pass `-Repo <path>` to verify a workspace elsewhere. It fails fast if no
`.backlogit` directory is found at the resolved root. The verification harness is
intentionally slow (it shells out to the CLI per assertion) and takes roughly
25 minutes.

Both harnesses exit non-zero on any failed assertion, and both treat a nonzero
`backlogit` exit code as fatal — a failed CLI call throws rather than being
captured as ordinary output, so a proof can never "pass" against a topology that
was never actually constructed.

## Harness hardening (post-cycle-3)

The closure simulation originally published **57/57**. Copilot review of this PR
raised three robustness defects, all fixed here; the total rose to **60/60**
solely because the fixes *added* assertions:

1. **Vacuous negative assertions.** The three `returned_ids` checks used
   `-notmatch '"returned_ids"\s*:\s*\[\s*"'`, which also passes when the field is
   absent, null, or renamed — so a green result could have proven nothing. They
   now parse the result and assert the property **exists** and has **zero
   elements** (+3 existence assertions, one per close).
2. **Swallowed CLI failures.** `Invoke-Bl` ignored `$LASTEXITCODE` in both
   harnesses. `$ErrorActionPreference = 'Stop'` does not make a native nonzero
   exit terminate, so a failed `dep add` / `link` / `claim` / `ship` would have
   been treated as ordinary output and the proof would have continued against a
   topology that was never built. Both now throw.
3. **Non-portable root.** The verifier hardcoded one developer's checkout path.
   It now derives the root from `$PSScriptRoot`, accepts `-Repo`, and fails fast
   when no `.backlogit` workspace is present.

The **60/60** and **194/194** totals published above are from the re-run *after*
this hardening; no total in this document predates it.

## Provenance

* Plan — `docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md`
* Hardening — `docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-hardening.md`
* Review (cycles 1-3 PASS; verdict now **BLOCKED** — 3 open P1s F16/F17/F18 raised post-budget by PR #325 Copilot review) —
  `docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md`
* Session memory — `docs/memory/2026-08-09-stage-copilot-supervisor-plan1-fasttrack.md`
