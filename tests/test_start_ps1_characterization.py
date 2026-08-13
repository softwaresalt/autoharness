"""Characterization suite for the repository-root ``start.ps1`` launcher.

POST-MIGRATION (120.007-T / shipment 129-S): ``start.ps1`` is now a THIN
COMPATIBILITY SHIM -- it contains no bootstrap/sidecar/resolve policy of its
own. All of that policy now lives in ``src/autoharness/supervise/``
(``bootstrap.py``, ``sidecar.py``, ``resolve.py``, ``app.py``) and is
invoked, end-to-end, via a single ``autoharness run --workspace
$PSScriptRoot @args`` call followed by ``exit $LASTEXITCODE``.

This suite exercises the REAL migrated architecture end-to-end wherever
practical: the actual (unmodified) ``start.ps1`` is copied into an isolated
temp workspace and invoked via a real ``pwsh``, with a fully-controlled,
hermetic ``PATH`` that includes (a) small ``.cmd`` stubs for the external
tools ``gh``/``backlogit``/``engram``/``copilot`` (unchanged from the
pre-migration suite -- the new Python implementation invokes these tools
with the IDENTICAL argv shapes the old inline PowerShell did) and (b) the
real installed ``autoharness`` console script's own directory (resolved via
``shutil.which("autoharness")`` at collection time), so the REAL
``bootstrap.py``/``sidecar.py``/``resolve.py``/``app.py`` chain runs inside
the sandboxed ``pwsh`` subprocess.

Structural "genuinely thin shim" lexical assertions (no subprocess required)
are also included: they assert the shim's OWN source text contains none of
the bootstrap/sidecar/resolve/``--remote`` policy tokens that used to live
inline, so an accidental re-introduction of duplicated policy fails fast
without needing a live sandbox run.

APPROVED BEHAVIOR DELTAS pinned by this suite (see
``docs/design-docs/2026-08-12-supervisor-observability-rollout-rollback.md``
and ``src/autoharness/supervise/bootstrap.py`` for the authoritative
rationale):

* DELTA 1 (WINDOWS_PAT_NO_GH) -- ``gh`` absent/failing is non-fatal, leaves
  the affected variable(s) UNSET (never empty-string), same as it always was
  on POSIX.
* DELTA 2 (POSIX_ENGRAM_DATA_DIR) -- covered by the POSIX suite
  (``test_start_sh_characterization.py``); this file only pins the
  Windows-side ``ENGRAM_DATA_DIR`` default, which is unchanged in shape but
  now resolved via ``bootstrap.py`` rather than inline PowerShell.
* DELTA 3 (POSIX_PAT_BOOTSTRAP) -- covered by the POSIX suite.
* PAT guard asymmetry is PRESERVED BYTE-IDENTICAL, not unified (this is
  deliberately NOT a fourth delta): the pre-migration script resolved
  ``GITHUB_TOKEN`` (guarded/no-clobber) and ``GITHUB_PERSONAL_ACCESS_TOKEN``
  (UNGUARDED, always re-resolved when ``gh`` is available) as two SEPARATE
  per-variable contracts. ``bootstrap.py`` preserves this exact asymmetry
  rather than unifying it -- unifying the two variables' guard behavior
  with each other would be an unnamed additional delta outside the approved
  three-entry matrix (ruling A, 2026-08-12), which only names DELTA 1
  (WINDOWS_PAT_NO_GH), DELTA 2 (POSIX_ENGRAM_DATA_DIR), and DELTA 3
  (POSIX_PAT_BOOTSTRAP).
* DELTA 5 (H3 EXIT CODE FIX) -- the pre-migration ``start.ps1`` had NO
  ``exit $LASTEXITCODE`` after its final invocation, so the host process's
  own exit code was ALWAYS 0 regardless of the supervised child's real exit
  code (pinned by the old suite as
  ``test_pwsh_host_exit_code_does_not_mirror_child_exit_code``, itself
  documented as a latent bug). The new shim's ``exit $LASTEXITCODE`` is a
  deliberate, task-mandated (H3) fix: this suite now pins VERBATIM exit-code
  propagation as the new, correct, intended behavior.

VALIDATION DEPTH NOTE: not every pre-migration assertion is re-validated
end-to-end through a live sandbox run in this file. Assertions covering
``bootstrap.py``/``sidecar.py``/``resolve.py``'s own internal decision
logic in exhaustive per-branch detail are already covered far more cheaply
and thoroughly by ``tests/test_supervise_bootstrap.py``,
``tests/test_supervise_sidecar.py``, and ``tests/test_supervise_resolve.py``
(unit level, no subprocess). This file's end-to-end tests are a
representative, high-value subset proving the WIRING through the actual
shim script is correct (workspace anchoring, argv/exit-code passthrough,
tool resolution order, sidecar invocation, terminal env var names actually
reaching the child) -- not a second exhaustive copy of every unit-level
branch.
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
START_PS1_TMPL = REPO_ROOT / "templates" / "scripts" / "start.ps1.tmpl"

PWSH = shutil.which("pwsh") or shutil.which("powershell")
_AUTOHARNESS_EXE = shutil.which("autoharness")
AUTOHARNESS_BIN_DIR = str(Path(_AUTOHARNESS_EXE).parent) if _AUTOHARNESS_EXE else None

# This sandbox's stub mechanism is Windows-only BY DESIGN: stub commands are
# plain .cmd/batch scripts resolved via Windows' PATHEXT bare-name lookup.
IS_WINDOWS = sys.platform == "win32"


def _minimal_system_path() -> str:
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

    def _env(self, extra_env: Optional[dict]) -> dict:
        path_parts = [str(self.stub_dir)]
        if AUTOHARNESS_BIN_DIR:
            path_parts.append(AUTOHARNESS_BIN_DIR)
        path_parts.append(_minimal_system_path())
        env = {
            "SystemRoot": os.environ.get("SystemRoot", r"C:\Windows"),
            "ComSpec": os.environ.get("ComSpec", r"C:\Windows\System32\cmd.exe"),
            "PATH": os.pathsep.join(path_parts),
            # PATHEXT is required for bare-name command resolution (both the
            # `.cmd` stubs AND `autoharness.exe` via PATHEXT's `.EXE` entry)
            # to work; subprocess.run's `env=` fully replaces the child
            # environment, so this must be supplied explicitly.
            "PATHEXT": os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD"),
            "TEMP": os.environ.get("TEMP", str(self.result_dir)),
            "TMP": os.environ.get("TMP", str(self.result_dir)),
            "USERPROFILE": os.environ.get("USERPROFILE", str(self.result_dir)),
            "STUB_RESULT_DIR": str(self.result_dir),
        }
        if extra_env:
            env.update(extra_env)
        return env

    def run(
        self,
        argv: Optional[list] = None,
        extra_env: Optional[dict] = None,
        timeout: float = 60.0,
    ) -> subprocess.CompletedProcess:
        cmd = [PWSH, "-NoProfile", "-NonInteractive", "-File", str(self.workspace / "start.ps1")]
        if argv:
            cmd.extend(argv)
        return subprocess.run(
            cmd,
            cwd=str(self.workspace),
            env=self._env(extra_env),
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


# ---------------------------------------------------------------------------
# Structural "genuinely thin shim" lexical checks -- no subprocess needed.
# ---------------------------------------------------------------------------


_BANNED_TOKENS = (
    ".env.local",
    "COPILOT_HOME",
    "ENGRAM_DATA_DIR",
    "GITHUB_PERSONAL_ACCESS_TOKEN",
    "GITHUB_TOKEN",
    "gh auth token",
    "backlogit",
    "engram",
    "--remote",
    "COPILOT_USE_REMOTE",
    "AUTOHARNESS_SUPERVISOR",
)


class ShimIsGenuinelyThinTests(unittest.TestCase):
    """Structural checks that need no sandbox/subprocess at all."""

    def test_start_ps1_contains_no_bootstrap_sidecar_resolve_policy(self):
        text = START_PS1.read_text(encoding="utf-8")
        for token in _BANNED_TOKENS:
            self.assertNotIn(token, text, f"start.ps1 must not contain {token!r}")

    def test_start_ps1_tmpl_contains_no_bootstrap_sidecar_resolve_policy(self):
        text = START_PS1_TMPL.read_text(encoding="utf-8")
        for token in _BANNED_TOKENS:
            self.assertNotIn(token, text, f"start.ps1.tmpl must not contain {token!r}")

    def test_start_ps1_invokes_autoharness_run(self):
        text = START_PS1.read_text(encoding="utf-8")
        self.assertIn("autoharness run", text)

    def test_start_ps1_propagates_exit_code(self):
        text = START_PS1.read_text(encoding="utf-8")
        self.assertIn("exit $LASTEXITCODE", text)

    def test_start_ps1_tmpl_preserves_project_name_placeholder(self):
        text = START_PS1_TMPL.read_text(encoding="utf-8")
        self.assertIn("{{PROJECT_NAME}}", text)

    def test_start_ps1_final_invocation_has_no_stdio_redirection(self):
        """Structural proxy: no redirection operator, no Start-Process (which
        would detach the child from the console)."""

        source = START_PS1.read_text(encoding="utf-8")
        lines = [line.strip() for line in source.splitlines() if line.strip() and not line.strip().startswith("#")]
        invocation_lines = [line for line in lines if line.startswith("autoharness run")]
        assert len(invocation_lines) == 1
        invocation = invocation_lines[0]
        for operator in (">", "2>", "1>", "*>", "|", "<"):
            assert operator not in invocation, f"unexpected redirection operator {operator!r}"
        assert "Start-Process" not in source


@unittest.skipIf(
    not IS_WINDOWS or PWSH is None or AUTOHARNESS_BIN_DIR is None,
    "Windows-only sandbox (Windows-specific .cmd stub mechanism); requires "
    "a pwsh/powershell executable AND a resolvable `autoharness` console "
    "script found on PATH",
)
class StartPs1EndToEndTests(unittest.TestCase):
    """End-to-end characterization: real pwsh -> real `autoharness run` ->
    real bootstrap.py/sidecar.py/resolve.py/app.py -> stub external tools."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.sandbox = Sandbox(Path(self._tmpdir.name))
        self.sandbox.install_stub("gh", GH_STUB)
        self.sandbox.install_stub("backlogit", BACKLOGIT_STUB)
        self.sandbox.install_stub("engram", ENGRAM_STUB)
        self.sandbox.install_stub("copilot", COPILOT_STUB)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- .env.local: no-clobber + quote stripping -----------------------

    def test_env_local_parses_plain_and_quoted_values(self):
        self.sandbox.write_env_local(
            "\n".join(
                [
                    "PLAIN_VALUE=hello",
                    'DOUBLE_QUOTED="hello world"',
                    "SINGLE_QUOTED='hello world'",
                    "MISMATCHED_QUOTES=\"hello'",
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
        assert env["MISMATCHED_QUOTES"] == '"hello\''

    def test_env_local_no_clobber_pre_set_process_var_wins(self):
        self.sandbox.write_env_local("MY_CUSTOM_VAR=from_file\n")
        result = self.sandbox.run(
            extra_env={
                "STUB_GH_TOKEN": "tok",
                "STUB_COPILOT_EXIT_CODE": "0",
                "MY_CUSTOM_VAR": "from_process",
            }
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env["MY_CUSTOM_VAR"] == "from_process"

    # -- COPILOT_HOME / ENGRAM_DATA_DIR defaults, anchored to $PSScriptRoot --

    def test_copilot_home_and_engram_data_dir_default_to_workspace_subdirs(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
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
                "STUB_COPILOT_EXIT_CODE": "0",
                "COPILOT_HOME": r"C:\custom\copilot-home",
                "ENGRAM_DATA_DIR": r"C:\custom\engram-data",
            }
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env["COPILOT_HOME"] == r"C:\custom\copilot-home"
        assert env["ENGRAM_DATA_DIR"] == r"C:\custom\engram-data"

    # -- GitHub token resolution: per-variable guard asymmetry preserved --
    # -- byte-identical to the pre-migration script (GITHUB_TOKEN guarded, --
    # -- GITHUB_PERSONAL_ACCESS_TOKEN unguarded/always re-resolved).       --

    def test_github_tokens_resolved_from_gh_when_both_unset(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "resolved-token", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env["GITHUB_TOKEN"] == "resolved-token"
        assert env["GITHUB_PERSONAL_ACCESS_TOKEN"] == "resolved-token"
        # Two independent gh invocations (one per variable), matching the
        # pre-migration script's own call pattern (PAT unconditionally,
        # GITHUB_TOKEN separately when unset).
        assert len(self.sandbox.calls_log("gh")) == 2

    def test_github_token_preset_is_not_overwritten_and_gh_still_called_for_the_other(self):
        result = self.sandbox.run(
            extra_env={
                "STUB_GH_TOKEN": "resolved-token",
                "STUB_COPILOT_EXIT_CODE": "0",
                "GITHUB_TOKEN": "already-set",
            }
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env["GITHUB_TOKEN"] == "already-set"
        assert env["GITHUB_PERSONAL_ACCESS_TOKEN"] == "resolved-token"
        assert len(self.sandbox.calls_log("gh")) == 1

    def test_github_token_preset_pat_is_still_unguarded_reresolved(self):
        """GITHUB_PERSONAL_ACCESS_TOKEN is UNGUARDED -- byte-identical to the
        pre-migration script's unconditional `$env:GITHUB_PERSONAL_ACCESS_TOKEN
        = (gh auth token)` assignment -- so even when already set, it is
        re-resolved whenever gh is available. Only GITHUB_TOKEN is guarded."""

        result = self.sandbox.run(
            extra_env={
                "STUB_GH_TOKEN": "resolved-token",
                "STUB_COPILOT_EXIT_CODE": "0",
                "GITHUB_TOKEN": "already-set-1",
                "GITHUB_PERSONAL_ACCESS_TOKEN": "already-set-2",
            }
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env["GITHUB_TOKEN"] == "already-set-1"
        assert env["GITHUB_PERSONAL_ACCESS_TOKEN"] == "resolved-token"
        assert len(self.sandbox.calls_log("gh")) == 1

    # -- DELTA 1 (WINDOWS_PAT_NO_GH): gh absent/failing is non-fatal, leaves --
    # -- the token variables UNSET (never empty string).                    --

    def test_delta1_windows_pat_no_gh_absent_is_non_fatal_and_leaves_vars_unset(self):
        self.sandbox.stub_dir.joinpath("gh.cmd").unlink()
        result = self.sandbox.run(extra_env={"STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None, "script must still reach and invoke copilot (non-fatal)"
        assert "GITHUB_TOKEN" not in env
        assert "GITHUB_PERSONAL_ACCESS_TOKEN" not in env
        assert "not found on PATH" in result.stdout or "not found on PATH" in result.stderr

    def test_delta1_windows_pat_no_gh_failing_is_non_fatal_and_leaves_vars_unset(self):
        result = self.sandbox.run(extra_env={"STUB_GH_FAIL": "1", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert "GITHUB_TOKEN" not in env
        assert "GITHUB_PERSONAL_ACCESS_TOKEN" not in env

    # -- Copilot exe resolution order + hard failure message ------------

    def test_copilot_exe_path_takes_precedence(self):
        fake_exe = self.sandbox.stub_dir / "custom_copilot.cmd"
        fake_exe.write_text(COPILOT_STUB, encoding="utf-8")
        result = self.sandbox.run(
            extra_env={
                "STUB_GH_TOKEN": "tok",
                "STUB_COPILOT_EXIT_CODE": "0",
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
        result = self.sandbox.run(
            extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0", "COPILOT_EXE": str(fake_exe)}
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None

    def test_copilot_resolved_from_path_when_no_explicit_vars_set(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None

    def test_copilot_unresolvable_raises_actionable_error_and_exits_nonzero(self):
        (self.sandbox.stub_dir / "copilot.cmd").unlink()
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok"})
        assert result.returncode != 0
        assert "Unable to locate Copilot CLI" in result.stdout or "Unable to locate Copilot CLI" in result.stderr
        assert "COPILOT_EXE_PATH" in result.stdout or "COPILOT_EXE_PATH" in result.stderr

    # -- --remote composition (now unified/shared with POSIX; still gated) --

    def test_remote_flag_appended_when_use_remote_truthy(self):
        for value in ["true", "True", "TRUE", "1"]:
            with self.subTest(value=value):
                result = self.sandbox.run(
                    argv=["foo"],
                    extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0", "COPILOT_USE_REMOTE": value},
                )
                assert result.returncode == 0, result.stderr
                assert self.sandbox.copilot_args() == "--remote foo"

    def test_remote_flag_not_appended_when_use_remote_not_truthy(self):
        for value in ["false", "0", "yes", ""]:
            with self.subTest(value=value):
                result = self.sandbox.run(
                    argv=["foo"],
                    extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0", "COPILOT_USE_REMOTE": value},
                )
                assert result.returncode == 0, result.stderr
                assert self.sandbox.copilot_args() == "foo"

    def test_remote_flag_not_duplicated_when_operator_already_passed_it(self):
        result = self.sandbox.run(
            argv=["--remote", "foo"],
            extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0", "COPILOT_USE_REMOTE": "true"},
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_args() == "--remote foo"

    # -- operator argv forwarded verbatim --------------------------------

    def test_operator_argv_forwarded_verbatim(self):
        result = self.sandbox.run(
            argv=["alpha", "--flag", "value123"],
            extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"},
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_args() == "alpha --flag value123"

    # -- DELTA 5 (H3): exit code now propagates VERBATIM (bug fix) -------

    def test_child_exit_code_propagates_verbatim(self):
        for child_exit_code in ["0", "3", "7"]:
            with self.subTest(child_exit_code=child_exit_code):
                result = self.sandbox.run(
                    extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": child_exit_code}
                )
                assert result.returncode == int(child_exit_code), (
                    f"expected host exit code {child_exit_code} (verbatim propagation, "
                    f"H3 fix), got {result.returncode}"
                )

    # -- Sidecar side effects: backlogit sync + Engram pre-warm ----------

    def test_backlogit_sync_runs_when_resolved(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        calls = self.sandbox.calls_log("backlogit")
        assert any("sync" in c for c in calls)

    def test_backlogit_sync_failure_is_non_fatal(self):
        result = self.sandbox.run(
            extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0", "STUB_BACKLOGIT_FAIL": "1"}
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None
        calls = self.sandbox.calls_log("backlogit")
        assert any("sync" in c for c in calls), "backlogit sync must still be attempted"

    def test_backlogit_absent_is_skipped_non_fatally(self):
        (self.sandbox.stub_dir / "backlogit.cmd").unlink()
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None

    def test_engram_direct_prewarm_happy_path(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        calls = self.sandbox.calls_log("engram")
        assert len(calls) == 1
        assert "--direct" in calls[0]

    def test_engram_direct_failure_falls_back_to_bind_and_daemon_sync(self):
        result = self.sandbox.run(
            extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0", "STUB_ENGRAM_DIRECT_FAIL": "1"}
        )
        assert result.returncode == 0, result.stderr
        calls = self.sandbox.calls_log("engram")
        assert len(calls) == 3
        assert "--direct" in calls[0]
        assert "bind" in calls[1]
        assert "sync" in calls[2] and "--direct" not in calls[2]
        assert self.sandbox.copilot_env() is not None

    def test_engram_fallback_failure_is_non_fatal(self):
        result = self.sandbox.run(
            extra_env={
                "STUB_GH_TOKEN": "tok",
                "STUB_COPILOT_EXIT_CODE": "0",
                "STUB_ENGRAM_DIRECT_FAIL": "1",
                "STUB_ENGRAM_BIND_FAIL": "1",
                "STUB_ENGRAM_FALLBACK_FAIL": "1",
            }
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None

    def test_engram_absent_is_skipped_non_fatally(self):
        (self.sandbox.stub_dir / "engram.cmd").unlink()
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None
        assert self.sandbox.calls_log("engram") == []

    # -- Terminal/stdio pass-through (functional proxy) ------------------

    def test_child_stdio_is_not_intercepted_functionally(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        assert "COPILOT_STUB_STDOUT_MARKER" in result.stdout
        assert "COPILOT_STUB_STDERR_MARKER" in result.stderr


if __name__ == "__main__":
    unittest.main()
