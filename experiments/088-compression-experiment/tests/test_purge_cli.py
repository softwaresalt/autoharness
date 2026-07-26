"""Tests for the purge CLI (finding #11).

088.001-T's contract requires TTL + purge + session-end cleanup, but
``BrainspaceStore.purge_expired``/``purge_all`` previously had no standalone
command or session-end wiring exercised outside unit tests, so expired raw
output could persist indefinitely. This CLI is the explicit, operator- or
scheduler-invokable purge command for that contract.
"""

import time

from brainspace import purge_cli
from brainspace.store import BrainspaceStore


def test_purge_cli_expired_mode_removes_only_expired_rows(tmp_path, capsys):
    store = BrainspaceStore(str(tmp_path), ttl_seconds=1, max_size_bytes=10_000)
    try:
        expired_handle = store.put("expired content")
        time.sleep(1.2)  # past the 1s TTL
        live_handle = store.put("still-live content")
    finally:
        store.close()

    exit_code = purge_cli.main(["--repo-root", str(tmp_path), "--mode", "expired"])
    assert exit_code == 0

    verify = BrainspaceStore(str(tmp_path), ttl_seconds=1, max_size_bytes=10_000)
    try:
        assert verify.get(expired_handle) is None
        assert verify.get(live_handle) == "still-live content"
    finally:
        verify.close()

    captured = capsys.readouterr()
    assert "Purged" in captured.out


def test_purge_cli_all_mode_clears_entire_store(tmp_path):
    store = BrainspaceStore(str(tmp_path), ttl_seconds=3600, max_size_bytes=10_000)
    try:
        store.put("some content")
        store.put("some other content")
    finally:
        store.close()

    exit_code = purge_cli.main(["--repo-root", str(tmp_path), "--mode", "all"])
    assert exit_code == 0

    verify = BrainspaceStore(str(tmp_path), ttl_seconds=3600, max_size_bytes=10_000)
    try:
        assert verify.row_count() == 0
    finally:
        verify.close()


def test_purge_cli_defaults_to_expired_mode(tmp_path):
    # No --mode flag supplied: must default to the safer "expired" mode,
    # never silently clearing live (non-expired) rows.
    store = BrainspaceStore(str(tmp_path), ttl_seconds=3600, max_size_bytes=10_000)
    try:
        handle = store.put("live content")
    finally:
        store.close()

    exit_code = purge_cli.main(["--repo-root", str(tmp_path)])
    assert exit_code == 0

    verify = BrainspaceStore(str(tmp_path), ttl_seconds=3600, max_size_bytes=10_000)
    try:
        assert verify.get(handle) == "live content"
    finally:
        verify.close()
