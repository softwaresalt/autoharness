#!/usr/bin/env python3
"""Purge command CLI (088.001-T TTL + purge + session-end cleanup contract).

Finding #11 (P-018 review): ``BrainspaceStore.purge_expired``/``purge_all``
existed but nothing outside tests implemented or called a standalone purge
command or session-end cleanup path, so expired raw output could persist in
the durable store indefinitely. ``hook_cli.py`` calls ``purge_expired``
opportunistically after each hook invocation (an approximation of
session-end cleanup, since each hook call is a discrete subprocess with no
single observable "session end" event to hook into); this CLI is the
explicit, operator- or scheduler-invokable purge command for the same
contract.

Not wired into any CI job, pre-push hook, or hook chain by default -- this
is a manual, opt-in command for the 088-F throwaway experiment. Run with:

    python experiments/088-compression-experiment/brainspace/purge_cli.py [--mode expired|all]

from the repository root.
"""

import argparse
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_EXPERIMENT_ROOT = os.path.dirname(_THIS_DIR)
if _EXPERIMENT_ROOT not in sys.path:
    sys.path.insert(0, _EXPERIMENT_ROOT)

from brainspace.store import BrainspaceStore  # noqa: E402
from brainspace.workspace import resolve_workspace_root  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Workspace root to anchor the store to. Takes precedence over "
        "an ambient BRAINSPACE_WORKSPACE env var, which in turn takes "
        "precedence over the process cwd.",
    )
    parser.add_argument(
        "--mode",
        choices=("expired", "all"),
        default="expired",
        help="'expired' (default, safe) deletes only TTL-expired rows; "
        "'all' clears the entire store, including live rows.",
    )
    parser.add_argument(
        "--ttl-seconds",
        type=int,
        default=None,
        help="Override the store's TTL (seconds) used to decide which rows "
        "are 'expired'. Defaults to the store's own default TTL "
        "(brainspace.config.DEFAULT_TTL_SECONDS) when not supplied. Mainly "
        "useful for operators/tests that need 'expired' mode to agree with "
        "a store that was written with a non-default TTL.",
    )
    args = parser.parse_args(argv)

    if args.ttl_seconds is not None and args.ttl_seconds < 0:
        # purge_expired() computes cutoff = now - ttl; a negative ttl puts
        # the cutoff in the future, making the supposedly-safe "expired"
        # mode delete every live row. Reject before the store is even
        # opened.
        print(
            f"error: --ttl-seconds must not be negative; got {args.ttl_seconds}",
            file=sys.stderr,
        )
        return 1

    # An explicit --repo-root is an operator's per-invocation intent and
    # must win over an ambient BRAINSPACE_WORKSPACE env pin (finding #4).
    workspace_root = resolve_workspace_root(explicit_root=args.repo_root)

    store = BrainspaceStore(workspace_root, ttl_seconds=args.ttl_seconds)
    try:
        if args.mode == "all":
            before = store.row_count()
            store.purge_all()
            print(f"Purged all {before} row(s) from the brainspace store.")
        else:
            count = store.purge_expired()
            print(f"Purged {count} expired row(s) from the brainspace store.")
    finally:
        store.close()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
