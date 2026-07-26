"""Tests for the byte-equivalent retrieval core logic (088.003-T).

MUST return the FULL original or provide tested pagination/chunking -- NO
silent truncation. Also proves a direct-store recovery path independent of
any MCP transport, so byte-equivalence is testable without a live client.
"""

import pytest

from brainspace.retrieval import RetrievalError, retrieve_chunk, retrieve_full
from brainspace.store import BrainspaceStore


@pytest.fixture
def store(tmp_path):
    s = BrainspaceStore(str(tmp_path))
    yield s
    s.close()


def test_retrieve_full_returns_byte_equivalent_original(store):
    original = "x" * 50_000 + "\ntail marker\n"
    handle = store.put(original)
    assert retrieve_full(store, handle) == original


def test_retrieve_full_missing_handle_raises(store):
    with pytest.raises(RetrievalError):
        retrieve_full(store, "does-not-exist")


def test_retrieve_chunk_full_reassembly_is_byte_equivalent(store):
    original = "".join(f"line {i}\n" for i in range(5000))
    handle = store.put(original)

    chunk_size = 512
    offset = 0
    reassembled = []
    while True:
        result = retrieve_chunk(store, handle, offset=offset, limit=chunk_size)
        reassembled.append(result["chunk"])
        if not result["has_more"]:
            break
        offset += chunk_size

    assert "".join(reassembled) == original


def test_retrieve_chunk_reports_total_length(store):
    original = "abcdefghij" * 10
    handle = store.put(original)
    result = retrieve_chunk(store, handle, offset=0, limit=10)
    assert result["total_length"] == len(original)
    assert result["chunk"] == original[:10]
    assert result["has_more"] is True


def test_retrieve_chunk_no_silent_truncation_at_final_page(store):
    original = "z" * 25
    handle = store.put(original)
    result = retrieve_chunk(store, handle, offset=20, limit=10)
    assert result["chunk"] == original[20:25]
    assert result["has_more"] is False


def test_retrieve_chunk_missing_handle_raises(store):
    with pytest.raises(RetrievalError):
        retrieve_chunk(store, "nope", offset=0, limit=10)


def test_retrieve_chunk_rejects_zero_limit(store):
    handle = store.put("some content that is long enough" * 5)
    with pytest.raises(ValueError):
        retrieve_chunk(store, handle, offset=0, limit=0)


def test_retrieve_chunk_rejects_negative_limit(store):
    handle = store.put("some content that is long enough" * 5)
    with pytest.raises(ValueError):
        retrieve_chunk(store, handle, offset=0, limit=-1)


def test_retrieve_chunk_rejects_negative_offset(store):
    handle = store.put("some content that is long enough" * 5)
    with pytest.raises(ValueError):
        retrieve_chunk(store, handle, offset=-1, limit=10)


def test_retrieve_chunk_rejects_non_integer_offset(store):
    handle = store.put("some content that is long enough" * 5)
    with pytest.raises(ValueError):
        retrieve_chunk(store, handle, offset="0", limit=10)


def test_retrieve_chunk_rejects_non_integer_limit(store):
    handle = store.put("some content that is long enough" * 5)
    with pytest.raises(ValueError):
        retrieve_chunk(store, handle, offset=0, limit="10")


def test_retrieve_preserves_surrogate_content(store):
    original = "before\ud800after" * 100
    handle = store.put(original)
    assert retrieve_full(store, handle) == original


def test_direct_store_recovery_path_independent_of_mcp_surface(store):
    """A large original is recoverable directly from the store, proving
    byte-equivalence can be tested without going through any MCP transport.
    """
    original = "y" * 200_000
    handle = store.put(original)
    direct = store.get(handle)
    assert direct == original
    assert direct == retrieve_full(store, handle)
