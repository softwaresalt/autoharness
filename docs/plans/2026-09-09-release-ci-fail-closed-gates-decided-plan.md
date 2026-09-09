---
title: "Decided plan — SHIP-2 — Release and CI pipeline fail-closed gates"
doc_type: decided-plan
status: shipped
created: 2026-09-09
supersedes: docs/archive/plans/2026-08-31-ship2-release-ci-fail-closed-gates-plan.md
shipment_unit: "SHIP-2"
shipment: 160-S
feature: 152-F
tasks: [152.001-T, 152.002-T, 152.003-T]
merge_commit: 12b2d4a36f0cdcd9a07aa2cfc13b372cea2ef386
pr: 439
plan_review_verdict: PASS
---

# SHIP-2 — Release and CI pipeline fail-closed gates (decided plan)

Consolidated from the fully-reviewed plan (multi-persona adversarial gate,
`Verdict: PASS`): 1 P0 + 4 P1 raised across cycles 0/1 and resolved
**before harvest**, plus a second P0 raised in the extended cycle 5 (after
harvest — task `152.001-T` already existed — but before its implementation
was executed) and likewise resolved. Cumulative across the full
review-fix history: 2 P0 + 4 P1 raised, all resolved, zero unresolved
P0/P1. Consolidated together with the shipment's own review-fix history.
Shipped as `160-S` / PR #439, merge commit `12b2d4a3`.

## Problem consolidated

Two independent fail-open conditions:

* **8E10B13B** — the release workflow's pre-publish PyPI probe
  (`.github/workflows/release.yml`) exited 0 when the target version already
  existed, silently skipping the upload (`skip-existing: true`) and smoke-
  testing pre-existing artifacts instead of failing the run.
* **E738A7D1** — no end-to-end regression guard existed for GitHub Actions'
  ambient empty-string `GITHUB_HEAD_REF` in push-triggered runs; five
  `test_gates_topology.py` tests had been hotfixed individually
  (`_clear_ambient_github_head_ref()`) with no guard against recurrence.

## Final decisions

* **Hard-fail unconditionally** on a present version; retain
  `skip-existing: true` as defence in depth; **no override mechanism** (an
  unattended, tag-triggered workflow has no operator to invoke one; bump +
  re-tag is the correct remedy).
* **H1**: fail on presence only, never on inferred build-hash identity.
* **H2/H2a**: "present" requires the final resolved host to be `pypi.org`,
  a JSON-decodable body, and the body naming **the requested version**; any
  other well-formed-but-wrong response is a re-raised transport/integrity
  error, never "present" and never "absent".
* **H2b**: a version *mismatch* on the exact-version endpoint is an
  integrity anomaly (cache/mirror/interception), not evidence of absence —
  re-raise, never proceed. Absence is proved by `404` alone.
* **H3**: no change to the pinned publish action SHA, trigger, permissions,
  or secrets.
* **H4**: the regression test suite is fully hermetic (injected responses,
  no network I/O).
* **H5**: TDD sequencing — task 2 (extraction + red tests) lands before
  task 1 (the fail-closed fix), so the fix's effect is observed turning a
  genuinely red case green.
* **H6**: every task runs in `careful` safety mode; task 1 additionally
  `freeze-scope`-bounded to the extracted probe helper plus one inline
  comment in `release.yml`.

## Implementation units that survived review

1. **152.001-T** (S/medium) — `build_support/pypi_probe.py`'s
   present-version branch replaced with the fail-closed outcome (CLI exit 2
   with an R1/R2/R3 remedy message: bump+re-tag; out-of-band post-publish
   completion; never disable the gate). Only other edit: one inline comment
   on `skip-existing: true` in `release.yml`.
2. **152.002-T** (M/medium) — extracted the inline heredoc probe into
   `build_support/pypi_probe.py` (shared `build_support/__init__.py` with
   SHIP-10; as shipped, `build_support/**` is present in the sdist and
   absent from the wheel — full exclusion from the sdist as well is
   SHIP-10's explicitly out-of-scope future work, not this shipment's
   delivered state), with typed outcomes
   (`ProbeResult` ABSENT/PRESENT, `ProbeIntegrityError`/`ProbeTransportError`
   derived from `ProbeError`), `HTTPError`-before-`URLError` exception
   ordering, and 6 hermetic cases C1–C6 (404-proceeds; present-version
   exit-2; transport-error propagates; wrong-host redirect; malformed JSON
   both shapes; mismatched-version integrity error) plus CLI-mapping cases.
3. **152.003-T** (M/medium) — end-to-end push-context test for ambient
   empty-string `GITHUB_HEAD_REF`, plus an AST-based static guard asserting
   every `patched_environ(GITHUB_HEAD_REF=...)` call site in
   `test_gates_topology.py` is preceded by `_clear_ambient_github_head_ref()`
   (later extended in review-fix to also cover `except`/`match` blocks).

## Key constraints (binding, unchanged through review-fix)

* No artifact-identity verification against PyPI (H1).
* No override/workflow-dispatch/repo-variable bypass mechanism.
* No change to `tests/_env_patch.py` A4/A5 semantics.
* `build_support/**` coordinated with SHIP-10 on distribution-channel
  exclusion; as shipped, it is present in the sdist and absent from the
  wheel — excluding it from the sdist as well is SHIP-10's explicitly
  out-of-scope future work, not a constraint this shipment achieved.

## Rejected alternatives

* Telling the operator to "re-run only the post-publish jobs" (P0 finding 1)
  — rejected because the workflow has exactly one job and GitHub Actions
  cannot re-run an individual step; replaced with R1/R2/R3 remedy wording.
* Treating a version mismatch as "proceed" (cycle-1 disposition of C6) —
  reversed in cycle 2: a mismatch on the exact-version endpoint is positive
  evidence of an anomaly, not weak evidence of absence.
* Generalizing the `GITHUB_HEAD_REF` guard into a suite-wide environment-
  hygiene framework — bounded to `test_gates_topology.py`; broader scope is
  a P-021 capture, not this shipment (see follow-ups below).

## Post-shipment follow-ups (P-021, Stage-owned)

`364681C4` (release.yml concurrency group gap), `D25080A3` (AST guard
nested-call detection gap), `65402F31` (pre-existing `__main__` guard
misplacement in `test_gates_topology.py`) — all captured during PR #439
review, require Stage deliberation, none block this shipment.

## Verification

`PYTHONPATH=src python -m unittest discover -s tests` (2087 tests, 0
failures, 20 skipped, final run); `uv build` (sdist + wheel content
verified); markdownlint on changed docs (pre-push hook). All required CI
checks green at merge.
