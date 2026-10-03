"""CLI engine-semantics probe tests (192.012-T, plan unit A2a).

Four table-driven scenarios (plan ``### A2a``), all through the A3a
``ResolvedBinary`` test seam (no real backlogit binary is spawned):

1. a verified probe, the exact fixed argv, excerpt redaction, and commit
   sanitization (re-plan cycle-1 R6, R18);
2. unverified versions and version sanitization (``redact(v)[0] == v``;
   Copilot PR #481 T5);
3. probe failures never raise and always yield ``UNVERIFIED`` (R18);
4. working-directory isolation and workspace containment (re-plan cycle-1
   R3; Copilot PR #481 T4; constitution IV and VII).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from autoharness.gates.cascade_evidence import redact
from autoharness.gates.shipment_closure import EngineSemanticsVerdict
from autoharness.shipment_close import engine_probe
from autoharness.shipment_close.engine_probe import (
    PROBE_ARGS,
    PROBE_ROOT,
    EngineProbe,
    probe_engine_semantics,
)
from autoharness.shipment_close.persist import PersistError
from autoharness.shipment_close.runner import ResolvedBinary, resolve_backlogit_binary, run_bounded

_PREFIX = "ENGINE_SEMANTICS_UNVERIFIED:"


def _make_dir_link(link: Path, target: Path) -> str | None:
    try:
        os.symlink(target, link, target_is_directory=True)
        return None
    except (OSError, NotImplementedError) as exc:
        symlink_error = exc
    if os.name == "nt":
        try:
            import _winapi

            _winapi.CreateJunction(str(target), str(link))
            return None
        except (OSError, ImportError, AttributeError) as exc:  # pragma: no cover - platform
            return f"cannot create symlink ({symlink_error}) or junction ({exc})"
    return f"cannot create directory symlink: {symlink_error}"


class _Fixture:
    def __init__(self, test: unittest.TestCase) -> None:
        tmp = tempfile.TemporaryDirectory()
        test.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.root = self.base / "ws"
        self.fakes = self.base / "fakes"
        self.outside = self.base / "outside"
        for path in (self.root, self.fakes, self.outside):
            path.mkdir()

    def emitter(self, name: str, *, stdout: str = "", exit_code: int = 0, sleep: float = 0) -> ResolvedBinary:
        script = self.fakes / name
        script.write_text(
            "import sys, time\n"
            f"time.sleep({sleep!r})\n"
            f"sys.stdout.write({stdout!r})\n"
            "sys.stdout.flush()\n"
            f"sys.exit({exit_code})\n",
            encoding="utf-8",
        )
        return ResolvedBinary(
            binary_path=sys.executable,
            binary_sha256="0" * 64,
            argv_prefix=(sys.executable, str(script)),
        )

    def probe_dirs(self) -> list[Path]:
        root = self.root / PROBE_ROOT
        return sorted(root.iterdir()) if root.is_dir() else []


def _payload(version: object = "1.11.0", commit: object = "131577c", **extra: object) -> str:
    return json.dumps({"version": version, "commit": commit, **extra}) + "\n"


class VerifiedProbeTests(unittest.TestCase):
    """Scenario 1: a released 1.11.x probe on cli/cli is VERIFIED; commits are sanitized."""

    def test_verified_probe_table(self) -> None:
        with self.subTest("verified, exact argv, redacted excerpt"):
            fixture = _Fixture(self)
            resolved = fixture.emitter("ok.py", stdout=_payload(note="token=abc123"))
            spy = mock.Mock(wraps=run_bounded)
            with mock.patch.object(engine_probe, "run_bounded", spy):
                probe = probe_engine_semantics(resolved, workspace=fixture.root)
            self.assertIsInstance(probe, EngineProbe)
            self.assertEqual(probe.decision.verdict, EngineSemanticsVerdict.VERIFIED)
            self.assertEqual(probe.decision.minor_line, (1, 11))
            self.assertEqual(probe.decision.probed_version, "1.11.0")
            self.assertEqual(probe.decision.probed_commit, "131577c")
            self.assertEqual(probe.decision.probe_surface, "cli")
            self.assertEqual(probe.invocation_surface, "cli")
            spy.assert_called_once()
            argv = spy.call_args.args[0]
            self.assertEqual(list(argv), [*resolved.argv_prefix, "version", "--no-update-check", "--format", "json"])
            self.assertEqual(PROBE_ARGS, ("version", "--no-update-check", "--format", "json"))
            self.assertEqual(spy.call_args.kwargs["timeout"], 30)
            cwd = Path(spy.call_args.kwargs["cwd"])
            self.assertEqual(cwd.parent, fixture.root / PROBE_ROOT)
            self.assertTrue(cwd.name.startswith("probe-"))
            self.assertNotIn("abc123", probe.version_excerpt)
            self.assertIn("token=[REDACTED]", probe.version_excerpt)

        for label, commit in (
            ("non-hex commit", "xyz"),
            ("credential-looking commit", "token=abc"),
            ("integer commit", 131577),
            ("list commit", ["131577c"]),
            ("65-character hex commit", "a" * 65),
            ("uppercase hex commit", "131577C"),
            ("short hex commit", "abc12"),
        ):
            with self.subTest(label):
                fixture = _Fixture(self)
                probe = probe_engine_semantics(
                    fixture.emitter("c.py", stdout=_payload(commit=commit)), workspace=fixture.root
                )
                self.assertIsNone(probe.decision.probed_commit)
                self.assertEqual(probe.decision.verdict, EngineSemanticsVerdict.VERIFIED)

        with self.subTest("a 64-character hex commit is kept"):
            fixture = _Fixture(self)
            probe = probe_engine_semantics(
                fixture.emitter("c64.py", stdout=_payload(commit="b" * 64)), workspace=fixture.root
            )
            self.assertEqual(probe.decision.probed_commit, "b" * 64)


class UnverifiedVersionTests(unittest.TestCase):
    """Scenario 2: unverified versions; unsafe version strings are passed as null."""

    def test_unverified_version_table(self) -> None:
        rows = [
            ("unverified minor line", "1.10.1", "1.10.1"),
            ("pre-release build", "1.11.1-rc1", "1.11.1-rc1"),
            ("65-character version", "1.11.0+" + "a" * 58, None),
            ("version carrying a credential", "1.11.0 token=abc", None),
            ("version with a trailing newline", "1.11.0\n", None),
            ("non-string version", 1.11, None),
        ]
        for label, version, expected in rows:
            with self.subTest(label):
                if type(version) is str and label.startswith("65"):
                    self.assertEqual(len(version), 65)
                fixture = _Fixture(self)
                probe = probe_engine_semantics(
                    fixture.emitter("v.py", stdout=_payload(version=version)), workspace=fixture.root
                )
                self.assertEqual(probe.decision.verdict, EngineSemanticsVerdict.UNVERIFIED)
                self.assertTrue(probe.decision.reason.startswith(_PREFIX), probe.decision.reason)
                self.assertEqual(probe.decision.probed_version, expected)
                self.assertEqual(redact(probe.decision.reason)[0], probe.decision.reason)


class ProbeFailureTests(unittest.TestCase):
    """Scenario 3: every probe failure is UNVERIFIED with a null version, and nothing raises."""

    def test_probe_failure_table(self) -> None:
        def raising(*args, **kwargs):
            raise RuntimeError("unexpected")

        def persist_raising(*args, **kwargs):
            raise PersistError(2, "cannot spawn")

        rows = [
            ("non-zero exit", lambda f: f.emitter("e.py", stdout=_payload(), exit_code=1), None),
            ("timeout", lambda f: f.emitter("s.py", stdout=_payload(), sleep=30), None),
            ("non-JSON stdout", lambda f: f.emitter("n.py", stdout="backlogit 1.11.0\n"), None),
            ("empty stdout", lambda f: f.emitter("z.py", stdout=""), None),
            ("JSON that is not an object", lambda f: f.emitter("l.py", stdout='["1.11.0"]\n'), None),
            ("run_bounded raises unexpectedly", lambda f: f.emitter("r.py", stdout=_payload()), raising),
            ("run_bounded refuses the spawn", lambda f: f.emitter("p.py", stdout=_payload()), persist_raising),
        ]
        for label, build, replacement in rows:
            with self.subTest(label):
                fixture = _Fixture(self)
                resolved = build(fixture)
                patches = [mock.patch.object(engine_probe, "PROBE_TIMEOUT_SECONDS", 1)]
                if replacement is not None:
                    patches.append(mock.patch.object(engine_probe, "run_bounded", side_effect=replacement))
                with patches[0]:
                    if len(patches) > 1:
                        with patches[1]:
                            probe = probe_engine_semantics(resolved, workspace=fixture.root)
                    else:
                        probe = probe_engine_semantics(resolved, workspace=fixture.root)
                self.assertIsNone(probe.decision.probed_version)
                self.assertEqual(probe.decision.verdict, EngineSemanticsVerdict.UNVERIFIED)
                self.assertTrue(probe.decision.reason.startswith(_PREFIX), probe.decision.reason)
                self.assertEqual(probe.invocation_surface, "cli")


class WorkingDirectoryIsolationTests(unittest.TestCase):
    """Scenario 4: the probe runs in a fresh, contained, never-deleted probe directory."""

    def test_planted_version_script_never_runs(self) -> None:
        fixture = _Fixture(self)
        sentinel = fixture.root / "SENTINEL"
        (fixture.root / "version").write_text(
            f"open({str(sentinel)!r}, 'w').write('ran')\n"
            "print('{\"version\": \"1.11.0\", \"commit\": \"131577c\"}')\n",
            encoding="utf-8",
        )
        (fixture.root / ".autoharness").mkdir()
        (fixture.root / ".autoharness" / "backlog-registry.yaml").write_text(
            'cli:\n  binary: "python"\n', encoding="utf-8"
        )
        try:
            resolved = resolve_backlogit_binary(fixture.root, which=lambda name: sys.executable)
        except PersistError:
            # e.g. a POSIX venv interpreter that is a symlink or named python3:
            # inject the same bare-name interpreter through the seam instead.
            resolved = ResolvedBinary(
                binary_path=sys.executable,
                binary_sha256=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
                argv_prefix=(sys.executable,),
            )
        before = set(fixture.base.iterdir())
        probe = probe_engine_semantics(resolved, workspace=fixture.root)
        self.assertFalse(sentinel.exists(), "the planted workspace-root script executed")
        self.assertEqual(probe.decision.verdict, EngineSemanticsVerdict.UNVERIFIED)
        self.assertIsNone(probe.decision.probed_version)
        probe_dirs = fixture.probe_dirs()
        self.assertEqual(len(probe_dirs), 1)
        self.assertTrue(probe_dirs[0].is_dir(), "the probe directory was deleted")
        self.assertTrue(probe_dirs[0].name.startswith("probe-"))
        self.assertEqual(set(fixture.base.iterdir()), before, "something was created outside the workspace")
        self.assertEqual(list(fixture.outside.iterdir()), [])

        # A second probe gets its own fresh directory; the first is still never deleted.
        probe_engine_semantics(resolved, workspace=fixture.root)
        self.assertEqual(len(fixture.probe_dirs()), 2)

    def test_linked_probe_component_spawns_nothing(self) -> None:
        for linked in (PROBE_ROOT, PROBE_ROOT.parent):
            with self.subTest(linked=linked.as_posix()):
                fixture = _Fixture(self)
                link = fixture.root / linked
                link.parent.mkdir(parents=True, exist_ok=True)
                skip = _make_dir_link(link, fixture.outside)
                if skip:
                    self.skipTest(skip)
                spawn = mock.Mock(side_effect=AssertionError("spawned"))
                with mock.patch.object(engine_probe, "run_bounded", spawn):
                    probe = probe_engine_semantics(
                        fixture.emitter("x.py", stdout=_payload()), workspace=fixture.root
                    )
                spawn.assert_not_called()
                self.assertEqual(probe.decision.verdict, EngineSemanticsVerdict.UNVERIFIED)
                self.assertIsNone(probe.decision.probed_version)
                self.assertEqual(list(fixture.outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
