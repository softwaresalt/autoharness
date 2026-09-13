---
title: "DAG-authoritative predecessor derivation for pipeline-topology pre_claim — decided plan"
description: "Test-first implementation plan retiring the implicit numeric-adjacency predecessor heuristic in `pipeline-topology --phase pre_claim` in favour of explicit backlogit `blocks` DAG edges under a four-state declared-root contract, adding deterministic predecessor provenance and a read-only sequencing audit phase, aligning `dag-readiness` advisory output across every derivation state, and coupling agent templates, installed dogfood copies, and documentation."
doc_type: plan
source: docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md
date: 2026-09-12
status: decided
revision: 3
revision_note: "Review-fix cycle 2 — genesis narrowed to a non-fail-open sole-extancy rule, labels given their own validator (the artifact-ID validator would hard-fail every labelled record), template/mirror work merged into one atomic task, T6 given its missing dependency on T3, legacy-test knowledge re-homed to audit expectations instead of `_prior_shipment_id` pins, the F6 deferral escape hatch removed, closure parity narrowed to the explicit state, rollback re-posed as data-ordered with a migration ledger, and the original intake bug report committed verbatim."
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

**Source integrity corrected (review-fix cycle 2).** The original intake document,
`docs/bugs/2026-09-11-autoharness-pipeline-topology-numeric-predecessor-bug.md`,
recommended a presentation-only remedy and classified numeric-fallback removal as
a future option; operator direction supersedes that recommendation. Cycle 1
handled the fact that the file was untracked by deleting every reference to it —
but the archived stash record `AF2890B7` and the cycle-1 session memory still
named the path, so the durable record referenced a file no reader could resolve.
Under operator authorization the document is now **committed verbatim and
unmodified**, so those references resolve. It is a **historical record, not a
design input**: nothing in this plan depends on it, and where it conflicts with
the decision, the decision governs. Its substance is also preserved as prose in
the decision's *Historical context* section.

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
| Shipment reader | `topology.py::ShipmentState` (L91–98) and its frontmatter parser (L560–600) | Add a root-declaration field parsed from the record's `labels` via a **new labels-specific** fail-closed validator (not `_tuple_of_str`) |
| Advisory readiness | `topology.py::_dag_all_predecessors_finished` (L1873), `compute_dag_readiness` (L1968) | Consume the shared derivation/closure helper; advisory labelling |
| Next-eligible | `topology.py::compute_next_eligible` (L2075) | Exclude policy-blocked shipments; non-authorizing disambiguation |
| Closure evidence | `topology.py::FilesystemTopologyReaders.closure_complete` (L654) | **Read-only reuse** through the shared helper — behaviour unchanged (see fence below) |
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
| Genesis | no edges, no declaration, **and G2 ∧ G3 ∧ G4** (below) | pass | `genesis` |
| Unsequenced | no edges, no declaration, **any** genesis condition fails | **block** `UNSEQUENCED_SHIPMENT` | `unsequenced` |

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
must not self-declare a root to unblock its own claim. Every declared-root pass is
auditable because provenance names it.

**Labels get their own validator (review-fix cycle 2).** `labels` must **not** be
parsed with `_tuple_of_str`. Verified against source: that function (L331)
validates every member against `_ARTIFACT_ID_PATTERN` (`^\d+(?:\.\d+)*-[A-Z]+$`)
and raises `BacklogUnavailableError` on any non-match — and `dag-root` does not
match. Reusing it would turn **every labelled shipment record**, `173-S`
included, into a hard read failure across the whole gate. A labels-specific
validator carries over the fail-closed *discipline* (absent field is fine;
present-but-wrong-shaped container raises; non-string, blank, or traversal-shaped
member raises; never coerce or drop) while applying label syntax. Reader-level
tests assert both polarities, including a positive anti-regression that
`[dag-root, topology-gate]` parses cleanly.

### 3.3 Sequencing audit (read-only migration path)

`--phase audit_sequencing` is non-authorizing, never blocks, and never mutates.
For every edge-less shipment it reports the derived state, the raw
numerically-adjacent candidate the retired heuristic would have inferred, which
genesis disqualifier applied where the state is `unsequenced`, and the remediation
choice. It must **not** apply the reverse-dependency suppression predicate.

It also emits a durable, append-only **migration ledger** recording each
shipment's pre-migration edge set and label set. The ledger exists because
migration mutates backlog *data*, which a code revert cannot undo; it is what
makes an ordered rollback possible (§H4).

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
| T3 | Sequencing audit phase + migration ledger + tests | 165.003-T | impl | M | medium | T2 |
| T4 | Advisory parity test matrix (characterization + expected-failure) | 165.004-T | test | S | medium | T2 |
| T5 | Engine: `dag-readiness` parity via shared helper | 165.005-T | impl | M | high | T4 |
| T6 | CLI: provenance, remediation, and audit output + tests | 165.006-T | impl | S | low | T2, **T3** |
| T7 | Agent template sources **and** installed dogfood mirrors (atomic) | 165.008-T | docs | M | medium | T5, T6 |
| T9 | Gate documentation + audit/migration/rollback guide | 165.009-T | docs | S | low | T5, T6 |

**Cycle-2 structural corrections.**

* **T8 is gone.** The cycle-1 split of template sources (T7) from installed
  dogfood mirrors (T8/`165.010-T`) is **reversed**; `165.010-T` is archived and
  its work is now part of T7. A dependency edge only *schedules* drift — between
  the two tasks the repository would hold template sources stating the four-state
  contract while the installed `.github/agents/` mirrors, which the dogfooded
  agents in this repository actually read, still stated retired numeric
  sequencing. That window is a live wrong-contract window at any duration. T7
  absorbed the size (S → M); no work was descoped.
* **T6 now depends on T3.** T6 renders `--phase audit_sequencing` output, which T3
  produces; the cycle-1 edge set omitted that, allowing T6 to start against a
  phase that does not exist.

### T1 — Derivation test harness (165.001-T)

**Characterization (passes on current `main`, must keep passing):**

1. Explicit linear chain blocks correctly on an unshipped explicit predecessor.
2. Closure evidence is demanded for an actual explicit predecessor.
3. Converging DAG — two explicit predecessors on one successor; every explicit
   predecessor is evaluated, none skipped.
4. Malformed/unresolvable dependency IDs fail closed and are never silently
   dropped.

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
7. **Reader-level label parsing** (cycle 2): `[dag-root, topology-gate]` parses
   cleanly and raises nothing (the positive anti-regression against artifact-ID
   validation); absent `labels` is no declaration and no error; a bare-string
   `labels` raises; non-string, blank, and traversal-shaped members raise;
   unrelated labels yield no declaration; the `dag-root` match is exact and
   case-sensitive.

Fixtures must make each state distinguishable — a fixture in which two states
would produce the same observation cannot assert either (vacuous-test learning).
Each genesis disqualifier is asserted independently so no composite fixture can
carry the rule vacuously.

### T2 — Engine change (165.002-T)

Implement §3.1: derive from `blocking_predecessor_ids` only; parse the root
declaration into `ShipmentState` **through a labels-specific fail-closed validator,
never `_tuple_of_str`** (§3.2); implement the four-state resolution with the
narrowed genesis rule (G2/G3/G4); attach `predecessor_source` to every payload; add
`UNSEQUENCED_SHIPMENT` with remedy-naming text; remove `_prior_shipment_id` from
the claim path (do not delete the function — T3 re-homes it as audit input, so
deleting it would create a dangling reference).

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
remediation choice. Emit the **migration ledger** (pre-migration edge/label state
per shipment) that makes ordered rollback possible. Tests must assert the audit
reports a candidate in the exact configuration where the suppression predicate
would have hidden it, that the audit never blocks or authorizes, and that the
ledger is well-formed and faithful.

**T3 also flips the strict-xfail audit expectations inherited from T2** (the
re-expressed historical directional cases). If any cannot be flipped green, the
audit has inherited the suppression predicate and T3 is not done.

### T4 — Advisory parity matrix (165.004-T)

Characterization for existing agreement; expected-failure for the new parity
requirements. The matrix is **total over the four derivation states**, but the
closure-evidence dimension is applied **only to the `explicit` state** (cycle 2
correction): closure evidence is evaluated per explicit predecessor, and the other
three states have no predecessor to evaluate it against, so crossing them with
closure variants would build cells in which the closure dimension cannot change
the outcome — vacuous by construction, the very failure the vacuous-tiebreak
learning warns about. `declared_root`, `genesis`, and `unsequenced` are therefore
each tested **once** for derivation/advisory parity.

Specifically: a `unsequenced`-blocked shipment must never be `next_eligible` or in
`ready_set`; a `declared_root` must never be advisory-blocked; a `genesis` case
built on a **genesis-valid** fixture (sole extant record) is reported consistently,
and one narrowness case asserts that a genesis-disqualified workspace reads
`unsequenced` in *both* gates; an `explicit` shipment whose predecessor is
shipped-terminal but lacks recognized closure evidence must not read as ready while
`pre_claim` blocks it; advisory output is labelled non-authorizing; and
`dag-readiness` never authorizes under any configuration.

### T5 — Advisory engine alignment (165.005-T)

Turn T4 green. The closure-evidence and derivation logic **must** be a single
shared helper consumed by both gates, reusing `closure_complete` read-only — a
parallel reimplementation is a review-blocking defect, because independent logic is
the architectural root cause of the original divergence. The genesis facts
G2/G3/G4 are computed **once** inside that helper from one snapshot and handed to
both gates; the advisory side must consume the **same narrow** genesis rule, never
a broader "nothing shipped yet" notion. State in the task record whether the helper
lives in `topology.py` or a new module. Exclude policy-blocked shipments from
`next_eligible`. `pre_claim` remains sole claim authority.

### T6 — CLI output (165.006-T)

Surface `predecessor_source` and the selected predecessor IDs in JSON and human
output on blocked and passed paths; render the `UNSEQUENCED_SHIPMENT` remedy text
and the applicable genesis disqualifier; render audit-phase output and its ledger
reference readably. Changes are **additive** — no existing field is renamed or
removed. Assert in `tests/test_gate_pipeline_topology_cli.py`. **Depends on T3 as
well as T2**, because deliverable 4 renders a surface T3 creates.

### T7 — Agent contract text, sources and mirrors atomically (165.008-T)

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
self-declare `dag-root`**; the audit phase and its ledger are the migration path,
and a code-only rollback does not undo migrated data.

A source-versus-mirror **parity check is recorded in the task**, performed against
the final working tree before commit; drift found is fixed, not noted. Introduce no
unresolved template placeholder tokens, and keep markdownlint heading hierarchy
clean (P-008).

### T9 — Documentation and migration guide (165.009-T)

Document the contract, the four provenance values, the `UNSEQUENCED_SHIPMENT`
signal and its two remedies, the **narrow genesis rule** and why absence of
shipped history alone is insufficient, the root-declaration surface and who may use
it, and the `audit_sequencing` migration procedure end to end. Explain why numeric
adjacency was retired, citing the three recorded defect cycles. Record the
**data-ordered rollback posture** (§H4): what is code-reversible, what is not, the
migration ledger's role, the mandatory data-first ordering, and the narrowed claim
where no ledger exists. Cross-reference the decision, this plan, and the committed
intake bug report.

## 5. Risks

| Risk | Mitigation |
|---|---|
| Silent fail-open for prior numeric-reliant workspaces | Unsequenced state blocks in any genesis-disqualified workspace (§3.1); audit phase migrates intent (T3) |
| Genesis granted too broadly, becoming a back-door fail-open | Genesis narrowed to sole-extancy (G3) plus archived-inclusive shipped history (G2) and abandoned history (G4); each disqualifier asserted independently (T1) |
| `labels` parsed with the artifact-ID validator, hard-failing every labelled record | Labels-specific fail-closed validator required (§3.2); positive reader-level anti-regression test (T1) |
| Blocking posture deadlocks legitimate roots | Declared-root state plus genesis bootstrap; block message names both remedies and the disqualifier |
| Ship self-declares a root to unblock itself | Declaration authority is operator/Stage; provenance makes it auditable; T7 states the prohibition in both sources and mirrors |
| A task leaves the suite red | Expected-failure harness flipped by its implementer; legacy-test re-expression atomic with removal (T2); T2's audit expectations land strict-xfail and are flipped by T3 |
| Advisory/authoritative divergence recurs | Shared helper (T5) with one-snapshot genesis facts plus a parity matrix (T4) |
| Audit inherits the suppression defect | T3 reports raw candidates, asserted by the expectations T2 authors and T3 flips |
| Template/installed-copy drift | T7 updates sources and mirrors in one commit and records a parity check; no intermediate window exists |
| Rollback assumed code-only, stranding migrated edges/labels | Migration ledger (T3) plus documented data-first rollback ordering (T9, H4) |
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
| F4 | Legacy safety cases deleted in bulk under cover of "migration" | T2 requires a per-case disposition for all five cases with written rationale for any non-migratable case, and permits only two disposition kinds |
| F5 | A task ends red because test disposition trails the behaviour change | Expected-failure flip and legacy re-expression both occur inside the task that changes behaviour; T2's audit expectations are strict-xfail until T3 |
| F6 | Retirement silently inherits the unfixed forward-dependent defect | T2 must **prove** claim-path moot-ness by test, with **no deferral option** — residue blocks the task and the shipment; T3 forbids the audit from inheriting the suppression predicate |
| F7 | A new config surface is added without schema versioning discipline | No config key is added at all (D2); the schema surface does not exist to mutate |
| F8 | Installed dogfood copies drift from template sources | Sources and mirrors land in **one task and one commit** (T7) with a recorded parity check; the cycle-1 dependency-only split is reversed because it scheduled drift rather than preventing it |
| F9 | Closure-gate weakening sneaks in as a way to unblock `163-S` | No task touches closure semantics; the defect is descoped to `FD0CCB42` with an explicit no-weakening, no-competing-artifact constraint |
| F10 | Parity tests pass vacuously | T4 is total over states but does **not** cross closure evidence with states where it cannot apply; T1 asserts each genesis disqualifier independently with distinguishable fixtures |
| F11 | Genesis re-entered through a back door (archiving, abandonment, or a populated-but-unshipped workspace) | Three-clause genesis rule (G2/G3/G4) computed from one snapshot, with per-clause tests |
| F12 | `labels` validation reuses artifact-ID syntax and bricks the gate | Labels-specific validator mandated in §3.2 and T2, with a positive reader-level anti-regression test |

### H3 — Explicit non-goals (scope fences)

* Does **not** change branch-naming authority (`86498B64`, separate and next).
* Does **not** alter `--force` override semantics; `--force` remains
  human-authorized, shipment-specific, and audited — never agent-issued.
* Does **not** make `dag-readiness` authorizing under any configuration.
* Does **not** modify backlogit.
* Does **not** touch closure-evidence semantics (`FD0CCB42`).
* Does **not** add configuration or schema surfaces.

### H4 — Rollback posture (corrected in review-fix cycle 2)

Cycle 1 claimed "a full revert of the engine change restores prior behaviour". That
is **false on its own** and is narrowed here.

* **Code-reversible**: the derivation logic, the additive `predecessor_source`
  field (safe for older consumers to ignore), the `audit_sequencing` phase, and the
  `UNSEQUENCED_SHIPMENT` token. No orphaned configuration is left behind, because
  no configuration was introduced.
* **Not code-reversible**: the `blocks` edges and `dag-root` labels the migration
  writes into backlog records. These persist after an engine revert, and the
  restored numeric engine then reads the migrated edges as real explicit
  predecessors — a state that existed in neither the before nor the after
  configuration, and the most likely source of a confusing mid-rollback block.
* **Migration ledger** (T3): the audit records each shipment's pre-migration edge
  set and label set, so prior state is restored exactly rather than guessed.
* **Mandatory ordering**: revert **backlog data first** using the ledger, **then**
  revert the engine. Never the reverse.
* **Narrowed claim**: for a workspace migrated by hand with no ledger, data
  rollback is manual reconstruction from record history. It is not automatic, and
  this plan does not claim otherwise.

### H5 — Residual risk accepted

In a workspace with shipping history and no explicit `blocks` edges anywhere, every
shipment blocks as `unsequenced` until audited. This is the intended fail-closed
posture: it converts an unstated assumption into a one-time, bounded, self-service
action with tooling (T3) and documentation (T9) to support it. The alternative —
passing by default — is the silent fail-open this design exists to prevent. Cycle 2
widens this slightly: a workspace that has *never shipped* but holds more than one
shipment record is also in this posture, by design (G3).

### H6 — Bootstrap disposition carried into execution (decision D6)

`173-S` is blocked by the very defect it fixes: under current code its absent edges
cause `172-S` to be synthesised as a predecessor. Operator authorization dated
2026-09-12, **re-scoped in review-fix cycle 2**, permits **exactly two** audited
`pre_claim --force` invocations for `173-S` only:

| # | Invocation point |
|---|---|
| U1 | `pre_claim` before branch/worktree creation |
| U2 | `pre_claim` immediately before the claim |

Cycle 1's "single-use" grant was **unsatisfiable**: the Ship protocol runs the gate
twice before claiming and gates the claim on both passing, so a one-use grant would
either halt Ship at the second gate or invite it to stretch one authorization
silently across two invocations.

Each invocation is valid only if, at that moment: the sole blocking token is
`PREDECESSOR_NOT_SHIPPED`; the inferred predecessor is exactly `172-S`; `HEAD` and
the `173-S` manifest match the reviewed state; and no other topology, check,
closure, or secrets violation is present. Each is recorded as an audit event naming
the invocation, payload, token, predecessor, `HEAD` SHA, and decision D6.

Authority **expires immediately** on the successful claim or on any mismatch; on
mismatch Ship halts to the operator. A **third** invocation — for example the
post-claim `CLAIM_NOT_OBSERVED` retry path's `pre_claim` re-run — is **not
authorized** and must be evaluated without `--force`.

The authorization confers no broader force authority, does not change `--force`
semantics, and becomes unnecessary once T2 lands — `173-S` already carries
`labels: [dag-root]`, so it will then pass natively as `declared_root`.

**Hardening complete. Plan is ready for `plan-review`.**

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

Review-fix cycle 2 re-review recorded in full at
`docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md`
(cycle 3): **0 P0, 0 P1, 2 P2, 3 P3**. All twelve operator findings from the
cycle-2 correction request are verified resolved in the review's "Operator
Findings Verification" table. Review cycles used: **3 of 3** — this is the final
normal correction cycle, and no further in-cycle correction budget remains.

Plan hardening was required and is present, re-performed against the corrected
contract. The plan is harvest-ready and `173-S` is staging-PR ready.
