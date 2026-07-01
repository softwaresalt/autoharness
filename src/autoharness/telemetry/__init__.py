"""Repo-local execution telemetry for autoharness (Phase 2 capture core).

This package owns the Execution Epoch schema and its local sinks (SQLite +
JSONL). It is deliberately decoupled from the ``gates/`` package and from the
install/tune modules (``verify_workspace``, ``schema_contracts``): telemetry is
observational and must evolve independently of gating (Plan Review P2-2).

Telemetry is fail-open. An absent or ``mode: none`` configuration disables all
emission and behaves exactly as an install without telemetry.
"""

from __future__ import annotations

from autoharness.telemetry.config import TelemetryConfig, load_telemetry_config
from autoharness.telemetry.epoch import (
    AbsoluteOutcome,
    EconomicPayload,
    ExecutionEpoch,
    OperationalReality,
    RouteConfiguration,
)

__all__ = [
    "AbsoluteOutcome",
    "EconomicPayload",
    "ExecutionEpoch",
    "OperationalReality",
    "RouteConfiguration",
    "TelemetryConfig",
    "load_telemetry_config",
]
