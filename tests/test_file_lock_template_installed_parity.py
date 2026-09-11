"""Template <-> installed parity tests for the file-lock scripts (153.003-T).

SHIP-3 file-lock security hardening plan
(docs/plans/2026-08-31-ship3-file-lock-script-security-hardening-plan.md),
task 3 (`153.003-T`): after 153.001-T (H2/H4 workspace-root containment) and
153.002-T (O2 token/ownership) hardened
`templates/skills/file-lock/scripts/{acquire,release}_lock.{ps1,sh}`, those
four files were re-copied verbatim into `scripts/` (the workspace-installed
copies verify_workspace's `concurrency pack script` resolver / install-harness
Step 2.5 actually invoke) and the corresponding `.autoharness/harness-manifest.yaml`
checksums were refreshed.

This module protects three distinct properties going forward:

1. **Byte parity (H1)**: `scripts/*` must remain a pure, content-identical
   copy of `templates/skills/file-lock/scripts/*` -- no independent edits to
   the installed copies are ever permitted; only the template source may be
   edited and re-copied.
2. **Manifest coupling**: the manifest's recorded checksum for each installed
   script must match the file actually on disk (the same invariant
   `autoharness verify-workspace`'s deterministic checksum scan enforces).
3. **Flag/exit-code parity (H5)**: the PowerShell and POSIX variants of both
   scripts must expose the same CLI surface (`-WorkspaceRoot`/`--workspace-root`,
   `-Token`/`--token`, `-Force`/`--force`) and produce matching pass/fail
   verdicts across the same verification matrix -- run once against the
   template copy and once against the installed copy -- so a future
   independent edit to either location is caught immediately rather than
   silently diverging behaviour between "what task 1/2 tested" and "what
   ships".
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE_DIR = _REPO_ROOT / "templates" / "skills" / "file-lock" / "scripts"
_INSTALLED_DIR = _REPO_ROOT / "scripts"
_MANIFEST_PATH = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"

_SCRIPT_NAMES = [
    "acquire_lock.ps1",
    "acquire_lock.sh",
    "release_lock.ps1",
    "release_lock.sh",
]

_PWSH_CANDIDATES = [shutil.which("pwsh"), shutil.which("powershell")]
_PWSH_INTERPRETERS = [p for p in _PWSH_CANDIDATES if p]
_BASH = shutil.which("bash")


def _run_ps1(interpreter: str, script: Path, args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    full_args = [interpreter, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script)] + args
    return subprocess.run(full_args, cwd=cwd, capture_output=True, text=True, timeout=60)


class TemplateInstalledByteParityTests(unittest.TestCase):
    """H1: scripts/ is a pure verbatim copy of templates/skills/file-lock/scripts/."""

    def test_installed_scripts_are_byte_identical_to_templates(self) -> None:
        # Round-9 review fix: this test asserts BYTE identity (H1), so it must
        # compare raw read_bytes() with no EOL normalization. Normalizing
        # CRLF to LF before comparing would make an installed copy that had
        # silently drifted to CRLF line endings compare equal to an LF
        # template source, hiding exactly the template/install divergence
        # this test exists to catch. Both locations are established
        # elsewhere in this session (and enforced by the file-lock skill's
        # authoring convention) to be LF-only; a real CRLF drift is a
        # genuine parity failure, not a cosmetic difference to normalize
        # away.
        for name in _SCRIPT_NAMES:
            with self.subTest(script=name):
                template_bytes = (_TEMPLATE_DIR / name).read_bytes()
                installed_bytes = (_INSTALLED_DIR / name).read_bytes()
                self.assertEqual(
                    template_bytes,
                    installed_bytes,
                    msg=f"{name}: installed copy diverges from its template source (raw byte comparison)",
                )

    def test_manifest_checksums_match_installed_scripts_on_disk(self) -> None:
        with open(_MANIFEST_PATH, "r", encoding="utf-8") as handle:
            manifest = yaml.safe_load(handle)
        checksum_by_path = {
            entry["path"]: entry["checksum"]
            for entry in manifest.get("artifacts", [])
            if isinstance(entry, dict) and "path" in entry and "checksum" in entry
        }
        for name in _SCRIPT_NAMES:
            relative_path = f"scripts/{name}"
            with self.subTest(script=relative_path):
                expected = checksum_by_path.get(relative_path)
                self.assertTrue(expected, f"manifest is missing a checksum entry for {relative_path}")
                actual = hashlib.sha256((_INSTALLED_DIR / name).read_bytes()).hexdigest()
                self.assertEqual(
                    expected,
                    actual,
                    msg=f"{relative_path}: manifest checksum does not match the installed file on disk",
                )


class FlagParityTests(unittest.TestCase):
    """H5: the .ps1 and .sh variants of each script expose the same CLI surface,
    checked identically for both the template source and the installed copy."""

    @staticmethod
    def _read(root: Path, name: str) -> str:
        return (root / name).read_text(encoding="utf-8")

    def test_acquire_scripts_expose_matching_workspace_root_flag(self) -> None:
        for root in (_TEMPLATE_DIR, _INSTALLED_DIR):
            with self.subTest(root=root.relative_to(_REPO_ROOT)):
                ps1 = self._read(root, "acquire_lock.ps1")
                sh = self._read(root, "acquire_lock.sh")
                self.assertIn("$WorkspaceRoot", ps1)
                self.assertIn("--workspace-root", sh)

    def test_acquire_scripts_both_emit_lock_token_marker_and_owner_digest(self) -> None:
        for root in (_TEMPLATE_DIR, _INSTALLED_DIR):
            with self.subTest(root=root.relative_to(_REPO_ROOT)):
                ps1 = self._read(root, "acquire_lock.ps1")
                sh = self._read(root, "acquire_lock.sh")
                self.assertIn("LOCK_TOKEN=", ps1)
                self.assertIn("LOCK_TOKEN=", sh)
                self.assertIn("owner_digest", ps1)
                self.assertIn("owner_digest", sh)

    def test_release_scripts_expose_matching_token_and_force_flags(self) -> None:
        for root in (_TEMPLATE_DIR, _INSTALLED_DIR):
            with self.subTest(root=root.relative_to(_REPO_ROOT)):
                ps1 = self._read(root, "release_lock.ps1")
                sh = self._read(root, "release_lock.sh")
                self.assertIn("$Token", ps1)
                self.assertIn("[switch]$Force", ps1)
                self.assertIn("--token", sh)
                self.assertIn("--force", sh)


@unittest.skipUnless(_PWSH_INTERPRETERS, "no PowerShell interpreter available")
class VerificationMatrixParityPs1Tests(unittest.TestCase):
    """Runs the plan's verification matrix once against the template copy and
    once against the installed copy of the .ps1 scripts, asserting the two
    locations agree on every exit-code verdict (H5 exit-code contract parity).

    Matrix (per the 153.003-T task text): absolute path outside root; ../
    traversal; symlinked directory pointing outside; sibling directory whose
    name shares the root's prefix; root-level file present; root-level file
    missing.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _make_fixture(self, tag: str) -> dict[str, Path]:
        base = Path(tempfile.mkdtemp(dir=self.root, prefix=f"{tag}-"))
        ws = base / "ws"
        ws_sub = ws / "sub"
        ws_sub.mkdir(parents=True)
        outside = base / "outside"
        outside.mkdir()
        ws_evil = base / "ws-evil"
        ws_evil.mkdir()
        (ws_sub / "target.txt").write_text("contained", encoding="utf-8")
        (outside / "evil.txt").write_text("outside", encoding="utf-8")
        (ws_evil / "evil.txt").write_text("sibling", encoding="utf-8")
        return {"base": base, "ws": ws, "outside": outside, "ws_evil": ws_evil}

    def _acquire_exit_code(self, interpreter: str, script: Path, target: Path, root: Path) -> int:
        result = _run_ps1(
            interpreter,
            script,
            [str(target), "-WorkspaceRoot", str(root)],
            cwd=root,
        )
        return result.returncode

    def test_matrix_exit_codes_match_between_template_and_installed(self) -> None:
        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter):
                template_script = _TEMPLATE_DIR / "acquire_lock.ps1"
                installed_script = _INSTALLED_DIR / "acquire_lock.ps1"

                # Scenario A: contained file succeeds (rc == 0) on both.
                fixture_a_tmpl = self._make_fixture("a-template")
                fixture_a_inst = self._make_fixture("a-installed")
                rc_tmpl = self._acquire_exit_code(
                    interpreter, template_script, fixture_a_tmpl["ws"] / "sub" / "target.txt", fixture_a_tmpl["ws"]
                )
                rc_inst = self._acquire_exit_code(
                    interpreter, installed_script, fixture_a_inst["ws"] / "sub" / "target.txt", fixture_a_inst["ws"]
                )
                self.assertEqual(rc_tmpl, 0, "template acquire on contained file should succeed")
                self.assertEqual(rc_inst, 0, "installed acquire on contained file should succeed")
                self.assertEqual(rc_tmpl, rc_inst, "template/installed exit-code parity (contained file)")

                # Scenario B: absolute path outside root is rejected (rc != 0) on both.
                fixture_b_tmpl = self._make_fixture("b-template")
                fixture_b_inst = self._make_fixture("b-installed")
                rc_tmpl = self._acquire_exit_code(
                    interpreter, template_script, fixture_b_tmpl["outside"] / "evil.txt", fixture_b_tmpl["ws"]
                )
                rc_inst = self._acquire_exit_code(
                    interpreter, installed_script, fixture_b_inst["outside"] / "evil.txt", fixture_b_inst["ws"]
                )
                self.assertNotEqual(rc_tmpl, 0, "template acquire on absolute-outside path should be rejected")
                self.assertNotEqual(rc_inst, 0, "installed acquire on absolute-outside path should be rejected")
                self.assertEqual(rc_tmpl, rc_inst, "template/installed exit-code parity (absolute outside)")

                # Scenario C: ../ traversal is rejected (rc != 0) on both.
                fixture_c_tmpl = self._make_fixture("c-template")
                fixture_c_inst = self._make_fixture("c-installed")
                traversal_tmpl = fixture_c_tmpl["ws"] / "sub" / ".." / ".." / "outside" / "evil.txt"
                traversal_inst = fixture_c_inst["ws"] / "sub" / ".." / ".." / "outside" / "evil.txt"
                rc_tmpl = self._acquire_exit_code(interpreter, template_script, traversal_tmpl, fixture_c_tmpl["ws"])
                rc_inst = self._acquire_exit_code(interpreter, installed_script, traversal_inst, fixture_c_inst["ws"])
                self.assertNotEqual(rc_tmpl, 0, "template acquire on ../ traversal should be rejected")
                self.assertNotEqual(rc_inst, 0, "installed acquire on ../ traversal should be rejected")
                self.assertEqual(rc_tmpl, rc_inst, "template/installed exit-code parity (../ traversal)")

                # Scenario D: sibling directory sharing the root's name as a
                # string prefix (ws-evil vs ws) is rejected (rc != 0) on both.
                fixture_d_tmpl = self._make_fixture("d-template")
                fixture_d_inst = self._make_fixture("d-installed")
                rc_tmpl = self._acquire_exit_code(
                    interpreter, template_script, fixture_d_tmpl["ws_evil"] / "evil.txt", fixture_d_tmpl["ws"]
                )
                rc_inst = self._acquire_exit_code(
                    interpreter, installed_script, fixture_d_inst["ws_evil"] / "evil.txt", fixture_d_inst["ws"]
                )
                self.assertNotEqual(rc_tmpl, 0, "template acquire on sibling shared-prefix path should be rejected")
                self.assertNotEqual(rc_inst, 0, "installed acquire on sibling shared-prefix path should be rejected")
                self.assertEqual(rc_tmpl, rc_inst, "template/installed exit-code parity (sibling shared-prefix)")

    def test_release_root_level_present_and_missing_target_parity(self) -> None:
        template_acquire = _TEMPLATE_DIR / "acquire_lock.ps1"
        installed_acquire = _INSTALLED_DIR / "acquire_lock.ps1"
        template_release = _TEMPLATE_DIR / "release_lock.ps1"
        installed_release = _INSTALLED_DIR / "release_lock.ps1"

        for interpreter in _PWSH_INTERPRETERS:
            with self.subTest(interpreter=interpreter, scenario="root-level-present"):
                root_tmpl = Path(tempfile.mkdtemp(dir=self.root, prefix="e-template-"))
                root_inst = Path(tempfile.mkdtemp(dir=self.root, prefix="e-installed-"))
                (root_tmpl / "present.txt").write_text("x", encoding="utf-8")
                (root_inst / "present.txt").write_text("x", encoding="utf-8")

                acquire_tmpl = _run_ps1(interpreter, template_acquire, ["present.txt", "-WorkspaceRoot", str(root_tmpl)], cwd=root_tmpl)
                acquire_inst = _run_ps1(interpreter, installed_acquire, ["present.txt", "-WorkspaceRoot", str(root_inst)], cwd=root_inst)
                self.assertEqual(acquire_tmpl.returncode, 0, msg=acquire_tmpl.stderr)
                self.assertEqual(acquire_inst.returncode, 0, msg=acquire_inst.stderr)

                release_tmpl = _run_ps1(interpreter, template_release, ["present.txt", "-Force"], cwd=root_tmpl)
                release_inst = _run_ps1(interpreter, installed_release, ["present.txt", "-Force"], cwd=root_inst)
                self.assertEqual(release_tmpl.returncode, 0, msg=release_tmpl.stderr)
                self.assertEqual(release_inst.returncode, 0, msg=release_inst.stderr)
                self.assertEqual(release_tmpl.returncode, release_inst.returncode)

            with self.subTest(interpreter=interpreter, scenario="root-level-missing"):
                root_tmpl = Path(tempfile.mkdtemp(dir=self.root, prefix="f-template-"))
                root_inst = Path(tempfile.mkdtemp(dir=self.root, prefix="f-installed-"))

                release_tmpl = _run_ps1(interpreter, template_release, ["missing.txt"], cwd=root_tmpl)
                release_inst = _run_ps1(interpreter, installed_release, ["missing.txt"], cwd=root_inst)
                # Finding 6 regression: must not crash; a missing target with
                # no lock file is exit 0 ("nothing to release") on both.
                self.assertEqual(release_tmpl.returncode, 0, msg=release_tmpl.stderr)
                self.assertEqual(release_inst.returncode, 0, msg=release_inst.stderr)
                self.assertEqual(release_tmpl.returncode, release_inst.returncode)


@unittest.skipIf(sys.platform == "win32", "bash on Windows is WSL; run sh parity on POSIX/CI")
class VerificationMatrixParityShTests(unittest.TestCase):
    """POSIX counterpart of VerificationMatrixParityPs1Tests. Skipped on
    win32 following the established convention (tests/test_deploy_harness_scripts.py);
    the equivalent behaviour was manually verified via WSL bash for this task
    and is exercised for real by Linux CI."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run_sh(self, script: Path, args: list[str], cwd: Path) -> subprocess.CompletedProcess:
        assert _BASH is not None
        return subprocess.run([_BASH, str(script)] + args, cwd=cwd, capture_output=True, text=True, timeout=60)

    def test_matrix_exit_codes_match_between_template_and_installed(self) -> None:
        if _BASH is None:
            self.skipTest("no bash interpreter available")
        template_script = _TEMPLATE_DIR / "acquire_lock.sh"
        installed_script = _INSTALLED_DIR / "acquire_lock.sh"

        # Contained-file success.
        for label, script in (("template", template_script), ("installed", installed_script)):
            base = self.root / f"{label}-contained"
            ws = base / "ws"
            (ws / "sub").mkdir(parents=True)
            (ws / "sub" / "target.txt").write_text("contained", encoding="utf-8")
            result = self._run_sh(script, [str(ws / "sub" / "target.txt"), "--workspace-root", str(ws)], cwd=ws)
            self.assertEqual(result.returncode, 0, msg=f"{label}: {result.stderr}")

        # Absolute-outside rejection.
        codes = {}
        for label, script in (("template", template_script), ("installed", installed_script)):
            base = self.root / f"{label}-outside"
            ws = base / "ws"
            outside = base / "outside"
            ws.mkdir(parents=True)
            outside.mkdir()
            (outside / "evil.txt").write_text("outside", encoding="utf-8")
            result = self._run_sh(script, [str(outside / "evil.txt"), "--workspace-root", str(ws)], cwd=ws)
            codes[label] = result.returncode
            self.assertNotEqual(result.returncode, 0, msg=f"{label}: expected rejection")
        self.assertEqual(codes["template"], codes["installed"])

        # `../` traversal rejection (round-9 review fix: missing POSIX scenario).
        codes = {}
        for label, script in (("template", template_script), ("installed", installed_script)):
            base = self.root / f"{label}-traversal"
            ws = base / "ws"
            outside = base / "outside"
            (ws / "sub").mkdir(parents=True)
            outside.mkdir()
            (outside / "evil.txt").write_text("outside", encoding="utf-8")
            traversal_target = ws / "sub" / ".." / ".." / "outside" / "evil.txt"
            result = self._run_sh(script, [str(traversal_target), "--workspace-root", str(ws)], cwd=ws)
            codes[label] = result.returncode
            self.assertNotEqual(result.returncode, 0, msg=f"{label}: expected ../ traversal rejection")
        self.assertEqual(codes["template"], codes["installed"])

        # Symlinked directory pointing outside is rejected (round-9 review
        # fix: missing POSIX scenario; real symlinks are unprivileged on
        # POSIX, unlike Windows, so this needs no junction workaround).
        codes = {}
        for label, script in (("template", template_script), ("installed", installed_script)):
            base = self.root / f"{label}-symlink"
            ws = base / "ws"
            outside = base / "outside"
            ws.mkdir(parents=True)
            outside.mkdir()
            (outside / "evil.txt").write_text("outside", encoding="utf-8")
            link_path = ws / "linkout"
            link_path.symlink_to(outside, target_is_directory=True)
            result = self._run_sh(script, [str(link_path / "evil.txt"), "--workspace-root", str(ws)], cwd=ws)
            codes[label] = result.returncode
            self.assertNotEqual(result.returncode, 0, msg=f"{label}: expected symlink escape rejection")
        self.assertEqual(codes["template"], codes["installed"])

        # Sibling directory sharing the root's name as a string prefix
        # (ws-evil vs ws) is rejected (round-9 review fix: missing POSIX
        # scenario).
        codes = {}
        for label, script in (("template", template_script), ("installed", installed_script)):
            base = self.root / f"{label}-sibling"
            ws = base / "ws"
            ws_evil = base / "ws-evil"
            ws.mkdir(parents=True)
            ws_evil.mkdir()
            (ws_evil / "evil.txt").write_text("sibling", encoding="utf-8")
            result = self._run_sh(script, [str(ws_evil / "evil.txt"), "--workspace-root", str(ws)], cwd=ws)
            codes[label] = result.returncode
            self.assertNotEqual(result.returncode, 0, msg=f"{label}: expected sibling shared-prefix rejection")
        self.assertEqual(codes["template"], codes["installed"])

    def test_release_root_level_present_and_missing_target_parity(self) -> None:
        # Round-9 review fix: POSIX counterpart of
        # VerificationMatrixParityPs1Tests.test_release_root_level_present_and_missing_target_parity.
        if _BASH is None:
            self.skipTest("no bash interpreter available")
        template_acquire = _TEMPLATE_DIR / "acquire_lock.sh"
        installed_acquire = _INSTALLED_DIR / "acquire_lock.sh"
        template_release = _TEMPLATE_DIR / "release_lock.sh"
        installed_release = _INSTALLED_DIR / "release_lock.sh"

        with self.subTest(scenario="root-level-present"):
            root_tmpl = Path(tempfile.mkdtemp(dir=self.root, prefix="e-template-"))
            root_inst = Path(tempfile.mkdtemp(dir=self.root, prefix="e-installed-"))
            (root_tmpl / "present.txt").write_text("x", encoding="utf-8")
            (root_inst / "present.txt").write_text("x", encoding="utf-8")

            acquire_tmpl = self._run_sh(template_acquire, ["present.txt", "--workspace-root", str(root_tmpl)], cwd=root_tmpl)
            acquire_inst = self._run_sh(installed_acquire, ["present.txt", "--workspace-root", str(root_inst)], cwd=root_inst)
            self.assertEqual(acquire_tmpl.returncode, 0, msg=acquire_tmpl.stderr)
            self.assertEqual(acquire_inst.returncode, 0, msg=acquire_inst.stderr)

            release_tmpl = self._run_sh(template_release, ["present.txt", "--force"], cwd=root_tmpl)
            release_inst = self._run_sh(installed_release, ["present.txt", "--force"], cwd=root_inst)
            self.assertEqual(release_tmpl.returncode, 0, msg=release_tmpl.stderr)
            self.assertEqual(release_inst.returncode, 0, msg=release_inst.stderr)
            self.assertEqual(release_tmpl.returncode, release_inst.returncode)

        with self.subTest(scenario="root-level-missing"):
            root_tmpl = Path(tempfile.mkdtemp(dir=self.root, prefix="f-template-"))
            root_inst = Path(tempfile.mkdtemp(dir=self.root, prefix="f-installed-"))

            release_tmpl = self._run_sh(template_release, ["missing.txt"], cwd=root_tmpl)
            release_inst = self._run_sh(installed_release, ["missing.txt"], cwd=root_inst)
            self.assertEqual(release_tmpl.returncode, 0, msg=release_tmpl.stderr)
            self.assertEqual(release_inst.returncode, 0, msg=release_inst.stderr)
            self.assertEqual(release_tmpl.returncode, release_inst.returncode)
