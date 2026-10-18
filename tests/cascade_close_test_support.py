"""Shared helpers for the cascade-close journaling/recovery tests (211-F)."""

from __future__ import annotations

import os
from pathlib import Path


def make_dir_link(link: Path, target: Path) -> str | None:
    """Create a directory symlink (or Windows junction). Return a skip reason on failure."""

    try:
        os.symlink(target, link, target_is_directory=True)
        return None
    except (OSError, NotImplementedError) as exc:
        symlink_error = exc
    if os.name == "nt":
        try:
            import _winapi

            _winapi.CreateJunction(str(target), str(link))
            return None
        except (OSError, ImportError, AttributeError) as exc:
            return f"cannot create symlink ({symlink_error}) or junction ({exc})"
    return f"cannot create directory symlink: {symlink_error}"
