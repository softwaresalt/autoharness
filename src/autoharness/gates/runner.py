"""Injection-safe subprocess gate runner.

Executes an interpolated gate ``command`` per matched file with a hard timeout,
capturing the outcome into the shared :class:`GateResult` dataclass.

Security invariant (Plan Hardening A1): the command template is tokenized into an
argv array *before* any placeholder substitution, and each ``{file_path}`` is
substituted into a single, pre-existing argv token. Therefore the number of argv
elements is fixed by the operator-authored template and can never be changed by
the *content* of a matched file path. Execution always uses ``shell=False`` — a
crafted path containing ``;``, ``&&``, ``$(...)`` or backticks is passed inertly
as a single argument and cannot spawn a second command.
"""

from __future__ import annotations

import re
import shlex
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from autoharness.gates.config import ValidationGate

_PLACEHOLDER_RE = re.compile(r"\{([a-z_]+)\}")
_ALLOWED_PLACEHOLDERS = frozenset({"file_path", "task_id", "result"})


@dataclass(frozen=True)
class GateResult:
    """The outcome of running one gate against one file (shared T5/T6/T8 type)."""

    file: str
    pattern: str
    command: str
    exit_code: int | None
    stderr: str
    duration: float
    timed_out: bool = False
    missing_binary: bool = False
    enforcement: str | None = None
    argv: tuple[str, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return (
            self.exit_code == 0
            and not self.timed_out
            and not self.missing_binary
        )

    @property
    def failure_reason(self) -> str | None:
        if self.passed:
            return None
        if self.missing_binary:
            return "missing-binary"
        if self.timed_out:
            return "timeout"
        return "nonzero-exit"


def _interpolate_token(token: str, values: dict[str, str]) -> str:
    def repl(match: "re.Match[str]") -> str:
        name = match.group(1)
        if name in values:
            return values[name]
        # Unknown placeholders are rejected by the schema; leave literal here.
        return match.group(0)

    return _PLACEHOLDER_RE.sub(repl, token)


def build_argv(command_template: str, values: dict[str, str]) -> list[str]:
    """Tokenize the template, then substitute placeholders per-token.

    Tokenization happens first so a substituted value (e.g. a file path) always
    lands inside exactly one argv element and cannot alter argv arity.
    """
    tokens = shlex.split(command_template, posix=True)
    if not tokens:
        raise ValueError("gate command is empty after tokenization")
    return [_interpolate_token(tok, values) for tok in tokens]


def run_gate(
    gate: ValidationGate,
    file_path: str,
    *,
    task_id: str | None = None,
    cwd: Path | None = None,
    run_fn: Callable[..., Any] | None = None,
) -> GateResult:
    """Run a single gate command against ``file_path`` and capture the result."""
    values: dict[str, str] = {"file_path": file_path}
    if task_id is not None:
        values["task_id"] = task_id

    argv = build_argv(gate.command, values)
    run = run_fn or subprocess.run

    start = time.monotonic()
    try:
        proc = run(
            argv,
            cwd=str(cwd) if cwd is not None else None,
            capture_output=True,
            text=True,
            timeout=gate.timeout_seconds,
            shell=False,
        )
    except FileNotFoundError:
        duration = time.monotonic() - start
        return GateResult(
            file=file_path,
            pattern=gate.pattern,
            command=gate.command,
            exit_code=None,
            stderr=(
                f"gate configuration error: command binary '{argv[0]}' was not found. "
                f"Install it or fix the gate 'command' in .autoharness/config.yaml."
            ),
            duration=duration,
            missing_binary=True,
            enforcement=gate.enforcement,
            argv=tuple(argv),
        )
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - start
        partial = exc.stderr or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", "replace")
        return GateResult(
            file=file_path,
            pattern=gate.pattern,
            command=gate.command,
            exit_code=None,
            stderr=(partial + f"\n[gate killed: exceeded timeout of {gate.timeout_seconds}s]").strip(),
            duration=duration,
            timed_out=True,
            enforcement=gate.enforcement,
            argv=tuple(argv),
        )

    duration = time.monotonic() - start
    return GateResult(
        file=file_path,
        pattern=gate.pattern,
        command=gate.command,
        exit_code=proc.returncode,
        stderr=proc.stderr or "",
        duration=duration,
        enforcement=gate.enforcement,
        argv=tuple(argv),
    )
