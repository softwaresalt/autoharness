---
title: "DEFERRED Design & Operational Plan — Gradio + Microsoft devtunnel Remote Control Plane (Plan 2)"
date: "2026-08-09"
description: "DEFERRED to a later autoharness version. Design and operational plan for remote control of a supervised Copilot CLI session via a Gradio UI exposed through a Microsoft devtunnel: remote threat model, authentication, authorization, workspace binding, streaming/control protocol, remote approvals, tunnel lifecycle, multi-user/session concerns, deployment, rollback, and the credential-compromise response runbook (issuer-side revocation and replacement; `gh auth refresh` is explicitly not rotation). NO implementation feature, tasks, or shipment exist for this plan."
doc_type: design-doc
status: DEFERRED
source: docs/design-docs/2026-08-09-deferred-gradio-devtunnel-remote-control-plan.md
plan_id: "PLAN-2"
model_route:
  model_family: claude-opus-5
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md"
tags: ["DEFERRED", "plan-2", "gradio", "devtunnel", "remote-control", "threat-model", "design"]
---

# DEFERRED — Gradio + Microsoft devtunnel Remote Control Plane (Plan 2)

> **STATUS: DEFERRED to a later autoharness version.**
>
> This is a **design and operational plan only**. There is **no implementation
> feature, no tasks, and no shipment** for Plan 2, and none may be created from
> this document without a fresh operator decision followed by its own
> spike → impl-plan → plan-harden → plan-review → harvest cycle.
>
> Plan 2 is **not** a dependency of Plan 1 and must never be added as one.
> Plan 1 (`docs/plans/2026-08-09-copilot-cli-supervisor-control-plane-plan.md`)
> is explicitly scoped to a **local, operator-driven** supervisor with **zero**
> network listeners, and it must remain shippable and complete without any part
> of this document.
>
> Living tracker: see the dedicated Plan 2 stash entry (kind `feature`,
> priority `low`, marked DEFERRED).

## 1. Premise and prerequisite

Plan 2 would add a **remote control surface** over the local supervisor Plan 1
builds: a Gradio web UI, exposed off-machine through a Microsoft devtunnel, from
which an operator could observe and steer a long-horizon Copilot CLI session.

**Hard prerequisite:** Plan 1 must be shipped and stable first. Plan 2 is a
*transport and identity layer over an existing local control plane* — it is not
a parallel implementation. If Plan 2 ever needs to reimplement session state,
process management, approvals, or journaling, that is a signal that Plan 1's
service boundary was wrong and must be fixed rather than duplicated.

**Unchanged product boundaries.** Even in Plan 2, Copilot CLI remains the
reasoning/agent-execution engine, autoharness implements no action/observation
loop, backlogit owns backlog/checkpoints, Engram stays read-only and
non-authoritative, graphtor owns docs retrieval, and `.autoharness/config.yaml`
remains model-routing authority.

## 2. Why this is deferred rather than dropped

The operator use case is real: long-horizon workloads run for hours, and being
tethered to one terminal on one machine is a genuine constraint. But remote
exposure changes the product's risk class entirely — it converts a local
developer tool that can already execute arbitrary code in a workspace into a
**remotely reachable code-execution surface holding live GitHub credentials**.
That deserves its own threat model, its own review, and its own release, not a
rider on a local-supervisor increment.

## 3. Remote threat model

### 3.1 Assets

| Asset | Exposure if compromised |
|---|---|
| Live `GITHUB_TOKEN` / `GITHUB_PERSONAL_ACCESS_TOKEN` in the session environment | Full impersonation of the operator's GitHub identity. **Once exposed, the credential is unrecoverable by any local action** — it stays valid until revoked at the issuer (§3.3 T11, §11.1). |
| The supervised Copilot CLI session | Arbitrary code execution on the operator's machine, in the operator's workspace, as the operator |
| The approval channel | Approving destructive operations the operator never saw |
| The workspace filesystem | Source, secrets, `.env.local`, git credentials |
| The session journal / streamed output | Source code, prompts, tool output; secrets if redaction fails |
| The tunnel URL itself | A capability — anyone who learns it reaches the front door |

### 3.2 Adversaries

1. **Opportunistic internet scanner** — finds the tunnel hostname.
2. **URL-leak adversary** — obtains the tunnel URL from a chat message, a
   screenshot, a log, a browser history, or a shared terminal.
3. **Authenticated-but-wrong tenant** — holds a valid Microsoft identity that is
   not the operator's.
4. **Session-hijack adversary** — steals a session cookie/token from a browser or
   an intercepted link.
5. **Malicious/compromised model output** — attempts prompt-injected actions that
   the remote UI would auto-approve.
6. **Local co-tenant** — another process on the machine binding or probing the
   local Gradio port.

### 3.3 Principal threats and required mitigations

| # | Threat | Required mitigation |
|---|---|---|
| T1 | Tunnel URL treated as a secret (it is not) | **The tunnel must never be the security boundary.** Authentication is mandatory and independent of URL secrecy. Anonymous tunnels are prohibited. |
| T2 | Unauthenticated reach to the control surface | devtunnel **access control set to authenticated-tenant/allow-list**, *plus* an independent application-layer auth check. Defense in depth, not either/or. |
| T3 | Remote approval of destructive actions | Remote approvals are **capability-scoped and default-deny**. High-impact classes (git push, PR merge, shipment claim, credential use, filesystem writes outside the workspace) are **never remotely approvable** in a first release. |
| T4 | Session hijack | Short-lived, rotating, `HttpOnly`+`Secure`+`SameSite=Strict` session tokens bound to the authenticated identity; idle timeout; explicit remote-session revocation from the local console. |
| T5 | Secret exfiltration via streamed output | Plan 1's redaction choke point applies to the stream **before** it leaves the process. A remote stream may never bypass the redactor, and the redactor must fail closed (drop, not pass through). |
| T6 | Terminal streaming becoming arbitrary remote shell | The remote surface exposes a **fixed structured command vocabulary** (pause/resume/cancel/restart/approve/deny/status), **not** raw stdin to the child. Raw-stdin passthrough is a separate, explicitly-gated decision. |
| T7 | Local port exposure | Gradio binds `127.0.0.1` only; the devtunnel is the sole path off-machine. Never `0.0.0.0`. |
| T8 | Wrong-workspace control | Cryptographic workspace binding (§6): a remote session is bound to exactly one workspace/session id and rejects any command carrying a different one. |
| T9 | Tunnel outliving the session | Tunnel lifetime is strictly nested inside session lifetime; supervisor drain **must** tear the tunnel down, including on crash (§8). |
| T10 | Audit gap | Every remote-originated command and approval is journaled with authenticated principal, timestamp, source, and outcome — non-repudiable and locally inspectable. |
| T11 | Exposed GitHub credential (PAT / OAuth token) treated as recoverable by re-authentication | **A compromised credential is only neutralized by issuer-side revocation.** The exposed PAT/OAuth token must be **revoked at GitHub** and **replaced with a newly issued credential**. `gh auth refresh` is **not** a remediation — it re-authorizes scopes for the *same* credential and leaves the exposed secret valid. See §11.1 for the required response sequence. |

## 4. Authentication

* **Identity provider: Microsoft Entra ID**, reached through devtunnel's
  authenticated access control. Anonymous tunnels are prohibited outright.
* **Application-layer verification is independent.** The app validates the
  identity assertion itself rather than trusting "the request arrived through the
  tunnel". A tunnel misconfiguration must not be a total auth bypass.
* **Local enrollment ceremony.** The *first* remote session for a workspace
  requires an explicit action at the **local console** (an out-of-band pairing
  code shown locally and entered remotely). Remote-only bootstrap is prohibited.
* **No shared secrets, no static bearer tokens, no basic auth, no
  password-in-config.**
* **Explicit non-goal:** SSO federation to arbitrary third-party IdPs in a first
  release.

## 5. Authorization

* **Default deny.** Every remote capability is individually granted.
* **Capability tiers**

  | Tier | Capabilities | Remote default |
  |---|---|---|
  | Observe | status, phase, progress, redacted output stream, journal tail | **Allowed** |
  | Steer | pause, resume, cancel, request checkpoint | Allowed, per-session opt-in |
  | Approve | resolve a low-impact approval request | Opt-in, class-restricted |
  | Privileged | git push, PR create/merge, shipment claim, credential use, restart with elevated budget, writes outside the workspace | **Never remotely allowed in v1** |

* **Local override is absolute.** The local console can revoke any remote grant,
  kill any remote session, and terminate the tunnel at any moment; remote
  principals can never revoke local control.
* **Role separation is preserved.** A remote surface grants no agent-role
  authority: it cannot make Stage do Ship's work or vice versa (P-001/P-010).

## 6. Workspace binding

1. A remote session is bound to a `(workspace_root, session_id)` pair at
   enrollment, with a binding token derived locally.
2. Every remote command carries the binding; a mismatch is rejected and journaled
   as a security event.
3. **One workspace per tunnel.** Multi-workspace fan-out from a single tunnel is
   an explicit non-goal — it would make workspace containment a runtime
   authorization decision rather than a structural one.
4. Workspace path containment from Plan 1 (§3.5/H2) applies unchanged; the remote
   surface adds **no** new write paths.
5. Binding is invalidated by: session end, workspace move, tunnel teardown, or
   local revocation.

## 7. Streaming and control protocol

* **Two logically separate channels**: a one-way **observation stream** (redacted
  events/output) and a **control channel** carrying a closed, versioned,
  schema-validated command vocabulary.
* **Observation** reuses Plan 1's typed event catalog verbatim — the remote UI is
  a *renderer of existing events*, and Plan 2 must not invent a second event
  model.
* **Control commands** are structured messages, never raw bytes to the child's
  stdin. Every command is idempotency-keyed, rate-limited, size-bounded, schema
  validated, and rejected if the session is not in a state that permits it (the
  Plan 1 state machine remains the authority).
* **Backpressure and truncation** are explicit: a slow remote consumer must never
  block or stall the supervised child. The local session is authoritative and
  never waits on the network.
* **Reconnect** resumes from the journal cursor; the remote client is stateless
  with respect to session truth.
* **Browser terminal streaming** (full interactive terminal emulation in the
  browser) is called out as its **own** later decision, gated on T6 — it is not
  in this design's first release.

## 8. Tunnel lifecycle

| Phase | Behavior |
|---|---|
| Create | Only on explicit operator action at the local console. Never automatic, never on by default, never persisted across sessions. |
| Configure | Authenticated access control; single port; TLS enforced end-to-end; no anonymous access; short-lived. |
| Bind | Tunnel lifetime strictly nested inside supervisor session lifetime. |
| Health | Continuous liveness probe; loss of tunnel is a warning, never a supervised-session failure — the local session keeps running. |
| Teardown | **Mandatory** on session drain, on cancel, on crash, and on `SIGINT`. A crash-safe teardown (best-effort on exit **plus** an orphan sweep at next startup) is required — an orphaned tunnel is a P0-class defect. |
| Audit | Creation, principal, port, access-control mode, and teardown are journaled. |

## 9. Multi-user and multi-session concerns

* **v1 is single-operator, single-session.** Plan 1's one-active-session-per-
  workspace lock stays in force and is *not* relaxed to accommodate a UI.
* Multiple *viewers* of one session may be allowed; multiple *controllers* are
  not. Control is a single-holder lease with explicit hand-off and a visible
  holder indicator.
* Concurrent approval requests are queued and answered in order; no parallel
  approval resolution.
* Multi-workspace and multi-tenant hosting are explicit non-goals — that would be
  the persistent multi-workspace daemon whose existence is Plan 1 §7's stated
  re-evaluation trigger for a different implementation language, and it would
  need its own program of work.

## 10. Deployment

* **Optional extra**, e.g. `autoharness[remote]`, pulling `gradio` and a
  devtunnel client. **Never** a base dependency — Plan 1's guarantee that the
  base install adds no new required dependency must survive Plan 2.
* Disabled by default; requires explicit config **and** an explicit local
  command. There is no "remote on by default" configuration.
* Preflight: verify the devtunnel client, authenticated access-control support,
  loopback-only bind, and redactor health **before** exposing anything.
* CI must prove that with the extra uninstalled, `supervise/` still imports and
  the local path is byte-for-byte unaffected.

## 11. Rollback

* Uninstall the extra, or set the disable flag — the local supervisor is
  unaffected because Plan 2 adds only an optional adapter over existing services.
* Emergency: local console `revoke-remote` kills remote sessions and tears down
  the tunnel without stopping the supervised Copilot session.
* Rollback of the *remote surface* must never require terminating in-flight agent
  work. **This convenience guarantee does not extend to credential
  compromise** — see §11.1, where containment explicitly outranks preserving
  in-flight work.

### 11.1 Credential-compromise response (runbook)

Any credential that may have been exposed during an incident is treated as
**compromised**, not as suspect-but-usable.

**`gh auth refresh` is not a remediation.** It refreshes scopes/authorization for
the **same underlying credential**; it neither invalidates the exposed secret nor
issues a replacement. An attacker holding the exposed PAT or OAuth token retains
full access after a `refresh`. It may be used only for its actual purpose —
adjusting scopes on a credential that is *not* believed to be compromised — and
must never be described, documented, or scripted as rotation.

**Required sequence (in order):**

1. **Contain first.** Tear down the tunnel and terminate all remote sessions
   (`revoke-remote`). Assume the credential is already replicated off-machine.
2. **Revoke at the issuer.** Delete/revoke the exposed PAT, or revoke the OAuth
   authorization, in GitHub settings (or via the org/enterprise admin path for a
   managed identity). Revocation is the **only** action that invalidates the
   exposed secret; every other step is secondary.
3. **Issue a replacement.** Mint a **new** credential with least-privilege
   scopes. Rotation means *revoke the old and issue a new one* — never reuse,
   never re-scope the exposed credential.
4. **Purge the old credential from every process environment.** The exposed value
   is resident in the supervisor process, the supervised Copilot CLI child, and
   any process they spawned; those environments cannot be rewritten in place.
   **A controlled supervisor session restart is therefore explicitly permitted
   and, where the old value is still resident in a live process environment,
   required** — drain the session, release the workspace lock, and relaunch so
   the child is spawned with only the replacement credential. **Containment
   outranks preserving in-flight work:** the general "rollback must never
   terminate in-flight agent work" guarantee is **suspended** for this path. Loss
   of in-progress agent work is an accepted and expected cost.
5. **Purge at-rest copies.** Remove the old value from `.env.local`, shell
   history, CI/secret stores, and any local credential helper cache.
6. **Journal the incident.** Record detection, containment, revocation
   confirmation, replacement issuance, restart, and purge — with timestamps and
   the authenticated principal — as a non-repudiable local record. Journal the
   **event**, never the credential value; the redaction choke point (T4 —
   `supervise/redact.py`, harvested as `118.004-T`) applies unchanged. T5 is
   workspace/session locking and is not the control meant here.
7. **Verify.** Confirm the old credential is rejected by the issuer and that the
   supervised session is operating on the replacement.

**Rollback dependency.** Rolling back the remote surface (uninstalling the extra,
disabling the flag, tearing down the tunnel) does **not** discharge steps 2–7. A
disabled remote surface does not invalidate a credential that has already left
the machine.

## 12. Open questions (must be answered before any Plan 2 harvest)

1. Is Gradio the right surface, or is a minimal purpose-built control page a
   smaller attack surface for a fixed command vocabulary?
2. What exactly is the minimum viable remote capability set — is *observe-only*
   enough to deliver most of the operator value at a fraction of the risk?
3. Does devtunnel's authenticated access control meet the requirement on its own,
   or is a second application-layer factor mandatory?
4. What is the approval-class taxonomy, and which classes are permanently
   local-only?
5. What is the retention and access policy for streamed session content?
6. Is browser terminal streaming ever acceptable, and under what containment?
7. Corporate-network and tunnel-policy constraints in the target environments?

## 13. Explicit boundaries of this document

* Creates **no** implementation feature, task, or shipment.
* Is **not** a dependency of Plan 1 and must not be added to Plan 1's dependency
  graph.
* Does **not** authorize any source, template, schema, or config change.
* Does **not** revisit candidate (c) (background Verification & Compaction), which
  remains a separate later capability tracked on stash `34D50F2D`.
* Does **not** introduce a native autoharness MCP server, which remains an
  explicit non-goal absent a concrete consumer.
