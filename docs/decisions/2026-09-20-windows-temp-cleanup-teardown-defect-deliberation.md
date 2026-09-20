---
title: "Windows temp-directory teardown failure in the capability-pack enforcement verifier test: a test-only bounded-retry repair, staged as a separate P-021 work unit"
description: "Stage deliberation over deferred-scope-expansion stash entry 78548873. After the authorized test-only synchronization repair 183.001-T landed as 622a41a1, the canonical suite failed twice at tests/test_capability_pack_enforcement_verifier.py::CapabilityPackEnforcementVerifierTests::test_orphaned_manifest_entry_without_pack_fails inside tempfile.TemporaryDirectory.__exit__ with PermissionError [WinError 32] / [WinError 5] -- in teardown, not in an assertion. A read-only concurrency review found no production verifier file-handle leak, which selects a test-only repair: a bounded retry on PermissionError with winerror 32 or 5, ending in a final re-raise, with ignore-cleanup-errors explicitly rejected. Promotes the decision to a minimum separate work unit (184-F / 184.001-T / 190-S). The separate Graphtor shim tearDown resource leak is captured as stash 8CB606F8 and deliberately NOT combined into this repair."
doc_type: decision
source: docs/decisions/2026-09-20-windows-temp-cleanup-teardown-defect-deliberation.md
date: 2026-09-20
status: decided
decision_status: decided
depth: lightweight
deciders: operator, Stage
promoted_to: 184-F
promoted_to_note: "Promoted to the queue as covering feature 184-F with single task 184.001-T, assembled into shipment 190-S (SHIP-24). The work unit is deliberately minimum: one helper function, one test file, test-only."
branch: chore/stage-176-s-workflow-defects
head_at_decision: c128812b
deliberation_id: 034-DL
stash_sources:
  promoted: 78548873
  deferred_followup: 8CB606F8
  related_not_duplicate: AD0F128D
discovered_after: 622a41a1
unblocks: "PR #457 Push B canonical-suite verification gate"
scope: test-only
production_change_authorized: false
plan_hardening_required: false
policies: [P-021, P-006, P-005, P-010, P-012, P-016, P-001]
---

# Windows temp-directory teardown defect — test-only bounded-retry repair

## Question

After `622a41a1` (the authorized test-only synchronization repair for
`183.001-T`), the canonical suite failed **twice** at a completely different
test. Is that failure in scope for the fix cycle that discovered it, what is
its cause, and what exactly may the repair touch?

## The failure

| | Observation |
|---|---|
| Test | `tests/test_capability_pack_enforcement_verifier.py::CapabilityPackEnforcementVerifierTests::test_orphaned_manifest_entry_without_pack_fails` |
| Command | `PYTHONPATH=src python -m unittest discover -s tests` |
| Occurrences | 2 (both after `622a41a1`) |
| Failure site | `tempfile.TemporaryDirectory.__exit__` → `shutil.rmtree` |
| Errors | `PermissionError [WinError 32]` (file in use by another process), `PermissionError [WinError 5]` (access denied) |
| Assertions | **All passing.** The test body succeeds; only the context manager's teardown raises. |

The mechanism is ordinary Windows semantics. The module-level `_run()` helper
(line ~114) wraps the entire fixture build *and* the `verify_workspace()` call
in a bare `with tempfile.TemporaryDirectory() as temp_dir:`. Windows refuses to
remove a directory tree while any handle to a file inside it remains open, and
handle release after close is not instantaneous — antivirus scanning, the search
indexer, and delayed-close semantics all widen that window. `shutil.rmtree`
raises rather than waiting.

## Scope classification (P-021 C1) — OUT of scope

The discovering cycle's authorized change was `183.001-T`: replace a fixed
`time.sleep(0.3)` with deterministic child-stdin-close synchronization in
**`tests/test_graphtor_mcp_shim.py`**. This failure is in a different module,
in a different mechanism, on a different contract surface.

C1's worked discrimination **(b)** governs directly: "same file, same function,
same PR, same subsystem, related" are *not* scope tests. Here not even the file
matches — only the suite and the verification gate do. Genuine ambiguity
resolves **out** of scope (fail-safe default).

C4 closes the remaining door: no authorization, *including explicit operator
authorization*, retroactively widens the cycle that discovered an expansion.
What the operator's authorization does do — and did do here — is open a
**separate** work unit through the normal intake path: C2 capture → C6
deliberation → new approved scope. Fixing this inside `183.001-T` would have
been a **C7 violation**.

## Root-cause discrimination

Two candidates were distinguished before choosing a repair:

**(A) A production file-handle leak** — `src/autoharness/verify_workspace.py`
leaving a manifest, config, or instruction reader open past the targeted
`capability_pack_enforcement` check, pinning the temp tree.

**(B) A test-harness teardown race** with no production defect.

A **read-only concurrency review of the production verifier path found no
handle leak**. That negative finding is what selects **(B)** — and it is also
what *prohibits* production mutation under this unit. It is a finding, not a
proof of absence: if execution evidence later contradicts it, the task stops and
returns to Stage rather than quietly editing `src/`.

## Options

| # | Option | Verdict |
|---|---|---|
| 1 | Fix it inside the `183.001-T` / `189-S` cycle that found it | **Rejected** — P-021 C1/C4; would be a C7 violation |
| 2 | Change the production verifier to release handles earlier | **Rejected** — unevidenced production mutation on a shipped verification gate; the review found no leak to fix |
| 3 | `ignore_cleanup_errors=True` / `shutil.rmtree(ignore_errors=True)` | **Rejected** — see below |
| 4 | Relocate the fixture under `.autoharness/staging/tmp/` per D7b | **Rejected as out of scope** — recorded as an open question |
| 5 | **Test-only bounded, re-raising retry at the teardown site** | **SELECTED** |

### Why option 3 is rejected on principle

Swallowing the cleanup error is the one variant that *looks* like a fix and is
not one. It makes a persistent handle leak indistinguishable from a healthy
run; it permanently suppresses the `WinError 5` access-denied case, which is
**not** the benign sharing-violation story and may indicate a genuine
permissions or leaked-handle defect; and it leaks a temp tree into the OS temp
area on every affected run.

It is also already a known local anti-pattern: `tests/test_graphtor_mcp_shim.py`
`tearDown` calls `shutil.rmtree(..., ignore_errors=True)` today, and that line
is recorded as a defect in its own right in stash `8CB606F8`. Adopting it here
would spread a defect while claiming to remove one.

A bounded retry that **re-raises** absorbs a transient sharing violation and
still fails the suite loudly on a real leak. That is the whole difference.

## Decision (option 5)

In `tests/test_capability_pack_enforcement_verifier.py` only, at the `_run()`
temp-workspace teardown site:

* catch `PermissionError` whose `winerror` is **32** or **5**;
* retry the removal a **small fixed** number of times with a **short bounded**
  backoff;
* **re-raise** the final exception once the bound is exhausted.

Any `PermissionError` with another `winerror`, and any other `OSError`,
propagates immediately without retry. Both 32 and 5 are retried because both
were observed; the catch is narrowed to those two codes so unrelated failures
still surface at once.

### Blast radius and the P-006 hardening gate

One test module, teardown path only. No assertion changes, no production code,
no schema, no CLI distribution surface, no template family. **`Requires plan
hardening: no`** — none of the elevated-blast-radius signals is present, so
`plan-harden` is not invoked. Plan depth is lightweight by operator direction
and proportionate to the work; the plan content (scope, prohibitions,
verification order, stop condition) is carried inline here and on `184.001-T`
rather than in a separate `impl-plan` artifact. **No gate was bypassed**, and
`force_harvest_no_gates` was neither required nor used.

### Prohibited under this unit

* `ignore_cleanup_errors=True`, `shutil.rmtree(ignore_errors=True)`, or any
  retry that ends in `pass`/`return` instead of a raise.
* An unbounded retry or unbounded backoff.
* Any change under `src/`, notably `src/autoharness/verify_workspace.py`.
* Any change to another test module — including the `8CB606F8` tearDown repair,
  **even if verification implicates it**.
* Weakening, deleting, skipping, or `xfail`-ing any assertion.
* Adding a `dir=Path.cwd()` anchor to `TemporaryDirectory`.
  `tests/test_test_suite_isolation_contract.py` guards against reintroducing
  that pattern anywhere under `tests/`
  (`docs/closure/149-S-141-F-post-merge-closure.md`); doing so regresses that
  guard immediately.

## Verification order (mandatory, in this order, after the code change)

1. **The exact test** —
   `python -m unittest tests.test_capability_pack_enforcement_verifier.CapabilityPackEnforcementVerifierTests.test_orphaned_manifest_entry_without_pack_fails`.
2. **Cross-test sequence with the Graphtor module** — run
   `tests/test_capability_pack_enforcement_verifier.py` together with
   `tests/test_graphtor_mcp_shim.py` in a **single process**, both orderings.
3. **No lingering relevant processes or temp directories** — after step 2,
   confirm no leftover `node`/`python` child from the shim tests survives and no
   leftover temp workspace from this module remains.
4. **Canonical suite** — `PYTHONPATH=src python -m unittest discover -s tests`.

Steps 2 and 3 are not ceremony. They exist because `8CB606F8` is the leading
hypothesis for external handle pressure, and running the repaired test *in
isolation* would prove nothing about it.

### Stop condition

If step 2 or 3 shows lingering processes or directories, that is evidence the
true cause is the `8CB606F8` teardown leak. **Do not raise the retry bound to
mask it, and do not fix `8CB606F8` here** — record the finding and return the
unit to Stage. Likewise, if a correctly bounded retry still fails
deterministically, the test-only diagnosis is disproved: stop and return to
Stage rather than editing production code.

## The Graphtor tearDown leak — captured, deliberately not combined

Stash `8CB606F8` records a separate defect in
`tests/test_graphtor_mcp_shim.py` `GraphtorMcpShimHandshakeTests.tearDown`:

1. the whole cleanup block is gated on `self._proc.poll() is None`, so an
   already-exited child is never `wait()`-ed and its `stdin`/`stdout`/`stderr`
   PIPE objects are never closed;
2. on the live path only `stdin` is closed;
3. there is no final `wait()` after the `kill()` fallback;
4. the `_start_reader` pump thread iterating `proc.stdout` is never joined;
5. `shutil.rmtree(..., ignore_errors=True)` silently swallows failures.

It is a **plausible but unproven** contributing cause of the sharing violations
above, held at **P2 / medium** as a follow-up. It stays in the stash and is
**not** harvested, **not** combined, and **not** archived.

Keeping the two units apart is the point, not an oversight: merging them would
widen a bounded test-only repair *and* destroy the ability to tell a test-local
teardown race apart from cross-module handle pollution — which is precisely
what step 2 is designed to measure.

## Open questions

1. **Unproven causal link** between `8CB606F8` and this failure. Steps 2–3
   produce evidence either way; a negative result does not block this repair.
2. **Why this test** — `test_orphaned_manifest_entry_without_pack_fails` is the
   manifest-listed-but-file-absent path. Whether that path holds a handle
   marginally longer than its siblings, or is simply unlucky in ordering, was
   not determined and is not needed for the repair.
3. **Containment tension (deferred).**
   `docs/decisions/2026-09-15-flat-manifest-shipment-closure-deliberation.md`
   D7b requires fixture workspaces under the repo-internal
   `.autoharness/staging/tmp/` root rather than the OS temp area. This test uses
   a bare `tempfile.TemporaryDirectory()`. Reconciling that is a separate
   containment-scoped unit, explicitly **not** authorized here; the bounded
   retry neither advances nor obstructs it.
4. **Generalizing the retry helper** to other `TemporaryDirectory` sites is
   deferred. This unit fixes the one observed site; premature generalization
   would touch modules with no observed defect.
5. **Retry bound values** are left to implementation within the "small and
   fixed" constraint. They are not a contract surface — but the bound MUST be
   finite and MUST end in a re-raise.

## Traceability

| Artifact | ID / path |
|---|---|
| Promoted stash entry | `78548873` (high, bug) |
| Deferred follow-up | `8CB606F8` (medium, bug — remains in stash) |
| Related, not duplicate | `AD0F128D` (`.autoharness/staging/tmp/` fixture accumulation) |
| Deliberation | `034-DL` |
| Covering feature | `184-F` |
| Task | `184.001-T` (`size: S`, `size_source: agent`, `size_ruleset_version: 2h-rule-v1`, `complexity: medium`) |
| Shipment | `190-S` (SHIP-24, priority high, manifest `[184-F, 184.001-T]`, verified by read-back) |
| Discovered after | `622a41a1` on `chore/stage-176-s-workflow-defects` |
| Unblocks | PR #457 Push B canonical-suite verification gate |

### Sequencing note (no dependency edge added)

`190-S` is deliberately **not** wired to `189-S` with a `blocks` edge. The
edge would have to run `190-S` → `189-S` (this repair before the shim
shipment), because `189-S`'s own verification order ends in the canonical
suite — the very gate this defect breaks. The reverse edge would deadlock the
pair. Rather than mutate the peer's in-flight `189-S` record to encode that,
the ordering is recorded here and in the Ship handoff: **`190-S` lands first**.

## Session mode

`DEGRADED_MODE`. backlogit MCP available; `backlogit_stash_archive` is not
exposed by this server build, so the canonical non-destructive CLI fallback
`backlogit stash archive` was recorded and used. `ENGRAM_DEGRADED`,
`INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE` — those servers exposed no tools
this session, so file-based exploration was used throughout. `INDEX_SYNC_OK`
(1447 indexed). Checkpoint enumeration: 66 stage-owned records, 0 active, 0
quarantined, 0 anomalies → zero-candidate normal startup.

**P-021 C5/C6 triage obligations.** Unconditional duplicate scan run over all
116 active entries: **CLEAN** — no pre-existing entry describes either
expansion; `AD0F128D` and `C3B84C7A` examined and explicitly rejected as
duplicates; no merge, no duplicate archived. Late-identifier reconciliation
triggered by `review-thread=N/A` on both entries: **no late identifier found** —
both were captured from threadless surfaces and no Ship-owned residual-risk
record cites them yet, so the `N/A` stands as a truthful terminal record. That
is a no-op completion, not a C3/C6 shortfall.

**Learnings retrieval.** `docs/compound/` searched for Windows/`rmtree`/retry
prior art — **confidence: low**, no directly applicable prior solution.
Adjacent context used: `docs/closure/149-S-141-F-post-merge-closure.md` (source
of the `dir=Path.cwd()` prohibition) and
`docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md`
(~line 829), which records a *prior* unscoped-suite observation of this same
`PermissionError [WinError 32]` in `shutil.rmtree` — corroborating that this is
a recurring, previously unowned defect rather than a one-off.

**Role boundary.** Stage produced backlog and planning artifacts only. No
source, test, config, or script file was created, modified, or deleted; no
build, suite, or linter was run; no branch or worktree created; no PR touched;
no push; no shipment claimed. The verification order above is a specification
for Ship to execute, not work performed here.
