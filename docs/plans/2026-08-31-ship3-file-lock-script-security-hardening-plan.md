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

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Enforce workspace-root containment and symlink-escape prevention in both acquire scripts | M | high | `templates/skills/file-lock/scripts/acquire_lock.{ps1,sh}` |
| 2 | Enforce lock-ownership verification and consistent lock-path computation in both release scripts | M | high | `templates/skills/file-lock/scripts/release_lock.{ps1,sh}` |
| 3 | Re-copy hardened scripts to `scripts/`, refresh manifest checksums, and add a template↔installed parity test | S | medium | `scripts/**`, `.autoharness/harness-manifest.yaml`, `tests/` |

Task 1 covers findings 1, 2, 3. Task 2 covers findings 4, 5, 6 — 6 travels with
4/5 because the root-level path defect is a *release-side lock-path* bug and
fixing ownership requires reading the lock at the correct path first.

## Non-goals

* No redesign of the acquire race handling — `FileMode::CreateNew` is correct.
* No new lock-file format field. `agent` and `pid` are already recorded; this
  work reads what is already written.
* No change to `concurrency.instructions.md`. The policy is correct; the scripts
  are what disagree with it.
* No automatic stale-lock reaping.

## Verification

`PYTHONPATH=src python -m unittest discover -s tests`; `verify-harness`
(checksum validation is the gate that proves H1 was honoured); manual matrix of
containment cases on both platforms: absolute path outside root, `../` traversal,
symlinked directory pointing outside, sibling directory whose name shares the
root's prefix, root-level file present, root-level file missing.

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
