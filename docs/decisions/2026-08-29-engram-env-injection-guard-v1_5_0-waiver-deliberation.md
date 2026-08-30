---
title: "Stale Engram env-injection guard after supervisor deletion: v1.5.0 disposition and waiver"
date: 2026-08-29
doc_type: decision
stash_id: B698F01B
agent: "Stage (planning only - Ship executes)"
classification: "bug / test-guard coherence + local capability degradation"
blast_radius: "none on the published artifact; local dev workspace only"
route: "claude-opus-5 / anthropic / high"
---

# Deliberation - stale Engram env-injection guard (`B698F01B`)

Date: 2026-08-29
Agent: Stage (planning only - Ship executes)
Stash source: `B698F01B` (critical, bug — operator-labeled **work-in-progress**)
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Decision (one line)

**Explicit, evidence-backed WAIVER for v1.5.0.** The entry's blocking symptom
no longer exists at `484da671`, none of its residual defects can reach the
published artifact, and its one genuine open question is a design decision the
operator has reserved. The entry **remains ACTIVE and is NOT archived**;
operator work-in-progress intent is preserved.

## Problem statement

`B698F01B` was filed as **critical/BLOCKING**: an uncommitted `.mcp.json` change
failed the test suite, and the entry argued the `120-F` guard had become
*unsatisfiable* because the supervisor that was supposed to supply
`ENGRAM_WORKSPACE` had been deleted — a "penalizing mechanism outlived the
producing mechanism" trap in which all three remediation options were blocked.

The release question: **is this a v1.5.0 blocker, or can it be waived with
evidence?**

## Research findings (verified at `484da671`, current HEAD)

**Finding 1 — the blocking symptom is GONE.** The entry's premise was a dirty
working tree. Current state: worktree **clean**, single worktree, `main` exactly
equal to `origin/main`, **CI green**. The committed `.mcp.json` contains
`backlogit`, `engram`, `graphtor-docs`, `context7`, `tavily`, `github` — with
**no `env` block on any server**.

Re-evaluating all three guards against the *committed* file:

| Guard | Location | Status at HEAD |
|---|---|---|
| `assertIn('"graphtor-docs"', ...)` | `test_verify_workspace.py:249` | **PASSES** — entry present |
| `assertNotIn("${workspaceFolder}", ...)` | `:257` | **PASSES** — absent |
| `assertNotIn('"env"', ...)` | `:296` | **PASSES** — no `env` block |

The guard is **not currently unsatisfiable**; it is satisfied. The "trap" was a
property of the operator's pending edit, not of the committed tree.

**Finding 2 — graphtor-docs is NOT being removed.** The entry's decision
question 1 asks whether the pack is being deliberately dropped. Evidence says
no: it is present in `.mcp.json`, `.github/instructions/graphtor-docs.instructions.md`
ships, and the pack remains declared. Question 1 is **answered: it stays.**

**Finding 3 — the orphaned `__pycache__` CANNOT ship.** `src/autoharness/supervise/`
contains only `__pycache__/` with 17 source-less `.pyc` files. But:

* `git ls-files src/autoharness/supervise/` returns **empty** — untracked.
* `.gitignore` L5 `*.pyc` and L25 pin it as ignored.

`release.yml` builds from a **fresh CI checkout**, where this directory does not
exist. It is a **local-machine-only artifact** and is structurally incapable of
entering the wheel or sdist. Real hygiene debt; **zero release risk**.

**Finding 4 — the stale guard comment is real but unshipped.** `ENGRAM_WORKSPACE`
appears in exactly **one** live location repository-wide:
`tests/test_verify_workspace.py:264`. The sole live `supervise` reference in
`src/` or `tests/` is the guard's own comment at `:266`, citing the deleted
`autoharness.supervise.bootstrap`. This is a genuine documentation-accuracy
defect **inside a comment** — no runtime effect — and `tests/` is not packaged.

**Finding 5 — the env-injection gap is real, and is a design question.**
Nothing supplies `ENGRAM_WORKSPACE`. `.env.local` (gitignored, per-developer)
carries `workspace_folder` / `workspaceFolder` / `GRAPHTOR_EMBED_MODEL_DIR` but
**not** `ENGRAM_WORKSPACE`. Corroborating live evidence: **this very Stage
session ran in `ENGRAM_DEGRADED` mode.** The capability degradation is real and
observable — but it degrades *local agent tooling*, not the published package.

## Options evaluated

### Option A: Fix before v1.5.0 (choose and implement a new env mechanism)

*Pro*: restores Engram; removes the stale comment.
*Con*: the entry itself states **"do NOT auto-fix — needs operator intent"** and
poses three open design choices (launcher wrapper vs `.env.local` sourcing vs
relaxing the guard to a workspace-relative value). Each has different, non-obvious
consequences, including the documented `120-F` crash where the standalone
`copilot` CLI passes `${workspaceFolder}` through **literally**. Deciding this
under release pressure is exactly how the original regression happened.
**Rejected.**

### Option B: Explicit evidence-backed waiver; entry stays ACTIVE (SELECTED)

Waive for v1.5.0 on the recorded evidence; keep the entry open with the waiver
appended so the operator's WIP is preserved and re-triage is cheap.

*Pro*: honest, evidence-based, zero risk to the release, preserves operator
intent, does not prejudge a reserved design decision.
*Con*: Engram stays degraded locally until the operator decides — an accepted,
recorded cost.

### Option C: Archive the entry as resolved

*Pro*: tidy.
*Con*: **factually wrong and explicitly forbidden here.** Findings 4 and 5 are
unresolved; the operator labeled this work-in-progress. Archiving would destroy
a live design question. **Rejected.**

### Option D: Partial fix — delete the orphaned `__pycache__` and correct the comment only

*Pro*: cheap; removes phantom-import risk and a false citation.
*Con*: touches `tests/` and `src/` during a release whose entire value is a
*clean, verifiable* publish of already-shipped work. Neither sub-defect can
reach the artifact (Findings 3–4), so this buys no release safety while adding
diff surface to the release PR. It also leaves the *substantive* question
(Finding 5) untouched, so the entry stays open regardless — meaning the fix
does not even close the item. **Rejected for v1.5.0**; folded into the deferred
follow-up.

## Trade-off comparison

| Option | Release risk closed | Respects operator WIP | Diff added to release PR | v1.5.0 fit |
|---|---|---|---|---|
| A | None (none exists) | **No** | Large | Poor |
| B | N/A — none to close | **Yes** | None | **Best** |
| C | N/A | **No** | None | Unacceptable |
| D | None | Partial | Moderate | Poor |

## Decision

Adopt **Option B: explicit WAIVER for v1.5.0.**

**Waiver justification, on the record:**

1. The originally-cited **CI-blocking failure does not exist at `484da671`** —
   all three guards pass and CI is green (Finding 1).
2. The **orphaned `.pyc` files are untracked and gitignored**, so they cannot
   enter the wheel built from CI's clean checkout (Finding 3).
3. The **stale guard comment lives in `tests/`, which is not packaged**, and has
   no runtime effect (Finding 4).
4. The **only substantive defect is a local capability degradation** that the
   entry itself reserves for operator decision (Finding 5).

No part of `B698F01B` can affect the correctness of the v1.5.0 wheel, sdist,
PyPI publish, or the published-package smoke test.

**Disposition: the entry REMAINS ACTIVE**, priority unchanged, with this waiver
recorded as an append. It is **not** archived, and it is **not** silently
downgraded.

## Rejected alternatives

Options A, C, and D above, for the recorded reasons.

## Unresolved questions (reserved for the operator)

1. What replaces the deleted supervisor as the env-injection mechanism —
   launcher wrapper, `.env.local` sourcing, or relaxing the guard to permit a
   workspace-relative (not absolute, not `${workspaceFolder}`) value?
2. Should the `:259–272` guard comment be rewritten to cite the *replacement*
   mechanism once chosen (it must stop citing a nonexistent module either way)?
3. Should `src/autoharness/supervise/` be removed outright as dead weight?

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Engram remains degraded for agent sessions | Documented; sessions fall back to file-based exploration (this session did so successfully) |
| The waiver is mistaken for a permanent dismissal | Entry stays ACTIVE at **critical**; waiver is explicitly scoped to "v1.5.0 publish" only |
| A future `.mcp.json` edit re-triggers the trap | The guard still passes today and still penalizes the unsafe patterns; the trap only reappears if someone re-adds an `env` block, which this deliberation documents |

## Traceability

* Stash: `B698F01B` (remains **ACTIVE** — waived, not consumed, not archived)
* Disposition: **NON-BLOCKER for v1.5.0 — explicit evidence-backed waiver**
* Operator intent (work-in-progress) preserved by design
