---
type: session-memory
agent: Ship
date: 2026-07-01
session: backlog-to-shipped — telemetry-capture core (Phase 2, autonomous)
shipment: 055-S
tags: [telemetry, phase-2, evaluation, ship, closure, autonomous, backlog-integrity]
---

# Ship Session — Telemetry-Capture Core (051-F Phase 2)

## Summary

Shipped shipment **055-S** — the Phase-2 telemetry-capture core (feature 051-F,
tasks **051.001 + 051.003 + 051.006**): `autoharness telemetry record` emitting
structured Execution Epochs to a repo-local SQLite aggregator and an emit-only
JSONL stream. Merged via PR
[#122](https://github.com/softwaresalt/autoharness/pull/122) as merge commit
`a36ea8335db18bc7487dafd2f7ffa374e0e3e11a`. Includes the reviewed Phase-2 plan
(`docs/plans/2026-07-01-telemetry-eval-phase2-plan.md`).

## What shipped

New decoupled `src/autoharness/telemetry/` package (epoch model + 4 payload
classes, typed TelemetryConfig with workspace path confinement, WAL SQLite sink
with busy_timeout+retry, atomic emit-only JSONL sink, fail-open dispatch),
`telemetry record` CLI, `.gitignore` for `.autoharness/metrics/`, config-template
activation, and `docs/telemetry-reference.md`.

## Review

Extensive multi-model adversarial review (Claude Sonnet 4.6 + GPT-5.4 +
security-review). No security vulns. Progressive robustness findings fixed across
3 cycles: fail-open/no-op ordering; comprehensive payload error normalization
(bad JSON, wrong shapes, bad/overflowing coercion, non-UTF-8, malformed YAML) →
controlled exit 2; workspace path confinement (reject `..`/absolute-escape);
atomic JSONL append + short-write detection (POSIX `O_APPEND`; Windows
`CreateFileW`/`FILE_APPEND_DATA`); SQLite busy_timeout + bounded retry; real
gitignore hard-gate test. Final: **169 passed, 51 subtests**.

## Backlog-integrity incident + recovery (LEARNING)

**Mistake:** shipment 055-S was assembled with the **parent feature 051-F**
included alongside the three capture-core tasks. `backlogit shipment ship`
archived the parent AND cascaded to archive ALL its children — including the
still-deferred, UNIMPLEMENTED tasks 051.002 (sizing gate), 051.004 (eval runner),
051.005 (reviewer matrix). They were marked `archived/done` despite not existing.

**Recovery:** `archived` is terminal (no `move` transitions). Created a fresh
carry-forward feature **055-F** with tasks **055.001** (eval runner), **055.002**
(reviewer matrix), **055.003** (sizing gate, blocked on external backlogit
`--size`) so the backlog again reflects the real remaining Phase-2 work. The
deferred scope was never lost — it is fully specified in the Phase-2 plan
(Shipment B and C) and the #122 PR body.

**Rule for the future:** a shipment that ships only SOME of a feature's tasks
must NOT include the parent feature ID — including the parent causes
`shipment ship` to archive the whole feature subtree. Include only the tasks
actually delivered; archive the parent feature only when its final task ships.

## Closure

`backlogit shipment ship 055-S --sha a36ea83…` → shipped. Capture core is on
main. No release obligations (feature; no tag/publish).

## Autonomous session context

Cycle 4/5 of the autonomous overnight run. Remaining backlog: **055-F** (Phase-2
Shipments B & C — eval runner, reviewer matrix, sizing gate); **053-F**
(model_routing removal — blocked on operator intent). Approaching the
Orchestrator 5-cycle checkpoint.
