---
type: compound-learning
shipment: 157-S
feature: 149-F
task: 149.002-T
date: 2026-08-30
problem_type: schema_mirror_mutated_in_place_without_version_bump
category: workflow-issues
root_cause: A task commit added an entire new schema block (the `detectors` block plus a `tool_version_dims` conditional) directly into an already-published schema mirror file (`schemas/validation-gates/1.0.0.schema.json`, published by 052-S) instead of publishing a new versioned mirror, mutating a snapshot that downstream consumers may already depend on as immutable.
resolution_type: fix
severity: high
source: docs/compound/2026-08-30-157-s-149-f-schema-mutation-in-place-third-occurrence.md
doc_type: learning
title: "Schema-mutation-in-place is a recurring bug class -- third occurrence, with a shorter fix path for contracts unregistered in SCHEMA_CONTRACTS"
citations:
  - docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md
  - src/autoharness/schema_contracts.py
  - schemas/validation-gates/1.0.0.schema.json
  - schemas/validation-gates/1.1.0.schema.json
tags:
  - schema-versioning
  - copilot-review
  - p-021
---

# Schema-mutation-in-place is a recurring bug class -- third occurrence

## Problem

157-S round 8 (Copilot hosted review on PR #420) found that
`149.002-T`'s commit (`c8ba608a`) had added the entire `detectors` schema
block directly into the already-published
`schemas/validation-gates/1.0.0.schema.json` mirror (234 insertions/14
deletions) instead of publishing a new version. This is the **third**
occurrence of this bug class in this repository; the first is documented in
`docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`,
which contains the general 7-step repeatable fix procedure.

## Root Cause

Editing an already-published schema mirror file in place is easy to do by
accident: the file lives at the same conceptual path a developer would
naturally reach for when adding a new field to "the" schema, and nothing in
the file itself signals that it is an immutable, previously-shipped snapshot
rather than a live, freely-editable document.

## Resolution

Applied the general 7-step procedure from the first occurrence's compound
doc, with one new discovery: `validation-gates` is **not** registered in the
`SCHEMA_CONTRACTS` dict (`schema_contracts.py`) used by the doc-driven
contracts (`harness-config`, `tool-telemetry-event`, `execution-epoch`,
`manifest`). It is resolved via a **standalone module constant**
(`VALIDATION_GATES_SCHEMA_VERSION`), with no per-document `schema_version`
field selecting which mirror to validate against. This simplifies the fix
procedure for this specific contract: there is no
`SCHEMA_CONTRACTS[contract]["current_version"]`/`known_versions` entry to
update, and no `CONTRACT_MIGRATIONS` entry to add (purely additive bump) --
just bump the standalone constant and update the coupled file set (3
hardcoded test paths + doc references).

Concretely: (1) `git checkout main -- schemas/validation-gates/1.0.0.schema.json`
restored the mirror byte-identical; (2) created
`schemas/validation-gates/1.1.0.schema.json` carrying the detectors block
plus the `tool_version_dims` conditional, with `$id` updated; (3) bumped
`VALIDATION_GATES_SCHEMA_VERSION` to `"1.1.0"`; (4) updated 3 hardcoded test
paths and `docs/gates-reference.md` references; (5) added
`test_legacy_1_0_0_mirror_preserved_unchanged`.

## Prevention

Before editing any file under `schemas/{contract}/{version}.schema.json`,
check `git log main -- <path>` first. If the file has commits predating the
current shipment, it is an already-published, immutable snapshot -- never
edit it directly; add a new versioned file instead, exactly as for any other
already-published artifact. This check is now cheap and should be habitual
for any shipment touching `schemas/**`. When applying the general 7-step
procedure from the first-occurrence doc to a new contract, first check
whether that contract is registered in `SCHEMA_CONTRACTS` at all -- an
unregistered, constant-resolved contract has a shorter fix path than a
registered one.
