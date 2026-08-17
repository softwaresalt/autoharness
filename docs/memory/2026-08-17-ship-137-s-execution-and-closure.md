# Ship session — 137-S execution: docline frontmatter conformance for spike template

**Date**: 2026-08-17
**Mode**: standard (non-dark) Ship execution, operator's explicit "Ship 137-S
now" trigger. Prior dark-mode activation was already closed after a blocker
before this session began. Intercom unavailable (degraded operator
visibility, no bypass of approval-dependent gates). Bounded stop: 137-S only
— no other stash/backlog item touched.

## Starting state

Orchestrator handoff: shipment `137-S` (queued, medium priority; items
`128-F`, `128.001-T`, `128.002-T`) with no blocking predecessor. Single
worktree, `main` clean, HEAD == `origin/main` == `0ec98ce4`. A `.backlogit`
stash.jsonl "M" status was verified (hash-object, `git diff --quiet`,
byte-for-byte compare) to be a stat/CRLF false positive, not real content
drift. `pipeline-topology` gate treated as not-installed per the operator's
stated bootstrap exemption (global `autoharness` CLI on PATH lacks `gate`
subcommands), though a repo-local dev venv (`.venv\Scripts\autoharness.exe`)
does expose it and was used for later gate checks (`gate copilot-review`)
once discovered.

## Scope

`128-F`: correct `templates/skills/spike/SKILL.md.tmpl`'s Phase 5
findings-artifact frontmatter to nest spike-specific fields under a
`docline` mapping (docline-required fields — `title`, `source`,
`doc_type: decision`, `description` — stay top-level), and repoint Step
4.2's promotion instructions accordingly (`128.001-T`); add a new test
module proving both the structural shape and, when `backlogit` is on PATH,
real-linter acceptance evidence (`128.002-T`).

## Execution summary

- TDD: wrote `tests/test_spike_template_docline_frontmatter.py` first,
  observed a genuine RED state (11 failed / 4 passed) against the unmodified
  template, then implemented the fix and reached GREEN (15/15).
- Caught a real, previously unflagged YAML bug during TDD: an unquoted
  `source: {{DOCS_DECISIONS}}/{YYYY-MM-DD}-{slug}-spike.md` is invalid YAML
  (two adjacent unbalanced `{...}` flow-mapping groups). Fixed by quoting
  the value — resolved in-flight, before commit.
- Full local build: `PYTHONPATH=src python -m unittest discover -s tests` —
  1536 tests, OK, both locally and (after the CI remediation below) in CI.
- In-context multi-persona adversarial review (Security, Reliability,
  Simplicity, Composability, Maintainer, Adversary) — PASS, 0 P0/P1.
- Committed with required trailers
  (`Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`,
  `Copilot-Session: 54d2f2f8-eef2-46b7-95e4-ecd6e2287c3b`) across three
  scoped commits (template fix, test module, backlog completion).
- **Branch-rename mishap**: renamed the branch server-side to fix a
  `pipeline-topology` `BRANCH_MISMATCH` finding on the already-open PR #353;
  this unexpectedly auto-closed #353 instead of retargeting it. Recovered by
  opening PR #354 from the renamed branch. See
  `docs/compound/2026-08-17-branch-rename-after-pr-open-auto-closes-pr.md`.
- **Copilot review round 1** (HEAD `99a1408d`): 1 actionable P1 finding — the
  new acceptance-test class silently skips in CI (no `backlogit` binary
  there), so the PR's core external-contract claim was CI-unverified. Fixed
  by adding a pinned, SHA256-checksum-verified `backlogit v1.9.0` binary
  install step to `.github/workflows/ci.yml`'s `test` job (see
  `docs/compound/2026-08-17-ci-skip-coverage-gap-prefer-pinned-binary-over-reimplementation.md`).
  Replied to the comment (after first accidentally mangling the reply body
  via a double-quoted PowerShell here-string — corrected via a follow-up
  PATCH; see
  `docs/compound/2026-08-17-powershell-doublequote-herestring-mangles-backticks-in-comment-bodies.md`)
  and resolved the thread via GraphQL `resolveReviewThread`.
- **Copilot review round 2** (HEAD `b145578c`, explicitly re-requested via
  `POST .../requested_reviewers` with reviewer login `Copilot`): reviewed
  11/11 changed files, generated no new comments. `autoharness gate
  copilot-review 354 --enforcement auto` → `SATISFIED`.
- P-014 §1.9 readiness: Local Review Readiness block updated to the final
  HEAD with full CI + local build evidence; P-018 gate SATISFIED; CI green
  (`ci gate`, `detect code changes`, `pipeline-topology (ambient)`, `test`
  all pass); `mergeStateStatus: CLEAN`.
- Operator pre-authorization ("previously granted permission to open PRs and
  approve normal merges for this scoped pipeline... treat that as the P-014
  approval signal for the 137-S PR only after all readiness gates pass") was
  treated as satisfying the operator-approval gate once all readiness gates
  passed — not before.
- Merged PR #354 with `--merge` (merge-commit strategy; repo disallows
  squash/rebase). Merge commit `aa460cce` verified to have 2 parents and be
  an ancestor of `origin/main`.
- Post-merge: created `post-merge/spike-skill-template-docline-frontmatter-conformance`
  branch from `main`. Ran the shipment-reconcile classifier
  (`classify_shipment_close_path`) against the manifest
  (`128-F`, `128.001-T`, `128.002-T`) — verdict: `CASCADE` (128-F is a
  verified fully-covered root; both children are manifest members, terminal,
  parent_id preserved). Ran the cascade close path
  (`backlogit shipment ship 137-S --sha aa460cce... `) per the P-015 verified
  exception rather than safe-close. Verified `returned_ids: []`,
  `archived_ids` exactly `[128.001-T, 128.002-T, 128-F, 137-S]`, and
  `parent_id` preserved on both tasks against the pre-close snapshot. Gate
  decision: CLOSED.
- Wrote three compound-learning docs (branch-rename pitfall, PowerShell
  backtick/here-string pitfall, CI-skip-coverage-gap remediation pattern).

## Notable process points for future sessions

1. Never rename a branch via the GitHub API after its PR is already open —
   push a new branch + open a new PR instead.
2. In PowerShell, build any file-backed GitHub comment/PR body containing
   Markdown backticks with a **single-quoted** here-string (`@'...'@`), never
   a double-quoted one.
3. When a review finding says an acceptance test silently skips in CI for
   lack of an external tool, check for a pinned/checksummed release binary
   before writing a Python re-implementation of the same rules — the
   re-implementation is the exact drift risk the finding is warning about.
4. Re-requesting a Copilot re-review after a fix push is done via
   `gh api -X POST .../requested_reviewers -f "reviewers[]=Copilot"` (exact
   login `Copilot`, not `copilot-pull-request-reviewer[bot]`, for the REST
   requested-reviewers endpoint).
5. `uv run` fails in this environment (no PyPI network access) — use the
   repo-local `.venv` directly for autoharness CLI and Python invocations.
6. The correct full-build/test command for this repo is
   `PYTHONPATH=src python -m unittest discover -s tests`, not bare `pytest`
   (which incorrectly walks vendored `references/` git submodules).

## Final state

- Shipment `137-S`: `shipped`/archived (`archived_status: shipped`).
- Feature `128-F`, tasks `128.001-T`/`128.002-T`: archived, `archived_status: done`.
- PR #353: closed (superseded). PR #354: merged (`aa460cce`, 2 parents,
  confirmed ancestor of `origin/main`).
- No other active shipment/feature/task (P-001 clear).
- Local `main` fast-forwarded to `origin/main` at `aa460cce`.
- Post-merge closure work committed to
  `post-merge/spike-skill-template-docline-frontmatter-conformance`
  (not yet merged as of this memory write — see closure PR follow-up).
