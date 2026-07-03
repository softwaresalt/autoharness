---
title: "verify_workspace Manifest Scalar Placeholder Scan — Implementation Plan"
description: "Harden verify_workspace.py to detect unresolved {{...}} placeholders in harness-manifest.yaml scalar fields (esp. autoharness_version), closing a gap where the verifier only scans rendered artifacts[]."
source_documents:
  - "src/autoharness/verify_workspace.py"
  - "tests/test_verify_workspace.py"
feature: "057-F"
tasks:
  - "057.001-T"
source_stash_ids:
  - "B2F96A58"
scope: "autoharness CLI (verify_workspace) — single domain"
tags:
  - "cli"
  - "verification"
  - "hardening"
  - "install-harness"
---

## Problem Frame

`install-harness` Step 4.1 item 5 requires that no unresolved `{{...}}`
placeholder ships in installed output. `verify_workspace.py` enforces this only
for **rendered artifacts**: the loop at `verify_workspace.py:2159`
(`for artifact in manifest.get("artifacts")`) reads each installed file and runs
`_find_unresolved_placeholders` (`verify_workspace.py:805`). The manifest's own
**top-level scalar fields** are never scanned. A literal
`autoharness_version: "{{AUTOHARNESS_VERSION}}"` in `.autoharness/harness-manifest.yaml`
would therefore ship undetected. This is a follow-up from the `054-F`
adversarial review.

## Design

Add a manifest-scalar placeholder scan in `verify_workspace()` after the
manifest is loaded (`verify_workspace.py:2073`) and before/near the artifacts
loop:

1. Walk the manifest's top-level scalar fields (at minimum `autoharness_version`;
   generalize to all string-valued scalars, skipping the `artifacts` list which
   is already covered).
2. Apply the same placeholder regex used by `_find_unresolved_placeholders`.
3. On a match, append a **blocker** (e.g. `kind: "unresolved-manifest-placeholder"`)
   with the field name and the offending placeholder text, so verification
   fails rather than warns — an unresolved version string is a hard install
   error, consistent with the artifacts[] treatment.

Prefer reusing the existing placeholder pattern rather than introducing a second
regex, to keep detection semantics identical to the artifact scan.

## Task Breakdown

### 057.001-T — Scan manifest scalar fields + regression test

* **Code**: add the manifest-scalar scan to `src/autoharness/verify_workspace.py`
  and emit a blocker on any unresolved `{{...}}` in a scalar field.
* **Test**: add a regression test to `tests/test_verify_workspace.py` that
  builds a manifest whose `autoharness_version` is a literal
  `{{AUTOHARNESS_VERSION}}` and asserts (a) the blocker is raised and (b)
  verification fails; confirm a fully-resolved manifest still passes.
* **Acceptance**: blocker fires for placeholders in manifest scalar fields (not
  only artifacts[]); regression test covers the `autoharness_version` case;
  existing tests still pass.
* **Width**: single CLI concern (code + its co-located test, TDD-aligned).

## Verification

* Run the existing verify_workspace test suite (`uv run python -m pytest
  tests/test_verify_workspace.py`) — green before and after.
* Confirm the new blocker appears in both the JSON and Markdown report paths
  (the report writers already surface `blockers`).

## Out of Scope

* No changes to install-harness rendering (this is detection, not resolution).
* No template or agent changes.
