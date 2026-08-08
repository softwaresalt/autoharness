---
title: "121-S / 113-F: schema mirror mutated in place without a version bump"
date: 2026-08-08
problem_type: contract-versioning-violation
category: schema-contract-versioning
component: schemas/harness-config, src/autoharness/schema_contracts.py
root_cause: "a new additive schema constraint (nested additionalProperties:false properties + a cross-field not ambiguity check) was applied uniformly across the root schema AND an already-published versioned mirror file, without bumping the version identifier, so the same schema_version string silently came to mean two different byte-level validation contracts"
resolution_type: code_fix
severity: high
message: "schema_version.const and SCHEMA_CONTRACTS[\"config\"].current_version left at 1.0.0 while schemas/harness-config/1.0.0.schema.json was mutated in place with new additionalProperties:false nested properties and a new not constraint"
file_path: schemas/harness-config/1.0.0.schema.json
citations:
  - "PR #316 (121-S / 113-F)"
  - "src/autoharness/schema_contracts.py:42-54"
  - "commit 6da2f55b (PR #294 review cycle 2, tool-telemetry-event v1.0->v1.1 precedent)"
  - "docs/design-docs/2026-08-08-escalation-flat-to-nested-per-role-migration.md"
tags: [schema-versioning, contract-integrity, copilot-review, harness-config, versioned-contract, migration]
shipment: 121-S
feature: 113-F
pr: 316
---

# Compound Learning: A schema-behavior change without a version bump silently redefines an already-published version

**Discovered**: 2026-08-08, PR #316 review round 5 (Copilot), shipment 121-S /
feature 113-F (F02FD596 nested per-role escalation hierarchy).

## The pattern

`schemas/{contract}.schema.json` is the *current* schema; each published
`schemas/{contract}/{version}.schema.json` file is a **pinned, immutable
snapshot** of what a given `schema_version` string means, per the versioned-contract
discipline documented in `src/autoharness/schema_contracts.py:42-54`
(`resolve_contract_schema_path` picks the versioned mirror matching a
document's own `schema_version` field so old documents validate forever
against the contract they were written against).

PR #316 added new `additionalProperties: false` nested properties
(`stage.escalation` / `ship.escalation`) and a new cross-field `not` ambiguity
constraint to `schemas/harness-config.schema.json` — and, because the fix was
applied with a simple find-and-copy pattern across "the schema files", the
*same* additive diff was also applied **in place** to the already-published
`schemas/harness-config/1.0.0.schema.json` mirror. `schema_version.const` and
`SCHEMA_CONTRACTS["config"].current_version` were both left at `"1.0.0"`.

The result: the string `"1.0.0"` now meant two different validation contracts
depending on *when* you read the file. A config written before this change
validated fine under the pre-PR 1.0.0 mirror; after this change, an old
1.0.0 validator (or any tooling caching the old byte content) would reject a
document using the new nested escalation override, while the patched-in-place
mirror would accept it. Same version identifier, two different behaviors —
exactly the ambiguity the versioned-contract discipline exists to prevent.

Copilot caught this in review (not local review, not the test suite) because
none of the schema/contract tests assert byte-identity of a *previously
published* versioned mirror against its prior git history — they only assert
the mirror's *current* content is internally self-consistent.

## The fix pattern (now a repeatable precedent)

This is the **second** time this exact bug class has occurred (the first was
`tool-telemetry-event` v1.0 → v1.1, commit `6da2f55b`, PR #294 review cycle 2).
The fix is now a named, repeatable procedure:

1. `git checkout main -- schemas/{contract}/{old_version}.schema.json` to
   restore the mutated mirror to byte-identical pre-change content.
2. Copy the *current* (already-edited) root schema to a **new**
   `schemas/{contract}/{new_version}.schema.json` mirror, changing only `$id`.
3. Bump `schema_version.const` in the root schema to `{new_version}`.
4. Bump `SCHEMA_CONTRACTS[{contract}]["current_version"]` and append
   `{new_version}` to `known_versions` (keep the old version(s) — old
   documents must keep validating).
5. Do **not** add a `CONTRACT_MIGRATIONS` entry for a purely additive bump —
   confirmed neither `tool-telemetry-event` nor this `config` bump needed one,
   and `tests/test_verify_workspace.py` asserts `migration_proposals == []`
   for a workspace still declaring the old version. An additive bump is
   `status: known-legacy` (informational), never a forced migration.
6. Update every coupled surface in the same commit: template default
   (`templates/{contract}.yaml.tmpl`), this repo's own dogfood config,
   `harness-manifest.yaml` checksum + note for any dogfood artifact whose
   bytes changed, and every test fixture that hardcodes the old version
   string (a schema with `schema_version.const` enforced means any raw
   validate-against-root-schema test with a stale version string fails on
   version mismatch alone, independent of the feature under test).
7. Add a regression test asserting the restored old mirror is *byte*-free of
   the new constraint/properties (`test_legacy_{old_version}_mirror_preserved_unchanged`
   pattern) — this is the test that would have caught this bug class
   immediately, and neither precedent occurrence had one until after the
   Copilot finding.

## Generalizable lesson

**When a diff needs to touch "the schema" for a contract that has published
versioned mirrors, treat the root schema and every versioned mirror as
*separate, individually-owned* files from the first edit — never batch-apply
the same patch across all of them.** The moment new validation behavior is
introduced, ask: does this change what an *existing* version string means? If
yes, the fix is a version bump with an old-mirror restore, not an in-place
edit. Add the "mirror preserved unchanged" regression test in the same PR
that introduces the versioned contract in the first place, not retroactively
after a review catches the second occurrence.

## Cross-references

- `src/autoharness/schema_contracts.py:42-54` — the versioned-contract
  discipline this bug class violates.
- Commit `6da2f55b` (PR #294 cycle 2) — first occurrence
  (`tool-telemetry-event` v1.0 → v1.1).
- Commit `c355d378` (PR #316 review round 5) — second occurrence and this
  compound doc's origin (`harness-config` v1.0.0 → v1.1.0).
- `docs/design-docs/2026-08-08-escalation-flat-to-nested-per-role-migration.md`
  — design doc section "Schema-version bump: 1.0.0 -> 1.1.0 (PR #316 Copilot
  review)".
