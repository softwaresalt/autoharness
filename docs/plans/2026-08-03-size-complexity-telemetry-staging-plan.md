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
blast_radius: elevated (F2 mutates the ratified tool-telemetry-event schema — forward contract)
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
  retrieval_pack=backlogit, route_kind=backlog_index, sensitivity fields).
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
  agent template). size M / complexity medium. dep: F1.T1.
  Edit `templates/agents/_stage.agent.md.tmpl` harvest/decomposition steps so every created
  task MUST set `size` (with `size_source: agent`, non-empty `size_ruleset_version`) and
  `complexity`; validate both enums before write; apply the two-axis 2-hour/granularity gate;
  forbid conflating the axes; reference F1.T1. Frontmatter/variable integrity preserved
  (no unresolved `{{...}}`).

- **F1.T3 — Harvest skill: size+complexity emission + enum validation gate** (family: skill
  template). size M / complexity medium. dep: F1.T1.
  Edit `templates/skills/harvest/SKILL.md.tmpl` to require size+complexity on every emitted
  work item, reject invalid enum values, and integrate the two-axis granularity check into the
  existing P-003 granularity gate. Cross-reference F1.T1.

- **F1.T4 — Enum + non-conflation validation checklist/fixture** (family: docs/test-fixture).
  size S / complexity low. dep: F1.T2, F1.T3.
  Add a reviewer checklist (and, if a lightweight fixture harness exists, a sample) asserting:
  both enums validated, provenance-completeness enforced, and no single scalar combines the two
  axes. Cross-reference integrity: all referenced files exist.

### Feature F2 — backlogit-telemetry-evidence-mapping (family: schema + docs) — depends on F1

- **F2.T1 — backlogit evidence → ToolTelemetryEvent field map** (family: docs). size M /
  complexity high. dep: F1.T1.
  Author `docs/telemetry/backlogit-evidence-map.md` mapping each backlogit telemetry field
  (`session_summary`, `tool_usage`, `telemetry_sessions`/`telemetry_tool_usage`,
  `size_composition`) to ToolTelemetryEvent fields, labelling each target field
  **observed** (host_reported/backlogit direct: server_name, tool_name, duration_ms,
  input/output/cached tokens, compaction_count, context tokens), **derived** (tokens_per_task,
  depletion_rate, peak_utilization, remaining_capacity, avoided/offload estimates), or
  **unavailable/not_applicable** (event_id/epoch_id/argv_fingerprint/exit_code/error_kind and
  other autoharness-only identity fields), populating `metric_sources`/`metric_quality`
  accordingly. No emitter code (084-F owns emission).

- **F2.T2 — Non-conflated complexity dimension in the event contract** (family: schema). size M
  / complexity high. dep: F2.T1.
  Extend `schemas/tool-telemetry-event/1.0.0.schema.json` with a structurally-SEPARATE optional
  complexity field (e.g. top-level `task_complexity_label` enum trivial|low|medium|high|null +
  `complexity_source`), explicitly NOT nested in `work_sizing_snapshot`, so size and complexity
  never conflate. Feature/shipment complexity = `not_applicable` (backlogit complexity is
  task-only). Additive, backward-compatible; update `docs/telemetry-reference.md`. Version-bump
  decision recorded (see hardening).

- **F2.T3 — Sensitivity/redaction + defensible-correlation guardrails** (family: docs). size S /
  complexity medium. dep: F2.T1, F2.T2.
  Document backlogit-adapter safety defaults: `sensitivity`, `redaction_applied`,
  `secret_scan_status`, no raw-content exfiltration (only counts/durations/labels/hashes cross
  the boundary); permit size/complexity correlations ONLY where semantics are defensible
  (task-level, non-conflated) and forbid normalized metrics that imply precision the source
  lacks. Land the backlogit carve-out note that unblocks the backlogit portion of 082-F.

## Dependency order

F1.T1 → (F1.T2, F1.T3) → F1.T4  [S1]
F1 (whole) ⇒ F2.T1 → F2.T2 → F2.T3  [S2, blocked on S1]

## Width-isolation ledger

- F1 touches ONLY agent/skill templates + docs. F2 touches ONLY schema + docs. No task mixes
  template-family work with CLI or schema work in the same unit. F2's single schema-mutating
  task (F2.T2) is isolated from all doc tasks.

## Risks

- R1: Redefining size/complexity semantics divergently from backlogit. Mitigation: F1.T1 adopts
  backlogit's released wording verbatim; no re-definition.
- R2: Conflation creeping back via a nested/combined field. Mitigation: F2.T2 mandates a
  structurally-separate field + F1.T4 checklist asserts non-conflation.
- R3: Implying precision from derived metrics. Mitigation: F2.T1 metric_quality labelling +
  F2.T3 guardrails.

## Plan hardening (P-006) — determination: REQUIRED, and APPLIED

Trigger: F2.T2 mutates the ratified `tool-telemetry-event` schema (elevated blast radius —
schema family). Fail-safe default would also require hardening; it is applied here explicitly.

### Failure-mode analysis + mitigations
- FM1 — Schema change breaks existing validators/consumers. Reality: the schema is a **forward
  contract with no live Python event model, emitter, sink, composer, or store** (per its own
  description and the ownership decision). The complexity field is **additive and optional**
  (nullable), so every currently-valid record remains valid. Mitigation: additive-only; new
  field defaults to null/omitted; no required-field change.
- FM2 — Conflation regression. Mitigation: structurally-separate field, enforced by F1.T4
  checklist and F2.T2 acceptance.
- FM3 — Raw-content exfiltration via the adapter. Mitigation: F2.T3 restricts the boundary to
  counts/durations/labels/hashes; sensitivity/redaction/secret_scan defaults documented.
- FM4 — Sizing/complexity provenance incompleteness. Mitigation: F1.T1 encodes the
  source⇒ruleset rule; Stage tasks (this session included) set size_source + size_ruleset_version.

### Rollback / blast-containment
- Schema change is additive and lives behind the forward-contract boundary (no runtime emission
  depends on it). Rollback = revert the single additive property + doc lines; no data migration,
  no consumer breakage. Version handling: bump only if the schema's versioning policy treats an
  additive-optional field as a new minor; F2.T2 records the version decision explicitly and, if
  a new versioned schema file is required, adds it without deleting `1.0.0.schema.json`.
- Template changes (F1) are prose-only; revert is a text revert with no build/runtime coupling.

## Policy checks
- P-010: all tasks are staging/backlog/planning artifacts for Ship to implement; Stage authors
  only planning docs + backlog. No source/template/schema mutation performed by Stage in this
  session.
- P-003: every task is single-family, ≤2h, with explicit acceptance and dependency edges.
