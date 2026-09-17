---
title: "Closure-evidence naming contract: single source of truth, rewired consumer, write-time validation, composed pinning test"
description: "Implementation plan reconciling the closure-evidence producer/consumer naming contract via a single authoritative contract module, a rewired pipeline-topology closure reader with distinguishable discovery diagnostics, a write-time validation gate, atomic producer-spec reconciliation across template and installed mirror, and a composed producer/consumer state-machine test — unblocking 162-S/174-S closure recognition and therefore 163-S, with zero closure artifacts modified."
doc_type: plan
source: docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md
date: 2026-09-17
status: reviewed
revision: 2
revision_note: "Revision 2 — plan-harden applied (5/5 hardening signals assessed, 3 present), then plan-review cycle 1 returned PASS_WITH_CONDITIONS and its 2 P1 + 3 P2 in-scope findings were resolved in place. See `## Plan Hardening` and `## Plan Review`."
source_decision: docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md
source_bug_report: docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md
source_stash_id: FD0CCB42
stash_ids:
  - FD0CCB42
prior_learnings:
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
linked_review: docs/reviews/2026-09-17-closure-evidence-naming-contract-plan-review.md
tags:
  - "closure"
  - "contract-drift"
  - "pipeline-topology"
  - "producer-consumer"
  - "fail-closed-design"
---

# Closure-Evidence Naming Contract — Implementation Plan

Source decision: `docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md`
(Option C adopted; decisions **D1**-**D9** are binding on this plan and are
referenced by ID throughout).

## Problem Frame

`FilesystemTopologyReaders.closure_complete()`
(`src/autoharness/gates/topology.py:714-725`) discovers post-merge closure
evidence with a single hard-coded glob:

```python
matches = sorted(closure_dir.glob(f"{shipment_id}-*-post-merge-closure.md"))
if not matches:
    return None
```

The `operational-closure` skill — in both the template
(`templates/skills/operational-closure/SKILL.md.tmpl:23`) and the installed
dogfood mirror (`.github/skills/operational-closure/SKILL.md:23`) — documents its
output as `{DOCS_CLOSURE}/{YYYY-MM-DD}-{slug}-closure.md`. No filename satisfies
both. Discovery is filename-first, so a conforming producer output is never
opened, and the reader's `None` is consumed by
`_shipment_readiness_check` (`topology.py:1866-1882`) as
`PREDECESSOR_CLOSURE_INCOMPLETE`.

Verified in this workspace, read-only, 2026-09-17:

| Shipment | Closure artifact present | `closure_complete()` | Effect |
|---|---|---|---|
| `162-S` | `docs/closure/2026-09-11-162-s-154-f-closure.md` (valid, `READY`, `done`) | `None` | **blocks `163-S`** |
| `174-S` | `docs/closure/2026-09-16-174-s-166-f-closure.md` | `None` | blocks any future dependent |
| `173-S` | both namings (ID-anchored authored as a `supersedes:` repair) | `True` | masked by a hand repair |
| `160-S`, `161-S` | ID-anchored only | `True` | unaffected |

`autoharness gate pipeline-topology --mode manual --shipment 163-S --phase pre_claim --json`
returns `exit_code: 1`, `token: PREDECESSOR_CLOSURE_INCOMPLETE`,
`details.predecessor_source: "explicit"`, `details.closure_complete: null`.
Predecessor derivation is correct; only discovery fails.

## Requirements Trace

| # | Requirement (decision / source-report criterion) | Implementation unit(s) |
|---|---|---|
| RQ-1 | `closure_complete("162-S")` is `True` from the committed tree with **zero** closure-artifact changes; `163-S` no longer blocks on `PREDECESSOR_CLOSURE_INCOMPLETE` (D3, D8; criterion 1) | U1, U2, U7 |
| RQ-2 | The filename contract is stated in exactly one machine-readable place; producer and consumer both derive from it (D1; criterion 1/2-naming half) | U1, U5, U9 |
| RQ-3 | Canonical WRITE pattern is `{DOCS_CLOSURE}/{shipment_id}-{feature_id}-post-merge-closure.md` (D2) | U1, U5, U6 |
| RQ-4 | RECOGNIZED READ set is permanent, closed, and exactly two anchored patterns; ID matching is delimiter-anchored and case-insensitive (D3) | U1, U8 |
| RQ-5 | Discovery resolves deterministically for zero-, one-, and multi-match (D5; criterion 4) | U1, U2, U7 |
| RQ-6 | Absent / unrecognized-name / invalid-metadata are separately diagnosable; the unrecognized case names the candidate path found and the pattern expected (D4; criterion 5) | U2, U3 |
| RQ-7 | Write-time validation fails a non-conforming artifact at authoring time, naming the offending field or path (D6; criterion 3) | U4, U5 |
| RQ-8 | Producer spec reconciled in template **and** installed mirror atomically (D1, R4) | U5 |
| RQ-9 | Ship agent references aligned in template **and** installed mirror atomically (D1, R4) | U6 |
| RQ-10 | A composed test drives the documented producer path into the real consumer reader and fails if either side changes alone (D7; criterion 6) | U7 |
| RQ-11 | Regression coverage for the three historical failure shapes plus the ID-collision hazard (criterion 7, R2) | U8 |
| RQ-12 | A non-drift guard ties documented pattern text to the code constant (R8; criterion 1) | U9 |
| RQ-13 | The gate remains fail-closed: validity predicate byte-unchanged, malformed frontmatter still raises (D3, R1, R3; criterion 6, non-goals) | U2, U8 |
| RQ-14 | Zero files under `docs/closure/` are created, renamed, edited, or deleted (D8) | verification step (all units) |

## Implementation Units

Each unit satisfies the 2-hour rule (< 3 production files, < 5 functions, < 4
test scenarios), width isolation (a single domain per unit), and produces an
atomic verifiable milestone.

### U1 — Closure-evidence contract module *(domain: Python source)*

**Files**: `src/autoharness/gates/closure_contract.py` (new),
`tests/test_closure_contract.py` (new).

**Changes**

* `CANONICAL_CLOSURE_FILENAME_TEMPLATE` — the single authoritative write pattern
  string (D2), plus `CANONICAL_CLOSURE_PATTERN_DOC` holding the exact
  human-readable pattern text that the producer skill files must quote verbatim
  (consumed by U9).
* `RECOGNIZED_CLOSURE_PATTERNS` — an ordered, **closed** tuple of exactly two
  compiled, fully-anchored (`\A…\Z`) regexes (D3):
  * `R1` canonical: `{shipment_id}-{suffix}-post-merge-closure.md`
  * `R2` legacy: `{YYYY-MM-DD}-{shipment_id}-{suffix}-closure.md`
  Both interpolate a `re.escape`d shipment ID bounded by literal `-`
  delimiters and are matched case-insensitively **only on the ID segment**;
  never a substring search (R2 mitigation).
* `build_closure_path(closure_dir, shipment_id, feature_id) -> Path` — the path
  builder the producer documentation directs authors to, and the **only**
  construction path the composed test in U7 may use.
* `classify_closure_candidates(closure_dir, shipment_id) -> ClosureDiscovery` —
  returns a frozen dataclass carrying `canonical_matches`, `legacy_matches`,
  `unrecognized_candidates`, and an `outcome` of
  `absent | unrecognized | recognized`, applying D5's ordering: canonical
  partition wins outright when non-empty; within a partition, candidates are
  returned in deterministic sorted order.
* `CONSUMER_SITES` — an in-source enumerated tuple of every site that derives
  from this contract (the topology reader, the validation CLI, the two producer
  skill files, the two Ship agent files), per compound lesson 4. U9 asserts it
  is complete.

**Scope guard**: this module performs **no** frontmatter parsing and makes **no**
validity judgement. It answers "which files are candidates, and how are they
classified by name" and nothing else.

**Tests (4)**: canonical/legacy/both/neither classification; anchored-ID
rejection of a foreign-ID filename; deterministic ordering under multiple
matches; `build_closure_path` round-trips through `classify_closure_candidates`
as canonical.

**Posture**: test-first.

### U2 — Rewire the topology closure reader onto the contract *(domain: Python source)*

**Files**: `src/autoharness/gates/topology.py`, `tests/test_gates_topology.py`.

**Changes**

* `FilesystemTopologyReaders.closure_complete()` delegates discovery to
  `classify_closure_candidates`. It keeps its existing
  `bool | None` return type for backward compatibility and gains a sibling
  `closure_discovery(shipment_id) -> ClosureDiscovery | None` used by the gate
  layer (U3) for diagnostics.
* Evaluation order per D5: evaluate canonical matches first, accept on the first
  candidate satisfying `_closure_artifact_complete`; only if the canonical
  partition is empty, evaluate legacy matches the same way.
* `_NullReaders.closure_complete` and the protocol declaration at
  `topology.py:131` gain the matching `closure_discovery` member so the
  structural protocol stays satisfied.

**Explicitly unchanged (RQ-13)**: `_closure_artifact_complete`
(`topology.py:303-337`) and `_closure_conditions_satisfied`
(`topology.py:281-300`) are **byte-identical** after this unit.
`_frontmatter`'s `BacklogUnavailableError` raise path is untouched, so malformed
frontmatter still fails closed as `BACKLOG_UNAVAILABLE`.

**Tests (3)**: legacy-named valid artifact now returns `True`; canonical takes
precedence when both exist; malformed frontmatter under a recognized name still
raises `BacklogUnavailableError`.

**Posture**: characterization-first — pin current behaviour for the
ID-anchored corpus before changing discovery.

### U3 — Distinguishable gate diagnostics *(domain: Python source)*

**Files**: `src/autoharness/gates/topology.py`, `tests/test_gates_topology.py`.

**Changes**

* `_shipment_readiness_check` consults `closure_discovery`. When the outcome is
  `unrecognized`, it emits the new token `PREDECESSOR_CLOSURE_UNRECOGNIZED`
  with a message naming **the candidate path(s) found and the canonical pattern
  expected**; `absent` and `recognized-but-invalid` continue to emit
  `PREDECESSOR_CLOSURE_INCOMPLETE` unchanged (D4).
* `_shipment_readiness_details` gains `closure_discovery_outcome`,
  `closure_candidate_paths`, and `closure_expected_pattern`. The existing
  `closure_complete` detail key is **retained with unchanged semantics** so no
  existing consumer of the JSON payload breaks.

**Scope guard**: no gate is relaxed. `PREDECESSOR_CLOSURE_UNRECOGNIZED` is a
**blocking** token; it renames a failure, it never permits one (OQ-4).

**Tests (3)**: unrecognized candidate produces the new token with the candidate
path in `details`; absent produces the original token; the JSON payload still
carries `closure_complete`.

**Posture**: test-first.

### U4 — `autoharness gate closure-evidence` write-time validation *(domain: Python CLI)*

**Files**: `src/autoharness/cli.py`, `tests/test_cli_gate_closure_evidence.py` (new).

**Changes**

* New subcommand `autoharness gate closure-evidence --path <file>
  [--shipment <id>] [--workspace <path>] [--json]`, added as one additional
  branch in the flat dispatcher at `cli.py:369-389`, plus its usage/help block
  alongside the existing `pipeline-topology` / `dag-readiness` blocks.
* Validation, in order: (a) filename matches the **canonical write pattern**
  from U1 — a legacy-named artifact is a **write-time failure**, because
  recognition is read-side only (D3); (b) required frontmatter keys
  `closure_status` and `compaction_status` are present with permitted values;
  (c) the artifact is discoverable for its declared shipment via
  `classify_closure_candidates`. Each failure names the offending field or path.
* Exit codes follow the established gate convention: `0` pass, `1` validation
  failure, `2` invalid input.

**Scope guard**: validation only. This command never writes, renames, or repairs
an artifact (D8). It is not wired into any pre-existing gate path.

**Tests (4)**: canonical + valid frontmatter passes; legacy filename fails with
the canonical pattern quoted; missing `closure_status` fails naming that field;
unparseable path exits `2`.

**Posture**: test-first.

### U5 — Producer spec reconciliation *(domain: skill documentation — template + installed mirror, ATOMIC)*

**Files**: `templates/skills/operational-closure/SKILL.md.tmpl`,
`.github/skills/operational-closure/SKILL.md`.

**Changes** (both files, in **one commit** — R4 / the `165.008-T`+`165.010-T`
precedent):

* Line 23's Output bullet changes to the canonical pattern
  `{{DOCS_CLOSURE}}/{shipment_id}-{feature_id}-post-merge-closure.md`
  (installed mirror: `docs/closure/…`), quoting
  `CANONICAL_CLOSURE_PATTERN_DOC` **verbatim** so U9's guard can compare them.
* The Output section gains an explicit **required frontmatter keys** statement
  (`closure_status`, `compaction_status`) — previously implied by prose only,
  which is the metadata half of the historical drift.
* A new Required Protocol step mandates invoking
  `autoharness gate closure-evidence` before the closure artifact is committed
  (RQ-7).
* A short note records that the date is carried in frontmatter rather than the
  filename, and that legacy date-prefixed names remain **readable but are never
  written** (D2/D3), so the asymmetry cannot be misread as permission.

**Scope guard**: no other skill section is edited. No other skill file is
touched.

**Tests**: covered by U9's non-drift guard; no runtime behaviour changes here.

**Posture**: migration-first — the documentation must not land before U1
defines the constant it quotes.

### U6 — Ship agent reference alignment *(domain: agent documentation — template + installed mirror, ATOMIC)*

**Files**: `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md`.

**Changes** (both files, in **one commit**):

* The post-merge closure step (`_ship.agent.md.tmpl:863`, and the corresponding
  installed step) names the canonical closure path and the mandatory
  `autoharness gate closure-evidence` invocation, instead of naming only the
  `{{DOCS_CLOSURE}}/` directory.
* The step's gate-relevant metadata list names **both** `compaction_status` and
  `closure_status`. The source bug report identifies the omission of
  `closure_status` from the Ship-side guidance as the compounding half of the
  metadata axis; this closes it.

**Scope guard**: no change to Ship's role boundary, closure procedure, P-015
handling, or any other step.

**Posture**: migration-first (depends on U5's wording).

### U7 — Composed producer/consumer state-machine test *(domain: tests)*

**Files**: `tests/test_closure_contract_composition.py` (new).

**Changes** — the binding construction rule from **D7**: the test **must**
obtain the closure filename from `build_closure_path(...)` exactly as the
producer documentation directs, write a minimal valid artifact there, and feed
the result to the **real** `FilesystemTopologyReaders.closure_complete`. A
hand-written literal filename in this test is a **defect**, not a shortcut: such
a fixture would have passed throughout all six occurrences of this defect.

**Tests (4)**:

1. **Composed round-trip** — producer builder → real consumer reader → `True`.
   Fails if either the builder's pattern or the reader's recognition changes
   alone.
2. **Real-corpus unblock proof** — against the committed `docs/closure/`
   directory (read-only), assert `closure_complete("162-S") is True` and
   `closure_complete("174-S") is True`. This is the non-simulatable evidence for
   RQ-1 and cannot be faked by a fixture.
3. **Dual-artifact precedence** — `closure_complete("173-S") is True` and the
   canonical artifact is the one that produced the verdict (D5).
4. **Pre-existing corpus non-regression** — a sampled sweep over the
   `134-S` … `161-S` ID-anchored records still returns `True`.

**Posture**: test-first.

### U8 — Historical failure-shape and ID-collision regressions *(domain: tests)*

**Files**: `tests/test_gates_topology.py` (extended).

**Tests (4)**:

1. **Date-prefixed name, valid content** — the shape that silently failed for
   `001-S`, `008-S`, `162-S`, `174-S` — now resolves `True` and is reported as a
   **legacy** match, not a canonical one.
2. **Recognized name, missing frontmatter** — still raises
   `BacklogUnavailableError` → `BACKLOG_UNAVAILABLE` (the `005-S` shape; RQ-13).
3. **Recognized name, `compaction_status` without `closure_status`** — still
   fails closed (the second `005-S` axis; predicate unchanged).
4. **Adversarial ID collision** — an artifact for `16-S` must not satisfy
   `closure_complete("162-S")`, and an artifact for `162-S` must not satisfy
   `closure_complete("16-S")`, under **both** R1 and R2 (R2 mitigation).

**Posture**: test-first.

### U9 — Producer/consumer non-drift guard *(domain: tests)*

**Files**: `tests/test_closure_contract_nondrift.py` (new).

**Tests (3)**:

1. **Documented pattern equals code constant** — parse the Output bullet from
   `templates/skills/operational-closure/SKILL.md.tmpl` and
   `.github/skills/operational-closure/SKILL.md`, and assert each equals
   `CANONICAL_CLOSURE_PATTERN_DOC` (modulo the `{{DOCS_CLOSURE}}` ↔
   `docs/closure` variable substitution). Changing the pattern in prose alone
   fails; changing it in code alone fails.
2. **Template/installed parity** — the two producer files agree with each other,
   and the two Ship agent files agree with each other (R4).
3. **Consumer-site registry completeness** — every path listed in
   `CONSUMER_SITES` exists, and no file outside that list contains a literal
   `-post-merge-closure.md` pattern definition (closure artifacts and test
   fixtures excluded by an explicit allowlist).

**Posture**: test-first.

## Dependency Graph

```text
U1 (contract module)
 ├─► U2 (reader rewire) ─► U3 (gate diagnostics)
 ├─► U4 (validation CLI)
 └─► U5 (producer spec) ─► U6 (Ship agent)

U1,U2,U3,U4 ─► U7 (composed test)
U1,U2        ─► U8 (regression + adversarial)
U1,U5,U6     ─► U9 (non-drift guard)
```

Topologically sorted execution order: **U1 → U2 → U3 → U4 → U5 → U6 → U7 → U8 → U9**.
No cycles. U3 and U4 are independent of each other; U5/U6 are independent of
U2/U3/U4 beyond their shared dependency on U1.

**Critical path**: U1 → U2 → U3 → U7 (the chain that produces RQ-1's unblock
proof).

## Decisions and Rationale

| # | Decision | Rationale |
|---|---|---|
| P-D1 | Contract lives in a **new module**, not inside `topology.py` | `topology.py` is a consumer, not the definition. Putting the contract there reproduces the "definition co-located with one consumer" structure that generated the drift. A sibling module also matches `shipment_closure.py` / `bootstrap_grant.py` precedent. |
| P-D2 | `closure_complete()` keeps its `bool \| None` signature; diagnostics arrive via a **new sibling method** | Minimises blast radius on a fail-closed gate. Every existing caller, test double, and protocol implementer keeps working; the richer outcome is opt-in. |
| P-D3 | Name classification (U1) is strictly separated from content validity (U2's use of the untouched predicate) | Keeps the fail-closed validity predicate byte-unchanged and independently reviewable — the single largest safety property of this change (R1, R3). |
| P-D4 | Legacy naming is a **write-time failure** even though it is a read-time success | The asymmetry *is* the decision (D2/D3). Without a write-side failure, recognition would silently become permission and the canonical pattern would decay into a suggestion. |
| P-D5 | Producer template and installed mirror change in **one** unit | Direct application of the `165.008-T`/`165.010-T` precedent: a split leaves a window where the documented contract and the dogfooded contract disagree — the exact defect shape under repair. |
| P-D6 | The composed test's filename must come from the builder | D7. A literal filename would have passed through every one of the six historical occurrences and would pin nothing. |
| P-D7 | Real-corpus assertions on `162-S`/`174-S` live in the composed test | They are the only assertions that cannot be satisfied by a fixture, and they are the direct machine-checked statement of RQ-1. |
| P-D8 | New token `PREDECESSOR_CLOSURE_UNRECOGNIZED` rather than overloading the existing one | Compound lesson 8, "Overloading is a defect" and "Unrecognised is loud". The silent `None` conflation is the defect's real cost; a distinct token is the fix. |

## Risks and Caveats

Carried from the decision (R1-R9), with plan-level mitigations:

| # | Risk | Mitigation in this plan |
|---|---|---|
| R1 | Read-side widening weakens a fail-closed gate | Closed two-regex enumeration in U1; `_closure_artifact_complete` byte-unchanged in U2 (explicit unit scope guard); U8 tests 2-3 assert the fail-closed paths survive. |
| R2 | In-filename ID match collides across shipments | Fully anchored regexes with `re.escape`d, delimiter-bounded IDs (U1); U8 test 4 is a dedicated adversarial collision test in both directions. |
| R3 | `BACKLOG_UNAVAILABLE` regresses to a silent skip | `_frontmatter` untouched (U2 scope guard); U8 test 2 asserts the raise. |
| R4 | Template / installed mirror split-commit window | U5 and U6 are each single atomic units spanning both files; U9 test 2 asserts parity. |
| R5 | Composed test degenerates into a fixture | D7 construction rule stated as binding in U7; U7 test 2's real-corpus assertion cannot be faked. |
| R6 | Scope creep into closure artifact content or adjacent stash entries | RQ-14 verification step; every unit carries an explicit scope guard; the decision's OUT-of-scope list names the excluded stash IDs. |
| R7 | New `blocks` edge introduces a cycle | The fix's shipment is `dag-root` with no outgoing edges (D9); `autoharness gate dag-readiness --json` must report `cycle_detected: false` after the edge is added. |
| R8 | Future producer convention change drifts again | U9 test 1 fails the build unless the change is made at the single source. |
| R9 | New CLI subcommand regresses gate dispatch | Additive branch only (U4); existing gate CLI tests must pass unchanged. |
| R10 | `closure_discovery` added to the reader protocol breaks third-party/test implementers of that protocol | U2 explicitly updates `_NullReaders` and the protocol declaration; the in-repo test doubles in `tests/test_gates_topology.py` that implement `closure_complete` are updated in the same unit. |

**Caveat — bootstrap ordering.** This fix's own closure artifact is authored
*after* it merges, so the merged contract governs it and it is discoverable
under either recognized pattern (D9 bootstrap note). `163-S`'s new blocking edge
therefore cannot deadlock on the defect being repaired.

## Plan Hardening Signals (REQUIRED)

| Signal | Present | Justification |
|---|---|---|
| Public API, schema, or contract change | **YES** | The closure-evidence naming contract is a cross-component contract; `closure_complete`'s consumer protocol gains a member; a new gate token `PREDECESSOR_CLOSURE_UNRECOGNIZED` enters the gate's public token vocabulary; a new CLI subcommand enters the distributed CLI surface. No JSON schema under `schemas/` changes (OQ-2 deferred). |
| Security, auth, permission, or compliance-sensitive behavior | No | No authentication, authorization, secret handling, or permission surface is touched. Filesystem reads stay within the existing `docs/closure/` traversal already performed by the reader. |
| Migration, backfill, destructive data/config action, irreversible step | No | **Zero** closure artifacts are created, renamed, edited, or deleted (D8/RQ-14). Recognition is added rather than the corpus migrated — deliberately, so that no irreversible rewrite of committed closure history occurs. |
| External integration, operator checkpoint, or external dependency | No | No external service, network call, or new third-party dependency. backlogit interaction is unchanged. |
| High runtime, rollout, or rollback risk | **YES** | The change rewires a **fail-closed release gate** that authorizes shipment claims. An over-permissive regression would let a shipment claim without genuine closure evidence; an over-restrictive regression would block the entire queue. Blast radius additionally spans the distributed CLI and two template families (`templates/skills/`, `templates/agents/`) plus their installed dogfood mirrors. |

**Requires plan hardening: yes**

## Runtime Verification and Closure

| Unit | Changes a runtime surface? | Runtime verification required | Closure expectation |
|---|---|---|---|
| U1 | No (library only) | Unit tests green | — |
| U2 | **Yes** — topology gate behaviour | `autoharness gate pipeline-topology --mode manual --shipment 163-S --phase pre_claim --json` transitions from `exit_code: 1` / `PREDECESSOR_CLOSURE_INCOMPLETE` to a pass on this check, captured verbatim before and after | Before/after gate JSON in the closure artifact |
| U3 | **Yes** — gate token vocabulary and JSON payload | Construct an unrecognized candidate in a scratch workspace and confirm `PREDECESSOR_CLOSURE_UNRECOGNIZED` with the candidate path in `details`; confirm `details.closure_complete` still present | Token-vocabulary change recorded |
| U4 | **Yes** — new CLI subcommand | `autoharness gate closure-evidence --help`; one passing and one failing invocation with exit codes recorded | CLI surface addition recorded |
| U5 | No (documentation) | `autoharness verify` / harness verification passes; rendered template resolves `{{DOCS_CLOSURE}}` with no unresolved `{{...}}` | Template-contract change recorded |
| U6 | No (documentation) | Same as U5 for the agent template family | Agent-contract change recorded |
| U7-U9 | No (tests) | Full test suite green | Composed-test existence recorded as the durable non-drift guarantee |

**Rollback trigger**: any post-merge observation of a shipment passing
`pre_claim` without genuine, valid closure evidence, or of a previously-passing
shipment newly blocked, is an immediate rollback trigger. Rollback is a plain
revert — no data migration is involved, which is a direct consequence of D8.

**Validation window**: the next `pre_claim` evaluation of `163-S` is the
first real-world exercise of the change and is the designated observation point.

---

## Plan Hardening

Applied 2026-09-17 per **P-006**, triggered by the two present hardening signals
(public/contract change; high runtime/rollout risk) and the elevated blast
radius (fail-closed release gate + distributed CLI + two template families).

### H1 — Fail-closed verification is a first-class deliverable, not a side effect

The dominant hazard is **over-permissiveness**: a discovery change that lets a
shipment claim without genuine closure evidence. Hardening requires that the
following be demonstrated, with captured evidence, and not merely asserted:

1. `_closure_artifact_complete` and `_closure_conditions_satisfied` are
   **byte-identical** before and after U2. Evidence: a diff over those line
   ranges showing zero changes. This is a hard acceptance criterion on U2, not a
   review observation.
2. An artifact with a recognized name and `closure_status: BLOCKED` still
   blocks (U8 test 3 extension).
3. An artifact with a recognized name and **no** `conditions:` block under
   `READY_WITH_CONDITIONS` still blocks.
4. The recognized-read set is asserted to have **exactly two** members; a test
   fails if a third pattern is added without a corresponding deliberate contract
   change. This converts D3's "closed enumeration" from prose into a machine
   check.

### H2 — Ordering constraint: the gate must not change before the contract exists

U2 must not merge ahead of U1, and U5/U6 must not merge ahead of U1, because
each would create exactly the transient split-contract state this work exists to
eliminate. The dependency graph already encodes this; hardening makes it a
**merge-order constraint**, and U9's parity test (test 2) is the mechanical
detector if it is violated.

### H3 — Explicit negative scope assertion for `docs/closure/`

RQ-14 is hardened from an intention into a verification step with a concrete
command: `git diff --name-status <base>..HEAD -- docs/closure/` must return
**empty** at every commit of this work. Any non-empty result is a halt, not a
discussion — it means the seventh per-artifact workaround is being performed
under the contract fix's name.

### H4 — Rollback is bounded and proven trivial by construction

Because D8 forbids artifact migration, rollback is a pure code/doc revert with
no data-state to unwind. Hardening records this explicitly so a future reader
does not assume a migration exists: **there is no backfill, no state file, no
ledger, and no irreversible step in this plan.** The single reversibility
question — "does reverting re-block `163-S`?" — has the answer "yes, to exactly
its current state", which is a safe restoration rather than a corrupted one.

### H5 — Unsatisfiable-gate check (compound lesson 6, carried as OQ-6 of the prior learning)

For every gate outcome introduced or modified, a concrete legitimate passing
state and a concrete legitimate failing state are named in the decision's
D3 outcome table. Re-verified during hardening: all seven rows name a real or
constructible state; **no row is unreachable**. Specifically,
`PREDECESSOR_CLOSURE_UNRECOGNIZED` is reachable (a file named `162-S-notes.md`)
and escapable (rename to the canonical pattern), so it is not a trap state.

### H6 — Operator checkpoint at the token-vocabulary boundary

Adding `PREDECESSOR_CLOSURE_UNRECOGNIZED` widens the gate's public token
vocabulary. Any downstream consumer that switches on the token set must fail
**loudly** on an unrecognised token rather than falling through (compound lesson
8). Hardening adds a verification item to U3: grep the repository for
token-dispatch sites over `PREDECESSOR_CLOSURE_*` and confirm each either
handles the new token or fails closed on unknown tokens. If a silent
fall-through site is found, it is a **blocking** finding for U3, not a follow-up.

### H7 — Residual risk accepted

`R2` (ID-collision in the legacy pattern) is the highest residual risk after
mitigation, because the legacy corpus lowercases shipment IDs and therefore
requires case-insensitive matching, which is inherently weaker than an exact
match. It is accepted because (a) matching is fully anchored with literal
delimiters on both sides of the ID, (b) a dedicated bidirectional adversarial
test covers the realistic collision shape, and (c) the legacy pattern is
read-only and applies to a **closed, finite, already-committed** corpus that
will never grow.

---

## Plan Review

**Reviewer**: plan-review (declared-degradation mode — cross-model persona
dispatch unavailable in this session; always-on personas applied directly).
**Cycle**: 1 of a maximum 3. **Date**: 2026-09-17.
**Full record**: `docs/reviews/2026-09-17-closure-evidence-naming-contract-plan-review.md`.

**Decision: PASS_WITH_CONDITIONS → resolved to PASS.**
0 × P0, 2 × P1, 3 × P2, 2 × P3. All P1 and all in-scope P2 findings were
resolved in place in this revision; the P3 findings are recorded as
out-of-scope follow-ups.

| ID | Sev | Finding | Resolution |
|---|---|---|---|
| F-1 | **P1** | U2 changed the reader's *protocol* (adding `closure_discovery`) but the plan did not account for the ~15 in-repo test doubles in `tests/test_gates_topology.py` that implement `closure_complete` structurally. Omitting them would break the suite and tempt a scope-widening mid-execution edit. | **Resolved** — R10 added to Risks and Caveats; U2's scope now explicitly includes updating `_NullReaders`, the protocol declaration at `topology.py:131`, and the in-repo test doubles. |
| F-2 | **P1** | The plan asserted the validity predicate stays unchanged but provided no *mechanical* check, leaving the single most important safety property as prose. A reviewer of a future revision could not verify it cheaply. | **Resolved** — hardening item **H1.1** makes byte-identity of `_closure_artifact_complete` / `_closure_conditions_satisfied` a hard acceptance criterion on U2 with a diff-based evidence requirement. |
| F-3 | P2 | D3 described the recognized-read set as "closed" but nothing prevented a third pattern being added later without a contract decision. | **Resolved** — **H1.4** adds a cardinality assertion test (exactly two recognized patterns). |
| F-4 | P2 | The new gate token could be silently swallowed by an existing token-dispatch site, converting a vocabulary extension into an undetected behaviour change (the exact failure compound lesson 8 warns about). | **Resolved** — **H6** adds a mandatory token-dispatch-site sweep to U3, with silent fall-through classified as blocking. |
| F-5 | P2 | U7 originally carried 5 test scenarios, exceeding the 2-hour-rule ceiling of 4. | **Resolved** — the historical failure-shape and adversarial-collision scenarios were split out into a separate unit **U8**; U7 and U8 now carry 4 each. Unit count went 8 → 9. |
| F-6 | P3 | A full canonical closure **writer** (source-report criterion 2) is not delivered. | **Accepted as out of scope** — decision OQ-1. The naming axis is fully closed; body/frontmatter generation is a distinct surface. |
| F-7 | P3 | The closure-evidence frontmatter schema is not promoted into `schemas/`. | **Accepted as out of scope** — decision OQ-2. Would cross into schema evolution and materially widen blast radius. |

**Persona verdicts**

| Persona | Verdict | Note |
|---|---|---|
| Architecture | PASS | Contract-module placement matches `gates/` sibling precedent; definition correctly separated from consumers (P-D1). |
| Scope-boundary | PASS | Every unit carries an explicit scope guard; D8's zero-artifact invariant is mechanically verified by H3; excluded stash IDs are named; `3EF5AAF2` is explicitly untouched. |
| Standards | PASS | All 9 units satisfy the 2-hour rule and width isolation after F-5; no unit mixes Python source with template/agent documentation. |
| Fail-closed / safety | PASS after F-2, F-3, F-4 | The predicate is now mechanically pinned, the read set's closedness is asserted, and token-vocabulary extension is swept for silent fall-through. |
| Test-efficacy | PASS | D7's construction rule plus U7 test 2's real-corpus assertion defeat the fixture anti-pattern that let this defect survive six occurrences. |
| Dependency / sequencing | PASS | Graph acyclic; merge-order constraint hardened (H2); the DAG edge's cycle-freedom is verified by re-running `dag-readiness` (R7). |

**Gate outcome**: the plan is cleared for harvest.
