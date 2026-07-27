---
problem_type: api-design
category: telemetry-metric-provenance
root_cause: qualitative-provenance-polluting-numeric-fields
tags: [telemetry, derived-metrics, provenance, backward-compat, dataclass, fail-closed, copilot-review, p-018, additive-field]
shipment: 095-S
feature: 090-F
pr: 235
merged_at: "2026-07-27T21:40:54Z"
---

# 095-S / PR #235: Carrying Provenance Without Breaking Numeric Metric Consumers

Five auto-triggered Copilot review rounds on PR #235 converged on one design
theme: how to attach *qualitative* provenance (was a derived ratio computed from
observed operands, or estimated/derived ones?) to *numeric* telemetry metrics
without breaking the machine-readable contract downstream consumers depend on.
The final design and the three hardening fixes below are reusable any time a
metric pipeline needs to report both a value and how trustworthy that value is.

## Pattern: Additive Sibling Provenance Map (keep numeric fields numeric)

The first instinct — embedding provenance inline, e.g. a derived ratio rendered
as the string `"0.42 (estimated)"` — breaks every consumer that parses the field
as a number, and it silently changes the field's type from `float` to `str`.

The durable pattern instead keeps each derived metric **strictly numeric** (a
bare `float`, or a single documented `UNAVAILABLE` sentinel when an operand is
missing) and carries the provenance in a **separate additive map** keyed by
metric name, alongside the metric block:

- `derived_efficiency_metrics` stays `{metric_name: float | "unavailable"}`.
- A sibling `derived_quality: {metric_name: "observed" | "estimated" | ...}` map
  is *added*, never interleaved. Consumers that never look at `derived_quality`
  are completely unaffected; consumers that want provenance opt in by reading it.

This honors the plan's additive-field contract (`docs/plans/2026-07-26-telemetry-hardening-plan.md`
lines 482-486) and the invariant in `docs/telemetry-reference.md` that derived
metrics are always numeric-or-`unavailable`. The provenance helper
(`_ratio_provenance(value, *operand_qualities)`) returns the worst non-observed
marker only for a usable numeric value, and `None`/`unavailable` for a
sentinel value — so the two maps never disagree about whether a metric is real.

**Reusable rule:** when a value field and a "how good is this value" field both
need to travel, make the quality field an additive sibling keyed by the same
name. Never overload the value field's type to smuggle qualitative metadata.

## Fail-Closed Normalization of Untrusted Enum-Like Labels

`metric_quality` labels can arrive malformed (a non-string, a list, or an
out-of-vocabulary string) because they originate from recorded event data. Two
concrete failures resulted, and both were fixed by one guard, `_normalize_quality`:

1. **Unhashable-key crash** — a non-string label (e.g. a list) used directly as
   a `dict.get` key against the `_QUALITY_RANK` ranking map raises `TypeError:
   unhashable type`. A malformed input must never be able to crash the
   aggregation path.
2. **Undocumented-marker leak** — an out-of-vocabulary string passed straight
   through would surface a marker that no consumer or doc defines.

`_normalize_quality(value)` fail-closes: `None` → `"observed"` (preserves the
legacy optimistic default for genuinely-absent labels), a valid vocab string →
itself, and *anything else* → `"unavailable"` (pessimistic — a malformed label
is treated as "we cannot vouch for this", not as a silent pass). Normalize
untrusted enum-like values **before** using them as dict keys or in ranking.

## Pitfall: The Same Gap Exists at Every Parallel Site

`aggregation.py` and `report.py` each keep their **own** copy of `_QUALITY_RANK`
and their own quality-labelling function (`_field_quality` / `_quality`). Fixing
the malformed-label crash in `aggregation.py` (round 3) left the identical gap in
`report.py._quality` (round 5). When a normalization or safety fix lands in one
module, grep for parallel copies of the same helper in sibling modules and fix
them in the same shipment — a reviewer *will* find the second site otherwise, and
each miss costs another auto-triggered review round.

**Preserve deliberate asymmetry, though:** an *unlabeled populated* field
defaults to `"observed"` (optimistic) in `aggregation._field_quality` but
`"unavailable"` (pessimistic) in `report._quality`. That asymmetry is
contract-pinned and intentional; the round-5 fix normalized only the
*explicit-label* path in report, leaving the `None`-path asymmetry intact. Do not
"unify" the two sites into identical behavior just because they share a helper
name.

## Pitfall: Adding a Field to an Exported Frozen Dataclass Is a Breaking Change

`ConfigSummary` / `BaselineSummary` are `@dataclass(frozen=True)` and exported via
`autoharness.eval.__all__`. Adding a **required** field mid-class breaks every
external constructor call and reorders positional args. The compatible form:

- Make the new field optional: `derived_quality: dict[str, str] = field(default_factory=dict)`
  (needs `from dataclasses import dataclass, field`; never a mutable `{}` default).
- A field with a default must come **after** all non-default fields, so it goes
  **last**. Construction is keyword-based throughout, so the position change is
  safe for internal callers and additive for external ones.

Treat any new field on an exported dataclass as an API change: optional, with a
default, appended last.
