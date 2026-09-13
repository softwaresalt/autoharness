---
title: "DAG-authoritative predecessor derivation for pipeline-topology pre_claim — decided plan"
description: "Test-first implementation plan retiring the implicit numeric-adjacency predecessor heuristic in `pipeline-topology --phase pre_claim` in favour of explicit backlogit `blocks` DAG edges under a four-state declared-root contract, adding deterministic predecessor provenance and a read-only sequencing audit phase, aligning `dag-readiness` advisory output across every derivation state, and coupling agent templates, installed dogfood copies, and documentation."
doc_type: plan
source: docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md
date: 2026-09-12
status: decided
revision: 4
revision_note: "Review-fix cycle 3 (authorized final narrow correction) — N7a reclassified as a passing characterization with constrained expected-failure reasons, the audit re-posed as a pure read-only report with the durable-ledger subsystem removed (version-controlled migration commits/diffs are the external record), closure-evidence parity removed entirely from T4/T5 and every acceptance criterion in favour of FD0CCB42's exclusive ownership, bootstrap re-scoped to exactly three audited forced invocations (Orchestrator U0 plus Ship U1/U2), `dag-root` authority narrowed to a version-controlled review-gated declaration that is not a security boundary, `ShipmentState` given a validated immutable labels tuple, the intake bug report made self-contained, and the 173-S closure posture recorded as verified per-item SAFE_CLOSE."
decision_source: docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md
source_bug_report: docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md
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

Every claim below is derived from committed sources in this repository —
production code, committed tests, committed `docs/compound/` learnings, committed
`docs/closure/` artifacts, committed backlog records — plus explicit operator
direction dated 2026-09-12.

**Source integrity corrected (review-fix cycles 2–3).** The original intake
document, `docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md`,
recommended a presentation-only remedy and classified numeric-fallback removal as
a future option; operator direction supersedes that recommendation. Cycle 1
handled the fact that the file was untracked by deleting every reference to it —
but the archived stash record `AF2890B7` and the cycle-1 session memory still
named the path, so the durable record referenced a file no reader could resolve.
Cycle 2 committed the document so those references resolve. **Cycle 3 makes the
committed copy self-contained**: its frontmatter now declares its own local path
and `doc_type: bug`, and its transfer note now states its external provenance
explicitly (`softwaresalt/backlogit#438`, with the source commit and source path
named as *source-workspace* references that do **not** resolve here) instead of
describing itself as living under a `docs/scratch/` path it no longer occupies.
The **analysis body is unchanged** and its historical meaning is preserved; only
the self-locating metadata and the provenance framing were corrected. It remains
a **historical record, not a design input**: nothing in this plan depends on it,
and where it conflicts with the decision, the decision governs. Its substance is
also preserved as prose in the decision's *Historical context* section.

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
| Shipment reader | `topology.py::ShipmentState` (L91–98) and its frontmatter parser (L560–600) | Add a validated, immutable `labels` tuple parsed from the record's `labels` via a **new labels-specific** fail-closed validator (not `_tuple_of_str`); root classification is **derived** from that tuple |
| Advisory readiness | `topology.py::_dag_all_predecessors_finished` (L1873), `compute_dag_readiness` (L1968) | Consume the shared **derivation** helper; advisory labelling |
| Next-eligible | `topology.py::compute_next_eligible` (L2075) | Exclude policy-blocked shipments; non-authorizing disambiguation |
| Engine tests | `tests/test_gates_topology.py::ImplicitNumericPredecessorTests` (L1648–~1750, 5 cases) | Re-expressed atomically with the production change |
| CLI tests | `tests/test_gate_pipeline_topology_cli.py` | Provenance and remediation text in output |
| Agent templates | `templates/agents/_orchestrator.agent.md.tmpl`, `templates/agents/_ship.agent.md.tmpl` | Sequencing contract text (same commit as the mirrors below) |
| Installed dogfood | `.github/agents/_orchestrator.agent.md`, `.github/agents/_ship.agent.md` | Mirror the template changes **atomically, in the same commit** |

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
* **`closure_complete()` and closure-evidence semantics** — **entirely out of scope
  (cycle 3, strengthened)**. No task in this plan reads, evaluates, reuses,
  discovers, or asserts parity over closure evidence, and no acceptance criterion
  in `173-S` references it. The shared helper of §3.4 covers **derivation only**.
  `FD0CCB42` is the **exclusive** owner of closure-evidence producer/consumer
  naming and of any test that composes the two halves. Cycle 2 still routed a
  read-only `closure_complete` reuse through T5 and a closure-variant dimension
  through T4; both are removed, because a descoped surface that is still evaluated
  by this shipment's tests is not descoped.
* **backlogit** — dependency and label data already support the contract; no
  backlogit change is required (validated: `backlogit update 173-S --labels
  "dag-root,topology-gate"` persists `labels:` on a shipment record).

### Prior learnings applied (from `docs/compound/`)

| Learning | Applied as |
|---|---|
| `2026-08-18-topology-gate-multi-hop-reverse-dependency-fallback.md` and `2026-08-18-topology-gate-forward-dependent-suppression-residual-defect.md` | Three defect cycles all rooted in **directional numeric reasoning**. The replacement contract therefore contains **no** numeric comparison on the claim path in any state, and the audit path is forbidden from inheriting the suppression predicate (T3). |
| `2026-05-07-backlogit-shipment-status-constraints.md` | Sequencing intent must be recorded explicitly in backlog data (`queued` status plus real `blocks` edges), not inferred. The audit (T3) migrates workspaces onto explicit edges rather than leaving intent implicit. |
| `2026-09-06-composed-workflow-protocol-state-machine-validation.md` | A producer/consumer pair must be tested as a **composed** state machine — each half can pass its own unit tests while the composition is broken. Applied to advisory/authoritative parity (T4/T5) as a full matrix over the **four derivation states**, and cited into `FD0CCB42`, which **exclusively** owns the closure producer/consumer naming defect and its composed test. |
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
| Explicit | edges present | existing per-predecessor ambiguity / shipped-terminal / closure checks run **unchanged** (pre-existing behaviour, not modified, not re-tested here) | `explicit` |
| Declared root | no edges, record declares `dag-root` | pass | `declared_root` |
| Genesis | no edges, no declaration, **and G2 ∧ G3 ∧ G4** (below) | pass | `genesis` |
| Unsequenced | no edges, no declaration, **any** genesis condition fails | **block** `UNSEQUENCED_SHIPMENT` | `unsequenced` |

The `explicit` row's closure check is named only to describe what already happens
on that path. This plan does **not** touch it, and no task asserts over it
(`FD0CCB42` owns that surface exclusively).

#### Genesis conditions (narrowed — review-fix cycle 2)

* **G2** — no shipped-terminal shipment exists anywhere, **live or archived**.
* **G3** — the candidate is the **sole extant nonterminal shipment**: no other
  shipment record exists in a nonterminal state (`queued`/`active`), live or
  archived.
* **G4** — no `abandoned` shipment record exists anywhere, live or archived.

The cycle-1 rule ("no shipped-terminal shipment exists") is **replaced** because it
fails open. In a workspace with many queued shipments and nothing yet shipped it
returns `genesis` for **every** edge-less shipment at once, including
later-numbered candidates downstream of other pending work. G3 makes genesis a
**cardinality-1** state that cannot be true for two shipments simultaneously and
ceases to be available once a workspace holds a second shipment record of any
kind — so a later-numbered candidate has no genesis path and blocks as
`unsequenced` until intent is recorded. G4 exists because `abandoned` is terminal
but not *shipped*, so G2 alone would admit an abandoned-only history as a fresh
install.

| Workspace | Genesis? | Edge-less undeclared candidate |
|---|---|---|
| Exactly one shipment record, nothing else | yes | pass `genesis` |
| Several `queued`, nothing ever shipped | no (G3) | block `unsequenced` |
| Shipped history only as archived records | no (G2) | block `unsequenced` |
| Only an `abandoned` record in history | no (G4) | block `unsequenced` |
| Any of the above + `dag-root` on candidate | n/a | pass `declared_root` |

G2/G3/G4 are workspace-level facts computed **once per evaluation** from a single
snapshot inside the shared helper (§3.4) and handed to both gates.

The four states are total and mutually exclusive. `predecessor_source` is present
on **every** `shipment_readiness` payload — blocked and passed alike.

The `UNSEQUENCED_SHIPMENT` message must name the two remedies explicitly (record
the real `blocks` edge, or declare the shipment a root), so the block is never a
dead end; where genesis was disqualified, it also names which of G2/G3/G4 applied.

### 3.2 Root declaration

The declaration is the label `dag-root` on the shipment's own backlogit record,
read from existing frontmatter. Declaring a root is an operator/Stage act; Ship
must not self-declare a root to unblock its own claim.

**What that authority actually is (narrowed, cycle 3).** The declaration is a
**version-controlled, review-gated statement inside the repository trust
boundary**. Its force comes from three properties and no others: the label lives
in a committed backlog record, so applying it produces a **diff**; that diff
passes through the same review path as any other change to the repository; and
`predecessor_source: declared_root` names the state on every payload, so each
such pass is **attributable after the fact**.

It is therefore **auditable but not mechanically permission-enforced**, and it is
**not a security boundary**. Any actor that can already commit to the repository
can apply the label, and nothing in this plan detects or prevents that at gate
time — a permission model would have to live in backlogit, which this plan does
not modify. The prohibition on Ship self-declaring a root is an **agent-contract
rule carried in the agent instructions (T8)**, enforced by review and audit, not
by the gate. No claim is made here that the declaration has no escape hatch, and
none should be inferred: within the repository trust boundary it is a convention
backed by review and provenance, and that is the whole of its strength.

**Labels get their own validator, and `ShipmentState` keeps the tuple
(cycle 2, refined in cycle 3).** `labels` must **not** be parsed with
`_tuple_of_str`. Verified against source: that function (L331) validates every
member against `_ARTIFACT_ID_PATTERN` (`^\d+(?:\.\d+)*-[A-Z]+$`) and raises
`BacklogUnavailableError` on any non-match — and `dag-root` does not match.
Reusing it would turn **every labelled shipment record**, `173-S` included, into a
hard read failure across the whole gate. A labels-specific validator carries over
the fail-closed *discipline* (absent field is fine; present-but-wrong-shaped
container raises; non-string, blank, or traversal-shaped member raises; never
coerce or drop) while applying label syntax.

`ShipmentState` **retains the validated, immutable `labels` tuple** as its stored
field — it does not collapse the parse result into a single boolean. Root
classification is a **derived** property computed from that tuple (an exact,
case-sensitive membership test for `dag-root`). Keeping the tuple preserves the
evidence behind the classification, so audit output can show *which* labels were
read rather than only the verdict, and a future label-carried contract does not
require re-plumbing the reader. Reader-level tests assert both polarities,
including a positive anti-regression that `[dag-root, topology-gate]` parses
cleanly.

### 3.3 Sequencing audit (read-only migration path)

`--phase audit_sequencing` is non-authorizing, never blocks, and never mutates.
For every edge-less shipment it reports the derived state, the raw
numerically-adjacent candidate the retired heuristic would have inferred, which
genesis disqualifier applied where the state is `unsequenced`, and the remediation
options available. It must **not** apply the reverse-dependency suppression
predicate.

**It is a pure report and nothing more (cycle 3).** The audit computes from the
workspace it reads and emits output; it **writes nothing**, persists nothing, and
owns no storage. The cycle-2 "durable, append-only migration ledger" is
**removed** — along with every persistence claim, every durable-artifact
requirement, and the field recording the remediation an operator *would later*
choose. That field described a decision that has not happened at audit time, so
the audit could only ever have recorded a guess or an empty slot.

Building a ledger would have given a **read-only gate phase its own write path and
its own durable file format** — a persistence subsystem inside the component whose
defining property is that it does not mutate, and a second source of truth about
backlog state that can itself drift from the backlog. The migration record already
exists and needs no invention: operators migrate by editing backlog records with
ordinary backlogit commands, and those edits are **version-controlled commits**.
The commit history and its diffs are the external migration record and the
rollback evidence — durable, reviewable, attributable, and already trusted for
every other change in the repository (§H4).

### 3.4 Advisory alignment (`dag-readiness`)

`dag-readiness` remains advisory and non-authorizing. It must model **all four**
derivation states through the **same shared derivation helper** `pre_claim` uses;
must never place a `unsequenced`-blocked shipment in `ready_set`/`next_eligible`;
must never report a `declared_root` blocked; must label output non-authorizing; and
must disambiguate `next_eligible` so it cannot read as authorization.

The shared helper covers **derivation only** (cycle 3). Closure evidence is
**not** part of it, not discovered by it, not evaluated by it, and not asserted
for parity anywhere in this plan — `FD0CCB42` owns that surface exclusively.

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

**Expected-failure reasons are constrained (cycle 3).** Every strict
expected-failure marker must be scoped to the *specific* expected defect — the
assertion it is allowed to fail on, and the exception types it is allowed to raise
— so that an unrelated cause cannot satisfy RED. A fixture/setup error, an import
or collection error, an unknown or unregistered `--phase` value, a typo in a
fixture, or any other incidental failure must **not** count as the expected
failure. Where the harness supports it, pin the marker with an explicit
`raises=`/reason and assert the expected message or payload shape, so the test
fails loudly on the wrong failure instead of passing quietly as "still red".

**Task labels track task IDs (cycle 3).** The task numbering below is `T{n}` for
`165.00{n}-T`; there is no `T7`, because `165.007-T` is archived and descoped.
Cycle 2 left `165.008-T` labelled "T7" after the merge, which made the plan, the
review, and the backlog records disagree about which task was which.

| # | Task | ID | Kind | Size | Complexity | Depends on |
|---|---|---|---|---|---|---|
| T1 | Derivation test harness: characterization + expected-failure matrix | 165.001-T | test | M | medium | — |
| T2 | Engine: four-state derivation, provenance, legacy-test re-expression | 165.002-T | impl | M | high | T1 |
| T3 | Sequencing audit phase (pure read-only report) + tests | 165.003-T | impl | M | medium | T2 |
| T4 | Advisory parity test matrix (characterization + expected-failure) | 165.004-T | test | S | medium | T2 |
| T5 | Engine: `dag-readiness` parity via shared derivation helper | 165.005-T | impl | M | high | T4 |
| T6 | CLI: provenance, remediation, and audit output + tests | 165.006-T | impl | S | low | T2, **T3** |
| T8 | Agent template sources **and** installed dogfood mirrors (atomic) | 165.008-T | docs | M | medium | T5, T6 |
| T9 | Gate documentation + audit/migration/rollback guide | 165.009-T | docs | S | low | T5, T6 |

**Cycle-2 structural corrections (retained).**

* **The source/mirror split is gone.** The cycle-1 split of template sources from
  installed dogfood mirrors (then `165.010-T`) is **reversed**; `165.010-T` is
  archived and its work is part of **T8 (`165.008-T`)**. A dependency edge only
  *schedules* drift — between the two tasks the repository would hold template
  sources stating the four-state contract while the installed `.github/agents/`
  mirrors, which the dogfooded agents in this repository actually read, still
  stated retired numeric sequencing. That window is a live wrong-contract window
  at any duration. T8 absorbed the size (S → M); no work was descoped.
* **T6 now depends on T3.** T6 renders `--phase audit_sequencing` output, which T3
  produces; the cycle-1 edge set omitted that, allowing T6 to start against a
  phase that does not exist.

### T1 — Derivation test harness (165.001-T)

**Characterization (passes on current `main`, must keep passing):**

1. Explicit linear chain blocks correctly on an unshipped explicit predecessor.
2. Closure evidence is demanded for an actual explicit predecessor. *(Pins
   pre-existing behaviour so the refactor cannot disturb it. This is the only
   closure-touching test in the plan, and it is a lock, not a new requirement.)*
3. Converging DAG — two explicit predecessors on one successor; every explicit
   predecessor is evaluated, none skipped.
4. **Malformed/unresolvable dependency IDs fail closed** and are never silently
   dropped. This is **existing** behaviour: `_tuple_of_str` already validates
   dependency members against `_ARTIFACT_ID_PATTERN` and raises, so it is a
   characterization test and must **not** be written as an expected failure.
5. **Label parsing does not currently raise (cycle 3 reclassification).** A
   shipment record carrying `labels: [dag-root, topology-gate]` is read
   **successfully today** and raises nothing. Verified against source:
   `ShipmentState` (L91–98) has no `labels` field and `topology.py` contains no
   reference to `labels` at all, so the field is simply not consulted. This is the
   **positive anti-regression** against ever validating labels with the artifact-ID
   validator, and it belongs here as a **passing characterization test** (former
   N7a). Marking it strict expected-failure would have been wrong twice over: it
   asserts behaviour that already holds, and under `xfail(strict=True)` it would
   **XPASS and fail the suite** the moment it ran.

**New expectations (strict expected-failure; flipped by T2):**

1. Two numerically adjacent edge-less shipments are **not** blocked by numeric
   inference.
2. Closure evidence is **never** demanded for a merely numerically-adjacent
   non-predecessor.
3. `predecessor_source` is present and correct on a **passing** payload and on a
   **blocked** payload.
4. Declared root passes with `predecessor_source: declared_root`.
5. **Genesis, asserted per disqualifier** (cycle 2): (a) a workspace holding
   exactly one shipment record passes `genesis`; (b) archived-only shipped history
   is **not** genesis (G2); (c) several queued shipments with nothing ever shipped
   is **not** genesis for *any* of them — asserted over at least two candidates
   including a later-numbered one (G3); (d) abandoned-only history is **not**
   genesis (G4); (e) `dag-root` still passes as `declared_root` in each
   non-genesis workspace, proving the narrow rule does not deadlock real roots.
6. Unsequenced shipment blocks with `UNSEQUENCED_SHIPMENT`, and the message names
   both remedies.
7. **Label preservation and root classification** — genuinely absent today, so
   legitimately RED: the reader stores a validated immutable `labels` tuple on
   `ShipmentState`, and root classification derives from it (exact,
   case-sensitive `dag-root` membership; unrelated labels yield no declaration).
8. **Malformed-label rejection** — genuinely absent today, so legitimately RED:
   labels are currently ignored entirely, so **nothing raises**. A bare-string or
   scalar `labels` must raise; a non-string member, a blank/whitespace-only
   member, and a traversal-shaped member (`/`, `\`, or `..`) must each raise.

**Malformed dependency vs. malformed label — do not conflate (cycle 3).**
Malformed *dependency* IDs already fail closed → characterization (item 4 above).
Malformed *labels* are currently not validated at all → expected failure (item 8
above). Writing the first as RED would be dishonest; writing the second as
characterization would assert behaviour that does not exist.

Every expected-failure marker above must be constrained per the reason rule in
§4: scoped to its specific assertion and exception type, so a fixture error or an
unregistered-phase error cannot satisfy RED.

Fixtures must make each state distinguishable — a fixture in which two states
would produce the same observation cannot assert either (vacuous-test learning).
Each genesis disqualifier is asserted independently so no composite fixture can
carry the rule vacuously.

### T2 — Engine change (165.002-T)

Implement §3.1: derive from `blocking_predecessor_ids` only; parse the record's
`labels` into a **validated, immutable `labels` tuple on `ShipmentState`** through
a labels-specific fail-closed validator, **never `_tuple_of_str`**, and derive
root classification from that tuple rather than storing a bare boolean (§3.2);
implement the four-state resolution with the narrowed genesis rule (G2/G3/G4);
attach `predecessor_source` to every payload; add `UNSEQUENCED_SHIPMENT` with
remedy-naming text; remove `_prior_shipment_id` from the claim path (do not delete
the function — T3 re-homes it as audit input, so deleting it would create a
dangling reference).

**Atomic legacy-test re-expression (same task, same commit).** The five
`ImplicitNumericPredecessorTests` cases pin claim-path numeric behaviour that this
task removes; they cannot be handled in a later task without leaving the suite red
in between. Each case gets a recorded disposition, and — corrected in cycle 2 —
only **two** dispositions are permitted:

1. **Surviving safety intent** → re-expressed as an explicit-DAG or four-state
   assertion that passes in this task.
2. **Historical directional knowledge** → re-expressed as a **raw
   `audit_sequencing` numeric-candidate expectation**, written here as a *strict
   expected-failure* test (the audit surface arrives in T3) and flipped green by
   T3. Stated as the **negation** of suppression: the multi-hop and
   forward-dependent configurations, where suppression would have hidden the
   candidate, must still yield a reported raw candidate.

**Retracted:** cycle 1 allowed suppression-only cases to become direct unit tests
of `_prior_shipment_id`. That would pin the retired, defective predicate as a live
tested contract and contradicts D3/F6, which require the audit to report the raw
candidate *without* suppression. Bulk deletion remains forbidden; any case with
genuinely no equivalent requires written rationale. Update the class docstring to
record the heuristic as retired history.

Flip T1's expected-failure markers to ordinary assertions. **Prove by test — not by
assertion — that the still-unfixed forward-dependent suppression defect can no
longer affect a claim. There is no deferral option (cycle 2):** any surviving
numeric inference reachable from a claim path blocks this task *and* `173-S` until
removed. Cycle 1's "record a follow-up stash entry rather than silently fixing it"
is **retracted** — it permitted the task to close with the exact defect class it
exists to eliminate still live, shipping a shipment whose stated contract ("no
numeric comparison on the claim path in any state") would be false. Escalate to
the operator if removal exceeds budget; splitting the remaining removal into
another task *inside* `173-S` is acceptable, shipping with the residue is not.

### T3 — Sequencing audit phase (165.003-T)

Implement §3.3. Register `audit_sequencing` in `VALID_PHASES` only, **not** in
`SCOPED_PHASES`, and give it no phase status requirement, so it cannot disturb the
`lifecycle` phase's active-target invariant. Report per edge-less shipment: derived
state, raw numeric-adjacency candidate, the applicable genesis disqualifier, and
the remediation options available. **Emit that report and nothing else** — the
phase performs no write of any kind, owns no durable artifact, and defines no file
format. The cycle-2 migration-ledger requirement is **removed** (§3.3); the
external migration record is the version-controlled commit history of the backlog
records the operator edits, and the rollback evidence is those commits and their
diffs (§H4). Tests must assert the audit reports a candidate in the exact
configuration where the suppression predicate would have hidden it, that the audit
never blocks or authorizes, and that it performs **no mutation and no persistence**.

**T3 also flips the strict-xfail audit expectations inherited from T2** (the
re-expressed historical directional cases). If any cannot be flipped green, the
audit has inherited the suppression predicate and T3 is not done.

### T4 — Advisory parity matrix (165.004-T)

Characterization for existing agreement; expected-failure for the new parity
requirements. The matrix is **total over the four derivation states and covers
nothing else** (cycle 3 correction).

**Closure evidence is out of this matrix entirely.** Cycle 2 narrowed the closure
dimension to the `explicit` state; cycle 3 **removes it**. T4 does not discover,
read, evaluate, or assert parity over closure evidence in any state, and no
acceptance criterion here mentions it. Closure-evidence producer/consumer
behaviour — including any test that composes the two halves — belongs exclusively
to `FD0CCB42`. Keeping even one closure cell in this shipment would re-import a
surface that decision D4 descoped and would create a second, competing owner for
naming semantics `FD0CCB42` must be free to redefine.

Parity is therefore asserted over predecessor **state** only:

* `explicit` — a shipment with edges resolves to the same predecessor state in
  both gates. Tested with the predecessor **unshipped** and with the predecessor
  **shipped-terminal**; the assertion is on the derived state and on
  `ready_set`/`next_eligible` membership, never on closure evidence.
* `declared_root` — must never be advisory-blocked while `pre_claim` passes it;
  parity fails in **both** directions, not just the permissive one.
* `genesis` — built on a **genesis-valid** fixture (sole extant record) and
  reported consistently with `pre_claim`'s pass.
* `unsequenced` — must never be `next_eligible` or in `ready_set`.
* One **genesis-narrowness** case: a genesis-disqualified workspace reads
  `unsequenced` in *both* gates.

Advisory output is labelled non-authorizing, and `dag-readiness` never authorizes
under any configuration.

Each edge-less state is asserted **once**; only `explicit` carries more than one
case, because only it has a predecessor whose shipped-status can vary. Expected
failures follow the constrained-reason rule in §4.

### T5 — Advisory engine alignment (165.005-T)

Turn T4 green. The **derivation** logic **must** be a single shared helper consumed
by both gates — a parallel reimplementation is a review-blocking defect, because
independent logic is the architectural root cause of the original divergence.

**The helper is derivation-only (cycle 3).** It does not wrap, call, reuse, or
re-expose `closure_complete`, and closure evidence is not part of the parity
contract. Cycle 2's "reusing `closure_complete` read-only" instruction is
**withdrawn**: read-only reuse still made this shipment a consumer of the exact
producer/consumer surface `FD0CCB42` exists to redefine, which would force
`FD0CCB42` to coordinate with an already-shipped consumer it never agreed to.
`pre_claim`'s own pre-existing closure check on the `explicit` path is untouched
and stays where it is.

The genesis facts G2/G3/G4 are computed **once** inside that helper from one
snapshot and handed to both gates; the advisory side must consume the **same
narrow** genesis rule, never a broader "nothing shipped yet" notion. State in the
task record whether the helper lives in `topology.py` or a new module. Exclude
policy-blocked shipments from `next_eligible`. `pre_claim` remains sole claim
authority.

### T6 — CLI output (165.006-T)

Surface `predecessor_source` and the selected predecessor IDs in JSON and human
output on blocked and passed paths; render the `UNSEQUENCED_SHIPMENT` remedy text
and the applicable genesis disqualifier; render **audit-phase output** readably.
The audit rendering is **pure report rendering** — there is no ledger and no
persisted artifact to reference (§3.3), so the CLI displays only what the audit
computes. Changes are **additive** — no existing field is renamed or removed.
Assert in `tests/test_gate_pipeline_topology_cli.py`. **Retains dependencies on
both T2 and T3**: T2 supplies `predecessor_source` for the provenance
deliverables, and T3 supplies the audit payload that deliverable renders.

### T8 — Agent contract text, sources and mirrors atomically (165.008-T)

A **mandatory member of `173-S`** that may not be deferred, split, or partially
delivered. Template sources and installed dogfood mirrors are updated in **one
task and one commit**:

* **Sources**: `templates/agents/_orchestrator.agent.md.tmpl` (L312, L314, L339,
  L341) and `templates/agents/_ship.agent.md.tmpl` (L172–175, L200–201, L224–225,
  L235).
* **Mirrors, same commit**: `.github/agents/_orchestrator.agent.md` and
  `.github/agents/_ship.agent.md`. No other installed instruction file is in scope.

Content: predecessors derive from explicit `blocks` edges; the four states and
their provenance values; **genesis is narrow** — an agent must not expect a second
or later-numbered edge-less shipment to pass as `genesis`; `pre_claim` is the sole
claim authority and `dag-readiness` is advisory/non-authorizing; **Ship must not
self-declare `dag-root`**, stated as an agent-contract rule enforced by review and
audit rather than by the gate (§3.2); and the audit phase is the migration path,
with a code-only rollback not undoing migrated data.

A source-versus-mirror **parity check is recorded in the task**, performed against
the final working tree before commit; drift found is fixed, not noted. Introduce no
unresolved template placeholder tokens, and keep markdownlint heading hierarchy
clean (P-008).

### T9 — Documentation and migration guide (165.009-T)

Document the contract, the four provenance values, the `UNSEQUENCED_SHIPMENT`
signal and its two remedies, the **narrow genesis rule** and why absence of
shipped history alone is insufficient, the root-declaration surface — including
what its authority is and is not (§3.2) — and the `audit_sequencing` migration
procedure end to end. Explain why numeric adjacency was retired, citing the three
recorded defect cycles. Record the **data-ordered rollback posture** (§H4): what is
code-reversible, what is not, that the operator's own **migration commits and their
diffs** are the record used to reverse migrated data, the mandatory data-first
ordering, and the narrowed claim where migration was not committed. Cross-reference
the decision, this plan, and the committed intake bug report.

## 5. Risks

| Risk | Mitigation |
|---|---|
| Silent fail-open for prior numeric-reliant workspaces | Unsequenced state blocks in any genesis-disqualified workspace (§3.1); audit phase migrates intent (T3) |
| Genesis granted too broadly, becoming a back-door fail-open | Genesis narrowed to sole-extancy (G3) plus archived-inclusive shipped history (G2) and abandoned history (G4); each disqualifier asserted independently (T1) |
| `labels` parsed with the artifact-ID validator, hard-failing every labelled record | Labels-specific fail-closed validator required (§3.2); positive reader-level anti-regression as a **characterization** test (T1) |
| Blocking posture deadlocks legitimate roots | Declared-root state plus genesis bootstrap; block message names both remedies and the disqualifier |
| Ship self-declares a root to unblock itself | Declaration authority is operator/Stage; the label is a committed, diffable, review-gated record and provenance makes each pass attributable; T8 states the prohibition in both sources and mirrors. **Not mechanically enforced** — see §3.2 and H5 |
| A task leaves the suite red | Expected-failure harness flipped by its implementer; legacy-test re-expression atomic with removal (T2); T2's audit expectations land strict-xfail and are flipped by T3 |
| **A strict-xfail passes for the wrong reason, or XPASSes** | Expected-failure reasons are constrained to a specific assertion and exception type (§4); behaviour that already exists is characterization, never RED (T1 items 4–5) |
| Advisory/authoritative divergence recurs | Shared **derivation** helper (T5) with one-snapshot genesis facts plus a state-parity matrix (T4) |
| Audit inherits the suppression defect | T3 reports raw candidates, asserted by the expectations T2 authors and T3 flips |
| **A read-only gate phase acquires a write path** | T3 emits a report only; no ledger, no durable artifact, no file format (§3.3); tests assert no mutation and no persistence |
| Template/installed-copy drift | T8 updates sources and mirrors in one commit and records a parity check; no intermediate window exists |
| Rollback assumed code-only, stranding migrated edges/labels | Documented data-first rollback ordering against the operator's version-controlled migration commits and diffs (T9, H4) |
| Scope creep into closure evidence | Descoped to `FD0CCB42`, which owns it **exclusively**; no task reads, evaluates, or asserts parity over closure evidence, and no acceptance criterion references it |

## 6. Quality Criteria

* Genuinely new behaviour lands as a failing expectation before implementation;
  existing behaviour is characterized, not faked as RED, and every expected-failure
  marker is constrained so an incidental error cannot satisfy it.
* Every task ends with a green suite.
* `pre_claim` remains sole claim authority in code, output, templates, and docs.
* The `audit_sequencing` phase writes nothing and persists nothing.
* No closure-evidence discovery, evaluation, or parity assertion appears in any
  task or acceptance criterion; `FD0CCB42` owns that surface exclusively.
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
| F3 | Advisory alignment reimplements derivation logic and re-diverges | T5 MUST consume one shared **derivation** helper; a parallel implementation is a review-blocking defect. The helper does **not** include closure evidence (cycle 3) |
| F4 | Legacy safety cases deleted in bulk under cover of "migration" | T2 requires a per-case disposition for all five cases with written rationale for any non-migratable case, and permits only two disposition kinds |
| F5 | A task ends red because test disposition trails the behaviour change | Expected-failure flip and legacy re-expression both occur inside the task that changes behaviour; T2's audit expectations are strict-xfail until T3 |
| F6 | Retirement silently inherits the unfixed forward-dependent defect | T2 must **prove** claim-path moot-ness by test, with **no deferral option** — residue blocks the task and the shipment; T3 forbids the audit from inheriting the suppression predicate |
| F7 | A new config surface is added without schema versioning discipline | No config key is added at all (D2); the schema surface does not exist to mutate |
| F8 | Installed dogfood copies drift from template sources | Sources and mirrors land in **one task and one commit** (T8) with a recorded parity check; the cycle-1 dependency-only split is reversed because it scheduled drift rather than preventing it |
| F9 | Closure-gate weakening sneaks in as a way to unblock `163-S` | No task touches closure semantics; the defect is descoped to `FD0CCB42` with an explicit no-weakening, no-competing-artifact constraint |
| F10 | Parity tests pass vacuously | T4 is total over the four derivation states and carries no dimension that cannot apply to them; T1 asserts each genesis disqualifier independently with distinguishable fixtures |
| F11 | Genesis re-entered through a back door (archiving, abandonment, or a populated-but-unshipped workspace) | Three-clause genesis rule (G2/G3/G4) computed from one snapshot, with per-clause tests |
| F12 | `labels` validation reuses artifact-ID syntax and bricks the gate | Labels-specific validator mandated in §3.2 and T2, with a positive reader-level anti-regression **characterization** test |
| F13 | A strict-xfail is satisfied by a setup/collection/unknown-phase error, or XPASSes because the behaviour already exists | Expected-failure reasons constrained to a specific assertion and exception type (§4); the label-parse anti-regression reclassified to characterization (T1) |
| F14 | The read-only audit grows a durable write path and becomes a second source of truth | Ledger removed (§3.3); the audit emits a report only, and version-controlled migration commits/diffs are the external record (H4) |
| F15 | A descoped surface is re-imported through "read-only reuse" or a single test cell | Closure evidence removed from T4/T5 and every acceptance criterion; `FD0CCB42` is the exclusive owner |

### H3 — Explicit non-goals (scope fences)

* Does **not** change branch-naming authority (`86498B64`, separate and next).
* Does **not** alter `--force` override semantics; `--force` remains
  human-authorized, shipment-specific, and audited — never agent-issued.
* Does **not** make `dag-readiness` authorizing under any configuration.
* Does **not** modify backlogit.
* Does **not** touch closure-evidence semantics (`FD0CCB42`).
* Does **not** add configuration or schema surfaces.

### H4 — Rollback posture (corrected in cycle 2, re-posed in cycle 3)

Cycle 1 claimed "a full revert of the engine change restores prior behaviour". That
is **false on its own** and is narrowed here.

* **Code-reversible**: the derivation logic, the additive `predecessor_source`
  field (safe for older consumers to ignore), the `audit_sequencing` phase, and the
  `UNSEQUENCED_SHIPMENT` token. No orphaned configuration is left behind, because
  no configuration was introduced.
* **Not code-reversible**: the `blocks` edges and `dag-root` labels the migration
  writes into backlog records. **A code rollback does not undo migration data.**
  These persist after an engine revert, and the restored numeric engine then reads
  the migrated edges as real explicit predecessors — a state that existed in
  neither the before nor the after configuration, and the most likely source of a
  confusing mid-rollback block.
* **The migration record is the commit history, not a gate-owned ledger**
  (cycle 3). Migration is performed by editing backlog records with ordinary
  backlogit commands, and those records are version-controlled. The **migration
  commits and their diffs** are therefore the ledger: they show exactly which
  edges and labels were added, to which records, when, and by whom, and
  `git revert`/`git diff` reverses them precisely. This plan deliberately does
  **not** build a persistence subsystem inside the gate to duplicate a record git
  already keeps — a gate-owned ledger would be a second source of truth that can
  drift from the backlog it describes, and it would give a phase defined as
  read-only its own write path.
* **Mandatory ordering**: revert **backlog data first**, using the migration
  commits/diffs to restore the recorded pre-migration edge and label state,
  **then** revert the engine. Never the reverse.
* **Narrowed claim**: where migration was performed without being committed — hand
  edits never recorded in version control — data rollback is manual reconstruction
  from record history. It is not automatic, and this plan does not claim otherwise.

### H5 — Residual risk accepted

In a workspace with shipping history and no explicit `blocks` edges anywhere, every
shipment blocks as `unsequenced` until audited. This is the intended fail-closed
posture: it converts an unstated assumption into a one-time, bounded, self-service
action with tooling (T3) and documentation (T9) to support it. The alternative —
passing by default — is the silent fail-open this design exists to prevent. Cycle 2
widens this slightly: a workspace that has *never shipped* but holds more than one
shipment record is also in this posture, by design (G3).

**Also accepted (cycle 3): `dag-root` is not mechanically enforced.** Any actor who
can commit to the repository can apply the label, and the gate neither detects nor
prevents that. The declaration is a version-controlled, review-gated statement
inside the repository trust boundary — auditable through diffs and through
`predecessor_source: declared_root`, but **not a security boundary** and not
permission-checked. Mechanical enforcement would require a backlogit-side
permission model, which is outside this shipment (§3.2).

### H6 — Bootstrap disposition carried into execution (decision D6)

`173-S` is blocked by the very defect it fixes: under current code its absent edges
cause `172-S` to be synthesised as a predecessor. Operator authorization dated
2026-09-12, **re-scoped in cycle 2 and corrected in cycle 3**, permits **exactly
three** audited `pre_claim --force` invocations for `173-S` only:

| # | Invoked by | Invocation point |
|---|---|---|
| U0 | **Orchestrator** | `pre_claim` route-to-Ship eligibility check, **before Ship is invoked** (`_orchestrator.agent.md` L239–241) |
| U1 | Ship | `pre_claim` before branch/worktree creation (`_ship.agent.md` L227–229) |
| U2 | Ship | `pre_claim` immediately before the claim (`_ship.agent.md` L254–255) |

Cycle 1's "single-use" grant was **unsatisfiable**, and cycle 2's two-use grant was
**still short by one**: it counted only Ship's two gate runs and missed the
Orchestrator's **pre-route** eligibility gate, which runs first and against the same
shipment. Under a two-use grant the very first gate in the pipeline would have been
unauthorized — the Orchestrator would have blocked and never routed `173-S` to Ship
at all, or would have silently stretched an authorization written for Ship across a
run Ship did not make.

The Orchestrator's **cursor-advance** eligibility check (L261–263) evaluates
`{next_shipment_id}` — a *different* shipment — and is therefore **not** covered by
this grant and never consumes one of the three invocations.

Each invocation is valid only if, at that moment: the sole blocking token is
`PREDECESSOR_NOT_SHIPPED`; the inferred predecessor is exactly `172-S`; `HEAD` and
the `173-S` manifest match the reviewed state; and no other topology, check,
closure, or secrets violation is present. Each is recorded as an audit event naming
the invocation, payload, token, predecessor, `HEAD` SHA, and decision D6.

Authority **expires immediately** on the successful claim or on any mismatch; on
mismatch the invoking agent halts to the operator. A **fourth** invocation — for
example the post-claim `CLAIM_NOT_OBSERVED` retry path's `pre_claim` re-run — is
**not authorized** and must be evaluated without `--force`. Post-claim retry is
never covered: the grant exists to reach the claim, and it is exhausted by it.

The authorization confers no broader force authority, does not change `--force`
semantics, and becomes unnecessary once T2 lands — `173-S` already carries
`labels: [dag-root]`, so it will then pass natively as `declared_root`.

**Hardening complete. Plan is ready for `plan-review`.**

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

Cycle-3 correction re-review recorded in full at
`docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md`
(cycle 4): **0 P0, 0 P1, 2 P2, 4 P3**. All fifteen operator correction items from
the authorized final narrow correction cycle are verified resolved in the review's
"Operator Correction Verification" table. This was the **authorized final review**:
the three normal correction cycles were consumed by cycles 1–3, and cycle 4 is the
single additional narrow correction cycle the operator authorized. **No further
fix loop remains.**

Plan hardening was required and is present, re-performed against the corrected
contract. The plan is harvest-ready and `173-S` is staging-PR ready.

### Closure posture for `173-S` (verified, cycle 3)

`173-S` closes via **per-item `SAFE_CLOSE`**, which is a supported close path and
is **not** a blocker. This was established empirically by a read-only execution of
`classify_shipment_close_path` against the live workspace: it returns
`ClosePath.SAFE_CLOSE`, with the reason naming `165.007-T` and `165.010-T` as
descendants of feature member `165-F` that sit outside the manifest.

`CASCADE` is **unavailable by design**, because those two archived tasks remain
off-manifest descendants — which is exactly the intended outcome of descope
decision D4 and of the cycle-2 merge, not a defect. Restoring `CASCADE` would
require re-adding both archived tasks to the manifest, which D4 forbids.

Their provenance and off-manifest status are **preserved unchanged**: `165.007-T`
remains archived and descoped to `FD0CCB42`, `165.010-T` remains archived and
merged into `165.008-T`, and neither is reparented, re-added to the manifest, or
moved under an invented holding feature. Any statement that `173-S` cannot be
closed, or that both close paths are impossible, is **false and is retracted** —
`SAFE_CLOSE` is the final closure strategy for this shipment.
