---
title: "Closure-evidence window checks: treat timestamp-precision ambiguity as fail-closed, parse event logs strictly, and probe paths without swallowing errors"
problem_type: logic-error
category: correctness
root_cause: "The new closure-evidence engine-window check compared a whole-second writer timestamp against engine logs with microsecond precision, and the review rounds found that every unspecified edge defaulted to pass: more than six fractional digits, a lowercase t separator, max-date overflow, JSONL split on U+0085, events missing event_type or payload, and an existence probe that swallowed PermissionError."
tags: [closure-evidence, timestamp-precision, fail-closed, jsonl, lstat, permission-error, copilot-review, shipment-reconcile]
shipment: 171-S
date: 2026-10-16
source: docs/compound/2026-10-16-closure-evidence-window-timestamp-precision-and-fail-closed-event-parsing.md
doc_type: learning
---

## Problem

Shipment 171-S added an engine-window check to the closure-evidence validator. It
asserts that the pre-close evidence was captured inside the window the engine log
records. Nine Copilot review rounds all converged on edge cases of that one check.
The base logic was sound each time. The unspecified inputs were not.

## What we learned

### Time-window gates need a precision contract

* The capture writer emits whole-second timestamps. Engine logs carry microseconds.
  A whole-second value can sit on either side of a sub-second boundary, so
  precision ambiguity is a fail-closed condition, not a pass.
* Define behavior for more than six fractional digits (reject, never truncate or
  round), a lowercase `t` separator, and max-date overflow when the comparison
  adds a tolerance to a datetime at the end of the representable range.
* Decide each of these before the first review round. Each one cost a round.

### Log parsers must be strict

* Split JSONL on LF only. `str.splitlines()` also splits on U+0085 and other
  Unicode line boundaries, which can occur inside a valid JSON string and corrupt
  a record.
* Validate that `event_type` and `payload` are present and well-typed, not just
  that their values match. Distinguish key presence from a null value.

### Existence probes must not hide errors

* `os.path.lexists` returns `False` on `PermissionError`, so an unreadable path
  looks absent. Use `os.lstat` and treat only `FileNotFoundError` as absent.
* Do containment checks before probing, so a probe never touches a path outside
  the workspace.

### Mistakes made

* An archive-resident `location` is not an archived status. A record can sit in
  the archive directory without having the archived status.
* One of my own edits left a stray line that silently overwrote the previous
  assignment. Re-read the edited region after every edit.

## Prevention

* For any new comparison gate, write the edge-case table (precision, format,
  range, absent, null) first and make every ambiguous cell fail closed.
* Add regression tests for each parser edge above, including a U+0085 inside a
  JSON string and a permission-denied path.
* Capture-writer subsecond precision is deferred as stash `CA919C4C`. Until it
  lands, the gate must keep failing closed on ambiguous precision.
