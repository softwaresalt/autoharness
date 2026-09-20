# Stage session — Graphtor shim test synchronization defect family (2026-09-20)

## Outcome

Deliberated the two deferred-scope-expansion stash entries naming
`tests/test_graphtor_mcp_shim.py::GraphtorMcpShimHandshakeTests::test_child_stdin_write_error_fails_requests_without_crashing`
and concluded they are **one timing-synchronization defect family**, repaired
test-only. Promoted to a minimum separate work unit and assembled a shipment.

* Decision: `docs/decisions/2026-09-20-graphtor-shim-test-synchronization-defect-family-deliberation.md`
* Covering feature: **183-F**
* Task: **183.001-T** (`size: S`, `size_source: agent`, `size_ruleset_version: 2h-rule-v1`, `complexity: medium`)
* Shipment: **189-S** (SHIP-23, priority high, manifest `[183-F, 183.001-T]`, verified by read-back)

## Diagnosis (evidence, read-only)

* Test line ~455 executes a bare `time.sleep(0.3)` instead of waiting for the
  fake child (`close-stdin-only` mode) to close its stdin read end.
* `scripts/graphtor-mcp-shim.cjs` lines 244–257 already install
  `child.stdin.on('error')` → `handleChildTermination`; production is unchanged.
* `_collect_all` (10 s budget) returns every observed message, so
  `messages seen: []` means no shim output arrived at all — consistent with a
  write landing in a still-open pipe and no `EPIPE` ever being emitted.
* Intermittent (`24A85BF8`: varying `satisfied[0]`/`satisfied[1]`) vs
  deterministic (`AD3D41FA`: 3/3 empty) is the same race under different host
  timing, which is why a 70 s cooldown changed nothing.

Falsifier: a provably synchronized test that still observes no synthesized
error. On that evidence only, the task STOPS and returns to Stage; production
code stays untouched otherwise.

## Stash disposition (P-021 C5/C6)

* Unconditional duplicate scan over 118 active entries → exactly two matches.
* Merged into earliest-captured survivor `24A85BF8`; `AD3D41FA` archived as the
  merged duplicate. **Non-destructive archive only** (`backlogit stash archive`);
  both archived records verified to retain full text and forward references.
* Late-identifier reconciliation: `24A85BF8`'s `PR: N/A` closed to **PR #435**
  and `feature: N/A` to **151-F**, recovered from the Ship-owned residual-risk
  record `docs/closure/159-S-151-F-post-merge-closure.md`. `task`/`review-thread`
  `N/A` stand as truthful terminal records.
* Survivor priority raised `low` → `high` (now blocks a publication gate).

## Unblocker context

Prerequisite/toolchain unblocker for **PR #457 Push B** (local `eabcecc8` on
`chore/stage-176-s-workflow-defects`, unpushed; PR #457 remains at `a192e50c`).
Operator authorized reopening the universal breaker
`graphtor-mcp-shim-child-stdin-write-error-no-response` **only after test code
changes are made**. Verification order: targeted test → bounded repeat under
Windows/Node → canonical suite → ordinary pre-push hook (no bypass).

## Session mode notes

* `INDEX_SYNC_OK`; checkpoint enumeration clean (65 records, all resolved,
  0 quarantined) → zero-candidate normal startup.
* `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE` — those MCP
  servers exposed no tools this session; file-based exploration used instead.
* Registry gap noted: `.autoharness/backlog-registry.yaml` `features:` block
  declares no `sizing` key, but `backlogit_update_item` does accept
  `size`/`size_source`/`size_ruleset_version` and `complexity` as separate
  mutually exclusive writes. Structured emission was used; the registry's
  missing `sizing` flag is a documentation/parity gap worth a later fix.

## Next step (Ship)

Claim shipment **189-S**, execute **183.001-T** test-only, then resume PR #457
Push B publication.
