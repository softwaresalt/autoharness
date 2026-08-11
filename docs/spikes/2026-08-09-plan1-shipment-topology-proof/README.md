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

## ⛔ Evidence scope caveat — F26 (P1, OPEN)

**What this suite proves is contested, though nothing in it is wrong.** Both
harnesses exercise the **cascade** close operation `backlogit shipment ship`, and
prove that under the fully-covered-root topology it returns `returned_ids: []`
with no post-close repair. But `.github/agents/_ship.agent.md` prohibits that
operation **unconditionally** under **P-015** ("NEVER the cascade
`backlogit_ship_shipment`"), with no fully-covered-root carve-out — so if
`shipment-reconcile` safe-close is the operative close path, **this evidence
concerns an operation Ship will never call.**

The proposition that would then matter is different: that archiving each manifest
item in turn, with an **empty protected set**, leaves the backlog consistent.

This is worth naming precisely, because every assertion below is sound and the
run is green: it is **not a vacuous assertion inside a proof, but a rigorous proof
of a proposition that may not be the operative one**. No amount of
assertion-hardening catches that — only asking *who will execute this, and what
will they actually call?*

**The topology is unaffected either way**: under safe-close the fully-covered-root
manifest is still correct, since the covering feature is itself a manifest item
and no unshipped siblings exist, so the protected set is empty. F14's structural
elimination stands. Pending the operator's F26 ruling, read the totals below as
**cascade-close** evidence specifically. See
`docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md`.

## Harness hardening (post-cycle-3)

The closure simulation originally published **57/57** and the verifier
**194/194**. Successive Copilot reviews of this PR raised robustness defects
against the harnesses themselves — **including two that had made part of the
published claim inaccurate** — and one review found a **destructive** fixture-setup
hazard. All are fixed here. The totals rose to **64/64**
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

11. **The fixture setup could have destroyed an unrelated workspace.** Both
    harnesses built their temp fixture path from the **first 8 hex characters**
    of a GUID — 32 bits — and the simulation then ran
    `Remove-Item -Recurse -Force` on it "to be safe". On a collision with a
    stale or **concurrent** fixture that recursive delete would have destroyed
    someone else's workspace *before the proof started*. `New-Item -Force` was
    the mirror-image hazard: it silently **reuses** an existing directory, so a
    collision would have replayed the topology into a polluted fixture and
    proven nothing. Both now use the **full 128-bit GUID**, create the directory
    without `-Force`, and **throw** if the path somehow already exists — at 128
    bits that signals a real problem rather than noise. A destructive
    pre-emptive delete has no place in setup code that runs outside a workspace
    it owns.

12. **`Invoke-Sql` could not tell "zero rows" from "unparsed output".** It
    returned `@()` whenever the captured output contained no `[` marker, so a
    format change, a truncated read or an unexpected banner would have been
    indistinguishable from an empty result set. That is precisely the wrong
    default here, because several of the **strongest** proofs in this suite are
    **zero-result** proofs — V8's "`127-S` has no dependencies", V9's "no stale
    `117.x` tasks", V4's "`117-F` has no children". Every one of them would have
    passed **vacuously** the moment the query stopped reporting.

    **The first fix for this was itself wrong, and running it is what proved
    it.** Making the absence of a `[` marker throw seemed obviously correct —
    and it immediately failed V4, a proof that had been passing for twelve
    review cycles. The cause was not a regression: **backlogit emits the literal
    JSON token `null` for a zero-row query, never `[]`.** So the strict guard had
    replaced one conflation with another, treating a *legitimate* empty result as
    a harness failure. The shipped version distinguishes all three cases: `null`
    is a genuine zero-row result and is accepted, a `[` array is parsed, and
    **anything else throws**. The check is also now an *exact* payload match with
    log lines stripped, rather than a substring search for a bracket — substring
    matching is how the original vacuity got in, since it accepted any output
    containing a bracket anywhere.

    This is the **second** time a fix for this family introduced a new defect
    (item 10 was the first). Both were caught the same way: by **running the fix
    and reading what it actually reported** rather than trusting that the
    reasoning behind it was sound. A guard that has never been observed to fire
    correctly on a real empty result is an untested guard.

Items 6, 7, 8, 10 and 12 are the same failure mode five times over: **an assertion
can be robust and still test the wrong proposition.** Adding `$LASTEXITCODE`
checks made these checks reliable at measuring something that was never the
claim. Item 10 is the sharpest instance, because it was introduced *by a fix for
an earlier instance of the same mistake* and was caught only by **reading the
numbers a passing run printed** rather than the PASS line. Item 12 shows the
family has a **signature**: every instance turns a failure to *observe* into the
observation "nothing was there" — and it also shows the correction has a
symmetric failure mode, since over-strictness turns a real empty result into a
phantom failure. The fix is never "be stricter"; it is **enumerate the outcomes
the tool can actually produce and handle each explicitly**. The durable lesson is
to state the proposition first, confirm the assertion would fail if it were
false, and treat a suspiciously empty measurement as failure rather than
success.

The **64/64** and **197/197** totals published above are from the re-run *after*
all of the above; no total in this document predates it.

## Provenance

* Plan — `docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md`
* Hardening — `docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-hardening.md`
* Review (cycles 1-3 PASS; verdict now **BLOCKED** — **11 open P1s F16–F26** raised post-budget by PR #325 Copilot reviews; F17 gates `127-S`, F18+F19+F22+F23+F24 gate `128-S` with F22 possibly touching `127-S`, F16+F20+F21+F25 gate `129-S`, and **F26 gates all three**) —
  `docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md`
* Session memory — `docs/memory/2026-08-09-stage-copilot-supervisor-plan1-fasttrack.md`
* Close-path contract — `docs/compound/097-S-shipment-task-only-safe-close.md`,
  section "Reconciliation — the FULLY-COVERED ROOT exception". The task-only rule
  recorded there targets **partial-feature** shipments; this topology is the
  fully-covered-root case, which is why `127-S`/`128-S`/`129-S` intentionally
  list their covering features.
