---
title: "Stage session — 1EFDA8EE root scratch artifact removal (142-S)"
date: 2026-08-18
agent: stage
stash_id: 1EFDA8EE
shipment: 142-S
feature: 133-F
mode: DARK_MODE_ACTIVE
---

# Stage session — 1EFDA8EE (shipment 142-S)

Second and final item of the ordered DARK_MODE_ACTIVE run
(`EDE3CC2D` -> 141-S completed; cursor advanced to `1EFDA8EE`).

## Outcome

Reviewed backlog hierarchy plus exactly one queued shipment.

| Artifact | ID | Status |
|---|---|---|
| Covering feature | `133-F` | queued |
| Deletion task | `133.001-T` | queued, size XS, complexity trivial |
| Prevention/verification task | `133.002-T` | queued, size S, complexity low |
| Shipment | `142-S` | queued, 3 items |

Dependency: `133.002-T` depends on `133.001-T` (the allowlist test asserts the
artifacts are absent, so it must land after the deletion).

## Evidence verified read-only (Stage did NOT delete anything)

All three files remain present and byte-unmodified at session end. Deletion is
handed to Ship under the explicit operator authorization.

| Path | Git blob | Bytes | Lines | SHA-256 |
|---|---|---|---|---|
| `out.json` | `29a08875…` | 26390 | 588 | `12F53D59…C525843` |
| `res.json` | `47be98ac…` | 26388 | 587 | `8D6948EA…8635395` |
| `results.json` | `47be98ac…` | 26388 | 587 | `8D6948EA…8635395` |

**Evidence correction (P1):** the stash entry and F7 claim all three are
*identical*. False. `res.json` and `results.json` are byte-identical to each
other; `out.json` is a different blob (one-line delta). The corrected per-file
hashes are embedded in `133.001-T` so Ship's re-verification does not fail closed
on the inaccurate premise.

Provenance: `mode: verify-workspace`, `workspace_path: D:\Source\GitHub\backlogit`
(external). Single introducing commit `24777b44` (2026-04-25), which also added
`verify_workspace.py` — accidental capture of ad-hoc CLI output. No functional
dependents anywhere in the repo (source, tests, CI, scripts, packaging).

## Prevention decision

**One deterministic root-JSON allowlist test. NO `.gitignore` rule.**

The stash entry suggested "a gitignore rule or a CI check". The ignore rule was
deliberately rejected: strictly weaker coverage (three literal names vs. any
unexpected root JSON), *silent* failure mode, no effect on already-tracked files,
and it would silently suppress a legitimate future root JSON. The allowlist test
is the narrowest **robust** control and simultaneously satisfies the required
deterministic verification, so it adds no artifact beyond the mandatory
verification surface. Allowlist: `.mcp.json`, `plugin.json`.

## Gates

- Plan: `docs/plans/2026-08-18-root-scratch-artifact-removal-plan.md`
- Hardening: **not required** (`requires_plan_hardening: no`) — no schema, CLI
  distribution or template-family blast radius; three-file deletion plus one
  additive test with zero dependents.
- Review: `docs/reviews/2026-08-18-root-scratch-artifact-removal-review.md`
  6 personas, 19 findings, verdict **PASS**, 0 unresolved P0/P1.

## Protected operator-staged state

Baseline captured and re-verified identical after the branch transition and
after the commit:

- `.gitmodules` blob `4e0b9c4cb2d2c18737ecb16525383d2c1dd179de`
- `references/skillopt` `9c776fcb51ae681c046d6f619b55e5f337d4f900`
- `references/waza` `23cad910e93dd687f36f533da893c8552a4e76b6`
- `references/witr` `dc4fa1da82d3e266fcbd928641b4f30b3077c64f`

Stage committed with **explicit pathspecs only**, so these staged entries were
never swept into a Stage commit and remain staged for the operator.

## Follow-ups (not actioned)

1. **Backlog registry drift** — `.autoharness/backlog-registry.yaml` declares no
   `features.sizing` and its `update_task` params omit `size`/`complexity`, but
   backlogit v1.9.0 supports `--size`, `--size-source`, `--size-ruleset-version`
   and `--complexity`. Sizing was emitted using the tool's real capability.
   Recorded as review finding F16 (P3, ACCEPTED).
2. Installed autoharness CLI lacks `gate`; source-tree gate remains the path.

## Next action

Ship claims `142-S` and executes `133.001-T` then `133.002-T`.
