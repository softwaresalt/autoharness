"""Benchmark reproducibility controls + run manifest (085.005-T).

Reproducibility controls on the harness: pinned route capture (via the
existing eval frozen-state seam, :func:`autoharness.eval.runner.
resolve_frozen_state`), seed pinning, warm/cold/stale index-state
classification, ``ENGRAM_DEGRADED``-style capture
(``degraded_tool_count`` / ``stale_or_unavailable_index_count`` roll-ups),
N-repeat dispersion, and a :class:`RunManifest` recording
``workspace_id`` / ``commit_sha`` / corpus-hash / route / seed — plus the
**isolated benchmark sink path** (review-fix R1c) so a published result is
independently reproducible and provably sink-isolated.

Mandatory invariant (H5/R5): a degraded/cold-index treatment run is captured
and classified — **never dropped or treated as an error**. A scenario whose
treatment arm degraded under a cold/stale index is demoted from its nominal
``scenario_class`` to a ``negative``/``neutral`` **outcome classification**
for reporting purposes (an otherwise-``positive`` scenario that failed under
a cold index is a ``negative`` outcome, not a silently-dropped success).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean as _mean
from typing import Any

from autoharness.eval.benchmark.harness import (
    ARMS,
    Arm,
    ArmExecutor,
    BenchmarkHarnessError,
    RepeatRun,
    default_arm_executor,
    isolated_benchmark_telemetry_config,
    run_corpus,
)
from autoharness.eval.benchmark.scenarios import Scenario, ScenarioCorpus
from autoharness.eval.runner import FrozenState, resolve_frozen_state
from autoharness.telemetry.config import TelemetryConfig
from autoharness.telemetry.reader import read_epoch_records


def _outcome_classification(scenario: Scenario, *, degraded: bool) -> str:
    """The reporting-facing outcome class, demoted when the run degraded.

    A non-degraded run keeps its nominal ``scenario_class``. A degraded run
    (cold-index full miss, or any positive tool_degraded_count) demotes an
    otherwise-``positive`` scenario to ``negative`` (a real correctness
    failure, never a silent win) and keeps any other class at ``neutral`` at
    minimum — it is never promoted back to ``positive``.
    """
    if not degraded:
        return scenario.scenario_class
    return "negative" if scenario.scenario_class == "positive" else "neutral"


@dataclass(frozen=True)
class ScenarioClassification:
    """Per-scenario degraded-run capture and outcome classification."""

    scenario_id: str
    scenario_class: str
    index_state: str
    degraded: bool
    outcome_classification: str
    retained: bool = True  # H5/R5: a degraded/cold run is always retained, never dropped.

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_class": self.scenario_class,
            "index_state": self.index_state,
            "degraded": self.degraded,
            "outcome_classification": self.outcome_classification,
            "retained": self.retained,
        }


@dataclass(frozen=True)
class RepeatDispersion:
    """Repeat-to-repeat dispersion of one field for one scenario/arm."""

    scenario_id: str
    arm: Arm
    field: str
    values: tuple[float, ...]
    minimum: float
    maximum: float
    mean: float
    spread: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "arm": self.arm,
            "field": self.field,
            "values": list(self.values),
            "minimum": self.minimum,
            "maximum": self.maximum,
            "mean": self.mean,
            "spread": self.spread,
        }


def compute_dispersion(
    repeat_runs: tuple[RepeatRun, ...],
    *,
    arm: Arm,
    field_name: str = "input_tokens",
) -> RepeatDispersion:
    """Repeat-to-repeat dispersion of an economics field across ``repeat_runs``."""
    values = tuple(
        float(getattr((run.baseline if arm == "baseline" else run.treatment).epoch.economics, field_name))
        for run in repeat_runs
    )
    scenario_id = repeat_runs[0].scenario_id if repeat_runs else ""
    minimum = min(values) if values else 0.0
    maximum = max(values) if values else 0.0
    return RepeatDispersion(
        scenario_id=scenario_id,
        arm=arm,
        field=field_name,
        values=values,
        minimum=minimum,
        maximum=maximum,
        mean=_mean(values) if values else 0.0,
        spread=maximum - minimum,
    )


def classify_scenario_runs(scenario: Scenario, repeat_runs: tuple[RepeatRun, ...]) -> ScenarioClassification:
    """Classify one scenario's repeat runs, capturing any degraded treatment run."""
    degraded = any(run.treatment.epoch.operations.degraded_tool_count > 0 for run in repeat_runs)
    return ScenarioClassification(
        scenario_id=scenario.id,
        scenario_class=scenario.scenario_class,
        index_state=scenario.index_state,
        degraded=degraded,
        outcome_classification=_outcome_classification(scenario, degraded=degraded),
    )


@dataclass(frozen=True)
class RunManifest:
    """A reproducible record of one benchmark run's controls."""

    workspace_id: str
    commit_sha: str | None
    corpus_hash: str
    route: tuple[str, ...]
    seed: int
    repeats: int
    sink_database_path: str
    sink_jsonl_path: str | None
    degraded_tool_count_total: int
    stale_or_unavailable_index_count_total: int
    scenario_classifications: tuple[ScenarioClassification, ...] = field(default_factory=tuple)
    dispersion: tuple[RepeatDispersion, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "commit_sha": self.commit_sha,
            "corpus_hash": self.corpus_hash,
            "route": list(self.route),
            "seed": self.seed,
            "repeats": self.repeats,
            "sink_database_path": self.sink_database_path,
            "sink_jsonl_path": self.sink_jsonl_path,
            "degraded_tool_count_total": self.degraded_tool_count_total,
            "stale_or_unavailable_index_count_total": self.stale_or_unavailable_index_count_total,
            "scenario_classifications": [c.to_dict() for c in self.scenario_classifications],
            "dispersion": [d.to_dict() for d in self.dispersion],
        }


DEFAULT_ROUTE: tuple[str, ...] = ("benchmark-deterministic-replay",)
DEFAULT_WORKSPACE_ID = "benchmark:workspace"


def run_benchmark(
    corpus: ScenarioCorpus,
    sink_root: Path | str,
    *,
    repeats: int = 3,
    seed: int = 0,
    workspace_id: str | None = None,
    workspace_root: Path | str | None = None,
    executor: ArmExecutor = default_arm_executor,
) -> tuple[dict[str, tuple[RepeatRun, ...]], RunManifest]:
    """Run every scenario in ``corpus`` and produce a reproducible :class:`RunManifest`.

    Pins the route (``DEFAULT_ROUTE`` — the harness's deterministic-replay
    identity) and the seed, resolves the frozen ``commit_sha`` via the
    existing eval frozen-state seam (never raises; ``None`` when git is
    unavailable), and builds the isolated benchmark telemetry sink via
    :func:`~autoharness.eval.benchmark.harness.isolated_benchmark_telemetry_config`.

    Raises:
        BenchmarkHarnessError: ``sink_root`` already holds epoch records from
            a prior run (see the "reject a reused sink" note below), or
            ``sink_root`` resolves to the authoritative production metrics
            store (sink isolation, raised by
            :func:`isolated_benchmark_telemetry_config`).

    ``sink_root`` MUST be fresh (no pre-existing epoch records) for every
    call — this run's manifest fields (``repeats``, degraded/stale totals,
    dispersion) are only valid for the records this specific invocation
    writes, and reusing a sink would let them silently accumulate across
    runs while the manifest keeps reporting only the current call's
    ``repeats`` (a reproducibility integrity gap). Pass a distinct,
    run-scoped directory per call (e.g. a fresh temp directory or a
    UUID-suffixed path).
    """
    workspace_root_path = Path(workspace_root).resolve() if workspace_root is not None else Path.cwd().resolve()
    telemetry_config: TelemetryConfig = isolated_benchmark_telemetry_config(
        sink_root, workspace_root=workspace_root_path
    )

    # Reject a reused, non-empty sink (review-fix): run_benchmark's manifest
    # (repeats, degraded/stale totals, dispersion) is only valid for the
    # records this specific invocation writes. Appending to a sink that
    # already holds epochs from a prior run would let a later
    # read_epoch_records/metrics/reporting pass silently aggregate both runs
    # together while the manifest still reports only the current run's
    # `repeats` — a reproducibility integrity gap. Every run_benchmark call
    # therefore requires a fresh, empty sink_root; callers must pass a
    # distinct run-scoped directory (e.g. a temp dir or a UUID-suffixed path)
    # per run.
    existing = read_epoch_records(telemetry_config)
    if existing.status == "ok" and existing.records:
        raise BenchmarkHarnessError(
            f"Refusing to run into a non-empty benchmark sink ({telemetry_config.database_path}); "
            f"it already holds {len(existing.records)} epoch record(s) from a prior run. Pass a "
            "fresh, run-scoped sink_root so this run's manifest (repeats, degraded/stale totals, "
            "dispersion) stays valid for exactly the records this invocation writes."
        )

    resolved = resolve_frozen_state(FrozenState(base="HEAD", head="HEAD"), cwd=workspace_root_path)
    commit_sha = resolved.resolved_sha if resolved is not None else None
    ws_id = workspace_id or DEFAULT_WORKSPACE_ID

    results = run_corpus(
        corpus.scenarios,
        telemetry_config,
        repeats=repeats,
        seed=seed,
        executor=executor,
        workspace_id=ws_id,
    )

    degraded_total = sum(
        run.treatment.epoch.operations.degraded_tool_count
        for repeat_runs in results.values()
        for run in repeat_runs
    )
    stale_total = sum(
        run.treatment.epoch.operations.stale_or_unavailable_index_count
        for repeat_runs in results.values()
        for run in repeat_runs
    )
    classifications = tuple(
        classify_scenario_runs(scenario, results[scenario.id]) for scenario in corpus.scenarios
    )
    dispersion = tuple(
        compute_dispersion(results[scenario.id], arm=arm)
        for scenario in corpus.scenarios
        for arm in ARMS
        if repeats > 1
    )

    manifest = RunManifest(
        workspace_id=ws_id,
        commit_sha=commit_sha,
        corpus_hash=corpus.manifest_hash,
        route=DEFAULT_ROUTE,
        seed=seed,
        repeats=repeats,
        sink_database_path=str(telemetry_config.database_path),
        sink_jsonl_path=str(telemetry_config.jsonl_path) if telemetry_config.jsonl_path else None,
        degraded_tool_count_total=degraded_total,
        stale_or_unavailable_index_count_total=stale_total,
        scenario_classifications=classifications,
        dispersion=dispersion,
    )
    return results, manifest
