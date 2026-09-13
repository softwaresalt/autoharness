---
title: "DAG-authoritative predecessor derivation for pipeline-topology pre_claim — decided plan"
description: "Test-first implementation plan retiring the implicit numeric-adjacency predecessor heuristic in `pipeline-topology --phase pre_claim` in favour of explicit backlogit `blocks` DAG edges under a four-state declared-root contract, adding deterministic predecessor provenance and a read-only sequencing audit phase, aligning `dag-readiness` advisory output across every derivation state, and coupling agent templates, installed dogfood copies, and documentation."
doc_type: plan
source: docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md
date: 2026-09-12
status: decided
revision: 2
revision_note: "Review-fix cycle 1 — migration contract redesigned, config key removed, test ordering made green-per-task, advisory parity made total, closure defect descoped, source provenance made self-contained."
decision_source: docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md
stash_ids:
  - AF2890B7
deferred_scope_expansions:
  - FD0CCB42
---

# Decided Plan — DAG-Authoritative Predecessor Derivation

## 1. Source Understanding

Implements Option D of
`docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md`:
explicit backlogit `blocks` edges become the sole predecessor authority for
`pipeline-topology --phase pre_claim`; the implicit numeric-adjacency heuristic is
retired from the claim path; edge-less shipments resolve through an explicit
four-state contract (explicit / declared root / genesis / unsequenced); gate output
gains deterministic provenance; a read-only audit phase migrates previously
implicit sequencing; and `dag-readiness` is aligned to the same model across every
state.

### Provenance of this plan

This plan is **self-contained**. Every claim below is derived from committed
sources in this repository — production code, committed tests, committed
`docs/compound/` learnings, committed `docs/closure/` artifacts, committed backlog
records — plus explicit operator direction dated 2026-09-12. An earlier
operator-owned working document recommended a presentation-only remedy and
classified numeric-fallback removal as a future option; operator direction
supersedes that recommendation. That document is not part of the committed record
and is deliberately **not referenced**, so nothing here depends on an unresolvable
link. Its substance is preserved as prose in the decision's *Historical context*
section.

### Carried-forward critical correction

Reproduced in-workspace (decision Finding 1): `163-S` declares
`dependencies: [162-S]` **explicitly**. The numeric heuristic is a **no-op** for
`163-S`, and its block token is `PREDECESSOR_CLOSURE_INCOMPLETE`
(`closure_complete: null`), not `PREDECESSOR_NOT_SHIPPED`.

**Retiring the numeric fallback will not, by itself, unblock `163-S`.** That
symptom is a closure-evidence producer/consumer naming defect, **descoped** from
this feature and captured as deferred scope expansion `FD0CCB42` (decision D4). No
task in this plan may claim to fix `163-S`.

## 2. Codebase Research

| Surface | Location | Change |
|---|---|---|
| Numeric heuristic | `src/autoharness/gates/topology.py::_prior_shipment_id` (L1433–1469) | Removed from the claim path; retained solely as audit-report input |
| Predecessor union | `topology.py::_shipment_readiness_check` (L1574–1578) | Derive from explicit edges only; add four-state resolution and provenance |
| Block tokens | `topology.py` L1585–1628 | Add `predecessor_source` to all payloads; add `UNSEQUENCED_SHIPMENT` |
| Phase registry | `topology.py` L31–32 (`VALID_PHASES`, `SCOPED_PHASES`) | Add `audit_sequencing` to `VALID_PHASES` only — it is workspace-wide, not target-scoped, and carries no phase status requirement |
| Shipment reader | `topology.py::ShipmentState` (L91–98) and its frontmatter parser (L560–600) | Add a root-declaration field parsed from the record's `labels` |
| Advisory readiness | `topology.py::_dag_all_predecessors_finished` (L1873), `compute_dag_readiness` (L1968) | Consume the shared derivation/closure helper; advisory labelling |
| Next-eligible | `topology.py::compute_next_eligible` (L2075) | Exclude policy-blocked shipments; non-authorizing disambiguation |
| Closure evidence | `topology.py::FilesystemTopologyReaders.closure_complete` (L654) | **Read-only reuse** through the shared helper — behaviour unchanged (see fence below) |
| Engine tests | `tests/test_gates_topology.py::ImplicitNumericPredecessorTests` (L1648–~1750, 5 cases) | Re-expressed atomically with the production change |
| CLI tests | `tests/test_gate_pipeline_topology_cli.py` | Provenance and remediation text in output |
| Agent templates | `templates/agents/_orchestrator.agent.md.tmpl`, `templates/agents/_ship.agent.md.tmpl` | Sequencing contract text |
| Installed dogfood | `.github/agents/_orchestrator.agent.md`, `.github/agents/_ship.agent.md` | Mirror the template changes |

### Surfaces deliberately NOT touched

* **No `.autoharness/config.yaml` key** (decision D2). Consequently: no root schema
  change, no new versioned schema mirror, no `schema_contracts.py` work, no
  `templates/harness-config.yaml.tmpl` change, no install/tune preservation logic,
  no dogfood config change, no config parity tests. The contract is carried by
  backlog record data that already exists.
* **`templates/policies/workflow-policies.md.tmpl`** — verified by grep to contain
  no `pre_claim` and no `PREDECESSOR_` token. Not an edit surface.
* **`.github/instructions/workflows.instructions.md`** — verified by grep to
  contain no `pre_claim`, `PREDECESSOR_`, or `dag-readiness` token. The first-round
  plan listed it in error; that mapping is **removed**, and no task may edit it.
* **`closure_complete()` semantics** — the closure gate is not weakened, relaxed,
  or bypassed anywhere in this plan; the naming defect is `FD0CCB42`'s to resolve.
* **backlogit** — dependency and label data already support the contract; no
  backlogit change is required (validated: `backlogit update 173-S --labels
  "dag-root,topology-gate"` persists `labels:` on a shipment record).

### Prior learnings applied (from `docs/compound/`)

| Learning | Applied as |
|---|---|
| `2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md` and `2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md` | Three defect cycles all rooted in **directional numeric reasoning**. The replacement contract therefore contains **no** numeric comparison on the claim path in any state, and the audit path is forbidden from inheriting the suppression predicate (T3). |
| `2026-05-07-backlogit-shipment-status-constraints.md` | Sequencing intent must be recorded explicitly in backlog data (`queued` status plus real `blocks` edges), not inferred. The audit (T3) migrates workspaces onto explicit edges rather than leaving intent implicit. |
| `2026-09-06-composed-workflow-protocol-state-machine-validation.md` | A producer/consumer pair must be tested as a **composed** state machine — each half can pass its own unit tests while the composition is broken. Applied to advisory/authoritative parity (T4/T5) as a full state matrix, and cited into `FD0CCB42` for the closure naming defect, which is exactly this failure shape. |
| `2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md` | Never mutate a versioned schema mirror in place. Honoured by needing **no** schema version at all (D2). |
| `2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md` | Gate phases carry status preconditions and ordering meaning. The new `audit_sequencing` phase is registered as workspace-wide with **no** status requirement, so it cannot disturb `lifecycle`'s active-target invariant. |
| `2026-08-09-next-eligible-detail-scoping-and-vacuous-tiebreak-tests.md` | Ordering/tie-break tests pass vacuously when the fixture cannot distinguish outcomes. T1/T4 fixtures must make each asserted state reachable and distinguishable; parity is a total matrix, not a sample. |

## 3. Contract Definition

### 3.1 Predecessor derivation (authoritative, `pre_claim`)

```text
predecessor_ids := ShipmentState.blocking_predecessor_ids   # explicit `blocks` only
```

`_prior_shipment_id` is **never** consulted for claim blocking. When
`predecessor_ids` is empty, exactly one of three states applies:

| State | Condition | Outcome | `predecessor_source` |
|---|---|---|---|
| Explicit | edges present | existing ambiguity / shipped-terminal / closure checks per predecessor | `explicit` |
| Declared root | no edges, record declares `dag-root` | pass | `declared_root` |
| Genesis | no edges, no declaration, workspace has no shipped-terminal shipment | pass | `genesis` |
| Unsequenced | no edges, no declaration, workspace has shipping history | **block** `UNSEQUENCED_SHIPMENT` | `unsequenced` |

The four states are total and mutually exclusive. `predecessor_source` is present
on **every** `shipment_readiness` payload — blocked and passed alike.

The `UNSEQUENCED_SHIPMENT` message must name the two remedies explicitly (record
the real `blocks` edge, or declare the shipment a root), so the block is never a
dead end.

### 3.2 Root declaration

The declaration is the label `dag-root` on the shipment's own backlogit record,
read from existing frontmatter. Declaring a root is an operator/Stage act; Ship
must not self-declare a root to unblock its own claim. Every declared-root pass is
auditable because provenance names it.

### 3.3 Sequencing audit (read-only migration path)

`--phase audit_sequencing` is non-authorizing, never blocks, and never mutates.
For every edge-less shipment it reports the derived state, the raw
numerically-adjacent candidate the retired heuristic would have inferred, and the
remediation choice. It must **not** apply the reverse-dependency suppression
predicate.

### 3.4 Advisory alignment (`dag-readiness`)

`dag-readiness` remains advisory and non-authorizing. It must model **all four**
states plus closure evidence through the **same shared helper** `pre_claim` uses;
must never place a `unsequenced`-blocked shipment in `ready_set`/`next_eligible`;
must never report a `declared_root` blocked; must label output non-authorizing; and
must disambiguate `next_eligible` so it cannot read as authorization.

`pipeline-topology --phase pre_claim` remains the **sole claim authority**.

## 4. Test-First Task Breakdown

All tasks are sized at or under 2 hours human-equivalent. Width isolation is
observed: engine, CLI, template sources, installed mirrors, and docs are separate
tasks.

**Every task ends green.** New expectations land as strict expected-failure tests
in the harness task and are flipped to ordinary passing tests by the implementation
task that delivers the behaviour; tests that pin behaviour being removed are
re-expressed in the **same** task that removes the behaviour. No task may leave the
suite red for a successor to repair.

**Characterization vs. RED.** Behaviour that already exists is covered by
*characterization* tests that pass immediately (they lock in current behaviour so
the refactor cannot silently change it). Only genuinely new behaviour is written
as a failing expectation. Demanding a RED observation for existing behaviour would
be impossible to satisfy honestly, so it is not required anywhere below.

| # | Task | ID | Kind | Size | Complexity | Depends on |
|---|---|---|---|---|---|---|
| T1 | Derivation test harness: characterization + expected-failure matrix | 165.001-T | test | M | medium | — |
| T2 | Engine: four-state derivation, provenance, legacy-test re-expression | 165.002-T | impl | M | high | T1 |
| T3 | Sequencing audit phase + tests | 165.003-T | impl | M | medium | T2 |
| T4 | Advisory parity test matrix (characterization + expected-failure) | 165.004-T | test | S | medium | T2 |
| T5 | Engine: `dag-readiness` parity via shared helper | 165.005-T | impl | M | high | T4 |
| T6 | CLI: provenance and remediation output + tests | 165.006-T | impl | S | low | T2 |
| T7 | Agent template sources | 165.008-T | docs | S | medium | T5, T6 |
| T8 | Installed dogfood mirrors + parity check | 165.010-T | docs | S | medium | T7 |
| T9 | Gate documentation + audit/migration guide | 165.009-T | docs | S | low | T5, T6 |

### T1 — Derivation test harness (165.001-T)

**Characterization (passes on current `main`, must keep passing):**

1. Explicit linear chain blocks correctly on an unshipped explicit predecessor.
2. Closure evidence is demanded for an actual explicit predecessor.
3. Converging DAG — two explicit predecessors on one successor; every explicit
   predecessor is evaluated, none skipped.
4. Malformed/unresolvable dependency IDs fail closed and are never silently
   dropped.

**New expectations (strict expected-failure; flipped by T2):**

1. Two numerically adjacent edge-less roots are **not** blocked by numeric
   inference.
2. Closure evidence is **never** demanded for a merely numerically-adjacent
   non-predecessor.
3. `predecessor_source` is present and correct on a **passing** payload and on a
   **blocked** payload.
4. Declared root passes with `predecessor_source: declared_root`.
5. Genesis workspace (no shipped-terminal shipment) passes with
   `predecessor_source: genesis`.
6. Unsequenced shipment in a workspace with shipping history blocks with
   `UNSEQUENCED_SHIPMENT`, and the message names both remedies.

Fixtures must make each state distinguishable — a fixture in which two states
would produce the same observation cannot assert either (vacuous-test learning).

### T2 — Engine change (165.002-T)

Implement §3.1: derive from `blocking_predecessor_ids` only; parse the root
declaration into `ShipmentState`; implement the four-state resolution; attach
`predecessor_source` to every payload; add `UNSEQUENCED_SHIPMENT` with
remedy-naming text; remove `_prior_shipment_id` from the claim path (do not delete
the function — T3 re-homes it as audit input, so deleting it would create a
dangling reference).

**Atomic legacy-test re-expression (same task, same commit).** The five
`ImplicitNumericPredecessorTests` cases pin claim-path numeric behaviour that this
task removes; they cannot be handled in a later task without leaving the suite red
in between. In this task each case is re-expressed with a recorded per-case
disposition: cases whose intent survives become explicit-DAG or four-state
assertions; cases that only ever described the heuristic's internal
reverse-dependency suppression become direct unit tests of `_prior_shipment_id` as
a pure function (preserving the encoded knowledge for the audit path without
asserting any claim behaviour). Bulk deletion is forbidden; any case genuinely
without an equivalent requires written rationale. Update the class docstring to
record the heuristic as retired history.

Flip T1's expected-failure markers to ordinary assertions. Prove by test — not by
assertion — that the still-unfixed forward-dependent suppression defect can no
longer affect a claim; if any claim-path residue remains, record a follow-up rather
than silently fixing it.

### T3 — Sequencing audit phase (165.003-T)

Implement §3.3. Register `audit_sequencing` in `VALID_PHASES` only, **not** in
`SCOPED_PHASES`, and give it no phase status requirement, so it cannot disturb the
`lifecycle` phase's active-target invariant. Report per edge-less shipment: derived
state, raw numeric-adjacency candidate, and remediation choice. Tests must assert
the audit reports a candidate in the exact configuration where the suppression
predicate would have hidden it, and that the audit never blocks or authorizes.

### T4 — Advisory parity matrix (165.004-T)

Characterization for existing agreement; expected-failure for the new parity
requirements. The matrix is **total**: for each of the four derivation states
crossed with the closure-evidence dimension, assert that advisory output and
`pre_claim` cannot contradict each other. Specifically: a `unsequenced`-blocked
shipment must never be `next_eligible` or in `ready_set`; a `declared_root` must
never be advisory-blocked; a shipment whose explicit predecessor is shipped-terminal
but lacks recognized closure evidence must not read as ready while `pre_claim`
blocks it; advisory output is labelled non-authorizing; and `dag-readiness` never
authorizes under any configuration.

### T5 — Advisory engine alignment (165.005-T)

Turn T4 green. The closure-evidence and derivation logic **must** be a single
shared helper consumed by both gates, reusing `closure_complete` read-only — a
parallel reimplementation is a review-blocking defect, because independent logic is
the architectural root cause of the original divergence. State in the task record
whether the helper lives in `topology.py` or a new module. Exclude policy-blocked
shipments from `next_eligible`. `pre_claim` remains sole claim authority.

### T6 — CLI output (165.006-T)

Surface `predecessor_source` and the selected predecessor IDs in JSON and human
output on blocked and passed paths; render the `UNSEQUENCED_SHIPMENT` remedy text;
render audit-phase output readably. Changes are **additive** — no existing field is
renamed or removed. Assert in `tests/test_gate_pipeline_topology_cli.py`.

### T7 / T8 — Agent contract text (165.008-T, 165.010-T)

Both tasks are **mandatory members of `173-S`**; neither may be deferred outside
the shipment. They are split only to keep each under the 2-hour ceiling, and T8
depends on T7 so the mirror is written from the finished source.

* **T7 — template sources**: `templates/agents/_orchestrator.agent.md.tmpl`
  (L312, L314, L339, L341) and `templates/agents/_ship.agent.md.tmpl` (L172–175,
  L200–201, L224–225, L235). Content: predecessors derive from explicit `blocks`
  edges; the four states and their provenance values; `pre_claim` is the sole claim
  authority and `dag-readiness` is advisory/non-authorizing; **Ship must not
  self-declare `dag-root`**; the audit phase exists as the migration path.
* **T8 — installed dogfood mirrors**: `.github/agents/_orchestrator.agent.md` and
  `.github/agents/_ship.agent.md`, plus an explicit source-versus-mirror parity
  check recorded in the task. No other installed instruction file is in scope.

Both tasks: introduce no unresolved template placeholder tokens, and keep
markdownlint heading hierarchy clean (P-008).

### T9 — Documentation and migration guide (165.009-T)

Document the contract, the four provenance values, the `UNSEQUENCED_SHIPMENT`
signal and its two remedies, the root-declaration surface and who may use it, and
the `audit_sequencing` migration procedure end to end. Explain why numeric
adjacency was retired, citing the three recorded defect cycles. Record the rollback
posture. Cross-reference the decision and this plan only — no reference to
uncommitted documents.

## 5. Risks

| Risk | Mitigation |
|---|---|
| Silent fail-open for prior numeric-reliant workspaces | Unsequenced state blocks in any workspace with shipping history (§3.1); audit phase migrates intent (T3) |
| Blocking posture deadlocks legitimate roots | Declared-root state plus genesis bootstrap; block message names both remedies |
| Ship self-declares a root to unblock itself | Declaration authority is operator/Stage; provenance makes it auditable; T7/T8 state the prohibition in agent contracts |
| A task leaves the suite red | Expected-failure harness flipped by its implementer; legacy-test re-expression atomic with removal (T2) |
| Advisory/authoritative divergence recurs | Shared helper (T5) plus total parity matrix (T4) |
| Audit inherits the suppression defect | T3 reports raw candidates, asserted by test |
| Template/installed-copy drift | T8 depends on T7 and records an explicit parity check; both stay in `173-S` |
| Scope creep into closure evidence | Descoped to `FD0CCB42`; no task in this plan touches closure semantics |

## 6. Quality Criteria

* Genuinely new behaviour lands as a failing expectation before implementation;
  existing behaviour is characterized, not faked as RED.
* Every task ends with a green suite.
* `pre_claim` remains sole claim authority in code, output, templates, and docs.
* No unresolved template placeholder tokens in touched templates; markdownlint
  clean (P-008).
* Gate output provenance is deterministic, total, and auditable.
* Engine, CLI, template sources, installed mirrors, and docs ship together in
  `173-S`.

## 7. Hardening Assessment

Blast radius is elevated: this changes the **sole claim authority** for every
shipment in every autoharness-managed workspace and alters CLI output contracts.
Cross-workspace migration impact remains, though it is now bounded by an explicit
audit rather than a silent default, and the config/schema surface has been removed
entirely.

**Requires plan hardening: yes**

## Plan Hardening

Performed 2026-09-12 (Stage, `claude-opus-5`/`anthropic`/`high`) per P-006, because
§7 concluded `Requires plan hardening: yes`. Re-performed in review-fix cycle 1
against the redesigned contract.

### H1 — Reinforcing context pulled

* Compound learnings as tabulated in §2, each mapped to a concrete plan constraint
  rather than cited decoratively.
* Template sequencing surfaces confirmed by grep:
  `templates/agents/_orchestrator.agent.md.tmpl` (L312, L314, L339, L341),
  `templates/agents/_ship.agent.md.tmpl` (L172–175, L200–201, L224–225, L235), and
  the installed copies `.github/agents/_orchestrator.agent.md` and
  `.github/agents/_ship.agent.md`.
* **Negative findings, verified by grep and honoured as scope fences:**
  `templates/policies/workflow-policies.md.tmpl` contains no `pre_claim` or
  `PREDECESSOR_` token, and `.github/instructions/workflows.instructions.md`
  contains no `pre_claim`, `PREDECESSOR_`, or `dag-readiness` token. Neither is an
  edit surface; the first-round mapping of the latter was wrong and is removed.
* Root-declaration feasibility validated empirically (labels persist on a shipment
  record) before the contract depended on it.

### H2 — Hardened failure modes

| ID | Failure mode | Hardening |
|---|---|---|
| F1 | Provenance lands only on the blocked path, leaving passes unattributable | `predecessor_source` is REQUIRED on blocked **and** passed payloads; T1 asserts it on a passing case |
| F2 | A migration posture blocks every DAG root with no way out | Four-state contract: declared roots and genesis pass; the unsequenced block names two concrete remedies; T1 asserts each state independently |
| F3 | Advisory alignment reimplements closure/derivation logic and re-diverges | T5 MUST consume one shared helper; a parallel implementation is a review-blocking defect |
| F4 | Legacy safety cases deleted in bulk under cover of "migration" | T2 requires a per-case disposition for all five cases with written rationale for any non-migratable case |
| F5 | A task ends red because test disposition trails the behaviour change | Expected-failure flip and legacy re-expression both occur inside the task that changes behaviour |
| F6 | Retirement silently inherits the unfixed forward-dependent defect | T2 must **prove** claim-path moot-ness by test; T3 forbids the audit from inheriting the suppression predicate |
| F7 | A new config surface is added without schema versioning discipline | No config key is added at all (D2); the schema surface does not exist to mutate |
| F8 | Installed dogfood copies drift from template sources | T8 depends on T7, records an explicit parity check, and remains inside `173-S` |
| F9 | Closure-gate weakening sneaks in as a way to unblock `163-S` | No task touches closure semantics; the defect is descoped to `FD0CCB42` with an explicit no-weakening, no-competing-artifact constraint |
| F10 | Parity tests pass vacuously | T4 is a total state matrix with distinguishable fixtures per the vacuous-tiebreak learning |

### H3 — Explicit non-goals (scope fences)

* Does **not** change branch-naming authority (`86498B64`, separate and next).
* Does **not** alter `--force` override semantics; `--force` remains
  human-authorized, shipment-specific, and audited — never agent-issued.
* Does **not** make `dag-readiness` authorizing under any configuration.
* Does **not** modify backlogit.
* Does **not** touch closure-evidence semantics (`FD0CCB42`).
* Does **not** add configuration or schema surfaces.

### H4 — Rollback posture

The contract is data-driven: labelling shipments `dag-root` or adding real `blocks`
edges are reversible backlog operations requiring no code change. Provenance fields
are additive to output and safe for older consumers to ignore. A full revert of the
engine change restores prior behaviour without leaving orphaned configuration,
because no configuration was introduced.

### H5 — Residual risk accepted

In a workspace with shipping history and no explicit `blocks` edges anywhere, every
shipment blocks as `unsequenced` until audited. This is the intended fail-closed
posture: it converts an unstated assumption into a one-time, bounded, self-service
action with tooling (T3) and documentation (T9) to support it. The alternative —
passing by default — is the silent fail-open this design exists to prevent.

### H6 — Bootstrap disposition carried into execution (decision D6)

`173-S` is blocked by the very defect it fixes: under current code its absent edges
cause `172-S` to be synthesised as a predecessor. Operator authorization dated
2026-09-12 permits a single **audited `pre_claim --force` for `173-S` only**. That
authorization confers no broader force authority, is single-use, does not change
`--force` semantics, must be recorded by Ship in the claim and PR/closure evidence
citing decision D6, and becomes unnecessary once T2 lands — `173-S` already carries
`labels: [dag-root]`, so it will then pass natively as `declared_root`.

**Hardening complete. Plan is ready for `plan-review`.**

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

Review-fix cycle 1 re-review recorded in full at
`docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md`
(cycle 2): **0 P0, 0 P1, 5 P2, 3 P3**. Of the P2 findings, three were resolved
in-cycle by amending task records (P2-1 archived-history genesis probe, P2-2
fail-closed `labels` parsing, P2-3 single genesis snapshot in the shared helper),
one is accepted with recorded handling (P2-4 `dag-root` has no mechanical
enforcement), and one is externalized to stash `9AA34143` (P2-5 shipment rollup
member set). The three P3 findings are advisory. Review cycles used: 2 of 3.

Plan hardening was required and is present, re-performed against the redesigned
contract. All eleven operator findings from the cycle-1 BLOCK are verified
resolved in the review's "Operator Findings Verification" table. The plan is
harvest-ready.
