"""Docs-only task route checker: pure fail-closed path rules and a two-layer git snapshot.

Implements deliberation 042-DL D-1 (items 2-3) and D-3 for the verification-gated
docs-only route (216-F). This module is read-only and offline: every git call
uses a fixed argv list (no shell, no interpolation) and nothing touches the
network.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

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


_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(?:(.*?)\r?\n)?---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_MUTABLE_KEYS = ("status", "updated_at", "commit", "archived_from", "archived_status")
_MUTABLE_CUSTOM_FIELDS = ("harness_status",)
ROUTE_LABELS = ("harness-verification-gated", "harness-ready")


def frontmatter_fingerprints(path: str, data: bytes) -> tuple[str, str]:
    """Return the SHA-256 of the raw body and of the protected frontmatter.

    The protected frontmatter is the frontmatter minus the allowlisted mutable keys and
    the two route labels, canonically serialized. An unparseable frontmatter raises
    ``DocsOnlyError`` (fail closed).
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DocsOnlyError(f"FRONTMATTER_UNPARSEABLE: {path}: not UTF-8") from exc
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        raise DocsOnlyError(f"FRONTMATTER_UNPARSEABLE: {path}: no frontmatter block")
    try:
        meta = yaml.safe_load(match.group(1) or "")
    except yaml.YAMLError as exc:
        raise DocsOnlyError(f"FRONTMATTER_UNPARSEABLE: {path}: invalid YAML") from exc
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        raise DocsOnlyError(f"FRONTMATTER_UNPARSEABLE: {path}: frontmatter is not a mapping")
    protected = {k: v for k, v in meta.items() if k not in _MUTABLE_KEYS}
    labels = protected.get("labels")
    if isinstance(labels, list):
        kept = [label for label in labels if label not in ROUTE_LABELS]
        if kept:
            protected["labels"] = kept
        else:
            protected.pop("labels")
    custom = protected.get("custom_fields")
    if isinstance(custom, dict):
        custom = {k: v for k, v in custom.items() if k not in _MUTABLE_CUSTOM_FIELDS}
        if custom:
            protected["custom_fields"] = custom
        else:
            protected.pop("custom_fields")
    canonical = json.dumps(protected, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=True)
    return lf_sha256(text[match.end():].encode("utf-8")), lf_sha256(canonical.encode("utf-8"))


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


def _unfingerprintable(entry: Entry) -> bool:
    """A gitlink/submodule or directory entry: its contents cannot be fingerprinted, so edits inside it are invisible."""
    return (entry.index is not None and entry.index.startswith("160000 ")) or entry.worktree == "other"


def _fingerprinted(root: Path, entry: Entry) -> Entry:
    """Add the body and protected-frontmatter fingerprints of an existing backlog Markdown file."""
    if entry.worktree is None or not entry.path.lower().endswith(".md") or entry.worktree in ("other",):
        return entry
    if entry.worktree.startswith("symlink"):
        return entry
    body, protected = frontmatter_fingerprints(entry.path, root.joinpath(*entry.path.split("/")).read_bytes())
    return Entry(entry.path, entry.index, entry.worktree, body, protected)


def take_snapshot(repo_root: Path | str, backlog_root: str | None = None) -> Snapshot:
    """Return ``HEAD`` and every changed path with independent index and working-tree entries.

    The changed set is the union of staged changes, unstaged changes and untracked
    files; renames and copies are reported as a deletion of the source plus an
    addition of the target so rename sources are always present. With a
    ``backlog_root``, each changed Markdown file under it also carries its body and
    protected-frontmatter fingerprints.
    """
    root = Path(repo_root)
    if not root.is_dir():
        raise DocsOnlyError("INVALID_INPUT: repository root is not a directory")
    head = _decode(_git(root, "rev-parse", "--verify", "HEAD")).strip()
    changed = set(_name_status_paths(_git(root, "diff", "--cached", "--ignore-submodules=none", "--name-status", "--no-renames", "-z", "HEAD")))
    changed.update(_name_status_paths(_git(root, "diff", "--ignore-submodules=none", "--name-status", "--no-renames", "-z")))
    untracked = _decode(_git(root, "ls-files", "--others", "--exclude-standard", "-z"))
    changed.update(p for p in untracked.split("\0") if p)
    index = _index_entries(root) if changed else {}
    entries = {
        path: Entry(path=path, index=index.get(path), worktree=_worktree_entry(root.joinpath(*path.split("/"))))
        for path in sorted(changed)
    }
    if backlog_root is not None:
        prefix = backlog_root.lower() + "/"
        entries = {
            path: _fingerprinted(root, entry) if path.lower().startswith(prefix) else entry
            for path, entry in entries.items()
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


# --- baseline phase --------------------------------------------------------------


def compute_self_digest(record: dict[str, Any]) -> str:
    """SHA-256 over the canonical form of every baseline entry, ``head_sha`` and the bound admission inputs."""
    body = {
        "schema_version": record.get("schema_version"),
        "phase": record.get("phase"),
        "head_sha": record.get("head_sha"),
        "entries": record.get("entries"),
        "owned_paths": record.get("owned_paths"),
        "docs_root": record.get("docs_root"),
        "backlog_root": record.get("backlog_root"),
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_self_digest(record: dict[str, Any]) -> bool:
    digest = record.get("self_digest")
    return isinstance(digest, str) and digest == compute_self_digest(record)


def _prepare(
    repo_root: Path | str, owned: Iterable[str] | None, docs_root: str, backlog_root: str, phase: str
) -> tuple[CheckResult, Path, str, str]:
    result = check_owned_paths(repo_root, owned, docs_root, backlog_root)
    result.phase = phase
    return result, Path(repo_root), docs_root, backlog_root


def baseline_phase(
    repo_root: Path | str, owned: Iterable[str] | None, docs_root: str, backlog_root: str
) -> CheckResult:
    """Record the pre-implementation snapshot without judging pre-existing state.

    Only an owned path that is already changed, staged, untracked or deleted is a
    violation (``OWNED_PATH_DIRTY_AT_BASELINE``); everything else is recorded.
    """
    result, root, _, backlog = _prepare(repo_root, owned, docs_root, backlog_root, "baseline")
    inputs = (sorted({str(o) for o in (owned or [])}), str(docs_root), str(backlog_root))
    if result.errors:
        result.record = _record("baseline", result, None, [], inputs)
        return result
    try:
        snapshot = take_snapshot(root, backlog)
    except DocsOnlyError as exc:
        result.errors.append(str(exc))
        result.record = _record("baseline", result, None, [], inputs)
        return result
    owned_lower = {str(raw).lower() for raw in (owned or [])}
    for path in snapshot.entries:
        if path.lower() in owned_lower:
            result.violations.append(
                Violation("OWNED_PATH_DIRTY_AT_BASELINE", path, "owned path is changed, staged, untracked or deleted at baseline")
            )
    for path, entry in snapshot.entries.items():
        if _unfingerprintable(entry):
            result.violations.append(
                Violation(
                    "SUBMODULE_DIRTY_AT_BASELINE", path,
                    "a dirty submodule, gitlink or nested repository cannot be fingerprinted; clean it before baseline",
                )
            )
    entries = [entry.to_dict() for entry in snapshot.entries.values()]
    result.record = _record("baseline", result, snapshot.head_sha, entries, inputs)
    result.record["self_digest"] = compute_self_digest(result.record)
    return result


def _record(
    phase: str, result: CheckResult, head_sha: str | None, entries: list[dict[str, Any]],
    inputs: tuple[list[str], str, str] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "phase": phase,
        "result": result.status,
        "head_sha": head_sha,
        "entries": entries,
        "violations": [v.to_dict() for v in result.violations],
        "errors": list(result.errors),
        "self_digest": None,
    }
    if phase == "baseline":
        owned_paths, docs_root, backlog_root = inputs if inputs is not None else ([], "", "")
        data["owned_paths"] = owned_paths
        data["docs_root"] = docs_root
        data["backlog_root"] = backlog_root
    return data


# --- completion phase ------------------------------------------------------------

_ID_RE = re.compile(r"\A[A-Za-z0-9]+(?:[.\-][A-Za-z0-9]+)*\Z")


def _valid_id(value: object, label: str) -> str:
    if not isinstance(value, str) or _ID_RE.match(value) is None:
        raise DocsOnlyError(f"INVALID_INPUT: {label} is not a valid item ID")
    return value


def _item_candidates(backlog: str, item_id: str) -> tuple[str, str]:
    return (f"{backlog}/queue/{item_id}.md", f"{backlog}/archive/{item_id}.md")


def read_manifest_ids(repo_root: Path | str, backlog_root: str, shipment_id: str) -> list[str]:
    """Read the member IDs from the live shipment file (``custom_fields.items``)."""
    root = Path(repo_root)
    try:
        backlog = _normalize(backlog_root, "backlog root")
    except ValueError as exc:
        raise DocsOnlyError(f"INVALID_INPUT: {exc}") from exc
    _valid_id(shipment_id, "shipment")
    for candidate in _item_candidates(backlog, shipment_id):
        path = root.joinpath(*candidate.split("/"))
        if not path.is_file():
            continue
        text = path.read_bytes().decode("utf-8", "replace")
        frontmatter_fingerprints(candidate, text.encode("utf-8"))
        match = _FRONTMATTER_RE.match(text)
        meta = yaml.safe_load(match.group(1) or "") if match else None
        custom = meta.get("custom_fields") if isinstance(meta, dict) else None
        items = custom.get("items") if isinstance(custom, dict) else None
        if not isinstance(items, list) or not items or not all(isinstance(i, str) for i in items):
            raise DocsOnlyError(f"INVALID_INPUT: shipment {shipment_id} has no readable member list")
        return [_valid_id(i, "manifest member") for i in items]
    raise DocsOnlyError(f"INVALID_INPUT: shipment {shipment_id} file not found under the backlog root")


def _in_head(root: Path, rel: str) -> bool:
    return bool(_git(root, "ls-tree", "-z", "--name-only", "HEAD", "--", f":(literal){rel}"))


def _validated_baseline(record: object) -> dict[str, Any]:
    if not isinstance(record, dict) or record.get("phase") != "baseline":
        raise DocsOnlyError("INVALID_INPUT: baseline record is not a baseline phase record")
    entries = record.get("entries")
    head = record.get("head_sha")
    owned_paths = record.get("owned_paths")
    if (
        not isinstance(head, str) or not isinstance(entries, list)
        or not isinstance(owned_paths, list) or not all(isinstance(o, str) for o in owned_paths)
        or not isinstance(record.get("docs_root"), str) or not isinstance(record.get("backlog_root"), str)
    ):
        raise DocsOnlyError("INVALID_INPUT: baseline record is malformed")
    if record.get("result") != "pass" or record.get("errors") or record.get("violations"):
        raise DocsOnlyError("INVALID_INPUT: baseline record is not a passing baseline")
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise DocsOnlyError("INVALID_INPUT: baseline record entry is malformed")
        for key in ("index", "worktree"):
            if key not in entry or not (entry[key] is None or isinstance(entry[key], str)):
                raise DocsOnlyError("INVALID_INPUT: baseline record entry is malformed")
    if not verify_self_digest(record):
        raise DocsOnlyError("DIGEST_MISMATCH: baseline record self-digest does not match its entries")
    return record


def _baseline_copies(
    root: Path, by_path: dict[str, dict[str, Any]], backlog: str, item_id: str
) -> dict[str, tuple[str, str]]:
    """Each retained baseline copy of the item keyed by exact path: the recorded entry when dirty, else the ``HEAD`` blob."""
    copies: dict[str, tuple[str, str]] = {}
    for candidate in _item_candidates(backlog, item_id):
        entry = by_path.get(candidate)
        if entry is not None:
            if entry.get("body_sha256"):
                copies[candidate] = (entry["body_sha256"], entry["protected_frontmatter_sha256"])
            continue
        try:
            blob = _git(root, "cat-file", "blob", f"HEAD:{candidate}")
        except DocsOnlyError:
            continue
        copies[candidate] = frontmatter_fingerprints(candidate, blob)
    return copies


def _current_copies(root: Path, backlog: str, item_id: str) -> dict[str, tuple[str, str]]:
    copies: dict[str, tuple[str, str]] = {}
    for candidate in _item_candidates(backlog, item_id):
        path = root.joinpath(*candidate.split("/"))
        if _link_in_path(root, candidate):
            continue
        if path.is_file():
            copies[candidate] = frontmatter_fingerprints(candidate, path.read_bytes())
    return copies


def _task_parent(root: Path, backlog: str, task: str) -> str | None:
    """The ``parent_id`` of the task's single live item file."""
    found = [
        root.joinpath(*c.split("/")) for c in _item_candidates(backlog, task) if root.joinpath(*c.split("/")).is_file()
    ]
    if len(found) != 1:
        raise DocsOnlyError(f"INVALID_INPUT: task {task} must have exactly one item file under the backlog root")
    text = found[0].read_bytes().decode("utf-8", "replace")
    frontmatter_fingerprints(found[0].name, text.encode("utf-8"))
    match = _FRONTMATTER_RE.match(text)
    meta = yaml.safe_load(match.group(1) or "") if match else None
    parent = meta.get("parent_id") if isinstance(meta, dict) else None
    return parent if isinstance(parent, str) else None


_REGULAR_INDEX_MODES = ("100644 ", "100755 ")
_DEFERRED_TOKEN = "DEFERRED SCOPE EXPANSION"


def _well_formed_deferred_entries(added: bytes) -> bool:
    if not added.endswith(b"\n"):
        return False
    for line in added[:-1].split(b"\n"):
        try:
            entry = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, ValueError):
            return False
        if not (
            isinstance(entry, dict) and isinstance(entry.get("id"), str) and entry["id"]
            and isinstance(entry.get("text"), str) and _DEFERRED_TOKEN in entry["text"]
        ):
            return False
    return True


def _stash_append_problem(root: Path, rel: str, by_path: dict[str, dict[str, Any]]) -> str | None:
    """Why a stash change is not a pure append of well-formed deferred entries (``None`` when it is one).

    The baseline bytes are the ``HEAD`` blob; a stash already dirty at baseline has no recoverable baseline, so it fails closed.
    """
    refusal = "stash.jsonl changed other than by appending well-formed deferred-scope-expansion entries"
    if rel in by_path:
        return refusal + " (it was already dirty at baseline)"
    try:
        tracked = _in_head(root, rel)
        if tracked and rel not in _index_entries(root):
            return refusal + " (an existing stash was deleted from the index)"
        base = _git(root, "cat-file", "blob", f"HEAD:{rel}") if tracked else b""
        path = root.joinpath(*rel.split("/"))
        if _link_in_path(root, rel) or not path.is_file():
            return refusal
        layers = [path.read_bytes()]
        indexed = _index_entries(root).get(rel)
        if indexed is not None:
            if not indexed.startswith(_REGULAR_INDEX_MODES):
                return refusal + " (its index entry is not a regular file)"
            staged = _git(root, "cat-file", "blob", f":{rel}")
            if staged != base:
                layers.append(staged)
    except (DocsOnlyError, OSError):
        return refusal
    if base and not base.endswith(b"\n"):
        return refusal
    for current in layers:
        if not current.startswith(base) or len(current) == len(base):
            return refusal
        if not _well_formed_deferred_entries(current[len(base):]):
            return refusal
    return None



def _is_regular_entry(entry: Entry) -> bool:
    """A regular working-tree file whose index entry, when staged, has a regular mode."""
    if entry.worktree is None or not entry.worktree.startswith(_REGULAR_INDEX_MODES):
        return False
    return entry.index is None or entry.index.startswith(_REGULAR_INDEX_MODES)


def _completion_result(result: CheckResult, head: str | None, digest: str | None, delta: list[str]) -> CheckResult:
    implementation = [v.to_dict() for v in result.violations if v.check_class == "implementation"]
    lifecycle = [v.to_dict() for v in result.violations if v.check_class == "lifecycle"]
    result.record = {
        "schema_version": SCHEMA_VERSION,
        "phase": "completion",
        "result": result.status,
        "head_sha": head,
        "baseline_self_digest": digest,
        "delta_paths": sorted(delta),
        "implementation": {"result": "violation" if implementation else "pass", "violations": implementation},
        "lifecycle": {"result": "violation" if lifecycle else "pass", "violations": lifecycle},
        "violations": [v.to_dict() for v in result.violations],
        "errors": list(result.errors),
    }
    return result


def error_result(phase: str, message: str) -> CheckResult:
    """An error result (exit 2) with a schema-valid record, for failures outside the phase functions."""
    result = CheckResult(phase=phase, errors=[message])
    if phase == "baseline":
        result.record = _record("baseline", result, None, [])
        return result
    return _completion_result(result, None, None, [])


def resolve_repo_root(cwd: Path | str) -> Path:
    """The git top-level of ``cwd``; every repository-relative argument resolves against it."""
    path = Path(cwd)
    if not path.is_dir():
        raise DocsOnlyError("INVALID_INPUT: working directory is not a directory")
    return Path(_decode(_git(path, "rev-parse", "--show-toplevel")).strip())


def completion_phase(
    repo_root: Path | str,
    owned: Iterable[str] | None,
    docs_root: str,
    backlog_root: str,
    baseline_record: object,
    *,
    task_id: str,
    feature_id: str,
    shipment_id: str,
    manifest_ids: Sequence[str],
) -> CheckResult:
    """Judge the task delta (per git layer) against the recorded baseline; run before the task commit."""
    result, root, docs, backlog = _prepare(repo_root, owned, docs_root, backlog_root, "completion")
    implementation: list[Violation] = []
    lifecycle: list[Violation] = []
    delta: list[str] = []
    digest: str | None = None
    head: str | None = None

    def finish() -> CheckResult:
        result.violations = [*result.violations, *implementation, *lifecycle]
        return _completion_result(result, head, digest, delta)

    if result.errors:
        return finish()
    try:
        record = _validated_baseline(baseline_record)
        digest = record.get("self_digest")
        # A rule-violating owned path can never match a passing baseline; report the path violation instead.
        if not result.violations and (
            sorted({str(o) for o in (owned or [])}) != record["owned_paths"]
            or str(docs_root) != record["docs_root"] or str(backlog_root) != record["backlog_root"]
        ):
            raise DocsOnlyError(
                "INPUT_MISMATCH: --owned/--docs-root/--backlog-root differ from the inputs bound into the baseline record"
            )
        # A rule-violating owned path can never match a passing baseline; report the path violation instead.
        if not result.violations and (
            sorted({str(o) for o in (owned or [])}) != record["owned_paths"]
            or str(docs_root) != record["docs_root"] or str(backlog_root) != record["backlog_root"]
        ):
            raise DocsOnlyError(
                "INPUT_MISMATCH: --owned/--docs-root/--backlog-root differ from the inputs bound into the baseline record"
            )
        task = _valid_id(task_id, "task")
        feature = _valid_id(feature_id, "feature")
        shipment = _valid_id(shipment_id, "shipment")
        members = [_valid_id(m, "manifest member") for m in manifest_ids]
        if task not in members:
            raise DocsOnlyError("INVALID_INPUT: task is not a member of the shipment manifest")
        if len({task, feature, shipment}) != 3:
            raise DocsOnlyError("INVALID_INPUT: task, feature and shipment must be three distinct items")
        if _task_parent(root, backlog, task) != feature:
            raise DocsOnlyError("IDENTITY_MISMATCH: the task's parent_id is not the supplied feature")
        # Ship accepts task-only manifests: the covering feature is resolved through parent_id, not membership.
        if not any(root.joinpath(*c.split("/")).is_file() for c in _item_candidates(backlog, feature)):
            raise DocsOnlyError("INVALID_INPUT: the task's parent feature has no item file under the backlog root")
        snapshot = take_snapshot(root)
        head = snapshot.head_sha
        if snapshot.head_sha != record["head_sha"]:
            raise DocsOnlyError("HEAD_MOVED: HEAD differs from the baseline head_sha; run completion before the task commit")
        by_path = {e["path"]: e for e in record["entries"]}
        current = snapshot.entries
        names = set(snapshot.entries) | set(by_path)
        delta = []
        for name in names:
            before = (by_path[name]["index"], by_path[name]["worktree"]) if name in by_path else None
            after = current[name].layers() if name in current else None
            if before != after:
                delta.append(name)

        for path in sorted(delta):
            if path in current and _unfingerprintable(current[path]):
                implementation.append(
                    Violation("UNFINGERPRINTABLE_ENTRY", path, "a changed submodule, gitlink or directory entry cannot be fingerprinted")
                )
        owned_lower = {str(o).lower() for o in (owned or [])}
        for index_path, index_value in _index_entries(root).items():
            if index_path.lower() in owned_lower and not index_value.startswith(_REGULAR_INDEX_MODES):
                implementation.append(
                    Violation("NOT_REGULAR_FILE", index_path, "owned path has a non-regular git index entry (symlink or gitlink)")
                )
        backlog_lower = backlog.lower()
        lifecycle_ids = {task, feature, shipment}
        lifecycle_paths = {c: i for i in lifecycle_ids for c in _item_candidates(backlog, i)}
        lifecycle_lower = {c.lower() for c in lifecycle_paths}
        sibling_paths = {
            c.lower(): i for i in members if i not in lifecycle_ids for c in _item_candidates(backlog, i)
        }
        checkpoint_re = re.compile(re.escape(backlog_lower) + r"/checkpoints/[^/]+\.json\Z")
        touched: set[str] = set()
        for path in sorted(delta):
            lower = path.lower()
            if not lower.startswith(backlog_lower + "/"):
                if lower not in owned_lower:
                    implementation.append(Violation("NOT_OWNED_PATH", path, "task delta path is not an owned path"))
                # The exact delta path is judged even when it matches ownership only case-insensitively.
                implementation.extend(_owned_violations(root, [path], docs, backlog))
                continue
            if path in lifecycle_paths:
                touched.add(lifecycle_paths[path])
            elif lower in sibling_paths:
                lifecycle.append(
                    Violation("SIBLING_MEMBER_CHANGED", path, "a sibling shipment member changed during the task", "lifecycle")
                )
            elif lower in lifecycle_lower:
                lifecycle.append(
                    Violation("BACKLOG_PATH_NOT_LIFECYCLE", path, "backlog path matches a lifecycle file only by letter case", "lifecycle")
                )
            elif checkpoint_re.match(lower) and path not in by_path and path in current and not _in_head(root, path):
                if _link_in_path(root, path) or not _is_regular_entry(current[path]):
                    lifecycle.append(
                        Violation(
                            "NOT_REGULAR_FILE", path,
                            "a new checkpoint is not a regular file (symlink, reparse point, gitlink or non-regular index entry)",
                            "lifecycle",
                        )
                    )
            elif path == f"{backlog}/stash.jsonl":
                problem = _stash_append_problem(root, path, by_path)
                if problem:
                    lifecycle.append(Violation("BACKLOG_PATH_NOT_LIFECYCLE", path, problem, "lifecycle"))
            else:
                lifecycle.append(
                    Violation("BACKLOG_PATH_NOT_LIFECYCLE", path, "backlog path is not the task, feature, shipment or a new checkpoint", "lifecycle")
                )
        for item_id in sorted(touched):
            before = _baseline_copies(root, by_path, backlog, item_id)
            after = _current_copies(root, backlog, item_id)
            path = _item_candidates(backlog, item_id)[0]
            if len(before) > 1 or len(after) > 1:
                dup = sorted(after if len(after) > 1 else before)[-1]
                lifecycle.append(
                    Violation("LIFECYCLE_DUPLICATE_COPY", dup, "a lifecycle item has simultaneous queue and archive copies", "lifecycle")
                )
                continue
            if not before or not after:
                lifecycle.append(
                    Violation("LIFECYCLE_FILE_MISSING", path, "lifecycle file has no baseline or current content", "lifecycle")
                )
                continue
            # A queue-to-archive relocation is legitimate only when the single copy keeps its baseline content.
            path, actual = next(iter(after.items()))
            expected = next(iter(before.values()))
            if expected[0] != actual[0]:
                lifecycle.append(
                    Violation("LIFECYCLE_BODY_CHANGED", path, "the body of a lifecycle file changed during the task", "lifecycle")
                )
            if expected[1] != actual[1]:
                lifecycle.append(
                    Violation(
                        "LIFECYCLE_PROTECTED_FRONTMATTER_CHANGED", path,
                        "protected frontmatter or a non-route label changed during the task", "lifecycle",
                    )
                )
    except DocsOnlyError as exc:
        result.errors.append(str(exc))
    return finish()
