"""Byte-equivalent retrieval core logic (088.003-T).

Returns the FULL original or provides tested pagination/chunking -- no
silent truncation (086-F flagged ``MAX_RETRIEVE_CHARS`` truncation as a
defect; this module must not repeat it). Also exposes a direct-store
recovery path (``store.get`` is already that path) so byte-equivalence is
provable independent of any MCP transport.
"""


class RetrievalError(Exception):
    """Raised when a handle is missing, expired, or otherwise unrecoverable."""


def retrieve_full(store, handle: str) -> str:
    """Return the complete byte-equivalent original for ``handle``."""
    original = store.get(handle)
    if original is None:
        raise RetrievalError(f"handle not found or expired: {handle}")
    return original


def retrieve_chunk(store, handle: str, offset: int = 0, limit: int = 4096):
    """Return one page of the original starting at ``offset``.

    Returns a dict: ``{"chunk": str, "offset": int, "total_length": int,
    "has_more": bool}``. Repeated calls advancing ``offset`` by the returned
    chunk length, until ``has_more`` is False, reassemble the exact original
    with no silent truncation.

    ``offset`` and ``limit`` are validated strictly: both must be ``int``
    (bool excluded, since ``bool`` is an ``int`` subclass and would silently
    coerce to 0/1), ``offset`` must be non-negative, and ``limit`` must be a
    positive integer. A zero/negative ``limit`` would otherwise return an
    empty chunk with ``has_more=True`` forever (an infinite pagination
    loop), and a non-integer value would raise an uncaught ``TypeError``
    deep in the slice arithmetic instead of a clear, callable-facing error.
    """
    if isinstance(offset, bool) or not isinstance(offset, int):
        raise ValueError(f"offset must be an int, got {type(offset).__name__}")
    if isinstance(limit, bool) or not isinstance(limit, int):
        raise ValueError(f"limit must be an int, got {type(limit).__name__}")
    if offset < 0:
        raise ValueError(f"offset must be >= 0, got {offset}")
    if limit <= 0:
        raise ValueError(f"limit must be a positive integer, got {limit}")

    original = store.get(handle)
    if original is None:
        raise RetrievalError(f"handle not found or expired: {handle}")

    total_length = len(original)
    chunk = original[offset : offset + limit]
    has_more = (offset + len(chunk)) < total_length
    return {
        "chunk": chunk,
        "offset": offset,
        "total_length": total_length,
        "has_more": has_more,
    }
