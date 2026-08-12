"""Standalone worker script for real multi-process SessionLock tests (118.005-T).

Not a pytest test module (filename has no ``test_`` prefix, so pytest does
not collect it) -- invoked via ``subprocess`` by
``tests/test_supervise_locking.py`` (and extended for
``tests/test_supervise_locking_stale.py``, 118.006-T) to exercise the guard
lock from genuinely separate OS processes, as required by the mandatory
real-parallel-contender test.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from autoharness.supervise.locking import (  # noqa: E402
    SessionLock,
    SessionLockRefused,
)


def _cmd_contend(args: argparse.Namespace) -> int:
    """Attempt a single non-blocking acquisition; hold briefly if acquired."""

    lock = SessionLock(args.workspace, session_id=args.session_id)
    try:
        lock.acquire()
    except SessionLockRefused:
        Path(args.result).write_text("refused", encoding="utf-8")
        return 0

    Path(args.result).write_text("acquired", encoding="utf-8")
    time.sleep(args.hold)
    lock.release()
    Path(args.result).write_text("acquired:released", encoding="utf-8")
    return 0


def _cmd_park(args: argparse.Namespace) -> int:
    """Acquire and hold the lock until a stop-file appears or timeout.

    Used to simulate a live holder (for contention/refusal tests) and, when
    killed externally without ``--clean-release``, a crashed holder (for
    OS-release-on-death tests).
    """

    lock = SessionLock(args.workspace, session_id=args.session_id)
    try:
        lock.acquire()
    except SessionLockRefused:
        Path(args.result).write_text("refused", encoding="utf-8")
        return 0

    status = {
        "outcome": "acquired",
        "pid": os.getpid(),
        "record_path": str(lock.record_path),
        "guard_path": str(lock.guard_path),
        "session_id": lock.session_id,
    }
    Path(args.result).write_text(json.dumps(status), encoding="utf-8")

    stop_path = Path(args.stop_file) if args.stop_file else None
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        if stop_path is not None and stop_path.exists():
            break
        time.sleep(0.05)

    if args.clean_release:
        lock.release()
    # else: exit without releasing. The parent test either lets us exit here
    # (relying on process-exit-based OS lock release) or kills this process
    # externally before we get here -- both are valid "crash" surrogates for
    # the OS-release-on-death test.
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--session-id", dest="session_id", default=None)
    sub = parser.add_subparsers(dest="mode", required=True)

    contend_p = sub.add_parser("contend")
    contend_p.add_argument("--hold", type=float, default=0.3)

    park_p = sub.add_parser("park")
    park_p.add_argument("--timeout", type=float, default=15.0)
    park_p.add_argument("--stop-file", dest="stop_file", default=None)
    park_p.add_argument("--clean-release", dest="clean_release", action="store_true")

    args = parser.parse_args()

    if args.mode == "contend":
        return _cmd_contend(args)
    if args.mode == "park":
        return _cmd_park(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
