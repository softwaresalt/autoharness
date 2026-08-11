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

## Verdict: BLOCKED — 0 unresolved P0, **10 unresolved P1 (F16–F25)**

> **Cycle-3 verdict was PASS (0 P0 / 0 P1) and remains accurate as of HEAD
> `48368657` for findings F1–F15.** **Ten** new P1s (**F16** through **F25**)
> were raised by successive PR #325 Copilot reviews of HEADs `48368657`,
> `91538e74`, `d8644c46`, `66f1220f`, `914cb214` and `a20c5b50`, *after* the 3-cycle budget
> was exhausted. Because no review cycle remains and their resolutions are
> genuine product trade-offs, they are recorded as **open and escalated** rather
> than absorbed, and the verdict is downgraded to **BLOCKED**. See the *Cycle 4*
> sections below.
>
> **NO SHIPMENT IS SAFELY CLAIMABLE.** F17 invalidates acceptance criteria in
> `118.001-T` and `118.002-T`, both members of the otherwise-eligible cursor
> `127-S`. F18, F19, F22 and F23 gate `128-S` — and **F22 may also touch `127-S`**
> if the lock-release obligation is placed on `118.005-T` rather than on the
> transition table. **F24 also gates `128-S`**; **F16, F20, F21 and F25 gate
> `129-S`**.
>
> **Three clusters, not ten independent decisions.** F18 + F22 + F23 are one
> missing invariant (cleanup and cancellation are guaranteed only from
> `RUNNING`); F19 + F21 are one missing contract boundary (a shared event/approval
> contract landing after its consumers); **F24 + F25 are one missing *reachability*
> rule** (a capability is specified in one task and no task is obligated to make it
> real — an ignore rule with no installing surface, CLI flags with no exposing
> task). Framing these as three rulings rather than ten is the fastest path off
> BLOCKED. **F25 compounds F22**: `--force-unlock` is the documented remedy for the
> very lockout F22 creates, so one finding sets the trap and the other removes the
> exit.
>
> Cycles 5–7 raised no new P0/P1; **cycle 8 raised F21, cycle 10 raised F22 and
> F23, and cycle 12 raised F24 and F25**. A quiet cycle is not evidence the set is
> complete — this has now been demonstrated **three** times, across three separate
> quiet-then-new-P1 windows. **Finding discovery has not converged**, and that
> non-convergence is itself a reportable result: the correct claim is "no new
> findings in *that* window", never "the set is complete".

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
| **F7** | **P1** | **Four** tasks carry `complexity: high` (T7, T11, T15, T18); without de-risking controls they would likely exceed the 2-hour box. | **RESOLVED** — H8 assigns a specific control to each: T7 is off the default path with a documented pipe-only degradation escape; T11's restart budget defaults to 0 so the complex path is opt-in; T15 is pure composition over already-tested dependencies and *must be split* if it grows an algorithm. T18 is gated by T1/T2 plus an escape hatch. |
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
| **F14-R** | **P1** | **F14's `adopt_item` mitigation is invalid; the defect must be structurally eliminated.** Two independent grounds. (a) **P-010 role-boundary violation.** The mitigation assigns Ship a re-parent/adopt mutation after each close. Ship's Role Boundary enumerates claim, move, close, and archive; re-parent/adopt is not enumerated, and the fail-closed rule renders an unenumerated mutation *forbidden*, not merely undocumented. A review cannot discharge a P1 by prescribing a policy violation. (b) **Not reliability-first.** It mandates manual repair after *every* predecessor close, on the precise path where a single missed step silently detaches two thirds of the program — a latent, high-blast-radius failure gated on operator diligence. Consequently the cycle-2 claim of "0 unresolved P1" was not truthful, because the only thing standing between the plan and a 14-task orphaning event was a forbidden manual step. | **RESOLVED — STRUCTURALLY ELIMINATED (no mitigation, no repair step).** The decomposition was redesigned so the destructive code path has nothing to act on. Each serial shipment now owns its own **ROOT** covering feature that is **fully covered** by, and an **explicit member** of, that shipment's manifest (H10.5). Full coverage ⇒ `returnUnreleasedFeatureItems` iterates an empty remainder and returns `∅`; root placement ⇒ `featureScopeRoots`' upward `parent_id` walk cannot reach a sibling shipment's scope. `117-F` is demoted to a **childless** product umbrella, grouped by `related_to` links (which `featureScopeRoots` does not traverse) and closed engine-natively as a member of the final shipment. `adopt_item`, post-close repair, feature reactivation, forbidden status transitions, and operator intervention are all absent from the close path — and are banned by new Non-Goal 11. Proven empirically against the real backlogit 1.8.0 engine: `docs/spikes/2026-08-09-plan1-shipment-topology-proof/sim-shipment-closure.ps1` ARM A reproduces the defect (14/14 orphaned), ARM B shows the redesign closing all three shipments with `returned_ids: []` (64/64); `docs/spikes/2026-08-09-plan1-shipment-topology-proof/verify-plan1-shipment-topology.ps1` replays the exact live topology including the real 27-edge DAG (196/196, `returned_ids: []` on every close). |
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

**Revised containment across F16–F25.** `127-S` is **no longer safely
claimable**: F17 invalidates acceptance criteria in `118.001-T` and `118.002-T`,
both S1 members. F18, F19, **F22** and **F23** must be dispositioned before
`128-S`; F16, F20 and F21 before `129-S`. **F22 may additionally touch `127-S`**
if the guaranteed-lock-release obligation is placed on `118.005-T` (T5) rather
than on the `119.003-T` transition table.
None of these findings affect the F14 structural elimination, the shipment
topology, or the 64/64 + 197/197 closure evidence, all of which stand.

### Cycle 4 (third Copilot pass, HEAD `d8644c46`) — two further P1s

The third review raised **no new P0/P1 against the topology work** — both of its
top-level comments restated F18. Its suppressed comments, however, surfaced two
additional decomposition/plan defects and a genuine defect **in this review's own
evidence** (recorded below the table).

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| **F19** | **P1** | **Circular ordering between the state machine and its event contract.** `119.003-T` requires `session.py` to emit `SessionPhaseChanged`, but that event type is not defined until `119.004-T`, whose dependency edge points **back** to `119.003-T` (`119.004-T -> 119.003-T`, confirmed in the live graph). The staged implementation therefore cannot satisfy `119.003-T` without either defining the event in the wrong module or implementing `119.004-T` early — i.e. the declared order is unimplementable as written. | **OPEN.** Resolution requires moving the shared event contract into an earlier dependency (or splitting a minimal `events.py` contract task ahead of the state machine) and revising the task/dependency split accordingly. That is a decomposition change to an already-reviewed plan, so Stage records rather than applies it. Members of `128-S`; does **not** affect the eligible cursor `127-S`, but must be dispositioned before `128-S` is claimed. |
| **F20** | **P1** | **The "no mutation" authority boundary contradicts the mandated pre-warm.** Plan §3.1's `Must NOT` contract forbids the service writing a sidecar store, and `120.002-T` states the service "does not mutate backlogit or Engram" — while the *same* task and plan row **require** `backlogit sync` and an Engram bind/sync pre-warm. Those lifecycle calls necessarily refresh tool-managed indexes and state, so an implementation cannot honour both statements literally; whichever reading is taken, the other requirement is violated. | **OPEN.** The intended distinction is almost certainly domain-content/authority mutation (forbidden) versus cache/index lifecycle refresh (required and benign), but that is not what the documents say, and `120.002-T` is a **P1-blast-radius** task. Resolution is to restrict the prohibition to domain-record/authority mutations while explicitly permitting index and lifecycle refresh, consistently in plan §3.1 and `120.002-T`. Member of `129-S`; must be dispositioned before `129-S` is claimed. |

**A defect in this review's own evidence — found, corrected, and disclosed.** The
same pass found that the Part 2 fixture replay was **not** the "isomorphic replay
of the exact live 27-edge DAG" this document claimed: its hand-maintained edge
list carried a spurious `120.004-T -> 119.002-T` edge absent from the live graph
(**28 replayed vs 27 live**), and the original V7 could not detect this because it
only *counted* live edges without comparing them to the replay. Both harnesses
were corrected — V7 now asserts **set equality** against 27 named endpoint pairs,
and Part 2 **derives** its replay from that verified list so drift is impossible
by construction — and both were re-run: **64/64** and **196/196**. The safety
*conclusion* is unaffected (dependency edges play no part in `ShipShipment`'s
parent-clearing path, and the spurious edge only made the replayed graph strictly
more constrained), but the isomorphism *claim* was inaccurate and is corrected
here rather than quietly restated.

### Cycle 4 (fifth Copilot pass, HEAD `df3924f5`) — no new P0/P1; one contract reconciliation

The fifth review raised **no new P0 and no new P1**. Its findings were clerical
(stale counts and a mislabelled fixture comment, all corrected) plus one
substantive **contract reconciliation** and one further vacuous-assertion defect
in this review's evidence. Neither changes the finding ledger: the open set
remains exactly **F16, F17, F18, F19, F20**.

**Contract reconciliation — close-path guidance vs. these manifests.** The
durable compound rule `docs/compound/097-S-shipment-task-only-safe-close.md`
states that a shipment manifest must be task-only and must never list its
covering feature. `127-S`/`128-S`/`129-S` deliberately do the opposite, so Ship
would have received two contradictory close instructions. Adjudicated as **two
hazards, two manifest shapes**:

* the durable rule governs **partial-feature** manifests, where the covering
  feature retains children outside the manifest and a broad close cascades into
  unshipped siblings — unchanged and still correct;
* task-only membership does **not** confer safety on its own, because
  `returnUnreleasedFeatureItems` is not gated by `explicitScope` and also runs
  for a non-member **ancestor** feature reached by the `featureScopeRoots`
  upward walk (ARM A reproduces this and orphans 14/14 downstream tasks);
* the **fully-covered root** shape — every child in the manifest, feature has no
  parent — makes the cascade *structurally impossible*, which is the shape these
  three shipments were redesigned into under H10.5.

Recorded as an append-only reconciliation section in the compound doc (original
rule preserved verbatim, plus a table stating which contract applies to which
shape) and cross-referenced from all three manifests and the spike README.
Documentation only: no topology, task, dependency edge, or manifest changed.

**A further vacuous assertion in the evidence, corrected.** V10's proof that
pre-existing out-of-scope backlog debt was left untouched piped
`git --no-pager status` directly into a filter. `git` is a native call, so a
nonzero exit yields empty output, zero rows match, and the assertion would have
passed **vacuously** — "no matches" silently read as "untouched". It now
captures, checks `$LASTEXITCODE`, throws on failure, and only then filters. This
is the third instance of the same root cause in these harnesses (native nonzero
exits do not terminate under `$ErrorActionPreference = 'Stop'`). Both harnesses
re-run after the fix: **64/64** and **196/196**, V7 set-equality clean.
### Cycle 4 (sixth Copilot pass, HEAD `e50fc808`) — no new P0/P1; evidence and record defects

The sixth review raised **no new P0 and no new P1**. Its four suppressed comments
were all valid and are all fixed. The open finding set is unchanged at exactly
**F16, F17, F18, F19, F20**.

Two landed on this review's own evidence:

* **A hardened assertion that was measuring the wrong proposition.** Cycle 5
  added `$LASTEXITCODE` handling to V10's `git status` call — a real fix, but
  `git status` was the wrong instrument. It reports only *uncommitted* worktree
  changes, so on the committed HEAD every published run executes against, it
  returns nothing for the pre-existing-debt paths **whether or not this branch
  changed them**; the assertion passed vacuously on any clean checkout. V10 now
  derives the branch footprint from `merge-base(origin/main, HEAD)..HEAD` and
  unions in the worktree status. Re-verified: 60 `.backlogit` files touched by
  the branch, **zero** of them pre-existing-debt artifacts — the claim was true,
  but is now actually proven.
* **A printed result treated as an asserted one.** The closure simulation printed
  `backlogit doctor` at the terminal fixture state without asserting it.
  `doctor` exits 0 while reporting findings (V10 relies on that), so the proof
  could have passed against a dirty fixture. Now asserted. The simulation total
  rises to **64/64**; the verifier is unchanged at **196/196**.

Two were defects in the planning record, both corrected:

* H8 of the hardening record stated "Three tasks carry `complexity: high`" while
  its own table lists **four** — T7, T11, T15, T18 — matching exactly the four
  queued tasks whose `complexity` is `high` (`119.002-T`, `119.006-T`,
  `120.004-T`, `120.007-T`). The same undercount had propagated into F7 above and
  is corrected there too.
* The deferred Plan-2 credential-rotation runbook attributed the redaction choke
  point to **T5**, which is workspace/session locking. It is **T4**
  (`supervise/redact.py`, harvested as `118.004-T`). Corrected so the
  credential-response control traces to its actual implementation task.

### Cycle 4 (seventh Copilot pass, HEAD `857e208d`) — no new P0/P1 (heading claim of a "stable" set RETRACTED below)

The seventh review raised **no new P0 and no new P1**. Its three suppressed
comments were all valid consistency defects and are all fixed. The open finding
set is unchanged at exactly **F16, F17, F18, F19, F20** across cycles 5, 6 and 7,
each of which produced only evidence-robustness or record-consistency defects and
never a new plan finding.

> **RETRACTED.** As originally written, this paragraph read that three-cycle
> quiet window as evidence that the blocking set was *stable* — i.e. complete.
> Cycle 8 raised **F21**, a genuine new P1, and falsified it. Absence of new
> findings in a window is not evidence of completeness; it is only evidence about
> that window. The accurate statement is "no new findings in cycles 5-7".

* **The documented `-Repo` invocation did not work.** A relative `-Repo` passed
  the initial `.backlogit` existence check (resolved against the *invocation*
  directory) but was stored unresolved, so V9's archive probes and the final
  `Set-Location $repo` — which runs from the temp fixture — would re-resolve it
  against a different directory. The advertised out-of-tree reproduction path was
  broken for exactly the users it was added for. `-Repo` is now canonicalized
  with `Resolve-Path` before any `Set-Location`, and the harness was re-run with
  `-Repo .` to prove the documented path executes. Same failure family as cycle
  6: a correctness property that was documented but never executed.
* **The Ship handoff checkpoint recorded a stale reviewed HEAD** (`df3924f5`
  against a PR declaring `857e208d`), so a consumer restoring it would have
  picked up stale review provenance. Reconciled to the current HEAD with the full
  supersession chain and the cycle-5/6/7 outcome.
* A safety-properties line in the spike README still described fixtures as
  created under `$env:TEMP`, contradicting the portability fix and its own
  explanation later in the same file. Corrected.

Assertion totals are unchanged by this cycle: **64/64** and **196/196**.

### Cycle 4 (eighth Copilot pass, HEAD `66f1220f`) — a NEW P1: F21

**This cycle retracts the stability claim made one cycle earlier.** Section
"seventh Copilot pass" above recorded that the blocking set had been stable
across three consecutive reviews and treated that as evidence the set was
complete. The eighth review raised a **new P1**, so that inference was wrong and
is withdrawn. Three quiet cycles were not evidence of completeness; they were
three cycles that happened not to surface the next defect. The open set is now
**six**: F16, F17, F18, F19, F20, **F21**.

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| **F21** | **P1** | **The fail-closed approval channel can be omitted from the shipped runtime without any task failing.** Verified against the live dependency graph: `120.005-T` (T16, `approvals.py`) **depends on** `120.004-T` (T15, `run_session()`) and has **zero reverse dependencies** — nothing in the program depends on it. The runtime chain `120.004-T` → `120.006-T` (T17, CLI adapter) → `120.007-T` (T18, shims) → `120.008-T` (T19, docs) is fully satisfiable with `120.005-T` never started. Yet T15 is specified as **the single orchestrator**, and plan §3.6 places the approval exchange inside supervisor runtime behaviour. T15's acceptance can therefore be met against a `run_session()` with no approval path, and no later task forces the wiring — so the **H2 fail-closed guarantee** (non-interactive approvals resolve to a declared safe default or `REFUSED`, never silent auto-approval) is a *safety* control this ordering permits to be silently dropped. | **OPEN.** Same family as F19 — a shared contract ordered downstream of its only consumer — but with a safety consequence rather than only an unimplementable order. Resolution options: **(A)** split the approval *contract* (typed request/response + fail-closed semantics) into a task ordered **before** T15, make T15 depend on it, leave console rendering downstream; **(B)** keep T16 whole, make T15 depend on it, and move the approval-path integration tests into T15's DoD; **(C)** attach an explicit wiring obligation, with a test asserting `run_session()` routes approvals through `approvals.py`, to a task already on the runtime chain. **(A) matches the direction already recorded for F19, so one decomposition change could discharge both.** Requires an operator product decision; Stage adopted none and changed no dependency edge. Member of `129-S`, which is now gated by **F16, F20 and F21**. |

The review's second suppressed comment concerned the durable Ship checkpoint,
which kept recording a *stale* reviewed HEAD each time it was updated — because a
commit cannot embed its own resulting SHA, so naming the "current" HEAD inside
the committed artifact is structurally unwinnable. Fixed by changing what the
field claims: it now records the **evidence HEAD** (the tree the 64/64 + 196/196
run was executed against) and points to the PR readiness record for
current-HEAD coverage, instead of asserting a "current" value it cannot hold.

Assertion totals are unchanged: **64/64** and **196/196**. F21 is a decomposition
and safety-ordering defect; it does not touch the topology, the 27 dependency
edges, or the closure evidence.

### Cycle 4 (ninth Copilot pass, HEAD `11de7aba`) — no new P0/P1; consistency fallout from recording F21

The ninth review raised **no new P0 and no new P1**. All four suppressed comments
were consistency defects introduced by the F21 recording pass itself, and all are
fixed. The open set remains **F16–F21**.

* This document's **top-level verdict summary** still described five post-budget
  findings and omitted F21 from the gate map, while its own header and final gate
  re-run already said six — so a reader stopping at the summary would have
  concluded `129-S` was gated only by F16/F20. Reconciled.
* `117-F`'s hardening summary still said "the three complexity-high tasks" — the
  same undercount corrected in H8 and **F7** a cycle earlier, not yet propagated
  into the live feature record. Now names all four (T7, T11, T15, T18) with their
  live IDs.
* The durable checkpoint attributed **all six** P1s to five reviews ending at
  `df3924f5`, which is internally impossible since F21 was raised in cycle 8 on
  `66f1220f`. Corrected to the full eight-review HEAD range, retaining the
  evidence-HEAD distinction.
* **`117-F`'s event log still ended with "NEVER re-add 117-F to a manifest"** —
  the opposite of the current close contract, since H10.5 deliberately makes the
  childless umbrella an explicit member of the final shipment `129-S`. A
  log-based consumer reading only the event stream would have received an
  instruction contradicting every other artifact. Fixed by **appending** a
  superseding comment event (the historical event preserved verbatim, not
  rewritten) that records why the original was correct for its topology and why
  it no longer applies.

Assertion totals unchanged: **64/64** and **196/196**.

### Cycle 4 (tenth Copilot pass, HEAD `914cb214`) — TWO NEW P1 (F22, F23); open set now EIGHT

The tenth review reported "no new comments" at top level with **five suppressed
comments**. Three were defects in my own evidence and records and are fixed. Two
are **new P1 plan findings**, verified against the plan text rather than accepted
on assertion. The open set is now **F16–F23**.

Both new findings are instances of one structural gap: **the plan guarantees
cleanup only from `RUNNING`.** Rule 2 of §3.2 states that `DRAINING` "is the only
path to a terminal state **from `RUNNING`**", and `DRAINING` is where the plan
places journal flush, lock release and child reaping. Every phase between
`LOCKING` and `RUNNING` therefore has terminal edges with no defined cleanup.

#### F22 (P1, OPEN, NEW): post-`LOCKING` failures terminate without releasing the workspace lock

`§3.2` routes three failure edges straight to `FAILED`, all of them *after*
`LOCKING` has already succeeded:

* `BOOTSTRAPPING ─(fatal)→ FAILED`
* `RESOLVING ─(no copilot exe)→ FAILED`
* `LAUNCHING ─(spawn error)→ FAILED`

None passes through `DRAINING`, so on this plan the lockfile is never released.
`§3.4` then makes the consequence durable rather than transient: **"Lock
contention → `REFUSED` (never auto-break). Stale lock (dead PID / mismatched
start-time) requires an explicit operator `--force-unlock`."** The fail-closed
stale policy is deliberate and correct on its own; combined with the missing
cleanup edges it converts an ordinary failure into a **persistent self-inflicted
lockout of the operator's own workspace**.

The severity comes from *which* failure triggers it. `RESOLVING ─(no copilot
exe)` is the single most likely first-run outcome on a machine where the Copilot
CLI is not on `PATH` — so the plan's most probable first failure leaves the
workspace locked, and the operator must discover an undocumented
`--force-unlock` before they can retry. Every retry fails the same way.

Owners: `119.003-T` (T8, transition table) and `118.005-T` (T5, lock lifecycle).
Note that `118.005-T` sits in **`127-S`**, so a fix that puts the release
obligation on T5 (for example scope-guarding acquisition so release is
structural) touches the first shipment, whereas a fix in the transition table is
confined to `128-S`.

#### F23 (P1, OPEN, NEW): `119.006-T`'s "cancel during launch" test is unsatisfiable

`119.006-T` lists `cancel during launch` among its required tests, but §3.2
defines exactly one cancellation edge, `RUNNING ─(operator cancel)→ CANCELLING`,
and Rule 1 states that transitions outside the table are rejected with
`ILLEGAL_TRANSITION`. A cancel request while `LAUNCHING` can therefore only be
*refused* — which contradicts the cancellation contract stated in the same task
("operator cancel drives `RUNNING → CANCELLING → DRAINING → EXITED`, …
releasing the lock").

This is the same defect class as **F17**: a task carries acceptance criteria that
the fixed contract it depends on cannot satisfy. Left unresolved the implementer
either silently drops the test — leaving cancellation during a slow bootstrap or
resolve undefined — or unilaterally invents a state-machine edge, diverging from
the contract `119.003-T` owns and that `119.004-T`/`119.005-T` are written
against.

#### These two, plus F18, are one decision

F18 (`CANCELLING → EXITED` bypassing `DRAINING`), F22 (post-lock failures
bypassing `DRAINING`) and F23 (no pre-`RUNNING` cancellation edge) are three
symptoms of the same missing invariant. A single operator ruling — *"once
`LOCKING` succeeds, every terminal exit routes through `DRAINING`, and operator
cancel is legal from every post-`LOCKING` phase"* — discharges all three and
turns Rule 2 into an unconditional guarantee instead of a `RUNNING`-scoped one.
Stage has NOT adopted this; it is recorded as the recommended framing for the
operator decision, alongside F21's Option A which would likewise discharge F19.

#### Non-blocking defects in Stage's own artifacts (all fixed)

* **V4 claimed to verify `related_to` links but did not test `link_type`.** The
  assertion projected only `target_id`, so a link of *any* type — including the
  hierarchical or `blocks` edge this proof exists to rule out for the umbrella —
  would have passed, and Part 2 would then have replayed a relationship the live
  topology does not have. This is the **fourth** instance of the recurring family
  "the assertion is robust but tests the wrong proposition". Fixed by filtering on
  `link_type` first *and* asserting that the set of non-`related_to` outgoing
  links is empty, so a stray edge cannot hide behind a passing lookup.
* **V10's base ref was hardcoded to `origin/main`**, which is not guaranteed in
  the "any clone" the proof advertises (source archive, fork with a differently
  named remote, pruned remote-tracking refs). V10 would abort before the topology
  proof ran. Now resolves tracked upstream → `origin/main` → `origin/master` →
  `main` → `master`, with an explicit `-BaseRef` override, failing only when none
  resolves.
* **The checkpoint's structured `decisions` collection still carried the retired
  state**: decision #4 recorded the gate as `PASS, 0 P0 / 0 P1`, and decision #8
  recorded the retired 117.x/124-126-S topology. The corrections existed only in
  `tasks_remaining` and the free-form `resume_hint`, so a consumer reading
  `decisions` as authoritative received stale state. Fixed **append-only**: two
  explicit superseding decisions now carry the BLOCKED verdict and the
  127/128/129-S topology, with the originals preserved verbatim.

### Cycle 4 (twelfth Copilot pass, HEAD `a20c5b50`) — TWO NEW P1 (F24, F25); open set now TEN

Two more new P1s, both **reachability** defects: a capability is specified in one
task and **no task is obligated to make it real**, so the DAG is satisfiable with
the capability absent. Open set is now **F16–F25**.

#### F24 (P1, OPEN, NEW): `119.005-T` targets a gitignore template that does not exist

`119.005-T` requires "Add `.autoharness/sessions/` to the gitignore template."
**There is no gitignore template in this repository.** Verified: `templates/`
contains no `*gitignore*` artifact, and the root `.gitignore` covers only this
dogfood checkout. Target-workspace ignore rules are handled **procedurally** by
`.github/skills/install-harness/SKILL.md`, which *confirms* an existing workspace
`.gitignore` ignores `.env.local` rather than rendering a template.

Two consequences:

* **Unsatisfiable by vacuity.** The criterion is "met" by searching for a
  nonexistent artifact and finding nothing to change. Same class as F17 and F23,
  but **worse**, because it fails *silently* — nothing forces the implementer to
  notice.
* **It falsifies an H6 hardening property.** The same task asserts the journal is
  "gitignored local operational state" and leans on that for authority
  containment. If nothing installs the rule into generated workspaces, that is
  simply untrue there: every supervised session writes JSONL under
  `<workspace>/.autoharness/sessions/` and git tracks it. The journal is redacted
  at the `118.004-T` choke point so this is not a direct secret leak, but
  operational session state would be committed to every consumer repository and a
  documented hardening guarantee would be unbacked.

Resolution requires assigning the rule to the surfaces that actually install
workspace files (install-harness skill, tuner) and requiring a real
`git check-ignore` test in a disposable target workspace. That likely moves scope
out of S2 and into the installer surfaces — a **shipment-boundary** question, not
a wording fix. Gates `128-S`.

#### F25 (P1, OPEN, NEW): the CLI task never defines the option contract, so two operator controls are unreachable

`120.006-T` is the **only** task that touches the CLI, and it does not enumerate
the `autoharness run` options. Two controls are specified elsewhere with no task
obligated to expose them:

* **`--force-unlock`** — required by `118.005-T` (T5, `locking.py`) and §3.4;
* **`--max-restarts N`** and resume-from-cursor — required by `119.006-T` (T11,
  `recovery.py`).

Neither T5 nor T11 touches `cli.py`. `120.006-T`'s tests cover "argument parsing,
human and `--json` rendering, and exit-code propagation" but never say *which
arguments*. So every task can pass while these controls remain unreachable from
the product's sole public surface — **structurally identical to F21**.

**F25 is sharper than F21 because it compounds with F22.** `--force-unlock` is the
documented remedy for exactly the lockout F22 creates. If no task must expose that
flag, **the escape hatch for the lockout is itself unreachable**, and the
operator's only recourse is deleting the lockfile by hand. One finding creates the
trap; the other removes the exit. Gates `129-S`.

#### Non-blocking defects (all fixed)

* **A fifth instance of the recurring family, in `Invoke-Sql`.** It returned `@()`
  whenever the output contained no JSON array marker — so a format change, a
  truncated read or an unexpected banner would have been indistinguishable from
  "zero rows". Several of the strongest proofs here are **zero-result** proofs
  (V8's "`127-S` has no dependencies", V9's "no stale `117.x` tasks", V4's "`117-F`
  has no children"), and every one of them would have passed vacuously. It now
  throws: an absent array marker means the query did not report its result, which
  is a harness failure, not an empty set.
* **`118-F` still called `127-S` "the ONLY eligible shipment in the chain"** while
  the shipment record says **DO NOT CLAIM**. Feature records are a consumer
  surface, so a Ship reader could have taken that as authorization. It now
  distinguishes *structural eligibility* (a scheduling fact) from *claimability*
  (a gate decision), names F17 as the current block, and notes the F22/F24
  exposure.

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
* **Verdict: BLOCKED (current).** 0 unresolved P0, **10 unresolved P1s (F16–F25)**.
  Cycles used: **3 of 3 — limit reached, no further review-fix cycle is
  available.** Cycles 1–3 concluded PASS and that conclusion stands for F1–F15;
  the verdict was subsequently downgraded when the PR #325 Copilot review of HEAD
  `48368657` raised **F16**, plus the follow-on findings **F17**–**F25** recorded
  in the Cycle 4 sections. All ten are open and require operator disposition.
  Do **not** read this document as an approval to claim **any** shipment:
  **F17 gates `127-S`**, **F18 + F19 + F22 + F23 + F24 gate `128-S`** (with
  **F22** potentially touching `127-S` as well), and
  **F16 + F20 + F21 + F25 gate `129-S`**.
* **Three rulings, not ten.** F18 + F22 + F23 collapse into one invariant
  (*every terminal exit after `LOCKING` routes through `DRAINING`, and operator
  cancel is legal from every post-`LOCKING` phase*); F19 + F21 collapse into one
  contract-placement ruling (*where the shared event/approval contract lives and
  which task owns it*); **F24 + F25 collapse into one reachability ruling**
  (*every specified capability must have a task obligated to make it reachable —
  an ignore rule needs an installing surface, a CLI flag needs an exposing task*).
  F16, F17 and F20 remain genuinely independent. **F25 is not merely analogous to
  F22, it compounds it**: `--force-unlock` is F22's own documented remedy, so
  resolving F22 without F25 leaves the lockout with no reachable exit.
