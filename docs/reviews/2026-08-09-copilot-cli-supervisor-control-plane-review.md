---
title: "Plan Review — Local Copilot CLI Supervisor / Control Plane (Plan 1, FAST-TRACK)"
date: "2026-08-09"
description: "Adversarial plan review of the Plan 1 local Copilot CLI supervisor/control-plane plan and its P-006 hardening, gating harvest."
doc_type: review
source: docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md
review_id: "PLAN-1-R"
verdict: "BLOCKED"
stash_ids: ["34D50F2D"]
model_route:
  model_family: claude-opus-5
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md"
  - "docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-hardening.md"
  - ".backlogit/archive/004-SP.md"
  - "docs/decisions/2026-08-09-composability-single-source-of-truth-spike.md"
tags: ["plan-review", "34D50F2D", "candidate-a", "supervisor", "P-006"]
---

# Plan Review (PLAN-1-R)

## Verdict: BLOCKED — 0 unresolved P0, **3 unresolved P1 (F16, F17, F18)**

> **Cycle-3 verdict was PASS (0 P0 / 0 P1) and remains accurate as of HEAD
> `48368657` for findings F1–F15.** Three **new** P1s (**F16**, **F17**,
> **F18**) were raised by PR #325 Copilot reviews of HEAD `48368657` and
> `91538e74`, *after* the 3-cycle budget was exhausted. Because no review cycle
> remains and their resolutions are genuine product trade-offs, they are
> recorded as **open and escalated** rather than absorbed, and the verdict is
> downgraded to **BLOCKED**. See *Cycle 4* below.
>
> **`127-S` is NOT safely claimable.** F17 invalidates acceptance criteria in
> `118.001-T` and `118.002-T`, both members of the otherwise-eligible cursor.
> F18 gates `128-S`; F16 gates `129-S`.

Review cycles used: **3 of 3 (limit reached)**. Cycle 1 (2026-08-09) raised
F1–F12, all resolved in-cycle by amending the plan and hardening documents before
harvest. Cycle 2 (2026-08-10) was a post-harvest review-fix cycle triggered by PR
#325 Copilot review; it raised F13 (P0) and F14 (P1). Cycle 3 (2026-08-10)
**reopened F14**, rejected its cycle-2 mitigation, and eliminated it
structurally. No cycles remain; this verdict is final.

## Scope reviewed

The Plan 1 implementation plan and its P-006 hardening, against: the operator's
authoritative product decision, the `004-SP` spike evidence, the preserved
product boundaries (Copilot CLI as reasoning engine; Engram read-only;
backlogit authoritative for backlog/checkpoints; graphtor for docs;
`.autoharness/config.yaml` as routing authority), the candidate (c) boundary,
the Stage role boundary (P-010), and the 2-hour task rule.

## Findings

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| **F1** | **P0** | The spike's recorded verdict was CONDITIONAL PROCEED with an explicit **NO-GO** for "process supervision"-adjacent scope, because the only reading available was spec §3 as an in-process action/observation executor. Harvesting a supervisor plan against an un-reconciled NO-GO would leave PR #325 contradicting the shipped backlog. | **RESOLVED** — Plan §2 reconciles the disposition to evidence-backed **PROCEED** under the clarified scope, drawing the bright line *supervising an external engine is in scope; implementing a new agent runtime is not*. The literal-§3 NO-GO is preserved verbatim as a still-standing non-goal. The same reconciliation is appended (append-only) to `004-SP`, the decision doc, the session memory, and the completion checkpoint. |
| **F2** | **P0** | Nothing structurally prevented "control plane" from acquiring a network listener, which would silently pull deferred Plan 2 scope (remote UI/auth/approvals/tunnel) into Plan 1. | **RESOLVED** — H7.2 adds a test-level invariant: no `bind`/`listen` in `supervise/`, and an import ban on `gradio`/`fastapi`/`flask`/`uvicorn`/`aiohttp`/devtunnel clients. Plan §3.6 constrains approvals to console/TTY only. Plan §11.1 states the exclusion. Enforced in Shipment 1, before any supervision code exists. |
| **F3** | **P1** | `start.ps1`'s semantics are subtle (no-clobber `.env.local` precedence, single-pair quote stripping, `--remote` double-add guard, non-fatal sidecars). A "port then test" ordering would have baked in drift. | **RESOLVED** — H1 makes characterize-before-migrate a hard ordering constraint enforced by `blocks` edges (S1 → S2 → S3), and T18's acceptance criterion requires the T1/T2 suites to be re-run **byte-identical**. Changing a characterization assertion is escalated to an operator product decision. |
| **F4** | **P1** | The session journal (checkpoints + resume cursor) risked becoming a second checkpoint/backlog authority competing with backlogit. | **RESOLVED** — H6.1 and Plan §3.7 declare the journal gitignored local operational state, explicitly not readable by any agent-recovery protocol and not a checkpoint. backlogit remains sole authority. |
| **F5** | **P1** | The typed event bus is exactly the hook candidate (c) needs; incremental "just one subscriber" additions would silently implement candidate (c) and could drift Engram toward authority. | **RESOLVED** — H7.1 permits only the journal and console renderer as subscribers; no background verification/summarization/compaction thread. H6.2 forbids any supervisor decision from reading Engram. Plan §8 and §11.6 restate it. `34D50F2D` stays ACTIVE as candidate (c)'s tracker. |
| **F6** | **P1** | Exit-code masking is a *known, already-realized* defect class in this repository's shell scripts (compound learning, trailing `|| true`). A new shim layer reintroduces the exact surface. | **RESOLVED** — H3 makes verbatim exit-status propagation a hard invariant with a dedicated round-trip test over `{0,1,2,42,130}` across both process backends and both shims, and explicitly prohibits `|| true` / `-ErrorAction SilentlyContinue` around the child launch. |
| **F7** | **P1** | Three tasks carry `complexity: high`; without de-risking controls they would likely exceed the 2-hour box. | **RESOLVED** — H8 assigns a specific control to each: T7 is off the default path with a documented pipe-only degradation escape; T11's restart budget defaults to 0 so the complex path is opt-in; T15 is pure composition over already-tested dependencies and *must be split* if it grows an algorithm. T18 is gated by T1/T2 plus an escape hatch. |
| **F8** | **P2** | "Control plane" invites daemon/database/framework overreach (scheduler, SQLite session store, asyncio rewrite, TUI library). | **RESOLVED** — Plan §6 lists these as explicitly rejected; §11.4 makes daemon/scheduler/database/web-framework/plugin-registry non-goals; §7 confines any Go re-evaluation to a hypothetical future persistent multi-workspace daemon with no work item now. |
| **F9** | **P2** | Secret redaction implemented per-writer would eventually be forgotten by one writer. | **RESOLVED** — H5 makes redaction a single choke point with no raw-write API, registers resolved secret *values* (not just regex patterns), and adds a ≥8-character no-substring-survival property test. |
| **F10** | **P2** | Sidecar degradation (e.g. Engram unavailable) could be mapped onto the supervisor call's own `status`, repeating a documented telemetry defect. | **RESOLVED** — Plan §8 cites compound learning `2026-08-08-state-vs-call-outcome-conflation-in-telemetry-mapping` and requires a sidecar's reported state to stay a per-sidecar typed outcome, never the supervisor's `status`. Telemetry, if emitted, is emitted by the service with `tool_surface` supplied by the adapter. |
| **F11** | **P2** | Templates under `templates/` carry copies of the start scripts; migrating only the repository-root scripts would leave generated workspaces with orphaned inline policy. | **RESOLVED** — T18 scope explicitly includes the `templates/` copies; H9.5 states the guarantee. |
| **F12** | **P2** | A native autoharness MCP server could be re-argued as "the control-plane API". | **RESOLVED** — Plan §11.3 keeps it an explicit non-goal absent a concrete consumer; §2 preserves the three distinct MCP vocabularies (server-framework absence vs. registry-validation vs. telemetry) so the absence claim stays precisely scoped and is not overstated. |

### Cycle 2 findings — 2026-08-10 post-harvest review-fix (PR #325)

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| **F13** | **P0** | **Cascade-close hazard.** The harvested `124-S` manifest listed the covering feature `117-F` alongside the five S1 tasks. Backlogit's `ShipShipment` gates its two destructive covering-feature operations on *explicit manifest membership*: `setArtifactStatus(featureID, done)` and the `collectArchiveCandidateIDs` sweep (which also pulls the feature's descendants and linked deliberations) both fire only when `explicitScope[featureID]` is true. Closing S1 would therefore have marked `117-F` **done and archived it** while 14 of its 19 children (`117.006-T`…`117.019-T`) were still queued in `125-S`/`126-S`, silently destroying two thirds of the program and leaving the serial chain pointing at an archived parent. | **RESOLVED** — `117-F` removed from the `124-S` manifest; all three Plan-1 shipments are now uniformly **task-only** (`125-S`/`126-S` already were). H10.4 added to the hardening doc as an explicit invariant with the engine-level rationale, and restated in the `124-S` shipment description and Plan §10. As a non-member ancestor `117-F` is now skipped by both destructive paths, and `snapshotNonMemberFeatureStatuses`/`restoreRolledUpNonMemberFeatures` revert any incidental parent-status rollup. Verified by re-reading all three manifests after `backlogit sync`. |
| **F14** | **P1** | **Residual `parent_id`-clearing asymmetry (upstream).** The `explicitScope` gate added by backlogit 133-F covers the `done`-marking and archive paths but **not** `returnUnreleasedFeatureItems`, which still runs for every ancestor feature discovered by `featureScopeRoots` — including a non-member one — and clears `parent_id` on that feature's not-yet-released descendants. Closing `124-S` will therefore orphan `117.006-T`…`117.019-T` from `117-F`. Left unaddressed, this would break the derived covering-feature relationship that the F13 fix depends on for traceability. | **SUPERSEDED BY CYCLE 3 — this cycle-2 resolution was REJECTED. See F14-R below.** ~~Severity is P1, not P0, because the effect is a **recoverable relationship change**: statuses, IDs, task content, and shipment memberships are all preserved, and only `parent_id` is cleared — no closure, no archival, no data loss. Mitigation is mandatory and recorded in H10.4, the `124-S` description, and the session memory: Ship re-adopts the orphaned tasks under `117-F` via `backlogit_adopt_item` immediately after closing `124-S`, and again after `125-S`, and verifies parentage before claiming the next shipment. Recorded for a separate upstream backlogit report. It explicitly does **not** justify re-adding the feature to a manifest — that would reinstate F13, a strictly worse and unrecoverable outcome.~~ |

### Cycle 3 findings — 2026-08-10 final review-fix (F14 structural elimination)

Cycle 3 was triggered by an operator determination that F14's cycle-2 resolution
was not acceptable. F14 is **reopened as F14-R** and re-adjudicated below. This
is the last permitted cycle (3 of 3).

| ID | Sev | Finding | Resolution |
|---|---|---|---|
| **F14-R** | **P1** | **F14's `adopt_item` mitigation is invalid; the defect must be structurally eliminated.** Two independent grounds. (a) **P-010 role-boundary violation.** The mitigation assigns Ship a re-parent/adopt mutation after each close. Ship's Role Boundary enumerates claim, move, close, and archive; re-parent/adopt is not enumerated, and the fail-closed rule renders an unenumerated mutation *forbidden*, not merely undocumented. A review cannot discharge a P1 by prescribing a policy violation. (b) **Not reliability-first.** It mandates manual repair after *every* predecessor close, on the precise path where a single missed step silently detaches two thirds of the program — a latent, high-blast-radius failure gated on operator diligence. Consequently the cycle-2 claim of "0 unresolved P1" was not truthful, because the only thing standing between the plan and a 14-task orphaning event was a forbidden manual step. | **RESOLVED — STRUCTURALLY ELIMINATED (no mitigation, no repair step).** The decomposition was redesigned so the destructive code path has nothing to act on. Each serial shipment now owns its own **ROOT** covering feature that is **fully covered** by, and an **explicit member** of, that shipment's manifest (H10.5). Full coverage ⇒ `returnUnreleasedFeatureItems` iterates an empty remainder and returns `∅`; root placement ⇒ `featureScopeRoots`' upward `parent_id` walk cannot reach a sibling shipment's scope. `117-F` is demoted to a **childless** product umbrella, grouped by `related_to` links (which `featureScopeRoots` does not traverse) and closed engine-natively as a member of the final shipment. `adopt_item`, post-close repair, feature reactivation, forbidden status transitions, and operator intervention are all absent from the close path — and are banned by new Non-Goal 11. Proven empirically against the real backlogit 1.8.0 engine: `docs/spikes/2026-08-09-plan1-shipment-topology-proof/sim-shipment-closure.ps1` ARM A reproduces the defect (14/14 orphaned), ARM B shows the redesign closing all three shipments with `returned_ids: []` (60/60); `docs/spikes/2026-08-09-plan1-shipment-topology-proof/verify-plan1-shipment-topology.ps1` replays the exact live topology including the real 27-edge DAG (194/194, `returned_ids: []` on every close). |
| **F15** | **P2** | **Manifest edits are not possible in place.** `AdoptItem` rewrites `parent_id`, hierarchical IDs, filenames, and cross-artifact dependency/link edges, but it does **not** rewrite shipment `custom_fields.items`; and backlogit 1.8.0 exposes no remove-item-from-shipment operation. The old manifests therefore could not be corrected in place. | **RESOLVED.** Replacement shipments `127-S`/`128-S`/`129-S` were created with correct manifests; `124-S`/`125-S`/`126-S` were annotated with supersession rationale and full ID remap tables, linked via `supersedes`, and **archived rather than deleted** so traceability and link targets remain resolvable. Verified by V9 (archived, absent from queue, supersedes links present, zero stale `117.x` artifacts). |

**Upstream report still stands.** The `explicitScope` asymmetry in
`returnUnreleasedFeatureItems` remains a genuine backlogit defect and is still
recorded for a separate upstream report. H10.5 makes *this* plan immune to it;
it does not fix it for other consumers.

### Cycle 4 (post-cycle-limit) — OPEN P1 raised by PR #325 Copilot review on HEAD `48368657`

> **STATUS: UNRESOLVED — BLOCKING. Requires an operator product decision.**
> The 3-cycle plan-review budget was already exhausted, so this finding is
> recorded as **open** rather than silently absorbed. The document verdict is
> therefore downgraded from PASS to **BLOCKED** until F16 is dispositioned. The
> cycle-3 review rejected an untruthful "0 unresolved P1" claim; repeating that
> error here would be a worse failure than reporting the block.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| **F16** | **P1** | **T18's rollback requirements are mutually exclusive.** `120.007-T` mandates that the shim contain **no** legacy shell policy ("NO POLICY DUPLICATION MAY SURVIVE in PowerShell or bash"), which is also hard **DoD #2** ("No orchestration policy remains in PowerShell or bash"). The *same* task simultaneously mandates an `AUTOHARNESS_SUPERVISOR=0` escape hatch that "makes the shim execute the legacy inline path **without a redeploy**". A runtime branch into the legacy inline path requires that path to be present in the shipped shim — which is precisely the duplication the task and the DoD forbid. A git SHA reference is *documentation*; it cannot supply a runtime branch. The contradiction is not confined to the harvested task: it originates in the reviewed plan (§9 rollback bullet, §10 T18) and hardening (H8 T18 row, H10 S3) and propagates into `120.008-T`, which is instructed to document the escape hatch in the migration/rollback runbook. | **OPEN — ESCALATED, NOT DISPOSITIONED.** Resolving it is a genuine product trade-off that Stage may not decide unilaterally after the review budget is spent. **Option A — drop the escape hatch:** rollback becomes a documented single-file revert per shim (plus the `templates/` copies), preserving DoD #2 and the no-duplication invariant intact, at the cost of requiring a redeploy to roll back during the S3 bake. **Option B — retain a versioned legacy implementation:** keep the legacy inline path as an explicitly versioned, separately-named artifact the shim can dispatch to, which **relaxes** DoD #2 and the no-duplication invariant and therefore requires amending the plan, the hardening doc, `120.007-T`, and `120.008-T`. Option A is the smaller blast radius and is consistent with the already-reviewed H9.6 ("rollback is a single-file revert per shim"); Option B is the only one that preserves redeploy-free rollback. **No option is adopted here.** |

**Containment.** F16 affects `120.007-T` and `120.008-T`, both members of
`129-S` — the **final** shipment, gated behind `127-S` and `128-S`. It therefore
does **not** block execution of the eligible cursor `127-S`, and does not
invalidate the F14 structural elimination or any evidence in this document. It
must be dispositioned before `129-S` is claimed.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| **F17** | **P1** | **The plan's "two divergent implementations of the same policy" premise is factually wrong for `start.sh`, and it invalidates S1 acceptance criteria in the ELIGIBLE shipment.** Plan §5 (and the `004-SP` PROCEED reconciliation, and the composability decision doc) assert that `start.ps1` and `start.sh` already implement the same seven-dimension launch policy in two languages. Verified against the working tree: `start.sh` (80 lines) implements **only** `.env.local` no-clobber parsing with quote stripping (lines 20–36), a `COPILOT_HOME` default (54), an unguarded `export GITHUB_TOKEN="$(gh auth token)"` (56), Copilot exe resolution (57–64), and `exec "$copilot_exe" "$@"` (66). It has **no** `ENGRAM_DATA_DIR` default (line 55 is commented out), **no** backlogit sync, **no** Engram pre-warm/fallback, **no** `GITHUB_PERSONAL_ACCESS_TOKEN` handling, and **no** `COPILOT_USE_REMOTE`/`--remote` logic (0 occurrences each). Separately, `start.ps1:65` sets `GITHUB_PERSONAL_ACCESS_TOKEN = (gh auth token)` **unconditionally and unguarded**; the non-fatal `try`/`Write-Warning` path at 68–77 covers `GITHUB_TOKEN` only. Consequences: `118.002-T` requires a suite that "passes against today's `start.sh` unmodified" across "the same seven dimensions" — **unsatisfiable**, because three of those dimensions do not exist in `start.sh`; and `118.001-T`'s criterion (c) that PAT resolution is non-fatal when `gh` is absent or failing **misstates `start.ps1`'s actual behavior**. | **OPEN — ESCALATED. BLOCKS THE ELIGIBLE CURSOR.** Unlike F16, `118.001-T` and `118.002-T` are members of **`127-S`**, so this blocks the shipment Ship would claim first. Resolution requires re-inventorying both scripts and separating *shared* behavior from *PowerShell-only* behavior, then revising the H1 characterize-before-migrate contract so each suite characterizes **its own** script's real contract, with any cross-platform normalization reclassified as an **explicit behavior change** (which S1's "zero observable behavior change" rule forbids, so it must move to S3 or be separately approved). The `004-SP` PROCEED rationale and the composability decision doc's evidence paragraph must be corrected in the same pass, since both rest on the same overstated premise. Stage does not amend them here: the review budget is exhausted and the consolidation thesis underpinning the PROCEED disposition is an operator product decision. |
| **F18** | **P1** | **The plan's state-transition diagram contradicts its own DRAINING rule and the harvested task.** Plan §3.2's diagram routes operator cancellation `CANCELLING -> EXITED`, bypassing `DRAINING`, while the rules immediately below state that DRAINING is the **only** path from RUNNING to a terminal state and always flushes the journal, releases the lock, and reaps the child. `119.006-T` independently mandates `RUNNING -> CANCELLING -> DRAINING -> EXITED`. Implementing the diagram as drawn would leak the workspace lock and the child process and lose journal data on every cancellation. Relatedly, `119.003-T`'s linear state summary omits `LOCKING -> REFUSED`, the bootstrap/resolve/launch failure edges to `FAILED`, and `RESTARTING -> LAUNCHING`; because absent transitions must raise `ILLEGAL_TRANSITION`, implementing that summary verbatim would reject documented outcomes. | **OPEN — low-ambiguity, but still unresolved.** Unlike F16/F17 the correct resolution is not genuinely contested: the diagram is the outlier, and both the prose rules and `119.006-T` already mandate routing cancellation through `DRAINING`. The fix is to correct the §3.2 diagram and complete `119.003-T`'s transition table against Plan §3.2. Stage records rather than applies it because the review budget is exhausted and it is a plan-document amendment. `119.003-T` and `119.006-T` are members of `128-S`, so this does **not** block the eligible cursor `127-S`, but it must be dispositioned before `128-S` is claimed. |

**Revised containment across F16–F18.** `127-S` is **no longer safely
claimable**: F17 invalidates acceptance criteria in `118.001-T` and `118.002-T`,
both S1 members. F18 must be dispositioned before `128-S`; F16 before `129-S`.
None of these findings affect the F14 structural elimination, the shipment
topology, or the 60/60 + 194/194 closure evidence, all of which stand.

## Decomposition check (2-hour rule, width isolation)

* **19 tasks**, each scoped to a single module or a single script surface.
* **No task mixes** template work with CLI work with schema work. T18 is the only
  cross-surface task and it is deliberately a *mechanical* deletion-plus-delegation
  with a pre-existing test gate.
* **No schema changes** anywhere in the plan — `schemas/` is untouched.
* Every task is independently testable; the fake-`ChildProcess` seam removes the
  Copilot dependency from all but one opt-in smoke test.
* Sizes and complexities are assigned on two independent axes; every
  `complexity: high` task has an H8 control.

## Priority assignment

* **P0** — Shipment 1 (T1–T5) and Shipment 2 (T6–T11): process safety,
  contracts, characterization, containment. These are the correctness and
  security substrate.
* **P1** — Shipment 3 (T12–T19): application services, the CLI adapter, the local
  approval path, migration, and documentation. Convenience and UX ride at the
  back, per the operator's fast-track ordering directive.
* No P2-only tasks were harvested.

## Boundary confirmations (explicitly re-verified)

1. Copilot CLI remains the external reasoning/tool-execution runtime; autoharness
   implements **no** action/observation loop. ✅
2. Engram is read-only, non-authoritative, and no supervisor decision depends on
   it. ✅
3. backlogit owns backlog and checkpoints; the session journal is not a
   checkpoint. ✅
4. graphtor owns docs retrieval; untouched. ✅
5. `.autoharness/config.yaml` remains model-routing authority; no model names
   hardcoded; the supervisor does not read model routing at all. ✅
6. Candidate (c) is not implemented; only hook surfaces are exposed. ✅
7. Native autoharness MCP server remains an explicit non-goal. ✅
8. Gradio / devtunnel / remote UI / remote auth / remote approvals / browser
   terminal streaming / remote services are wholly absent and deferred to
   Plan 2. ✅
9. Python-first with a replaceable `ChildProcess` Protocol; no Python+Go split. ✅
10. Every shipment manifest is **fully covered and root-isolated**: each of the
    three manifests contains exactly its own ROOT covering feature (listed
    first) plus every one of that feature's children, and nothing else. The
    product umbrella `117-F` is **childless**, appears in the **final** shipment
    only (listed last), and is grouped to the per-shipment features by
    non-hierarchical `related_to` links (H10.5). ✅ *(re-verified cycle 3;
    supersedes the cycle-2 task-only confirmation, which was found to arm the
    parent-clearing cascade)*
11. **No close path requires `adopt_item`, post-close repair, feature
    reactivation, a forbidden status transition, or any operator intervention.**
    Every shipment closes cleanly and independently under real `ShipShipment`
    execution (H10.5, Non-Goal 11). ✅ *(added cycle 3)*

## Gate outcome

`PASS`. Harvest authorized for Plan 1 only. Plan 2 is design/tracker-only and
must not be harvested into implementation work.

### Cycle 2 gate re-run — 2026-08-10

Re-run against the changed shipment safety contract only; F1–F12 dispositions
were re-read and are unaffected.

* **P0 clear** — F13 resolved; no unresolved P0.
* **P1 clear** — ~~F14 resolved (accepted with a mandatory, recorded Ship-side
  mitigation)~~ **withdrawn in cycle 3 — this P1 clearance was not valid.**
* **Fail-safe direction confirmed** — the correction *removes* a destructive
  capability from the S1 close path rather than introducing a new mechanism that
  must itself be trusted.
* **Verdict: PASS (re-affirmed).** Cycles used: 2 of 3. *(Superseded by the
  cycle-3 gate re-run below.)*

### Cycle 3 gate re-run — 2026-08-10 (FINAL, 3 of 3)

Re-run against the redesigned decomposition. F1–F13 dispositions were re-read
and are unaffected; F13's cascade-close hazard remains disarmed (a fully covered
member feature cannot destroy out-of-scope work, because under full coverage no
out-of-scope work exists).

* **P0 clear** — no unresolved P0. F13 remains resolved.
* **P1 clear** — F14-R **structurally eliminated**, not mitigated. No unresolved
  P1. The clearance rests on executed engine behavior (`returned_ids: []` on
  every close), not on an argument or a promised operator action.
* **Closure simulation discharged** — the mandatory proof obligation is met:
  * closing S1 preserves **all** S2 and S3 `parent_id` values and `queued`
    statuses (14/14 unchanged);
  * closing S2 preserves **all** S3 `parent_id` values and statuses (8/8);
  * S3 closes its own fully covered feature and the childless umbrella,
    terminating with zero non-archived residue;
  * **no** feature outside the closing shipment is marked done, archived, or
    otherwise modified at any step.
* **Structural checks clear** — every task has a valid covering feature; each
  manifest fully covers exactly its own feature's children with no foreign
  items; the 344-edge dependency DAG is acyclic; all 27 Plan-1 task edges
  survived re-parenting with zero dangling references; only the first shipment
  is eligible; zero active/quarantined/error checkpoints; git diff check passes.
* **Fail-safe direction confirmed, strengthened** — H10.5 removes the
  *precondition* for the destructive code path rather than removing a
  capability. `returnUnreleasedFeatureItems` still executes on every close; it
  simply has an empty set to act on.
* **Role-boundary clear** — the close path requires nothing outside Ship's
  enumerated claim/move/close/archive capabilities. The P-010 violation that
  cycle 2 would have required is gone.
* **Verdict: BLOCKED (current).** 0 unresolved P0, **1 unresolved P1 (F16)**.
  Cycles used: **3 of 3 — limit reached, no further review-fix cycle is
  available.** Cycles 1–3 concluded PASS and that conclusion stands for F1–F15;
  the verdict was subsequently downgraded when the PR #325 Copilot review of HEAD
  `48368657` raised **F16**, plus the follow-on findings **F17** and **F18**
  recorded in the Cycle 4 section. Those findings are open and require operator
  disposition; do **not** read this document as an approval to claim `129-S`.
