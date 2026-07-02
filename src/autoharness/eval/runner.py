"""Eval frozen-state execution loop (Phase 2, U8 sub-unit, task 055.005-T).

Executes the matrix-loaded eval runs against a frozen git state and persists one
comparable :class:`~autoharness.telemetry.epoch.ExecutionEpoch` per model config
through the shipped telemetry sink(s).

**No live models.** The run outcome for each config is produced by an
**injectable, pluggable runner** (:data:`RunnerFn`). The default
:func:`replay_runner` replays each config's recorded ``baseline`` block — it
performs no model or network call, so runs are fully deterministic and hermetic.
A real harness runtime can inject a runner that supplies live economics.

The frozen state is pinned once (via ``git rev-parse``) so every config is
evaluated against the identical git state, keeping the emitted epochs directly
comparable. State resolution degrades gracefully (``resolved_sha=None``) when
git is unavailable and never raises.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from autoharness.eval.matrix import EvalMatrix, FrozenState, ModelConfig
from autoharness.telemetry.config import TelemetryConfig
from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
)
from autoharness.telemetry.record import RecordSummary, record_epoch

DEFAULT_TASK_ID_PREFIX = "eval"

# A git runner takes an argv list + cwd and returns (returncode, stdout, stderr),
# mirroring the injectable pattern used by autoharness.gates.discovery so tests
# stay hermetic without importing that module.
GitRunner = Callable[[list[str], "Path | None"], "tuple[int, str, str]"]


@dataclass(frozen=True)
class EvalRunOutcome:
    """The deterministic per-config run payloads a runner produces.

    ``route`` is supplied by the loop from the config's models; a runner only
    reports the economic, operational, and outcome payloads.
    """

    economics: EconomicPayload
    operations: OperationalReality
    outcome: AbsoluteOutcome


@dataclass(frozen=True)
class ResolvedFrozenState:
    """The frozen git state pinned for a run (``resolved_sha`` may be None)."""

    base: str
    head: str
    resolved_sha: str | None


@dataclass(frozen=True)
class EvalRun:
    """A single config's run: its epoch plus the sink dispatch summary."""

    config_name: str
    epoch: ExecutionEpoch
    record: RecordSummary


@dataclass(frozen=True)
class EvalRunReport:
    """The outcome of running the full matrix against one frozen state."""

    frozen_state: ResolvedFrozenState | None
    runs: tuple[EvalRun, ...]

    @property
    def epochs(self) -> tuple[ExecutionEpoch, ...]:
        return tuple(run.epoch for run in self.runs)


# ---------------------------------------------------------------------------
# Runner interface
# ---------------------------------------------------------------------------

RunnerFn = Callable[[ModelConfig, "ResolvedFrozenState | None"], EvalRunOutcome]


def replay_runner(config: ModelConfig, frozen: ResolvedFrozenState | None) -> EvalRunOutcome:
    """Default runner — replay a config's recorded ``baseline`` (no model call).

    An absent baseline yields a zero-valued outcome, which is the honest
    "measured nothing" baseline for a config that has no recorded run yet.
    """
    baseline = dict(config.baseline) if config.baseline else {}
    return EvalRunOutcome(
        economics=EconomicPayload.from_mapping(baseline.get("economics", {})),
        operations=OperationalReality.from_mapping(baseline.get("operations", {})),
        outcome=AbsoluteOutcome.from_mapping(baseline.get("outcome", {})),
    )


def _default_git_runner(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
    proc = subprocess.run(
        argv,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _rev_parse(ref: str, *, cwd: Path | None, runner: GitRunner) -> str | None:
    """Return the pinned SHA for ``ref`` or None when git is unavailable."""
    try:
        returncode, stdout, _stderr = runner(["git", "rev-parse", ref], cwd)
    except (FileNotFoundError, OSError):
        return None
    if returncode != 0:
        return None
    sha = stdout.strip()
    return sha or None


def resolve_frozen_state(
    frozen: FrozenState | None,
    *,
    base_override: str | None = None,
    head_override: str | None = None,
    cwd: Path | None = None,
    git_runner: GitRunner | None = None,
) -> ResolvedFrozenState | None:
    """Pin the frozen git state for a run, degrading gracefully.

    Returns None when no base can be determined (from the matrix or an
    override). Otherwise resolves ``head`` to a concrete SHA when git is
    available; ``resolved_sha`` is None when it is not. Never raises.
    """
    base = base_override or (frozen.base if frozen else None)
    if not base:
        return None
    head = head_override or (frozen.head if frozen else None) or "HEAD"
    runner = git_runner or _default_git_runner
    sha = _rev_parse(head, cwd=cwd, runner=runner)
    return ResolvedFrozenState(base=base, head=head, resolved_sha=sha)


def run_matrix(
    matrix: EvalMatrix,
    telemetry_config: TelemetryConfig,
    *,
    runner: RunnerFn = replay_runner,
    base_override: str | None = None,
    head_override: str | None = None,
    cwd: Path | None = None,
    git_runner: GitRunner | None = None,
    task_id_prefix: str = DEFAULT_TASK_ID_PREFIX,
) -> EvalRunReport:
    """Execute every config against the frozen state; persist one epoch each.

    Persistence goes through :func:`~autoharness.telemetry.record.record_epoch`,
    which is fail-open and a no-op when telemetry is disabled. The runs are
    always returned regardless of sink state.
    """
    frozen = resolve_frozen_state(
        matrix.frozen_state,
        base_override=base_override,
        head_override=head_override,
        cwd=cwd,
        git_runner=git_runner,
    )

    runs: list[EvalRun] = []
    for config in matrix.configs:
        outcome = runner(config, frozen)
        epoch = ExecutionEpoch(
            task_id=f"{task_id_prefix}:{config.name}",
            route=RouteConfiguration(models=config.models),
            economics=outcome.economics,
            operations=outcome.operations,
            outcome=outcome.outcome,
        )
        summary = record_epoch(epoch, telemetry_config)
        runs.append(EvalRun(config_name=config.name, epoch=epoch, record=summary))

    return EvalRunReport(frozen_state=frozen, runs=tuple(runs))
