"""Test helpers for files and directories that another process may still be touching (Windows sharing violations).

On Windows a file another process is replacing, writing, or holding open can fail a read or a delete with a
transient ``PermissionError`` (WinError 5 / 32). These helpers bound the wait instead of failing on the first try.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from autoharness.shipment_close.journal import JournalError

T = TypeVar("T")

_TRANSIENT = (OSError, ValueError, IndexError, JournalError)


def retry_read(read: Callable[[], T], *, timeout: float = 30.0, interval: float = 0.1) -> T:
    """Call ``read`` until it stops raising a transient error; re-raise the last error once ``timeout`` elapses."""

    deadline = time.monotonic() + timeout
    while True:
        try:
            return read()
        except _TRANSIENT:
            if time.monotonic() >= deadline:
                raise
        time.sleep(interval)


def cleanup_tempdir(tmp, *, timeout: float = 30.0, interval: float = 0.2) -> None:
    """``TemporaryDirectory.cleanup`` that waits out a spawned child still releasing a file in the tree."""

    deadline = time.monotonic() + timeout
    while True:
        try:
            tmp.cleanup()
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise
        time.sleep(interval)
