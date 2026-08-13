---
type: session-memory
agent: ship
related_shipment: 129-S
related_feature: 120-F
correction_pr: 334
correction_merge_commit: 43b531b0e63c10be2e0870faca38484bb9366b1b
date: 2026-08-13
---

# Ship Session Memory — 129-S/120-F Post-Closure Runtime-Binding Correction

## Context

`129-S`/`120-F` (Plan-1, S3 Copilot supervisor) was already merged, archived,
and closed before this session began. The operator directly reported a
**verified live defect**: even with `129-S`'s fix in place, a real running
Copilot session's Engram daemon bound to the wrong sibling workspace
(`C:\Source\GitHub\engram` instead of `C:\Source\GitHub\autoharness`). Per
explicit operator instruction, `129-S` was **not** reopened, reclaimed, or
re-triaged; no backlogit shipment or task was created for this work. This
was executed entirely as a standalone git branch/PR under Ship's post-merge
correction authority, with dark-mode full-merge approval already
pre-authorized by the operator for this specific delivery.

## Decisions

1. **Root cause correction, not new work**: The prior fix's premise (remove
   `${workspaceFolder}`, rely on CWD anchoring) was disproven, not
   incomplete-but-on-track. Framed the correction as a root-cause
   correction addendum to the existing closure record, not a new feature.
2. **No new environment variable invented for backlogit**: verified via
   `backlogit --help` that no `BACKLOGIT_WORKSPACE`-equivalent exists;
   backlogit relies solely on `--cwd`. Avoided inventing unsupported env
   surface.
3. **Reused the existing `_ENVIRON_MUTATION_LOCK` serialization** in
   `app.py` rather than refactoring to explicit per-child env threading —
   a deliberate, documented, smaller-blast-radius choice given the
   existing mechanism was already proven to span the full child lifetime.
4. **Force-apply, not NO-CLOBBER**: the three binding vars
   (`ENGRAM_WORKSPACE`, `GRAPHTOR_DB_PATH`, `GRAPHTOR_SOURCES`) are the
   sole exception to `bootstrap.py`'s universal additions-only contract,
   applied last so the explicit `--workspace` target always wins over
   ambient/`.env.local` values.
5. **Never touch the operator's live process tree**: every verification
   step used new, isolated, git-initialized temp workspaces with careful
   before/after PID diffing and exact-PID/marker-based cleanup.

## Files Modified (correction PR #334)

- `src/autoharness/supervise/bootstrap.py` (core fix)
- `tests/test_supervise_bootstrap.py`, `test_supervise_app.py`,
  `test_supervise_process.py`, `test_supervise_process_pty.py`,
  `test_verify_workspace.py` (regression coverage)
- `tests/test_supervise_binding_real_binary_smoke.py` (new, opt-in
  real-binary smoke suite)
- `docs/closure/129-S-120-F-post-merge-closure.md` (Post-Closure Correction
  Addendum section appended)
- `docs/compound/129-s-supervisor-engram-graphtor-startup-and-review-hardening.md`
  (root-cause narrative corrected, `correction_pr: 334` set)

## Key Learnings

1. **"CWD is correct" and "env binds to the correct target" are
   independent claims.** A tool with both a CWD-relative default and an
   env-var override can still bind wrong even with provably-correct CWD,
   if any ambient/stale value for that override is present at spawn time.
2. **Both `engram` and `graphtor-docs` CLI invocations can leave a
   detached daemon holding inherited stdout/stderr pipe handles**, causing
   `subprocess.run(capture_output=True, timeout=N)` to hang indefinitely
   even with a timeout (CPython's timeout path still does one final
   blocking `communicate()`). Fix: redirect to real files, use
   `proc.wait()`, clean up with `shutil.rmtree(ignore_errors=True)` in a
   `finally`, not a context manager.
3. **`graphtor-docs`'s path-violation boundary only activates once a
   `.graphtor/config/sources.yaml` marker exists at cwd** — without it, no
   boundary is enforced at all. Any test asserting rejection of an
   out-of-workspace path must pre-create that marker.
4. **Never echo an untrusted override-diagnostic value verbatim** — a
   Copilot review finding caught that the original warning implementation
   echoed the ambient/`.env.local` preset value being overridden, which is
   untrusted input, not guaranteed to be a filesystem path.  Fixed to log
   only the variable name and the new trusted (workspace-derived) value.
5. **PowerShell single-quoted string interpolation of a temp-path marker
   needs escaping** (`'` -> `''`) since environment/username data can
   contain characters that break a literal.

## Outcome

- PR #334 merged via merge commit `43b531b0e63c10be2e0870faca38484bb9366b1b`
  (2 parents, confirmed ancestor of `origin/main`).
- 1 round of Copilot (P-018) review, 5/5 findings fixed and resolved.
- CI green at every polled HEAD.
- Full local suite: 1887 tests, OK (skipped=23), both before and after the
  review-fix commit.
- No backlogit shipment/task created or touched; `129-S` remains archived
  exactly as before.
