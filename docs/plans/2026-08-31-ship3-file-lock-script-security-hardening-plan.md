---
title: "SHIP-3 — file-lock script security hardening (template-first)"
date: 2026-08-31
slug: file-lock-script-security-hardening
doc_type: plan
source_stash: "74C62374"
source_decision: "docs/decisions/2026-08-31-dark-factory-staging-triage-and-shipment-portfolio.md"
shipment_unit: "SHIP-3"
route: "claude-opus-5 / anthropic / high"
status: reviewed
requires_plan_hardening: "yes"
plan_review_verdict: "PASS"
---

# SHIP-3 — file-lock script security hardening (template-first)

## Problem

The four concurrency-pack scripts under `templates/skills/file-lock/scripts/` are
copied **verbatim** into `scripts/` by the installer (the `verify_workspace.py`
"concurrency pack script" branch, `mode=copy`, no variable substitution). Six
findings were raised on PR #409 (Copilot review threads [4]–[9]); they were
correctly deferred under P-021 C1 because editing the installed copies in place
would diverge them from their templates and break checksum validation.

| # | Script | Finding | Class |
|---|---|---|---|
| 1 | `acquire_lock.ps1` | No workspace-root containment. `Resolve-Path` accepts absolute paths and `../` traversal; the docstring claims "relative to the workspace root" but nothing enforces it. Lock files can be created outside the workspace. | **Security** |
| 2 | `acquire_lock.sh` L22 | Same gap. `cd $(dirname "$FILEPATH") && pwd -P` resolves symlinks but never verifies the result stays inside the workspace root. | **Security** |
| 3 | both acquire scripts | Symlink/junction escape: resolution happens *through* links before the lock path is computed, so a symlinked directory redirects lock creation outside the workspace. Violates Constitution Principle III (workspace isolation) and Principle IV (CLI workspace containment). | **Security** |
| 4 | `release_lock.ps1` | Removes the lock with `Remove-Item -Force` **unconditionally**, never reading the `agent`/`pid` recorded inside the lock file. | **Security — correctness of the guarantee** |
| 5 | `release_lock.sh` L35 | Same: `rm -f $LOCKFILE` with no ownership check. | **Security** |
| 6 | `release_lock.ps1` | `Split-Path -Parent` returns an empty string for a root-level relative path such as `AGENTS.md` when the target file is missing; `Join-Path` then throws under `Set-StrictMode`. The missing-file branch also uses the raw relative path while acquire used `Resolve-Path`, so the two can compute **different lock paths for the same target**. | Correctness |

**Findings 4 and 5 are the most serious**: the shipped scripts contradict the
shipped policy. `.github/instructions/concurrency.instructions.md` states "Do not
force-break locks. If a lock exists, only the operator may decide to break it.
Agents MUST NOT delete lock files they did not create." The lock file already
records `agent` and `pid`; release never reads them. **Any agent can silently
break any other agent's lock, so the mutual-exclusion guarantee the pack exists
to provide does not hold.**

Acquire is otherwise well built: it uses `FileMode::CreateNew` for atomic
exclusive creation and handles the race correctly. It needs containment only —
not a redesign.

## Deliberation — the three reserved choices

The entry flags three decisions. Each is decided here.

**(i) Containment strategy.** Options: an explicit workspace-root argument,
`git rev-parse --show-toplevel`, or an environment variable.

**Decision: explicit workspace-root parameter, defaulting to
`git rev-parse --show-toplevel`, with the resolved root itself validated.**
An env var is invisible and spoofable. `git rev-parse` alone fails in a
non-git target workspace and silently resolves to a *parent* repository if the
workspace is nested — the exact escape being closed. An explicit parameter is
testable and is what a caller in a foreign workspace needs; the git default keeps
the common case ergonomic.

**(ii) Ownership-check policy.** Options: refuse, warn, or a stale-age override.

**Decision: refuse, with the existing 1-hour staleness heuristic honoured only
behind an explicit `-Force`/`--force` flag that the operator supplies.**
`concurrency.instructions.md` already defines the 1-hour heuristic *and* already
says only the operator may break a lock. Warning-only would leave the guarantee
broken while appearing fixed. An automatic age override would let an agent break
a foreign lock without operator involvement, contradicting the same sentence.

**(ii-a) What "ownership" actually means — corrected in review-fix cycle 1
(binding).** Cycle 0 resolved finding 4 by making the recorded `agent` identity
the *primary* authorisation input. That was **wrong as a security claim** and is
withdrawn. The evidence:
`templates/skills/file-lock/scripts/acquire_lock.ps1:38` reads
`$agentName = if ($env:AGENT_NAME) { $env:AGENT_NAME } else { "unknown" }` and
`acquire_lock.sh:32` reads `AGENT_NAME="${AGENT_NAME:-unknown}"`. `AGENT_NAME` is
a **caller-controlled environment variable with a default**. Any process may set
it to any value, including another agent's. It is not an identity; it is a label
the caller chose.

Therefore, restated honestly:

* **O1 — `agent` is an anti-accident / courtesy identity, not a security
  identity.** Its purpose is to make a *mistaken* cross-agent release visible and
  diagnosable, and to name a human-meaningful owner in the refusal message. It
  carries **no** authorisation weight against a caller that wants to bypass it.
* **O2 — the structurally stronger mechanism: an acquisition token
  (ADOPTED, in scope).** `acquire` generates a high-entropy random token, writes
  **only its digest** into the lock file (`owner_digest`), and returns the token
  itself to the caller on stdout. `release` requires the caller to present the
  token (`-Token` / `--token`, or `LOCK_TOKEN`) and releases only when the digest
  matches. This is a **capability** check — possession of a secret established at
  acquire time — rather than a self-asserted label, so it does not collapse under
  a spoofed `AGENT_NAME`. It needs no new infrastructure: one random value, one
  digest, one argument. Storing the digest rather than the token is what makes it
  stronger than `agent`; reading the lock file no longer yields the credential.

  **Token contract, PINNED in review-fix cycle 2 (TC1–TC6, all binding).** Cycle 1
  said only "high-entropy random token" and "digest". That is not an implementable
  cross-platform contract: it permits the PowerShell and POSIX variants to pick
  different — and possibly weak — primitives, and a non-CSPRNG token silently
  destroys the capability property the whole mechanism rests on.

  * **TC1 — CSPRNG only, minimum 128 bits.** At least 128 bits (16 bytes) of
    entropy from a cryptographically secure source. PowerShell:
    `System.Security.Cryptography.RandomNumberGenerator`. POSIX: `/dev/urandom` or
    `openssl rand`. **Forbidden on both:** `Get-Random`, `$RANDOM`, `awk rand()`,
    date/time- or pid-derived values, and any non-CSPRNG PRNG.
  * **TC2 — encoding.** Lowercase hex (or unpadded base64url), fixed length,
    identical on both platforms, so the token is a single shell-safe word.
  * **TC3 — digest: SHA-256 or equivalent-or-stronger.** `owner_digest` is
    SHA-256 (or a stronger SHA-2/SHA-3 member) of the token's canonical encoded
    form, hex-lowercase. **MD5 and SHA-1 are forbidden.** POSIX uses `sha256sum`
    with a documented `shasum -a 256` fallback; if neither exists the script
    **fails closed** with a named remedy rather than downgrading the digest or
    storing the token in plaintext.
  * **TC4 — identical cross-platform semantics** (extends **H5**): a token
    acquired under one variant must verify under the other, so canonical encoding,
    trailing-newline handling, and case are specified exactly and covered by a
    cross-variant vector in task 0's matrix.
  * **TC5 — exposure and safe handling, documented rather than assumed.** The
    token is a short-lived secret returned on **stdout** so the caller can capture
    it. The shipped documentation must state, and the scripts must honour:
    (a) stdout capture means the token can land in CI logs, transcripts, shell
    history, and agent conversation logs if the caller echoes it — callers must
    capture rather than print, and the scripts must never re-echo the token in any
    status, verbose, or error output; (b) the token is never written to the lock
    file, to any log the scripts create, or to telemetry — only the digest is
    persisted; (c) `LOCK_TOKEN` is visible to child processes and, on some systems,
    to same-user processes, so both `--token` and the env var are supported and
    their exposure difference is stated; (d) refusal and staleness messages print
    lock path, `agent`, `pid` and age but **never** the token or `owner_digest`;
    (e) these exposure paths are acceptable **only because** this is an
    anti-accident capability for an *advisory* lock (**O3**) — leakage degrades
    the anti-accident property without creating an adversarial exposure that did
    not already exist.
  * **TC6 — no new lock-file field beyond `owner_digest`**, and no change to the
    acquire race handling.
* **O3 — the honest bound, stated so no adversarial claim survives.** These are
  **advisory** locks: an ordinary file in a workspace the caller can write. A
  local process with write access can delete the lock file directly and never
  invoke `release` at all. **No script-level mechanism can prevent that, and this
  plan does not claim to.** What O2 buys is precise and limited: breaking another
  agent's lock stops being *trivially and accidentally possible through the
  supplied tooling* and becomes *a deliberate bypass of it*. That is a real
  integrity improvement against accident, confusion, and buggy automation. It is
  **not** a defence against a hostile local process, and the shipped documentation
  must say so in those words (**H6**).
* **O4 — `pid` remains corroborating evidence only**, used in the staleness report,
  never as authorisation. `pid` reuse on Windows makes it unsound as an authority
  (cycle 0 finding 4's one correct half, retained).

**(iii) Exit code on refusal.** **Decision: non-zero.** A release that declines
to break a foreign lock has not achieved the caller's intent, and the caller must
be able to detect that. Exit 0 would make the refusal indistinguishable from
success — the fail-open shape this whole run is removing.

## Hardening (P-006)

Triggered: security-sensitive, and a wrong containment fix is worse than none.

* **H1 (binding).** Template-first, always. Edit
  `templates/skills/file-lock/scripts/**`, then re-copy to `scripts/**`, then
  refresh manifest checksums. Never patch `scripts/**` directly.
* **H2 (binding).** Containment must be enforced **after** full symlink/junction
  resolution of *both* the candidate path and the workspace root, comparing
  fully-resolved real paths. Resolving one side only, or comparing string
  prefixes before resolution, leaves finding 3 open.
* **H3 (binding, from adversarial finding R4 in the portfolio deliberation).**
  Containment and ownership must land **in the same shipment**. A partially
  hardened lock — containment enforced, ownership still unchecked — is worse than
  none, because operators would trust a mutual-exclusion guarantee that still
  does not hold. No intermediate state of this shipment is independently
  shippable.
* **H4 (binding).** Prefix-string containment (`startsWith`) is forbidden;
  `/repo` must not be treated as containing `/repo-evil`. Use path-segment
  comparison (`Path.relative_to`-equivalent semantics on each platform).
* **H5.** PowerShell and POSIX variants must implement *identical* semantics.
  Divergence between the two is itself the defect class of finding 6.
* **H6 (binding) — the CLI contract change drags its documentation with it.**
  Cycle 0 declared "no change to `concurrency.instructions.md`" and named no skill
  surface. That was **wrong**: this shipment changes the scripts' *published CLI
  contract*, and that contract is documented, verbatim, in surfaces this plan
  omitted. Verified:
  * `templates/skills/file-lock/SKILL.md.tmpl:43-44,58-59` publishes the exact
    invocation signatures (`scripts/acquire_lock.ps1 <filepath>`), which gain
    `--workspace-root`, `--token` and `--force`.
  * `templates/skills/file-lock/SKILL.md.tmpl:27-30` publishes the exit-code
    contract, and **L30 directly contradicts the new behaviour**: it states
    *"On `release` failure: lock file not found (already released), exit code 0
    with warning."* Decision (iii) makes refusal non-zero. Shipping the scripts
    without this edit leaves the documentation asserting the opposite of the code.
  * `.github/skills/file-lock/SKILL.md` is the installed dogfood mirror of the
    above and must move in the same shipment (paired-edit contract).
  * `templates/instructions/concurrency.instructions.md.tmpl` and its mirror
    `.github/instructions/concurrency.instructions.md` carry the operator-only
    lock-breaking rule and the 1-hour staleness heuristic that decision (ii) now
    *implements*. The policy prose stays correct in intent, but it must gain the
    token mechanism (**O2**), the explicit advisory-not-adversarial bound
    (**O3**), and the `--force` operator procedure, or agents will follow prose
    that no longer matches the tool.
  * `.autoharness/harness-manifest.yaml` checksums cover every file above.

  All six surfaces land **in the same shipment** as the script changes. **H3**'s
  no-partial-state rule extends to them: shipped scripts whose published contract
  is documented wrong are the same fail-open shape this shipment removes.
* **H7 (binding) — honest documentation of the guarantee.** The `O3` bound must
  appear in `concurrency.instructions.md` and the file-lock `SKILL.md` in plain
  words: these are advisory locks; the token defends against accident and
  confusion, not against a hostile local process that can delete the lock file
  directly. No text in any shipped surface may claim or imply an adversarial
  security guarantee.
* **H8 (binding) — safety mode.** Every task in this shipment enters `careful`.
  Tasks 1 and 2 additionally enter `freeze-scope` bounded to
  `templates/skills/file-lock/scripts/`, because they rewrite path-resolution and
  deletion logic where an over-broad edit is the risk.
* **H9 (binding) — de-risking prerequisite for tasks 1 and 2 (two-axis gate).**
  Both tasks are `complexity: high`, which forces a split or an explicit
  de-risking step regardless of size. Splitting is rejected: **H3** forbids
  shipping containment without ownership, and splitting either task along its
  platform seam would violate **H5**. The de-risking step is therefore adopted and
  is a **hard prerequisite**, not advice — task 0 below. Neither task 1 nor task 2
  may begin before task 0's matrix is recorded.

## De-risking prerequisite — task 0 (blocking, `S` / `low`)

The `high` complexity in tasks 1 and 2 is concentrated in one place: *what the two
platforms' path-resolution primitives actually do* on the six escape cases, which
is an empirical question that has not been answered. Answer it first, on the
current scripts, and the remaining work is mechanical.

Task 0 produces a recorded behaviour matrix — no production edits — covering, on
**both** Windows and POSIX: an absolute path outside the root; a `../` traversal;
a directory symlink/junction pointing outside; a sibling directory whose name
shares the root's prefix (`/repo` vs `/repo-evil`); a root-level target that
exists; a root-level target that is missing; and a nested-git-checkout root where
`git rev-parse --show-toplevel` resolves to the parent (finding 2). For each cell
it records the observed behaviour of the resolution primitive and the intended
post-fix behaviour. Tasks 1 and 2 consume the matrix as their test vectors.

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 0 | **De-risking prerequisite (H9)**: record the two-platform path-resolution and lock-path behaviour matrix for the seven escape cases | S | low | `docs/` (recorded matrix only; no production edits) |
| 1 | Enforce workspace-root containment and symlink-escape prevention in both acquire scripts | M | high | `templates/skills/file-lock/scripts/acquire_lock.{ps1,sh}` |
| 2 | Enforce token-based lock-ownership verification and consistent lock-path computation in both release scripts | M | high | `templates/skills/file-lock/scripts/{acquire,release}_lock.{ps1,sh}` |
| 3 | Re-copy hardened scripts to `scripts/`, refresh manifest checksums, and add a template↔installed parity test | S | medium | `scripts/**`, `.autoharness/harness-manifest.yaml`, `tests/` |
| 4 | Update the file-lock skill and concurrency instruction contracts (template + dogfood) to the new CLI, exit codes, token model, and honest guarantee | M | medium | `templates/skills/file-lock/SKILL.md.tmpl`, `.github/skills/file-lock/SKILL.md`, `templates/instructions/concurrency.instructions.md.tmpl`, `.github/instructions/concurrency.instructions.md`, `.autoharness/harness-manifest.yaml` |

Task 1 covers findings 1, 2, 3. Task 2 covers findings 4, 5, 6 — 6 travels with
4/5 because the root-level path defect is a *release-side lock-path* bug and
fixing ownership requires reading the lock at the correct path first. Task 2 also
touches the acquire scripts because **O2**'s token is *generated* at acquire time.

**Task 1 → task 2 is a MACHINE dependency, corrected in review-fix cycle 2.**
Cycle 1 expressed this sequencing only as prose ("sequenced 1→2 explicitly, and
recorded in the task table's note"). Prose does not sequence anything a scheduler
reads: both tasks edit `acquire_lock.ps1` and `acquire_lock.sh`, so without an
encoded edge they could be picked up concurrently or out of order and collide on
the same files. `153.002-T` is now encoded as blocked by **both** `153.004-T` (the
behaviour matrix, **H9**, which supplies its test vectors) **and** `153.001-T` (the
acquire-script containment rewrite). Task 4 is the **H6** documentation-contract
task and is sequenced last so it documents the contract as actually shipped —
including the **TC5** exposure and safe-handling guidance verbatim. Task 0 blocks
1 and 2 (**H9**).

## Non-goals

* No redesign of the acquire race handling — `FileMode::CreateNew` is correct.
* No new lock-file format field **beyond `owner_digest`**, which **O2** requires.
  `agent` and `pid` are already recorded and their meaning is unchanged (**O1**,
  **O4**).
* **No change to the *intent* of `concurrency.instructions.md`.** The policy is
  correct; the scripts are what disagree with it. Its *text* is nonetheless
  updated to document the token mechanism, the `--force` procedure, and the
  **O3** bound (**H6**, **H7**) — the earlier blanket "no change" was a scope
  error, corrected in cycle 1.
* No automatic stale-lock reaping.
* **No claim of adversarial security.** These are advisory locks (**O3**).
* No cross-machine, network, or kernel-level locking.

## Deferred scope (P-021, captured not silently broadened)

| Ref | Capture | Residual risk if never built |
|---|---|---|
| DSE-S3-1 | A tamper-evident or OS-enforced lock (mandatory file locking, a lock daemon, or an OS-level advisory lock held by a live handle). This is the only class of mechanism that would defend against a hostile local process, and it is a genuinely new product capability well beyond a script hardening. | **Accepted, low.** The residual exposure is a local process that *deliberately* bypasses the supplied tooling. The threat model here is concurrent cooperating agents, not a local adversary; **O3** and **H7** ensure no shipped text claims otherwise, so nobody relies on a guarantee that is not there. |
| DSE-S3-2 | A shared cross-platform path-containment utility for the whole harness (carried forward from cycle 0 finding 7). | **Low.** Four scripts each carry their own containment logic and could drift. **H5** plus task 3's parity test bound the drift to something a test detects. |

## Verification

`PYTHONPATH=src python -m unittest discover -s tests`; `verify-harness`
(checksum validation is the gate that proves H1 was honoured); manual matrix of
containment cases on both platforms: absolute path outside root, `../` traversal,
symlinked directory pointing outside, sibling directory whose name shares the
root's prefix, root-level file present, root-level file missing.

**Token contract verification (TC1–TC6, added cycle 2).** Assert the CSPRNG source
and the 128-bit minimum on both platforms; assert the forbidden primitives
(`Get-Random`, `$RANDOM`, `awk rand()`, time/pid-derived values) appear in neither
script; assert the digest is SHA-256-or-stronger and that MD5/SHA-1 appear nowhere;
assert the no-SHA-256-utility path **fails closed** rather than downgrading; assert
a token acquired under one variant verifies under the other (**TC4**); and assert
that no emitted message, log line, or telemetry record contains the token or
`owner_digest` (**TC5b**, **TC5d**).

## Plan review — multi-persona adversarial gate

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 1 | Security | **P0** | Refusing to release a foreign lock with a non-zero exit creates a **denial-of-service on the workspace**: a crashed agent leaves a lock nobody may remove, and the `-Force` flag requires an operator who, in dark-factory mode, is AFK. | **Resolved.** The refusal message must state the exact operator remedy (the lock path, the recorded `agent` and `pid`, the lock age, and the explicit `--force` invocation). The 1-hour staleness heuristic is *reported* in that message so the operator can act immediately. Automatic breaking remains forbidden — the alternative (agents silently breaking each other's locks) is the defect being fixed, and a DoS that halts loudly is strictly safer than a corruption that proceeds quietly. Recorded as acceptance criterion on task 2. |
| 2 | Security | **P1** | `git rev-parse --show-toplevel` as the default root silently resolves to a **parent** repository when the workspace is a nested checkout, widening containment rather than narrowing it. | **Resolved.** Decision (i) amended: when the explicit parameter is absent and the git-derived root is not an ancestor-or-equal of the script's own installed location, the script **fails closed** and demands the explicit parameter rather than guessing. |
| 3 | Security | **P1** | Comparing a resolved candidate against an *unresolved* root passes a symlinked-root workspace. | Already covered by **H2**, restated as an explicit acceptance case: both sides fully resolved before comparison. |
| 4 | Correctness | **P1** | On Windows, `pid` reuse means a recorded `pid` can match an unrelated live process, so an ownership check keyed on `pid` alone can wrongly authorise a break. | **Resolved.** Ownership is decided on the recorded **`agent` identity** as primary; `pid` is corroborating evidence used only for the staleness report, never as sole authorisation. |
| 5 | Template integrity | P2 | Hand-editing `scripts/**` would diverge installed artifacts from templates and break checksum validation. | **H1**; task 3 makes the re-copy and checksum refresh an explicit deliverable with `verify-harness` as its gate. |
| 6 | Maintainability | P2 | Two language variants drift over time. | Task 3's parity test asserts the two variants expose the same flags and the same exit-code contract. **H5.** |
| 7 | Scope | P2 | Containment work could expand into a general path-safety utility for the whole harness. | Bounded to these four scripts. A shared utility is a P-021 capture. |
| 8 | Constitution | P3 | The scripts currently violate Principles III and IV; the fix must not introduce a new destructive default. | `--force` is opt-in, never defaulted, and the refusal path performs no deletion. |

**Verdict: PASS.** 1 P0 and 3 P1 raised; all four resolved before harvest. Zero
unresolved P0/P1. Two review-fix cycles of three.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass.`
Every selected persona was covered inline against the Persona Rubric Adapter and normalized to
the P0–P3 scale; no persona was skipped. Declared, not silent.

**Plan hardening (P-006): required — `yes`. Satisfied.** **H1**–**H9** and **O1**–**O4** are
binding and each is propagated into a task acceptance criterion.

### Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Security | inline persona pass | 1 P0 + 2 P1 (cycle 0), 1 P1 (cycle 1) |
| Correctness | inline persona pass | 1 P1 (cycle 0) |
| Template integrity | inline persona pass | 1 P2 (cycle 0) |
| Maintainability | inline persona pass | 1 P2 (cycle 0) |
| Scope boundary | inline persona pass | 1 P2 (cycle 0), 1 P1 (cycle 1) |
| Constitution | inline persona pass | 1 P3 (cycle 0), 1 P1 (cycle 1) |
| Schema/CLI/docs coupling | inline persona pass | 1 P1 (cycle 1) |
| Architecture | inline persona pass | 1 P2 (cycle 1) |

### Review-fix cycle 1 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 9 | Security | **P1** | Cycle 0's finding-4 resolution made the recorded `agent` value the primary authorisation input. `AGENT_NAME` is a caller-controlled env var with an `unknown` default (`acquire_lock.ps1:38`, `acquire_lock.sh:32`), so this treated a spoofable label as a security identity and would have shipped a false guarantee. | **Resolved by O1–O4.** `agent` is reframed as an anti-accident/courtesy identity with no authorisation weight (**O1**). A structurally stronger acquisition-token capability is adopted **within this contract** — digest stored in the lock file, token returned to the caller (**O2**). The advisory bound is stated explicitly so no adversarial claim survives (**O3**), and `pid` is corroborating only (**O4**). |
| 10 | Schema/CLI/docs coupling | **P1** | The shipment changes the scripts' published CLI signature and exit-code contract while declaring the documenting surfaces out of scope. `templates/skills/file-lock/SKILL.md.tmpl:30` would be left asserting *the opposite* of the shipped release semantics. | **Resolved by H6.** Six coupled surfaces (skill template + dogfood, concurrency instruction template + dogfood, manifest checksums) are pulled into the shipment as task 4, sequenced last, under **H3**'s no-partial-state rule. |
| 11 | Constitution | **P1** | Tasks rewriting deletion and path-resolution logic carried no explicit safety-mode declaration. | **Resolved by H8**: `careful` for all tasks; `freeze-scope` on `scripts/` for tasks 1 and 2. |
| 12 | Correctness / Maintainability | **P1** | Tasks 1 and 2 are `M`/`high`, tripping the complexity axis of the two-axis gate with no split and no de-risking step. | **Resolved by H9.** Splitting is unavailable (**H3** forbids containment-without-ownership; a platform split violates **H5**), so a blocking de-risking prerequisite is adopted: **task 0** records the two-platform behaviour matrix for the seven escape cases before either task begins, and its matrix supplies their test vectors. |
| 13 | Architecture | P2 | Task 2 now also edits the acquire scripts (token generation), creating a same-file collision risk with task 1. | Sequenced 1→2 explicitly, and recorded in the task table's note. Same mitigation shape as SHIP-1's **H5**. **Superseded in cycle 2 by finding 15 — prose sequencing was insufficient and the edge is now machine-encoded.** |

**Verdict: PASS.** Cycle 1: 4 P1 raised, all 4 resolved; 1 P2 dispositioned.
Cumulative: **zero unresolved P0/P1**.

### Review-fix cycle 2 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 14 | Security | **P1** | **O2's token contract was unimplementable as specified.** "High-entropy random token" and "digest" name no primitive, no entropy floor, and no digest algorithm, so the PowerShell and POSIX variants could legally ship different and possibly weak choices — `Get-Random`/`$RANDOM` are the obvious reach on each platform and are *not* CSPRNGs. A guessable token silently voids the capability property the entire ownership model rests on, while the shipped documentation would still claim the stronger guarantee. | **Resolved by TC1–TC4/TC6.** CSPRNG-only with a **128-bit minimum**, named per-platform sources, an explicit forbidden-primitive list, fixed identical encoding, **SHA-256-or-stronger** digest with MD5/SHA-1 forbidden and a fail-closed path when no SHA-256 utility exists, and a cross-variant interoperability vector. Each is mandatory acceptance on `153.002-T` with a named assertion. |
| 15 | Correctness | **P1** | The task 1 → task 2 ordering that prevents a same-file collision on the acquire scripts existed **only as prose**. Nothing in the machine graph stopped `153.002-T` from being scheduled first or concurrently, and cycle 1's own finding 13 resolution ("sequenced explicitly … recorded in the task table's note") is exactly the comment-not-edge shape this portfolio rejects elsewhere. | **Resolved.** `153.002-T` is now encoded as blocked by **both** `153.004-T` and `153.001-T`. Verified present in the dependency graph and confirmed acyclic. |
| 16 | Security | P2 | The token is returned on **stdout**, but no plan text addressed where that stdout goes. In CI and agent transcripts an uncaptured or echoed token lands in logs, and `LOCK_TOKEN` is readable by child processes — neither exposure was documented, so implementers would have had to invent handling rules. | **Resolved by TC5.** Exposure paths are enumerated, the scripts are forbidden from re-echoing the token or printing `owner_digest` in any message, the env-var-versus-argument exposure difference is stated so callers can choose, and the documentation must record that these paths are tolerable only under the **O3** advisory bound. Task 4 carries the guidance verbatim. |
| 17 | Constitution | P2 | **H8** declared `careful` for every task, but `153.001-T` and `153.003-T` carried no safety-mode line in their own bodies — the mode existed only in the plan. | **Resolved.** Both tasks now declare their safety mode inline; `153.001-T` carries `careful` + `freeze-scope` bounded to `templates/skills/file-lock/scripts/`, matching **H8**. |

**Verdict: PASS.** Cycle 2: 2 P1 and 2 P2 raised, all 4 resolved. Cumulative:
**zero unresolved P0/P1**. Three review-fix cycles of three consumed; the next
review is the final independent disposition cycle.
