"""Gate feedback, policy enforcement, and the structured correction report.

This module folds the completion-path feedback loop (CD0EFDF3) and the gate
policy engine (feature 050.008) on top of the atomic gate report produced by
:mod:`autoharness.gates.gate`.

Policy enforced here (Phase 1 only — NO telemetry DB/epoch/JSONL, which is
Phase 2 / P3-1):

* ``enforcement: absolute | advisory`` — advisory failures warn but never block.
  A gate may override the block-level policy via its own ``enforcement`` field.
* ``on_repeated_failure: block | escalate`` + ``max_gate_failures`` (default 3,
  aligned with ``MAXIMUM_RETRY_THRESHOLD=3`` in the circuit-breaker
  instructions). On the Nth consecutive blocking failure for a task the gate
  requeues the task and writes a ``docs/memory/`` circuit-breaker checkpoint.
* ``--force`` — an operator-only bypass. It is never reachable from an agent
  surface, and every use is audited (P-005 telemetry style) to a plain log
  under ``.autoharness/`` AND echoed in the correction report.

This module depends only on other ``gates.*`` modules (Plan Review P2-2).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from autoharness.gates.config import GatePolicy
from autoharness.gates.gate import GateCheckReport
from autoharness.gates.runner import GateResult

# Enforcement / policy vocabulary (mirrors the validation-gates JSON Schema).
ABSOLUTE = "absolute"
ADVISORY = "advisory"
BLOCK = "block"
ESCALATE = "escalate"

# Outcome status values.
STATUS_PASSED = "passed"
STATUS_ADVISORY = "advisory"
STATUS_BLOCKED = "blocked"
STATUS_BLOCKED_REQUEUE = "blocked-requeue"
STATUS_ESCALATE = "escalate"
STATUS_FORCED = "forced"


@dataclass(frozen=True)
class GateOutcome:
    """The policy decision derived from a :class:`GateCheckReport`."""

    status: str
    exit_code: int
    blocked: bool
    consecutive_failures: int = 0
    requeue: bool = False
    escalate: bool = False
    forced: bool = False
    checkpoint_path: str | None = None
    messages: tuple[str, ...] = field(default_factory=tuple)


def _effective_enforcement(result: GateResult, policy: GatePolicy) -> str:
    """A failing gate blocks unless it (or the block policy) is advisory."""
    return result.enforcement or policy.enforcement or ABSOLUTE


def _state_path(workspace: Path) -> Path:
    return Path(workspace) / ".autoharness" / "gate-state.json"


def _read_state(workspace: Path) -> dict:
    path = _state_path(workspace)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_state(workspace: Path, state: dict) -> None:
    path = _state_path(workspace)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def _consecutive_key(task_id: str | None) -> str:
    return task_id or "<no-task>"


def _now(clock: Callable[[], datetime] | None) -> datetime:
    return (clock or (lambda: datetime.now(timezone.utc)))()


def _audit_force(workspace: Path, task_id: str | None, report: GateCheckReport, when: datetime) -> str:
    """Append a P-005-style audit line for an operator --force bypass."""
    audit_path = Path(workspace) / ".autoharness" / "gate-force-audit.log"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    failed = ", ".join(sorted({r.file for r in report.failures})) or "<none>"
    line = (
        f"{when.isoformat()} FORCE_BYPASS task={_consecutive_key(task_id)} "
        f"blocked_files=[{failed}] failures={len(report.failures)}\n"
    )
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(line)
    return str(audit_path)


def _write_checkpoint(
    workspace: Path,
    task_id: str | None,
    report: GateCheckReport,
    attempts: int,
    when: datetime,
) -> str:
    """Write a circuit-breaker checkpoint per circuit-breaker.instructions.md."""
    slug = (task_id or "unknown-task").replace("/", "-").replace(" ", "-")
    date_dir = Path(workspace) / "docs" / "memory" / when.strftime("%Y-%m-%d")
    date_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = date_dir / f"circuit-break-gate-{slug}.md"

    lines = [
        "---",
        "type: circuit-breaker",
        f"timestamp: {when.isoformat()}",
        "agent: ship",
        "skill: gate-check",
        "breaker_type: skill-managed",
        f"operation: validation gate check for task {_consecutive_key(task_id)}",
        f"attempts: {attempts}",
        "---",
        "",
        "## Failure Chain",
        "",
        f"The pre_task_completion validation gate failed {attempts} consecutive "
        "times for the same task, reaching `max_gate_failures`. The task has been "
        "requeued for rework.",
        "",
        "## Failing Files",
        "",
    ]
    for result in report.failures:
        reason = result.failure_reason or "nonzero-exit"
        exit_code = "None" if result.exit_code is None else str(result.exit_code)
        lines.append(f"- `{result.file}` — {reason} (exit={exit_code}, pattern=`{result.pattern}`)")
        stderr = (result.stderr or "").strip()
        if stderr:
            first_line = stderr.splitlines()[0]
            lines.append(f"  - stderr: {first_line}")
    lines += [
        "",
        "## Context",
        "",
        f"- Files involved: {len(report.failures)} failing gate(s)",
        "- Resolution: Circuit breaker triggered. Task requeued for rework.",
        "- Suggested next steps: Fix the failing files, then re-run "
        "`autoharness gate check`.",
        "",
    ]
    checkpoint.write_text("\n".join(lines), encoding="utf-8")
    return str(checkpoint)


def enforce(
    report: GateCheckReport,
    policy: GatePolicy,
    *,
    task_id: str | None = None,
    workspace: Path | str = ".",
    force: bool = False,
    clock: Callable[[], datetime] | None = None,
) -> GateOutcome:
    """Apply gate policy to a report and return the enforcement outcome.

    * All-pass (no failures) ⇒ ``passed`` (exit 0), consecutive counter reset.
    * Failures that are all advisory ⇒ ``advisory`` (exit 0, warn only).
    * At least one blocking (absolute) failure ⇒ block (exit 1) and increment the
      per-task consecutive-failure counter. On reaching ``max_gate_failures`` the
      task is requeued (or escalated) and a checkpoint is written.
    * ``force`` on a blocking report ⇒ ``forced`` (exit 0), counter reset, audited.
    """
    workspace_path = Path(workspace)
    when = _now(clock)
    key = _consecutive_key(task_id)

    # No failures: success. Reset the consecutive counter for this task.
    if not report.failures:
        state = _read_state(workspace_path)
        if state.get(key):
            state[key] = 0
            _write_state(workspace_path, state)
        return GateOutcome(status=STATUS_PASSED, exit_code=0, blocked=False)

    blocking = [r for r in report.failures if _effective_enforcement(r, policy) == ABSOLUTE]

    # All failures advisory: warn but do not block, and do not count toward the
    # circuit breaker.
    if not blocking:
        messages = (
            f"{len(report.failures)} advisory gate finding(s) — not blocking.",
        )
        return GateOutcome(
            status=STATUS_ADVISORY,
            exit_code=0,
            blocked=False,
            messages=messages,
        )

    # Operator force bypass. Reset the counter and audit the bypass.
    if force:
        audit_path = _audit_force(workspace_path, task_id, report, when)
        state = _read_state(workspace_path)
        state[key] = 0
        _write_state(workspace_path, state)
        return GateOutcome(
            status=STATUS_FORCED,
            exit_code=0,
            blocked=True,
            forced=True,
            messages=(
                f"OPERATOR FORCE BYPASS applied to {len(blocking)} blocking "
                f"gate failure(s). Audited to {audit_path}.",
            ),
        )

    # Blocking failure. Increment the consecutive counter for this task.
    state = _read_state(workspace_path)
    attempts = int(state.get(key, 0)) + 1
    state[key] = attempts
    _write_state(workspace_path, state)

    limit = max(1, int(policy.max_gate_failures))
    if attempts >= limit:
        checkpoint_path = _write_checkpoint(workspace_path, task_id, report, attempts, when)
        if policy.on_repeated_failure == ESCALATE:
            return GateOutcome(
                status=STATUS_ESCALATE,
                exit_code=1,
                blocked=True,
                consecutive_failures=attempts,
                escalate=True,
                checkpoint_path=checkpoint_path,
                messages=(
                    f"Gate failed {attempts} consecutive times "
                    f"(max_gate_failures={limit}); escalating. "
                    f"Checkpoint: {checkpoint_path}.",
                ),
            )
        return GateOutcome(
            status=STATUS_BLOCKED_REQUEUE,
            exit_code=1,
            blocked=True,
            consecutive_failures=attempts,
            requeue=True,
            checkpoint_path=checkpoint_path,
            messages=(
                f"Gate failed {attempts} consecutive times "
                f"(max_gate_failures={limit}); requeuing task for rework. "
                f"Checkpoint: {checkpoint_path}.",
            ),
        )

    return GateOutcome(
        status=STATUS_BLOCKED,
        exit_code=1,
        blocked=True,
        consecutive_failures=attempts,
        messages=(
            f"{len(blocking)} gate failure(s) blocked task completion "
            f"(attempt {attempts}/{limit}).",
        ),
    )


def _result_dict(result: GateResult) -> dict:
    return {
        "file": result.file,
        "pattern": result.pattern,
        "command": result.command,
        "exit_code": result.exit_code,
        "stderr": result.stderr,
        "duration": round(result.duration, 4),
        "passed": result.passed,
        "failure_reason": result.failure_reason,
        "enforcement": result.enforcement,
    }


def build_correction_report(
    report: GateCheckReport,
    outcome: GateOutcome,
    *,
    emit_json: bool = False,
) -> str:
    """Build a per-file pass/fail + stderr correction report.

    Enumerates every matched file's exit code and stderr so an agent can act on
    the feedback deterministically. JSON mode returns a machine-readable object.
    """
    if emit_json:
        payload = {
            "status": outcome.status,
            "exit_code": outcome.exit_code,
            "blocked": outcome.blocked,
            "requeue": outcome.requeue,
            "escalate": outcome.escalate,
            "forced": outcome.forced,
            "consecutive_failures": outcome.consecutive_failures,
            "checkpoint_path": outcome.checkpoint_path,
            "messages": list(outcome.messages),
            "matched_files": list(report.matched_files),
            "results": [_result_dict(r) for r in report.results],
        }
        return json.dumps(payload, indent=2, sort_keys=True)

    lines: list[str] = []
    lines.append(f"Gate check: {outcome.status.upper()} (exit {outcome.exit_code})")
    if not report.results:
        lines.append("No files matched any configured gate; nothing to validate.")
        return "\n".join(lines)

    passed = [r for r in report.results if r.passed]
    failed = [r for r in report.results if not r.passed]
    lines.append(f"Matched {len(report.matched_files)} file(s): {len(passed)} passed, {len(failed)} failed.")
    lines.append("")

    for result in report.results:
        status = "PASS" if result.passed else "FAIL"
        exit_code = "None" if result.exit_code is None else str(result.exit_code)
        lines.append(f"[{status}] {result.file}  (pattern={result.pattern}, exit={exit_code})")
        if not result.passed:
            reason = result.failure_reason or "nonzero-exit"
            lines.append(f"       reason: {reason}")
            stderr = (result.stderr or "").strip()
            if stderr:
                for stderr_line in stderr.splitlines():
                    lines.append(f"       | {stderr_line}")

    if outcome.messages:
        lines.append("")
        for message in outcome.messages:
            lines.append(message)

    return "\n".join(lines)
