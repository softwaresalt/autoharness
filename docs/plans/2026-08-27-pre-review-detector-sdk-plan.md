---
title: "S1 — Detector SDK, evidence-node contract, and gate pre-review reader"
date: 2026-08-27
slug: pre-review-detector-sdk
source_stash: "D911A3B2 (program frame); 89E833E1 split (a)"
source_decision: "docs/decisions/2026-08-27-pre-review-evidence-dag-shipment-portfolio-deliberation.md"
shipment_unit: "S1"
status: reviewed
---

# S1 — Detector SDK, Evidence-Node Contract, and `gate pre-review` Reader

## Provenance and split lineage

* **Authoritative scope**: `031-DL`
  `docs/decisions/2026-08-27-pre-review-evidence-dag-shipment-portfolio-deliberation.md`
  §"Shipment Portfolio" -> **S1 — Detector SDK, evidence-node contract, and
  `gate pre-review` reader**, plus §"DAG Contract" D1-D10.

* **Input stash `D911A3B2`** (critical, epic) — *program frame*, disposition
  **RETAIN (scope-narrowed)** per `031-DL` §"Normalization of the Imported Scope".
  It is the program epic over **S1-S10**. **This entry is NOT consumed and NOT
  archived by this plan** — it continues to own S2-S10.
  Two narrowings inherited from the normalization table and binding here:
  1. *"evidence persistence"* is bounded to a **HEAD-keyed report** under Law 1 —
     never a persisted graph.
  2. *"extension points for repository-specific adapters"* is **deferred** until a
     second consumer repository exists (Law 2). Explicit non-goal below.

* **Input stash `89E833E1`, split (a) only** (critical, feature) — disposition
  **SPLIT (3 ways)**. **This entry is NOT consumed and NOT archived** — splits
  (b) and (c) remain its property:
  | Split | Content | Target | Owned here? |
  |---|---|---|---|
  | **(a)** | Detector/evidence-node **SDK + node contract** — the foundation everything plugs into | **S1** | **YES — this plan** |
  | (b) | DAG **family assembly + incremental evaluation + shipment attachment** | S8 | No |
  | (c) | *"Require verified evidence at every applicable terminal node before review readiness"* + **waiver/override authority** | S10 | No — this is a blocking-policy promotion and **must not travel with (a)** |
  | *pruned* | *"query/visualization"* | — | **PRUNED** until a reader exists (Law 2) |

* **Operator authority consumed**:
  * **Q1 APPROVED** — a derived pre-review evidence report **may** persist under
    `.autoharness/gates/`, because named PR-readiness and closure consumers
    require it. It remains **derived evidence, not the source of truth**;
    **report-only first**; **no blocking authority**. This is the sole
    persistence exception (D9) and it is bounded by U7 below.
  * **Q5 APPROVED** — authoritative test command is
    `PYTHONPATH=src python -m unittest discover -s tests` (matches `ci.yml` L112).
    Acceptance criteria in this plan do **not** substitute pytest.
  * **Q7 APPROVED** — S0 is cleared, not waived. **S1 is sequenced after S0** and
    its shipment carries a `blocks` edge on S0's.

## Problem Frame

`031-DL` §R4 measured the existing gate surface and concluded that **no new
scheduler, no new persistence layer, and no new verdict vocabulary are required**.
S1 must therefore land a detector SDK **by extension of** that surface, and must
prove the abstraction by shipping exactly one real detector end-to-end.

Measured substrate this plan builds on (all verified at `d2e9a7e6`):

| Existing asset | Location | Role in S1 |
|---|---|---|
| `CheckResult{name,status,token,message,details}` (frozen dataclass, `to_dict()`) | `gates/topology.py` L130-L146 | `NodeResult` reuses these semantics rather than inventing a verdict shape |
| `TopologyResult` exit-code semantics 0/1/2/3, `blocked`/`invalid`/`retry_required` properties | `gates/topology.py` L148+ | Exit-code mapping precedent for `gate pre-review` |
| Three-colour DFS cycle detection `_dag_detect_cycle` | `gates/topology.py` L1842-L1870 | The **proven algorithm** the registry validator mirrors (see D-3) |
| `discover_modified_files(base, head, ...)` — forward-slash, never raises, warns and returns `[]` on git failure | `gates/discovery.py` | The applicability-context source |
| `path_matches(pattern, path)` doublestar globs, `filter_matching`, `normalize_path` | `gates/match.py` | `changed_paths_any` predicate semantics |
| `_gate_dag_readiness_command` — `--json`, degraded-payload synthesis, read-only contract | `cli.py` L944+ | The **shape** `gate pre-review` follows |
| `_gate_command` dispatch + `GATE_USAGE` | `cli.py` L351-L374 | Subcommand registration point |
| `schemas/validation-gates.schema.json` v1.0.0, `additionalProperties: true` at root | `schemas/` | The registry declaration extension point |
| `.autoharness/gates/*-force-audit.log`, `pipeline-topology-telemetry.jsonl` | `.autoharness/gates/` | The Q1 persistence precedent |
| `.backlogit/templates/{task,feature,subtask,shipment,deliberation,review}.md` | `.backlogit/templates/` | `ART-01`'s declared-shape source |

**The reference detector, made concrete.** `ART-01` is *backlogit section-marker
conformance*. Each `.backlogit/templates/<type>.md` declares, in YAML frontmatter,
a `sections:` list with `name` and `required`. The body then declares
`<!-- BEGIN:<name> -->` / `<!-- END:<name> -->` marker pairs. `ART-01` asserts
that every artifact under `.backlogit/queue/` carries, for its `artifact_type`,
a well-formed marker pair for each declared section — paired, correctly ordered,
non-nested, non-duplicated — and that every `required: true` section is non-empty.

This is the right reference detector because it is **closed-surface,
declared-shape, and fully deterministic**, and — critically for `031-DL` RK2 — it
**reads data that already exists for another reason** and requires **no new
author-minted identifier** (A8).

## Requirements Trace

| # | Requirement (source) | Implementation action | Unit |
|---|---|---|---|
| R1 | Node contract D1-D8: identity, applicability, producer/validator, deps, verdicts, provenance, severity/mode, remediation | `NodeSpec` / `Evidence` / `NodeResult` dataclasses + verdict vocabulary | **U1** |
| R2 | Registry is the declaration point; schema-validated | Extend `validation-gates.schema.json` with a `detectors` block | **U2** |
| R3 | Registry loader; invalid registry -> `invalid` | Loader + reference resolution + validation errors | **U3** |
| R4 | D2 applicability + **FC1** (context unbuildable -> `insufficient_evidence`, never `not_applicable`) + **FC2** (record the excluding clause) | Applicability engine over `discover_modified_files` + `path_matches` | **U4** |
| R5 | D4 derived DAG + cycle detection; **cycle = registry defect -> exit 2, evaluate nothing, never auto-break**; upstream non-pass -> `blocked_upstream` | Assembler with three-colour cycle detection | **U5** |
| R6 | One real detector end-to-end (RK1 falsification) | `ART-01` section-marker conformance | **U6** |
| R7 | **Q1**: HEAD-keyed report under `.autoharness/gates/pre-review/`; D6 freshness rule | Report emitter + freshness evaluation | **U7** |
| R8 | `autoharness gate pre-review [--json] [--base <ref>]` | CLI wiring following the `dag-readiness` shape | **U8** |
| R9 | D5: report-only, **always exit 0 except registry-invalid (exit 2)** | Exit-code mapping asserted in tests | **U8, U11** |
| R10 | Acceptance: `ART-01` re-detects a historical defect; cycle injection exits 2 | Retro-validation + end-to-end acceptance tests | **U11** |
| R11 | Q5: authoritative gate command | All test units run under `PYTHONPATH=src python -m unittest discover -s tests` | **U9-U11** |

## Non-goals (architectural laws — violating any of these fails the shipment)

* **NO PERSISTED GRAPH.** Law 1. The DAG is reassembled from the registry on
  **every** invocation. Nothing derived from topology is written to disk. The
  only artifact written is the flat run report (R7), which is *not a graph*.
* **NO SECOND DETECTOR.** `ART-01` only. `ART-02`+ belong to S2.
* **NO BLOCKING, NO PROMOTION.** Every detector is `mode: report_only`. **A
  detector may never set its own `mode`**, and **no detector ships with
  `mode: blocking`** (D7). Promotion is S10-only. Exit code is **always 0**
  except a registry defect (exit 2), which is the gate refusing to report a
  result it cannot compute — *not* a policy promotion.
* **NO WAIVER ENGINE.** D10 waivers are `89E833E1` split (c) -> S10. `NodeSpec`
  may carry no waiver field in this shipment.
* **NO QUERY OR VISUALIZATION.** Explicitly pruned from `89E833E1` until a reader
  exists (Law 2).
* **NO REPOSITORY-SPECIFIC ADAPTER EXTENSION POINTS.** `D911A3B2` narrowing 2.
* **NO INCREMENTAL EVALUATION / SHIPMENT ATTACHMENT.** That is split (b) -> S8.
* **NO NEW SCHEDULER.** The standing `dag-readiness` non-goal, restated by
  requirement 13. No new ordering authority; `compute_next_eligible` is untouched.
* **NO BACKLOGIT CHANGE.** `031-DL` Q9 asserts zero backlogit change for S1-S9.
  `ART-01` **reads** `.backlogit/**` and mutates nothing.
* **NO NEW AUTHOR-MINTED IDENTIFIER** (A8 / RK2).

## Implementation Units

### U1 — Node, evidence, and verdict contract

* **Domain**: code. **Files: 2** (`src/autoharness/detectors/__init__.py`,
  `src/autoharness/detectors/contract.py`).
* `NodeSpec` (frozen): `node_id` (D1 `det:<domain>/<detector-id>@<version>`),
  `domain`, `detector_id`, `version`, `applies_when`, `producer`, `validator`,
  `depends_on`, `severity`, `mode`, `remediation`.
* `Evidence` (frozen): `node_id`, `payload`, `provenance`.
* `NodeResult` (frozen): mirrors `CheckResult` field-for-field
  (`name`,`status`,`token`,`message`,`details`) **plus** `verdict`,
  `provenance`, and `excluded_by` (FC2). `to_dict()` matches the existing
  convention.
* **Verdict vocabulary (8, closed)**: `passed`, `failed`, `insufficient_evidence`,
  `blocked_upstream`, `not_applicable`, `skipped`, `waived`, `invalid`.
  `waived` is **declared but unreachable** in S1 (no waiver engine) and must be
  asserted unreachable in U9.
* **Verdict -> exit mapping**: report-only column of D5 — everything maps to 0
  except `invalid` -> 2.
* **`mode` is constructor-fixed to `report_only`**; `NodeSpec` exposes no setter
  and the registry loader rejects `mode: blocking` (U3).
* **Posture**: test-first.

### U2 — Detector registry schema extension

* **Domain**: schema. **Files: 1** (`schemas/validation-gates.schema.json`).
* Add a top-level optional `detectors` block: array of node declarations with
  `node_id` (pattern-constrained to the D1 scheme), `applies_when`
  (`changed_paths_any`, `shipment_has_items_of_type`, `workspace_surfaces_any`,
  `always`), `producer` (`kind` enum `pure|ast|coverage|api|command`, `ref`,
  `tool_version_dims`), `validator` (`ref`, `consumes`), `depends_on`,
  `severity` enum, `mode` **const `report_only`**, `remediation`
  (`class` enum, `hint`, `target_refs`, `authority` enum).
* `additionalProperties: false` inside each node object so an unknown key is a
  registry defect rather than silent tolerance.
* **Backward compatibility**: the whole block is optional; an absent `detectors`
  block means zero nodes and behavior identical to today.
* **Posture**: schema-first. No code in this unit (width isolation).

### U3 — Registry loader and validation

* **Domain**: code. **Files: 1** (`src/autoharness/detectors/registry.py`).
* Load and schema-validate the `detectors` block; resolve `producer.ref` /
  `validator.ref` to importable callables; build `NodeSpec` objects.
* **Validation failures produce `invalid` (exit 2), never a partial run**:
  schema violation, unknown/unimportable ref, duplicate `node_id`, malformed
  `node_id`, `mode: blocking`, `depends_on` naming an unknown node.
* Missing/absent registry is **not** a defect — it yields zero nodes and exit 0.
* **Posture**: test-first. **Depends on U1, U2.**

### U4 — Applicability engine (D2, FC1, FC2)

* **Domain**: code. **Files: 1** (`src/autoharness/detectors/applicability.py`).
* Build the applicability context **once per run** from
  `discover_modified_files(base, head)`, the resolved shipment manifest, and
  `workspace-profile.yaml` `runtime_surfaces`.
* Evaluate `applies_when` using `gates/match.py::path_matches` semantics.
* **FC1 (fail-closed)**: if the context cannot be built — unresolvable diff base,
  unreadable manifest, missing profile — every node evaluates to
  **`insufficient_evidence`**, *never* `not_applicable`.
  **Caveat requiring care**: `discover_modified_files` **never raises** and
  returns `[]` with a warning on git failure. An empty list is therefore
  ambiguous — "no files changed" and "git unavailable" look identical. The engine
  MUST distinguish these by explicitly resolving the base ref **before** calling
  discovery, so a genuine failure is not silently rendered as an empty-but-valid
  context. **This is the single most likely way FC1 is accidentally violated.**
* **FC2**: every `not_applicable` result records the excluding predicate clause
  in `excluded_by`.
* **Posture**: test-first. **Depends on U1.**

### U5 — Derived DAG assembler and cycle detection (D4)

* **Domain**: code. **Files: 1** (`src/autoharness/detectors/assembler.py`).
* Assemble the graph **in memory, at read time, on every invocation**. Nothing
  persisted (Law 1).
* Three-colour DFS cycle detection over `depends_on`, mirroring the proven
  `_dag_detect_cycle` algorithm; deterministic node iteration (`sorted`) so the
  reported cycle is stable.
* **Cycle -> `invalid`, exit 2, evaluate nothing, never auto-break.**
* Deterministic topological evaluation order; upstream `failed` or
  `insufficient_evidence` -> downstream `blocked_upstream` (**never** `passed`,
  **never** `skipped`).
* A validator may consume upstream evidence but **may never re-run an upstream
  producer** (D3) — enforced by passing an immutable evidence map.
* **De-risking decision (D-3 below)**: implement a self-contained cycle detector
  in this module rather than refactoring `topology.py`.
* **Posture**: test-first. **Depends on U1, U3.**

### U6 — `ART-01` reference detector

* **Domain**: code. **Files: 2** (`src/autoharness/detectors/art/__init__.py`,
  `src/autoharness/detectors/art/section_markers.py`).
* `produce`: read `.backlogit/templates/*.md` frontmatter for declared sections
  per artifact type; scan `.backlogit/queue/*.md`; emit an `Evidence` record of
  observed marker pairs per artifact.
* `validate`: pure function over that evidence — for each artifact, every
  declared section has a well-formed `BEGIN`/`END` pair (paired, ordered,
  non-nested, non-duplicated) and every `required: true` section is non-empty.
* `applies_when: {changed_paths_any: [".backlogit/**"]}`.
* `severity: medium`, `mode: report_only`, `remediation.class: guided_fix`,
  `remediation.authority: stage`.
* **Read-only**: no backlogit mutation (Q9).
* **Posture**: test-first. **Depends on U1, U4.**

### U7 — Report emitter and freshness rule (Q1, D6, D9)

* **Domain**: code. **Files: 1** (`src/autoharness/detectors/report.py`).
* Write `.autoharness/gates/pre-review/<head_sha>.json` — a **flat list of node
  results**, keyed by immutable epoch, **append-only per epoch, never
  overwritten**.
* `provenance`: `base_sha`, `head_sha`, `reviewed_sha` (nullable), `platform`,
  `tool_versions`, `produced_at` (RFC3339), and
  `touches_reviewable_paths: bool`.
* **Freshness (D6)**: a result is fresh iff its `head_sha` equals current HEAD
  **and** every dimension in `producer.tool_version_dims` is unchanged. A stale
  result is **`insufficient_evidence`**, never a reused `passed`.
* **Q1 boundary, asserted in code**: the report is **derived evidence, not the
  source of truth**. It is never read back as authoritative input to a verdict in
  this shipment; regeneration from the tree at that SHA must be possible. The
  emitter has **no blocking authority** and cannot influence the exit code.
* **Not a graph**: the writer accepts a flat sequence of `NodeResult` and has no
  access to edges — the type signature makes a persisted graph unrepresentable.
* **Posture**: test-first. **Depends on U1.**

### U8 — `gate pre-review` CLI wiring

* **Domain**: CLI. **Files: 1** (`src/autoharness/cli.py`).
* Register `pre-review` in `_gate_command` dispatch; add
  `_gate_pre_review_command(rest)` and `_parse_gate_pre_review_args`;
  extend `GATE_USAGE`.
* Flags: `--json`, `--base <ref>`; `--help`/`-h` prints usage and returns.
* Follows the `_gate_dag_readiness_command` shape exactly, including the
  **degraded-payload synthesis** precedent (never fabricate a graph).
* **Exit codes**: 0 always; 2 for invalid arguments **or** invalid registry.
* **Posture**: characterization-first against the existing `dag-readiness` CLI
  tests. **Depends on U3, U5, U6, U7.**

### U9 — Tests: contract, registry, applicability

* **Domain**: tests. **Files: 3** (`tests/test_detectors_contract.py`,
  `tests/test_detectors_registry.py`, `tests/test_detectors_applicability.py`).
* Scenarios (4): verdict->exit mapping incl. `waived` unreachable; registry
  rejects `mode: blocking` / duplicate / unknown ref -> `invalid`; absent
  registry -> zero nodes, exit 0; **FC1 unresolvable base -> `insufficient_evidence`
  (explicitly NOT `not_applicable`)** and FC2 records `excluded_by`.

### U10 — Tests: assembler, cycle detection, report, freshness

* **Domain**: tests. **Files: 2** (`tests/test_detectors_assembler.py`,
  `tests/test_detectors_report.py`).
* Scenarios (4): cycle injection -> `invalid`, exit 2, **zero nodes evaluated**;
  upstream `failed` -> downstream `blocked_upstream` (not `passed`/`skipped`);
  stale `head_sha` or changed `tool_version_dims` -> `insufficient_evidence`;
  report is a flat list, epoch-keyed, and a second run at the same epoch does not
  overwrite.

### U11 — Tests: `ART-01` retro-validation and CLI acceptance

* **Domain**: tests. **Files: 2** (`tests/test_detectors_art_section_markers.py`,
  `tests/test_gate_pre_review_cli.py`).
* Scenarios (4): `ART-01` flags a fixture artifact with a missing/unpaired
  marker and passes a conformant one; **retro-validation** — `ART-01` re-detects
  at least one historical defect from PR #234 / #185 / #183 / #189 / #202 /
  #123 / #213 (reconstructed as a fixture, no network); `gate pre-review --json`
  emits a schema-valid report and **exits 0 even when `ART-01` reports `failed`**;
  `--base <ref>` is honored and an unresolvable base yields
  `insufficient_evidence` at exit 0.
* **RK1 falsification gate**: if `ART-01` cannot re-detect **any** listed
  historical defect, that is the designed early exit — **halt and reconsider
  Option A (independent gates)** rather than shipping an unjustified SDK.
* **Gate command (Q5)**: `PYTHONPATH=src python -m unittest discover -s tests`.

## Dependency Graph

```text
U1 ──> U3 ──> U5 ──> U8
U2 ──> U3
U1 ──> U4 ──> U6 ──> U8
U1 ──> U7 ──> U8
U1,U3,U4 ──> U9
U5,U7     ──> U10
U6,U8     ──> U11
```

Serial order: `U1 -> U2 -> U3 -> U4 -> U5 -> U6 -> U7 -> U8 -> U9 -> U10 -> U11`.

## Decisions and Rationale

| # | Decision | Rationale |
|---|---|---|
| D-1 | `NodeResult` **mirrors** `CheckResult` rather than subclassing it | `CheckResult` is a frozen dataclass in a 96 KB high-traffic module; mirroring avoids coupling the detector package to topology's import graph while keeping D5's "reuse unchanged" intent. |
| D-2 | The `detectors` block extends `validation-gates.schema.json` rather than a new schema file | `031-DL` §R4 names it the declaration extension point; root is already `additionalProperties: true`, so the block is additive and back-compatible. |
| D-3 | **Self-contained cycle detector in `assembler.py`**, not a refactor of `topology.py::_dag_detect_cycle` | The existing helper is typed to `ShipmentState` and lives in a 96 KB module on the critical path of the shipment topology gate. Generalizing it would put S1's blast radius into P-001/P-016 enforcement code. The algorithm is ~20 lines and proven; **mirroring it is strictly cheaper and safer than generalizing it**. This is the de-risking that keeps U5 at medium rather than high complexity. Recorded as deliberate, reviewable duplication. |
| D-4 | `mode` is `const: report_only` **in the schema**, not merely defaulted | D7/RK4: a default can be overridden by a config edit; a `const` makes `mode: blocking` a **registry defect**. This makes silent promotion structurally impossible in S1 rather than merely discouraged. |
| D-5 | The report writer's signature accepts a flat `Sequence[NodeResult]` and never receives edges | Makes a persisted graph **unrepresentable** rather than merely forbidden — Law 1 enforced by type, not by review. |
| D-6 | `waived` is declared in the vocabulary but unreachable, and asserted unreachable | Keeps the vocabulary closed and stable for S10 without importing waiver authority into S1 (split (c)). |
| D-7 | Base ref is resolved **before** calling `discover_modified_files` | That function never raises and returns `[]` on failure, so empty-vs-broken is otherwise indistinguishable — the exact way FC1 gets accidentally violated. |
| D-8 | `ART-01` chosen as the reference detector | Closed surface, declared shape, fully deterministic, reads pre-existing data, needs no new identifier (A8/RK2), and has a real historical defect corpus for retro-validation. |

## Risks and Caveats

| # | Risk | Mitigation |
|---|---|---|
| RK1 | **The SDK becomes a write-only abstraction** (`031-DL` RK1, the strongest objection to Option C) | S1 ships `ART-01` end-to-end or does not ship. U11 encodes the falsification gate with a named early exit to Option A. |
| RK2 | FC1 violated via the empty-list ambiguity in `discover_modified_files` | D-7 resolves the base ref first; U9 tests the unresolvable-base path explicitly. |
| RK3 | Silent promotion to blocking by accretion (`031-DL` RK4) | D-4 `const: report_only` in schema; loader rejects `mode: blocking`; U11 asserts exit 0 even when a detector reports `failed`. |
| RK4 | Q1's persistence exception widens into a persisted graph or a source of truth | D-5 type-level constraint; report is flat, epoch-keyed, append-only, never read back as authoritative; U10 asserts shape and non-overwrite. |
| RK5 | Duplicated cycle-detection logic (D-3) drifts from `topology.py` | Deliberate and recorded; U10 tests the behavior independently. The alternative — refactoring P-001/P-016 enforcement code — is materially worse. |
| RK6 | Schema extension breaks existing config consumers | Block is optional; absent block = zero nodes = today's behavior; back-compat asserted in U9. |
| RK7 | Scope creep from split (b)/(c) — incremental evaluation, shipment attachment, waivers, visualization | Enumerated as hard non-goals; `NodeSpec` carries no waiver field; assembler has no shipment-attachment surface. |
| RK8 | `ART-01` mutates `.backlogit/**` | Producer is read-only by construction; Q9 asserts zero backlogit change. |
| RK9 | Retro-validation requires network access to historical PRs | Historical defects are reconstructed as **local fixtures**; no network in tests. |

## Plan Hardening Signals (REQUIRED)

* **Public API, schema, or contract change** — **PRESENT**. New public CLI
  subcommand `gate pre-review`; new `detectors` schema block; a new inter-module
  contract (`NodeSpec`/`Evidence`/`NodeResult`) that S2-S10 will all depend on.
* **Security, auth, permission, or compliance-sensitive behavior** — **PRESENT**.
  `producer.kind` includes `command`; ref resolution imports callables named in
  configuration — an injection/arbitrary-import surface.
* **Migration, backfill, destructive data/config action, or irreversible step** —
  **PRESENT (bounded)**. New write surface `.autoharness/gates/pre-review/` under
  the Q1 exception. No migration, no backfill, no deletion.
* **External integration, operator checkpoint, or external dependency** —
  **PRESENT**. Q1 is an operator-granted architectural exception with a named
  condition; RK1's falsification gate is an operator checkpoint.
* **High runtime, rollout, or rollback risk** — **PRESENT**. This is the
  foundation four tier-1 shipments plug into; a wrong contract propagates.

**Requires plan hardening: yes**

## Runtime Verification and Closure

* **Runtime surface changed?** Yes — CLI. `autoharness gate pre-review` is a new
  public subcommand.
* **Runtime verification**: `gate pre-review` runs against a real diff and emits
  a schema-valid report; `--json` parses; a registry with an injected cycle exits
  2 and evaluates nothing; a `failed` `ART-01` still exits 0.
* **Gate command (Q5)**: `PYTHONPATH=src python -m unittest discover -s tests`.
* **Operational closure artifact**: closure record naming the report path
  convention, the Q1 consumer condition (S8 must wire a named consumer or the
  writer must be withdrawn), the RK1 retro-validation outcome, and confirmation
  that zero backlogit change occurred.
* **Rollback trigger**: RK1 falsification fails; or exit-code invariance breaks
  (anything other than 0/2 escapes); or the report is found to be read back as
  authoritative input.

---

## Plan Hardening

**Hardening pass — 2026-08-27. Mandatory: critical new abstraction; 5 of 5
signals present (P-006).**

### Protected invariants

| Invariant | Guard |
|---|---|
| **INV-1 — No persisted graph (Law 1)** | Report writer accepts `Sequence[NodeResult]` only and is structurally incapable of receiving edges (D-5). Assembler holds the graph in local scope and returns results, never a graph object. U10 asserts the on-disk artifact is a flat list. |
| **INV-2 — Report is derived evidence, never the source of truth (Q1)** | The report module exposes **no read-back API** in S1. Verdicts are computed only from freshly produced evidence. A future read-back is an S8 decision, not an S1 capability. |
| **INV-3 — Report-only; exit 0 except invalid registry** | `const: report_only` in schema (D-4); loader rejects `blocking`; the report emitter has no return path into the exit code; U11 asserts exit 0 on `failed`. |
| **INV-4 — Cycle never auto-broken** | Cycle -> `invalid` -> exit 2 -> **zero nodes evaluated**. U10 asserts the evaluation count is exactly zero, not merely that the exit code is 2. |
| **INV-5 — FC1 never degrades to `not_applicable`** | Base ref resolved before discovery (D-7); U9 asserts the unresolvable-base path yields `insufficient_evidence`. |
| **INV-6 — Exactly one detector** | U11 asserts the shipped registry contains exactly one node. A second detector fails the test — structural enforcement of the S1/S2 boundary. |
| **INV-7 — Zero backlogit mutation** | `ART-01` opens `.backlogit/**` read-only; U11 asserts file mtimes/content unchanged after a run. |

### Risky actions (ProposedAction / ActionRisk / ActionResult)

| ProposedAction | ActionRisk | Required ActionResult |
|---|---|---|
| Resolve `producer.ref` / `validator.ref` to importable callables from config | **HIGH** — arbitrary-import surface driven by configuration | **Allow-list containment**: refs MUST resolve **inside the `autoharness.detectors` package namespace**. Any ref outside it is a **registry defect -> `invalid` -> exit 2**, never imported. Asserted in U9. |
| `producer.kind: command` declared in the schema | **HIGH** — subprocess surface | **`command` is schema-declared but NOT implemented in S1.** `ART-01` is `kind: pure`. A registry declaring `kind: command` yields `invalid` in this shipment. Subprocess execution, if ever added, must reuse `gates/runner.py`'s argv-tokenization-before-substitution invariant — it is out of scope here. |
| Create the write surface `.autoharness/gates/pre-review/` | **MEDIUM** — Q1 exception | Path is fixed, epoch-keyed, append-only, never overwritten, never deleted. Q1's condition is recorded in closure: **if S8 wires no named consumer, the writer must be withdrawn** (D9 / Law 2). |
| Add a public CLI subcommand | **MEDIUM** — public surface, permanent | Follows `dag-readiness` shape; read-only; `--help` before parsing; invalid args exit 2. |
| Establish the contract S2-S10 depend on | **HIGH** — a wrong contract propagates to four tier-1 shipments | Vocabulary closed at 8 verdicts; `NodeResult` mirrors the existing `CheckResult` shape; no field added that S1 does not itself exercise, except `waived` (D-6, asserted unreachable). |
| Duplicate cycle-detection logic (D-3) | **LOW-MEDIUM** — drift | Deliberate, recorded, independently tested. Explicitly preferred over refactoring P-001/P-016 enforcement code. |

**Explicitly forbidden in this shipment**: any second detector; any `mode` other
than `report_only`; any waiver field or logic; any read-back of the report as
authoritative; any persisted graph or derived topology on disk; any backlogit
mutation; any change to `compute_next_eligible` or shipment topology; any ref
importing outside `autoharness.detectors`; any implementation of
`producer.kind: command`; any network access in tests.

### Added verification detail

1. **Contract-freeze check**: U9 asserts the verdict vocabulary is exactly the 8
   named values — an added verdict fails the suite, so S2-S10 cannot widen the
   contract silently.
2. **Zero-evaluation assertion on cycle** (INV-4) — count, not just exit code.
3. **Exit-code invariance sweep**: across every fixture, the only observed exit
   codes are 0 and 2. Any 1 or 3 is a hard stop.
4. **Read-only assertion** for `ART-01` (INV-7).
5. **Back-compat assertion**: an existing config with no `detectors` block still
   validates and yields zero nodes at exit 0.
6. **RK1 falsification is a gate, not a metric**: if no historical defect is
   re-detected, **halt the shipment and escalate to the operator** for the
   Option A reconsideration. This does not authorize proceeding with a weaker
   claim.

### Rollback and monitoring

* **Rollback order** (reverse dependency): U8 CLI registration -> U7 report
  writer + delete `.autoharness/gates/pre-review/` -> U6 `ART-01` -> U5 assembler
  -> U4 applicability -> U3 loader -> U2 schema block -> U1 contract. Every step
  is additive-file removal or a single-block schema revert; **no migration and
  nothing irreversible**, because nothing derived is authoritative (INV-2).
* **Rollback triggers**: RK1 falsification failure; any exit code outside {0,2};
  discovery that the report is consumed as authoritative; any detected backlogit
  mutation.
* **Monitoring window**: the first S2 detector authored against this contract is
  the real test of whether the SDK is usable — if S2's first detector needs a
  contract change, that is the RK1 signal arriving late.

### Review-gate capability risk (P-012), carried into plan review

S0 has not executed yet, so `.github/agents/subagents/` still does not exist and
reviewer subagent dispatch remains genuinely unavailable for **this** plan's
review. Plan review must declare
`dispatch_mode: single-agent-declared-degradation`, cover every selected persona
inline, and emit both literal markers. **After S0 lands, a future review of a
successor plan should be able to use real dispatch — if it still cannot, S0 did
not close GAP 2.**

---

## Plan Review

**Reviewed**: 2026-08-27 · **Plan**: `docs/plans/2026-08-27-pre-review-detector-sdk-plan.md`

### Dispatch capability (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`
  — `.github/agents/subagents/` does not exist (S0 GAP 2, not yet executed).
  Probed by direct path existence check.
* `TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass`
* `TOOL_DEGRADED: agent-intercom — operator visibility reduced`
* `ENGRAM_DEGRADED` / `GRAPHTOR_UNAVAILABLE` — file-based retrieval used.

**Every selected persona was covered inline.** No persona was dropped. Because
this plan touches a security-sensitive import surface and a new public contract,
the conditional cross-model personas (Security Lens, Agent-Native Parity) were
triggered and covered.

```text
dispatch_mode: single-agent-declared-degradation
```

### Persona findings (P0-P3)

| Persona | Finding | Sev | Disposition |
|---|---|---|---|
| Security Lens Reviewer | **`producer.ref` / `validator.ref` resolve importable callables from configuration — arbitrary-import surface.** Without containment this is a P0 blocker: a registry edit becomes code execution. | **P0 -> mitigated** | **Addressed in hardening before review**: refs MUST resolve inside `autoharness.detectors`; anything else is `invalid` -> exit 2, never imported. Asserted in U9. **Verdict contingent on this containment remaining in the built artifact.** |
| Security Lens Reviewer | `producer.kind: command` declares a subprocess surface. | **P1 -> mitigated** | Schema-declared but **not implemented** in S1; a `command` registry is `invalid`. If ever implemented it must reuse `gates/runner.py`'s tokenize-before-substitute invariant. |
| Security Lens Reviewer | Report path is fixed and epoch-keyed; no user-controlled path component; no secrets written. | — | PASS |
| Constitution Reviewer | Law 1 is enforced **by type** (D-5) rather than by convention — the strongest available form. | — | PASS (strength) |
| Constitution Reviewer | Law 2: query/visualization pruned; adapter extension points deferred; the Q1 writer carries an explicit withdrawal condition if S8 wires no consumer. | — | PASS |
| Constitution Reviewer | `mode` as schema `const` makes silent promotion structurally impossible rather than merely discouraged (RK4). | — | PASS (strength) |
| Architecture Strategist | **D-3 duplicates cycle detection instead of generalizing `topology.py`.** Duplication is normally a defect. | P2 | **Justified.** `_dag_detect_cycle` is typed to `ShipmentState` inside a 96 KB module that enforces P-001/P-016. Generalizing it would push S1's blast radius into shipment-topology enforcement. ~20 lines of proven algorithm, independently tested, explicitly recorded. Accepted. |
| Architecture Strategist | Contract stability is the real risk — S2-S10 all depend on `NodeSpec`/`NodeResult`. | P1 | **Addressed** by the contract-freeze check (verification 1) and by the monitoring trigger: if S2's first detector needs a contract change, that is the RK1 signal. |
| Architecture Strategist | `NodeResult` mirrors rather than subclasses `CheckResult` (D-1) — correct coupling call. | — | PASS |
| Python Reviewer | Frozen dataclasses with `to_dict()` match the established `CheckResult`/`GateResult`/`TopologyResult` convention. | — | PASS |
| Python Reviewer | **The `discover_modified_files` empty-list ambiguity is a genuine latent trap** — it never raises and returns `[]` on git failure, so "clean tree" and "git broken" are indistinguishable. | P1 | **Addressed** by D-7 (resolve base before discovery) and U9's explicit unresolvable-base test. This finding is called out in the plan body rather than left implicit — good. |
| Python Reviewer | 11 units, single-domain each, max 3 files, max 4 test scenarios — within granularity budget. | — | PASS |
| Scope Boundary Auditor | Splits (b) and (c) of `89E833E1` are enumerated as hard non-goals, and `NodeSpec` carries no waiver field — the boundary is structural, not merely stated. | — | PASS (strength) |
| Scope Boundary Auditor | INV-6 asserts **exactly one** detector, making the S1/S2 boundary a failing test rather than a promise. | — | PASS (strength) |
| Scope Boundary Auditor | Schema declares fields (`kind: command`, `waived`) that S1 does not implement — mild YAGNI. | P3 | Accepted: both are explicitly unreachable and asserted so, which keeps the vocabulary closed for S10 without importing its authority. |
| Learnings Researcher | `docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md` — the "defined but not wired" class. Applies directly: a registry whose nodes are never actually evaluated would present as passing. | P2 | **Addressed** by INV-4's zero-evaluation *count* assertion and by U11's end-to-end run, which asserts a real verdict rather than a clean exit. |
| Learnings Researcher | `docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md` — structural parsing beats line regex. `ART-01` parses marker **pairs** structurally (ordering, nesting, duplication) rather than grepping for `BEGIN:`. | — | PASS (alignment) |
| Learnings Researcher | `docs/compound/093-S-review-loop-convergence.md` and `2026-08-07-copilot-review-fix-introduces-new-filter-bug.md` — the fix-regenerates-the-family mechanism. S1 ships no auto-fix, so the mechanism is not reachable here. | — | PASS |
| Agent-Native Parity Reviewer | New CLI surface follows the `dag-readiness` precedent including degraded-payload synthesis; `--json` gives agents a machine-readable path at parity with the human report. | — | PASS |
| Agent-Native Parity Reviewer | The gate is read-only and advisory; it adds no agent-facing authority. | — | PASS |

### Verdict rationale

One P0 was raised (config-driven arbitrary import) and it is **fully contained by
a namespace allow-list that was written into the hardening section before review
and is asserted by a test in U9** — the verdict is contingent on that containment
surviving into the built artifact, and U9 is the enforcement. The three P1
findings (subprocess surface, contract stability, discovery ambiguity) each have
a concrete structural mitigation rather than a promised follow-up. The single P2
duplication finding is justified against a materially worse alternative.

Granularity, width isolation, and the 2-hour rule hold across all 11 units. Every
architectural law from `031-DL` is enforced structurally — by type signature,
schema `const`, or failing test — rather than by prose.

```text
decision: PASS
```
