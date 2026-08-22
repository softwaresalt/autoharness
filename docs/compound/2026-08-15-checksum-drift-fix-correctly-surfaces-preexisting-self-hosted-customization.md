---
title: "A checksum-drift fix can correctly surface a self-hosting repo's own long-standing customization"
source: docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md
doc_type: learning
---

# A checksum-drift fix can correctly surface a self-hosting repo's own long-standing customization

**Context**: shipment 134-S / feature 125-F (startup-script contract
migration, PR #340). Round 2 of Copilot review found that `verify_workspace`'s
generic manifest-checksum-drift scan was computed but never consulted by the
new startup-script classifier: a `known-legacy`/`current` script whose
installed content diverged from its manifest-recorded checksum for reasons
the marker-based custom-tail extractor couldn't explain could still get
`manual_review: false`, silently discarding an unattributed edit on refresh.

**Fix**: track `checksum_status` across the existing checksum-scan branches
and downgrade the classification to `ambiguous` (manual review, never
auto-applied) when checksum drift is present and unattributed to a
recognized custom-section tail.

**Surprising but correct consequence**: re-running `verify-workspace` against
*this repository's own self-hosted install* after the fix went from 0
migration proposals to 2 — `start.sh` and `start.ps1` both newly classified
`ambiguous`. Investigation (via `Get-FileHash` and `git show HEAD:start.sh`
comparison) confirmed this is **pre-existing, unrelated staleness**: both
scripts' manifest-recorded checksums have been stale since before this
shipment, and both scripts' own manifest `note` fields already documented
them as intentional "pre-existing, custom self-install version with agent
injection" artifacts — i.e., genuinely customized dogfood files, not pristine
template copies.

**Decision made**: do NOT "fix" this by refreshing the stale checksums to
suppress the new `ambiguous` proposals. That would recreate the exact blind
spot the round-2 fix exists to close — silently treating unattributed
core-content drift as safe. The correct response was: (1) confirm the
2-proposal result is expected/safe (`manual_review: true`, never mutates
anything), not a regression; (2) correct a previously-inaccurate
documentation claim (`tune-harness/SKILL.md` had said the classifier "must
never flag this repository's own root start.ps1/start.sh") to instead state
the classifier does not special-case them and may correctly report
`ambiguous`, while never modifying them.

**Generalizable rule**: when a new fail-closed check starts flagging your own
already-customized, already-intentional artifacts, resist the urge to tune
the check (or refresh stale baseline metadata) merely to make the new
proposal count go back to zero. First prove via independent evidence
(file-hash diff, git history, existing documentation/manifest notes) whether
the flagged state is a real regression or a correctly-surfaced pre-existing
condition. If the latter, the fix belongs in documentation/expectations, not
in loosening the check — loosening it would silently reintroduce the very
gap that motivated the check in the first place.
