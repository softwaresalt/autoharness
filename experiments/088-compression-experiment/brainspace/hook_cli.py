#!/usr/bin/env python3
"""Command-hook entrypoint for Copilot CLI ``postToolUse`` (088.002-T).

Not wired into ``.github/hooks/`` by default — see
``experiments/088-compression-experiment/hooks.json.example`` and the README
for how to opt in locally. Reads the hook JSON payload from stdin, resolves
the store relative to ``cwd`` (falling back to the process cwd), and writes
the hook output JSON to stdout.
"""

import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_EXPERIMENT_ROOT = os.path.dirname(_THIS_DIR)
if _EXPERIMENT_ROOT not in sys.path:
    sys.path.insert(0, _EXPERIMENT_ROOT)

from brainspace import config  # noqa: E402
from brainspace.hook import process_post_tool_use  # noqa: E402
from brainspace.store import BrainspaceStore  # noqa: E402
from brainspace.workspace import WorkspaceContainmentError, resolve_workspace_root  # noqa: E402


def main() -> int:
    raw = sys.stdin.read()

    # Disabled-by-default gate MUST run before the store is ever
    # constructed. ``BrainspaceStore.__init__`` performs a durable
    # filesystem write (mkdir + sqlite3.connect creates the DB file) as a
    # side effect of construction alone, independent of whether any row is
    # ever inserted -- so checking the flag only *inside*
    # ``process_post_tool_use`` is not enough to guarantee a disabled
    # invocation makes zero durable writes (finding #9).
    if not config.is_enabled():
        print("{}")
        return 0

    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Fail-safe: malformed input -> no-op passthrough.
        print("{}")
        return 0

    try:
        workspace_root = resolve_workspace_root(payload)
    except WorkspaceContainmentError:
        # Fail-safe: a crafted or stale payload cwd unrelated to this
        # process's working directory tree must never be honored, but the
        # invariant is fail-safe passthrough, not a crash -- never emit a
        # placeholder-free elision or let an unhandled exception propagate.
        print("{}")
        return 0
    store = BrainspaceStore(workspace_root)
    try:
        result = process_post_tool_use(payload, store)
        # Opportunistic session-end-style cleanup: each hook invocation is
        # a discrete subprocess (there is no single observable "session
        # end" event to hook), so progressive expiry-purge-per-invocation
        # is the practical approximation of the 088.001-T TTL+purge
        # contract -- it bounds how long expired raw output can persist
        # without requiring a separate scheduled process.
        #
        # This cleanup is best-effort and MUST NOT be allowed to prevent
        # the already-decided `result` (and any retrieval handle it
        # references) from being emitted: a purge failure (lock
        # contention, I/O error) here is not a reason to fail the whole
        # invocation and drop an already-created handle (P-018 round-6
        # finding).
        try:
            store.purge_expired()
        except Exception:
            pass
    finally:
        store.close()

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
