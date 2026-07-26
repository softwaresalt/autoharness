"""Tests for the shared workspace-root resolution helper (finding #12).

Both the hook (``hook_cli.py``, per-invocation subprocess) and the MCP
retrieval server (``mcp_server.py``, long-lived process) must resolve the
SAME workspace root given the same environment/payload inputs, or a tool run
from a subdirectory could be stored where the server never looks.

``explicit_root``/``BRAINSPACE_WORKSPACE`` must also be validated as related
to the process's actual working directory tree (P-018 round-3 finding: an
unrelated candidate must be rejected -- Constitution IV containment -- or a
misconfigured env var / CLI argument could point the store, and therefore
``purge_cli --mode all``, at a completely unrelated filesystem location).
"""

import os

import pytest

from brainspace.workspace import WorkspaceContainmentError, resolve_workspace_root


def test_env_var_takes_precedence_over_payload_cwd(monkeypatch, tmp_path):
    pinned = tmp_path / "pinned-root"
    nested = pinned / "nested"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    monkeypatch.setenv("BRAINSPACE_WORKSPACE", str(pinned))
    payload = {"cwd": str(tmp_path / "subdir")}
    assert resolve_workspace_root(payload) == str(pinned)


def test_payload_cwd_used_when_no_env_pin(monkeypatch, tmp_path):
    monkeypatch.delenv("BRAINSPACE_WORKSPACE", raising=False)
    monkeypatch.chdir(tmp_path)
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    payload = {"cwd": str(subdir)}
    assert resolve_workspace_root(payload) == str(subdir)


def test_falls_back_to_process_cwd_when_no_env_or_payload(monkeypatch):
    monkeypatch.delenv("BRAINSPACE_WORKSPACE", raising=False)
    assert resolve_workspace_root(None) == os.getcwd()
    assert resolve_workspace_root({}) == os.getcwd()


def test_hook_and_server_resolve_identically_given_same_inputs(monkeypatch, tmp_path):
    # The "subdir case": a tool runs from a subdirectory, but the operator
    # has pinned BRAINSPACE_WORKSPACE so both entry points still agree.
    session_dir = tmp_path / "anywhere-under-pinned-root"
    session_dir.mkdir()
    monkeypatch.chdir(session_dir)
    pinned = str(tmp_path)
    monkeypatch.setenv("BRAINSPACE_WORKSPACE", pinned)
    hook_payload = {"cwd": str(tmp_path / "sub" / "dir")}
    server_payload = None  # server has no per-call payload
    assert resolve_workspace_root(hook_payload) == resolve_workspace_root(server_payload)
    assert resolve_workspace_root(hook_payload) == pinned


def test_explicit_root_takes_precedence_over_env_pin(monkeypatch, tmp_path):
    # P-018 re-review finding #4 (round 2): an explicit CLI argument (e.g.
    # purge_cli.py's ``--repo-root``) must win over an ambient
    # BRAINSPACE_WORKSPACE env var, or an operator's explicit intent could be
    # silently overridden -- in ``--mode all`` that could purge the wrong
    # workspace's live rows.
    explicit = tmp_path / "explicit-root"
    nested = explicit / "nested"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    ambient = str(tmp_path / "ambient-root")
    monkeypatch.setenv("BRAINSPACE_WORKSPACE", ambient)
    assert resolve_workspace_root(explicit_root=str(explicit)) == str(explicit)


def test_explicit_root_wins_over_env_pin_and_payload(monkeypatch, tmp_path):
    explicit = tmp_path / "explicit-root"
    nested = explicit / "nested"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    ambient = str(tmp_path / "ambient-root")
    monkeypatch.setenv("BRAINSPACE_WORKSPACE", ambient)
    payload = {"cwd": str(tmp_path / "payload-root")}
    assert resolve_workspace_root(payload, explicit_root=str(explicit)) == str(explicit)


def test_explicit_root_as_descendant_of_process_cwd_is_allowed(monkeypatch, tmp_path):
    # Legitimate reverse relationship: invoking from the top-level repo root
    # but explicitly pinning a nested workspace.
    monkeypatch.chdir(tmp_path)
    nested = tmp_path / "nested-workspace"
    nested.mkdir()
    assert resolve_workspace_root(explicit_root=str(nested)) == str(nested)


def test_explicit_root_unrelated_to_process_cwd_is_rejected(monkeypatch, tmp_path):
    # P-018 round-3 finding #3: explicit_root must be validated as related to
    # the process's actual working directory tree -- an unrelated sibling
    # directory must never be silently accepted (it would let
    # ``purge_cli --mode all --repo-root <unrelated>`` delete another
    # workspace's rows).
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    monkeypatch.chdir(session_dir)
    unrelated = tmp_path / "completely-unrelated-project"
    unrelated.mkdir()
    with pytest.raises(WorkspaceContainmentError):
        resolve_workspace_root(explicit_root=str(unrelated))


def test_env_pin_unrelated_to_process_cwd_is_rejected(monkeypatch, tmp_path):
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    monkeypatch.chdir(session_dir)
    unrelated = tmp_path / "completely-unrelated-project"
    unrelated.mkdir()
    monkeypatch.setenv("BRAINSPACE_WORKSPACE", str(unrelated))
    with pytest.raises(WorkspaceContainmentError):
        resolve_workspace_root(None)


def test_payload_cwd_unrelated_to_process_cwd_is_rejected(monkeypatch, tmp_path):
    # P-018 round-3 follow-up finding: the third resolution branch
    # (``payload["cwd"]``, used when neither ``explicit_root`` nor
    # ``BRAINSPACE_WORKSPACE`` is set) returned the payload cwd verbatim with
    # NO containment check at all -- a crafted or stale hook payload could
    # carry an arbitrary absolute cwd unrelated to the process's actual
    # working directory, so ``hook_cli.py`` would create the SQLite store
    # (and write to it) outside the workspace despite the containment
    # validation already applied to explicit_root/env_root.
    monkeypatch.delenv("BRAINSPACE_WORKSPACE", raising=False)
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    monkeypatch.chdir(session_dir)
    unrelated = tmp_path / "completely-unrelated-project"
    unrelated.mkdir()
    payload = {"cwd": str(unrelated)}
    with pytest.raises(WorkspaceContainmentError):
        resolve_workspace_root(payload)


def test_explicit_empty_root_is_rejected_not_treated_as_unset(monkeypatch, tmp_path):
    # P-018 round-3 follow-up finding: ``if explicit_root:`` truthiness meant
    # an *explicitly supplied* empty string (e.g. ``purge_cli.py --repo-root
    # "" --mode all``) fell through to the ambient BRAINSPACE_WORKSPACE pin
    # instead of being rejected -- silently changing which workspace's rows
    # got purged despite the operator's explicit (if malformed) argument.
    # An explicit empty root must never be treated as "not supplied".
    monkeypatch.chdir(tmp_path)
    ambient = tmp_path / "ambient-root"
    ambient.mkdir()
    monkeypatch.setenv("BRAINSPACE_WORKSPACE", str(ambient))
    with pytest.raises(WorkspaceContainmentError):
        resolve_workspace_root(explicit_root="")


