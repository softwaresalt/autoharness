"""Atomic pre_task_completion gate: discovery -> match -> run -> aggregate.

This module depends only on other ``gates.*`` modules. It MUST NOT import
install/tune modules (``verify_workspace``, ``schema_contracts``) so the gating
subsystem can evolve independently (Plan Review P2-2). Config loading and schema
resolution are performed by the CLI, which passes a parsed
:class:`~autoharness.gates.config.GatesConfig` in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from autoharness.gates.config import GatesConfig
from autoharness.gates.discovery import discover_modified_files
from autoharness.gates.match import filter_matching
from autoharness.gates.runner import GateResult, run_gate


@dataclass(frozen=True)
class GateCheckReport:
    """Aggregated result of running every matched gate over the modified files."""

    results: tuple[GateResult, ...] = ()
    matched_files: tuple[str, ...] = ()
    discovered_files: tuple[str, ...] = ()

    @property
    def failures(self) -> tuple[GateResult, ...]:
        return tuple(r for r in self.results if not r.passed)

    @property
    def blocked(self) -> bool:
        """True when ANY matched file failed its gate (atomic all-or-nothing)."""
        return bool(self.failures)


def run_gates(
    config: GatesConfig,
    modified_files: "list[str]",
    *,
    task_id: str | None = None,
    cwd: Path | None = None,
    case_sensitive: bool | None = None,
    run_fn: Callable[..., Any] | None = None,
) -> GateCheckReport:
    """Run every configured gate against each matching modified file."""
    results: list[GateResult] = []
    matched: list[str] = []
    for gate in config.validation_gates:
        for path in filter_matching(gate.pattern, list(modified_files), case_sensitive=case_sensitive):
            matched.append(path)
            results.append(run_gate(gate, path, task_id=task_id, cwd=cwd, run_fn=run_fn))
    return GateCheckReport(
        results=tuple(results),
        matched_files=tuple(dict.fromkeys(matched)),
        discovered_files=tuple(modified_files),
    )


def check(
    config: GatesConfig,
    base: str,
    head: str = "HEAD",
    *,
    task_id: str | None = None,
    cwd: Path | None = None,
    case_sensitive: bool | None = None,
    run_fn: Callable[..., Any] | None = None,
    discover: Callable[..., "list[str]"] | None = None,
) -> GateCheckReport:
    """Discover modified files then run gates. No gates ⇒ empty (passing) report."""
    if not config.enabled or not config.validation_gates:
        return GateCheckReport()
    discover_fn = discover or discover_modified_files
    files = discover_fn(base, head, cwd=cwd)
    return run_gates(
        config,
        files,
        task_id=task_id,
        cwd=cwd,
        case_sensitive=case_sensitive,
        run_fn=run_fn,
    )
