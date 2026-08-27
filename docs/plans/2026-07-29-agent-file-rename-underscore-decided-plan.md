---
source: docs/plans/2026-07-29-agent-file-rename-underscore-decided-plan.md
title: "Rename dot-prefixed agent definition files to underscore-prefixed"
doc_type: decided-plan
status: shipped
created: 2026-07-29
feature: "097-F"
shipment: "102-S"
tasks: ["097.001-T", "097.002-T", "097.003-T", "097.004-T", "097.005-T"]
source_stash_id: "157C41D0"
supersedes:
  - docs/archive/plans/2026-07-29-agent-file-rename-underscore-plan.md
---

# Decided Plan: Rename dot-prefixed agent definition files to underscore-prefixed

**Outcome:** Reviewed as a high-blast-radius five-task rename sweep for feature
`097-F` / shipment `102-S`. Plan review finished `READY`, P0 = 0, P1 = 0, and a
second Copilot staging review on PR #255 raised 13 valid plan-precision threads
that were folded in before re-review. The source plan contains no PR or merge
proof of shipment, so this decided-plan records the reviewed state rather than a
shipped outcome. This replaces the verbose original, archived for traceability
at `docs/archive/plans/2026-07-29-agent-file-rename-underscore-plan.md`.

**Delivery status (verified against the backlog at compaction time):** shipped — `097-F`, `097.001-T`, `097.002-T`, `097.003-T`, `097.004-T`, `097.005-T` confirmed complete in `.backlogit/`. Remaining open follow-up work tracked separately: `102-S` (active).

## Problem (settled)

Rename the dogfood Stage/Ship agent definition files and frontmatter handles
from dot-prefixed names to underscore-prefixed names, then sweep every live
cross-reference, test, and manifest assertion so no dangling old-name reference
survives outside explicit legacy aliases and historical/archive exemptions.

## Decisions

1. **Use a five-task dependency-ordered sweep.** Rename the four files and their
   frontmatter handles first, then update non-code references, installer/tuner
   logic, coupled tests, and finally manifest/checksum/verification surfaces.
2. **Keep old dot names only where legacy or history requires them.** The zero
   residual goal applies to live canonical surfaces; old strings may remain only
   in the declared exemption set and explicit `legacy_files` / `legacy_names`
   compatibility tables.
3. **Move canonical agent identity to underscore names without renaming the
   conceptual roles.** `verify_workspace.py`, install/tune alias tables, and the
   manifest become underscore-canonical, but prose display names `Stage` and
   `Ship` remain unchanged.
4. **Treat checksum refresh as a raw-bytes problem, not a text-printout
   problem.** `.gitattributes` pins alone are insufficient; the plan requires
   normalize -> assert no CRLF -> hash raw working-tree bytes before writing the
   manifest.

## Implementation (5 tasks)

- **097.001-T — Renames + frontmatter:** rename the four agent-definition files
  and change frontmatter `name` handles from `.Stage` / `.Ship` to `_Stage` /
  `_Ship`; the source plan specified git-aware renames so history would stay
  legible.
- **097.002-T — Non-code cross-reference sweep:** update docs, instructions,
  `.gitattributes`, workspace profile references, the shipment-reconcile skill,
  and the changelog where live references still used the dot-prefixed names.
- **097.003-T — Installer/tuner logic + emit surfaces:** make
  `src/autoharness/verify_workspace.py` underscore-canonical, retain old names
  only as explicit legacy aliases, and update install/tune alias tables.
- **097.004-T — Coupled tests:** refresh the integrity, telemetry, and CLI tests
  that encode the canonical names.
- **097.005-T — Manifest + gates:** update manifest paths/checksums, then run the
  zero-old-name gate, `autoharness verify`, and the canonical
  `PYTHONPATH=src python -m unittest discover -s tests` gate.

## Key constraints preserved

- The rename has an explicitly enumerated 22-file blast radius; completeness of
  the sweep is treated as the primary risk.
- Old names may legitimately remain only in the documented exemption set,
  including historical docs, backlog artifacts, and deliberate legacy alias
  tables.
- The canonical verification gate is `PYTHONPATH=src python -m unittest discover
  -s tests`; `pytest tests/` is explicitly non-canonical because of vendored
  `references/` collection behavior.
- `.gitattributes` must pin LF for the renamed agent files, but the manifest
  checksums must still be computed from raw working-tree bytes after LF
  normalization is asserted.
- No edits are needed in `_orchestrator.agent.md`, role-enforcement
  instructions, schemas, scripts, prompts, or foundation templates because they
  do not reference the dot-prefixed filenames or handles.

## Rejected alternatives

- **Partial live aliasing or a partial sweep** — rejected because the main risk
  is leaving dangling live references; compatibility is limited to explicit
  legacy tables and historical/archive surfaces.
- **Use `pytest tests/` as the canonical integrity gate** — rejected because it
  pulls in vendored `references/`; the plan locked onto `unittest discover`.
- **Rename the conceptual display names `Stage` / `Ship`** — rejected; only the
  filenames and frontmatter handles change.
- **Rely on `.gitattributes` alone for manifest correctness** — rejected because
  `verify_workspace.py` hashes raw working-tree bytes, so LF normalization has to
  be asserted before hashing.

## Review findings that changed the plan

The second review pass on PR #255 materially tightened the plan. It fixed the
canonical test gate at `PYTHONPATH=src python -m unittest discover -s tests`,
replaced any ambiguous checksum language with the CRLF-safe
normalize -> assert -> hash recipe, corrected the backlogit section marker to
`acceptance-criteria`, and exempted historical `CHANGELOG.md` entries from the
zero-old-name gate. Re-review then returned `READY`, P0 = 0, P1 = 0.