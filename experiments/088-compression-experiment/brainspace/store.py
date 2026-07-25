"""Containment-safe, byte-lossless local reversible store (088.001-T).

Backed by SQLite under the resolver-anchored store root. Handles are
content-derived (deterministic — no timestamps/mutable counters), so
identical content always maps to the same handle across puts, which keeps
placeholders stable for prompt caching.
"""

import hashlib
import sqlite3
import time

from brainspace import config
from brainspace.codec import decode_lossless, encode_lossless
from brainspace.resolver import resolve_store_root


class BrainspaceStore:
    """A TTL- and size-capped local store for exact raw tool outputs."""

    def __init__(self, workspace_root, ttl_seconds=None, max_size_bytes=None):
        self._root = resolve_store_root(workspace_root)
        self._ttl_seconds = (
            config.DEFAULT_TTL_SECONDS if ttl_seconds is None else ttl_seconds
        )
        self._max_size_bytes = (
            config.DEFAULT_MAX_STORE_SIZE_BYTES
            if max_size_bytes is None
            else max_size_bytes
        )
        db_path = self._root / config.STORE_DB_FILENAME
        self._conn = sqlite3.connect(str(db_path))
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS entries ("
            " handle TEXT PRIMARY KEY,"
            " content BLOB NOT NULL,"
            " size_bytes INTEGER NOT NULL,"
            " stored_at REAL NOT NULL"
            ")"
        )
        self._conn.commit()

    @property
    def root(self):
        return self._root

    @staticmethod
    def compute_handle(text: str) -> str:
        """Deterministic content-derived handle (no timestamps/counters)."""
        digest = hashlib.sha256(encode_lossless(text)).hexdigest()
        return digest[:16]

    def put(self, text: str) -> str:
        """Durably store ``text`` and return its deterministic handle."""
        handle = self.compute_handle(text)
        blob = encode_lossless(text)
        size = len(blob)
        now = time.time()
        self._conn.execute(
            "INSERT OR REPLACE INTO entries (handle, content, size_bytes, stored_at) "
            "VALUES (?, ?, ?, ?)",
            (handle, blob, size, now),
        )
        self._conn.commit()
        self._enforce_size_cap()
        return handle

    def get(self, handle: str):
        """Return the byte-equivalent original, or None if missing/expired."""
        row = self._conn.execute(
            "SELECT content, stored_at FROM entries WHERE handle = ?", (handle,)
        ).fetchone()
        if row is None:
            return None
        content, stored_at = row
        if self._ttl_seconds is not None and (time.time() - stored_at) > self._ttl_seconds:
            self.delete(handle)
            return None
        return decode_lossless(content)

    def delete(self, handle: str) -> None:
        self._conn.execute("DELETE FROM entries WHERE handle = ?", (handle,))
        self._conn.commit()

    def purge_expired(self) -> int:
        """Delete all entries older than the configured TTL. Returns count."""
        if self._ttl_seconds is None:
            return 0
        cutoff = time.time() - self._ttl_seconds
        cur = self._conn.execute("DELETE FROM entries WHERE stored_at < ?", (cutoff,))
        self._conn.commit()
        return cur.rowcount

    def purge_all(self) -> None:
        """Remove every row — used by the purge command and session-end cleanup."""
        self._conn.execute("DELETE FROM entries")
        self._conn.commit()
        # SQLite checkpoint/compaction guidance: reclaim WAL/free pages so a
        # purge actually shrinks on-disk size rather than leaving free pages.
        self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        self._conn.execute("VACUUM")

    def row_count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]

    def total_size_bytes(self) -> int:
        result = self._conn.execute("SELECT COALESCE(SUM(size_bytes), 0) FROM entries").fetchone()
        return result[0]

    def _enforce_size_cap(self) -> None:
        """Evict oldest entries first until total size is within the cap."""
        while self.total_size_bytes() > self._max_size_bytes:
            oldest = self._conn.execute(
                "SELECT handle FROM entries ORDER BY stored_at ASC LIMIT 1"
            ).fetchone()
            if oldest is None:
                break
            self.delete(oldest[0])

    def close(self) -> None:
        self._conn.close()
