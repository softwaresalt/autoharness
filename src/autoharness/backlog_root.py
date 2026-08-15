"""Shared backlog storage-root resolution helpers."""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path
import stat

BACKLOG_ROOT_OVERRIDE_ENV = "BACKLOGIT_WORKSPACE_DIR"

# The only two directory names backlogit 1.9.0's own
# ``validateWorkspaceDirOverride`` (internal/core/workspace.go) accepts for
# BACKLOGIT_WORKSPACE_DIR, in discovery precedence order. Never derived from
# config; mirrors upstream's private ``workspaceRootCandidates`` exactly.
_CANDIDATE_NAMES: tuple[str, ...] = (".backlog", ".backlogit")


class BacklogUnavailableError(RuntimeError):
    def __init__(self, path: Path, reason: str) -> None:
        self.path = str(path)
        self.reason = reason
        super().__init__(f"{reason}: {path}")


class AmbiguousBacklogRootError(BacklogUnavailableError):
    def __init__(self, workspace: Path, candidates: tuple[Path, Path]) -> None:
        self.workspace = str(workspace)
        self.candidates = tuple(str(candidate) for candidate in candidates)
        names = ", ".join(candidate.name for candidate in candidates)
        super().__init__(workspace, f"multiple backlog directories are present ({names})")


def _must_be_one_of_message() -> str:
    return f"{BACKLOG_ROOT_OVERRIDE_ENV} must be one of {', '.join(_CANDIDATE_NAMES)}"


def _validate_override_name(override: str) -> str:
    """Validate a raw BACKLOGIT_WORKSPACE_DIR override value.

    Mirrors backlogit 1.9.0's ``validateWorkspaceDirOverride`` (PR #344
    Copilot review, thread PRRT_kwDORzpWpM6ZihN2): the override is NOT an
    arbitrary filesystem path. It must be exactly one of ``_CANDIDATE_NAMES``
    (case-sensitive) -- no path separators, no ``.``/``..``, no absolute
    paths, and no drive/UNC prefixes. A value that only differs from a
    candidate by case is rejected with a distinct diagnostic (upstream
    requires the exact supported case) rather than silently accepted or
    silently treated as ambiguous.
    """
    if not override:
        raise BacklogUnavailableError(Path(override), f"{BACKLOG_ROOT_OVERRIDE_ENV} is set but empty")
    if "\x00" in override:
        raise BacklogUnavailableError(
            Path(override), f"{BACKLOG_ROOT_OVERRIDE_ENV} contains a NUL byte"
        )
    if override in (".", ".."):
        raise BacklogUnavailableError(Path(override), _must_be_one_of_message())
    if any(sep in override for sep in ("/", "\\")):
        raise BacklogUnavailableError(Path(override), _must_be_one_of_message())
    if os.path.isabs(override):
        raise BacklogUnavailableError(Path(override), _must_be_one_of_message())
    drive, _tail = os.path.splitdrive(override)
    if drive:
        raise BacklogUnavailableError(Path(override), _must_be_one_of_message())
    if override in _CANDIDATE_NAMES:
        return override
    for candidate in _CANDIDATE_NAMES:
        if override.lower() == candidate.lower():
            raise BacklogUnavailableError(
                Path(override),
                f"{BACKLOG_ROOT_OVERRIDE_ENV} must use the exact supported case ({candidate})",
            )
    raise BacklogUnavailableError(Path(override), _must_be_one_of_message())


def _is_reparse_point(candidate_path: Path) -> bool:
    """Detect a Windows reparse point (e.g. a directory junction) that
    ``Path.is_symlink()`` alone would miss (PR #344 Copilot review round 3,
    thread PRRT_kwDORzpWpM6ZipoH): on Windows, directory junctions are
    reparse points but are NOT symbolic links, so ``Path.is_symlink()``
    returns ``False`` for them while ``Path.is_dir()`` still follows them --
    letting a junction silently redirect the backlog root outside the
    workspace. Inspects ``os.lstat(...).st_file_attributes`` (populated on
    Windows since Python 3.5; the attribute is simply absent/``None`` on
    POSIX, where junctions do not exist and ``Path.is_symlink()`` already
    covers real symlinks)."""
    st_file_attributes = getattr(os.lstat(candidate_path), "st_file_attributes", None)
    if st_file_attributes is None:
        return False
    return bool(st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _reject_symlink(candidate_path: Path) -> None:
    """Reject a resolved backlog directory that is a symlink or reparse
    point (PR #344 Copilot review, threads PRRT_kwDORzpWpM6ZihN5 and
    PRRT_kwDORzpWpM6ZipoH): upstream's ``probeWorkspaceCandidate`` lstats the
    candidate and refuses to treat a symlink/reparse point as a valid
    workspace storage root, since ``Path.is_dir()`` alone follows symlinks
    (and, on Windows, directory junctions) and would let an unrelated or
    escaping directory be selected. ``Path.is_symlink()`` alone does not
    reject Windows junctions, so the reparse-point attribute check above is
    required in addition to it."""
    if candidate_path.is_symlink() or _is_reparse_point(candidate_path):
        raise BacklogUnavailableError(
            candidate_path, "backlog directory is a symlink or reparse point"
        )


def resolve_backlog_root(
    workspace: Path | str = ".",
    *,
    env: Mapping[str, str] | None = None,
) -> Path:
    """Resolve a workspace's backlog storage root using backlogit precedence."""
    workspace_path = Path(workspace)
    env_map = os.environ if env is None else env
    override = env_map.get(BACKLOG_ROOT_OVERRIDE_ENV)
    if override is not None:
        validated_name = _validate_override_name(override)
        override_path = workspace_path / validated_name
        if not override_path.exists():
            raise BacklogUnavailableError(override_path, "configured backlog directory is unavailable")
        _reject_symlink(override_path)
        if not override_path.is_dir():
            raise BacklogUnavailableError(override_path, "configured backlog directory is unavailable")
        return override_path

    matches: list[Path] = []
    for name in _CANDIDATE_NAMES:
        candidate_path = workspace_path / name
        if not candidate_path.exists():
            continue
        _reject_symlink(candidate_path)
        if candidate_path.is_dir():
            matches.append(candidate_path)
    if len(matches) > 1:
        raise AmbiguousBacklogRootError(workspace_path, (matches[0], matches[1]))
    if matches:
        return matches[0]
    raise BacklogUnavailableError(workspace_path, "backlog directory is unavailable")
