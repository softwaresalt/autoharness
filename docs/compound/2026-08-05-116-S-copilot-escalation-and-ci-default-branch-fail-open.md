---
title: "116-S / 109-F: nine-round Copilot escalation chain, CI-default-branch anti-pattern, and Windows-authoring gotchas"
date: 2026-08-05
problem_type: agent-workflow
category: ci-fail-open-default-and-test-authoring
root_cause: unvalidated-fallback-default-and-incomplete-ci-env-scrub
tags: [ship, copilot-review, ci, topology-gate, fail-closed, windows, testing, p-018, install-harness]
shipment: 116-S
pr: 302
merged_at: "2026-08-05T23:04:57Z"
---

# 116-S / 109-F: nine-round Copilot escalation chain, CI-default-branch anti-pattern, and Windows-authoring gotchas

## Problem 1 — a fix-the-symptom loop can hide a fail-open default for several rounds

Shipment `116-S` (gate C: the CI topology-check backstop) went through **9**
Copilot review rounds / **13** distinct threads before reaching
`SATISFIED`. The interesting pattern was not thread volume — it was that
**each fix narrowed scope without ever asking "what happens when this whole
resolution strategy fails?"** until round 6/7:

1. Round 3 added a CI-mode default-branch fallback reading
   `GITHUB_EVENT_PATH`'s webhook payload.
2. Round 5 discovered the *workflow trigger filter itself* was still
   hard-coded to `main`, making round 3's fallback moot for
   `master`/`trunk`-default repos. Fixed by adding a `{{CI_DEFAULT_BRANCH}}`
   install-time template variable, resolved via `git symbolic-ref` or
   `gh repo view`.
3. Round 6/7 finally asked the missing question: **what does the installing
   agent do when *both* resolution methods fail?** The original guidance
   said "fall back to `main`." That is fail-*open*, not fail-closed: it
   silently installs a CI workflow that will never trigger on the repo's
   actual default branch — a complete, silent disablement of the very
   backstop being built, worse than the bug that motivated round 5's fix in
   the first place.

## Root cause

A "make it resolve automatically" fix pattern tends to reach for a
plausible-sounding default (`main` is the single most common default
branch name) instead of treating **resolution failure as a first-class,
fail-closed outcome**. This is easy to miss because the default *looks*
like it's handling the failure case — it just handles it wrong.

## Preventive rule

For any install-time or runtime resolution of an environment-dependent
value that gates a security/enforcement mechanism (branch names, required
tool paths, credential scopes, etc.): explicitly design and test the
**both-methods-failed** branch before considering the feature complete.
The correct behavior is almost never "guess a plausible default" — it is
either (a) halt and ask the operator for the actual value, or (b) omit the
gating entirely and report degraded/non-applicable, never silently
degrade coverage while claiming success. `install-harness/SKILL.md`'s
`{{CI_DEFAULT_BRANCH}}` row now says explicitly: *"halt installation and
prompt the operator... never guess `main`."*

## Problem 2 — `mode='ci'` tests must scrub the full CI env-var surface, not just the var under test

A regression (caught only by the real GitHub-hosted runner, never
locally) came from a test that popped `GITHUB_EVENT_PATH` to simulate
"default-branch discovery unavailable" but did not also pop
`GITHUB_HEAD_REF`. On the actual runner, `GITHUB_HEAD_REF` genuinely *is*
set (the test job itself runs via a `pull_request`-triggered workflow), so
a completely unrelated piece of new logic (PR-suppression of the
default-branch shortcut, from a different round's fix) fired unexpectedly
inside the test's own `evaluate()` call, only on CI.

## Preventive rule

Any test in a file that exercises `mode='ci'` CI-environment-fallback
logic (here: `tests/test_gates_topology.py`) must explicitly pop **every**
CI-only env var the code under test reads — `GITHUB_HEAD_REF`,
`GITHUB_REF_NAME`, `GITHUB_REF_TYPE`, `GITHUB_EVENT_PATH` — not just the
one the test is nominally targeting, because the real runner has all of
them set simultaneously. Audit every `mode='ci'` call site in the file
after any related fix, not just the one that changed.

## Problem 3 — PyYAML's "Norway problem" defeats naive `on:` key lookups

A new test parsing a rendered `ci.yml.tmpl` with `yaml.safe_load()` and
indexing `doc["on"]` silently failed, because YAML 1.1's implicit boolean
resolution parses the **bare** `on:` key as the Python boolean `True`, not
the string `"on"` (the "Norway problem" — same class of gotcha as `NO`
parsing as `False`). Any GitHub Actions workflow parsed this way must be
indexed with `doc[True]`.

## Problem 4 — PowerShell single-quoted strings do not process `\"` escapes

Attempting `git commit -m '...text with \"quoted\" text...'` in PowerShell
does not escape the embedded double-quotes the way it would in bash.
**Correction of an earlier imprecise description**: single quotes in
PowerShell do not process `\"` as an escape at all — the backslash and
quote remain two literal characters inside the string at the PowerShell
parser stage, so single-quoting by itself does not terminate the string
early. The observed failure (a fragment of the message, e.g.
`CODEOWNERS`, being treated as if it were a separate command token)
arises **downstream**, when PowerShell serializes the argument array into
a single command-line string for a *native* executable (`git.exe`) — a
known class of PowerShell-to-native-argument-marshalling quirk around
embedded quote characters, not a single-quoted-string parsing failure.

**Fix**: write the commit message to a temp file (e.g. under the gitignored
`.autoharness/staging/`) and use `git commit -F <file>`, deleting the file
after. Established as the default, reliable pattern for any commit message
containing embedded double-quotes or other shell-sensitive characters in
this Windows PowerShell environment, regardless of the exact upstream
tokenization mechanism.

## Cross-reference

* `docs/closure/116-S-109-F-post-merge-closure.md` — full shipment closure
  record, all 13 thread dispositions with fixing SHAs (9 Copilot review
  rounds, 13 distinct threads).
* `docs/pipeline-topology-gate-ci-rollout.md` — "Threat Model & CODEOWNERS
  Hardening" section (round 4b's overclaim correction).
* `.github/skills/install-harness/SKILL.md` — `{{CI_DEFAULT_BRANCH}}`
  variable-table row (round 6/7's halt-not-guess fix) and Phase 4 verify
  step extension.
