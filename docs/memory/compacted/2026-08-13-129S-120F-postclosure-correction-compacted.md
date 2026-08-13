---
compacted_from: docs/archive/memory/2026-08-13-ship-129-s-post-closure-runtime-binding-correction.md
release_unit: 129-S / 120-F (post-closure correction, PR #334)
date: 2026-08-13
---

# Compacted Memory — 129-S/120-F Post-Closure Runtime-Binding Correction (PR #334)

**Source (archived verbose original)**:
`docs/archive/memory/2026-08-13-ship-129-s-post-closure-runtime-binding-correction.md`

## Decisions

1. Delivered as a standalone correction PR (#334) on its own branch, under
   Ship's post-merge correction authority — `129-S`/`120-F` was **not**
   reopened, reclaimed, or re-triaged, and no backlogit shipment/task was
   created for this work, per explicit operator instruction.
2. Corrected root cause: `129-S`'s own fix (remove `.mcp.json`'s
   `${workspaceFolder}`, anchor child `cwd`) was necessary but not
   sufficient — an explicit `ENGRAM_WORKSPACE`/`GRAPHTOR_DB_PATH`/
   `GRAPHTOR_SOURCES` env var always wins over a CWD-relative default in
   both Engram's and graphtor-docs's own documented precedence.
3. `bootstrap_workspace()` now force-applies these three binding vars from
   the resolved `workspace_root`, last, overriding any stale ambient/
   `.env.local` value — the sole exception to the module's NO-CLOBBER
   contract. `BACKLOGIT_WORKSPACE` deliberately not invented (verified via
   `backlogit --help`: no such variable exists).
4. Reused the existing `_ENVIRON_MUTATION_LOCK` serialization in `app.py`
   rather than a new per-child explicit env-threading mechanism —
   deliberate, documented scope decision.
5. All live-process verification was read-only against the operator's
   real session; all fix verification used new, isolated, git-initialized
   temp workspaces with exact-PID/marker-based diff-and-reap discipline.

## Files Modified

- `src/autoharness/supervise/bootstrap.py` (core fix)
- `tests/test_supervise_bootstrap.py`, `test_supervise_app.py`,
  `test_supervise_process.py`, `test_supervise_process_pty.py`,
  `test_verify_workspace.py` (regression coverage)
- `tests/test_supervise_binding_real_binary_smoke.py` (new opt-in
  real-binary smoke suite, `AUTOHARNESS_REAL_BINARY_SMOKE=1`, Windows-only)
- `docs/closure/129-S-120-F-post-merge-closure.md` (Post-Closure Correction
  Addendum appended)
- `docs/compound/129-s-supervisor-engram-graphtor-startup-and-review-hardening.md`
  (root-cause narrative corrected, `correction_pr: 334` set)

## Key Learnings (cross-references)

- Full detail: `docs/compound/129-s-supervisor-engram-graphtor-startup-and-review-hardening.md`
  Post-Closure Correction section, and `docs/closure/129-S-120-F-post-merge-closure.md`
  Post-Closure Correction Addendum.
- Durable lesson: "CWD is correct" and "env binds to the correct target"
  are independent claims — an env-var override always wins over a
  CWD-relative default when a tool supports both, regardless of how the
  CWD was anchored.
- `engram`/`graphtor-docs` CLI invocations can leave a detached daemon
  holding inherited stdout/stderr pipe handles, hanging
  `subprocess.run(capture_output=True, timeout=N)` indefinitely even with
  a timeout — redirect to real files, use `proc.wait()`, clean up with
  `shutil.rmtree(ignore_errors=True)` in `finally`.
- `graphtor-docs`'s path-violation boundary only activates once a
  `.graphtor/config/sources.yaml` marker exists at cwd.
- Never echo an untrusted override-diagnostic value verbatim in a log/
  warning (Copilot review finding, round 1) — log only the variable name
  and the new trusted value.

## Outcomes

- PR #334 merged via merge commit `43b531b0e63c10be2e0870faca38484bb9366b1b`
  (2 parents, confirmed ancestor of `origin/main`).
- 1 round of Copilot (P-018) review, 5/5 findings fixed, replied-to, and
  GraphQL-resolved. CI green at every polled HEAD.
- Full local suite: 1887 tests, OK (skipped=23), both before and after the
  review-fix commit.
- No backlogit shipment/task created or touched; `129-S` remains archived
  exactly as it was before this correction.

## Provenance Chain

`docs/closure/129-S-120-F-post-merge-closure.md` (Post-Closure Correction
Addendum, full detail) ->
`docs/archive/memory/2026-08-13-ship-129-s-post-closure-runtime-binding-correction.md`
(archived verbose original) -> this compacted summary.

## Deferred

None new. Pre-existing `129-S`-scope follow-up (Windows-local-only
`RealParallelContenderTests` flakiness) is unaffected by this correction.
