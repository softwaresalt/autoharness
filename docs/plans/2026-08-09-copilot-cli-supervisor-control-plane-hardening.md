---
title: "Plan Hardening (P-006) — Local Copilot CLI Supervisor / Control Plane (Plan 1)"
date: "2026-08-09"
description: "P-006 plan hardening for the Plan 1 local Copilot CLI supervisor/control-plane plan. Enumerates blast-radius controls, fail-closed invariants, backward-compatibility guarantees, and de-risking for the high-complexity tasks."
doc_type: plan-hardening
source: docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-hardening.md
plan_id: "PLAN-1"
stash_ids: ["34D50F2D"]
model_route:
  model_family: claude-opus-5
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md"
  - ".backlogit/archive/004-SP.md"
tags: ["P-006", "hardening", "supervisor", "copilot-cli", "34D50F2D", "candidate-a"]
---

# Plan Hardening (P-006) — Local Copilot CLI Supervisor / Control Plane

## Blast-radius summary — hardening REQUIRED

The plan rewrites **`start.ps1` and `start.sh`**, which are the entry point every
operator and every generated workspace uses to launch the agent runtime, plus
their `templates/` counterparts (so the blast radius extends to every future
installed workspace), plus packaging (`pyproject.toml` entry points and an
optional dependency extra). A defect here does not degrade a feature — it
prevents the harness from starting at all, in this repository *and* in every
downstream workspace generated from the templates. It additionally introduces
child-process spawning and secret-bearing log persistence, which are security
surfaces the product does not currently have.

`Requires plan hardening: yes.`

## H1 — Characterize-before-migrate is a hard ordering constraint, not a preference

**Risk.** The single largest failure mode is silently changing `start.ps1`
semantics while "porting" them. The current behavior is subtle: no-clobber
`.env.local` precedence, single-pair quote stripping, `--remote` added only when
`COPILOT_USE_REMOTE` is `true`/`1` **and** the operator did not already pass
`--remote`, non-fatal sidecar failures, and `throw` on unresolvable Copilot.

**Hardening.**

1. T1/T2 (characterization) are **P0 and land in Shipment 1**, before any service
   exists. Shipment 2 and 3 are blocked on Shipment 1 by explicit `blocks` edges.
2. T18 (shim conversion) has an acceptance criterion that T1/T2 are re-run
   **byte-identical** — no test may be edited to accommodate the migration. If a
   characterization assertion must change, that is a **product decision requiring
   operator sign-off**, not an implementation detail.
3. The characterization suites must assert the *observable contract* (env state,
   argv handed to the child, exit code), not internal script structure, so the
   shims can satisfy them.

## H2 — Fail-closed invariants

| Invariant | Fail-closed behavior |
|---|---|
| Workspace lock contention | `REFUSED` terminal state. **Never** auto-break a lock whose PID is live. Stale lock (dead PID or start-time mismatch) still requires explicit `--force-unlock`. |
| Path containment | Every supervisor write path is resolved and asserted inside the workspace root **before** the write. A path escaping the root aborts the session; it is never "clamped" or silently rewritten. |
| Redaction | If the redactor cannot process a record, the record is **dropped with a warning**, never written raw. Redaction failure never degrades to pass-through. |
| Illegal state transition | Raises `ErrorKind.ILLEGAL_TRANSITION`; the session drains and fails. There is no permissive fallback transition. |
| Non-interactive approval | Resolves to a declared safe default, or `REFUSED` where none exists. **Never auto-approves.** |
| Restart budget | Default **0**. Restart requires both remaining budget and explicit operator confirmation. Budget exhaustion drains to a terminal state; it never loops. |
| PTY unavailable | Degrades to pipe with a recorded warning. A *requested-and-unavailable* PTY never silently becomes an interactive-looking pipe without that warning. |
| Copilot CLI unresolvable | Fatal `FAILED` with the current actionable message. Never falls back to a guessed path. |

## H3 — Exit-status fidelity (regression-class defect already in the corpus)

Compound learning `2026-08-08-shell-pipeline-exit-status-masking-in-version-probes`
records this exact class of bug in this repository's shell scripts: a trailing
`|| true` discarded a pipeline's failure while partial stdout still implied
success.

**Hardening.** The child's exit code propagates verbatim through
`ChildProcess.wait()` → `SupervisorResult.exit_code` → process exit. Explicitly
prohibited: `|| true` / `-ErrorAction SilentlyContinue` around the child launch
in the shims, inferring success from non-empty output, and remapping a non-zero
child exit into a supervisor-level status. A dedicated test asserts a table of
child exit codes (0, 1, 2, 42, 130) round-trips unchanged through both the pipe
and PTY backends **and** through both shims.

## H4 — Subprocess safety

Compound learning `2026-07-01-subprocess-validation-gating` documents the
injection surface from interpolating paths into command strings.

**Hardening.** Argv-array spawn only; `shell=True` is prohibited and asserted
against in tests. Operator passthrough args are forwarded **verbatim as a list**
and never re-parsed, re-quoted, joined, or filtered. Sidecar invocations
(`backlogit sync`, `engram sync/bind`) likewise use argv arrays with resolved
absolute executable paths.

## H5 — Secret handling is a single choke point

**Risk.** Three writers (events, journal, console) could each grow their own
redaction, and one of them will forget.

**Hardening.** There is exactly **one** persistence/emit path, and it runs the
redactor. `journal.py` and `events.py` must not expose a raw-write API. Property
tests assert that for a generated secret `S`, no substring of `S` of length ≥ 8
appears in any produced journal file, event payload, or `SupervisorResult`.
Resolved secret *values* (not just patterns) are registered with the redactor at
bootstrap, so a token that does not match any regex is still redacted.

## H6 — Authority containment (backlogit / Engram / graphtor / config)

**Risk.** A session journal with checkpoints and a resume cursor looks a lot like
a backlog checkpoint store, and an event bus looks a lot like a place to let
Engram drive.

**Hardening.**

1. The session journal is **gitignored local operational state**. It must not be
   referenced as a backlog artifact, must not be read by any agent-recovery
   protocol, and must not be presented as a checkpoint. **backlogit remains the
   sole authority for backlog items and agent checkpoints.**
2. Engram stays **read-only with no execution or mutation authority**. No
   supervisor decision (restart, approval, cancellation, phase transition) may
   read from or depend on Engram.
3. graphtor-docs is untouched.
4. `.autoharness/config.yaml` remains the model-routing authority. The supervisor
   does not select, name, or hardcode models; it does not read model routing at
   all in Plan 1.
5. Plan-review must explicitly confirm all four.

## H7 — Anti-drift guard against candidate (c) and against Plan 2

**Risk.** The event bus is precisely the hook a background Verification &
Compaction layer (candidate (c)) needs, and "just add a small web view" is one
import away from Plan 2.

**Hardening.**

1. Plan 1 ships **zero** event subscribers beyond the journal and console
   renderer. No background thread performs verification, summarization, or
   compaction.
2. A test asserts the supervisor opens **no listening socket** (no `bind`/`listen`
   in `supervise/`), and a repository-level check asserts `supervise/` imports
   nothing from `gradio`, `fastapi`, `flask`, `uvicorn`, `aiohttp`, or a devtunnel
   client.
3. Candidate (c) remains a separate, later capability with its own
   spike → impl-plan → plan-review → harvest cycle; `34D50F2D` stays ACTIVE as its
   living tracker.

## H8 — De-risking the high-complexity tasks

Three tasks carry `complexity: high`. Each gets an explicit de-risking control so
"high complexity" does not silently mean "> 2 hours".

| Task | Why high | De-risking control |
|---|---|---|
| **T7** — PTY/ConPTY backend | Platform-divergent, optional dependency, hardest to test | Bounded by the `ChildProcess` Protocol already fixed by T6. Scope is *one* class. Not on the default path. If `pywinpty` integration exceeds the box, the fallback is to ship pipe-only and re-file PTY as a follow-up — the plan degrades gracefully. |
| **T11** — cancellation / restart / resume | Concurrency + partial state | State machine (T8) and journal (T10) are already fixed contracts. Restart budget defaults to **0**, so the default path is "cancel and drain" — the complex restart path is opt-in and separately testable against the fake child. |
| **T15** — `run_session()` orchestration | Integrates everything | Pure composition: every dependency (T6, T8, T10, T12, T13, T14) is already implemented and independently tested. T15 adds no new algorithm; if it grows one, that is a decomposition failure and the task must be split. |
| **T18** — shim migration | Highest blast radius | Gated by the unchanged T1/T2 suites, plus the `AUTOHARNESS_SUPERVISOR=0` escape hatch and a single-file-revert rollback. |

## H9 — Backward-compatibility guarantees (explicit contract)

1. `./start.ps1 <args>` and `./start.sh <args>` continue to work with identical
   observable behavior and identical exit codes.
2. Every currently-honored environment variable keeps its meaning **and its
   precedence**: `COPILOT_HOME`, `ENGRAM_DATA_DIR`, `GITHUB_TOKEN`,
   `GITHUB_PERSONAL_ACCESS_TOKEN`, `COPILOT_EXE_PATH`, `COPILOT_EXE`,
   `COPILOT_USE_REMOTE`, and every `.env.local` key.
3. The base install gains **no new required dependency**; PTY is an optional
   extra.
4. The existing 10 top-level / 17 leaf CLI commands are unchanged. `autoharness
   run` is purely additive.
5. Workspaces generated from `templates/` receive the shim; no generated
   workspace is left with orphaned inline policy.
6. Rollback is a single-file revert per shim, with the Python package able to
   remain installed and dormant.

## H10 — Shipment gating

The three shipments form a **strict serial chain** with explicit `blocks` edges:
`S1 → S2 → S3`. Only S1 is eligible at harvest time.

* **S1** must land with **zero observable behavior change** — pure additions plus
  characterization tests. If S1 changes any existing behavior, it is
  mis-decomposed.
* **S2** must land as an **unwired library** — nothing in `cli.py`, `start.ps1`,
  or `start.sh` calls it yet.
* **S3** is the only shipment permitted to change observable behavior, and it
  lands behind the S1 characterization gate plus the `AUTOHARNESS_SUPERVISOR=0`
  escape hatch.

### H10.4 — Task-only manifests (SUPERSEDED by H10.5 on 2026-08-10)

> **STATUS: SUPERSEDED — DO NOT APPLY.** H10.4 required task-only manifests with
> a single shared covering feature `117-F`, and absorbed the resulting
> parent-clearing defect as review finding F14 (P1) with a "Ship re-adopts via
> `adopt_item`" mitigation. Cycle-3 plan review **rejected** that mitigation on
> two independent grounds:
>
> 1. **Role-boundary violation (P-010).** Ship's Role Boundary enumerates claim,
>    move, close, and archive. Re-parent/adopt is not an enumerated Ship
>    capability, and the fail-closed rule makes an unenumerated mutation
>    forbidden, not merely undocumented.
> 2. **Not reliability-first.** It requires fragile manual repair after *every*
>    predecessor close, on the exact path where a missed step silently detaches
>    two thirds of the program.
>
> H10.4's *analysis* of the `explicitScope` gate remains correct and is retained
> below for provenance; its *prescription* (task-only manifests, shared covering
> feature) is replaced wholesale by **H10.5**. The residual-hazard paragraph that
> accepted F14 is withdrawn — F14 is now structurally eliminated, not mitigated.

**Retained analysis (still true of backlogit 1.8.0).** `ShipShipment` resolves
covering features by walking `parent_id` upward from the explicitly listed
members (`featureScopeRoots`), but it gates the *destructive* operations on
**explicit membership**:

* `setArtifactStatus(featureID, done)` fires **only** when
  `explicitScope[featureID]` is true.
* `collectArchiveCandidateIDs` adds the feature — plus its descendants and its
  linked deliberations — to the archive set **only** when
  `explicitScope[featureID]` is true.
* A covering feature that is merely a non-member ancestor is snapshotted by
  `snapshotNonMemberFeatureStatuses` and any incidental parent-status rollup is
  reverted by `restoreRolledUpNonMemberFeatures`.

**The gap H10.4 could not close.** `returnUnreleasedFeatureItems` is **not**
gated by `explicitScope`. It runs for *every* feature returned by
`featureScopeRoots` — member or not — and for each descendant outside the
release scope it forces `status → queued` and calls `clearParentID`. Excluding
the feature from the manifest therefore disarms the `done`/archive cascade but
**arms** the parent-clearing cascade. Under H10.4, closing `124-S` would have
cleared `parent_id` on all 14 downstream tasks. This is reproduced as ARM A of
`docs/spikes/2026-08-09-plan1-shipment-topology-proof/sim-shipment-closure.ps1` (14/14 orphaned — the defect is real, not
theoretical).

### H10.5 — Per-shipment ROOT covering features, fully covered and explicitly a member

**Invariant (two clauses, both required).** For every shipment in this chain:

1. **FULL COVERAGE** — every descendant of the shipment's covering feature is in
   that same shipment's release scope. Then
   `returnUnreleasedFeatureItems(feature, releaseScope)` iterates an empty
   remainder set, returns `∅`, and clears **no** `parent_id`.
2. **ROOT PLACEMENT** — the covering feature has no parent feature
   (`parent_id == ""`). Then `featureScopeRoots`' upward `parent_id` walk
   terminates at that feature and **cannot escape** into a sibling shipment's
   scope.

Both clauses are load-bearing and neither is sufficient alone. In particular,
nesting the per-shipment features under `117-F` would satisfy (1) but violate
(2): closing S1 would walk `118.001-T → 118-F → 117-F` and then orphan
everything under `119-F` and `120-F` — strictly worse than H10.4. **The
per-shipment covering features MUST remain root-level.**

**Resulting topology.**

| Shipment | Covering feature (ROOT) | Tasks | Feature is a manifest member? |
|---|---|---|---|
| `127-S` (S1) | `118-F` | `118.001-T`…`118.005-T` | yes, listed **first** |
| `128-S` (S2) | `119-F` | `119.001-T`…`119.006-T` | yes, listed **first** |
| `129-S` (S3, final) | `120-F` | `120.001-T`…`120.008-T` | yes, listed **first**; `117-F` listed **last** |

**Why the covering feature is now an explicit member (reversing H10.4).**
Because each feature is *fully covered*, membership is strictly **safer** than
non-membership:

* Member + fully covered ⇒ engine marks the feature `done` and archives it
  together with its own tasks. Nothing outside the shipment is touched.
* Non-member ⇒ the feature is left permanently `queued` with all children
  `done`, requiring a manual archive action after close. That is precisely the
  post-close repair the cycle-3 brief forbids.

The `done`/archive cascade that H10.4 feared cannot occur here, because the
cascade only destroys work that is *outside* the release scope — and under full
coverage there is no such work.

**Product grouping is preserved without lifecycle coupling.** `117-F` is
retained as a **childless** product umbrella. Grouping is expressed through
non-hierarchical `related_to` links (`117-F → 118-F`, `119-F`, `120-F`).
`featureScopeRoots` walks `parent_id` **only** and does not traverse
`item_links`, so these links carry documentation value with **zero** lifecycle
reachability. Because `117-F` is childless, `descendantItems(117-F)` is empty,
so `returnUnreleasedFeatureItems(117-F)` is a no-op even when it is in scope.

**Program closure is engine-native.** `117-F` is an explicit member of the final
shipment `129-S` only, listed **last** so that `120-F` (listed first) wins the
read-only `covering_feature` render projection. At `129-S` close the engine marks
`117-F` done and archives it. No operator action, no separate closing step.

**Deliberation-sweep check.** `collectArchiveCandidateIDs` also pulls
`linkedDeliberationIDs(feature)` for member features, matching
`\b(?:DL\d+|[0-9]+(?:\.[0-9]+)*-DL)\b` over `source_deliberation_id`,
`Description`, and `References`. All four features (`117-F`, `118-F`, `119-F`,
`120-F`) were checked and contain **no** `-DL` match, so no unrelated
deliberation is swept into the archive. (`004-SP` and the label `34D50F2D` do not
match the pattern.)

**Proof obligation discharged.** `docs/spikes/2026-08-09-plan1-shipment-topology-proof/sim-shipment-closure.ps1` runs both
arms against the real backlogit 1.8.0 engine on disposable fixtures: ARM A
(H10.4 control) orphans 14/14 downstream tasks; ARM B (H10.5 redesign) closes
all three shipments with `returned_ids: []` and a clean `doctor`. 63/63
assertions. `docs/spikes/2026-08-09-plan1-shipment-topology-proof/verify-plan1-shipment-topology.ps1` additionally replays the
*exact* live topology — including the real 27-edge dependency DAG — through real
`ShipShipment` calls: 196/196 assertions, `returned_ids: []` on every close.

## Hardening verdict

**HARDENED.** H1–H10 (including **H10.5**, added in the 2026-08-10 cycle-3
re-hardening pass and superseding H10.4) are bound into the plan's task
acceptance criteria, the shipment sequencing, and the non-goals. Proceed to
plan-review.

### Re-hardening pass — 2026-08-10 (PR #325 review-fix)

Triggered by PR #325 Copilot finding 1 (critical shipment safety). Scope of the
re-hardening was limited to the shipment-manifest safety contract; H1–H9 were
re-read and are unchanged and unaffected.

* **H10.4 added** — task-only manifests; covering feature is never a shipment
  member. Disarms the cascade-close hazard described above.
* **H10 verdict re-affirmed HARDENED.** The changed safety contract is
  fail-safe: the correction *removes* a destructive capability from the S1 close
  path rather than adding a new mechanism that must itself be trusted.

### Re-hardening pass — 2026-08-10 (cycle 3 of 3, F14 structural elimination)

Triggered by the rejection of F14's `adopt_item` mitigation on P-010
role-boundary and reliability-first grounds. Scope was again limited to the
shipment-safety contract; H1–H9 re-read, unchanged and unaffected.

* **H10.4 superseded by H10.5** — per-shipment ROOT covering features, fully
  covered, explicitly a manifest member; `117-F` demoted to a childless umbrella
  grouped by `related_to` links and closed by the final shipment.
* **F14 eliminated structurally, not mitigated.** No `adopt_item`, no post-close
  repair, no operator intervention, no feature reactivation, no forbidden status
  transition anywhere in the close path.
* **H10 verdict re-affirmed HARDENED.** H10.5 is fail-safe in a stronger sense
  than H10.4: it does not merely remove a destructive capability, it removes the
  *precondition* for the destructive code path. `returnUnreleasedFeatureItems`
  still runs on every close — it simply has nothing to act on, which is verified
  empirically (`returned_ids: []`) rather than argued.
* **Blast radius of the redesign itself:** backlog metadata only. No source,
  schema, template, or CLI file is touched by this pass.
* **One residual, explicitly carried** — the `parent_id`-clearing asymmetry
  (F14, P1), accepted with a required Ship-side re-adoption mitigation and an
  upstream report. It is a recoverable, non-destructive relationship change (no
  status change, no archival, no data loss), which is why it is P1 and not P0.
