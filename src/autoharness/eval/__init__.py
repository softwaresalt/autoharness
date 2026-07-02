"""Headless evaluation for autoharness (Phase 2, Shipment B).

This package owns the ``autoharness eval`` capability: loading an eval
model-configuration matrix, executing comparable frozen-state baseline runs
through an **injectable, pluggable runner** (never a live model), running a
**deterministic rule-based reviewer matrix** over a git diff, and summarizing
comparable baseline metrics across configs.

Design constraints (see docs/plans/2026-07-01-telemetry-eval-phase2-plan.md):

* **No live LLM / network calls.** autoharness has no in-process model runtime.
  The runner interface is injectable so runs are fully deterministic and
  hermetic; the default CLI runner replays recorded baseline data.
* **Emit-only telemetry.** Epochs are persisted through the shipped
  ``autoharness.telemetry`` ExecutionEpoch model + SQLite/JSONL sinks. This
  package depends on ``telemetry`` in one direction only; ``telemetry`` never
  imports ``eval``.
* **Deterministic reviewer.** The reviewer is a seeded/pinned rule-based grader,
  not a model call; every penalty carries a line-number citation.
"""

from __future__ import annotations

from autoharness.eval.matrix import (
    EvalMatrix,
    EvalMatrixError,
    FrozenState,
    ModelConfig,
    load_matrix,
    load_matrix_file,
)
from autoharness.eval.reviewer import (
    AddedLine,
    DimensionScore,
    Penalty,
    ReviewMatrixResult,
    parse_unified_diff,
    review_diff,
    review_git_diff,
)
from autoharness.eval.runner import (
    EvalRun,
    EvalRunOutcome,
    EvalRunReport,
    ResolvedFrozenState,
    replay_runner,
    resolve_frozen_state,
    run_matrix,
)
from autoharness.eval.summary import (
    BaselineSummary,
    ConfigSummary,
    summarize_baseline,
)

__all__ = [
    # matrix
    "EvalMatrix",
    "EvalMatrixError",
    "FrozenState",
    "ModelConfig",
    "load_matrix",
    "load_matrix_file",
    # runner
    "EvalRun",
    "EvalRunOutcome",
    "EvalRunReport",
    "ResolvedFrozenState",
    "replay_runner",
    "resolve_frozen_state",
    "run_matrix",
    # reviewer
    "AddedLine",
    "DimensionScore",
    "Penalty",
    "ReviewMatrixResult",
    "parse_unified_diff",
    "review_diff",
    "review_git_diff",
    # summary
    "BaselineSummary",
    "ConfigSummary",
    "summarize_baseline",
]
