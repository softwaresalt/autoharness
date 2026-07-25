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
