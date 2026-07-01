"""JSONL epoch sink — emit-only (Phase 2, U4, task 051.006).

Appends each :class:`~autoharness.telemetry.epoch.ExecutionEpoch` as exactly one
well-formed JSON object per line to the configured JSONL path (default alongside
the SQLite DB under ``.autoharness/metrics/``).

**Emit-only boundary:** this sink stops at the file. The external relational
schema and the ingestion path that consumes this stream are an agent-engram
concern (design §4) and are intentionally NOT implemented here.
"""

from __future__ import annotations

import json
from pathlib import Path

from autoharness.telemetry.epoch import ExecutionEpoch


def append_epoch(epoch: ExecutionEpoch, jsonl_path: Path) -> None:
    """Append one epoch as a single JSON line, preserving existing lines."""
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(epoch.to_record(), ensure_ascii=False, sort_keys=True)
    with jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
