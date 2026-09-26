---
title: "Graphtor MCP shim stdin-write-error test: one timing-synchronization defect family, repaired test-only"
description: "Stage deliberation comparing deferred-expansion stash entries AD3D41FA (deterministic Windows `messages seen: []` failure under the PR #457 Push B pre-push gate) and 24A85BF8 (intermittent varying-assertion-index failure during 159-S pre-PR verification). Concludes both signatures are ONE timing-synchronization defect family in the test harness: the test waits a fixed 300 ms instead of waiting for the fake child to actually close its stdin read end, so the first write can land in a still-open pipe and no EPIPE is ever emitted. Production scripts/graphtor-mcp-shim.cjs already installs the expected child.stdin error handler and is unchanged, so the authorized repair is test-only. Promotes the decision to a minimum separate work unit (183-F / 183.001-T / 189-S) that unblocks PR #457 Push B."
doc_type: decision
source: docs/decisions/2026-09-20-graphtor-shim-test-synchronization-defect-family-deliberation.md
date: 2026-09-20
status: decided
decision_status: decided
depth: lightweight
deciders: operator, Stage
promoted_to: 183-F
promoted_to_note: "Promoted to the queue as covering feature 183-F with single task 183.001-T, assembled into shipment 189-S (SHIP-23). The work unit is deliberately minimum: one test function, one file, test-only."
branch: chore/stage-176-s-workflow-defects
head_at_decision: eabcecc8
stash_sources:
  survivor: 24A85BF8
  merged_duplicate: AD3D41FA
unblocks: "PR #457 Push B (local commit eabcecc8, unpushed)"
scope: test-only
production_change_authorized: false
policies: [P-021, P-005, P-010, P-016, P-001]
---

# Graphtor MCP shim stdin-write-error test — one defect family, test-only repair

## Question

Are deferred-scope-expansion stash entries `AD3D41FA` and `24A85BF8` one
defect or two? `AD3D41FA` explicitly deferred this merge-or-split decision to
deliberation rather than resolving it at capture time, and the answer
determines whether the authorized repair is one test-only work unit or two
separately scoped investigations.

## The two captures

| | `24A85BF8` (earliest, 14 days) | `AD3D41FA` (current, 0 days) |
|---|---|---|
| Test | `GraphtorMcpShimHandshakeTests::test_child_stdin_write_error_fails_requests_without_crashing` | same test |
| Signature | intermittent; the failing assertion index varied between runs (`satisfied[0]` vs `satisfied[1]`) | deterministic; 3/3 attempts, `messages seen: []` (neither predicate satisfied) |
| Discovery context | 159-S / 151-F pre-PR full-suite verification, no PR open | PR #457 Push B pre-push publication gate, universal circuit breaker (3 attempts) |
| Attributed cause at capture | "timing/race condition in the shim's error-synthesis path" | "test/implementation contract mismatch" |
| Production diff | zero diff in the test vs merge-base `05bbfc2f` | zero files under `src/`, `tests/`, `scripts/` across `a192e50c..eabcecc8` |

## Evidence read this session (read-only)

1. `tests/test_graphtor_mcp_shim.py` (the test, ~line 455): after spawning the
   fake child in `close-stdin-only` mode the test executes a bare
   `time.sleep(0.3)` with the comment "Give the fake server time to actually
   close its stdin read end before the first write is attempted". This is a
   **fixed-duration guess, not a synchronization**: nothing observes whether
   the child has in fact closed its stdin read end before `_write` runs.
2. `scripts/graphtor-mcp-shim.cjs` lines 244–257: `child.stdin.on('error', …)`
   is installed and routed through `handleChildTermination`, which synthesizes
   the JSON-RPC errors for the outstanding `initialize` and the queued request.
   The handler the test asserts on **already exists** and is unchanged.
3. `_collect_all` (test helper, line 247) drains with a 10 s budget and returns
   every observed message; an empty `seen` list therefore means *no shim output
   at all arrived*, not that a message was dropped by a naive collector.

## Diagnosis — one family

Both signatures are the same unsynchronized handoff observed under different
host timing:

* If the 300 ms elapses **after** the child closed its stdin read end, both
  writes fail, `child.stdin` emits `error`, `handleChildTermination` synthesizes
  both responses, and the test passes. This is the historical green path.
* If the 300 ms elapses while the pipe is **partly** resolved, one write lands
  and one fails — producing exactly `24A85BF8`'s observation that *which*
  assertion index fails varies between runs.
* If the 300 ms elapses **before** the child closed its stdin read end at all
  (slower/loaded Windows + Node process startup), both writes land in a
  still-open pipe, no `EPIPE` is ever emitted, the shim has nothing to
  synthesize, and the collector times out with `messages seen: []` — exactly
  `AD3D41FA`'s deterministic three-attempt signature.

The determinism in `AD3D41FA` is not a different defect; it is the same race
losing *consistently* on this host, which is why a 70-second cooldown between
attempts 2 and 3 changed nothing. Intermittent-vs-deterministic is a property
of the environment, not of the fault.

Nothing in the evidence implicates production code: the shim's handler exists,
is registered before any write, and is unchanged since the merge-base. The
fault is that the test never establishes the precondition its own comment
claims to establish.

**Decision: ONE timing-synchronization defect family, located in the test
harness. The authorized repair is test-only.**

## Falsification condition

This diagnosis is disprovable by exactly one observation: a correctly
synchronized test — one that provably waits for the child's stdin read end to
close before the first write — that *still* observes no synthesized error
response. If Ship produces that observation, the task STOPS and returns the
finding to Stage. `scripts/graphtor-mcp-shim.cjs` must not be modified under
this authorization on any weaker evidence.

## Authorized work unit (minimum)

* Covering feature **183-F** — Graphtor MCP shim test synchronization repair.
* Task **183.001-T** (`size: S`, `complexity: medium`, ruleset `2h-rule-v1`) —
  replace the fixed `time.sleep(0.3)` with a deterministic readiness
  synchronization in `tests/test_graphtor_mcp_shim.py`, preserving both
  assertions and the test's isolation of the `child.stdin` `error` path.
* Shipment **189-S** (SHIP-23, priority high) — manifest `[183-F, 183.001-T]`.

Out of scope, explicitly: `scripts/graphtor-mcp-shim.cjs`, any other test or
source file, assertion weakening/skipping, and sleep-based "fixes".

## Prerequisite / unblocker status

This work unit is a **prerequisite toolchain unblocker for PR #457 Push B**.
Push B exists locally as `eabcecc8` on `chore/stage-176-s-workflow-defects` and
is unpushed; PR #457 remains at Push A HEAD `a192e50c`. The pre-push
verification gate cannot pass while this test fails, and Push B itself touches
no `src/`, `tests/` or `scripts/` file — so the block is environmental to the
publication, not caused by it. Repairing the test is the smallest change that
restores the publication path without bypassing the gate.

The operator's latest instruction **explicitly authorizes reopening the
universal circuit breaker** `graphtor-mcp-shim-child-stdin-write-error-no-response`
(`docs/memory/2026-09-20/circuit-break-graphtor-mcp-shim-stdin-write-error-test.md`,
3 attempts) **only after test code changes have been made**. Re-running the
failing operation before editing the test remains prohibited, as does any
`--no-verify` bypass of the pre-push hook.

## Verification order (binding, in order)

1. Targeted test:
   `python -m unittest tests.test_graphtor_mcp_shim.GraphtorMcpShimHandshakeTests.test_child_stdin_write_error_fails_requests_without_crashing`
2. Bounded repeat of that same targeted test under Windows/Node (fixed small
   repeat count, all green) — proves the race is *closed*, not re-won.
3. Canonical suite: `PYTHONPATH=src python -m unittest discover -s tests`.
4. Ordinary pre-push hook, unbypassed.

## P-021 C5 / C6 stash disposition

* **Duplicate scan (C5, unconditional)**: performed over all 118 active stash
  entries for `graphtor|shim|stdin|EPIPE`. Exactly two matches — `24A85BF8` and
  `AD3D41FA`. No third entry describes this expansion.
* **Merge**: because deliberation concludes one expansion, the entries are
  reconciled into the **earliest-captured survivor `24A85BF8`**, and
  **`AD3D41FA` is archived as the merged duplicate** via the non-destructive
  stash archive operation. No destructive removal was used, and no evidence was
  discarded — `AD3D41FA` retains its full circuit-breaker source refs in the
  archive.
* **Late-identifier reconciliation (C6)**: `24A85BF8` recorded `PR: N/A`
  (captured pre-PR). The Ship-owned residual-risk record
  `docs/closure/159-S-151-F-post-merge-closure.md` cites the entry by ID and
  binds its discovery run to shipment 159-S / feature 151-F, whose feature PR
  is **#435**. That identifier is reconciled into the surviving entry in place.
  `task ID` legitimately remains `N/A` — no 159-S task ever covered this
  surface. `AD3D41FA`'s `feature ID: N/A` / `shipment ID: N/A` are now closed
  forward by this decision's promotion to 183-F / 183.001-T / 189-S.
* Both entries are archived non-destructively as **consumed**, each carrying a
  forward reference to 183-F / 183.001-T / 189-S and to this decision.

## What this decision does not do

It does not authorize any production change, any push, any PR-body or review
thread edit, any modification of existing portfolio plans, and it confers no
Ship claim authority beyond shipment 189-S.
