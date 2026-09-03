"""Execution-level regression tests for scripts/graphtor-mcp-shim.cjs.

Follows the execution-level coverage precedent established for helper
scripts in ``tests/test_deploy_harness_scripts.py``: rather than asserting on
the shim's source text, these tests actually spawn the shim (via ``node`` or
``bun``, whichever is available) wrapping a small fake MCP-like server
process, drive the real stdio handshake protocol, and assert on what the
wrapped ("child") server actually observed and what the client actually
received back.

Regression coverage (158-S/150-F closure-repair follow-up, PR #429 Copilot
review rounds 2, 3, and 4):

* an early ``notifications/initialized`` sent by the client with nothing
  else queued must still be flushed to the child once the child's
  ``initialize`` response is observed -- ``flushQueuedClientMessages()``
  previously short-circuited on an empty queue and silently dropped this
  exact case (fixed by removing the ``queuedClientMessages.length === 0``
  guard so ``sendInitialized()`` always runs once the response is seen);
* a request queued between ``initialize`` and the child's response is
  flushed to the child, in order, only after the synthesized
  ``notifications/initialized``;
* a JSON-RPC ``initialize`` error from the child causes every queued
  request to receive a synthesized JSON-RPC error response instead of
  hanging forever;
* the child process exiting before it ever responds to ``initialize``
  synthesizes an error response for the outstanding ``initialize`` request
  itself (not merely for messages queued behind it -- that was a distinct,
  separately-flagged gap) AND the proxy actually terminates instead of
  merely setting ``process.exitCode`` while readline's read loop on stdin
  keeps the event loop, and therefore the process, alive indefinitely;
* the wrapped server's stdin write end failing (a broken-pipe/EPIPE-class
  error on the child.stdin Writable stream itself, distinct from the
  ChildProcess-level ``error``/``close`` events covered by the previous
  case) still synthesizes the promised JSON-RPC error responses and
  terminates the proxy cleanly, instead of crashing the whole process on
  an unhandled stream error.
"""

from __future__ import annotations

import json
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SHIM_SCRIPT = _REPO_ROOT / "scripts" / "graphtor-mcp-shim.cjs"

# Resolve the *real* interpreter behind any venv launcher indirection.
# ``sys.executable`` inside a Windows venv created by ``uv``/``venv`` can be
# a small re-exec launcher stub rather than the actual CPython binary; the
# fake server's ``close-stdin-only`` mode below depends on ``os.close(0)``
# closing the literal OS pipe handle that this test process's spawned child
# holds, which only happens reliably when the interpreter that runs the
# fake server script *is* that process (no extra re-exec hop in between).
# ``sys._base_executable`` (present since Python 3.11) points at that real
# interpreter; fall back to ``sys.executable`` when it is unavailable.
_PYTHON_INTERPRETER = getattr(sys, "_base_executable", None) or sys.executable

_NODE = shutil.which("node")
_BUN = shutil.which("bun")
_JS_RUNTIME = _NODE or _BUN

_FAKE_SERVER_SOURCE = '''\
"""Fake MCP-like server used only by tests/test_graphtor_mcp_shim.py.

Reads newline-delimited JSON-RPC messages from stdin and reacts according to
the mode selected by argv[1]:

  normal             -- initialize succeeds after a short delay (simulating
                         a slow-starting real server, the exact race the
                         shim exists to close); every other message the
                         server actually receives gets an observable
                         acknowledgement written to its own stdout, so the
                         test can assert on what the server *actually saw*
                         rather than what the shim decided to forward.
  init-error         -- initialize responds with a JSON-RPC error.
  crash-before-init  -- the process exits before ever responding to
                         initialize (but after having already read and
                         consumed that request off stdin).
  close-stdin-only   -- the process force-closes the underlying OS file
                         descriptors for both its own stdin and stdout
                         immediately via os.close() (bypassing Python's io
                         wrapper, whose own .close() does not reliably
                         cause an immediate broken-pipe write error on
                         every platform) without exiting the process
                         itself, so no ChildProcess `exit`/`close` event
                         fires for several seconds. Any write the shim
                         performs to this process's stdin therefore fails
                         immediately on the write side (broken pipe/EPIPE),
                         isolating that failure mode from the
                         already-covered child-process-exited case above.
"""
import json
import os
import sys
import time

mode = sys.argv[1] if len(sys.argv) > 1 else "normal"

if mode == "close-stdin-only":
    os.close(0)
    os.close(1)
    time.sleep(5)
    sys.exit(0)


def send(obj):
    sys.stdout.write(json.dumps(obj) + "\\n")
    sys.stdout.flush()


for raw_line in sys.stdin:
    line = raw_line.strip()
    if not line:
        continue
    try:
        msg = json.loads(line)
    except ValueError:
        continue

    method = msg.get("method")

    if method == "initialize":
        if mode == "crash-before-init":
            sys.exit(1)
        time.sleep(0.3)
        if mode == "init-error":
            send(
                {
                    "jsonrpc": "2.0",
                    "id": msg.get("id"),
                    "error": {"code": -32001, "message": "boom"},
                }
            )
        else:
            send({"jsonrpc": "2.0", "id": msg.get("id"), "result": {}})
        continue

    if method == "notifications/initialized":
        send({"jsonrpc": "2.0", "method": "test/receivedInitialized", "params": {}})
        continue

    if "id" in msg:
        send({"jsonrpc": "2.0", "id": msg["id"], "result": {"echoed": method}})
'''


@unittest.skipUnless(_JS_RUNTIME, "neither node nor bun is available")
class GraphtorMcpShimHandshakeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_dir = tempfile.mkdtemp(prefix="graphtor-shim-test-")
        self._server_script = Path(self._tmp_dir) / "fake_server.py"
        self._server_script.write_text(
            _FAKE_SERVER_SOURCE, encoding="utf-8", newline="\n"
        )
        self._proc: subprocess.Popen | None = None

    def tearDown(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            try:
                self._proc.stdin.close()
            except Exception:
                pass
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def _spawn(self, mode: str) -> subprocess.Popen:
        args = [
            _JS_RUNTIME,
            str(_SHIM_SCRIPT),
            _PYTHON_INTERPRETER,
            str(self._server_script),
            mode,
        ]
        self._proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        return self._proc

    @staticmethod
    def _write(proc: subprocess.Popen, obj: dict) -> None:
        proc.stdin.write(json.dumps(obj) + "\n")
        proc.stdin.flush()

    @staticmethod
    def _start_reader(proc: subprocess.Popen) -> "queue.Queue[dict]":
        out: "queue.Queue[dict]" = queue.Queue()

        def _pump() -> None:
            for raw_line in proc.stdout:
                stripped = raw_line.strip()
                if not stripped:
                    continue
                try:
                    out.put(json.loads(stripped))
                except ValueError:
                    continue

        threading.Thread(target=_pump, daemon=True).start()
        return out

    @staticmethod
    def _collect_all(
        messages: "queue.Queue[dict]", predicates: list, timeout: float = 10.0
    ) -> tuple[list[dict], list[bool]]:
        """Drain `messages` until every predicate has matched at least one
        collected message, or until `timeout` elapses.

        Returns the FULL list of messages observed, in arrival order, plus a
        parallel list of which predicates were satisfied. Deliberately never
        discards a message that satisfied one predicate before the others
        were satisfied -- a naive "collect-until-first-match" helper called
        twice in sequence against the same queue would silently drop an
        earlier-arriving message needed by the second call, since arrival
        order between the child's synthesized responses and its passed-
        through lines is not fixed across code paths (e.g. the initialize
        response line is written to stdout before the synthesized
        notifications/initialized flush in the success path, but the
        synthesized queued-request error is written before the echoed
        initialize-error line in the failure path).
        """
        deadline = time.time() + timeout
        seen: list[dict] = []
        satisfied = [False] * len(predicates)
        while not all(satisfied):
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            try:
                msg = messages.get(timeout=remaining)
            except queue.Empty:
                break
            seen.append(msg)
            for i, predicate in enumerate(predicates):
                if not satisfied[i] and predicate(msg):
                    satisfied[i] = True
        return seen, satisfied

    def test_early_notifications_initialized_with_empty_queue_is_flushed(
        self,
    ) -> None:
        # Regression for the bug flagged in PR #429 Copilot review round 2:
        # a client that sends ONLY `initialize` followed immediately by its
        # own `notifications/initialized` (nothing else queued) previously
        # left flushQueuedClientMessages() short-circuiting on an empty
        # queue -- the child never saw the notification at all.
        proc = self._spawn("normal")
        messages = self._start_reader(proc)

        self._write(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self._write(
            proc,
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        )

        seen, satisfied = self._collect_all(
            messages,
            [
                lambda m: m.get("id") == 1 and "result" in m,
                lambda m: m.get("method") == "test/receivedInitialized",
            ],
        )
        self.assertTrue(
            satisfied[0], f"initialize response never observed; messages seen: {seen!r}"
        )
        self.assertTrue(
            satisfied[1],
            "child server never observed notifications/initialized "
            f"(empty-queue flush regression); messages seen: {seen!r}",
        )

    def test_queued_request_and_late_initialized_are_flushed_in_order(self) -> None:
        proc = self._spawn("normal")
        messages = self._start_reader(proc)

        self._write(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self._write(proc, {"jsonrpc": "2.0", "id": 2, "method": "test/echo", "params": {}})
        self._write(
            proc,
            {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        )

        seen, satisfied = self._collect_all(
            messages,
            [
                lambda m: m.get("id") == 2 and "result" in m,
                lambda m: m.get("method") == "test/receivedInitialized",
            ],
        )
        self.assertTrue(
            satisfied[0], f"queued request (id=2) was never answered; messages seen: {seen!r}"
        )
        self.assertTrue(
            satisfied[1],
            f"child server never observed notifications/initialized; messages seen: {seen!r}",
        )

        initialized_index = next(
            i for i, m in enumerate(seen) if m.get("method") == "test/receivedInitialized"
        )
        echoed_index = next(i for i, m in enumerate(seen) if m.get("id") == 2)
        self.assertLess(
            initialized_index,
            echoed_index,
            "notifications/initialized must reach the child before the "
            "queued request that was buffered behind it",
        )

    def test_initialize_error_fails_queued_request(self) -> None:
        proc = self._spawn("init-error")
        messages = self._start_reader(proc)

        self._write(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self._write(proc, {"jsonrpc": "2.0", "id": 2, "method": "test/echo", "params": {}})

        seen, satisfied = self._collect_all(
            messages,
            [
                lambda m: m.get("id") == 1 and "error" in m,
                lambda m: m.get("id") == 2 and "error" in m,
            ],
        )
        self.assertTrue(
            satisfied[0], f"initialize error response never observed; messages seen: {seen!r}"
        )
        self.assertTrue(
            satisfied[1],
            "queued request never received a synthesized error response "
            f"after initialize failed; messages seen: {seen!r}",
        )

    def test_child_exit_before_initialize_response_fails_initialize_and_terminates(
        self,
    ) -> None:
        proc = self._spawn("crash-before-init")
        messages = self._start_reader(proc)

        self._write(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self._write(proc, {"jsonrpc": "2.0", "id": 2, "method": "test/echo", "params": {}})

        seen, satisfied = self._collect_all(
            messages,
            [
                lambda m: m.get("id") == 1 and "error" in m,
                lambda m: m.get("id") == 2 and "error" in m,
            ],
        )
        self.assertTrue(
            satisfied[0],
            "the outstanding initialize request itself never received a "
            "synthesized error response after the child exited before "
            f"responding to it; messages seen: {seen!r}",
        )
        self.assertTrue(
            satisfied[1],
            "queued request never received a synthesized error response "
            f"after the child exited before responding to initialize; "
            f"messages seen: {seen!r}",
        )

        # The proxy must actually terminate once the wrapped server is gone
        # -- merely assigning process.exitCode does not stop readline's read
        # loop on stdin from keeping the event loop (and therefore the
        # process) alive, which would otherwise leave the client waiting
        # forever for either a response or transport EOF even after every
        # outstanding request has been answered above. Deliberately leave
        # stdin OPEN here (never close it before wait()): closing it would
        # itself supply the exact EOF that terminates readline's read loop,
        # which would let even the old, process.exitCode-only implementation
        # pass this check for the wrong reason. `wait()` either returns the
        # exit code or raises `subprocess.TimeoutExpired` -- there is no
        # third, falsy-but-non-exceptional outcome to assert on, so a
        # successful return (of any value, including 0) is itself the proof
        # of autonomous termination.
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
            self.fail(
                "shim process never terminated on its own after the wrapped "
                "server exited before responding to initialize (stdin was "
                "deliberately left open so termination could not be "
                "attributed to an externally-supplied EOF)"
            )

    def test_child_stdin_write_error_fails_requests_without_crashing(
        self,
    ) -> None:
        # Regression for PR #429 Copilot review round 5: writeToChild()
        # writes directly to child.stdin, but only the ChildProcess-level
        # `error`/`close` events were handled -- an EPIPE (or similar)
        # emitted on the child.stdin Writable stream itself was previously
        # unhandled. Node treats an unhandled stream `error` as fatal and
        # would crash the whole proxy process before
        # handleChildTermination() ever ran, instead of synthesizing the
        # promised JSON-RPC error responses.
        #
        # This is deliberately a different code path than
        # test_child_exit_before_initialize_response_fails_initialize_and_terminates
        # above: that test's fake server exits, which fires the
        # ChildProcess `close` event (already handled before this fix).
        # This test's fake server instead closes only its own stdin read
        # end while remaining alive (no exit, so no `close`/`exit` event
        # fires on the ChildProcess), isolating the failure to the
        # child.stdin stream's own `error` event -- exactly the event this
        # fix adds a listener for.
        proc = self._spawn("close-stdin-only")
        messages = self._start_reader(proc)

        # Give the fake server time to actually close its stdin read end
        # before the first write is attempted, so the write reliably fails
        # on the stdin stream itself rather than racing a still-open pipe.
        time.sleep(0.3)

        self._write(proc, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self._write(proc, {"jsonrpc": "2.0", "id": 2, "method": "test/echo", "params": {}})

        seen, satisfied = self._collect_all(
            messages,
            [
                lambda m: m.get("id") == 1 and "error" in m,
                lambda m: m.get("id") == 2 and "error" in m,
            ],
        )
        self.assertTrue(
            satisfied[0],
            "the initialize request never received a synthesized error "
            "response after a write to the child's stdin failed "
            f"(possible unhandled child.stdin EPIPE crash); messages seen: {seen!r}",
        )
        self.assertTrue(
            satisfied[1],
            "queued request never received a synthesized error response "
            "after a write to the child's stdin failed (possible "
            f"unhandled child.stdin EPIPE crash); messages seen: {seen!r}",
        )

        # As above: the proxy must terminate on its own without an
        # externally-supplied EOF, and wait() returning at all (rather than
        # raising TimeoutExpired) is the only meaningful assertion --
        # crucially, it must return normally rather than the process having
        # already died from an uncaught exception before this point (which
        # would have already made the assertions above fail, since no
        # error responses would have been written).
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
            self.fail(
                "shim process never terminated on its own after a write to "
                "the child's stdin failed"
            )


if __name__ == "__main__":
    unittest.main()
