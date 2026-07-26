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


class StoreCapacityError(Exception):
    """Raised when a single put's content cannot be retained under the cap.

    ``BrainspaceStore._enforce_size_cap`` evicts oldest-first until the
    total store size is within the configured cap; if the content just
    inserted by this ``put()`` call is itself evicted (e.g. a single output
    larger than the whole cap), ``put()`` must not hand back a handle whose
    row no longer exists -- a caller writing a retrieval footer around a
    dangling handle would point at unretrievable content. Raising here lets
    the hook's existing fail-safe wrapper pass the original through
    byte-identically instead.
    """


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
        # Explicit WAL journal mode: keeps the on-disk sidecar set limited to
        # the two guarded/gitignored WAL-mode files (-wal/-shm) instead of
        # SQLite's default rollback-journal mode, which can leave a
        # crash-time -journal file containing raw output. The staged-file
        # guard and .gitignore also cover -journal defensively in case a
        # filesystem falls back to rollback mode (e.g. no shared-memory
        # locking support), but WAL mode is the primary containment control.
        self._conn.execute("PRAGMA journal_mode=WAL")
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
        """Durably store ``text`` and return its deterministic handle.

        Dedup is a no-op on ``stored_at`` for a LIVE (non-expired) existing
        row: since ``handle`` is a content-derived hash, re-putting
        identical content never changes what is stored, so the TTL clock
        must not be silently extended by repeated access.

        If the existing row is ALREADY expired, a re-put of identical
        content refreshes ``stored_at`` (delete-then-insert) instead of
        silently returning a handle whose row the very next ``get()``
        would delete as expired.

        Raises ``StoreCapacityError`` instead of returning a handle whose
        row ``_enforce_size_cap`` evicted immediately (e.g. a single put
        larger than the whole cap) -- callers must never receive a
        dangling handle.
        """
        handle = self.compute_handle(text)
        blob = encode_lossless(text)
        size = len(blob)
        now = time.time()

        existing = self._conn.execute(
            "SELECT stored_at FROM entries WHERE handle = ?", (handle,)
        ).fetchone()
        is_expired = existing is not None and (
            self._ttl_seconds is not None
            and (now - existing[0]) > self._ttl_seconds
        )
        if existing is None or is_expired:
            if is_expired:
                # Refresh: delete the stale (expired) row before
                # re-inserting so stored_at reflects this new put.
                self._conn.execute("DELETE FROM entries WHERE handle = ?", (handle,))
            self._conn.execute(
                "INSERT OR IGNORE INTO entries "
                "(handle, content, size_bytes, stored_at) VALUES (?, ?, ?, ?)",
                (handle, blob, size, now),
            )
            self._conn.commit()
        # else: live (non-expired) dedup -- leave the existing row and its
        # original stored_at untouched, never silently extending the TTL.

        self._enforce_size_cap()

        still_present = self._conn.execute(
            "SELECT 1 FROM entries WHERE handle = ?", (handle,)
        ).fetchone()
        if still_present is None:
            raise StoreCapacityError(
                f"content ({size} bytes) could not be retained under the "
                f"{self._max_size_bytes}-byte store cap; evicted immediately "
                "on insert"
            )
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
            self._delete_if_still_expired(handle, stored_at)
            return None
        return decode_lossless(content)

    def _delete_if_still_expired(self, handle: str, stored_at: float) -> None:
        """Delete ``handle`` only if its row's ``stored_at`` still matches
        the value just read as expired (P-018 round-9 finding).

        Handles are content-derived, so a concurrent ``put()`` refreshing
        identical content between this method's caller reading the row and
        this delete would give the row a NEW ``stored_at``. An unconditional
        ``DELETE ... WHERE handle = ?`` would remove that freshly-refreshed
        row out from under the concurrent writer, leaving its already-issued
        handle dangling. Keying the delete on the stale ``stored_at`` value
        makes it a no-op whenever a refresh has already happened, so the
        refreshed row survives.
        """
        self._conn.execute(
            "DELETE FROM entries WHERE handle = ? AND stored_at = ?",
            (handle, stored_at),
        )
        self._conn.commit()

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
