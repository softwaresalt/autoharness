"""Temporary git repository fixture shared by the docs-only route tests (216-F)."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

BACKLOG = ".backlogit"
DOCS = "docs"


def _env() -> dict[str, str]:
    drop = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE")
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_CONFIG") and k not in drop}


class TempRepo:
    """A throwaway git repository with one initial commit."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")
        self.git("config", "core.autocrlf", "false")
        self.write("README.md", "readme\n")
        self.commit_all("init")

    def cleanup(self) -> None:
        self._tmp.cleanup()

    def git(self, *args: str) -> str:
        done = subprocess.run(
            ["git", "-C", str(self.root), *args], capture_output=True, env=_env(), check=True, text=True
        )
        return done.stdout

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def commit_all(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", message)
        return self.head()

    def head(self) -> str:
        return self.git("rev-parse", "HEAD").strip()


def item_text(
    item_id: str,
    *,
    status: str = "queued",
    labels: tuple[str, ...] = (),
    body: str = "body\n",
    extra: str = "",
    items: tuple[str, ...] = (),
    updated: str = "2026-01-01T00:00:00Z",
) -> str:
    """Render a backlog item file."""
    lines = ["---", f"id: {item_id}", f"status: {status}", f"updated_at: {updated}"]
    if labels:
        lines.append("labels:")
        lines.extend(f"    - {label}" for label in labels)
    if items:
        lines.append("custom_fields:")
        lines.append("    items:")
        lines.extend(f"        - {member}" for member in items)
    if extra:
        lines.append(extra)
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body
