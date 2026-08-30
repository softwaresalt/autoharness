---
title: "v1.5.0 release preparation and publish — operational closure"
date: 2026-08-30
doc_type: closure
agent: "Ship"
source: "150-F / 158-S"
---

# Operational Closure — v1.5.0 Release Preparation and Publish

Shipment `158-S` / feature `150-F`. Mode: `pre-merge` (initial). This
artifact is the canonical releasability evidence record for the v1.5.0
release and will be updated at `post-merge` (after PR #423 merges) and
again after `150.009-T`/`150.010-T` (tag push, publish monitoring).

## Summary of the Change

Prepares and publishes `autoharness` v1.5.0: two accepted release-blocker
fixes (circuit-breaker checkpoint YAML-safety, stale manifest checksum), a
curated `CHANGELOG.md` section from 34 closure records, a synchronized
six-surface version bump, and two pre-merge dry-run gates (build/package
integrity, quality gates) — both PASS.

## CI Status and Unresolved Review Items

- CI: all checks green (`detect code changes`, `pipeline-topology
  (ambient)`, `test`, `ci gate`) on PR #423 at HEAD
  `3f6172a53845a8f47abd4d53ea3ccc01a2896d6f`.
- Copilot review (P-018): `SATISFIED` — 1 Copilot-authored thread raised
  and resolved (test-coverage gap; fixed and thread resolved).
- Local review: `READY_WITH_FOLLOWUPS` — 0 P0/P1, 3 P2 fixed, 2 P3 accepted
  as residual risk (see PR #423 Local Review Readiness block for detail).
- No unresolved review items remain.

## Runtime Verification Report

`docs/closure/2026-08-30-v1_5_0-release-preparation-runtime-verification.md`
— Verdict: **PASS**. CLI surface (`autoharness --help`, `autoharness
version`, `autoharness home`) verified both from the source tree and from
an isolated packaged-wheel install.

## Risky Actions

- **PA-1** (push annotated tag `v1.5.0`) — CRITICAL — not yet executed;
  gated on explicit operator go/no-go per `150.009-T`. `ActionResult`:
  pending.
- **PA-2** (PyPI publish, automated by `release.yml`) — CRITICAL —
  irreversible; implied by PA-1. `ActionResult`: pending.
- **PA-3** (re-record two manifest checksums) — MEDIUM — executed and
  verified (`150.001-T`, `150.002-T`); each checksum change was justified
  against committed content before rewriting. `ActionResult`: complete.
- **PA-4** (regenerate `uv.lock`) — MEDIUM — executed via WSL (native
  Windows networking blocked); diff inspected and confirmed limited to the
  `autoharness` version field only. `ActionResult`: complete.
- **PA-5** (fold/remove `## Unreleased`) — MEDIUM — executed; content
  moved into the new `## 1.5.0` section, verified via diff. `ActionResult`:
  complete.
- **PA-6** (paired template/installed edit) — MEDIUM — executed; template
  and installed circuit-breaker instruction re-verified byte-identical
  modulo declared placeholders. `ActionResult`: complete.

## Affected Runtime Surfaces

`cli` (packaging/distribution surface: `pyproject.toml` force-includes,
`uv build` wheel/sdist, PyPI publish). No API, browser, or background-job
surfaces are affected.

## Deployment / Release Path

Merge-only for this PR (`chore/158-s-...` → `main`, merge commit). The
actual "deployment" is the subsequent tag-triggered `release.yml` workflow
(`150.009-T`/`150.010-T`), which builds, publishes to PyPI, and creates the
GitHub Release — tracked as a separate, later step in this same closure
record.

## Pre-Deploy Audits

- Confirmed no versioned schema mirror (`schemas/**/<version>.schema.json`)
  was mutated in place (INV-4).
- Confirmed all six version-bump surfaces are consistent
  (`test_distribution_and_plugin_versions_stay_in_sync` passes).
- Confirmed `release.yml`'s `awk` changelog-extraction contract locally
  dry-run against the new `## 1.5.0 - 2026-08-30` heading (139-line
  non-empty notes file).
- Confirmed the PyPI publish credential / OIDC trusted-publishing
  configuration is declared in `release.yml` (`pypa/gh-action-pypi-publish`,
  `id-token: write` permission) — will be re-confirmed as part of
  `150.010-T` monitoring.

## Post-Deploy Checks (deferred to `150.010-T`)

- `uv tool run --isolated --no-config --from "autoharness==1.5.0"
  autoharness version` → must equal exactly `1.5.0`.
- `uv tool run --isolated --no-config --from "autoharness==1.5.0"
  autoharness home` → must resolve.
- GitHub Release created/updated with non-empty notes.

## Healthy Signals

- `release.yml` completes all steps (tag validation, changelog extraction,
  build, twine check, PyPI publish, PyPI smoke test, GitHub Release
  creation) with green status.
- Published-package smoke test (above) passes within the 280-second PyPI
  propagation window.

## Failure Signals

- Any `release.yml` step fails.
- Published-package smoke test fails after a confirmed successful publish.
- PyPI probe for `autoharness==1.5.0` returns ambiguous/unreachable at any
  point where a determination is required.

## Monitoring Plan

Watch the `release.yml` workflow run to completion (up to the ~5-minute
budget implied by the 280-second PyPI polling window plus build time).
Record the conclusion of each monitoring signal in order per `150.010-T`'s
scope: tag-version validation → changelog extraction → build → twine check
→ PyPI pre-publish state → publish → PyPI JSON probe → isolated smoke →
GitHub Release creation.

## Rollback Trigger

- `release.yml` fails **before** the PyPI publish step → safe: delete the
  tag, fix, re-tag. No version burned.
- `release.yml` fails **at or after** the PyPI publish step → probe PyPI
  first (`https://pypi.org/pypi/autoharness/1.5.0/json`); absent → safe
  path above; present → version is permanently consumed, do NOT retry
  `1.5.0`, escalate, remediate as `1.5.1`.

## Rollback Procedure

Per the plan's Rollback and stop conditions table
(`docs/plans/2026-08-29-v1_5_0-release-preparation-plan.md`): delete the
tag only in the confirmed-safe (pre-upload) case; never delete the tag once
`1.5.0` is confirmed present on PyPI (deleting does not unpublish and
creates misleading history).

## Validation Window

Up to 280 seconds of PyPI CDN propagation (per `release.yml` L127), plus
the workflow's own build/publish duration. Slow propagation is not a
failure and must not trigger rollback before the window elapses.

## Owner

Ship (this session) monitors through `150.010-T`; the operator owns the
PA-1 tag-push go/no-go decision and any post-publish escalation.

## Compaction Status (P-020)

`pending` — will be finalized to `done` or `degraded` during Ship's
post-merge closure, after `compact-context` is invoked.

## Releasability Evidence

Per `runtime_validation.releasability` (`required: false`,
`status_when_satisfied: "READY"`, `required_evidence: []`):

**Status: READY** (pre-merge). All required pre-merge evidence is present:
CI green, Copilot review satisfied, local review readiness
`READY_WITH_FOLLOWUPS` with documented residual risk, runtime verification
`PASS`, both dry runs `PASS`, no unresolved review items. The irreversible
tag-push/publish step (`150.009-T`/`150.010-T`) remains gated on explicit
operator approval and is tracked as the next phase of this same closure
record, not a blocker to the merge itself.
