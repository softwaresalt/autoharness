---
title: "Stage session memory — 165-F / 173-S review-fix cycle 1"
description: "Session memory for the Stage review-fix cycle that resolved the eleven-finding BLOCK against plan revision 1 (commit 4c09e50b)."
doc_type: memory
source: docs/memory/2026-09-12/stage-165f-173s-review-fix-cycle-1.md
date: 2026-09-12
agent: stage
feature_id: 165-F
shipment_id: 173-S
---

# Stage — 165-F / 173-S, review-fix cycle 1

Supersedes the planning narrative in
`docs/memory/2026-09-12/stage-dag-authoritative-predecessor-derivation.md`, which
describes plan **revision 1** (commit `4c09e50b`). That revision's review was
overturned to **BLOCKED** by the operator with eleven findings. This session
produced plan **revision 2** and a cycle-2 **PASS**.

## What changed, and why it mattered

The single load-bearing correction: revision 1 proposed a config key
`unsequenced_shipment: warn|block` and described `block` as restoring legacy
behaviour. That framing was wrong in a way that would have shipped a deadlock.
Legacy behaviour blocked a shipment only when a numerically lower **unshipped**
shipment existed — a genuine DAG root passed. A flat `block` is strictly more
restrictive: it blocks *every* edge-less shipment, including all legitimate roots,
permanently, with no exit.

Revision 2 replaces it with a **four-state contract** carried entirely in data
that already exists:

| State | Condition | Outcome | `predecessor_source` |
|---|---|---|---|
| Explicit | `blocking_predecessor_ids` non-empty | existing ambiguity/terminal/closure checks | `explicit` |
| Declared root | no edges + record carries the `dag-root` label | pass | `declared_root` |
| Genesis | no edges, no label, workspace has **no** shipped-terminal shipment (live **or archived**) | pass (bootstrap) | `genesis` |
| Unsequenced | no edges, no label, workspace **has** shipping history | **block** `UNSEQUENCED_SHIPMENT`, naming both remedies | `unsequenced` |

The states are total and mutually exclusive. No numeric comparison survives on the
claim path in any state — which matters because all three prior defects in this
file came from getting the *direction* of a numeric predicate wrong, so removing
the predicate beats re-tuning it.

## Key decisions

* **D1** — the four-state contract above.
* **D2** — **no config key, therefore no schema surface.** Empirically validated
  that `backlogit update <id> --labels ...` persists `labels:` on a shipment
  record, so root declaration needs no backlogit change, no root-schema change, no
  new immutable versioned schema mirror, no `schema_contracts.py` change, no
  `templates/harness-config.yaml.tmpl` edit, no install/tune preservation work,
  and no dogfood config edit. The operator's finding 7 offered "add a task to cover
  all those surfaces" or "simplify the key away"; the simpler branch is taken.
* **D3** — a read-only, **non-authorizing** sequencing audit phase
  (`audit_sequencing`, registered in `VALID_PHASES` only, never `SCOPED_PHASES`)
  re-homes `_prior_shipment_id` as a migration *report* input. The heuristic is
  therefore retained, not deleted — deleting it in 165.002-T would dangle.
* **D4** — the closure producer/consumer defect is **descoped**.
* **D5** — advisory parity across all four states, both directions, via one shared
  helper; `pre_claim` stays sole claim authority.
* **D6** — a bounded, durable bootstrap disposition authorizing **one** audited
  `pre_claim --force` for `173-S` only. Recorded in the shipment record with five
  explicit bounds. Grants no broader force authority.

## Backlog changes

* `165-F` description rewritten to the new contract.
* `165.001-T` — retitled; characterization tests (C1–C4, behaviour that already
  exists) separated from genuinely new strict-xfail expectations (N1–N6 + N5b
  archived-history genesis). S→M.
* `165.002-T` — now performs the **atomic** re-expression of all five
  `ImplicitNumericPredecessorTests` cases in the same commit that removes the
  behaviour they pin. This is what makes every task end green; revision 1 had the
  migration in a later task, which would have left the suite red in between.
  Also gained fail-closed `labels` parsing and the archived-history genesis probe.
* `165.003-T` — **repurposed** from "migrate numeric tests" to the audit phase. S→M.
* `165.004-T` — total P1–P7 advisory-parity matrix.
* `165.005-T` — shared derivation/closure helper; policy-blocked shipments excluded
  from `ready_set`/`next_eligible`; one workspace genesis snapshot for both gates.
* `165.006-T` — four provenance values, remedy-naming CLI text, audit rendering.
* `165.007-T` — **archived**, removed from the manifest via
  `backlogit shipment return-blocked`, dependency edge removed first, forward
  reference to `FD0CCB42` recorded.
* `165.008-T` — scope reduced to the two agent `.tmpl` sources; the incorrect
  `.github/instructions/workflows.instructions.md` mapping removed (verified: that
  file carries no `pre_claim`/`PREDECESSOR_`/`dag-readiness` token); the "optional
  follow-up" escape hatch removed. M→S.
* `165.010-T` — **created** to carry the installed dogfood mirrors as a mandatory
  dependent task inside 173-S, replacing 165.007-T's slot.
* `165.009-T` — docs rewritten; committed-artifact cross-references only.
* `173-S` — labels `dag-root,topology-gate`; D6 disposition recorded in body.

## Stash entries created

* **`FD0CCB42`** (bug, high, `DEFERRED SCOPE EXPANSION`) — closure producer/consumer
  naming contract. Producer
  (`.github/skills/operational-closure/SKILL.md:23`) writes
  `docs/closure/{date}-{slug}-closure.md`; the consumer globs
  `{shipment_id}-*-post-merge-closure.md`. 162-S is the first shipment under the new
  producer naming, which is why `163-S`'s dependency on it reads as missing closure
  evidence. The artifact **exists** — this is naming drift, not a missing file — so
  authoring a "correct-name" closure doc is explicitly prohibited as it would create
  a competing artifact. Do not weaken the closure gate.
* **`9AA34143`** (bug, low, `DEFERRED SCOPE EXPANSION`) — shipment
  `size_composition.members` derives from `parent_id` children rather than the
  manifest, so archived/descoped `165.007-T` still appears in 173-S's rollup. The
  manifest itself is correct.

## Provenance hygiene

All references to the untracked operator-owned bug document were removed from both
the decision and the plan, including an ellipsized path. Historical context is
preserved as prose. The plan and decision are now self-contained against committed
sources only (current `topology.py`/tests, `docs/compound/`, and the operator
directive). The untracked operator files were neither modified nor committed.

## Next steps

1. Ship claims `173-S` using the single audited `pre_claim --force` authorized by
   D6, and records the audit.
2. Execute 165.001-T → 165.010-T in dependency order.
3. `FD0CCB42` needs its own deliberation and work unit — separate from 165-F.
4. `9AA34143` is a backlogit-side fix, outside autoharness shipments.
5. Scope fences hold: `86498B64` (explicit branch contracts) is next but separate;
   `9B582824` cost epic separate; `97B28746`/`50434138` separate; `58A85283`
   excluded.
