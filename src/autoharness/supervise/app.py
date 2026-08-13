"""The single supervisor orchestrator: run_session() (120.004-T).

Composes, in order: lock (:mod:`autoharness.supervise.locking`) -> bootstrap
(:mod:`autoharness.supervise.bootstrap`) -> sidecar preflight
(:mod:`autoharness.supervise.sidecar`) -> resolve
(:mod:`autoharness.supervise.resolve`) -> spawn (a
:class:`~autoharness.supervise.process.ChildProcess` backend) -> supervise/
drain (the :class:`~autoharness.supervise.session.SessionStateMachine`, an
:class:`~autoharness.supervise.events.EventBus`, and a
:class:`~autoharness.supervise.journal.SessionJournal`) -> cancellation
(:func:`autoharness.supervise.recovery.cancel_session`) and restart
(:class:`autoharness.supervise.recovery.RestartController`).

This module is PURE COMPOSITION (H8): every algorithm it uses -- the
lifecycle graph, the redaction choke point, the restart budget/backoff, the
lock contention/force-unlock protocol -- already exists in an earlier
shipment's module. Nothing here reimplements any of that; it only wires
those pieces together in the documented order and dispatches every gated
action through the caller-supplied ``approval_service``.

**Mandatory gated-action wiring (the entire point of this module)**:
:func:`run_session` REQUIRES an ``approval_service`` argument (no default --
see the signature below) and dispatches EVERY entry in
:data:`autoharness.supervise.contracts.GATED_ACTION_CATALOG` -- currently
exactly ``"session_restart"`` and ``"force_unlock"`` -- through
``approval_service.request_approval(identifier, ...)`` before performing the
corresponding side effect:

* ``"force_unlock"`` -- dispatched directly by this module, immediately
  before calling :func:`autoharness.supervise.locking.force_unlock`, only
  when lock acquisition was refused AND the caller opted in via
  ``force_unlock=True`` AND the on-disk record is diagnosed
  :attr:`~autoharness.supervise.locking.Liveness.STALE`
  (:func:`~autoharness.supervise.locking.is_stale_eligible_for_force_unlock`).
  A resolution other than the exact string ``"force_unlock"`` (including the
  catalog's own ``"REFUSED"`` fallback) means the side effect is skipped and
  the session resolves ``LOCKING -> REFUSED`` / ``SupervisorResult.status ==
  "blocked"``.
* ``"session_restart"`` -- dispatched INDIRECTLY, via a ``confirm_restart``
  closure handed to :class:`~autoharness.supervise.recovery.RestartController`;
  ``RestartController.attempt`` itself calls that closure (and, per its own
  documented contract, treats any exception raised by it identically to an
  explicit decline) before ever spawning a replacement child. This module
  therefore never needs its own decline-on-exception logic for this action;
  ``recovery.py`` already fails closed here (an existing, pinned S1/S2
  contract this module reuses rather than duplicates).

Any exception raised anywhere in this composition -- including one raised
by ``approval_service.request_approval`` itself -- is caught at the
top level and converted to a ``"failed"`` :class:`SupervisorResult` (H2:
fail closed, never swallow silently, never perform the gated side effect
first and fail after).

**Status vs. exit code (documented distinction)**: ``SupervisorResult.status``
describes THIS SUPERVISOR's own outcome (did the orchestration itself
complete cleanly?), never the supervised child's own exit code. A child
that exits non-zero, cleanly, with no further restart attempted (because no
restart budget was configured, or the child was not eligible for restart)
still yields ``status="ok"`` with ``exit_code`` set to that same non-zero
value, propagated VERBATIM (H3) -- this mirrors the "state-vs-call-outcome"
distinction already documented for ``sidecar.py``'s per-sidecar outcomes
versus this module's own return value.

**EventBus vs. journal coverage (documented scope)**: every phase
transition this module drives directly (``LOCKING``, ``BOOTSTRAPPING``,
``PREFLIGHT``, ``RESOLVING``, ``LAUNCHING``, ``RUNNING``, and the terminal
``DRAINING``/``EXITED``/``FAILED``/``REFUSED`` transitions it performs
itself) is emitted through BOTH the ``EventBus`` and the ``SessionJournal``.
Phase transitions driven INSIDE ``recovery.cancel_session``/
``RestartController.attempt`` (``CANCELLING``, ``RESTARTING``, and the
``DRAINING``/terminal transitions performed by those two functions) are
journaled by those functions themselves (this module passes its
``SessionJournal`` instance through to them) but are NOT separately
re-emitted on the ``EventBus`` -- recovery.py's public contract only
accepts a journal, not a bus, so duplicating those transitions here would
mean reconstructing events recovery.py already privately owns. This is a
deliberate, documented scope boundary, not an oversight.

**Cancellation trigger**: this module has no polling/signal-handling loop of
its own. It honors operator cancellation by catching a ``KeyboardInterrupt``
raised out of the blocking ``child.wait()`` call and routing it straight to
:func:`autoharness.supervise.recovery.cancel_session` (which performs the
entire ``RUNNING -> CANCELLING -> DRAINING -> CANCELLED`` sequence, child
termination, and lock release itself) -- no separate cancellation algorithm
is introduced here.
"""

from __future__ import annotations

import os
import signal as signal_module
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

from autoharness.supervise import bootstrap as bootstrap_mod
from autoharness.supervise import resolve as resolve_mod
from autoharness.supervise import sidecar as sidecar_mod
from autoharness.supervise.contracts import (
    ApprovalRequested,
    ApprovalResolved,
    ChildExited,
    ChildOutput,
    ChildSpawned,
    CopilotResolved,
    SidecarProbed,
    UseSafeDefault,
    get_gated_action,
)
from autoharness.supervise.errors import EXIT_CODE_BY_KIND, AutoharnessError, ErrorKind
from autoharness.supervise.events import EventBus
from autoharness.supervise.journal import SessionJournal
from autoharness.supervise.locking import (
    ForceUnlockOutcome,
    SessionLock,
    SessionLockRefused,
    diagnose_liveness,
    force_unlock as locking_force_unlock,
    is_stale_eligible_for_force_unlock,
    read_record,
)
from autoharness.supervise.process import ChildProcess, InheritStdioChildProcess
from autoharness.supervise.process_pty import create_pty_or_inherited_child_process
from autoharness.supervise.recovery import RestartController, cancel_session
from autoharness.supervise.result import SupervisorResult
from autoharness.supervise.session import Phase, SessionStateMachine

ChildProcessFactory = Callable[[Sequence[str]], ChildProcess]
LockFactory = Callable[[Path, Optional[str]], Any]


def _default_lock_factory(workspace_root: Path, session_id: Optional[str]) -> SessionLock:
    return SessionLock(workspace_root, session_id=session_id)


def _default_child_process_factory(
    use_pty: Optional[bool], cwd: Optional[str] = None
) -> ChildProcessFactory:
    """Build the default Copilot child-process factory, anchored to ``cwd``.

    ``cwd`` (when supplied) is forwarded to whichever backend is
    constructed -- PTY or inherited-stdio alike -- so the spawned Copilot
    child (and, by inheritance, any local stdio MCP server IT in turn
    spawns per ``.mcp.json``, e.g. Engram/graphtor-docs) resolves its own
    CWD-relative behavior against the real workspace root rather than
    whatever directory the invoking shell happened to have as its own cwd.
    This is the reinforcing half of the 120-F runtime-defect remediation:
    the actual crash was `.mcp.json`'s use of an unresolved
    ``${workspaceFolder}`` placeholder (fixed at the config level), but
    Copilot's own cwd must still be anchored for the CWD-relative defaults
    those tools fall back to once that placeholder is removed.
    """

    def factory(argv: Sequence[str]) -> ChildProcess:
        if use_pty:
            child, _warning = create_pty_or_inherited_child_process(argv, cwd=cwd)
            return child
        return InheritStdioChildProcess(argv, cwd=cwd)

    return factory


def _pump_child_output(child: ChildProcess, emit: Callable[[Any], None]) -> None:
    """Continuously drain capture-capable child output to the real console.

    Reviewer-flagged gap (P-018 Copilot review, PR #331, comment
    3777840441): the previous implementation blocked in ``child.wait()``
    without ever calling :meth:`ChildProcess.read`. For a PTY-backed child
    (``supports_output_capture`` is ``True``), nothing ever drained the
    master side of the pseudo-terminal: Copilot's own output was invisible
    to the operator, and once the PTY's kernel buffer filled a chatty
    child could block forever on its own writes. This helper runs as a
    daemon thread for the lifetime of a single child, forwarding every
    drained chunk straight through to the real ``sys.stdout`` and also
    emitting/journaling it as a :class:`ChildOutput` event so the session
    journal captures what the operator actually saw. Returns (thread
    exits) once :meth:`ChildProcess.read` reports EOF (``None``) or raises.
    """

    while True:
        try:
            data = child.read()
        except Exception:  # noqa: BLE001 - a pump thread must never raise into the interpreter
            return
        if data is None:
            return
        try:
            sys.stdout.write(data)
            sys.stdout.flush()
        except Exception:  # noqa: BLE001 - a console write failure does not stop draining the child
            pass
        emit(ChildOutput(stream="stdout", line=data))


def _pump_operator_input(child: ChildProcess) -> None:
    """Continuously forward operator keyboard input into a PTY-backed child.

    Reviewer-flagged gap (P-018 Copilot review, PR #331, comment
    3777840441): without this pump, a PTY-backed interactive session could
    never receive operator input at all -- prompts would appear to hang
    indefinitely. This forwards line-buffered input (``sys.stdin.readline``)
    to :meth:`ChildProcess.write`; it intentionally does not attempt raw,
    single-keystroke terminal forwarding (arrow-key history navigation,
    live tab-completion redraws), which would require putting the real
    terminal into raw/cbreak mode and is out of scope for this fix. Runs
    as a daemon thread so an unread line (or a stdin that never closes)
    never blocks process/interpreter shutdown once the child has exited.
    """

    while True:
        try:
            line = sys.stdin.readline()
        except Exception:  # noqa: BLE001 - a pump thread must never raise into the interpreter
            return
        if not line:
            return
        try:
            child.write(line.encode("utf-8", errors="replace"))
        except Exception:  # noqa: BLE001 - write failure means the child is gone; wait() will notice
            return


def _start_pty_pumps(child: ChildProcess, emit: Callable[[Any], None]) -> None:
    """Start the bidirectional I/O pump threads for a capture-capable child.

    No-op when ``child.supports_output_capture`` is ``False`` (the
    inherited-stdio backend already shares the real console's file
    descriptors directly with the child -- there is nothing to pump).
    """

    if not child.supports_output_capture:
        return
    threading.Thread(target=_pump_child_output, args=(child, emit), daemon=True).start()
    threading.Thread(target=_pump_operator_input, args=(child,), daemon=True).start()


def _close_child_before_lock_release(child: Optional[ChildProcess]) -> None:
    """Best-effort, idempotent child termination.

    Reviewer-flagged gap (P-018 Copilot review, PR #331, comment
    3777958619): both top-level failure handlers in :func:`run_session`
    previously released the workspace lock directly in the ``except``
    block, deferring child termination to a module-level ``finally`` that
    always runs strictly AFTER that release. A supervisor failure
    occurring any time after ``child.spawn()`` (for example, while
    journaling ``ChildSpawned``, or inside sidecar/resolve bookkeeping)
    could therefore free the lock while the just-spawned Copilot child was
    still alive -- letting a second supervisor invocation acquire the lock
    and launch a concurrent session against the same workspace. Both
    failure handlers now call this directly, BEFORE releasing the lock;
    the trailing ``finally`` retains its own call purely as an idempotent
    fallback for any return path added later without the same discipline.
    Every backend's own ``close()`` is already idempotent and
    terminate-then-reap (SIGTERM, bounded wait, SIGKILL fallback for the
    real backends), so calling it twice is safe.
    """

    if child is None:
        return
    try:
        child.close()
    except Exception:  # noqa: BLE001 - best-effort resource cleanup only
        pass


def _build_approval_requested_event(identifier: str) -> ApprovalRequested:
    """Build the ``ApprovalRequested`` event for gated action ``identifier``.

    Reviewer-flagged gap (P-018 Copilot review, PR #331): this orchestrator
    previously dispatched straight from catalog lookup to
    ``approval_service.request_approval(...)`` and journaled only the
    ``ApprovalResolved`` response, leaving the EventBus/journal without the
    request metadata (``summary``, ``options``, ``default``, ``timeout``)
    documented in the event catalog. Both gated-action call sites in
    :func:`run_session` now emit this event immediately before blocking for
    input.
    """

    spec = get_gated_action(identifier)
    default = (
        spec.fallback_policy.reference_or_value
        if isinstance(spec.fallback_policy, UseSafeDefault)
        else None
    )
    return ApprovalRequested(
        kind=identifier,
        summary=spec.summary,
        options=spec.options,
        default=default,
        timeout=spec.timeout,
    )


def run_session(
    *,
    workspace_root: Path,
    argv: Sequence[str],
    approval_service: Any,
    session_id: Optional[str] = None,
    max_restarts: int = 0,
    use_pty: Optional[bool] = None,
    force_unlock: bool = False,
    non_interactive: bool = False,
    event_bus: Optional[EventBus] = None,
    child_process_factory: Optional[ChildProcessFactory] = None,
    lock_factory: LockFactory = _default_lock_factory,
    gh_executable: str = "gh",
    backlogit_executable: str = "backlogit",
    engram_executable: str = "engram",
    graphtor_docs_executable: str = "graphtor-docs",
    signal_num: int = signal_module.SIGTERM,
) -> SupervisorResult:
    """Run a single supervised Copilot CLI session end-to-end.

    ``approval_service`` has NO default -- every caller must explicitly
    supply one (see the module docstring's mandatory gated-action wiring
    section). There is no permissive fallback that would let a gated action
    proceed without an approval channel.
    """

    workspace_root = Path(workspace_root)
    bus = event_bus if event_bus is not None else EventBus()
    lock = lock_factory(workspace_root, session_id)
    journal = SessionJournal(workspace_root, lock.session_id)
    machine = SessionStateMachine(Phase.INIT)

    warnings: list[str] = []
    messages: list[str] = []
    lock_held_by_us = False
    child: Optional[ChildProcess] = None
    # Snapshot the caller's own environment BEFORE any bootstrap-resolved
    # secret/config additions are applied to this process's os.environ
    # below, so the top-level `finally` can restore it -- otherwise a
    # resolved GitHub token (and any other bootstrap addition) would leak
    # process-wide into later run_session() calls / unrelated library
    # callers sharing this same Python process (P-018 Copilot review
    # finding, PR #331).
    _environ_snapshot: dict[str, str] = dict(os.environ)
    _environ_mutated = False
    # Guards `_emit` against interleaved bus/journal writes once the PTY
    # output-pump daemon thread (started below) begins emitting `ChildOutput`
    # events concurrently with this function's own main-thread transitions.
    _emit_lock = threading.Lock()

    def _emit(event: Any) -> None:
        with _emit_lock:
            bus.emit(event)
            journal.append_event(event)

    def _transition(to_phase: Phase) -> None:
        event = machine.transition(to_phase)
        _emit(event)

    def _result(status: str, exit_code: int, extra_messages: Sequence[str] = ()) -> SupervisorResult:
        return SupervisorResult(
            status=status,
            exit_code=exit_code,
            messages=tuple(messages) + tuple(extra_messages),
            warnings=tuple(warnings),
        )

    def _confirm_restart() -> bool:
        _emit(_build_approval_requested_event("session_restart"))
        resolved = approval_service.request_approval(
            "session_restart", interactive=not non_interactive
        )
        _emit(resolved)
        return resolved.resolution == "restart"

    try:
        _transition(Phase.LOCKING)

        try:
            lock.acquire()
            lock_held_by_us = True
        except SessionLockRefused:
            unlocked = False
            if force_unlock:
                current_record = read_record(lock.record_path)
                if current_record is not None and is_stale_eligible_for_force_unlock(
                    diagnose_liveness(current_record)
                ):
                    try:
                        _emit(_build_approval_requested_event("force_unlock"))
                        resolved: ApprovalResolved = approval_service.request_approval(
                            "force_unlock", interactive=not non_interactive
                        )
                    except Exception as exc:  # noqa: BLE001 - fail closed, never propagate to a side effect
                        warnings.append(f"force_unlock approval raised: {exc}")
                        resolved = None
                    if resolved is not None:
                        _emit(resolved)
                        if resolved.resolution == "force_unlock":
                            outcome = locking_force_unlock(workspace_root, current_record)
                            if outcome is ForceUnlockOutcome.REMOVED:
                                try:
                                    lock.acquire()
                                    lock_held_by_us = True
                                    unlocked = True
                                except SessionLockRefused:
                                    unlocked = False
            if not unlocked:
                _transition(Phase.REFUSED)
                return _result("blocked", EXIT_CODE_BY_KIND[ErrorKind.LOCK])

        _transition(Phase.BOOTSTRAPPING)
        bootstrap_result = bootstrap_mod.bootstrap_workspace(
            workspace_root, gh_executable=gh_executable
        )
        warnings.extend(bootstrap_result.warnings)
        messages.extend(bootstrap_result.messages)
        # Applying resolved additions to this process's own environment is
        # the deliberate mutation point bootstrap.py's own docs defer to its
        # caller: the ChildProcess backends in process.py/process_pty.py
        # inherit the parent's environment verbatim with no per-call env
        # override, so this is the only way those additions reach the
        # supervised child. This mutation is RESTORED in the top-level
        # `finally` below so any resolved secret never outlives this single
        # run_session() call in this process's environment (P-018 Copilot
        # review finding, PR #331).
        if bootstrap_result.env:
            os.environ.update(bootstrap_result.env)
            _environ_mutated = True

        _transition(Phase.PREFLIGHT)
        sidecar_report = sidecar_mod.run_sidecars(
            workspace_root,
            backlogit_executable=backlogit_executable,
            engram_executable=engram_executable,
            graphtor_docs_executable=graphtor_docs_executable,
        )
        warnings.extend(sidecar_report.warnings)
        for name, outcome in sidecar_report.outcomes.items():
            _emit(SidecarProbed(name=name, available=(outcome == "ok"), detail=outcome))

        _transition(Phase.RESOLVING)
        resolve_result = resolve_mod.resolve_copilot(argv)
        _emit(CopilotResolved(exe_path=resolve_result.exe_path, source=resolve_result.source))

        _transition(Phase.LAUNCHING)
        factory = child_process_factory or _default_child_process_factory(
            use_pty, str(workspace_root)
        )
        child = factory(resolve_result.argv)
        child.spawn()
        _emit(ChildSpawned(argv=resolve_result.argv, pid=child.pid))
        if not child.supports_output_capture:
            journal.append_child_output_unavailable(
                "child process backend does not support output capture"
            )
        else:
            _start_pty_pumps(child, _emit)

        _transition(Phase.RUNNING)

        restart_controller = RestartController(
            max_restarts=max_restarts, confirm_restart=_confirm_restart
        )

        while True:
            try:
                exit_code = child.wait()
            except KeyboardInterrupt:
                # Operator-initiated cancellation: honor it via recovery.py's
                # own cancel_session, which drives RUNNING -> CANCELLING ->
                # DRAINING -> CANCELLED, terminates the child, and releases
                # the lock exactly once (all internal to that function).
                cancel_session(
                    machine,
                    child=child,
                    journal=journal,
                    lock=lock,
                    reason="operator cancellation (KeyboardInterrupt)",
                    signal_num=signal_num,
                )
                lock_held_by_us = False
                return _result("cancelled", EXIT_CODE_BY_KIND[ErrorKind.UNKNOWN])
            _emit(ChildExited(exit_code=exit_code))

            if exit_code == 0 or restart_controller.remaining_budget <= 0:
                break

            phase_after_attempt = restart_controller.attempt(
                machine,
                journal=journal,
                child=child,
                lock=lock,
                reason=f"child exited with code {exit_code}",
                signal_num=signal_num,
            )
            if phase_after_attempt is Phase.FAILED:
                # RestartController.attempt() already released the lock and
                # drove DRAINING -> FAILED (journaled internally). Do not
                # release the lock again below.
                lock_held_by_us = False
                return _result("failed", EXIT_CODE_BY_KIND[ErrorKind.RESTART])

            # Approved restart: RestartController.attempt() already drove
            # RUNNING -> RESTARTING -> LAUNCHING (journaled internally) and
            # terminated the previous child. Spawn the replacement here and
            # return the machine to RUNNING via our own emitted transition.
            child = factory(resolve_result.argv)
            child.spawn()
            _emit(ChildSpawned(argv=resolve_result.argv, pid=child.pid))
            _start_pty_pumps(child, _emit)
            _transition(Phase.RUNNING)

        _transition(Phase.DRAINING)
        _transition(Phase.EXITED)
        lock.release()
        lock_held_by_us = False
        return _result("ok", exit_code)

    except AutoharnessError as exc:
        if machine.phase not in (Phase.EXITED, Phase.FAILED, Phase.REFUSED, Phase.CANCELLED):
            _fail_closed_drain(machine, _emit)
        _close_child_before_lock_release(child)
        if lock_held_by_us:
            lock.release()
            lock_held_by_us = False
        return _result("failed", exc.exit_code, (str(exc),))
    except Exception as exc:  # noqa: BLE001 - top-level fail-closed boundary (H2)
        if machine.phase not in (Phase.EXITED, Phase.FAILED, Phase.REFUSED, Phase.CANCELLED):
            _fail_closed_drain(machine, _emit)
        _close_child_before_lock_release(child)
        if lock_held_by_us:
            lock.release()
            lock_held_by_us = False
        return _result("failed", EXIT_CODE_BY_KIND[ErrorKind.UNKNOWN], (str(exc),))
    finally:
        # Idempotent fallback only -- see _close_child_before_lock_release's
        # own docstring (P-018 Copilot review finding, PR #331, comment
        # 3777958619): both failure paths above already close the child
        # BEFORE releasing the workspace lock.
        _close_child_before_lock_release(child)
        if _environ_mutated:
            # Restore the caller's pre-call environment verbatim so any
            # bootstrap-resolved secret (e.g. a GitHub token) never outlives
            # this single run_session() call in this process's own
            # environment -- never leaked process-wide to later sessions or
            # unrelated library callers sharing the same Python process.
            os.environ.clear()
            os.environ.update(_environ_snapshot)


def _fail_closed_drain(machine: SessionStateMachine, emit: Callable[[Any], None]) -> None:
    """Best-effort drive ``machine`` to FAILED via DRAINING after an exception.

    Every phase except ``INIT`` has a legal edge to either ``DRAINING`` or
    ``REFUSED``; ``INIT`` itself has no legal edge to either (its only legal
    destination is ``LOCKING``), so an exception raised before the first
    transition leaves the machine at ``INIT`` with nothing to drain --
    exactly mirrored by the ``try/except`` blocks below.
    """

    try:
        if machine.phase is not Phase.DRAINING:
            emit(machine.transition(Phase.DRAINING))
        emit(machine.transition(Phase.FAILED))
    except Exception:  # noqa: BLE001 - best-effort only; never mask the real exception
        pass
