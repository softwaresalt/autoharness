// graphtor-mcp-shim.cjs — MCP stdio handshake proxy for graphtor-docs.
//
// Purpose: the Copilot CLI's MCP client can send follow-on client messages
// (including `notifications/initialized`) before it has actually observed the
// wrapped server's `initialize` response on stdout. Against a slower-starting
// server such as `graphtor-docs serve`, this race caused the server to never
// come up live at Copilot launch (see: "fix(supervise): Engram/graphtor-docs
// never became live at Copilot launch"). This shim sits between the MCP
// client and the real server process, buffering client messages sent after
// `initialize` (including the client's own `notifications/initialized`,
// which is never forwarded ahead of the server's response) until the
// server's `initialize` response has actually been seen, then flushing them
// (sending `notifications/initialized` first, synthesized exactly once). All
// other stdio traffic is passed through unmodified line-by-line. If the
// server's `initialize` call itself returns a JSON-RPC error, or the child
// process exits/errors before responding, every queued client request is
// answered with a synthesized JSON-RPC error rather than left to hang
// indefinitely.
//
// Invocation (see .mcp.json): `bun scripts/graphtor-mcp-shim.cjs <command> [args...]`
// wraps the real server command/args, e.g. `graphtor-docs serve --read-only`.
//
// This file must live in a tracked, non-gitignored location (unlike the
// `.copilot/` workspace-state directory) so a fresh clone has it available;
// `.mcp.json` is a committed root config read directly by MCP clients.
const readline = require('node:readline');
const { spawn } = require('node:child_process');

const [command, ...args] = process.argv.slice(2);

if (!command) {
  console.error('Usage: node graphtor-mcp-shim.cjs <command> [args...]');
  process.exit(2);
}

const child = spawn(command, args, {
  env: process.env,
  stdio: ['pipe', 'pipe', 'pipe'],
});

let initializeId;
let initializeResponseSeen = false;
let initializeFailed = false;
let initializedSent = false;
const queuedClientMessages = [];

function parseMessage(line) {
  try {
    return JSON.parse(line);
  } catch {
    return undefined;
  }
}

function writeToChild(line) {
  child.stdin.write(`${line}\n`);
}

function emitErrorResponse(id, message) {
  if (id === undefined || id === null) {
    // Cannot answer a notification (no id) with a response.
    return;
  }

  process.stdout.write(
    `${JSON.stringify({
      jsonrpc: '2.0',
      id,
      error: { code: -32000, message },
    })}\n`,
  );
}

function failQueuedClientMessages(reason) {
  for (const queuedLine of queuedClientMessages.splice(0)) {
    const queuedMessage = parseMessage(queuedLine);
    if (queuedMessage) {
      emitErrorResponse(queuedMessage.id, reason);
    }
  }
}

function sendInitialized() {
  if (initializedSent) {
    return;
  }

  writeToChild(
    JSON.stringify({
      jsonrpc: '2.0',
      method: 'notifications/initialized',
      params: {},
    }),
  );
  initializedSent = true;
}

function flushQueuedClientMessages() {
  if (!initializeResponseSeen) {
    return;
  }

  // Always synthesize `notifications/initialized` once the response has been
  // seen, even when nothing else is queued -- e.g. a client that sends only
  // `initialize` followed immediately by its own `notifications/initialized`
  // and then waits idly for further server-initiated interaction has an
  // empty queue at this point, but the server still must be told the
  // handshake completed. `sendInitialized()` is itself idempotent, so this
  // is safe to call on every server line observed after the response.
  sendInitialized();
  for (const line of queuedClientMessages.splice(0)) {
    writeToChild(line);
  }
}

const clientLines = readline.createInterface({
  input: process.stdin,
  crlfDelay: Infinity,
});

clientLines.on('line', (line) => {
  const message = parseMessage(line);

  if (message?.method === 'server/discover') {
    process.stdout.write(
      `${JSON.stringify({
        jsonrpc: '2.0',
        id: message.id,
        result: {},
      })}\n`,
    );
    return;
  }

  if (message?.method === 'initialize') {
    initializeId = message.id;
    writeToChild(line);
    return;
  }

  if (message?.method === 'notifications/initialized') {
    // Never forward the client's own copy ahead of the server's initialize
    // response -- that is exactly the race this shim exists to close. The
    // notification is content-invariant, so if the response has already
    // been seen we simply (idempotently) emit our own synthesized copy;
    // otherwise there is nothing to do here -- flushQueuedClientMessages()
    // synthesizes it once the response actually arrives.
    if (initializeResponseSeen) {
      sendInitialized();
    }
    return;
  }

  if (initializeFailed) {
    emitErrorResponse(
      message?.id,
      'Graphtor MCP server failed to initialize; request rejected.',
    );
    return;
  }

  if (initializeId !== undefined && !initializeResponseSeen) {
    queuedClientMessages.push(line);
    return;
  }

  if (initializeResponseSeen) {
    sendInitialized();
  }

  writeToChild(line);
});

clientLines.on('close', () => {
  child.stdin.end();
});

const serverLines = readline.createInterface({
  input: child.stdout,
  crlfDelay: Infinity,
});

serverLines.on('line', (line) => {
  const message = parseMessage(line);

  if (message?.id === initializeId && !initializeResponseSeen && !initializeFailed) {
    if (message.result) {
      initializeResponseSeen = true;
    } else if (message.error) {
      initializeFailed = true;
      failQueuedClientMessages('Graphtor MCP server failed to initialize.');
    }
  }

  process.stdout.write(`${line}\n`);
  flushQueuedClientMessages();
});

child.stderr.pipe(process.stderr);

function handleChildTermination(reason) {
  if (initializeId !== undefined && !initializeResponseSeen && !initializeFailed) {
    // The child is gone (or never started) before it ever answered the
    // client's own `initialize` request -- as opposed to a message merely
    // queued behind it. Without this, the client would wait forever for a
    // response that will now never arrive.
    initializeFailed = true;
    emitErrorResponse(initializeId, reason);
  }

  if (queuedClientMessages.length > 0) {
    failQueuedClientMessages(reason);
  }

  // There is nothing left to proxy. Stop reading further client input so
  // the process can actually exit -- merely assigning process.exitCode does
  // not terminate the proxy while readline's read loop on stdin keeps the
  // event loop alive, which would otherwise leave the client waiting
  // forever for either a response or transport EOF.
  clientLines.close();
  process.stdin.destroy();

  // The wrapped child process itself may still be alive at this point --
  // e.g. it closed only its own stdin read end (or otherwise caused a
  // child.stdin write error) without ever exiting. If left running, its
  // still-open stdout/stderr pipes keep this proxy's own event loop alive
  // indefinitely, hanging the client even though every outstanding request
  // has already been answered above. Forcibly terminate it so the proxy
  // itself can exit promptly instead of merely waiting on the child to
  // eventually die on its own (or never). child.kill() is a safe no-op
  // when the process has already exited -- e.g. when this function is
  // invoked from the `close` handler below, where there is nothing left to
  // terminate.
  child.stdin.destroy();
  child.kill();
}

child.on('error', (error) => {
  console.error(`Failed to launch Graphtor MCP server: ${error.message}`);
  handleChildTermination(`Graphtor MCP server failed to launch: ${error.message}`);
  process.exitCode = 2;
});

child.stdin.on('error', (error) => {
  // writeToChild() writes directly to child.stdin. If the wrapped server
  // closes its input or exits while a write is pending -- including before
  // the shim ever writes its first byte -- Node emits `error` (e.g. EPIPE)
  // on the child.stdin Writable stream itself, separately from the
  // ChildProcess-level `error`/`close` events handled above. Without this
  // listener, Node treats it as an unhandled stream error and terminates
  // the whole proxy process before handleChildTermination() can run,
  // defeating the promised "every outstanding/queued request gets a
  // synthesized JSON-RPC error instead of hanging or crashing" guarantee.
  console.error(`Graphtor MCP server stdin write failed: ${error.message}`);
  handleChildTermination(`Graphtor MCP server stdin write failed: ${error.message}`);
  process.exitCode = 2;
});

child.on('close', (code, signal) => {
  handleChildTermination('Graphtor MCP server exited before responding.');

  if (signal) {
    console.error(`Graphtor MCP server terminated by signal ${signal}`);
    process.exitCode = 2;
    return;
  }

  process.exitCode = code ?? 0;
});
