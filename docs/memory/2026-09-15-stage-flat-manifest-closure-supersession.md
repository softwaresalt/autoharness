---
date: 2026-09-15
agent: stage
session: flat-manifest-shipment-closure-supersession
feature: 166-F
shipment: 174-S
decision: docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md
plan: docs/plans/2026-09-15-flat-manifest-shipment-closure-plan.md
supersedes:
  - docs/decisions/2026-09-15-173-s-terminal-shipment-closure-deliberation.md
  - docs/plans/2026-09-15-terminal-shipment-closure-plan.md
status: complete
---

# Stage session — flat-manifest shipment closure supersession

## Trigger

Operator issued a binding architectural correction superseding the core premise
of the 166-F / 174-S decision and reviewed plan: a shipment manifest is a **flat
manifest of exactly what is delivered**, not a container over a covering feature
and all its descendants. Closure scope is exactly the listed manifest items plus
the shipment record. Ancestry must never block closure. A feature may be split
across multiple shipments, with the feature item as the final manifest entry of
the final shipment.

## What was decided

`INV-1..INV-10` in the superseding decision. Load-bearing points:

* **INV-1/INV-2** — closure scope is manifest items + shipment record. Hierarchy
  is planning/traceability metadata only; it never expands closure.
* **INV-3** — excluded, removed, descoped, rejected, or merged items never block
  the feature record or shipment record on the ground of ancestry.
* **INV-4/INV-5** — multi-shipment feature delivery: the feature item is the
  final manifest entry of the final shipment, after tasks delivered across the
  sequence are complete.
* **INV-6** — the descendant walk is **retained but re-purposed**: its verdict
  changes from *"is it in the manifest?"* (scope) to *"can the engine mutate
  it?"* (blast radius). This is the single most important design point.
* **INV-8** — manifest ordering is a **Stage assembly convention, never a Ship
  closure precondition**. Without this, every historical manifest (which lists
  the feature *first*) would have been invalidated, including 173-S.

`TERMINAL_CLOSE` and the terminal-descope exemption are **withdrawn**. No third
close verdict is added.

## Why the prior approach was withdrawn

* Prior `E1` precondition 2 ("every descendant already archived and terminal")
  is hierarchical closure restated under another name — exactly what the
  operator directive forbids.
* Prior `E1` precondition 3 ("the only live artifact is the shipment record")
  makes multi-shipment feature delivery structurally **unreachable**.
* Prior `E2` replaced an ancestry gate with a disposition-note gate over
  artifacts that `INV-3` says must not gate closure at all.

## Empirical grounding (four disposable spikes, backlogit 1.10.1)

Run in `%TEMP%` workspaces under the P-016 spike exception; all destroyed.

| Manifest shape | Out-of-manifest descendant | Engine effect |
|---|---|---|
| has feature member | declares `status: archived` | **INERT** — skipped, byte-identical |
| has feature member | `status: done` | **ARCHIVED** (out-of-scope mutation) |
| has feature member | live `queued` | **ARCHIVED**, `returned_ids` was `[]` |
| no feature member | live sibling | **RETURNED**, `parent_id` silently **CLEARED** |
| any | ancestor of a manifest item | untouched (no upward walk) |

The overlay is simultaneously **too strict** (blocks 173-S on provably inert
artifacts) and **too weak** (its `returned_ids` guard does not fire on the real
destructive case). That asymmetry is the whole argument for INV-6.

## Migration / back-compat

Migration is **purely additive**. The test helper `_write_artifact` in
`tests/test_shipment_closure_classification.py` writes **no `status` field**, so
every existing out-of-manifest fixture is non-inert under INV-6 and still yields
`SAFE_CLOSE`. The existing 23-test negative suite survives unchanged.

## 173-S closure path (read-only dry-run executed, no writes)

Dry-run returned **`CASCADE`**, containment-clean. Both excluded siblings
(`165.007-T`, `165.010-T`) were absent from `allowed_ids` and `required_ids`; no
STOP condition fired. Both declare `status: archived` and are therefore
engine-inert, so the refused `move --status shipped` deadlock is never reached.

After 174-S ships, 173-S closure is a **full re-run of shipment-reconcile from
Step 0/1** — never a resume at Step 8.

## Residual risks routed upstream

* **R1** — for a genuine `SAFE_CLOSE` shipment there is **no** safe path to
  `archived_status: shipped` in 1.10.1: `move --status shipped` is refused
  (exit 9) and the cascade is unsafe. Handled as a fail-closed halt,
  `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`. Out of scope for this shipment.
* **R2** — the engine silently clears `parent_id` on returned siblings. Upstream
  backlogit defect; report filed as a follow-up.

## Backlog disposition

Reframed **in place** (not replaced) to avoid requiring a fresh operator
`dag-root` authorization and to preserve traceability. 166-F retitled and
rewritten; all six tasks retitled/rewritten with corrected size/complexity; one
dependency edge added (`166.005-T ← 166.004-T`) to serialize two units editing
the same two skill mirrors.

Final DAG (acyclic): `166.002 → {166.001, 166.003, 166.004} → 166.005 → 166.006`.

174-S manifest MEMBERSHIP (same 7 items), `dag-root` label, empty `dependencies`,
and `status: queued` all **unchanged**; its description was updated to point at
the new decision and plan.

**Manifest ordering reconciled (2026-09-15, follow-up correction).** As first
assembled, 174-S listed the covering feature `166-F` **first** and its body
asserted that feature-first ordering "remains valid and requires no rewrite" for
this shipment. That was a packaging defect: 174-S is a **newly assembled**
shipment, and under INV-4/INV-5 — as bound by the superseding decision (D3) and
the reviewed plan (trace rows R05/R06) — the final shipment delivering a feature
carries that feature as the **final** manifest entry, after the delivered tasks.
The manifest was reconciled in place to the operator-authorized **feature-last**
assembly convention:

`166.002-T, 166.001-T, 166.003-T, 166.004-T, 166.005-T, 166.006-T, 166-F`

(delivered tasks first in DAG order, covering feature last). Membership, labels,
dependencies, status, and the task DAG are untouched. Because backlogit 1.10.1
exposes no shipment item-order mutation operation (`shipment add` is append-only;
no remove/reorder command exists), this was applied as a minimal out-of-band edit
to `.backlogit/queue/174-S.md` followed immediately by `backlogit sync`.

Scope limits of this correction: ordering is **not** promoted to a Ship closure
precondition — INV-8 still holds, and Ship MUST NOT evaluate manifest ordering as
a closure gate. **No historical manifest is invalidated, rewritten, or reordered**;
manifests listing the feature first (including 173-S) remain valid, since INV-4's
feature-last applies to newly assembled shipments only. The reviewed plan's
`decision: PASS` verdict and all of its findings — including P1-1 and its INV-8
resolution — are unchanged; no re-deliberation and no re-review were performed.

## Invariants held

173-S, 165-F, 165.007-T, 165.010-T byte-identical to HEAD. No P-001 overlap
authority granted. No bootstrap grant. No claimability expansion. No code
implemented, no PR, no shipment claimed or closed. Unrelated dirty worktree
state preserved. Test suite green (2251 passed, 54 skipped).

## Next action

Operator-owned: grant or withhold **P-001 overlap authority** for 174-S against
the still-active 173-S. That is the sole outstanding claim blocker.
