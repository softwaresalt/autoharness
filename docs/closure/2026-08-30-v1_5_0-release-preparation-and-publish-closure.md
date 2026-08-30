---
title: "v1.5.0 release preparation and publish — operational closure"
date: 2026-08-30
doc_type: closure
agent: "Ship"
source: "150-F / 158-S"
---

# Operational Closure — v1.5.0 Release Preparation and Publish

Shipment `158-S` / feature `150-F`. Mode: `post-deploy` (final). This
artifact is the canonical releasability evidence record for the v1.5.0
release, covering pre-merge, post-merge, tag, and publish-monitoring
phases in full.

## Summary of the Change

Prepares and publishes `autoharness` v1.5.0: two accepted release-blocker
fixes (circuit-breaker checkpoint YAML-safety, stale manifest checksum), a
curated `CHANGELOG.md` section from 34 closure records, a synchronized
six-surface version bump, and two pre-merge dry-run gates (build/package
integrity, quality gates) — both PASS.

## CI Status and Unresolved Review Items

- PR #423 (main implementation): CI green, Copilot review `SATISFIED`
  (1 thread raised and resolved), local review `READY_WITH_FOLLOWUPS`.
  Merged as `8b79de94e6705f4e950257073b263369a7e258a7`.
- PR #425 (post-merge hotfix, P-021 stash `E738A7D1`): fixed 10
  pre-existing `tests/test_gates_topology.py` tests that only ever ran in
  `pull_request`-triggered CI, surfaced by `158-S` being the first
  push-triggered CI run to actually execute the `test` job in a while. CI
  green, Copilot review `SATISFIED` (no findings). Merged as
  `8922b62e4c548daaa0dc0c1c56be2c8817862af9`.
- PR #426 (PyPI publish-compatibility fix): pinned
  `core-metadata-version = "2.4"` after the first `v1.5.0` tag attempt
  failed at publish time (hatchling 1.32.0's Metadata-Version 2.5 vs. the
  pinned publish action's older twine). CI green, Copilot review
  `SATISFIED` (1 thread raised — missing regression-test coverage — fixed
  and resolved). Merged as `ca3232a8969b321f085eb4958d5e2f8f47259d2c`.
- Main confirmed green (push-triggered CI, all 4 checks) after each of the
  three merges above.
- No unresolved review items remain across all three PRs.

## Runtime Verification Report

`docs/closure/2026-08-30-v1_5_0-release-preparation-runtime-verification.md`
— Verdict: **PASS**. CLI surface (`autoharness --help`, `autoharness
version`, `autoharness home`) verified both from the source tree and from
an isolated packaged-wheel install, and again from the actual published
PyPI package (see the publish-evidence closure doc below).

## Publish Monitoring and Evidence

`docs/closure/2026-08-30-v1_5_0-release-monitoring-and-publish-evidence.md`
— full monitoring signal log for both the failed first tag attempt (safely
rolled back, no version burned) and the successful second attempt,
published-package smoke evidence, and the PyPI project page / GitHub
Release URLs.

## Risky Actions

- **PA-1** (push annotated tag `v1.5.0`) — CRITICAL — **executed twice**:
  attempt 1 on `8922b62e` (safely rolled back pre-upload after a confirmed
  PyPI 404 probe, no version burned); attempt 2 on the corrected commit
  `ca3232a8` (succeeded). `ActionResult`: **complete**.
- **PA-2** (PyPI publish, automated by `release.yml`) — CRITICAL —
  irreversible; succeeded on attempt 2. `1.5.0` is now permanently
  consumed on PyPI. `ActionResult`: **complete**.
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
  configuration declared in `release.yml` (`pypa/gh-action-pypi-publish`,
  `id-token: write` permission) is genuinely functional — confirmed
  end-to-end by the successful publish itself (attempt 2, run
  `33333803838`): OIDC authentication succeeded and the distribution
  actually uploaded to PyPI. This is a completed gate, not an outstanding
  one.

## Post-Deploy Checks (executed — see 150.010-T evidence doc)

- `uv tool run --isolated --no-config --from "autoharness==1.5.0"
  autoharness version` → **`1.5.0`** exactly, exit 0. ✅
- `uv tool run --isolated --no-config --from "autoharness==1.5.0"
  autoharness home` → resolved. ✅
- GitHub Release created with non-empty notes:
  <https://github.com/softwaresalt/autoharness/releases/tag/v1.5.0> ✅

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
the workflow's own build/publish duration. Actual propagation was
immediate — the published-package smoke test succeeded on first probe,
and the full `release.yml` run completed in 1m32s.

## Owner

Ship (this session) executed and monitored through `150.010-T`; the
operator's upfront authorization ("create/push the annotated v1.5.0 tag
only after all irreversible-boundary gates pass") served as the PA-1
go/no-go, satisfied at both tag attempts once all gates genuinely passed.

## Compaction Status (P-020)

`done` — `compact-context` invoked at post-merge closure; the just-closed
release unit's session memory was compacted into
`docs/memory/compacted/2026-08-30-158-s-compacted.md`, with the verbose
original archived to `docs/archive/memory/2026-08-30/`.

## Releasability Evidence

Per `runtime_validation.releasability` (`required: false`,
`status_when_satisfied: "READY"`, `required_evidence: []`):

**Status: READY (final).** `autoharness` v1.5.0 is published to PyPI
(<https://pypi.org/project/autoharness/1.5.0/>), the GitHub Release is
live (<https://github.com/softwaresalt/autoharness/releases/tag/v1.5.0>),
the published-package smoke test passed, and main is confirmed green
after all three merges (PR #423, #425, #426). All required evidence for
this release is satisfied; no conditions remain outstanding. The one
emergent finding outside `158-S`'s original scope (the `GITHUB_HEAD_REF`
push-context test fix, PR #425) is captured as P-021 stash entry
`E738A7D1` for Stage's retrospective review — it does not block this
release's releasability status.

