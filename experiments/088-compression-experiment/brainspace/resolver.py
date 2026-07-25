"""Containment-safe local store path resolver (088.001-T).

Constitution IV (CLI Workspace Containment, NON-NEGOTIABLE): the store MUST
anchor to the workspace root and reject every escape vector. This module
does not honor any absolute-path environment variable override, does not
follow symlinks that resolve outside the workspace root, and does not search
upward through parent directories looking for an existing store.
"""

import os
from pathlib import Path

from brainspace import config


class ContainmentError(Exception):
    """Raised when a store path would resolve outside the workspace root."""


def resolve_store_root(workspace_root, relative_dir=None):
    """Resolve the containment-safe store root directory and create it.

    Args:
        workspace_root: absolute or relative path to the workspace root
            (typically the current working directory / repo root). Must be
            a non-empty string.
        relative_dir: override for the relative store directory, used only
            by tests to exercise rejection of malicious configuration. Must
            never contain ``..`` or resolve outside ``workspace_root``.

    Returns:
        pathlib.Path: the resolved, existing store root directory.

    Raises:
        ContainmentError: if the resolved path would escape the workspace
            root by any vector (``..`` traversal, symlink escape, absolute
            override, or upward parent search).
    """
    if not workspace_root or not isinstance(workspace_root, (str, os.PathLike)):
        raise ContainmentError("workspace_root must be a non-empty path string")

    # Anchor strictly to the given workspace root — resolve() collapses any
    # `..` segments in workspace_root itself, but we additionally verify the
    # relative_dir segment never walks upward below.
    anchor = Path(workspace_root).resolve()

    rel = relative_dir if relative_dir is not None else config.STORE_RELATIVE_DIR
    rel_path = Path(rel)

    if rel_path.is_absolute():
        raise ContainmentError(f"store relative dir must not be absolute: {rel}")

    if any(part == ".." for part in rel_path.parts):
        raise ContainmentError(f"store relative dir must not contain '..': {rel}")

    candidate = (anchor / rel_path).resolve()

    # Deliberately ignore any BRAINSPACE_CCR (or similar) environment
    # variable — no arbitrary absolute env path is ever honored. (No lookup
    # is performed by design; this comment documents the intentional
    # omission so a future edit does not "helpfully" add one.)

    # Reject if the resolved candidate (following any existing symlinks)
    # escapes the anchor. Path.resolve() already follows symlinks, so if a
    # component of `candidate` is a symlink pointing outside `anchor`, the
    # final resolved path will not be relative to anchor.
    try:
        candidate.relative_to(anchor)
    except ValueError as exc:
        raise ContainmentError(
            f"resolved store path escapes workspace root: {candidate} not under {anchor}"
        ) from exc

    # Anchor exactly to the given workspace root — never walk upward to find
    # a pre-existing .autoharness directory in a parent.
    candidate.mkdir(parents=True, exist_ok=True)

    # Defense in depth: if any *existing* intermediate component was a
    # symlink, re-verify post-creation the real path still resolves under
    # anchor (covers races and misconfigured pre-existing symlinks).
    real_candidate = Path(os.path.realpath(str(candidate)))
    real_anchor = Path(os.path.realpath(str(anchor)))
    try:
        real_candidate.relative_to(real_anchor)
    except ValueError as exc:
        raise ContainmentError(
            f"resolved store path escapes workspace root via symlink: {real_candidate}"
        ) from exc

    return candidate
