---
title: "Decided plan — SHIP-3 — file-lock script security hardening (template-first)"
doc_type: decided-plan
status: shipped
created: 2026-09-11
supersedes: docs/archive/plans/2026-08-31-ship3-file-lock-script-security-hardening-plan.md
slug: file-lock-script-security-hardening
source_stash: "74C62374"
source_decision: "docs/decisions/2026-08-31-dark-factory-staging-triage-and-shipment-portfolio.md"
shipment_unit: "SHIP-3"
shipment: 161-S
feature: 153-F
tasks: [153.001-T, 153.002-T, 153.003-T, 153.004-T, 153.005-T]
merge_commit: 6da9aed580f9ed232a6871281f47567c9060ffa8
pr: 444
plan_review_verdict: "PASS (2 review-fix cycles, zero unresolved P0/P1)"
---

# SHIP-3 — file-lock script security hardening — Decided Plan

Consolidated per P-020 `compact-context` at post-merge closure of 161-S. This
is a decided-plan: final decisions and binding constraints only, with the
review-fix deliberation history moved to the verbose original in
`docs/archive/plans/`.

## Problem (resolved)

The four concurrency-pack scripts (`acquire_lock.{ps1,sh}`,
`release_lock.{ps1,sh}`) under `templates/skills/file-lock/scripts/` had six
findings deferred from PR #409 under P-021 C1: no workspace-root containment,
symlink/junction escape through path resolution, and — most seriously —
unconditional lock deletion in `release` that never validated ownership,
meaning any agent could break any other agent's lock and the mutual-exclusion
guarantee the pack exists to provide did not hold.

## Final decisions

1. **Containment**: explicit workspace-root parameter, defaulting to
   `git rev-parse --show-toplevel`; if the git-derived root is not an
   ancestor-or-equal of the script's own installed location, fail closed and
   demand the explicit parameter (amended in plan review finding 2 — the
   original nested-checkout default silently widened containment).
2. **Ownership check**: refuse by default; a `-Force`/`--force` flag
   (operator-supplied only) honors the existing 1-hour staleness heuristic.
   No automatic age-based override.
3. **Ownership mechanism — token capability (O2, ADOPTED)**: `agent` is
   demoted to an anti-accident/courtesy identity with **no** authorisation
   weight (`AGENT_NAME` is caller-controlled and spoofable — O1). The real
   mechanism is a CSPRNG-generated acquisition token: `acquire` stores only
   its SHA-256-or-stronger digest (`owner_digest`) in the lock file and
   returns the token itself to the caller on stdout; `release` requires the
   token (`-Token`/`--token` or `LOCK_TOKEN`) and only releases on digest
   match. `pid` remains corroborating evidence only (O4), never authorisation
   (Windows pid reuse makes it unsound as sole authority).
4. **Token contract (TC1–TC6, binding, pinned in review-fix cycle 2)**:
   CSPRNG only, minimum 128 bits (forbidden: `Get-Random`, `$RANDOM`, `awk
   rand()`, time/pid-derived values); fixed-length lowercase-hex (or
   base64url) encoding, one valid length only — no distinct min/max valid
   length; SHA-256-or-stronger digest, MD5/SHA-1 forbidden, fail-closed if no
   SHA-256 utility exists; identical cross-platform semantics (a token
   acquired on one platform verifies on the other); token/digest never
   re-echoed in any status/verbose/error output, never written to logs or
   telemetry; no new lock-file field beyond `owner_digest`.
5. **Honest bound (O3, binding)**: these are advisory locks. A local process
   with write access can delete the lock file directly, bypassing all of the
   above. The token mechanism defends against **accidental/careless**
   cross-agent breaks, not a hostile local process. This bound is stated in
   plain words in shipped documentation (H7) — no shipped text may claim an
   adversarial security guarantee.
6. **Exit code on refusal**: non-zero (a declined release must be
   distinguishable from success). The refusal message states the exact
   operator remedy: lock path, recorded `agent`/`pid`, lock age, and the
   explicit `--force` invocation (plan-review P0 finding 1 — a silent
   non-zero-only refusal would be an unrecoverable DoS in an AFK dark-factory
   session).

## Binding hardening constraints (P-006: H1–H9)

* **H1**: template-first always — edit `templates/skills/file-lock/scripts/**`,
  re-copy to `scripts/**`, refresh manifest checksums. Never patch
  `scripts/**` directly.
* **H2**: containment compared only after full symlink/junction resolution of
  *both* the candidate path and the workspace root (fully-resolved real
  paths, not unresolved/prefix comparison).
* **H3**: containment and ownership must land in the same shipment — no
  independently-shippable partial-hardened intermediate state.
* **H4**: path-segment comparison only; prefix-string (`startsWith`)
  containment is forbidden (`/repo` must not be treated as containing
  `/repo-evil`).
* **H5**: PowerShell and POSIX variants implement identical semantics.
* **H6**: the CLI/exit-code contract change propagates to its documentation
  in the same shipment — `templates/skills/file-lock/SKILL.md.tmpl` (+
  installed dogfood mirror `.github/skills/file-lock/SKILL.md`),
  `templates/instructions/concurrency.instructions.md.tmpl` (+ mirror), and
  `.autoharness/harness-manifest.yaml` checksums.
* **H7**: the O3 advisory-not-adversarial bound stated in plain words in
  `concurrency.instructions.md` and the file-lock `SKILL.md`.
* **H8**: every task in `careful` safety mode; tasks 1–2 additionally
  `freeze-scope` bounded to `templates/skills/file-lock/scripts/`.
* **H9**: task 1 and task 2 are both `complexity: high`, forcing a
  de-risking prerequisite (task 0) rather than a split (splitting would
  violate H3's no-partial-state rule or H5's cross-platform-identical rule).

## Task list (as shipped — 153.001-T .. 153.005-T under 153-F)

| # | Title | Surface |
|---|---|---|
| 0 (153.004-T*) | De-risking prerequisite: two-platform path-resolution/lock-path behaviour matrix (7 escape cases) + canonical token/digest interoperability vectors V-a–V-e (incl. V-c2/V-c3 length-boundary rejection vectors, added cycle 2) | `docs/` (record-only) |
| 1 (153.001-T) | Workspace-root containment + symlink-escape prevention in both acquire scripts | `templates/skills/file-lock/scripts/acquire_lock.{ps1,sh}` |
| 2 (153.002-T) | Token-based lock-ownership verification + consistent lock-path computation in both release scripts | `templates/skills/file-lock/scripts/{acquire,release}_lock.{ps1,sh}` |
| 3 (153.003-T) | Re-copy hardened scripts to `scripts/`, refresh manifest checksums, template↔installed parity test | `scripts/**`, `.autoharness/harness-manifest.yaml`, `tests/` |
| 4 (153.005-T) | Update file-lock skill + concurrency instruction contracts (template + dogfood) to new CLI/exit-codes/token model/honest guarantee | `templates/skills/file-lock/SKILL.md.tmpl`, `.github/skills/file-lock/SKILL.md`, `templates/instructions/concurrency.instructions.md.tmpl`, `.github/instructions/concurrency.instructions.md`, manifest |

*Task numbering in the plan (0–4) is NOT sequential with backlog IDs: the
mapping is 0→`153.004-T`, 1→`153.001-T`, 2→`153.002-T`, 3→`153.003-T`,
4→`153.005-T` (the de-risking prerequisite was assigned the last backlog ID,
`153.004-T`, despite being task 0 in execution order). Machine dependency:
`153.002-T` (task 2) is blocked by both `153.001-T`
(task 1) and `153.004-T` (task 0's matrix) — encoded as a graph edge, not
prose, after plan-review cycle 2 found the prose-only version
unenforceable. Task 4 sequenced last so it documents the contract as
actually shipped.

## Non-goals (final)

* No redesign of acquire's race handling (`FileMode::CreateNew` is correct).
* No new lock-file field beyond `owner_digest`.
* No change to the *intent* of `concurrency.instructions.md` (only its text,
  to document the token mechanism/`--force`/O3 bound).
* No automatic stale-lock reaping.
* No claim of adversarial security (O3).
* No cross-machine, network, or kernel-level locking.

## Deferred scope (P-021 captures, still open — Stage-owned)

| Ref | Capture | Residual risk if never built |
|---|---|---|
| 13F5EEF0 | Tamper-evident or OS-enforced lock (mandatory file locking, lock daemon, OS-level advisory lock held by a live handle) | Accepted, low — threat model is cooperating agents, not a local adversary; O3/H7 ensure no shipped text claims otherwise |
| A7AD3044 | Shared cross-platform path-containment utility for the whole harness | Low — task 3's parity test bounds drift between the four scripts' independent containment logic |

**Additional captures from PR #444 review remediation** (post-plan, during
161-S implementation — see compacted session memory
`docs/memory/compacted/2026-09-11-ship-160s-closure-repair-161s-full-lifecycle-compacted.md`
for full detail): `04C4EA9A` (fsutil-fallback case-sensitivity gap, pre-existing
round-8 code), `BD46D364` (recursion-cap/depth-guard canonical-path gap,
pre-existing round-8 code), and reuse of pre-existing `58A85283` (V-d
cross-runtime interop coverage gap).

## Verification (as executed)

`PYTHONPATH=src python -m unittest discover -s tests` (full suite, 2152
tests, green); `verify-harness` (checksum validation gating H1); manual
containment matrix on both platforms; token-contract assertions (TC1–TC6)
including same-platform round-trip verification (TC4's PowerShell↔PowerShell
and POSIX↔POSIX cases; actual cross-runtime PowerShell↔POSIX round-trip
exercise remains open, disclosed as P-021 `58A85283`) and no-token-in-output
checks (TC5). All confirmed green through 13 rounds of PR #444 Copilot
review and final CI before merge.

## Outcome

Shipped as shipment 161-S, merged to `main` at commit `6da9aed5`
(2026-09-11). Cascade-closed via the P-015 verified-fully-covered-root
exception (all 6 manifest members archived, zero returned, all `parent_id`s
preserved). See
`.backlogit/reconcile/161-S-cascade-close-20260911-163333.md` for the full
mechanical closure verification.
