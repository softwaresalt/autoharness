---
title: "Remediating a CI-skip coverage gap: prefer a pinned, checksum-verified real binary over a Python re-implementation of the contract"
description: "When a review finding flags that acceptance tests silently skip in CI because an external CLI tool isn't installed there, installing a pinned + checksum-verified release binary in the CI job is usually the correct fix -- a hand-written re-implementation of the same rules is exactly the drift risk the finding warns about."
problem_type: "process-judgment"
category: "workflow-issues"
component: "ship-agent-fix-ci"
root_cause: "Acceptance tests gated with @unittest.skipUnless(shutil.which(tool)) protect a real external contract locally but silently no-op in any CI environment lacking that tool, leaving the PR's core contract claim unverified by CI even though the test suite reports OK."
resolution_type: "fix"
severity: "medium"
tags:
  - "ship"
  - "fix-ci"
  - "review-remediation"
  - "backlogit"
  - "external-contract-testing"
citations:
  - "PR #354 Copilot review comment 3799007126"
  - "Shipment 137-S / 128.002-T"
source: docs/compound/2026-08-17-ci-skip-coverage-gap-prefer-pinned-binary-over-reimplementation.md
doc_type: learning
---

# CI-Skip Coverage Gap: Install the Real Tool, Don't Re-Implement Its Rules

## Context

Task 128.002-T added `BacklogitLintAcceptanceTests`, gated with
`@unittest.skipUnless(shutil.which("backlogit"), ...)`, that renders a real
fixture into `docs/decisions/` and shells out to the actual `backlogit docs
lint` binary to prove the template's generated frontmatter passes the real
external linter. Locally this ran and passed. In CI it silently skipped,
because the `test` job only installs `jsonschema`/`PyYAML`, not `backlogit`.

Copilot's review correctly flagged this: the PR's core claim (generated
artifacts pass the real lint contract) was, in CI, protected only by
structural assertions that duplicate the *expected shape* of that contract —
exactly the thing that could drift out of sync with the real tool's
behavior over time, with CI staying green throughout.

## Two remediation options, and why one is usually wrong

1. **Add a pinned, checksum-verified download of the tool's release binary
   to the CI job.** For `backlogit` (a Go binary with GitHub Releases and a
   published `SHA256SUMS`), this is a small, self-contained, no-sudo-required
   step:

   ```yaml
   - name: Install backlogit (pinned vX.Y.Z, checksum-verified)
     run: |
       set -euo pipefail
       curl -fsSL -o backlogit-linux-amd64 https://github.com/{org}/{tool}/releases/download/vX.Y.Z/backlogit-linux-amd64
       echo "{sha256}  backlogit-linux-amd64" | sha256sum -c -
       chmod +x backlogit-linux-amd64
       mkdir -p "$RUNNER_TEMP/bin"
       mv backlogit-linux-amd64 "$RUNNER_TEMP/bin/backlogit"
       echo "$RUNNER_TEMP/bin" >> "$GITHUB_PATH"
   ```

   This exercises the **real** tool in CI. There is no drift risk, because
   nothing about the tool's behavior is being guessed or duplicated.

2. **Write a non-skipped pure-language re-implementation of the specific
   lint rules being verified** (e.g. "assert `source` and `doc_type` keys
   are non-empty; assert `doc_type` is in a hardcoded set including
   `decision`"). This *looks* like it closes the coverage gap, but it is
   **exactly the failure mode the review finding warns about**: a
   hand-maintained guess at the external contract that can silently drift
   out of sync with the real tool's actual behavior while continuing to
   pass. It converts an honest, environment-conditional skip into a false
   sense of coverage.

**Option 1 is the correct default whenever the tool ships a pinned,
checksum-verifiable release artifact usable in the CI runner's OS/arch.**
Option 2 should be treated as a fallback only when no such artifact exists
(e.g. the tool requires a license, network service, or build toolchain that
cannot reasonably be added to shared CI), and even then should be labeled
explicitly in comments as a secondary, non-live-linter-dependent guard that
does not replace the live-binary acceptance test.

## Scope-boundary note

The originating plan's stated file-scope constraint ("touch only the
template file and the new test module") predates the discovery of this gap
during PR review. Fixing a real, review-identified P1 finding legitimately
extends into a third file (`.github/workflows/ci.yml`) under Ship's
review-fix remediation authority — this is not a planning-scope violation,
it is in-cycle review remediation, and should be called out explicitly in
the PR body / reply to the reviewer rather than silently expanding scope.

## Applicability

Any time a review flags that an acceptance/contract test is silently skipped
in CI due to a missing external tool: check whether the tool publishes a
pinned, checksummed release binary before reaching for a re-implementation.
