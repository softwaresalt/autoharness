"""Isolated, opt-in, real-binary smoke test for the 120-F runtime-binding
correction (2026-08-13 post-closure correction to 129-S/120-F).

**Why this exists**: unit tests elsewhere in this suite (`test_supervise_
bootstrap.py`, `test_supervise_app.py`, `test_supervise_process*.py`) prove
the SUPERVISOR's own logic -- that ``bootstrap_workspace()`` always
resolves and force-applies ``ENGRAM_WORKSPACE``/``GRAPHTOR_DB_PATH``/
``GRAPHTOR_SOURCES`` to the target workspace root, and that this reaches
``os.environ`` for the full lifetime of the spawned child. None of those
tests exercise the REAL ``engram``/``graphtor-docs`` binaries, so they
cannot, by themselves, prove those tools actually HONOR the injected
values the way their own ``--help`` output documents. This module closes
that gap with a small number of bounded, isolated, real-subprocess probes,
directly reproducing the live defect verified 2026-08-13 (a Copilot child
inheriting a stale ``ENGRAM_WORKSPACE`` bound a completely different
sibling workspace) and proving the fix's precondition: the real binaries
DO read these env vars and DO bind/resolve against the workspace they
name, when given a correct value.

**Deliberately NOT part of the default test run**: spawning real
``engram``/``graphtor-docs`` processes creates real background daemons
(engram's own architecture: a "shim" that binds/spawns a persistent
per-workspace daemon) that must be individually discovered and reaped --
unsafe/noisy to do unconditionally on every `pytest` invocation, and the
CI runner (`.github/workflows/ci.yml`) installs neither binary anyway
(exactly like this suite's existing hermetic-by-default convention; see
`test_supervise_app.py`'s own module docstring). This module is skipped
unless ALL of the following hold:

* ``AUTOHARNESS_REAL_BINARY_SMOKE=1`` is set in the environment (explicit
  opt-in -- never runs by accident);
* both ``engram`` and ``graphtor-docs`` resolve via ``shutil.which``;
* the host platform is ``win32`` (the verified live defect and this
  module's cleanup helper are both Windows-specific; POSIX coverage of the
  same underlying env-var-precedence contract is unit-tested directly
  above via ``RealPtyEnvPropagationTests`` in `test_supervise_process_
  pty.py`, which does not require spawning a real Engram/graphtor-docs
  daemon at all).

**Process hygiene (non-negotiable)**: every subprocess spawned here uses a
bounded ``timeout=`` (never blocks indefinitely -- these binaries are
known, from manual investigation during this correction, to leave a
detached daemon process alive after the immediate CLI invocation exits,
which can hold pipe handles open and block an unbounded ``communicate()``
read). Cleanup only ever targets a process whose OS command line contains
the EXACT, randomly-generated temp-workspace path used by that specific
test run -- never a bare process name/PID guess, and NEVER a PID this
module did not itself just create. Cleanup failures are logged as
non-fatal (``warnings.warn``); they never mask a real assertion failure.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import warnings
from pathlib import Path

_REAL_BINARY_SMOKE_ENABLED = os.environ.get("AUTOHARNESS_REAL_BINARY_SMOKE") == "1"
_ENGRAM_AVAILABLE = shutil.which("engram") is not None
_GRAPHTOR_DOCS_AVAILABLE = shutil.which("graphtor-docs") is not None
_IS_WINDOWS = sys.platform == "win32"

_SKIP_REASON = (
    "opt-in real-binary smoke test: set AUTOHARNESS_REAL_BINARY_SMOKE=1 with "
    "real engram/graphtor-docs binaries on PATH (Windows) to run"
)


def _kill_processes_matching(executable_name: str, path_marker: str) -> None:
    """Best-effort: terminate any ``executable_name`` process whose OS
    command line contains ``path_marker`` verbatim. Windows-only (uses
    ``Get-CimInstance``/``Stop-Process`` via a bounded ``powershell``
    subprocess call). NEVER touches a process whose command line does not
    contain the exact marker -- this is always a randomly-generated,
    per-test temp directory path, so it can never collide with an
    operator's own real workspace path. Failures are logged, never raised.
    """

    script = (
        "Get-CimInstance Win32_Process -Filter \"Name='"
        f"{executable_name}'\" | Where-Object {{ $_.CommandLine -and "
        f"$_.CommandLine.Contains('{path_marker}') }} | ForEach-Object {{ "
        "Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover - best-effort cleanup
        warnings.warn(f"real-binary smoke cleanup for {executable_name!r} failed: {exc!r}")


def _run_bounded(
    argv: list, *, env: dict, cwd: "str | None" = None, timeout: float = 30.0
) -> tuple:
    """Run ``argv`` bounded by ``timeout``, WITHOUT ever blocking on pipe EOF.

    Both ``engram``/``graphtor-docs`` were observed, during manual
    investigation for this correction, to leave a detached daemon process
    alive after their own immediate CLI invocation exits -- and that
    daemon can inherit the immediate process's stdout/stderr PIPE write
    ends, so a plain ``subprocess.run(capture_output=True, timeout=...)``
    can still hang indefinitely: CPython's own timeout handling kills the
    immediate process but then performs one final BLOCKING
    ``communicate()`` to drain remaining output, which never sees EOF
    while the detached daemon still holds the pipe open. Redirecting
    stdout/stderr to real temp FILES instead of pipes sidesteps this
    entirely: this function's own read of those files never waits for
    another process to close a handle.

    Returns ``(returncode, stdout_text, stderr_text)``. Raises
    ``subprocess.TimeoutExpired`` if the IMMEDIATE process itself does not
    exit within ``timeout`` (verified in manual testing to complete in
    ~1-2s for every command this module actually issues, so a timeout here
    is a genuine test failure signal, not expected/normal behavior).
    """

    io_dir = tempfile.mkdtemp(prefix="autoharness-real-binary-smoke-io-")
    try:
        stdout_path = Path(io_dir) / "stdout.txt"
        stderr_path = Path(io_dir) / "stderr.txt"
        with open(stdout_path, "wb") as stdout_f, open(stderr_path, "wb") as stderr_f:
            proc = subprocess.Popen(
                argv,
                env=env,
                cwd=cwd,
                stdout=stdout_f,
                stderr=stderr_f,
                stdin=subprocess.DEVNULL,
                shell=False,
            )
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=10)
                raise
        stdout_text = stdout_path.read_text(encoding="utf-8", errors="replace")
        stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace")
        return proc.returncode, stdout_text, stderr_text
    finally:
        # Best-effort only: a detached daemon spawned by `argv` (observed
        # for both engram and graphtor-docs during manual investigation)
        # can inherit these file handles and keep them open well past this
        # function's own return, making an immediate `shutil.rmtree` raise
        # `PermissionError` on Windows. Leaving a few small, uniquely-named
        # temp files behind in the OS temp directory is an acceptable,
        # bounded cost; failing the calling test over unrelated OS temp
        # directory hygiene is not.
        shutil.rmtree(io_dir, ignore_errors=True)


@unittest.skipUnless(
    _REAL_BINARY_SMOKE_ENABLED and _ENGRAM_AVAILABLE and _IS_WINDOWS, _SKIP_REASON
)
class RealEngramWorkspaceBindingTests(unittest.TestCase):
    """Reproduces (and proves the fix for) the verified live defect: a
    real ``engram`` daemon binding to a workspace supplied ONLY via the
    ``ENGRAM_WORKSPACE`` environment variable (no ``--workspace`` CLI
    flag) -- exactly the mechanism ``.mcp.json``'s bare ``engram shim``
    entry relies on, and exactly the value ``bootstrap_workspace()`` now
    force-applies.
    """

    def test_engram_binds_to_the_env_supplied_workspace_not_a_stale_one(self) -> None:
        with tempfile.TemporaryDirectory(prefix="autoharness-real-engram-") as workspace:
            resolved_workspace = str(Path(workspace).resolve())
            git_init = subprocess.run(
                ["git", "init", "-q", resolved_workspace],
                capture_output=True,
                text=True,
                timeout=30,
                shell=False,
            )
            self.assertEqual(git_init.returncode, 0, msg=git_init.stderr)

            env = dict(os.environ)
            env["ENGRAM_WORKSPACE"] = resolved_workspace
            try:
                returncode, stdout_text, stderr_text = _run_bounded(
                    ["engram", "--format", "json", "bind"], env=env, timeout=30
                )
                self.assertEqual(returncode, 0, msg=stderr_text)
                payload = json.loads(stdout_text)
                bound_path = payload["result"]["path"]
                self.assertEqual(
                    str(Path(bound_path).resolve()),
                    resolved_workspace,
                    "engram must bind to the ENGRAM_WORKSPACE-supplied workspace, "
                    "not any other (e.g. stale/ambient) workspace",
                )
            finally:
                _kill_processes_matching("engram.exe", resolved_workspace)


@unittest.skipUnless(
    _REAL_BINARY_SMOKE_ENABLED and _GRAPHTOR_DOCS_AVAILABLE and _IS_WINDOWS, _SKIP_REASON
)
class RealGraphtorDocsWorkspaceBindingTests(unittest.TestCase):
    """Proves ``graphtor-docs`` reads ``GRAPHTOR_DB_PATH``/``GRAPHTOR_
    SOURCES`` from the environment (no CLI flags), and that this module's
    design choice -- deriving both paths from the SAME ``workspace_root``
    used to anchor the child's own ``cwd`` (129-S's original fix) -- is
    required: `graphtor-docs` rejects a db/config path that resolves
    OUTSIDE its cwd-derived workspace root with a ``path_violation`` error
    (verified manually during this correction), so the two values must
    always be derived together, never independently.
    """

    def _write_minimal_config(self, workspace_root: Path) -> tuple[Path, Path]:
        config_dir = workspace_root / ".graphtor" / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        sources_path = config_dir / "sources.yaml"
        sources_path.write_text("sources: []\n", encoding="utf-8")
        db_path = workspace_root / ".graphtor" / "graph.db"
        return db_path, sources_path

    def test_status_succeeds_when_env_paths_resolve_inside_cwd_workspace_root(self) -> None:
        with tempfile.TemporaryDirectory(prefix="autoharness-real-graphtor-ok-") as workspace:
            workspace_root = Path(workspace).resolve()
            db_path, sources_path = self._write_minimal_config(workspace_root)

            env = dict(os.environ)
            env["GRAPHTOR_DB_PATH"] = str(db_path)
            env["GRAPHTOR_SOURCES"] = str(sources_path)

            _returncode, stdout_text, _stderr_text = _run_bounded(
                ["graphtor-docs", "--json", "status"],
                env=env,
                cwd=str(workspace_root),
                timeout=30,
            )
            payload = json.loads(stdout_text)
            self.assertNotIn(
                "error",
                payload,
                "graphtor-docs must accept GRAPHTOR_DB_PATH/GRAPHTOR_SOURCES "
                "that resolve inside the cwd-derived workspace root",
            )

    def test_status_rejects_env_paths_outside_cwd_workspace_root(self) -> None:
        # Documents/proves the constraint that motivates deriving both
        # binding paths from the SAME workspace_root as the anchored cwd:
        # a db path outside the cwd-derived workspace root is a
        # `path_violation`, not silently accepted. The path-violation
        # boundary check only activates once a `.graphtor/config/
        # sources.yaml` marker establishes a workspace root at `cwd` --
        # verified manually during this correction: with NO such marker
        # present, graphtor-docs has no established boundary to enforce at
        # all and silently accepts an external path instead.
        with tempfile.TemporaryDirectory(
            prefix="autoharness-real-graphtor-cwd-"
        ) as cwd_workspace, tempfile.TemporaryDirectory(
            prefix="autoharness-real-graphtor-elsewhere-"
        ) as other_workspace:
            cwd_root = Path(cwd_workspace).resolve()
            self._write_minimal_config(cwd_root)
            outside_db_path = Path(other_workspace).resolve() / ".graphtor" / "graph.db"

            env = dict(os.environ)
            env["GRAPHTOR_DB_PATH"] = str(outside_db_path)
            env.pop("GRAPHTOR_SOURCES", None)

            _returncode, stdout_text, _stderr_text = _run_bounded(
                ["graphtor-docs", "--json", "status"],
                env=env,
                cwd=str(cwd_root),
                timeout=30,
            )
            payload = json.loads(stdout_text)
            self.assertIn("error", payload)
            self.assertEqual(payload["error"].get("data", {}).get("category"), "path_violation")


if __name__ == "__main__":
    unittest.main()
