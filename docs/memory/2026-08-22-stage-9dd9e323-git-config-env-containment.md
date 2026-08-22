---
title: "Stage Session: 9DD9E323 — Ambient GIT_CONFIG_* Environment Destruction Containment"
date: 2026-08-22
agent: stage
session_id: stage-2026-08-22-9dd9e323-git-config-env-containment
route: claude-opus-5 / anthropic / high
source_stash: 9DD9E323
features: [144-F, 145-F]
shipments: [152-S, 153-S]
source: docs/memory/2026-08-22-stage-9dd9e323-git-config-env-containment.md
doc_type: memory
---

# Stage Session Memory — `9DD9E323`

## Handoff to Ship (authoritative)

**Claim `152-S` first. `153-S` is blocked by `152-S` and must not be claimed until `152-S` closes.**

| Shipment | Status | Priority | Items | Ready |
| --- | --- | --- | --- | --- |
| `152-S` | queued | high | 8 (`144-F` + `144.001-T`..`144.007-T`) | **YES — claimable** |
| `153-S` | queued | high | 3 (`145-F` + `145.001-T`, `145.002-T`) | no — blocks on `152-S` |

First unblocked task: **`144.001-T`** (no forward dependencies; `144.002-T` depends on it).

## What this session did

Full Stage stash-to-backlog cycle over explicitly-selected active stash entry
`9DD9E323`, the unresolved residual of operator-selected bug `E8158860`.

* **Startup.** `TOOL_OK: backlogit` (MCP + CLI). `INDEX_SYNC_OK` (942 items).
  Zero active `stage`-owned checkpoints, zero quarantined, no validation
  anomalies -> normal startup, no recovery. No queued or active shipments.
  `main` clean at `bc6c387a`, one worktree.
  `ENGRAM_DEGRADED` per operator directive (same-operation circuit open from
  repeated Ready failures); Engram was **not** retried and no raw
  unified/graph/code-dependency scan was substituted. Only exact known-path
  reads and literal-text searches were used.
* **Triage.** `DEFERRED SCOPE EXPANSION` marker present -> P-021 C6 forced the
  deliberate route; Step 3 planning was unreachable until the deliberation
  artifact existed.
* **Duplicate detection (P-021 C5, unconditional).** CLEAN over 14 active + 176
  archived entries (backlogit `stash_entries` SQL scan plus a direct literal
  scan of `.backlogit/archive/stash.jsonl`). Exactly one ancestor match —
  `E8158860`, archived and already harvested into `141-F`/`149-S` and
  `143-F`/`151-S`. No duplicate merge required; no entry archived as a duplicate.
  Recorded explicitly as a clean scan.
* **Late-identifier reconciliation (P-021 C6).** Triggered (two `N/A` source-ref
  fields). PR reconciled `N/A -> #393` from
  `docs/closure/151-S-143-F-post-merge-closure.md` (`feature_pr: 393`, merge
  `f389fd59`, merged `2026-08-22T04:48:54Z`). Review-thread ID: **no result**,
  `N/A` stands truthfully — PR #393's two Copilot threads were about `{!r}`
  formatting, not this residual. Task/feature/shipment IDs already concrete;
  no overwrite (idempotence preserved). Priority re-prioritized medium -> high
  under Stage's own stash authority; no Ship write requested.
* **Deliberation, plan, P-006 hardening, plan review (PASS), harvest,
  two ordered shipments, stash archived.**

## The finding that closed the diagnosis

`141-F` returned `VERDICT: INCONCLUSIVE` and `143-F` returned `R3-still-red`
because both searched for code that *names* `GIT_CONFIG_*`. There is none — and
none is needed.

`unittest.mock.patch.dict('os.environ', ...)` restores by **clear-then-update**
(`_unpatch_dict` -> `_clear_dict(in_dict)` then `in_dict.update(original)`),
**regardless of the `clear=` argument**. For `os.environ` that is `unsetenv` for
every key then `putenv` for every key. On Windows, `putenv` of an empty value
reaches `SetEnvironmentVariableW(name, L"")`, which **deletes** the variable
from the true Win32 process environment block. CPython's `os.environ` keeps its
own dict entry showing `''`, so the destruction is invisible from Python.

Ambient `GIT_CONFIG_COUNT=3` with `KEY_2=core.fsmonitor` / `VALUE_2=(empty)`
therefore becomes `COUNT=3` + `KEY_2` with **no** `VALUE_2` after the first
`patch.dict` block exits. Child git (`env=None` -> `lpEnvironment=NULL`)
inherits the real block and dies with the captured
`error: missing config value GIT_CONFIG_VALUE_2`.

Direct literal scan found 13 such sites: `tests/test_gates_topology.py` lines
1004/1023/1045/1069/1090/1112/1141/1173/1207/1236/1266,
`tests/test_gate_dag_readiness_cli.py:217`,
`tests/test_gate_pipeline_topology_cli.py:273`.

Two seams then convert the broken child environment into the observed failures,
one of them silently: `src/autoharness/gates/topology.py:200` `_run_git` uses
`check=False` and returns `""`, laundering a git infrastructure failure into
`detached_head` -> `BRANCH_MISMATCH` -> `exit_code == 1`; and
`tests/test_telemetry_gitignore_template.py:33` asserts `returncode == 0` with
the message `"is not gitignored"`, reporting a gitignore defect that does not
exist.

## Mechanism separation (operator directive, honoured)

Kept strictly separate in two features and two ordered shipments. The
deliberation **does** record a falsifiable prediction that mechanism B is a
symptom of mechanism A (`BranchOwnershipTests` sorts before
`FilesystemTopologyReadersTests`; all five named polluters are `patch.dict`
sites; victim #2 reaches git through `_run_git`'s silent swallow) — but the
prediction is never used to close anything. `145.001-T` must measure it, and
hardening **A10** requires a reverted-checkout **negative control** before
`SUBSUMED` may be recorded; without it the disposition is
`INCONCLUSIVE-VACUOUS` and `145.002-T` proceeds as if `SURVIVES`.

## Design decision (deliberation option R9)

Restore-by-diff at the environment-mutation seam, with defense in depth.
Rejected: accept-permanent-red (R1), clear all `GIT_CONFIG_*` (R2),
`GIT_CONFIG_COUNT=0` (R3), mutate global/system git config (R4), skip/xfail the
victims (R5), scrub in `ci.yml` (R6), fix only `src/` seams (R7),
`tests/__init__.py` bootstrap (R8).

R2/R3 were rejected specifically because they violate the operator constraint
against indiscriminately clearing legitimate injections: `safe.bareRepository=explicit`
and `credential.interactive=never` are protective settings. Layer 1 satisfies
that constraint *perfectly* rather than approximately — it touches no
`GIT_CONFIG_*` variable at all; it simply stops corrupting them.

## Artifacts

| Kind | Path |
| --- | --- |
| Deliberation | `docs/decisions/2026-08-22-ambient-git-config-env-destruction-containment-deliberation.md` |
| Plan | `docs/plans/2026-08-22-git-config-env-containment-plan.md` |
| Hardening (P-006) | `docs/plans/2026-08-22-git-config-env-containment-hardening.md` |
| Review (PASS) | `docs/reviews/2026-08-22-git-config-env-containment-review.md` |
| Memory | this file |

## Binding amendments Ship must honour

Hardening **A1–A10** and review **R1–R9**. Highest-consequence ones:

* **A2/R6** — `144.001-T` is **RED by design on Windows**. Its gate is
  **failure-set equality** against an enumerated list, not `failures == 0`. The
  expected-red window is exactly one task wide. It must never be closed by
  `skipTest`, `expectedFailure`, deletion, or assertion weakening.
* **R3** — canonical Windows invocation is
  `$env:PYTHONPATH = 'src'; python -m unittest discover -s tests`.
  **`pytest` MUST NOT be substituted** for any measurement — it changes
  collection order and would silently invalidate every order-dependence result.
* **A6 (AIG-1..AIG-4)** — mechanical AST assertion-inventory equality with
  per-line citation. Exactly one authorized assertion-argument divergence in the
  whole feature (`144.006-T` part 2's message).
* **A1/R4** — flat `tests/_env_patch.py` and `tests/_git_env.py`. **No**
  `tests/__init__.py`, **no** `tests/conftest.py`, **no** `tests/support/` package.
* **A4/A5** — the helper fails loud (uniform `ValueError` on `""` overrides;
  entry-time `RuntimeError` on an empty prior value) rather than reintroducing
  the defect through its own restore path.
* **A7** — normalizer touches only the exact `GIT_CONFIG_{COUNT,KEY_n,VALUE_n}`
  triple; `GIT_CONFIG_PARAMETERS`/`GLOBAL`/`SYSTEM`/`NOSYSTEM` pass through.
* **A9** — named skip-**set** subset check, not a bare count bound (baseline 20).
* **R7** — `145.002-T` returns blocked for Stage re-decomposition rather than
  expanding past the 2-hour rule.

## Verification performed

* Manifests read back: `152-S` = 8 items, `153-S` = 3 items, `unsized: 0` on both.
* Covering-feature projection correct on both shipments.
* All 9 tasks carry both `size` and `complexity` (three-call registry sequence:
  create -> size + `size_source: agent` + `size_ruleset_version: 2h-rule-v1` -> complexity).
* 9 task dependency edges + `153-S` -> `152-S` shipment edge; graph acyclic.
* `backlogit queue view --type shipment` returns **`152-S` alone**.
* `144.001-T` has zero forward dependencies -> first unblocked task.
* `backlogit doctor`: 62 findings, **all pre-existing**, **zero** touching
  `144-F`/`145-F`/`144.00*`/`145.00*`/`152-S`/`153-S`/`9DD9E323`.
* Stash archived non-destructively via `backlogit stash archive`: active 14 -> 13,
  archive 176 -> 177; entry absent from active, present in archive at 12137 chars
  with all forward refs intact.
* Index synced at session start and at session end.

## Role boundary

Stage made **no** source/test/template/config edit, ran **no** build/test/linter,
created **no** branch/commit/push/PR/worktree, and claimed **no** shipment.
All Stage mutations (`.backlogit/**`, `docs/decisions/`, `docs/plans/`,
`docs/reviews/`, `docs/memory/`) are left **uncommitted** for Orchestrator
publication.

The two `.mcp.json` preservation git-stashes from the prior Ship sequence were
**not** inspected, applied, dropped, or modified.

## Blockers

None. `152-S` is ready to claim.

**Watch item for Ship:** if `144.001-T`'s reproduction does **not** go red on
Windows, the mechanism is unconfirmed — the task's mandatory halt condition
fires, the shipment returns blocked, and the design returns to Stage for
re-deliberation. Do not proceed to `144.002-T` on an unconfirmed hypothesis.
