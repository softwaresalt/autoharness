"""Benchmark baseline/treatment run harness (085.002-T).

Deterministic executor that runs each :class:`~autoharness.eval.benchmark.
scenarios.Scenario` under two arms:

- ``baseline`` — routing OFF (raw read/grep): exhaustive, always-correct but
  expensive.
- ``treatment`` — Engram-first routing ON: cheaper, but its recall degrades
  under a ``cold`` or ``stale`` index-state precondition (this is the
  deterministic proxy for a real routed-lookup miss under a degraded index).

Each arm run emits exactly one :class:`~autoharness.telemetry.epoch.
ExecutionEpoch` through the shipped ``telemetry begin``/``telemetry record``
path (:func:`autoharness.telemetry.record.record_epoch`), correlated by a
synthetic ``backlog_item_id`` (== ``task_id`` per the v1.1 identity contract)
and ``phase`` (``benchmark-baseline`` / ``benchmark-treatment``).

**Sink isolation (review-fix R1c, mandatory invariant):** every benchmark run
targets an isolated :class:`~autoharness.telemetry.config.TelemetryConfig`
whose sink lives under a run-scoped ``benchmark/`` directory — **never** the
repository's authoritative ``.autoharness/metrics`` store — so benchmark
epochs can never pollute production telemetry aggregates.
:func:`isolated_benchmark_telemetry_config` refuses to build a config pointed
at the default production metrics path. Synthetic ``backlog_item_id`` /
``workspace_id`` values use a reserved ``benchmark:`` namespace prefix.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal

from autoharness.eval.benchmark.scenarios import Scenario
from autoharness.telemetry.config import DEFAULT_DATABASE_PATH, TelemetryConfig
from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
)
from autoharness.telemetry.record import RecordSummary, record_epoch

Arm = Literal["baseline", "treatment"]
ARMS: tuple[Arm, ...] = ("baseline", "treatment")

#: Reserved namespace prefix for every synthetic benchmark identity value
#: (backlog_item_id / task_id / workspace_id) — never a real backlog artifact id.
BENCHMARK_NAMESPACE_PREFIX = "benchmark:"

PHASE_BY_ARM: dict[Arm, str] = {
    "baseline": "benchmark-baseline",
    "treatment": "benchmark-treatment",
}


class BenchmarkHarnessError(ValueError):
    """Raised when the benchmark harness is misconfigured (e.g. sink escape)."""


def _default_metrics_root(workspace_root: Path) -> Path:
    return (workspace_root / DEFAULT_DATABASE_PATH).parent.resolve()


def _is_within(root: Path, candidate: Path) -> bool:
    """True when ``candidate`` resolves inside (or equals) ``root``."""
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return candidate == root


def isolated_benchmark_telemetry_config(
    sink_root: Path | str,
    *,
    workspace_root: Path | str | None = None,
    emit_jsonl: bool = True,
) -> TelemetryConfig:
    """Build a :class:`TelemetryConfig` confined to an isolated benchmark sink.

    Refuses (raises :class:`BenchmarkHarnessError`) to build a config whose
    resolved sink directory is, or lives under, the workspace's default
    authoritative metrics store (``.autoharness/metrics``) — the mandatory
    sink-isolation invariant. The check is containment-based (review-fix),
    not exact-match-only: a subdirectory of the production metrics root
    (e.g. ``.autoharness/metrics/subdir``) is rejected too, not just the
    exact production path itself.

    A relative ``sink_root`` resolves against ``workspace_root`` (review-fix:
    previously resolved against the process CWD regardless of
    ``workspace_root``, which was misleading given ``workspace_root`` is the
    documented resolution base). An absolute ``sink_root`` is honored as
    given. The sink is deliberately allowed to live **outside**
    ``workspace_root`` entirely (e.g. a dedicated temp directory, or a
    ``benchmark-runs/`` area outside the project workspace) — that is the
    isolation this function exists to provide, not a defect: the only
    location that is forbidden is the authoritative production metrics
    store (and its subdirectories) itself. Any other in-workspace-or-not
    directory dedicated to the benchmark run is accepted; callers are
    expected to pass a run-scoped ``benchmark/`` path (e.g. a temp directory
    or ``.autoharness/benchmark-runs/<run-id>``).
    """
    workspace = Path(workspace_root).resolve() if workspace_root is not None else Path.cwd().resolve()
    sink_root_path = Path(sink_root)
    root = sink_root_path if sink_root_path.is_absolute() else (workspace / sink_root_path)
    root = root.resolve()
    default_root = _default_metrics_root(workspace)
    if _is_within(default_root, root):
        raise BenchmarkHarnessError(
            f"Refusing to point the benchmark telemetry sink at (or under) the "
            f"authoritative production metrics store ({default_root}); pass a "
            "dedicated run-scoped benchmark sink directory instead (sink isolation, R1c)."
        )
    database_path = root / "execution_epochs.db"
    jsonl_path = root / "execution_epochs.jsonl"
    return TelemetryConfig(
        enabled=True,
        mode="sqlite",
        database_path=database_path,
        emit_jsonl=emit_jsonl,
        jsonl_path=jsonl_path,
    )



@dataclass(frozen=True)
class ArmOutcome:
    """The deterministic per-arm payload an executor produces.

    ``produced_answer`` is the arm's navigation result — graded by
    :mod:`autoharness.eval.benchmark.scorer` — and is **not** part of the
    telemetry contract; it travels alongside the epoch in :class:`ArmRun` for
    same-process scoring.
    """

    produced_answer: tuple[str, ...]
    economics: EconomicPayload
    operations: OperationalReality
    outcome: AbsoluteOutcome


ArmExecutor = Callable[[Scenario, Arm, int, int], ArmOutcome]


def _seeded_tokens(scenario: Scenario, arm: Arm, repeat_index: int, seed: int, *, base: int) -> int:
    """A small, deterministic-but-dispersed token count for repeat dispersion (085.005-T).

    Purely a hash of (scenario id, arm, repeat_index, seed) — never random, so
    identical inputs always reproduce identical outputs, but distinct repeats
    disperse (085.005-T acceptance: "repeated runs report dispersion").
    """
    key = f"{scenario.id}:{arm}:{repeat_index}:{seed}".encode("utf-8")
    digest = hashlib.sha256(key).digest()
    jitter = int.from_bytes(digest[:2], "big") % 64
    return base + jitter


def default_arm_executor(scenario: Scenario, arm: Arm, repeat_index: int, seed: int) -> ArmOutcome:
    """Deterministic default executor — no model or network call.

    Correctness proxy rule (documented, 008): the ``baseline`` arm is an
    exhaustive raw-read/grep oracle that always recalls the gold answer
    exactly, but at high token/tool cost. The ``treatment`` arm is a routed
    lookup that recalls exactly under a ``warm`` index, partially under
    ``stale`` (drops the last gold target), and misses entirely under
    ``cold`` (the degraded/cold-index case, H5) — all marked with
    ``metric_quality: estimated`` because these are synthesized, not observed,
    values (H4). This executor never measures ``context_area_tokens`` (it is
    left at the dataclass default of ``0``), so it is included in the
    estimated-quality label set too (review-fix): without an explicit label
    an unset-but-zero field reads as a legitimate ``observed`` zero-count
    rather than the unmeasured proxy it actually is, contradicting H4.
    """
    estimated_quality = {
        name: "estimated"
        for name in (
            "input_tokens",
            "output_tokens",
            "cogs_usd",
            "duration_seconds",
            "context_area_tokens",
            "avoided_read_estimated_tokens",
            "tool_output_estimated_tokens",
        )
    }

    if arm == "baseline":
        produced = scenario.gold_answer
        input_tokens = _seeded_tokens(scenario, arm, repeat_index, seed, base=4000)
        output_tokens = _seeded_tokens(scenario, arm, repeat_index, seed, base=300)
        baseline_op_fields = (
            "raw_file_read_count",
            "raw_search_count",
            "routed_lookup_count",
            "expected_tool_count",
            "observed_expected_tool_count",
            "missing_expected_tool_count",
        )
        operations = OperationalReality(
            cli_tools=("grep", "cat"),
            tool_surfaces=("filesystem",),
            raw_file_read_count=20,
            raw_search_count=5,
            routed_lookup_count=0,
            expected_tool_count=1,
            observed_tool_counts={"raw_read": 1},
            observed_expected_tool_count=1,
            missing_expected_tool_count=0,
            metric_sources={name: "estimated" for name in baseline_op_fields},
            metric_quality={name: "estimated" for name in baseline_op_fields},
        )
        degraded = 0
        stale_or_unavailable = 0
    else:
        is_cold = scenario.index_state == "cold"
        is_stale = scenario.index_state == "stale"
        if is_cold:
            produced = ()
            degraded = 1
            stale_or_unavailable = 1
        elif is_stale and len(scenario.gold_answer) > 1:
            produced = scenario.gold_answer[:-1]
            degraded = 0
            stale_or_unavailable = 1
        else:
            produced = scenario.gold_answer
            degraded = 0
            stale_or_unavailable = 0
        input_tokens = _seeded_tokens(scenario, arm, repeat_index, seed, base=400)
        output_tokens = _seeded_tokens(scenario, arm, repeat_index, seed, base=50)
        treatment_op_fields = (
            "raw_file_read_count",
            "raw_search_count",
            "routed_lookup_count",
            "expected_tool_count",
            "observed_expected_tool_count",
            "missing_expected_tool_count",
            "degraded_tool_count",
            "stale_or_unavailable_index_count",
        )
        operations = OperationalReality(
            cli_tools=("engram",),
            tool_surfaces=("engram",),
            raw_file_read_count=1 if not is_cold else 0,
            raw_search_count=0,
            routed_lookup_count=3,
            expected_tool_count=1,
            observed_tool_counts={"routed_lookup": 0 if is_cold else 1},
            observed_expected_tool_count=0 if is_cold else 1,
            missing_expected_tool_count=1 if is_cold else 0,
            degraded_tool_count=degraded,
            stale_or_unavailable_index_count=stale_or_unavailable,
            metric_sources={name: "estimated" for name in treatment_op_fields},
            metric_quality={name: "estimated" for name in treatment_op_fields},
        )

    avoided = _seeded_tokens(scenario, arm, repeat_index, seed, base=1200 if arm == "treatment" else 0)
    tool_output = _seeded_tokens(scenario, arm, repeat_index, seed, base=100)

    economics = EconomicPayload(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cogs_usd=round((input_tokens + output_tokens) * 0.000002, 6),
        duration_seconds=float(_seeded_tokens(scenario, arm, repeat_index, seed, base=2)),
        avoided_read_estimated_tokens=avoided if arm == "treatment" else 0,
        tool_output_estimated_tokens=tool_output,
        metric_sources=dict(estimated_quality),
        metric_quality=dict(estimated_quality),
    )
    outcome = AbsoluteOutcome(
        gate_exit_codes=(0,),
        tool_degraded_count=degraded,
    )
    return ArmOutcome(
        produced_answer=produced,
        economics=economics,
        operations=operations,
        outcome=outcome,
    )


@dataclass(frozen=True)
class ArmRun:
    """One arm's persisted epoch + record dispatch summary + produced answer."""

    scenario_id: str
    arm: Arm
    repeat_index: int
    backlog_item_id: str
    epoch: ExecutionEpoch
    record: RecordSummary
    produced_answer: tuple[str, ...]


@dataclass(frozen=True)
class RepeatRun:
    """A single repeat's correlated baseline + treatment :class:`ArmRun` pair."""

    scenario_id: str
    repeat_index: int
    baseline: ArmRun
    treatment: ArmRun

    @property
    def arm_runs(self) -> tuple[ArmRun, ArmRun]:
        return (self.baseline, self.treatment)


def _benchmark_backlog_item_id(scenario_id: str, repeat_index: int, arm: Arm) -> str:
    return f"{BENCHMARK_NAMESPACE_PREFIX}{scenario_id}:{repeat_index}:{arm}"


def run_scenario(
    scenario: Scenario,
    telemetry_config: TelemetryConfig,
    *,
    repeats: int = 1,
    seed: int = 0,
    executor: ArmExecutor = default_arm_executor,
    workspace_id: str | None = None,
) -> tuple[RepeatRun, ...]:
    """Run ``scenario`` under both arms for ``repeats`` repeats.

    Persists exactly **two correlated epochs per repeat** (one baseline + one
    treatment) — i.e. **2xN epochs total for N repeats** — each with a unique
    per-repeat epoch identity (the ``backlog_item_id``/``task_id`` embeds the
    repeat index, so repeats never overwrite or collapse before persistence;
    every repeat remains independently readable via
    :func:`~autoharness.telemetry.reader.read_epoch_records`). Arms are
    distinguishable by ``phase``.

    Raises:
        BenchmarkHarnessError: an enabled ``telemetry_config`` accepted an
            epoch write into neither its sqlite nor its jsonl sink
            (review-fix). :func:`~autoharness.telemetry.record.record_epoch`
            is deliberately fail-open at the sink layer and reports failures
            through :class:`~autoharness.telemetry.record.RecordSummary`
            rather than raising; without this check, a total sink failure
            would let ``run_scenario`` return a successful result with fewer
            than the promised 2xN epochs actually persisted.
    """
    if repeats < 1:
        raise BenchmarkHarnessError("repeats must be >= 1.")

    ws_id = workspace_id or f"{BENCHMARK_NAMESPACE_PREFIX}workspace"
    runs: list[RepeatRun] = []
    for repeat_index in range(repeats):
        arm_runs: dict[Arm, ArmRun] = {}
        for arm in ARMS:
            outcome = executor(scenario, arm, repeat_index, seed)
            backlog_item_id = _benchmark_backlog_item_id(scenario.id, repeat_index, arm)
            epoch = ExecutionEpoch(
                task_id=backlog_item_id,
                backlog_item_id=backlog_item_id,
                phase=PHASE_BY_ARM[arm],
                workspace_id=ws_id,
                route=RouteConfiguration(
                    models=("benchmark-deterministic-replay",),
                    route_kinds=(arm,),
                ),
                economics=outcome.economics,
                operations=outcome.operations,
                outcome=outcome.outcome,
            )
            summary = record_epoch(epoch, telemetry_config)
            if telemetry_config.enabled and not summary.sqlite_written and not summary.jsonl_written:
                # record_epoch is deliberately fail-open at the telemetry-sink
                # layer (a single sink failure never crashes a caller) and
                # reports the outcome through RecordSummary rather than
                # raising. The benchmark harness promises exactly 2xN
                # persisted epochs for N repeats (mandatory invariant); if
                # every configured sink rejected this epoch, continuing
                # silently would let the run report success with fewer than
                # 2xN epochs actually persisted. Fail closed here instead
                # (review-fix).
                raise BenchmarkHarnessError(
                    f"Benchmark epoch for {backlog_item_id!r} was not persisted by any "
                    f"configured sink (sqlite_status={summary.sqlite_status!r}, "
                    f"jsonl_status={summary.jsonl_status!r}); refusing to continue since the "
                    "2xN persisted-epochs invariant would be violated."
                )
            arm_runs[arm] = ArmRun(
                scenario_id=scenario.id,
                arm=arm,
                repeat_index=repeat_index,
                backlog_item_id=backlog_item_id,
                epoch=epoch,
                record=summary,
                produced_answer=outcome.produced_answer,
            )
        runs.append(
            RepeatRun(
                scenario_id=scenario.id,
                repeat_index=repeat_index,
                baseline=arm_runs["baseline"],
                treatment=arm_runs["treatment"],
            )
        )
    return tuple(runs)


def run_corpus(
    scenarios: tuple[Scenario, ...],
    telemetry_config: TelemetryConfig,
    *,
    repeats: int = 1,
    seed: int = 0,
    executor: ArmExecutor = default_arm_executor,
    workspace_id: str | None = None,
) -> dict[str, tuple[RepeatRun, ...]]:
    """Run every scenario in a corpus; returns per-scenario repeat runs, keyed by id."""
    return {
        scenario.id: run_scenario(
            scenario,
            telemetry_config,
            repeats=repeats,
            seed=seed,
            executor=executor,
            workspace_id=workspace_id,
        )
        for scenario in scenarios
    }
