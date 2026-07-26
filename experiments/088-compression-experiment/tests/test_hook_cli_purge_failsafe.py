"""Fail-safe test for hook_cli.py's opportunistic purge cleanup (088.002-T).

P-018 round-6 finding: the opportunistic session-end-style purge call
(``store.purge_expired()``) ran unguarded inside the same ``try`` block as
``process_post_tool_use`` -- if it raised (lock contention, I/O error) after
a result had already been decided (and possibly a durable row already
stashed), the whole invocation would crash before ``result`` was ever
printed, silently dropping an already-created retrieval handle from the
caller's point of view. Purge is best-effort cleanup and must never be
allowed to invalidate an already-decided result.

Tested in-process (not via subprocess) so ``BrainspaceStore.purge_expired``
can be monkeypatched to raise deterministically.
"""

import io
import json

from brainspace import config, hook_cli
from brainspace.store import BrainspaceStore


def test_purge_failure_does_not_prevent_result_from_being_emitted(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setenv(config.ENABLED_ENV_VAR, "1")
    # resolve_workspace_root validates payload["cwd"] as related to the
    # process's actual working directory tree, so the two must match here,
    # matching the real subprocess invocation pattern used elsewhere.
    monkeypatch.chdir(tmp_path)

    def _boom(self):
        raise RuntimeError("simulated purge failure (lock contention)")

    monkeypatch.setattr(BrainspaceStore, "purge_expired", _boom)

    payload = {
        "sessionId": "s1",
        "timestamp": 1,
        "cwd": str(tmp_path),
        "toolName": "bash",
        "toolArgs": {},
        "toolResult": {
            "resultType": "success",
            "textResultForLlm": "noisy line\n" * 100,
        },
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))

    exit_code = hook_cli.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    # The hook must still emit its decided result (here: a byte-identical
    # passthrough decline, since no model tokenizer is available in this
    # test environment -- but the key assertion is that SOME valid JSON
    # result is printed, not that the process crashed with no output at
    # all before reaching the print statement).
    result = json.loads(captured.out)
    assert result == {}


def test_purge_failure_does_not_drop_an_already_created_handle(
    tmp_path, monkeypatch, capsys
):
    # Stronger version of the above: force compression to actually occur
    # (simulate a model tokenizer being available) so a durable row and a
    # retrieval handle are created, then force purge to fail afterward, and
    # confirm the handle-bearing result still reaches stdout rather than
    # being silently dropped by an unhandled purge exception.
    monkeypatch.setenv(config.ENABLED_ENV_VAR, "1")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("brainspace.hook.is_model_tokenizer_available", lambda: True)

    def _boom(self):
        raise RuntimeError("simulated purge failure (lock contention)")

    monkeypatch.setattr(BrainspaceStore, "purge_expired", _boom)

    payload = {
        "sessionId": "s1",
        "timestamp": 1,
        "cwd": str(tmp_path),
        "toolName": "bash",
        "toolArgs": {},
        "toolResult": {
            "resultType": "success",
            "textResultForLlm": "repeated noisy log line\n" * 200,
        },
    }
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))

    exit_code = hook_cli.main()

    assert exit_code == 0
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert "modifiedResult" in result
