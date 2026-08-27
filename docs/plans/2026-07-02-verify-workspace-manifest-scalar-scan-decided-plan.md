---
source: docs/plans/2026-07-02-verify-workspace-manifest-scalar-scan-decided-plan.md
title: "verify_workspace Manifest Scalar Placeholder Scan — decided plan"
doc_type: decided-plan
status: shipped
created: 2026-07-02
feature: "057-F"
tasks: ["057.001-T"]
supersedes:
  - docs/archive/plans/2026-07-02-verify-workspace-manifest-scalar-scan-plan.md
---

# Decided Plan: verify_workspace Manifest Scalar Placeholder Scan

**Outcome:** Shipped. The source plan for feature `057-F` closes a verifier gap: unresolved `{{...}}` placeholders in top-level scalar fields of `.autoharness/harness-manifest.yaml` can currently ship undetected because `verify_workspace.py` scans rendered artifacts but not the manifest's own scalar values.

**Delivery status (verified against the backlog at compaction time):** shipped — `057-F`, `057.001-T` confirmed complete in `.backlogit/`.

## Decision

Extend `verify_workspace()` to scan the manifest's top-level string-valued scalar fields — especially `autoharness_version` — for unresolved placeholders using the same detection semantics already applied to rendered artifacts. Any match should emit a blocker (for example `unresolved-manifest-placeholder`) so verification fails instead of warning.

## Implementation (1 task)

- **057.001-T** — add the scalar scan in `src/autoharness/verify_workspace.py` and the paired regression test in `tests/test_verify_workspace.py`, covering both the failing `{{AUTOHARNESS_VERSION}}` case and the passing resolved-manifest path.

## Key constraints preserved

- Reuse the existing placeholder regex rather than inventing a second detection rule.
- Generalize to top-level string-valued scalars, but skip the `artifacts` list because the artifact loop already covers it.
- Keep this as detection only: the plan does not change install-harness rendering or resolution behavior.
- Rely on the existing report writers to surface blockers in both JSON and Markdown outputs.

## Rejected alternatives

- **Scan only `artifacts[]`** — rejected because that leaves manifest-scalar placeholders invisible to verification.
- **Introduce a second placeholder regex** — rejected because it could drift from the artifact scan's semantics.
- **Fix rendering instead of verification** — rejected because this task is specifically about detection, not template/render changes.

## Verification expectations

- Run `uv run python -m pytest tests/test_verify_workspace.py`.
- Confirm the new blocker appears in both JSON and Markdown report paths.