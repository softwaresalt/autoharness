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
* The real `ClaimShipment` / `ShipShipment` engine is exercised — these are not
  mocks or re-implementations. The simulation prints an `ENGINE UNDER TEST`
  block and **fails closed** if the version or commit cannot be resolved, so
  every result is **self-attributing**: it names the build that produced it
  rather than relying on a version string. Published runs were produced on
  `v1.8.0-dirty` / `fd8d2c9d` (2026-08-11) and reproduced on the clean release
  `v1.9.0` / `39528a4` (2026-08-12). Those are evidence labels, not required
  builds.

## The harnesses

### `sim-shipment-closure.ps1` — controlled two-arm experiment

| Arm | Topology | Purpose |
|---|---|---|
| **ARM A** (control) | Pre-redesign: one shared covering feature, task-only manifests | Demonstrates the defect is **real**, not theoretical |
| **ARM B** (redesign) | Per-shipment **root** covering feature, fully covered, explicit manifest member | Demonstrates the redesign **removes** it |

**Result: 66/66 assertions passed** (64 structural + 2 version-binding). ARM A orphans 14/14 downstream tasks on the
first close. ARM B closes all three shipments with `returned_ids: []`, zero
`parent_id` clearing, zero cross-shipment cascade, and a clean terminal
`doctor`.

### `verify-plan1-shipment-topology.ps1` — live verification + isomorphic replay

Part 1 verifies the **live** workspace (V1–V11): covering-feature validity,
size/complexity enum validity and the 2-hour rule, `origin_feature` provenance,
root placement, full coverage, parent-first manifest ordering, umbrella
childlessness, cross-shipment reachability, DAG acyclicity, the 30 current
task-level `blocks` edges (27 survived re-parenting; the 2026-08-11 rulings then
removed one and added four), serial-chain eligibility, archival-not-deletion of the
superseded `124-S`/`125-S`/`126-S`, doctor cleanliness scoped to Plan-1
artifacts, and checkpoint integrity.

Part 2 rebuilds an **isomorphic copy of the exact live topology** — including the
real 30-edge dependency DAG — in the system temp directory
(`[System.IO.Path]::GetTempPath()`, which is portable; `$env:TEMP` is not
guaranteed on POSIX) and closes all three shipments for real.

**Result: 221/221 assertions passed**, `returned_ids: []` on every close, zero
non-archived residue in the terminal state.

## Reproducing

Requires `backlogit` on `PATH`. The evidence published here was produced against
**`v1.8.0-dirty` / `fd8d2c9d`** and reproduced against the clean release
**`v1.9.0` / `39528a4`**; see *Version binding* below. Neither is a required
build — the harnesses self-attribute, so run them against whatever is installed
and read the identity they report.

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

## ⏳ Evidence scope caveat — F26 (P1, resolved 2026-08-11; operative once `118.007-T` lands)

**What this suite proves was contested — though nothing in it was ever wrong.**
Both harnesses exercise the **cascade** close operation `backlogit shipment ship`
and prove that under the fully-covered-root topology it returns
`returned_ids: []` with no post-close repair. The contest was never about the
assertions; it was that `.github/agents/_ship.agent.md` prohibits that operation
**unconditionally** under **P-015** ("NEVER the cascade
`backlogit_ship_shipment`"), with no fully-covered-root carve-out — so if
safe-close were the operative path, this evidence would concern **an operation
Ship will never call**.

This is worth naming precisely, because it is a failure mode that
assertion-hardening cannot reach: **not a vacuous assertion inside a proof, but a
rigorous proof of a proposition that may not be the operative one.** Only asking
*who will execute this, and what will they actually call?* surfaces it.

**Operator ruling 8 (accepted 2026-08-11) resolves it in this evidence's favour —
but not yet.** The ruling amends P-015 so the permitted close operation and the
executable evidence agree, via a machine-checkable *verified fully-covered-root*
exception, without requiring Ship to perform any P-010-forbidden operation. Once
that lands, the cascade **is** the operative close path and the totals below prove
a property of the command that will actually be called.

**Until then, read the totals below as cascade-close evidence specifically.** The
ruling settles what the contract will say; it does not by itself change the files
that bind Ship. The amendment is carried by **`118.007-T`**, a member of
**`127-S`** — the first shipment — so it lands before any close in the chain.
Until it completes, **safe-close governs**, and under safe-close this suite's
totals still do not speak to the operative path.

**The topology was unaffected throughout.** Under either close path the
fully-covered-root manifest is correct: the covering feature is itself a manifest
item and no unshipped siblings exist, so the protected set is empty. F14's
structural elimination stands. See
`docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md`.

## Expectation update — 2026-08-11 Cycle 18 (F30/F31/F32-F33): a NET-ZERO edge change, and two new structural blocks

The three final rulings produced the most easily-missed kind of topology change:
**the edge count did not move.** `120.005-T→120.004-T` was **removed** and
`120.004-T→120.005-T` **added** — still 30 edges, with the meaning of the graph
inverted. A count assertion would have passed unchanged. This is the second time
the **SET** form of the expectation has earned its keep, and the reason it must
never be relaxed to a count.

Why the reversal: F21 was a **reachability** defect, not a definition-ordering
one. `120.005-T` (approvals) depended on the orchestrator and had **zero reverse
dependencies**, so the runtime chain T15→T17→T18→T19 was fully satisfiable with
approvals never started — and the H2 fail-closed guarantee could be omitted from
the shipped runtime while every task passed. Ruling 2 had moved the approval
*types* upstream, which fixed F19 and created no caller.

Two blocks were added, both asserting **behaviour rather than text**:

* **V13 (F30)** implements the corrected P-015 close-path predicate
  **generically** — every feature member must be a root and fully covered,
  nothing outside those features and their children, whole-manifest
  qualification — and runs it against all three real manifests. Three **negative
  controls** confirm it still rejects partial coverage, a foreign member, and a
  manifest with no feature member. Without those, a predicate that admits
  everything would look identical to a correct one.
* **V14 (F32/F33)** asserts the approval service now has a reverse dependency,
  that `120.004-T` is among them, that the inverted edge is gone, and that
  approvals are **transitively reachable from the chain tail** `120.008-T`.
  **V14 would have failed before the reversal**, including at the moment the
  earlier PASS declared F21 resolved.

**A correction to this harness itself.** V3 previously exempted the literal id
`'117-F'` from its foreign-member check. That is an id-specific allowance for the
single most interesting case — precisely what F30 is about, and precisely what
`118.007-T` now forbids in policy, agent and skill. It is now **derived**: a
member outside the feature's scope is allowed only if it is itself a root feature
that is *positively verified childless*. If `117-F` ever gains a child, V3 starts
failing. Making that change meant discarding an in-flight verifier run and
restarting it; an evidence harness that special-cases the case it is meant to
prove is not evidence.

## Expectation update — 2026-08-11 ruling delta (27 → 30 edges, 5 → 7 S1 tasks)

The eleven accepted rulings changed the live topology, so the verifier's
hardcoded expectations had to change with it. **This is the dangerous kind of
edit** — an evidence script revised until it passes proves nothing — so the
change was made in the shape that preserves its detective power:

* The expectation remains an explicit **edge SET**, never a count. A count-only
  check would accept one valid edge swapped for another; the set does not.
* Each of the five deltas is enumerated **inline with the finding that caused
  it**: `119.004-T→119.003-T` **removed** (that edge *was* the F19 cycle — the
  bus defined an event type the state machine had to emit while depending back on
  it), and `119.004-T→118.003-T`, `120.005-T→118.003-T`,
  `120.006-T→118.006-T`, `118.006-T→118.005-T` **added** by rulings 2, 2, 7/9
  and 9 respectively.
* **The set check caught a stale expectation — on its own author.** The first
  corrected list said 29 edges and the run failed with
  `extra: 118.006-T->118.005-T`. The live graph was correct; the expectation had
  been built from a `backlogit query` issued **before** `backlogit sync`, so the
  index had not yet seen the `dependencies:` frontmatter written when
  `118.006-T` was created. A count-only check would have failed identically while
  naming nothing. Rebuild expectations from a **post-sync** query.
* The Part 2 fixture widened from **five to seven** S1 tasks, because the derived
  replay would otherwise throw on `118.006-T` having no fixture counterpart — the
  derivation is what keeps the replay isomorphic by construction.
* The `origin_feature` assertion became **conditional in both directions**. The
  nineteen re-parented tasks must still carry `117-F`; `118.006-T` and  `118.007-T` were created natively under `118-F` and must assert **no**
  provenance. Asserting it unconditionally would have demanded a *false*
  provenance record; deleting it would have stopped detecting provenance loss on
  the nineteen.

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

The **64/64** and **197/197** totals discussed in this section are the totals as
they stood at the close of that correction round; no total quoted in this
section predates it. They have since been superseded by the current published
figures — **66/66** (simulation) and **221/221** (verifier) — which rose again
when Cycle 18 added the V13/V14 blocks and the version-binding assertions. The
counts changed only because assertions were *added*; no assertion was weakened
or removed to make a total go up.

## Provenance

* Plan — `docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md`
* Hardening — `docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-hardening.md`
* Review (cycles 1-3 PASS for F1–F15; the fourteen post-budget P1s **F16–F29** raised by fifteen PR #325 Copilot reviews were dispositioned by **eleven accepted operator rulings** on 2026-08-11 and validated in Cycle 16. **CURRENT STATE 2026-08-11 (Cycle 19): verdict PASS, 0 P0 / 0 P1, and all three shipments GATE-CLEAR.** F30/F31/F32/F33 were dispositioned by three further rulings in Cycle 18, and **F34 — a defect in the F31 remediation itself — was dispositioned by a fourth ruling (guard/record separation: a stable never-deleted OS-locked guard file as the sole exclusion primitive, holder metadata in a separate removable record, `O_CREAT|O_EXCL` removed as a backend, a live holder preventing cleanup)** and applied to `118.005-T`/`118.006-T`/`120.006-T`. **SUPERSEDED STATEMENT, retained for audit:** an earlier revision of this bullet said "F27 is a second finding on the eligible cursor — `118.005-T` never requires ATOMIC lock acquisition — therefore passing evidence in this directory must not be read as clearance to claim `127-S`." F27 **is** now dispositioned (atomic, OS-backed acquisition is required, as narrowed by F34), so that blocking statement is **withdrawn**. The scope caveat that motivated it still stands on its own terms and is worth keeping: **these harnesses verify shipment/feature structure and close behaviour, not lock runtime**, so they neither prove nor disprove the locking contract. Gate-clear is also **not** an instruction to claim — claiming remains Ship's decision under Ship's own Role Boundary) —
  `docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md`
* Session memory — `docs/memory/2026-08-09-stage-copilot-supervisor-plan1-fasttrack.md`
* Close-path contract — `docs/compound/097-S-shipment-task-only-safe-close.md`,
  section "Reconciliation — the FULLY-COVERED ROOT exception". The task-only rule
  recorded there targets **partial-feature** shipments; this topology is the
  fully-covered-root case, which is why `127-S`/`128-S`/`129-S` intentionally
  list their covering features.

## Version binding (2026-08-11)

The operator asked whether backlogit had been upgraded, and whether any newer
close semantics invalidate this evidence. Both were checked directly rather than
inferred from the version number.

**backlogit was NOT upgraded at the time of the original run.** The MCP surface
and the CLI both reported commit `fd8d2c9d`. The CLI reported `v1.8.0-dirty`
built `2026-08-11T01:25:43Z`; the MCP daemon reported the same commit built
`2026-08-02T07:27:31Z` — two builds of one commit, not two versions. **UPDATED
2026-08-11 (F34 pass): the daemon was restarted onto the SAME build; both
surfaces reported `2026-08-11T01:25:43Z`. The two-builds caveat is RETIRED for
work from that point forward. It is retained here because it applied to the
earlier mutations, which remain trustworthy — the CLI independently read back
and validated every edge the MCP surface wrote.**

**UPDATED 2026-08-12 — the engine DID subsequently change, and this is exactly
why the guard is now dynamic.** The installed CLI was upgraded to the clean
release **`v1.9.0` / `39528a4`**, and both harnesses were re-run unmodified:
verifier **221/221**, simulation **66/66**. Two consequences:

* The `-dirty` caveat is **discharged** — the proof now also holds on a build
  whose exact behaviour is reproducible from a commit.
* During that session the long-lived MCP process still reported the pre-upgrade
  `v1.8.0-dirty` / `fd8d2c9d`, because it held that binary in memory. So "both
  surfaces report the same build" is a **historical** statement, not a standing
  one. This is a session artifact rather than a workspace defect — the artifacts
  are plain Markdown read identically by both builds, and every structural
  assertion cited was produced by the CLI-driven harnesses.

This episode is the concrete argument against exact-commit pinning: a guard
demanding `fd8d2c9d` would, by 2026-08-12, have **rejected the very engine that
reproduced these results**. Identities recorded here are evidence labels; the
close guard attests whatever is actually installed.

Three things are nevertheless recorded, because "not upgraded" is not the same
as "safe to assume forever":

* **The build is `-dirty`** — not reproducible from any commit. The simulation
  now surfaces this as an explicit `CAVEAT` line rather than letting the
  transcript imply a clean build. It is *not* treated as a failure: Stage cannot
  rebuild or reinstall the binary, so failing there would block on something
  this role cannot remediate.
* **The source is 128 commits ahead**, with heavy changes to the exact close
  surface these proofs exercise — `shipment_lifecycle.go` (+188),
  `dependencies.go` (+178), a **new** `shipment_gate_manifest.go` (+177), plus
  `shipment_covering.go`, `shipment_verify.go`, and `archive.go`. An update is
  advertised by the CLI, so an upgrade is one command away.
* **The F30 premise survives that unreleased work** — verified by reading it,
  not assumed. `DeriveCoveringFeature` still picks the first root feature in
  parent-first order and still tolerates an extra root, so `129-S`'s childless
  terminal umbrella (`117-F`) remains valid; the new strict variant is
  fail-closed only on lookup errors and is reachable solely from the opt-in
  formal-gate digest, which is disabled here.

Because the refactored engine was **not executed**, these totals were originally
attributed to `fd8d2c9d`; the 2026-08-12 re-run reproduced them on the clean
release `v1.9.0` / `39528a4`. Both identities are **evidence labels**, not
required builds. The Ship-facing guard is in
`docs/compound/097-S-shipment-task-only-safe-close.md`, and it is a **dynamic
engine attestation**, not an exact-commit pin: before closing, identify and
record the version/commit/build of every backlogit surface the close relies on,
require that identity to be determinable and coherent, re-run this simulation
unmodified against the installed engine, and proceed only on a passing run with
all structural assertions holding. Unknown identity, a CLI/MCP mismatch on a
relied-upon behaviour, or a simulation failure blocks close; a merely newer or
older build does not.
