---
problem_type: cli-security
category: deterministic-gates
root_cause: config-driven-subprocess-execution-and-yaml-killswitch-semantics
tags: [gates, subprocess, command-injection, argv-array, kill-switch, yaml-null, fail-open]
created: 2026-07-01
shipment: 052-S
---

# Config-Driven Subprocess Validation Gates: Injection Safety and Kill-Switch Semantics

## Problem

Phase 1 of the deterministic gates engine executes operator-authored gate
`command` strings as subprocesses, interpolating a per-file `{file_path}`. Two
classes of hard-won correctness issues emerged that are easy to get subtly wrong
and were only surfaced by adversarial review:

1. **Command injection surface.** A naive `command.format(file_path=…)` followed
   by `shell=True` (or splitting after substitution) lets a crafted path
   containing `;`, `&&`, `$(...)`, or backticks inject a second command or alter
   argv arity.
2. **Kill-switch that silently fails closed.** The documented rollback is
   "remove **or empty** the `lifecycle_hooks` block." In YAML an *emptied* key
   (`lifecycle_hooks:`) parses as `null`. A strict schema (`type: object`) and a
   loader that treats "key present" as "gates enabled" then reject/attempt to
   validate `null`, so the advertised kill-switch actually breaks task completion
   instead of disabling gating.

## Root Cause

- Injection: substitution order and shell usage, not the command content itself.
- Kill-switch: mismatch between human-facing docs ("empty the block") and the
  YAML/schema/loader reality of what "empty" parses to.

## Solution

- **Tokenize before substitute, never `shell=True`.** `shlex.split(template)`
  first, then substitute placeholders *per argv token*, so a substituted value
  always lands inside exactly one pre-existing argv element and can never change
  argv arity. Execution is always `shell=False`. A negative test asserts a path
  full of shell metacharacters is passed inertly.
- **Normalize emptied blocks to "absent" before validation, and accept `null` in
  the schema.** The loader treats `null` / `{}` `lifecycle_hooks` (and
  `telemetry`) as absent → disabled; the JSON Schema declares
  `type: ["object", "null"]` so an emptied block still validates. This makes the
  kill-switch reliable and preserves the fail-open-to-current invariant.
- **Derive `enabled` from configured gates**, not from key presence, so a block
  with no `validation_gates` is honestly reported as disabled.
- **Keep runtime state out of the tracked tree.** Per-workspace runtime
  artifacts (`gate-state.json`, `gate-force-audit.log`) live under gitignored
  `.autoharness/gates/`; only the intentional circuit-breaker checkpoint is
  committed (to `docs/memory/`).

## Prevention

- For any config-driven command execution: argv-array only, substitute per-token,
  add an injection negative test as an acceptance-blocking criterion.
- When documenting a "remove or empty" kill-switch, test the *emptied* (YAML-null)
  form end-to-end — not just the fully-absent form — against schema + loader.
- Runtime/audit artifacts written into an install-managed directory must be
  gitignored so tool invocations never dirty a consumer's working tree.
