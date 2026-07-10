# Git hooks (opt-in)

autoharness dogfoods its own unified CI + local-gating primitive (P-019). This
directory holds the repository's opt-in **pre-push quality-gate hook**, the
local half of that primitive. Because remote CI is intentionally minimal and
Linux-only, running the gates locally before push is the primary safety net.

The hook runs autoharness's real gates and blocks the push on failure:

* the stdlib unittest suite — `PYTHONPATH=src python -m unittest discover -s tests`
* `markdownlint "**/*.md"` — skipped with a warning when not installed

It is a single deterministic pass (no retry loop, circuit-breaker compatible).

## Activation (opt-in)

The hook is **committed but inactive by default** — nothing sets `core.hooksPath`
for you, so normal pushes are never intercepted until you opt in. To activate:

```sh
git config core.hooksPath .githooks
```

Git invokes the hook by the exact name `.githooks/pre-push` (no extension) on
every platform, including Git for Windows, using its bundled POSIX shell. That
extensionless `pre-push` file is a small dispatcher that execs `pre-push.sh`, so
the single `core.hooksPath` command above is all that is needed — on Linux,
macOS, and Windows alike.

The `pre-push.ps1` script is provided for manual invocation or PowerShell-based
wiring (`pwsh -NoProfile -File .githooks/pre-push.ps1`); git itself always runs
the POSIX dispatcher.

Bypass once (e.g. an emergency push): `git push --no-verify`.

Deactivate: `git config --unset core.hooksPath`.
