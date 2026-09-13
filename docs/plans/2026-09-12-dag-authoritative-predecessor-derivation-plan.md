---
title: "DAG-authoritative predecessor derivation for pipeline-topology pre_claim — decided plan"
description: "Test-first implementation plan retiring the implicit numeric-adjacency predecessor heuristic in `pipeline-topology --phase pre_claim` in favour of explicit backlogit `blocks` DAG edges under a four-state declared-root contract, adding deterministic predecessor provenance and a read-only sequencing audit phase, aligning `dag-readiness` advisory output across every derivation state, and coupling agent templates, installed dogfood copies, and documentation."
doc_type: plan
source: docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md
date: 2026-09-12
status: decided
revision: 7
revision_note: "PR review-fix cycle 1 (staging PR #448, Copilot review threads; separate from and subsequent to the four completed plan-review cycles). Thread PRRT_kwDORzpWpM6h3Tgb: the cycle-3 U0/U1/U2 agent-run force grant is RETRACTED as not executable — no installed Orchestrator/Ship contract passes `--force` and both halt on exit 1, and `--force` is stateless so an operator force does not unblock an agent's own unforced run; replaced by BOOTSTRAP-A (a one-time operator-run entry path proven against installed agent text, with the branch-vantage error corrected: `pre_claim` short-circuits on `branch_ownership`, so a Stage-branch run yields `BRANCH_MISMATCH`, never `PREDECESSOR_NOT_SHIPPED`) plus BOOTSTRAP-B (new tasks T10/`165.011-T` and T11/`165.012-T` adding a version-controlled, exact-bound pre-claim bootstrap grant surface, an agent-consumable CLI flag, and a full-provenance force audit recording invocation, full observed payload, HEAD, manifest identity, token/predecessor, and the authorizing decision). Thread PRRT_kwDORzpWpM6h3Tgi: the audit's absolute no-write claim is narrowed to no backlog mutations and no migration-state/ledger writes, with the unconditional, observational, fail-open `pipeline-topology` telemetry emission explicitly allowed and its test assertions rewritten accordingly. Manifest 9 -> 11 items; `165.009-T` moved last behind its new T11 edge. PR REVIEW-FIX CYCLE 2 (staging PR #448, five same-contract-surface Copilot threads, 2026-09-13; content only, NO manifest/edge/size change — scope remains 10 executable tasks, 11 manifest items, and BOOTSTRAP-A steps B0/B1/B2, never U0/U1/U2). Thread PRRT_kwDORzpWpM6h3fqf: T10 at-most-once consumption gains a CONCRETE DURABLE ATOMIC MECHANISM (O_EXCL exclusive-create per-grant/per-label record under the gitignored `.autoharness/gates/bootstrap-grant-consumption/`, claimed before the force, audit emitted from the claimed record, fail-closed contention/replay/malformed/stale handling, operator-only recovery, containment, and an honestly stated per-clone scope bound); the undefined not-already-consumed phrasing is removed and T10 complexity is raised medium -> high (de-risked in place, not split). Thread PRRT_kwDORzpWpM6h3fq1: BOOTSTRAP-A B4 reverse-the-claim is REMOVED as unexecutable (backlogit exposes no active->queued transition) and replaced by a halt-with-173-S-active contract plus explicit operator remediation, with the supported and VERIFIED active->abandoned transition as the only alternative and no promise of requeue. Thread PRRT_kwDORzpWpM6h3frC: the strict-xfail/expectedFailure RED mechanism is REPLACED by a stdlib-only `expect_red(raises=, message_contains=)` helper, because canonical CI runs `python -m unittest discover -s tests` where a pytest xfail marker is inert and `unittest.expectedFailure` cannot constrain the reason. Thread PRRT_kwDORzpWpM6h3frF: the three-probe genesis rule (G2/G3/G4) admitted every value outside its three enumerations and is REPLACED by the SOLE-RECORD rule — genesis only when the candidate is the only shipment record across all live and archived records regardless of status or provenance, with missing/unrecognized status failing closed — and regression cases are added. Thread PRRT_kwDORzpWpM6h3frY: T6's reintroduced absolute zero-write assertion is REMOVED and narrowed to no backlog mutation and no migration-state/ledger write, with the pre-existing observational fail-open telemetry append explicitly allowed and positively tested. PR REVIEW-FIX CYCLE 3 (staging PR #448, three same-contract-surface Copilot threads, 2026-09-13; content only, NO manifest/edge/size/complexity/dependency change — scope remains 10 executable tasks, 11 manifest items, and BOOTSTRAP-A steps B0/B1/B2). Thread PRRT_kwDORzpWpM6h3ttF: T10 Deliverable 6h containment resolved only the CHILD under the RESOLVED root, so a root that itself symlinked outside the workspace still appeared contained, and the resolve-then-open re-walk left an intermediate-symlink-swap TOCTOU window; 6h is rewritten as 6h-1..6h-7 requiring the ROOT to resolve inside the resolved workspace, a descriptor-relative O_NOFOLLOW walk on POSIX, a reparse-point-checked walk with post-create st_dev/st_ino identity re-verification on Windows, capability-probe strategy selection and a fail-closed default with NO Path.resolve fallback; at-most-once (one O_EXCL create) and all 6a-6g semantics are preserved and seven containment tests are added. Thread PRRT_kwDORzpWpM6h3ttS: every claim that ``blocked`` is a member of the shipment status enum is RETRACTED — the current vocabulary is {queued, active, shipped, abandoned} and ``blocked`` is malformed legacy data; the status-agnostic sole-record cardinality rule is PRESERVED unchanged, but the ``blocked`` fixture is SPLIT so a LIVE record raises BacklogUnavailableError at reader time under existing malformed-input behaviour (never reaching unsequenced) while an ARCHIVED archived_status: blocked record counts as a disqualifying unclassifiable record and the candidate resolves to unsequenced. Thread PRRT_kwDORzpWpM6h3ttV: the BOOTSTRAP-A B6 direct Ship handoff is REMOVED as not executable — Ship Work Intake step 3 runs pre_claim unconditionally on a fresh invocation before any already-active state is interpreted, and the step-6 expected_status parenthetical confers no authority over step 3 — and is replaced by a checkpoint-mediated path: an operator-created schema_version 1, agent ship, status active checkpoint via backlogit checkpoint create --state-dump, then Orchestrator Step 0.0b recovery, explicit operator selection and restore confirmation, and Ship resuming from the recorded post-claim cursor instead of fresh Work Intake. Prior revision 4-6 notes retained in git history."
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
| Genesis | no edges, no declaration, **and G2 — sole record** (below) | pass | `genesis` |
| Unsequenced | no edges, no declaration, **G2 fails** (any other shipment record exists) | **block** `UNSEQUENCED_SHIPMENT` | `unsequenced` |

The `explicit` row's closure check is named only to describe what already happens
on that path. This plan does **not** touch it, and no task asserts over it
(`FD0CCB42` owns that surface exclusively).

#### Genesis conditions — the sole-record rule (PR review-fix cycle 2, thread `PRRT_kwDORzpWpM6h3frF`)

* **G1** — the candidate declares no `blocks` edges and carries no `dag-root`.
* **G2 — SOLE RECORD** — the candidate is the **only shipment record that exists
  in the workspace**, counting **live and archived records together**,
  **regardless of status and regardless of provenance**. Any other shipment record
  — whatever its status, recognized or not — disqualifies genesis.

**This replaces the cycle-2 three-probe form (G2 shipped / G3 nonterminal / G4
abandoned), which was a verified fail-open.** Cycle-2's G3 enumerated
the disqualifying nonterminal states as "`queued`/`active`", while G2 covered only
shipped-terminal records and G4 only abandoned ones — so **any value outside those
three enumerations appeared in no probe at all**. A workspace holding such a record
alongside an edge-less undeclared candidate satisfied G2, G3 and G4 simultaneously
and returned `genesis`: an unearned pass, in exactly the direction this feature
exists to close. Enumerating statuses is structurally fragile — every value the
vocabulary gains in future silently re-opens the same hole at a moment nobody is
looking. **Counting records is not**: "exactly one shipment record exists here" is
status-agnostic and cannot be widened by a later vocabulary change. It also reduces
the shared-snapshot surface from three facts to one, which strictly lowers the
divergence risk of §3.4.

> **Enum correction (PR review-fix cycle 3, staging PR #448, thread
> `PRRT_kwDORzpWpM6h3ttS` — ACCEPTED).** Cycle 2 illustrated the hole with a
> `blocked` shipment and asserted "the shipment status enum is {`queued`,
> `blocked`, `active`, `shipped`, `abandoned`}". **That assertion is false and is
> retracted.** Verified at this HEAD: the gate reader defines
> `_VALID_LIVE_SHIPMENT_STATUSES = frozenset({"queued", "active", "shipped",
> "abandoned"})` (`src/autoharness/gates/topology.py` L35), and backlogit's core
> declares exactly four `ShipmentStatus` constants — `queued`, `active`, `shipped`,
> `abandoned` — with `isValidShipmentTransition` returning false for anything else.
> **`blocked` is malformed legacy data on a shipment**, historically writable
> because `backlogit move` accepted unvalidated status writes and still advertised
> only because the `header-def` metadata catalog's shipment `status` enum is stale
> at five values (see
> `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`).
> **The fail-open finding and the sole-record replacement both stand** — and the
> hole was *wider* than cycle 2 described, since it admitted every unenumerated
> value rather than one named status. `blocked` remains the named regression
> fixture only because it is the malformed value this workspace can actually
> produce.

The cycle-1 rule ("no shipped-terminal shipment exists") remains **replaced** for
its own reason: in a workspace with many queued shipments and nothing yet shipped
it returned `genesis` for **every** edge-less shipment at once. Sole-extancy — now
expressed as sole-*record* — makes genesis a **cardinality-1** state that cannot be
true for two shipments simultaneously and ceases to be available once a workspace
holds a second shipment record of any kind, so a later-numbered candidate has no
genesis path and blocks as `unsequenced` until intent is recorded.

**Unclassifiable records fail closed.** A shipment record whose status is absent,
empty, whitespace-only, non-string, unparseable, or not a recognized member of the
current four-value vocabulary — including an archived record carrying an
unrecognized `archived_status` —
**still counts as a disqualifying record**. It is never skipped, never defaulted to
a benign value, and never treated as absent: a record that cannot be classified is
precisely the record whose sequencing significance is unknown, and discarding it is
the fail-open move. If the live or archived record set cannot be **enumerated** at
all, the evaluation raises `BacklogUnavailableError` rather than concluding
sole-extancy from a short or partial read.

**Live and archived malformed values take different paths — do not conflate them**
(cycle 3, same thread). A **live** queue-folder record whose status is outside the
recognized vocabulary never reaches four-state derivation: the reader already
raises `BacklogUnavailableError` on it (`topology.py` L553–563, *"missing or
unsupported status"*). An **archived** record is read via `_archived_status`, which
returns the value as an opaque lowercased string with no vocabulary validation, so
it is present, unclassifiable and therefore disqualifying — genesis is denied by
**cardinality**, and the candidate resolves to `unsequenced`. Both outcomes are
fail-closed; neither is `genesis`; and the existing reader behaviour is preserved
rather than special-cased.

| Workspace | Genesis? | Edge-less undeclared candidate |
|---|---|---|
| Exactly one shipment record, nothing else | yes | pass `genesis` |
| Several `queued`, nothing ever shipped | no | block `unsequenced` |
| Shipped history only as archived records | no | block `unsequenced` |
| Only an `abandoned` record in history | no | block `unsequenced` |
| **A LIVE `blocked` record present** | **n/a (fail closed at read)** | **`BacklogUnavailableError` — no verdict** |
| **An ARCHIVED `archived_status: blocked` record present** | **no** | **block `unsequenced`** *(the cycle-2 fail-open)* |
| **A LIVE record with missing/unrecognized status present** | **n/a (fail closed at read)** | **`BacklogUnavailableError` — no verdict** |
| **An ARCHIVED record with unrecognized `archived_status` present** | **no (fail closed)** | **block `unsequenced`** |
| Record set cannot be enumerated | n/a | `BacklogUnavailableError` |
| Any **archived-side** row above + `dag-root` on candidate | n/a | pass `declared_root` |

The sole-record count is a workspace-level fact computed **once per evaluation**
from a single snapshot inside the shared helper (§3.4) and handed to both gates.

The four states are total and mutually exclusive. `predecessor_source` is present
on **every** `shipment_readiness` payload — blocked and passed alike.

The `UNSEQUENCED_SHIPMENT` message must name the two remedies explicitly (record
the real `blocks` edge, or declare the shipment a root), so the block is never a
dead end; where genesis was disqualified, it also names **which record(s)**
disqualified it — id, live or archived, and the status as read.

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

`--phase audit_sequencing` is non-authorizing, never blocks, and never mutates
backlog or migration state.
For every edge-less shipment it reports the derived state, the raw
numerically-adjacent candidate the retired heuristic would have inferred, which
disqualifying record(s) denied genesis where the state is `unsequenced`, and the
remediation options available. It must **not** apply the reverse-dependency suppression
predicate.

**It is a pure report and nothing more (cycle 3; narrowed in PR review-fix cycle
1).** The audit computes from the workspace it reads and emits output. It performs
**no backlog mutation** — no item, feature, shipment, manifest, status, label, or
dependency write — and **no migration-state or ledger write**: no durable migration
record, no persisted audit artifact, no state file, no new file format, no
persistence subsystem inside the gate. The cycle-2 "durable, append-only migration
ledger" is **removed** — along with every persistence claim, every durable-artifact
requirement, and the field recording the remediation an operator *would later*
choose. That field described a decision that has not happened at audit time, so
the audit could only ever have recorded a guess or an empty slot.

**"Writes nothing" was false and is retracted (PR review-fix cycle 1, thread
`PRRT_kwDORzpWpM6h3Tgi`).** `_gate_pipeline_topology_command` calls
`_emit_pipeline_topology_telemetry` **unconditionally on every run**, appending a
structured tool-telemetry event to the workspace telemetry journal whenever
telemetry is enabled. `audit_sequencing` will emit that event exactly as
`pre_claim`, `post_claim`, `lifecycle`, and `ambient` do, so an absolute no-write
claim is unachievable and was never true of any phase. **The ordinary, pre-existing
telemetry emission is allowed and unchanged.** It is observational only and must
remain **fail-open** — the existing `except Exception` handler returns a warning
and never alters behaviour or exit code, and this work must not narrow, harden, or
make that fail-open contract load-bearing. The audit adds no new telemetry field,
no new journal, and no new emission site. Telemetry is **not** a migration record
and is never read back as authorization or state.

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

**Every task ends green.** New expectations land as **constrained RED** tests in the
harness task and are flipped to ordinary passing tests by the implementation
task that delivers the behaviour; tests that pin behaviour being removed are
re-expressed in the **same** task that removes the behaviour. No task may leave the
suite red for a successor to repair.

**Characterization vs. RED.** Behaviour that already exists is covered by
*characterization* tests that pass immediately (they lock in current behaviour so
the refactor cannot silently change it). Only genuinely new behaviour is written
as a failing expectation. Demanding a RED observation for existing behaviour would
be impossible to satisfy honestly, so it is not required anywhere below.

**RED mechanism — a narrow custom helper, not `xfail` and not
`unittest.expectedFailure` (PR review-fix cycle 2, thread `PRRT_kwDORzpWpM6h3frC`).**
This **replaces** cycle 3's "xfail-strict / `expectedFailure` pinned with
`raises=`/reason" instruction, which was not implementable in this repository.
Verified at this HEAD: canonical CI runs `python -m unittest discover -s tests`
(`.github/workflows/ci.yml`, whose own header records that "autoharness has no
ruff/pyright/pytest configured; the only real gates are the stdlib unittest suite
… and markdownlint"). Under `unittest` a `@pytest.mark.xfail(...)` decorator is
**inert** — it sets an attribute nothing reads — so the body runs, the expectation
raises, and **CI goes red**, directly contradicting "every task ends green".
`unittest.expectedFailure` does run under that runner and does fail the suite on an
unexpected success, but it **cannot constrain the reason**: it accepts *any*
exception and takes no `raises=` and no reason argument, so a fixture error, an
import error, an unregistered `--phase`, or a typo all register as "still red" —
the exact hazard cycle 3 set out to close.

Required instead: one small stdlib-only helper (e.g. `tests/support/red.py`)

```text
@expect_red(raises=<ExcType | tuple>, message_contains="<substring>", reason="<why>")
```

with three mandatory properties: (a) the expectation is satisfied — and the test
**passes** — only when the body raises an instance of `raises` whose *normalized*
message (`str(exc)`, whitespace-collapsed, stripped, casefolded) contains
`message_contains`; (b) **any other exception fails the test**, with a diagnostic
naming expected vs. observed and stating that this is a *wrong* failure, so a
broken fixture turns the suite red instead of masquerading as RED; (c) **no
exception at all fails the test as XPASS**, instructing the reader to flip the
expectation to an ordinary assertion — preserving the strictness that made
`xfail(strict=True)` desirable. The helper must be pure stdlib (`functools.wraps` +
`try`/`except`), must not import `pytest`, and must behave identically under
`python -m unittest discover -s tests` and under a local `pytest` run.
`assertRaises` is not a substitute: it cannot distinguish XPASS from a missing
behaviour and carries no "flip me later" intent.

**Simpler alternative, explicitly permitted.** Where the helper is awkward for a
particular expectation, that expectation may instead be authored **in the same task
as its implementation** — written red and turned green in one task and one commit —
**provided the RED observation is still recorded** (observed exception type and
message captured in that task's disposition notes before the implementation lands).
Either route is acceptable; leaving a genuinely unconstrained expectation is not.
**Every task ends green under both routes.**

**Task labels track task IDs (cycle 3).** The task numbering below is `T{n}` for
`165.00{n}-T`; there is no `T7`, because `165.007-T` is archived and descoped.
Cycle 2 left `165.008-T` labelled "T7" after the merge, which made the plan, the
review, and the backlog records disagree about which task was which.

| # | Task | ID | Kind | Size | Complexity | Depends on |
|---|---|---|---|---|---|---|
| T1 | Derivation test harness: characterization + constrained-RED matrix | 165.001-T | test | M | medium | — |
| T2 | Engine: four-state derivation, provenance, legacy-test re-expression | 165.002-T | impl | M | high | T1 |
| T3 | Sequencing audit phase (pure read-only report) + tests | 165.003-T | impl | M | medium | T2 |
| T4 | Advisory parity test matrix (characterization + constrained RED) | 165.004-T | test | S | medium | T2 |
| T5 | Engine: `dag-readiness` parity via shared derivation helper | 165.005-T | impl | M | high | T4 |
| T6 | CLI: provenance, remediation, and audit output + tests | 165.006-T | impl | S | low | T2, **T3** |
| T8 | Agent template sources **and** installed dogfood mirrors (atomic) | 165.008-T | docs | M | medium | T5, T6 |
| T10 | Pre-claim bootstrap grant surface + full-provenance force audit | 165.011-T | impl | M | **high** | T6 |
| T11 | Orchestrator + Ship bootstrap-grant consumption (sources **and** mirrors, atomic) | 165.012-T | docs | M | medium | T10, T8 |
| T9 | Gate documentation + audit/migration/rollback guide | 165.009-T | docs | M | low | T5, T6, **T11** |

**PR review-fix cycle 1 additions (staging PR #448, thread
`PRRT_kwDORzpWpM6h3Tgb`).** T10 and T11 are new. They exist because the bootstrap
authorization recorded in cycles 2–3 named forced gate invocations that **no
installed agent contract can perform** (§H6). T10 builds the grant surface; T11
makes the agents consume it. The labels intentionally break suffix correspondence
(`T10` = `165.011-T`, `T11` = `165.012-T`) because `165.010-T` is archived and its
ID may not be reused. `T9` is listed last because it now depends on `T11` and must
document the final contract; the shipment manifest order was reordered to match.

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
   characterization test and must **not** be written as a RED expectation.
5. **Label parsing does not currently raise (cycle 3 reclassification).** A
   shipment record carrying `labels: [dag-root, topology-gate]` is read
   **successfully today** and raises nothing. Verified against source:
   `ShipmentState` (L91–98) has no `labels` field and `topology.py` contains no
   reference to `labels` at all, so the field is simply not consulted. This is the
   **positive anti-regression** against ever validating labels with the artifact-ID
   validator, and it belongs here as a **passing characterization test** (former
   N7a). Marking it a RED expectation would have been wrong twice over: it
   asserts behaviour that already holds, and under any strict RED mechanism —
   `expect_red` included — it would
   **XPASS and fail the suite** the moment it ran.

**New expectations (constrained RED via `expect_red`; flipped by T2):**

1. Two numerically adjacent edge-less shipments are **not** blocked by numeric
   inference.
2. Closure evidence is **never** demanded for a merely numerically-adjacent
   non-predecessor.
3. `predecessor_source` is present and correct on a **passing** payload and on a
   **blocked** payload.
4. Declared root passes with `predecessor_source: declared_root`.
5. **Genesis, asserted per disqualifying record class** (PR review-fix cycle 2):
   (a) a workspace holding exactly one shipment record passes `genesis`; (b) a
   `blocked` record — **split by location** (PR review-fix cycle 3, thread
   `PRRT_kwDORzpWpM6h3ttS`): a **live** `status: blocked` record makes the reader
   raise `BacklogUnavailableError` before derivation runs (assert the raise, *not*
   `unsequenced`), while an **archived** `archived_status: blocked` record is a
   disqualifying unclassifiable record so the candidate is `unsequenced` — *the
   archived form is the cycle-2 fail-open this finding found, and the case that
   must fail against the retired three-probe rule*; (c) archived-only shipped
   history is **not** genesis; (d)
   several queued shipments with nothing ever shipped is **not** genesis for *any*
   of them — asserted over at least two candidates including a later-numbered one;
   (e) abandoned-only history is **not** genesis; (f) a record whose status is
   missing, empty, non-string, unrecognized, or whose `archived_status` is
   unrecognized is **not** genesis — **fail closed**, never skipped; (g) an
   enumeration failure raises `BacklogUnavailableError` rather than concluding
   sole-extancy from a partial read; (h) `dag-root` still passes as `declared_root`
   in each non-genesis workspace, proving the sole-record rule does not deadlock
   real roots.
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
Malformed *labels* are currently not validated at all → constrained RED (item 8
above). Writing the first as RED would be dishonest; writing the second as
characterization would assert behaviour that does not exist.

Every RED expectation above must be authored with xpect_red per the RED-mechanism
rule in §4: scoped to its specific exception type and normalized message, so a
fixture error or an unregistered-phase error cannot satisfy RED, and an XPASS fails
the suite.

Fixtures must make each state distinguishable — a fixture in which two states
would produce the same observation cannot assert either (vacuous-test learning).
Each disqualifying-record class is asserted independently so no composite fixture
can carry the sole-record rule vacuously.

### T2 — Engine change (165.002-T)

Implement §3.1: derive from `blocking_predecessor_ids` only; parse the record's
`labels` into a **validated, immutable `labels` tuple on `ShipmentState`** through
a labels-specific fail-closed validator, **never `_tuple_of_str`**, and derive
root classification from that tuple rather than storing a bare boolean (§3.2);
implement the four-state resolution with the **sole-record** genesis rule (§3.1);
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
   `audit_sequencing` numeric-candidate expectation**, written here as a
   *constrained RED* test via `expect_red` (the audit surface arrives in T3) and flipped green by
   T3. Stated as the **negation** of suppression: the multi-hop and
   forward-dependent configurations, where suppression would have hidden the
   candidate, must still yield a reported raw candidate.

**Retracted:** cycle 1 allowed suppression-only cases to become direct unit tests
of `_prior_shipment_id`. That would pin the retired, defective predicate as a live
tested contract and contradicts D3/F6, which require the audit to report the raw
candidate *without* suppression. Bulk deletion remains forbidden; any case with
genuinely no equivalent requires written rationale. Update the class docstring to
record the heuristic as retired history.

Flip T1's RED expectations to ordinary assertions. **Prove by test — not by
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
state, raw numeric-adjacency candidate, the record(s) that disqualified genesis, and
the remediation options available. **Emit that report and nothing else** — the
phase performs no backlog mutation and no migration-state/ledger write, owns no
durable artifact, and defines no file format. The cycle-2 migration-ledger
requirement is **removed** (§3.3); the external migration record is the
version-controlled commit history of the backlog records the operator edits, and
the rollback evidence is those commits and their diffs (§H4).

**Test scope, narrowed in PR review-fix cycle 1.** Tests must assert the audit
reports a candidate in the exact configuration where the suppression predicate
would have hidden it; that the audit never blocks or authorizes; and that it makes
**no backlog mutation and no migration-state/ledger write** — no file under the
backlog root created, modified, or deleted; no status, label, dependency, or
manifest change; no persisted audit artifact anywhere. **Do not assert "no file is
created or modified" in absolute terms**: the unconditional `pipeline-topology`
telemetry emission appends to the telemetry journal on every run when telemetry is
enabled, so that assertion is false by construction and would push an implementer
to suppress telemetry for this one phase and break parity with every other phase.
Instead assert that, with telemetry enabled, the event **is** emitted and the audit
output and exit code are identical to a telemetry-disabled run, and that a
telemetry failure during an audit run changes neither output nor exit code
(fail-open preserved).

**T3 also flips the constrained-RED audit expectations inherited from T2** (the
re-expressed historical directional cases). If any cannot be flipped green, the
audit has inherited the suppression predicate and T3 is not done.

### T4 — Advisory parity matrix (165.004-T)

Characterization for existing agreement; constrained RED for the new parity
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
* `genesis` — built on a **genesis-valid** fixture (the candidate is the *sole
  shipment record* in the workspace, live and archived counted together) and
  reported consistently with `pre_claim`'s pass. The narrowness-parity case is
  asserted over **two** disqualifier shapes — a second `queued` record, and an
  **archived** `archived_status: blocked` record (an unclassifiable value the
  retired three-probe rule admitted). The **live** `blocked` form cannot serve as a
  derived-state parity fixture — it fails closed at read time in both gates — so it
  is asserted separately as identical fail-closed behaviour across the two gates
  (PR review-fix cycle 3, thread `PRRT_kwDORzpWpM6h3ttS`).
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

The single sole-record genesis fact is computed **once** inside that helper from one
snapshot and handed to both gates; the advisory side must consume the **same
narrow** genesis rule, never a broader "nothing shipped yet" notion. State in the
task record whether the helper lives in `topology.py` or a new module. Exclude
policy-blocked shipments from `next_eligible`. `pre_claim` remains sole claim
authority.

### T6 — CLI output (165.006-T)

Surface `predecessor_source` and the selected predecessor IDs in JSON and human
output on blocked and passed paths; render the `UNSEQUENCED_SHIPMENT` remedy text
and the record(s) that disqualified genesis; render **audit-phase output** readably.
The audit rendering is **pure report rendering** — there is no ledger and no
persisted artifact to reference (§3.3), so the CLI displays only what the audit
computes. Changes are **additive** — no existing field is renamed or removed.
Assert in `tests/test_gate_pipeline_topology_cli.py`. **Retains dependencies on
both T2 and T3**: T2 supplies `predecessor_source` for the provenance
deliverables, and T3 supplies the audit payload that deliverable renders.

**Audit-render purity is scoped, not absolute (PR review-fix cycle 2, thread
`PRRT_kwDORzpWpM6h3frY`).** The cycle-1 form of this task required "an assertion
that the audit render path performs **no write** — no file created, no record
mutated". That is the *same absolute claim* PR review-fix cycle 1 had already
retracted from T3, `165-F`, T8 and T9 on thread `PRRT_kwDORzpWpM6h3Tgi`, and it is
false for the same verified reason: `_gate_pipeline_topology_command` calls
`_emit_pipeline_topology_telemetry` **unconditionally on every run of every
phase**, appending a telemetry event whenever telemetry is enabled. A test
encoding "no file is created" fails on any telemetry-enabled workspace or — worse —
pushes an implementer to suppress telemetry for this one phase, breaking parity
with `pre_claim`/`post_claim`/`lifecycle`/`ambient`. **The absolute assertion is
removed.** Assert exactly T3's contract and no more: (a) **no backlog mutation**;
(b) **no migration-state or ledger write**; (c) telemetry is **explicitly allowed
and positively tested** — with telemetry enabled the event *is* emitted while the
rendered output and exit code are identical to a telemetry-disabled run; (d) a
telemetry failure during a render changes neither output nor exit code (fail-open
preserved, not narrowed or made load-bearing). Reintroducing an absolute no-write
claim in this task is a regression of this finding.

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
their provenance values; **genesis is the sole-record rule** — genesis holds only
when the candidate is the *only* shipment record in the workspace, live and
archived together, regardless of status or provenance, so an agent must not expect
a second or later-numbered edge-less shipment to pass as `genesis` (and must not
restate the retired `G2`/`G3`/`G4` probe form); `pre_claim` is the sole
claim authority and `dag-readiness` is advisory/non-authorizing; **Ship must not
self-declare `dag-root`**, stated as an agent-contract rule enforced by review and
audit rather than by the gate (§3.2); and the audit phase is the migration path,
with a code-only rollback not undoing migrated data.

A source-versus-mirror **parity check is recorded in the task**, performed against
the final working tree before commit; drift found is fixed, not noted. Introduce no
unresolved template placeholder tokens, and keep markdownlint heading hierarchy
clean (P-008).

### T10 — Pre-claim bootstrap grant surface + full-provenance force audit (165.011-T)

**Added in PR review-fix cycle 1.** Build the mechanism the cycle-3 bootstrap
grant assumed already existed (§H6).

* **Grant record** at `.autoharness/bootstrap-grants/{shipment_id}.yaml` —
  deliberately outside the gitignored `.autoharness/gates|staging|metrics` trees,
  because a grant that cannot be committed cannot be reviewed. Fields:
  `schema_version`, exact `shipment_id`, `authorized_invocations` from the closed
  set {`orchestrator_pre_route`, `ship_pre_branch`, `ship_pre_claim`} (each
  consumable at most once, enforced by the durable consumption record below),
  `expected_token`, `expected_predecessor_id`,
  `manifest_digest`, `authorizing_decision`, `operator`, `expires_on_claim`.
* **Durable, atomic, at-most-once consumption (PR review-fix cycle 2, thread
  `PRRT_kwDORzpWpM6h3fqf`).** Cycle 1 said only that a label "is not already
  consumed" — naming no storage, no durability, no atomicity and no failure
  semantics, so it was satisfiable by an in-process set that resets every
  invocation, i.e. a zero-guarantee at-most-once. That phrasing is **removed** and
  replaced by a concrete mechanism:
  * **Exclusive creation is the claim.** A per-grant/per-label record at
    `.autoharness/gates/bootstrap-grant-consumption/{shipment_id}/{label}.json`,
    created with `os.open(..., O_CREAT | O_EXCL | O_WRONLY, 0o600)` — atomic on
    POSIX, `CREATE_NEW` on Windows — written and `fsync`'d before the force
    proceeds. No advisory lock, no lockfile-plus-rename, and **no read-then-write
    existence check** (a TOCTOU race, explicitly forbidden). The tree sits under the
    already-gitignored `.autoharness/gates/` prefix because it is node-local
    *runtime* state; the **grant** is the version-controlled, reviewable
    authorization, the **record** is the durable proof it was spent.
  * **Claim before force, always.** Evaluate unforced → apply every
    non-consumption match condition → only then claim → only if the claim succeeds,
    force. A non-matching grant must never burn a label. Claiming first is the
    fail-closed direction: a crash between claim and force spends a label without
    forcing (recoverable), whereas forcing first could force without recording the
    spend (unrecoverable).
  * **Record contents:** `schema_version`, `grant_digest` (SHA-256 over the grant
    file's exact bytes), `grant_path`, `shipment_id`, `label`, `phase`, `actor`,
    `session_id`, `head_sha`, `manifest_digest`, `blocking_token`,
    `inferred_predecessor_id`, `claimed_at`, `status` (`claimed` → `consumed`), and
    `audit_ref`.
  * **Contention and replay are fail-closed and indistinguishable.**
    `FileExistsError` → no force, ordinary exit 1, warning naming the record. Never
    wait, retry, poll, break, or steal a claim. **No TTL and no auto-expiry** — a
    TTL is at-most-once-*per-interval*, not at-most-once. A `grant_digest` mismatch
    is also fail-closed, which defeats "edit the grant to reset consumption".
  * **Crash states.** Crash after claim (before evaluation, or before the audit)
    leaves an intact `claimed` record carrying every field the audit would have
    carried, and later runs still fail closed. The `claimed` → `consumed` advance is
    a temp-file + `fsync` + `os.replace` in the same directory, so the record is
    never torn. **Recovery is operator-only and out-of-band**: no CLI reset flag
    exists, because such a flag would let an agent re-open an exhausted grant
    (P-005/P-001).
  * **The audit is emitted from the claimed record**, not recomputed from live
    state — recomputation could record a workspace state that was never the one
    authorized.
  * **Malformed/stale records fail closed**, i.e. are treated as *consumed*. This is
    the deliberate opposite of a malformed *grant* (treated as *no grant*); both
    defaults resolve toward **no force**.
  * **Containment and race-safe path resolution (PR review-fix cycle 3, thread
    `PRRT_kwDORzpWpM6h3ttF`).** `shipment_id` and `label` are validated against the
    artifact-ID pattern and the closed label set *before* any path is built;
    separators, `..`, NUL and drive/UNC prefixes are rejected with no filesystem
    call. Beyond that, the cycle-2 rule was insufficient in **two** ways and both
    are now closed. (1) It asserted only *child-under-resolved-root*, which is
    self-satisfying: if the consumption root itself (or `.autoharness/gates/`, or
    `.autoharness/`) is a symlink/junction out of the workspace, the child resolves
    *through* it and containment still passes. The **root must therefore itself
    resolve inside the resolved workspace**, asserted first and in addition to the
    child assertion. (2) `Path.resolve()` → `os.open` is a **TOCTOU re-walk**; an
    intermediate component can be swapped for a symlink in between. The claim is
    therefore issued **descriptor-relative**: on POSIX, each component is descended
    with `O_RDONLY | O_DIRECTORY | O_NOFOLLOW` from a workspace anchor fd and the
    record is created with `O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW` and
    `dir_fd=`; on Windows — where `O_NOFOLLOW` does not exist and `os.open` is not
    in `os.supports_dir_fd` — each component is `lstat`ed and rejected on
    `FILE_ATTRIBUTE_REPARSE_POINT` (catching directory symlinks *and* `mklink /J`
    junctions, which need no elevation), and the create is followed by an
    `fstat`/`lstat` `st_dev`+`st_ino` identity re-verification that fails closed on
    mismatch without deleting the file. Strategy selection is by **capability
    probe**, and if neither strategy is available the invocation **fails closed** —
    falling back to `Path.resolve()` + plain `os.open` is explicitly forbidden. The
    claim remains a **single** `O_EXCL` create, so at-most-once and every other 6a–6g
    semantic are unchanged, and a containment rejection never burns a label.
  * **Scope bound, stated honestly (accepted residual risk).** At-most-once holds
    **per workspace clone** — the tree is gitignored, so a fresh clone starts empty.
    Compensating bounds: `expires_on_claim`, the exact-token binding (which stops
    matching once the shipment leaves `queued`) and the manifest-digest binding. A
    cross-machine guarantee would need committed state or an external coordinator
    and is deliberately **not** invented here; T9 documents the bound.
* **Fail-closed exact matching.** A grant authorizes only when the label is listed
  **and its consumption claim succeeds**, the shipment id matches exactly, exit code is 1, the payload
  carries **exactly one** blocking check whose token equals `expected_token`, the
  derived predecessor equals `expected_predecessor_id`, and the current ordered
  manifest digest matches. Any mismatch — including an *additional* blocking check
  — means the grant does not apply and the ordinary exit-1 halt stands. A
  malformed grant is treated as **no grant** plus a warning; it never widens
  authority.
* **CLI.** Add `--bootstrap-grant-invocation {label}`. `--force` semantics are
  unchanged and remain the operator-only flag; the new flag is the agent-consumable
  path and cannot force a verdict with no matching grant. Combining the two is an
  argument error (exit 2).
* **Audit record.** `_audit_pipeline_topology_force` today records only
  `timestamp`, `actor`, `reason`, `mode`, `phase`, `target_shipment_id`, `token`,
  `message`. Add — additively, renaming and removing nothing — `invocation`,
  `observed_payload` (full pre-force result with every check's `details`),
  `head_sha`, `manifest` (id, ordered items, digest), `blocking_token`,
  `inferred_predecessor_id`, and `authorization` (source, decision, grant path,
  operator). This closes the second half of the review finding.
* **Telemetry parity, bounded.** Add `invocation`, `authorization_source`, and
  `inferred_predecessor_id` only. Do **not** serialize `observed_payload`,
  `head_sha`, or the manifest — the existing code comment excludes `result.message`
  from telemetry precisely because free text can carry raw frontmatter and
  filesystem paths, and bulk payload export falls under the same rule. Telemetry
  stays fail-open.
* **Tests.** No-grant behaviour byte-identical to today on both paths; exact-match
  grant forces and populates every audit field; each mismatch dimension
  independently fails to force (wrong shipment, unlisted label, already-claimed label,
  wrong token, wrong predecessor, stale digest, second blocking check); malformed
  grant is no grant; flag combination exits 2; telemetry failure never changes the
  exit code. **Consumption tests (cycle 2):** N ≥ 8 racing *processes* (not
  threads) on the same grant+label — exactly one forces, all others exit 1, exactly
  one record remains; sequential replay fails closed with the record byte-identical;
  a non-matching grant leaves **no** record behind and a later matching invocation
  still succeeds; crash injected between claim and evaluation, and between force and
  audit, each leave an intact `claimed` record and a fail-closed re-run; editing the
  grant after a spend fails closed on digest mismatch; truncated/unknown-version/
  missing-field/path-disagreeing records each fail closed without being overwritten;
  a far-past `claimed_at` still fails closed (guards against a TTL being added
  later); crafted `..`/separator/NUL ids and a symlinked consumption directory are
  rejected before any write; no code path unlinks, truncates or re-creates a record
  and no reset flag exists; with no grant present, no consumption directory is
  created at all. **Containment tests (cycle 3):** the consumption **root itself**
  linked out of the workspace (and the same at `.autoharness/gates/` and
  `.autoharness/`) is rejected with nothing written at either location and **no
  label burned** — every one of these passed the retired child-under-root rule, so
  each must fail against it; an intermediate component link and a pre-planted
  final-name symlink are rejected and never written through; a swap injected **at
  the validate/open seam** fails closed (a pre-planted link does not cover this
  case); the Windows variants are asserted over both a directory symlink and an
  `mklink /J` junction, with the junction case unconditional and the symlink cases
  skipped when the privilege is unavailable; and with both capability probes
  unavailable the invocation fails closed with no `Path.resolve()` fallback.

Depends on **T6**, which owns CLI audit/output rendering — serializing prevents two
tasks editing the same rendering surface.

### T11 — Orchestrator + Ship bootstrap-grant consumption (165.012-T)

**Added in PR review-fix cycle 1.** Without this task nothing consumes T10's grant,
because no installed agent contract passes a force or grant flag and both agents
halt unconditionally on exit 1. Template **sources and installed mirrors land in
one task and one commit**: `templates/agents/_orchestrator.agent.md.tmpl`,
`templates/agents/_ship.agent.md.tmpl`, `.github/agents/_orchestrator.agent.md`,
`.github/agents/_ship.agent.md`.

Three consumption sites, each bound to exactly one label: Orchestrator step 2a →
`orchestrator_pre_route`; Ship step 3 pre-branch run → `ship_pre_branch`; Ship
step 3 pre-claim run → `ship_pre_claim`. At each site: no grant file → invoke
exactly as today and the existing exit-1 halt is unchanged; grant file present →
invoke with this site's label only and let the CLI decide; exit 0 `forced: false`
→ ordinary pass; exit 0 `forced: true` → log `BOOTSTRAP_GRANT_CONSUMED`, surface
the audit path, proceed; exit 1/2 → halt exactly as today. Grant absence and grant
mismatch are indistinguishable in effect.

Stated prohibitions: **no agent may author, edit, or extend a grant** (an agent
writing its own grant has self-authorized a force — P-005/P-001), stated alongside
T8's "Ship must not self-declare `dag-root`" rule; the Orchestrator's
cursor-advance check evaluates a *different* shipment and is never a grant site;
the post-claim `CLAIM_NOT_OBSERVED` reclaim path's `pre_claim` re-run is never a
grant site; `post_claim`/`lifecycle`/`ambient` are never grant sites.

**Branch-vantage note (empirically verified this cycle).** `pre_claim` evaluates
`branch_ownership` before `shipment_readiness` and short-circuits, so a run from a
non-shipment, non-default branch returns a sole blocking check of
`BRANCH_MISMATCH`, never `PREDECESSOR_NOT_SHIPPED`. Because grants are bound to an
exact token, a `PREDECESSOR_NOT_SHIPPED` grant cannot match from a wrong-branch
vantage; the agent text records this and states that a `BRANCH_MISMATCH` block is
never grant-eligible.

Source/mirror parity is checked against the final working tree before commit and
drift is fixed, not noted. No unresolved placeholder tokens; markdownlint heading
hierarchy clean (P-008). Depends on **T10** (the surface consumed) and **T8**
(which edits the same four files first).

### T9 — Documentation and migration guide (165.009-T)

Document the contract, the four provenance values, the `UNSEQUENCED_SHIPMENT`
signal and its two remedies, the **sole-record genesis rule** — why absence of
shipped history alone is insufficient, and why the rule counts records instead of
enumerating statuses (the retired three-probe form admitted every unenumerated value; `blocked` is malformed legacy data, not a status) — the root-declaration surface — including
what its authority is and is not (§3.2) — and the `audit_sequencing` migration
procedure end to end. Explain why numeric adjacency was retired, citing the three
recorded defect cycles. Record the **data-ordered rollback posture** (§H4): what is
code-reversible, what is not, that the operator's own **migration commits and their
diffs** are the record used to reverse migrated data, the mandatory data-first
ordering, and the narrowed claim where migration was not committed. Document the
**bootstrap grant surface** shipped by T10/T11 — what a grant is, where it lives,
that it is operator-authored and review-gated, that no agent may write one, the
exact-match bounds, that a grant is `pre_claim`-only and at-most-once per named
site, **how that at-most-once is enforced** (an exclusive-create consumption record
claimed before the force, with the audit emitted from it), and its **honest scope
bound** — at-most-once holds per workspace clone, a fresh clone starts with no
consumption state, and the compensating bounds are `expires_on_claim` plus the
exact-token and manifest-digest bindings. Document that a second attempt fails
closed with the ordinary exit 1 and is never retried or stolen, that there is no
TTL, that editing the grant does not reset consumption (digest binding), that a
malformed record is treated as *consumed* while a malformed grant is treated as *no
grant* — both resolving toward no force — and that recovery from a crashed claim is
an operator-only out-of-band act with no CLI reset flag by design. Cross-reference the decision, this plan, and the committed intake bug report.
Now also depends on **T11**, so the documentation describes the final agent
contract rather than an intermediate one.

## 5. Risks

| Risk | Mitigation |
|---|---|
| Silent fail-open for prior numeric-reliant workspaces | Unsequenced state blocks in any genesis-disqualified workspace (§3.1); audit phase migrates intent (T3) |
| Genesis granted too broadly, becoming a back-door fail-open | **Sole-record** genesis rule (§3.1): the candidate must be the ONLY shipment record in the workspace, live and archived together, regardless of status or provenance; an unclassifiable status disqualifies fail-closed; each disqualifying record class asserted independently (T1) |
| `labels` parsed with the artifact-ID validator, hard-failing every labelled record | Labels-specific fail-closed validator required (§3.2); positive reader-level anti-regression as a **characterization** test (T1) |
| Blocking posture deadlocks legitimate roots | Declared-root state plus genesis bootstrap; block message names both remedies and the disqualifier |
| Ship self-declares a root to unblock itself | Declaration authority is operator/Stage; the label is a committed, diffable, review-gated record and provenance makes each pass attributable; T8 states the prohibition in both sources and mirrors. **Not mechanically enforced** — see §3.2 and H5 |
| A task leaves the suite red | Constrained-RED harness flipped by its implementer; legacy-test re-expression atomic with removal (T2); T2's audit expectations land as constrained RED and are flipped by T3. The RED mechanism is a stdlib helper, so it behaves identically under canonical `unittest` CI — a pytest `xfail` marker would have been inert there and left CI red |
| **A RED expectation passes for the wrong reason, or XPASSes** | ``expect_red`` matches only the named exception type and normalized message, fails on any other exception, and fails on XPASS (§4); behaviour that already exists is characterization, never RED (T1 items 4–5) |
| Advisory/authoritative divergence recurs | Shared **derivation** helper (T5) with one-snapshot genesis facts plus a state-parity matrix (T4) |
| Audit inherits the suppression defect | T3 reports raw candidates, asserted by the expectations T2 authors and T3 flips |
| **A read-only gate phase acquires a write path** | T3 emits a report only; no ledger, no durable artifact, no file format (§3.3); tests assert no backlog mutation and no migration-state/ledger write, while allowing the pre-existing observational, fail-open telemetry emission |
| Template/installed-copy drift | T8 updates sources and mirrors in one commit and records a parity check; no intermediate window exists |
| Rollback assumed code-only, stranding migrated edges/labels | Documented data-first rollback ordering against the operator's version-controlled migration commits and diffs (T9, H4) |
| Scope creep into closure evidence | Descoped to `FD0CCB42`, which owns it **exclusively**; no task reads, evaluates, or asserts parity over closure evidence, and no acceptance criterion references it |

## 6. Quality Criteria

* Genuinely new behaviour lands as a failing expectation before implementation;
  existing behaviour is characterized, not faked as RED, and every RED expectation
  marker is constrained so an incidental error cannot satisfy it.
* Every task ends with a green suite.
* `pre_claim` remains sole claim authority in code, output, templates, and docs.
* The `audit_sequencing` phase performs no backlog mutation and no
  migration-state/ledger write; the ordinary `pipeline-topology` telemetry emission
  is unchanged, observational, and fail-open.
* A bootstrap grant is operator-authored, version-controlled, exact-bound, and
  `pre_claim`-only; no agent may author one, and a missing grant is
  indistinguishable in effect from a non-matching one.
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
| F5 | A task ends red because test disposition trails the behaviour change | RED-expectation flip and legacy re-expression both occur inside the task that changes behaviour; T2's audit expectations are constrained RED until T3 |
| F6 | Retirement silently inherits the unfixed forward-dependent defect | T2 must **prove** claim-path moot-ness by test, with **no deferral option** — residue blocks the task and the shipment; T3 forbids the audit from inheriting the suppression predicate |
| F7 | A new config surface is added without schema versioning discipline | No config key is added at all (D2); the schema surface does not exist to mutate |
| F8 | Installed dogfood copies drift from template sources | Sources and mirrors land in **one task and one commit** (T8) with a recorded parity check; the cycle-1 dependency-only split is reversed because it scheduled drift rather than preventing it |
| F9 | Closure-gate weakening sneaks in as a way to unblock `163-S` | No task touches closure semantics; the defect is descoped to `FD0CCB42` with an explicit no-weakening, no-competing-artifact constraint |
| F10 | Parity tests pass vacuously | T4 is total over the four derivation states and carries no dimension that cannot apply to them; T1 asserts each disqualifying-record class independently with distinguishable fixtures |
| F11 | Genesis re-entered through a back door (archiving, abandonment, a malformed-legacy ``blocked`` record, an unrecognized status, or a populated-but-unshipped workspace) | Sole-record genesis rule computed from one snapshot — any other shipment record of any status disqualifies, and an unclassifiable record disqualifies fail-closed (live malformed values fail closed at the reader instead) — with per-record-class tests |
| F12 | `labels` validation reuses artifact-ID syntax and bricks the gate | Labels-specific validator mandated in §3.2 and T2, with a positive reader-level anti-regression **characterization** test |
| F13 | A RED expectation is satisfied by a setup/collection/unknown-phase error, or XPASSes because the behaviour already exists | ``expect_red`` constrains RED to a named exception type and normalized message, fails on any other exception, and fails on XPASS (§4); the label-parse anti-regression reclassified to characterization (T1) |
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
shipment record is also in this posture, by design (sole-record rule, §3.1).

**Also accepted (PR review-fix cycle 2): bootstrap-grant at-most-once is a
per-workspace-clone guarantee, not a global one.** The consumption record tree is
gitignored node-local runtime state, so a fresh clone of the repository starts with
no consumption state and could in principle re-spend a label. This is bounded by
`expires_on_claim`, by the exact-token binding (which stops matching the moment the
shipment leaves `queued`), and by the manifest-digest binding, all of which drift as
the shipment progresses. A cross-machine guarantee would require committing
consumption state — letting a merge conflict resurrect or destroy a spend — or an
external coordinator; both were judged worse than the stated bound, so neither is
invented here. T9 documents the bound rather than implying a stronger one.

**Also accepted (cycle 3): `dag-root` is not mechanically enforced.** Any actor who
can commit to the repository can apply the label, and the gate neither detects nor
prevents that. The declaration is a version-controlled, review-gated statement
inside the repository trust boundary — auditable through diffs and through
`predecessor_source: declared_root`, but **not a security boundary** and not
permission-checked. Mechanical enforcement would require a backlogit-side
permission model, which is outside this shipment (§3.2).

### H6 — Bootstrap disposition carried into execution (decision D6)

**Rewritten in PR review-fix cycle 1 (staging PR #448, thread
`PRRT_kwDORzpWpM6h3Tgb`). The cycle-3 formulation is retracted.**

`173-S` is blocked by the very defect it fixes: under current code its absent edges
cause `172-S` to be synthesised as a predecessor. Cycles 2–3 recorded an
authorization for "exactly three audited forced `pre_claim` invocations" performed
**by the Orchestrator and Ship** (U0/U1/U2). **No installed agent contract can
perform them**, so that grant was never executable:

* `_orchestrator.agent.md` step 2a and `_ship.agent.md` step 3 both invoke
  `autoharness gate pipeline-topology ... --phase pre_claim --json` with **no
  `--force`**, and both state that exit 1/2 **halts** — "never inferred, never
  fail-open".
* No agent template or installed mirror mentions `--force` for this gate anywhere.
  The only agent-visible force provision is for a *different* gate
  (`copilot-review`, `_ship.agent.md` L526–527).
* The shipment record itself forbids an agent self-authorizing a force.
* `--force` is **stateless**: an operator-run forced invocation exits 0 for that
  process and appends an audit line; it does not change the verdict any agent's own
  subsequent **unforced** run computes. Operator force followed by ordinary routing
  unblocks nothing.

The second half of the finding is also accepted: `_audit_pipeline_topology_force`
records only `timestamp`, `actor`, `reason`, `mode`, `phase`,
`target_shipment_id`, `token`, `message` — no invocation label, no full observed
payload, no HEAD SHA, no manifest identity, no explicit predecessor field, no
authorizing-decision reference. T10 closes that gap.

**No retroactive authorization.** T10/T11 are shipped *by* `173-S`; their surface is
not installed until `173-S` merges, and the claim necessarily precedes that merge.
A future code change cannot authorize an earlier claim, and no artifact in this
feature may say otherwise. The two mechanisms below are separate and must not be
conflated.

#### BOOTSTRAP-A — one-time operator-run entry for `173-S` (executable today)

Performed by the **human operator**, not by any agent, using `--force` exactly as
the CLI documents it ("Operator-only bypass of a failing gate. Audited."). Decision
D6 is its authorization.

**Vantage correction (empirically verified this cycle; cycle 3 got this wrong).**
`pre_claim` evaluates `branch_ownership` before `shipment_readiness` and
short-circuits. Observed at this HEAD: from `chore/stage-173-S` the sole blocking
check is `branch_ownership`/`BRANCH_MISMATCH` and `PREDECESSOR_NOT_SHIPPED` is
never reached; from `main` and from the canonical `173-S` shipment branch the sole
blocking check is `shipment_readiness`/`PREDECESSOR_NOT_SHIPPED` with
`details.predecessor_id: "172-S"`. Cycle-3 validity condition 3 named the **Stage
branch** as the required HEAD, which would have forced past a `BRANCH_MISMATCH` D6
never authorized. Corrected: B0/B1 run from `main`, B2 from the shipment branch,
never from a Stage branch.

| Step | Vantage | Action |
|---|---|---|
| B0 | `main` | Run `pre_claim` **unforced**, verify conditions 1–6, then re-run with `--force` (mirrors the Orchestrator route-to-Ship site) |
| B1 | `main` | Same verify-then-force sequence (mirrors Ship's pre-branch site) |
| B2 | `173-S` shipment branch (operator creates it) | Same verify-then-force sequence, immediately before the claim (TOCTOU narrowing) |
| B3 | `173-S` shipment branch | `backlogit shipment claim 173-S` |
| B4 | `173-S` shipment branch | `--phase post_claim` **unforced**; must exit 0. No force is authorized at `post_claim`. **On a non-zero verdict the operator halts with `173-S` left `active`** — see the B4 failure contract below |
| B5 | `173-S` shipment branch | Commit the durable evidence record (below) |
| B6 | `173-S` shipment branch | Operator creates a **ship-owned checkpoint**, then invokes **Orchestrator recovery**; Ship resumes from the recorded post-claim cursor (see below) |

**B4 failure contract — halt with `173-S` left `active`; there is no automatic
reversal (PR review-fix cycle 2, thread `PRRT_kwDORzpWpM6h3fq1`).** The cycle-1
wording said the operator "halts and reverses the claim". That promised an
operation that **does not exist**. Verified against the installed tool at this
HEAD: `backlogit shipment` exposes exactly `add`, `claim`, `create`, `get`,
`list`, `return-blocked`, `ship` — there is no `unclaim`, no `release`, no
`abort`, and no command or flag performing an `active` → `queued` transition. The
current shipment status vocabulary is {`queued`, `active`, `shipped`, `abandoned`}
(corrected in PR review-fix cycle 3, thread `PRRT_kwDORzpWpM6h3ttS`: cycle 2 wrote
this as a five-value enum including `blocked`, which is malformed legacy data, not
a status — the argument is unaffected);
`queued` is reachable only as the create-time default, never as a transition *out
of* `active`. A bootstrap contract whose failure branch terminates in an
unexecutable step — at the exact moment the workspace sits half-entered — is worse
than having no failure branch at all.

The executable contract: on any non-zero B4 verdict the operator **halts
immediately**; `173-S` **remains `active`**; B5 and B6 are not performed; Ship is
not invoked; and no forced re-run is attempted (BOOTSTRAP-A's force authority
already expired on the successful B3 claim). The operator records the failing
payload verbatim and then performs **explicit remediation**:

* **(a) Diagnose and converge — the expected path.** A non-zero `post_claim` after
  a successful claim means the workspace holds a condition the gate rejects (most
  plausibly a second `active` shipment — a P-001 single-active violation that
  predates or races this entry). Resolve *that* condition, re-run B4 **unforced**
  until it exits 0, then resume at B5. `173-S` stays `active` throughout; this is a
  forward fix, not a rollback.
* **(b) Abandon — only if the entry must not proceed at all.** `active` →
  `abandoned` *is* supported (`abandoned` is in the status enum, reachable via
  `backlogit update 173-S --status abandoned`). The operator **must verify** it by
  re-reading the record (`backlogit shipment get 173-S`) and confirming
  `status: abandoned`, recording observed before/after status. **Abandonment is
  terminal and is not a requeue**: it does not return `173-S` to `queued` and does
  not make it re-claimable, and under this feature's own sole-record genesis rule an
  abandoned record permanently disqualifies genesis in this workspace. Choosing (b)
  means the scope must be re-shipped under a **new** shipment record, as its own
  work unit with its own authorization.

**No artifact in this feature may promise automatic reversal, automatic requeue, or
any `active` → `queued` transition.** No agent performs any part of this
remediation: BOOTSTRAP-A is an operator path end to end, and a halt inside it hands
control to the operator, never to Ship or the Orchestrator.

**Handoff at B6 — checkpoint-mediated, not direct (PR review-fix cycle 3, thread
`PRRT_kwDORzpWpM6h3ttV`).** The cycle-1 B6 told the operator to invoke Ship
directly and to *state* that Ship runs neither step-3 `pre_claim` invocation nor
the step-5 `post_claim` verification. **That path is not executable and is
retracted.** Ship's Work Intake **step 3 is unconditional for a fresh invocation**
(`_ship.agent.md` L226–257): it opens *"Before claiming (the first workspace
mutation)"* and runs `pre_claim` before any branch/worktree creation and again
immediately before the step-4 claim, with **no already-claimed branch anywhere in
the step**. A fresh Ship invocation therefore evaluates `pre_claim` against an
already-`active` `173-S` and halts under its own *"never inferred, never
fail-open"* clause, long before reaching the step-6 text. An operator instruction
cannot suppress a step Ship runs unconditionally. The step-6
`expected_status: queued` *"(or `active` if already claimed)"* parenthetical
governs **only the `expected_status` argument at step 6** and confers no authority
over step 3; every claim that it, or direct invocation, authorizes skipping
`pre_claim` is **false and retracted**.

The executable replacement **enters Ship at a later cursor** so that fresh Work
Intake is never the entry point:

1. **B6a** — the operator creates a **ship-owned active checkpoint** through the
   official operation, `backlogit checkpoint create --state-dump '{...}'`. The V1
   top level is a **closed** namespace (`schema_version`, `agent`, `session_id`,
   `phase`, `status`, `created_at`, `updated_at`, `context`, `progress`,
   `resume_hint`); `agent` must be exactly `ship`; `status: "abandoned"` and the
   reserved `disposition*` fields are rejected at create; `context` is the **open**
   counterpart and carries `shipment_id: "173-S"`, `feature_id: "165-F"`, the
   shipment `branch`, the B5 `bootstrap_evidence_path`, the
   `observed_manifest_status` read at B3, and `authorizing_decision: "D6"`. The
   `resume_hint` records that B3/B4 are complete and that Ship must resume at step 6
   rather than re-entering steps 1–5.
2. **B6b** — the operator invokes **Orchestrator Step 0.0b** recovery, which
   enumerates all checkpoint summaries with no filter, fails closed first on any
   validation/quarantine anomaly, and routes owner-exclusively — `agent: ship`
   invokes the Ship subagent under Ship's own protocol (P-001).
3. **B6c** — the operator **explicitly selects** that checkpoint by filename (no
   auto-pick, ever) and **explicitly confirms** restore and the bounded prune.
4. **B6d** — Ship restores via `get_checkpoint` and, per its own contract,
   *"resume[s] from the recorded phase instead of restarting execution from
   scratch"*. Work Intake (Step 0.5) is continued to **only on the zero-candidate
   path**, which this is not, so step 3 is **not reached** — never skipped.
5. **B6e** — only after a confirmed successful resume does Ship
   `resolve_checkpoint` that single ownership-matched checkpoint.

Any invalid, ambiguous, torn or unreadable checkpoint **fails closed to operator
handoff**; there is no fresh-start fallback, because a fresh start is exactly the
outcome that lands Ship back on the unconditional step-3 `pre_claim`. The
checkpoint is an **entry cursor, not an authorization**: BOOTSTRAP-A's force
authority already expired at B3, the B5 commit remains the authorization of record,
and no agent-side force, grant or gate bypass is authorized anywhere in B6.

**This is not an exemption path.** `_orchestrator.agent.md` (L245–247) and
`_ship.agent.md` (L232–234, L297–299) carry "Bootstrap exemption" notes that skip
the topology gate **while the gate is not yet installed**. It *is* installed here,
so those notes are inapplicable by their own stated condition and must never be
cited to skip a `pre_claim` evaluation for `173-S`. BOOTSTRAP-A does not skip the
gate — it runs the gate unforced at every step and forces only a verified,
condition-matched block.

**Durable evidence (B5).** `.autoharness/gates/` is **gitignored** in this
repository, so the force audit log is local-only and is not by itself reviewable
authorization evidence. The operator transcribes the three unforced pre-force JSON
payloads verbatim, the HEAD SHA at each invocation, the 11 ordered manifest item
IDs, the blocking token, the inferred predecessor `172-S`, the B4 result, and
decision D6 into a version-controlled record committed on the shipment branch at
`docs/bootstrap/2026-09-13-173-S-bootstrap-evidence.md`. **That commit is the
durable authorization record.**

**Why B6 honours the currently installed contracts** (each proven against installed
text, not asserted; rewritten in PR review-fix cycle 3):

* The Orchestrator's step-2a gate is a precondition of *the Orchestrator routing* a
  queued candidate to Ship. B6b invokes Step 0.0b recovery, which runs before Step 0
  State Assessment and routes a checkpoint to its owner, so step 2a is **not
  reached** — not skipped, waived, or exempted.
* Ship's Work Intake **step 3 pre_claim and step 4 claim are unconditional for a
  fresh invocation** — that is precisely why direct invocation failed and why entry
  is now via recovery. On the checkpoint path Ship resumes from the recorded phase,
  so Work Intake is never the entry point and step 3 **never begins**.
* Ship's recovery contract states verbatim that on operator-confirmed restore it
  *"[r]esume[s] from the recorded phase instead of restarting execution from
  scratch"*, and continues to Work Intake **only** on the zero-candidate path.
* Ship's step 5 states verbatim that post-claim verification "applies only when a
  shipment was claimed in step 4". Ship claims nothing here; the operator performed
  the equivalent at B4, unforced.
* Ship's step 6 intake reconciliation directs `mode: pre` with
  `expected_status: queued` "(or `active` if already claimed)". This supplies the
  **`expected_status` argument only** — it is *not* authority to skip step 3. The
  value Ship uses is the `observed_manifest_status` restored from the checkpoint
  context; a **mixed** manifest means Ship skips that check per its own Scope note
  rather than passing a value it would classify `status-mismatch`.
* Ship's step 1a `SHIPMENT_STATE_INCONSISTENT` halt fires only when the record is
  `queued` while a manifest task is `active`/`done`. After B3 the record is
  `active`, so the condition cannot be met whatever the claim did to task statuses.
* Ship's step 1 P-001 gate holds: `173-S` is the sole active release unit, confirmed
  unforced at B4.
* The checkpoint is written through the **official create operation** with a
  schema-valid V1 payload and domain data nested under the open `context` object,
  per the installed Checkpoint Payload Contract — never hand-written.
* **No agent forces, bypasses, or reinterprets any gate, and no agent
  self-authorizes.** Every forced invocation (B0/B1/B2 only) is a human act on the
  operator-only flag, and that authority expired at B3.

**Per-invocation validity conditions for B0/B1/B2** (checked on the *unforced* run;
any failure voids the authorization and the operator halts): (1) exactly one
blocking check, token `PREDECESSOR_NOT_SHIPPED` — any second check or other token,
including `BRANCH_MISMATCH`, `PRECLAIM_ACTIVE_SHIPMENT_PRESENT`,
`SHIPMENT_STATE_INCONSISTENT`, `TARGET_NOT_CLAIMABLE`, `PREDECESSOR_STATE_AMBIGUOUS`,
`UNSEQUENCED_SHIPMENT`, any closure-evidence block, or any secrets finding, voids
it; (2) `details.predecessor_id` is exactly `172-S`; (3) correct vantage per the
table; (4) HEAD contains the merged PR #448 correction set and the live manifest
matches the 11 stored items exactly; (5) zero active shipments and `173-S` still
`queued`; (6) the forced run is recorded per B5.

**Bounds.** Exactly three forced invocations (B0/B1/B2), `173-S` only, `pre_claim`
only, bound to token `PREDECESSOR_NOT_SHIPPED` and predecessor `172-S` only.
Authority expires on the earlier of the successful B3 claim or any condition
mismatch. A fourth forced invocation is unauthorized, including the post-claim
`CLAIM_NOT_OBSERVED` reclaim path's `pre_claim` re-run, which runs unforced and
halts to the operator if it blocks. `--force` semantics are unchanged; no precedent
and no broader authority.

#### BOOTSTRAP-B — product behaviour shipped by `173-S` (future migrations only)

T10 (`165.011-T`) and T11 (`165.012-T`), specified in §4. A version-controlled,
operator-authored, review-gated grant; fail-closed exact matching on shipment id,
token, predecessor, manifest digest, and an at-most-once invocation label; an
agent-consumable CLI flag; and a full-provenance audit record. Agents consult the
grant before invoking the gate and otherwise behave exactly as today — a missing
grant and a non-matching grant are indistinguishable, and both halt. This applies
to **future** self-hosted migrations, never to `173-S`'s own claim.

**Self-liquidation (unchanged).** `173-S` carries `labels: [dag-root]`, so once T2
lands it derives `predecessor_source: declared_root` and passes `pre_claim`
natively — no force, no grant — on every subsequent evaluation.

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

**PR review-fix cycle 1 (2026-09-13).** Two Copilot review threads on staging PR
#448 were resolved against this plan; both were accepted as valid same-contract-surface
findings and applied here in revision 5. This is a **PR review-fix cycle**, distinct
from the four completed plan-review cycles, and consumes none of them. The
verification record is the "PR Review-Fix Cycle 1" section of
`docs/reviews/2026-09-12-dag-authoritative-predecessor-derivation-plan-review.md`:
**0 P0, 0 P1**.

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
