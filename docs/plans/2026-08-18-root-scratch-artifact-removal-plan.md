---
title: "Remove stale tracked root scratch artifacts (out.json, res.json, results.json)"
date: 2026-08-18
stash_id: 1EFDA8EE
source_finding: "F7 (P2, OUT OF SCOPE) — docs/reviews/2026-08-17-backlogit-self-migration-review.md"
requires_plan_hardening: no
blast_radius: low
---

# Plan — Remove stale tracked root scratch artifacts

## 1. Problem

Three tracked files at the autoharness repository root are stale scratch output
from an `autoharness verify-workspace --format json` run that targeted an
**external** workspace. They are accidental commits with no functional role.

## 2. Verified evidence (Stage, read-only)

### 2.1 Tracking and blob identity

| Path | Mode | Git blob (HEAD == index == worktree) | Bytes | Lines |
|---|---|---|---|---|
| `out.json` | 100644 | `29a088754b362b6e9e45198225adefadbb3e7913` | 26390 | 588 |
| `res.json` | 100644 | `47be98ac91bee2502ee56a41f120e0255236112b` | 26388 | 587 |
| `results.json` | 100644 | `47be98ac91bee2502ee56a41f120e0255236112b` | 26388 | 587 |

Worktree SHA-256:

| Path | SHA-256 |
|---|---|
| `out.json` | `12F53D59E58B771EB627EAA6915ABAB35ABFB684E99BE2AD44D9C9278C525843` |
| `res.json` | `8D6948EA28B83C771B2DA71C9D2BA41B029025784FDF0183169A3A2FA8635395` |
| `results.json` | `8D6948EA28B83C771B2DA71C9D2BA41B029025784FDF0183169A3A2FA8635395` |

### 2.2 EVIDENCE CORRECTION vs. the stash entry

The stash entry and F7 both assert **"all three are identical 25.8 KB"**. That is
**inaccurate** and is corrected here:

- `res.json` and `results.json` ARE byte-identical (same git blob
  `47be98ac…`, same SHA-256).
- `out.json` is **NOT** identical: distinct blob, distinct SHA-256, 26390 vs
  26388 bytes, 588 vs 587 lines — a one-line delta
  (`git diff --no-index out.json res.json` = `1 file changed, 1 deletion(-)`).
- Actual size is ~25.77 KiB (26388–26390 bytes), consistent with "~25.8 KB".

This correction does **not** change the disposition: all three remain external,
non-functional scratch output. It is recorded so the deletion is authorized on
*verified* facts rather than on the inaccurate "identical" premise.

### 2.3 Provenance

All three begin with:

```json
{
  "mode": "verify-workspace",
  "workspace_path": "D:\\Source\\GitHub\\backlogit",
  "autoharness_home": "D:\\Source\\GitHub\\autoharness",
```

`workspace_path` is the **external** `D:\Source\GitHub\backlogit` repository.
Their `.backlogit` references are that external workspace's storage directory,
so they are outside the autoharness storage-root migration surface, confirming
the F7 disposition.

### 2.4 History

Introduced by exactly one commit and never modified since:

- `24777b4409de04da05a9ff535cb23d249e32603f` — "Refactor code structure for
  improved readability and maintainability", williamsderek, 2026-04-25.
- That same commit added `src/autoharness/verify_workspace.py` and
  `tests/test_verify_workspace.py`, corroborating accidental capture of ad-hoc
  CLI output during feature development.
- `git log --all -- out.json res.json results.json` returns this single commit.

### 2.5 Collateral-reference analysis (no functional dependents)

`git grep` across the whole repository for `out.json` / `res.json` /
`results.json` returns only **prose** references in historical records:

- `.backlogit/stash.jsonl` (entry 1EFDA8EE itself)
- `docs/memory/2026-08-17-stage-bed0dded-self-migration-staging.md`
- `docs/reviews/2026-08-17-backlogit-self-migration-review.md` (F7)

There are **no** references from source, tests, CI workflows, scripts,
`pyproject.toml`, or packaging. Deletion has zero functional blast radius.
The three historical documents are immutable records and MUST NOT be edited.

### 2.6 Root-level tracked JSON inventory

`git ls-files "*.json"` restricted to the repository root returns exactly five
paths:

- `.mcp.json` — **legitimate**, canonical shared MCP workspace config (tracked
  by explicit `.gitignore` comment).
- `plugin.json` — **legitimate**, plugin manifest (`"name": "autoharness"`,
  `"version": "1.4.11"`).
- `out.json`, `res.json`, `results.json` — the three deletion targets.

## 3. Scope

### 3.1 IN SCOPE

1. Delete exactly three tracked files: `out.json`, `res.json`, `results.json`.
2. Add one deterministic regression test enforcing a root-level tracked-JSON
   allowlist.

### 3.2 OUT OF SCOPE (explicit)

- Any other file, wildcard, or "general cleanup" of the repository root.
- Any `*.json` ignore rule (broad ignores are explicitly prohibited).
- Editing `docs/reviews/2026-08-17-backlogit-self-migration-review.md`,
  `docs/memory/2026-08-17-stage-bed0dded-self-migration-staging.md`, or the
  historical stash record.
- `.gitmodules` and every `references/*` gitlink (operator-staged; protected).
- Any change to `.mcp.json` or `plugin.json`.

## 4. Recurrence-prevention decision

**Decision: adopt a single deterministic allowlist test. Add NO `.gitignore` rule.**

Options considered:

| Option | Coverage | Failure mode | Verdict |
|---|---|---|---|
| A. No control | none | silent recurrence | Rejected — names are maximally generic (`out`/`res`/`results`), so recurrence is plausible |
| B. Root-anchored ignore of the 3 exact names | only these 3 names | **silent** non-staging | Rejected — see below |
| C. Deterministic root-JSON allowlist test | **any** unexpected root `*.json` | loud, explicit failure | **ADOPTED** |
| D. B + C | same as C | inherits B's silent footgun | Rejected as over-engineering |

Rationale for rejecting the `.gitignore` rule (Option B), despite the stash
entry suggesting one:

1. **Strictly weaker coverage.** B matches three literal names. The next ad-hoc
   dump (`verify.json`, `out2.json`, `o.json`) bypasses it entirely. C's
   coverage is a strict superset.
2. **Worse failure mode.** An ignore rule causes a file to be *silently*
   skipped by `git add`, which is a known footgun; C fails loudly with an
   actionable message naming the offending file.
3. **No effect on the present defect.** `.gitignore` does not untrack
   already-tracked files, so B contributes nothing to the actual fix.
4. **Future false-negative.** B would silently block a hypothetical legitimate
   future root `results.json`; C would reject it loudly and reviewably.

Answering the stash entry's "gitignore rule **or** a CI check": the CI check is
selected. The names ARE generic outputs (confirmed §2.6), which is precisely why
a name-list control is the wrong shape and an allowlist control is the right one.
This is the narrowest **robust** control, and it doubles as the deterministic
verification required for the deletion, so it adds no artifact beyond what
verification already demands.

## 5. Deterministic verification

### 5.1 Post-deletion assertions (exit-code checked)

1. `git ls-files --error-unmatch out.json` exits **non-zero** (untracked); same
   for `res.json`, `results.json`.
2. `Test-Path out.json` is `$false`; same for `res.json`, `results.json`.
3. `git ls-files "*.json"` filtered to root == exactly `.mcp.json`, `plugin.json`
   — proving both absence AND no collateral file loss.
4. `git status --porcelain` shows exactly three `D ` entries for the three
   named paths and no other deletion.
5. `git diff --cached --stat` for the deletion commit touches exactly 3 files,
   `0 insertions`, `1762 deletions` (588 + 587 + 587).

### 5.2 Regression test

New stdlib `unittest.TestCase` (canonical gate per
`docs/compound/097-S-canonical-unittest-gate.md` — `PYTHONPATH=src python -m
unittest discover -s tests`; root `pytest` is NOT canonical here) that:

- shells `git ls-files -z -- "*.json"` from the repository root,
- filters to depth-0 entries only (no `/` in the path),
- asserts the resulting set equals `{".mcp.json", "plugin.json"}`,
- names any unexpected path in the assertion message,
- `skipTest`s if `git` is unavailable or the tree is not a git checkout
  (subprocess-gating precedent), so the suite stays deterministic offline.

It must NOT recurse into `references/*` (vendored) — the depth-0 filter and the
`git ls-files` source guarantee this.

### 5.3 CI behaviour

`.github/workflows/ci.yml`'s `changes` job is a fail-closed denylist excluding
only `docs/**`, `.backlogit/**`, `.autoharness/**`. Root `*.json` and `tests/**`
are therefore classified **code**, so the `test` job runs for this change and the
new test executes in CI. No workflow edit is required.

## 6. Execution steps (for Ship)

1. Branch per P-011, then `git rm out.json res.json results.json` (three explicit
   pathspecs; no wildcard, no `-r`, no `.`).
2. Run §5.1 assertions 1–4.
3. Add `tests/test_repo_root_artifacts.py` implementing §5.2.
4. Run `PYTHONPATH=src python -m unittest discover -s tests` — full suite green.
5. Commit with explicit pathspecs only.

## 7. Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Deletion touches an unintended file | High | Three literal pathspecs; §5.1.3/§5.1.4 collateral assertions; no wildcards |
| Content is actually needed later | Low | Recoverable from `24777b44`; provenance is an external workspace; no dependents (§2.5) |
| Allowlist test breaks on a future legitimate root JSON | Low | Loud, self-describing failure; allowlist edit is a one-line reviewable change |
| Test wanders into `references/*` | Low | `git ls-files` + depth-0 filter |
| Operator-staged `.gitmodules`/`references/*` disturbed | **Critical** | Stage never stages/commits them; explicit-pathspec commits only; index verified before and after every transition |

## 8. Plan-hardening conclusion

**Requires plan hardening: no.**

No elevated-blast-radius signal is present: no schema change, no CLI
distribution change, no template-family change, no multi-surface refactor. The
change is a three-file deletion plus one additive test, with zero functional
dependents (§2.5). The destructive action is explicitly operator-authorized,
name-bounded, and fully recoverable from git history. Proportionate assurance is
provided by the multi-persona adversarial review instead.
