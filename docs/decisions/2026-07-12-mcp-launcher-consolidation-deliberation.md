---
title: ".mcp.json Launcher Strategy Consolidation (npx / pwsh mix)"
description: "Deliberation for stash item FD962DCC. The workspace-root .mcp.json mixes plain npx launchers with pwsh -Command wrappers that guard an env var (tavily) and read the gh credential (github). Reframes the problem around the deprecated @modelcontextprotocol/server-github package, then evaluates standardizing on a launcher, per-OS variants, a client-native env-forwarding approach (secrets forwarded via each client's declarative env field rather than a shell wrapper or an assumption of ambient inheritance), and a Node helper. Recommends resolving the github server first (official hosted/local server or Copilot-CLI built-in) — which retires the deprecated package and removes the only command-substitution launcher — then consolidating toward npx + native binaries away from pwsh. Left at decision_status proposed because the client-set and github-server choices are operator/product tradeoffs and implementation mutates the live dogfood MCP config."
topic: "How should the harness resolve the mixed npx/pwsh launcher strategy in the workspace-root .mcp.json so the configuration stays cross-platform, keeps the gh credential read, and accounts for the deprecated github MCP package and differing per-client config locations?"
depth: "significant"
decision_status: "proposed"
doc_type: decision
source: docs/decisions/2026-07-12-mcp-launcher-consolidation-deliberation.md
source_stash_ids:
  - "FD962DCC"
backlog_items:
  - "077-F"
linked_artifacts:
  - ".mcp.json"
  - "templates/scripts/start.ps1.tmpl"
  - "templates/scripts/start.sh.tmpl"
  - "templates/scripts/.env.local.tmpl"
tags:
  - "mcp"
  - "cross-platform"
  - "secrets"
  - "launcher"
  - "primitive-5"
  - "operator-decision"
---

# .mcp.json Launcher Strategy Consolidation

## Status

**PROPOSED — operator decision required before implementation.** This
deliberation was produced autonomously under dark factory mode (P-017). It does
**not** modify the live `.mcp.json`. Implementation is deferred to the operator
because the `github`-server target and the supported-client set are
environment/product tradeoffs to ratify, and because editing the live dogfood
`.mcp.json` changes how auth reaches the GitHub server and can break MCP on the
next IDE/CLI restart — a state an AFK operator cannot recover from. Automatable
checks (JSON/schema validity, `PATH` resolution, `gh` failure handling, a direct
MCP handshake) remain possible now; only end-to-end IDE trust needs the operator
present (see Verification split).

## Problem (stash FD962DCC)

The workspace-root `.mcp.json` is the harness's declared canonical MCP surface,
with editor-local files (VS Code `.vscode/mcp.json`, Cursor `.cursor/mcp.json`)
as compatibility fallbacks. Copilot CLI and Claude Code read the root
`.mcp.json` (`mcpServers` key) directly. Today it mixes three launcher styles:

| Server | Launcher | Why |
|---|---|---|
| `backlogit`, `engram`, `graphtor-docs` | native binary on `PATH` | Installed executables; no wrapper needed. |
| `context7` | `npx -y @upstash/context7-mcp` | Plain npx; cross-platform; no secret needed. |
| `tavily` | `pwsh -NoProfile -Command "if empty TAVILY_API_KEY throw; npx -y tavily-mcp@latest"` | Fail-fast guard on a required env var, then npx. |
| `github` | `pwsh -NoProfile -Command "$env:GITHUB_PERSONAL_ACCESS_TOKEN = (gh auth token); npx -y @modelcontextprotocol/server-github"` | Sets the env var from the configured `gh` credential, then npx. |

The `pwsh -Command` wrappers do real work that a bare `command`/`args` entry
cannot express:

* **tavily** — a guard clause that fails fast with a clear message when the API
  key is absent (a usability nicety, not essential).
* **github** — a *dynamic command substitution* (`gh auth token`) evaluated at
  server-launch time. It reads the credential the local `gh` CLI already has
  configured (an OAuth token or PAT, persisted by `gh` in its own credential
  store) so the token is **not duplicated** into `.mcp.json`. Note the wrapper
  does **not** check whether `gh` failed or returned an empty value before
  launching, so a broken `gh` login yields an opaque server failure.

Two facts reframe the problem before any launcher decision:

* The npm package `@modelcontextprotocol/server-github` is **deprecated**
  ("Package no longer supported"). GitHub now ships an official
  `github/github-mcp-server` (local Go binary and a hosted remote server), and
  Copilot CLI has a **built-in** GitHub MCP server. Optimizing a `pwsh` wrapper
  around a retired package may be optimizing the wrong thing.
* The concern `pwsh` couples the config to PowerShell Core. On a POSIX dev box
  without `pwsh` installed, the `tavily` and `github` servers fail to launch.

The stash asks whether to (a) standardize on one launcher, (b) adopt an
alternate cross-platform approach, or (c) generate per-OS `.mcp.json` variants.

## Constraints

1. **Config-location differs by client, and the root file is not committed.**
   Copilot CLI and Claude Code read the root `.mcp.json`; VS Code reads
   `.vscode/mcp.json` (`servers` key); Cursor reads `.cursor/mcp.json`. A "single
   file for all clients" assumption is false. Moreover the root `.mcp.json` is
   **gitignored / untracked** (`.gitignore:24`, commit `2b34b8c` "stop tracking
   local MCP config"), so it is a **developer-local** artifact: a fresh clone has
   **no** root config until one is created locally, and an existing clone may
   keep a stale local copy. The IDE-reads-it-before-any-start-script race applies
   to whatever local `.mcp.json` exists on workspace open. For Copilot CLI
   launched *by* `start.ps1`/`start.sh`, the script runs before config load, so a
   start-script-generated config is safe there but not for IDE-direct launches.
2. **Avoid duplicating the token.** The `github` server reads the credential
   `gh` already holds rather than copying a token into `.mcp.json`. Any solution
   should preserve that property or accept a documented UX/secret-hygiene change.
3. **Client-agnostic.** The `env`/`inputs`/`${command:...}` interpolation
   features differ across MCP clients; a solution that relies on one client's
   extension is not portable across the IDEs the harness targets.
4. **Environment-agnostic product.** autoharness targets Windows, macOS, and
   Linux dev boxes. The chosen default must degrade gracefully, not hard-fail,
   on any of them.

## Prerequisite question (evaluate before choosing a launcher)

Because `@modelcontextprotocol/server-github` is deprecated, the first decision
is **whether the custom `github` entry should exist at all**, not how to wrap
it:

* **Copilot CLI** ships a built-in GitHub MCP server → the custom entry may be
  redundant there. Caveat: GitHub's install guide says the built-in server
  enables **read-only** tools by default, with additional toolsets requiring
  explicit CLI flags — so treating it as a drop-in for the custom entry can
  silently remove write/toolset functionality unless those flags are set.
* Migrating to GitHub's **hosted remote** `github-mcp-server` removes the local
  process and the `pwsh` wrapper. But remote **OAuth is not universal**: GitHub's
  support matrix lists remote OAuth for supported Copilot IDE hosts, while
  Copilot CLI, Claude Code, and Cursor still require a **PAT** for the hosted
  server. For those clients the hosted option re-introduces token
  provisioning/forwarding, so it does not by itself satisfy the
  no-duplication/client-agnostic goals — the choice must be split by client/auth
  capability.
* Migrating to the **official local** `github-mcp-server` binary replaces `npx`
  with a native binary (like `backlogit`/`engram`). As of GitHub MCP Server
  v1.5.0 (2026-06-27) the stdio binary has **built-in OAuth**: `github-mcp-server
  stdio` starts on github.com with no PAT, client ID, or `env` block, and a
  static token is only an optional override. **Lifecycle caveat:** per the
  official `oauth-login.md`, the OAuth token is held **in memory only** (nothing
  written to disk), so **every server-process restart requires a fresh
  interactive browser/device authorization**. That is a material cost given this
  document's AFK/restart concern — a static token override trades the
  no-secret-on-disk property for unattended restarts.

Any of these removes the only launcher that genuinely needs command
substitution. That would shrink the launcher problem down to `tavily`'s optional
guard, which is trivially expressible without `pwsh`.

## Options

### Option A — Retain the current mixed strategy; formalize `pwsh` as a prerequisite

Keep `tavily`/`github` as `pwsh -NoProfile -Command` wrappers and plain
`command` entries for the rest (this is essentially today's state, not a
consolidation).

* **Pro:** No config change. Preserves the guards and the `gh` credential read.
* **Con:** `pwsh` being *installable* on macOS/Linux is not the same as being
  *available* — those OSes do not ship it, so `tavily`/`github` hard-fail until
  the user installs `pwsh`, contrary to Constraint 4. A start-script warning does
  not help IDE-direct launches. Does not address the deprecated `github` package.

### Option B — Standardize on `sh -c` wrappers

Use `sh -c 'export GITHUB_PERSONAL_ACCESS_TOKEN=$(gh auth token); exec npx ...'`.

* **Pro:** `sh` is native on macOS/Linux; preserves the credential read.
* **Con:** Windows does not ship `sh`. Git Bash may expose it only under a
  suitable PATH/install; WSL requires invoking through `wsl.exe` (`wsl sh -c`),
  not a bare `sh` on the Windows PATH. Since the primary dogfood box is
  Windows-first, this *inverts* the portability problem.

### Option C — Per-OS `.mcp.json` variants selected by the start script

Ship `.mcp.windows.json` + `.mcp.posix.json`; `start.ps1` / `start.sh` copy the
right one to `.mcp.json`.

* **Pro:** Each variant uses the most native launcher. Because the root
  `.mcp.json` is already gitignored and developer-local (not committed),
  producing it per OS fits the existing "local artifact" model rather than
  overwriting a tracked file.
* **Con:** No generator exists today — the file appears hand-authored locally,
  and ignoring a file does not make it generated. This option therefore requires
  *building* a start-script generator first. For IDE-direct launches on a fresh
  clone there is **no** config until that generator runs (Constraint 1), and an
  existing clone may keep a stale local variant. Doubles the maintained source
  surface. Fragile and non-obvious.

### Option D — Drop wrappers; forward secrets via each client's env mechanism

All servers use plain `command`; secrets (`GITHUB_PERSONAL_ACCESS_TOKEN`,
`TAVILY_API_KEY`) are supplied through the MCP client's own environment policy
rather than a shell wrapper. **This is not zero-config or uniformly ambient.**
Env inheritance is client-specific: VS Code-style hosts pass the parent process
environment to local servers, but **Copilot CLI auto-inherits only `PATH`** for
local/STDIO servers — every other variable must be forwarded explicitly in the
server's declarative `env` field. The portable, shell-free mechanism is therefore
the standard per-server `env` field carrying a **non-literal reference**
(`${input:...}` in VS Code-style config, `${VAR}` for Copilot CLI) — not a
literal secret and not an assumption of ambient inheritance.

* **Pro:** Launcher-free config; no OS shell dependency; uses the standard MCP
  `env` field every client already supports.
* **Con:** Not a single copy-paste value across clients — the forwarding syntax
  differs per client, so the `env` field must be set per each targeted client's
  policy. For IDE-direct launches the user must still ensure the source variable
  is set in their environment. Loses the automatic `gh` credential read unless
  paired with the github-server migration above (which supplies its own auth).

### Option E — Small cross-platform Node launcher (dependency-neutral)

Node/npm is already required by every `npx` entry. A tiny repo-local Node script
could validate `gh auth token` (checking for failure/empty output), set the
environment, and spawn the target server with inherited stdio on all three OSes.

* **Pro:** Adds **no new** prerequisite beyond the Node that npx already needs;
  works identically on Windows/macOS/Linux; can add the missing `gh`
  failure/empty checks.
* **Con:** Introduces a maintained launcher script (path resolution, trust). May
  be unnecessary if the `github` migration removes the only command-substitution
  case; strongest as a fallback if a custom local github launcher must remain.

## Recommendation

Sequence the decision, don't jump to a launcher:

1. **Resolve the `github` server first, routed by client/auth capability.** Retire
   the deprecated `@modelcontextprotocol/server-github` and migrate to GitHub's
   official server. There **is** one client-agnostic PAT-free option: the official
   local `github-mcp-server stdio` binary performs OAuth itself and launches
   without a PAT on each targeted stdio client (Copilot CLI, Claude Code, Cursor),
   at the cost of an in-memory token that re-authorizes on each restart (a static
   token avoids the re-auth but reintroduces a PAT). Only the **hosted-remote**
   path forces the per-client auth split: OAuth on supported Copilot IDE hosts but
   a **PAT** on Copilot CLI / Claude Code / Cursor. Copilot CLI additionally has a
   built-in GitHub server. Pick per the client(s) actually targeted. Any of these
   removes the only launcher that needs command substitution.
2. **With `github` resolved, the launcher question narrows to secret
   forwarding.** The only remaining wrapper is `tavily`'s optional API-key guard.
   Dropping the `pwsh` wrapper does **not** by itself make `TAVILY_API_KEY`
   available on every client: env inheritance is client-specific (VS Code-style
   hosts pass the ambient environment, but Copilot CLI auto-inherits only `PATH`
   and needs other vars forwarded explicitly). Replace the shell wrapper with the
   standard declarative per-server `env` field carrying a **non-literal
   reference** (`${input:...}` in VS Code-style config, `${VAR}` for Copilot CLI),
   set per each targeted client's env policy — no `pwsh`, no `sh`, and no literal
   secret duplicated in config. Only after that forwarding is in place is the
   wrapper safe to drop. If a custom local launcher must remain for any server,
   use a small Node helper (Option E) rather than adding a `pwsh`/`sh` OS
   dependency.

Net direction: **npx + native binaries + the official GitHub MCP server**, which
consolidates *away* from `pwsh` while staying cross-platform — the outcome the
stash was reaching for. Option A (keep `pwsh`) is the smallest change but does
not satisfy the cross-platform constraint and leaves the deprecated package in
place.

This is a recommendation with `decision_status: proposed`, not an applied
change, because:

* Choosing among hosted-remote vs. local-binary vs. Copilot-CLI-built-in for
  `github`, and deciding which client set the harness commits to supporting,
  are environment/product tradeoffs the operator should ratify.
* Implementation edits the **live** dogfood `.mcp.json`; a wrong edit changes how
  auth reaches the GitHub server and can break MCP on the next IDE/CLI restart,
  which an AFK operator cannot recover from.

## Verification split (what can be checked without the operator)

Deferring *ratification* does not mean nothing is verifiable. Separate:

* **Automatable now:** JSON well-formedness and schema of `.mcp.json`; that each
  `command` resolves on `PATH`; that the launcher handles `gh` failure/empty
  output; a direct MCP `initialize` handshake against a chosen server.
* **Requires operator-present restart:** end-to-end IDE trust/authentication and
  confirming every server reconnects in the live client.

## Deferred implementation checklist (for operator ratification)

1. Decide the `github` server target and route by client/auth capability: hosted
   remote (OAuth on Copilot IDE hosts; **PAT** on Copilot CLI / Claude Code /
   Cursor), official local stdio binary (built-in OAuth, but in-memory token →
   re-auth on every restart, or a static token override for unattended restarts),
   or Copilot-CLI built-in. Update the entry accordingly.
2. Replace `tavily`'s `pwsh` wrapper with a standard per-server `env` field that
   forwards `TAVILY_API_KEY` via a non-literal reference, set per each targeted
   client's env policy (VS Code-style ambient vs Copilot CLI explicit `env`); do
   not rely on ambient inheritance alone, since Copilot CLI forwards only `PATH`.
3. **Pin every `npx`-launched server to an exact reviewed version** (not `-y
   ...@latest`) with an explicit update process. Both `tavily`
   (`npx -y tavily-mcp@latest`) and `context7` (`npx -y @upstash/context7-mcp`)
   currently resolve moving releases, so a newly published or compromised release
   would execute immediately and launches are non-reproducible. Where the client
   or config forwards `TAVILY_API_KEY` to the process (see step 2), such a release
   also runs with the secret in its environment — so pin `tavily` regardless of
   forwarding mechanism. Prefer an official hosted service where one is available.
4. Add `gh` failure/empty-output handling wherever a launcher still reads the
   credential.
5. Run the automatable checks above in CI or locally.
6. Restart the IDE/CLI and confirm every MCP server connects (operator-present);
   for local stdio OAuth, verify the restart re-authorization flow specifically.
7. Update `docs/environment-setup.md` to match the chosen strategy and note any
   remaining external prerequisite.

## Out of scope

* Building an `.mcp.json` **template** for target-workspace install. The harness
  does not currently ship an `.mcp.json.tmpl`; the workspace-root `.mcp.json` is
  a dogfood artifact. Templatizing MCP registration is a separate, larger item.
* Fixing the operator-reported `graphtor-docs` `graph.db` open failure. That is
  tool-managed local daemon state (reindex/reset), not a repository change.
* Resolving the `.gitignore` inconsistency: lines 19-20 comment that "The root
  `.mcp.json` ... is tracked," but line 24 actually ignores it and commit
  `2b34b8c` stopped tracking it. Whether the root `.mcp.json` should be tracked
  (canonical, committed) or generated-and-ignored (local) is itself an operator
  decision that gates the per-OS-variant option above; flagged here, not changed.
