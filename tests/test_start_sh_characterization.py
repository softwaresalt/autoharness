"""Characterization suite for the repository-root ``start.sh`` launcher.

POST-MIGRATION (120.007-T / shipment 129-S): ``start.sh`` is now a THIN
COMPATIBILITY SHIM -- it contains no bootstrap/sidecar/resolve policy of its
own. All of that policy now lives in ``src/autoharness/supervise/``
(``bootstrap.py``, ``sidecar.py``, ``resolve.py``, ``app.py``) and is
invoked, end-to-end, via a single ``exec autoharness run --workspace
"$script_dir" -- "$@"`` call (``exec`` -- no subshell, no ``|| true``, no
masking -- preserves verbatim exit-code propagation, H3).

This suite exercises the REAL migrated architecture end-to-end wherever
practical: the actual (unmodified) ``start.sh`` is copied into an isolated
temp workspace and invoked via a real POSIX ``bash`` (Git for Windows on
this sandbox), with a fully-controlled, hermetic ``PATH`` that includes (a)
small extensionless shebang-script stubs for the external tools
``gh``/``backlogit``/``engram``/``copilot`` (unchanged from the
pre-migration suite -- the new Python implementation invokes these tools
with the IDENTICAL argv shapes the old inline scripts did, and NOW also
invokes ``backlogit``/``engram`` on POSIX -- see DELTA 6 below) and (b) the
real installed ``autoharness`` console script's own directory (resolved via
``shutil.which("autoharness")`` at collection time), so the REAL
``bootstrap.py``/``sidecar.py``/``resolve.py``/``app.py`` chain runs inside
the sandboxed ``bash`` subprocess.

Structural "genuinely thin shim" lexical assertions (no subprocess required)
are also included.

ENVIRONMENT NOTE: this sandbox is Windows. A genuine POSIX shell is located
via ``shutil.which("bash")`` or the well-known Git for Windows install
location (``C:\\Program Files\\Git\\bin\\bash.exe``). If no POSIX shell can
be found, the entire end-to-end class is skipped via ``unittest.skipIf``.

APPROVED BEHAVIOR DELTAS pinned by this suite (see
``docs/design-docs/2026-08-12-supervisor-observability-rollout-rollback.md``
and ``src/autoharness/supervise/bootstrap.py``/``sidecar.py``/``resolve.py``
for the authoritative rationale):

* DELTA 2 (POSIX_ENGRAM_DATA_DIR) -- ``ENGRAM_DATA_DIR`` now defaults to
  ``<workspace_root>/.engram`` on POSIX (the pre-migration ``start.sh`` had
  this line present but COMMENTED OUT -- it was never active).
* DELTA 3 (POSIX_PAT_BOOTSTRAP) -- ``GITHUB_TOKEN``/
  ``GITHUB_PERSONAL_ACCESS_TOKEN`` resolution via ``gh auth token`` now runs
  on POSIX (the pre-migration ``start.sh`` had NO PAT handling at all), with
  the SAME non-fatal-on-``gh``-absent/failing contract Windows always had
  (DELTA 1, pinned by the sibling PS1 suite).
* DELTA 6 (POSIX_SIDECAR_PREFLIGHT, implied by consolidation) -- ``backlogit
  sync`` and the Engram pre-warm sequence now run on POSIX too (the
  pre-migration ``start.sh`` had NO sidecar logic at all -- pinned by the old
  suite as an explicit ABSENCE test). This is an unavoidable consequence of
  ``sidecar.py`` being a single, platform-branch-free module shared by both
  shims (the task's own "no platform branching for behavior" constraint
  leaves no way to keep this Windows-only without introducing a branch).
* DELTA 7 (POSIX_REMOTE_FLAG, implied by consolidation) -- ``--remote``
  composition (``COPILOT_USE_REMOTE`` truthy + double-add guard) now applies
  on POSIX too (the pre-migration ``start.sh`` had NO ``--remote``/
  ``COPILOT_USE_REMOTE`` logic at all -- pinned by the old suite as an
  explicit ABSENCE test). Same rationale as DELTA 6: ``resolve.py`` is one
  shared, platform-branch-free module.
* PAT guard asymmetry is PRESERVED BYTE-IDENTICAL, not unified (deliberately
  NOT a fourth delta): ``GITHUB_TOKEN`` remains guarded/no-clobber while
  ``GITHUB_PERSONAL_ACCESS_TOKEN`` remains UNGUARDED and always re-resolved
  when ``gh`` is available -- exactly mirroring the pre-migration
  ``start.ps1`` asymmetry (see the sibling PS1 suite), now simply extended
  non-fatally to POSIX by DELTA 3 above rather than unified into a single
  guard contract.
* WORKSPACE ROOT ANCHORING -- the pre-migration ``start.sh`` anchored
  ``.env.local`` lookup to its own script directory (absolute, cwd
  independent) but defaulted ``COPILOT_HOME`` to a CWD-relative ``"./.copilot"``
  literal -- an internal inconsistency. The new shim passes
  ``--workspace "$script_dir"`` explicitly so ALL bootstrap defaults
  (``.env.local`` lookup, ``COPILOT_HOME``, ``ENGRAM_DATA_DIR``) are
  consistently anchored to the script's own directory, matching (and fixing)
  the more correct of the two pre-existing conventions.

VALIDATION DEPTH NOTE: not every pre-migration assertion is re-validated
end-to-end through a live sandbox run in this file. Assertions covering
``bootstrap.py``/``sidecar.py``/``resolve.py``'s own internal decision logic
in exhaustive per-branch detail are already covered far more cheaply and
thoroughly by ``tests/test_supervise_bootstrap.py``,
``tests/test_supervise_sidecar.py``, and ``tests/test_supervise_resolve.py``
(unit level, no subprocess, and platform-agnostic since none of those
modules branch by OS). This file's end-to-end tests are a representative,
high-value subset proving the WIRING through the actual shim script is
correct, plus the exec-based exit-code/argv passthrough this suite can only
observe at the shell level.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import textwrap
from pathlib import Path
from typing import Optional

import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
START_SH = REPO_ROOT / "start.sh"
START_SH_TMPL = REPO_ROOT / "templates" / "scripts" / "start.sh.tmpl"

_GIT_BASH_CANDIDATES = [
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
]


def _find_bash() -> Optional[str]:
    for candidate in _GIT_BASH_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    found = shutil.which("bash")
    if found and "system32" not in found.lower() and "windowsapps" not in found.lower():
        return found
    return None


BASH = _find_bash()

_AUTOHARNESS_EXE = shutil.which("autoharness")
AUTOHARNESS_BIN_DIR = str(Path(_AUTOHARNESS_EXE).parent) if _AUTOHARNESS_EXE else None


def _git_usr_bin() -> Optional[str]:
    """Locate Git for Windows' ``usr/bin`` (coreutils: ``dirname``, ``chmod``)."""

    if BASH is None:
        return None
    bash_dir = Path(BASH).parent
    for candidate in (bash_dir, bash_dir.parent / "usr" / "bin"):
        if (candidate / "dirname.exe").is_file() or (candidate / "dirname").is_file():
            return str(candidate)
    return None


GIT_USR_BIN = _git_usr_bin()


# ---------------------------------------------------------------------------
# Stub scripts -- unchanged in argv shape from the pre-migration suite: the
# new Python sidecar.py/bootstrap.py invoke these tools with the identical
# argv the old inline scripts did.
#
# IMPORTANT: even though ``start.sh`` itself is invoked by ``bash``, EVERY
# ``gh``/``backlogit``/``engram``/``copilot`` invocation in the migrated
# architecture is made by the ``autoharness run`` PYTHON PROCESS (via
# ``shutil.which`` + ``subprocess.Popen`` in bootstrap.py/sidecar.py/
# resolve.py/process.py) -- NOT by bash. On this Windows sandbox, that
# Python process is a native Win32 executable, so it can only resolve and
# launch these stub tools if they are genuine Win32-executable files (``
# .cmd``/``.bat``/``.exe``, discoverable via ``PATHEXT``). A POSIX
# extensionless shebang script is NOT directly launchable by
# ``subprocess.Popen`` on native Windows (there is no shebang-line
# interpretation in ``CreateProcess``), even though bash's own MSYS exec
# layer could launch one just fine. So these stubs use the SAME batch-file
# bodies as the PS1 suite's stubs -- only ``start.sh``/``autoharness.exe``
# need to be POSIX/bash-invokable, and both already are (``bash`` invokes
# ``.exe`` files natively).
# ---------------------------------------------------------------------------

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
    """A single isolated invocation environment for ``start.sh``."""

    def __init__(self, tmp_path: Path):
        self.workspace = tmp_path / "workspace"
        self.workspace.mkdir()
        self.stub_dir = tmp_path / "stubs"
        self.stub_dir.mkdir()
        self.result_dir = tmp_path / "results"
        self.result_dir.mkdir()
        shutil.copy2(START_SH, self.workspace / "start.sh")

    def write_env_local(self, content: str) -> None:
        with open(
            self.workspace / ".env.local", "w", encoding="utf-8", newline=""
        ) as fh:
            fh.write(content)

    def install_stub(self, name: str, content: str) -> None:
        # `.cmd` (not an extensionless shebang script) -- see the module
        # docstring: these are resolved and launched by the native-Win32
        # ``autoharness run`` Python process, not by bash.
        (self.stub_dir / f"{name}.cmd").write_text(content, encoding="utf-8")

    def _env(self, extra_env: Optional[dict]) -> dict:
        path_parts = [str(self.stub_dir)]
        if AUTOHARNESS_BIN_DIR:
            path_parts.append(AUTOHARNESS_BIN_DIR)
        if GIT_USR_BIN:
            path_parts.append(GIT_USR_BIN)
        # Also include bash's own directory so the shebang line's
        # `#!/usr/bin/env bash` can resolve `bash` itself.
        path_parts.append(str(Path(BASH).parent))
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        path_parts.append(os.path.join(system_root, "System32"))
        env = {
            "SystemRoot": system_root,
            "ComSpec": os.environ.get("ComSpec", r"C:\Windows\System32\cmd.exe"),
            "PATH": os.pathsep.join(path_parts),
            # Required for the native-Win32 ``autoharness run`` Python
            # process to resolve the `.cmd` stubs (and `autoharness.exe`
            # itself) via bare-name lookup (``shutil.which``); subprocess
            # env replacement means this must be supplied explicitly.
            "PATHEXT": os.environ.get("PATHEXT", ".COM;.EXE;.BAT;.CMD"),
            "HOME": os.environ.get("HOME", str(self.result_dir)),
            "USERPROFILE": os.environ.get("USERPROFILE", str(self.result_dir)),
            "TEMP": os.environ.get("TEMP", str(self.result_dir)),
            "TMP": os.environ.get("TMP", str(self.result_dir)),
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
        cmd = [BASH, str(self.workspace / "start.sh")]
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
        # The batch stub dumps ``%*`` as a single space-joined line (same
        # format as the PS1 suite's stub) since the copilot invocation is
        # made by the native-Win32 ``autoharness run`` process regardless of
        # which shell launched the top-level shim.
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
    "--remote",
    "COPILOT_USE_REMOTE",
    "AUTOHARNESS_SUPERVISOR",
)


def _active_lines(text: str) -> list:
    return [line for line in text.splitlines() if not line.strip().startswith("#")]


class ShimIsGenuinelyThinTests(unittest.TestCase):
    """Structural checks that need no sandbox/subprocess at all."""

    def test_start_sh_active_lines_contain_no_bootstrap_sidecar_resolve_policy(self):
        # "engram" legitimately appears in the (unchanged, preserved)
        # commented-out Claude/Codex sections' surrounding prose is not
        # expected -- but to be safe this checks only ACTIVE (non-comment)
        # lines, consistent with the pre-migration suite's own convention
        # for the (now fully removed) commented-out ENGRAM_DATA_DIR line.
        active_text = "\n".join(_active_lines(START_SH.read_text(encoding="utf-8")))
        for token in _BANNED_TOKENS:
            self.assertNotIn(token, active_text, f"start.sh must not contain {token!r} in an active line")
        self.assertNotIn("engram", active_text.lower())

    def test_start_sh_tmpl_active_lines_contain_no_bootstrap_sidecar_resolve_policy(self):
        active_text = "\n".join(_active_lines(START_SH_TMPL.read_text(encoding="utf-8")))
        for token in _BANNED_TOKENS:
            self.assertNotIn(token, active_text, f"start.sh.tmpl must not contain {token!r} in an active line")
        self.assertNotIn("engram", active_text.lower())

    def test_start_sh_invokes_autoharness_run(self):
        text = START_SH.read_text(encoding="utf-8")
        self.assertIn("autoharness run", text)

    def test_start_sh_uses_exec_for_verbatim_exit_propagation(self):
        text = START_SH.read_text(encoding="utf-8")
        self.assertIn("exec autoharness run", text)
        self.assertNotIn("|| true", text)

    def test_start_sh_tmpl_preserves_project_name_placeholder(self):
        text = START_SH_TMPL.read_text(encoding="utf-8")
        self.assertIn("{{PROJECT_NAME}}", text)

    def test_start_sh_final_invocation_has_no_stdio_redirection(self):
        source = START_SH.read_text(encoding="utf-8")
        lines = [line.strip() for line in source.splitlines() if line.strip() and not line.strip().startswith("#")]
        invocation_lines = [line for line in lines if line.startswith("exec autoharness run")]
        assert len(invocation_lines) == 1
        invocation = invocation_lines[0]
        for operator in (">", "2>", "1>", "*>", "|", "<"):
            assert operator not in invocation, f"unexpected redirection operator {operator!r}"


@unittest.skipIf(
    BASH is None or AUTOHARNESS_BIN_DIR is None,
    reason=(
        "no POSIX shell (bash) found on PATH or at the well-known Git for "
        "Windows install location, or no resolvable `autoharness` console "
        "script found on PATH; start.sh end-to-end characterization "
        "requires both and is skipped gracefully rather than faked"
    ),
)
class StartShEndToEndTests(unittest.TestCase):
    """End-to-end characterization: real bash -> real `autoharness run` ->
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

    # -- .env.local: no-clobber + quote/CR stripping ---------------------

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
        assert env["MISMATCHED_QUOTES"] == '"hello\''
        # NOTE: on Windows, CPython's `os.environ` machinery normalizes
        # newly-set variable NAMES to uppercase when the process env block
        # crosses a child-process boundary (confirmed empirically -- this is
        # a CPython/Windows environment-block quirk, not a bootstrap.py
        # defect: bootstrap.py's own KEY=VALUE regex is deliberately
        # case-inclusive, see its module docstring). A real POSIX system has
        # no such normalization. Assert case-insensitively here so this
        # suite still pins "lowercase names ARE parsed and applied", without
        # asserting an exact-case property this Windows sandbox cannot
        # observe through the real child-process boundary.
        assert {k.lower(): v for k, v in env.items()}.get("lowercase_ignored") == "nope"

    def test_env_local_strips_trailing_carriage_return(self):
        self.sandbox.write_env_local("WITH_CRLF=value_with_cr\r\n")
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["WITH_CRLF"] == "value_with_cr"

    def test_env_local_no_clobber_preset_var_wins(self):
        # Use a non-path-shaped preset value: Git-Bash/MSYS auto-converts
        # POSIX-absolute-path-looking env values into Windows paths when
        # spawning a native-Win32 child (autoharness.exe); an arbitrary
        # non-path token avoids that MSYS-specific translation while still
        # proving no-clobber preset-value preservation.
        self.sandbox.write_env_local("COPILOT_HOME=should-not-win\n")
        result = self.sandbox.run(
            extra_env={
                "COPILOT_HOME": "already-set-value",
                "STUB_GH_TOKEN": "tok",
                "STUB_COPILOT_EXIT_CODE": "0",
            }
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["COPILOT_HOME"] == "already-set-value"

    def test_env_local_absent_is_not_fatal(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr

    # -- COPILOT_HOME / ENGRAM_DATA_DIR defaults, anchored to $script_dir --
    # -- DELTA 2: ENGRAM_DATA_DIR NOW defaults on POSIX (was commented out) --

    def test_copilot_home_and_engram_data_dir_default_to_workspace_subdirs(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert os.path.realpath(env["COPILOT_HOME"]) == os.path.realpath(
            str(self.sandbox.workspace / ".copilot")
        )
        assert os.path.realpath(env["ENGRAM_DATA_DIR"]) == os.path.realpath(
            str(self.sandbox.workspace / ".engram")
        )

    def test_copilot_home_and_engram_data_dir_honor_preset_values(self):
        # Non-path-shaped preset values (see the no-clobber test above for
        # why): MSYS/Git-Bash auto-converts POSIX-absolute-path-looking env
        # values when spawning the native-Win32 `autoharness.exe` child.
        result = self.sandbox.run(
            extra_env={
                "COPILOT_HOME": "custom-copilot-home",
                "ENGRAM_DATA_DIR": "custom-engram-data",
                "STUB_GH_TOKEN": "tok",
                "STUB_COPILOT_EXIT_CODE": "0",
            }
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["COPILOT_HOME"] == "custom-copilot-home"
        assert env["ENGRAM_DATA_DIR"] == "custom-engram-data"

    # -- DELTA 3: PAT resolution NOW runs on POSIX. Per-variable guard -----
    # -- asymmetry (GITHUB_TOKEN guarded, GITHUB_PERSONAL_ACCESS_TOKEN -----
    # -- unguarded) is PRESERVED byte-identical to Windows, not unified. ---

    def test_delta3_github_tokens_resolved_from_gh_when_both_unset(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "resolved-token", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["GITHUB_TOKEN"] == "resolved-token"
        assert env["GITHUB_PERSONAL_ACCESS_TOKEN"] == "resolved-token"
        # Two independent gh invocations (one per variable), matching the
        # pre-migration start.ps1 call pattern extended non-fatally to POSIX.
        assert [c.strip() for c in self.sandbox.calls_log("gh")] == ["gh auth token", "gh auth token"]

    def test_github_token_preset_is_not_overwritten_and_gh_still_resolves_the_other(self):
        result = self.sandbox.run(
            extra_env={
                "STUB_GH_TOKEN": "resolved-token",
                "STUB_COPILOT_EXIT_CODE": "0",
                "GITHUB_TOKEN": "already-set",
            }
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["GITHUB_TOKEN"] == "already-set"
        assert env["GITHUB_PERSONAL_ACCESS_TOKEN"] == "resolved-token"
        assert [c.strip() for c in self.sandbox.calls_log("gh")] == ["gh auth token"]

    # -- DELTA 1 (shared contract): gh absent/failing is non-fatal on POSIX --
    # -- too, leaving the token variables UNSET (never empty string). ------

    def test_delta1_shared_gh_absent_is_non_fatal_and_leaves_vars_unset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            box = Sandbox(Path(tmpdir))
            box.install_stub("copilot", COPILOT_STUB)
            result = box.run(extra_env={"STUB_COPILOT_EXIT_CODE": "0"})
            assert result.returncode == 0, result.stderr
            env = box.copilot_env()
            assert env is not None
            assert "GITHUB_TOKEN" not in env
            assert "GITHUB_PERSONAL_ACCESS_TOKEN" not in env

    def test_github_token_unset_when_gh_fails_non_fatally(self):
        result = self.sandbox.run(
            extra_env={
                "STUB_GH_FAIL": "1",
                "STUB_GH_TOKEN": "should-not-appear",
                "STUB_COPILOT_EXIT_CODE": "0",
            }
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert "GITHUB_TOKEN" not in env
        assert "GITHUB_PERSONAL_ACCESS_TOKEN" not in env
        assert [c.strip() for c in self.sandbox.calls_log("gh")] == ["gh auth token", "gh auth token"]

    def test_github_token_preset_pat_is_still_unguarded_reresolved(self):
        """GITHUB_PERSONAL_ACCESS_TOKEN is UNGUARDED on POSIX too -- byte
        for-byte the same asymmetry as the pre-migration start.ps1 -- so
        even when already set, it is re-resolved whenever gh is available.
        Only GITHUB_TOKEN is guarded/no-clobber."""

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
        assert env is not None
        assert env["GITHUB_TOKEN"] == "already-set-1"
        assert env["GITHUB_PERSONAL_ACCESS_TOKEN"] == "resolved-token"
        assert [c.strip() for c in self.sandbox.calls_log("gh")] == ["gh auth token"]

    # -- Copilot exe resolution order + hard failure message ---------------

    def test_copilot_exe_resolved_from_path_by_default(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None

    def test_copilot_exe_path_takes_precedence(self):
        explicit_copilot = self.sandbox.stub_dir / "explicit-copilot-binary.cmd"
        explicit_copilot.write_text(COPILOT_STUB, encoding="utf-8")
        (self.sandbox.stub_dir / "copilot.cmd").unlink()
        result = self.sandbox.run(
            extra_env={
                "STUB_GH_TOKEN": "tok",
                "STUB_COPILOT_EXIT_CODE": "0",
                "COPILOT_EXE_PATH": str(explicit_copilot),
            }
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None

    def test_copilot_exe_env_var_used_when_exe_path_unset(self):
        explicit_copilot = self.sandbox.stub_dir / "legacy-copilot-binary.cmd"
        explicit_copilot.write_text(COPILOT_STUB, encoding="utf-8")
        (self.sandbox.stub_dir / "copilot.cmd").unlink()
        result = self.sandbox.run(
            extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0", "COPILOT_EXE": str(explicit_copilot)}
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None

    def test_copilot_exe_unresolvable_hard_fails_with_actionable_message(self):
        (self.sandbox.stub_dir / "copilot.cmd").unlink()
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok"})
        assert result.returncode != 0
        assert "Unable to locate Copilot CLI" in result.stdout or "Unable to locate Copilot CLI" in result.stderr
        assert "COPILOT_EXE_PATH" in result.stdout or "COPILOT_EXE_PATH" in result.stderr

    # -- DELTA 7: --remote composition NOW applies on POSIX too ------------

    def test_delta7_remote_flag_appended_when_use_remote_truthy(self):
        result = self.sandbox.run(
            extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0", "COPILOT_USE_REMOTE": "true"},
            argv=["explicit", "args"],
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_args() == "--remote explicit args"

    def test_remote_flag_not_appended_when_use_remote_not_truthy(self):
        result = self.sandbox.run(
            extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0", "COPILOT_USE_REMOTE": "false"},
            argv=["explicit", "args"],
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_args() == "explicit args"

    def test_remote_flag_not_duplicated_when_operator_already_passed_it(self):
        result = self.sandbox.run(
            extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0", "COPILOT_USE_REMOTE": "true"},
            argv=["--remote", "explicit"],
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_args() == "--remote explicit"

    # -- operator argv forwarded verbatim -----------------------------------

    def test_operator_argv_forwarded_verbatim(self):
        result = self.sandbox.run(
            argv=["explicit", "args"], extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"}
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_args() == "explicit args"

    # -- exec-based verbatim exit code propagation (was already correct) ---

    def test_child_exit_code_propagates_verbatim(self):
        for child_exit_code in ["0", "3", "7"]:
            with self.subTest(child_exit_code=child_exit_code):
                result = self.sandbox.run(
                    extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": child_exit_code}
                )
                assert result.returncode == int(child_exit_code), (
                    f"expected host exit code {child_exit_code} (exec-based verbatim "
                    f"propagation), got {result.returncode}"
                )

    # -- DELTA 6: sidecar preflight NOW runs on POSIX too -------------------

    def test_delta6_backlogit_sync_runs_when_resolved(self):
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
        assert any("sync" in c for c in calls)

    def test_backlogit_absent_is_skipped_non_fatally(self):
        (self.sandbox.stub_dir / "backlogit.cmd").unlink()
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None

    def test_delta6_engram_direct_prewarm_happy_path(self):
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

    # -- terminal/stdio pass-through (functional proxy) ---------------------

    def test_child_stdio_is_not_intercepted_functionally(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        assert "COPILOT_STUB_STDOUT_MARKER" in result.stdout
        assert "COPILOT_STUB_STDERR_MARKER" in result.stderr


if __name__ == "__main__":
    unittest.main()
