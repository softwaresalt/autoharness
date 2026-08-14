---
title: "Plan 2 V1 remote control plane — security boundaries, accepted risks, and operational recovery"
status: active
related_feature: 121-F
related_shipment: 130-S
doc_type: design
source: docs/design-docs/2026-08-14-plan2-v1-remote-control-security-operations.md
linked_artifacts:
  - "docs/design-docs/2026-08-09-deferred-gradio-devtunnel-remote-control-plan.md"
  - "docs/design-docs/2026-08-12-supervisor-observability-rollout-rollback.md"
tags: ["plan-2", "v1", "security", "operations", "remote-control"]
---

# Plan 2 V1 Remote Control Plane — Security Boundaries, Accepted Risks, and Operational Recovery (121.001-T)

## Summary

This is the operator-facing security and operations reference for
`src/autoharness/remote/`, the Plan 2 V1 remote control plane shipped in
`130-S`. It documents the seven operator rulings that bound V1 scope, the
exact Observe + Steer capability set exposed, the accepted V1 risks (most
importantly devtunnel-only authentication), the credential-compromise
containment procedure, and the deployment/rollback contract. It is the
authoritative "what V1 actually does and does not do" reference for anyone
enabling `autoharness[remote]`.

Nothing in this document authorizes any expansion of scope. Where this
document and `docs/design-docs/2026-08-09-deferred-gradio-devtunnel-remote-control-plan.md`
(the original Plan 2 design + threat model) appear to differ, the seven
operator rulings below are authoritative for V1 — the earlier document's
open questions (§12) are resolved by those rulings, not superseded wholesale.

## 1. The seven operator rulings (V1 scope, locked at planning)

| # | Ruling | V1 disposition |
|---|---|---|
| 1 | **Combined Observe + Steer**, not Observe-only | V1 ships both; a separate Observe-only release was considered and rejected — see `121-F` goals. |
| 2 | **Loopback-only binding** | The listener binds `127.0.0.1`/`::1`/`localhost` only, enforced by `autoharness.remote.tunnel.validate_loopback_bind()`. Any other bind host fails closed with `NonLoopbackBindError`. Non-negotiable; not configurable. |
| 3 | **Devtunnel authenticated access control is the SOLE V1 identity mechanism** | No independent application-layer identity verification exists in V1 (see §3, accepted risk). This is an explicit, deliberate acceptance of design-doc §12 Q3 risk, not an oversight. |
| 4 | **Closed structured command vocabulary; no raw shell** | Every remotely reachable command is enumerated in `autoharness.remote.contracts.ObserveCommand`/`SteerCommand`. `ensure_remotely_dispatchable()` fails closed (`UnknownRemoteCommandError`/`LocalOnlyCommandError`) for anything else. There is no raw-stdin passthrough anywhere in this package. |
| 5 | **No browser terminal** | Permanently out of scope (T6 in the design doc); `autoharness.remote.ui` contains no terminal/code-editor/shell component (see the 121.003-T spike, F1/F3). |
| 6 | **No separate remote retention; local journal authoritative** | `autoharness.remote.observe.ObserveService`/`BoundedOutputTail` are stateless readers over Plan 1's own event bus and journal. There is no remote-side database, file, or cache that persists session content. |
| 7 | **Four-tier authorization model (Observe/Steer/Approve/Privileged); only Observe/Steer exposed in V1** | `autoharness.remote.contracts.AuthorityTier` defines all four tiers; `REMOTE_EXPOSED_TIERS = {OBSERVE, STEER}` is the only remotely reachable subset, enforced structurally (not by configuration) via `ensure_remotely_dispatchable()`. `LocalOnlyCommand` mirrors Plan 1's `GATED_ACTION_CATALOG` exactly, with a module-load-time drift-guard assertion. |

## 2. Exact V1 Observe + Steer scope

**Observe (read-only, `AuthorityTier.OBSERVE`):**

| Command | Behavior |
|---|---|
| `status` | Current supervisor `Phase` |
| `phase` | Current supervisor `Phase` (alias surface for `status`) |
| `progress` | Current journal cursor (`journal.read_own_cursor()`) |
| `output_tail` | Bounded tail of already-redacted `ChildOutput` lines, with `truncated`/`dropped_count` backpressure signaling |
| `journal_tail` | Current journal cursor, exposed under the `journal_tail` command name |

**Steer (state-changing, `AuthorityTier.STEER`):**

| Command | Behavior |
|---|---|
| `pause` | Routes through `ConsoleApprovalService.handle_command("pause")`; legal only while `Phase.RUNNING` and not already paused |
| `resume` | Routes through `ConsoleApprovalService.handle_command("resume")`; legal only after a prior `pause` |
| `cancel` | Transitions the state machine to `Phase.CANCELLING` (legal only from a pre-terminal, cancellable phase) and journals a `CancelRequested` event |
| `request_checkpoint` | Appends a `JournalCheckpoint` event with a dispatcher-local logical sequence number; illegal once the session has reached a terminal phase |

**Never remotely reachable in V1** (`AuthorityTier.APPROVE`/`AuthorityTier.PRIVILEGED`): approval resolution, `session_restart`, `force_unlock`, git push/PR merge/shipment claim, credential use, or any filesystem write outside the workspace. These remain exclusively local-console operations; Plan 2 grants no new authority over them.

## 3. Accepted V1 risk: devtunnel-only authentication

**This is an accepted risk, not a silent omission.** V1 relies entirely on
Microsoft devtunnel's own authenticated access control (tenant/allow-list
enforcement at the tunnel layer) as the sole identity mechanism for the
remote control plane. There is **no independent application-layer identity
verification** inside `autoharness.remote` in this release.

Consequences operators must understand:

* Anyone who can authenticate through the configured devtunnel access
  control reaches the full Observe + Steer surface for the bound
  workspace/session. There is no secondary factor inside the application.
* `autoharness.remote.binding.WorkspaceSessionBinding` prevents a request
  from being replayed against a *different* workspace/session than the one
  it was issued for (cryptographic HMAC binding, §4) — it does **not**
  substitute for identity verification of the *caller*. A binding-scoped
  token proves "this request is for workspace X," not "this caller is
  authorized to be here" beyond what devtunnel already established.
* Application-layer identity verification (design doc §12 Q3, §4) is
  **explicitly deferred future work**, tracked separately. It must not be
  silently added as a "hardening" change without its own operator ruling,
  spike, and review — doing so would change the V1 security model without
  the accompanying threat-model update this document exists to make
  explicit.

## 4. Cryptographic workspace/session binding

Every Observe/Steer request carries a `workspace_id`/`session_id` pair and
an HMAC-SHA256 binding token (`WorkspaceSessionBinding.issue_token()`).
`WorkspaceSessionBinding.verify()` fails closed (`BindingMismatchError`,
one exception type for every failure mode) on: workspace mismatch, session
mismatch, missing token, token mismatch (constant-time comparison via
`hmac.compare_digest`), future-dated `issued_at`, and stale requests
(default 300s freshness window). The binding secret is generated locally
via `secrets.token_bytes(32)` and never derived from request data, so a
token issued for one workspace can never validate against another by
construction. The binding grants **no** Approve/Privileged authority — it
is purely an anti-confusion/anti-replay control scoped to Observe/Steer.

## 5. Rate limiting and request size bounds

* **16 KiB maximum request size** (`autoharness.remote.contracts.MAX_REQUEST_BYTES`,
  `validate_request_size()`) — oversized payloads fail closed with
  `RequestTooLargeError` before any further processing.
* **30 requests/minute, burst of 5** (`autoharness.remote.rate_limit.TokenBucketRateLimiter`,
  `RATE_LIMIT_PER_MINUTE`/`RATE_LIMIT_BURST`) — the limiter never blocks or
  queues; it grants a token immediately or raises `RateLimitExceededError`
  immediately. A slow or abusive remote consumer can never stall the
  locally supervised session.

## 6. Audit privacy: role-based, never workstation identity

`autoharness.remote.contracts.RemoteRequest.role` is a coarse authorization
role string (default `"remote_operator"`) — it is deliberately never a
workstation hostname, IP address, or other machine-identifying value. This
is an explicit audit-privacy requirement from the shipment: journaled
remote activity records *what role acted*, not *which physical machine or
network location it came from*.

## 7. Redaction: single choke point, no second pass

`autoharness.remote.observe.BoundedOutputTail` subscribes to `ChildOutput`
events delivered by `autoharness.supervise.events.EventBus`. `EventBus.emit()`
has already applied `autoharness.supervise.redact.redact_record()` before
any subscriber — including this one — ever sees the event. The Plan 2
Observe surface performs **no** second redaction pass; it only ever
observes data that was already redacted by Plan 1's own choke point. If
redaction fails closed upstream, the event is dropped before it ever
reaches the remote surface.

## 8. Loopback binding and devtunnel lifecycle

* `autoharness.remote.tunnel.validate_loopback_bind()` accepts only
  `127.0.0.1`, `::1`, and `localhost` (case-insensitive); every other host,
  including `0.0.0.0`/`::`/any LAN address, is rejected with
  `NonLoopbackBindError`. This check runs at `TunnelLifecycle` construction
  time — a lifecycle can never be built pointed at a non-loopback host.
* `autoharness.remote.tunnel.resolve_devtunnel_executable()` fails closed
  with `DevtunnelUnavailableError` (an actionable, "install/configure
  devtunnel" message, never a generic error) when the `devtunnel` CLI is
  not present on `PATH`.
* `TunnelLifecycle.start()`/`.teardown()` are both idempotent.
  `teardown()` is always safe to call before `start()`, safe to call
  multiple times, and is designed to run from a `finally` block on a crash
  path so an orphaned tunnel never survives an unhandled exception in the
  guarded body (see `TunnelLifecycleTests` in `tests/test_remote_tunnel.py`
  for the pinned crash-path contract).
* V1 does **not** implement a corporate-network fallback or a separate
  preflight requirement beyond devtunnel resolution itself — this is a
  deliberate scope limitation (`121.005-T` acceptance criteria), not an
  oversight. Operators in environments where devtunnel is blocked at the
  network layer should expect V1 to fail closed with the
  `DevtunnelUnavailableError`/transport-error path rather than silently
  degrade to an alternate transport.

## 9. Credential-compromise containment

Plan 2 introduces no new credential material of its own, but it does
introduce a new remote reachability path to a process that already holds
the operator's live GitHub credential (the supervised Copilot CLI child).
The credential-compromise response runbook is unchanged from
`docs/design-docs/2026-08-09-deferred-gradio-devtunnel-remote-control-plan.md`
§11.1 and is restated here for operational visibility:

1. **Contain first** — tear down the tunnel and terminate remote sessions.
2. **Revoke at the issuer** — `gh auth refresh` is explicitly **not**
   remediation; it re-authorizes scopes on the same credential and leaves
   an exposed secret valid. The exposed PAT/OAuth token must be revoked at
   GitHub.
3. **Issue a replacement** credential with least-privilege scopes.
4. **Purge the old credential from every process environment** — a
   controlled supervisor session restart is explicitly permitted, and
   required where the old value is still resident in a live process, even
   at the cost of in-progress agent work.
5. **Purge at-rest copies** (`.env.local`, shell history, CI/secret
   stores, local credential helper caches).
6. **Journal the incident** — record detection, containment, revocation
   confirmation, replacement issuance, restart, and purge with timestamps.
   Journal the event, never the credential value.
7. **Verify** the old credential is rejected by the issuer and the
   supervised session is operating on the replacement.

Rolling back the Plan 2 remote surface (uninstalling `autoharness[remote]`,
disabling remote configuration, tearing down the tunnel) does **not**
discharge steps 2-7 above — a disabled remote surface does not invalidate
a credential that has already left the machine.

## 10. Deployment and rollback

* **Optional extra**: `pyproject.toml` declares
  `[project.optional-dependencies] remote = ["gradio>=4.0"]`. The base
  `autoharness` install never requires gradio or a devtunnel client;
  `autoharness.remote.ui` imports `gradio` lazily, only inside
  `build_gradio_app()`.
* **Disabled by default**: nothing in this package starts a listener, a
  tunnel, or a Gradio app as a side effect of import. Enabling the remote
  control plane requires explicit operator action.
* **Rollback**: uninstalling the `remote` extra, or simply never invoking
  the remote entry point, leaves the local Plan 1 supervisor completely
  unaffected — Plan 2 adds only an optional adapter over existing Plan 1
  services and introduces no new write paths, no new event types, and no
  change to Plan 1 behavior.

## 11. Explicitly deferred and permanently out of scope

| Item | Disposition |
|---|---|
| Application-layer identity verification beyond devtunnel access control | Deferred future work (design doc §12 Q3); requires its own operator ruling before it may be added |
| Approve/Privileged remote exposure | Local-only, permanently in V1; no roadmap item in `121-F` changes this |
| Browser terminal streaming | Permanently out of scope (T6) |
| Corporate-network fallback / separate preflight | Not implemented in V1 (`121.005-T`); devtunnel-unavailable fails closed |
| Separate remote retention store | Never added; local journal remains the sole source of truth |
| Multi-workspace fan-out from a single tunnel | Out of scope; one workspace per tunnel, per the original design doc §9 |
