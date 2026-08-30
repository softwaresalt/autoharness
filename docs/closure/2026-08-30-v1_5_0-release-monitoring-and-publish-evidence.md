---
title: "v1.5.0 release monitoring, publish evidence, and rollback record (150.010-T)"
date: 2026-08-30
doc_type: closure
agent: "Ship"
source: "150-F / 158-S"
---

# v1.5.0 Release Monitoring and Publish Evidence

Shipment `158-S` / feature `150-F`, task `150.010-T`.

## Attempt 1 (FAILED, safely rolled back — no version burned)

- Tag `v1.5.0` pushed on merge commit `8922b62e4c548daaa0dc0c1c56be2c8817862af9`.
- `release.yml` run [`33329970485`](https://github.com/softwaresalt/autoharness/actions/runs/33329970485)
  (exact per-step conclusions confirmed via the GitHub Actions jobs API,
  not inferred from the failing log excerpt alone):
  1. Validate tag matches pyproject version — PASS
  2. Extract changelog for this version — PASS (non-empty notes)
  3. Build wheel and sdist (`uv build`) — PASS
  4. Validate built distributions (`uvx twine check dist/*`) — **PASS**
  5. Check PyPI pre-publish state — **PASS**
  6. Publish distribution to PyPI — **FAIL**: the pinned
     `pypa/gh-action-pypi-publish` action runs its own internal
     distribution validation before uploading, and that internal check
     failed with `InvalidDistribution: Invalid distribution metadata:
     '2.5' is not a valid metadata version`. The standalone "Validate
     built distributions" step (step 4, using whatever `twine` version
     `uvx` resolves fresh) had already passed — it did not catch this,
     because it resolves the *latest* twine (which already understands
     Metadata-Version 2.5), while the pinned action's *bundled* twine
     does not. This is exactly the toolchain-version-skew explained in
     `docs/compound/2026-08-30-unpinned-hatchling-metadata-version-vs-pinned-publish-action.md`.
  7. (not reached, `skipped`) Smoke test published package from PyPI
  8. (not reached, `skipped`) Create or update GitHub Release

  Root cause: `hatchling` 1.32.0 defaults to `Metadata-Version: 2.5` (PEP
  794); the pinned `pypa/gh-action-pypi-publish` action bundles
  `twine < 7.0.0` / `packaging < 26.0`, which does not recognize 2.5.

- **Rollback determination (per the release plan's rollback protocol)**:
  immediately probed `https://pypi.org/pypi/autoharness/1.5.0/json` —
  returned **404**. Failure occurred **at** the PyPI publish step but
  strictly **before** any file was actually uploaded (the action's
  internal validation runs before the upload call, and the 404 probe
  independently confirms nothing reached PyPI) — this is the SAFE,
  no-version-burned path.
- **Action taken**: deleted the `v1.5.0` tag (`git push origin --delete
  v1.5.0` + `git tag -d v1.5.0`). Fixed the root cause (pinned
  `core-metadata-version = "2.4"` in `pyproject.toml`, PR #426 — merged as
  commit `ca3232a8969b321f085eb4958d5e2f8f47259d2c`). No version was
  burned; `1.5.0` remained available for re-tagging.

## Attempt 2 (SUCCEEDED)

- Tag `v1.5.0` re-created and pushed on the corrected merge commit
  `ca3232a8969b321f085eb4958d5e2f8f47259d2c` (after re-running the full
  pre-tag assertion checklist against this exact commit: dry run A/B PASS,
  main green, CHANGELOG section present, PyPI absence re-confirmed 404).
- `release.yml` run [`33333803838`](https://github.com/softwaresalt/autoharness/actions/runs/33333803838)
  completed successfully in 1m32s. Monitoring signals, in order:
  1. Validate tag matches pyproject version — PASS
  2. Extract changelog for this version — PASS
  3. Build wheel and sdist — PASS
  4. Validate built distributions (`uvx twine check`) — PASS
  5. Check PyPI pre-publish state — PASS
  6. Publish distribution to PyPI — PASS
  7. Smoke test published package from PyPI — PASS
  8. Create or update GitHub Release — PASS

## Published-Package Smoke Evidence (captured independently by Ship)

- PyPI JSON API: `https://pypi.org/pypi/autoharness/1.5.0/json` →
  **HTTP 200**, `info.version == "1.5.0"`.
- `uv tool run --isolated --no-config --from "autoharness==1.5.0"
  autoharness version` → **`1.5.0`** exactly, exit 0.
- `uv tool run --isolated --no-config --from "autoharness==1.5.0"
  autoharness home` → resolved to an installed
  `site-packages/autoharness/data` path, exit 0.
- PyPI project page: <https://pypi.org/project/autoharness/1.5.0/>
- GitHub Release: <https://github.com/softwaresalt/autoharness/releases/tag/v1.5.0>
  (`isDraft: false`, `isPrerelease: false`, published
  `2026-08-30T20:31:29Z`).

## Validation Window

The published-package smoke test above succeeded on first probe,
well within the workflow's own 280-second PyPI-propagation polling
budget — no propagation delay was observed.

## Rollback / Forward-Fix Decisions Summary

| Event | Decision | Outcome |
|---|---|---|
| Attempt 1 `twine check` failure | Probe PyPI first (404 confirmed) → SAFE pre-upload path | Tag deleted, no version burned |
| Root cause fix | Pin `core-metadata-version = "2.4"` (PR #426) | Merged, main green |
| Attempt 2 | Re-tag on corrected commit after full re-verification | Full success: published, smoke-tested, GitHub Release created |

No yank, no `1.5.1` remediation release was required — the issue was
caught and fixed entirely within the pre-upload window.
