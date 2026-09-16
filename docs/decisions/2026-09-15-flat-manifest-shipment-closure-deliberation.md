---
title: "Flat-manifest shipment closure: superseding the hierarchical-closure premise (operator architectural correction)"
description: "A shipment manifest is a flat list of exactly what is delivered, not a container over a covering feature and its descendants. Replaces the TERMINAL_CLOSE + terminal-descope-exemption decision with an engine-inertness containment model grounded in measured backlogit 1.10.1 behavior."
topic: "Shipment closure scope semantics: flat manifest vs. hierarchical closure"
depth: "deep"
decision_status: "decided"
promoted_to: "both"
linked_artifacts:
  - "docs/plans/2026-09-15-flat-manifest-shipment-closure-plan.md"
  - "docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md"
supersedes:
  - "docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md"
stash_entries:
  - "FBD2F6BE"
  - "2B42392E"
related_entries:
  - "3CA122AC"
tags:
  - "shipment-closure"
  - "flat-manifest"
  - "p-015"
  - "blast-radius-containment"
  - "backlogit-tooling"
  - "supersession"
---

## Problem Frame

The operator has issued an **architectural correction that supersedes the core
premise** of decision `docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md`
and its reviewed plan `docs/plans/2026-09-15-terminal-shipment-closure-plan.md`.

**The operator directive (binding product constraint, not an option):**

1. The current policy is **defective** because it ties a shipment to a covering
   feature *and all descendants* instead of treating it as a **flat manifest of
   exactly what is delivered**.
2. A shipment manifest **is not a container** and carries **no implicit
   hierarchical closure semantics**.
3. A feature **may be decomposed across multiple shipments**.
4. The **final** shipment for that feature carries the **feature item itself as
   the final manifest entry**, after the tasks delivered across the sequence are
   complete.
5. Items under a feature that are **excluded, removed, descoped, rejected,
   merged into other work, or otherwise absent from a shipment** must **never**
   block the feature record or shipment record from being marked shipped
   *solely because of their ancestry*.
6. **Shipment closure applies only to explicitly listed manifest items plus the
   shipment record.** Hierarchy may remain useful for planning and traceability
   but **must not expand closure scope**.

This deliberation treats (1)–(6) as **binding**. The prior decision's
`TERMINAL_CLOSE` + terminal-descope-exemption design is evaluated *against* that
constraint, not alongside it.

**Presenting symptom (unchanged).** Shipment `173-S` is functionally complete —
PR #450 merged (`9cc98c41`), closure PR #451 merged (`358b63b4`, current `main`
HEAD), all 11 manifest members terminal — but remains `active` because the
P-015 classifier, the `shipment-reconcile` safe-close protected-set gate, and the
policy text all expand closure scope through `parent_id` descendants and there
find two **archived, descoped, out-of-manifest** siblings, `165.007-T` and
`165.010-T`.

**Out of scope**: implementation; source/template/schema mutation; shipment
claim/close; PR creation; any mutation of `173-S`; granting P-001 overlap
authority; expanding `174-S` claimability.

## Research Findings

### F1 — The defect reproduces exactly as the operator characterizes it

Running the live classifier against `173-S`'s actual stored manifest:

```text
CLOSE_PATH: ClosePath.SAFE_CLOSE
REASON: feature member '165-F' has descendants outside the manifest:
        ('165.007-T', '165.010-T')
```

The disqualifying predicate in `src/autoharness/gates/shipment_closure.py` is
literally a **hierarchical-closure test**:

```python
missing = tuple(d for d in descendants if d not in manifest_id_set)
if missing:
    return ClosePathDecision(close_path=ClosePath.SAFE_CLOSE, ...)
```

It asks *"is every descendant a manifest member?"* — i.e. it requires the
manifest to be a **closed container over the feature subtree**. That is precisely
the premise the operator declares defective. The same predicate is mirrored in
P-015 precondition 1 and in `shipment-reconcile` Step 0(c).

### F2 — Verified live state of the 173-S closure scope

| Artifact | Location | declared `status` | `archived_status` | `parent_id` | In manifest |
|---|---|---|---|---|---|
| `165-F` | `archive/` | `done` | — | *(root)* | **yes** |
| `165.001-T` … `165.006-T`, `165.008-T`, `165.009-T`, `165.011-T`, `165.012-T` | `archive/` | `done` | — | `165-F` | **yes** |
| `165.007-T` | `archive/` | **`archived`** | `blocked` | `165-F` | **no** (descoped) |
| `165.010-T` | `archive/` | **`archived`** | `blocked` | `165-F` | **no** (merged) |
| `173-S` | `queue/` | `active` | — | — | *(the record)* |

The full `parent_id` walk from `165-F` yields exactly 12 descendants; exactly two
are out-of-manifest, and **both declare `status: archived`** in their own
frontmatter.

### F3 — Spike: what the backlogit 1.10.1 engine *actually* does

Four time-boxed Stage spikes (P-016 spike/research exception) ran in **disposable
`%TEMP%` workspaces** — no git branch, no worktree, repository untouched; all
four workspaces destroyed afterwards. Each mirrored a manifest shape exactly and
measured `archived_ids` / `returned_ids` plus per-file SHA-256 before and after.

**Arm 1 — the 173-S shape** (feature member in manifest; one out-of-manifest
sibling truly `status: archived`, `archived_status: blocked`):

```json
{ "archived_ids": ["001.001-T","001.003-T","001-F","001-S"],
  "returned_ids": [] }
```

| Artifact | Result |
|---|---|
| in-manifest members + feature + record | archived (expected) |
| **out-of-manifest, truly `archived` sibling** | **byte-identical** — hash, `updated_at`, `archived_status: blocked`, `parent_id` all preserved |

**The engine already behaves flat here.** `archived_ids` was exactly
`manifest ∪ {record}`. The truly-archived out-of-manifest sibling was *skipped*,
never touched.

**Arm 2 — feature member in manifest, out-of-manifest descendants NOT truly
archived** (one `status: done`, one **live `status: queued`**):

```json
{ "archived_ids": ["001.001-T","001.002-T","001.003-T","001-F","001-S"],
  "returned_ids": [] }
```

Both out-of-manifest descendants were **archived** — including the **live
`queued`** one, which was forced to `done` and archived. **`returned_ids` was
empty**, so the skill's step-2 `returned_ids` guard did **not** fire. This is a
genuinely destructive, out-of-scope cascade that only the *post-mutation*
`archived_ids - allowed_ids` check would catch.

**Arm 3 / Arm 4 — partial-feature shape, no feature member in manifest**
(manifest `[001.001-T]`; live parent `001-F` and live sibling `001.002-T` both
out-of-manifest), reproduced twice in independent clean workspaces:

```json
{ "archived_ids": ["001.001-T","001-S"],
  "returned_ids": ["001.002-T"] }
```

| Artifact | Result |
|---|---|
| live parent feature `001-F` (out-of-manifest) | **untouched** — engine never walks *up* to parents |
| in-manifest `001.001-T` | archived, `parent_id` **preserved** |
| live out-of-manifest sibling `001.002-T` | returned — **but its `parent_id` was silently CLEARED** (orphaned) |

**Synthesis of F3 (the governing empirical law).** The engine's blast radius is
**not** a function of hierarchy per se; it is a function of **the presence of a
feature member in the manifest** and **the declared status of out-of-manifest
descendants**:

| Manifest shape | Out-of-manifest descendant state | Engine effect on it |
|---|---|---|
| contains a feature member | declared `status: archived` | **inert** — skipped, byte-identical |
| contains a feature member | `done`, or live (`queued`/`active`) | **archived** (destructive; `returned_ids` empty) |
| no feature member | live | **returned, `parent_id` cleared** (orphaned) |
| any | *parent/ancestor* of a manifest item | untouched (no upward walk) |

### F4 — `move --status shipped` is refused; `ShipShipment` is the only path to provenance

Reproduced independently (2B42392E):

```text
$ backlogit move 001-S --status shipped
move shipment 001-S to shipped via generic path:
backlogit: shipment must be shipped via ShipShipment, not a direct status update
EXITCODE=9
```

`backlogit shipment ship` yields exactly `status: archived` +
`archived_status: shipped` — the precise provenance safe-close Step 8 demands.
There is **no non-cascading path to `shipped` in 1.10.1**.

### F5 — The autoharness overlay is *stricter* than the engine, and in the wrong dimension

Arm 1 proves the engine is already flat for truly-archived out-of-manifest
descendants. `173-S` is therefore blocked **not by the engine**, but by an
autoharness-invented hierarchical-closure precondition that the engine itself
does not enforce. Conversely, Arm 2 proves the overlay's *`returned_ids`* guard
is **insufficient** where the engine genuinely is destructive.

So the existing design is simultaneously **too strict** (blocks 173-S on inert
artifacts) and **too weak** (relies on a guard that does not fire on the real
destructive case). Both errors share one root cause: the overlay reasons about
**hierarchy membership** when the safety-relevant question is **mutability**.

### F6 — Why the superseded TERMINAL_CLOSE design is structurally incompatible

The prior decision's E1 preconditions cannot be reconciled with the directive:

* **E1 precondition 2** — "*every descendant, at every depth, of every manifest
  feature member … is likewise already archived and terminal, whether or not it
  is a manifest member*" — is hierarchical closure **restated**, merely with a
  terminality test substituted for a membership test. It still expands closure
  scope through ancestry, violating directive (6).
* **E1 precondition 3** — "*the only artifact in the closure scope still live is
  the shipment record*" — makes **multi-shipment feature delivery unreachable**.
  When feature `F` is split across `S1..Sn`, at `S1`'s closure the tasks destined
  for `S2..Sn` are live descendants of `F`, so `TERMINAL_CLOSE` can never fire.
  This directly contradicts directive (3).
* **E2**'s exemption requires a sibling to carry "*a verified P-021 C1
  descope/merge disposition*". Directive (5) says excluded items must never block
  closure **solely because of their ancestry** — it grants no license to demand a
  disposition note as the price of exclusion. E2 replaces an ancestry gate with a
  *paperwork* gate over the same out-of-scope artifacts.

E1/E2 are therefore not merely sub-optimal under the new premise; they encode the
superseded premise. They must be withdrawn, not tuned.

### F7 — Class scope is unchanged

Stash `3CA122AC` records the identical failure for `168-S` / `160-F` /
`160.019-T`. P-015 forbids narrowing any exception "to any particular feature ID,
shipment ID, or manifest shape". The remedy below is defined purely by
**declared status and manifest membership**, never by ID.

## Options Evaluated

### Option F (RECOMMENDED): Flat manifest + engine-inertness containment gate

Redefine closure scope as flat, and demote the descendant walk from a
*scope-definition* device to a *blast-radius containment* check over the engine.

* Closure scope is **exactly** `items(S) ∪ {S}` (plus engine-forced linked
  deliberations of manifest feature members).
* The cascade op is permitted **only when every out-of-manifest artifact the
  engine can reach is provably engine-inert** — i.e. declares `status: archived`.
* Out-of-manifest artifacts require **no** manifest membership, **no** disposition
  note, and **no** particular `archived_status`.
* **Pros**: implements the directive exactly; unblocks `173-S` with *no* new
  verdict; strictly **safer** than today (Arm 2's destructive case is caught
  *before* mutation rather than after); permits multi-shipment feature delivery;
  purely shape-based; eliminates E1/E2 machinery entirely.
* **Cons**: touches classifier + policy + skill + mirrors (elevated blast radius,
  P-006 hardening mandatory); does not by itself fix the partial-shipment record
  transition (see Option H / residual R1).
* **Effort**: medium. **Fit**: best.

**Is this "hierarchy closure under another name"?** No — and the difference is
*observable*, which is the test that matters:

| Out-of-manifest descendant | Hierarchical closure (old) | Inertness containment (new) |
|---|---|---|
| archived, descoped (`165.007-T`) | **disqualifies** | **passes** (inert) |
| archived, no disposition note | disqualifies (and fails E2) | **passes** (inert) |
| `done`, not archived | disqualifies | disqualifies — *because the engine would archive it* |
| live `queued` | disqualifies | disqualifies — *because the engine would destroy it* |
| live, in a later shipment `S2` of the same feature | disqualifies → blocks split delivery | disqualifies **this cascade only**; `S1` closes via safe-close, `Sn` carries the feature |

The old predicate asks *"is the subtree inside the manifest?"* (scope). The new
predicate asks *"can this tool mutate anything outside the manifest?"* (blast
radius). The first grows closure scope; the second constrains an instrument. The
row that proves they are different is row 1 — the exact `173-S` case.

### Option G: Pure flat manifest with no descendant inspection at all

Take directive (6) maximally literally: never enumerate descendants; always
invoke the cascade; rely solely on the post-hoc `archived_ids - allowed_ids` gate.

* **Pros**: simplest possible reading; zero hierarchy code.
* **Cons**: **empirically unsafe**. Arm 2 shows the engine archives live
  out-of-manifest tasks and reports `returned_ids: []`; Arm 3/4 show it silently
  clears `parent_id` on returned siblings. A post-mutation check halts *after*
  the corruption, and P-015's own violation action then demands a destructive
  `git restore`. This would make the policy *cause* the corruption it exists to
  prevent.
* **Fit**: rejected — the directive constrains **closure scope**, not the
  agent's duty to avoid destroying out-of-scope artifacts. Declining to mutate
  what is outside the manifest is the directive's *enforcement*, not a violation
  of it.

### Option H: Upstream backlogit change for a non-cascading `shipped` transition

Request `shipment ship --no-cascade`, or permit a direct status update.

* **Pros**: the only clean fix for the partial-shipment record transition (F4);
  would let a flat manifest close with literally zero engine scope expansion.
* **Cons**: external Go project; unbounded timeline; cannot unblock `173-S` now.
* **Fit**: **required follow-up**, not the critical path. Recorded as R1.

### Option I: Reframe 166-F in place vs. supersede with a new feature/shipment

* **Reframe in place** (`166-F`, `166.001-T`..`166.006-T`, `174-S` retained):
  preserves the **operator-authorized `dag-root` label already on `174-S`**;
  requires no new authorization; keeps one traceable lineage.
* **Supersede with a new `NNN-F`/`NNN-S`**: would require a **new** operator
  `dag-root` authorization — i.e. it would *expand* operator-owned authority,
  which the operator explicitly forbade in this session.
* **Fit**: **reframe in place**, with explicit supersession markers on the old
  decision and plan.

### Option J: Retain TERMINAL_CLOSE as a third verdict alongside the flat model

* **Cons**: `TERMINAL_CLOSE`'s preconditions are unreachable under Option F
  (anything it would accept, Option F already accepts via inertness), so it is
  dead code carrying a superseded premise into the codebase.
* **Fit**: rejected as redundant and premise-contaminating.

## Trade-off Comparison

| Criterion | F (flat + inertness) | G (no inspection) | H (upstream) | J (keep TERMINAL_CLOSE) |
|---|---|---|---|---|
| Honors operator directive (flat manifest) | **Yes** | Yes (literal) | N/A | **No** |
| Permits multi-shipment feature delivery | **Yes** | Yes | N/A | **No** |
| Excluded items never block on ancestry | **Yes** | Yes | N/A | Only with a disposition note |
| Unblocks `173-S` now | **Yes** | Yes (unsafely) | No | Yes |
| Prevents Arm-2 destructive cascade | **Yes (pre-mutation)** | **No** | Yes | Yes |
| Prevents Arm-3/4 `parent_id` orphaning | **Yes** | **No** | Yes | Partially |
| Adds new closure verdicts | No | No | No | Yes |
| Self-owned / bounded timeline | Yes | Yes | **No** | Yes |
| Generalizes to `168-S` / the class | Yes | Yes | Yes | Yes |

## Decision

**Adopt Option F (flat manifest + engine-inertness containment), reframing
`166-F`/`174-S` in place per Option I, and record Option H as required follow-up
R1. The prior decision's `TERMINAL_CLOSE` (E1) and terminal-descope exemption
(E2) are WITHDRAWN.**

### D1 — Closure-scope invariants (normative)

Let `S` be a shipment with declared manifest `items(S)`.

* **INV-1 (Flat closure scope).** `closure_scope(S) = items(S) ∪ {S}`, extended
  only by linked deliberations of manifest **feature** members that the engine
  itself forces into scope. **Ancestry never adds a member.** No artifact outside
  `closure_scope(S)` may be created, modified, moved, or deleted by closing `S`.
* **INV-2 (Membership is explicit and exhaustive).** An artifact is in scope
  **iff** its ID appears in `items(S)`. Absence from `items(S)` is a complete and
  sufficient statement that the artifact is **not** part of this delivery.
* **INV-3 (Exclusion is never a gate).** An artifact under a feature but absent
  from `items(S)` may be in **any** state — `queued`, `active`, `blocked`,
  `archived`, descoped, merged, rejected, or absent from the workspace entirely —
  and **MUST NOT** block `S`, or the feature record, from reaching a terminal
  state *on the ground of ancestry*. No disposition note, no `archived_status`
  value, and no provenance is required of it.
* **INV-4 (Multi-shipment feature delivery).** A feature `F` MAY be delivered
  across an ordered sequence `S1 … Sn`. `S1..Sn-1` carry **no** feature member.
  **Exactly one** shipment — the final `Sn` — carries `F` itself as a manifest
  entry, placed **last** in `items(Sn)`.
* **INV-5 (Feature terminality precondition).** `Sn` may carry `F` only when every
  task **actually delivered** by `S1..Sn` is terminal. Tasks excluded from every
  manifest in the sequence are **not** subject to this precondition (INV-3).
* **INV-6 (Engine-inertness containment gate).** The cascade op MAY be used only
  when **every** artifact reachable by the engine's own scope expansion from
  `items(S)` but **outside** `closure_scope(S)` declares `status: archived` in its
  own frontmatter (read from the record, never inferred from `queue/`/`archive/`
  location). Any such artifact that is live or merely `done` **forbids the
  cascade** and forces safe-close. This is a **blast-radius constraint on an
  instrument**, not a definition of closure scope — it never adds a member to
  `closure_scope(S)` and never requires an out-of-manifest artifact to join the
  manifest.
* **INV-7 (Baseline invariance replaces baseline presence).** Safe-close's
  protected-set gate is redefined: record each out-of-manifest artifact's
  **baseline location and content hash**, and require that **nothing outside
  `closure_scope(S)` changes** during the run. A protected artifact that was
  *already* archived, descoped, or missing **at baseline** is recorded as baseline
  state and is **NOT** a halt — it carries no signal about *this* run.
* **INV-8 (Manifest ordering is an assembly convention, never a closure gate).**
  INV-4's "feature last" ordering is enforced by **Stage at shipment assembly**.
  Ship MUST NOT evaluate manifest ordering as a closure precondition. *(Required
  for backward compatibility — see D3.)*
* **INV-9 (DAG orthogonality).** Shipment sequencing (`dag-root`, declared
  predecessors, `pipeline-topology`) is **orthogonal** to closure scope. INV-4
  creates a shipment-level ordering `S1 → … → Sn`; it does **not** create or
  imply any dependency edge, and closure never consults the DAG.
* **INV-10 (Postconditions).** After closing `S`:
  `archived_ids ⊆ closure_scope(S) ∪ validated_linked_deliberations`;
  every member of that set not truly `archived` in the pre-close snapshot appears
  in `archived_ids`; every artifact outside it is **byte-identical** to baseline
  (including `parent_id`); and `S` declares `status: archived` +
  `archived_status: shipped`.

### D2 — What changes, concretely

1. **Classifier** (`src/autoharness/gates/shipment_closure.py`): replace the
   `descendants ⊆ manifest` coverage predicate with the INV-6 inertness predicate.
   The descendant walk is **retained** — it is the only way to compute the engine's
   reachable set — but its verdict changes from *"must be in the manifest"* to
   *"must be engine-inert"*. Fail-closed default remains `SAFE_CLOSE`.
2. **P-015** (`.github/policies/workflow-policies.md` + `templates/` mirror):
   restate the exception in flat-manifest terms; add INV-1..INV-10; record the
   withdrawal of the hierarchical-closure preconditions with a supersession note.
3. **`shipment-reconcile` skill** (both mirrors): Step 0(c) adopts INV-6;
   Step 2/3 adopt INV-7; the Arm-2 finding is recorded as the reason the
   `returned_ids` guard is **not** sufficient on its own.
4. **No `TERMINAL_CLOSE` verdict is added.** The classifier keeps exactly two
   verdicts.

### D3 — Migration and backward compatibility

* **Existing manifests are unaffected in membership.** No manifest is rewritten.
* **Ordering**: every historical manifest (including `173-S`) lists the covering
  feature **first**, not last. INV-8 therefore makes ordering non-normative at
  closure, so **no historical manifest is invalidated** and `173-S` need not be
  touched. INV-4's "feature last" applies to **newly assembled** shipments only.
* **`173-S` expected closure path** (read-only dry-run, D4): out-of-manifest
  descendants `{165.007-T, 165.010-T}` both declare `status: archived` → **inert**
  → INV-6 satisfied → classifier returns `CASCADE` → the engine op transitions the
  record to `archived_status: shipped`. Step 8's `move --status shipped` deadlock
  (2B42392E) is **never reached**, because safe-close is not the selected path.
  Predicted `archived_ids` = the 11 manifest members + `173-S` = 12 IDs;
  `returned_ids` = `[]`; `165.007-T` and `165.010-T` **byte-identical**.
* **`168-S` / `160-F`** (`3CA122AC`): classified at its own closure by the same
  shape-based rule; used as a **control fixture**, never assumed.

### D4 — Read-only dry-run obligation

A mandatory, **read-only** dry-run must prove, without mutating anything, that
`173-S` is closable under flat-manifest semantics and that
`{165.007-T, 165.010-T}` are untouched. It computes the classifier verdict, the
engine-reachable set, the predicted `archived_ids`/`required_ids`/`allowed_ids`,
and a pre-image hash manifest of every out-of-manifest artifact. It performs
**no** writes. A dry-run returning anything other than `CASCADE` with a
containment-clean prediction is a **STOP, DO-NOT-SHIP** condition.

### D5 — Authority boundaries (unchanged by this decision)

* **No P-001 overlap authority is granted or implied.** It remains operator-owned
  and is still `174-S`'s sole outstanding claim blocker.
* **No bootstrap grant is issued.** `174-S` retains the *existing*
  operator-authorized `dag-root` label and its empty `dependencies` field. This
  deliberation does **not** prove the root itself must change, so it is preserved
  exactly as authorized.
* **`173-S` is not altered** by this deliberation or its plan.

## Rejected Alternatives

* **TERMINAL_CLOSE (prior E1)** — withdrawn: precondition 2 is hierarchical
  closure restated, and precondition 3 makes multi-shipment feature delivery
  unreachable (F6).
* **Terminal-descope exemption (prior E2)** — withdrawn: substitutes a
  disposition-note gate for an ancestry gate over artifacts that INV-3 says must
  not gate closure at all.
* **Option G (no descendant inspection)** — rejected: empirically destructive
  (Arms 2–4).
* **Option J (keep TERMINAL_CLOSE alongside)** — rejected as unreachable dead
  code carrying a superseded premise.
* **Clearing `parent_id` / re-manifesting the descoped siblings** — remain
  rejected exactly as in the prior decision; both falsify history, and INV-3 now
  makes both unnecessary.
* **Creating a replacement feature/shipment** — rejected per Option I: it would
  require new operator `dag-root` authorization the operator forbade expanding.

## Unresolved Questions

1. **R1 (operator/upstream):** the partial-shipment record transition. For a
   genuine `SAFE_CLOSE` shipment, `move --status shipped` is refused (F4) and the
   cascade is unsafe (Arms 3–4 clear `parent_id` on returned siblings), so **no
   safe path to `archived_status: shipped` exists in 1.10.1**. Not on `173-S`'s
   critical path. Must be surfaced as a fail-closed halt with an explicit
   escalation message rather than a silent workaround, and pursued upstream
   (Option H).
2. **R2:** the engine's `parent_id`-clearing on returned siblings (Arms 3–4) is
   arguably an upstream defect and should be reported regardless of R1.
3. **R3:** P-001 overlap authority for `174-S` vs. the still-active `173-S` —
   operator-owned, still open.
4. **R4:** whether `168-S` qualifies under INV-6 — to be classified at its own
   closure.
5. **R5:** the widespread `done`-without-provenance archive shape (366 records)
   remains an observation, accommodated rather than corrected.

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Inertness gate misread as hierarchy closure in review or implementation | INV-6 is stated as a constraint on the *instrument*; the Option F discrimination table pins the observable difference (row 1 = `173-S`); a pinning test asserts an archived descoped sibling **passes** |
| Arm-2 destructive cascade regresses | Pre-mutation inertness check + retained post-mutation two-set gate; Arm 2 becomes a mandatory negative-scenario test |
| `returned_ids` treated as sufficient protection | Explicitly recorded as **insufficient** (Arm 2 returned `[]` while archiving a live task); the skill text must say so |
| Multi-shipment delivery still blocked in practice | INV-4/INV-5 pinned by a split-delivery fixture (`S1` tasks only, `Sn` tasks + feature last) |
| Historical manifests invalidated by "feature last" | INV-8 makes ordering non-normative at closure; `173-S` remains untouched and closable |
| Change special-cased to `173-S` | INV-1..INV-10 are defined by declared status + membership only; acceptance requires the `168-S`/`160-F` control fixture |
| Dry-run mutates something | D4 dry-run is read-only by construction and hash-verifies the workspace before/after |
| R1 silently worked around | Fail-closed halt with an explicit escalation message; never substitute the cascade on a non-inert manifest |
