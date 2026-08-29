"""CLI regression test: `autoharness gate check` must fail closed (exit 2)
with a clean message on an unresolvable `--base`/`--head` ref instead of
raising `InvalidGitRefError` uncaught (149.012-T/149.013-T ref-safety
hardening regressed this existing command; see 157-S local review Finding
A)."""

from __future__ import annotations

import io
import subprocess
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from autoharness.cli import main

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMP_ROOT = _REPO_ROOT / ".test-output"

_CONFIG = textwrap.dedent(
    """\
    schema_version: "1.0.0"
    lifecycle_hooks:
      pre_task_completion:
        enforcement: "advisory"
        validation_gates:
          - pattern: "docs/**/*.md"
            command: "echo ok"
            timeout_seconds: 5
    """
)


def _run(*argv: str) -> tuple[str, str, int | None]:
    out, err = io.StringIO(), io.StringIO()
    code: int | None = 0
    try:
        with redirect_stdout(out), redirect_stderr(err):
            main(list(argv))
    except SystemExit as exc:  # noqa: PERF203 - CLI harness
        code = exc.code
    return out.getvalue(), err.getvalue(), code


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True
    )
    return completed.stdout.strip()


class GateCheckBadRefTests(unittest.TestCase):
    def test_unresolvable_base_ref_exits_2_without_traceback(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            _git(workspace, "init", "--initial-branch", "main")
            _git(workspace, "config", "user.name", "Autoharness Tests")
            _git(workspace, "config", "user.email", "autoharness-tests@example.com")
            (workspace / "docs").mkdir()
            (workspace / "docs" / "a.md").write_text("hello\n", encoding="utf-8")
            _git(workspace, "add", ".")
            _git(workspace, "commit", "-m", "init")

            config_dir = workspace / ".autoharness"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.yaml").write_text(_CONFIG, encoding="utf-8")

            _out, err, code = _run(
                "gate", "check", "--workspace", str(workspace), "--base", "totally-nonexistent-ref"
            )
            self.assertEqual(code, 2)
            self.assertNotIn("Traceback", err)

    def test_option_like_base_ref_exits_2_without_traceback(self) -> None:
        _TEMP_ROOT.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=_TEMP_ROOT) as tmp:
            workspace = Path(tmp)
            _git(workspace, "init", "--initial-branch", "main")
            _git(workspace, "config", "user.name", "Autoharness Tests")
            _git(workspace, "config", "user.email", "autoharness-tests@example.com")
            (workspace / "docs").mkdir()
            (workspace / "docs" / "a.md").write_text("hello\n", encoding="utf-8")
            _git(workspace, "add", ".")
            _git(workspace, "commit", "-m", "init")

            config_dir = workspace / ".autoharness"
            config_dir.mkdir(parents=True, exist_ok=True)
            (config_dir / "config.yaml").write_text(_CONFIG, encoding="utf-8")

            _out, err, code = _run(
                "gate", "check", "--workspace", str(workspace), "--base", "--output=pwned"
            )
            self.assertEqual(code, 2)
            self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main()
