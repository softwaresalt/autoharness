"""TDD tests for SHIP-3 workspace-root containment in the file-lock acquire
scripts (153.001-T).

Protects `templates/skills/file-lock/scripts/acquire_lock.{ps1,sh}` against
the H2/H4 escape classes recorded empirically in task 0's behaviour matrix
(`docs/research/2026-09-10-ship3-file-lock-behavior-matrix-and-token-vectors.md`):
absolute path outside the root, `../` traversal, directory symlink/junction
escape, sibling shared-prefix false containment, and nested-git-checkout
root widening (`git rev-parse --show-toplevel` resolving to a parent repo).

PowerShell tests run against both `pwsh` (PowerShell 7+) and Windows
PowerShell 5.1 (`powershell.exe`) when available, because the real-path
resolver must work identically on both (H5) — a P/Invoke `GetFinalPathNameByHandle`
implementation is used specifically because it is available on both runtimes,
unlike the newer `FileSystemInfo.ResolveLinkTarget`/`LinkTarget` APIs which are
.NET-Core-only.

POSIX (`.sh`) tests are skipped on `win32` following the same convention as
`tests/test_deploy_harness_scripts.py` ("bash on Windows is WSL; run sh on
POSIX/CI") — the equivalent behaviour was manually verified against WSL bash
during task 0's de-risking matrix and is exercised for real by Linux CI.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PS1_ACQUIRE = _REPO_ROOT / "templates" / "skills" / "file-lock" / "scripts" / "acquire_lock.ps1"
_SH_ACQUIRE = _REPO_ROOT / "templates" / "skills" / "file-lock" / "scripts" / "acquire_lock.sh"

_PWSH_CANDIDATES = [shutil.which("pwsh"), shutil.which("powershell")]
_PWSH_INTERPRETERS = [p for p in _PWSH_CANDIDATES if p]
_BASH = shutil.which("bash")


def _run_ps1(interpreter: str, args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    full_args = [
        interpreter,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(_PS1_ACQUIRE),
    ] + args
    return subprocess.run(
        full_args, cwd=cwd, capture_output=True, text=True, timeout=60
    )


def _make_junction(link_path: Path, target: Path, interpreter: str) -> None:
    """Create a Windows directory junction without requiring admin rights."""
    cmd = [
        interpreter,
        "-NoProfile",
        "-Command",
        f"New-Item -ItemType Junction -Path '{link_path}' -Target '{target}' | Out-Null",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"junction creation failed: {result.stderr}")


@unittest.skipUnless(_PWSH_INTERPRETERS, "no PowerShell interpreter available")
class AcquireLockContainmentPs1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.ws = self.root / "ws"
        self.ws_sub = self.ws / "sub"
        self.ws_sub.mkdir(parents=True)
        self.outside = self.root / "outside"
        self.outside.mkdir()
        self.ws_evil = self.root / "ws-evil"
        self.ws_evil.mkdir()

        (self.ws_sub / "target.txt").write_text("contained", encoding="utf-8")
        (self.outside / "evil.txt").write_text("outside", encoding="utf-8")
        (self.ws_evil / "evil.txt").write_text("sibling", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_contained_file_with_explicit_root_succeeds(self) -> None:
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                target = self.ws_sub / "target.txt"
                result = _run_ps1(
                    interpreter,
                    [str(target), "-WorkspaceRoot", str(self.ws)],
                    cwd=self.ws,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    msg=f"stdout={result.stdout} stderr={result.stderr}",
                )
                lock_file = self.ws_sub / ".target.txt.lock"
                self.assertTrue(lock_file.exists())
                lock_file.unlink()

    def test_absolute_path_outside_root_rejected(self) -> None:
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                target = self.outside / "evil.txt"
                result = _run_ps1(
                    interpreter,
                    [str(target), "-WorkspaceRoot", str(self.ws)],
                    cwd=self.ws,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.outside / ".evil.txt.lock").exists())

    def test_relative_traversal_outside_root_rejected(self) -> None:
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                result = _run_ps1(
                    interpreter,
                    ["../../outside/evil.txt", "-WorkspaceRoot", str(self.ws)],
                    cwd=self.ws_sub,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.outside / ".evil.txt.lock").exists())

    def test_sibling_shared_prefix_directory_rejected(self) -> None:
        """Regression test for the H4 naive-prefix bug: `ws-evil` must never
        be treated as contained within `ws` merely because the string
        `ws-evil` starts with `ws`."""
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                target = self.ws_evil / "evil.txt"
                result = _run_ps1(
                    interpreter,
                    [str(target), "-WorkspaceRoot", str(self.ws)],
                    cwd=self.ws,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.ws_evil / ".evil.txt.lock").exists())

    def test_directory_junction_escape_rejected(self) -> None:
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                link_path = self.ws / f"linkout-{Path(interpreter).stem}"
                _make_junction(link_path, self.outside, interpreter)
                target = link_path / "evil.txt"
                result = _run_ps1(
                    interpreter,
                    [str(target), "-WorkspaceRoot", str(self.ws)],
                    cwd=self.ws,
                )
                self.assertNotEqual(
                    result.returncode,
                    0,
                    msg=(
                        "a directory junction inside the workspace root that "
                        "points outside must not be treated as contained "
                        f"(stdout={result.stdout} stderr={result.stderr})"
                    ),
                )
                self.assertFalse((self.outside / ".evil.txt.lock").exists())

    def test_missing_workspace_root_git_derived_default_succeeds(self) -> None:
        """When --workspace-root is omitted, a git-derived root is trusted
        only when the script's own installed directory is a direct `scripts/`
        child of that root (the concrete, checkable operationalisation of
        plan decision (i), recorded in task 0's matrix)."""
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                repo_root = self.root / f"repo-{Path(interpreter).stem}"
                scripts_dir = repo_root / "scripts"
                scripts_dir.mkdir(parents=True)
                subprocess.run(
                    ["git", "init", "-q"],
                    cwd=repo_root,
                    check=True,
                    capture_output=True,
                )
                shutil.copy2(_PS1_ACQUIRE, scripts_dir / "acquire_lock.ps1")
                target = repo_root / "AGENTS.md"
                target.write_text("root-level", encoding="utf-8")

                full_args = [
                    interpreter,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(scripts_dir / "acquire_lock.ps1"),
                    str(target),
                ]
                result = subprocess.run(
                    full_args,
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    msg=f"stdout={result.stdout} stderr={result.stderr}",
                )

    def test_missing_workspace_root_nested_checkout_fails_closed(self) -> None:
        """Case 7 (finding 2): a nested workspace with no `.git` of its own,
        inside an outer repo, must not silently widen to the outer root."""
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                outer_repo = self.root / f"outer-{Path(interpreter).stem}"
                nested_ws = outer_repo / "nested-ws"
                scripts_dir = nested_ws / "scripts"
                scripts_dir.mkdir(parents=True)
                subprocess.run(
                    ["git", "init", "-q"],
                    cwd=outer_repo,
                    check=True,
                    capture_output=True,
                )
                shutil.copy2(_PS1_ACQUIRE, scripts_dir / "acquire_lock.ps1")
                target = nested_ws / "AGENTS.md"
                target.write_text("root-level", encoding="utf-8")

                full_args = [
                    interpreter,
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(scripts_dir / "acquire_lock.ps1"),
                    str(target),
                ]
                result = subprocess.run(
                    full_args,
                    cwd=nested_ws,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertNotEqual(
                    result.returncode,
                    0,
                    msg=(
                        "a nested checkout without its own .git must fail closed "
                        "and demand an explicit -WorkspaceRoot rather than "
                        f"silently widening to the outer repo (stdout={result.stdout} "
                        f"stderr={result.stderr})"
                    ),
                )


def _read_lf(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


@unittest.skipIf(sys.platform == "win32", "bash on Windows is WSL; run sh on POSIX/CI")
@unittest.skipUnless(_BASH, "bash not available")
class AcquireLockContainmentShTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.ws = self.root / "ws"
        self.ws_sub = self.ws / "sub"
        self.ws_sub.mkdir(parents=True)
        self.outside = self.root / "outside"
        self.outside.mkdir()
        self.ws_evil = self.root / "ws-evil"
        self.ws_evil.mkdir()

        (self.ws_sub / "target.txt").write_text("contained", encoding="utf-8")
        (self.outside / "evil.txt").write_text("outside", encoding="utf-8")
        (self.ws_evil / "evil.txt").write_text("sibling", encoding="utf-8")

        self.script = self.root / "acquire_lock.sh"
        self.script.write_bytes(_read_lf(_SH_ACQUIRE).encode("utf-8"))
        self.script.chmod(0o755)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, args: list[str], cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [_BASH, str(self.script)] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_contained_file_with_explicit_root_succeeds(self) -> None:
        target = self.ws_sub / "target.txt"
        result = self._run(
            [str(target), "--workspace-root", str(self.ws)], cwd=self.ws
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((self.ws_sub / ".target.txt.lock").exists())

    def test_absolute_path_outside_root_rejected(self) -> None:
        target = self.outside / "evil.txt"
        result = self._run(
            [str(target), "--workspace-root", str(self.ws)], cwd=self.ws
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.outside / ".evil.txt.lock").exists())

    def test_relative_traversal_outside_root_rejected(self) -> None:
        result = self._run(
            ["../../outside/evil.txt", "--workspace-root", str(self.ws)],
            cwd=self.ws_sub,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.outside / ".evil.txt.lock").exists())

    def test_sibling_shared_prefix_directory_rejected(self) -> None:
        target = self.ws_evil / "evil.txt"
        result = self._run(
            [str(target), "--workspace-root", str(self.ws)], cwd=self.ws
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.ws_evil / ".evil.txt.lock").exists())

    def test_symlink_escape_rejected(self) -> None:
        link_path = self.ws / "linkout"
        link_path.symlink_to(self.outside, target_is_directory=True)
        target = link_path / "evil.txt"
        result = self._run(
            [str(target), "--workspace-root", str(self.ws)], cwd=self.ws
        )
        self.assertNotEqual(result.returncode, 0, msg=result.stderr)
        self.assertFalse((self.outside / ".evil.txt.lock").exists())

    def test_missing_workspace_root_git_derived_default_succeeds(self) -> None:
        repo_root = self.root / "repo"
        scripts_dir = repo_root / "scripts"
        scripts_dir.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-q"], cwd=repo_root, check=True, capture_output=True
        )
        script_copy = scripts_dir / "acquire_lock.sh"
        script_copy.write_bytes(_read_lf(_SH_ACQUIRE).encode("utf-8"))
        script_copy.chmod(0o755)
        target = repo_root / "AGENTS.md"
        target.write_text("root-level", encoding="utf-8")

        result = subprocess.run(
            [_BASH, str(script_copy), str(target)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

    def test_missing_workspace_root_nested_checkout_fails_closed(self) -> None:
        outer_repo = self.root / "outer"
        nested_ws = outer_repo / "nested-ws"
        scripts_dir = nested_ws / "scripts"
        scripts_dir.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-q"], cwd=outer_repo, check=True, capture_output=True
        )
        script_copy = scripts_dir / "acquire_lock.sh"
        script_copy.write_bytes(_read_lf(_SH_ACQUIRE).encode("utf-8"))
        script_copy.chmod(0o755)
        target = nested_ws / "AGENTS.md"
        target.write_text("root-level", encoding="utf-8")

        result = subprocess.run(
            [_BASH, str(script_copy), str(target)],
            cwd=nested_ws,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertNotEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
