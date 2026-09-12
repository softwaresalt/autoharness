---
title: "DAG-authoritative predecessor derivation for the pipeline-topology pre_claim gate"
description: "Decision to make explicit backlogit `blocks` dependencies the sole source of predecessor derivation in `pipeline-topology --phase pre_claim`, retiring the implicit numeric-adjacency heuristic behind a fail-closed migration posture, and aligning `dag-readiness` advisory output with the authoritative model."
doc_type: decision
source: docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md
date: 2026-09-12
status: decided
deciders: operator, Stage
stash_ids:
  - AF2890B7
related_stash_ids:
  - 86498B64
  - 9B582824
  - 97B28746
  - 50434138
supersedes_recommendation_in: docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md
---

# DAG-Authoritative Predecessor Derivation for `pipeline-topology pre_claim`

## Problem Frame

The autoharness gate binary derives a shipment's claim-blocking predecessors in
`src/autoharness/gates/topology.py::_shipment_readiness_check` from **two**
sources unioned together:

1. `ShipmentState.blocking_predecessor_ids` — the explicit backlogit `blocks`
   DAG edges (authoritative dependency protocol).
2. `_prior_shipment_id()` — an **implicit numeric-adjacency** heuristic that,
   when no explicit predecessor exists, substitutes the nearest lower-numbered
   `{N}-S` shipment as a synthetic predecessor.

The operator has requested (2026-09-12) that explicit DAG dependencies become
the authoritative sequencing source, because the numeric heuristic "is
consistently causing problems in this and other workspaces."

The prior bug report
(`docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md`,
§7) recommended a **presentation-only** remedy and explicitly labelled
numeric-fallback removal a *future* contract-change option, not the presumed
fix. **This deliberation supersedes that recommendation** under new operator
product direction. The bug document is preserved unmodified as the historical
record; this artifact records the new decision rather than rewriting history.

## Research Findings

### Finding 1 (CRITICAL — corrects the triggering framing)

The orchestrator framing stated the gate blocked `163-S` because it *inferred*
archived `162-S` as a numeric predecessor. **This is factually incorrect and
was disproven by direct reproduction in this workspace.**

```text
$ backlogit dep list 163-S
163-S → 162-S (blocks)                      # EXPLICIT DAG edge

$ Get-Content .backlogit/queue/163-S.md
dependencies:
    - 162-S                                  # EXPLICIT, recorded in frontmatter

$ autoharness gate pipeline-topology --mode agent --shipment 163-S \
      --phase pre_claim --json
"token": "PREDECESSOR_CLOSURE_INCOMPLETE",
"details": { "predecessor_id": "162-S", "closure_complete": null }
```

`162-S` is an **explicit** `blocks` predecessor of `163-S`. Because
`_prior_shipment_id()` only appends a synthetic predecessor when it is *not
already present* (`if prior_id and prior_id not in predecessor_ids`), and the
numerically adjacent shipment here **is** `162-S`, the numeric heuristic is a
**no-op** for `163-S`.

**Consequence: removing the numeric fallback would NOT unblock `163-S`.** Any
plan premised on that causal claim would have shipped a change that failed to
resolve the motivating symptom.

### Finding 2 — the actual cause of the `163-S` block

`163-S` is blocked by `PREDECESSOR_CLOSURE_INCOMPLETE`, not
`PREDECESSOR_NOT_SHIPPED`. `FilesystemTopologyReaders.closure_complete("162-S")`
returns `None` because `docs/closure/` contains no `162-S-*-post-merge-closure.md`
artifact (only `160-S-152-F-*` and `161-S-153-F-*` exist). `162-S` is shipped and
archived (`.backlogit/archive/162-S.md`) but its closure evidence artifact is
absent.

This is a **closure-evidence** defect, orthogonal to predecessor derivation.

### Finding 3 — the real advisory contradiction, precisely located

`dag-readiness` places `163-S` in `ready_set`; `pre_claim` blocks it. Both gates
**agree** on the edge `163-S → 162-S`. They diverge because `pre_claim` applies a
**third requirement that `dag-readiness` does not model at all**: closure
evidence. `_dag_all_predecessors_finished` tests only shipped-terminal status.

So the advisory mismatch is *not* primarily caused by numeric adjacency (as the
bug doc assumed from the 148-S/149-S fixture); in this workspace it is caused by
the unmodelled closure-evidence dimension. Aligning the advisory output requires
modelling closure evidence, not merely deleting the heuristic.

### Finding 4 — prior learnings strongly favour retirement (confidence: high)

Retrieved from `docs/compound/`:

* `2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md`
* `2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md`

Together these record **three successive correctness defects in the same
heuristic**: PR #357 introduced a multi-hop reverse-dependency false PASS; the
fix for it introduced an opposite-direction false NEGATIVE (fallback wrongly
suppressed by normal forward dependents); the corrected predicate required a
third iteration restricting suppression to numerically *lower* declarants. The
second learning is still marked **"unfixed on `main`"** with a verified,
uncommitted fix handed off to Stage.

This is direct evidence that the heuristic's interaction surface is inherently
fragile: its correctness depends on reasoning about numeric direction that
carries no real semantic meaning. It is the strongest argument for retirement.

### Finding 5 — current suppression logic is itself a silent fail-open

`_prior_shipment_id` returns `None` (disabling the fallback entirely for the
whole target) whenever any numerically lower shipment declares the target as its
dependency. That means the "safety" heuristic is already silently absent for an
arbitrary subset of shipments — its protection is not uniform, so the claim that
it provides dependable fail-closed safety is weaker than assumed.

## Options Evaluated

### Option A: Presentation-only fix (the superseded bug-doc recommendation)

Label `dag-readiness` advisory, surface `pre_claim` outcome, disambiguate
`next_eligible`. Leave numeric derivation intact.

### Option B: Hard removal of the numeric fallback

Delete `_prior_shipment_id` and derive predecessors exclusively from
`blocking_predecessor_ids`. Delete `ImplicitNumericPredecessorTests`.

### Option C: DAG-authoritative with explicit, fail-closed migration state (RECOMMENDED)

Make explicit `blocks` edges the sole predecessor authority. Retire numeric
adjacency as a *claim-blocking* input. Add deterministic provenance to gate
output (`predecessor_source: explicit | none`). For the case the heuristic was
protecting — a shipment with **no** explicit predecessor in a workspace that
previously relied on unstated numeric sequencing — emit a distinct, auditable
`UNSEQUENCED_SHIPMENT` migration signal governed by an explicit, declarative
workspace setting rather than a silent ID-derived guess. Align `dag-readiness`
to model the same authoritative inputs, including closure evidence.

## Trade-off Comparison

| Criterion | A: Presentation-only | B: Hard removal | C: DAG-authoritative + migration |
|---|---|---|---|
| Satisfies operator direction | No — leaves numeric authoritative | Yes | Yes |
| Fixes `163-S` symptom | No | No | No (separate closure-evidence defect; tracked in-scope) |
| Eliminates fragile heuristic | No — 4th defect likely | Yes | Yes |
| Backward-compat safety | High (no change) | **Low — silently converts prior blocks into passes** | High — fail-closed, explicit, auditable |
| Blast radius | Low | High + unsignalled | Medium, signalled |
| Auditability of sequencing | Poor | Good | Best (explicit provenance field) |
| Migration path for other workspaces | N/A | None | Declarative + documented |
| Alignment with dependency protocol | Contradicts it | Aligns | Aligns |

## Decision

**Adopt Option C — DAG-authoritative predecessor derivation with an explicit,
fail-closed migration posture.**

Rationale:

1. **Operator product direction is explicit** and supersedes the bug doc's
   presentation-only recommendation. The explicit dependency protocol is the
   intended sequencing source; a gate that overrides it with an ID-numbering
   coincidence contradicts the documented contract.
2. **Empirical fragility** (Finding 4): three defects in one heuristic, one still
   unfixed on `main`. Continued patching has negative expected value.
3. **Option B is rejected for safety**, not for direction. Hard removal silently
   converts previously-blocked claims into passes in workspaces that depended on
   unstated numeric sequencing. That is precisely the class of silent fail-open
   this repository's fail-closed principles forbid. Option C preserves the
   *safety intent* of the heuristic while removing its *guessing mechanism*, by
   converting an implicit inference into an explicit, auditable signal.
4. **Provenance is the durable fix** for the advisory-semantics complaint: once
   gate output states *where* a predecessor came from, advisory and authoritative
   outputs can be reconciled and can no longer silently disagree.

### Scope boundary decisions

* **`pipeline-topology pre_claim` remains the SOLE claim authority.**
  `dag-readiness` stays advisory and non-authorizing; it is aligned to the same
  model so operators are not shown contradictory readiness, but it never
  authorizes a claim.
* **The `163-S` closure-evidence defect (Findings 2–3) is IN SCOPE** for this
  covering feature, because aligning advisory with authoritative output is
  impossible without modelling closure evidence. It is, however, a **distinct
  task** from predecessor derivation and is not conflated with it.
* **`86498B64` (workspace-driven `implementation_branch`) stays SEPARATE.**
  It touches the same file (`topology.py`) but a genuinely different contract:
  *branch naming* authority, not *sequencing* authority. Same-file adjacency is
  not same-contract necessity. It is the recommended next unit of work.
* **`9B582824` (cost-per-unit-of-work epic) stays SEPARATE** — broad
  multi-component epic, no contract overlap.
* **`97B28746` / `50434138` (verify-workspace / Ship branch drift) stay SEPARATE**
  as related follow-ups.
* **`58A85283` (file-lock test follow-up) excluded** — unrelated.

## Rejected Alternatives

* **Option A (presentation-only)** — rejected: does not satisfy operator
  direction and leaves the defect-generating heuristic authoritative.
* **Option B (hard removal)** — rejected: correct direction, unsafe execution;
  silent backward-compatibility fail-open.
* **Bundling `86498B64` into this feature** — rejected: distinct contract
  surface; bundling would inflate blast radius and violate width isolation.
* **Treating this as a trivial bug fix** — rejected: it is a contract change to
  the sole claim authority, with documented intentional prior behaviour and
  cross-workspace migration impact.

## Unresolved Questions

1. **Migration default**: should `UNSEQUENCED_SHIPMENT` default to *block*
   (maximally fail-closed, but immediately blocks every DAG root in every
   existing workspace) or to *warn-and-pass with provenance* (smoother, relies
   on advisory honesty)? Recommendation carried into planning: default to
   **warn-and-pass with explicit provenance**, because after this change a DAG
   root with no explicit predecessor is a *legitimate* state, not an anomaly —
   with an opt-in strict mode for workspaces wanting the old blocking posture.
2. **Missing closure artifact for `162-S`**: is the correct remedy to author the
   missing closure artifact, or to treat archived-without-closure-artifact as
   satisfied? Requires evidence review during planning; must not be resolved by
   weakening the closure gate.
3. Whether the still-unfixed `_prior_shipment_id` forward-dependent defect should
   be fixed en route or is rendered moot by retirement. Planning should confirm
   moot-ness rather than assume it.

## Risks and Mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Silent fail-open in workspaces relying on numeric sequencing | High | Explicit `UNSEQUENCED_SHIPMENT` provenance signal; documented migration; strict opt-in mode |
| Plan built on the incorrect `163-S` causal premise | High | Finding 1 recorded; closure-evidence work tracked as a separate task |
| `ImplicitNumericPredecessorTests` deletion loses encoded safety knowledge | Medium | Migrate each case to an equivalent explicit-DAG or migration-state assertion; do not simply delete |
| Advisory/authoritative divergence reappears on a new dimension | Medium | Shared derivation helper consumed by both gates, not parallel implementations |
| Scope creep into `86498B64` branch resolution | Medium | Explicit scope boundary above; separate shipment |

## Quality Criteria

* Test-first: every behaviour change lands with a RED test first.
* Regression coverage for: independent numerically adjacent DAG roots; explicit
  dependency chains; closure evidence demanded only for actual explicit
  predecessors; converging DAGs; missing/invalid dependency data; migration
  and backward-compatibility behaviour.
* `pre_claim` remains sole claim authority in both code and documentation.
* Engine, CLI output, templates/policies, installed dogfood instructions, and
  documentation move together.
* Orchestrator/Ship shipment-sequencing text matches the new gate contract.

## Model Routing

Stage route: `claude-opus-5` / `anthropic` / `high` (propagated to inherited
skills). Non-dark run.
