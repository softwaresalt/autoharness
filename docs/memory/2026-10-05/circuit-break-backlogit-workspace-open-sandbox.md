---
type: circuit-breaker
timestamp: 2026-10-05T23:11:30Z
agent: "Orchestrator"
skill: "direct"
breaker_type: universal
operation: "backlogit workspace open under Copilot CLI local sandbox"
attempts: 3
identity: "backlogit-open-workspace-ops-dir-handle-denied"
---

# Circuit Breaker - backlogit workspace open under local sandbox

## Failure Chain

### Attempt 1

- Exit/timeout: non-zero
- Operation evidence: `backlogit shipment list`, cwd repo root, phase resume-194-S preflight
- Normalized message: resolve workspace root: Access is denied
- Diagnostic artifact: none

### Attempt 2

- Exit/timeout: 1
- Operation evidence: `backlogit shipment get 194-S` / `backlogit stash list`, cwd repo root, phase resume-194-S preflight
- Normalized message: open workspace: recover shipment operations: validate shipment operation journals: resolve shipment operations directory handle: Access is denied
- Diagnostic artifact: none

### Attempt 3

- Exit/timeout: 0 (pipeline), backlogit error emitted
- Operation evidence: `backlogit shipment get 194-S`, cwd repo root, phase resume-194-S preflight
- Normalized message: identical to attempt 2; TEMP still resolves inside the sandbox AppContainer, so sandbox remained enabled
- Diagnostic artifact: none

## Context

- Files involved: `.backlogit/ops/` (empty, readable, ACL readable from shell)
- Provisional-to-concrete identity link: attempt 1 was a path-rule gap (fixed by operator); attempts 2-3 share the concrete handle-denial identity
- Logging controls: no raw capture; redacted summaries only
- Resolution: Circuit breaker triggered. Awaiting operator guidance.
- Suggested next steps: operator runs `/sandbox disable` for the session (saved policy unchanged), then `resume 194-S`; optionally report backlogit AppContainer handle incompatibility upstream.
