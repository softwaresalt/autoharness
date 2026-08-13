"""Copilot CLI resolution + argv composition (120.003-T). PURE: no spawning.

Resolution order (matching start.ps1/start.sh's documented contract):

1. ``COPILOT_EXE_PATH`` environment variable.
2. ``COPILOT_EXE`` environment variable (back-compat).
3. ``copilot`` resolved via ``shutil.which`` on PATH.

If none resolves, raises :class:`~autoharness.supervise.errors.ResolutionError`
with the CURRENT actionable message from ``start.ps1``. This module never
fabricates/guesses a path (H2).

Argv composition: ``--remote`` is appended ONLY when
``COPILOT_USE_REMOTE`` is ``"true"``/``"1"`` (case-insensitive) AND the
operator-supplied args do not already contain ``--remote`` (double-add
guard). The operator's argv is then appended VERBATIM -- never re-parsed,
re-quoted, reordered, or filtered.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from autoharness.supervise.errors import ResolutionError

_UNRESOLVABLE_MESSAGE = (
    "Unable to locate Copilot CLI. Set COPILOT_EXE_PATH (or COPILOT_EXE for "
    "backward compatibility) or add 'copilot' to PATH."
)

_TRUTHY_REMOTE_VALUES = frozenset({"true", "1"})


@dataclass(frozen=True)
class ResolveResult:
    """Typed, frozen outcome of :func:`resolve_copilot`.

    Attributes:
        exe_path: The resolved, absolute-or-as-given Copilot CLI executable
            path.
        source: One of ``"env_path"`` (``COPILOT_EXE_PATH``), ``"env_exe"``
            (``COPILOT_EXE``), or ``"path_lookup"`` (resolved via PATH).
        argv: The FULL composed argv, with ``exe_path`` at index 0, followed
            by an optional ``"--remote"``, followed by the operator's
            argument list verbatim.
    """

    exe_path: str
    source: str
    argv: tuple[str, ...]


def _resolve_exe(env: Mapping[str, str]) -> tuple[str, str]:
    exe_path = env.get("COPILOT_EXE_PATH")
    if exe_path:
        return exe_path, "env_path"

    exe = env.get("COPILOT_EXE")
    if exe:
        return exe, "env_exe"

    found = shutil.which("copilot")
    if found:
        return found, "path_lookup"

    raise ResolutionError(_UNRESOLVABLE_MESSAGE)


def _should_append_remote(env: Mapping[str, str], operator_args: Sequence[str]) -> bool:
    use_remote = env.get("COPILOT_USE_REMOTE", "")
    if use_remote.lower() not in _TRUTHY_REMOTE_VALUES:
        return False
    return "--remote" not in operator_args


def resolve_copilot(
    operator_args: Sequence[str], *, env: Optional[Mapping[str, str]] = None
) -> ResolveResult:
    """Resolve the Copilot CLI executable and compose the full launch argv.

    ``env`` defaults to ``os.environ`` (read-only) when ``None``. This
    function never spawns a process and never mutates any environment.
    """

    if env is None:
        import os

        env = os.environ

    exe_path, source = _resolve_exe(env)

    argv: list[str] = [exe_path]
    if _should_append_remote(env, operator_args):
        argv.append("--remote")
    argv.extend(operator_args)

    return ResolveResult(exe_path=exe_path, source=source, argv=tuple(argv))
