"""Shared backlog storage-root resolution helpers."""

from __future__ import annotations

from collections.abc import Mapping
import os
from pathlib import Path

BACKLOG_ROOT_OVERRIDE_ENV = "BACKLOGIT_WORKSPACE_DIR"


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
        if not override:
            raise BacklogUnavailableError(workspace_path, f"{BACKLOG_ROOT_OVERRIDE_ENV} is empty")
        if "\x00" in override:
            raise BacklogUnavailableError(
                workspace_path,
                f"{BACKLOG_ROOT_OVERRIDE_ENV} contains a NUL byte",
            )
        override_path = Path(override)
        if not override_path.is_absolute():
            override_path = workspace_path / override_path
        if not override_path.exists() or not override_path.is_dir():
            raise BacklogUnavailableError(override_path, "configured backlog directory is unavailable")
        return override_path

    backlog_root = workspace_path / ".backlog"
    legacy_root = workspace_path / ".backlogit"
    backlog_exists = backlog_root.is_dir()
    legacy_exists = legacy_root.is_dir()
    if backlog_exists and legacy_exists:
        raise AmbiguousBacklogRootError(workspace_path, (backlog_root, legacy_root))
    if backlog_exists:
        return backlog_root
    if legacy_exists:
        return legacy_root
    raise BacklogUnavailableError(workspace_path, "backlog directory is unavailable")
