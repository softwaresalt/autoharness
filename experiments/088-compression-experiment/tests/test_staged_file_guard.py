"""Tests for the staged-file guard (088.001-T).

A doctor/pre-commit check must fail if any store SQLite/-wal/-shm sidecar
file is staged, so raw tool output never lands in a commit.
"""

from brainspace.staged_guard import find_staged_store_violations


def test_flags_staged_sqlite_file():
    staged = [".autoharness/cache/brainspace/ccr.sqlite3", "README.md"]
    violations = find_staged_store_violations(staged)
    assert ".autoharness/cache/brainspace/ccr.sqlite3" in violations


def test_flags_staged_wal_and_shm_sidecars():
    staged = [
        ".autoharness/cache/brainspace/ccr.sqlite3-wal",
        ".autoharness/cache/brainspace/ccr.sqlite3-shm",
    ]
    violations = find_staged_store_violations(staged)
    assert len(violations) == 2


def test_flags_staged_rollback_journal_sidecar():
    # SQLite's default rollback-journal mode can leave a ``-journal`` file
    # behind after a crash mid-transaction -- this sidecar must be covered
    # by the same guard as -wal/-shm, not just the two WAL-mode sidecars.
    staged = [".autoharness/cache/brainspace/ccr.sqlite3-journal"]
    violations = find_staged_store_violations(staged)
    assert violations == [".autoharness/cache/brainspace/ccr.sqlite3-journal"]


def test_does_not_flag_unrelated_files():
    staged = ["src/autoharness/cli.py", "docs/README.md", "tests/test_foo.py"]
    assert find_staged_store_violations(staged) == []


def test_does_not_flag_similarly_named_files_outside_store_dir():
    staged = ["some/other/ccr.sqlite3"]
    assert find_staged_store_violations(staged) == []


def test_empty_staged_list_returns_no_violations():
    assert find_staged_store_violations([]) == []


def test_handles_windows_style_backslash_paths():
    staged = [".autoharness\\cache\\brainspace\\ccr.sqlite3"]
    assert find_staged_store_violations(staged) != []


def test_flags_store_files_nested_under_a_subdirectory():
    # The store is anchored to the Copilot CLI session cwd (hook_cli.py),
    # which may be any subdirectory of the repo, not only the repo root.
    # A store nested under a subdirectory must still be flagged.
    staged = [
        "subdir/.autoharness/cache/brainspace/ccr.sqlite3",
        "deeply/nested/path/.autoharness/cache/brainspace/ccr.sqlite3-wal",
    ]
    violations = find_staged_store_violations(staged)
    assert len(violations) == 2
