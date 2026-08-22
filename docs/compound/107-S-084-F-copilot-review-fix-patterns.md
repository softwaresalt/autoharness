---
title: Token-efficiency telemetry — Copilot review-fix patterns (107-S / 084-F)
tags: [telemetry, tool-event, review-fix, path-validation, composition]
related_pr: 273
related_shipment: 107-S
related_feature: 084-F
source: docs/compound/107-S-084-F-copilot-review-fix-patterns.md
doc_type: learning
---

# Compound Learning: Six hardening fixes for `ToolTelemetryEvent` ingestion and composition

Captured from PR #273's hosted Copilot review (6 threads, all resolved) — the
sole hosted Copilot review round on that PR. (A separate, earlier
`parent_event_id`-linkage fix, commit `1c09212`, came from implementing the
plan's own ratified `## Review Fixes` item during task build/local review —
not from a hosted Copilot PR comment — and is not one of the six.)
Each fix corrects a place where implementation drifted from the frozen schema
contract or from safe-composition semantics. Recorded here so future telemetry
schema/composer work reuses the same reasoning instead of re-deriving it.

## 1. `event_id` schema says "any non-whitespace string", not "must be a UUID"

The frozen schema (`schemas/tool-telemetry-event.schema.json`) declares
`event_id` as `{"type": "string", "minLength": 1, "pattern": "\\S"}`. The
original `from_mapping()` unconditionally ran every provided value through a
UUID normalizer, silently replacing arbitrary caller-supplied IDs (e.g. IDs
correlated with an external system) with a generated UUID. **Fix**: only
generate a UUID when `event_id` is omitted entirely (`None`); an explicitly
provided empty string is still rejected by `_normalize_event_id` (the schema's
`minLength: 1` / non-whitespace pattern applies to any provided value — empty
is not treated as "omitted"). Otherwise preserve the caller's value verbatim
once it passes the non-whitespace pattern. Lesson:
when a frozen schema and an ingestion helper disagree on strictness, the
schema wins — don't let a convenience normalizer quietly narrow a public
contract.

## 2. Path-bearing fields need repo-local containment checks, not just schema validation

`evidence_path` / `artifact_refs` are schema-valid as long as they're
non-empty strings — the schema can't express "must resolve inside the
workspace." Absolute paths and `..` traversal (and, on Windows, drive-relative
forms like `C:evil.txt`) all pass schema validation but can escape the
workspace root. **Fix**: added `validate_event_workspace_references()`,
mirroring the existing `_is_within` / `Path.resolve()` containment pattern
already used in `context.py`'s `resolve_context_ref`. `Path.resolve()` follows
symlinks, so checking `candidate.relative_to(root)` after resolution catches
traversal, symlink escapes, and drive-relative edge cases in one check.
Validation is wired at the CLI layer (`_telemetry_event_command`, right after
`from_mapping()`), not inside the frozen dataclass, because workspace root
isn't known to the dataclass and existing direct-construction tests
(e.g. `artifact_refs=("docs/telemetry-reference.md",)`) shouldn't require a
workspace parameter. Lesson: schema validation and workspace-containment
validation are different concerns with different natural owners (dataclass vs.
CLI boundary) — don't force one function to do both.

## 3. A composer must never silently operate on a truncated/partial read

`read_events()` originally could raise partway through reading segments and
still return whatever partial event list had been collected before the
failure — and `record_epoch` would compose against that undercounted list,
producing a corrupted-but-plausible-looking epoch. **Fix**: any segment
`OSError` now discards all collected events for that read and returns
`status="unavailable", events=()`; `record_epoch` checks for `unavailable` and
skips composition entirely (appending a diagnostic), preserving the original
close payload instead of persisting an undercount. Lesson: for anything
downstream of a read that will be composed into an immutable record, "return
nothing and flag unavailable" is strictly safer than "return what we got" —
partial success is often indistinguishable from a quietly wrong answer.

## 4. Monotonicity violations in derived cumulative metrics deserve diagnostics, not silent max()

The composer already used `max()` aggregation across a stream of
cumulative-token values (so any prior decrease can't corrupt the result), but
that same decrease is itself signal — it usually means an out-of-order event
or an upstream counter reset. **Fix**: added `_non_monotonic_diagnostics()`
that walks the timestamp-sorted stream and reports every place a later value
is smaller than an earlier one, while still returning the `max()` for the
actual aggregate. Applies to both cumulative token streams. Lesson: a
defensive aggregation function that clamps/normalizes bad input should still
surface that the input was bad — silently "handling" an anomaly and saying
nothing about it is a lost diagnostic opportunity for whoever generated the
anomaly upstream.

## 5. Zero is not "present but small" — it's absent for provenance-quality purposes

`_metric_quality_for` originally treated any non-`None` metric value
(including `0`) as contributing to composition provenance quality. But the
schema declares these fields `exclusiveMinimum: 0`, meaning `0` is not a valid
"real" observation for this metric — it's a default/unset sentinel in
practice. **Fix**: `_metric_contributes()` requires
`isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0`,
matching `tool_event._metric_populated`'s existing semantics, and provenance
aggregation now only counts strictly-positive contributors. Lesson: when a
schema declares an exclusive bound, downstream "is this value meaningful"
logic must respect that bound too — `is not None` is the wrong proxy for
"populated" whenever `0`/`False`/empty-string are in-domain-but-meaningless
values.

## 6. Strict ingestion means malformed input fails loudly, not `None`

`from_mapping()`'s handling of `work_sizing_snapshot` treated any value that
wasn't a dict as `None` (fail-open). The schema declares `anyOf(object, null)`
— i.e. any other JSON type (string, number, array) is invalid, not
`null`-equivalent. **Fix**: raise `ToolTelemetryEventError` for any
non-object, non-null `work_sizing_snapshot`. Lesson: "coerce unexpected shape
to a safe default" is the wrong default behavior for a field with a strict
schema type union — coercion hides a caller bug that strict rejection would
have surfaced immediately.

## Process notes

- Copilot re-arms review on every push to the PR branch — after pushing the
  fix commit, the CLI gate (`autoharness gate copilot-review`) returned
  `WAITING_FOR_REVIEW` even though the prior round had passed on the old HEAD.
  Re-requesting the reviewer
  (`gh api repos/OWNER/REPO/pulls/N/requested_reviewers -f reviewers[]=copilot-pull-request-reviewer[bot]`)
  and polling with `--max-wait` is the correct recovery, not waiting indefinitely
  or assuming the old pass still counts.
- Reply-then-resolve ordering matters for auditability: every thread got an
  explicit reply citing the fixing commit SHA and test coverage before the
  GraphQL `resolveReviewThread` mutation ran against it.
