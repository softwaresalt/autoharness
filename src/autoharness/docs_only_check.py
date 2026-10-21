"""Docs-only task route checker: pure fail-closed path rules and a two-layer git snapshot.

Implements deliberation 042-DL D-1 (items 2-3) and D-3 for the verification-gated
docs-only route (216-F). This module is read-only and offline: every git call
uses a fixed argv list (no shell, no interpolation) and nothing touches the
network.
"""

from __future__ import annotations

import hashlib
import os
import stat
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"

_GIT_TIMEOUT_SECONDS = 60
_ALWAYS_DENIED_ROOTS = (".github", ".autoharness", "templates", "schemas", "scripts", "src", "tests")
_DENIED_NAME_SUFFIXES = (".agent.md", ".instructions.md", ".prompt.md", ".chatmode.md")
_DENIED_NAMES = ("skill.md", "agents.md", "claude.md", "copilot-instructions.md", "workflow-policies.md")
_FILE_ATTRIBUTE_REPARSE_POINT = 0x400


class DocsOnlyError(Exception):
    """Invalid input, record corruption or git failure: the checker's error result (exit 2)."""


@dataclass(frozen=True)
class Violation:
    """One rule violation naming the offending path."""

    rule: str
    path: str
    message: str
    check_class: str = "implementation"

    def to_dict(self) -> dict[str, str]:
        return {"rule": self.rule, "path": self.path, "message": self.message, "class": self.check_class}


@dataclass
class CheckResult:
    """The outcome of one check: pass (0), violation (1) or error (2)."""

    phase: str
    violations: list[Violation] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    record: dict[str, Any] | None = None

    @property
    def status(self) -> str:
        if self.errors:
            return "error"
        return "violation" if self.violations else "pass"

    @property
    def exit_code(self) -> int:
        return {"pass": 0, "violation": 1, "error": 2}[self.status]


@dataclass(frozen=True)
class Entry:
    """One changed path with its independent index-layer and working-tree-layer fingerprints."""

    path: str
    index: str | None
    worktree: str | None
    body_sha256: str | None = None
    protected_frontmatter_sha256: str | None = None

    def layers(self) -> tuple[str | None, str | None]:
        return (self.index, self.worktree)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"path": self.path, "index": self.index, "worktree": self.worktree}
        if self.body_sha256 is not None:
            data["body_sha256"] = self.body_sha256
            data["protected_frontmatter_sha256"] = self.protected_frontmatter_sha256
        return data


@dataclass(frozen=True)
class Snapshot:
    """``HEAD`` plus every changed path keyed by its repository-relative POSIX path."""

    head_sha: str
    entries: dict[str, Entry]


# --- git -----------------------------------------------------------------------


def _git_env() -> dict[str, str]:
    drop = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG") and k not in drop}


def _git(repo_root: Path, *args: str) -> bytes:
    argv = ["git", "--no-optional-locks", "-C", str(repo_root), *args]
    try:
        done = subprocess.run(
            argv, capture_output=True, env=_git_env(), check=False, timeout=_GIT_TIMEOUT_SECONDS
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DocsOnlyError(f"GIT_FAILURE: {type(exc).__name__}") from exc
    if done.returncode != 0:
        raise DocsOnlyError(f"GIT_FAILURE: git {args[0]} exited {done.returncode}")
    return done.stdout


def _decode(raw: bytes) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocsOnlyError("GIT_FAILURE: non-UTF-8 path or output") from exc


def _name_status_paths(raw: bytes) -> list[str]:
    tokens = _decode(raw).split("\0")
    if tokens and tokens[-1] == "":
        tokens.pop()
    if len(tokens) % 2:
        raise DocsOnlyError("GIT_FAILURE: malformed name-status output")
    paths: list[str] = []
    for status, path in zip(tokens[0::2], tokens[1::2]):
        if status.startswith("U"):
            raise DocsOnlyError(f"GIT_FAILURE: unmerged path {path}")
        paths.append(path)
    return paths


def _index_entries(repo_root: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for record in _decode(_git(repo_root, "ls-files", "-s", "-z")).split("\0"):
        if not record:
            continue
        meta, _, path = record.partition("\t")
        mode, blob, stage = meta.split(" ")
        if stage != "0":
            raise DocsOnlyError(f"GIT_FAILURE: unmerged path {path}")
        entries[path] = f"{mode} {blob}"
    return entries


# --- fingerprints --------------------------------------------------------------


def lf_sha256(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def _is_reparse(st: os.stat_result) -> bool:
    return bool(getattr(st, "st_file_attributes", 0) & _FILE_ATTRIBUTE_REPARSE_POINT)


def _worktree_entry(path: Path) -> str | None:
    try:
        st = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise DocsOnlyError(f"IO_FAILURE: {type(exc).__name__}") from exc
    try:
        if stat.S_ISLNK(st.st_mode) or _is_reparse(st):
            return "symlink " + hashlib.sha256(os.fsencode(os.readlink(path))).hexdigest()
        if stat.S_ISREG(st.st_mode):
            mode = "100755" if st.st_mode & stat.S_IXUSR else "100644"
            return f"{mode} {lf_sha256(path.read_bytes())}"
    except OSError as exc:
        raise DocsOnlyError(f"IO_FAILURE: {type(exc).__name__}") from exc
    return "other"


def take_snapshot(repo_root: Path | str) -> Snapshot:
    """Return ``HEAD`` and every changed path with independent index and working-tree entries.

    The changed set is the union of staged changes, unstaged changes and untracked
    files; renames and copies are reported as a deletion of the source plus an
    addition of the target so rename sources are always present.
    """
    root = Path(repo_root)
    if not root.is_dir():
        raise DocsOnlyError("INVALID_INPUT: repository root is not a directory")
    head = _decode(_git(root, "rev-parse", "--verify", "HEAD")).strip()
    changed = set(_name_status_paths(_git(root, "diff", "--cached", "--name-status", "--no-renames", "-z", "HEAD")))
    changed.update(_name_status_paths(_git(root, "diff", "--name-status", "--no-renames", "-z")))
    untracked = _decode(_git(root, "ls-files", "--others", "--exclude-standard", "-z"))
    changed.update(p for p in untracked.split("\0") if p)
    index = _index_entries(root) if changed else {}
    entries = {
        path: Entry(path=path, index=index.get(path), worktree=_worktree_entry(root.joinpath(*path.split("/"))))
        for path in sorted(changed)
    }
    return Snapshot(head_sha=head, entries=entries)


# --- path rules ----------------------------------------------------------------


def _normalize(raw: object, label: str) -> str:
    """Return a clean repository-relative POSIX path or raise ``ValueError`` naming the defect."""
    if not isinstance(raw, str) or not raw:
        raise ValueError(f"{label} is empty or not a string")
    if "\0" in raw or "\\" in raw or ":" in raw:
        raise ValueError(f"{label} contains a backslash, colon or NUL")
    if raw.startswith("/"):
        raise ValueError(f"{label} is absolute")
    for segment in raw.split("/"):
        if segment in ("", ".", ".."):
            raise ValueError(f"{label} has an empty, dot or dotdot segment")
    return raw


def _link_in_path(root: Path, rel: str) -> bool:
    current = root
    for segment in rel.split("/"):
        current = current / segment
        try:
            st = current.lstat()
        except FileNotFoundError:
            return False
        except OSError:
            return True
        if stat.S_ISLNK(st.st_mode) or _is_reparse(st):
            return True
    return False


def _denied(rel_lower: str, backlog_lower: str) -> bool:
    first = rel_lower.split("/", 1)[0]
    if first in _ALWAYS_DENIED_ROOTS:
        return True
    if rel_lower == backlog_lower or rel_lower.startswith(backlog_lower + "/"):
        return True
    name = rel_lower.rsplit("/", 1)[-1]
    return name in _DENIED_NAMES or name.endswith(_DENIED_NAME_SUFFIXES)


def _owned_violations(root: Path, owned: Sequence[str], docs_root: str, backlog_root: str) -> list[Violation]:
    docs_lower = docs_root.lower()
    backlog_lower = backlog_root.lower()
    found: list[Violation] = []
    for raw in owned:
        try:
            rel = _normalize(raw, "owned path")
        except ValueError as exc:
            found.append(Violation("INVALID_PATH", str(raw), str(exc)))
            continue
        lower = rel.lower()
        if _denied(lower, backlog_lower) or _denied(docs_lower, backlog_lower):
            found.append(Violation("DENY_LIST", rel, "owned path is on the deny list, which overrides the docs root"))
            continue
        if not lower.startswith(docs_lower + "/"):
            found.append(Violation("OUTSIDE_DOCS_ROOT", rel, f"owned path is not under the docs root {docs_root}"))
            continue
        if not lower.endswith(".md"):
            found.append(Violation("NOT_MARKDOWN", rel, "owned path is not a prose .md file"))
            continue
        if _link_in_path(root, rel):
            found.append(Violation("SYMLINK", rel, "owned path or a parent is a symlink or reparse point"))
            continue
        target = root.joinpath(*rel.split("/"))
        if target.exists() and not target.is_file():
            found.append(Violation("NOT_REGULAR_FILE", rel, "owned path is not a regular file"))
    return found


def check_owned_paths(
    repo_root: Path | str, owned: Iterable[str] | None, docs_root: str, backlog_root: str
) -> CheckResult:
    """Apply the D-1 path rules to the owned paths. Fail closed: bad input is an error result."""
    result = CheckResult(phase="paths")
    root = Path(repo_root)
    if not root.is_dir():
        result.errors.append("INVALID_INPUT: repository root is not a directory")
        return result
    if owned is None or isinstance(owned, str):
        result.errors.append("INVALID_INPUT: owned paths must be a non-empty list")
        return result
    owned_list = list(owned)
    if not owned_list:
        result.errors.append("INVALID_INPUT: owned paths must be a non-empty list")
        return result
    try:
        docs = _normalize(docs_root, "docs root")
        backlog = _normalize(backlog_root, "backlog root")
    except ValueError as exc:
        result.errors.append(f"INVALID_INPUT: {exc}")
        return result
    if _link_in_path(root, docs):
        result.errors.append("INVALID_INPUT: docs root is or sits under a symlink or reparse point")
        return result
    result.violations.extend(_owned_violations(root, owned_list, docs, backlog))
    return result
