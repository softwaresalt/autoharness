---
title: Rename dot-prefixed agent definition files to underscore-prefixed
doc_type: plan
status: reviewed
created: 2026-07-29
feature: 097-F
shipment: 102-S
stash: 157C41D0
blast_radius: high
---

# Plan: Rename `.ship`/`.stage` agent files to `_ship`/`_stage`

## Problem

The two dogfood workflow agents are stored as dot-prefixed files
(`.ship.agent.md`, `.stage.agent.md`) with dot-prefixed frontmatter handles
(`name: .Ship`, `name: .Stage`). Stash **157C41D0** requests renaming both the
installed mirrors and the source templates to an underscore prefix, updating the
frontmatter `name` handles, and sweeping every cross-reference so nothing points
at the old dot-prefixed names after the rename.

This is a mechanical but wide change with **HIGH blast radius**: completeness of
the sweep is the primary risk. An incomplete sweep leaves dangling references in
installer/tuner logic, tests, docs, and the harness manifest.

## Approach

Five width-isolated tasks (each ≤2h), executed in dependency order:

| Task | Domain | Depends on |
|---|---|---|
| 097.001-T | Rename 4 files (`git mv`) + frontmatter `name` | — |
| 097.002-T | Non-code cross-reference sweep (docs, instructions, `.gitattributes`, workspace-profile, CHANGELOG) | 097.001 |
| 097.003-T | Installer/tuner logic + emit surfaces (`verify_workspace.py` `CANONICAL_AGENTS`, install/tune SKILL alias tables) | 097.001 |
| 097.004-T | Coupled tests (`test_verify_workspace`, telemetry ship lifecycle, telemetry record CLI) | 097.003, 097.001 |
| 097.005-T | Manifest paths + checksums + `verify` + `pytest` + zero-residual gate | 097.001-004 |

Git semantics: the 4 renames MUST use `git mv` to preserve history (2 instance
files + 2 templates). Frontmatter edits happen in the renamed files.

## Authoritative blast-radius file list (22 distinct files)

### Group A — Renames + frontmatter (4)

* `.github/agents/.stage.agent.md`  → `_stage.agent.md`  (`name: .Stage` → `_Stage`)
* `.github/agents/.ship.agent.md`   → `_ship.agent.md`   (`name: .Ship`  → `_Ship`)
* `templates/agents/.stage.agent.md.tmpl` → `_stage.agent.md.tmpl` (`name: .Stage` → `_Stage`)
* `templates/agents/.ship.agent.md.tmpl`  → `_ship.agent.md.tmpl`  (`name: .Ship`  → `_Ship`)

### Group B — Non-code cross-reference sweep (11)

* `.github/instructions/harness-architecture.instructions.md` (7 refs)
* `.github/copilot-review-instructions.md` (1)
* `docs/capability-packs.md` (5)
* `docs/getting-started.md` (3)
* `docs/backlogit-operating-model.md` (2, `.tmpl` names)
* `docs/backlogit-compatibility-matrix.md` (1, `.tmpl` names)
* `docs/copilot-review-gate.md` (1, relative link)
* `templates/skills/shipment-reconcile/SKILL.md.tmpl` (2)
* `.autoharness/workspace-profile.yaml` (2 path refs)
* `.gitattributes` (rename ship LF pin; **add** stage LF pin — closes portability gap)
* `CHANGELOG.md` (add new entry; keep historical entries)

### Group C — Installer/tuner logic + emit surfaces (3)

* `src/autoharness/verify_workspace.py` — `CANONICAL_AGENTS` (canonical_file/name
  → underscore; add old dot-names to `legacy_files`/`legacy_names`) + ~26 path
  strings
* `.github/skills/install-harness/SKILL.md` (26 refs incl. canonical/legacy alias table)
* `.github/skills/tune-harness/SKILL.md` (3 refs incl. alias table)

### Group D — Coupled tests (3)

* `tests/test_verify_workspace.py` (39)
* `tests/test_telemetry_ship_lifecycle.py` (6)
* `tests/test_telemetry_record_cli.py` (1)

### Group E — Manifest + gate (2 files + runs)

* `.autoharness/harness-manifest.yaml` (2 path keys + 2 checksums + 3 assertion-text lines)
* Gate runs: `autoharness verify`, `uv run pytest tests/`, zero-residual grep

## EXEMPT paths (old strings may legitimately remain)

`.backlogit/**`, `docs/memory/**`, `docs/decisions/**`, `docs/plans/**` (existing),
`docs/closure/**`, `docs/compound/**`, `docs/spikes/**`, `docs/deferred/**`,
`CHANGELOG.md` historical entries, and the intentional legacy-alias entries in
`verify_workspace.py` (`legacy_files`/`legacy_names`) and the install/tune SKILL
alias-table legacy columns.

## Plan-harden (P-006)

* **H1 Zero-residual gate** — grep the tokens `.ship.agent.md`, `.stage.agent.md`,
  `.ship.agent.md.tmpl`, `.stage.agent.md.tmpl`, `name: .Ship`, `name: .Stage`,
  `.Ship`, `.Stage`; assert ZERO hits outside EXEMPT paths and the legacy-alias
  allow-list.
* **H2 Checksum method** — the generic manifest scan hashes RAW working-tree bytes
  (`hashlib.sha256(read_bytes())`, verify_workspace.py ~3186); committed form is
  LF. Pin BOTH renamed agent files to `eol=lf` in `.gitattributes` and recompute
  checksums on LF bytes. Only 2 manifest artifact entries change.
* **H3 Verify + tests** — `autoharness verify` must pass;
  `tests/test_verify_workspace.py` is the integrity test; full `pytest` green.
* **H4** — every task carries mechanically verifiable acceptance criteria.

## Non-edits (verified, do not touch)

* `_orchestrator.agent.md` and `role-enforcement.instructions.md` reference the
  agents only by prose display names ("Stage"/"Ship"), not dot-filenames or the
  `.Stage`/`.Ship` handle — no edits needed.
* No `schemas/**`, `scripts/**`, `.github/prompts/**`, `templates/prompts/**`, or
  `templates/foundation/**` reference these names.
* Prose display names "Stage"/"Ship" (no dot) are conceptual names and MUST NOT change.

## Plan-review outcome

Multi-persona pass (completeness, correctness, safety, test-integrity): **READY**,
P0 = 0, P1 = 0. See feature 097-F for full acceptance criteria.
