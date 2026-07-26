"""Tests for the shared workspace-root resolution helper (finding #12).

Both the hook (``hook_cli.py``, per-invocation subprocess) and the MCP
retrieval server (``mcp_server.py``, long-lived process) must resolve the
SAME workspace root given the same environment/payload inputs, or a tool run
from a subdirectory could be stored where the server never looks.
"""

import os

from brainspace.workspace import resolve_workspace_root


def test_env_var_takes_precedence_over_payload_cwd(monkeypatch, tmp_path):
    pinned = str(tmp_path / "pinned-root")
    monkeypatch.setenv("BRAINSPACE_WORKSPACE", pinned)
    payload = {"cwd": str(tmp_path / "subdir")}
    assert resolve_workspace_root(payload) == pinned


def test_payload_cwd_used_when_no_env_pin(monkeypatch, tmp_path):
    monkeypatch.delenv("BRAINSPACE_WORKSPACE", raising=False)
    payload = {"cwd": str(tmp_path / "subdir")}
    assert resolve_workspace_root(payload) == str(tmp_path / "subdir")


def test_falls_back_to_process_cwd_when_no_env_or_payload(monkeypatch):
    monkeypatch.delenv("BRAINSPACE_WORKSPACE", raising=False)
    assert resolve_workspace_root(None) == os.getcwd()
    assert resolve_workspace_root({}) == os.getcwd()


def test_hook_and_server_resolve_identically_given_same_inputs(monkeypatch, tmp_path):
    # The "subdir case": a tool runs from a subdirectory, but the operator
    # has pinned BRAINSPACE_WORKSPACE so both entry points still agree.
    pinned = str(tmp_path)
    monkeypatch.setenv("BRAINSPACE_WORKSPACE", pinned)
    hook_payload = {"cwd": str(tmp_path / "sub" / "dir")}
    server_payload = None  # server has no per-call payload
    assert resolve_workspace_root(hook_payload) == resolve_workspace_root(server_payload)
    assert resolve_workspace_root(hook_payload) == pinned
