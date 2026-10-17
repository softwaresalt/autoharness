---
spike_id: 211.002-T
title: "Spike: can the backlogit engine event log attribute item-level archival to a shipment cascade?"
status: complete
recommendation: refuse-postconditions-only-passing-recovery
date: 2026-10-17
source: ".backlogit/logs/*.jsonl (read-only; git-ignored, 90 shipped shipments, 987 archived events)"
deliverable: "src/autoharness/shipment_close/event_log.py and tests/fixtures/cascade_close_event_logs/"
plan: docs/plans/2026-10-16-cascade-close-recovery-and-journaling-plan.md
hardening: H1, H9
---

# Spike Findings: engine event-log provenance for cascade-close recovery

## Question

Plan unit T1 and hardening H1 require that a `postconditions_only` recovered record prove the **whole mutation
footprint** was produced by this cascade: the engine-authored `shipment_status_changed -> shipped` event after
`invocation.started_at`, plus, for every required archived id, an engine-authored `archived` event inside the cascade's
operation window with no foreign-actor event on those items. Can the event log supply that correlation, and is 214-S
recoverable?

## Method

Read-only characterisation of every `.backlogit/logs/*.jsonl` (the logs are git-ignored; the fixtures are sanitized
slices: titles, authors, commit messages and comments replaced by `<sanitized>`). Event shapes were tabulated across all
files, then per-shipment timing and actor analysis was run for every shipment with a `shipped` event.

## Findings

### 1. What the engine does correlate

| Event | Where | Correlation |
|---|---|---|
| `shipment_status_changed` (`status: shipped`) | shipment log | `delta._shipment_operation == "<S>"` (the claim event uses an opaque hex id, the ship event uses the shipment id) |
| `pre_task_completion_gate_passed` (level `shipment`) | shipment log | `_shipment_operation == "<S>"` |
| `status_changed` (`shipment released`, feature `active -> done`) | feature log | `_shipment_operation == "<S>"` |
| `status_changed` (`shipment claimed`) | shipment, feature, task logs | opaque hex operation id shared by the claim |

The `shipped` event is present and operation-correlated in 52 of 90 shipped shipments (all recent ones; older logs
pre-date the key). Timestamps are offset-bearing (`-07:00`, 7-digit fractions); the reader converts to UTC instants
(`parse_rfc3339_instant`, H9).

### 2. What the engine does not correlate: archival

All 987 `archived` events have actor `backlogit` and `delta` keys exactly `{archive_path}`. There is no
`_shipment_operation`, no operation id, and no caller identity. The actor is the engine whether the archive was run by a
cascade, by a human running `backlogit archive`, or by another tool, so "engine-authored" does **not** distinguish a
cascade from a manual archive.

Timing is not a substitute. In recent healthy runs the item `archived` events land 60-750 s after the `shipped`
event (one per item, minutes apart, which also suggests separate archive operations rather than one atomic engine
step). A window can therefore only say "this archive happened soon after shipped", never "this cascade did it". A
human completing the archival within the same window is indistinguishable.

### 3. 214-S

`shipment_status_changed -> shipped` (`_shipment_operation: "214-S"`) is present at 10:45:43-07:00. The 207-F feature
release (`_shipment_operation: "214-S"`) is at 10:45:29. But the item `archived` events are 3609-3933 s later
(11:45-11:51), 207.001-T is archived twice (11:45:51 and 11:46:38), and the shipment itself is archived at 11:51:45. The
log is consistent with a wrapper killed mid-cascade followed by a later archival by some other actor; the log itself
cannot say which.

### 4. Foreign actors

Actors present across the logs include `human`, `agent`, `stage`, `ship`, `operator`, and others, but they appear on
comments, estimates and mutations, not on `archived`. Foreign-actor detection is therefore possible for non-archive
events in the window and is implemented, but it cannot reveal a manual `backlogit archive`.

## Conclusion (explicit)

* **Item-level `archived` events cannot be attributed to a cascade** with the current engine event log: they carry only
  `archive_path` and the engine actor. Only the shipment `shipped` transition and the feature release are
  operation-correlated.
* Under H1 a `postconditions_only` recovery that would pass is therefore **refused (exit 10)**. Only a journal-observed
  recovery (`journal_complete`, where the engine's own stdout names the archived ids) may pass. The reader's
  `attribute_archived_footprint` attributes only if every in-window archived event itself carries
  `_shipment_operation == <shipment id>`; real logs return `attributed=False`, and a future backlogit that adds the key
  turns this on without code change.
* **214-S is not recoverable to a passing record** from the event log. It has no journal (legacy record), its archival
  events are an hour after `shipped`, one is duplicated, and none are attributable. The `shipped` transition alone is
  evidence that the engine reached `shipped`, not that the cascade finished. This matches OQ-4: 214-S itself is not
  repaired by shipment 218-S.

## Reader contract (T1 deliverable)

`read_cascade_events(backlog_dir, shipment_id, since)` returns the `shipped` events (operation-correlated), release
events, in-window `archived` events, foreign-actor events and any scope item whose log is missing. A missing logs
directory or shipment log, a linked path, an oversize or non-UTF-8 file, malformed JSON, a missing field, or a naive
timestamp is an `EventLogError`; the reader never returns an empty result for a log it could not read. Unknown event
types are ignored, but every event it relies on is shape-checked, so a backlogit schema change degrades recovery to
refusal rather than to a wrong pass.

## Fixtures

* `tests/fixtures/cascade_close_event_logs/shipment_213_s_clean/`: a healthy cascade (six items plus shipment).
* `tests/fixtures/cascade_close_event_logs/shipment_214_s_incident/`: the 214-S-shaped log (late, duplicated archival).
