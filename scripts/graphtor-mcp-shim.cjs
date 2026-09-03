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
  if (!initializeResponseSeen || queuedClientMessages.length === 0) {
    return;
  }

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

child.on('error', (error) => {
  console.error(`Failed to launch Graphtor MCP server: ${error.message}`);
  failQueuedClientMessages(`Graphtor MCP server failed to launch: ${error.message}`);
  process.exitCode = 2;
});

child.on('close', (code, signal) => {
  if (queuedClientMessages.length > 0) {
    failQueuedClientMessages('Graphtor MCP server exited before responding.');
  }

  if (signal) {
    console.error(`Graphtor MCP server terminated by signal ${signal}`);
    process.exitCode = 2;
    return;
  }

  process.exitCode = code ?? 0;
});
