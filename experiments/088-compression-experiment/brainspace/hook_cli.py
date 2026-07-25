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

from brainspace.hook import process_post_tool_use  # noqa: E402
from brainspace.store import BrainspaceStore  # noqa: E402


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # Fail-safe: malformed input -> no-op passthrough.
        print("{}")
        return 0

    workspace_root = payload.get("cwd") or os.getcwd()
    store = BrainspaceStore(workspace_root)
    try:
        result = process_post_tool_use(payload, store)
    finally:
        store.close()

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
