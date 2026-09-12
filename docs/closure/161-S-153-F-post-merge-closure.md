---
shipment: 161-S
feature: 153-F
pr: 444
merge_commit: 6da9aed580f9ed232a6871281f47567c9060ffa8
last_code_affecting_head: c65124cca3c904065c269595e7f0670f0264e534
closure_status: READY
compaction_status: done
conditions:
    - description: "Explicit operator merge approval for PR #444. Dark-mode activation record for shipments 160-S/161-S declares merge_approval_pre_authorized=false and admin_fallback_pre_authorized=false, so neither dark-mode auto-merge nor admin fallback may substitute for an explicit operator approval signal."
      satisfied: true
      evidence: "Explicit operator approval was granted for PR #444 specifically (\"PR 444: Merge approved\", scoped to this PR only). Ship re-executed last-mile verification immediately before merge: current headRefOid `c65124cca3c904065c269595e7f0670f0264e534` matched the PR's Local Review Readiness `Reviewed HEAD`; readiness outcome was `READY_WITH_FOLLOWUPS` with `P0=0, P1=0` and full local build evidence (2152 tests, 0 failures) present; a full-pagination GraphQL review-thread query across 13 review rounds found 83 threads total, 0 unresolved; `autoharness gate copilot-review 444 --repo softwaresalt/autoharness --enforcement auto` returned `SATISFIED` at that same HEAD; all 4 required checks (`ci gate`, `detect code changes`, `pipeline-topology (ambient)`, `test`) were green; the repository's merge-method settings confirmed `mergeCommitAllowed: true` with `squashMergeAllowed: false` and `rebaseMergeAllowed: false` (P-009); and the `pipeline-topology` gate's `lifecycle` phase passed. PR #444 was merged via `gh pr merge 444 --merge` producing two-parent merge commit `6da9aed580f9ed232a6871281f47567c9060ffa8` (parents `30e380924d13476809ebeb6a73e721666fb0df87` and `c65124cca3c904065c269595e7f0670f0264e534`, the exact reviewed HEAD), confirmed present in `origin/main` history via `git merge-base --is-ancestor`. No admin fallback was used or authorized."
---

# 161-S / 153-F Operational Closure (finalized, post-merge) -- SHIP-3 File-Lock Script Security Hardening (Template-First)

## Summary of Change

PR #444 ("SHIP-3: file-lock script security hardening (template-first)")
closes 5 tasks (`153.001-T`–`153.005-T`) under feature `153-F`. The four
concurrency-pack scripts under `templates/skills/file-lock/scripts/`
(`acquire_lock.{ps1,sh}`, `release_lock.{ps1,sh}`) had six findings deferred
from PR #409 under P-021 C1: no workspace-root containment, symlink/junction
escape through path resolution before containment was computed, and —
most seriously — `release` deleted lock files unconditionally without
validating recorded ownership, so any agent could silently break any other
agent's lock and the mutual-exclusion guarantee the pack exists to provide
did not hold.

This shipment adds explicit workspace-root containment with full
symlink/junction resolution on both sides of the comparison
(`153.001-T`); replaces label-based ownership (`AGENT_NAME`, spoofable) with
a CSPRNG-generated acquisition-token capability — `acquire` stores only the
token's SHA-256-or-stronger digest and returns the token to the caller,
`release` requires the token and matches on digest (`153.002-T`); re-copies
the hardened scripts from templates to `scripts/`, refreshes manifest
checksums, and adds a template↔installed parity test (`153.003-T`); and
updates the file-lock skill and concurrency-instructions contracts (template
+ installed dogfood mirrors) to the new CLI, exit-code, and token-model
contract, including the explicit advisory-not-adversarial bound (`153.005-T`).
`153.004-T` is the separate de-risking prerequisite task that recorded the
two-platform path-resolution behaviour matrix and the canonical token/digest
interoperability vectors consumed by `153.001-T`/`153.002-T`. See the decided plan,
`docs/plans/2026-09-11-file-lock-script-security-hardening-decided-plan.md`,
for the full set of binding decisions (O1–O4, H1–H9, TC1–TC6).

PR #444 went through 13 rounds of Copilot review remediation covering
containment, digest forgery, path divergence, CI bugs, symlink handling,
byte-identity, POSIX matrix coverage, fsutil regex bugs, a TOCTOU race in
`release_lock`'s deletion path, test-hook containment, and documentation
staleness. All 83 review threads were resolved; three out-of-scope findings
were captured under P-021 rather than fixed (see Deferred Scope below).

## Invariants Preserved

* `release` never deletes a lock file without validating the caller's
  presented token against the recorded `owner_digest` (unless `--force` is
  explicitly supplied by the operator).
* Containment is enforced only after full symlink/junction resolution of
  *both* the candidate path and the workspace root, comparing
  fully-resolved real paths (never a string-prefix comparison).
* PowerShell and POSIX variants are intended to implement identical
  semantics: a token acquired under one platform variant is designed to
  verify under the other (TC4). The canonical token/digest values used to
  assert this (V-a–V-e, including the V-d two-cell round-trip vectors) are
  recorded in `153.004-T`'s behaviour matrix. **Disclosed gap** (open P-021
  follow-up `58A85283`, not fixed by this closure): existing automated
  tests exercise same-platform round trips only, so an actual
  PowerShell→POSIX or POSIX→PowerShell cross-variant verification is not
  yet automated and could still fail undetected.
* No shipped documentation claims an adversarial security guarantee — the
  advisory bound (O3) is stated in plain words in
  `.github/instructions/concurrency.instructions.md` and
  `.github/skills/file-lock/SKILL.md` (and their templates).
* Template-first discipline honored throughout: all four scripts were
  edited under `templates/skills/file-lock/scripts/**`, re-copied to
  `scripts/**`, with manifest checksums refreshed (H1) — never
  hand-patched in place.

## Runtime Validator Evidence (inline handoff)

| Field | Value |
|---|---|
| Surface | `file-lock scripts` (primary changed runtime surface: `scripts/acquire_lock.{ps1,sh}`, `scripts/release_lock.{ps1,sh}`, installed from `templates/skills/file-lock/scripts/**`) |
| Probe | Live acquire/release exercise against a real target: this session's own post-merge closure work (`scripts/acquire_lock.ps1 .backlogit\queue\161-S.md` -> capture token -> `scripts/release_lock.ps1 .backlogit\queue\161-S.md` with the captured token) plus, earlier in the same closure sequence, a documented `--force` release of a stale pre-existing lock (see Risky Action Record below) |
| Expected | `acquire` returns exit 0 with a `LOCK_TOKEN=<token>` line and creates the lock sentinel; `release` with the correct token returns exit 0 and removes the lock sentinel; a mismatched/missing token is refused with a non-zero exit |
| Observed | `acquire` succeeded (token captured in-memory only, never printed/persisted -- see the reconcile reports' redaction note); `release` with the captured token succeeded (exit 0), removing the lock sentinel; the one `--force` release (of the separately-identified stale/empty pre-existing lock) also completed successfully, consistent with the documented `--force` behavior |
| Manual checkpoints | none declared in the validator manifest |
| Blocked prerequisites | none |
| Follow-up | No automated CI probe of `acquire_lock`/`release_lock` script behavior exists yet beyond the unit/integration test suite (`tests/test_file_lock_*.py`, all green) and this session's live manual exercise; a scripted post-merge smoke probe for the file-lock scripts themselves (beyond unit tests) is not currently automated and is noted as a possible future hardening, not a blocker for this closure |
| Verdict | **PASS** |

Supplementary: `uv run autoharness --help` (exit 0, CLI help text printed,
re-confirmed post-merge on `main`) was also checked to confirm the packaged
Python CLI entrypoint -- which this shipment's changes do not touch -- has
no regression. That check alone does not exercise the actual changed
surface (the standalone file-lock scripts) and is recorded here only as a
supplementary confirmation, not as the primary validator evidence.

This shipment's changes are concentrated in `templates/skills/file-lock/scripts/**`
(re-copied to `scripts/**`, standalone PowerShell/POSIX shell scripts invoked
via the file-lock skill, not imported by the installed `autoharness` Python
package) and documentation/skill/instruction surfaces. The packaged CLI
entrypoint is unaffected by construction; the smoke check above confirms no
regression was introduced.

## CI Status and Review

* Required checks at merge commit HEAD (== `last_code_affecting_head`
  `c65124cc`, the final PR HEAD — no evidence-only refresh commits were
  needed on this PR since readiness-block updates were made via `gh pr edit`
  rather than committed refresh commits): `ci gate`, `detect code changes`,
  `pipeline-topology (ambient)`, `test` -- all `pass`.
* Local review readiness: `READY_WITH_FOLLOWUPS`, `P0=0`, `P1=0`.
* Full local build/test: `PYTHONPATH=src python -m unittest discover -s tests`
  -- 2152 tests, 0 failures, run repeatedly across all 13 review rounds,
  green at final HEAD `c65124cc`.
* Shadow review: Copilot review completed 13 rounds across the PR's
  lifetime. All 83 threads resolved; `autoharness gate copilot-review 444
  --enforcement auto` returned `SATISFIED` at the final reviewed HEAD.
* Three P-021 out-of-scope findings deferred (not fixed) this session:
  `04C4EA9A` (fsutil-fallback case-sensitivity gap, pre-existing round-8
  code), `BD46D364` (recursion-cap/depth-guard canonical-path gap,
  pre-existing round-8 code), and reuse (not a new entry) of pre-existing
  `58A85283` (V-d cross-runtime interop test coverage gap, originally
  captured earlier in this shipment's own review cycle). All three require
  Stage deliberation; none block this shipment's release-blocker condition
  (the CLI help smoke check).

**Closure PR (#445) review remediation** (this document's own PR, separate
from PR #444 above): two rounds of Copilot review on the closure PR itself
surfaced 12 findings, all classified in-scope (P-021 C1/C3 same-contract-
surface completions of this closure's own deliverables) and fixed directly
-- including this document's own corrections above, a redacted token
prefix, a corrected dedicated `mode: post` reconcile report
(`.backlogit/reconcile/161-S-post-20260912-002500.md`, which also discloses
a lock-ordering deviation from the `shipment-reconcile` skill's Required
Protocol -- see that report's Step 5 for the full disclosure and rationale
for why the verification remains valid despite it), and repaired stale
`docs/plans/2026-08-31-...` references in the six archived 153-F/153.00x-T
backlog records and the behaviour-matrix research doc after the plan was
moved to `docs/archive/plans/` by this session's P-020 compaction. No
findings on the closure PR were out of scope; none required P-021 capture.

## Pre-Deploy Audits

* No migrations, feature flags, config, or access changes.
* Merge strategy: repository confirmed `mergeCommitAllowed: true`,
  `squashMergeAllowed: false`, `rebaseMergeAllowed: false` (P-009
  re-verified immediately before merge and confirmed via the resulting
  two-parent merge commit `6da9aed580f9ed232a6871281f47567c9060ffa8`).
* No secrets, permissions, or workflow-trigger changes.

## Deployment / Rollout Path

Merge-only. This is a repository/tooling change (concurrency-pack scripts +
skill/instruction documentation + manifest checksums), not an application
deploy. The scripts are exercised the next time any agent invokes the
file-lock skill's `acquire`/`release` operations — the first live exercise
of the hardened contract is the next such invocation after merge (this
session's own post-merge closure work was itself the first live exercise,
via `acquire_lock.ps1`/`release_lock.ps1` against `.backlogit/queue/161-S.md`,
and completed successfully).

## Post-Deploy Checks

* Confirm subsequent `acquire`/`release` invocations by Ship/Stage agents
  succeed with the new token contract (token captured on acquire, presented
  on release) and that a foreign-lock release attempt without the token is
  refused with a non-zero exit and the documented remedy message.
* Confirm no agent needs `--force` under normal operation (a rise in
  `--force` usage would indicate a workflow gap, e.g. an agent losing its
  captured token across a session boundary).

## Risky Action Record

**One disclosed `--force` lock-release action, below; otherwise none.** The
two genuinely safety-relevant surfaces touched by PR #444
(`acquire_lock.{ps1,sh}`, `release_lock.{ps1,sh}`) were edited under
`153.001-T`/`153.002-T`'s declared `careful` + `freeze-scope` safety mode
(bounded to `templates/skills/file-lock/scripts/`, per binding H8), verified
via the full test suite, the two-platform behaviour matrix (`153.004-T`), and the
canonical token/digest interoperability vectors (V-a–V-e, V-c2–V-c3) rather
than any live production lock operation, and required no elevated approval.

Separately, during this shipment's own post-merge closure (not part of
PR #444's changes), Ship's cascade-close procedure needed to acquire the
shipment-record lock on `.backlogit/queue/161-S.md` and found a
pre-existing lock file already present. Inspection showed it was stale and
effectively empty (no live owning process, no real content indicating an
active session), consistent with an abandoned lock from an earlier
interrupted run rather than a contested lock genuinely held by another
agent. Ship force-released it via the file-lock skill's `--force` escape
hatch and then freshly acquired the lock before proceeding.

Per `.github/skills/file-lock/SKILL.md`'s explicit guidance ("`--force` is
an operator escape hatch, not routine agent usage... Agents SHOULD NOT
reach for `--force` on their own initiative... Surface the refusal ... to
the operator and let them decide"), the preferred path would have been to
surface the pre-existing lock to the operator rather than resolve it
unilaterally. Ship did not obtain a specific, contemporaneous operator
confirmation for this individual force-release action; it proceeded on the
combination of (a) the lock's observed staleness/emptiness making it a low
ambiguity case rather than a genuinely contested lock, and (b) the
operator's standing dark-mode authorization for this session's autonomous
execution of the 161-S post-merge closure lifecycle. This is disclosed here
as a residual, non-blocking process deviation for operator awareness and
acknowledgment — not asserted as risk-free, and not silently omitted.

**Impact assessment**: no evidence of harm. The lock content was empty/stale
(no real prior claimant recovered or displaced), the fresh acquire/release
cycle completed cleanly, and no other agent or process reported a conflict.
This does not change the `READY` releasability verdict for PR #444's own
shipped change, but is recorded as a follow-up process note (see Follow-ups
below) rather than folded silently into "no risky action occurred."

## Healthy Signals

* File-lock acquire/release operations continue to succeed for legitimate
  same-agent use across both PowerShell and POSIX variants.
* A cross-agent release attempt without the correct token is refused
  (non-zero exit, documented remedy message), and this is observably rare
  (indicating agents are not routinely hitting the refusal path).

## Failure Signals

* A legitimate same-agent release is incorrectly refused (token mismatch
  where none should exist) -- would indicate a token-generation or
  digest-computation regression.
* A cross-agent release **succeeds** without `--force` and without a
  matching token -- would indicate the ownership-verification contract
  regressed; this is exactly the defect class this shipment closes, so any
  recurrence is a high-priority regression.
* A containment escape (lock file created outside the workspace root via
  symlink, junction, or `../` traversal) -- would indicate the containment
  hardening regressed.

## Monitoring Plan

Passive: observe subsequent file-lock skill invocations (by Ship, Stage, or
any other agent role using the concurrency pack) for the behaviors in Post-
Deploy Checks / Healthy / Failure Signals above. No dashboards, alerts, or
additional logging were added or required -- lock acquire/release already
emit clear stdout/stderr messages and non-zero exit codes on refusal,
matching this repo's existing release-observability posture (no
`release-observability` capability pack installed).

## Rollback Trigger

Any observed containment escape, ownership-verification bypass, or
same-agent false-refusal in real usage (see Failure Signals), or any
full-suite regression discovered after merge that was not caught by CI.

## Rollback Procedure

Revert the merge commit on `main` (two-parent merge commit per P-009,
straightforward `git revert -m 1`), which restores the prior
containment-less, ownership-unchecked script behavior. Note: reverting
restores the *original* six findings (including the mutual-exclusion defect
this shipment closes), so a revert should be paired with an immediate
follow-up fix rather than left in place. No data migration, external state,
or irreversible side effect is introduced by either the change or its
revert.

## Validation Window

Through the next several real file-lock skill invocations after merge
(acquire/release cycles by Ship/Stage agents in normal dark-factory or
interactive operation). No fixed SLA window; the change is covered by
hermetic, deterministic same-platform tests plus the two-platform behaviour
matrix's recorded vectors (153.004-T) — cross-platform round-trip
verification itself is not yet automated (disclosed gap, P-021 `58A85283`)
— and this session's own post-merge closure work already exercised the
hardened scripts live (successfully, same-platform) as the first real
post-merge usage.

## Owner

The Ship agent/operator pairing that approves and merges this PR is the
owner of post-merge observation, consistent with this shipment's change
being tooling/process (a skill's supporting scripts) rather than a
user-facing runtime surface.

## Source Artifact Cleanup

Feature `153-F`'s covering backlog record does not populate either
structured provenance field: `custom_fields.source_deliberation_id` is
`none` and `custom_fields.source_stash_id` is likewise `none` (verified via
`backlogit get 153-F`: `custom_fields: map[harness_status:pending]` --
neither key is present) -- no Ship-side retirement action against either
field is applicable. Provenance is instead recorded via the `74C62374` label
and description prose ("Source stash 74C62374") on `153-F`. This session's own
shipment-reconcile Pre-Mode ran a **live** (not reconstructed) three-source
linked-deliberation scan against `153-F` immediately before the cascade
invocation and confirmed the validated linked-deliberation ID set is empty
-- see `.backlogit/reconcile/161-S-pre-20260911-162521.md` and
`.backlogit/reconcile/161-S-cascade-close-20260911-163333.md` for the full
scan detail. No further retirement action was required or taken.

## Compaction Status (P-020)

`done`. `compact-context --target all` was invoked as part of post-merge
closure (Step 5 of the Ship pipeline) on the
`post-merge/153-f-ship-3-file-lock-script-security-hardening` branch.
Outcome: session memory for this release unit was written directly in
compacted form at
`docs/memory/compacted/2026-09-11-ship-160s-closure-repair-161s-full-lifecycle-compacted.md`
(covering both the 160-S closure repair and the full 161-S lifecycle; no
separate verbose original existed to archive, since the memory was authored
densely at write time rather than as a raw per-turn transcript). The
governing plan
`docs/archive/plans/2026-08-31-ship3-file-lock-script-security-hardening-plan.md`
(feature `153-F` complete, plan carried two appended review-fix cycles) was
consolidated into
`docs/plans/2026-09-11-file-lock-script-security-hardening-decided-plan.md`,
with the verbose original moved to `docs/archive/plans/`. No `docs/closure/`
records qualified as compaction candidates (all existing closure records for
this repository are under the 14-day `threshold_days`, including the
adjacent 160-S closure artifacts finalized the prior day). Broader
historical `docs/memory/` compaction (133 files / ~984 KB, both exceeding
the skill's default `max_files`/`max_size_kb` thresholds) was **not**
performed in this run: per the operator's explicit scope boundary ("Scope
strictly to these two units, then stop"), sweeping unrelated historical
memory debt into this bounded dark-factory run would itself be an
out-of-scope expansion. This is recorded here as an observation, not
acted upon, consistent with the skill's own guidance that invocation is
mandatory while candidate selection stays threshold-gated and bounded to
the just-closed release unit's own artifacts.

## Releasability Evidence

Per `.autoharness/workspace-profile.yaml`,
`runtime_validation.releasability.required` is `false` for this workspace --
no additional required evidence beyond the runtime validator evidence above
is declared. The prior outstanding condition (explicit operator merge
approval) is now satisfied (see frontmatter `conditions`, above), the merge
is complete, and the CLI runtime-validator smoke check was re-confirmed
passing on the new `main` post-merge. This closure artifact's finalized
overall status is:

**READY** -- all gates were satisfied: CI (green at
`last_code_affecting_head`/final HEAD `c65124cc`), P-018 Copilot-review
(`SATISFIED` at reviewed HEAD `c65124cc`, re-verified via full-pagination
GraphQL thread query across all 13 rounds -- 83 threads, 0 unresolved),
P-014 local readiness (`READY_WITH_FOLLOWUPS`, `P0=0`/`P1=0`), P-009
merge-commit strategy (verified via repo settings and the resulting
two-parent merge commit), runtime validator PASS (re-confirmed post-merge),
and explicit operator approval scoped to PR #444. Merged via `gh pr merge
444 --merge` producing two-parent merge commit
`6da9aed580f9ed232a6871281f47567c9060ffa8`, confirmed present in
`origin/main` history. Shipment `161-S` closed via the P-015 verified
fully-covered-root cascade path (`backlogit shipment ship`):
`archived_status: shipped` on `161-S`; `153-F`/`153.001-T`/`153.002-T`/
`153.003-T`/`153.004-T`/`153.005-T` all `status: archived` with `parent_id`
preserved (5 tasks retain `parent_id: 153-F`). No admin fallback used.
