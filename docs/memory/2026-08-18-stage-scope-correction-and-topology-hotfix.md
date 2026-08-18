# Stage session — operator scope correction (129-F/138-S cancellation) + topology-gate reliability hotfix

Date: 2026-08-18
Agent: Stage (route `claude-opus-5` / anthropic / high)
Mode: normal sequential (NOT P-017 dark mode)
Branch: `chore/stage-topology-hotfix-cancel-138` from `main` @ `747193fe`
Commits: `456844c0` (Objective A), `c0b3748c` (Objective B), plus this memory doc
Remote publication: **none** — not pushed, no PR. Ship owns the publication gate.

## Session gates

| Gate | Result |
|---|---|
| Tool availability (P-012) | `TOOL_OK: backlogit` (MCP). `DEGRADED_MODE: agent-engram, agent-intercom, graphtor-docs` — instruction packs installed but no MCP tools exposed this session; used documented file-based fallbacks (compound/doc grep) per each pack's degraded-mode rule, not ad-hoc substitution for an available tool |
| Index sync (start) | `INDEX_SYNC_OK` — 855 items |
| Checkpoint scan | **34 valid (32 `stage` + 2 `ship`), 0 anomalies, 0 quarantined, 0 active** → ZERO-CANDIDATE NORMAL STARTUP, no recovery needed |
| Working tree | `.backlogit/stash.jsonl` showed `M` from a stale stat; normalized blob `f02bdca7…` **identical** to HEAD → no real drift, proceeded |
| Worktrees | one (`D:/Source/GitHub/autoharness`); no spike/research worktree created (P-016 not invoked) |
| Role boundary | no source, test, or config file modified; no shipment claimed/abandoned/shipped; no PR opened; no build or test run |

## Objective A — operator-decision disposition

**Decision recorded:** `docs/decisions/2026-08-18-backlogit-legacy-root-support-operator-scope-correction.md`

`.backlogit` remains an acceptable, supported workspace directory permanently;
`.backlog` is the default for **new workspaces only**; existing workspaces
(including this repo) need **no** migration. The live self-migration is
therefore cancelled, not deferred.

The already-shipped product surface (`126-F` / `135-S`, PR #345, merge
`9851cc3`) is unaffected and remains correct. `.backlogit` exists, `.backlog`
does not — now the permanent correct steady state.

### Disposition applied

* `129-F` and `129.001-T` … `129.009-T` → **`rejected`** (all 10 verified via SQL).
* Supersession banners appended (**append-only**, nothing rewritten) to the
  plan, the H1–H16 hardening, the review, and the deliberation. Prior PASS
  verdicts stand as issued: this is a **scope withdrawal, not a quality
  failure**, and must not be recorded as a review failure in any metric.
* Hardening marked **DORMANT, not retired** — H16 and the G1–G6 containment
  proof stay reusable if a root migration is ever authorized later.

### Transition constraint discovered (reusable)

`queued → rejected` is **refused** by the `validate_status_transition`
pre-hook. Per `.backlogit/hooks.yaml` `lifecycle.transitions`:

```
queued: [active, blocked]        review: [done, accepted, rejected]
active: [done, blocked, review, shipped, abandoned]
blocked: [active]                done:   [archived]
```

`rejected` is reachable **only from `review`**. The supported cancellation
path for an item is therefore `queued → active → review → rejected`.
`done`/`archived` were rejected as options because they would falsely assert
completion of work never performed. Also discovered: a parent feature cannot
leave `queued` while it has non-terminal children (`blocking_children` error) —
children must be dispositioned first. Moves are slow (~2.5 min/task) because
the gate broker runs per move; budget ~25 min for a 9-task cancellation.

backlogit's routing then relocated the 10 records `queue/ → archive/`
automatically; git detected them as renames, so history is preserved.

## Objective B — topology-gate reliability hotfix

**New artifacts:** feature `131-F`, task `131.001-T` (`size: XS`,
`complexity: low`, `priority: high`), shipment `140-S`.

* Plan: `docs/plans/2026-08-18-topology-gate-forward-dependent-directional-predicate-plan.md`
* Hardening (P-006, H1–H9): `…-directional-predicate-hardening.md`
* Review: `docs/reviews/2026-08-18-…-directional-predicate-review.md` — **PASS, 0 unresolved P0 / 0 unresolved P1**

### The defect (confirmed read-only; source untouched)

`src/autoharness/gates/topology.py::_prior_shipment_id` line **1345** still
carries the direction-blind guard from PR #357 / `0568f044`. It suppresses the
implicit-predecessor fallback for *any* declaring shipment, so an ordinary
**forward** dependent (`113-S depends on 112-S`) disables the check for
`112-S` — silently permitting a claim that should return
`PREDECESSOR_NOT_SHIPPED`. A **silent fail-open in a safety gate**.

### Key analysis done at plan time

* **Regression compatibility proved, not assumed.** The existing
  `test_multi_hop_reverse_dependency_disables_fallback_entirely_not_just_the_violator`
  (target `139-S`, declarer `138-S`, `138 < 139`) still reaches the same
  `return None` branch under the directional predicate → passes unchanged.
  The two tests are separated exactly by declarer direction.
* **No chicken-and-egg hazard (H8).** `138-S` (lower) declaring `140-S`
  (higher) takes the lower-numbered-declarer branch under **both** old and new
  code → `140-S` stays claimable. Independently, `139-S` is already shipped.
  Two unrelated reasons.
* **Third correction to the same predicate** (skip-violator → any-direction →
  directional), which is why hardening was done despite a two-file diff.
* **Review-surface hazard (H6).** The v2 defect *was* caught by Copilot on PR
  #357 — twice, on the exact line — but only inside "Suppressed comments"
  blocks, never as `reviewThreads`. Thread-based review was followed
  faithfully and still missed it.

## Sequencing

`138-S` now has `blocks` edges on **both** `139-S` (shipped ✓) and `140-S`
(queued ✗). `140-S` has **no** blocking predecessors.

**Deterministic order: `140-S` → then `138-S` abandonment.** Rationale:
abandoning `138-S` requires `shipment claim`, which executes the `pre_claim`
topology gate — the very gate `140-S` fixes.

## Ship handoff — `138-S` abandonment (Stage did NOT claim; P-010)

backlogit exposes **no** `shipment abandon` command and **no** direct
`queued → abandoned` transition. Only supported route:

```powershell
backlogit shipment get 138-S            # confirm queued, 140-S shipped
backlogit shipment claim 138-S          # queued -> active (mechanical prerequisite)
backlogit move 138-S --status abandoned # active -> abandoned
backlogit shipment get 138-S            # verify
```

Ship must **not** create a branch for `138-S`, execute any `129.00x-T`, touch
any storage root, open a migration PR, or run `shipment ship 138-S`.

**If the move is refused:** do not force, do not hand-edit the markdown. Leave
it `active`, record the refusal, escalate. A `blocked` shipment status is a
**dead end** — not a defined `ShipmentStatus`, can never legally transition out.

## Open state for the next session

* `BED0DDED` — **ACTIVE, high**, final disposition appended (24881 chars, all
  prior evidence intact). Archive as consumed **only** when `138-S` is durably
  `abandoned`. Archiving now would destroy the sole tracker if abandonment is
  interrupted.
* Closure condition `topology-forward-dependent-suppression-fix` —
  **UNSATISFIED**, deliberately. Satisfied only when Ship merges the fix to
  `main` and the merge confirmation gate passes. `139-S` closure remains
  READY_WITH_CONDITIONS until then.
* Branch `chore/stage-topology-hotfix-cancel-138` is **local only**.
* Deferred follow-up (review F6, not stashed to avoid scope creep this
  session): the Copilot "Suppressed comments" blind spot is **repo-wide**; H6
  covers only this PR. A durable fix belongs in the review workflow
  instruction surface.

## Registry gap worth fixing

`.autoharness/backlog-registry.yaml` declares **no `features.sizing` flag**,
even though the installed backlogit MCP `update_task` accepts `size`,
`size_source`, `size_ruleset_version` and `complexity`. Per the
structured-emission capability gate that reads as degraded. Both paths were
used defensively: structured fields set via two separate mutually-exclusive
update calls **and** recorded as labelled prose in the task description.
The registry should gain `sizing: true` so the degradation is not spurious.
