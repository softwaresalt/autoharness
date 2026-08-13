"""Sidecar lifecycle/preflight service (120.002-T).

Runs the THREE derived-index-maintenance sidecar invocations that
``start.ps1``/``start.sh`` historically performed (or, for graphtor-docs,
should have performed alongside them -- see the 120-F runtime-defect
remediation note below) inline before launching the Copilot CLI:

* ``backlogit sync`` -- when ``backlogit`` is resolvable on PATH.
* Engram pre-warm -- a DIRECT sync first (``engram --format text sync
  --timeout 300 --direct``), with a DAEMON bind+sync FALLBACK on failure
  (``engram --format text bind`` then ``engram --format text sync
  --timeout 300``), mirroring ``start.ps1``'s
  ``Invoke-EngramCommandWithProgress`` helper's fallback sequence.
* ``graphtor-docs sync`` -- when ``graphtor-docs`` is resolvable on PATH,
  or (mirroring ``scripts/deploy-harness.ps1``'s ``Get-PackDetectionStatus``
  workspace-local fallback) at ``<workspace_root>/.graphtor/bin/``.

120-F RUNTIME-DEFECT REMEDIATION (operator-reported, 2026-08-13): a real
launch showed Copilot reaching the child-spawn phase with NEITHER Engram
NOR graphtor-docs ever becoming a live process. The ROOT CAUSE was NOT
this module: it was the repository's own root ``.mcp.json``, which set
``ENGRAM_WORKSPACE``/``GRAPHTOR_DB_PATH``/``GRAPHTOR_SOURCES`` to the
literal, UNSUBSTITUTED string ``${workspaceFolder}`` -- a VS-Code-only
editor variable that the standalone ``copilot`` CLI does not resolve (
verified empirically: ``copilot mcp get engram --json`` echoes the raw
``${workspaceFolder}`` string back verbatim, and both ``engram shim`` and
``graphtor-docs serve`` crash immediately when handed that literal path).
That config-level defect is fixed directly in ``.mcp.json`` (the broken
env overrides are removed; every affected tool already defaults correctly
to the current working directory when the variable is unset). This
module's own, COMPLEMENTARY contribution to the fix is CWD-independence:
every subprocess invocation below now runs with ``cwd`` explicitly anchored
to ``workspace_root`` (previously accepted only "for interface
symmetry/future use" and never actually applied), and
:mod:`autoharness.supervise.app`/:mod:`autoharness.supervise.process`/
:mod:`autoharness.supervise.process_pty` anchor the SPAWNED COPILOT CHILD's
own cwd the same way -- so that once ``.mcp.json``'s broken override is
gone, the CWD-relative defaults Engram/graphtor-docs fall back to resolve
against the real workspace regardless of the invoking shell's own cwd.
graphtor-docs's ``serve`` MCP stdio process itself is spawned BY COPILOT
(per ``.mcp.json``), never by this module -- exactly like Engram's own
``shim``/``serve`` process. This module's ``graphtor-docs`` entry performs
ONLY the one-shot ``sync`` index-prewarm step, mirroring backlogit/Engram.

Every sidecar's absence or failure is ALWAYS non-fatal: this module never
raises for a sidecar being absent or failing. Each sidecar always produces
a per-sidecar outcome ("ok" | "degraded" | "unavailable") plus a warning on
anything other than "ok" -- never silently swallowed. A degraded/unavailable
outcome is purely DATA in the returned :class:`SidecarReport`; it is never
reflected as this function's own exception or as any implicit "failed"
status of its own.

This module performs NO backlog-artifact mutation (no add/move/archive/
checkpoint calls) and NO Engram/graphtor-docs authority writes -- ``backlogit
sync``, ``engram sync``/``engram bind``, and ``graphtor-docs sync`` are
explicitly permitted derived-index maintenance (F20/H6 ruling), and nothing
else is invoked here. Every subprocess call uses an argv array with an
absolute path resolved via ``shutil.which`` (or, for graphtor-docs, the
documented workspace-local fallback) -- NEVER ``shell=True``, and never a
bare command name relying on implicit shell PATH search.
"""


from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional

#: Closed, exhaustive set of per-sidecar outcome strings.
OUTCOMES = frozenset({"ok", "degraded", "unavailable"})

_ENGRAM_TIMEOUT_SECONDS = "300"

#: Workspace-local fallback candidate names for graphtor-docs, mirroring
#: scripts/deploy-harness.ps1's Get-PackDetectionStatus (graphtor-docs may
#: be installed at .graphtor/bin/ without being on PATH).
_GRAPHTOR_DOCS_LOCAL_CANDIDATES: tuple[str, ...] = ("graphtor-docs.exe", "graphtor-docs")


@dataclass(frozen=True)
class SidecarReport:
    """Typed, frozen outcome of :func:`run_sidecars`.

    Attributes:
        outcomes: Per-sidecar outcome mapping, e.g.
            ``{"backlogit": "ok", "engram": "degraded",
            "graphtor-docs": "ok"}``. Every value is one of
            :data:`OUTCOMES`.
        warnings: Human-readable non-fatal warnings, in emission order.
    """

    outcomes: Mapping[str, str] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


def _run(
    argv: list[str], timeout: float = 300.0, *, cwd: Optional[str] = None
) -> subprocess.CompletedProcess:
    """Run ``argv`` (already an absolute-path-first argv list). Never shell=True.

    ``cwd`` anchors the subprocess to the resolved workspace root (120-F
    runtime-defect remediation) rather than leaving it to inherit whatever
    directory the supervisor's own Python process happened to have as its
    cwd.
    """

    return subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=False,
        cwd=cwd,
    )


def _run_backlogit(backlogit_executable: str, cwd: Optional[str] = None) -> tuple[str, list[str]]:
    """Run ``backlogit sync``. Returns ``(outcome, warnings)``."""

    resolved = shutil.which(backlogit_executable)
    if resolved is None:
        return "unavailable", [f"{backlogit_executable!r} not found on PATH; backlogit sync skipped"]

    try:
        proc = _run([resolved, "sync"], cwd=cwd)
    except (OSError, subprocess.SubprocessError) as exc:
        return "degraded", [f"backlogit sync failed ({type(exc).__name__}); non-fatal"]

    if proc.returncode != 0:
        return "degraded", [f"backlogit sync exited {proc.returncode}; non-fatal"]

    return "ok", []


def _resolve_graphtor_docs_executable(
    graphtor_docs_executable: str, workspace_root: Path
) -> Optional[str]:
    """Resolve graphtor-docs: PATH first, then workspace-local ``.graphtor/bin/``.

    Mirrors ``scripts/deploy-harness.ps1``'s workspace-local fallback
    pattern for graphtor-docs -- installations that are not on PATH but are
    present at ``<workspace_root>/.graphtor/bin/graphtor-docs(.exe)`` are
    still discovered, without ever writing outside the workspace or
    inventing a path that does not actually exist on disk.
    """

    resolved = shutil.which(graphtor_docs_executable)
    if resolved is not None:
        return resolved

    local_bin = Path(workspace_root) / ".graphtor" / "bin"
    for candidate_name in _GRAPHTOR_DOCS_LOCAL_CANDIDATES:
        candidate = local_bin / candidate_name
        if candidate.is_file():
            return str(candidate)

    return None


def _run_graphtor_docs(
    graphtor_docs_executable: str, workspace_root: Path, cwd: Optional[str] = None
) -> tuple[str, list[str]]:
    """Run ``graphtor-docs sync``. Returns ``(outcome, warnings)``.

    Only the one-shot index-prewarm ``sync`` subcommand is invoked here --
    never ``serve`` (the persistent MCP stdio server, which Copilot itself
    spawns per ``.mcp.json``, exactly like Engram's ``shim``/``serve``).
    Mirrors ``_run_backlogit``/``_run_engram``'s non-fatal-on-failure
    contract precisely.
    """

    resolved = _resolve_graphtor_docs_executable(graphtor_docs_executable, workspace_root)
    if resolved is None:
        return "unavailable", [
            f"{graphtor_docs_executable!r} not found on PATH or workspace-local "
            ".graphtor/bin/; graphtor-docs sync skipped"
        ]

    try:
        proc = _run([resolved, "sync"], cwd=cwd)
    except (OSError, subprocess.SubprocessError) as exc:
        return "degraded", [f"graphtor-docs sync failed ({type(exc).__name__}); non-fatal"]

    if proc.returncode != 0:
        return "degraded", [f"graphtor-docs sync exited {proc.returncode}; non-fatal"]

    return "ok", []


def _run_engram(engram_executable: str, cwd: Optional[str] = None) -> tuple[str, list[str]]:
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
            [resolved, "--format", "text", "sync", "--timeout", _ENGRAM_TIMEOUT_SECONDS, "--direct"],
            cwd=cwd,
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
        bind = _run([resolved, "--format", "text", "bind"], cwd=cwd)
    except (OSError, subprocess.SubprocessError) as exc:
        bind = None
        bind_error = f"{type(exc).__name__}"
    else:
        bind_error = None

    try:
        daemon_sync = _run(
            [resolved, "--format", "text", "sync", "--timeout", _ENGRAM_TIMEOUT_SECONDS], cwd=cwd
        )
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
    graphtor_docs_executable: str = "graphtor-docs",
) -> SidecarReport:
    """Run the backlogit-sync, Engram-pre-warm, and graphtor-docs-sync sidecar checks.

    ``workspace_root`` is now ACTIVELY used: every subprocess invocation
    below is anchored with ``cwd=str(workspace_root)`` (120-F runtime-defect
    remediation -- previously accepted only "for interface symmetry/future
    use" and never actually applied), and it is also the base directory
    consulted for graphtor-docs's workspace-local ``.graphtor/bin/``
    fallback resolution.

    FAILURE IS NON-FATAL: this function never raises for a sidecar being
    absent or failing. Every subprocess call is wrapped so an unexpected
    exception degrades that sidecar's outcome rather than propagating.
    """

    resolved_workspace_root = Path(workspace_root)
    cwd = str(resolved_workspace_root)

    outcomes: dict[str, str] = {}
    warnings: list[str] = []

    try:
        backlogit_outcome, backlogit_warnings = _run_backlogit(backlogit_executable, cwd=cwd)
    except Exception as exc:  # pragma: no cover - defensive: never let a sidecar raise
        backlogit_outcome, backlogit_warnings = "degraded", [
            f"backlogit sidecar raised unexpectedly ({type(exc).__name__}); non-fatal"
        ]
    outcomes["backlogit"] = backlogit_outcome
    warnings.extend(backlogit_warnings)

    try:
        engram_outcome, engram_warnings = _run_engram(engram_executable, cwd=cwd)
    except Exception as exc:  # pragma: no cover - defensive: never let a sidecar raise
        engram_outcome, engram_warnings = "degraded", [
            f"engram sidecar raised unexpectedly ({type(exc).__name__}); non-fatal"
        ]
    outcomes["engram"] = engram_outcome
    warnings.extend(engram_warnings)

    try:
        graphtor_docs_outcome, graphtor_docs_warnings = _run_graphtor_docs(
            graphtor_docs_executable, resolved_workspace_root, cwd=cwd
        )
    except Exception as exc:  # pragma: no cover - defensive: never let a sidecar raise
        graphtor_docs_outcome, graphtor_docs_warnings = "degraded", [
            f"graphtor-docs sidecar raised unexpectedly ({type(exc).__name__}); non-fatal"
        ]
    outcomes["graphtor-docs"] = graphtor_docs_outcome
    warnings.extend(graphtor_docs_warnings)

    return SidecarReport(outcomes=outcomes, warnings=tuple(warnings))
