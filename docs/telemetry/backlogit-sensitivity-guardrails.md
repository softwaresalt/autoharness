---
title: Backlogit Sensitivity/Redaction Guardrails and 082-F Backlogit Carve-Out
description: Documents backlogit-adapter safety defaults (sensitivity, redaction_applied, secret_scan_status), the safe evidence surface (counts/durations/labels/hashes only), permitted task-level size/complexity correlations, and the formal statement unblocking the backlogit-only portion of 082-F.
---

# Backlogit Sensitivity/Redaction Guardrails and 082-F Backlogit Carve-Out

> **Navigation**: [README](../../README.md) · [Telemetry Reference](../telemetry-reference.md) ·
> [Backlogit Evidence Map](backlogit-evidence-map.md) ·
> [Size + Complexity Reference](../size-complexity-reference.md)

## Purpose and scope

This document is the second half of the backlogit-only carve-out of feature 082-F (108.003-T),
paired with [`docs/telemetry/backlogit-evidence-map.md`](backlogit-evidence-map.md) (108.001-T).
Where the evidence map answers "what backlogit data maps to which ratified field, at what
granularity," this document answers "what is safe to retain and emit at all." It contains
**no emitter code** — 084-F owns event emission; this document owns safety-boundary policy for
backlogit-sourced evidence only. Engram, graphtor-docs, and agent-intercom portions of 082-F
remain **blocked-on-operator** (no read access or sanitized fixtures for those workspaces exist
in this session) and are explicitly **not** unblocked by this document.

## Safety defaults for backlogit-sourced evidence

`schemas/tool-telemetry-event.schema.json` already defines the three safety fields any
backlogit-sourced `ToolTelemetryEvent` (or an `ExecutionEpoch` roll-up derived from one) must
populate:

| Field | Default when the source is backlogit-harvested evidence | Rationale |
|---|---|---|
| `sensitivity` | `internal` | Backlogit records (`tool_call_fact`, `tool_usage`, `session_summary`, `session_fact`, `size_composition`) originate from a workspace-internal harvester and are never `public` by default. The schema's own rule — "ambiguous defaults to internal handling" — applies whenever provenance is uncertain; adapters must never default to `public`. |
| `redaction_applied` | `true` whenever any field capable of carrying free-form content (tool arguments, prompt text, command strings) was excluded rather than merely truncated | Per the evidence map, backlogit's per-invocation record (`tool_call_fact`) exposes no free-form content fields at all — the safe fields (`tool_name`, `server_name`, `model`, timestamps, `duration_ms`, `success`, `session_id`, `branch`, `repository`, `turn_id`) are already redaction-safe by construction. `redaction_applied: true` documents that this is a deliberate exclusion, not an oversight, whenever a hypothetical richer future backlogit surface is adapted. |
| `secret_scan_status` | `not_run` (not `passed`) unless a scan actually executed | A backlogit-carve-out adapter that only ever retains counts/durations/enums/hashes (see below) has no free-form content to scan, so no scan is truthfully claimed to have run. `not_run` is the honest default; `passed` must never be asserted without an actual scan step, and `unavailable` is reserved for cases where scanning was attempted but the tooling itself was inaccessible.

These defaults apply specifically to the backlogit adapter surface described in the evidence
map. They do not relax or override any stricter policy the eventual 084-F emitter chooses to
apply to other tool surfaces.

## What may cross the boundary: safe evidence classes only

Per the evidence map's per-field breakdown, only the following evidence classes are permitted
to flow from backlogit's harvested records into a `ToolTelemetryEvent` or `ExecutionEpoch`:

* **Counts** — e.g. `completed_tasks` cardinality, `WorkSizingSnapshot` manifest/child counts,
  histogram bucket counts. Never a raw list of task titles or descriptions — task/shipment
  **IDs** are safe (structural identifiers, not content), but any accompanying free-form title
  or description text is out of scope for this carve-out.
* **Durations** — e.g. `duration_ms`, `total_duration_ms`, `total_api_duration_ms` (unit
  conversion only, no content).
* **Enums/labels** — e.g. `success` (mapped to `status`), `task_size_label`,
  `task_complexity_label`, `sensitivity`, `secret_scan_status`. Closed vocabularies only; no
  free-text label values.
* **Hashes** — e.g. `WorkSizingSnapshot`'s SHA-256 membership hash over the canonical sorted
  task-ID set. A hash is a safe one-way summary of a member set; it never round-trips to the
  underlying content.

**Explicitly forbidden, with no exception carved out by this document:**

* Raw prompts or conversation content (backlogit's harvester never even reaches this surface
  in its own per-invocation record; this document does not open a new path to it).
* Command contents or tool call arguments/parameters (not present on `tool_call_fact` per the
  evidence map; must never be back-filled from a different, richer backlogit surface without a
  fresh sensitivity review).
* Secrets, credentials, or tokens of any kind.
* Internal document content (task/feature/shipment descriptions, DoD text, deliberation
  content). Task and shipment **identifiers** are safe structural correlation keys; the prose
  bodies of those artifacts are not part of the safe evidence surface.

Any future backlogit surface that exposes content beyond counts/durations/enums/hashes requires
a new sensitivity review before it can be mapped — this document's permission does not
retroactively extend to unreviewed future fields.

## Permitted size/complexity correlations (task-level, non-conflated only)

Per [`docs/size-complexity-reference.md`](../size-complexity-reference.md) and the evidence
map's mapping section, size/complexity correlations are permitted **only** where the semantics
are defensible:

* `task_size_label` and `task_complexity_label` may be correlated with each other and with
  outcome/economics fields **only at task granularity**, because backlogit's own `complexity`
  custom field is task-artifact-type only (`.backlogit/header-def.yaml`). Feature- and
  shipment-level `task_complexity_label` is always `not_applicable` — there is no backlogit
  source for a feature- or shipment-level complexity value, and inventing one by averaging or
  rolling up task-level labels would imply a precision (and a semantic — "average difficulty"
  is not a coherent concept) the source data does not support.
* Size (`WorkSizingSnapshot`'s `shipment_manifest_size_histogram`, `feature_child_size_histogram`,
  `task_size_label`) and complexity (`task_complexity_label`) are **never combined into one
  scalar or nested inside each other's payload** — they remain structurally separate top-level
  fields (108.002-T/108.004-T) so a downstream reader cannot conflate "how much" with "how
  hard."
* **Forbidden normalized metrics**: no cost-per-complexity-point, no
  complexity-weighted-size score, no derived "difficulty-adjusted size" scalar. Size labels are
  ordinal and level-relative per the telemetry reference ("cost-per-size-point stays
  `unavailable` unless a future named/versioned label-to-point mapping is present"); the same
  caution applies doubly to complexity, which has no numeric scale at all — it is a closed
  4-value enum (`trivial|low|medium|high`), not an interval measurement. Any metric that
  implies complexity is arithmetically combinable with size or with itself (e.g. averaging
  `high`/`low` into a synthetic "medium") fabricates precision the source lacks and is
  forbidden.
* Reports may group and count by label (e.g. "N tasks labelled `high` complexity") and may show
  co-occurrence with observed outcome/economics fields as a correlation observation, but must
  never present a normalized or weighted numeric derived from complexity labels.

## 082-F backlogit carve-out statement

**This document formally unblocks the backlogit-specific portion of feature 082-F.**

082-F (`cross-pack-measurability-telemetry-access`) called for a cross-pack measurability
session with read access to Engram, backlogit, graphtor-docs, and agent-intercom workspaces,
blocked pending operator-provided access or sanitized fixtures for each pack. Shipment 113-S
(108-F) had, and used, **authoritative read-only access to the upstream `backlogit` source
repository** (`C:\Source\GitHub\backlogit`, read-only, never written to) — satisfying 082-F's
access precondition for backlogit specifically. Combined with
[`docs/telemetry/backlogit-evidence-map.md`](backlogit-evidence-map.md) (which identifies which
metrics are observed, derived, unavailable, or not applicable for backlogit, per 082-F's own
definition of done) and this document (which defines the sensitivity/redaction safety boundary
for that evidence), 082-F's backlogit-specific deliverables are satisfied:

* Operator-equivalent authoritative access existed (upstream backlogit source, read-only).
* The safe-to-inspect record types were identified and scoped (`tool_call_fact`, `tool_usage`,
  `session_summary`, `session_fact`, and backlogit `custom_fields` size/complexity — no other
  backlogit surface was inspected or is claimed as reviewed).
* Real backlogit surfaces were mapped to the ratified `ToolTelemetryEvent`/`ExecutionEpoch`
  contract, and adapter gaps were reported (`compaction_count`, per-model economics breakdown,
  per-call token evidence — all documented as absent, not fabricated).
* Evidence classes were sorted into observed/derived/unavailable/not_applicable per pack surface
  as 082-F's definition of done requires, scoped to backlogit only.

**The Engram, graphtor-docs, and agent-intercom portions of 082-F remain
blocked-on-operator.** No read access or sanitized fixtures for those three workspaces exist in
this session or shipment. This carve-out does not infer, assume, or fabricate any detail about
those packs' telemetry/logging surfaces from public web sources or guesswork — it addresses
backlogit only, as its scope is limited to what 113-S/108-F actually reviewed.

## Cross-references

* [`docs/telemetry/backlogit-evidence-map.md`](backlogit-evidence-map.md) — the field-level
  evidence mapping this document's safety boundary applies to (108.001-T).
* [`docs/size-complexity-reference.md`](../size-complexity-reference.md) — non-conflated
  size/complexity semantics underlying the permitted-correlations section above.
* [`docs/telemetry-reference.md`](../telemetry-reference.md) — `ToolTelemetryEvent` v1.0 /
  `ExecutionEpoch` v1.1 schema overviews, including the non-conflated complexity dimension
  (108.002-T/108.004-T).
* `schemas/tool-telemetry-event.schema.json` — authoritative definitions of `sensitivity`,
  `redaction_applied`, and `secret_scan_status`.
* `docs/decisions/2026-07-13-cross-pack-measurability-telemetry-deliberation.md` and
  `docs/decisions/2026-07-13-telemetry-metrics-reporting-ownership.md` — 082-F's original
  scope and the ratified ownership split (082-F=evidence, 084-F=emission) this carve-out
  operates within.
