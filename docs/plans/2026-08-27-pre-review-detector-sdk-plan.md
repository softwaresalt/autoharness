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
  (`name`,`status`,`token`,`message`,`details`) **plus** `provenance` and
  `excluded_by` (FC2). `to_dict()` matches the existing convention.
* **ONE canonical outcome field (D-9)**: `status` carries the full outcome
  vocabulary. There is **no independent `verdict` field**. `CheckResult.status`
  is an unconstrained `str` (`gates/topology.py:130-142`) and consumers already
  branch on `.status` directly, so widening the vocabulary of that one field is
  exactly D5's stated intent — *"reuses `CheckResult{...}` unchanged; the
  extension is additional statuses"*.
* **Status vocabulary (8, closed)**: `passed`, `failed`, `insufficient_evidence`,
  `blocked_upstream`, `not_applicable`, `skipped`, `waived`, `invalid`.
  `waived` is **declared but unreachable** in S1 (no waiver engine) and must be
  asserted unreachable in U9.
* **Compatibility alias is derived, never stored**: if a `verdict` name is
  wanted for readability it is a read-only `@property` returning `self.status`.
  It is **not** a dataclass field, is **absent from `to_dict()`**, and takes no
  constructor argument — so a contradictory
  `status="passed" / verdict="failed"` state is **unrepresentable**, not merely
  discouraged.
* **Status -> exit mapping**: report-only column of D5, keyed off `status`
  **only** — everything maps to 0 except `invalid` -> 2.
* **`mode` is constructor-fixed to `report_only`**; `NodeSpec` exposes no setter
  and the registry loader rejects `mode: blocking` (U3).
* **Posture**: test-first.

### U2 — Detector registry schema extension

* **Domain**: schema contract. **Files: 3** (`schemas/validation-gates.schema.json`,
  `schemas/validation-gates/1.0.0.schema.json`,
  `tests/test_validation_gates_schema.py`).
* **BOTH schema files must change together (D-10).** Runtime resolution returns
  the **versioned** file first — `resolve_validation_gates_schema_path()` checks
  `schemas/validation-gates/1.0.0.schema.json` and only falls back to the
  pointer (`schema_contracts.py:511-532`). Editing the pointer alone would leave
  **runtime validation blind to `detectors`** while
  `test_validation_gates_schema.py::test_pointer_schema_mirrors_versioned_schema_except_id`
  — which asserts full dict equality after popping `$id` — **fails outright**.
* Add a top-level optional `detectors` block: array of node declarations with
  `node_id` (pattern-constrained to the D1 scheme), `applies_when`
  (`changed_paths_any`, `shipment_has_items_of_type`, `workspace_surfaces_any`,
  `always`), `producer` (`kind` enum `pure|ast|coverage|api|command`, `ref`,
  `tool_version_dims`), `validator` (`ref`, `consumes`), `depends_on`,
  `severity` enum, `mode` **const `report_only`**, `remediation`
  (`class` enum, `hint`, `target_refs`, `authority` enum).
* `additionalProperties: false` inside each node object so an unknown key is a
  registry defect rather than silent tolerance.
* The two files stay **byte-identical except `$id`**; each keeps the `$id`
  matching its own path.
* **Detector validation cases run against the VERSIONED schema** (the
  runtime-resolved document) — a valid `detectors` block validates, `mode:
  blocking` fails, an unknown per-node key fails, a malformed `node_id` fails —
  plus the existing parity test extended to cover the new block.
* **Backward compatibility**: the whole block is optional; an absent `detectors`
  block means zero nodes and behavior identical to today.
* **Posture**: schema-first. No detector code in this unit. The test file is the
  schema's **own contract test**, co-located by the existing convention — width
  isolation holds because this unit contains no detector runtime logic.

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

### U7 — Report emitter, epoch key, and freshness rule (Q1, D6, D9)

* **Domain**: code. **Files: 1** (`src/autoharness/detectors/report.py`).
* Write `.autoharness/gates/pre-review/<epoch_key>.json` — a **flat list of node
  results**, keyed by immutable epoch, **append-only per epoch, never
  overwritten**.
* **Epoch key (D-11) — HEAD alone is NOT sufficient.** The key is
  `<head_sha>-<fingerprint>` where `<fingerprint>` is the first 16 hex chars of
  `SHA-256` over a **canonical** serialization (JSON, `sort_keys=True`, no
  whitespace, UTF-8) of every freshness dimension the report depends on:
  * the detector-registry version and the validation-gates schema version, and
  * the resolved values of all declared `producer.tool_version_dims`, sorted.
  Same inputs -> same key on every platform and process (deterministic); any
  freshness-relevant change -> a **different** key.
* **Why**: with `<head_sha>.json` alone, changing a `tool_version_dims` value
  makes the sole persisted report **stale**, while append-only-never-overwrite
  **prevents a rerun from writing fresh evidence at that same HEAD**. Consumers
  would be pinned at `insufficient_evidence` until an unrelated commit moved
  HEAD. Folding the fingerprint into the key dissolves the deadlock without
  weakening immutability: nothing is ever mutated or replaced, a *new* file is
  written under a *new* key.
* **Consumer selection rule**: a consumer **computes** the expected key from
  current HEAD plus the current fingerprint and reads **exactly that path**. It
  never scans-and-guesses. Because the key is a pure function of the freshness
  dimensions, **at most one** report can match, so "the current report" is
  unique by construction.
* **Stale siblings**: other `<head_sha>-*.json` files at the same HEAD remain on
  disk as **history** and are **never consumable as fresh** — their key cannot
  equal the computed current key. Rejection is **structural (key mismatch)**,
  not a comparison a consumer could forget to perform.
* **Rerun at unchanged HEAD after a tool-version change** therefore writes a new
  fresh file under a new key, with **no overwrite and no data loss**.
* **Concurrency / idempotence — no-clobber publication (D-13)**: a same-key write
  is idempotent, and `os.replace` is **NOT** an allowed strategy. It is defined to
  replace an existing destination, so at the same key it destroys the prior report
  — a direct contradiction of `append-only, never overwritten` above. The protocol
  is **exclusive claim, then atomic publish**: serialize to a unique temp file in
  the target directory, `fsync`, then `os.link(tmp, final)` (atomic; raises
  `FileExistsError` rather than clobbering), unlinking the temp in `finally`.
  `FileExistsError` is **success** and the existing file is left byte-for-byte
  untouched.
* **NO DIRECT-TO-FINAL FALLBACK (D-15, cycle-3 thread `PRRT_kwDORzpWpM6dVfzE`)**:
  where atomic no-replace linking is unavailable, the emitter **fails without
  publishing** and reports a non-fatal publication failure. Claiming the final
  pathname with `os.open(final, O_CREAT|O_EXCL|O_WRONLY)` — the cycle-2 fallback —
  is now **FORBIDDEN**, because it publishes the final pathname *before* the
  payload is complete. Absence of a report is a **safe, self-healing** state
  (the consumer computes `insufficient_evidence` and the next run retries
  cleanly); a *partial* report at the final path is **not**.
* **Payloads at one key are NOT byte-identical**: `provenance.produced_at` is
  wall-clock RFC3339. The cycle-1 justification that "content is deterministic per
  key" was **false** — determinism holds for the *key*, not the *payload* — which
  is precisely why no-clobber is load-bearing rather than cosmetic. A published
  report is always one whole payload from one writer.
* **Torn-file containment — complete-or-absent is UNCONDITIONAL (D-15)**: the
  only publication path is `os.link` from a fully-written, fsynced temp, so the
  final path is **always** complete-or-absent and no code path can leave a
  partial file at the final pathname. The consumer rule that an **unparseable
  report is `insufficient_evidence`** is retained as defence in depth against
  *external* corruption — never evidence, never repaired in place — but it is no
  longer load-bearing for the emitter's own failure modes.
* `provenance`: `base_sha`, `head_sha`, `epoch_key`, `fingerprint`,
  `reviewed_sha` (nullable), `platform`, `tool_versions`, `produced_at`
  (RFC3339), and `touches_reviewable_paths: bool`.
* **Freshness (D6, unchanged in meaning)**: a result is fresh iff its `head_sha`
  equals current HEAD **and** every dimension in `producer.tool_version_dims` is
  unchanged. Both conditions are now **encoded in the key itself**. A stale
  result is **`insufficient_evidence`**, never a reused `passed`.
* **Q1 boundary, asserted in code (UNCHANGED)**: the report is **derived
  evidence, not the source of truth**. It is never read back as authoritative
  input to a verdict in this shipment, and **S1 ships no read-back API** — the
  selection rule above is a *specification* for the S8 consumer plus a tested
  pure key-computation function, **not** a production read path. Regeneration
  from the tree at that SHA must remain possible. The emitter has **no blocking
  authority** and cannot influence the exit code.
* **Not a graph (Law 1, UNCHANGED)**: the writer accepts a flat sequence of
  `NodeResult` and has no access to edges — the type signature makes a persisted
  graph unrepresentable. Derive-never-persist still holds for the graph itself;
  only the derived *report* is persisted, under the Q1 exception.
* **Posture**: test-first. **Depends on U1.**

### U8 — `gate pre-review` CLI wiring

* **Domain**: CLI. **Files: 1** (`src/autoharness/cli.py`).
* Register `pre-review` in `_gate_command` dispatch; add
  `_gate_pre_review_command(rest)` and `_parse_gate_pre_review_args`;
  extend `GATE_USAGE`.
* Flags: `--json`, `--base <ref>`; `--help`/`-h` prints usage and returns.
* **Option-safe `--base` handling (D-12)**: `--base` is user-controlled. The CLI
  MUST call the U8b resolver **before** any discovery call and pass **only the
  validated 40-char hex SHA** onward. Raw user ref text is **never** interpolated
  into a `git diff` argument.
* **Rejection is the invalid-input exit class (exit 2) with NO side effect** —
  no `git diff` invocation, no file written, no report emitted.
* Follows the `_gate_dag_readiness_command` shape exactly, including the
  **degraded-payload synthesis** precedent (never fabricate a graph).
* **Exit codes**: 0 always; 2 for invalid arguments (including an unsafe or
  unresolvable `--base`) **or** invalid registry.
* **Posture**: characterization-first against the existing `dag-readiness` CLI
  tests. **Depends on U3, U5, U6, U7, U8b.**

### U8b — Option-safe Git ref resolution (security)

* **Domain**: code (security). **Files: 2** (`src/autoharness/gates/discovery.py`,
  `src/autoharness/gates/gate.py`).
* **The vulnerability**: `discover_modified_files` builds
  `["git","diff","--name-only", f"{base}...{head}"]` (`gates/discovery.py:61`)
  with **no option terminator**. A `--base` of `--output=/tmp/x` yields the
  argument `--output=/tmp/x...HEAD`, which `git diff` parses as its
  **`--output=<file>` option and writes a file** — directly contradicting this
  gate's read-only guarantee.
* Add `resolve_commit_ref(ref) -> str | None`: run
  `git rev-parse --verify --end-of-options <ref>^{commit}`, and accept the result
  **only** if it matches `^[0-9a-f]{40}$`. Anything else returns `None`
  (unresolvable/unsafe) — including option-like refs, which `--end-of-options`
  forces git to treat as a ref rather than a flag.
* Harden `discover_modified_files` itself: assert its `base`/`head` arguments are
  validated full hex SHAs, and add the `--end-of-options` / `--` separators so
  the module is safe **even if a future caller forgets to pre-resolve**. Defence
  in depth — the resolver is the primary control, this is the backstop.
* Applies to **every** user-controlled ref, head as well as base.
* **Read-only**: resolution performs no mutation and writes no file.
* **Input-contract change is BREAKING for symbolic-ref callers, and is
  characterized rather than assumed.** `discover_modified_files` no longer accepts
  `main`/`HEAD`/branch/tag; callers pre-resolve. Symbolic-ref handling is not
  removed from the system — it moves **up** into `resolve_commit_ref`, the single
  place allowed to invoke `git rev-parse`. Retaining symbolic-ref compatibility
  inside `discover_modified_files` was considered and **rejected**: it reopens the
  hole D-12 closes by letting unvalidated ref text reach `git diff`.
* **Blast radius on the existing suite**: `tests/test_gates_discovery.py` calls
  `discover_modified_files("main", "HEAD", ...)` at lines 32/40/49 and pins the
  exact pre-change argv at line 45. All four assertions fail under this contract,
  so the canonical Q5 gate goes red. That file is in **U8c**'s scope (tests
  domain — folding it here would breach U8b's width isolation), and U8b is not
  complete while it is red.
* **PRODUCTION CALLERS *ARE* AFFECTED — cycle-2 claim RETRACTED (D-17, cycle-3
  thread `PRRT_kwDORzpWpM6dVfzg`)**. The cycle-1/cycle-2 assertion that "the only
  production caller, `gates/gate.py:77`, passes internally-derived refs and is
  unaffected" is **FALSE on two counts**, verified against current `main`:
  * `gate.py::check` declares **`head: str = "HEAD"`** (`gates/gate.py:65`) and
    forwards `base`/`head` **unresolved** straight into `discover_fn(base, head,
    cwd=cwd)` (`gates/gate.py:77`). `"HEAD"` is a *symbolic* ref, so every
    `check(config, base_sha)` call that relies on the default head breaks under
    U8b's hex-only contract.
  * The shipped CLI path `autoharness gate check` reaches that default: `cli.py:290`
    defaults `parsed["head"]` to `"HEAD"` and `cli.py:400-405` passes it through.
    So the break is reachable from a **released command**, not just from
    hypothetical library callers.
* **Fix — resolve at the `check()` boundary, do NOT weaken discovery.** `check()`
  resolves `base` and `head` through `resolve_commit_ref` **after** its
  no-gates/disabled early return and **before** `discover_fn`, passing only
  validated 40-hex SHAs onward; an unresolvable/unsafe ref is rejected there with
  no `git diff` and no side effect. Retaining symbolic-ref tolerance inside
  `discover_modified_files` remains **rejected** (it reopens the D-12 hole); the
  ref→SHA conversion moves *up* to the boundary, exactly as D-12 intends.
* **Early-return ordering is load-bearing**: `test_gates_gate.py:86` calls
  `check(GatesConfig(enabled=False), base="main")` with a symbolic ref and must
  keep returning an empty report **without** resolving, so resolution must sit
  after the `not config.enabled or not config.validation_gates` guard.
* **Posture**: test-first. **No dependencies** — self-contained hardening of two
  existing modules in one domain, schedulable first. **Lands together with U8c**
  (U8b is not complete while the Q5 gate is red on `test_gates_discovery.py` or
  `test_gates_gate.py`). Cycle 3 raises **size S -> M** (Files 1 -> 2); complexity
  stays **medium**.

### U9 — Tests: contract, registry, applicability

* **Domain**: tests. **Files: 3** (`tests/test_detectors_contract.py`,
  `tests/test_detectors_registry.py`, `tests/test_detectors_applicability.py`).
* Scenarios (4): status->exit mapping incl. `waived` unreachable **and the
  canonical-field contract — `verdict` is absent from `dataclasses.fields()` and
  from `to_dict()`, any `verdict` property always equals `status`, and no
  constructor path can produce a contradictory pair**; registry rejects
  `mode: blocking` / duplicate / unknown ref -> `invalid`; absent
  registry -> zero nodes, exit 0; **FC1 (engine layer, D-14) — a context that
  cannot be built from *already-validated* input -> `insufficient_evidence`
  (explicitly NOT `not_applicable`)** and FC2 records `excluded_by`. FC1 is driven
  against the engine directly; an unsafe/unresolvable **user** `--base` exits 2 at
  the CLI and never reaches here.

### U10 — Tests: assembler and cycle detection

* **Domain**: tests. **Files: 1** (`tests/test_detectors_assembler.py`).
* Scenarios (2): cycle injection -> `invalid`, exit 2, **zero nodes evaluated**;
  upstream `failed` **and** upstream `insufficient_evidence` -> downstream
  `blocked_upstream` (not `passed`/`skipped`).
* **Depends on U5.**

### U10b — Tests: report shape and freshness semantics

* **Domain**: tests. **Files: 1** (`tests/test_detectors_report.py`).
* Scenarios (4): report is a flat list with **no edge/topology data**;
  a second run at the same epoch key does **not** overwrite; stale `head_sha`
  -> `insufficient_evidence`; changed `tool_version_dims`
  -> `insufficient_evidence`, never a reused `passed`.
* **Depends on U7.**

### U10c — Tests: epoch-key determinism, staleness, and concurrency

* **Domain**: tests. **Files: 1** (`tests/test_detectors_report_epoch.py`).
* Scenarios (4), all targeting the D-11 defect class directly:
  1. **Deterministic fingerprinting** — identical freshness dimensions produce
     an identical key across processes and across input orderings; any changed
     dimension produces a different key.
  2. **Refresh at unchanged HEAD** — after a `tool_version_dims` change at the
     *same* HEAD, a rerun writes a **new fresh report** under a new key, the
     prior file is **not** overwritten, and the consumer is **not** left at
     `insufficient_evidence`. This is the regression test for the reported bug.
  3. **Stale sibling rejection** — a sibling report at the same HEAD with a
     different fingerprint is retained as history and is **never** selected as
     the current fresh report.
  4. **Concurrent / idempotent same-key writes, and no-clobber (D-16)** — two
     *real* concurrent writers at the same key yield exactly one well-formed,
     non-corrupt, non-duplicated report, and **either** complete payload may win
     the race. The race winner is **NOT** asserted. No-clobber is then proved
     **deterministically** in a second, serialized phase: after the race settles,
     record the published bytes and `st_mtime`, issue a **distinguishable**
     third write at the same key (a payload whose `provenance.produced_at` — and
     therefore whose bytes — differ from the published one), and assert that the
     call **reports success** while the published **bytes and `st_mtime` are
     both unchanged**. That is the assertion that fails on a last-writer-wins
     emitter.
* **Depends on U7.**

### U11 — Tests: `ART-01` retro-validation and CLI acceptance

* **Domain**: tests. **Files: 2** (`tests/test_detectors_art_section_markers.py`,
  `tests/test_gate_pre_review_cli.py`).
* Scenarios (4): `ART-01` flags a fixture artifact with a missing/unpaired
  marker and passes a conformant one; **retro-validation** — `ART-01` re-detects
  at least one historical defect from PR #234 / #185 / #183 / #189 / #202 /
  #123 / #213 (reconstructed as a fixture, no network); `gate pre-review --json`
  emits a schema-valid report and **exits 0 even when `ART-01` reports `failed`**;
  a valid `--base <ref>` is honored (resolved to a 40-hex SHA before discovery)
  while an **unsafe or unresolvable** `--base` is rejected with the invalid-input
  class — **exit 2, no `git diff`, no report** (D-12). `insufficient_evidence` is
  **not** an expected outcome at this boundary; it is the applicability-engine
  **FC1** outcome, asserted in U9 scenario 4.
* **RK1 falsification gate**: if `ART-01` cannot re-detect **any** listed
  historical defect, that is the designed early exit — **halt and reconsider
  Option A (independent gates)** rather than shipping an unjustified SDK.
* **Gate command (Q5)**: `PYTHONPATH=src python -m unittest discover -s tests`.

### U8c — Tests: option-safe ref resolution (security)

* **Domain**: tests. **Files: 3** (`tests/test_gate_ref_safety.py` — new;
  `tests/test_gates_discovery.py` — re-characterized;
  `tests/test_gates_gate.py` — re-characterized, cycle-3 D-17).
* Scenarios (4):
  1. **Option-like refs are rejected** — `--output=<tmp>`, `--upload-pack=...`,
     and a leading-dash ref all resolve to `None`, produce the invalid-input
     exit class, and — asserted explicitly — **the would-be output file does not
     exist afterwards** (no side effect).
  2. **Invalid refs** (nonexistent branch/SHA) are rejected with the same class.
  3. **Valid symbolic refs** (`HEAD`, `HEAD~1`, a branch, a tag) resolve to a
     full 40-char hex SHA.
  4. **Full-SHA pass-through** — an already-full SHA resolves to itself, and
     `discover_modified_files` receives only validated hex SHAs.
* **Plus existing-suite reconciliation** (a mechanical update to an existing file,
  not a fifth scenario): `tests/test_gates_discovery.py` is updated so the Q5 gate
  passes under U8b's contract — the three call sites pass validated 40-hex SHAs,
  the exact-argv assertion is updated to the option-safe argv, and one new
  assertion pins the **rejection of a symbolic ref** passed directly to
  `discover_modified_files`. The two graceful-degradation tests still assert
  `[]` + warning (deliberately unchanged, asserted not assumed); the
  `parse_diff_output` tests are untouched (no ref surface).
* **Plus `tests/test_gates_gate.py` reconciliation (D-17, cycle-3 thread
  `PRRT_kwDORzpWpM6dVfzg`)** — bounded and enumerated, **two** edits and **one**
  addition:
  * `test_check_uses_injected_discover` (line ~90) currently asserts the injected
    discover receives `captured["base"] == "main"`. Under D-17 `check()` resolves
    first, so the assertion is re-characterized to pin that the injected discover
    receives **validated 40-hex SHAs**, not the raw symbolic text.
  * `test_check_no_gates_returns_empty_report` (line ~86) is asserted **unchanged**
    — it must still return an empty report for a symbolic `base="main"` without
    resolving, proving the early return precedes resolution.
  * **One new assertion**: `check()` with an unresolvable/option-like `base`
    rejects with the invalid-input class, invokes **no** `git diff`, and writes
    **no** file.
* **Depends on U8b.** Scenario count stays at 4; Files rises 2 -> 3, at the
  ceiling of the max-3 budget. Because the file count and the reconciliation
  surface both grew in cycle 3, **size is raised S -> M and complexity low ->
  medium**; the 2-hour rule still holds because all three additions are
  characterization edits against an existing suite, not new test design.

## Dependency Graph

```text
U1  ──> U3  ──> U5 ──> U8
U2  ──> U3
U1  ──> U4  ──> U6 ──> U8
U1  ──> U7  ──> U8
U8b ──> U8
U8b ──> U4          (D-7: base resolved before discovery)
U1,U3,U4  ──> U9
U5        ──> U10
U7        ──> U10b
U7        ──> U10c
U6,U8     ──> U11
U8b       ──> U8c
```

Serial order:
`U8b -> U1 -> U2 -> U3 -> U4 -> U5 -> U6 -> U7 -> U8 -> U8c -> U9 -> U10 -> U10b -> U10c -> U11`.

`U8b` is a self-contained hardening of an existing module with no dependencies,
so it is scheduled first and unblocks both `U4` and `U8`.

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
| D-9 | **One canonical outcome field: `status`.** No independent `verdict` field; any `verdict` is a derived read-only property equal to `status`, absent from `to_dict()` | Two independent fields with no invariant between them can serialize `status="passed"` with `verdict="failed"`, leaving exit mapping and consumers ambiguous. D5 governs this as *"reuses `CheckResult` unchanged; the extension is additional statuses"* — i.e. a **widened vocabulary on one field**, not a second field. `CheckResult.status` is an unconstrained `str` and consumers already branch on `.status`, so one field is both compatible and sufficient. Contradiction becomes **unrepresentable** rather than merely tested-against. |
| D-10 | **The `detectors` block is added to BOTH the pointer and the versioned schema in the same unit** | `resolve_validation_gates_schema_path()` returns `schemas/validation-gates/1.0.0.schema.json` **first** and only falls back to the pointer (`schema_contracts.py:511-532`), so a pointer-only edit leaves **runtime validation blind to `detectors`**. Independently, `test_pointer_schema_mirrors_versioned_schema_except_id` asserts full dict equality after popping `$id`, so a pointer-only edit **fails the existing suite**. The two files are one atomic contract. |
| D-11 | **Epoch key is `<head_sha>-<fingerprint>`**, not `<head_sha>` alone | HEAD alone conflicts with the D6 freshness rule: change a `tool_version_dims` value and the sole persisted report is stale, while append-only-never-overwrite blocks a rerun from writing fresh evidence at that same HEAD — pinning consumers at `insufficient_evidence` until an unrelated commit moves HEAD. Folding a canonical fingerprint of all freshness dimensions into the key makes freshness and identity the *same* predicate: a new dimension set writes a **new** file under a **new** key. Immutability is strengthened, not weakened — nothing is ever mutated or replaced. |
| D-12 | **User-controlled Git refs are resolved with `git rev-parse --verify --end-of-options <ref>^{commit}` and validated to `^[0-9a-f]{40}$` before any use** | `discover_modified_files` interpolates `base` into `f"{base}...{head}"` with no option terminator (`gates/discovery.py:61`), so `--base=--output=/path` is parsed by `git diff` as its `--output` option and **writes a file**, breaking the gate's read-only guarantee. Resolving first and passing only a validated hex SHA removes the injection surface entirely; the `--end-of-options`/`--` backstop inside discovery is defence in depth. |
| D-13 | **Report publication is a no-clobber exclusive claim plus atomic publish; `os.replace` is forbidden** | Cycle 1 offered `os.replace` *or* `O_EXCL` as interchangeable. They are not. `os.replace` is defined to replace an existing destination, so at the same epoch key it destroys immutable evidence -- a direct contradiction of the `append-only, never overwritten` clause in the same unit. The justification offered ("content is deterministic per key") is **false**: `provenance.produced_at` is wall-clock RFC3339, so two writers at one key produce different bytes, making `os.replace` a last-writer-wins overwrite rather than a benign idempotent write. Publication is now: temp file in the target dir -> `fsync` -> `os.link(tmp, final)` (atomic, raises `FileExistsError` instead of clobbering), with `os.open(final, O_CREAT|O_EXCL|O_WRONLY)` as the no-hardlink fallback; `FileExistsError` is **success** and the existing file is untouched. A published report becomes unreachable by any write path. |
| D-14 | **The exit-2 (CLI boundary) and `insufficient_evidence` (FC1) outcomes belong to different layers and are never asserted for the same input** | U11 scenario 4 expected `insufficient_evidence` at exit 0 for an unresolvable `--base`, while U8/U8b/U8c require exit 2 with no report for exactly that input -- the two suites were mutually unsatisfiable. The boundary: **user-controlled ref text** is validated at the CLI and an unsafe/unresolvable value exits **2** before any discovery call or side effect (D-12); **FC1** is the applicability engine's fail-closed outcome when a context cannot be built from *already-validated* input (unreadable manifest, missing profile, internally-derived base that fails to resolve) and yields `insufficient_evidence` for every node, explicitly NOT `not_applicable` (D-7). The CLI path can never reach FC1 with bad user input because it exits first. |
| D-15 | **There is NO direct-to-final publication fallback. Where atomic no-replace linking is unavailable, the emitter fails WITHOUT publishing** | D-13's `os.open(final, O_CREAT\|O_EXCL\|O_WRONLY)` fallback claims the **final pathname before the payload is written**. A writer that dies mid-write therefore leaves a *partial* file at the very path consumers read, and — because D-13 also makes `FileExistsError` mean **success** — every subsequent retry short-circuits as already-published and never repairs it. Since the report is append-only and may never be repaired in place, that epoch key is **permanently stranded at `insufficient_evidence`**: exactly the refresh deadlock D-11 was created to dissolve, reintroduced through the back door. The key only recovers if HEAD or the fingerprint changes, which is outside the writer's control. Failing without publication keeps the unit's own **complete-or-absent** contract unconditional, and absence is *self-healing* (the next run simply retries) whereas a partial file is *terminal*. |
| D-16 | **U10c scenario 4 asserts no-clobber via an mtime+bytes-stable third write, NOT by pinning the race winner to the "first" writer** | The cycle-2 wording required the published bytes to equal the **first** writer's payload. No such writer is identifiable: with `os.link`, thread/process *start* order does not determine which claim the kernel accepts, so a **correct** no-clobber emitter fails that assertion nondeterministically — a flaky test that punishes correct implementations. The property actually under test is *no-clobber*, not *ordering*. Letting either complete payload win the race and then proving that a subsequent **distinguishable** same-key write leaves **bytes and `st_mtime` unchanged** tests exactly that property, deterministically and without a race. `provenance.produced_at` still supplies the distinguishability that makes an overwrite visible, which was the sound half of the cycle-2 correction and is retained. |
| D-17 | **`gate.py::check` resolves `base`/`head` at the boundary; the cycle-2 "production callers are unaffected" claim is RETRACTED** | Verified against current `main`: `check()` declares `head: str = "HEAD"` (`gates/gate.py:65`) and forwards `base`/`head` unresolved into `discover_fn` (`gates/gate.py:77`), and the shipped `autoharness gate check` command reaches that default (`cli.py:290`, `cli.py:400-405`). Making discovery hex-only therefore breaks a **released command**, not merely hypothetical callers — so U8b could not have shipped as scoped. The fix resolves at `check()`, after its disabled/no-gates early return and before discovery, preserving D-12 (raw ref text still never reaches `git diff`) instead of weakening discovery back to symbolic-ref tolerance, which was considered and re-rejected. U8b gains `gates/gate.py` (Files 1->2, same code domain); the matching test re-characterization goes to U8c (Files 2->3), preserving width isolation. |

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
| RK10 | **Contradictory outcome serialization** — two independent outcome fields disagree and consumers/exit mapping diverge | D-9 collapses to one canonical `status`; any alias is a derived property absent from `to_dict()`. U9 asserts the field is absent from `dataclasses.fields()` and that no constructor path yields a contradictory pair — unrepresentable, not merely untested. |
| RK11 | **Schema mirror drift** — runtime validates the versioned schema while only the pointer was extended, so `detectors` is silently unvalidated | D-10 makes both files one atomic unit in U2; the pre-existing parity test fails loudly on drift, and detector validation cases run against the **versioned** (runtime-resolved) document. |
| RK12 | **Evidence deadlock at unchanged HEAD** — a tool-version change strands consumers at `insufficient_evidence` with no way to write fresh evidence | D-11 folds the freshness fingerprint into the epoch key. U10c scenario 2 is the direct regression test; scenarios 1/3/4 cover determinism, stale-sibling rejection, and concurrent same-key idempotence. |
| RK13 | **Argument injection via user-controlled Git refs** — an option-like `--base` makes a read-only gate write a file | D-12 resolves and hex-validates before any git invocation, rejects with the invalid-input exit class and no side effect, and adds `--end-of-options`/`--` inside discovery as a backstop. U8c asserts the would-be output file does not exist after a rejected option-like ref. |

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
  2 and evaluates nothing; a `failed` `ART-01` still exits 0; an option-like
  `--base` (e.g. `--output=<tmp>`) exits 2 **and writes no file**; a rerun at
  unchanged HEAD after a tool-version change writes a **new** report under a new
  epoch key without overwriting the prior one.
* **Gate command (Q5)**: `PYTHONPATH=src python -m unittest discover -s tests`.
* **Operational closure artifact**: closure record naming the report path
  convention **`<head_sha>-<fingerprint>.json` and the canonical fingerprint
  input list (D-11)**, the Q1 consumer condition (S8 must wire a named consumer
  or the writer must be withdrawn), the RK1 retro-validation outcome, and
  confirmation that zero backlogit change occurred.
* **Rollback trigger**: RK1 falsification fails; or exit-code invariance breaks
  (anything other than 0/2 escapes); or the report is found to be read back as
  authoritative input; or a user-controlled ref reaches `git diff` unresolved.

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

> **SUPERSEDED — the verdict block immediately above belongs to the
> 2026-08-27 round-0 review and is retained for lineage only. The authoritative
> markers for this plan are the `dispatch_mode:` and `decision:` blocks at the
> END of this file (hosted review-fix cycle 1, 2026-08-28).**

---

## Plan Hardening — re-run (hosted review-fix cycle 1, 2026-08-28)

Re-run is **mandatory**, not discretionary: the cycle-1 corrections alter
**schema files** (U2, both pointer and versioned), **public CLI input handling**
(U8/U8b, `--base`), the **serialization contract** (U1, canonical `status`), and
**persisted-report identity** (U7, epoch key). Each independently trips a P-006
hardening signal, so all five signals remain PRESENT and the prior hardening pass
cannot be carried forward unexamined.

### Protected invariants — delta

* **INV-1 (Law 1, flat report)** — UNCHANGED. The writer still accepts a flat
  `Sequence[NodeResult]` with no edge access. D-11 changes the *filename*, never
  the *shape*; derive-never-persist still holds for the graph itself.
* **INV-2 (Q1 boundary)** — UNCHANGED and re-verified. S1 still ships **no
  read-back API**. The D-11 consumer-selection rule is a written specification
  plus a pure, tested key-computation function — not a production read path.
  Q1's approved derived-report persistence exception is preserved exactly as
  granted, and its withdrawal condition (S8 wires a named consumer or the writer
  is withdrawn) is unchanged.
* **INV-3 (report has no exit authority)** — UNCHANGED.
* **INV-4 (cycle -> zero nodes evaluated)** — UNCHANGED, now asserted in U10.
* **INV-5 (refs resolve only inside `autoharness.detectors`)** — UNCHANGED; the
  P0 import containment from round 0 survives intact and is still asserted in U9.
* **INV-6 (exactly one detector)** — UNCHANGED.
* **INV-7 (NEW, D-9)** — a `NodeResult` **cannot represent a contradictory
  outcome**. One stored outcome field exists; any alias is derived. Enforced by
  type/shape, asserted in U9.
* **INV-8 (NEW, D-11)** — the epoch key is a **pure deterministic function** of
  HEAD plus the canonical freshness fingerprint. At most one report can match the
  current dimensions; stale siblings are rejected by key mismatch, structurally.
* **INV-9 (NEW, D-12)** — **no user-controlled ref text ever reaches a `git`
  argument unresolved.** Only `^[0-9a-f]{40}$` values are passed to discovery.

### Risky actions — delta

| Action | Risk | Containment |
|---|---|---|
| Editing **two** schema files instead of one | A partial edit leaves runtime blind to `detectors` while the pointer claims support | Both files are one atomic unit in U2; the pre-existing parity test fails loudly on drift; detector cases run against the **versioned** document |
| Changing the persisted-report filename convention | Orphaning any evidence already written under the old `<head_sha>.json` convention | **No migration and no backfill are required**: S1 has not shipped, so **no report has ever been written** by this code path. The convention is new-at-birth, not changed-in-flight. Nothing to migrate, nothing to delete |
| Removing a field (`verdict`) from an unshipped contract | Would be breaking if consumers existed | **No consumer exists** — S1 is the first shipment to define `NodeResult`. Removing it *before* first ship is precisely why this must land now rather than after S2-S10 bind to it |
| Adding `--end-of-options` inside `discover_modified_files` | Behaviour change to an **existing shipped** function used by other callers | `--end-of-options` only constrains *option parsing*; it cannot change the meaning of an already-valid ref. Existing callers pass internally-derived refs, so the observable diff output is unchanged. This is the one genuinely pre-existing surface touched, and U8c scenario 4 characterizes pass-through |
| ^ **CORRECTED IN CYCLE 2 (thread `PRRT_kwDORzpWpM6dVQdY`) -- the row above is retained for lineage and is NOT the live containment.** | The containment understated the blast radius: it conflated *option parsing* (genuinely unchanged) with the *input contract* (genuinely changed). Asserting `base`/`head` are 40-hex SHAs rejects symbolic refs, and `tests/test_gates_discovery.py` passes `"main"`/`"HEAD"` at lines 32/40/49 and pins the exact old argv at line 45 -- four failing assertions, so the canonical Q5 gate goes red | **Live containment**: only the *production* caller (`gates/gate.py:77`) is unaffected. `tests/test_gates_discovery.py` is added to **U8c**'s scope (Files 1 -> 2) and re-characterized there; U8b is not complete while that suite is red; U8b and U8c land together |
| Concurrent writes at the same epoch key | Torn or duplicated report file | Atomic `os.replace` (or `O_EXCL` treat-exists-as-success); content is deterministic per key; U10c scenario 4 asserts it |
| ^ **CORRECTED IN CYCLE 2 (thread `PRRT_kwDORzpWpM6dVQec`) -- the row above is retained for lineage and is NOT the live containment.** | `os.replace` overwrites the prior report at the same key, contradicting append-only; and the "deterministic content" premise is false because `produced_at` varies | **Live containment (D-13)**: no-clobber exclusive claim (`os.link` / `O_EXCL`, `FileExistsError` == success) plus atomic publish; `os.replace` forbidden throughout; U10c scenario 4 now asserts the published bytes equal the **first** writer's payload, so last-writer-wins is a failing test |

### Rollback and monitoring — delta

* Rollback is unchanged and remains cheap: every new file is additive, and the
  two edited pre-existing surfaces (`gates/discovery.py`, the schema pair) are
  independently revertible.
* **New monitoring trigger**: if a consumer is ever observed selecting a report
  by directory scan rather than by computed key, INV-8 has been violated in
  spirit and the stale-sibling guarantee is void.

**Requires plan hardening: yes — re-run completed 2026-08-28.**

---

## Plan Review — re-run (hosted review-fix cycle 1)

**Reviewed**: 2026-08-28 · **Plan**: `docs/plans/2026-08-27-pre-review-detector-sdk-plan.md`
**Trigger**: 4 unresolved Copilot review threads on PR #414 at HEAD
`12f8c9743899b6177a1658b9bb9cff29611fb159`.

### Dispatch capability (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`
  — `.github/agents/subagents/` still does not exist (S0/GAP 2 has **not**
  executed; `156-S` remains queued). Probed by direct path existence check.
* `TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass`
* `TOOL_DEGRADED: agent-intercom — operator visibility reduced`
* `ENGRAM_DEGRADED` / `GRAPHTOR_UNAVAILABLE` — file-based retrieval used; all
  four findings were re-verified by direct source read rather than index lookup.

Every selected persona was covered inline; no persona was dropped. The
security-sensitive personas (Security Lens, Agent-Native Parity) were triggered
again because cycle 1 touches an argument-injection surface.

```text
dispatch_mode: single-agent-declared-degradation
```

### Persona findings (P0-P3)

| Persona | Finding | Sev | Disposition |
|---|---|---|---|
| Security Lens Reviewer | **Argument injection via `--base` (thread `PRRT_kwDORzpWpM6dGx_a`).** Verified real at `gates/discovery.py:61`: `f"{base}...{head}"` with no option terminator; `--output=/path` is accepted by `git diff` as its output option and **writes a file** from a read-only gate. | **P0 -> mitigated** | D-12 + U8b: `git rev-parse --verify --end-of-options <ref>^{commit}` with `^[0-9a-f]{40}$` validation, invalid-input exit 2 with **no side effect**, plus an `--end-of-options`/`--` backstop inside discovery. U8c scenario 1 asserts the would-be output file **does not exist** after rejection — the assertion that makes this verdict valid. |
| Security Lens Reviewer | Round-0 P0 (config-driven arbitrary import) — is the namespace allow-list still intact after the cycle-1 edits? | **P0 -> re-verified** | Intact. INV-5 unchanged; U9's containment assertion untouched by these edits. |
| Security Lens Reviewer | Epoch key now embeds a fingerprint — could it become a path-injection vector? | P2 | **No.** The fingerprint is a hex SHA-256 prefix derived internally; no user-controlled text enters the filename. Path remains fixed and non-user-controlled. |
| Constitution Reviewer | Does D-11 widen Q1's persistence exception? | **P1 -> resolved** | **No.** Q1 permits persisting the derived *report*; D-11 changes only its *key*, not its shape, authority, or read-back status. Law 1 (derive-never-persist for the **graph**) is untouched — INV-1 and D-5's type-level constraint are unchanged. The exception's withdrawal condition is preserved verbatim. |
| Constitution Reviewer | D-9 aligns the contract with the **governing D5 text**, which describes the extension as additional *statuses* rather than a second field. | — | PASS (correction of a genuine plan/deliberation divergence). |
| Architecture Strategist | **Contract stability — is removing `verdict` a breaking change?** | P1 | **No, and the timing is the point.** S1 is the first shipment to define `NodeResult`; no consumer exists. Round 0 already flagged that S2-S10 all bind to this contract, so collapsing to one field **before** first ship is strictly cheaper than after. Deferring it would guarantee the breaking change. |
| Architecture Strategist | Unit count 11 -> 15. Is this scope creep? | P2 | **No.** No new capability was added; three splits (U8b, U10b/U10c, U8c) were forced by the plan's own granularity budget (max 3 files, max 4 test scenarios per unit). Absorbing 8 scenarios into U10 or 8 into U11 would have breached the 2-hour rule. |
| Python Reviewer | `CheckResult.status` is an unconstrained `str` and consumers branch on `.status` (`gates/topology.py:172-180`) — a widened vocabulary on that one field is compatible. | — | PASS (verified in source, not assumed). |
| Python Reviewer | Concurrent same-key writes need an explicit strategy or the report can tear. | P1 | **Addressed**: atomic `os.replace` or `O_EXCL`-treat-exists-as-success; deterministic content per key; U10c scenario 4. |
| ^ **SUPERSEDED IN CYCLE 2 (thread `PRRT_kwDORzpWpM6dVQec`)** — the cycle-1 disposition above is retained for lineage and is **not** the live contract. | The `os.replace` half of that disposition contradicts append-only, and its "deterministic content per key" premise is false (`produced_at` is wall-clock). | **Live contract: D-13** — no-clobber exclusive claim (`os.link` / `O_EXCL`, `FileExistsError` == success), `os.replace` forbidden, and U10c scenario 4 now pins the published bytes to the first writer. |
| Python Reviewer | `--end-of-options` requires Git >= 2.24. | P2 | Acceptable — already implied by the repo's `gh`/worktree usage. On an older Git, `rev-parse --verify` fails closed to the invalid-input class, which is the safe direction. |
| Scope Boundary Auditor | Do the cycle-1 edits leak S2-S10 scope into S1? | — | PASS. No waiver surface, no incremental evaluation, no shipment attachment, no read-back consumer. The D-11 selection rule is specified for S8 but **not implemented** here. |
| Scope Boundary Auditor | U2 now contains a test file — width-isolation breach? | P3 | Accepted. `tests/test_validation_gates_schema.py` is the **schema's own contract test** and already contains the parity assertion that the schema edit would break. Splitting them would ship a knowingly red suite mid-shipment. No detector runtime logic enters U2. |
| Learnings Researcher | `docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md` — the "defined but not wired" class recurs here as **"schema declared but not the one runtime loads"** (thread 1). | P2 | **Addressed** by D-10: the fix is not "edit the other file too" but "validate against the file the runtime actually resolves", asserted in U2. |
| Learnings Researcher | `docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md` — prefer structural impossibility to assertion. | — | PASS (alignment). D-9 and D-11 both make the defect **unrepresentable** rather than merely tested: one stored field, and identity-equals-freshness. |
| Agent-Native Parity Reviewer | Does exit 2 for an unsafe `--base` break the report-only guarantee? | — | PASS. Exit 2 is the pre-existing **invalid-input** class (already used for invalid registries), not a detector verdict escaping. RK3's invariant — a `failed` detector still exits 0 — is untouched. |

### Verdict rationale

All four PR #414 findings were **independently re-verified against source**
before disposition: the schema resolution order (`schema_contracts.py:511-532`),
the exact-equality mirror test, the D5 governing text in `031-DL`, and the
unterminated `git diff` argument (`gates/discovery.py:61`). None was speculative;
all four are accepted as correct.

One new P0 (argument injection) is fully contained by D-12/U8b with a
**no-side-effect assertion** in U8c, and the round-0 P0 containment was
re-verified intact. The P1 findings each resolve structurally: D-9 makes
contradictory outcomes unrepresentable, D-11 makes freshness and identity the
same predicate, and the atomic-write strategy closes the concurrency gap. The
unit-count growth is forced by the plan's own granularity budget, not by added
scope.

Q1's approved derived-report persistence exception is preserved unchanged, and
derive-never-persist for the graph itself is untouched. Granularity, width
isolation, and the 2-hour rule hold across all 15 units.

```text
decision: PASS
```

> **SUPERSEDED — the `dispatch_mode:` and `decision:` blocks immediately above
> belong to the 2026-08-28 hosted review-fix **cycle 1** review and are retained
> for lineage only. The authoritative markers for this plan are the
> `dispatch_mode:` and `decision:` blocks at the END of this file (hosted
> review-fix **cycle 2**, 2026-08-28).**

---

## Plan Hardening — re-run (hosted review-fix cycle 2, 2026-08-28)

Re-run is **mandatory**, not discretionary. The cycle-2 corrections change a
**persistence protocol** (U7, publication strategy), a **public CLI acceptance
contract** (U11, `--base` exit class), and the **declared scope of an existing
shipped test surface** (U8b/U8c, `tests/test_gates_discovery.py`). Each trips a
P-006 hardening signal independently, so the cycle-1 hardening pass cannot be
carried forward unexamined.

**Reviewed HEAD**: `5c907b4fd75a02772388bd20f4d09d14950f046b`.
**Trigger**: 5 unresolved Copilot review threads on PR #414.

### Protected invariants — delta

* **INV-1 (Law 1, flat report)** — UNCHANGED. D-13 changes *how* the file is
  published, never its shape. The writer still has no edge access.
* **INV-2 (Q1 boundary)** — UNCHANGED and re-verified. S1 still ships **no
  read-back API**. D-13's consumer rule ("an unparseable report is
  `insufficient_evidence`") is a written specification, not a production read
  path; nothing in S1 reads a report back.
* **INV-3 (report has no exit authority)** — UNCHANGED, and explicitly
  re-confirmed against D-14: exit 2 is the pre-existing **invalid-input** class,
  not a detector verdict escaping into the exit code. A `failed` detector still
  exits 0.
* **INV-4, INV-5, INV-6, INV-7** — UNCHANGED.
* **INV-8 (epoch key)** — UNCHANGED as to the key; **strengthened** as to the
  file: under D-13 a published report is now unreachable by any write path, so
  "append-only" is enforced by the publication primitive rather than by a
  convention an implementer could pick the wrong overload of.
* **INV-9 (no unresolved user ref reaches `git`)** — UNCHANGED and now
  **falsifiable end-to-end**: the U11 acceptance case no longer contradicts it.
* **INV-10 (NEW, D-13)** — **a published report is immutable by construction.**
  No code path opens a published report for writing; publication fails closed on
  an existing destination and reports that failure as success.
* **INV-11 (NEW, D-14)** — **exactly one outcome is correct per layer.** Unsafe
  or unresolvable *user* ref text -> exit 2 at the CLI, no side effect. A context
  that cannot be built from validated input -> `insufficient_evidence` at the
  engine. No test asserts both for one input.

### Risky actions — delta

| Action | Risk | Containment |
|---|---|---|
| Forbidding `os.replace` and mandating a link/`O_EXCL` claim | `os.link` is unavailable on some filesystems, so a naive implementation could fail to publish at all | The `O_EXCL` path is a **specified fallback**, not an afterthought, and both paths treat `FileExistsError` as success. U10c scenario 4 exercises real concurrent writers, so a broken publish surfaces as a failing test rather than as missing evidence |
| Relying on `O_EXCL` alone in the fallback path | A writer that dies mid-write leaves a partial file that a later reader could consume as evidence | Contained by specification, not by hope: an **unparseable report is `insufficient_evidence`**, never evidence, and is never repaired in place. The link path never publishes a partial file at all |
| Adding an existing shipped test file to U8c's scope | Scope creep into an unrelated suite; or a unit that silently exceeds the 2-hour rule | Bounded and enumerated: **four** existing assertions are re-characterized plus **one** new rejection assertion, in **one** file. Files 1 -> 2 (max 3), scenarios stay at 4, size stays S. `parse_diff_output` tests and both graceful-degradation tests are explicitly out of scope and asserted unchanged |
| Changing U11's expected exit class from 0 to 2 | Could be mistaken for weakening the report-only guarantee (RK3) | Explicitly **not** a weakening: exit 2 is the pre-existing invalid-input class already used for invalid registries, and U11 still asserts exit 0 while `ART-01` reports `failed`. The exit-code invariance sweep (only 0 and 2) is unchanged |

### Rollback and monitoring — delta

* Rollback is unchanged and remains cheap: no cycle-2 change adds a new file or a
  new dependency edge. Every change is a contract tightening inside units that
  have not yet been implemented.
* **New monitoring trigger (D-13)**: if `os.replace`, `os.rename`, `shutil.move`,
  or any `open(..., "w")` is ever observed on a path under
  `.autoharness/gates/pre-review/`, INV-10 is violated and the append-only
  guarantee is void.
* **New monitoring trigger (D-14)**: if any test asserts `insufficient_evidence`
  for an unsafe or unresolvable **user-supplied** `--base`, INV-11 has regressed
  and U8/U8c are no longer satisfiable alongside U11.

**Requires plan hardening: yes — re-run completed 2026-08-28 (cycle 2).**

---

## Plan Review — re-run (hosted review-fix cycle 2)

**Reviewed**: 2026-08-28 · **Plan**: `docs/plans/2026-08-27-pre-review-detector-sdk-plan.md`
**Trigger**: 5 unresolved Copilot review threads on PR #414 at HEAD
`5c907b4fd75a02772388bd20f4d09d14950f046b`.

### Dispatch capability (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`
  — `.github/agents/subagents/` still does not exist (S0/GAP 2 has **not**
  executed; `156-S` remains queued and unclaimed). Probed by direct path check.
* `TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass`
* `TOOL_DEGRADED: backlogit-MCP — CLI fallback: `backlogit` (v1.10.1) used for
  sync, doctor, and checkpoint operations`
* `TOOL_DEGRADED: agent-intercom — operator visibility reduced` (dark mode,
  `visibility=local`)
* `ENGRAM_DEGRADED` / `GRAPHTOR_UNAVAILABLE` — file-based retrieval used. All
  five findings were re-verified by **direct source read** (`gates/discovery.py`,
  `tests/test_gates_discovery.py`, the shipment manifests, and the `031-DL`
  source corpus) rather than by index lookup.

Every selected persona was covered inline; no persona was dropped. Security Lens
and Agent-Native Parity were triggered again because cycle 2 touches an
argument-injection surface and a CLI acceptance contract.

```text
dispatch_mode: single-agent-declared-degradation
```

### Persona findings (P0-P3)

| Persona | Finding | Sev | Disposition |
|---|---|---|---|
| Python Reviewer | `os.replace` was offered as an allowed publication strategy beside an `append-only, never overwritten` clause in the same unit. The two cannot both hold. | **P1** | **Fixed (D-13)**. `os.replace` removed from U7 and from the plan. Publication is an exclusive claim (`os.link`, `O_EXCL` fallback) plus atomic publish; `FileExistsError` is success. |
| Python Reviewer | The premise justifying `os.replace` — "content is deterministic per key" — is false, because `provenance.produced_at` is wall-clock. | **P1** | **Fixed (D-13)**. The false premise is named and retracted in both the task and the plan. Determinism is asserted for the *key*, never for the *payload*. |
| Python Reviewer | U10c scenario 4 asserted only "exactly one well-formed report", which an overwriting emitter also satisfies — the assertion could not have caught the defect. | **P1** | **Fixed**. Scenario 4 now pins the published bytes to the **first** writer's payload; last-writer-wins is a failing test. |
| Security Lens Reviewer | U8b changes `discover_modified_files`' accepted inputs and argv, but no unit owned `tests/test_gates_discovery.py`, which pins the old argv at line 45 and passes symbolic refs at lines 32/40/49. The canonical Q5 gate would go red. | **P1** | **Fixed**. That file is added to **U8c** (tests domain, Files 1 -> 2); U8b is not complete while it is red; U8b/U8c land together. Symbolic-ref behaviour is now characterized explicitly rather than assumed. |
| Security Lens Reviewer | Retaining symbolic-ref compatibility inside `discover_modified_files` would be the cheaper fix. | P2 | **Rejected, recorded.** It reopens the hole D-12 closes by letting unvalidated ref text reach `git diff`. Resolution moves up into `resolve_commit_ref`; the capability is preserved, its location is not. |
| Constitution Reviewer | U11 acceptance expected `insufficient_evidence` at exit 0 for an unresolvable `--base`, while U8/U8b/U8c require exit 2 with no report for that same input. Mutually unsatisfiable. | **P1** | **Fixed (D-14)**. U11 now asserts the CLI boundary (exit 2, no side effect); FC1's `insufficient_evidence` is pinned to the **engine** layer in U4 and U9 and is driven against the engine directly. |
| Constitution Reviewer | Law 1 / Law 2 posture unchanged by cycle 2; Q1's exception is neither widened nor re-argued. | — | PASS |
| Architecture Strategist | Are D-13/D-14 new scope? | P2 | **No.** Both remove contradictions between artifacts of the already-authorized contract; no unit, file, dependency edge, or capability was added. Unit count stays **15**; the dependency graph is unchanged. |
| Scope Boundary Auditor | `031-DL`'s problem frame said "Nine" while the adjacent list carried ten IDs. | P2 | **Fixed, and the reviewer's literal suggestion was not followed.** "Nine" is **correct** — it matches the decision artifact's "`D911A3B2` epic + eight features". The tenth ID `34AAF1C7` is a **retained living tracker**, not an imported entry; only its branch (a) is consumed, via S9. The list label now records that provenance instead of inflating the count, which would have contradicted the source arithmetic. |
| Scope Boundary Auditor | Shipment member counts drifted: the PR description still published 19 tasks / 21 members after cycle 1 raised S1 from 11 to 15. | P2 | **Verified and handed off.** Authoritative counts from the manifests: `156-S` = 1 feature + 8 tasks = **9 members**; `157-S` = 1 feature + 15 tasks = **16 members**; total **23 implementation tasks, 25 members**. The PR body is Orchestrator-owned; Stage does not edit it (P-010). |
| Agent-Native Parity Reviewer | Exit 2 for an unsafe `--base` is machine-legible and matches the existing invalid-registry class; `--json` parity unchanged. | — | PASS |
| Learnings Researcher | `docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md` — the "defined but not wired" class. Applies to the U8c reconciliation: a task that changes a contract without owning the tests that pin it presents as complete while the gate is red. | P2 | **Addressed** by the explicit "U8b MUST NOT be marked complete while that suite is red" clause plus the co-landing requirement. |

### Verdict rationale

Five findings, all **P1/P2**, no P0. Every one was a **contradiction between two
artifacts of the already-authorized contract** rather than a request for new
capability — which is why all five passed the P-021 C1 same-contract-surface
test and none was deferred.

The two P1 clusters are now enforced structurally rather than by prose: D-13
makes a published report unreachable by any write path (INV-10) and gives U10c
an assertion that can actually fail on an overwrite; D-14 assigns exactly one
correct outcome per layer (INV-11) so U11 and U8/U8c are simultaneously
satisfiable. The U8c scope addition converts a silent Q5-gate failure into an
enumerated, bounded, in-budget edit.

Granularity, width isolation, and the 2-hour rule hold across all **15** units.
No unit, file, dependency edge, or capability was added in cycle 2; `U8c` moves
from Files 1 to Files 2, still inside the max-3 budget at size S.

*(SUPERSEDED by the hosted review-fix cycle-3 markers at the end of this file.)*

```text
dispatch_mode: single-agent-declared-degradation
```

```text
decision: PASS
```

## Plan Hardening — re-run (hosted review-fix cycle 3, 2026-08-28)

Triggered by P-006: cycle 3 alters a **publication protocol** (U7), a
**security-critical call boundary** (U8b/`gate.py`), and a **concurrency test
contract** (U10c). All three are hardening signals, so `plan-harden` re-runs
before `plan-review`.

### Protected invariants — delta

| # | Invariant | Status |
|---|---|---|
| INV-10 | A published report is unreachable by any write path | **STRENGTHENED.** Cycle 2 established this for `os.replace`. Cycle 3 (D-15) closes the remaining hole: the `O_EXCL`-onto-`final` fallback made the final pathname reachable by a *partial* write. The invariant now holds on every path because `os.link` from a fsynced temp is the **only** publication path. |
| INV-12 | **NEW.** The final report pathname is complete-or-absent at all times | Previously conditional ("except on the `O_EXCL` fallback"). D-15 makes it unconditional by removing the only path that could violate it. Absence is a *recoverable* state; a partial file is *terminal* under append-only. |
| INV-13 | **NEW.** No raw, unvalidated ref text reaches `git diff` from **any** caller, including shipped commands | D-12 asserted this but was enforced only at the CLI and inside discovery. `gate.py::check` sat between them forwarding `head="HEAD"` unresolved. D-17 closes that gap at the boundary. |
| INV-14 | **NEW.** A test may not assert an outcome the implementation is not required to produce | D-16. U10c's "first writer wins" pinned a race outcome no correct emitter guarantees. Assertions must target the *specified property* (no-clobber), never an incidental scheduling artifact. |
| INV-1, INV-2, INV-3, INV-11 | Law 1 / no read-back API / report-only exit 0 / layer separation | **UNCHANGED.** Cycle 3 touches no graph, no read-back surface, no exit mapping, and no layer assignment. |

### Risky actions — delta

| Action | Risk | Containment |
|---|---|---|
| Removing the `O_EXCL` fallback (D-15) | Platforms without hard-link support lose report publication entirely | **Accepted and bounded.** The report is *derived, non-authoritative* evidence with no blocking authority (INV-3), so its absence degrades to `insufficient_evidence` — an already-specified, self-healing outcome — and never blocks or falsely passes a gate. Publishing a *partial* report is strictly worse: it is terminal, silently poisons the epoch key, and cannot be repaired under append-only. NTFS and all mainstream POSIX filesystems support `os.link`; the fallback was for an unenumerated hypothetical. |
| Adding `gates/gate.py` to U8b (D-17) | Scope creep into a shipped, pre-existing module on the gate critical path | **Bounded and enumerated.** One function (`check`), resolution inserted between the existing early return and the existing `discover_fn` call. No signature change, no new parameter, no behaviour change for `enabled=False`/no-gates. Files 1 -> 2, same `code` domain, within the max-3 budget; size raised S -> M honestly rather than hiding the growth. |
| Adding `tests/test_gates_gate.py` to U8c (D-17) | A tests unit at the max-3 file ceiling exceeding the 2-hour rule | **Enumerated to two edits and one addition** (§U8c). All three are characterization edits against an existing suite, not new test design. Size raised S -> M and complexity low -> medium. Scenario count stays at 4. |
| Loosening U10c's race assertion (D-16) | A weaker test that no longer catches last-writer-wins | **Net stronger, not weaker.** The removed assertion was *unreliable* (nondeterministic) and the retained one is *deterministic*: a serialized distinguishable third write proving bytes + `st_mtime` unchanged fails on exactly the emitter class the original assertion targeted, without a race. |

### Rollback and monitoring — delta

* **D-15**: revert is textual (restore the fallback bullet in U7/`149.007-T`). No
  code has shipped. Monitoring: U10c must observe that a hard-link-unavailable
  emitter reports failure and leaves **no file** at the final path.
* **D-17**: `gates/gate.py` is a ~10-line insertion with a pure-function
  resolver; revert is removal of that block. Monitoring: the Q5 suite is the
  detector — `test_gates_gate.py` and `test_gates_discovery.py` both go red if
  the boundary is removed while discovery stays hex-only.
* **Co-landing constraint reaffirmed**: U8b and U8c must land together. Cycle 3
  extends that to a **three-file** red surface (`test_gates_discovery.py`,
  `test_gates_gate.py`, plus the new `test_gate_ref_safety.py`).

## Plan Review — re-run (hosted review-fix cycle 3)

### Dispatch capability (P-012)

No reviewer-subagent dispatch tool is available in this invocation (no MCP
surface; backlogit reached via registry-declared CLI fallback). Declared
degradation, consistent with cycles 1 and 2: personas are applied as
single-agent structured self-review, not parallel dispatch.

```text
dispatch_mode: single-agent-declared-degradation
```

### Persona findings (P0-P3)

| Persona | Finding | Severity | Disposition |
|---|---|---|---|
| Security Reviewer | Does D-17 reintroduce the D-12 injection surface by letting `check()` accept symbolic refs? | P1 | **No.** `check()` accepts refs and *resolves* them; `discover_modified_files` remains hex-only with the `--end-of-options`/`--` backstop. Raw text still never reaches `git diff`. The conversion point moved *up*, which is what D-12 always specified for the CLI — D-17 applies the same rule to the library boundary that was silently exempt. |
| Security Reviewer | Is the `enabled=False` early return a bypass of ref validation? | P2 | **No.** It returns before *any* discovery call, so no ref reaches git on that path. Validating there would be validation with nothing to protect. Pinned explicitly by the retained `test_check_no_gates_returns_empty_report`. |
| Reliability Reviewer | D-15 removes publication on hard-link-less platforms — is silent evidence loss acceptable? | P1 | **Yes, and it is not silent.** The emitter surfaces a non-fatal publication failure; the consumer computes `insufficient_evidence`, which is a *specified* outcome (D6) with no blocking authority (INV-3). The alternative — a partial file at the final path — is terminal under append-only and strands the epoch key permanently, which is the D-11 deadlock class. Recoverable-and-loud beats terminal-and-silent. |
| Test Architect | Does D-16 leave any window where last-writer-wins passes? | P1 | **No.** The serialized phase issues a distinguishable payload at an already-published key and asserts bytes **and** `st_mtime` unchanged. An `os.replace`/`os.rename` emitter changes both. The race phase still proves single-well-formed-report; only the *winner identity* — never specified, never guaranteed — is no longer asserted. |
| Architecture Strategist | Unit count 15 -> 15, but two units grew. Scope creep? | P2 | **No.** No unit, capability, dependency edge, or file *family* was added. Two existing units gained one file each (U8b 1->2, U8c 2->3), both inside the plan's own max-3 budget, and both sizes were raised S -> M rather than absorbed silently. D-17 growth was **forced**: the cycle-2 scope was unshippable because it broke a released command. |
| Python Reviewer | Is `st_mtime` granularity sufficient to detect an overwrite? | P2 | **Byte comparison is the primary assertion; `st_mtime` is corroborating.** A rewrite with differing `produced_at` changes the bytes regardless of clock granularity, so the test cannot pass a last-writer-wins emitter even if mtime resolution is coarse. |
| Maintainability Reviewer | Three cycles of corrections to U7's write protocol — is the unit unstable? | P3 | **Converging, not oscillating.** Cycle 1 keyed the epoch (D-11), cycle 2 removed `os.replace` (D-13), cycle 3 removed the last non-atomic path (D-15). Each narrowed the publication surface; the protocol is now a single path with no alternatives, which is terminal by construction. |
| Correctness Reviewer | Does the retracted "production callers unaffected" claim invalidate cycle-1/cycle-2 verdicts? | P2 | **No.** It invalidates one *supporting statement*, not the D-12 decision it supported. D-12's rationale (argument injection via `--output=`) is independently verified against `discovery.py:61` and unaffected. The retraction is recorded in-place in D-17 and in `149.012-T` so the false claim cannot be re-cited. |

**No P0 findings.** All eight are P1/P2/P3 and dispositioned in place.

### Verdict rationale

Four findings, all **P1/P2**, no P0. Every one was a **contradiction between two
artifacts of the already-authorized contract** — a fallback that contradicted
its own unit's complete-or-absent clause; a test assertion that contradicted
what the implementation is required to guarantee; and an invariant claim that
contradicted the shipped source it described. All four therefore passed the
P-021 C1 same-contract-surface test and **none was deferred**.

Cycle 3 adds **no capability, no unit, no dependency edge, and no new file
family**. Unit count holds at **15**; the 157-S manifest holds at **16 members**;
total implementation tasks hold at **23** and PR members at **25**. Granularity,
width isolation, and the 2-hour rule hold across all 15 units, with U8b and U8c
re-sized S -> M so the growth is declared rather than absorbed.

**Cycle budget: this is cycle 3 of 3 against the 149-F plan. The review-fix
budget is now EXHAUSTED.** No in-scope finding remains open.

```text
dispatch_mode: single-agent-declared-degradation
```

```text
decision: PASS
```
