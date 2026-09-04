---
title: "Stage session — minimal Copilot plugin payload staging (E9E5E6CC)"
date: 2026-09-03
doc_type: memory
agent: stage
route: "claude-opus-5 / anthropic / high"
branch: chore/stage-159-167-publication
shipment: 168-S
---

# Stage session — 2026-09-03

## Outcome

Staged stash `E9E5E6CC` end-to-end into shipment **`168-S`** (SHIP-10), inserted
deterministically between `166-S` and `167-S`. No Git operations performed;
Orchestrator publishes.

## Capability status

`ALL_TOOLS_OK` for backlogit (MCP + CLI). Three declared degradations, all
non-halting with sanctioned file-based fallbacks:

* `ENGRAM_DEGRADED` — no `unified_search`/`impact_analysis` surface
* `GRAPHTOR_UNAVAILABLE` — no doc-index surface
* `INTERCOM_DEGRADED` — no broadcast surface; operator visibility reduced
* `TOOL_DEGRADED: reviewer-subagent-dispatch` — plan review ran inline with full
  persona coverage (`dispatch_mode: single-agent-declared-degradation`)

Startup recovery: 21 checkpoints enumerated unfiltered, all `stage`-owned and
`resolved`, zero quarantine/validation anomalies → zero-candidate normal startup.

## Key evidence established

* `.github/plugin/marketplace.json` declares `source: "."` → the **entire repo**
  (3,238 tracked files / ~18 MB) is the plugin payload.
* `.backlogit/` = 2,110 files (**65% of all tracked files**), zero runtime role.
* `pyproject.toml` force-includes all 642 `docs/` files (6.9 MB) into every wheel;
  only 21 are user-facing guides.
* **Proof the docs force-include is dead weight:** `verify_workspace.py` resolves
  every `docs/*` path against `workspace_path` (target workspace), never the
  packaged data dir (lines 1949, 1976, 2892-2912). `cli.py:14-21` `_DATA_DIR`
  serves only templates/schemas.
* **"Referenced ≠ required payload":** 77 skill references to
  `docs/compound|plans|memory|decisions|closure` are target-workspace *output
  destinations*, not engine payload. A naive dependency scan misreads these.
* Zero packaging tests existed (`tests/` scan for `packag|plugin|dist|wheel|install`
  returned nothing).

## Decisions

* **Allowlist manifest** (Option 2) over denylist (fails open), repo split
  (complexity), or wheel-only fix (leaves the `.backlogit` disclosure).
* **Hardening H1:** manifest is source of truth; `pyproject.toml` include table is
  *generated and asserted equal by test* rather than read by a custom hatchling
  build hook — avoids adding a failure mode to the release pipeline.
* **Placement:** between `166-S` and `167-S`. Reliability/security work
  (`159-S`–`166-S`) supersedes this packaging refactor; this refactor supersedes
  `167-S` (documentation/record hygiene).

## Plan review — PASS (2 of 3 cycles)

Six P0/P1 findings, all remediated in the plan before harvest:

| ID | Finding | Remediation |
|---|---|---|
| P0-1 | Plugin-channel trimming mechanism unverified | Blocking spike `160.002-T` with branch (a)/(b) |
| P1-2 | Task order violated Test-First (Constitution II) | Composition tests moved before wiring |
| P1-3 | Gate 4 cross-refs not asserted on built payload | AC9 + test |
| P1-4 | Plan contradicted its own AC2 (~12 unclassified paths) | AC11 disposition table |
| P1-5 | `{{AUTOHARNESS_VERSION}}` resolution unprotected | AC10 + no-CLI install test |
| P1-6 | Build logic shipped inside runtime payload | Relocated to `build_support/` |

P2-7 (loader error handling), P2-8 (forward-only disclosure), P2-9 (compound
learning) recorded as follow-ups on `160.004-T` / `160.011-T`.

## Traps carried into the backlog

* **`core-metadata-version = "2.4"` pins are NON-NEGOTIABLE** on both wheel and
  sdist. hatchling 1.32.0 defaults to Metadata-Version 2.5, which the SHA-pinned
  publish action's twine < 7.0.0 rejects. Local `twine check` **cannot** reproduce
  the failure. (`docs/compound/2026-08-30-unpinned-hatchling-...md`)
* `start.ps1`/`start.sh` look like engine files but are *generated dogfood output* —
  shipping them would violate the plan's own AC5.
* New schema only; no in-place schema mutation (three prior occurrences recorded).

## Next steps

1. Orchestrator publishes staging artifacts (Stage performed no Git operations).
2. Ship executes `159-S` first; `168-S` unblocks only after `166-S` completes.
3. Within `168-S`, spike `160.002-T` gates `160.007-T`.
