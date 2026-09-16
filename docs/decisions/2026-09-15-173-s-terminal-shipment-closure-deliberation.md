---
title: "Terminal-shipment closure: resolving the coupled 173-S safe-close deadlock (FBD2F6BE + 2B42392E)"
description: "One coupled decision for two stash findings that jointly block 173-S closure: the safe-close protected-set baseline gate halting on pre-existing descoped archived siblings, and backlogit 1.10.1 refusing every non-cascading transition to shipped."
topic: "Shipment closure contract gap for fully-terminal shipment scope"
depth: "deep"
decision_status: "superseded"
superseded_by: "docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md"
superseded_on: "2026-09-15"
promoted_to: "queue"
linked_artifacts:
  - "docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md"
  - "docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md"
stash_entries:
  - "FBD2F6BE"
  - "2B42392E"
related_entries:
  - "3CA122AC"
tags:
  - "shipment-closure"
  - "safe-close"
  - "protected-set"
  - "p-015"
  - "p-021"
  - "backlogit-tooling"
---

---

> ## ⛔ SUPERSEDED — 2026-09-15
>
> **This decision's core premise has been superseded by an operator
> architectural correction.** It is retained **unmodified below this banner**
> for historical traceability. Do **NOT** implement from it.
>
> **Superseded by:**
> `docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md`
>
> **What was superseded and why:**
>
> * The operator ruled that tying a shipment to a covering feature *and all
>   descendants* is **defective**. A shipment manifest is a **flat manifest of
>   exactly what is delivered** and carries **no implicit hierarchical closure
>   semantics**.
> * **`TERMINAL_CLOSE` (E1) is WITHDRAWN.** Its precondition 2 ("every
>   descendant … is likewise already archived and terminal") is hierarchical
>   closure restated, and its precondition 3 ("the only live artifact is the
>   shipment record") makes multi-shipment feature delivery unreachable.
> * **The terminal-descope exemption (E2) is WITHDRAWN.** It substitutes a
>   disposition-note gate for an ancestry gate over artifacts that must not gate
>   closure at all.
> * The replacement is an **engine-inertness containment** model: closure scope
>   is exactly `manifest ∪ {shipment record}`, and the descendant walk survives
>   only as a blast-radius constraint on the backlogit cascade instrument.
>
> **What remains valid from this document:** the verified live state of the
> blocking artifacts, the archive-shape survey (1029 records), the class-scope
> finding (`3CA122AC` / `168-S`), and the observation that
> `move --status shipped` is refused by backlogit 1.10.1.
>
> **Superseded handoff conditions.** The five `174-S` claimability conditions
> stated at the end of this document are superseded by the successor decision;
> only the operator-owned **P-001 overlap authority** remains outstanding.

---

## Problem Frame

Shipment `173-S` (covering feature `165-F`, "DAG-authoritative predecessor
derivation for the pipeline-topology pre_claim gate") is functionally complete:
PR #450 merged (merge commit `9cc98c41`), the post-merge closure PR #451 merged
(merge commit `358b63b4`, current `main` HEAD), all 11 manifest members are
terminal, and P-020 closure compaction is done. Only the **shipment record's own
close** remains, and it cannot be performed. Ship halted and handed off.

Two deferred-scope-expansion entries describe the blockage. They are deliberated
**together** because they block the same single operation and, as established
below, share one root cause.

* **FBD2F6BE** — `shipment-reconcile` safe-close Step 2 enumerates every sibling
  sharing the covering feature's hierarchy prefix (scanning `queue/` **and**
  `archive/`) into the *protected set*; Step 3 then requires every protected-set
  member to be present in `.backlogit/queue/`. Tasks `165.007-T` and `165.010-T`
  are permanently descoped, already archived, and still carry `parent_id: 165-F`,
  so Step 3 halts with `HALT — cascade detected, revert required`.
* **2B42392E** — safe-close Step 8 mandates
  `backlogit move <shipment_id> --status shipped`, which backlogit 1.10.1 refuses
  ("shipment must be shipped via ShipShipment, not a direct status update",
  exit 9), while the P-015 classifier returns `SAFE_CLOSE` for this manifest,
  which forbids the cascade `ShipShipment` op.

**Explicit constraints carried into this deliberation** (operator-stated and
policy-derived): do not simply clear `parent_id`; do not weaken the baseline
gate; do not authorize an unsafe or destructive workaround. The cited compound
learning is emphatic that an agent must not unilaterally narrow this
NON-NEGOTIABLE halt gate by ad hoc in-session judgment "even when the underlying
archived-sibling state is verified benign."

**Out of scope**: implementation, source/template/schema mutation, shipment
claim/close, PR creation, and triage of unrelated stash entries.

## Research Findings

### Verified state of the blocking artifacts

| Artifact | Location | `status` | `archived_status` | `parent_id` |
|---|---|---|---|---|
| `165.007-T` | `archive/` | `archived` | `blocked` | `165-F` |
| `165.010-T` | `archive/` | `archived` | `blocked` | `165-F` |
| 11 manifest members | `archive/` | `done` | *(absent)* | `165-F` |
| `173-S` | `queue/` | `active` | — | — |

Both siblings carry explicit, permanent dispositions: `165.007-T` was DESCOPED
(Stage review-fix cycle 1, decision D4; work deferred to stash `FD0CCB42`), and
`165.010-T` was MERGED into `165.008-T` (review-fix cycle 2, finding 8) and is
marked "DO NOT EXECUTE, DO NOT REOPEN". Both were archived in commits
`2744359a` / `730c3fc5`, which **predate** Ship's claim of 173-S. Their archived
state is therefore provably not a cascade caused by this closure run.

### Why the existing exemptions do not apply

Step 2's only existing escape hatch is the **sequence-aware exclusion**, which
requires the sibling's predecessor shipment to carry verified provenance
`archived_status: shipped` (or legacy `done`). Both siblings are
`archived_status: blocked`, so they stay protected fail-closed — correctly, per
the contract as written. Step 3's `pre-archived` exemption is explicitly scoped
to **manifest items only** and never to the protected set (P-015 restates this).

### The classifier forces SAFE_CLOSE

`classify_shipment_close_path` (`src/autoharness/gates/shipment_closure.py`)
walks the **full** `parent_id` descendant graph across `queue/` + `archive/`.
`165-F`'s descendants include `165.007-T` and `165.010-T`, which are **not**
manifest members, so `165-F` is not "fully covered" and the whole manifest falls
back to `SAFE_CLOSE`. The cascade path is therefore forbidden — exactly as
2B42392E reports.

### Spike evidence (isolated throwaway workspace, backlogit 1.10.1)

A time-boxed Stage spike reproduced the closure in a disposable workspace under
`%TEMP%` (no git branch, no worktree, repository untouched; workspace destroyed
afterwards). Results:

| Probe | Result |
|---|---|
| `backlogit move <S> --status shipped` | **Refused**, exit 9 (ShipShipment guard) |
| `backlogit update <S> --status shipped` | **Refused**, exit 9 (same guard) |
| `backlogit archive <S>` while `active` | Succeeds but stamps `archived_status: active` → fails Step 8's provenance gate (`RECONCILE_FAIL_SHIPMENT_RECORD_PROVENANCE`) |
| `backlogit shipment ship <S>` on a 173-S-shaped, fully-terminal manifest | Succeeds; yields exactly `status: archived` + `archived_status: shipped` + commit traceability |

**There is no non-cascading path to `shipped` in backlogit 1.10.1.**
`ShipShipment` is the *only* mechanism that produces the terminal provenance
Step 8 itself demands.

The cascade's blast radius was then measured directly on a mirror of the 173-S
shape (manifest members already archived; one out-of-manifest descoped sibling
archived with `archived_status: blocked`):

* the descoped out-of-manifest sibling was **byte-identical** afterwards
  (hash unchanged, `archived_status: blocked` preserved, `updated_at` unchanged);
* the already-archived manifest task was untouched;
* the qualifying feature retained `archived_status: done` and gained only
  `commit:` traceability;
* `archived_ids` was `[feature, shipment]`, matching P-015 item 7's superseded-
  claim correction exactly.

**Interpretation.** P-015 exists to prevent the cascade from archiving a *live*
covering feature and *live* unshipped siblings. When every artifact in the
closure scope is already terminal, there is nothing live for the cascade to
destroy — the feared failure mode is not merely unlikely, it is unreachable.
This is evidence about the *shape*, not a licence to bypass the gate ad hoc.

### Additional finding: archived-without-provenance is the workspace norm

The 11 manifest members sit in `archive/` declaring `status: done` with **no**
`archived_status`. A survey of all 1029 archived records shows this is not fresh
corruption but a widespread historical shape:

| Shape | Count |
|---|---|
| `archived` + provenance | 462 |
| `archived`, no provenance | 168 |
| `done`, no provenance | 366 |
| `shipped` / `rejected`, no provenance | 33 |

**Design consequence:** any terminality precondition must accept
`status ∈ {done, archived, shipped}` inside `archive/`, and must **not** be
written as "declares `status: archived`" — that stricter phrasing would fail to
fire on 173-S and on roughly a third of this workspace's archived history.

### Class scope, not a 173-S incident

Stash `3CA122AC` records the identical failure for `168-S` / `160-F` /
`160.019-T`, and the compound learning
`docs/compound/2026-09-03-copilot-review-surfaces-latent-parent-id-closure-blocker.md`
explicitly predicted this class rather than resolving it. P-015 additionally
forbids narrowing or special-casing its exception "to any particular feature ID,
shipment ID, or manifest shape". Any remedy must therefore be general and
machine-checkable.

## Options Evaluated

### Option A: Clear `parent_id` on the two descoped siblings

Retire the `parent_id` field so the siblings stop being enumerated.

* **Pros**: trivial; unblocks Step 3 immediately.
* **Cons**: operator-excluded. Destroys ancestry and the audit trail of *why*
  those tasks existed. Critically, it also **silently flips the classifier**:
  with no out-of-manifest descendants, `165-F` becomes a fully-covered root and
  the path changes from `SAFE_CLOSE` to `CASCADE` — mutating historical records
  to change a safety classifier's verdict is precisely the unsafe workaround the
  operator prohibited. Leaves two parentless orphans.
* **Effort**: low. **Fit**: rejected.

### Option B: Protected-set terminal-descope exemption only

Generalize the existing sequence-aware exclusion: drop a sibling from the
protected set when it is verifiably terminal, already archived before the run,
and carries a P-021 C1 descope disposition.

* **Pros**: principled and narrowly targeted; resolves FBD2F6BE and 3CA122AC;
  preserves the gate fully for live siblings.
* **Cons**: **insufficient alone** — 173-S still dies at Step 8 on 2B42392E.
* **Effort**: low-medium. **Fit**: necessary but not sufficient.

### Option C: Backlogit CLI change request for a non-cascading `shipped`

Ask upstream for `shipment ship --no-cascade`, or relax the guard.

* **Pros**: cleanest long-term contract; removes the root tooling gap.
* **Cons**: external dependency on a separate Go project; cannot unblock 173-S
  now; unbounded timeline.
* **Effort**: high / not self-owned. **Fit**: valid follow-up, not the path.

### Option D: Re-include the two tasks in the 173-S manifest

* **Pros**: makes the feature fully covered.
* **Cons**: falsifies the release record by claiming work shipped that was
  deliberately descoped; contradicts decisions D4 and finding 8; `165.007-T`'s
  work is explicitly deferred to `FD0CCB42` and has not shipped.
* **Effort**: low. **Fit**: rejected.

### Option E (RECOMMENDED): `TERMINAL_CLOSE` — a third classified close path, plus Option B

Add an explicit, machine-checkable third classification alongside `SAFE_CLOSE`
and `CASCADE`, for shipments whose entire closure scope is already terminal, and
adopt Option B's exemption for the live-sibling case.

* **Pros**: resolves both findings with one coherent contract change; general and
  shape-based (P-015-compliant); fail-closed by construction; grounded in
  measured engine behaviour rather than prose judgment; also unblocks 168-S.
* **Cons**: touches policy + skill + classifier (elevated blast radius); requires
  plan hardening and review before implementation.
* **Effort**: medium. **Fit**: best.

## Trade-off Comparison

| Criterion | A (clear parent_id) | B (exemption only) | C (CLI change) | D (re-manifest) | E (TERMINAL_CLOSE + B) |
|---|---|---|---|---|---|
| Resolves FBD2F6BE | Yes (unsafely) | Yes | No | Yes | Yes |
| Resolves 2B42392E | Only via silent cascade flip | No | Yes | Only via cascade flip | Yes |
| Preserves audit trail | No | Yes | Yes | No | Yes |
| Weakens a safety gate | Yes | No | No | Yes | No |
| Honors operator constraints | No | Yes | Yes | No | Yes |
| Generalizes to 168-S / the class | No | Yes | Yes | No | Yes |
| Unblocks 173-S now | Yes | No | No | Yes | Yes |

## Decision

**Adopt Option E as a single coupled resolution. Implementation is REQUIRED
before 173-S can be safely closed; 173-S remains `active` and blocked until that
implementation ships.**

Both findings are one root cause: **the closure contract models a shipment as
operating on a live backlog** — a live covering feature, live unshipped siblings,
and a live shipment record transitioning `active → shipped`. It has no model for
a **fully-terminal closure**, where the entire scope was already archived before
closure began. Finding 1 is that assumption failing on the protected set; finding
2 is the same assumption failing on the record transition.

### E1 — `TERMINAL_CLOSE` classification (unblocks 173-S)

Extend `classify_shipment_close_path` with a third verdict, evaluated
fail-closed, defaulting to `SAFE_CLOSE` on any ambiguity and **never** to
`CASCADE`. All preconditions must hold:

1. Every manifest member resides in `.backlogit/archive/` and declares a
   terminal `status` (`done`, `archived`, or `shipped`) read from its own
   frontmatter — never inferred from location alone.
2. Every descendant, at every depth, of every manifest feature member — derived
   from the full `parent_id` walk across `queue/` + `archive/` — is likewise
   already archived and terminal, whether or not it is a manifest member.
3. The **only** artifact in the closure scope still live in `.backlogit/queue/`
   is the shipment record itself.
4. A git baseline proves every one of those archives **pre-exists this closure
   run** (present in `HEAD`, not produced by the working tree since claim). This
   is what distinguishes "already terminal" from "cascaded by me".
5. Any torn state (record in both `queue/` and `archive/`), missing record,
   malformed frontmatter, or failed enumeration → fall back to `SAFE_CLOSE`.

When `TERMINAL_CLOSE` holds, the close action is the backlogit shipment-ship
operation used **solely to transition the shipment record**, followed by a strict
post-condition: `archived_ids` must contain nothing outside the manifest closure
set, and no artifact outside that set may change content, verified by git
comparison against the Step 3 baseline.

**On any deviation, FAIL CLOSED in this order — never auto-restore:**

1. **Capture evidence**: record the observed `archived_ids` set, the git diff
   against the Step 3 baseline, and every affected artifact ID into the closure
   report. Leave the deviating working-tree state in place as evidence.
2. **HALT immediately**: perform no further mutation and do not continue the
   close sub-procedure.
3. **Emit a P-005 violation event** naming the affected IDs and the deviation.
4. **Request explicit operator approval**, presenting the captured evidence and
   the proposed repository-approved rollback action.
5. **Perform the repository-approved rollback ONLY after approval is granted.**

An automatic or immediate `git restore` — or any other destructive revert,
delete, or overwrite — is **PROHIBITED** here. Constitution Principle VII
(*Destructive Command Approval*, NON-NEGOTIABLE) requires operator approval
before any destructive terminal command or file overwrite, regardless of
permissive agent modes. The agent MUST NEVER silently auto-restore, and MUST
NOT treat a deviation as self-authorizing remediation.

Rationale for permitting the engine op here: the spike proves it is the *only*
mechanism in 1.10.1 that yields `archived_status: shipped`, and proves it is
observably inert against already-archived artifacts. Precondition 3 reduces its
reachable blast radius to the shipment record alone.

### E2 — Protected-set terminal-descope exemption (closes the class)

Generalize Step 2's sequence-aware exclusion so a sibling is excluded from the
protected set when it is (a) already archived at baseline, (b) terminal, (c)
carrying a verified P-021 C1 descope/merge disposition, and (d) git-proven to
pre-exist the run. Fail-closed on any missing element. The gate's real protection
— the Step 5 verify-after-each invariant measured against the Step 3 baseline —
is untouched, because an artifact already archived at baseline can carry no
signal about *this* run's cascade.

This does **not** weaken the gate: a live sibling, or an archived sibling without
a verified disposition, remains protected exactly as today.

### Sequencing note surfaced for the operator

The unblocking work must be executed while `173-S` is still `active`. `173-S` is
a closure-record remnant only — all its work is merged and landed — so it
consumes no execution capacity, but Ship claiming the new shipment while `173-S`
remains open is a **P-001 sequencing question that requires explicit operator
authorization**. Flagged, not assumed.

### Handoff status of shipment `174-S` (NOT EXECUTABLE)

Shipment `174-S` carries the harvested `166-F` hierarchy. Its `queued` status is
a **planning handoff record only**. It is **NOT executable and NOT claimable by
Ship**, and its deliberately **fail-closed unsequenced state** (no `dag_root`, no
declared dependencies, no bootstrap grant) is intentional and **MUST be
preserved as-is** by this deliberation. `174-S` becomes eligible for Ship
execution only when **all** of the following are satisfied:

1. `impl-plan` has produced an implementation plan for `166-F`.
2. **Mandatory `plan-harden`** has run (P-006: elevated blast radius across
   policy + skill + classifier + template mirrors — this is not optional here).
3. `plan-review` has returned a passing verdict on the hardened plan.
4. A **valid DAG declaration** exists for the shipment, **or** an
   operator-authored bootstrap grant has been issued.
5. **Explicit P-001 authority** has been granted for the sequencing overlap with
   the still-`active` `173-S`.

Until every one of those five conditions holds, `174-S` must remain unclaimed.
Stage does not and cannot grant any of them; conditions 4 and 5 are
operator-owned.

## Rejected Alternatives

* **A / D** are rejected as record-falsifying workarounds that change a safety
  classifier's verdict by editing history.
* **B alone** is rejected as insufficient — it leaves Step 8 deadlocked.
* **C** is retained as an optional upstream follow-up, not the critical path;
  E1's post-condition gate makes it unnecessary for correctness.
* **Cascading 173-S today on the strength of the spike alone** is explicitly
  rejected. The behaviour is benign in this shape, but authorizing it without the
  codified precondition is exactly the ad hoc narrowing the compound learning
  forbids.

## Unresolved Questions

1. Operator authorization for the P-001 sequencing overlap described above.
2. Whether `168-S` is fully terminal (→ E1) or retains live siblings (→ E2); to
   be classified at its own closure, not assumed here.
3. Whether to pursue Option C upstream once E1/E2 land.
4. Whether the widespread `done`-without-provenance archive shape warrants a
   separate normalization effort — **out of scope here**, recorded as an
   observation, and deliberately accommodated rather than corrected by E1.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| `TERMINAL_CLOSE` misfires on a shipment with live scope | Preconditions 1-3 require universal terminality across the full descendant walk; fail-closed default is `SAFE_CLOSE`, never `CASCADE` |
| Engine archives something unexpected | Strict `archived_ids` + git content post-condition; on deviation, fail closed — capture evidence, HALT, emit P-005, request operator approval, and roll back via a repository-approved action only after approval (never an automatic `git restore`; Constitution Principle VII) |
| Precondition written too strictly to ever fire | Terminality accepts `done`/`archived`/`shipped`; validated against the measured 1029-record archive survey |
| Exemption becomes a general gate bypass | E2 requires four independent conditions including git-proven pre-existence and a verified disposition note |
| Change is special-cased to 173-S | Both E1 and E2 are defined purely by shape; acceptance requires the `168-S`/`160-F` fixture to pass |
