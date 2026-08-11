---
session_id: stage-2026-08-09-plan1-copilot-supervisor-fasttrack
agent: stage
date: 2026-08-09
branch: chore/spike-unified-surfaces-20260809
pr: 325
tracker: 34D50F2D
supersedes: docs/memory/2026-08-09-stage-34d50f2d-candidate-a-composability-spike.md
status: complete
---

# Stage session memory — Plan 1 fast-track (local Copilot CLI supervisor / control plane)

## Operator product decision (authoritative)

The operator issued a new authoritative product decision extending the completed
`34D50F2D` candidate-(a) composability spike and open PR #325:

1. **FAST-TRACK Plan 1** — autoharness becomes a **local Copilot CLI supervisor /
   control-plane runtime** for long-horizon workloads, preserving Copilot CLI as the
   reasoning/agent execution engine. All local runtime components are in scope;
   everything Gradio / devtunnel / remote UI / remote control / remote authentication /
   remote approvals / browser terminal streaming / remote services is **excluded**.
2. **DEFER Plan 2** — Gradio + Microsoft devtunnel + remote-control services move to a
   later autoharness version with their own design/operational plan and tracking item,
   and **no implementation feature, tasks, or shipment now**.

## The bright line that resolved the spike

> **Supervising an external agent runtime is IN SCOPE.
> Implementing a new agent runtime is OUT OF SCOPE.**

The original spike returned `CONDITIONAL PROCEED` against spec §3 read as an
**in-process action/observation execution engine**. That reading **remains NO-GO** and
was not overturned — it was *narrowed*. Supervising an external Copilot child process is
a different activity, and it is exactly the "consolidation of logic that already exists"
condition the spike attached: `start.ps1` / `start.sh` already perform bootstrap, sidecar
preflight, resolution, and launch. Plan 1 consolidates duplicated policy rather than
inventing a new capability. Disposition reconciled to **PROCEED** under the clarified
scope.

### Two corrections PR #325 required

1. **MCP parity is NOT recommended.** A native autoharness MCP server remains an
   **explicit non-goal** absent a concrete consumer.
2. **Process-supervision scope is NOT wholly rejected.** The NO-GO narrows to a model
   reasoning loop, sequential model pipelining, and stderr-to-model routing.

### Evidence preserved verbatim (must not regress)

* **10 top-level commands / 17 executable leaf command paths** (`main()` at
  `cli.py:2253`); 7 ungrouped leaves + `gate` 5 + `telemetry` 3 + `eval` 2 = 17. The
  retracted "11 commands" figure is **not** reinstated.
* **Three distinct MCP vocabularies**: (a) server-framework **absence** in `src/`
  (no MCP SDK; zero `FastMCP` / `mcp.server` / `stdio_server` / `@mcp.` / `Server(`
  hits) — the supported narrow claim; (b) registry-validation vocabulary for *external*
  tools (`verify_workspace.py`, 31 occurrences, `OP_CREATE_MCP`..`OP_RESOLVE_CHECKPOINT_MCP`
  at `:140-159`); (c) telemetry vocabulary (`tool_event.py:35`, `TOOL_SURFACES` contains
  `'mcp'`, 1 occurrence; sole emission site hardcodes `tool_surface='cli'` at
  `cli.py:789`).

## Plan 1 — artifacts and gates

| Artifact | Path | Verdict |
|---|---|---|
| Implementation plan | `docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md` | authored |
| P-006 hardening | `docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-hardening.md` | **HARDENED** (H1–H10) |
| Plan review gate | `docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md` | **PASS**, 0 P0 / 0 P1 outstanding, **2 of 3 cycles** (cycle 2 = 2026-08-10 PR #325 review-fix, F13/F14) |

Hardening themes: H1 characterize-before-migrate (hard ordering constraint), H2
fail-closed invariant table, H3 exit-status fidelity, H4 subprocess safety (argv-array
only, no `shell=True`), H5 single redaction choke point, H6 authority containment, H7
anti-drift (no bind/listen, web/tunnel import ban), H8 per-task de-risking for the four
riskiest tasks, H9 backward-compatibility contract, H10 shipment gating.

## Architecture decided

New package `src/autoharness/supervise/`: `result.py`, `errors.py`, `redact.py`,
`locking.py`, `process.py` (ChildProcess Protocol + PipeChildProcess default),
`process_pty.py` (ConPTY / POSIX, optional `pywinpty` extra, degrade-to-pipe),
`session.py`, `events.py`, `journal.py`, `recovery.py`, `bootstrap.py`, `sidecar.py`,
`resolve.py`, `approvals.py`, `app.py` (`run_session()` — the **only** orchestrator).
The sole adapter is `autoharness run` in `cli.py`; `start.ps1` / `start.sh` become thin
compatibility shims with **no surviving policy duplication**. Base install stays stdlib +
existing `jsonschema` / `PyYAML`.

**Session state machine:**
`INIT → LOCKING → BOOTSTRAPPING → PREFLIGHT → RESOLVING → LAUNCHING → RUNNING →
{CANCELLING | RESTARTING | DRAINING} → {EXITED | FAILED | REFUSED}`.
`REFUSED` (lock contention) is a distinct terminal state from `FAILED`; `DRAINING` is the
only path from `RUNNING` to a terminal state.

**Language decision:** Python-first, **no Python+Go split now**. Process-supervisor
interfaces stay replaceable; Go is reevaluated only if a future persistent multi-workspace
daemon requires it.

**Authority boundaries (unchanged):** Engram is a read-only memory sidecar with no
authority; backlogit is the sole owner of backlog items and agent checkpoints (the
supervisor session journal is gitignored local operational state and is **never** a
checkpoint); graphtor owns docs retrieval; autoharness owns lifecycle/policy/supervision
only; `.autoharness/config.yaml` remains the model-routing authority.

## Harvested backlog (Plan 1 only)

> **CYCLE-3 REDESIGN (2026-08-10).** The IDs in this section were remapped by the
> F14 structural fix. `117-F` is now a **childless product umbrella**; the 19
> tasks live under three new ROOT covering features. See the cycle-3 section at
> the end of this document for the full remap table and rationale. The original
> IDs are retained below for provenance and are annotated inline.

**Product umbrella `117-F`** — "Local Copilot CLI supervisor / control-plane runtime
(Plan 1, fast-track)". Originally the direct parent of 19 width-isolated sub-2h tasks
`117.001-T`…`117.019-T`; **now childless**, grouped to the per-shipment features by
`related_to` links. Each task carries **two independent axes** (`size` + `complexity`)
as structured fields *and* as labeled prose, plus **27 `blocks` dependency edges**
(all preserved across the remap).

**Serial shipment chain (only the first is eligible):**

| Order | ID | Covering feature (ROOT) | Scope | Priority | Items |
|---|---|---|---|---|---|
| 1 (cursor) | `127-S` | `118-F` | S1 safety contracts + characterization baseline — zero behavior change | critical (P0) | `118-F` (first), `118.003-T`, `118.001-T`, `118.002-T`, `118.004-T`, `118.005-T` |
| 2 | `128-S` | `119-F` | S2 supervision core — unwired library | critical (P0) | `119-F` (first), `119.001-T`…`119.006-T` |
| 3 | `129-S` | `120-F` | S3 application services, adapters, `start.ps1`/`start.sh` migration — the only behavior-changing shipment | high (P1) | `120-F` (first), `120.001-T`…`120.008-T`, `117-F` (last) |

`128-S` **blocks-on** `127-S`; `129-S` **blocks-on** `128-S`. Ordering deliberately
front-loads process safety, typed contracts, and characterization tests **before** any
adapter or convenience surface.

*(Superseded: `124-S`/`125-S`/`126-S` — archived, not deleted, with `supersedes` links
from their replacements.)*

**Each manifest is fully covered and root-isolated (H10.5, supersedes H10.4).** Every
shipment lists its own ROOT covering feature **first**, plus exactly that feature's
children. Full coverage means no `parent_id` is ever cleared on close; ROOT placement
means no close can reach a sibling shipment's scope. `117-F` is childless and appears
only in the final shipment, where the engine closes it natively. **No close requires
`adopt_item` or any post-close repair.**

### Task ↔ plan map (cycle-3 IDs; `origin_feature: 117-F` retained on every task)

> Column **Old ID** is the pre-cycle-3 identifier, kept for cross-referencing PR #325
> and the archived `124-S`/`125-S`/`126-S` manifests.

| Plan | ID (current) | Old ID | Focus | Shipment | Size | Complexity |
|---|---|---|---|---|---|---|
| T1 | `118.001-T` | `117.001-T` | `start.ps1` characterization suite | S1 | M | medium |
| T3 | `118.003-T` | `117.002-T` | `result.py` + `errors.py` contracts | S1 | S | low |
| T2 | `118.002-T` | `117.003-T` | `start.sh` characterization suite | S1 | S | low |
| T5 | `118.005-T` | `117.004-T` | `locking.py` | S1 | M | medium |
| T4 | `118.004-T` | `117.005-T` | `redact.py` | S1 | S | medium |
| T6 | `119.001-T` | `117.006-T` | `process.py` Protocol + Pipe backend | S2 | M | medium |
| T7 | `119.002-T` | `117.007-T` | `process_pty.py` ConPTY/POSIX | S2 | M | high |
| T8 | `119.003-T` | `117.008-T` | `session.py` state machine | S2 | M | medium |
| T9 | `119.004-T` | `117.009-T` | `events.py` event bus | S2 | S | low |
| T10 | `119.005-T` | `117.010-T` | `journal.py` | S2 | M | medium |
| T11 | `119.006-T` | `117.011-T` | `recovery.py` | S2 | M | high |
| T12 | `120.001-T` | `117.012-T` | `bootstrap.py` | S3 | M | medium |
| T13 | `120.002-T` | `117.013-T` | `sidecar.py` | S3 | M | medium |
| T14 | `120.003-T` | `117.014-T` | `resolve.py` | S3 | S | low |
| T15 | `120.004-T` | `117.015-T` | `app.py` `run_session()` | S3 | M | high |
| T16 | `120.005-T` | `117.016-T` | `approvals.py` (console-only) | S3 | M | medium |
| T17 | `120.006-T` | `117.017-T` | `autoharness run` CLI adapter | S3 | S | medium |
| T18 | `120.007-T` | `117.018-T` | `start.ps1`/`start.sh` → shims | S3 | M | high |
| T19 | `120.008-T` | `117.019-T` | observability + rollout/rollback docs | S3 | S | low |

## Plan 2 — deferred

* Design doc: `docs/design-docs/2026-08-09-deferred-gradio-devtunnel-remote-control-plan.md`
  (remote threat model with 6 assets / 6 adversary classes / T1–T11 threats, incl. T11
  credential compromise; Entra ID
  authentication; 4-tier authorization with a local-only privileged tier; cryptographic
  workspace binding; two-channel streaming/control protocol; remote approvals; devtunnel
  lifecycle with crash-safe teardown; multi-user/session concerns; optional-extra
  deployment; rollback plus the §11.1 credential-compromise runbook; 7 open questions).
* Dedicated living tracker: **stash `04AFF97B`** (kind `feature`, priority `low`, marked
  DEFERRED).
* **No implementation feature, tasks, or shipment exist**, and Plan 2 is **not** a Plan 1
  dependency and must not be added to Plan 1's dependency graph or shipment chain.

## Candidate (c) boundary

Background **Verification & Compaction** remains a later, distinct, unselected capability
and is the reason `34D50F2D` **stays ACTIVE**. Plan 1 exposes the typed event bus
(`117.009-T`) and session journal (`117.010-T`) as hook surfaces a future candidate-(c)
layer could consume, but Plan 1 must not silently implement candidate (c) and must not
make Engram authoritative — enforced as H7 anti-drift with a test asserting `supervise/`
opens no socket, binds no port, and imports no web/tunnel framework.

## Non-goals reaffirmed

* Native autoharness MCP server (explicit non-goal absent a concrete consumer).
* Any model action/observation reasoning loop, model pipelining, or stderr-to-model routing.
* Any remote surface, socket, port, tunnel, or web framework in `supervise/`.
* Daemon, database, or framework overreach; no Python+Go split.
* Candidate (c) implementation.

## Decisions worth carrying forward

* Characterize-before-migrate is a **hard ordering constraint**, not a preference: the
  characterization suites are re-run byte-identical by `117.018-T`, and any required
  assertion change escalates as an operator product decision.
* Exit-status fidelity is a hard invariant across the pipe backend, the PTY backend, the
  orchestrator, the CLI adapter, and both shims.
* The restart budget defaults to **0** so the default path is simply cancel-and-drain;
  the complex restart path is opt-in and separately testable.
* PTY is opt-in and degrades to pipe with a recorded warning — never a silent
  substitution, never a hard failure.

## Session boundaries

Stage-scoped planning only: **no** source/template/schema/config implementation, **no**
branch or worktree creation, **no** commit/push/PR mutation, **no** shipment claim, and
**no** Ship execution. All changes are left **uncommitted** for the Orchestrator.

## Next steps for Ship

1. Claim `127-S` (S1) — the only eligible cursor. `128-S` and `129-S` are blocked.
2. Honor H1: land the characterization suites before any policy moves to Python.
3. Do not begin S3 migration until S1 and S2 are released.
4. **No post-close backlog repair is required or permitted.** Each shipment closes
   cleanly on its own fully covered ROOT feature; `returnUnreleasedFeatureItems`
   returns `∅` on every close (proven, `returned_ids: []`). Do **not** call
   `adopt_item`, re-parent tasks, reactivate a feature, or hand-edit parentage —
   those are outside Ship's Role Boundary (P-010) and are banned by Non-Goal 11.
   If a close *does* return a non-empty `returned_ids`, that is a regression:
   **halt and escalate to Stage** rather than repairing it.
5. **Do not add or remove members from any manifest.** Each shipment's manifest is
   a safety contract (H10.5): exactly its own ROOT covering feature listed first
   plus that feature's children. Adding a foreign item, or nesting the covering
   features under `117-F`, reinstates the cascade hazard.
6. `117-F` is a **childless umbrella** and is already a member of the final
   shipment `129-S`. The engine closes and archives it at `129-S` close — no
   separate closing action is needed.

---

## Review-fix cycle — 2026-08-10 (PR #325 Copilot findings)

Bounded Stage planning review-fix cycle. No source implementation, no shipment claim,
no branch/worktree, no commit/push, no PR thread mutation.

### Finding 1 (critical, shipment safety) — RESOLVED

`124-S` listed the covering feature `117-F` in `custom_fields.items` alongside the five
S1 tasks.

**Why it was critical.** Backlogit `ShipShipment` (v1.8.0, `fd8d2c9d`) gates both of its
destructive covering-feature operations on **explicit manifest membership**:

* `setArtifactStatus(featureID, done)` fires only when `explicitScope[featureID]`.
* `collectArchiveCandidateIDs` sweeps the feature — plus its descendants and its linked
  deliberations — into the archive set only when `explicitScope[featureID]`.

So closing S1 would have marked `117-F` **done and archived it** while 14 of its 19
children (`117.006-T`…`117.019-T`) were still queued in `125-S`/`126-S`.

**Correction.** `117-F` removed from the `124-S` manifest. There is **no**
remove-from-shipment operation in backlogit (`shipment` exposes only `add`, `claim`,
`get`, `list`, `return-blocked`, `ship`; `return-blocked` would have wrongly forced a
`blocked` status), so the minimum safe correction was a direct frontmatter edit followed
by `backlogit sync`. No IDs, statuses, priorities, dependencies, or queue positions were
recreated or changed. An append-only `manifest_corrected` event was added to
`.backlogit/logs/124-S.jsonl`.

**Accepted trade-off.** Backlogit derives the read-only `covering_feature` render
projection from a *root feature member*, so it is now omitted for `124-S` — uniform with
`125-S`/`126-S`, which were always task-only. Lifecycle correctness outranks a render
convenience; the feature link stays recoverable from member `parent_id` and the shared
`117.` ID prefix.

**Residual (F14, P1, accepted with mandatory mitigation).**
`returnUnreleasedFeatureItems` is **not** gated by `explicitScope` and clears `parent_id`
on a non-member ancestor feature's unreleased descendants — see "Next steps for Ship"
step 4. Recoverable relationship change only: no closure, no archival, no data loss.
Recorded for a separate upstream backlogit report.

### Finding 2 (deferred remote threat model) — RESOLVED

`docs/design-docs/2026-08-09-deferred-gradio-devtunnel-remote-control-plan.md` advised
that an exposed credential be "rotated (`gh auth refresh`)". That is wrong:
`gh auth refresh` re-authorizes scopes on the **same** credential and leaves an exposed
secret fully valid.

Replaced with threat **T11** and a new **§11.1 credential-compromise runbook** requiring
issuer-side **revocation** plus **replacement** with a newly issued least-privilege
credential; `gh auth refresh` is explicitly confined to scope/authorization changes on a
credential that is *not* compromised. **Containment outranks preserving in-flight work**:
a controlled supervisor session restart is explicitly permitted and, where the old value
is still resident in a live process environment, required — and the document's general
"rollback must never terminate in-flight agent work" guarantee is explicitly suspended
for this path. Asset table, T11, rollback, runbook, and the Plan 2 stash tracker
(`04AFF97B`) are reconciled.

### Gate results

* **plan-review: PASS re-affirmed** — 0 unresolved P0, 0 unresolved P1.
  Cycles used **2 of 3** (truthful; cycle 1 = F1–F12 on 2026-08-09, cycle 2 = F13/F14 on
  2026-08-10). One cycle remains.
* **plan-harden: HARDENED re-affirmed** — H10.4 added; H1–H9 re-read and unaffected. The
  correction is fail-safe in direction: it *removes* a destructive capability from the S1
  close path rather than adding a new mechanism that must itself be trusted.

---

## Review-fix cycle 3 of 3 — 2026-08-10 (F14 structural elimination)

FINAL permitted review-fix cycle. Bounded Stage planning work only: no source
implementation, no shipment claim, no branch/worktree, no commit/push, no PR or thread
activity. All changes left uncommitted for the Orchestrator.

### Why cycle 2's F14 resolution was rejected

Cycle 2 discharged F14 (P1) by requiring Ship to re-adopt orphaned tasks via
`backlogit_adopt_item` after each predecessor close. That is invalid on two independent
grounds:

1. **P-010 role-boundary violation.** Ship's Role Boundary enumerates claim, move, close,
   and archive. Re-parent/adopt is not enumerated; the fail-closed rule makes it
   *forbidden*, not merely undocumented. A review cannot clear a P1 by prescribing a
   policy violation.
2. **Not reliability-first.** It mandates fragile manual repair after every close, on the
   exact path where one missed step silently detaches two thirds of the program.

So the cycle-2 "0 unresolved P1" claim was not truthful. F14 was reopened as **F14-R** and
eliminated structurally.

### The engine defect, precisely

`ShipShipment` builds `releaseScope` = manifest members + all their descendants, and
`featureScopeRoots` = every ancestor feature reachable by walking `parent_id` **upward**
from the members. It then runs `returnUnreleasedFeatureItems` for **every** feature in
that set — **member or not** — forcing each out-of-scope descendant to `queued` and
calling `clearParentID`.

The `explicitScope` gate added by backlogit `133-F` covers `setArtifactStatus(done)` and
`collectArchiveCandidateIDs`, but **not** this path. So the cycle-2 task-only design
disarmed the archive cascade and *armed* the parent-clearing cascade.

Two further engine properties were decisive:

* `featureScopeRoots` walks `parent_id` **only** — it does **not** traverse `item_links`.
  Semantic links therefore carry zero lifecycle reachability.
* `findCrossArtifactReferences` (used by `AdoptItem`) rewrites `parent_id`,
  `dependencies`, and `links`, but **not** shipment `custom_fields.items` — and backlogit
  1.8.0 exposes no remove-from-shipment operation. Manifests are effectively immutable,
  which is why the shipments had to be replaced rather than edited (finding F15).

### The fix — H10.5 (supersedes H10.4)

Two invariants, both required, neither sufficient alone:

1. **FULL COVERAGE** — every descendant of a shipment's covering feature is in that same
   shipment's release scope ⇒ `returnUnreleasedFeatureItems` returns `∅` ⇒ nothing is
   ever orphaned.
2. **ROOT PLACEMENT** — the covering feature has no parent ⇒ the upward walk cannot
   escape into a sibling shipment's scope.

**Trap avoided:** nesting `118-F`/`119-F`/`120-F` under `117-F` satisfies (1) but breaks
(2) — closing S1 would walk `118.001-T → 118-F → 117-F` and orphan *everything* under
`119-F` and `120-F`, strictly worse than the original defect. The per-shipment features
**must stay root-level**.

**Membership reversed on purpose.** Because each feature is fully covered, listing it in
its own manifest is *safer* than omitting it: the engine marks it done and archives it
with its own tasks. Omitting it would leave a permanently-`queued` feature with all
children done, requiring a manual archive — i.e. the post-close repair this cycle forbids.

**Grouping preserved without lifecycle coupling.** `117-F` becomes a **childless**
umbrella linked by `related_to` to the three per-shipment features. Childless ⇒
`descendantItems(117-F)` is empty ⇒ it is inert even when in scope. It is a member of the
final shipment `129-S` only, listed **last** so `120-F` wins the read-only
`covering_feature` render projection; the engine closes and archives it there — native
program closure, zero operator action.

### Evidence (real backlogit 1.8.0, disposable fixtures)

* `docs/spikes/2026-08-09-plan1-shipment-topology-proof/sim-shipment-closure.ps1` — **64/64**. ARM A (cycle-2 control) reproduces the
  defect: closing S1 returns **14/14** downstream tasks with `parent_id` cleared. ARM B
  (H10.5) closes all three shipments with `returned_ids: []` and a clean fixture doctor.
* `docs/spikes/2026-08-09-plan1-shipment-topology-proof/verify-plan1-shipment-topology.ps1` — **197/197**. Part 1 = 11 read-only
  structural checks against the live workspace; Part 2 = fixture replay of the **exact**
  live topology including the real 27-edge DAG, driven through real `ShipShipment`:
  `returned_ids: []` on every close, zero non-archived residue at the end.

Both harnesses were **re-executed on the final corrected tree** immediately before
push and reproduced their published totals exactly (63/63 and 196/196 — the
cycle-4 figures; see Cycle 6 for the progression to the current 64/64) — the
evidence in this document is verified, not merely asserted from an earlier run.

**Harness hardening (post-cycle-3, in response to Copilot robustness findings).**
The closure simulation originally published **57/57**. Three defects were fixed
and the harnesses re-run green; the total rose to **63/63** (the cycle-4 figure;
now **64/64**, see Cycle 6) purely because the
fixes *added* assertions, not because behaviour changed:

1. The three `returned_ids` checks were negative regexes (`-notmatch '"returned_ids"\s*:\s*\[\s*"'`).
   Those also "pass" when the field is **absent, null, or renamed** — i.e. they
   could have proven nothing. Replaced with a parse-and-assert helper that
   requires the property to **exist** and to have **zero elements**. This is the
   source of the +3 assertions (one existence check per shipment close).
2. `Invoke-Bl` in **both** harnesses ignored `$LASTEXITCODE`. `$ErrorActionPreference = 'Stop'`
   does **not** make a native nonzero exit terminate, so a failed `dep add` /
   `link` / `claim` / `ship` would have been captured as ordinary output and the
   proof would have continued against a topology that was never constructed.
   Both now throw on nonzero exit.
3. `verify-plan1-shipment-topology.ps1` hardcoded `$repo = 'C:\Source\GitHub\autoharness'`.
   It now resolves the root from `$PSScriptRoot` (with a `-Repo` override and a
   fail-fast `.backlogit` existence check), so the published proof is
   reproducible in any clone.

Both totals above (**64/64**, **196/196**) are from the re-run **after** this
hardening — no total in this document is carried over from a pre-hardening run.

**Evidence placement — P-010 role-boundary adjudication.** The two harnesses were
originally written to `scripts/`. That directory is a **product and CI tooling
surface**: it holds the shipped `deploy-harness.ps1` / `deploy-harness.sh`
installers and `ci-topology-check.sh`, which `.github/workflows/ci.yml:135`
invokes directly, and its history is exclusively task-ID-tagged Ship execution
commits. Committing Stage-authored executables there would have extended the
product/CI surface under a Stage commit — a P-010 violation. The evidence was
therefore **relocated, not deleted**, to
`docs/spikes/2026-08-09-plan1-shipment-topology-proof/` (with a README recording
provenance, safety properties, and reproduction steps), and all references in the
plan, hardening, review, and memory documents were repointed. `scripts/` is
restored bit-for-bit to its committed state; nothing in CI, `pyproject.toml`
packaging, or the deploy wrappers referenced the moved files, so the relocation
changes no product behavior. Consequently this PR remains **docs + backlog only
and non-code-changing**, and the code-changing build gate is not triggered.

Three first-pass FAILs were adjudicated as probe defects, not product defects:
`get --format json` does not project `size`/`complexity` (read the `items` table instead);
a regex over `checkpoint list` false-positives on both `resume_hint` prose and the summary
field name `"quarantined": 0` (assert structured fields instead); and a loose `\b003[-.]`
pattern matches task filenames like `118.003-T.md`. `backlogit doctor` reports **zero**
findings against any Plan-1 artifact; the 62 remaining findings are pre-existing debt on
`048.00x-T` and `003-*`, artifacts this session never touched (verified via git status).

### Gate results — cycle 3
* **plan-review: PASS (final)** — 0 unresolved P0, 0 unresolved P1. F14-R structurally
  eliminated; F15 resolved. Cycles used **3 of 3 — limit reached.**
* **plan-harden: HARDENED re-affirmed** — H10.5 added, H10.4 superseded; H1–H9 re-read
  and unaffected. H10.5 is fail-safe in a stronger sense than H10.4: it removes the
  *precondition* for the destructive path rather than a capability.
  `returnUnreleasedFeatureItems` still runs on every close — it simply has nothing to act
  on, verified empirically rather than argued.
* **Blast radius of this cycle:** backlog metadata and planning documents only. No source,
  schema, template, or CLI file touched.


### Cycle 4 — NEW OPEN P1 (F16), session terminal state: BLOCKED

The PR #325 Copilot review of HEAD `48368657` (the corrected topology HEAD)
raised one new finding, and it is valid.

**F16 (P1, OPEN).** T18's rollback requirements are mutually exclusive.
`120.007-T` forbids any legacy shell policy surviving in the shim — which is also
hard **DoD #2** — while simultaneously requiring an `AUTOHARNESS_SUPERVISOR=0`
escape hatch that executes the legacy inline path **without a redeploy**. A
runtime branch needs the legacy path present in the shipped shim; a git SHA is
documentation and cannot supply one. The contradiction originates **upstream in
the reviewed plan** (§9 rollback bullet, §10 T18) and hardening (H8 T18 row, H10
S3), and propagates into `120.008-T`, which is told to document the escape hatch
in the rollback runbook.

**Why it was not fixed in-session.** The 3-cycle plan-review budget was already
exhausted at cycle 3, and the resolution is a genuine product trade-off, not a
clerical correction: Option A drops the escape hatch (preserves DoD #2; rollback
becomes a documented single-file revert per shim; costs redeploy-free rollback
during the S3 bake), while Option B retains a versioned legacy implementation
(preserves redeploy-free rollback; **relaxes** DoD #2 and the no-duplication
invariant, requiring amendments to the plan, hardening doc, and both tasks).
Stage may not pick between these unilaterally after the budget is spent.

Per the operator's standing rule — *any new P0/P1 blocks and escalates* — the
review verdict was downgraded **PASS -> BLOCKED**, F16 was recorded as **open**
rather than absorbed, and both affected tasks carry a blocking backlog comment.
Cycle 3 explicitly condemned an untruthful "0 unresolved P1" claim; silently
re-asserting PASS here would have repeated exactly that failure in a worse form.

**Escalation route resolved** (fresh config reload, H6): no nested
`model_routing.stage.escalation` override exists, so the flat
`model_routing.escalation` route resolves to `gpt-5.6-sol` / `openai` /
`reasoning_effort: high`. That is a different vendor and family from Stage's own
route (`claude-opus-5` / `anthropic`), so the **same-route guard does not fire**
and escalation is genuine, not `ESCALATION_DEGRADED`.

**Containment — SUPERSEDED, see F17 below.** F16 itself touches only `120.007-T`
and `120.008-T`, both members of `129-S`, the **final** shipment, gated behind
`127-S` and `128-S`. Considered alone it does **not** block the eligible cursor
`127-S`, does not affect `128-S`, and invalidates none of the F14
structural-elimination work or its evidence. It must be dispositioned before
`129-S` is claimed. **However, the "eligible cursor is unaffected" conclusion no
longer holds for the session as a whole** — the later F17 finding does block
`127-S`. See the next section.

---

## Cycle 4 (cont.) — TWO FURTHER OPEN P1s (F17, F18)

A second Copilot review, requested on the F16 HEAD, reported "no new comments" at
the top level but carried **24 suppressed comments** inside a collapsed
`<details>` block. Reading the full review body (not just the summary) surfaced
two more genuine defects plus clerical fallout of my own re-parenting.

### F17 (P1) — **BLOCKS THE ELIGIBLE CURSOR `127-S`**

`118.001-T` / `118.002-T` assert a characterization baseline over "the same seven
dimensions against an unmodified `start.sh`". Empirically verified against the
actual files, that premise is false:

* `start.sh` is 80 lines: `.env.local` no-clobber parsing with quote stripping
  (20–36), `COPILOT_HOME` default (54), an **unguarded**
  `export GITHUB_TOKEN="$(gh auth token)"` (56), exe resolution (57–64),
  `exec "$copilot_exe" "$@"` (66). It contains **zero** occurrences of
  `backlogit`, `COPILOT_USE_REMOTE`, or `GITHUB_PERSONAL_ACCESS_TOKEN`;
  `ENGRAM_DATA_DIR` appears only in a **commented-out** line 55.
* `start.ps1:65` sets `$env:GITHUB_PERSONAL_ACCESS_TOKEN = (gh auth token)`
  **unconditionally**; the non-fatal `try` / `Write-Warning` at 68–77 guards
  `GITHUB_TOKEN` only.

So the seven-dimension parity baseline is **unsatisfiable as written**, and
`118.001-T` criterion (c) misstates the current behaviour. The same overstated
premise underpins the `004-SP` PROCEED reconciliation and the composability
decision doc. Because `118.001-T` and `118.002-T` are members of **`127-S`**,
this blocks the only eligible shipment.

**Operator decision needed:** re-inventory the real `start.ps1` / `start.sh`
contracts and restate the baseline; and decide whether cross-platform
normalization belongs in **S3** or requires separate approval, given that **S1
mandates zero observable behaviour change**.

### F18 (P1) — state-machine contradiction (gates `128-S`)

Plan §3.2's diagram routes `CANCELLING -> EXITED`, bypassing `DRAINING`, which
contradicts the plan's own prose rule and `119.006-T`. Separately,
`119.003-T`'s transition table omits `LOCKING -> REFUSED`, the failure edges to
`FAILED`, and `RESTARTING -> LAUNCHING`.

Resolution is low-ambiguity (the diagram is almost certainly the outlier), but it
is still a plan amendment and the review budget is spent, so it is recorded open
rather than adopted. **Operator confirmation needed** that cancellation routes
through `DRAINING`.

### Clerical fallout corrected (not findings)

Seven stale `117.x` task references — fallout from my own cycle-3 re-parenting —
were repointed to live IDs using the authoritative remap table above; zero
residual, every target resolves. Verdict-consistency defects were fixed in the
review doc header and tail, the spike README provenance, `117-F`'s Review
section, and the checkpoint (whose Ship-claim instruction is now **gated**:
"DO NOT CLAIM ANY SHIPMENT YET — open P1 F17 blocks 127-S").

### Terminal state

**Three open P1s: F16, F17, F18.** All three require operator **product**
decisions; Stage adopted none of them, because the 3-cycle review budget was
exhausted before they surfaced. **`127-S` is NOT safely claimable** pending F17.
None of F16–F18 invalidates the F14 structural elimination, the shipment
topology, or the 64/64 + 197/197 closure evidence.

---

## Cycle 4 (cont.) — TWO MORE OPEN P1s (F19, F20) + a corrected evidence defect

A third Copilot review (HEAD `d8644c46`) raised **no new P0/P1 against the
topology work** — both top-level comments restated F18. Its suppressed comments
surfaced two more decomposition/plan defects, and one genuine defect in my own
evidence.

### F19 (P1) — circular ordering, gates `128-S`

`119.003-T` requires `session.py` to emit `SessionPhaseChanged`, but that event
type is not defined until `119.004-T`, whose dependency edge points **back** to
`119.003-T` (`119.004-T -> 119.003-T`, confirmed in the live graph). The declared
order is unimplementable: satisfying `119.003-T` requires defining the event in
the wrong module or implementing `119.004-T` early. Needs the shared event
contract moved into an earlier dependency and the task/dependency split revised.

### F20 (P1) — authority boundary contradiction, gates `129-S`

`120.002-T` requires a `backlogit sync` + Engram bind/sync pre-warm while
simultaneously asserting the service "does not mutate backlogit or Engram"; plan
§3.1's `Must NOT` row likewise forbids writing a sidecar store. Lifecycle calls
necessarily refresh tool-managed indexes, so no implementation honours both
literally. Intended distinction is almost certainly domain/authority mutation
(forbidden) vs cache/index refresh (required) — but that is not what the
documents say, on a P1-blast-radius task.

### Evidence defect found, corrected, disclosed

The Part 2 replay was **not** the "isomorphic replay of the exact live 27-edge
DAG" I had published. Its hand-maintained index-based edge list carried a
spurious `120.004-T -> 119.002-T` edge absent from the live graph — **28 replayed
vs 27 live** — and the original V7 could not catch it because it only *counted*
live edges without comparing them to the replay.

Fixed in two parts, so this class of drift cannot recur:
* V7 now asserts **set equality** against 27 explicitly named endpoint pairs and
  reports any missing/extra edge by name (a count-only check would still pass if
  one valid edge were swapped for another).
* Part 2 **derives** its replay from that same verified list via an ID map, so
  the fixture cannot drift from what V7 proved — isomorphism by construction.

Also fixed: the `returned_ids` emptiness checks still passed on a **null** value
(`@($null).Count` is `0`), so both harnesses now require **present, non-null and
zero-length**; and both used `$env:TEMP`, which is not guaranteed on POSIX,
now `[System.IO.Path]::GetTempPath()`.

Re-run after all corrections: **64/64** and **196/196**. The safety *conclusion*
is unaffected — dependency edges play no part in `ShipShipment`'s parent-clearing
path, and the spurious edge only made the replayed graph strictly more
constrained — but the isomorphism *claim* was inaccurate and was corrected rather
than quietly restated.

### Cycle 5 — compound-library reconciliation and the last vacuous assertion

The fifth Copilot review raised no new P0/P1. It surfaced clerical drift plus one
substantive reconciliation, all resolved here.

**Substantive: the durable close guidance contradicted these manifests.**
`docs/compound/097-S-shipment-task-only-safe-close.md` records a durable rule that
a shipment manifest must be **task-only** and must never list its covering
feature. `127-S`/`128-S`/`129-S` do exactly the opposite. Left unreconciled, Ship
would have received two contradictory close instructions for the same artifacts.

Adjudication: **both are correct for different manifest shapes**, and the durable
rule's hazard model is narrower than its wording.

* The durable rule targets a **PARTIAL-feature** shipment — a covering feature
  with children *outside* the manifest — where `shipment ship` cascades into
  unshipped siblings. Correct and unchanged for that shape.
* The opposite hazard exists too, and task-only membership does **not** avoid it.
  On backlogit 1.8.0 `returnUnreleasedFeatureItems` is not gated by
  `explicitScope`; it also runs for a non-member **ancestor** feature reached via
  `featureScopeRoots`' upward `parent_id` walk. ARM A of the closure simulation
  reproduces exactly that and orphans **14/14** downstream tasks.
* The **FULLY-COVERED ROOT** exception applies when (1) every child of the
  covering feature is in the same manifest, and (2) the feature has no parent.
  Then the remainder set is empty and the scope walk cannot escape upward, so the
  cascade is **structurally impossible** rather than procedurally avoided.

Recorded as an append-only "Reconciliation" section in the compound doc (the
original rule is preserved verbatim, with a table stating which contract applies
to which shape) and cross-referenced from all three shipment manifests and from
the spike README. This is a documentation reconciliation only — no topology, no
task, and no manifest changed.

**One more vacuous assertion, same family as the earlier ones.** V10's proof that
pre-existing backlog debt was left untouched piped `git --no-pager status`
straight into a filter. `git` is a native call, so under a nonzero exit the output
would be empty, zero rows would match, and the assertion would have passed
**vacuously** — "no matches" silently read as "untouched". It now captures,
checks `$LASTEXITCODE`, throws on failure, and only then filters, matching the
`Invoke-Bl` contract. This is the third instance of the same root cause
(native/nonzero exits do not terminate under `$ErrorActionPreference = 'Stop'`),
which is worth carrying forward as a standing review check for any harness.

Both harnesses re-run after these edits: **64/64** and **196/196**, V7 set
equality clean. Clerical fixes: README provenance still said 3 open P1s and still
described the temp directory as `$env:TEMP`; the closure fixture comment
mislabelled the covering features as `127-F/128-F/129-F` (they are
`118-F/119-F/120-F`); the Ship checkpoint's `resume_hint` said "All three" where
five findings are listed and still cited the superseded reviewed HEAD.

The terminal state below is unchanged by cycle 5.

### Cycle 6 — no new P0/P1; two more vacuous assertions in my own evidence

The sixth Copilot review (HEAD `e50fc808`) reported "no new comments" at top
level and **four suppressed comments**, all valid, none a new P0/P1. The open
finding set is unchanged at exactly **F16-F20**. Two of the four landed on the
evidence again, and both are worth carrying forward as review checks.

**1. I hardened a check that was measuring the wrong thing.** In cycle 5 I added
`$LASTEXITCODE` handling to V10's `git status` call, which was a real fix - but
`git status` was the wrong instrument entirely. It reports only *uncommitted*
worktree changes, so on the committed HEAD that every published run executes
against, it returns nothing for the pre-existing-debt paths **whether or not this
branch changed them**. The assertion passed vacuously on any clean checkout. V10
now derives the branch's real footprint from
`merge-base(origin/main, HEAD)..HEAD` and unions in the worktree status so an
uncommitted edit cannot slip past either. Re-verified: the branch touches 60
`.backlogit` files, **zero** of them pre-existing-debt artifacts - so the claim
was true, but for the first time it is actually *proven*.

Lesson: a robustness fix to an assertion is not evidence that the assertion tests
the right proposition. Ask what would have to be true for the check to fail
before hardening how it fails.

**2. A printed result masquerading as an asserted one.** The closure simulation
*printed* `backlogit doctor` output at the terminal fixture state and never
asserted it. `doctor` exits 0 while reporting findings - V10 depends on exactly
that behaviour - so the advertised proof could have passed against a dirty
fixture. Now asserted, as Part 2 of the verifier already did. The simulation
total is therefore **64/64**, up from 63/63; the verifier is unchanged at
**196/196**. Progression to date: simulation 57 -> 60 -> 63 -> 64, verifier
194 -> 196, with no correction ever changing observed engine behaviour.

The other two suppressed comments were documentation defects, both real and both
fixed: H8 in the hardening record said "Three tasks carry `complexity: high`"
while its own table lists four (T7, T11, T15, T18), matching the four queued
tasks with `complexity: high` (`119.002-T`, `119.006-T`, `120.004-T`,
`120.007-T`) - the same undercount had propagated into review finding F7; and the
deferred Plan-2 credential-rotation runbook attributed the redaction choke point
to T5, which is workspace/session locking, when it is T4 (`supervise/redact.py`,
harvested as `118.004-T`).

The terminal state below is unchanged by cycle 6.

### Cycle 7 — no new P0/P1; three consistency defects

The seventh Copilot review (HEAD `857e208d`) again reported "no new comments" at
top level with **three suppressed comments**, all valid, none a new P0/P1. The
blocking set was unchanged at F16-F20 across cycles 5, 6 and 7, which produced
only evidence-robustness and record-consistency defects. **[RETRACTED IN CYCLE 8:
this section originally read that stability as evidence the five open P1s were
the complete remaining gate. Cycle 8 raised F21. Absence of new findings is not
evidence of absence of defects - see the Cycle 8 section below.]**

1. **The documented `-Repo` invocation did not actually work.** A relative
   `-Repo` passed the initial `.backlogit` existence check - which resolves
   against the *invocation* directory - but was then stored unresolved. V9's
   archive probes run after `Set-Location $repo`, and the final
   `Set-Location $repo` runs from the *temp fixture*, so a relative path would be
   re-resolved against a different directory each time. The advertised
   out-of-tree reproduction path was broken for exactly the users it was added
   for. `-Repo` is now canonicalized with `Resolve-Path` before any
   `Set-Location`, and the harness was re-run with `-Repo .` to prove it.

   This is the same failure family as cycle 6's `git status` defect: a
   correctness property that was *documented* but never *executed*. Anything the
   README tells a reader to run must actually be run at least once.

2. **The Ship handoff checkpoint recorded a stale reviewed HEAD.** It still named
   `df3924f5` while the PR declared `857e208d`, so a consumer restoring it would
   have picked up stale review provenance. Reconciled to the current HEAD with
   the full supersession chain, and annotated with the cycle-5/6/7 outcome so the
   next reader can see those cycles produced no new findings rather than being
   merely unexamined. (As written at the time this said the set "has been
   stable" - RETRACTED in the cycle-8 section below, where F21 falsified it.)

3. A safety-properties line in the spike README still said fixtures are created
   under `$env:TEMP`, contradicting the portability fix (and its own explanation
   later in the same file). Corrected.

The terminal state below is unchanged by cycle 7.

### Cycle 8 — a NEW P1 (F21), and the retraction of my stability claim

The eighth Copilot review (HEAD `66f1220f`) raised a **new P1**. One cycle
earlier I had written that the blocking set was "stable at exactly F16-F20 across
three consecutive reviews" and treated that stability as *evidence the set was
complete*. **That inference was wrong and is withdrawn.** Three quiet cycles were
not evidence of completeness; they were three cycles that happened not to surface
the next defect. The open set is now **six**: F16-F21.

This is worth carrying forward as a general lesson: **absence of new findings is
not evidence of absence of defects**, and it is especially tempting to treat it
that way when you are trying to reach a terminal state. I should have reported
the quiet cycles as "no new findings in cycles 5-7" without the inferential
gloss.

**F21 - the fail-closed approval channel can be omitted from the shipped runtime
without any task failing.** Verified against the live dependency graph rather
than inferred:
* `120.005-T` (T16, `approvals.py`) DEPENDS ON `120.004-T` (T15, `run_session()`)
  and has **zero reverse dependencies** - nothing in the program depends on it.
* The runtime chain `120.004-T` -> `120.006-T` (T17, CLI adapter) ->
  `120.007-T` (T18, shims) -> `120.008-T` (T19, docs) is fully satisfiable with
  `120.005-T` never started.
* Yet T15 is specified as THE SINGLE ORCHESTRATOR, and plan section 3.6 places
  the approval exchange inside supervisor runtime behaviour.

So T15's acceptance can be met against a `run_session()` with no approval path,
and no later task forces the wiring. The H2 fail-closed guarantee - non-interactive
approvals resolve to a declared safe default or REFUSED, never silent
auto-approval - is a SAFETY control that this ordering permits to be dropped
silently. Same family as F19 (a shared contract ordered downstream of its only
consumer), but with a safety consequence rather than only an unimplementable
order.

Recorded, not adopted: the budget is spent and the fix is a decomposition change
to an already-reviewed plan. Options (A) split the approval CONTRACT ahead of
T15 and make T15 depend on it, leaving console rendering downstream;
(B) make T15 depend on T16 and move the approval-path integration tests into
T15's DoD; (C) attach an explicit wiring obligation plus a test asserting
`run_session()` routes approvals through `approvals.py` to a task already on the
runtime chain. **Option (A) matches the direction already recorded for F19, so
one decomposition change could discharge both.** Blocking comments were appended
to `120.005-T`, `120.004-T` and `120.006-T`; no dependency edge was changed.

**The checkpoint HEAD chase, ended structurally.** The review's second comment
noted the durable handoff still named a stale reviewed HEAD - which it did, and
would have again, because **a commit cannot embed its own resulting SHA**. Naming
the "current" HEAD inside a committed artifact is unwinnable by construction, and
I had been re-fixing the symptom each cycle. The field now records the **evidence
HEAD** (the tree the 64/64 + 196/196 run was executed against) and points to the
PR readiness record for current-HEAD coverage, which is the only place that can
be authoritative because it is edited *after* each push.

Assertion totals are unchanged: **64/64** and **196/196**. F21 is a decomposition
and safety-ordering defect; it does not touch the topology, the 27 dependency
edges, or the closure evidence.

### Cycle 9 — no new P0/P1; four consistency defects from recording F21

The ninth Copilot review (HEAD `11de7aba`) raised **no new P0/P1**. All four
suppressed comments were consistency defects created by my own F21 recording pass
- a useful reminder that adding a finding is a multi-artifact edit, and the
places that summarize the finding set drift silently.

1. The review document's **top-level verdict summary** still described five
   post-budget findings and omitted F21 from the gate map, while its header and
   final gate re-run already said six. A reader stopping at the summary would
   have concluded `129-S` was gated only by F16/F20.
2. `117-F`'s hardening summary still said "the three complexity-high tasks",
   the same undercount I had corrected in H8 and F7 one cycle earlier but had not
   propagated into the live feature record. Now names all four (T7, T11, T15,
   T18) with their live IDs.
3. The checkpoint's final reconciliation attributed **all six** P1s to five
   reviews ending at `df3924f5` - internally impossible, since F21 was raised in
   cycle 8 on `66f1220f`. Corrected to eight reviews with the full HEAD range,
   retaining the evidence-HEAD distinction.
4. **`117-F`'s event log still ended with "NEVER re-add 117-F to a manifest"** -
   the exact opposite of the current close contract, since the H10.5 redesign
   deliberately makes the childless umbrella a member of the final shipment
   `129-S`. This was the most consequential of the four: a log-based consumer
   reading only the event stream would have received an instruction contradicting
   every other artifact. Fixed by APPENDING a superseding comment event that
   explains why the earlier instruction was correct for the topology it was
   written against and why it no longer applies - the historical event is
   preserved verbatim, not rewritten.

Lesson worth carrying: **the event log is a consumer surface, not just an audit
trail.** When a decision is reversed, an append-only correction has to be written
into the log itself; correcting the artifact body is not sufficient.

Assertion totals unchanged: **64/64** and **196/196**. Open set unchanged at six:
F16-F21.

### Cycle 10 — TWO NEW P1s (F22, F23), and the most instructive self-inflicted defect yet

The tenth Copilot review raised **two genuine new P1 plan findings**, taking the
open set to **eight (F16–F23)**. Both were verified against the plan text before
recording, not accepted on assertion.

**F22 — post-`LOCKING` failures never release the workspace lock.** Plan §3.2
sends `BOOTSTRAPPING —(fatal)→ FAILED`, `RESOLVING —(no copilot exe)→ FAILED`
and `LAUNCHING —(spawn error)→ FAILED` straight to terminal states. None goes
through `DRAINING`, and Rule 2 scopes the cleanup guarantee to "the only path to
a terminal state **from `RUNNING`**". §3.4 then makes it permanent: a stale lock
is never auto-broken and needs an explicit `--force-unlock`. So the single most
likely first-run failure — Copilot CLI not on `PATH` — locks the operator out of
their own workspace, and every retry returns `REFUSED`.

**F23 — `119.006-T`'s "cancel during launch" test cannot be written.** §3.2 has
exactly one cancellation edge (`RUNNING → CANCELLING`) and Rule 1 rejects
anything outside the table with `ILLEGAL_TRANSITION`. Same class as F17:
acceptance criteria the fixed contract cannot satisfy.

**The synthesis worth carrying to the operator:** F18, F22 and F23 are not three
problems. They are one missing invariant — *cleanup and cancellation are
guaranteed only from `RUNNING`* — and a single ruling ("every terminal exit after
`LOCKING` routes through `DRAINING`; operator cancel is legal from every
post-`LOCKING` phase") discharges all three. Likewise F19 + F21 are one
contract-placement ruling. Eight findings, **two** decisions. Presenting them as
eight would have made the blockage look far more intractable than it is.

#### The defect I introduced while fixing a defect

The review also caught V4 asserting `related_to` links without ever testing
`link_type`, and V10 hard-coding `origin/main`. Fixing the latter, I resolved the
branch's **tracked upstream** first — it seemed like the most authoritative base.
For a topic branch the tracked upstream is *the remote copy of the same branch*,
so `merge-base(upstream, HEAD) == HEAD`, the diff range was empty, and the run
printed a **0-file** branch footprint. It passed. It proved nothing. **It was the
exact vacuity that V10's rewrite existed to eliminate, re-introduced by the fix
for the previous instance of the same mistake.**

I caught it only because I read the numbers the passing run printed instead of
the PASS line — `0 .backlogit files` for a branch that had touched sixty of them
is not a plausible measurement. Two changes followed: `@{upstream}` is gone
(`origin/HEAD` first), and V10 now **throws** when the merge-base equals `HEAD`,
so no base ref — including a bad operator-supplied `-BaseRef` — can produce a
vacuous pass again.

That is now **four** instances of one family (a fifth, `Invoke-Sql`, follows in
cycle 12): an assertion can be robust and still test the wrong proposition. The habit that actually catches it is not
"check exit codes"; it is **treat a suspiciously empty measurement as failure**,
and read what a green run reports rather than that it was green.

Totals after re-execution: **197/197** (V4 gained the negative link-type
assertion) and **64/64**.

## Cycle 12 (twelfth Copilot review, HEAD `a20c5b50`) — F24 and F25: capabilities nobody has to make real

Two more new P1s, and they are the same shape as each other: **a capability is
specified in one task and no task is obligated to make it reachable.** The DAG is
satisfiable with the capability simply absent.

**F24** — `119.005-T` says "add `.autoharness/sessions/` to the gitignore
template". I went looking for that template. **It does not exist.** `templates/`
has no gitignore artifact at all; workspace ignore rules are handled
*procedurally* by the install-harness skill, which only *confirms* an existing
`.gitignore` covers `.env.local`. So the criterion is discharged by searching for
a nonexistent file and finding nothing to change. That is worse than F17 or F23,
which at least fail loudly — **this one fails silently**. And it takes an H6
hardening property with it: the same task calls the journal "gitignored local
operational state" and uses that to argue authority containment. In a generated
workspace nothing installs the rule, so the journal is git-tracked and the
property is simply false there.

**F25** — `120.006-T` is the *only* task that touches the CLI, and it never says
which options `autoharness run` accepts. `--force-unlock` lives in `118.005-T`
(`locking.py`); `--max-restarts N` and resume live in `119.006-T` (`recovery.py`).
Neither touches `cli.py`. Every task can pass while both controls are unreachable
from the product's sole public surface. **And `--force-unlock` is F22's own
documented remedy** — so F22 sets the lockout trap and F25 removes the exit. That
compounding is the part worth carrying forward: two findings that are individually
arguable become jointly severe.

The lesson I want to keep: **"is it specified?" and "is it reachable?" are
different questions**, and a task-level DoD review only ever answers the first.
Reachability is a property of the *graph*, not of any task, so nothing in a
per-task review will surface it. F21 was the same defect and I did not generalize
it at the time; had I done so, F25 would have been found four cycles earlier.

Also fixed this cycle: `Invoke-Sql` returned `@()` whenever output contained no
JSON array marker — the **fifth** instance of the vacuity family, and the most
dangerous, because several of the strongest proofs here are *zero-result* proofs
(V8, V9, V4) that would all have passed on a swallowed format change.

**My first fix for it was wrong, and only running it showed that.** Making a
missing `[` throw looked unarguable — and it instantly failed V4, a proof that had
passed for twelve cycles. Not a regression: **backlogit emits the literal `null`
for a zero-row query, never `[]`**, so I had swapped one conflation for another
and turned a legitimate empty result into a phantom failure. The shipped version
enumerates all three outcomes — `null` accepted as genuinely empty, `[` parsed,
everything else throws — and matches the payload *exactly* with log lines
stripped, since substring-searching for a bracket is how the original vacuity got
in. That is **twice** now that a fix for this family was itself defective (item 10
was the first), and both were caught by running the fix and reading its output
rather than trusting the reasoning. **A guard never observed to fire correctly on
a real empty result is an untested guard**, and "be stricter" is not the
correction — enumerating the outcomes the tool can actually emit is. And
`118-F` still called `127-S` "the ONLY eligible shipment in the chain" while the
shipment record says DO NOT CLAIM — a feature record is a consumer surface, so
that was an authorization a Ship reader could have acted on. It now separates
*structural eligibility* from *claimability*.

## Cycle 14 — F26: a planning doc cannot grant Ship an exemption from Ship's own rule

The fourteenth review pointed at `docs/compound/097-S-shipment-task-only-safe-close.md`
and said its close command conflicts with policy. I verified all three files, and
it is right — this is a **new P1**, and the most consequential since F17.

The compound doc says the fully-covered-root case closes "with a single
`shipment ship`" and that "Ship should read this reconciliation, not the
partial-feature rule". But `.github/agents/_ship.agent.md` says "**NEVER** the
cascade `backlogit_ship_shipment`, P-015" and "**Do NOT call
`backlogit shipment ship`**" — **unconditionally**, with no fully-covered-root
carve-out. P-015 in `templates/policies/workflow-policies.md.tmpl` *is* scoped to
partial-feature shipments in its "Applies when", but its Statement and
Postcondition are absolute and the Ship agent repeats them without the
qualification. Under fail-closed P-010/P-015, an operation Ship's own agent file
says never to call is **forbidden**, whatever a planning document asserts.

**That is the real lesson, and it is a role-boundary one.** I wrote a compound doc
that declared an exception to a policy without amending the policy or the Ship
agent, and then told Ship to prefer my document over its own rule. **Stage does
not have that authority.** Documenting an exception is not being granted one, and
the fact that the exception is *technically* sound — the preconditions really do
make the cascade harmless — does not make it *operative*. It should have been
raised as a policy amendment for the operator to rule on, not published as a
contract Ship was instructed to follow.

**A second-order consequence I should have seen unaided.** The 64/64 simulation
proves `shipment ship` returns `returned_ids: []` under this topology — it proves
the safety of **an operation Ship must never call**. If closure actually runs
through `shipment-reconcile` safe-close, the relevant proposition is different:
that archiving each manifest item in turn, with an **empty** protected set, leaves
the backlog consistent. So the strongest evidence in this PR answers a question
Ship will never ask. That is the **vacuity family one level up** — not a vacuous
assertion inside a proof, but a **rigorous proof of the wrong proposition**. Sixth
instance, and the largest: no amount of assertion-hardening would have caught it,
because every assertion was sound. Only asking *"who executes this, and what will
they actually call?"* catches it.

**What is NOT broken:** the topology. Under safe-close the fully-covered-root
manifests remain correct — the covering feature is itself a manifest item and
there are no unshipped siblings, so the protected set is empty and safe-close
archives exactly the release unit. F14's structural elimination stands. What
breaks is the **close command** in the contract and the **scope** of the evidence.

Resolution is an operator/policy ruling and Stage adopted none: either amend
P-015, the Ship agent and `shipment-reconcile` coherently for a *verified*
fully-covered-root exception, or keep safe-close and revise the compound contract
and its expected evidence (`returned_ids: []` stops being the artifact to expect).
**Gates all three shipments**, since closure is on every shipment's path.

## Cycle 15 — F27, F28, F29: three findings, and the one that hit the cursor

The fifteenth pass was the largest single-cycle yield since cycle 10, and it came
straight after a quiet cycle — the **fifth** time that has happened.

**F27 is the one that matters most, because it lands on `127-S`.** `118.005-T`
owns the lockfile that enforces the single-active-session invariant — the whole
point of the module. It specifies a PID + process-start-time liveness check
(genuinely good: it handles PID reuse) and sequential contention tests. It never
requires the acquisition to be **atomic**. Check-then-write is a TOCTOU window, so
two supervisors starting *simultaneously* can both see no live holder and both
write. Every acceptance criterion still passes.

This is the wrong-proposition family for a sixth time, and the clearest instance
of it yet: **a sequential contention test proves mutual exclusion against a
non-contending peer.** That is a different proposition from the one the invariant
needs. No amount of tightening the sequential assertion reaches it — the test
would have to be restructured to start contenders in parallel. Worth remembering
that the *sound-looking* part (the liveness check) is what made the gap easy to
miss: it is necessary for stale-lock recovery and it is not sufficient for
exclusion, and the task text reads as if it were both.

**F28**: `119.004-T`'s anti-drift guard is lexical — no `bind`/`listen` token, no
banned framework import. `socket.create_server`, `socketserver.TCPServer`,
`asyncio.start_server` and `http.server.HTTPServer` all sail through. What makes
it P1 rather than hygiene is *what the guard is for*: it is the control that
discharged **F2, a cycle-1 P0**. So a P0 I recorded as mitigated is less mitigated
than this review's own record claims. Lesson: when a guard closes a P0, the guard
inherits that severity, and a denylist should never be the whole of it.

**F29**: `119.001-T` defaults child stdio to `subprocess.PIPE`. But `start.sh:66`
is `exec "$copilot_exe" "$@"` — the child *replaces* the shell and stays on the
terminal — and `start.ps1` inherits handles. Piping makes stdio non-TTY, which
changes prompts, input handling, colour and buffering for what is an interactive
TUI. T1/T2 never characterize terminal attachment, so the migration can pass every
assertion and still break normal use. **Same class as F17 and F23: the
characterization baseline omits the property the change most affects.** Three
findings now share that shape, which makes it a pattern rather than an accident —
if a plan promises "zero observable behaviour change", the first question is which
observable properties the baseline actually captures.

**Where I stopped, and why.** Cycles 5–7, 9, 11 and 13 were quiet; 8, 10, 12, 14
and 15 each produced new P1s. Five quiet-then-new-P1 windows in fifteen passes
means a quiet cycle has *never once* predicted a fixed point in this PR. I could
keep going and would almost certainly keep finding real defects. But every one of
them lands on the same operator gate that is already blocking all three shipments,
so additional cycles add findings without changing the decision the operator has
to make. **Non-convergence is the result to report**, not a reason to keep
looping.

**Two other things I fixed this cycle, both mine.** The hardening doc still
carried a bullet saying F14 was "accepted with a required Ship-side re-adoption
mitigation" — a cycle-2 position that cycle 3 rejected. Left standing, it was a
live instruction telling Ship to re-parent items, which is **not in Ship's role
boundary and therefore P-010-forbidden**. That is *exactly* F26's defect class,
sitting in my own document, and I had read past it for twelve cycles. I retracted
it by quoting it rather than deleting it, so the change of position stays
auditable. And `117-F`'s summary line still said "plan-review PASS (0 P0 / 0 P1)"
with no qualification — the single most dangerous sentence in the backlog, since a
summary line is what an agent skims before claiming.

## Cycle 16 — the operator ruled, and I got to find out which of my compressions were wrong

The operator accepted **all eleven** recommended rulings and authorised exactly
one bounded remediation + focused validation pass, with a standing instruction to
**halt** on any surviving P0/P1 rather than open round sixteen. That instruction
mattered more than it looks: it removed the temptation I had been resisting for
five cycles — to solicit one more review and hope it came back quiet.

**I had been saying "ten rulings". It was eleven.** F24 and F25 were correctly
*diagnosed* as one cluster: both were capabilities specified in one task with no
task obligated to make them real. The diagnosis is what caught them. But the
fixes land on completely unrelated surfaces — core-owned ignore behaviour inside
`journal.py` versus the `autoharness run` option contract — so collapsing them
into one ruling would have produced a decision that could not be executed as a
single change. **A shared root cause is not a shared remedy**, and I had let the
tidiness of "three clusters" carry an inference it did not support. I corrected
the count in the review doc rather than quietly keeping ten.

**Ruling 8 was the one that tested my own boundary.** It required amending P-015
and the Ship agent so the permitted close operation and the executable evidence
agree. Both live in `templates/` — the **product**. The tempting move was to make
the edit, since the operator had approved the ruling and the change is small. But
F26 exists *precisely because* a Stage planning artifact tried to grant Ship an
exemption from Ship's own operative prohibition. Editing the Ship agent template
myself would have been the same defect at a higher privilege level: Stage
rewriting the constraints Stage is bound by. I created **`118.007-T`** instead and
placed it in **`127-S`**, the first shipment, so the amendment lands before any
close in the chain. The compound doc now says safe-close governs *until that task
lands* — which is the honest state, not the convenient one.

**Placing `118.007-T` in the first shipment instead of building a new one.** The
alternative was a prerequisite feature plus a fourth shipment ahead of `127-S`.
That would have re-chained the serial order and disturbed exactly the topology
the 197-assertion verifier was built to protect, to solve a sequencing problem
that membership in `127-S` already solves. The invariants both hold: full
coverage (I re-verified `118-F`'s child count *after* adding the two tasks —
adding a child to a covering feature without adding it to the manifest is
precisely how H10.5 breaks) and root isolation (both new tasks are children of
`118-F`, which has no parent).

**Updating my own evidence harness was the subtle risk.** The verifier hardcoded
the pre-ruling task list, edge set and counts, so after the rulings it would have
failed against a *correct* topology. But an evidence script that gets edited until
it passes proves nothing. I kept the expected edge **set** rather than a count,
enumerated each of the four deltas inline with the finding that caused it, and
widened the S1 fixture from five to seven. The assertion I nearly got wrong was
`origin_feature`: the nineteen re-parented tasks must still carry `117-F`, but
`118.006-T` and `118.007-T` were created natively under `118-F` and never lived
under `117-F`. Asserting it unconditionally would have demanded a **false
provenance record**; deleting the assertion would have stopped detecting
provenance loss on the nineteen. It had to become **conditional in both
directions** — the new tasks are now asserted to claim *no* provenance.

**The validation pass caught me building an expectation from a stale index.** My
first corrected edge set said **29**, and the verifier failed with
`extra: 118.006-T->118.005-T`. The live graph was right; my *expectation* was
wrong. I had derived it from a `backlogit query` run **before** `backlogit sync`,
so the index had not yet picked up the `dependencies:` frontmatter written when
`118.006-T` was created — an edge I had authored myself minutes earlier. Two
things saved it. First, the expectation is a **set**, not a count: a count check
would have failed identically but told me only that a number was off, whereas the
set named the missing edge outright. Second, I had not touched the assertion to
make it pass. The temptation with a red evidence script is to adjust it until it
is green, which is exactly how such a script stops being evidence. The right
reading was that the check had done its job on its own author.

**What the DRAINING ruling actually bought.** F18, F22 and F23 all reduced to one
missing invariant, and the fix is structural rather than enumerative: `DRAINING`
is the **sole terminal gateway**, verified by a **graph-property test** instead of
a list of paths. That distinction is the whole lesson. The defect class here is
*an edge nobody thought to enumerate* — so an enumerated path list can never be
the control for it. The same reasoning drove F28's fix: a lexical denylist cannot
catch `socket.create_server`, so the control had to become behavioural, with
positive controls proving it fires.

### Terminal state (final)

**Zero open P0. Zero open P1.** All fourteen post-budget findings (F16–F29) were
dispositioned by **eleven** accepted operator rulings, applied to the owning task
specs and validated in one bounded pass (Cycle 16). All three shipments are
**GATE-CLEAR**; `127-S` remains the only structurally eligible cursor.

**This verdict is narrow, and the narrowness is the point.** It says every
disposition matches its accepted ruling. It does **not** say finding discovery
converged. Fifteen review passes never reached a fixed point, and five separate
quiet-then-new-P1 windows proved that a quiet cycle is not evidence of
completeness. That non-convergence is unchanged and still the honest characterisation
of the plan's defect density. What ended the block was **operator authority over
product trade-offs**, which is the only thing that could have — no amount of
additional reviewing would have produced a decision Stage had no standing to make.

**Gate-clear is not permission to claim.** Claiming remains Ship's call under
Ship's own boundary, and one gate is deliberately sequenced *inside* the first
shipment: until **`118.007-T`** lands, the cascade close operation is still
prohibited to Ship and safe-close governs. Ship must read `127-S` and the review
artifact, not this summary line.

**Topology delta to carry forward.** `118-F` now has **seven** children
(`118.006-T`, `118.007-T` added); `127-S`'s manifest has **eight** items. Plan-1
task edges went **27 → 30**: removed `119.004-T→119.003-T` (that edge *was* the
F19 cycle), added `119.004-T→118.003-T`, `120.005-T→118.003-T`,
`120.006-T→118.006-T` and `118.006-T→118.005-T` (declared when the task was created — the stale-lock lifecycle operates on the primitive `118.005-T` defines; both are `127-S` members, so it orders work *within* the eligible cursor and does not affect eligibility). None of it touches the F14 structural elimination or the
three-shipment serial chain.

**The single most useful question I found.** Six of the fourteen findings, and
five of my own defects, came from one habit: asking *"who executes this, and what
will they actually call?"* rather than *"is this assertion correct?"* Every
assertion in the 64/64 harness was sound, and F26 still meant the harness might be
proving the safety of a command Ship was forbidden to run. Ruling 8 resolved that
by changing what Ship may call — but only once `118.007-T` lands. Hardening could
never have reached that class of defect; only tracing an artifact to its executor
can.
