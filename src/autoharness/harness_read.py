"""Portable ordinary-containment reader for harness resolution inputs.

This reader makes no race, TOCTOU or hardlink-alias resistance claim.

Unit C of the ship lifecycle release units plan
(``docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md``). The reader
rejects ordinary hazards only (FI-10): malformed or escaping relative paths,
static links that resolve outside a trust root when the request is read,
oversized input and non-regular targets. It is internal to the resolver and
has no caller until Unit B.

Order of checks per request: lexical (no filesystem access), then one file
claim (never refunded), then resolve, containment, regular-file check and a
bounded read. Containment is judged before existence. There is no adapter,
opener or callback parameter anywhere; the private test patch points are
exactly ``_is_contained`` and ``_read_chunk``.
"""

from __future__ import annotations

import enum
import os
import re
import stat
import unicodedata
from dataclasses import dataclass

__all__ = [
    "ReadErrorCode",
    "ReadLimits",
    "ReadResult",
    "ReadUsage",
    "Reader",
    "TrustRoot",
    "open_reader",
]


class TrustRoot(enum.Enum):
    """The two static trust roots a request may name."""

    WORKSPACE = "workspace"
    AUTOHARNESS = "autoharness"


class ReadErrorCode(enum.Enum):
    """Closed set of read failure codes."""

    LEXICAL_INVALID = "LEXICAL_INVALID"
    OUTSIDE_TRUST_ROOT = "OUTSIDE_TRUST_ROOT"
    PATH_NOT_FOUND = "PATH_NOT_FOUND"
    NOT_REGULAR_FILE = "NOT_REGULAR_FILE"
    FILE_SIZE_LIMIT = "FILE_SIZE_LIMIT"
    TOTAL_SIZE_LIMIT = "TOTAL_SIZE_LIMIT"
    FILE_COUNT_LIMIT = "FILE_COUNT_LIMIT"
    IO = "IO"


def _require_count(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an int")
    if value < 0:
        raise ValueError(f"{name} must be >= 0")


@dataclass(frozen=True)
class ReadLimits:
    """Per-reader limits (FI-2 defaults). Claims and reservations are never refunded."""

    max_files: int = 256
    max_file_bytes: int = 4 * 1024 * 1024
    max_total_bytes: int = 32 * 1024 * 1024

    def __post_init__(self) -> None:
        _require_count("max_files", self.max_files)
        _require_count("max_file_bytes", self.max_file_bytes)
        _require_count("max_total_bytes", self.max_total_bytes)


@dataclass(frozen=True)
class ReadUsage:
    """Monotonic usage snapshot: file claims made and bytes reserved."""

    files_claimed: int = 0
    bytes_reserved: int = 0


@dataclass(frozen=True)
class ReadResult:
    """``data`` on success only; otherwise ``error`` with a root-relative, redacted ``path``.

    Exactly one of ``data`` and ``error`` is set; test success with
    ``error is None`` (an empty file succeeds with ``data == b""``).
    """

    data: bytes | None
    error: ReadErrorCode | None
    path: str

    def __post_init__(self) -> None:
        if (self.data is None) == (self.error is None):
            raise ValueError("exactly one of data and error must be set")


def _failure(code: ReadErrorCode, path: str) -> ReadResult:
    return ReadResult(data=None, error=code, path=path)


_REDACTED_PATH = "<redacted>"
# Unbuffered binary open on both hosts; O_NONBLOCK keeps a non-regular target
# from blocking the open on POSIX.
_OPEN_FLAGS = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
_CHUNK_BYTES = 64 * 1024
_SEPARATORS = re.compile(r"[\\/]")
_RESERVED_STEMS = frozenset(
    {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    | {f"{device}{suffix}" for device in ("COM", "LPT") for suffix in "0123456789\u00b9\u00b2\u00b3"}
)


def _lexical_components(relative_path: object) -> tuple[str, ...] | None:
    """Split a root-relative request into components, or ``None`` when it is lexically invalid.

    The same rules apply on every host and touch no filesystem state: empty;
    control characters; rooted, absolute, drive, UNC and device-prefix forms;
    ``..`` in any component (both slash styles); ``:`` anywhere (alternate
    data streams and drives); reserved device stems with or without an
    extension; a component ending in a dot or a space.
    """
    if not isinstance(relative_path, str) or not relative_path:
        return None
    if any(unicodedata.category(character) == "Cc" for character in relative_path):
        return None
    if relative_path[0] in "\\/" or ":" in relative_path:
        return None
    components = tuple(_SEPARATORS.split(relative_path))
    for component in components:
        if component == ".." or component.endswith((".", " ")):
            return None
        if component.split(".", 1)[0].rstrip(" ").upper() in _RESERVED_STEMS:
            return None
    return components


def _read_chunk(fd: int, n: int) -> bytes:
    """The only raw read: one unbuffered ``os.read`` of at most ``n`` bytes."""
    return os.read(fd, n)


def _resolve(path: str) -> str:
    """``os.path.realpath``, with the deepest existing ancestor canonicalized when the target is missing.

    On Windows ``realpath`` returns a dangling link's stored target verbatim,
    which may spell an in-root directory in another form (for example an 8.3
    short name); canonicalizing the existing ancestor keeps containment exact.
    """
    resolved = os.path.realpath(path)
    if os.path.exists(resolved):
        return resolved
    head, tail = resolved, []
    while True:
        parent, name = os.path.split(head)
        if not name or parent == head:
            return resolved
        tail.append(name)
        head = parent
        if os.path.exists(head):
            return os.path.join(os.path.realpath(head), *reversed(tail))


def _exact_parts(path: str) -> list[str]:
    drive, rest = os.path.splitdrive(os.path.normpath(path))
    if os.path.altsep:
        rest = rest.replace(os.path.altsep, os.path.sep)
    return [os.path.normcase(drive), *(part for part in rest.split(os.path.sep) if part)]


def _is_contained(root: str, target: str) -> bool:
    """True when resolved ``target`` lies under resolved ``root``.

    Compares ``os.path.commonpath`` over ``os.path.normcase`` forms (so the
    comparison is case-insensitive on Windows), never a string prefix. A
    ``ValueError`` (different drives, or mixed absolute and relative forms)
    means not contained. Both arguments are ``realpath`` forms, which carry
    the on-disk case, so the root's components must also match exactly: on a
    Windows directory with case sensitivity enabled, ``normcase`` alone would
    conflate distinct siblings such as ``ws`` and ``WS``.
    """
    root_key = os.path.normcase(root)
    target_key = os.path.normcase(target)
    try:
        if os.path.commonpath([root_key, target_key]) != os.path.commonpath([root_key]):
            return False
    except ValueError:
        return False
    root_parts = _exact_parts(root)
    return _exact_parts(target)[: len(root_parts)] == root_parts


class Reader:
    """Reads bounded bytes from files under the two trust roots of one workspace.

    One reader serves one resolution on one thread; it is not thread-safe.
    """

    def __init__(self, *, workspace_root: str | os.PathLike[str], limits: ReadLimits | None = None) -> None:
        if limits is None:
            limits = ReadLimits()
        if not isinstance(limits, ReadLimits):
            raise TypeError("limits must be a ReadLimits")
        self._limits = limits
        workspace = os.path.realpath(os.fspath(workspace_root))
        autoharness_path = os.path.join(workspace, ".autoharness")
        autoharness = os.path.realpath(autoharness_path)
        self._roots: dict[TrustRoot, str | None] = {
            TrustRoot.WORKSPACE: workspace,
            # .autoharness must be the workspace's own directory, not a link: a
            # .autoharness that resolves anywhere else (outside the workspace,
            # or onto another workspace directory) is not a trust root, and
            # every request through it is OUTSIDE_TRUST_ROOT.
            TrustRoot.AUTOHARNESS: (
                autoharness if _exact_parts(autoharness) == _exact_parts(autoharness_path) else None
            ),
        }
        self._files_claimed = 0
        self._bytes_reserved = 0

    @property
    def usage(self) -> ReadUsage:
        """Snapshot of file claims and byte reservations; neither ever decreases.

        ``bytes_reserved`` may exceed ``max_total_bytes`` by at most one byte,
        when a file grows past its reservation and the overshoot is charged.
        """
        return ReadUsage(files_claimed=self._files_claimed, bytes_reserved=self._bytes_reserved)

    def read_bytes(self, root: TrustRoot, relative_path: str) -> ReadResult:
        """Read one file under ``root``.

        Every read failure returns a closed ``ReadErrorCode`` (a non-``str``
        ``relative_path`` is ``LEXICAL_INVALID``); passing a ``root`` that is
        not a ``TrustRoot`` is a programming error and raises ``TypeError``.
        """
        if not isinstance(root, TrustRoot):
            raise TypeError("root must be a TrustRoot")
        components = _lexical_components(relative_path)
        if components is None:
            return _failure(ReadErrorCode.LEXICAL_INVALID, _REDACTED_PATH)
        display_path = "/".join(components)
        if self._files_claimed >= self._limits.max_files:
            return _failure(ReadErrorCode.FILE_COUNT_LIMIT, display_path)
        self._files_claimed += 1
        root_path = self._roots[root]
        if root_path is None:
            return _failure(ReadErrorCode.OUTSIDE_TRUST_ROOT, display_path)
        try:
            target = _resolve(os.path.join(root_path, *components))
        except (OSError, ValueError):
            return _failure(ReadErrorCode.IO, display_path)
        if not _is_contained(root_path, target):
            return _failure(ReadErrorCode.OUTSIDE_TRUST_ROOT, display_path)
        try:
            status = os.stat(target)
        except (FileNotFoundError, NotADirectoryError):
            return _failure(ReadErrorCode.PATH_NOT_FOUND, display_path)
        except OSError:
            return _failure(ReadErrorCode.IO, display_path)
        if not stat.S_ISREG(status.st_mode):
            return _failure(ReadErrorCode.NOT_REGULAR_FILE, display_path)
        return self._bounded_read(target, display_path)

    def _bounded_read(self, target: str, display_path: str) -> ReadResult:
        try:
            fd = os.open(target, _OPEN_FLAGS)
        except (FileNotFoundError, NotADirectoryError):
            return _failure(ReadErrorCode.PATH_NOT_FOUND, display_path)
        except OSError:
            return _failure(ReadErrorCode.IO, display_path)
        result = _failure(ReadErrorCode.IO, display_path)
        try:
            result = self._read_open_file(fd, display_path)
        finally:
            try:
                os.close(fd)
            except OSError:
                if result.error is None:
                    result = _failure(ReadErrorCode.IO, display_path)
        return result

    def _read_open_file(self, fd: int, display_path: str) -> ReadResult:
        try:
            status = os.fstat(fd)
        except OSError:
            return _failure(ReadErrorCode.IO, display_path)
        if not stat.S_ISREG(status.st_mode):
            return _failure(ReadErrorCode.NOT_REGULAR_FILE, display_path)
        size = status.st_size
        limits = self._limits
        remaining = limits.max_total_bytes - self._bytes_reserved
        if size > limits.max_file_bytes:
            return _failure(ReadErrorCode.FILE_SIZE_LIMIT, display_path)
        if size > remaining:
            return _failure(ReadErrorCode.TOTAL_SIZE_LIMIT, display_path)
        self._bytes_reserved += size
        charged = size
        bound = min(limits.max_file_bytes, remaining) + 1
        chunks: list[bytes] = []
        held = 0
        # Termination: ``charged`` starts at ``size`` <= ``bound - 1``, so once
        # ``held`` reaches ``bound`` it exceeds ``charged``, and the charge below
        # puts ``held`` over ``max_file_bytes`` or the total over
        # ``max_total_bytes``. Every request is therefore at least one byte, and
        # an empty chunk always means end of file.
        while True:
            try:
                chunk = _read_chunk(fd, min(bound - held, _CHUNK_BYTES))
            except OSError:
                return _failure(ReadErrorCode.IO, display_path)
            if not chunk:
                return ReadResult(data=b"".join(chunks), error=None, path=display_path)
            chunks.append(chunk)
            held += len(chunk)
            if held > charged:
                self._bytes_reserved += held - charged
                charged = held
                if held > limits.max_file_bytes:
                    return _failure(ReadErrorCode.FILE_SIZE_LIMIT, display_path)
                if self._bytes_reserved > limits.max_total_bytes:
                    return _failure(ReadErrorCode.TOTAL_SIZE_LIMIT, display_path)


def open_reader(*, workspace_root: str | os.PathLike[str], limits: ReadLimits | None = None) -> Reader:
    """Open a reader over ``workspace_root`` and ``<workspace_root>/.autoharness``."""
    return Reader(workspace_root=workspace_root, limits=limits)
