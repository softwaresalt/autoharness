---
title: "Ship session memory — v1.5.0 release execution (158-S)"
date: 2026-08-30
doc_type: memory
agent: "Ship"
source: "150-F / 158-S"
---

# Session Memory — v1.5.0 Release Execution (158-S)

## Outcome

`autoharness` v1.5.0 is published to PyPI and released on GitHub. Shipment
`158-S` safe-closed via the verified P-015 cascade path (`150-F`
`archived_status: done`, `158-S` `archived_status: shipped`).

## Task IDs completed

`150.001-T` through `150.010-T` — all done, archived, commit-tracked.

## PRs merged (chronological)

1. **PR #423** — main implementation (`chore/158-s-v1-5-0-release-preparation-and-publish`
   → `main`). Merge commit `8b79de94e6705f4e950257073b263369a7e258a7`.
   Circuit-breaker YAML-safety hardening, manifest checksum refresh,
   curated CHANGELOG, six-surface version bump, dry runs A/B PASS,
   runtime verification, operational closure (pre-merge).
2. **PR #425** — post-merge hotfix (`post-merge/150-f-github-head-ref-ci-hotfix`
   → `main`). Merge commit `8922b62e4c548daaa0dc0c1c56be2c8817862af9`.
   Fixed 10 tests in `tests/test_gates_topology.py` that failed on
   push-triggered CI (`GITHUB_HEAD_REF` ambient empty string). Captured as
   P-021 stash entry `E738A7D1` (out of `158-S`'s original scope, applied
   as a separate hotfix because it blocked confirming main-green before
   tagging).
3. **PR #426** — PyPI publish-compatibility fix
   (`post-merge/150-f-pin-core-metadata-version` → `main`). Merge commit
   `ca3232a8969b321f085eb4958d5e2f8f47259d2c`. Pinned
   `core-metadata-version = "2.4"` after the first tag/publish attempt
   failed (hatchling 1.32.0's Metadata-Version 2.5 rejected by the pinned
   publish action's older twine).

## Files modified (substantive, excluding .backlogit/ bookkeeping)

- `templates/instructions/circuit-breaker.instructions.md.tmpl` +
  `.github/instructions/circuit-breaker.instructions.md` (paired edit)
- `.autoharness/harness-manifest.yaml` (two checksum refreshes)
- `CHANGELOG.md`
- `pyproject.toml`, `src/autoharness/__init__.py`, `plugin.json`,
  `.github/plugin/marketplace.json`, `uv.lock` (version bump + metadata pin)
- `tests/test_circuit_breaker_checkpoint_yaml_safety.py` (new)
- `tests/test_gates_topology.py` (GITHUB_HEAD_REF fix)
- `tests/test_verify_workspace.py` (new core-metadata-version regression test)
- `docs/plans/2026-08-29-v1_5_0-changelog-curated-inventory.md` (new)
- `docs/plans/2026-08-29-v1_5_0-dry-run-evidence.md` (new)
- `docs/closure/2026-08-30-v1_5_0-release-preparation-runtime-verification.md` (new)
- `docs/closure/2026-08-30-v1_5_0-release-preparation-and-publish-closure.md` (new)
- `docs/closure/2026-08-30-v1_5_0-release-monitoring-and-publish-evidence.md` (new)
- `docs/compound/2026-08-30-github-actions-push-event-github-head-ref-empty-string-not-absent.md` (new)
- `docs/compound/2026-08-30-unpinned-hatchling-metadata-version-vs-pinned-publish-action.md` (new)

## Decisions and rationale

- Treated the `GITHUB_HEAD_REF` push-context test failure as an emergent
  release blocker discovered mid-execution (not part of `158-S`'s original
  authorized scope) and applied a small, precedented, separate hotfix
  rather than expanding `158-S`'s own manifest — captured via P-021 stash
  entry `E738A7D1` for Stage's retrospective review.
- Treated the hatchling metadata-version publish failure as squarely
  in-scope for `150.009-T`'s own contract (making the tagged release
  actually publish) since it was the direct build-time mechanism blocking
  this shipment's core deliverable.
- Used WSL (Ubuntu 26.04) as the working execution transport for all
  `uv build` / `uv lock` / `twine check` / isolated-install operations
  throughout the session, because native Windows networking in this
  sandbox cannot complete a TLS handshake with `files.pythonhosted.org`
  (confirmed via `curl.exe -4/-6` schannel errors and
  `Invoke-WebRequest` `HandshakeFailure`), while `pypi.org`'s JSON API and
  WSL's own network path both work natively. This is a local-sandbox
  network-path quirk, not a release-workflow issue — GitHub Actions'
  runner is unaffected.
- First `v1.5.0` tag attempt failed at PyPI publish; immediately probed
  PyPI (confirmed 404, nothing uploaded) before any remediation, per the
  release plan's rollback protocol — deleted the tag safely, fixed the
  root cause, and re-tagged on the corrected commit after re-running the
  full pre-tag assertion checklist. No version was ever burned.

## Failed approaches / dead ends

- Attempted `gh api repos/.../requested_reviewers` to explicitly request
  Copilot review before discovering the repository already auto-requests
  Copilot review on PR creation — the explicit requests were unnecessary
  no-ops.
- Initial hotfix branch name (`fix/push-ci-github-head-ref-empty-string-env-guard`)
  was rejected by the `pipeline-topology` gate's ambient CI backstop
  (`BRANCH_MISMATCH`) because shipment `158-S` was still active — renamed
  to the `post-merge/150-f-...` pattern, which the gate already treats as
  ownership-eligible for a still-active shipment's post-merge work.
- `150.008-T` was completed in substance (PR opened, reviewed, merged) but
  never explicitly moved to `done` status at the time — caught only when
  `backlogit shipment ship` refused to close with it still `active`. Fixed
  before retrying the cascade close.

## Open questions / follow-ups for Stage

- P-021 stash entry `E738A7D1` (GITHUB_HEAD_REF push-context test gap):
  requires deliberation on whether the fix treatment (separate hotfix
  applied immediately) was correct, and whether a dedicated push-context
  regression test suite gap should be addressed more broadly.
- Stash `8E10B13B` (release.yml fail-closed-on-existing-PyPI-version
  hardening) remains deferred, unchanged by this shipment.
- Stashes `6A2D62DD` and `2E67938C` (sizing/session-lifecycle spike and
  feature) remain deferred, unchanged by this shipment.

## Next steps

**Historical note**: this section captured the state as of when this
memory was originally written, before `compact-context` ran. By the time
this document was archived (as part of that same `compact-context`
invocation), the actual sequence had already completed: `compact-context`
(P-020) ran first, producing this archival and
`docs/memory/compacted/2026-08-30-158-s-compacted.md`; the post-merge
closure PR (`post-merge/150-f-v1-5-0-release-preparation-and-publish`)
was opened afterward, already carrying the compacted memory rather than
needing it as a future step. The original (now-stale) text is preserved
below for historical accuracy of what was known at write time:

Post-merge closure PR (this branch, `post-merge/150-f-v1-5-0-release-preparation-and-publish`)
needs: local review, §1.9 readiness gate, operator approval, merge. Then
mandatory `compact-context` invocation (P-020), closure index resync, and
return to `main`.
