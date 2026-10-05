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
import sys
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
    """``data`` on success only; otherwise ``error`` with a root-relative, redacted ``path``."""

    data: bytes | None
    error: ReadErrorCode | None
    path: str


_REDACTED_PATH = "<redacted>"
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


def _red_marker(prefix: str) -> str:
    # RED-phase scaffold (P-004 Marker Convention): derives <t> from the calling
    # test method name (its Proof G case ID when the name carries one).
    frame = sys._getframe(1)
    while frame is not None:
        name = frame.f_code.co_name
        if name.startswith("test_"):
            match = re.match(r"test_(G\d\d[a-z]?)(?:_|$)", name)
            return f"{prefix}:{match.group(1) if match else name}"
        frame = frame.f_back
    return f"{prefix}:unattributed"


def _read_chunk(fd: int, n: int) -> bytes:
    raise NotImplementedError(_red_marker("AHLC_C3_READ_BOUNDS"))


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


def _is_contained(root: str, target: str) -> bool:
    """True when resolved ``target`` lies under resolved ``root``.

    Compares ``os.path.commonpath`` over ``os.path.normcase`` forms (so the
    comparison is case-insensitive on Windows), never a string prefix. A
    ``ValueError`` (different drives, or mixed absolute and relative forms)
    means not contained.
    """
    root_key = os.path.normcase(root)
    target_key = os.path.normcase(target)
    try:
        return os.path.commonpath([root_key, target_key]) == os.path.commonpath([root_key])
    except ValueError:
        return False


class Reader:
    """Reads bounded bytes from files under the two trust roots of one workspace."""

    def __init__(self, *, workspace_root: str | os.PathLike[str], limits: ReadLimits | None = None) -> None:
        if limits is None:
            limits = ReadLimits()
        if not isinstance(limits, ReadLimits):
            raise TypeError("limits must be a ReadLimits")
        self._limits = limits
        workspace = os.path.realpath(os.fspath(workspace_root))
        self._roots = {
            TrustRoot.WORKSPACE: workspace,
            TrustRoot.AUTOHARNESS: os.path.realpath(os.path.join(workspace, ".autoharness")),
        }
        self._files_claimed = 0
        self._bytes_reserved = 0

    @property
    def usage(self) -> ReadUsage:
        return ReadUsage(files_claimed=self._files_claimed, bytes_reserved=self._bytes_reserved)

    def read_bytes(self, root: TrustRoot, relative_path: str) -> ReadResult:
        """Read one file under ``root``; every failure returns a closed ``ReadErrorCode``."""
        if not isinstance(root, TrustRoot):
            raise TypeError("root must be a TrustRoot")
        components = _lexical_components(relative_path)
        if components is None:
            return ReadResult(data=None, error=ReadErrorCode.LEXICAL_INVALID, path=_REDACTED_PATH)
        display_path = "/".join(components)
        if self._files_claimed >= self._limits.max_files:
            return ReadResult(data=None, error=ReadErrorCode.FILE_COUNT_LIMIT, path=display_path)
        self._files_claimed += 1
        root_path = self._roots[root]
        try:
            target = _resolve(os.path.join(root_path, *components))
        except (OSError, ValueError):
            return ReadResult(data=None, error=ReadErrorCode.IO, path=display_path)
        if not _is_contained(root_path, target):
            return ReadResult(data=None, error=ReadErrorCode.OUTSIDE_TRUST_ROOT, path=display_path)
        try:
            os.stat(target)
        except (FileNotFoundError, NotADirectoryError):
            return ReadResult(data=None, error=ReadErrorCode.PATH_NOT_FOUND, path=display_path)
        except OSError:
            return ReadResult(data=None, error=ReadErrorCode.IO, path=display_path)
        return self._bounded_read(target, display_path)

    def _bounded_read(self, target: str, display_path: str) -> ReadResult:
        raise NotImplementedError(_red_marker("AHLC_C3_READ_BOUNDS"))


def open_reader(*, workspace_root: str | os.PathLike[str], limits: ReadLimits | None = None) -> Reader:
    """Open a reader over ``workspace_root`` and ``<workspace_root>/.autoharness``."""
    return Reader(workspace_root=workspace_root, limits=limits)
