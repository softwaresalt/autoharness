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
    parent_id: str = "",
) -> str:
    """Render a backlog item file."""
    lines = ["---", f"id: {item_id}", f"status: {status}", f"updated_at: {updated}"]
    if parent_id:
        lines.append(f"parent_id: {parent_id}")
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


class ShipmentRepo(TempRepo):
    """A repository holding one shipment, its feature and two docs-route tasks."""

    SHIPMENT = "900-S"
    FEATURE = "900-F"
    TASKS = ("900.001-T", "900.002-T")

    def __init__(self) -> None:
        super().__init__()
        self.members = (self.FEATURE, *self.TASKS)
        self.state: dict[str, dict] = {
            item: {"status": "queued", "labels": (), "body": f"body of {item}\n", "extra": "", "updated": "2026-01-01T00:00:00Z"}
            for item in (self.SHIPMENT, *self.members)
        }
        for item in self.state:
            self.save(item)
        self.write("docs/a.md", "a\n")
        self.write("docs/b.md", "b\n")
        self.write("docs/memory/keep.md", "keep\n")
        self.write("src/mod.py", "x = 1\n")
        self.write(f"{BACKLOG}/stash.jsonl", "{}\n")
        self.write(f"{BACKLOG}/checkpoints/old.json", "{}\n")
        self.write(f"{BACKLOG}/queue/777-T.md", item_text("777-T"))
        self.commit_all("seed shipment")

    def path_of(self, item: str) -> str:
        return f"{BACKLOG}/queue/{item}.md"

    def save(self, item: str, **changes) -> None:
        self.state[item].update(changes)
        kwargs = dict(self.state[item])
        text = item_text(
            item,
            status=kwargs["status"],
            labels=tuple(kwargs["labels"]),
            body=kwargs["body"],
            extra=kwargs["extra"],
            items=self.members if item == self.SHIPMENT else (),
            updated=kwargs["updated"],
            parent_id=self.FEATURE if item in self.TASKS else "",
        )
        self.write(self.path_of(item), text)

    def claim_all(self) -> None:
        for item in (self.SHIPMENT, *self.members):
            self.save(item, status="active", updated="2026-02-01T00:00:00Z")

    def add_label(self, item: str, label: str = "harness-verification-gated") -> None:
        self.save(item, labels=(*self.state[item]["labels"], label))

    def close_out(self, item: str, message: str, docs: tuple[str, ...]) -> None:
        """Commit the task's docs edit and its own file; claim writes and session memory stay dirty."""
        self.write("docs/memory/session.md", f"memory after {item}\n")
        self.save(item, status="done", updated="2026-03-01T00:00:00Z", extra="commit: abc")
        self.git("add", "--", self.path_of(item), *docs)
        self.git("commit", "-q", "-m", message)
