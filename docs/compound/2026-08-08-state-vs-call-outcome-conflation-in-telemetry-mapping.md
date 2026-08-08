# Compound Learning: A Subsystem's Reported State Is Not the Same as the Call's Own Outcome

**Origin**: PR #314 (120-S / 082-F, cross-pack measurability documentation —
Engram + graphtor-docs evidence mapping), 1 round of Copilot review, 5 findings,
all genuine, all fixed at HEAD `d8ef5e5d`.

## The pattern

When mapping a pack's real telemetry surface onto the ratified `ToolTelemetryEvent`
`status` field, it is tempting to reach for whatever enum the pack already exposes
that "looks like" an outcome — but a **background subsystem's reported state** is a
different axis than **the outcome of the specific call that reported it**. Conflating
the two silently misattributes a healthy call to a failed status:

- **graphtor-docs**: the `get_status` MCP tool call **always succeeds** when it
  returns a value — that value happens to be a `SyncStatus` enum
  (`Idle`/`Syncing`/`InProgress`/`Done`/`Complete`/`Error`) describing the
  **background sync process's** state, not the outcome of the `get_status`
  invocation itself. A `get_status` call that successfully reports
  `SyncStatus::Error` (the background sync failed) is itself a **successful** call
  and must be `status: success` — mapping `SyncStatus::Error` directly to
  `status: failed` would falsely mark a healthy diagnostic call as failed.
  `SyncStatus`'s own value may only be mapped onto a **separately wrapped
  sync-cycle event's** status, never onto the calling `get_status` invocation's own
  status.
- **Engram** (a related but distinct conflation caught in the same review):
  `UsageEvent.timestamp` is constructed via `chrono::Utc::now()` **after** the
  response is fully computed (i.e. after `latency_ms`/`response_bytes`-derived
  fields are already known) — it is the call's **completion** time, not its start.
  Mapping it directly onto `started_at` silently shifts every recorded call start to
  its completion, which would corrupt any later duration-window or ordering
  analysis built on `started_at`.
- **A structural/wire-shape variant of the same class of error**: graphtor's
  search tools (`search_local_docs`, `search_semantic`, `traverse_doc_links`)
  return a single markdown `CallToolResult` text blob assembled from an internal
  result vector — **there is no separate, named `result_count` field on the wire
  at all**. Documenting `result_count` as `host_reported`/`observed` overstates
  the evidence: any count is adapter-derived from the returned blocks, not
  directly reported by the host.

## The generalizable check

Before mapping any pack-native field onto a `ToolTelemetryEvent` provenance-bearing
field (`status`, `started_at`, `result_count`, etc.), ask two separate questions:

1. **Does this field describe the call's own outcome, or a different subsystem's
   state that the call happens to report?** (the `SyncStatus`/`status` conflation)
2. **Does this field's value get set at the moment the axis it's supposed to
   represent actually occurs, or at some other point in the call lifecycle?** (the
   `timestamp`/`started_at` conflation)
3. **Does the field exist on the wire at all, or is it something an adapter would
   have to compute from a differently-shaped return value?** (the `result_count`
   provenance overstatement)

A field failing any of these three checks must never be labeled
`host_reported`/`observed` — it belongs under `derived` (adapter-computed from
correlated evidence) or `unavailable` (does not exist at any granularity reviewed),
per the same evidence-class vocabulary already established for 079-F/108-F.

## A related, separate lesson from the same review: metadata flags are not the
## redaction itself

The same review round also flagged that a binding acceptance criterion
(`redaction_applied: true`) was written as if setting the flag were the redaction —
an emitter could set `redaction_applied: true` on a payload that still contains the
raw sensitive value, satisfying the letter of the check while violating its intent.
The fix requires the actual omission or transformation to happen **first**, with the
flag only attesting to a transformation that has already occurred; verification of
compliance must check the emitted value itself, not merely the presence of the flag.

## Where this applies

- `docs/telemetry/graphtor-docs-evidence-map.md` (`status`, `result_count`)
- `docs/telemetry/engram-evidence-map.md` (`timestamp`/`started_at`)
- `docs/telemetry/cross-pack-adapter-gap-report.md` (mirrored `status`/`SyncStatus`
  correction; AC1 redaction-flag wording)
- **Forward-looking**: any future 084-F-scoped adapter that emits real
  `ToolTelemetryEvent` records from these packs must apply the same
  state-vs-call-outcome, timing-axis, and wire-shape checks to its own field
  mappings, and must verify actual redaction rather than trusting the flag alone.

## Session process note (unrelated defect class, same session)

During this session's CI verification, the `test` and `ci gate` checks failed once
on a pre-existing, non-deterministically-named concurrency test
(`test_two_writers_interleaved_seal_preserve_every_distinct_segment` in
`tests/test_telemetry_jsonl_sink.py`) that this PR's diff (three `docs/telemetry/*.md`
files only, zero Python changes) could not have caused. Confirming the diff touched
no Python files before deciding this was CI-environment flakiness (rather than a
real regression requiring a code fix) — and then simply re-running the failed CI
jobs, which passed clean the second time — avoided misattributing a genuine
race-condition flake in unrelated test infrastructure to a documentation-only change.
