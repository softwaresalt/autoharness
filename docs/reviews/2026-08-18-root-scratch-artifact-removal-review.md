---
title: "Adversarial Review — Remove stale tracked root scratch artifacts"
date: 2026-08-18
plan: docs/plans/2026-08-18-root-scratch-artifact-removal-plan.md
stash_id: 1EFDA8EE
personas: 6
verdict: PASS
unresolved_p0: 0
unresolved_p1: 0
---

# Adversarial Review — Root scratch artifact removal (1EFDA8EE)

Mandatory multi-persona adversarial review (DARK_MODE_ACTIVE, operator AFK).
Six personas. Verdict **PASS** — no unresolved P0/P1.

## Persona 1 — Destructive-action safety auditor

### F1 (P1, RESOLVED) — The authorizing premise "all three are identical" is FALSE

The stash entry and review finding F7 both authorize deletion on the premise
that all three files are *identical* 25.8 KB outputs. Verification disproves it:
`res.json` and `results.json` are byte-identical (blob `47be98ac…`), but
`out.json` is a **different** blob (`29a08875…`), 26390 vs 26388 bytes, 588 vs
587 lines.

**Why this is P1:** Ship is required to re-verify hashes before executing an
authorized destructive action. If the task carried the false "identical"
premise, Ship's own verification would contradict its authorization and it would
correctly **fail closed**, stalling the shipment. Worse, a careless
implementation could treat "identical" as licence to delete by content match.

**Resolution:** the plan records the correction explicitly (§2.2) and the
deletion task embeds **per-file** git blob IDs and SHA-256 digests. Authorization
is re-grounded on three *individually named and individually hashed* paths, not
on content equality. Disposition is unchanged: all three are external scratch
output.

### F2 (P1, RESOLVED) — Deletion must be pathspec-literal, never pattern-based

A `git rm *.json` or `git rm -r .` style invocation would destroy `.mcp.json`
and `plugin.json`, both legitimate tracked root files.

**Resolution:** plan §6.1 mandates three literal pathspecs with no wildcard, no
`-r`, no `.`; §5.1.3/§5.1.4 add post-conditions that assert the surviving root
allowlist and that exactly three deletions appear in `git status`.

### F3 (P2, RESOLVED) — Is the content recoverable if the deletion is wrong?

Yes. Single introducing commit `24777b44` is reachable on `main`; content is
restorable via `git show 24777b44:out.json`. Provenance is an external
workspace, so no autoharness-owned data is lost.

## Persona 2 — Evidence / provenance auditor

### F4 (P2, RESOLVED) — Provenance asserted, now proven

`workspace_path` is `D:\Source\GitHub\backlogit` in all three files, and
`mode` is `verify-workspace`. History corroborates accident: the single
introducing commit also added `src/autoharness/verify_workspace.py` and
`tests/test_verify_workspace.py`. No autoharness-owned state is embedded.

### F5 (P2, RESOLVED) — Historical records must not be rewritten

`docs/reviews/2026-08-17-backlogit-self-migration-review.md` (F7) and
`docs/memory/2026-08-17-stage-bed0dded-self-migration-staging.md` reference the
files in prose and repeat the inaccurate "identical" claim. Editing them to
"clean up" references would falsify the historical record and widen scope.

**Resolution:** plan §3.2 declares them explicitly OUT OF SCOPE. The correction
lives in the new plan/review artifacts, which is where corrections belong.

## Persona 3 — Test / CI engineer

### F6 (P1, RESOLVED) — Task ordering would otherwise produce a transient red CI

The allowlist test asserts the three files are absent. If the test task landed
before the deletion task, CI would be red at that commit.

**Resolution:** a hard `blocks`/`depends_on` dependency wires the prevention task
behind the deletion task, and plan §6 fixes the execution order (delete, verify,
then add the test).

### F7 (P2, RESOLVED) — `git ls-files "*.json"` is NOT root-anchored

Git pathspec wildcards match across `/`, so `*.json` returns nested matches
including vendored `references/*` content. An unfiltered assertion would fail
immediately and could drag the suite into vendored trees — the exact failure
class recorded in `docs/compound/097-S-canonical-unittest-gate.md`.

**Resolution:** plan §5.2 mandates a depth-0 filter (reject any path containing
`/`) applied to `git ls-files` output.

### F8 (P2, RESOLVED) — Repo root must be derived from `__file__`, not cwd

`python -m unittest discover -s tests` normally runs from the repo root, but
relying on cwd makes the test environment-dependent and non-deterministic.

**Resolution:** the test resolves the repository root as the parent of the
`tests/` directory containing `__file__`, and passes it as the subprocess cwd.

### F9 (P2, RESOLVED) — Canonical gate is `unittest`, not `pytest`

Per `docs/compound/097-S-canonical-unittest-gate.md`, root `pytest` wanders into
`references/*`. The new test is a stdlib `unittest.TestCase`, discoverable by
`PYTHONPATH=src python -m unittest discover -s tests`, and `skipTest`s when git
is unavailable.

### F10 (P2, RESOLVED) — Will CI actually run the new test?

Yes, verified against `.github/workflows/ci.yml`. The `changes` job is a
fail-closed denylist excluding only `docs/**`, `.backlogit/**`, `.autoharness/**`.
Root `*.json` and `tests/**` fall outside those exclusions, so `code == 'true'`
and the `test` job runs. **No workflow edit is required** — proposing one would
have been unnecessary scope.

### F11 (P2, RESOLVED) — Is the exact deletion-stat assertion (1762) safe?

Empirically verified: `git show --numstat 24777b44` reports 588/587/587
insertions, and all three files terminate with byte `0x0A`, so no
"\ No newline at end of file" accounting skew exists. 588+587+587 = 1762 is a
sound deterministic gate.

## Persona 4 — Minimalism / over-engineering reviewer

### F12 (P2, RESOLVED) — The stash entry's suggested `.gitignore` rule is the WRONG control

The stash entry proposes "a gitignore rule **or** a CI check". Adopting both, or
the ignore alone, was challenged and rejected:

- an ignore rule matching three literal names has **strictly weaker** coverage
  than the allowlist test (any new generic name bypasses it);
- it fails **silently** — files vanish from `git add` with no diagnostic —
  whereas the test fails loudly and names the offender;
- it does nothing about the present defect, since `.gitignore` never untracks
  already-tracked files;
- it would silently suppress a hypothetical legitimate future root JSON file.

**Resolution:** plan §4 selects the allowlist test only, with the rejection
rationale recorded so this is auditable as a *deliberate* decision rather than a
dropped requirement. This also fully honours the prohibition on broad `*.json`
ignores — no ignore rule is added at all.

### F13 (P2, RESOLVED) — Is even one test over-engineering for a `low` hygiene item?

Challenged. Justified: the operator independently requires *deterministic
verification for absence/tracking and no collateral files*. The allowlist test
**is** that verification. It therefore adds zero artifacts beyond the mandatory
verification surface while also serving as the recurrence control — the cheapest
possible way to satisfy both requirements. A no-control option was considered
and rejected only because the filenames are maximally generic.

## Persona 5 — Backlog / process governance

### F14 (P1, RESOLVED) — Stage must not perform the deletion

Deleting tracked files is implementation work (P-010 role boundary). Stage
inspected and hashed read-only and preserved byte content; the three files remain
present and unmodified at Stage completion (re-verified post-commit).

### F15 (P2, RESOLVED) — Scope containment

Exactly one stash entry (1EFDA8EE) is consumed. `EDE3CC2D` was already consumed
by shipment 141-S and is absent from `stash.jsonl`; it is not re-touched. No
other stash or queue item is read into scope, and the shipment manifest is
restricted to IDs emitted by this harvest.

### F16 (P3, ACCEPTED — follow-up) — Backlog registry drift

`.autoharness/backlog-registry.yaml` declares no `features.sizing` flag and its
`update_task` params omit `size`/`complexity`, but the installed backlogit
v1.9.0 CLI supports `--size`, `--size-source`, `--size-ruleset-version` and
`--complexity` as body-preserving, mutually exclusive mutations (and
`shipment list` already emits `size_composition`). The registry is stale
relative to the tool.

**Disposition:** ACCEPTED, not fixed here — unrelated to 1EFDA8EE and would
widen the diff. Sizing is emitted using the tool's real capability. Recorded as a
follow-up.

## Persona 6 — Concurrency / operator-staged-state auditor

### F17 (P1, RESOLVED) — Operator-staged submodule entries must survive Stage's commit

`.gitmodules` (blob `4e0b9c4c…`) and gitlinks `references/skillopt`,
`references/waza`, `references/witr` are staged by the operator, who may add more
concurrently. A bare `git commit` would sweep them into Stage's commit — a
drift/loss event and an immediate halt condition.

**Resolution:** Stage performs **explicit-pathspec commits only**
(`git commit -- <paths>`), which builds a temporary index from HEAD plus the
named paths and leaves all other staged entries untouched. The full index is
snapshotted before and after every branch transition and every commit and
compared byte-for-byte. `references/` is additionally `.gitignore`d at large, and
no Stage artifact path intersects `.gitmodules` or `references/*`.

### F18 (P2, RESOLVED) — Branch transition safety

`git switch -c` from the current HEAD creates a ref and moves HEAD without
touching the index or worktree, so staged entries are preserved by construction.
Verified empirically before and after.

### F19 (P2, RESOLVED) — Packaging impact

`pyproject.toml` uses `[tool.hatch.build.targets.wheel.force-include]` with an
explicit allowlist of directories/files; root `*.json` is not among them, and
`packages = ["src/autoharness"]`. Deleting the three files cannot affect the
wheel or sdist.

## Summary

| ID | Severity | Status |
|---|---|---|
| F1 | P1 | RESOLVED |
| F2 | P1 | RESOLVED |
| F6 | P1 | RESOLVED |
| F14 | P1 | RESOLVED |
| F17 | P1 | RESOLVED |
| F3, F4, F5, F7, F8, F9, F10, F11, F12, F13, F15, F18, F19 | P2 | RESOLVED |
| F16 | P3 | ACCEPTED (follow-up) |

**Unresolved P0: 0. Unresolved P1: 0. Verdict: PASS — cleared for harvest.**
