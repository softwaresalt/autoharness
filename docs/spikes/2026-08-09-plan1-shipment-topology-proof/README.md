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
  throwaway backlogit workspaces created under the system temp directory
  (`[System.IO.Path]::GetTempPath()` — not `$env:TEMP`, which is not guaranteed
  to be set on POSIX).
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

**Result: 64/64 assertions passed.** ARM A orphans 14/14 downstream tasks on the
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
real 27-edge dependency DAG — in the system temp directory
(`[System.IO.Path]::GetTempPath()`, which is portable; `$env:TEMP` is not
guaranteed on POSIX) and closes all three shipments for real.

**Result: 197/197 assertions passed**, `returned_ids: []` on every close, zero
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

The closure simulation originally published **57/57** and the verifier
**194/194**. Successive Copilot reviews of this PR raised robustness defects
against the harnesses themselves — **including two that had made part of the
published claim inaccurate**. All are fixed here. The totals rose to **64/64**
and **197/197** solely because the fixes *added* assertions; the simulation
progressed 57 → 60 → 63 → 64 and the verifier 194 → 196 → 197, and **no** correction
changed observed engine behaviour.

**A real defect in the evidence, now corrected.** The Part 2 replay was described
as an "isomorphic replay of the exact live 27-edge DAG". It was not: the
hand-maintained index-based edge list carried a spurious `120.004-T -> 119.002-T`
edge that does **not** exist in the live graph — **28 replayed edges against 27
live**. The original V7 could not detect this because it only *counted* the live
edges; it never compared them to what Part 2 replayed. Fixed in two parts:

* V7 now asserts **set equality** between the live edge set and an explicit list
  of 27 expected endpoint pairs, reporting any missing/extra edge by name. A
  count-only check would still pass if one valid edge were swapped for another.
* Part 2 now **derives** its replay from that same verified list via an ID map,
  so the fixture cannot drift from what V7 proved. Drift is impossible by
  construction rather than by discipline.

The safety **conclusion** is unaffected — dependency edges play no part in
`ShipShipment`'s parent-clearing path, and the extra edge only made the replayed
graph strictly more constrained — but the *isomorphism claim* was wrong and is
now both corrected and enforced.

The remaining fixes:

1. **Vacuous emptiness assertions.** The three `returned_ids` checks used
   `-notmatch '"returned_ids"\s*:\s*\[\s*"'`, which also passes when the field is
   absent, null, or renamed — so a green result could have proven nothing. The
   first correction (assert the property **exists**, then count) was still
   insufficient, because `@($null).Count` is `0` and a null value would have
   passed. Both harnesses now require the field to be **present, non-null, and
   zero-length**.
2. **Swallowed CLI failures.** `Invoke-Bl` ignored `$LASTEXITCODE` in both
   harnesses. `$ErrorActionPreference = 'Stop'` does not make a native nonzero
   exit terminate, so a failed `dep add` / `link` / `claim` / `ship` would have
   been treated as ordinary output and the proof would have continued against a
   topology that was never built. Both now throw.
3. **Non-portable root.** The verifier hardcoded one developer's checkout path.
   It now derives the root from `$PSScriptRoot`, accepts `-Repo`, and fails fast
   when no `.backlogit` workspace is present.
4. **Non-portable temp directory.** Both harnesses used `$env:TEMP`, which is not
   guaranteed to be set on POSIX and would have broken the advertised
   cross-platform reproduction. Both now use
   `[System.IO.Path]::GetTempPath()`.
5. **One more swallowed native failure.** V10's proof that pre-existing backlog
   debt was left untouched piped `git --no-pager status` straight into a filter.
   `git` is a native call, so a nonzero exit would have produced empty output and
   the assertion would have passed **vacuously** ("no matches" read as
   "untouched"). It now captures the output, checks `$LASTEXITCODE`, and throws
   before filtering — the same contract `Invoke-Bl` applies to `backlogit`.
6. **A second, deeper defect in the very same V10 assertion.** Checking
   `git status` at all was the wrong instrument: it reports only *uncommitted*
   worktree changes, so on the committed HEAD that every published run executes
   against it returns nothing for those paths **whether or not this branch
   changed them**. The assertion would therefore have passed vacuously on any
   clean checkout — the `$LASTEXITCODE` fix above hardened a check that was
   measuring the wrong thing. V10 now computes the branch's actual footprint
   from `merge-base(<base ref>, HEAD)..HEAD` (see items 9-10) and **unions in** the worktree
   status so an uncommitted edit cannot slip past either. Verified: the branch
   touches 60 `.backlogit` files and **none** of the pre-existing flagged
   artifacts.
7. **A printed result masquerading as an asserted one.** The closure
   simulation *printed* `backlogit doctor` at the terminal fixture state without
   asserting it. `doctor` exits 0 while reporting findings — V10 depends on
   exactly that behaviour — so the advertised proof could have passed against a
   dirty fixture. Now asserted, matching what Part 2 of the verifier already
   did. This is the sole reason the simulation total is **64** rather than 63.

8. **A third assertion that tested the wrong proposition.** V4's message claimed
   to verify the umbrella's three `related_to` links, but the assertion projected
   only `target_id` and discarded `link_type` — so a link of **any** type,
   including the hierarchical or `blocks` edge this proof exists to rule out for
   `117-F`, would have satisfied it, and Part 2 would then have replayed a
   relationship the live topology does not have. V4 now filters on `link_type`
   **before** asserting the three targets, *and* separately asserts that the set
   of non-`related_to` outgoing links is empty, so a stray edge cannot hide
   behind a passing lookup.
9. **A hardcoded base ref defeated the advertised "any clone" reproduction.**
   The merge-base fix in item 6 resolved against `origin/main`, which is not
   guaranteed to exist in a source archive, a fork whose remote is not named
   `origin`, or a clone with pruned remote-tracking refs — V10 would `throw`
   before the topology proof ran. The base ref is now resolved as
   `origin/HEAD` → `origin/main` → `origin/master` → `main` → `master`, with an
   explicit `-BaseRef` override, failing only when **none** resolves.
10. **The first attempt at item 9 re-introduced the vacuity it was fixing —
    caught by running it.** That version tried the branch's **tracked upstream**
    first, on the reasoning that it is the most authoritative base. For a topic
    branch the tracked upstream is *the remote copy of the same branch*, so
    `merge-base(upstream, HEAD) == HEAD`, the diff range was empty, and the run
    reported a **0-file** branch footprint — passing while proving nothing, the
    exact defect item 6 existed to remove. `@{upstream}` is gone, and V10 now
    carries a **degeneracy guard**: if the resolved merge-base equals `HEAD`, the
    range cannot demonstrate anything and the harness `throw`s instead of
    reporting a vacuous pass. The guard makes the check safe under *any* base
    ref, including a bad `-BaseRef` supplied by an operator.

Items 6, 7, 8 and 10 are the same failure mode four times over: **an assertion
can be robust and still test the wrong proposition.** Adding `$LASTEXITCODE`
checks made these checks reliable at measuring something that was never the
claim. Item 10 is the sharpest instance, because it was introduced *by a fix for
an earlier instance of the same mistake* and was caught only by **reading the
numbers a passing run printed** rather than the PASS line. The durable lesson is
to state the proposition first, confirm the assertion would fail if it were
false, and treat a suspiciously empty measurement as failure rather than
success.

The **64/64** and **197/197** totals published above are from the re-run *after*
all of the above; no total in this document predates it.

## Provenance

* Plan — `docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md`
* Hardening — `docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-hardening.md`
* Review (cycles 1-3 PASS; verdict now **BLOCKED** — **8 open P1s F16–F23** raised post-budget by PR #325 Copilot reviews; F17 gates `127-S`, F18+F19+F22+F23 gate `128-S` with F22 possibly touching `127-S`, F16+F20+F21 gate `129-S`) —
  `docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md`
* Session memory — `docs/memory/2026-08-09-stage-copilot-supervisor-plan1-fasttrack.md`
* Close-path contract — `docs/compound/097-S-shipment-task-only-safe-close.md`,
  section "Reconciliation — the FULLY-COVERED ROOT exception". The task-only rule
  recorded there targets **partial-feature** shipments; this topology is the
  fully-covered-root case, which is why `127-S`/`128-S`/`129-S` intentionally
  list their covering features.
