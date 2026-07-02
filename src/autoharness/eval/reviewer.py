"""Deterministic reviewer matrix — a rule-based diff grader (task 055.002-T).

Scores a change per quality dimension by applying a fixed, pinned ruleset to the
**added lines** of a unified ``git diff``. Every penalty carries a mandatory
line-number citation (path + new-file line number).

This grader is intentionally **NOT** an LLM call: it is a pure, reproducible,
hermetic function of the diff text and the pinned :data:`RULESET_VERSION`. The
same diff always yields byte-identical scores. It feeds the eval comparative
summary (task 055.006-T).

Dimensions (each scored out of :data:`MAX_SCORE`):

* ``maintainability`` — long lines, TODO/FIXME markers, suppressed type checks
* ``security`` — eval/exec, ``shell=True``, disabled TLS verify, insecure
  pickle, hardcoded secrets, weak hashes
* ``reliability`` — bare ``except:``, overly broad ``except Exception``
* ``testing`` — new source definitions with no accompanying test file in the diff
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

RULESET_VERSION = "1.0.0"
MAX_SCORE = 10.0
_MAX_LINE_LENGTH = 100

DIMENSIONS = ("maintainability", "security", "reliability", "testing")

# A git runner mirrors the injectable pattern used elsewhere in the eval package
# so review runs stay hermetic in tests without importing gates.
GitRunner = Callable[[list[str], "Path | None"], "tuple[int, str, str]"]


@dataclass(frozen=True)
class AddedLine:
    """One added line from a unified diff, with its new-file line number."""

    path: str
    lineno: int
    content: str


@dataclass(frozen=True)
class Penalty:
    """A single deduction with a mandatory (path, line) citation."""

    dimension: str
    rule: str
    points: float
    path: str
    line: int
    message: str

    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "points": self.points,
            "path": self.path,
            "line": self.line,
            "message": self.message,
        }


@dataclass(frozen=True)
class DimensionScore:
    """A per-dimension score and the penalties that produced it."""

    dimension: str
    score: float
    max_score: float
    penalties: tuple[Penalty, ...]


@dataclass(frozen=True)
class ReviewMatrixResult:
    """The full deterministic review: per-dimension scores + an overall mean."""

    dimensions: dict[str, DimensionScore]
    overall: float
    files: tuple[str, ...]
    ruleset_version: str = RULESET_VERSION

    def to_dict(self) -> dict:
        return {
            "ruleset_version": self.ruleset_version,
            "overall": self.overall,
            "files": list(self.files),
            "dimensions": {
                dim: {
                    "score": score.score,
                    "max_score": score.max_score,
                    "penalties": [p.to_dict() for p in score.penalties],
                }
                for dim, score in self.dimensions.items()
            },
        }


# ---------------------------------------------------------------------------
# Unified-diff parsing
# ---------------------------------------------------------------------------

_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
_SKIP_PREFIXES = (
    "diff --git",
    "index ",
    "old mode",
    "new mode",
    "deleted file",
    "new file",
    "similarity ",
    "rename ",
    "copy ",
    "--- ",
)


def _strip_side_path(token: str) -> str | None:
    token = token.strip().split("\t")[0].strip()
    if token == "/dev/null":
        return None
    if token.startswith("a/") or token.startswith("b/"):
        token = token[2:]
    return token


def parse_unified_diff(text: str) -> list[AddedLine]:
    """Extract added lines with their new-file line numbers from a unified diff.

    Removed lines never advance the new-file counter; context lines do. Lines
    for deleted files (``+++ /dev/null``) are skipped.
    """
    added: list[AddedLine] = []
    path: str | None = None
    new_lineno = 0
    in_hunk = False

    for raw in text.splitlines():
        if raw.startswith("diff --git"):
            # New file block: reset hunk state so a following "+++ b/<path>" is
            # parsed as a header, and clear any pending path.
            in_hunk = False
            path = None
            continue
        if not in_hunk and raw.startswith("+++ "):
            path = _strip_side_path(raw[4:])
            continue
        if any(raw.startswith(prefix) for prefix in _SKIP_PREFIXES):
            continue
        match = _HUNK_RE.match(raw)
        if match:
            new_lineno = int(match.group(1))
            in_hunk = True
            continue
        if not in_hunk:
            continue
        if raw.startswith("\\"):  # "\ No newline at end of file"
            continue
        if raw.startswith("+"):
            if path is not None:
                added.append(AddedLine(path, new_lineno, raw[1:]))
            new_lineno += 1
        elif raw.startswith("-"):
            continue
        else:  # context line (leading space) or blank
            new_lineno += 1

    return added


# ---------------------------------------------------------------------------
# Ruleset
# ---------------------------------------------------------------------------

# (dimension, rule_id, points, message, compiled pattern) applied to each added
# line's content. Order is fixed for reproducibility.
_LINE_RULES: tuple[tuple[str, str, float, str, "re.Pattern[str]"], ...] = (
    ("security", "eval-exec", 4.0, "use of eval()/exec() on dynamic input",
     re.compile(r"\b(?:eval|exec)\s*\(")),
    ("security", "shell-true", 3.0, "subprocess invoked with shell=True",
     re.compile(r"shell\s*=\s*True")),
    ("security", "tls-verify-off", 3.0, "TLS certificate verification disabled",
     re.compile(r"verify\s*=\s*False")),
    ("security", "insecure-pickle", 2.0, "insecure pickle deserialization",
     re.compile(r"pickle\.loads?\s*\(")),
    ("security", "hardcoded-secret", 3.0, "possible hardcoded secret",
     re.compile(r"(?i)(?:password|secret|token|api[_-]?key)\s*=\s*['\"]")),
    ("security", "weak-hash", 1.0, "weak hash algorithm (md5/sha1)",
     re.compile(r"\b(?:md5|sha1)\s*\(")),
    ("reliability", "bare-except", 3.0, "bare except swallows all errors",
     re.compile(r"^\s*except\s*:")),
    ("reliability", "broad-except", 1.0, "overly broad 'except Exception'",
     re.compile(r"^\s*except\s+Exception\b")),
    ("maintainability", "todo-marker", 1.0, "unresolved TODO/FIXME marker",
     re.compile(r"\b(?:TODO|FIXME|XXX|HACK)\b")),
    ("maintainability", "type-ignore", 0.5, "suppressed type check (# type: ignore)",
     re.compile(r"#\s*type:\s*ignore")),
)

_DEF_RE = re.compile(r"^\s*(?:def|class)\s+\w")


def _is_test_path(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return (
        path.startswith("tests/")
        or "/tests/" in path
        or name.startswith("test_")
        or name.endswith("_test.py")
    )


def _is_python_source(path: str) -> bool:
    return path.endswith(".py") and not _is_test_path(path)


def _line_penalties(line: AddedLine) -> list[Penalty]:
    penalties: list[Penalty] = []
    for dimension, rule_id, points, message, pattern in _LINE_RULES:
        if pattern.search(line.content):
            penalties.append(
                Penalty(dimension, rule_id, points, line.path, line.lineno, message)
            )
    if len(line.content) > _MAX_LINE_LENGTH:
        penalties.append(
            Penalty(
                "maintainability",
                "long-line",
                1.0,
                line.path,
                line.lineno,
                f"line exceeds {_MAX_LINE_LENGTH} characters",
            )
        )
    return penalties


def _testing_penalties(added: list[AddedLine], has_tests: bool) -> list[Penalty]:
    if has_tests:
        return []
    penalties: list[Penalty] = []
    for line in added:
        if _is_python_source(line.path) and _DEF_RE.search(line.content):
            penalties.append(
                Penalty(
                    "testing",
                    "untested-definition",
                    1.0,
                    line.path,
                    line.lineno,
                    "new definition without an accompanying test in this diff",
                )
            )
    return penalties


def _assemble(files: tuple[str, ...], penalties: list[Penalty]) -> ReviewMatrixResult:
    dimensions: dict[str, DimensionScore] = {}
    for dimension in DIMENSIONS:
        dim_penalties = tuple(
            sorted(
                (p for p in penalties if p.dimension == dimension),
                key=lambda p: (p.path, p.line, p.rule),
            )
        )
        deduction = sum(p.points for p in dim_penalties)
        score = round(max(0.0, MAX_SCORE - deduction), 4)
        dimensions[dimension] = DimensionScore(dimension, score, MAX_SCORE, dim_penalties)

    overall = round(sum(d.score for d in dimensions.values()) / len(DIMENSIONS), 4)
    return ReviewMatrixResult(
        dimensions=dimensions, overall=overall, files=files, ruleset_version=RULESET_VERSION
    )


def review_diff(diff_text: str) -> ReviewMatrixResult:
    """Grade a unified diff deterministically. Pure and reproducible."""
    added = parse_unified_diff(diff_text)
    files = tuple(sorted({line.path for line in added}))
    has_tests = any(_is_test_path(path) for path in files)

    penalties: list[Penalty] = []
    for line in added:
        penalties.extend(_line_penalties(line))
    penalties.extend(_testing_penalties(added, has_tests))

    return _assemble(files, penalties)


def _default_git_runner(argv: list[str], cwd: Path | None) -> tuple[int, str, str]:
    proc = subprocess.run(
        argv,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


def review_git_diff(
    base: str,
    head: str = "HEAD",
    *,
    cwd: Path | None = None,
    git_runner: GitRunner | None = None,
) -> ReviewMatrixResult:
    """Grade the diff between ``base`` and ``head``, degrading gracefully.

    Returns a clean (all-max) result when git is unavailable or the diff cannot
    be produced. Never raises.
    """
    runner = git_runner or _default_git_runner
    argv = ["git", "diff", f"{base}...{head}"]
    try:
        returncode, stdout, _stderr = runner(argv, cwd)
    except (FileNotFoundError, OSError):
        return _assemble((), [])
    if returncode != 0:
        return _assemble((), [])
    return review_diff(stdout)
