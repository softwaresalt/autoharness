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


def test_purge_cli_expired_mode_removes_only_expired_rows(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = BrainspaceStore(str(tmp_path), ttl_seconds=1, max_size_bytes=10_000)
    try:
        expired_handle = store.put("expired content")
        time.sleep(1.2)  # past the 1s TTL
        live_handle = store.put("still-live content")
    finally:
        store.close()

    # P-018 round-3 follow-up finding: purge_cli previously always reopened
    # the store with the (4-hour) default TTL, so this test's 1-second TTL
    # rows were never actually "expired" from the CLI's point of view and
    # `purge_expired()` purged zero rows. The only reason the assertions
    # below used to pass anyway is that `store.get()` *lazily* deletes an
    # expired row as a side effect of reading it -- masking the fact that
    # the CLI's own purge path was never exercised. Passing --ttl-seconds
    # to match the rows' actual TTL, and asserting the reported count, makes
    # this test validate the real purge path rather than the lazy-get path.
    exit_code = purge_cli.main(
        ["--repo-root", str(tmp_path), "--mode", "expired", "--ttl-seconds", "1"]
    )
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "Purged 1" in captured.out

    verify = BrainspaceStore(str(tmp_path), ttl_seconds=1, max_size_bytes=10_000)
    try:
        assert verify.get(expired_handle) is None
        assert verify.get(live_handle) == "still-live content"
    finally:
        verify.close()


def test_purge_cli_all_mode_clears_entire_store(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
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


def test_purge_cli_defaults_to_expired_mode(tmp_path, monkeypatch):
    # No --mode flag supplied: must default to the safer "expired" mode,
    # never silently clearing live (non-expired) rows.
    monkeypatch.chdir(tmp_path)
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


def test_negative_ttl_seconds_is_rejected(tmp_path, monkeypatch, capsys):
    # P-018 round-3 (4th cycle) finding: --ttl-seconds accepted negative
    # values. purge_expired() computes cutoff = now - ttl, so a negative
    # TTL puts the cutoff in the FUTURE and makes the supposedly-safe
    # "expired" mode delete every live row -- a live-data-loss bug in a
    # mode explicitly documented as safe. Reject before opening the store.
    monkeypatch.chdir(tmp_path)
    store = BrainspaceStore(str(tmp_path), ttl_seconds=3600, max_size_bytes=10_000)
    try:
        handle = store.put("live content that must survive")
    finally:
        store.close()

    exit_code = purge_cli.main(
        ["--repo-root", str(tmp_path), "--mode", "expired", "--ttl-seconds", "-5"]
    )
    assert exit_code != 0
    assert "negative" in capsys.readouterr().err.lower()

    verify = BrainspaceStore(str(tmp_path), ttl_seconds=3600, max_size_bytes=10_000)
    try:
        assert verify.get(handle) == "live content that must survive"
    finally:
        verify.close()


def test_repo_root_arg_takes_precedence_over_ambient_env_pin(tmp_path, monkeypatch):
    # P-018 re-review finding #4 (round 2): an ambient BRAINSPACE_WORKSPACE
    # must NOT silently override an explicit --repo-root -- otherwise
    # "--mode all" could purge the wrong workspace's live rows even though
    # the CLI's own help text says --repo-root anchors the target store.
    monkeypatch.chdir(tmp_path)
    wrong_root = tmp_path / "wrong-workspace"
    right_root = tmp_path / "right-workspace"
    wrong_root.mkdir()
    right_root.mkdir()
    monkeypatch.setenv("BRAINSPACE_WORKSPACE", str(wrong_root))

    wrong_store = BrainspaceStore(str(wrong_root), ttl_seconds=3600, max_size_bytes=10_000)
    right_store = BrainspaceStore(str(right_root), ttl_seconds=3600, max_size_bytes=10_000)
    try:
        wrong_handle = wrong_store.put("must survive -- wrong workspace")
        right_handle = right_store.put("must be purged -- explicit target")
    finally:
        wrong_store.close()
        right_store.close()

    exit_code = purge_cli.main(
        ["--repo-root", str(right_root), "--mode", "all"]
    )
    assert exit_code == 0

    verify_wrong = BrainspaceStore(str(wrong_root), ttl_seconds=3600, max_size_bytes=10_000)
    verify_right = BrainspaceStore(str(right_root), ttl_seconds=3600, max_size_bytes=10_000)
    try:
        assert verify_wrong.get(wrong_handle) == "must survive -- wrong workspace"
        assert verify_right.row_count() == 0
    finally:
        verify_wrong.close()
        verify_right.close()
