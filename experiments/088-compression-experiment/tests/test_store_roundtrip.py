"""Tests for the containment-safe local store (088.001-T): put/get,
byte-equivalence, deterministic handles, TTL expiry, and size-cap eviction.
"""

import time

import pytest

from brainspace.store import BrainspaceStore, StoreCapacityError


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


def test_dedup_put_does_not_extend_ttl_clock(tmp_path):
    # 086-F carried-forward invariant: retention is a short TTL + size cap
    # that is never silently extended on dedup/access. Re-putting identical
    # content (same content-derived handle) must not reset stored_at.
    s = BrainspaceStore(str(tmp_path), ttl_seconds=1, max_size_bytes=10_000)
    try:
        text = "repeated status output, polled multiple times"
        handle = s.put(text)
        time.sleep(0.6)
        s.put(text)  # dedup re-put of identical content, well before TTL
        time.sleep(0.6)  # now ~1.2s since the ORIGINAL put -> past the 1s TTL
        assert s.get(handle) is None
        assert s.row_count() == 0
    finally:
        s.close()


def test_reput_of_expired_content_refreshes_stored_at(tmp_path):
    # Finding #4 (P-018 review): if the existing row is ALREADY expired
    # when identical content is re-put, INSERT OR IGNORE alone would leave
    # the stale (expired) stored_at untouched, silently handing back a
    # handle whose row the very next get() would delete. A re-put of
    # expired content must refresh stored_at so the content survives.
    s = BrainspaceStore(str(tmp_path), ttl_seconds=1, max_size_bytes=10_000)
    try:
        text = "content that will be re-put after expiry"
        handle = s.put(text)
        time.sleep(1.2)  # row is now expired per the 1s TTL
        handle2 = s.put(text)  # re-put of expired-but-identical content
        assert handle2 == handle
        # Immediately retrievable -- stored_at must have been refreshed,
        # not left at the original (now-expired) timestamp.
        assert s.get(handle) == text
    finally:
        s.close()


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


def test_expired_get_delete_does_not_clobber_a_concurrent_refresh(tmp_path, monkeypatch):
    # P-018 round-9 finding: get()'s expired-row cleanup previously called
    # the unconditional self.delete(handle). If a concurrent process's
    # put() refreshes this same content-derived handle (e.g. a concurrent
    # hook re-puts identical content) between this get() reading the row as
    # expired and issuing its delete, the unconditional delete would wipe
    # out the freshly-refreshed row too, leaving the concurrent writer's
    # already-issued handle dangling. Simulate the interleaving
    # deterministically by racing a "concurrent refresh" inside the
    # deletion seam itself.
    s = BrainspaceStore(str(tmp_path), ttl_seconds=1, max_size_bytes=10_000)
    try:
        text = "content a concurrent process refreshes mid-expiry-check"
        handle = s.put(text)
        # Backdate stored_at directly so this get() sees it as expired,
        # without a real sleep (avoids wall-clock flakiness).
        s._conn.execute(
            "UPDATE entries SET stored_at = ? WHERE handle = ?",
            (time.time() - 1000, handle),
        )
        s._conn.commit()

        from brainspace.store import BrainspaceStore as _Store

        original_delete_if_still_expired = _Store._delete_if_still_expired

        def racing_delete(self, h, stored_at):
            # Simulate the concurrent refresh landing *between* the read
            # that decided "expired" and this delete call.
            self._conn.execute(
                "UPDATE entries SET stored_at = ? WHERE handle = ?",
                (time.time(), h),
            )
            self._conn.commit()
            original_delete_if_still_expired(self, h, stored_at)

        monkeypatch.setattr(_Store, "_delete_if_still_expired", racing_delete)

        result = s.get(handle)
        assert result is None  # this call still correctly reports expired

        # But the concurrently-refreshed row must have survived the delete.
        row = s._conn.execute(
            "SELECT content FROM entries WHERE handle = ?", (handle,)
        ).fetchone()
        assert row is not None
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


def test_put_raises_capacity_error_instead_of_dangling_handle(tmp_path):
    # Finding #10 (P-018 review): if a SINGLE put's content exceeds the
    # cap, ``_enforce_size_cap`` evicts the just-inserted row (oldest-first
    # eviction), but ``put()`` must not still hand back that now-deleted
    # handle -- a caller (the hook) writing a retrieval footer around a
    # dangling handle would point at unretrievable content. ``put()`` must
    # raise instead, so the hook's existing fail-safe wrapper passes the
    # ORIGINAL through byte-identically.
    s = BrainspaceStore(str(tmp_path), ttl_seconds=3600, max_size_bytes=50)
    try:
        with pytest.raises(StoreCapacityError):
            s.put("x" * 200)  # a single put larger than the entire cap
        assert s.row_count() == 0  # no dangling row left behind
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
