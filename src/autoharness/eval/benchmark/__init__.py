"""Structural-navigation benchmark suite (085-F, deterministic core).

An **additive** layer over the existing ``autoharness.eval`` A/B harness and the
shipped telemetry read/report/aggregation APIs (ExecutionEpoch v1.1 /
ToolTelemetryEvent v1.0). This package delivers the *deterministic replay*
benchmark core end to end:

- :mod:`autoharness.eval.benchmark.scenarios` — scenario corpus model + loader
- :mod:`autoharness.eval.benchmark.harness` — baseline/treatment run harness
- :mod:`autoharness.eval.benchmark.scorer` — correctness scorer
- :mod:`autoharness.eval.benchmark.metrics` — telemetry A/B delta adapter
- :mod:`autoharness.eval.benchmark.controls` — reproducibility controls + run manifest
- :mod:`autoharness.eval.benchmark.reporting` — honest reporting renderer

**Live-run mode is out of scope.** No task in this package implements or verifies
a callable live-agent path; it remains a documented, off-by-default, additive
extension point (see ``docs/benchmark-suite-methodology.md``).

**No telemetry-contract, schema, or CLI-distribution change.** Every module here
consumes the shipped telemetry/eval APIs read-only.
"""

from __future__ import annotations
