---
type: session-memory
agent: Ship
date: 2026-07-03
session: post-merge closure - 057-F verify_workspace manifest scalar placeholder scan
shipment: 059-S
pr: 132
merge_commit: 6e6fd1cb1b24d16860004f42da5a098c16408c99
tags: [ship, closure, backlogit, safe-close, cascade-guard, verify-workspace, manifest, placeholders]
---

# Ship Session - 057-F Manifest Scalar Placeholder Scan (059-S)

## Summary

Shipment **059-S** delivered feature **057-F** / task **057.001-T** via PR
[#132](https://github.com/softwaresalt/autoharness/pull/132), merged into
`main` as merge commit `6e6fd1cb1b24d16860004f42da5a098c16408c99`.

The change hardens `verify_workspace.py` so `.autoharness/harness-manifest.yaml`
top-level scalar fields are scanned for unresolved `{{...}}` placeholders. The
primary target was `autoharness_version`, which could previously contain a
literal template token without being reported because only rendered artifacts
were scanned.

## What shipped

- Added `_scan_manifest_scalar_placeholders()` in
  `src/autoharness/verify_workspace.py`.
- Emitted `unresolved-manifest-placeholder` blockers for unresolved manifest
  scalar values.
- Added regression coverage in `tests/test_verify_workspace.py` for unresolved
  and resolved manifest scalar values.
- Relaxed the MCP config policy test so root `.mcp.json` may be absent or
  local-only, while still validating required MCP server entries when the file
  exists.
- Clarified that manifest scalar scanning reuses the placeholder token regex but
  does not apply Markdown code-fence skipping.
- Removed tracked `.mcp.json` from the PR after review identified the committed
  file as developer-local and non-portable; `.mcp.json` remains ignored.

## Review and merge notes

Copilot advisory comments on PR #132 were all addressed and resolved before
merge. The required local readiness block covered head
`2b34b8c503da0d3ca50cac6e6c6bace1ddfb2ab6` with outcome `READY`, blocking
findings `P0=0, P1=0`, and no follow-ups.

The normal merge attempt was rejected because GitHub branch policy still
reported `REVIEW_REQUIRED`. After explicit operator approval, the PR was merged
with `--admin --merge`. The resulting merge commit has two parents and satisfies
the repository merge-commit policy.

## Closure method

`backlogit shipment ship` was not used. Closure used safe single-artifact
operations:

1. `backlogit move 059-S --status done`
2. `backlogit move 057-F --status done`
3. `backlogit update 059-S --commit 6e6fd1cb1b24d16860004f42da5a098c16408c99`
4. `backlogit update 057-F --commit 6e6fd1cb1b24d16860004f42da5a098c16408c99`
5. `backlogit sync`
6. `backlogit doctor --format json`

The shipment, feature, and task are all archived. `backlogit doctor` reported no
new findings for `057-F`, `057.001-T`, or `059-S`; remaining doctor findings are
pre-existing historical `003`-`048` archive/orphan warnings.

## Remaining work

No follow-up work was identified for 059-S.
