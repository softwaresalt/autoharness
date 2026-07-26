"""Smoke tests for the hook_cli.py command-hook entrypoint (088.002-T).

Exercises the actual subprocess path Copilot CLI would invoke as a command
hook: JSON on stdin, JSON on stdout.
"""

import json
import os
import subprocess
import sys

_BRAINSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HOOK_CLI = os.path.join(_BRAINSPACE_DIR, "brainspace", "hook_cli.py")


def _run_hook_cli(payload, env_overrides=None):
    env = dict(os.environ)
    env.pop("BRAINSPACE_EXPERIMENT_ENABLED", None)
    if env_overrides:
        env.update(env_overrides)
    proc = subprocess.run(
        [sys.executable, _HOOK_CLI],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_disabled_by_default_passes_through(tmp_path):
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
    result = _run_hook_cli(payload)
    assert result == {}


def test_disabled_invocation_makes_no_durable_write(tmp_path):
    # A disabled invocation must make ZERO filesystem writes -- not even
    # creating the (empty) store database file. Constructing the store is
    # itself a durable side effect (mkdir + sqlite3.connect creates the
    # file on disk), so the flag check must happen BEFORE the store is
    # ever constructed, not merely before any row is written to it.
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
    _run_hook_cli(payload)
    store_dir = tmp_path / ".autoharness" / "cache" / "brainspace"
    assert not store_dir.exists()


def test_enabled_compresses_large_matching_output(tmp_path):
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
    result = _run_hook_cli(payload, env_overrides={"BRAINSPACE_EXPERIMENT_ENABLED": "1"})
    assert "modifiedResult" in result


def test_malformed_stdin_is_safe_noop(tmp_path):
    env = dict(os.environ)
    env["BRAINSPACE_EXPERIMENT_ENABLED"] = "1"
    proc = subprocess.run(
        [sys.executable, _HOOK_CLI],
        input="not valid json{{{",
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0
    assert json.loads(proc.stdout) == {}
