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


class Reader:
    """Reads bounded bytes from files under the two trust roots of one workspace."""

    def __init__(self, *, workspace_root: str | os.PathLike[str], limits: ReadLimits | None = None) -> None:
        if limits is None:
            limits = ReadLimits()
        if not isinstance(limits, ReadLimits):
            raise TypeError("limits must be a ReadLimits")
        self._limits = limits
        self._workspace_root = os.fspath(workspace_root)
        self._files_claimed = 0
        self._bytes_reserved = 0

    @property
    def usage(self) -> ReadUsage:
        return ReadUsage(files_claimed=self._files_claimed, bytes_reserved=self._bytes_reserved)

    def read_bytes(self, root: TrustRoot, relative_path: str) -> ReadResult:
        raise NotImplementedError(_red_marker("AHLC_C1_READ_LEXICAL"))


def open_reader(*, workspace_root: str | os.PathLike[str], limits: ReadLimits | None = None) -> Reader:
    """Open a reader over ``workspace_root`` and ``<workspace_root>/.autoharness``."""
    return Reader(workspace_root=workspace_root, limits=limits)
