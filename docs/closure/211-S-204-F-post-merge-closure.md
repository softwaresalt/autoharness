---
shipment: 211-S
feature: 204-F
pr: 520
merge_commit: 8110a0cda760419f3d0a4873fe0297ea3fade9f9
reviewed_head: fc9be451
date: 2026-10-15
closure_status: READY
compaction_status: done
close_path: cascade
close_evidence: docs/closure/evidence/211-S-204-F-close-evidence.json
---

# 211-S / 204-F Post-Merge Closure: P7 Mandatory UTC for Recorded Dates and Times

## Summary

Shipment 211-S (covering feature 204-F, tasks 204.001-T through 204.004-T) merged through PR #520 as merge commit `8110a0cd` (`--merge`, merged 2026-10-15T06:52:28Z). Parents: `aac7a507` (main) and `fc9be451` (reviewed PR head). The change makes UTC with a `Z` suffix mandatory for recorded dates and times across the output-timestamps instruction, the foundation copilot-instructions and AGENTS surfaces, and the compact-context skill, with a P7 contract test that rejects offset-bearing ISO-8601 literals in templates and manifest-recorded mirrors and checks exact UTC anchors.

Review-fix cycle 4 (operator-approved, one extension, commit `ab42b6a2`) replaced the Python 3.12-only `Path.is_junction` check with a fail-closed Windows reparse-point check. Link fixtures refuse to skip on CI.

## Validator evidence (runtime-verification)

* Surface: `cli`. Probe `cli-help` (`uv run autoharness --help`, command adapter): exit 0, usage text printed. Verdict: PASS. Required probe, satisfied.
* Manual checkpoints: none declared.
* Blocked prerequisites: none.
* Build evidence: `uv build --offline` built `autoharness-1.5.0` sdist and wheel (exit 0). The online build could not reach PyPI from this sandbox.

## Operational closure checklist

* **Invariants to preserve**: every recorded date and time is UTC with a `Z` suffix. The P7 contract test (`tests/test_utc_timestamp_contract.py`) fails closed on offset-bearing literals, on symlinks and junctions under `templates/`, and on missing UTC anchors.
* **Pre-deploy audits**: none required. Installed mirrors and manifest checksums were refreshed in the PR. The CHANGELOG records the expected template drift for consumers.
* **Deployment path**: merge-only to `main`. Consumers receive the rule through `install-harness` or `tune-harness` on their next run.
* **Post-deploy checks**: on `main`, run `PYTHONPATH=src python -m unittest tests.test_utc_timestamp_contract -v`. Run `markdownlint "**/*.md"`.
* **Risky action record**: CASCADE close through `autoharness shipment cascade-close` (mutating). The classifier selected CASCADE under engine VERIFIED. Postcondition: pass. Linked-deliberation disposition: none.
* **Healthy signals**: the suite stays green on `main` with the same skip count (58). CI `test` job green.
* **Failure signals**: new offset-bearing literal in a template or mirror, a missing UTC anchor, or a junction or symlink under `templates/`.

## Releasability

`closure_status: READY`. No release or tag obligation is recorded on 211-S. `runtime_validation.releasability.required` is false. No closure conditions are open.

## Follow-ups (P-021 C2 captures, capture-only)

New captures: `083F1DAD` (Windows CI job for the P7 junction and reparse fixtures), `E1B4E9B2` (manifest-mirror path hardening), `1A97BC9B` (junction fixture `cmd` quoting), `D2537F45` (`_is_junction` naming and reparse semantics), `0CD465DA` (slim the P7 test), `B7928086` (test-harness error paths and pytest subTest skips), `785D4FC5` (local-time derivation denylist), `CECA0004` (output-timestamps pointer per installed preset).

Reused captures: `6A811556` (`.autoharness/` generated-state offsets), `68D55E6C` (offset-lint regex widening), `003312F1` (UTC rule single source), `F8BDCEAD` (install-harness DATE row), `48654A2B` (foundation template frontmatter).

Triage belongs to Stage. Ship did not triage, reprioritize, or edit any entry.

## Operator actions

* **Release the shipment lock.** `.backlogit/queue/.211-S.md.lock` is still held. The owner's capability token was not retained after acquire because of a handling error in this session, so the normal release is refused. The operator must run `scripts/release_lock.ps1 .backlogit/queue/211-S.md -Force`. The lock file is git-ignored.
* Stage triage of the eight new captures and the five reused captures.

## Close evidence

Record: `docs/closure/evidence/211-S-204-F-close-evidence.json` (phase `post_close`, `merge_commit_sha` `8110a0cd`, `classifier_verdict` CASCADE, `engine_verdict` VERIFIED, `postcondition_verdict` pass, `failures` none, `operator_action` none).

## Compaction (P-020)

`compaction_status: done`. Bounded Tier-1 consolidation of this release unit's memory. Compacted summary: `docs/memory/compacted/2026-10-15-211-s-204-f-compacted.md`. Verbose original archived with a traceable path: `docs/archive/memory/2026-10-15-ship-211-s-204-f-p7-utc-closure.md`. The memory store is still over the compaction thresholds (196 files, 1405 KB). Broader compaction is an operator or Stage decision and is not part of this closure.
