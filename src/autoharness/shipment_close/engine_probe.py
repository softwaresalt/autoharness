"""CLI engine-semantics probe for ``cascade-close`` (192-F, plan unit A2a).

:func:`probe_engine_semantics` probes the backlogit build the command will
invoke, on the same CLI surface and through the same resolved absolute binary,
and returns the ``pre_close.engine_semantics`` decision of the merged
:func:`~autoharness.gates.shipment_closure.assess_cascade_engine_semantics`
(038-DL D4a). The probe never halts and never raises: every failure is
``UNVERIFIED``, so ``select_close_path`` selects SAFE_CLOSE.

It sanitizes the *inputs* of the merged function, never its outputs (re-plan
cycle-1 R6): ``version`` is passed only when it is a ``str`` of at most 64
characters that fully matches the merged release-version pattern and is
redaction-neutral (``redact(version)[0] == version``; Copilot PR #481 T5), and
``commit`` only when it fully matches ``^[0-9a-f]{7,64}$``.

The probe ``cwd`` is a fresh, empty, workspace-contained directory under the
Git-ignored ``.autoharness/gates/cascade-close/probe/`` (re-plan cycle-1 R3;
Copilot PR #481 T3/T4; constitution IV). This module is the only probe
spawner. It **never deletes** a probe directory: removing accumulated probe
directories is an operator action under the destructive-command approval path
(constitution VII).
"""

from __future__ import annotations

import json
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from autoharness.gates.cascade_evidence import redact
from autoharness.gates.closure_contract import ClosureContractError, assert_path_within_workspace
from autoharness.gates.shipment_closure import EngineSemanticsDecision, assess_cascade_engine_semantics
from autoharness.shipment_close import EXIT_INPUT
from autoharness.shipment_close.persist import LOCK_DIR, PersistError, _is_link, ensure_trusted_directory
from autoharness.shipment_close.runner import ResolvedBinary, run_bounded

__all__ = [
    "PROBE_ARGS",
    "PROBE_ROOT",
    "PROBE_TIMEOUT_SECONDS",
    "EngineProbe",
    "create_probe_directory",
    "probe_engine_semantics",
]

PROBE_ROOT: Final = LOCK_DIR / "probe"
PROBE_ARGS: Final = ("version", "--no-update-check", "--format", "json")
PROBE_TIMEOUT_SECONDS = 30  # fixed; a module global so tests can bound it
INVOCATION_SURFACE: Final = "cli"

_MAX_VERSION_LENGTH: Final = 64
_COMMIT_PATTERN: Final = re.compile(r"[0-9a-f]{7,64}")


@dataclass(frozen=True)
class EngineProbe:
    """The probe result: the merged decision, its invocation surface, and the audit excerpt.

    ``version_excerpt`` is the bounded, redacted ``StreamCapture`` excerpt of
    this probe's stdout. It becomes ``tool.version_excerpt`` (the probe is the
    only version spawn, re-plan cycle-1 R7) and is never re-assessed.
    """

    decision: EngineSemanticsDecision
    invocation_surface: str
    version_excerpt: str


def create_probe_directory(workspace: Path | str) -> Path:
    """Create a fresh, empty, trust-checked probe directory inside the workspace.

    Every component down to ``probe/`` passes the A1b directory-trust walk;
    the directory itself is created exclusively with ``mkdtemp`` and confirmed
    empty, non-linked, and contained. Raises :class:`PersistError`.
    """

    probe_root = ensure_trusted_directory(workspace, PROBE_ROOT)
    directory = Path(tempfile.mkdtemp(prefix="probe-", dir=probe_root))
    _confirm_probe_directory(directory, workspace)
    return directory


def _confirm_probe_directory(directory: Path, workspace: Path | str) -> None:
    if _is_link(directory) or not directory.is_dir():
        raise PersistError(EXIT_INPUT, f"probe directory is not a real directory: {directory}")
    if any(directory.iterdir()):
        raise PersistError(EXIT_INPUT, f"probe directory is not empty: {directory}")
    try:
        assert_path_within_workspace(directory, workspace_root=Path(workspace).resolve())
    except ClosureContractError as exc:
        raise PersistError(EXIT_INPUT, str(exc)) from exc


def _sanitize_version(value: object, pattern: str) -> str | None:
    if type(value) is not str or len(value) > _MAX_VERSION_LENGTH:
        return None
    if re.fullmatch(pattern, value, flags=re.ASCII) is None:
        return None
    if redact(value)[0] != value:
        return None
    return value


def _sanitize_commit(value: object) -> str | None:
    if type(value) is not str or _COMMIT_PATTERN.fullmatch(value) is None:
        return None
    return value


def _assess(version: str | None, commit: str | None) -> EngineSemanticsDecision:
    return assess_cascade_engine_semantics(
        version,
        probe_surface=INVOCATION_SURFACE,
        invocation_surface=INVOCATION_SURFACE,
        probed_commit=commit,
    )


def probe_engine_semantics(resolved: ResolvedBinary, *, workspace: Path | str) -> EngineProbe:
    """Probe ``[*resolved.argv_prefix, "version", "--no-update-check", "--format", "json"]``.

    Never raises. A probe directory that cannot be established spawns
    nothing; a non-zero exit, a timeout, a stdout overflow, unparseable JSON,
    or any unexpected exception passes ``probed_version=None`` to the merged
    function, so the result is ``UNVERIFIED``.
    """

    try:
        # Reused, lazily imported (private-name rule, re-plan cycle-2 C2-4).
        from autoharness.gates.shipment_closure import _RELEASE_VERSION_PATTERN

        try:
            cwd = create_probe_directory(workspace)
            _confirm_probe_directory(cwd, workspace)  # immediately before the spawn
        except Exception:  # noqa: BLE001 - containment/trust/I-O failure: spawn nothing
            return EngineProbe(_assess(None, None), INVOCATION_SURFACE, "")
        result = run_bounded(
            [*resolved.argv_prefix, *PROBE_ARGS], cwd=cwd, timeout=PROBE_TIMEOUT_SECONDS
        )
        version = commit = None
        stdout = result.stdout
        if (
            not result.timed_out
            and result.exit_code == 0
            and stdout.parse_error is None
            and stdout.parse_bytes
        ):
            try:
                payload = json.loads(stdout.parse_bytes.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                payload = None
            if isinstance(payload, dict):
                version = _sanitize_version(payload.get("version"), _RELEASE_VERSION_PATTERN)
                commit = _sanitize_commit(payload.get("commit"))
        return EngineProbe(_assess(version, commit), INVOCATION_SURFACE, stdout.excerpt)
    except Exception:  # noqa: BLE001 - the probe must fail closed, never raise
        return EngineProbe(_assess(None, None), INVOCATION_SURFACE, "")
