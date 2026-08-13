"""Sidecar lifecycle/preflight service (120.002-T).

Runs the two derived-index-maintenance sidecar invocations that
``start.ps1``/``start.sh`` currently perform inline before launching the
Copilot CLI:

* ``backlogit sync`` -- when ``backlogit`` is resolvable on PATH.
* Engram pre-warm -- a DIRECT sync first (``engram --format text sync
  --timeout 300 --direct``), with a DAEMON bind+sync FALLBACK on failure
  (``engram --format text bind`` then ``engram --format text sync
  --timeout 300``), mirroring ``start.ps1``'s
  ``Invoke-EngramCommandWithProgress`` helper's fallback sequence.

Every sidecar's absence or failure is ALWAYS non-fatal: this module never
raises for a sidecar being absent or failing. Each sidecar always produces
a per-sidecar outcome ("ok" | "degraded" | "unavailable") plus a warning on
anything other than "ok" -- never silently swallowed. A degraded/unavailable
outcome is purely DATA in the returned :class:`SidecarReport`; it is never
reflected as this function's own exception or as any implicit "failed"
status of its own.

This module performs NO backlog-artifact mutation (no add/move/archive/
checkpoint calls) and NO Engram authority writes -- ``backlogit sync`` and
``engram sync``/``engram bind`` are explicitly permitted derived-index
maintenance, and nothing else is invoked here. Every subprocess call uses
an argv array with an absolute path resolved via ``shutil.which`` --
NEVER ``shell=True``, and never a bare command name relying on implicit
shell PATH search.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

#: Closed, exhaustive set of per-sidecar outcome strings.
OUTCOMES = frozenset({"ok", "degraded", "unavailable"})

_ENGRAM_TIMEOUT_SECONDS = "300"


@dataclass(frozen=True)
class SidecarReport:
    """Typed, frozen outcome of :func:`run_sidecars`.

    Attributes:
        outcomes: Per-sidecar outcome mapping, e.g.
            ``{"backlogit": "ok", "engram": "degraded"}``. Every value is
            one of :data:`OUTCOMES`.
        warnings: Human-readable non-fatal warnings, in emission order.
    """

    outcomes: Mapping[str, str] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


def _run(argv: list[str], timeout: float = 300.0) -> subprocess.CompletedProcess:
    """Run ``argv`` (already an absolute-path-first argv list). Never shell=True."""

    return subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
    )


def _run_backlogit(backlogit_executable: str) -> tuple[str, list[str]]:
    """Run ``backlogit sync``. Returns ``(outcome, warnings)``."""

    resolved = shutil.which(backlogit_executable)
    if resolved is None:
        return "unavailable", [f"{backlogit_executable!r} not found on PATH; backlogit sync skipped"]

    try:
        proc = _run([resolved, "sync"])
    except (OSError, subprocess.SubprocessError) as exc:
        return "degraded", [f"backlogit sync failed ({type(exc).__name__}); non-fatal"]

    if proc.returncode != 0:
        return "degraded", [f"backlogit sync exited {proc.returncode}; non-fatal"]

    return "ok", []


def _run_engram(engram_executable: str) -> tuple[str, list[str]]:
    """Run the Engram direct-sync-first-with-daemon-fallback sequence.

    Returns ``(outcome, warnings)``. Mirrors start.ps1's
    ``Invoke-EngramCommandWithProgress`` fallback: direct sync first; on
    failure, bind then a daemon-backed sync retry; on that also failing,
    degrade non-fatally.
    """

    resolved = shutil.which(engram_executable)
    if resolved is None:
        return "unavailable", [f"{engram_executable!r} not found on PATH; Engram pre-warm skipped"]

    try:
        direct = _run(
            [resolved, "--format", "text", "sync", "--timeout", _ENGRAM_TIMEOUT_SECONDS, "--direct"]
        )
    except (OSError, subprocess.SubprocessError) as exc:
        direct = None
        direct_error = f"{type(exc).__name__}"
    else:
        direct_error = None

    if direct is not None and direct.returncode == 0:
        return "ok", []

    # Direct sync failed (either raised or returned non-zero): fall back to
    # daemon bind + sync, mirroring start.ps1's fallback path.
    try:
        bind = _run([resolved, "--format", "text", "bind"])
    except (OSError, subprocess.SubprocessError) as exc:
        bind = None
        bind_error = f"{type(exc).__name__}"
    else:
        bind_error = None

    try:
        daemon_sync = _run([resolved, "--format", "text", "sync", "--timeout", _ENGRAM_TIMEOUT_SECONDS])
    except (OSError, subprocess.SubprocessError) as exc:
        daemon_sync = None
        daemon_sync_error = f"{type(exc).__name__}"
    else:
        daemon_sync_error = None

    if daemon_sync is not None and daemon_sync.returncode == 0 and (bind is None or bind.returncode == 0):
        return "ok", [
            "Engram direct pre-warm failed; recovered via daemon bind+sync fallback"
        ]

    detail = direct_error or (f"exit {direct.returncode}" if direct is not None else "unknown")
    return "degraded", [f"Engram pre-warm failed ({detail}); non-fatal"]


def run_sidecars(
    workspace_root: Path,
    *,
    backlogit_executable: str = "backlogit",
    engram_executable: str = "engram",
) -> SidecarReport:
    """Run the backlogit-sync and Engram-pre-warm sidecar checks.

    ``workspace_root`` is accepted for interface symmetry/future use (e.g.
    a sidecar that needs to run with ``cwd=workspace_root``) but is not
    otherwise inspected by this function today.

    FAILURE IS NON-FATAL: this function never raises for a sidecar being
    absent or failing. Every subprocess call is wrapped so an unexpected
    exception degrades that sidecar's outcome rather than propagating.
    """

    _ = Path(workspace_root)  # symmetry/future cwd use; not otherwise inspected.

    outcomes: dict[str, str] = {}
    warnings: list[str] = []

    try:
        backlogit_outcome, backlogit_warnings = _run_backlogit(backlogit_executable)
    except Exception as exc:  # pragma: no cover - defensive: never let a sidecar raise
        backlogit_outcome, backlogit_warnings = "degraded", [
            f"backlogit sidecar raised unexpectedly ({type(exc).__name__}); non-fatal"
        ]
    outcomes["backlogit"] = backlogit_outcome
    warnings.extend(backlogit_warnings)

    try:
        engram_outcome, engram_warnings = _run_engram(engram_executable)
    except Exception as exc:  # pragma: no cover - defensive: never let a sidecar raise
        engram_outcome, engram_warnings = "degraded", [
            f"engram sidecar raised unexpectedly ({type(exc).__name__}); non-fatal"
        ]
    outcomes["engram"] = engram_outcome
    warnings.extend(engram_warnings)

    return SidecarReport(outcomes=outcomes, warnings=tuple(warnings))
