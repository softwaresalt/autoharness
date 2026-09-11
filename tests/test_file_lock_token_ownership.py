"""TDD tests for SHIP-3 token-based lock ownership verification (153.002-T).

Protects the O2 capability-token mechanism added to
`templates/skills/file-lock/scripts/{acquire,release}_lock.{ps1,sh}`:

* acquire generates a CSPRNG token (V-a: 32 bytes / 256 bits, 64-char
  lowercase hex), writes only its SHA-256 digest (`owner_digest`, V-b) into
  the lock file, and prints the token itself on stdout as a
  `LOCK_TOKEN=<token>` line so the caller can capture it (TC5).
* release requires the caller to present the same token (`-Token`/`--token`,
  or the `LOCK_TOKEN` environment variable) and refuses (non-zero exit, lock
  left in place) when it is absent or does not match the recorded digest,
  unless the operator supplies `-Force`/`--force` (decision (ii)).
* release never re-prints the token or the `owner_digest` in any status,
  warning, or error message (TC5d).
* release no longer crashes on a root-level, relative, non-existent target
  (finding 6 regression, already covered narrowly for the "no lock file at
  all" branch here; the acquire/release path-consistency claim is exercised
  by the successful acquire->release round trip in
  `test_release_with_correct_token_succeeds_and_removes_lock`).

Vectors V-a/V-b and the frozen V-c/V-c2 constants are recorded in
`docs/research/2026-09-10-ship3-file-lock-behavior-matrix-and-token-vectors.md`;
this suite exercises the *scripts'* own token generation and verification
logic (an integration-level check), not a re-derivation of those frozen
values.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "templates" / "skills" / "file-lock" / "scripts"
_PS1_ACQUIRE = _SCRIPTS_DIR / "acquire_lock.ps1"
_PS1_RELEASE = _SCRIPTS_DIR / "release_lock.ps1"
_SH_ACQUIRE = _SCRIPTS_DIR / "acquire_lock.sh"
_SH_RELEASE = _SCRIPTS_DIR / "release_lock.sh"

_PWSH_CANDIDATES = [shutil.which("pwsh"), shutil.which("powershell")]
_PWSH_INTERPRETERS = [p for p in _PWSH_CANDIDATES if p]
_BASH = shutil.which("bash")

_TOKEN_LINE_RE = re.compile(r"^LOCK_TOKEN=([0-9a-f]{64})$", re.MULTILINE)


def _expected_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _run_ps1(interpreter: str, script: Path, args: list[str], cwd: Path):
    full_args = [
        interpreter,
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script),
    ] + args
    return subprocess.run(
        full_args, cwd=cwd, capture_output=True, text=True, timeout=60
    )


@unittest.skipUnless(_PWSH_INTERPRETERS, "no PowerShell interpreter available")
class FileLockTokenOwnershipPs1Tests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.target = self.root / "target.txt"
        self.target.write_text("contained", encoding="utf-8")
        self.lock_file = self.root / ".target.txt.lock"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _acquire(self, interpreter: str):
        return _run_ps1(
            interpreter,
            _PS1_ACQUIRE,
            [str(self.target), "-WorkspaceRoot", str(self.root)],
            cwd=self.root,
        )

    def _release(self, interpreter: str, extra_args: list[str] | None = None):
        args = [str(self.target)]
        if extra_args:
            args += extra_args
        return _run_ps1(interpreter, _PS1_RELEASE, args, cwd=self.root)

    def test_acquire_prints_capturable_token_and_stores_digest_not_token(self) -> None:
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                if self.lock_file.exists():
                    self.lock_file.unlink()
                result = self._acquire(interpreter)
                self.assertEqual(result.returncode, 0, msg=result.stderr)
                match = _TOKEN_LINE_RE.search(result.stdout)
                self.assertIsNotNone(
                    match, msg=f"no LOCK_TOKEN= line found in: {result.stdout!r}"
                )
                token = match.group(1)
                lock_content = self.lock_file.read_text(encoding="utf-8")
                self.assertNotIn(
                    token, lock_content, msg="token itself must never be persisted"
                )
                expected_digest = _expected_digest(token)
                self.assertIn(f"owner_digest: {expected_digest}", lock_content)
                self.lock_file.unlink()

    def test_release_without_token_and_without_force_is_refused(self) -> None:
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                if self.lock_file.exists():
                    self.lock_file.unlink()
                acquire_result = self._acquire(interpreter)
                self.assertEqual(acquire_result.returncode, 0, msg=acquire_result.stderr)
                release_result = self._release(interpreter)
                self.assertNotEqual(release_result.returncode, 0)
                self.assertTrue(self.lock_file.exists())
                self.lock_file.unlink()

    def test_release_with_correct_token_succeeds_and_removes_lock(self) -> None:
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                if self.lock_file.exists():
                    self.lock_file.unlink()
                acquire_result = self._acquire(interpreter)
                token = _TOKEN_LINE_RE.search(acquire_result.stdout).group(1)
                release_result = self._release(
                    interpreter, ["-Token", token]
                )
                self.assertEqual(release_result.returncode, 0, msg=release_result.stderr)
                self.assertFalse(self.lock_file.exists())

    def test_release_with_wrong_token_is_refused(self) -> None:
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                if self.lock_file.exists():
                    self.lock_file.unlink()
                acquire_result = self._acquire(interpreter)
                self.assertEqual(acquire_result.returncode, 0, msg=acquire_result.stderr)
                wrong_token = "0" * 64
                release_result = self._release(interpreter, ["-Token", wrong_token])
                self.assertNotEqual(release_result.returncode, 0)
                self.assertTrue(self.lock_file.exists())
                self.lock_file.unlink()

    def test_release_with_force_overrides_missing_token(self) -> None:
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                if self.lock_file.exists():
                    self.lock_file.unlink()
                acquire_result = self._acquire(interpreter)
                self.assertEqual(acquire_result.returncode, 0, msg=acquire_result.stderr)
                release_result = self._release(interpreter, ["-Force"])
                self.assertEqual(release_result.returncode, 0, msg=release_result.stderr)
                self.assertFalse(self.lock_file.exists())

    def test_release_never_prints_token_or_digest(self) -> None:
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                if self.lock_file.exists():
                    self.lock_file.unlink()
                acquire_result = self._acquire(interpreter)
                token = _TOKEN_LINE_RE.search(acquire_result.stdout).group(1)
                digest = _expected_digest(token)
                # Wrong-token refusal path.
                wrong_release = self._release(interpreter, ["-Token", "1" * 64])
                combined = wrong_release.stdout + wrong_release.stderr
                self.assertNotIn(token, combined)
                self.assertNotIn(digest, combined)
                # Correct-token success path.
                right_release = self._release(interpreter, ["-Token", token])
                combined_ok = right_release.stdout + right_release.stderr
                self.assertNotIn(digest, combined_ok)

    def test_release_root_level_missing_target_does_not_crash(self) -> None:
        """Finding 6 regression: a root-level relative target that does not
        exist, and has no lock file, must not throw under strict mode."""
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                missing_root_level = self.root / "MISSING.md"
                self.assertFalse(missing_root_level.exists())
                result = _run_ps1(
                    interpreter,
                    _PS1_RELEASE,
                    ["MISSING.md"],
                    cwd=self.root,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    msg=(
                        "a missing root-level relative target with no lock "
                        f"file must warn and exit 0, not crash: "
                        f"stdout={result.stdout} stderr={result.stderr}"
                    ),
                )


def _read_lf(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


@unittest.skipIf(sys.platform == "win32", "bash on Windows is WSL; run sh on POSIX/CI")
@unittest.skipUnless(_BASH, "bash not available")
class FileLockTokenOwnershipShTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.target = self.root / "target.txt"
        self.target.write_text("contained", encoding="utf-8")
        self.lock_file = self.root / ".target.txt.lock"

        self.acquire_script = self.root / "acquire_lock.sh"
        self.acquire_script.write_bytes(_read_lf(_SH_ACQUIRE).encode("utf-8"))
        self.acquire_script.chmod(0o755)
        self.release_script = self.root / "release_lock.sh"
        self.release_script.write_bytes(_read_lf(_SH_RELEASE).encode("utf-8"))
        self.release_script.chmod(0o755)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _acquire(self):
        return subprocess.run(
            [_BASH, str(self.acquire_script), str(self.target), "--workspace-root", str(self.root)],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def _release(self, extra_args: list[str] | None = None):
        args = [str(self.target)]
        if extra_args:
            args += extra_args
        return subprocess.run(
            [_BASH, str(self.release_script)] + args,
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def test_acquire_prints_capturable_token_and_stores_digest_not_token(self) -> None:
        result = self._acquire()
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        match = _TOKEN_LINE_RE.search(result.stdout)
        self.assertIsNotNone(match, msg=f"no LOCK_TOKEN= line found in: {result.stdout!r}")
        token = match.group(1)
        lock_content = self.lock_file.read_text(encoding="utf-8")
        self.assertNotIn(token, lock_content)
        expected_digest = _expected_digest(token)
        self.assertIn(f"owner_digest: {expected_digest}", lock_content)

    def test_release_without_token_and_without_force_is_refused(self) -> None:
        acquire_result = self._acquire()
        self.assertEqual(acquire_result.returncode, 0, msg=acquire_result.stderr)
        release_result = self._release()
        self.assertNotEqual(release_result.returncode, 0)
        self.assertTrue(self.lock_file.exists())

    def test_release_with_correct_token_succeeds_and_removes_lock(self) -> None:
        acquire_result = self._acquire()
        token = _TOKEN_LINE_RE.search(acquire_result.stdout).group(1)
        release_result = self._release(["--token", token])
        self.assertEqual(release_result.returncode, 0, msg=release_result.stderr)
        self.assertFalse(self.lock_file.exists())

    def test_release_with_wrong_token_is_refused(self) -> None:
        acquire_result = self._acquire()
        self.assertEqual(acquire_result.returncode, 0, msg=acquire_result.stderr)
        release_result = self._release(["--token", "0" * 64])
        self.assertNotEqual(release_result.returncode, 0)
        self.assertTrue(self.lock_file.exists())

    def test_release_with_force_overrides_missing_token(self) -> None:
        acquire_result = self._acquire()
        self.assertEqual(acquire_result.returncode, 0, msg=acquire_result.stderr)
        release_result = self._release(["--force"])
        self.assertEqual(release_result.returncode, 0, msg=release_result.stderr)
        self.assertFalse(self.lock_file.exists())

    def test_release_never_prints_token_or_digest(self) -> None:
        acquire_result = self._acquire()
        token = _TOKEN_LINE_RE.search(acquire_result.stdout).group(1)
        digest = _expected_digest(token)
        wrong_release = self._release(["--token", "1" * 64])
        combined = wrong_release.stdout + wrong_release.stderr
        self.assertNotIn(token, combined)
        self.assertNotIn(digest, combined)
        right_release = self._release(["--token", token])
        combined_ok = right_release.stdout + right_release.stderr
        self.assertNotIn(digest, combined_ok)

    def test_release_root_level_missing_target_does_not_crash(self) -> None:
        missing_root_level = self.root / "MISSING.md"
        self.assertFalse(missing_root_level.exists())
        result = subprocess.run(
            [_BASH, str(self.release_script), "MISSING.md"],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout={result.stdout} stderr={result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
