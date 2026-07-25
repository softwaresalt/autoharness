"""Tests for the containment-safe path resolver (088.001-T).

Constitution IV / plan hardening: the resolver MUST anchor to the workspace
root and reject every escape vector before any store file is touched.
"""

import os
import sys

import pytest

from brainspace.resolver import ContainmentError, resolve_store_root


def test_resolve_store_root_returns_path_under_workspace(tmp_path):
    root = resolve_store_root(str(tmp_path))
    assert str(root).startswith(str(tmp_path))
    assert root.name == "brainspace"
    assert ".autoharness" in str(root)
    assert "cache" in str(root)


def test_resolve_store_root_creates_directory(tmp_path):
    root = resolve_store_root(str(tmp_path))
    assert root.exists()
    assert root.is_dir()


def test_resolve_store_root_rejects_dotdot_traversal(tmp_path):
    # Simulate a maliciously configured relative dir containing `..`.
    with pytest.raises(ContainmentError):
        resolve_store_root(str(tmp_path), relative_dir="../../etc")


def test_resolve_store_root_rejects_absolute_env_override(tmp_path, monkeypatch):
    # No arbitrary BRAINSPACE_CCR env override is honored — the resolver
    # must not read any absolute-path environment variable at all.
    other = tmp_path / "elsewhere"
    other.mkdir()
    monkeypatch.setenv("BRAINSPACE_CCR", str(other))
    root = resolve_store_root(str(tmp_path))
    assert str(root).startswith(str(tmp_path))
    assert "elsewhere" not in str(root)


def test_resolve_store_root_rejects_symlink_escape(tmp_path):
    if sys.platform == "win32" and os.environ.get("CI"):
        pytest.skip("symlink creation may require elevation on CI runners")
    outside = tmp_path.parent / "outside_target"
    outside.mkdir(exist_ok=True)
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    link_parent = workspace / ".autoharness" / "cache"
    link_parent.mkdir(parents=True)
    link_path = link_parent / "brainspace"
    try:
        os.symlink(str(outside), str(link_path), target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported/permitted in this environment")
    with pytest.raises(ContainmentError):
        resolve_store_root(str(workspace))


def test_resolve_store_root_rejects_upward_parent_search(tmp_path):
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    # The resolver must anchor exactly to the given workspace root; it must
    # not walk upward looking for an existing .autoharness directory.
    (tmp_path / ".autoharness").mkdir()
    root = resolve_store_root(str(nested))
    assert str(root).startswith(str(nested))


def test_resolve_store_root_rejects_non_string_workspace_root():
    with pytest.raises(ContainmentError):
        resolve_store_root(None)
