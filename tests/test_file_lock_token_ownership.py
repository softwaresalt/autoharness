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

# Frozen (token -> owner_digest) constants from V-c/V-c2 in
# docs/research/2026-09-10-ship3-file-lock-behavior-matrix-and-token-vectors.md.
# Per the plan (153.002-T), task 2 MUST cite these by name as the expected
# value source and MUST NOT compute an expected digest from its own
# implementation -- so these literals are transcribed verbatim from the
# research doc, not derived here.
_FROZEN_VECTORS_V_C = [
    (
        "V-c-1",
        "e83b05973c834241b240698aacb6d11e1722cf7e8261ba5bb2af45f6ec1ca30a",
        "96aa0ac1a81d5616a6a468f888d4f727958e15d33a6d9d00bf080d4c7ea2ae4e",
    ),
    (
        "V-c-2",
        "cec53b030c1d80eab1582ab06daf42204906075565aad99a6c0d23c52b1059c2",
        "be46528d300d259b3bfa5a32ace47f22972d500ae1412ce59a02fa7b480da4ad",
    ),
    (
        "V-c-3",
        "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "df0790f236013511e91fa4532fb7761f62320a51a3868dabf4a13fe5f53e3263",
    ),
    (
        "V-c-4a",
        "e0f0240b96cf3810ac4679762271e2916785e5ce24b755f2ae59d4c454914d21",
        "75004610c37b3f618cb133894712ee9c3fd68e9bb9036a33fc08ca4a6f9139e1",
    ),
    (
        "V-c-4b",
        "e0f0240b96cf3810ac4679762271e2916785e5ce24b755f2ae59d4c454914d22",
        "9c5fef6103f589f40e681b2ef292335e5145bc3b51f65464029d2b724573f6a7",
    ),
]

# V-c2: derived from V-c-1 by adding/removing exactly one trailing character.
# Rejected before a digest is ever computed -- there is no (token ->
# owner_digest) pair for either.
_FROZEN_VECTOR_V_C2_SHORT = (
    "V-c2-short",
    "e83b05973c834241b240698aacb6d11e1722cf7e8261ba5bb2af45f6ec1ca30",
)
_FROZEN_VECTOR_V_C2_LONG = (
    "V-c2-long",
    "e83b05973c834241b240698aacb6d11e1722cf7e8261ba5bb2af45f6ec1ca30aa",
)

# V-c "malformed/uppercase" vector: a charset violation (uppercase hex),
# not a length-boundary violation -- V-a's alphabet is lowercase-only.
_FROZEN_VECTOR_UPPERCASE_MALFORMED = (
    "V-c-uppercase-malformed",
    _FROZEN_VECTORS_V_C[0][1].upper(),
)


def _write_lock_file_with_digest(
    lock_path: Path,
    digest: str,
    agent: str = "test-agent",
    pid: int = 12345,
    timestamp: str = "2026-01-01T00:00:00Z",
    file_field: str = "target.txt",
) -> None:
    """Construct a lock file directly with a given owner_digest, bypassing
    acquire, so a release script can be exercised against the frozen V-c/
    V-c2 constants (which are not produced by any live acquire call)."""
    content = (
        f"agent: {agent}\n"
        f"timestamp: {timestamp}\n"
        f"pid: {pid}\n"
        f"file: {file_field}\n"
        f"owner_digest: {digest}\n"
    )
    lock_path.write_text(content, encoding="utf-8")


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


def _make_junction(link_path: Path, target: Path, interpreter: str) -> None:
    """Create a directory reparse point without requiring admin rights.

    Windows: a directory junction (`-ItemType Junction`) needs no elevated
    privileges. Non-Windows (pwsh on Linux/macOS): `-ItemType Junction` is
    an NTFS-only concept that PowerShell's Unix FileSystemProvider does not
    implement as a real reparse point -- it can return exit 0 without
    creating anything at all (a silent no-op, not a terminating error), so
    a bare returncode check is not sufficient. Use `-ItemType SymbolicLink`
    on non-Windows instead (ordinary users can create symlinks on
    Linux/macOS with no elevation), and explicitly verify the link now
    resolves to an existing path before returning, so a silent failure on
    either platform surfaces as a loud RuntimeError rather than a
    misleading downstream test failure."""
    item_type = "Junction" if sys.platform == "win32" else "SymbolicLink"
    cmd = [
        interpreter,
        "-NoProfile",
        "-Command",
        f"New-Item -ItemType {item_type} -Path '{link_path}' -Target '{target}' | Out-Null",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        raise RuntimeError(f"{item_type} creation failed: {result.stderr}")
    if not link_path.exists():
        raise RuntimeError(
            f"{item_type} creation reported success but '{link_path}' does "
            f"not resolve to an existing path (stderr={result.stderr!r})"
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

    def test_acquire_token_is_captured_by_powershell_success_stream(self) -> None:
        """Round-5 Copilot review regression: the token line used to be
        emitted via `Write-Host`, which writes to the host/information
        stream and is NEVER received by ordinary PowerShell success-stream
        capture (e.g. `$result = & ./acquire_lock.ps1 ...`) -- even though
        it does appear on the process's raw stdout, which is why the
        subprocess-based `result.stdout` assertions above did not catch
        this. Since release_lock.ps1 requires the token, any caller using
        the idiomatic capture pattern would silently receive no token at
        all. Invoke the script from WITHIN a wrapper PowerShell process via
        variable assignment (not raw stdout capture) and assert the
        LOCK_TOKEN line is present in that captured success-stream output."""
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                if self.lock_file.exists():
                    self.lock_file.unlink()
                wrapper_command = (
                    f"$result = & '{_PS1_ACQUIRE}' '{self.target}' "
                    f"-WorkspaceRoot '{self.root}'; "
                    "$result -join \"`n\""
                )
                result = subprocess.run(
                    [
                        interpreter,
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-Command",
                        wrapper_command,
                    ],
                    cwd=self.root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                self.assertEqual(result.returncode, 0, msg=result.stderr)
                match = _TOKEN_LINE_RE.search(result.stdout)
                self.assertIsNotNone(
                    match,
                    msg=(
                        "LOCK_TOKEN line missing from PowerShell success-stream "
                        f"capture (variable assignment): {result.stdout!r} "
                        f"stderr={result.stderr!r}"
                    ),
                )
                self.lock_file.unlink()

    def test_acquire_contention_diagnostic_never_prints_owner_digest(self) -> None:
        """Round-6 Copilot review regression: adding owner_digest (O2) to the
        lock payload made the pre-existing contention diagnostic (printed
        when acquire finds an existing lock) echo the raw lock file content,
        which now includes owner_digest -- contradicting TC5d's "status,
        verbose, or error messages must never print owner_digest or the
        token" guarantee. A second acquire attempt against an already-locked
        target must report agent/pid/timestamp but never the digest."""
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                if self.lock_file.exists():
                    self.lock_file.unlink()
                first = self._acquire(interpreter)
                self.assertEqual(first.returncode, 0, msg=first.stderr)
                first_token = _TOKEN_LINE_RE.search(first.stdout).group(1)
                expected_digest = _expected_digest(first_token)
                second = self._acquire(interpreter)
                self.assertNotEqual(second.returncode, 0)
                combined = second.stdout + second.stderr
                self.assertNotIn(
                    expected_digest,
                    combined,
                    msg=f"owner_digest leaked in contention diagnostic: {combined!r}",
                )
                self.assertNotIn("owner_digest", combined)
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

    def test_release_missing_target_resolves_lock_through_junction_parent(
        self,
    ) -> None:
        """Round-6 Copilot review regression (H5 parity): when the target
        does not exist, release_lock.ps1's missing-target branch used to
        resolve the parent directory purely lexically (GetFullPath, no
        reparse-point dereferencing), while release_lock.sh's equivalent
        branch already resolves the parent via `realpath` (dereferencing
        symlinks/junctions). A lock file created at the REAL parent path
        must be found and removed even when release is invoked through a
        junction that points at that real parent."""
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                iteration_root = Path(tempfile.mkdtemp(dir=self.root))
                real_parent = iteration_root / "real_parent"
                real_parent.mkdir()
                link_parent = iteration_root / "link_parent"
                _make_junction(link_parent, real_parent, interpreter)
                # Target does not exist under either path.
                real_lock_file = real_parent / ".missing.txt.lock"
                _write_lock_file_with_digest(
                    real_lock_file, _expected_digest("irrelevant-token")
                )
                self.assertTrue(real_lock_file.exists())
                result = _run_ps1(
                    interpreter,
                    _PS1_RELEASE,
                    [str(link_parent / "missing.txt"), "-Force"],
                    cwd=iteration_root,
                )
                self.assertEqual(
                    result.returncode,
                    0,
                    msg=(
                        "release through a junction to a missing target "
                        f"must succeed: stdout={result.stdout} "
                        f"stderr={result.stderr}"
                    ),
                )
                self.assertFalse(
                    real_lock_file.exists(),
                    msg=(
                        "release must resolve the junctioned parent to its "
                        "real path and remove the lock file created there, "
                        "matching acquire's/release_lock.sh's reparse-point "
                        "dereferencing behaviour (H5 parity)"
                    ),
                )
                lexical_lock_file = link_parent / ".missing.txt.lock"
                self.assertFalse(
                    lexical_lock_file.is_file(),
                    msg="no separate lock file should be created at the lexical junction path",
                )

    def test_release_workspace_root_anchoring_round_trip_from_different_cwd(
        self,
    ) -> None:
        """Round-6 Copilot review regression (finding 6, CWD-independence):
        acquire and release must compute the SAME lock path for the same
        documented workspace-relative path, regardless of the caller's
        current working directory, when -WorkspaceRoot is supplied. Acquire
        from one CWD, then release from a DIFFERENT CWD using the same
        relative path anchored by -WorkspaceRoot, and confirm the lock
        created during acquire is found and removed."""
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                iteration_root = Path(tempfile.mkdtemp(dir=self.root))
                nested_dir = iteration_root / "nested"
                nested_dir.mkdir()
                nested_target = nested_dir / "file.txt"
                nested_target.write_text("contained", encoding="utf-8")
                rel_path = "nested/file.txt"
                lock_file = nested_dir / ".file.txt.lock"
                if lock_file.exists():
                    lock_file.unlink()

                acquire_result = _run_ps1(
                    interpreter,
                    _PS1_ACQUIRE,
                    [rel_path, "-WorkspaceRoot", str(iteration_root)],
                    cwd=iteration_root,
                )
                self.assertEqual(acquire_result.returncode, 0, msg=acquire_result.stderr)
                token_match = _TOKEN_LINE_RE.search(acquire_result.stdout)
                self.assertIsNotNone(token_match)
                token = token_match.group(1)
                self.assertTrue(lock_file.exists())

                other_cwd_tmp = tempfile.TemporaryDirectory()
                try:
                    other_cwd = Path(other_cwd_tmp.name).resolve()
                    self.assertNotEqual(other_cwd, iteration_root)
                    release_result = _run_ps1(
                        interpreter,
                        _PS1_RELEASE,
                        [
                            rel_path,
                            "-WorkspaceRoot",
                            str(iteration_root),
                            "-Token",
                            token,
                        ],
                        cwd=other_cwd,
                    )
                    self.assertEqual(
                        release_result.returncode,
                        0,
                        msg=(
                            "release from a different CWD with the same "
                            "-WorkspaceRoot-anchored relative path must "
                            f"succeed: stdout={release_result.stdout} "
                            f"stderr={release_result.stderr}"
                        ),
                    )
                    self.assertFalse(
                        lock_file.exists(),
                        msg="release must remove the lock created by acquire at the anchored real path",
                    )
                finally:
                    other_cwd_tmp.cleanup()

    def test_frozen_v_c_vectors_release_succeeds(self) -> None:
        """TC1-TC6 mandatory acceptance (153.002-T): the release script's own
        digest routine must agree with every frozen V-c constant, not a
        digest re-derived from this test."""
        for interpreter in _PWSH_INTERPRETERS:
            for label, token, digest in _FROZEN_VECTORS_V_C:
                with self.subTest(interpreter=interpreter, vector=label):
                    _write_lock_file_with_digest(self.lock_file, digest)
                    result = self._release(interpreter, ["-Token", token])
                    self.assertEqual(
                        result.returncode, 0, msg=f"{label}: {result.stderr}"
                    )
                    self.assertFalse(self.lock_file.exists())

    def test_frozen_v_c2_length_boundary_vectors_rejected_before_digest(self) -> None:
        """V-c2: a wrong-length token must be rejected with a NAMED error
        before any digest is computed -- not silently hashed and compared."""
        for interpreter in _PWSH_INTERPRETERS:
            for label, token in (_FROZEN_VECTOR_V_C2_SHORT, _FROZEN_VECTOR_V_C2_LONG):
                with self.subTest(interpreter=interpreter, vector=label):
                    # The stored digest is irrelevant here -- V-c2 tokens must
                    # be rejected before any digest comparison is attempted.
                    _write_lock_file_with_digest(self.lock_file, _FROZEN_VECTORS_V_C[0][2])
                    result = self._release(interpreter, ["-Token", token])
                    self.assertNotEqual(
                        result.returncode, 0, msg=f"{label} must be rejected"
                    )
                    self.assertIn(
                        "TOKEN_MALFORMED",
                        result.stderr,
                        msg=f"{label} must surface a named validation error",
                    )
                    self.assertTrue(
                        self.lock_file.exists(),
                        msg=f"{label}: lock must remain since nothing was verified",
                    )
                    self.lock_file.unlink()

    def test_uppercase_token_rejected_as_malformed(self) -> None:
        """V-a's alphabet is lowercase-only; an uppercase rendering of an
        otherwise-valid-length token is a charset violation, not a digest
        mismatch, and must be rejected before hashing."""
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                label, token = _FROZEN_VECTOR_UPPERCASE_MALFORMED
                _write_lock_file_with_digest(self.lock_file, _FROZEN_VECTORS_V_C[0][2])
                result = self._release(interpreter, ["-Token", token])
                self.assertNotEqual(result.returncode, 0, msg=label)
                self.assertIn("TOKEN_MALFORMED", result.stderr)
                self.assertTrue(self.lock_file.exists())
                self.lock_file.unlink()

    def test_refusal_message_reports_lock_path_and_age_and_force_remedy(self) -> None:
        """Plan review finding 1 (P0), mandatory acceptance on 153.002-T: the
        refusal message must state the lock path, agent/pid, the computed
        age, the 1-hour staleness heuristic when exceeded, and the exact
        --force/-Force remedy -- never the token or owner_digest."""
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                if self.lock_file.exists():
                    self.lock_file.unlink()
                acquire_result = self._acquire(interpreter)
                self.assertEqual(acquire_result.returncode, 0, msg=acquire_result.stderr)
                lock_content = self.lock_file.read_text(encoding="utf-8")
                stale_ts = "2020-01-01T00:00:00Z"
                new_content = re.sub(
                    r"^timestamp: .*$", f"timestamp: {stale_ts}", lock_content, flags=re.MULTILINE
                )
                self.lock_file.write_text(new_content, encoding="utf-8")
                release_result = self._release(interpreter, ["-Token", "0" * 64])
                self.assertNotEqual(release_result.returncode, 0)
                self.assertIn(str(self.lock_file), release_result.stderr)
                self.assertIn("stale", release_result.stderr.lower())
                self.assertIn("-Force", release_result.stderr)
                self.lock_file.unlink()


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

    def test_acquire_contention_diagnostic_never_prints_owner_digest(self) -> None:
        """Round-6 Copilot review regression: adding owner_digest (O2) to the
        lock payload made the pre-existing contention diagnostic (printed
        when acquire finds an existing lock) echo the raw lock file content
        via `cat`, which now includes owner_digest -- contradicting TC5d's
        "status, verbose, or error messages must never print owner_digest or
        the token" guarantee. A second acquire attempt against an
        already-locked target must report agent/pid/timestamp but never the
        digest."""
        first = self._acquire()
        self.assertEqual(first.returncode, 0, msg=first.stderr)
        first_token = _TOKEN_LINE_RE.search(first.stdout).group(1)
        expected_digest = _expected_digest(first_token)
        second = self._acquire()
        self.assertNotEqual(second.returncode, 0)
        combined = second.stdout + second.stderr
        self.assertNotIn(
            expected_digest,
            combined,
            msg=f"owner_digest leaked in contention diagnostic: {combined!r}",
        )
        self.assertNotIn("owner_digest", combined)

    def test_release_workspace_root_anchoring_round_trip_from_different_cwd(
        self,
    ) -> None:
        """Round-6 Copilot review regression (finding 6, CWD-independence):
        acquire and release must compute the SAME lock path for the same
        documented workspace-relative path, regardless of the caller's
        current working directory, when --workspace-root is supplied.
        Acquire from one CWD, then release from a DIFFERENT CWD using the
        same relative path anchored by --workspace-root, and confirm the
        lock created during acquire is found and removed."""
        nested_dir = self.root / "nested"
        nested_dir.mkdir()
        nested_target = nested_dir / "file.txt"
        nested_target.write_text("contained", encoding="utf-8")
        rel_path = "nested/file.txt"
        lock_file = nested_dir / ".file.txt.lock"
        if lock_file.exists():
            lock_file.unlink()

        acquire_result = subprocess.run(
            [
                _BASH,
                str(self.acquire_script),
                rel_path,
                "--workspace-root",
                str(self.root),
            ],
            cwd=self.root,
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(acquire_result.returncode, 0, msg=acquire_result.stderr)
        token_match = _TOKEN_LINE_RE.search(acquire_result.stdout)
        self.assertIsNotNone(token_match)
        token = token_match.group(1)
        self.assertTrue(lock_file.exists())

        other_cwd_tmp = tempfile.TemporaryDirectory()
        try:
            other_cwd = Path(other_cwd_tmp.name).resolve()
            self.assertNotEqual(other_cwd, self.root)
            release_result = subprocess.run(
                [
                    _BASH,
                    str(self.release_script),
                    rel_path,
                    "--workspace-root",
                    str(self.root),
                    "--token",
                    token,
                ],
                cwd=other_cwd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            self.assertEqual(
                release_result.returncode,
                0,
                msg=(
                    "release from a different CWD with the same "
                    "--workspace-root-anchored relative path must succeed: "
                    f"stdout={release_result.stdout} stderr={release_result.stderr}"
                ),
            )
            self.assertFalse(
                lock_file.exists(),
                msg="release must remove the lock created by acquire at the anchored real path",
            )
        finally:
            other_cwd_tmp.cleanup()

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

    def test_release_missing_parent_directory_is_warning_not_error(self) -> None:
        """Regression: a target whose PARENT directory (not just the target
        itself) does not exist must still be treated as "no lock file
        exists" -- a warning and exit 0 -- matching the PowerShell variant
        (GetFullPath is pure string normalisation with no filesystem access),
        not a hard failure."""
        missing_nested = self.root / "gone" / "nested.txt"
        self.assertFalse(missing_nested.parent.exists())
        result = subprocess.run(
            [_BASH, str(self.release_script), str(missing_nested)],
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

    def test_release_with_force_succeeds_without_sha_tool_available(self) -> None:
        """Regression: --force must not depend on any token-processing
        tooling. An inherited LOCK_TOKEN plus --force on a host without
        sha256sum/shasum used to enter compute_digest and exit 1 before the
        force override could remove the stale lock."""
        acquire_result = self._acquire()
        self.assertEqual(acquire_result.returncode, 0, msg=acquire_result.stderr)

        limited_bin = Path(tempfile.mkdtemp(prefix="limited_bin_"))
        try:
            real_bash = Path(_BASH).resolve()
            for name in (
                "bash", "sh", "rm", "cat", "dirname", "basename", "sed",
                "date", "printf", "tr", "head", "realpath", "awk",
            ):
                candidate = shutil.which(name)
                if candidate:
                    (limited_bin / name).symlink_to(Path(candidate).resolve())
            # Deliberately exclude sha256sum and shasum from this PATH.
            env = {"PATH": str(limited_bin), "LOCK_TOKEN": "d" * 64}
            release_result = subprocess.run(
                [str(real_bash), str(self.release_script), str(self.target), "--force"],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            self.assertEqual(
                release_result.returncode,
                0,
                msg=f"stdout={release_result.stdout} stderr={release_result.stderr}",
            )
            self.assertFalse(self.lock_file.exists())
        finally:
            shutil.rmtree(limited_bin, ignore_errors=True)

    def test_acquire_fails_closed_without_sha_tool_available(self) -> None:
        """V-e / TC3 mandatory acceptance (153.002-T): when neither
        `sha256sum` nor `shasum -a 256` is resolvable on PATH, acquire must
        exit non-zero with a named remedy, must NOT create a lock file, and
        must NOT fall back to a weaker digest or store the token in
        plaintext -- never silently downgrading the digest guarantee."""
        limited_bin = Path(tempfile.mkdtemp(prefix="limited_bin_"))
        try:
            real_bash = Path(_BASH).resolve()
            for name in (
                "bash", "sh", "rm", "cat", "dirname", "basename", "sed",
                "date", "printf", "tr", "head", "realpath", "awk", "mkdir",
                "openssl", "od",
            ):
                candidate = shutil.which(name)
                if candidate:
                    (limited_bin / name).symlink_to(Path(candidate).resolve())
            # Deliberately exclude sha256sum and shasum from this PATH.
            # openssl/od are included so the script actually reaches the
            # digest-tool check (TC1's CSPRNG step) rather than failing
            # earlier for an unrelated reason.
            env = {"PATH": str(limited_bin)}
            acquire_result = subprocess.run(
                [
                    str(real_bash),
                    str(self.acquire_script),
                    str(self.target),
                    "--workspace-root",
                    str(self.root),
                ],
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            self.assertNotEqual(
                acquire_result.returncode,
                0,
                msg=(
                    "acquire must fail closed (non-zero exit) when no SHA-256 "
                    f"utility is available; stdout={acquire_result.stdout} "
                    f"stderr={acquire_result.stderr}"
                ),
            )
            self.assertFalse(
                self.lock_file.exists(),
                msg="acquire must not create a lock file when it fails closed",
            )
            combined = acquire_result.stdout + acquire_result.stderr
            self.assertIn(
                "sha256sum",
                combined,
                msg="the fail-closed error must name the missing utility",
            )
        finally:
            shutil.rmtree(limited_bin, ignore_errors=True)

    def test_frozen_v_c_vectors_release_succeeds(self) -> None:
        """TC1-TC6 mandatory acceptance (153.002-T): the release script's own
        digest routine must agree with every frozen V-c constant, not a
        digest re-derived from this test."""
        for label, token, digest in _FROZEN_VECTORS_V_C:
            with self.subTest(vector=label):
                _write_lock_file_with_digest(self.lock_file, digest)
                result = self._release(["--token", token])
                self.assertEqual(result.returncode, 0, msg=f"{label}: {result.stderr}")
                self.assertFalse(self.lock_file.exists())

    def test_frozen_v_c2_length_boundary_vectors_rejected_before_digest(self) -> None:
        """V-c2: a wrong-length token must be rejected with a NAMED error
        before any digest is computed -- not silently hashed and compared."""
        for label, token in (_FROZEN_VECTOR_V_C2_SHORT, _FROZEN_VECTOR_V_C2_LONG):
            with self.subTest(vector=label):
                _write_lock_file_with_digest(self.lock_file, _FROZEN_VECTORS_V_C[0][2])
                result = self._release(["--token", token])
                self.assertNotEqual(result.returncode, 0, msg=f"{label} must be rejected")
                self.assertIn(
                    "TOKEN_MALFORMED",
                    result.stderr,
                    msg=f"{label} must surface a named validation error",
                )
                self.assertTrue(
                    self.lock_file.exists(),
                    msg=f"{label}: lock must remain since nothing was verified",
                )
                self.lock_file.unlink()

    def test_uppercase_token_rejected_as_malformed(self) -> None:
        """V-a's alphabet is lowercase-only; an uppercase rendering of an
        otherwise-valid-length token is a charset violation, not a digest
        mismatch, and must be rejected before hashing."""
        label, token = _FROZEN_VECTOR_UPPERCASE_MALFORMED
        _write_lock_file_with_digest(self.lock_file, _FROZEN_VECTORS_V_C[0][2])
        result = self._release(["--token", token])
        self.assertNotEqual(result.returncode, 0, msg=label)
        self.assertIn("TOKEN_MALFORMED", result.stderr)
        self.assertTrue(self.lock_file.exists())
        self.lock_file.unlink()

    def test_refusal_message_reports_lock_path_and_age_and_force_remedy(self) -> None:
        """Plan review finding 1 (P0), mandatory acceptance on 153.002-T: the
        refusal message must state the lock path, agent/pid, the computed
        age, the 1-hour staleness heuristic when exceeded, and the exact
        --force remedy -- never the token or owner_digest."""
        acquire_result = self._acquire()
        self.assertEqual(acquire_result.returncode, 0, msg=acquire_result.stderr)
        lock_content = self.lock_file.read_text(encoding="utf-8")
        stale_ts = "2020-01-01T00:00:00Z"
        new_content = re.sub(
            r"^timestamp: .*$", f"timestamp: {stale_ts}", lock_content, flags=re.MULTILINE
        )
        self.lock_file.write_text(new_content, encoding="utf-8")
        release_result = self._release(["--token", "0" * 64])
        self.assertNotEqual(release_result.returncode, 0)
        self.assertIn(str(self.lock_file), release_result.stderr)
        self.assertIn("stale", release_result.stderr.lower())
        self.assertIn("--force", release_result.stderr)


if __name__ == "__main__":
    unittest.main()
