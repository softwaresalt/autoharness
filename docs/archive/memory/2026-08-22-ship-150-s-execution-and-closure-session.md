# Ship Session Memory — 150-S / 142-F Execution and Closure (2026-08-22)

## Summary

Executed shipment 150-S end-to-end as the final selected shipment in the
operator's chain (148-S -> 149-S -> 151-S -> 150-S). Feature 142-F fixed
`autoharness.verify_workspace._derive_template_variables` to fully conform
to the install-harness template-variable resolution contract
(`.github/skills/install-harness/SKILL.md`), eliminating all 62 previously
unresolved `{{VARIABLE}}` placeholders (83 occurrences / 10 staged files at
baseline) with zero regressions.

## Session Recovery Context

This session resumed a prior interrupted `_Ship` invocation for 148-S
(diagnosed clean state, no lost work), then continued through 149-S, 151-S,
and finally 150-S in sequence per operator direction, each as a fresh
shipment claim (not a recovery of the prior one).

## Key Technical Decisions (150-S)

1. **Reused existing verification-check logic for derivation.** The
   pre-existing `_add_escalation_route_resolution_check` /
   `_add_role_route_resolution_check` functions already implemented the
   exact per-role escalation/role-route resolution logic needed for
   derivation. Extracted a shared `_effective_escalation_route_for_role`
   helper and `_resolve_role_route_field`/`ROLE_ROUTE_TIER_FALLBACK` reuse,
   so the derivation and the installed-output verification check can never
   diverge.

2. **Tier-own-default consistency bug (caught by local review).** Initially,
   `STAGE_FAMILY`/`SHIP_FAMILY`/collapsed `ESCALATION_FAMILY` resolved to
   `""` (not the SKILL.md-documented tier own-default) when the referenced
   `model_routing.tier3`/`tier2` was absent entirely -- inconsistent with
   `TIER_3_FAMILY`/`TIER_2_FAMILY` themselves, which always resolve to their
   own literal default. Fixed with a `_tier_fallback_dict` helper applying
   each tier's own default before use as a fallback source. **Lesson**: when
   building a fallback chain across multiple derivation functions, verify
   ALL of them apply the SAME terminal default, not just the innermost one.

3. **DEFAULT_BRANCH: empty-string default is unsafe (caught by Copilot
   review).** Initially derived `DEFAULT_BRANCH` to `""` on total resolution
   failure. Copilot correctly flagged that this would render broken
   commands (e.g. `git checkout ` with a trailing space) while the
   zero-unresolved sweep reported false success. Fixed by NOT populating
   the key at all on failure, so the placeholder remains genuinely
   unresolved and detectable via the existing scan pipeline. **Lesson**:
   "never invent a value" (amendment B4) sometimes means the correct
   behavior is to leave a REAL gap detectable, not paper over it with an
   empty string that looks like a valid (if boring) answer.

4. **CI environment gap for git-based resolution.** `_resolve_default_branch`
   worked locally (this repo has `origin/HEAD` set) but failed in GitHub
   Actions CI, because `actions/checkout` does not configure
   `refs/remotes/origin/HEAD` locally. Added a `git ls-remote --symref
   origin HEAD` fallback rung, which queries the remote directly and works
   in any environment with network access to the remote, regardless of
   local ref setup. **Lesson**: a resolution chain that only tests clean
   locally may still fail in CI due to shallow/partial checkout semantics;
   always verify against actual CI output, not just local runs.

5. **json.dumps is not shell quoting (caught by Copilot review, high
   severity).** The array-literal variables (`ENABLED_SIDECARS_PS1/SH`,
   `COPILOT_CLI_ARGS_PS1/SH`) initially used `json.dumps`-based
   double-quoting for "quoting" purposes. This is safe for YAML/JSON
   contexts but NOT for shell/PowerShell array literals spliced directly
   into a generated script: a value containing `$(...)` or a backtick
   command would still be evaluated by bash/PowerShell inside a
   double-quoted string. Fixed with dedicated
   `_posix_shell_quote`/`_powershell_shell_quote` functions using
   single-quote literals (which suppress ALL expansion in both shells).
   **Lesson**: quoting for one context (JSON/YAML string escaping) is not
   interchangeable with quoting for a different execution context (shell
   array literals); always use the target context's own escaping rules,
   especially when the rendered output becomes EXECUTABLE script content.

6. **Rust-as-generic-fallback bug (caught by Copilot review).** The
   `_language_defaults()` generic fallback (no dedicated language branch)
   hard-coded Rust's `Result<T, Error>` / `/// doc comment` syntax as
   ERROR_PATTERN/DOC_COMMENT_STYLE, so any OTHER unbranched language (Java,
   C#, Ruby) would render Rust idioms into its own constitution. Fixed by
   adding a dedicated `rust` branch and making the truly-generic fallback
   language-neutral descriptive prose. **Lesson**: when one concrete
   example is the ONLY example given in source documentation for an
   otherwise-generic case, do not literally copy that example as the
   generic default -- either give it its own dedicated branch, or write
   genuinely neutral prose for the fallback.

## Fifth Occurrence of the Cascade-Close Deliberation Sweep

`backlogit shipment ship 150-S` archived `023-DL` (142-F's own originating
deliberation, referenced only via `references:`, never `parent_id`) --
the FIFTH occurrence of the documented recurring defect
(`docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`),
and a THIRD distinct deliberation ID across the five occurrences,
reinforcing that this is a per-feature/per-cascade-close engine behavior,
not tied to any single deliberation. Reverted via the now-established
procedure (git restore + delete the newly-created archive/log entries);
verified `023-DL` returns to `status: queued`.

## Process Notes

- **Stray file pollution during local verification**: while re-running
  `autoharness verify-workspace --json` and the full test suite multiple
  times during exploration, redirected output (`>`) directly into repo-root
  files (`verify_baseline.json`, `verify_progress.json`,
  `full_test_run.log`), which caused 5 unrelated tests (repo-root JSON
  allowlist, gitignore checks) to spuriously fail. Cleaned up and re-ran
  from a location outside version control (`New-TemporaryFile`) for all
  subsequent verification. **Lesson**: never redirect ad hoc command output
  into the repository working tree during investigation; always use a
  system temp path.
- **Accidental commit-message corruption via PowerShell `$(...)`
  interpolation**: a `git commit -m "... $(...) ..."` invocation caused
  PowerShell to attempt to EXECUTE the `$(...)` as a subexpression (the
  exact injection class this shipment's own fix addresses!), producing a
  parse error. Recovered by using file-backed commit messages via
  single-quoted here-strings (`@'...'@`) written to a temp file with `git
  commit -F`, which is now the established safe pattern for any commit
  message containing `$`, backticks, or other PowerShell-special
  characters.
- **Accidental commit history mangling via `--allow-empty-message` +
  `--amend` combo**: an initial attempt to fix a bad commit message used
  `git commit -F file -m "" --allow-empty-message` followed by `git commit
  --amend -F file`, which (because the first command silently produced no
  new commit) ended up amending the WRONG pre-existing commit, merging two
  unrelated changesets together. Recovered cleanly via `git reset --soft
  HEAD~1` followed by selective re-staging and two separate correct
  commits. **Lesson**: always verify a commit was actually created (check
  `git log`) before running a follow-up `--amend`.

## Final State

- Shipment 150-S: shipped/closed (cascade close, P-015).
- Feature 142-F and all 7 tasks: done/archived.
- Feature PR #395 merged (`927272da2cca01d43ccc109eb31fdf59c88db5dd`, 2
  parents verified).
- Closure PR: to be created from `post-merge/150-s-...` branch.
- This is the FINAL shipment in the operator's selected chain; no successor
  claimed.
