"""P7 UTC contract for recorded dates and times.

Contract: every recorded date and time uses UTC. Times are written with a ``Z``
suffix, and ISO-8601 date-time literals carrying a numeric offset (for example
``-07:00``) are forbidden in templates and installed mirrors. Each of the four
P7 targets (the output-timestamp instruction, the two foundation documents, and
the compact-context skill) must carry the UTC rule in both its template and its
installed mirror.

Scope: the offset scan covers every file under ``templates/`` plus every
installed artifact recorded in ``.autoharness/harness-manifest.yaml`` that has a
``template:`` key, excluding anything under ``.autoharness/``. Files under
``.autoharness/`` are operator-owned generated state and are excluded from the
scan; plan decision D4 in
``docs/plans/2026-10-08-backlogit-carryover-first-cut-plan.md`` keeps a
consumer-side generated-artifact lint out of scope for this cut. Template-tree
files must be UTF-8 text with no NUL bytes, and any symlink, junction, or
non-regular file under ``templates/`` fails the scan.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from collections.abc import Iterable
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST_RELPATH = ".autoharness/harness-manifest.yaml"
_OPERATOR_STATE_PREFIX = ".autoharness/"
_OFFSET_LITERAL = re.compile(r"T\d{2}:\d{2}(:\d{2})?(\.\d+)?[+-]\d{2}:?\d{2}")
_WINDOWS_DRIVE_PREFIX = re.compile(r"^[A-Za-z]:")

# Exact substrings each template and installed mirror must contain verbatim.
_MEMORY_UTC_ANCHOR = (
    "use the UTC date, and all recorded dates and times are UTC (`Z`); "
    "see `.github/instructions/output-timestamps.instructions.md`."
)

# (name, template relpath, installed mirror relpath, exact anchors)
_P7_TARGETS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "output-timestamps",
        "templates/instructions/output-timestamps.instructions.md.tmpl",
        ".github/instructions/output-timestamps.instructions.md",
        (
            "\n## UTC for Recorded Dates and Times\n",
            "Local-offset values (for example `-07:00`) are forbidden in recorded output.",
            "`[DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss', [Globalization.CultureInfo]::InvariantCulture) + 'Z'`",
            "`date -u +%Y-%m-%dT%H:%M:%SZ`",
            "`datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')`",
        ),
    ),
    (
        "copilot-instructions",
        "templates/foundation/copilot-instructions.md.tmpl",
        ".github/copilot-instructions.md",
        (_MEMORY_UTC_ANCHOR,),
    ),
    (
        "AGENTS",
        "templates/foundation/AGENTS.md.tmpl",
        "AGENTS.md",
        (_MEMORY_UTC_ANCHOR,),
    ),
    (
        "compact-context",
        "templates/skills/compact-context/SKILL.md.tmpl",
        ".github/skills/compact-context/SKILL.md",
        (
            "in every compacted, decided-plan, and closure-summary filename below is the UTC date; "
            "see `.github/instructions/output-timestamps.instructions.md` for the full rule.",
        ),
    ),
)


def _missing_anchors(text: str, anchors: Iterable[str]) -> list[str]:
    """Return the anchors that do not occur verbatim in ``text`` (CRLF normalized to LF)."""
    anchors = tuple(anchors)
    if not anchors:
        raise ValueError("anchor list is empty; nothing would be verified")
    if any(not anchor for anchor in anchors):
        raise ValueError("empty anchor would match vacuously")
    # Newline wrapping lets a leading-newline heading anchor match at the first or last line.
    normalized = "\n" + text.replace("\r\n", "\n") + "\n"
    return [anchor for anchor in anchors if anchor not in normalized]


def _is_parent_component(component: str) -> bool:
    """Return True for ``..`` and variants Windows resolves to it (extra trailing dots or spaces)."""
    return bool(component) and set(component) <= {".", " "} and component.count(".") >= 2


def _normalize_manifest_path(path: str) -> str:
    """Return ``path`` with backslashes as slashes and leading ``./`` segments removed."""
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _check_manifest_path(index: int, path: object) -> None:
    """Reject manifest ``path`` values that are not safe relative POSIX-style paths."""
    if not isinstance(path, str) or not path:
        raise AssertionError(
            f"{_MANIFEST_RELPATH} artifacts[{index}] 'path' must be a non-empty string "
            f"(got {path!r})"
        )
    if (
        Path(path).is_absolute()
        or _WINDOWS_DRIVE_PREFIX.match(path)
        or path.startswith(("/", "\\"))
        or any(_is_parent_component(part) for part in re.split(r"[/\\]", path))
    ):
        raise AssertionError(
            f"{_MANIFEST_RELPATH} artifacts[{index}] 'path' must be a relative path without "
            f"'..' components (got {path!r})"
        )


def _manifest_mirror_set(root: Path) -> set[str]:
    """Return the installed-mirror paths the manifest records with a ``template:`` key,
    excluding operator-owned ``.autoharness/`` state. Malformed manifests fail the test."""
    manifest_path = root / _MANIFEST_RELPATH
    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise AssertionError(f"{_MANIFEST_RELPATH} is not valid UTF-8: {exc}") from exc
    try:
        manifest = yaml.safe_load(manifest_text)
    except yaml.YAMLError as exc:
        raise AssertionError(f"{_MANIFEST_RELPATH} is not valid YAML: {exc}") from exc
    if not isinstance(manifest, dict):
        raise AssertionError(
            f"{_MANIFEST_RELPATH} must load to a mapping, got {type(manifest).__name__}"
        )
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        raise AssertionError(
            f"{_MANIFEST_RELPATH} must contain a list under 'artifacts', "
            f"got {type(artifacts).__name__}"
        )
    mirrors: set[str] = set()
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            raise AssertionError(
                f"{_MANIFEST_RELPATH} artifacts[{index}] must be a mapping, "
                f"got {type(artifact).__name__}"
            )
        if "template" not in artifact:
            continue
        path = artifact.get("path")
        _check_manifest_path(index, path)
        normalized = _normalize_manifest_path(path)
        if not normalized.startswith(_OPERATOR_STATE_PREFIX):
            mirrors.add(normalized)
    return mirrors


def _is_junction(path: Path) -> bool:
    return hasattr(path, "is_junction") and path.is_junction()


def _template_files(root: Path) -> set[str]:
    """Return POSIX relpaths of every regular file under ``templates/``; fail closed on
    any symlink or junction (checked before descending into a directory), non-regular
    file, file that contains a NUL byte, or non-UTF-8 file. ``.pyc`` bytecode under
    ``__pycache__`` is skipped; every other file there is validated."""
    templates_dir = root / "templates"
    if templates_dir.is_symlink() or _is_junction(templates_dir):
        raise AssertionError("templates/ must not be a symlink or junction")
    if not templates_dir.is_dir():
        raise AssertionError(f"templates/ must be a directory under {root}")
    relpaths: set[str] = set()
    pending = [templates_dir]
    while pending:
        for path in sorted(pending.pop().iterdir()):
            relpath = path.relative_to(root)
            if path.is_symlink():
                raise AssertionError(
                    f"{relpath.as_posix()}: symlink not allowed under templates/"
                )
            if _is_junction(path):
                raise AssertionError(
                    f"{relpath.as_posix()}: junction not allowed under templates/"
                )
            if path.is_dir():
                pending.append(path)
                continue
            if not path.is_file():
                raise AssertionError(
                    f"{relpath.as_posix()}: non-regular file not allowed under templates/"
                )
            if path.suffix == ".pyc" and "__pycache__" in relpath.parts:
                # __pycache__ holds generated bytecode, never template content.
                continue
            data = path.read_bytes()
            if b"\x00" in data:
                raise AssertionError(
                    f"{relpath.as_posix()} contains NUL bytes; templates must be UTF-8 text"
                )
            try:
                data.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise AssertionError(f"{relpath.as_posix()} is not valid UTF-8: {exc}") from exc
            relpaths.add(relpath.as_posix())
    return relpaths


def scan_targets(root: Path) -> list[str]:
    """Return sorted POSIX relpaths of every file under ``templates/`` plus the
    manifest-recorded installed mirrors outside ``.autoharness/``."""
    return sorted(_template_files(root) | _manifest_mirror_set(root))


def scan_offset_literals(root: Path, relpaths: Iterable[str]) -> list[tuple[str, int, str]]:
    """Return ``(relpath, line_number, matched_text)`` for every offset-bearing literal."""
    findings: list[tuple[str, int, str]] = []
    for relpath in relpaths:
        # read_text applies universal newline translation, so split("\n") yields editor line numbers.
        try:
            text = (root / relpath).read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise AssertionError(f"{relpath} is not valid UTF-8: {exc}") from exc
        for line_number, line in enumerate(text.split("\n"), start=1):
            findings.extend(
                (relpath, line_number, match.group(0)) for match in _OFFSET_LITERAL.finditer(line)
            )
    return findings


def _create_link(kind: str, root: Path, link_relpath: str, target_relpath: str) -> None:
    """Create a file symlink, directory symlink, or Windows junction; raises OSError if refused."""
    link = root / link_relpath
    target = root / target_relpath
    if kind == "junction":
        completed = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stdout + completed.stderr).decode(errors="replace").strip()
            raise OSError(f"mklink /J failed: {detail}")
    else:
        os.symlink(target, link, target_is_directory=kind == "dir_symlink")


class P7UtcContractTest(unittest.TestCase):
    def test_scanner_reports_file_line_for_planted_offset(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "fixture.md").write_text(
                "# Fixture\n"
                "Recorded 2026-07-02T18:49:41Z in UTC.\n"
                "Local 2026-07-02T18:49:41-07:00 must be reported.\n"
                "Offset 2026-07-02T18:49:41+00:00 must be reported.\n"
                "Millis 2026-07-02T18:49:41.123+0000 must be reported.\n"
                "Date only 2026-07-02 is not a date-time literal.\n",
                encoding="utf-8",
            )
            report = scan_offset_literals(root, ["fixture.md"])

        self.assertEqual(
            report,
            [
                ("fixture.md", 3, "T18:49:41-07:00"),
                ("fixture.md", 4, "T18:49:41+00:00"),
                ("fixture.md", 5, "T18:49:41.123+0000"),
            ],
        )

    def test_templates_and_installed_mirrors_carry_no_offset_literals(self) -> None:
        self.assertTrue(
            (_ROOT / "templates").is_dir(),
            "templates/ must exist as a directory at the repository root",
        )
        mirrors = _manifest_mirror_set(_ROOT)
        self.assertTrue(mirrors, "manifest-derived mirror set is empty")

        targets = scan_targets(_ROOT)
        self.assertTrue(targets, "no scan targets discovered")
        for name, template, mirror, _ in _P7_TARGETS:
            with self.subTest(target=name, path=mirror):
                self.assertIn(mirror, mirrors, "P7 mirror is not recorded in the manifest")
            for relpath in (template, mirror):
                with self.subTest(target=name, path=relpath):
                    self.assertIn(relpath, targets, "P7 path is not in the scan target list")
        self.assertFalse(
            [t for t in targets if _normalize_manifest_path(t).startswith(_OPERATOR_STATE_PREFIX)],
            "operator-owned .autoharness/ state must not be a scan target",
        )

        findings = scan_offset_literals(_ROOT, targets)
        if findings:
            self.fail(
                f"{len(findings)} offset-bearing ISO-8601 literal(s) found; "
                "record times in UTC with a Z suffix:\n"
                + "\n".join(f"{rel}:{line}: {match}" for rel, line, match in findings)
            )

    def test_p7_targets_and_mirrors_carry_exact_utc_anchors(self) -> None:
        for name, template, mirror, anchors in _P7_TARGETS:
            for relpath in (template, mirror):
                with self.subTest(target=name, path=relpath):
                    text = (_ROOT / relpath).read_text(encoding="utf-8")
                    missing = _missing_anchors(text, anchors)
                    self.assertFalse(
                        missing,
                        f"{relpath} lacks exact UTC anchor(s): {missing!r}",
                    )

    def test_manifest_and_template_tree_fail_closed(self) -> None:
        cases: tuple[
            tuple[str, str | bytes, dict[str, bytes], dict[str, tuple[str, str]], str], ...
        ] = (
            (
                "no artifacts list",
                "schema_version: '1.0.0'\n",
                {},
                {},
                "must contain a list under 'artifacts'",
            ),
            ("invalid YAML", "artifacts: [unclosed\n", {}, {}, "is not valid YAML"),
            ("empty manifest", "", {}, {}, "must load to a mapping, got NoneType"),
            ("top-level list", "- a\n", {}, {}, "must load to a mapping, got list"),
            ("artifacts not a list", "artifacts: {}\n", {}, {}, "must contain a list under 'artifacts'"),
            ("manifest not UTF-8", b"\xff\xfe\n", {}, {}, "is not valid UTF-8"),
            (
                "artifact not a mapping",
                "artifacts:\n  - just-a-string\n",
                {},
                {},
                "artifacts[0] must be a mapping",
            ),
            (
                "template entry without path",
                "artifacts:\n  - path: a.md\n  - template: x.tmpl\n",
                {},
                {},
                "artifacts[1] 'path' must be a non-empty string (got None)",
            ),
            (
                "template entry with non-string path",
                "artifacts:\n  - path: 42\n    template: x.tmpl\n",
                {},
                {},
                "artifacts[0] 'path' must be a non-empty string (got 42)",
            ),
            (
                "empty path",
                "artifacts:\n  - path: ''\n    template: x.tmpl\n",
                {},
                {},
                "artifacts[0] 'path' must be a non-empty string (got '')",
            ),
            (
                "absolute path",
                "artifacts:\n  - path: /etc/passwd\n    template: x.tmpl\n",
                {},
                {},
                "must be a relative path without '..' components (got '/etc/passwd')",
            ),
            (
                "windows drive path",
                "artifacts:\n  - path: C:/Windows/win.ini\n    template: x.tmpl\n",
                {},
                {},
                "must be a relative path without '..' components (got 'C:/Windows/win.ini')",
            ),
            (
                "backslash-rooted path",
                "artifacts:\n  - path: \\Windows\\win.ini\n    template: x.tmpl\n",
                {},
                {},
                "must be a relative path without '..' components (got '\\\\Windows\\\\win.ini')",
            ),
            (
                "parent traversal",
                "artifacts:\n  - path: ../outside.md\n    template: x.tmpl\n",
                {},
                {},
                "without '..' components (got '../outside.md')",
            ),
            (
                "backslash parent traversal",
                "artifacts:\n  - path: sub\\..\\..\\outside.md\n    template: x.tmpl\n",
                {},
                {},
                "without '..' components (got 'sub\\\\..\\\\..\\\\outside.md')",
            ),
            (
                "trailing-space parent component",
                "artifacts:\n  - path: 'sub/.. /outside.md'\n    template: x.tmpl\n",
                {},
                {},
                "without '..' components (got 'sub/.. /outside.md')",
            ),
            (
                "ellipsis parent component",
                "artifacts:\n  - path: 'sub/.../outside.md'\n    template: x.tmpl\n",
                {},
                {},
                "without '..' components (got 'sub/.../outside.md')",
            ),
            (
                "NUL byte in templates/",
                "artifacts: []\n",
                {"templates/bad.md": b"ok\x00bad\n"},
                {},
                "templates/bad.md contains NUL bytes",
            ),
            (
                "NUL byte in non-bytecode __pycache__ file",
                "artifacts: []\n",
                {"templates/__pycache__/bad.txt": b"ok\x00\n"},
                {},
                "templates/__pycache__/bad.txt contains NUL bytes",
            ),
            (
                "undecodable bytes in templates/",
                "artifacts: []\n",
                {"templates/bad.md": b"\xff\xfe\n"},
                {},
                "templates/bad.md is not valid UTF-8",
            ),
            (
                "symlink under templates/",
                "artifacts: []\n",
                {"templates/real.md": b"ok\n"},
                {"templates/link.md": ("symlink", "templates/real.md")},
                "templates/link.md: symlink not allowed under templates/",
            ),
            (
                "directory symlink under templates/",
                "artifacts: []\n",
                {"templates/real/ok.md": b"ok\n"},
                {"templates/linkdir": ("dir_symlink", "templates/real")},
                "templates/linkdir: symlink not allowed under templates/",
            ),
            (
                "junction under templates/",
                "artifacts: []\n",
                {"templates/real/ok.md": b"ok\n"},
                {"templates/jct": ("junction", "templates/real")},
                "templates/jct: junction not allowed under templates/",
            ),
            (
                "templates root is a symlink",
                "artifacts: []\n",
                {"real-templates/ok.md": b"ok\n"},
                {"templates": ("dir_symlink", "real-templates")},
                "templates/ must not be a symlink or junction",
            ),
        )
        for label, manifest, files, links, needle in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / ".autoharness").mkdir()
                (root / _MANIFEST_RELPATH).write_bytes(
                    manifest if isinstance(manifest, bytes) else manifest.encode("utf-8")
                )
                if "templates" not in links:
                    (root / "templates").mkdir()
                for relpath, data in files.items():
                    (root / relpath).parent.mkdir(parents=True, exist_ok=True)
                    (root / relpath).write_bytes(data)
                for link_relpath, (kind, target_relpath) in links.items():
                    (root / link_relpath).parent.mkdir(parents=True, exist_ok=True)
                    try:
                        _create_link(kind, root, link_relpath, target_relpath)
                    except OSError as exc:
                        self.skipTest(f"{kind} creation not permitted on this host: {exc}")
                with self.assertRaises(AssertionError) as ctx:
                    scan_targets(root)
                self.assertIn(needle, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
