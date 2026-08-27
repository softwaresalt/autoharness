---
title: Compacted memory — 109-F topology gate (114-S…116-S) + follow-on DAG-readiness/crash-resumption/self-repair (110-F/111-F/112-F, 117-S…119-S)
doc_type: memory
memory_class: compacted
created: 2026-08-04
scope: release-unit-saga
shipment: [114-S, 115-S, 116-S, 117-S, 118-S, 119-S]
feature: [109-F, 110-F, 111-F, 112-F]
pr: [296, 304]
consolidates:
  - docs/archive/memory/2026-08-04-stage-109F-topology-gate.md
  - docs/archive/memory/circuit-break-stage-pr296-review-fix.md            # from docs/memory/2026-08-05/
  - docs/archive/memory/stage-pr296-review-fix-noncascading-safeclose.md   # from docs/memory/2026-08-05/
  - docs/archive/memory/2026-08-05-stage-114s-closure-preactivation-fixes.md
  - docs/archive/memory/2026-08-05-stage-dark-factory-remaining-p017-scope.md
  - docs/archive/memory/2026-08-05-stage-publication-review-repair-p017.md
  - docs/archive/memory/2026-08-06-stage-copilot-pr304-five-finding-repair.md
  - docs/archive/memory/2026-08-06-stage-publication-review-p2-per-task-allowed-state.md
---

# Compacted: 109-F topology gate + follow-on DAG-readiness/crash-resumption/self-repair saga (2026-08-04 → 2026-08-06)

Two related but **distinct** release-unit branches ran back-to-back across these 8 files, each
heavily self-correcting via append-only addenda within the same source documents. This summary
records the **final authoritative state** of each branch plus the decisions, rejected
approaches, and root causes that produced it — intermediate "corrected again" passages are not
replayed verbatim.

* **Branch A — `109-F`**: the P-016 mechanical topology-gate feature itself (`gate
  pipeline-topology`). Shipments `114-S → 115-S → 116-S`. PR #296.
* **Branch B — `110-F`/`111-F`/`112-F`**: three follow-on features carved out of stashes that
  Branch A deliberately deferred (`33CC445C` DAG-readiness, `34D50F2D` crash-resumption
  candidate-d, `936C68F3` constrained self-repair). Shipments `117-S → 118-S → 119-S`. PR #304.
  These are **separate backlogit artifacts from Branch A's 114/115/116-S**, not a renumbering
  of them.

## Branch A — 109-F: P-016 topology-gate enforcement (`gate pipeline-topology`)

**Decision (012-DL)**: backlogit's `ClaimShipment` is **not** a CAS/lock/lease — it is an
unlocked read/check/write with per-shipment all-or-nothing persistence and no serialization at
any scope (same-checkout or cross-machine). The gate is therefore designed as a **fail-closed
external reader/validator**: detect-before (`SHIPMENT_STATE_INCONSISTENT`) + post-claim global
re-verify (`CLAIM_VERIFY_FAILED`) + pre-retry revalidation — detection and remediation, never
claimed atomic exclusion. It never mutates backlogit's own transition logic (external-guard
pattern; `C:/Source/GitHub/backlogit` is read-only evidence, never modified).

**Phase-aware invariant scope**: an explicit `--phase` flag distinguishes `pre_claim`
(zero-active required) / `post_claim`/`lifecycle` (exactly-one-active-and-target) / **`ambient`**
(at-most-one-active-and-target-when-present, non-blocking when zero — added specifically for
hook/CI paths that never claim anything themselves).

**Bypass model**: an operator `--force` is auditable because it runs through the gate and is
logged every time; a `git --no-verify` hook skip runs no gate code at all and is inherently
unobservable locally — so **required CI, not the local hook, is the actual non-bypassable
backstop**. DAG-style parallel/multi-worktree execution is a **permanent non-goal** under
P-001/P-016.

**Harvest / shipments**: feature `109-F`, 15 tasks initially (`109.001-T`…`109.015-T`), staged
serially as `114-S` (gate core, phase A) → `115-S` (hooks + install adapters, phase B) → `116-S`
(remote CI validation, phase C). The original plan tried to model `115-S`/`116-S` as
`blocked`-status shipments that would transition `blocked → queued` once their predecessor
shipped — **this transition does not exist in backlogit 1.8.0**; corrected during a P1 repair
cycle to keep successors `queued` from creation and enforce ordering purely through `blocks`
edges (later grew to 19 tasks across the three shipments after additional pre-activation
hardening below).

**PR #296 — 3 formal review-fix cycles + one operator-authorized extension** (circuit breaker
`circuit-break-stage-pr296-review-fix.md`): cycle 1 (`f82ead6`) fixed 9 planning-integrity
issues (archived-shipment provenance, unobservable `--no-verify` claims, shipment-log drift,
malformed checkpoints); cycle 2 (`71ff1b8`) fixed 4 claim/closure contract issues (pre-claim
active-shipment count, post-claim global re-verification, cross-machine lease overclaiming,
safe-close terminal provenance); cycle 3 (`d6ca4fb`) fixed 3 lifecycle issues (unlocked-claim
semantics, missing explicit phase input, impossible pre-archive provenance ordering); the
P-013.6 escalation route then fixed 3 residual P1 contradictions (`28e5c30`) but an independent
re-review still found **one more P1** (`109.010-T`/`109.005-T` assigned branch/worktree
handling to `post_claim/lifecycle` instead of the required `pre_claim`). **The operator
explicitly removed the 3-cycle limit for this session** and authorized continued repair rather
than halting — recorded as historical circuit-breaker evidence, not a silent bypass.

**Non-cascading safe-close (the follow-up session that used the extension)** — root-caused by
**reading backlogit's actual Go source**, not docs: `internal/core/shipment_lifecycle.go`'s
`ShipShipment` (`backlogit shipment ship`) performs `completeReleaseScope` +
`returnUnreleasedFeatureItems` (every unshipped non-release descendant is **requeued and
detached** — `parent_id` cleared, not archived) + `archiveItems`. For a partial-feature
shipment like `114-S` this would not archive `109-F` itself, but it **would** requeue/detach
`115-S`/`116-S`'s descendant tasks, orphaning them. `MoveShipmentStatus` (the safe, non-cascading
transition) exists in the Go source but is **not exposed by any CLI/MCP surface**. **Supported
non-cascading close pattern** (documented as canonical going forward): (1) `backlogit move
<shipment_id> --status shipped` (shipment record only, no cascade) → (2) verify `status:
shipped` → (3) `backlogit archive <shipment_id>` (single-item archive, no cascade, stamps
`archived_status: shipped`) → (4) verify. **Never invoke `shipment ship` for a partial-feature
manifest.** This generalizes the same forbidden-cascade lesson from `093-S` (Group 1) — it is a
structural property of the command, not incidental bad luck.

**114-S closure pre-activation fixes** (2026-08-05, ahead of `115-S` activation): staged 3
mandatory defects into `115-S` before its topology-gate activation tasks could run —
`109.021-T` (gate's post-claim retry becomes a read-only `CLAIM_NOT_OBSERVED` contract; the gate
never claims, per P-001/P-016; Ship's external claim-retry loop drives convergence),
`109.022-T` (CLI telemetry outcome mapping treats any non-zero/non-blocked/non-forced result,
including the new retry-required token, as `failed` not `success`), `109.023-T`
(`closure_complete()` requires `READY`, or `READY_WITH_CONDITIONS` only with machine-readable
per-condition `satisfied:true`+`evidence`, else fails closed). A 4th defect — an audit-log
discrepancy — was dispositioned as **external/backlogit-owned**, not an autoharness defect, and
recorded as a deferred low-priority stash (`84D8E6AB`) rather than fabricating an autoharness-
side fix or mutating the external `backlogit` repo.

## Branch B — 110-F/111-F/112-F: DAG-readiness, crash-resumption, constrained self-repair

Staged from three previously-deferred stashes: `33CC445C` (Phase 1 DAG-readiness reporting →
`110-F`/`117-S`), `34D50F2D` (candidate (d), orchestrator crash-resumption protocol →
`111-F`/`119-S`), `936C68F3` (part 2, constrained self-repair → `112-F`/`118-S`).

**Decision (013-DL — self-repair lift)**: chose **Option C, a constrained lift** — operator-
invoked, topology-gated, forward-only `queued → active` via the existing `ClaimShipment` (never
a new lock/CAS), single-shot, audited. Full/silent/backward auto-repair was **permanently
rejected**.

**Decision (002-SP — crash-resumption boundary spike)**: **PROCEED** via orchestration prose
layered over the existing checkpoint/engram substrate; no external binary change.

**Owner-exclusive recovery routing** (111-F): zero active recovery candidates at session start
is **normal startup**, not a failure — the Orchestrator simply continues normal orchestration.
When one or more valid candidates exist, and the operator makes an explicit, unique checkpoint
selection with valid `CheckpointV1` agent-ownership (`stage`/`ship`), the Orchestrator **routes
restore/resume/prune exclusively to the owning agent** and never performs any of the three
directly itself — failing closed on missing/invalid/ambiguous ownership or a non-unique
selection (among existing candidates only; zero candidates never fails closed).

**DAG ready-set predecessor-finished predicate** (repeatedly corrected across these files
before landing): a `queued` **or** `active` predecessor is **unfinished and blocking** — only a
`shipped`/`done` closure makes a dependent eligible; `abandoned`/malformed/unknown fails closed.
An earlier draft mislabeled `active` as terminal/non-blocking, which was wrong and corrected.

**112-F repair-record-status mode — unreachable-precondition defect and fix** (publication-
review P2-3): the original precondition required every manifest task to classify as `matched`
against a **single** `expected_status` parameter — but a genuine "queued-with-active-work"
repair target has **mixed** task statuses by definition, so the all-`matched` gate could never
actually fire; it always refused the exact state the repair mode exists to repair. **Fixed**
with a **per-task allowed-state predicate**: each task must be present in the location expected
for its own status (queue for `queued`/`active`; queue-or-archive for `done`), status confined
to `{queued, active, done}`, no orphan/malformed/torn anomaly — proceed only if every task
passes, refuse on any single anomaly. Ambiguity refusal stays unweakened; mixedness itself is
not the anomaly signal, a per-item defect is.

**Copilot PR #304 — five findings, one review-fix cycle** (`2026-08-06-stage-copilot-pr304-
five-finding-repair.md`):
1. **112-F's repair premise itself was invalid** — read-only inspection of backlogit's Go
   source (`ClaimShipment`/`NormalizeShipmentItems`/`rollbackShipmentClaim`,
   `isValidShipmentTransition`) proved a shipment-record-only forward re-claim is
   **unreachable**: `ClaimShipment` is single-shot all-or-nothing (`active→active` errors),
   there is no `active→queued` edge and no `blocked` shipment status. Re-scoped `112-F` and its
   4 tasks to **read-only detection + report-only diagnostic + operator-remediation guidance**
   — no mutation, no `ClaimShipment` call. True auto-repair deferred as unsupported; `936C68F3`
   **reactivated** as a living tracker (partial, report-only-slice consumption).
2. **Engram-unavailable contradiction** (crash-resumption prune-on-restore) — resolved to a
   single behavior: **fail-closed operator handoff** when the prune substrate (engram) is
   unavailable; eliminated an earlier alternate "bounded file-based prune degradation" path
   that had never been proven safe.
3. **Provenance/consumption contract on `112-F`** — added `custom_fields` documenting partial,
   report-only-slice consumption of `936C68F3` (later itself corrected — see below).
4. **Installed dogfood mirrors omitted** — added task `111.007-T` to refresh installed agent
   mirrors (`.github/agents/_orchestrator.agent.md`, `_stage.agent.md`, `_ship.agent.md`) and
   `.autoharness/harness-manifest.yaml` per-artifact checksums.
5. (Same repair pass) Mirror cross-references added to `111.001-T`/`111.006-T` implementation
   notes; `111-F` updated to reflect the resulting seven-task shape.

**PR #304 follow-up — `source_stash_id` vs `source_stash_tracker_id` (highest-value fix)**:
finding 3's `custom_fields.source_stash_id: 936C68F3` on `112-F` was itself a defect — Ship's
close contract **unconditionally retires** whatever stash a `source_stash_id` references,
which would have archived `936C68F3` and contradicted its intended living-tracker/partial-
consumption disposition. **Fixed** by removing `source_stash_id` and using the **separate,
non-cleanup-triggering** field `custom_fields.source_stash_tracker_id: 936C68F3` instead,
alongside explicit `source_stash_consumption`/`source_stash_disposition`/`provenance_note`
fields. `source_deliberation_id: 013-DL` was safely retained (already archived, so cleanup is
an idempotent no-op).

**Checkpoint hygiene root cause**: mid-saga, a checkpoint (`checkpoint-20260805-053524.json`)
was **improperly hand-amended in place** after creation instead of being replaced through the
supported create-new + resolve-old lifecycle. This was caught, and the checkpoint was
retroactively resolved and superseded by a freshly created one carrying the corrected state.
**Rule established here and enforced for the rest of the saga: never hand-edit a checkpoint's
`state_dump`; always `backlogit checkpoint create` the corrected state and `resolve` the
superseded one.** Checkpoint chain across Branch B's finalization:
`023057→034020→053524(improper amendment, corrected)→062506→072043→083118→150505` (final; each
predecessor formally resolved).

## Final authoritative state (Branch B, saga end)

* **14 tasks**: `110.001-T`–`110.003-T` (3, DAG-readiness reader + CLI `gate dag-readiness` +
  docs), `111.001-T`–`111.007-T` (7, crash-resumption protocol + prune-on-restore + degraded
  fallback + verify/docs + owner-exclusive-routing hardening + installed-mirror refresh),
  `112.001-T`–`112.004-T` (4, report-only repair-detection mode + regression guard + docs +
  audit/telemetry).
* **19 `blocks` edges**, acyclic (110: 2, 111: 13, 112: 4).
* **Shipments (task-only manifests), serial chain**: `117-S = {110.001-T, 110.003-T,
  110.002-T}` — **only eligible shipment**, the handoff token to Ship; `118-S = {112.001-T,
  112.004-T, 112.002-T, 112.003-T}` depends on `117-S`; `119-S = {111.001-T, 111.004-T,
  111.005-T, 111.006-T, 111.007-T, 111.002-T, 111.003-T}` depends on `118-S`.
* Sole active valid Stage checkpoint: `checkpoint-20260806-150505.json`.

## Cross-cutting learnings (this saga — high value, must not be dropped)

1. **P-015 cascade-safety is a structural property of `backlogit shipment ship`, confirmed by
   reading the Go source** — it requeues/detaches unshipped descendants for any partial-feature
   manifest. The only safe pattern is the generic per-item `move --status shipped` + `archive`,
   never the cascade command. Generalizes the `093-S` lesson (Group 1) from an observed incident
   to a proven structural defect.
2. **Checkpoints are append-only lifecycle objects** — never hand-amend a `state_dump` in
   place; always `create` new + `resolve` old. This saga is the origin of that explicit rule,
   root-caused after an in-place amendment was caught and repaired.
3. **`source_stash_id` (cleanup-triggering) vs `source_stash_tracker_id` (not) is a critical,
   easy-to-conflate distinction** — required whenever a stash entry (e.g. a living tracker like
   `936C68F3`) must outlive a single Ship close.
4. **A precondition that requires uniform state across a target whose entire purpose is
   handling non-uniform state is a load-bearing design defect, not an edge case** — 112-F's
   original all-`matched`-on-one-`expected_status` gate could never fire for the exact
   "mixed-status repair target" it was built for. Per-item predicates over per-run scalar
   predicates fix this class of defect.
5. **Operator-authorized circuit-breaker extensions are historically preserved, not silently
   discarded** — PR #296's 3-cycle trip plus operator override is recorded as-is; the extension
   itself did not guarantee convergence on the first additional attempt.
6. **A single-behavior fail-closed choice beats maintaining two divergent degraded-mode paths**
   — the crash-resumption engram-unavailable contradiction was resolved by deleting the unproven
   "bounded file-based degradation" alternative outright rather than trying to reconcile it with
   fail-closed-operator-handoff.
7. **Read the actual dependency's source before designing around its behavior** — both the
   cascade-safety root cause (Branch A) and the unreachable `ClaimShipment` re-scope
   (Branch B, PR #304 finding 1) were discovered by reading `backlogit`'s Go implementation
   directly, not by trusting docs or prior assumptions.

## Operator-only decisions remaining (carried forward — still open)

Preserved from the source checkpoint `docs/archive/memory/2026-08-04-stage-109F-topology-gate.md`.
These are operator-only calls that were never resolved inside this saga and therefore survive
compaction:

1. Whether to git-commit the `.backlogit` planning artifacts (Stage left the worktree
   unchanged beyond backlogit's own writes; untracked graphql files untouched).
2. **CI hard-fail vs warn in required mode** (default advisory-first; flip after bake-in) —
   still a live product question for the topology gate rollout.
3. Optional backlogit-recorded worktree-owner token for cross-machine worktree observability
   (deferred; out of the then-current bounded scope).
4. Prioritize the deferred DAG-visibility follow-up (`33CC445C`) in a future turn.

## Outcome

Branch A (`109-F`, PR #296) and Branch B (`110-F`/`111-F`/`112-F`, PR #304) both merged.
Branch A's shipment chain `114-S→115-S→116-S` and Branch B's `117-S→118-S→119-S` are
independent, both handoff tokens to Ship in their respective final states — only `117-S` is
eligible at Branch B's saga end (its Branch A analog, `114-S`, was the eligible cursor at
Branch A's saga end). Cross-referenced downstream Ship-side execution notes (outside this
input set) at `docs/archive/memory/2026-08-05-ship-114-S-109-F-session.md` and
`docs/archive/memory/2026-08-06-ship-117-S-110-F-session.md` confirm these shipment/feature IDs
match what actually executed.
