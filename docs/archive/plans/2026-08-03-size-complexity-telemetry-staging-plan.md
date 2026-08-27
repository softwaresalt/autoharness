---
title: "impl-plan — Size + Complexity first-class staging & backlogit telemetry evidence mapping"
type: impl-plan
date: 2026-08-03
route: claude-opus-4.8 / anthropic / high (P-013.5, inherited)
features: [F1 size-complexity-first-class-staging, F2 backlogit-telemetry-evidence-mapping]
deliberation: docs/decisions/2026-08-03-size-complexity-telemetry-staging-deliberation.md
informs: [082-F]
chosen_direction: "B — Two ordered shipments (S1 staging → S2 telemetry), non-conflated size/complexity"
requires_plan_hardening: yes
hardening_present: yes
blast_radius: elevated (F2 mutates the ratified tool-telemetry-event schema AND its live runtime model/composer/jsonl serialization; requires root+versioned schema-mirror parity, schema-contract version registration, and runtime schema-conformance/round-trip test coverage)
---

## Summary

Two width-isolated features, ordered S1 → S2. S1 makes `size` and `complexity` first-class,
validated, non-conflated planning metadata in the Stage staging workflow (agent template +
harvest skill + semantics reference). S2 maps backlogit 1.8 telemetry evidence to the ratified
`ToolTelemetryEvent`/`ExecutionEpoch` contract, adds a structurally-separate complexity
dimension, and lands the backlogit-only carve-out that unblocks feature 082-F. All tasks carry
`size` (size_source=agent, size_ruleset_version=`ah-stage-sizing-v1`) and `complexity`, and are
scoped ≤ 2h of human-equivalent effort.

## Grounding (shipped seams this plan consumes read-only)

- backlogit released contract: `size = implementation volume; complexity = implementation
  difficulty and uncertainty`; size provenance-completeness (source ⇒ non-empty ruleset);
  complexity enum [trivial,low,medium,high] task-only.
- `schemas/tool-telemetry-event/1.0.0.schema.json` (WorkSizingSnapshot, metric_sources/quality,
  retrieval_pack=backlogit, route_kind=backlog_index, sensitivity fields). **This schema is NOT an
  inert forward contract**: it has a byte-identical root mirror `schemas/tool-telemetry-event.schema.json`
  (a parity test requires the two to match except `$id`), a version registration in
  `src/autoharness/schema_contracts.py` (`known_versions`), and a **live strict runtime model** at
  `src/autoharness/telemetry/tool_event.py` (`additionalProperties:false` via `_SCHEMA_PROPERTY_NAMES`)
  with a composer (`tool_event_compose.py`), jsonl serialization (`tool_event_jsonl.py`), and tests that
  cross-check `to_dict()`/`from_mapping()` against the ratified schema. Any additive schema field must be
  applied to both mirrors, registered, and threaded through the runtime model to keep the contract tests
  green. (084-F still owns event *emission*; this plan does not wire emission.)
- `docs/decisions/2026-07-13-telemetry-metrics-reporting-ownership.md` (autoharness owns
  reporting; backlogit owns planned sizing/work-state; 082-F=evidence, 084-F=emission).
- backlogit `docs/telemetry-fields.md` (session_summary / tool_usage record fields).
- Templates to modify: `templates/agents/_stage.agent.md.tmpl`,
  `templates/skills/harvest/SKILL.md.tmpl` (both currently have zero size/complexity content).

## Task decomposition (width-isolated, ≤ 2h each)

### Feature F1 — size-complexity-first-class-staging (family: instruction/skill templates + docs)

- **F1.T1 — Size↔Complexity semantics reference doc** (family: docs). size S / complexity low.
  Author `docs/size-complexity-reference.md`: adopt backlogit's verbatim non-conflation
  definition (size=volume/effort; complexity=difficulty/uncertainty), enum tables (XS..XL;
  trivial..high), the rule that the 2-hour reliability gate consumes BOTH axes independently
  (size bounds volume; high complexity forces a split/de-risk regardless of size), and the
  provenance-completeness rule (size_source ⇒ non-empty size_ruleset_version). No code.

- **F1.T2 — Stage agent template: size+complexity mandatory at task creation** (family:
  agent template). size M / complexity medium. dep: F1.T1. **Backlog: 107.004-T.**
  Edit `templates/agents/_stage.agent.md.tmpl` harvest/decomposition steps so every created
  task MUST set `size` (with `size_source: agent`, non-empty `size_ruleset_version`) and
  `complexity`; validate both enums before write; apply the two-axis 2-hour/granularity gate;
  forbid conflating the axes; reference F1.T1. **Because this is a behavioral change to a
  dogfooded agent, propagate the identical edits to the installed copy `.github/agents/_stage.agent.md`
  and refresh the `.autoharness/harness-manifest.yaml` checksum for that path** (same procedure as
  prior dogfood agent edits, e.g. 110-S/106.004-T). Frontmatter/variable integrity preserved
  (no unresolved `{{...}}`); manifest verification passes.

- **F1.T3 — Harvest skill: size+complexity emission + enum validation gate** (family: skill
  template). size M / complexity medium. dep: F1.T1. **Backlog: 107.002-T.**
  Edit `templates/skills/harvest/SKILL.md.tmpl` to require size+complexity on every emitted
  work item, reject invalid enum values, and integrate the two-axis granularity check into the
  existing P-003 granularity gate. Cross-reference F1.T1.

- **F1.T4 — Enum + non-conflation validation checklist/fixture** (family: docs/test-fixture).
  size S / complexity low. dep: F1.T2, F1.T3. **Backlog: 107.003-T.**
  Add a reviewer checklist (and, if a lightweight fixture harness exists, a sample) asserting:
  both enums validated, provenance-completeness enforced, and no single scalar combines the two
  axes. Cross-reference integrity: all referenced files exist.

- **F1.T5 — Enable native `complexity` field in the backlogit workspace header-def** (family:
  config). size S / complexity low. dep: F1.T1. **Backlog: 107.005-T.**
  Enable the native task-level `complexity` enum (trivial|low|medium|high) in
  `.backlogit/header-def.yaml` so it matches the installed backlogit 1.8.0 defaults. Today the
  workspace defines `size` but NOT `complexity` for the task type, so `--complexity` mutations
  fail validation; until this lands, Stage records complexity via an enum-validated comment (the
  established convention on every task in this plan). Ship-owned config change (P-010). Acceptance:
  `backlogit update <task> --complexity high` succeeds; existing tasks stay valid; no size/other-field
  regressions. This task was harvested into shipment S1 (112-S) and is therefore reviewed here
  explicitly.

### Feature F2 — backlogit-telemetry-evidence-mapping (family: schema + docs) — depends on F1

- **F2.T1 — backlogit evidence → ToolTelemetryEvent field map** (family: docs). size M /
  complexity high. dep: F1.T1. **Backlog: 108.001-T.**
  Author `docs/telemetry/backlogit-evidence-map.md` mapping each backlogit telemetry field
  (`session_summary`, `tool_usage`, `telemetry_sessions`/`telemetry_tool_usage`,
  `size_composition`) to the ratified contract with an **explicit granularity dimension
  (per-invocation ToolTelemetryEvent vs per-epoch ExecutionEpoch)**. Every mapped target carries
  FOUR labels: `metric_sources`, `metric_quality`, evidence-class (**observed | derived |
  unavailable | not_applicable**), and granularity (**event | epoch**).
  **observed** is reserved for host_reported/backlogit-direct evidence at genuine *per-invocation*
  granularity ONLY: server_name, tool_name, operation, duration_ms, and per-call
  input/output/cached tokens. **Aggregate-only backlogit values (session cumulative tokens,
  tool_usage roll-ups, and `compaction_count`) MUST NOT be mapped onto per-operation
  ToolTelemetryEvent fields** — that misattributes/double-counts; route them to ExecutionEpoch
  (economics) granularity, or mark them unavailable at event granularity. **NOTE: `compaction_count`
  is NOT a ToolTelemetryEvent field** (it exists in neither the event nor the epoch schema today).
  **derived** (tokens_per_task, depletion_rate, peak_utilization, remaining_capacity,
  avoided/offload estimates) labelled at the granularity where computable;
  **unavailable/not_applicable** for autoharness-only identity fields
  (event_id/epoch_id/argv_fingerprint/exit_code/error_kind). No emitter code (084-F owns emission).

- **F2.T2 — Non-conflated complexity dimension in the event contract (schema)** (family: schema).
  size M / complexity high. dep: F2.T1. **Backlog: 108.002-T.**
  Add a structurally-SEPARATE optional complexity field (top-level `task_complexity_label` enum
  trivial|low|medium|high|null + `complexity_source`), explicitly NOT nested in
  `work_sizing_snapshot`, so size and complexity never conflate. **Apply the change to BOTH schema
  mirrors — `schemas/tool-telemetry-event.schema.json` (root) AND
  `schemas/tool-telemetry-event/1.0.0.schema.json` (versioned) — keeping them byte-identical except
  `$id` so the parity test stays green; record/apply the schema-version decision in
  `src/autoharness/schema_contracts.py` (`known_versions`); update the schema-contract tests
  (`tests/test_telemetry_schema_contracts.py`).** Feature/shipment complexity = `not_applicable`
  (backlogit complexity is task-only). Additive, backward-compatible; update
  `docs/telemetry-reference.md`. If a new versioned file is required, add it without deleting
  `1.0.0.schema.json`. **Runtime model + serialization/composer handling is split out to F2.T4.**

- **F2.T4 — ToolTelemetryEvent runtime model + serialization for the complexity field** (family:
  python-runtime). size M / complexity high. dep: F2.T2. **Backlog: 108.004-T.**
  Thread the additive optional complexity field through the live strict runtime model: add
  `task_complexity_label`/`complexity_source` to `_SCHEMA_PROPERTY_NAMES`, the dataclass fields, and
  to `to_dict`/`from_mapping` (nullable-safe, provenance-aware) in
  `src/autoharness/telemetry/tool_event.py`, then thread it through the composer
  (`tool_event_compose.py`) and jsonl serialization (`tool_event_jsonl.py`). Extend the runtime
  tests (`test_telemetry_tool_event.py`, `test_telemetry_tool_event_compose.py`,
  `test_telemetry_tool_event_jsonl.py`) so schema-conformance and round-trip cross-checks cover the
  new field. Required because `additionalProperties:false` + the schema-conformance/round-trip tests
  would otherwise reject or fail on the new field. No emitter wiring (084-F owns emission).
  Acceptance: round-trip preserves the field + provenance; records omitting it stay valid; the
  schema-conformance test passes; no emission call-site changes.

- **F2.T3 — Sensitivity/redaction + defensible-correlation guardrails** (family: docs). size S /
  complexity medium. dep: F2.T1, F2.T2. **Backlog: 108.003-T.**
  Document backlogit-adapter safety defaults: `sensitivity`, `redaction_applied`,
  `secret_scan_status`, no raw-content exfiltration (only counts/durations/labels/hashes cross
  the boundary); permit size/complexity correlations ONLY where semantics are defensible
  (task-level, non-conflated) and forbid normalized metrics that imply precision the source
  lacks. Land the backlogit carve-out note that unblocks the backlogit portion of 082-F.

## Dependency order

F1.T1 → (F1.T2, F1.T3, F1.T5) → F1.T4  [S1 / 112-S]
F1 (whole) ⇒ F2.T1 → F2.T2 → (F2.T3, F2.T4)  [S2 / 113-S, blocked on S1]

Backlog↔plan map: F1.T1=107.001-T, F1.T2=107.004-T, F1.T3=107.002-T, F1.T4=107.003-T,
F1.T5=107.005-T; F2.T1=108.001-T, F2.T2=108.002-T, F2.T3=108.003-T, F2.T4=108.004-T.
Published: 9 tasks (S1=5: 107.001/002/003/004/005; S2=4: 108.001/002/003/004). Parent
features 107-F/108-F are NOT shipment members.

## Width-isolation ledger

- F1 touches ONLY agent/skill templates + docs + the backlogit workspace config header-def
  (F1.T5). F1.T5 (config) is isolated from the template/docs tasks. F1.T2 keeps the template edit,
  its installed dogfood mirror, and the manifest-checksum refresh together as one coherent
  agent-template change (the checksum refresh is a deterministic consequence of the same edit, not
  an independent family). F2 touches ONLY schema + schema-registration + the schema's runtime
  model/serialization + docs. **F2.T2 (schema mirrors + registration) is width-isolated from
  F2.T4 (python-runtime model + composer + jsonl)** so schema-family and Python-runtime-family work
  never share a task; both are isolated from the F2 doc tasks (F2.T1/F2.T3).

## Risks

- R1: Redefining size/complexity semantics divergently from backlogit. Mitigation: F1.T1 adopts
  backlogit's released wording verbatim; no re-definition.
- R2: Conflation creeping back via a nested/combined field. Mitigation: F2.T2 mandates a
  structurally-separate field + F1.T4 checklist asserts non-conflation.
- R3: Implying precision from derived metrics. Mitigation: F2.T1 metric_quality labelling +
  F2.T3 guardrails.
- R4: **Schema/runtime/mirror drift.** An additive schema field applied to only one mirror, left
  unregistered, or not threaded through the strict runtime model would break the parity test,
  `schema_contracts` registration, or the schema-conformance/round-trip tests. Mitigation: F2.T2
  updates BOTH mirrors + registration + contract tests; F2.T4 threads the field through the runtime
  model/composer/jsonl with matching tests; the two are ordered F2.T2 → F2.T4.
- R5: **Aggregate/per-event misattribution.** Mapping session/tool aggregate totals (or the
  non-existent `compaction_count` event field) onto per-operation ToolTelemetryEvent fields would
  double-count/misattribute. Mitigation: F2.T1 mandates an explicit event-vs-epoch granularity label
  and routes aggregate-only values to ExecutionEpoch or marks them unavailable at event granularity.

## Plan hardening (P-006) — determination: REQUIRED, and APPLIED

Trigger: F2.T2/F2.T4 mutate the ratified `tool-telemetry-event` schema **and its live runtime
model/composer/serialization** (elevated blast radius — schema + Python-runtime families). Fail-safe
default would also require hardening; it is applied here explicitly.

### Failure-mode analysis + mitigations
- FM1 — Schema change breaks existing validators/consumers/tests. **Reality (corrected):** the schema
  is NOT inert — it has a byte-identical root mirror guarded by a parity test, a version registration
  in `src/autoharness/schema_contracts.py`, and a **live strict runtime model** (`tool_event.py`,
  `additionalProperties:false`) with a composer, jsonl serialization, and schema-conformance/round-trip
  tests. There is still **no live emitter/store wiring** (084-F owns emission), but a field added to
  only one mirror or not carried into the runtime model WOULD fail the parity/conformance tests.
  Mitigation: the complexity field is **additive and optional** (nullable), so every currently-valid
  record stays valid; F2.T2 updates BOTH mirrors + registration + contract tests; F2.T4 threads it
  through the runtime model/composer/jsonl with matching tests. Ordered F2.T2 → F2.T4.
- FM2 — Conflation regression. Mitigation: structurally-separate field, enforced by F1.T4
  checklist and F2.T2 acceptance.
- FM3 — Raw-content exfiltration via the adapter. Mitigation: F2.T3 restricts the boundary to
  counts/durations/labels/hashes; sensitivity/redaction/secret_scan defaults documented.
- FM4 — Sizing/complexity provenance incompleteness. Mitigation: F1.T1 encodes the
  source⇒ruleset rule; Stage tasks (this session included) set size_source + size_ruleset_version.

### Rollback / blast-containment
- The schema change is additive and optional; no live emitter/store depends on it. Rollback = revert
  the single additive property from BOTH mirrors, the `schema_contracts` registration delta, the
  runtime-model/composer/jsonl field, the doc lines, and the added test assertions — no data
  migration, no consumer breakage. Version handling: bump only if the schema's versioning policy
  treats an additive-optional field as a new minor; F2.T2 records the version decision explicitly
  and, if a new versioned schema file is required, adds it without deleting `1.0.0.schema.json` and
  registers it in `known_versions`.
- Template changes (F1) are prose-only; the F1.T5 header-def edit is an additive optional enum
  (revert = delete the block). Reverts are text-only with no build/runtime coupling except F2.T4,
  whose runtime revert is covered above.

## Policy checks
- P-010: all tasks are staging/backlog/planning artifacts for Ship to implement; Stage authors
  only planning docs + backlog. No source/template/schema mutation performed by Stage in this
  session.
- P-003: every task is single-family, ≤2h, with explicit acceptance and dependency edges.
