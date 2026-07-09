"""Pre-execution T-shirt sizing gate (task 055.003-T / design-doc U10).

When a task has no size, this module deterministically estimates a T-shirt size
(XS..XL) from the task's own metadata and writes it back through the external
``backlogit update <task_id> --size <result>`` CLI. An existing size is never
overwritten.

Design constraints (phase-2 plan, ProposedAction A3, MEDIUM risk):

* The estimator is a pure, reproducible function of the task metadata and the
  pinned :data:`SIZING_RULESET_VERSION` -- it is **not** a live model call, so the
  same task always yields the same size.
* The write-back invokes an external command as an argv array with
  ``shell=False``. The array is built with a fixed number of elements, so an
  interpolated value (a task id) always lands inside exactly one argv element and
  can never change argv arity or spawn a second command.
* A missing ``backlogit`` binary, a command timeout, or a backlogit validation
  error is a CONFIGURATION failure, never a task failure: the gate degrades
  gracefully, reports an actionable message, and never raises.

Boundary: this module depends only on the Python standard library. It must not
reach into install/tune surfaces or other gate modules, so the sizing gate can
evolve independently.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SIZING_RULESET_VERSION = "1.0.0"
SIZES = ("XS", "S", "M", "L", "XL")
DEFAULT_BACKLOGIT = "backlogit"

# Bound every external backlogit call so a hung or stuck binary can never wedge
# the pre-execution gate. A timeout degrades to a non-blocking config error.
_COMMAND_TIMEOUT_SECONDS = 30

# Keywords that raise (complexity) or lower (simplicity) the estimated size. The
# tuples are pinned to keep the estimate reproducible across runs. Matching is
# word/phrase-boundary aware (see :func:`_keyword_present`) so a keyword never
# matches inside an unrelated word (e.g. "typo" must not match "typography").
_COMPLEXITY_KEYWORDS = (
    "schema",
    "migration",
    "cross-cutting",
    "concurrency",
    "security",
    "architecture",
    "protocol",
    "breaking",
    "refactor",
    "distributed",
    "multi-repo",
    "monorepo",
)
_SIMPLICITY_KEYWORDS = (
    "typo",
    "rename",
    "wording",
    "copy-edit",
    "copyedit",
    "docstring",
)

_WORDS_PER_POINT = 40


# ---------------------------------------------------------------------------
# Signal extraction
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SizingSignals:
    """The metadata signals extracted from a task, used by the estimator."""

    title: str = ""
    description: str = ""
    acceptance: str = ""
    references: tuple[str, ...] = ()
    labels: tuple[str, ...] = ()


def _section(body: str, name: str) -> str:
    match = re.search(
        rf"<!--\s*BEGIN:{re.escape(name)}\s*-->(.*?)<!--\s*END:{re.escape(name)}\s*-->",
        body,
        flags=re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def _str_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value)


def _keyword_present(text: str, keyword: str) -> bool:
    """True when ``keyword`` appears as a whole word/phrase in ``text``.

    Boundaries are non-word characters, so ``typo`` does not match
    ``typography`` and hyphenated phrases like ``cross-cutting`` match only when
    standalone.
    """
    return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text) is not None


def _count_keywords(text: str, keywords: tuple[str, ...]) -> int:
    return sum(1 for kw in keywords if _keyword_present(text, kw))


def _count_ac_bullets(acceptance: str) -> int:
    """Count discrete acceptance criteria.

    Prefers explicit markdown bullet/numbered lines; falls back to ``1`` for a
    non-empty unbulleted acceptance block so a single prose criterion still
    counts once instead of once-per-wrapped-line.
    """
    lines = [line.strip() for line in acceptance.splitlines() if line.strip()]
    if not lines:
        return 0
    bullets = sum(1 for line in lines if re.match(r"^([-*+]|\d+[.)])\s+", line))
    return bullets if bullets else 1


def extract_signals(task: Mapping[str, Any]) -> SizingSignals:
    """Pull the sizing-relevant signals out of a backlogit-shaped task mapping."""
    body = task.get("body")
    body = body if isinstance(body, str) else ""

    raw_title = task.get("title")
    title = raw_title if isinstance(raw_title, str) else ""

    description = _section(body, "description")
    if not description:
        raw = task.get("description")
        description = raw if isinstance(raw, str) else ""

    acceptance = _section(body, "acceptance-criteria")
    if not acceptance:
        raw = task.get("acceptance_criteria")
        acceptance = raw if isinstance(raw, str) else ""

    return SizingSignals(
        title=title,
        description=description,
        acceptance=acceptance,
        references=_str_tuple(task.get("references")),
        labels=_str_tuple(task.get("labels")),
    )


# ---------------------------------------------------------------------------
# Deterministic estimator
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SizeEstimate:
    """A deterministic T-shirt size plus the score and signals that produced it."""

    size: str
    score: int
    signals: dict[str, int] = field(default_factory=dict)
    ruleset_version: str = SIZING_RULESET_VERSION


def _bucket(score: int) -> str:
    if score <= 1:
        return "XS"
    if score <= 4:
        return "S"
    if score <= 8:
        return "M"
    if score <= 13:
        return "L"
    return "XL"


def estimate_size(task: Mapping[str, Any]) -> SizeEstimate:
    """Estimate a T-shirt size for ``task``. Pure and reproducible."""
    sig = extract_signals(task)
    text = f"{sig.title}\n{sig.description}\n{sig.acceptance}".lower()

    words = len(text.split())
    word_points = words // _WORDS_PER_POINT
    ref_points = len(sig.references) * 2
    ac_bullets = _count_ac_bullets(sig.acceptance)
    label_points = max(0, len(sig.labels) - 1)
    complexity_points = _count_keywords(text, _COMPLEXITY_KEYWORDS) * 2
    simplicity_points = _count_keywords(text, _SIMPLICITY_KEYWORDS)

    score = max(
        0,
        word_points + ref_points + ac_bullets + label_points + complexity_points - simplicity_points,
    )
    signals = {
        "words": words,
        "word_points": word_points,
        "references": len(sig.references),
        "ref_points": ref_points,
        "acceptance_criteria": ac_bullets,
        "ac_points": ac_bullets,
        "labels": len(sig.labels),
        "label_points": label_points,
        "complexity_points": complexity_points,
        "simplicity_points": simplicity_points,
    }
    return SizeEstimate(size=_bucket(score), score=score, signals=signals)


# ---------------------------------------------------------------------------
# Safe write-back
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SizingResult:
    """The outcome of running the sizing gate against one task."""

    task_id: str
    existing_size: str | None
    estimated_size: str | None
    action: str  # "written" | "skipped-existing" | "dry-run" | "error"
    argv: tuple[str, ...] = ()
    exit_code: int | None = None
    stderr: str = ""
    missing_binary: bool = False
    ruleset_version: str = SIZING_RULESET_VERSION

    @property
    def ok(self) -> bool:
        """True when the gate reached a safe, non-failing outcome."""
        return self.action in ("written", "skipped-existing", "dry-run")

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "existing_size": self.existing_size,
            "estimated_size": self.estimated_size,
            "action": self.action,
            "argv": list(self.argv),
            "exit_code": self.exit_code,
            "stderr": self.stderr,
            "missing_binary": self.missing_binary,
            "ruleset_version": self.ruleset_version,
            "ok": self.ok,
        }


def _existing_size(task: Mapping[str, Any]) -> str | None:
    value = task.get("size")
    if isinstance(value, str) and value.strip():
        return value.strip()
    custom = task.get("custom_fields")
    if isinstance(custom, Mapping):
        cv = custom.get("size")
        if isinstance(cv, str) and cv.strip():
            return cv.strip()
    return None


def _missing_binary_message(binary: str) -> str:
    return (
        f"sizing gate configuration error: command binary '{binary}' was not found. "
        f"Install it or point --backlogit at the executable. This is a configuration "
        f"failure, not a task failure; task execution is not blocked."
    )


def fetch_task(
    task_id: str,
    cwd: "Path | None" = None,
    backlogit_bin: str = DEFAULT_BACKLOGIT,
) -> dict[str, Any]:
    """Default task fetcher: ``backlogit get <id> --format json`` -> mapping."""
    argv = [backlogit_bin, "get", task_id, "--format", "json"]
    proc = subprocess.run(
        argv,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        shell=False,
        timeout=_COMMAND_TIMEOUT_SECONDS,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or "").strip() or f"backlogit get {task_id} failed")
    return json.loads(proc.stdout)


def size_task(
    task_id: str,
    *,
    fetch_fn: "Callable[[str, Path | None], Mapping[str, Any]]",
    run_fn: "Callable[..., Any] | None" = None,
    cwd: "Path | None" = None,
    dry_run: bool = False,
    backlogit_bin: str = DEFAULT_BACKLOGIT,
) -> SizingResult:
    """Estimate and (unless a size exists) write back a task's T-shirt size.

    Never raises and never blocks task execution: a fetch failure, a timeout, a
    missing binary, or a backlogit rejection all resolve to an ``error`` result
    carrying an actionable message.

    The "do not overwrite an existing size" guarantee is best-effort: the fetch
    and the write-back are separate backlogit calls (backlogit exposes no
    conditional/compare-and-set mutation), so a concurrent writer between the two
    steps is theoretically possible. In the single-threaded pre-execution gate
    this race does not occur in practice.
    """
    try:
        task = fetch_fn(task_id, cwd)
    except FileNotFoundError:
        return SizingResult(
            task_id, None, None, "error",
            missing_binary=True, stderr=_missing_binary_message(backlogit_bin),
        )
    except Exception as exc:  # noqa: BLE001 - degrade gracefully on any fetch error
        return SizingResult(
            task_id, None, None, "error",
            stderr=f"failed to fetch task {task_id}: {exc}",
        )

    if not isinstance(task, Mapping):
        return SizingResult(
            task_id, None, None, "error",
            stderr=f"task {task_id} fetch returned a non-mapping value",
        )

    existing = _existing_size(task)
    if existing is not None:
        return SizingResult(task_id, existing, None, "skipped-existing")

    estimate = estimate_size(task)
    argv = [backlogit_bin, "update", task_id, "--size", estimate.size]

    if dry_run:
        return SizingResult(task_id, None, estimate.size, "dry-run", argv=tuple(argv))

    run = run_fn or subprocess.run
    try:
        proc = run(
            argv,
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            shell=False,
            timeout=_COMMAND_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        return SizingResult(
            task_id, None, estimate.size, "error",
            argv=tuple(argv), missing_binary=True,
            stderr=_missing_binary_message(backlogit_bin),
        )
    except subprocess.TimeoutExpired:
        return SizingResult(
            task_id, None, estimate.size, "error",
            argv=tuple(argv),
            stderr=(
                f"backlogit update timed out after {_COMMAND_TIMEOUT_SECONDS}s. "
                f"Configuration failure, not a task failure; task execution is not blocked."
            ),
        )
    except OSError as exc:
        return SizingResult(
            task_id, None, estimate.size, "error",
            argv=tuple(argv), stderr=str(exc),
        )

    stderr = (getattr(proc, "stderr", "") or "").strip()
    if proc.returncode != 0:
        return SizingResult(
            task_id, None, estimate.size, "error",
            argv=tuple(argv), exit_code=proc.returncode, stderr=stderr,
        )
    return SizingResult(
        task_id, None, estimate.size, "written",
        argv=tuple(argv), exit_code=proc.returncode, stderr=stderr,
    )
