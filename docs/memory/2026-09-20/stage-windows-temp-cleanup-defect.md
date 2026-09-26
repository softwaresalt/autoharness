# Stage session — Windows temp-cleanup teardown defect staged as a separate P-021 unit (2026-09-20)

## Outcome

Captured, deliberated, and promoted the newly discovered Windows
temp-directory teardown defect as its **own** P-021 work unit, separate from
the fix cycle that discovered it. Captured the Graphtor shim `tearDown`
resource leak as a **related but deliberately uncombined** P2 follow-up that
stays in the stash.

* Stash (promoted): **`78548873`** — high / bug
* Stash (deferred P2 follow-up): **`8CB606F8`** — medium / bug, **not** harvested
* Deliberation: **`034-DL`**
* Decision: `docs/decisions/2026-09-20-windows-temp-cleanup-teardown-defect-deliberation.md`
* Covering feature: **`184-F`**
* Task: **`184.001-T`** (`size: S`, `size_source: agent`,
  `size_ruleset_version: 2h-rule-v1`, `complexity: medium`)
* Shipment: **`190-S`** (SHIP-24, priority high, manifest `[184-F, 184.001-T]`,
  verified by read-back; `size_composition` S×1, `unsized: 0`)

## The defect

After `622a41a1` (the authorized `183.001-T` test-only synchronization repair),
the canonical suite failed **twice** at
`tests/test_capability_pack_enforcement_verifier.py::CapabilityPackEnforcementVerifierTests::test_orphaned_manifest_entry_without_pack_fails`,
inside `tempfile.TemporaryDirectory.__exit__` → `shutil.rmtree`, with
`PermissionError [WinError 32]` / `[WinError 5]`. The failure is in **teardown,
not in an assertion** — the test body passes.

Mechanism: the module-level `_run()` helper (line ~114) wraps the whole fixture
build and the `verify_workspace()` call in a bare
`with tempfile.TemporaryDirectory() as temp_dir:`, and Windows refuses to remove
a tree while any handle inside it is still open.

A read-only concurrency review of `src/autoharness/verify_workspace.py`
(`capability_pack_enforcement` targeted check) found **no production
file-handle leak** — which both selects a test-only repair and prohibits
production mutation under this unit.

## Decision path

1. **P-021 C1 → OUT of scope.** The discovering cycle was authorized only to
   change one test function's readiness synchronization in a *different* module
   (`tests/test_graphtor_mcp_shim.py`). C1 worked discrimination (b): same PR,
   same suite, same gate are not scope tests. C4: no authorization — including
   explicit operator authorization — retroactively widens the discovering
   cycle; it can only open a *separate* unit through C2 → C6 → new scope.
2. **C2 capture-first**, before any planning: `78548873` and `8CB606F8`, each
   with the literal `DEFERRED SCOPE EXPANSION` token, expansion statement, C1
   rationale, per-field source refs, `requires deliberation: yes`, and
   provisional kind/priority.
3. **C6 deliberation** (`034-DL` + decision doc), five options considered.
4. **Harvest** to the minimum `184-F` / `184.001-T`, then shipment `190-S`.

**Selected repair:** bounded retry at the teardown site — catch
`PermissionError` with `winerror` 32 or 5, retry a small fixed number of times
with short bounded backoff, **final re-raise**. `ignore_cleanup_errors` /
`ignore_errors` explicitly **rejected**: they make a persistent handle leak
indistinguishable from a healthy run and permanently hide the `WinError 5`
access-denied case. (That anti-pattern already exists in the shim test's
`tearDown` and is itself part of `8CB606F8`.)

## Verification order recorded on the task (Ship executes, in order)

1. the exact test;
2. cross-test sequence with the Graphtor module in a single process, both
   orderings;
3. no lingering relevant child processes or temp directories;
4. canonical suite `PYTHONPATH=src python -m unittest discover -s tests`.

**Stop condition:** if (2) or (3) shows lingering processes/dirs, the true cause
is likely `8CB606F8` — do **not** raise the retry bound to mask it and do **not**
fix `8CB606F8` here; return to Stage. If a correctly bounded retry still fails
deterministically, the test-only diagnosis is disproved — stop, do not edit
`src/`.

## Why the two defects stay separate

`8CB606F8` (shim `tearDown`: cleanup gated on `poll() is None` so exited
children are never reaped or their pipes closed; only `stdin` closed on the live
path; no `wait()` after `kill()`; `_start_reader` pump thread never joined;
`rmtree(ignore_errors=True)`) is a **plausible but unproven** contributing
cause. Merging it into the cleanup task would widen a bounded test-only repair
*and* destroy the ability to distinguish a test-local teardown race from
cross-module handle pollution — which is exactly what verification step 2
measures. Operator-directed separation, recorded on both entries.

`AD0F128D` (`.autoharness/staging/tmp/` fixture accumulation from
`test_shipment_closure_classification.py`) was examined and rejected as a
duplicate: different module, different mechanism (no cleanup at all vs. cleanup
that raises), different remedy.

## Gates

* **P-006 hardening: NOT REQUIRED.** Blast radius is one test module, teardown
  path only — no schema, no CLI distribution, no template family, no
  production code. Recorded on the decision, not skipped silently.
* **No gate bypassed.** Plan depth is lightweight by operator direction and
  proportionate; plan content (scope, prohibitions, verification order, stop
  condition) is carried inline on `034-DL` and `184.001-T` rather than in a
  separate `impl-plan` artifact. `force_harvest_no_gates` was neither required
  nor used.

## Sequencing (no dependency edge added)

`190-S` was deliberately **not** wired to `189-S`. A `blocks` edge would have to
run `190-S` → `189-S`, since `189-S`'s verification order ends in the canonical
suite — the gate this defect breaks; the reverse edge would deadlock the pair.
Rather than mutate the peer's in-flight `189-S` record, the ordering is recorded
in the decision and the handoff: **`190-S` lands first**, then `189-S`'s
canonical-suite gate can pass, then PR #457 Push B.

## Session mode notes

* `DEGRADED_MODE`. backlogit MCP healthy; `backlogit_stash_archive` not exposed
  by this server build → canonical non-destructive CLI fallback
  `backlogit stash archive` recorded and used (`TOOL_DEGRADED`).
* `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE` — no tools
  exposed; file-based exploration throughout. Same as the prior session.
* `INDEX_SYNC_OK` (1447 indexed). Checkpoint enumeration clean: 66 stage-owned
  records, 0 active, 0 quarantined, 0 anomalies → zero-candidate normal startup.
* Duplicate scan (unconditional) over 116 active entries: **clean**.
  Late-identifier reconciliation (triggered by `review-thread=N/A`): **no late
  identifier found**, `N/A` stands as a truthful terminal record — a no-op
  completion, not a C3/C6 shortfall.
* Learnings retrieval: **confidence low**, no directly applicable compound
  entry. `docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md`
  (~line 829) records a prior unscoped-suite sighting of this same
  `[WinError 32]` in `shutil.rmtree` — a recurring, previously unowned defect.
* File locks acquired and released around the two Stage artifacts written this
  session (peer agent holds uncommitted work on this branch).
* Commit scoped with `git commit --only` to Stage artifacts alone. The peer's
  10 uncommitted files (5 `.backlogit/queue/*.md`, 5 `docs/plans/*.md`),
  source/tests/scripts, pre-existing untracked portfolio memory files, the PR
  body, and GitHub were all untouched. No push, no shipment claim.

## Next step (Ship)

Claim shipment **`190-S`**, execute **`184.001-T`** test-only against the
recorded verification order, then unblock `189-S`'s canonical-suite gate and
PR #457 Push B. `8CB606F8` remains in the stash for a future Stage session.
