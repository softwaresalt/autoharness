"""Characterization suite for the repository-root ``start.ps1`` launcher.

This suite pins the CURRENT observable contract of ``start.ps1`` as-is. It
does NOT modify ``start.ps1``: the script under test is copied verbatim into
an isolated temporary workspace so its ``$PSScriptRoot``-relative behavior
(``.env.local`` lookup, ``COPILOT_HOME``/``ENGRAM_DATA_DIR`` defaults) can be
exercised without touching the real repository root.

External tools (``gh``, ``backlogit``, ``engram``, ``copilot``) are replaced
with small ``.cmd`` stub scripts on a fully controlled, minimal ``PATH`` so
no real network/CLI calls ever occur. Stubs are plain batch files -- NOT
PowerShell (``.ps1``) scripts -- because ``.cmd``/``.bat`` files run as
genuinely separate OS processes with independent exit codes, matching how
the real external tools behave; a ``.ps1`` stub invoked via PowerShell's
call operator would share process/runspace semantics with the parent script
in ways that do not faithfully reproduce a real external command failure.

TERMINAL ATTACHMENT LIMITATION (documented per task spec, item (i)): a full
TTY/console-inheritance assertion is not practically testable from within a
test-runner-driven subprocess harness, because the runner itself pipes
stdout/stderr of the ``pwsh`` process we spawn. What IS tested here is the closest
practical proxy: (1) a static/structural check that the final invocation
line in the actual source text contains no redirection operators
(``>``, ``2>``, ``|``, ``*>``, ``<``) and does not use ``Start-Process``
(which would detach the child from the console), and (2) a functional check
that stub-emitted stdout/stderr markers propagate all the way through to
our subprocess's captured output, proving nothing in ``start.ps1`` itself
intercepts or redirects the child's stdio streams. This does not prove
genuine interactive TTY attachment in a real terminal, only the absence of
explicit redirection in the script.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Optional

import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
START_PS1 = REPO_ROOT / "start.ps1"

PWSH = shutil.which("pwsh") or shutil.which("powershell")


def _minimal_system_path() -> str:
    """A PATH containing only base Windows system directories.

    Deliberately excludes any real developer-installed ``gh``, ``backlogit``,
    ``engram``, or ``copilot`` so that "absent" scenarios are genuinely
    absent, and "present" scenarios are unambiguously satisfied only by our
    stubs (which are always placed earlier in PATH).
    """

    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    parts = [
        os.path.join(system_root, "System32"),
        system_root,
        os.path.join(system_root, "System32", "Wbem"),
        os.path.join(system_root, "System32", "WindowsPowerShell", "v1.0"),
    ]
    return os.pathsep.join(parts)


GH_STUB = textwrap.dedent(
    r"""
    @echo off
    if defined STUB_RESULT_DIR (
        echo gh %* >> "%STUB_RESULT_DIR%\gh_calls.log"
    )
    if "%STUB_GH_FAIL%"=="1" (
        echo stub gh failure 1>&2
        exit /b 1
    )
    echo %STUB_GH_TOKEN%
    exit /b 0
    """
).strip("\n")

BACKLOGIT_STUB = textwrap.dedent(
    r"""
    @echo off
    if defined STUB_RESULT_DIR (
        echo backlogit %* >> "%STUB_RESULT_DIR%\backlogit_calls.log"
    )
    if "%STUB_BACKLOGIT_FAIL%"=="1" (
        echo stub backlogit failure 1>&2
        exit /b 1
    )
    exit /b 0
    """
).strip("\n")

ENGRAM_STUB = textwrap.dedent(
    r"""
    @echo off
    set "ARGS=%*"
    if defined STUB_RESULT_DIR (
        echo engram %ARGS% >> "%STUB_RESULT_DIR%\engram_calls.log"
    )
    echo %ARGS%| findstr /C:"bind" >nul
    if %ERRORLEVEL%==0 goto :handle_bind

    echo %ARGS%| findstr /C:"--direct" >nul
    if %ERRORLEVEL%==0 goto :handle_direct

    if "%STUB_ENGRAM_FALLBACK_FAIL%"=="1" (
        echo stub engram fallback failure 1>&2
        exit /b 1
    )
    exit /b 0

    :handle_bind
    if "%STUB_ENGRAM_BIND_FAIL%"=="1" (
        echo stub engram bind failure 1>&2
        exit /b 1
    )
    exit /b 0

    :handle_direct
    if "%STUB_ENGRAM_DIRECT_FAIL%"=="1" (
        echo stub engram direct failure 1>&2
        exit /b 1
    )
    exit /b 0
    """
).strip("\n")

COPILOT_STUB = textwrap.dedent(
    r"""
    @echo off
    > "%STUB_RESULT_DIR%\copilot_args.txt" (
        echo %*
    )
    > "%STUB_RESULT_DIR%\copilot_env.txt" (
        set
    )
    echo COPILOT_STUB_STDOUT_MARKER
    echo COPILOT_STUB_STDERR_MARKER 1>&2
    if not "%STUB_COPILOT_EXIT_CODE%"=="" (
        exit /b %STUB_COPILOT_EXIT_CODE%
    )
    exit /b 0
    """
).strip("\n")


def _parse_env_dump(text: str) -> dict:
    """Parse the output of the batch builtin ``set`` into a dict."""

    env = {}
    for line in text.splitlines():
        if "=" not in line:
            continue
        name, _, value = line.partition("=")
        env[name] = value
    return env


class Sandbox:
    """A single isolated invocation environment for ``start.ps1``."""

    def __init__(self, tmp_path: Path):
        self.workspace = tmp_path / "workspace"
        self.workspace.mkdir()
        self.stub_dir = tmp_path / "stubs"
        self.stub_dir.mkdir()
        self.result_dir = tmp_path / "results"
        self.result_dir.mkdir()
        shutil.copy2(START_PS1, self.workspace / "start.ps1")

    def write_env_local(self, content: str) -> None:
        (self.workspace / ".env.local").write_text(content, encoding="utf-8", newline="")

    def install_stub(self, name: str, content: str) -> None:
        (self.stub_dir / f"{name}.cmd").write_text(content, encoding="utf-8")

    def run(
        self,
        argv: Optional[list] = None,
        extra_env: Optional[dict] = None,
        timeout: float = 30.0,
    ) -> subprocess.CompletedProcess:
        env = {
            "SystemRoot": os.environ.get("SystemRoot", r"C:\Windows"),
            "ComSpec": os.environ.get("ComSpec", r"C:\Windows\System32\cmd.exe"),
            "PATH": str(self.stub_dir) + os.pathsep + _minimal_system_path(),
            # PATHEXT is required for PowerShell's bare-name command
            # resolution (e.g. `gh auth token`) to recognize `.cmd` stub
            # scripts as executables; subprocess.run's `env=` fully replaces
            # the child environment, so this must be supplied explicitly.
            "PATHEXT": os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD"),
            "TEMP": os.environ.get("TEMP", str(self.result_dir)),
            "TMP": os.environ.get("TMP", str(self.result_dir)),
            "STUB_RESULT_DIR": str(self.result_dir),
        }
        if extra_env:
            env.update(extra_env)
        cmd = [PWSH, "-NoProfile", "-NonInteractive", "-File", str(self.workspace / "start.ps1")]
        if argv:
            cmd.extend(argv)
        return subprocess.run(
            cmd,
            cwd=str(self.workspace),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def copilot_env(self) -> Optional[dict]:
        path = self.result_dir / "copilot_env.txt"
        if not path.exists():
            return None
        return _parse_env_dump(path.read_text(encoding="utf-8", errors="replace"))

    def copilot_args(self) -> Optional[str]:
        path = self.result_dir / "copilot_args.txt"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8").strip("\r\n")

    def calls_log(self, name: str) -> list:
        path = self.result_dir / f"{name}_calls.log"
        if not path.exists():
            return []
        return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]




@unittest.skipIf(PWSH is None, "no pwsh/powershell executable found on PATH")
class StartPs1CharacterizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.sandbox = Sandbox(Path(self._tmpdir.name))
        self.sandbox.install_stub("gh", GH_STUB)
        self.sandbox.install_stub("backlogit", BACKLOGIT_STUB)
        self.sandbox.install_stub("engram", ENGRAM_STUB)
        self.sandbox.install_stub("copilot", COPILOT_STUB)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # ---------------------------------------------------------------------------
    # (a) .env.local parsing: KEY=VALUE only, single matching quote pair
    #     stripped, NO-CLOBBER (pre-set process var wins).
    # ---------------------------------------------------------------------------


    def test_env_local_parses_plain_and_quoted_values(self):
        self.sandbox.write_env_local(
            "\n".join(
                [
                    "PLAIN_VALUE=hello",
                    'DOUBLE_QUOTED="hello world"',
                    "SINGLE_QUOTED='hello world'",
                    "MISMATCHED_QUOTES=\"hello'",
                    "lowercase_ignored=nope",
                    "",
                ]
            )
        )
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["PLAIN_VALUE"] == "hello"
        assert env["DOUBLE_QUOTED"] == "hello world"
        assert env["SINGLE_QUOTED"] == "hello world"
        # Mismatched surrounding quotes (" ... ') are NOT a matching pair, so
        # they are left untouched verbatim.
        assert env["MISMATCHED_QUOTES"] == '"hello\''
        # The regex uses PowerShell's default CASE-INSENSITIVE `-match` operator,
        # so `[A-Z_][A-Z0-9_]*` also matches lower-case names -- baseline
        # evidence: lower-case keys ARE parsed and set (not ignored).
        assert env["lowercase_ignored"] == "nope"


    def test_env_local_no_clobber_pre_set_process_var_wins(self):
        self.sandbox.write_env_local("MY_CUSTOM_VAR=from_file\n")
        result = self.sandbox.run(
            extra_env={
                "STUB_GH_TOKEN": "tok",
                "MY_CUSTOM_VAR": "from_process",
            }
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env["MY_CUSTOM_VAR"] == "from_process"


    # ---------------------------------------------------------------------------
    # (b) COPILOT_HOME / ENGRAM_DATA_DIR defaults, honoring a pre-set value.
    # ---------------------------------------------------------------------------


    def test_copilot_home_and_engram_data_dir_default_to_workspace_subdirs(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert os.path.realpath(env["COPILOT_HOME"]) == os.path.realpath(
            str(self.sandbox.workspace / ".copilot")
        )
        assert os.path.realpath(env["ENGRAM_DATA_DIR"]) == os.path.realpath(
            str(self.sandbox.workspace / ".engram")
        )


    def test_copilot_home_and_engram_data_dir_honor_preset_values(self):
        result = self.sandbox.run(
            extra_env={
                "STUB_GH_TOKEN": "tok",
                "COPILOT_HOME": r"C:\custom\copilot-home",
                "ENGRAM_DATA_DIR": r"C:\custom\engram-data",
            }
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env["COPILOT_HOME"] == r"C:\custom\copilot-home"
        assert env["ENGRAM_DATA_DIR"] == r"C:\custom\engram-data"


    # ---------------------------------------------------------------------------
    # (c) Two separate token-resolution contracts.
    # ---------------------------------------------------------------------------


    def test_github_token_resolved_only_when_unset_via_guarded_gh(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "guarded-token"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env["GITHUB_TOKEN"] == "guarded-token"


    def test_github_token_preset_is_not_overwritten_and_gh_called_once(self):
        result = self.sandbox.run(
            extra_env={"STUB_GH_TOKEN": "guarded-token", "GITHUB_TOKEN": "already-set"}
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env["GITHUB_TOKEN"] == "already-set"
        # Exactly one gh invocation: the unconditional GITHUB_PERSONAL_ACCESS_TOKEN
        # assignment. The guarded GITHUB_TOKEN branch is skipped entirely because
        # GITHUB_TOKEN was already set -- it must NOT call `gh` a second time.
        assert len(self.sandbox.calls_log("gh")) == 1


    def test_github_personal_access_token_assigned_unconditionally_and_unguarded(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "pat-token"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env["GITHUB_PERSONAL_ACCESS_TOKEN"] == "pat-token"


    def test_github_token_guard_is_non_fatal_when_gh_auth_token_fails(self):
        """When `gh` is present but `gh auth token` fails, the GUARDED
        GITHUB_TOKEN branch is non-fatal (try/catch): the script proceeds to
        invoke copilot. The UNGUARDED GITHUB_PERSONAL_ACCESS_TOKEN assignment is
        baseline-pinned as producing an EMPTY value on failure (Write-Error is a
        non-terminating error; the captured stdout of the failed command is
        empty), not a script abort -- this is baseline evidence only, not a
        mandate. Note: PowerShell's Write-Warning writes to the Warning stream,
        which is rendered into STDOUT (not STDERR) for this non-interactive
        `pwsh -File` invocation -- empirically verified separately -- so the
        warning text is looked for in stdout.
        """

        result = self.sandbox.run(extra_env={"STUB_GH_FAIL": "1"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None, "copilot must still be invoked (non-fatal failure)"
        assert env["GITHUB_PERSONAL_ACCESS_TOKEN"] == ""
        assert "GITHUB_TOKEN" not in env or env["GITHUB_TOKEN"] == ""
        assert "gh auth token failed" in result.stdout


    def test_gh_entirely_absent_is_a_non_terminating_error_script_continues(self):
        """BASELINE EVIDENCE ONLY (surprising, empirically verified): with `gh`
        entirely absent from PATH, PowerShell's "command not found" is a
        NON-TERMINATING error at the default $ErrorActionPreference ('Continue').
        The UNGUARDED `(gh auth token)` expression therefore does NOT abort the
        script -- it emits an error record (visible on stderr) and the
        expression evaluates to nothing, so the assignment effectively clears
        GITHUB_PERSONAL_ACCESS_TOKEN. Execution continues normally all the way
        to invoking copilot. This directly contradicts a naive reading of "gh
        absent aborts the script" and is pinned here as the real baseline,
        verified via a minimal isolated repro before writing this assertion.
        """

        (self.sandbox.stub_dir / "gh.cmd").unlink()
        result = self.sandbox.run()
        assert result.returncode == 0, result.stderr
        assert "is not recognized" in result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None, "script continues past the failed gh call to invoke copilot"
        assert env.get("GITHUB_PERSONAL_ACCESS_TOKEN", "") == ""


    # ---------------------------------------------------------------------------
    # (d) Copilot exe resolution order + hard failure message.
    # ---------------------------------------------------------------------------


    def test_copilot_exe_path_takes_precedence(self):
        fake_exe = self.sandbox.stub_dir / "custom_copilot.cmd"
        fake_exe.write_text(COPILOT_STUB, encoding="utf-8")
        result = self.sandbox.run(
            extra_env={
                "STUB_GH_TOKEN": "tok",
                "COPILOT_EXE_PATH": str(fake_exe),
                "COPILOT_EXE": str(self.sandbox.stub_dir / "other_copilot.cmd"),
            }
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None


    def test_copilot_exe_env_var_used_when_exe_path_unset(self):
        fake_exe = self.sandbox.stub_dir / "custom_copilot2.cmd"
        fake_exe.write_text(COPILOT_STUB, encoding="utf-8")
        (self.sandbox.stub_dir / "copilot.cmd").unlink()  # remove PATH resolution candidate
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "COPILOT_EXE": str(fake_exe)})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None


    def test_copilot_resolved_from_path_when_no_explicit_vars_set(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok"})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None


    def test_copilot_unresolvable_raises_actionable_error(self):
        (self.sandbox.stub_dir / "copilot.cmd").unlink()
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok"})
        assert result.returncode != 0
        assert "Unable to locate Copilot CLI" in result.stderr


    # ---------------------------------------------------------------------------
    # (e) --remote appended only when COPILOT_USE_REMOTE is true/1 (case
    #     insensitive) AND the operator didn't already pass --remote.
    # ---------------------------------------------------------------------------


    def test_remote_flag_appended_when_use_remote_truthy(self):
        for value in ["true", "True", "TRUE", "1"]:
            with self.subTest(value=value):
                result = self.sandbox.run(argv=["foo"], extra_env={"STUB_GH_TOKEN": "tok", "COPILOT_USE_REMOTE": value})
                assert result.returncode == 0, result.stderr
                assert self.sandbox.copilot_args() == "--remote foo"


    def test_remote_flag_not_appended_when_use_remote_not_truthy(self):
        for value in ["false", "0", "yes", ""]:
            with self.subTest(value=value):
                result = self.sandbox.run(argv=["foo"], extra_env={"STUB_GH_TOKEN": "tok", "COPILOT_USE_REMOTE": value})
                assert result.returncode == 0, result.stderr
                assert self.sandbox.copilot_args() == "foo"


    def test_remote_flag_not_duplicated_when_operator_already_passed_it(self):
        result = self.sandbox.run(
            argv=["--remote", "foo"], extra_env={"STUB_GH_TOKEN": "tok", "COPILOT_USE_REMOTE": "true"}
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_args() == "--remote foo"


    # ---------------------------------------------------------------------------
    # (f) operator argv forwarded verbatim.
    # ---------------------------------------------------------------------------


    def test_operator_argv_forwarded_verbatim(self):
        result = self.sandbox.run(argv=["alpha", "--flag", "value123"], extra_env={"STUB_GH_TOKEN": "tok"})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_args() == "alpha --flag value123"


    # ---------------------------------------------------------------------------
    # (g) child exit code propagation -- BASELINE EVIDENCE ONLY.
    #
    # EMPIRICAL FINDING: start.ps1's final statement is a bare
    # `& $copilotExe @copilotArguments` with no trailing `exit $LASTEXITCODE`.
    # In this environment $PSNativeCommandUseErrorActionPreference is $false
    # (verified via `pwsh -Command '$PSNativeCommandUseErrorActionPreference'`),
    # and pwsh's default top-level script exit code is 0 when the script runs to
    # completion without an unhandled terminating error -- regardless of
    # $LASTEXITCODE from the final native command. This means the CURRENT
    # observable behavior is that the child's exit code is NOT propagated to the
    # pwsh host process's own exit code; the host always exits 0 on a normal
    # (non-throwing) run. This directly contradicts a naive reading of "exit
    # code propagated unchanged" and is pinned here as the actual baseline.
    # ---------------------------------------------------------------------------


    def test_pwsh_host_exit_code_does_not_mirror_child_exit_code(self):
        for child_exit_code in ["0", "3", "7"]:
            with self.subTest(child_exit_code=child_exit_code):
                result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": child_exit_code})
                # Baseline: the wrapper's own exit code is always 0 here, never the
                # child's code, because start.ps1 never reads/propagates $LASTEXITCODE.
                assert result.returncode == 0, (
                    f"expected host exit code 0 regardless of child exit {child_exit_code}, "
                    f"got {result.returncode}"
                )


    # ---------------------------------------------------------------------------
    # (h) Sidecar side effects: backlogit sync + Engram pre-warm, each optional
    #     and non-fatal.
    # ---------------------------------------------------------------------------


    def test_backlogit_sync_runs_when_resolved(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok"})
        assert result.returncode == 0, result.stderr
        calls = self.sandbox.calls_log("backlogit")
        assert any("sync" in c for c in calls)


    def test_backlogit_sync_failure_is_non_fatal(self):
        """BASELINE EVIDENCE ONLY (surprising, empirically verified): the
        `backlogit sync` try/catch has NO explicit `$LASTEXITCODE` check --
        unlike the Engram helper's explicit `throw` on nonzero exit code. In
        this pwsh environment $PSNativeCommandUseErrorActionPreference is
        $false, so a NONZERO exit from a native command like our failing
        `backlogit.cmd` stub does NOT raise a terminating exception by default,
        meaning the `catch` block is effectively unreachable via an ordinary
        failing exit code alone: no "backlogit sync failed" warning is ever
        printed, and execution proceeds exactly as if the call had succeeded.
        Verified via a minimal isolated repro (`try { & failing.cmd } catch {
        ... }` prints nothing, $LASTEXITCODE=1) before writing this assertion.
        """

        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_BACKLOGIT_FAIL": "1"})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None
        calls = self.sandbox.calls_log("backlogit")
        assert any("sync" in c for c in calls), "backlogit sync must still be attempted"
        assert "backlogit sync failed" not in result.stdout
        assert "backlogit sync failed" not in result.stderr


    def test_backlogit_absent_is_skipped_silently(self):
        (self.sandbox.stub_dir / "backlogit.cmd").unlink()
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok"})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None


    def test_engram_direct_prewarm_happy_path(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok"})
        assert result.returncode == 0, result.stderr
        calls = self.sandbox.calls_log("engram")
        assert len(calls) == 1
        assert "--direct" in calls[0]


    def test_engram_direct_failure_falls_back_to_bind_and_daemon_sync(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_ENGRAM_DIRECT_FAIL": "1"})
        assert result.returncode == 0, result.stderr
        calls = self.sandbox.calls_log("engram")
        assert len(calls) == 3
        assert "--direct" in calls[0]
        assert "bind" in calls[1]
        assert "sync" in calls[2] and "--direct" not in calls[2]
        assert self.sandbox.copilot_env() is not None


    def test_engram_fallback_failure_is_non_fatal(self):
        """Unlike the backlogit path, the Engram helper explicitly checks
        $LASTEXITCODE and `throw`s -- an explicit `throw` is always a
        terminating exception regardless of $PSNativeCommandUseErrorActionPreference,
        so the enclosing try/catch reliably fires and the warning IS printed
        (to stdout, per Write-Warning's stream routing in this environment)."""

        result = self.sandbox.run(
            extra_env={
                "STUB_GH_TOKEN": "tok",
                "STUB_ENGRAM_DIRECT_FAIL": "1",
                "STUB_ENGRAM_BIND_FAIL": "1",
                "STUB_ENGRAM_FALLBACK_FAIL": "1",
            }
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None
        assert "engram sync failed" in result.stdout


    def test_engram_absent_is_skipped_silently(self):
        (self.sandbox.stub_dir / "engram.cmd").unlink()
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok"})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None
        assert self.sandbox.calls_log("engram") == []


    # ---------------------------------------------------------------------------
    # (i) Terminal attachment (structural proxy + functional stdio pass-through).
    # ---------------------------------------------------------------------------


    def test_final_invocation_line_has_no_stdio_redirection(self):
        """Structural proxy: the source text of the actual (unmodified)
        start.ps1's final invocation contains no redirection operators and does
        not use Start-Process (which would detach the child)."""

        source = START_PS1.read_text(encoding="utf-8")
        lines = [line.strip() for line in source.splitlines() if line.strip()]
        final_invocation = lines[-1]
        assert final_invocation.startswith("& $copilotExe")
        for operator in (">", "2>", "1>", "*>", "|", "<"):
            assert operator not in final_invocation, (
                f"unexpected redirection operator {operator!r} in final invocation line"
            )
        assert "Start-Process" not in source


    def test_child_stdio_is_not_intercepted_functionally(self):
        """Functional proxy: stub-emitted stdout/stderr markers surface all the
        way through to our subprocess's captured output, showing start.ps1 does
        not redirect or swallow the child's stdio. This does NOT prove genuine
        interactive TTY/console attachment (our own harness pipes pwsh's stdio to
        capture it) -- see module docstring for the documented limitation."""

        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok"})
        assert result.returncode == 0, result.stderr
        assert "COPILOT_STUB_STDOUT_MARKER" in result.stdout
        assert "COPILOT_STUB_STDERR_MARKER" in result.stderr


if __name__ == "__main__":
    unittest.main()
