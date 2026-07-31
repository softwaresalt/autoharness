---
title: "Release 1.4.5 Closure — Session Memory"
shipment: "038-S"
feature: "042-F"
version: "1.4.5"
merge_sha: "36c6a8b1cdfb87c48640c670f3a359bd5a551a56"
tag: "v1.4.5"
pr: 96
pr_url: "https://github.com/softwaresalt/autoharness/pull/96"
release_url: "https://github.com/softwaresalt/autoharness/releases/tag/v1.4.5"
release_workflow_run: 26050695560
pypi_confirmed: true
date: "2026-05-18"
---

# Release 1.4.5 Closure — Session Memory

## Release Summary

autoharness **v1.4.5** was released on 2026-05-18.

| Artifact | Value |
|---|---|
| Merge SHA | `36c6a8b1cdfb87c48640c670f3a359bd5a551a56` |
| Tag | `v1.4.5` |
| PR | [#96](https://github.com/softwaresalt/autoharness/pull/96) |
| Release | [v1.4.5](https://github.com/softwaresalt/autoharness/releases/tag/v1.4.5) |
| Workflow run | [26050695560](https://github.com/softwaresalt/autoharness/actions/runs/26050695560) |
| PyPI | `autoharness==1.4.5` confirmed |

## Closure State

- Persisted the local backlogit shipment archive for `038-S`
- Preserved task/archive log side effects for `042-F`, `042.001-T`, and `042.002-T`
- Removed `.backlogit/queue/038-S.md` from tracked queue state and added `.backlogit/archive/038-S.md`
- Corrected archive provenance fields for the `042-*` artifacts to point back to their queue origins

## Remaining Manual Gate

- A dedicated post-merge closure PR is still required to land these repository-tracked closure artifacts on `main`
- Per P-014, that PR must pass Copilot review readiness checks
- Per Ship policy, merge must wait for explicit operator approval after readiness is presented
