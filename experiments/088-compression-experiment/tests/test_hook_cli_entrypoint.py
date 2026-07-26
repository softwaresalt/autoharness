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
        # Real Copilot CLI invocations run the hook subprocess FROM the
        # session cwd it reports in the payload -- the two are the same
        # value. Passing cwd here keeps the test realistic now that
        # resolve_workspace_root validates payload["cwd"] as related to the
        # process's actual working directory (P-018 round-3 finding).
        cwd=payload.get("cwd"),
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


def test_enabled_without_model_tokenizer_still_passes_through_unchanged(tmp_path):
    # P-018 round-6 finding: without a real model tokenizer available, the
    # hook must decline (byte-identical passthrough) rather than stash and
    # rewrite output on the unproven char/4 fallback estimate alone. This
    # is the realistic default state of most environments (no ``tiktoken``
    # installed), so this smoke test intentionally does NOT inject a fake
    # tokenizer -- it proves the CLI's real, un-doctored default behavior.
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
    assert result == {}


def test_enabled_with_model_tokenizer_available_compresses_large_matching_output(tmp_path):
    # Companion to the decline test above: prove the compress-and-stash path
    # still works end-to-end (through the real subprocess CLI, not just the
    # in-process unit tests) once a real model tokenizer becomes available.
    # A tiny fake ``tiktoken`` stub is injected via PYTHONPATH so this does
    # not depend on the real dependency being installed in the environment
    # that runs the suite.
    stub_dir = tmp_path / "tiktoken_stub"
    stub_dir.mkdir()
    (stub_dir / "tiktoken.py").write_text(
        "class _Encoding:\n"
        "    def encode(self, text):\n"
        "        return text.split()\n"
        "\n"
        "\n"
        "def get_encoding(name):\n"
        "    return _Encoding()\n",
        encoding="utf-8",
    )
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
    result = _run_hook_cli(
        payload,
        env_overrides={
            "BRAINSPACE_EXPERIMENT_ENABLED": "1",
            "PYTHONPATH": str(stub_dir) + os.pathsep + os.environ.get("PYTHONPATH", ""),
        },
    )
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


def test_unrelated_payload_cwd_is_safe_noop_not_a_crash(tmp_path):
    # P-018 round-3 follow-up finding: a crafted or stale payload cwd
    # unrelated to the subprocess's actual working directory must never
    # crash the hook (unhandled WorkspaceContainmentError) or create a
    # store outside the workspace -- it must fail safe to a no-op
    # passthrough, exactly like the malformed-JSON case above.
    unrelated = tmp_path / "unrelated-cwd"
    unrelated.mkdir()
    session_dir = tmp_path / "actual-session-dir"
    session_dir.mkdir()
    payload = {
        "sessionId": "s1",
        "timestamp": 1,
        "cwd": str(unrelated),
        "toolName": "bash",
        "toolArgs": {},
        "toolResult": {
            "resultType": "success",
            "textResultForLlm": "noisy line\n" * 100,
        },
    }
    env = dict(os.environ)
    env["BRAINSPACE_EXPERIMENT_ENABLED"] = "1"
    env.pop("BRAINSPACE_WORKSPACE", None)
    proc = subprocess.run(
        [sys.executable, _HOOK_CLI],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        cwd=str(session_dir),  # deliberately NOT the payload's cwd
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout) == {}
    assert not (unrelated / ".autoharness").exists()
