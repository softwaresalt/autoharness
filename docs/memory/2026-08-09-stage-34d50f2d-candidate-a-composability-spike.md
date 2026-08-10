# Stage session memory — 2026-08-09 — 34D50F2D candidate (a) composability spike

* **Agent / route**: Stage — `claude-opus-5` / `anthropic` / `high`
* **Mode**: normal (non-dark) Stage research, read-only
* **Base**: `main` = `origin/main` = `6dbdde67a8932b0765af4af664f2d92c318a6ccc`
* **Stash**: `34D50F2D`, candidate **(a)** only — entry remains **ACTIVE**

## What was done

Executed a bounded Stage-owned research spike for stash `34D50F2D` candidate
(a) — the unified CLI/MCP/library composability question — and produced a durable
findings/decision artifact. No implementation work was performed or authorized.

## Pipeline steps

| Step | Outcome |
|---|---|
| 0.0 Tool availability gate | `TOOL_OK: backlogit` (v1.8.0; sizing/shipments/checkpoints/sql available). `ALL_TOOLS_OK` |
| 0.1 Index sync | `INDEX_SYNC_OK` — 746 indexed |
| 0 Session start / recovery | Checkpoints: 23 total, **0 quarantined, 0 active**, no validation anomalies → zero-candidate normal startup, **no recovery needed** (not a failure) |
| 1 Triage | Single operator-specified target: `34D50F2D` candidate (a) |
| 1.5 Grouping | Skipped — single feature-shaped target |
| 1.8 Learnings | Prior spike patterns `001-SP` / `002-SP` and `docs/decisions/` reviewed as templates |
| 2 Route | **Spike** (investigation) — executed |
| 3 Planning | **Not entered** — research-only session by operator instruction |
| 4 Harvest | **Not entered** — no implementation tasks created |
| 5 Shipment assembly | **Not applicable** — no harvested items; guardrail correctly prevented an empty shipment |
| 5.6 Stash archive | **Not applicable** — `34D50F2D` deliberately kept ACTIVE (candidate (c) outstanding) |
| 6 Continuity | This memo + end-of-session index sync |

## Result

* **Classification**: **PARTIAL GAP**
* **Verdict**: **CONDITIONAL PROCEED** (confidence medium-high)
* **Condition**: (a) must be scoped as *consolidation of existing logic*. If spec
  §3 is wanted literally (runtime action/observation executor, sequential
  pipelining, stderr-to-model routing) the verdict is **NO-GO** — that is
  agent-runtime territory, not autoharness.

### Headline findings

1. The **CLI is the only real surface**; autoharness exposes **no MCP server of
   its own** (MCP strings in `src/` are backlog-registry *validation* codes for
   external tools).
2. The **Python library surface is nominal** — zero consumers outside `src/` and
   `tests/`, no `__all__`, no declared public API.
3. **Policy is leaked into the CLI adapter**: verdict mutation on `--force`,
   audit-log authorship, the only `ToolTelemetryEvent` construction site,
   verify pass/fail definition, telemetry payload semantics, and a
   **CLI-exclusive `degraded` gate outcome**.
4. **Largest genuine duplication is prose-vs-code**: template-variable derivation
   is specified in the `install-harness` SKILL.md table *and* independently
   re-implemented in `verify_workspace.py`, with nothing forcing agreement.
5. **The core is already dependency-injected and well tested** — the gap is not
   testability, it is that policy sits above the core.
6. **`setup-*` has no core module at all** (~250 lines, 100% single-surface).

### Candidate (c) dependency verdict

**(c) benefits from (a) but does not depend on it.** (c) already has both
substrates (Python telemetry/log parsing; prose-side compaction incl. shipped
prune-on-restore). Keep the operator's (a)→(c) sequence, but **do not declare a
blocking dependency**.

## Operator decisions persisted

All four operator decisions (sequencing, Engram read-only/no-authority,
config-over-spec model routing, composability intent) were appended to
`34D50F2D` via `backlogit stash edit`. Notably this **closes the long-standing
"spec model-pick reconciliation" open question** on that tracker — resolved in
favor of `.autoharness/config.yaml`, requiring **no backlog work**.

## Boundary held

No source, template, schema, or config mutated. No implementation feature, task,
or shipment created. No branch, worktree, commit, push, or PR. No Ship work. No
spike/research worktree created — the P-016 Stage exception was **not**
exercised. External sidecars (`backlogit`, Engram, `graphtor`) read-only.

## Next steps

1. **Orchestrator**: publish the uncommitted artifact set below.
2. **Operator**: confirm the CONDITIONAL PROCEED condition (consolidation-only
   scope, non-goals accepted) before any `impl-plan` for (a).
3. If proceeding: `impl-plan` → **`plan-harden` is REQUIRED (P-006)**, elevated
   blast radius (CLI distribution + multiple template families) → `plan-review`
   → `harvest` over proposed T1–T8.
4. Candidate **(c)** remains DEFERRED, needing its own
   spike → impl-plan → plan-review → harvest.

## Artifacts changed (uncommitted)

* `.backlogit/queue/004-SP.md` — new spike artifact (status `done`)
* `.backlogit/stash.jsonl` — `34D50F2D` appended, still ACTIVE
* `docs/decisions/2026-08-09-composability-single-source-of-truth-spike.md` — new
* `docs/memory/2026-08-09-stage-34d50f2d-candidate-a-composability-spike.md` — this file
