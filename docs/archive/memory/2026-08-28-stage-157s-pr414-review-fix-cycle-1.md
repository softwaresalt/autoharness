# Stage session — 157-S / PR #414 hosted review-fix cycle 1

**Date**: 2026-08-28
**Shipment**: `157-S` (S1), covering feature `149-F`
**Plan**: `docs/plans/2026-08-27-pre-review-detector-sdk-plan.md`
**Branch**: `chore/stage-156-S`
**Reviewed HEAD before changes**: `12f8c9743899b6177a1658b9bb9cff29611fb159`

## Cycle-budget note (important)

This is **cycle 1 against the `149-F` plan**. The prior "budget exhausted"
checkpoint (`checkpoint-20260828-080526.json`) refers to **`148-F` / `156-S`**,
a *different* plan with a *separate* 3-cycle budget. Do not conflate them.

## What was addressed

Four unresolved current-HEAD Copilot review threads on PR #414, all treated as
**in-scope same-contract-surface corrections**, none deferred. Every finding was
independently re-verified against source before disposition — all four were
correct, none speculative.

| Thread | Comment | Finding | Fix |
|---|---|---|---|
| `PRRT_kwDORzpWpM6dGx-N` | 3879074410 | Schema mirror / runtime resolution | **D-10** |
| `PRRT_kwDORzpWpM6dGx-1` | 3879074470 | Immutable report freshness deadlock | **D-11** |
| `PRRT_kwDORzpWpM6dGx_H` | 3879074497 | Contradictory outcome fields | **D-9** |
| `PRRT_kwDORzpWpM6dGx_a` | 3879074528 | Option-unsafe user Git refs | **D-12** |

## Source facts verified (do not re-litigate)

* `resolve_validation_gates_schema_path()` (`src/autoharness/schema_contracts.py:511-532`)
  returns the **versioned** `schemas/validation-gates/1.0.0.schema.json` first;
  the pointer is only a fallback. The versioned file **exists** in this repo.
* `test_validation_gates_schema.py::test_pointer_schema_mirrors_versioned_schema_except_id`
  asserts **full dict equality** after popping `$id`.
* `031-DL` D5 (deliberation line 648+) says the extension is **additional
  statuses**, i.e. a widened vocabulary on ONE field — not a second field.
* `CheckResult.status` is an unconstrained `str` (`gates/topology.py:130-142`);
  consumers branch on `.status` (e.g. `topology.py:180`).
* `discover_modified_files` builds `f"{base}...{head}"` with **no option
  terminator** (`gates/discovery.py:61`), and **never raises** (returns `[]`).

## New decisions

* **D-9** — one canonical `status` field; any `verdict` is a derived read-only
  property, not a field, absent from `to_dict()`. Contradiction unrepresentable.
* **D-10** — pointer + versioned schema are ONE atomic contract; detector
  validation cases run against the **versioned** document.
* **D-11** — epoch key is `<head_sha>-<fingerprint>`, fingerprint = SHA-256[:16]
  over canonical JSON (`sort_keys`, no whitespace, UTF-8) of registry version,
  schema version, and sorted resolved `tool_version_dims`. Freshness and
  identity become the same predicate.
* **D-12** — resolve user refs with
  `git rev-parse --verify --end-of-options <ref>^{commit}`, accept only
  `^[0-9a-f]{40}$`, reject with exit 2 and **no side effect**.

New invariants **INV-7/8/9**; new risks **RK10-RK13**.

## Task changes

11 tasks -> **15**. Three splits, all forced by the plan's own granularity
budget (max 3 files, max 4 test scenarios), not by added scope.

| ID | Unit | Change | Size | Complexity |
|---|---|---|---|---|
| `149.001-T` | U1 | canonical `status`; retitled | S | low |
| `149.002-T` | U2 | 1 -> 3 files (both schemas + contract test) | S -> **M** | low -> **medium** |
| `149.007-T` | U7 | epoch key + atomic write; retitled | S -> **M** | medium |
| `149.008-T` | U8 | wires resolver; exit 2 no-side-effect | S | low -> **medium** |
| `149.009-T` | U9 | + D-9 canonical-field assertions | S | low |
| `149.010-T` | U10 | narrowed to assembler; 2 files -> 1 | S | low |
| `149.012-T` | **U8b** | NEW — option-safe resolver (security) | S | medium |
| `149.013-T` | **U8c** | NEW — ref-safety tests | S | low |
| `149.014-T` | **U10b** | NEW — report shape/freshness tests | S | low |
| `149.015-T` | **U10c** | NEW — epoch determinism/concurrency tests | M | medium |

## Dependency changes

* Added: `149.004-T`, `149.008-T`, `149.013-T` -> `149.012-T`
* Added: `149.014-T`, `149.015-T` -> `149.007-T`
* **Removed**: `149.010-T` -> `149.007-T` (report tests moved out)
* `149.012-T` (U8b) has **no dependencies** — schedulable first, unblocks U4/U8.

## Preserved (verified, not assumed)

* `157-S -> 156-S (blocks)` edge intact; both shipments **queued and unclaimed**.
* `156-S` and all `148-*` artifacts **byte-unchanged** (`git status` clean for them).
* **Q1** derived-report persistence exception preserved exactly as approved —
  D-11 changes only the *key*, not shape/authority/read-back. S1 still ships
  **no read-back API**.
* **Derive-never-persist** for the graph itself untouched (INV-1, D-5).
* Q5/Q7 unchanged; S0 not waived.

## Gate outcome

Plan hardening re-run (mandatory: schema files, public CLI input, serialization
contract, persisted-report identity all changed). Plan review re-run:

* `dispatch_mode: single-agent-declared-degradation` (terminal)
* `decision: PASS` (terminal)

Round-0 markers explicitly annotated **SUPERSEDED** so terminal markers are
unambiguous.

## Next actor

**Ship, via Orchestrator — execute `156-S` FIRST.** `157-S` is not eligible
until `156-S` ships. Stage claimed nothing and invoked no Ship (P-010).

Working tree has **uncommitted** staging edits (13 modified + 8 new backlog
files + plan). Stage does not commit; the operator owns that decision. GitHub
threads remain **unreplied and unresolved** — reply only after the fix commit
is pushed.
