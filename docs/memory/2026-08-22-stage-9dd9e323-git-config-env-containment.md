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

**Current binding set (A12/R13 — explicit enumeration, never an open range):**

* Hardening BINDING: `A1`, `A1R`, `A2R`, `A3R`, `A4`, `A5`, `A6`, `A7`, `A7R`,
  `A8R`, `A9`, `A9R`, `A10`, `A11`, `A12`
* Review BINDING: `R1`, `R2`, `R3`, `R4`, `R5R`, `R6`, `R7`, `R8`, `R9`, `R10`,
  `R11R`, `R12`, `R13`
* **WITHDRAWN — do NOT act on:** `A2` (→ A2R), `A8` (→ A8R, unsound),
  `R5` (→ R5R), `A3` nonzero-exit clause (→ A3R), `A7` property 2 (→ A7R),
  `R11` (→ R11R, impossible as written)

An open range like "A1–A10" cannot express withdrawals and silently
re-authorizes superseded text — that is exactly the defect cycle 3 finding 5
caught in this very section.

Highest-consequence amendments:

* **A7R** — the normalizer's drop rule is **symmetric**: drop pair `n` iff
  `KEY_n` **or** `VALUE_n` is absent. The old asymmetric wording contradicted
  the task's own deliverable and would have emitted a `VALUE_n` with no
  matching `KEY_n` — the same malformed triple in mirror image. Present-but-
  empty is **kept**; empty is not absent.
* **A3R** — `_run_git` takes `expected_absence_codes`. `symbolic-ref --quiet`
  exit **1** is an *expected absence* (the designed way to ask whether
  `origin/HEAD` exists), not an invocation failure. Without this the diagnostic
  would fire on every ordinary run — and, because `--quiet` suppresses stderr,
  fire with an empty string. Never populate the key with `""`; record the exit
  code instead.
* **A9R + R11R** — R11's demand that the in-process skipped **set** equal proof
  1's was impossible: `python -m unittest discover -s tests` emits counts only.
  R11R compares counts; A9R sources the **named** set from
  `prog.result.skipped` (post) and `... -v` (baseline).

* **A2R/R6** — `144.001-T` is **RED by design on Windows**. Its gate is
  **failure-set equality** against an enumerated list (expected-RED **and**
  expected-GREEN), not `failures == 0`. The expected-red window is exactly one
  task wide. It must never be closed by `skipTest`, `expectedFailure`,
  deletion, or assertion weakening.
* **A11 + R10** — the reproduction uses an **L0/L1/L2 process topology**. The
  blank sentinel is established **only** via an explicit environment block
  handed to a child process and its arrival is **verified** before the round
  trip; `os.environ[name] = ""` is *itself* the destructive operation and can
  never seed it. All destructive operations are confined to the **L1 child** —
  the L0 test process must not become a fourteenth polluting site.
* **A8R + R11** — the original A8 environment-restoration proof is
  **WITHDRAWN AS UNSOUND**: three probes spawned as siblings of the runner
  could never observe the runner's mutations, so `before == after` was
  trivially true on every platform. A8R runs the suite **in-process** inside an
  L1 controller whose **own children** are the probes, with a precondition
  gate, a mandatory negative control, and an R11 count-equivalence check
  against the canonical subprocess gate.
* **A1R + R5R + R12** — `ENV_MUTATION_ALLOWLIST` is **EMPTY**. There is **no**
  path exemption for `tests/_env_patch.py`: targeted set/delete is not a
  forbidden form, and an exemption would legalise the destructive forms in the
  one file most likely to reintroduce them. A negative non-vacuity case proving
  `os.environ[k] = v` / `del os.environ[k]` are not flagged is mandatory.
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

## Cycle 2 — PR #397 review-fix (2026-08-22, head `72bfdd9c`)

Three hosted Copilot threads, all **P-021 C1 same-contract-surface** corrections,
fixed in place. **Contract text only — no backlog item created, deleted,
re-parented, or re-sequenced; manifests and dependencies unchanged.**

| Thread | Carrier | Severity | Resolution |
| --- | --- | --- | --- |
| `PRRT_kwDORzpWpM6bXqlM` | `144.001-T` | **P0** | A11 + R10 — reproduction could not establish its own precondition; `os.environ[name] = ""` deletes the sentinel *before* the round trip, so the test would have confirmed the mechanism on non-evidence (false positive). Duplicate at line 41 (in-process `GIT_CONFIG_*` triple) fixed identically. |
| `PRRT_kwDORzpWpM6bXqlR` | `144.007-T` | **P0** | A8R + R11 — A8's sibling shell probes could never observe the runner's mutations; `before == after` was trivially true and would have reported PASS against un-fixed code. |
| `PRRT_kwDORzpWpM6bXqlV` | `144.004-T` | P1 | A1R + R5R + R12 — path-exempting `_env_patch.py` would legalise the destructive forms in the very file that exists to avoid them. Allowlist is now EMPTY. |

Both P0s share a root cause worth remembering: **a verification mechanism was
specified at the level of intent without tracing the process topology it would
actually execute in.** Each would have produced a *false PASS*, which is worse
than a red gate because it manufactures unwarranted confidence. A8R and A11 now
state process levels (L0/L1/L2) explicitly so the topology is reviewable rather
than implied.

Three further findings were raised while fixing them: **N1** (P1) — A11's new
`INVALID_PRECONDITION` outcome would have been swallowed by the failure-set
equality gate, so the precondition became its own expected-GREEN test (A2R);
**N2** (P2) — the in-process controller needs `PYTHONPATH` in the explicit block
and must read counts from `prog.result`, not by scraping stderr; **N3** (P2) —
A9's skip enumeration is unaffected by the topology change.

Re-gate: plan/hardening/review **PASS**, 0 unresolved P0/P1, cycle 2 of 3.

## Cycle 3 — PR #397 review-fix (2026-08-22, head `374672c8`) — FINAL PERMITTED CYCLE

Six hosted Copilot findings. **All six classified P-021 C1 PASS; zero required
C2 capture.** Contract text only — manifests, dependencies and claimability
unchanged for the third consecutive cycle.

| # | Thread | Carrier | Resolution |
| --- | --- | --- | --- |
| 1 | `PRRT_kwDORzpWpM6bXxuS` | `144.005-T:62` | **A7R** — drop rule made symmetric. The task's deliverable ("both present are kept") contradicted its own property 2 ("only `VALUE_n` absence drops"); following property 2 would emit a `VALUE_n` with no matching `KEY_n` — the same malformed triple in mirror image. Property 2 was written from the `9DD9E323` capture (value side) instead of git's two-sided rule. |
| 2 | `PRRT_kwDORzpWpM6bXxuh` | `144.006-T:45` | **A3R** — `expected_absence_codes`. `symbolic-ref --quiet` exit 1 is the *designed* existence probe for `origin/HEAD`, not a failure; A3 would have fired the diagnostic on every ordinary run, and — since `--quiet` suppresses stderr — fired it with an empty string. |
| 3 | `PRRT_kwDORzpWpM6bXxur` | `144.007-T:82` | **R11R + A9R** — R11's named-set comparison was *impossible* (proof 1 emits counts only). R11R compares counts; A9R sources the named set from `prog.result.skipped` and `... -v`. Also closed a latent gap: A9 had never specified a source at all. |
| 4–6 | `...Xxu2` / `...Xxu7` / `...Xxu-` | `144-F:33`, memory `:131`, `memories.json` | **A12 + R13** — the three carriers Ship reads *first* still asserted the cycle-1 set. An open range cannot express a withdrawal, so "A1-A10" silently re-authorized the unsound A8. All three now enumerate binding **and** withdrawn IDs explicitly. |

The recurring lesson across cycles 2 and 3: **a contract clause written from a
single captured instance generalises wrongly.** A8 generalised "probe the
environment" without tracing process topology; A7 property 2 and A3's
nonzero-exit rule both generalised from one observed symptom. A7R, A3R and A8R
now state the rule and the counter-cases, not the instance.

**Cycle budget exhausted.** Any further finding must be captured as a deferred
entry under P-021 C2, not fixed in a fourth cycle.


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
