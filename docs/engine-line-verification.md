---
title: "Backlogit engine-line verification runbook"
description: "Runbook for probing a candidate backlogit engine line before it may join the verified cascade engine-semantics set."
ms.date: 2026-10-21
ms.topic: how-to
keywords:
  - autoharness
  - backlogit
  - engine semantics
  - cascade close
  - compatibility
---

> **Navigation**: [README](../README.md) · [Backlogit Compatibility Matrix](backlogit-compatibility-matrix.md) · [Backlog Integration](backlog-integration.md)

## Purpose

The P-015 cascade close path (`CASCADE`) is permitted only on a backlogit engine
line whose archive and ship semantics were verified against engine source and
tests. Today the only verified line is `1.11`. A newer line (for example `1.12`)
joins the set only after the documented probe below. **Never widen the set by
version number alone.**

## Single source of truth

Three artifacts must always name the same verified set and are changed together:

1. The constant `VERIFIED_CASCADE_ENGINE_MINOR_LINES` in
   `src/autoharness/gates/shipment_closure.py` (currently `frozenset({(1, 11)})`).
2. The P-015 verified-lines token (see the final section) in
   `templates/policies/workflow-policies.md.tmpl` and its installed copy
   `.github/policies/workflow-policies.md` (currently `1.11`).
3. The `shipment-reconcile` skill, `templates/skills/shipment-reconcile/SKILL.md.tmpl`
   and its installed copy `.github/skills/shipment-reconcile/SKILL.md`.

The gate function is `assess_cascade_engine_semantics`, and
`select_close_path` composes it with the classifier verdict. Any result other than
`VERIFIED` (unverified line, unreleased or unparseable build, stale probe, or a
probe of a different surface) selects `SAFE_CLOSE` with reason
`ENGINE_SEMANTICS_UNVERIFIED`. This fallback applies to initial path selection
only. Once `CASCADE` has been selected and recorded, a changed or failed
revalidation halts the close; it is never a permission to switch to `SAFE_CLOSE`.

## Probe procedure

1. Install or build the candidate backlogit. Only a released build can qualify.
   A pre-release, `+dirty`, or `-N-gSHA` development build is rejected before
   the minor line is checked and stays unverified whatever the comparison
   shows; the procedure qualifies a future released line, never such a build.
2. Create a throwaway workspace (never this repository's `.backlogit/`) with a
   small shipment whose manifest lists only the feature and its intended tasks.
   Create an already-archived `parent_id` descendant and a linked deliberation
   outside the manifest, so they are non-members.
3. Run `autoharness shipment cascade-close --classify-only --shipment <S>
   --feature <F> --sha <40-hex merge sha> --workspace <throwaway path> --json`
   against the throwaway workspace (all four arguments are required), and run
   the engine version probe on the same surface (CLI or MCP) that the close
   path will invoke.
4. Compare the candidate's `ArchiveItem` and `ShipShipment` cascade semantics with
   the verified facts at `v1.11.0` in `internal/core/archive.go`:
   * an already-archived out-of-manifest `parent_id` descendant is left untouched;
   * a linked deliberation that is not an explicit manifest member is left
     independent;
   * `ArchiveItem` side effects (linked stash archival) are unchanged.
5. Only if every comparison matches, update the constant, the P-015 token, and
   the `shipment-reconcile` skill in one change, and extend the pin tests in
   `tests/test_cascade_engine_semantics_gate.py` and
   `tests/test_engine_line_verification_runbook.py`.
6. Record the probe (version, commit, surface, comparison result) in
   [Backlogit Compatibility Matrix](backlogit-compatibility-matrix.md).

If any comparison differs or cannot be performed, leave the line unverified.
Closes then use `SAFE_CLOSE`.

## Verified set

Verified engine-semantics lines: `1.11`
