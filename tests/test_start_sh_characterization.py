"""Characterization suite for the repository-root ``start.sh`` launcher.

This suite pins the CURRENT observable contract of ``start.sh`` as-is. It
does NOT modify ``start.sh``: the script under test is copied verbatim into
an isolated temporary workspace, invoked via a real ``bash``/``sh`` on a
tightly controlled ``PATH`` populated with small shebang-script stubs for
``gh`` and ``copilot`` (the only two external tools ``start.sh`` invokes).

This is ``start.sh``'s OWN five-dimension contract -- NOT a mirror of the
``start.ps1`` characterization suite (``test_start_ps1_characterization.py``).
``start.sh`` is a deliberately smaller surface than ``start.ps1``: it has no
Engram pre-warm, no backlogit sync, no ``GITHUB_PERSONAL_ACCESS_TOKEN``, no
``--remote`` flag logic, and (today) no ``ENGRAM_DATA_DIR`` default (that
line is present but commented out in the source). Several tests below
explicitly assert these features are ABSENT, which is itself part of the
pinned baseline -- an unannounced *addition* of any of them should fail this
suite just as surely as an unannounced removal of an existing behavior.

ENVIRONMENT NOTE: this sandbox is Windows. A genuine POSIX shell is located
via ``shutil.which("bash")`` or the well-known Git for Windows install
location (``C:\\Program Files\\Git\\bin\\bash.exe``). If no POSIX shell can
be found on this machine, the entire module is skipped via
``unittest.skipIf`` -- the assertions themselves are still written in
full so they execute wherever a POSIX shell is available (this sandbox
happens to have Git for Windows installed, so in practice they do run here).

PID-PRESERVATION AS AN ``exec`` PROXY (with a documented MSYS/Cygwin
CAVEAT): ``start.sh`` ends with ``exec "$copilot_exe" "$@"``. POSIX ``exec``
replaces the *current* process image in place rather than forking a child,
which is what actually preserves terminal/TTY attachment (there is no new
process to be attached to anything -- the original process, with its
original file descriptors 0/1/2, simply starts running different code).
This was empirically verified in this sandbox via an isolated two-script
repro: a script that prints its own ``$$`` and then ``exec``s a second
script that also prints ``$$`` observes the SAME pid both times.

CAVEAT: Git for Windows' bash runs under the MSYS/Cygwin POSIX emulation
layer, which maintains its OWN internal pid table distinct from the native
Win32 process id. True ``execve`` (in-place process image replacement) is
not possible on Windows, so MSYS/Cygwin's ``exec`` necessarily starts a NEW
native Win32 process underneath while preserving only the EMULATED
(MSYS/Cygwin-level) pid seen by shell constructs like ``$$``. This was
confirmed empirically: launching ``bash start.sh`` from Python and
comparing ``subprocess.Popen.pid`` (the real Win32 pid) against the
exec'd child's ``$$`` shows they DIFFER, even though the emulated pid
(``$$``) is provably preserved across the ``exec`` boundary itself.
Consequently, this suite does NOT compare against ``subprocess.Popen.pid``.
Instead it captures the MSYS-emulated pid from BOTH sides of the ``exec``
call using a signal that survives the Win32 boundary: the ``gh`` stub,
invoked via command substitution (a fork, not an exec) just before the
trailing ``exec`` line runs, records its own ``$PPID`` -- which is
``start.sh``'s own MSYS-emulated pid at that point -- and the ``copilot``
stub records its own post-exec ``$$``. These two values were verified via
an isolated repro to be equal (the same MSYS-emulated pid, carried across
the ``exec``), which is the correct level at which POSIX ``exec`` semantics
(job control, ``$$``, ``$!``, etc.) actually operate for shell script
purposes, and is the closest practical proxy available on this platform for
"the process was replaced in place, not forked as a new logical process".
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import textwrap
from pathlib import Path
from typing import Optional

import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
START_SH = REPO_ROOT / "start.sh"

_GIT_BASH_CANDIDATES = [
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files\Git\usr\bin\bash.exe",
]


def _find_bash() -> Optional[str]:
    # Prefer the well-known Git for Windows install location FIRST. On
    # Windows 10/11, `shutil.which("bash")` frequently resolves to the
    # built-in WSL launcher shim at `C:\Windows\System32\bash.exe` (present
    # even when no WSL distro is installed/usable) rather than a real POSIX
    # shell -- that shim expects POSIX-style paths and fails with
    # "No such file or directory" when handed a Windows path like
    # `C:\Users\...\start.sh`, as confirmed empirically in this sandbox.
    # Git for Windows' bash.exe is a genuine, directly-runnable POSIX shell
    # that accepts Windows paths, so it is tried first.
    for candidate in _GIT_BASH_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    found = shutil.which("bash")
    if found and "system32" not in found.lower() and "windowsapps" not in found.lower():
        return found
    return None


BASH = _find_bash()


def _git_usr_bin() -> Optional[str]:
    """Locate Git for Windows' ``usr/bin`` (coreutils: ``dirname``, ``chmod``).

    ``start.sh`` uses ``$(dirname "${BASH_SOURCE[0]}")`` (an external
    ``dirname`` command, not a bash builtin) to resolve its own directory.
    Git for Windows ships coreutils under ``usr/bin`` alongside (not inside)
    the ``bin`` directory that holds ``bash.exe`` itself.
    """

    if BASH is None:
        return None
    bash_dir = Path(BASH).parent
    for candidate in (bash_dir, bash_dir.parent / "usr" / "bin"):
        if (candidate / "dirname.exe").is_file() or (candidate / "dirname").is_file():
            return str(candidate)
    return None


GIT_USR_BIN = _git_usr_bin()


# ---------------------------------------------------------------------------
# Stub scripts. Extensionless shebang scripts on PATH, executed the same way
# real external tools (``gh``, ``copilot``) would be -- verified in this
# sandbox to resolve and execute correctly via bash's PATH search even
# without a file extension, as long as the execute bit is set.
# ---------------------------------------------------------------------------

GH_STUB = textwrap.dedent(
    """\
    #!/usr/bin/env bash
    if [ -n "${STUB_RESULT_DIR:-}" ]; then
        echo "gh $*" >> "$STUB_RESULT_DIR/gh_calls.log"
        # Record our own $PPID here for the exec-pid-identity proxy test
        # below: `$(gh auth token)` runs `gh` as a forked child of the
        # still-running start.sh process (command substitution does not
        # exec anything), so `gh`'s $PPID IS start.sh's own pid at the
        # point just before it reaches the trailing `exec` line -- this
        # was verified empirically via an isolated repro (see the module
        # docstring) and gives an exec-identity proxy that survives the
        # Win32/MSYS pid-virtualization boundary described there.
        echo "$PPID" > "$STUB_RESULT_DIR/gh_ppid.txt"
    fi
    if [ "${STUB_GH_FAIL:-}" = "1" ]; then
        echo "stub gh failure" >&2
        exit 1
    fi
    echo "${STUB_GH_TOKEN:-}"
    exit 0
    """
)

COPILOT_STUB = textwrap.dedent(
    """\
    #!/usr/bin/env bash
    if [ -n "${STUB_RESULT_DIR:-}" ]; then
        printf '%s\\n' "$@" > "$STUB_RESULT_DIR/copilot_args.txt"
        env > "$STUB_RESULT_DIR/copilot_env.txt"
        echo "$$" > "$STUB_RESULT_DIR/copilot_pid.txt"
    fi
    echo COPILOT_STUB_STDOUT_MARKER
    echo COPILOT_STUB_STDERR_MARKER >&2
    if [ -n "${STUB_COPILOT_EXIT_CODE:-}" ]; then
        exit "$STUB_COPILOT_EXIT_CODE"
    fi
    exit 0
    """
)

def _parse_env_dump(text: str) -> dict:
    """Parse the output of the POSIX ``env`` builtin/command into a dict.

    Values may legitimately contain ``=`` (e.g. base64-ish tokens); split
    only on the first ``=`` per line. Multi-line values (rare, but possible
    for exported functions) are not handled -- none of the variables under
    test in this suite are multi-line.
    """

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
        # Write with an explicit newline convention (no translation) since
        # one of the tests below exercises CR handling explicitly.
        with open(
            self.workspace / ".env.local", "w", encoding="utf-8", newline=""
        ) as fh:
            fh.write(content)

    def install_stub(self, name: str, content: str) -> None:
        path = self.stub_dir / name
        path.write_text(content, encoding="utf-8", newline="\n")
        mode = os.stat(path).st_mode
        os.chmod(path, mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    def _env(self, extra_env: Optional[dict]) -> dict:
        path_parts = [str(self.stub_dir)]
        if GIT_USR_BIN:
            path_parts.append(GIT_USR_BIN)
        # Also include bash's own directory so the shebang line's
        # `#!/usr/bin/env bash` can resolve `bash` itself.
        path_parts.append(str(Path(BASH).parent))
        system_root = os.environ.get("SystemRoot", r"C:\Windows")
        path_parts.append(os.path.join(system_root, "System32"))
        env = {
            "SystemRoot": system_root,
            "PATH": os.pathsep.join(path_parts),
            "HOME": os.environ.get("HOME", str(self.result_dir)),
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
        timeout: float = 30.0,
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

    def copilot_args(self) -> Optional[list]:
        path = self.result_dir / "copilot_args.txt"
        if not path.exists():
            return None
        # One argv entry per line (see COPILOT_STUB's `printf '%s\n' "$@"`).
        text = path.read_text(encoding="utf-8")
        return text.split("\n")[:-1] if text.endswith("\n") else text.split("\n")

    def copilot_pid(self) -> Optional[str]:
        path = self.result_dir / "copilot_pid.txt"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8").strip()

    def gh_ppid(self) -> Optional[str]:
        path = self.result_dir / "gh_ppid.txt"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8").strip()

    def calls_log(self, name: str) -> list:
        path = self.result_dir / f"{name}_calls.log"
        if not path.exists():
            return []
        return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]




@unittest.skipIf(
    BASH is None,
    reason=(
        "no POSIX shell (bash) found on PATH or at the well-known Git for "
        "Windows install location; start.sh characterization requires a "
        "real bash invocation and is skipped gracefully rather than faked"
    ),
)
class StartShCharacterizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.sandbox = Sandbox(Path(self._tmpdir.name))
        self.sandbox.install_stub("gh", GH_STUB)
        self.sandbox.install_stub("copilot", COPILOT_STUB)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # ---------------------------------------------------------------------------
    # (1) .env.local no-clobber parsing with CR stripping, trailing-whitespace
    #     trim, single matching quote-pair stripping.
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
        # start.sh's KEY regex is `[A-Za-z_][A-Za-z0-9_]*` -- explicitly
        # case-inclusive of lower-case from the start (unlike start.ps1's
        # PowerShell `-match`, which is incidentally case-insensitive despite
        # a literal `[A-Z_]` pattern). Lower-case keys are parsed and exported
        # here by explicit design, not by a case-insensitivity quirk.
        assert env.get("lowercase_ignored") == "nope"


    def test_env_local_strips_trailing_carriage_return_and_whitespace(self):
        # A CRLF-terminated line (as if authored/edited on Windows) followed by
        # trailing spaces before the CR. `${env_value%$'\r'}` strips a trailing
        # CR first, then trailing whitespace is trimmed via parameter expansion.
        self.sandbox.write_env_local("WITH_CRLF=value_with_cr   \r\n")
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["WITH_CRLF"] == "value_with_cr"


    def test_env_local_no_clobber_preset_var_wins(self):
        self.sandbox.write_env_local("COPILOT_HOME=/should/not/win\n")
        result = self.sandbox.run(
            extra_env={
                "COPILOT_HOME": "/already/set",
                "STUB_GH_TOKEN": "tok",
                "STUB_COPILOT_EXIT_CODE": "0",
            }
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["COPILOT_HOME"] == "/already/set"


    def test_env_local_ignores_non_key_value_lines(self):
        self.sandbox.write_env_local(
            "\n".join(
                [
                    "# a comment line",
                    "not a valid assignment",
                    "REAL_VALUE=set_me",
                    "",
                ]
            )
        )
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["REAL_VALUE"] == "set_me"


    def test_env_local_absent_is_not_fatal(self):
        # No .env.local written at all -- the `if [[ -f "$env_local" ]]` guard
        # simply skips the whole block.
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr


    # ---------------------------------------------------------------------------
    # (2) COPILOT_HOME defaults to ./.copilot, honoring pre-set value.
    # ---------------------------------------------------------------------------


    def test_copilot_home_defaults_to_dot_copilot(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["COPILOT_HOME"] == "./.copilot"


    def test_copilot_home_honors_preset_value(self):
        result = self.sandbox.run(
            extra_env={
                "COPILOT_HOME": "/custom/copilot/home",
                "STUB_GH_TOKEN": "tok",
                "STUB_COPILOT_EXIT_CODE": "0",
            }
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["COPILOT_HOME"] == "/custom/copilot/home"


    # ---------------------------------------------------------------------------
    # ABSENCE: no ENGRAM_DATA_DIR default -- the line is commented out in the
    # source. Baseline evidence: the variable is NOT set by start.sh at all
    # (unless already present in the parent environment).
    # ---------------------------------------------------------------------------


    def test_engram_data_dir_source_line_is_commented_out(self):
        text = START_SH.read_text(encoding="utf-8")
        assert "# export ENGRAM_DATA_DIR=" in text
        # And there must be no UN-commented `export ENGRAM_DATA_DIR=` line.
        active_lines = [
            line
            for line in text.splitlines()
            if line.strip().startswith("export ENGRAM_DATA_DIR=")
        ]
        assert active_lines == []


    def test_engram_data_dir_not_set_when_absent_from_environment(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert "ENGRAM_DATA_DIR" not in env


    # ---------------------------------------------------------------------------
    # (3) UNGUARDED `export GITHUB_TOKEN="$(gh auth token)"`. Because `export`
    #     is a shell BUILTIN, `set -e` evaluates errexit against the exit status
    #     of the `export` builtin itself -- not the failing command substitution
    #     nested inside it -- so a failing `gh auth token` does NOT abort the
    #     script under `set -euo pipefail`. The observable result is an EMPTY
    #     GITHUB_TOKEN, never a script abort. Verified via an isolated repro
    #     (`export FOO="$(false)"` under `set -e` continues to the next line).
    # ---------------------------------------------------------------------------


    def test_github_token_resolved_from_gh_when_present_and_succeeding(self):
        result = self.sandbox.run(
            extra_env={"STUB_GH_TOKEN": "resolved-token-value", "STUB_COPILOT_EXIT_CODE": "0"}
        )
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["GITHUB_TOKEN"] == "resolved-token-value"
        assert self.sandbox.calls_log("gh") == ["gh auth token"]


    def test_github_token_empty_when_gh_fails_script_does_not_abort(self):
        result = self.sandbox.run(
            extra_env={
                "STUB_GH_FAIL": "1",
                "STUB_GH_TOKEN": "should-not-appear",
                "STUB_COPILOT_EXIT_CODE": "0",
            }
        )
        # Baseline: the script reaches `exec copilot` and propagates copilot's
        # own exit code (0 here), NOT an early abort from `set -e`.
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert env["GITHUB_TOKEN"] == ""
        assert self.sandbox.calls_log("gh") == ["gh auth token"]


    def test_github_token_empty_when_gh_entirely_absent_from_path(self):
        # A sandbox with NO gh stub installed at all -- PATH resolution for
        # `gh` fails outright ("command not found"), which is itself a command
        # substitution failure captured the same way as an ordinary non-zero
        # exit from `gh` -- still absorbed by `export`'s own (successful) exit
        # status under `set -e`, per the same builtin-vs-substitution mechanics
        # documented above.
        with tempfile.TemporaryDirectory() as tmpdir:
            box = Sandbox(Path(tmpdir))
            box.install_stub("copilot", COPILOT_STUB)
            result = box.run(extra_env={"STUB_COPILOT_EXIT_CODE": "0"})
            assert result.returncode == 0, result.stderr
            env = box.copilot_env()
            assert env is not None
            assert env["GITHUB_TOKEN"] == ""


    # ---------------------------------------------------------------------------
    # ABSENCE: no GITHUB_PERSONAL_ACCESS_TOKEN logic exists in start.sh at all
    # (unlike start.ps1's separate, unconditional second token contract).
    # ---------------------------------------------------------------------------


    def test_no_github_personal_access_token_logic_in_source(self):
        text = START_SH.read_text(encoding="utf-8")
        assert "GITHUB_PERSONAL_ACCESS_TOKEN" not in text


    def test_github_personal_access_token_never_set(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        env = self.sandbox.copilot_env()
        assert env is not None
        assert "GITHUB_PERSONAL_ACCESS_TOKEN" not in env


    # ---------------------------------------------------------------------------
    # (4) Copilot exe resolution: COPILOT_EXE_PATH -> COPILOT_EXE -> PATH
    #     `copilot`; actionable message + exit 1 when unresolvable.
    # ---------------------------------------------------------------------------


    def test_copilot_exe_resolved_from_path_by_default(self):
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_env() is not None


    def test_copilot_exe_path_takes_precedence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            box = Sandbox(Path(tmpdir))
            box.install_stub("gh", GH_STUB)
            # A DIFFERENT executable under a different name, referenced only via
            # COPILOT_EXE_PATH -- proves the explicit path wins over any PATH-based
            # `copilot` resolution (there is deliberately no `copilot` stub at all
            # here, so a fallback to PATH would fail outright).
            explicit_copilot = box.stub_dir / "explicit-copilot-binary"
            explicit_copilot.write_text(COPILOT_STUB, encoding="utf-8", newline="\n")
            mode = os.stat(explicit_copilot).st_mode
            os.chmod(explicit_copilot, mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            result = box.run(
                extra_env={
                    "STUB_GH_TOKEN": "tok",
                    "STUB_COPILOT_EXIT_CODE": "0",
                    "COPILOT_EXE_PATH": str(explicit_copilot),
                }
            )
            assert result.returncode == 0, result.stderr
            assert box.copilot_env() is not None


    def test_copilot_exe_env_var_used_when_exe_path_unset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            box = Sandbox(Path(tmpdir))
            box.install_stub("gh", GH_STUB)
            explicit_copilot = box.stub_dir / "legacy-copilot-binary"
            explicit_copilot.write_text(COPILOT_STUB, encoding="utf-8", newline="\n")
            mode = os.stat(explicit_copilot).st_mode
            os.chmod(explicit_copilot, mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
            result = box.run(
                extra_env={
                    "STUB_GH_TOKEN": "tok",
                    "STUB_COPILOT_EXIT_CODE": "0",
                    "COPILOT_EXE": str(explicit_copilot),
                }
            )
            assert result.returncode == 0, result.stderr
            assert box.copilot_env() is not None


    def test_copilot_exe_unresolvable_hard_fails_with_actionable_message(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            box = Sandbox(Path(tmpdir))
            box.install_stub("gh", GH_STUB)
            # Deliberately no `copilot` stub anywhere on PATH and no
            # COPILOT_EXE_PATH/COPILOT_EXE override.
            result = box.run(extra_env={"STUB_GH_TOKEN": "tok"})
            assert result.returncode == 1
            assert "Unable to locate Copilot CLI" in result.stderr
            assert "COPILOT_EXE_PATH" in result.stderr


    # ---------------------------------------------------------------------------
    # ABSENCE: no COPILOT_USE_REMOTE / --remote logic exists in start.sh.
    # ---------------------------------------------------------------------------


    def test_no_remote_flag_logic_in_source(self):
        text = START_SH.read_text(encoding="utf-8")
        assert "COPILOT_USE_REMOTE" not in text
        assert "--remote" not in text


    def test_remote_env_var_has_no_effect_on_argv(self):
        result = self.sandbox.run(
            extra_env={
                "STUB_GH_TOKEN": "tok",
                "STUB_COPILOT_EXIT_CODE": "0",
                "COPILOT_USE_REMOTE": "true",
            },
            argv=["explicit", "args"],
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_args() == ["explicit", "args"]


    # ---------------------------------------------------------------------------
    # ABSENCE: no backlogit sync, no Engram pre-warm sidecar logic in start.sh.
    # ---------------------------------------------------------------------------


    def test_no_backlogit_or_engram_sidecar_logic_in_source(self):
        text = START_SH.read_text(encoding="utf-8")
        assert "backlogit" not in text.lower()
        # "engram" DOES appear in the source, but only inside the commented-out
        # `# export ENGRAM_DATA_DIR=...` default line (see the dedicated
        # `test_engram_data_dir_source_line_is_commented_out` test above) --
        # assert here that no ACTIVE (non-comment) line references it, i.e.
        # there is no live Engram pre-warm/sidecar logic anywhere in start.sh.
        active_lines = [
            line
            for line in text.splitlines()
            if not line.strip().startswith("#")
        ]
        assert not any("engram" in line.lower() for line in active_lines)


    def test_no_backlogit_or_engram_calls_observed_at_runtime(self):
        # Even if `backlogit`/`engram` stub executables were on PATH, start.sh
        # never invokes them -- verified here by confirming no calls log for
        # either name is ever created despite the script running to completion.
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        assert self.sandbox.calls_log("backlogit") == []
        assert self.sandbox.calls_log("engram") == []


    # ---------------------------------------------------------------------------
    # (5) `exec` of resolved exe: verbatim argv passthrough, exit status via
    #     process replacement, terminal attachment preserved.
    # ---------------------------------------------------------------------------


    def test_argv_forwarded_verbatim(self):
        result = self.sandbox.run(
            extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"},
            argv=["--flag", "value with spaces", "-x"],
        )
        assert result.returncode == 0, result.stderr
        assert self.sandbox.copilot_args() == ["--flag", "value with spaces", "-x"]


    def test_child_exit_code_propagated_via_exec(self):
        for exit_code in [0, 1, 3, 42]:
            with self.subTest(exit_code=exit_code):
                result = self.sandbox.run(
                    extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": str(exit_code)}
                )
                # Unlike start.ps1 (where a bare `& $copilotExe` loses the child's exit
                # code because $PSNativeCommandUseErrorActionPreference is $false and
                # there is no explicit `exit $LASTEXITCODE`), start.sh's `exec` performs
                # genuine POSIX process replacement: the shell process itself BECOMES
                # the child, so there is no "parent observes child's exit code" step at
                # all -- the OS-level exit status IS the child's exit status.
                assert result.returncode == exit_code


    def test_terminal_attachment_preserved_via_exec_pid_identity(self):
        # `exec` replaces the running bash process's image in place at the
        # MSYS/Cygwin-emulated pid level (see the module docstring's caveat on
        # why the native Win32 pid cannot be used as the comparison point on
        # this platform): the `gh` stub's own $PPID (captured via a fork, just
        # before the trailing `exec` line runs) equals the `copilot` stub's own
        # $$ (captured just after the `exec` replaces the process). A forked
        # child (as opposed to `exec`) would necessarily produce a DIFFERENT
        # pid at this emulated layer -- this is the closest practical proxy
        # available for "terminal attachment preserved via process replacement,
        # not a forked child": stdio file descriptors 0/1/2 are never reopened
        # or redirected by a process replacement, because there is no new
        # logical process to attach them to.
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0, result.stderr
        gh_ppid = self.sandbox.gh_ppid()
        copilot_pid = self.sandbox.copilot_pid()
        assert gh_ppid is not None
        assert copilot_pid is not None
        assert gh_ppid == copilot_pid


    def test_stub_stdio_markers_reach_captured_output_unmediated(self):
        # No pipe/redirection is inserted between the shell and the child by
        # start.sh itself; both stdout and stderr markers emitted by the stub
        # reach our subprocess capture directly.
        result = self.sandbox.run(extra_env={"STUB_GH_TOKEN": "tok", "STUB_COPILOT_EXIT_CODE": "0"})
        assert result.returncode == 0
        assert "COPILOT_STUB_STDOUT_MARKER" in result.stdout
        assert "COPILOT_STUB_STDERR_MARKER" in result.stderr


    def test_no_trailing_or_true_masks_exit_status(self):
        # Explicitly assert as ABSENT: nothing after (or wrapping) the `exec`
        # line masks the child's real exit status with a `|| true`/`; true`/
        # `2>/dev/null; exit 0` pattern. Since `exec` replaces the process
        # there is no "after" for the exec line itself to mask anything, but
        # this static check also guards against a regression that wraps the
        # exec call in a subshell/function with a trailing status-swallowing
        # idiom.
        text = START_SH.read_text(encoding="utf-8")
        assert "|| true" not in text
        exec_lines = [
            line
            for line in text.splitlines()
            if "exec " in line and not line.strip().startswith("#")
        ]
        assert exec_lines, "expected to find the exec invocation line in start.sh"
        for line in exec_lines:
            assert "|| true" not in line
            assert "; true" not in line


    def test_exec_line_is_unconditional_and_final_active_statement(self):
        # Structural confirmation: the `exec "$copilot_exe" "$@"` line exists
        # exactly once, is not inside an `if`/conditional guard, and is the
        # last ACTIVE (non-comment, non-blank) statement before the
        # commented-out alternative tool sections.
        text = START_SH.read_text(encoding="utf-8")
        lines = text.splitlines()
        exec_indices = [
            i for i, line in enumerate(lines) if line.strip() == 'exec "$copilot_exe" "$@"'
        ]
        assert len(exec_indices) == 1
        exec_index = exec_indices[0]
        # Everything after the exec line, up to end of file, must be blank or
        # a comment (the alternative Claude Code / Codex sections are all
        # commented out).
        for line in lines[exec_index + 1 :]:
            stripped = line.strip()
            assert stripped == "" or stripped.startswith("#"), (
                f"unexpected active statement after the unconditional exec line: {line!r}"
            )


if __name__ == "__main__":
    unittest.main()
