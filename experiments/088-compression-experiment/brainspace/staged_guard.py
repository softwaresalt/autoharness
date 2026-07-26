"""Staged-file guard (088.001-T).

A doctor / pre-commit check that fails if any brainspace store SQLite file
or its ``-wal``/``-shm``/``-journal`` sidecar is staged for commit, so raw
tool output never lands in git history.
"""

import os

from brainspace import config

_STORE_MARKER = config.STORE_RELATIVE_DIR.replace("\\", "/")
_DB_BASENAME = config.STORE_DB_FILENAME
_SIDECAR_SUFFIXES = ("", "-wal", "-shm", "-journal")


def find_staged_store_violations(staged_paths):
    """Return the subset of ``staged_paths`` that are store files.

    The store is anchored to the Copilot CLI session ``cwd`` (see
    ``hook_cli.py``), which may be any subdirectory of the repository, not
    only the repository root. A staged path is a violation whenever its
    directory *ends with* the store's relative marker
    (``.autoharness/cache/brainspace``) at any nesting depth -- matching
    only the exact top-level path would silently miss a store nested under
    a subdirectory.

    Args:
        staged_paths: iterable of path strings (as returned by
            ``git diff --cached --name-only``), forward- or back-slash.

    Returns:
        list[str]: the offending paths, in input order.
    """
    marker_parts = tuple(_STORE_MARKER.split("/"))
    violations = []
    for raw_path in staged_paths:
        normalized = raw_path.replace("\\", "/")
        parts = normalized.split("/")
        directory_parts = tuple(parts[:-1])
        filename = parts[-1]
        if directory_parts[-len(marker_parts):] != marker_parts:
            continue
        if any(filename == f"{_DB_BASENAME}{suffix}" for suffix in _SIDECAR_SUFFIXES):
            violations.append(raw_path)
    return violations


def main(staged_paths=None):
    """CLI entry point: exit non-zero if any store file is staged.

    Fails CLOSED if ``staged_paths`` is not supplied and the underlying
    ``git diff --cached --name-only`` invocation itself fails (nonzero
    returncode) -- a pre-commit control protecting raw stored output must
    never silently report "no violations" just because it could not inspect
    the index (P-018 round-3 follow-up finding).
    """
    import subprocess
    import sys

    if staged_paths is None:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(
                "088-F staged-file guard: `git diff --cached --name-only` "
                "failed, so the staged index could not be inspected. Failing "
                "closed rather than silently reporting no violations."
            )
            if result.stderr:
                print(result.stderr.strip())
            sys.exit(1)
        staged_paths = [line for line in result.stdout.splitlines() if line]

    violations = find_staged_store_violations(staged_paths)
    if violations:
        print("088-F staged-file guard: brainspace store files are staged:")
        for path in violations:
            print(f"  - {path}")
        print("Unstage these -- the store must never be committed.")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
