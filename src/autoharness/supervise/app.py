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

**Remote control composition**: ``remote_enabled=True`` creates the Plan 2
control plane over this same machine, journal, event bus, and active child.
Remote pause/resume invoke the child backend's platform capability directly;
remote cancel reuses :func:`cancel_session`; and tunnel teardown is performed
from the same ``finally`` boundary as child cleanup. The default remains local
only, so no UI or devtunnel prerequisite is introduced for existing callers.
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
from autoharness.supervise.redact import redact_record
from autoharness.supervise.result import SupervisorResult
from autoharness.supervise.session import Phase, SessionStateMachine

ChildProcessFactory = Callable[[Sequence[str]], ChildProcess]
LockFactory = Callable[[Path, Optional[str]], Any]
RemoteControlPlaneFactory = Callable[..., Any]

# Serializes the bootstrap-environment-READ-through-restore critical
# section (see the `_environ_snapshot`/`os.environ.update`/`os.environ.clear`
# + `update` sequence inside `run_session`) across ALL `run_session` calls
# sharing this Python process, regardless of workspace.
#
# P-018 Copilot review finding (PR #331, comment 3778273440): snapshotting
# and restoring `os.environ` around a single `run_session` call does NOT by
# itself make that mutation concurrency-safe -- workspace locks are
# per-workspace, so two `run_session` calls for TWO DIFFERENT workspaces can
# legitimately overlap in the same process (e.g. concurrent CLI-embedding
# test suites, or a future multi-workspace supervisor). Without
# serialization, the second call's snapshot could capture the first call's
# already-mutated environment, and/or the first call's restore could
# clobber additions the second call is still relying on. The reviewer
# offered two remedies: thread an explicit merged environment through every
# sidecar/child spawn call instead of mutating `os.environ` at all (a much
# larger refactor touching bootstrap.py, sidecar.py, process.py, and
# process_pty.py), or serialize this process-wide critical section. This
# module-level lock implements the latter, narrower, lower-risk fix.
#
# P-018 Copilot review finding (PR #331, comment 3778730372): the lock was
# initially acquired only around the environ APPLY step, not around
# `bootstrap_workspace()`'s own internal `os.environ` READ -- so the read
# itself was still unsynchronized, and a concurrent call could read another
# call's still-applied mutation and misinterpret it as its own NO-CLOBBER
# preset. The lock is now acquired BEFORE `bootstrap_workspace()` is
# called, making the whole read-apply-restore sequence one atomic critical
# section: two concurrent `run_session` calls now fully serialize around
# it instead of racing to observe or corrupt one another's environment.
_ENVIRON_MUTATION_LOCK = threading.Lock()


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


def _pump_child_output(
    child: ChildProcess,
    emit: Callable[[Any], None],
    report_emit_failure: Optional[Callable[[str], None]] = None,
) -> None:
    """Continuously drain capture-capable child output to the real console.

    Reviewer-flagged gap (P-018 Copilot review, PR #331, comment
    3777840441): the previous implementation blocked in ``child.wait()``
    without ever calling :meth:`ChildProcess.read`. For a PTY-backed child
    (``supports_output_capture`` is ``True``), nothing ever drained the
    master side of the pseudo-terminal: Copilot's own output was invisible
    to the operator, and once the PTY's kernel buffer filled a chatty
    child could block forever on its own writes. This helper runs as a
    daemon thread SCOPED TO A SINGLE CHILD (a new one is started per spawn,
    including each restart's replacement), forwarding every drained chunk
    straight through to the real ``sys.stdout`` and also emitting/
    journaling it as a :class:`ChildOutput` event so the session journal
    captures what the operator actually saw. Returns (thread exits) once
    :meth:`ChildProcess.read` reports EOF (``None``) or raises -- which
    happens promptly once ``child`` itself exits/closes, since the PTY's
    slave side closes with it.

    ``report_emit_failure`` (P-018 Copilot review, PR #331, comment
    3778273465): a raising ``emit`` (journal I/O error, e.g. a full disk,
    or a raising ``EventBus`` subscriber) previously terminated this whole
    pump thread -- the exact PTY-buffer-fills-and-the-child-deadlocks
    failure mode this pump exists to prevent, just moved one layer down.
    An emit failure is now caught and reported through this thread-safe
    callback (never raised into the interpreter), and draining CONTINUES
    for the rest of the child's lifetime -- the operator still sees live
    output on the real console even if journaling/bus delivery of that one
    chunk failed.

    **Console-write redaction (P-018 Copilot review, PR #331, comment
    3778627856)**: the direct ``sys.stdout.write(data)`` below previously
    ran BEFORE either redaction choke point -- :class:`EventBus` and
    :class:`SessionJournal` both redact the *reconstructed event copy* they
    each deliver/persist, but that happens strictly AFTER the raw chunk had
    already been printed verbatim to the real console. A bootstrap-resolved
    token (or any other registered secret) echoed by the child was already
    exposed on stdout by the time ``emit`` ever ran. Each captured chunk is
    now redacted with :func:`autoharness.supervise.redact.redact_record`
    (the SAME process-global default redactor instance
    ``bootstrap_workspace``/:class:`EventBus`/:class:`SessionJournal` all
    implicitly share whenever no explicit ``Redactor`` is threaded through)
    before it is ever written to the console, not merely before it is
    journaled/broadcast. A chunk that fails to redact (fail-closed) is
    dropped from the console entirely rather than ever printed raw, mirroring
    the existing fail-closed contract used everywhere else redaction is
    applied.
    """

    while True:
        try:
            data = child.read()
        except Exception:  # noqa: BLE001 - a pump thread must never raise into the interpreter
            return
        if data is None:
            return
        try:
            redacted_data, _redact_warning = redact_record(data)
        except Exception:  # noqa: BLE001 - redact_record already fails closed internally; defense in depth
            redacted_data = None
        if redacted_data is not None:
            try:
                sys.stdout.write(redacted_data)
                sys.stdout.flush()
            except Exception:  # noqa: BLE001 - a console write failure does not stop draining the child
                pass
        try:
            emit(ChildOutput(stream="stdout", line=data))
        except Exception as exc:  # noqa: BLE001 - emit failure must not kill this pump (3778273465)
            if report_emit_failure is not None:
                try:
                    report_emit_failure(f"ChildOutput emit failed: {exc}")
                except Exception:  # noqa: BLE001 - the failure channel itself must never propagate
                    pass


class _ActiveChildRef:
    """Thread-safe mutable holder for the operator-input pump's current
    write target.

    Reviewer-flagged gap (P-018 Copilot review, PR #331, comment
    3778121130): the original design started a brand-new input-forwarding
    thread per child spawn (initial AND every restart), each blocked
    reading ``sys.stdin`` with no stop/join handle. On an approved
    restart, the OLD input thread could remain blocked in
    ``sys.stdin.readline()`` at the exact moment the NEW one started,
    leaving two threads racing to consume the next operator line and
    forward it to two DIFFERENT children (one already closed). This
    holder lets ``run_session`` start exactly ONE persistent input-pump
    thread for the entire session and simply repoint it at whichever
    child is currently active across restarts -- "one input reader routed
    to the active child", per the reviewer's own suggested fix.
    """

    def __init__(self, child: ChildProcess) -> None:
        self._lock = threading.Lock()
        self._child = child

    def set(self, child: ChildProcess) -> None:
        with self._lock:
            self._child = child

    def get(self) -> ChildProcess:
        with self._lock:
            return self._child


def _pump_operator_input(active_ref: _ActiveChildRef) -> None:
    """Continuously forward operator keyboard input into whichever child
    ``active_ref`` currently references.

    Reviewer-flagged gap (P-018 Copilot review, PR #331, comments
    3777840441 and 3778121130): without this pump, a PTY-backed
    interactive session could never receive operator input at all --
    prompts would appear to hang indefinitely. This forwards line-buffered
    input (``sys.stdin.readline``) to :meth:`ChildProcess.write`; it
    intentionally does not attempt raw, single-keystroke terminal
    forwarding (arrow-key history navigation, live tab-completion
    redraws), which would require putting the real terminal into raw/
    cbreak mode and is out of scope for this fix.

    Exactly ONE instance of this pump runs for the whole life of a
    ``run_session`` call (see ``_ActiveChildRef``'s own docstring): a
    transient write failure (e.g. the active child has just exited and is
    mid-restart-handoff) does NOT terminate this thread -- that line's
    forwarding is simply dropped and the loop keeps reading, so a
    subsequent restart's replacement child still receives later operator
    input. The thread exits only when ``sys.stdin`` itself reports EOF/
    raises, and runs as a daemon so it never blocks process/interpreter
    shutdown.
    """

    while True:
        try:
            line = sys.stdin.readline()
        except Exception:  # noqa: BLE001 - a pump thread must never raise into the interpreter
            return
        if not line:
            return
        try:
            active_ref.get().write(line.encode("utf-8", errors="replace"))
        except Exception:  # noqa: BLE001 - forwarding to THIS child failed; keep reading for the next one
            continue


def _start_output_pump(
    child: ChildProcess,
    emit: Callable[[Any], None],
    report_emit_failure: Optional[Callable[[str], None]] = None,
) -> Optional[threading.Thread]:
    """Start (and return) the output-drain daemon thread for ``child``.

    Returns ``None`` (no-op, no thread started) when
    ``child.supports_output_capture`` is ``False`` (the inherited-stdio
    backend already shares the real console's file descriptors directly
    with the child -- there is nothing to pump). Callers should ``join()``
    the previously-returned thread (bounded timeout) before starting a new
    one for a replacement child, so trailing output from the OLD child is
    drained deterministically rather than left to timing luck (P-018
    Copilot review finding, PR #331, comment 3778121130 -- "quiesce it
    before restart/return"). ``report_emit_failure`` is forwarded to
    :func:`_pump_child_output` -- see its own docstring (P-018 Copilot
    review finding, PR #331, comment 3778273465).
    """

    if not child.supports_output_capture:
        return None
    thread = threading.Thread(
        target=_pump_child_output, args=(child, emit, report_emit_failure), daemon=True
    )
    thread.start()
    return thread


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
    remote_enabled: bool = False,
    remote_bind_host: str = "127.0.0.1",
    remote_port: int = 7860,
    remote_control_plane_factory: Optional[RemoteControlPlaneFactory] = None,
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
    # Output-drain pump thread for the CURRENT child (re-assigned to a new
    # thread on every spawn, including restarts); joined with a bounded
    # timeout before starting a new one and again in the top-level
    # `finally`, so trailing output is drained deterministically rather
    # than left to timing luck (P-018 Copilot review finding, PR #331,
    # comment 3778121130).
    output_pump_thread: Optional[threading.Thread] = None
    # Exactly ONE persistent input-forwarding thread is started for the
    # whole session (see `_ActiveChildRef`'s own docstring) -- this holder
    # is what lets it be re-pointed at each restart's replacement child
    # instead of a second competing thread ever being started.
    active_child_ref: Optional[_ActiveChildRef] = None
    remote_control: Any = None
    remote_cancelled = threading.Event()
    # Snapshot is taken lazily, immediately before the bootstrap-resolved
    # env is actually applied below, under `_ENVIRON_MUTATION_LOCK` (P-018
    # Copilot review finding, PR #331, comment 3778273440) -- not here at
    # the top, so nothing observes/holds the lock during phases (LOCKING,
    # etc.) that never touch `os.environ` at all.
    _environ_snapshot: dict[str, str] = {}
    _environ_mutated = False
    # True for exactly the span between acquiring `_ENVIRON_MUTATION_LOCK`
    # below and this function's own `finally` releasing it -- guards
    # against releasing a lock this call never acquired (e.g. when
    # `bootstrap_result.env` is empty, no mutation/lock is needed at all).
    _environ_lock_held = False
    # Guards `_emit` against interleaved bus/journal writes once the PTY
    # output-pump daemon thread (started below) begins emitting `ChildOutput`
    # events concurrently with this function's own main-thread transitions.
    _emit_lock = threading.Lock()

    def _emit(event: Any) -> None:
        with _emit_lock:
            bus.emit(event)
            journal.append_event(event)

    def _report_pump_emit_failure(message: str) -> None:
        # P-018 Copilot review finding, PR #331, comment 3778273465: a
        # raising `_emit` inside the output-drain pump thread must not be
        # silently swallowed into nothing -- record it as an
        # operator-visible warning (thread-safe: list.append is atomic
        # under CPython's GIL, and this is the same `warnings` list the
        # main thread only ever reads from after the pump thread has been
        # joined, never concurrently mutates).
        warnings.append(message)

    def _transition(to_phase: Phase) -> None:
        event = machine.transition(to_phase)
        _emit(event)

    def _result(status: str, exit_code: int, extra_messages: Sequence[str] = ()) -> SupervisorResult:
        return SupervisorResult(
            status=status,
            exit_code=exit_code,
            messages=tuple(messages) + tuple(extra_messages),
            # Cleanup runs after the return expression is evaluated; retain
            # the shared sequence so teardown warnings remain observable.
            warnings=warnings,
        )

    def _confirm_restart() -> bool:
        _emit(_build_approval_requested_event("session_restart"))
        resolved = approval_service.request_approval(
            "session_restart", interactive=not non_interactive
        )
        _emit(resolved)
        return resolved.resolution == "restart"

    def _remote_pause() -> object:
        if child is None:
            raise RuntimeError("remote pause requested before the child was started")
        child.pause()
        return "paused"

    def _remote_resume() -> object:
        if child is None:
            raise RuntimeError("remote resume requested before the child was started")
        child.resume()
        return "resumed"

    def _remote_cancel() -> object:
        nonlocal lock_held_by_us
        if child is None:
            raise RuntimeError("remote cancel requested before the child was started")
        phase = cancel_session(
            machine,
            child=child,
            emit=_emit,
            lock=lock,
            reason="remote steer request",
            signal_num=signal_num,
        )
        lock_held_by_us = False
        remote_cancelled.set()
        return phase.value

    def _remote_tunnel_loss() -> None:
        warnings.append("devtunnel exited; remote control-plane access is unavailable")

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
        # P-018 Copilot review finding, PR #331, comment 3778730372: the
        # lock was previously acquired only around the environ APPLY step
        # below, but `bootstrap_workspace()` (called with no explicit
        # `env=`) reads its own baseline via an internal `dict(os.environ)`
        # snapshot -- an UNSYNCHRONIZED read. A concurrent `run_session`
        # call for a different workspace, still holding this lock with its
        # own mutation applied, could have that mutated state read here and
        # misinterpreted as a NO-CLOBBER preset for a same-named variable
        # (e.g. COPILOT_HOME/ENGRAM_DATA_DIR, or even a token variable),
        # silently adopting the OTHER session's values once it eventually
        # proceeds. The lock is now acquired BEFORE this read, making the
        # read-apply-restore sequence a single atomic critical section, as
        # the reviewer's own suggested remedy describes. It is released
        # immediately below when there turns out to be nothing to mutate
        # (`bootstrap_result.env` is empty) so a bootstrap-only session
        # never holds it for its own child's entire lifetime for no reason.
        _ENVIRON_MUTATION_LOCK.acquire()
        _environ_lock_held = True
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
        # review finding, PR #331). The whole read-through-restore window
        # is serialized process-wide via `_ENVIRON_MUTATION_LOCK` (P-018
        # Copilot review finding, PR #331, comments 3778273440 and
        # 3778730372) -- see that lock's own module-level docstring -- so a
        # concurrent `run_session` call for a different workspace cannot
        # observe or clobber this call's read or mutation, and vice versa.
        # The snapshot is taken only now, still under the lock acquired
        # above, so it reflects exactly the environment this call must
        # restore, not whatever another call's still-applied mutation
        # happened to look like a moment earlier.
        if bootstrap_result.env:
            _environ_snapshot = dict(os.environ)
            os.environ.update(bootstrap_result.env)
            _environ_mutated = True
        else:
            # Nothing to mutate/restore: release right away rather than
            # holding the lock for this call's entire remaining lifetime.
            _ENVIRON_MUTATION_LOCK.release()
            _environ_lock_held = False

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

        if remote_enabled:
            from autoharness.remote.control_plane import RemoteControlPlane

            factory = remote_control_plane_factory or RemoteControlPlane.create
            remote_control = factory(
                workspace_root=workspace_root,
                session_id=lock.session_id,
                state_machine=machine,
                journal=journal,
                event_bus=bus,
                local_channel=approval_service,
                on_pause=_remote_pause,
                on_resume=_remote_resume,
                on_cancel=_remote_cancel,
                emit=_emit,
                on_tunnel_loss=_remote_tunnel_loss,
                bind_host=remote_bind_host,
                port=remote_port,
            )

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
            active_child_ref = _ActiveChildRef(child)
            threading.Thread(
                target=_pump_operator_input, args=(active_child_ref,), daemon=True
            ).start()
            output_pump_thread = _start_output_pump(child, _emit, _report_pump_emit_failure)

        _transition(Phase.RUNNING)
        if remote_control is not None:
            remote_control.start()

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
                    emit=_emit,
                    lock=lock,
                    reason="operator cancellation (KeyboardInterrupt)",
                    signal_num=signal_num,
                )
                lock_held_by_us = False
                return _result("cancelled", EXIT_CODE_BY_KIND[ErrorKind.UNKNOWN])
            except (OSError, RuntimeError):
                if remote_cancelled.is_set():
                    return _result("cancelled", EXIT_CODE_BY_KIND[ErrorKind.UNKNOWN])
                raise
            if remote_cancelled.is_set():
                return _result("cancelled", EXIT_CODE_BY_KIND[ErrorKind.UNKNOWN])
            _emit(ChildExited(exit_code=exit_code))

            if exit_code == 0 or restart_controller.remaining_budget <= 0:
                break

            phase_after_attempt = restart_controller.attempt(
                machine,
                emit=_emit,
                # `child` is intentionally NOT passed here (P-018 Copilot
                # review finding, PR #331, comment 3778730421): by this
                # point `child.wait()` immediately above has ALREADY
                # returned normally, meaning the OS has ALREADY reaped this
                # PID. `RestartController.attempt()`'s exhaustion/decline
                # path calls `child.signal(signal_num)` unconditionally
                # (the PTY backend's own `signal()` has no
                # already-exited guard, unlike its `close()`), which would
                # send a raw `os.kill(pid, ...)` to a PID the kernel may
                # have already reused for an entirely unrelated process.
                # There is nothing left for `attempt()` to terminate; the
                # top-level `finally` below still safely closes this same
                # `child` object via `_close_child_before_lock_release`
                # (its `close()` correctly no-ops the signal/wait sequence
                # once `_exit_code` is already recorded, only releasing the
                # file descriptor).
                child=None,
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

            # Approved restart: RestartController.attempt() drove
            # RUNNING -> RESTARTING -> LAUNCHING (journaled internally) but
            # -- since `child=None` was passed above (comment
            # 3778730421) -- did NOT itself touch the OLD child (already
            # exited/reaped by `child.wait()` above; nothing left to
            # signal). This call site now closes the OLD child's PTY
            # handle directly instead, before the `child` local is
            # reassigned to the replacement below, so its file descriptor
            # is still released promptly here rather than only reached via
            # the top-level `finally` (which would otherwise be the only
            # remaining reference once `child` is overwritten). Quiesce the
            # OLD output pump (bounded join -- the old child has already
            # exited/been closed, so its read() should EOF promptly)
            # before starting the replacement, then spawn it and repoint
            # (never duplicate) the single persistent input pump at it
            # (P-018 Copilot review finding, PR #331, comment 3778121130).
            if output_pump_thread is not None:
                output_pump_thread.join(timeout=2.0)
            try:
                child.close()
            except ProcessLookupError:
                pass  # already exited/reaped -- nothing left to close
            child = factory(resolve_result.argv)
            child.spawn()
            _emit(ChildSpawned(argv=resolve_result.argv, pid=child.pid))
            if child.supports_output_capture:
                if active_child_ref is not None:
                    active_child_ref.set(child)
                else:
                    # The very first child didn't support output capture,
                    # but this replacement does -- start the persistent
                    # input pump now, for the first time.
                    active_child_ref = _ActiveChildRef(child)
                    threading.Thread(
                        target=_pump_operator_input, args=(active_child_ref,), daemon=True
                    ).start()
                output_pump_thread = _start_output_pump(child, _emit, _report_pump_emit_failure)
            else:
                output_pump_thread = None
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
        if remote_control is not None:
            try:
                remote_control.stop()
            except Exception as exc:  # noqa: BLE001 - cleanup must not mask session teardown
                warnings.append(f"remote control-plane shutdown failed: {exc}")
        # Idempotent fallback only -- see _close_child_before_lock_release's
        # own docstring (P-018 Copilot review finding, PR #331, comment
        # 3777958619): both failure paths above already close the child
        # BEFORE releasing the workspace lock.
        _close_child_before_lock_release(child)
        # Quiesce the final output pump (bounded join) before returning, so
        # trailing output is drained deterministically rather than left
        # running past this function's own return (P-018 Copilot review
        # finding, PR #331, comment 3778121130). The child is already
        # closed by this point (immediately above), so its read() should
        # EOF promptly; the persistent input pump is intentionally left
        # running (daemon thread, harmless once the process itself exits).
        if output_pump_thread is not None:
            output_pump_thread.join(timeout=2.0)
        if _environ_mutated:
            # Restore the caller's pre-call environment verbatim so any
            # bootstrap-resolved secret (e.g. a GitHub token) never outlives
            # this single run_session() call in this process's own
            # environment -- never leaked process-wide to later sessions or
            # unrelated library callers sharing the same Python process.
            os.environ.clear()
            os.environ.update(_environ_snapshot)
        if _environ_lock_held:
            # Release LAST, only after the restore immediately above has
            # fully completed -- this is what actually serializes the
            # critical section (P-018 Copilot review finding, PR #331,
            # comment 3778273440): a concurrent `run_session` call blocked
            # on `_ENVIRON_MUTATION_LOCK.acquire()` above must never resume
            # (and take its own snapshot) until THIS call's mutation has
            # been fully undone.
            _ENVIRON_MUTATION_LOCK.release()


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
