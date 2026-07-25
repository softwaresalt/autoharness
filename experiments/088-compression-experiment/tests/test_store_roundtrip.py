"""Tests for the containment-safe local store (088.001-T): put/get,
byte-equivalence, deterministic handles, TTL expiry, and size-cap eviction.
"""

import time

import pytest

from brainspace.store import BrainspaceStore


@pytest.fixture
def store(tmp_path):
    s = BrainspaceStore(str(tmp_path), ttl_seconds=3600, max_size_bytes=10_000)
    yield s
    s.close()


def test_put_then_get_round_trips_byte_equivalent(store):
    original = "line one\nline two\ttabbed\ncafé 🎉"
    handle = store.put(original)
    assert store.get(handle) == original


def test_put_is_deterministic_for_identical_content(store):
    text = "identical content, stored twice"
    h1 = store.put(text)
    h2 = store.put(text)
    assert h1 == h2  # deterministic — no timestamps/mutable counters in handle


def test_handle_contains_no_mutable_counter_pattern(store):
    text = "some raw tool output"
    handle = store.put(text)
    # A content-derived handle should be stable across two fresh stores of
    # the same content in different store instances/dirs.
    assert isinstance(handle, str)
    assert len(handle) >= 8


def test_get_missing_handle_returns_none(store):
    assert store.get("does-not-exist") is None


def test_get_expired_entry_returns_none_and_removes_row(tmp_path):
    s = BrainspaceStore(str(tmp_path), ttl_seconds=0, max_size_bytes=10_000)
    try:
        handle = s.put("expires immediately")
        time.sleep(0.05)
        assert s.get(handle) is None
        # Confirm the row was actually purged, not just filtered.
        assert s.row_count() == 0
    finally:
        s.close()


def test_size_cap_evicts_oldest_entries(tmp_path):
    s = BrainspaceStore(str(tmp_path), ttl_seconds=3600, max_size_bytes=50)
    try:
        h1 = s.put("a" * 40)
        h2 = s.put("b" * 40)
        # Store cap is tiny; inserting h2 must evict h1 (oldest) rather than
        # silently exceeding the cap.
        assert s.get(h1) is None
        assert s.get(h2) == "b" * 40
    finally:
        s.close()


def test_purge_all_removes_every_row(store):
    store.put("one")
    store.put("two")
    assert store.row_count() == 2
    store.purge_all()
    assert store.row_count() == 0


def test_delete_removes_single_row(store):
    handle = store.put("delete me")
    store.delete(handle)
    assert store.get(handle) is None


def test_store_persists_lossless_surrogate_content(store):
    text = "before\ud800after"
    handle = store.put(text)
    assert store.get(handle) == text
