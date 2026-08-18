# Operator Decision — Legacy `.backlogit` remains supported; `.backlog` default applies to NEW workspaces only

Date: 2026-08-18
Agent: Stage (recording an authoritative operator decision — Stage did not originate it)
Decision type: scope correction / supersession
Status: **ACCEPTED — binding**
Stash lineage: `BED0DDED` (high, feature) → deliberation `018-DL`
Supersedes the residual scope of: `129-F`, `129.001-T` … `129.009-T`, shipment `138-S`

---

## 1. The decision

The operator has issued an authoritative scope correction governing the
`.backlogit` → `.backlog` workspace-directory work:

1. **`.backlogit` remains an acceptable, supported Backlogit workspace
   directory.** It is *not* deprecated, *not* legacy-in-the-pejorative-sense,
   and *not* scheduled for removal. Tooling, resolvers, agents and
   documentation MUST continue to discover and operate on a `.backlogit`
   root indefinitely.
2. **`.backlogit` is merely no longer the DEFAULT for NEW workspaces.** When
   Backlogit is installed into a workspace that does not already have a
   storage root, the newly created root defaults to `.backlog`.
3. **Existing workspaces do NOT need migration.** There is no migration
   obligation, no deadline, and no "eventual consistency" requirement for
   any workspace that already stores state under `.backlogit` — including
   *this* repository.

### Direct consequence

The live, in-place `.backlogit → .backlog` self-migration of this repository —
staged as feature `129-F`, tasks `129.001-T` … `129.009-T`, and shipment
`138-S` — is **unnecessary and MUST NOT execute**. It is cancelled, not
deferred.

## 2. What was already delivered, and remains correct

The *product* surface of `BED0DDED` — the new-workspace default and the
follower/resolver behaviour — **already shipped** as feature `126-F` /
shipment `135-S` (PR #345, merge `9851cc3`). That work is correct,
unaffected by this decision, and MUST NOT be re-opened or re-touched.

Specifically, the shipped behaviour that this decision confirms as final:

| Surface | Shipped behaviour | Status under this decision |
|---|---|---|
| New-workspace root creation | defaults to `.backlog` | **correct — keep** |
| Existing `.backlogit` root discovery | still resolved and supported | **correct — keep, permanently** |
| Dual-root detection (`.backlog` + `.backlogit` both present) | fail closed | **correct — keep** |
| Docs/templates/schemas/installer/tuner follower references | already updated | **correct — keep** |

The only item the prior staging cycle believed to be outstanding was the
self-migration of this repository's own live root. That belief is what this
decision retires.

## 3. Rationale (as stated by the operator)

* Supporting `.backlogit` indefinitely is *cheaper and safer* than migrating
  live workspaces. The resolver already handles both roots; keeping both
  supported costs nothing at runtime.
* A live storage-root rename of an actively used backlog is an inherently
  destructive, hard-to-reverse operation whose blast radius (1613 git-tracked
  files, agent instruction surfaces, hooks, CI paths, index rebuild) is wildly
  disproportionate to its benefit — which is purely cosmetic consistency.
* The prior plan's own hardening record is the strongest evidence for this
  conclusion: it required **sixteen** hardening controls (H1–H16), a
  six-gate containment proof for a pre-migration backup, and a fail-closed
  HALT-for-operator rollback, in order to make a *cosmetic rename* safe. A
  change that needs that much machinery to be survivable is a change that
  should not be made.
* "Default for new" and "mandatory for existing" are separable policies. The
  original stash text conflated them; this decision separates them
  permanently.

## 4. Disposition applied by Stage under this decision

Recorded here so the disposition is auditable from a single artifact.

| Artifact | Prior state | New state | Mechanism |
|---|---|---|---|
| `129-F` (feature) | `queued` | **`rejected`** | `backlogit move` — supported terminal status for feature type |
| `129.001-T` … `129.009-T` (9 tasks) | `queued` | **`rejected`** | `backlogit move` — supported terminal status for task type |
| `138-S` (shipment) | `queued` | **`abandoned`** — *pending, Ship-owned* | `claim` → `move --status abandoned` (see §5) |
| `BED0DDED` (stash) | `active`, high | **remains active** until `138-S` is durably `abandoned` | append-only disposition note |
| Plan / hardening / review / deliberation docs | PASS verdicts | **SUPERSEDED — CANCELLED** banners appended | append-only; no history rewritten |

### Evidence-preservation rule applied

Every correction is **append-only**. No prior rationale, verdict, finding,
hardening control, or containment proof was deleted, edited, or
back-dated. The prior PASS verdicts remain literally true statements about
a plan that was correct-as-designed but is no longer *wanted*. Cancellation
here is a **scope decision, not a quality judgement** — the plan did not
fail review; its premise was withdrawn.

## 5. Shipment `138-S` — Ship-owned abandonment (Stage MUST NOT execute)

Stage's role boundary forbids claiming, abandoning, or shipping any
shipment (P-010). `138-S` is therefore left `queued` with this decision
recorded against it, and handed to Ship.

**Tool limitation, stated explicitly:** backlogit exposes **no**
`shipment abandon` command and **no** `abandon` MCP operation. `backlogit
shipment --help` offers only `add | claim | create | get | list |
return-blocked | ship`. The only supported route to the `abandoned`
terminal state is the *generic* `backlogit move`.

**Transition constraint:** the only valid shipment transitions are
`queued → active`, `active → shipped`, and `active → abandoned` (verified
against `internal/core/shipment.go::isValidShipmentTransition`, recorded in
`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`).
There is **no** direct `queued → abandoned` transition. A shipment must
therefore be *claimed* before it can be abandoned — the claim is a
mechanical prerequisite of cancellation, not an intent to execute the
shipment's contents.

**Exact sequence Ship must use:**

```powershell
# 0. PREREQUISITE — the topology hotfix (140-S) must be shipped first;
#    138-S carries an explicit `blocks` edge on it. Do not force past this.
backlogit shipment get 138-S          # confirm status: queued, deps satisfied

# 1. queued -> active  (mechanical prerequisite; NOT an execution intent)
backlogit shipment claim 138-S

# 2. active -> abandoned  (generic move; no dedicated abandon command exists)
backlogit move 138-S --status abandoned

# 3. verify the terminal state landed
backlogit shipment get 138-S          # expect status: abandoned
```

**Ship MUST NOT**, at any point in this sequence: create a branch for
`138-S`, execute any of `129.001-T` … `129.009-T`, rename/create/delete any
storage root, open a PR for the migration, or call `backlogit shipment ship
138-S`. The claim in step 1 exists solely to satisfy the state machine.

**Safest traceable alternative, if step 2 is refused** (e.g. a gate broker
rejects the generic move on a shipment artifact): do **not** force it and do
**not** hand-edit the shipment markdown. Instead leave `138-S` `active`,
record the refusal verbatim, and escalate to the operator. An `active`
shipment with a recorded cancellation decision is recoverable; a
hand-mutated or `blocked`-status shipment record is a **dead end** — `blocked`
is not a defined `ShipmentStatus` constant and can never legally transition
out (same compound doc, correction of 2026-08-04).

## 6. Closure conditions

`BED0DDED` may be archived as consumed **only** when both hold:

1. this decision artifact is committed (satisfied on commit of this file), **and**
2. `138-S` is durably `abandoned` by Ship.

Until (2) holds, `BED0DDED` remains **active at high priority** with the
final disposition appended, so the tracker survives if abandonment is
interrupted.

## 7. Cross-references

* Stash: `BED0DDED` — deliberation `018-DL`
* Cancelled plan: `docs/plans/2026-08-17-backlogit-self-migration-plan.md`
* Cancelled hardening: `docs/plans/2026-08-17-backlogit-self-migration-hardening.md`
* Cancelled review: `docs/reviews/2026-08-17-backlogit-self-migration-review.md`
* Cancelled deliberation: `docs/decisions/2026-08-17-backlogit-self-migration-choreography-deliberation.md`
* Shipped and retained product surface: `126-F` / `135-S` / PR #345 / merge `9851cc3`
* Shipment status constraints: `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`

## 8. Ship-confirmed durable abandonment (append, 2026-08-18)

Ship executed the §5 backlogit-state-machine sequence (claim then move)
exactly as specified. **Deviation disclosure, not silently glossed over:**
§5 above also directs "Ship MUST NOT ... create a branch for `138-S`". A
later, session-specific operator instruction explicitly superseded that
clause for this cancellation: the operator directed Ship to "create a
dedicated cancellation branch based on current main" for traceability of
the closure commit, and explicitly authorized the literal name
`chore/abandon-138-s`. Ship therefore did create a branch — not to execute
or prepare `138-S`'s contents (no file under `129.001-T`…`129.009-T`'s
scope was touched, no storage root was touched), but solely as a commit
target for the cancellation-closure evidence itself, per that later
operator authorization. This is recorded here as an explicit, cited
supersession of §5's no-branch clause, not an unacknowledged deviation.
The branch was created from `main`
(`99b8ead601a72642ed9791cb99258ac4f2e1bd8e`), with all pre-existing
operator-staged worktree changes (`.gitmodules`, `references/skillopt`,
`references/waza`, `references/witr`) verified byte-for-byte preserved
across the branch operation:

1. `backlogit shipment get 138-S` — confirmed `queued`, dependencies
   `139-S`/`140-S` both `archived_status: shipped`.
2. `backlogit shipment claim 138-S` — `queued -> active`
   (`updated_at: 2026-08-18T18:10:04.0668911Z`).
3. `backlogit move 138-S --status abandoned` — `active -> abandoned`
   (`updated_at: 2026-08-18T18:10:56.0929182Z`).
4. `backlogit get 138-S --format json` — verified `"status": "abandoned"`.

**Closure condition (2) from §6 above is now satisfied.** `138-S` is
durably `abandoned`. Combined with condition (1) (this decision artifact,
already committed at `456844c0`), both §6 closure conditions hold as of
this append. `BED0DDED` archival remains **Stage-owned** per the bounded
stop in Ship's cancellation lifecycle instructions — Ship does not archive
the stash in this closure; that is left for Stage to perform in a
subsequent session now that both conditions are met.

Full evidence trail (pre-flight P-001/P-016/dependency verification, gate
output, index-preservation proof, and full state-transition timestamps) is
recorded in `docs/closure/138-S-129-F-cancellation-closure.md`.
