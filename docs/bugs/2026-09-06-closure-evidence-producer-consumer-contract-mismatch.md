---
title: "Closure evidence producer/consumer contract mismatch blocks successor shipment claims"
description: "Ship's operational-closure artifact spec and the pipeline-topology closure_complete reader specify incompatible filenames and metadata, so valid closure evidence is invisible to the gate"
status: "open"
severity: "high"
kind: "bug"
date: 2026-09-06
discovered_in: "008-S / 009-S predecessor-closure gate"
producer: ".github/skills/operational-closure/SKILL.md"
consumer: "autoharness.gates.topology.FilesystemTopologyReaders.closure_complete"
gate_token: "PREDECESSOR_CLOSURE_INCOMPLETE"
recurrence: ["001-S", "005-S", "008-S"]
immediate_remediation_pr: 26
immediate_remediation_merge_commit: 44b1cda5531d34bbe32b9d2b5c277e0a137fece3
tags:
  - "bug"
  - "tool-integration"
  - "closure"
  - "pipeline-topology"
  - "contract-drift"
---

## Summary

Post-merge closure evidence is written by one component and read by another, and the two
components specify the artifact differently. The Ship-side `operational-closure` skill documents
its output as `docs/closure/{YYYY-MM-DD}-{slug}-closure.md` and describes releasability and
compaction as narrative content. The `pipeline-topology` gate discovers closure evidence only
through the glob `docs/closure/{shipment_id}-*-post-merge-closure.md` and accepts it only when the
file carries machine-readable YAML frontmatter.

A file named exactly to the documented producer spec can never match the consumer glob. The
consequence is not a warning but a hard block: the successor shipment's pre-claim check fails with
`PREDECESSOR_CLOSURE_INCOMPLETE` even when closure was genuinely performed and documented well.
This has now been repaired reactively three times (001-S, 005-S, 008-S), which makes it systemic
integration drift rather than an authoring mistake.

## Affected components

| Role | Component | Contract it declares |
|---|---|---|
| Producer | `.github/skills/operational-closure/SKILL.md` (line 23) | `docs/closure/{YYYY-MM-DD}-{slug}-closure.md`; releasability and compaction status as content |
| Producer (caller) | `.github/agents/_ship.agent.md` (line 840) | Invokes `operational-closure`; names only `compaction_status` as gate-relevant |
| Consumer | `autoharness.gates.topology.FilesystemTopologyReaders.closure_complete` (lines 654-666) | `docs/closure/{shipment_id}-*-post-merge-closure.md`; frontmatter mapping required |
| Consumer (predicate) | `autoharness.gates.topology._closure_artifact_complete` (lines 294-329) | `compaction_status` in `{done, degraded}` **and** `closure_status: READY`, or `READY_WITH_CONDITIONS` with a fully satisfied `conditions:` block |
| Consumer (gate) | `autoharness.gates.topology._shipment_readiness_check` (lines 1611-1618) | Emits `PREDECESSOR_CLOSURE_INCOMPLETE` when the reader returns anything other than `True` |

The installed consumer module resolves to
`C:\Python\Python314\Lib\site-packages\autoharness\gates\topology.py`.

## Observed versus expected behavior

Expected: closure evidence produced by Ship according to its own documented skill contract is
discovered and accepted by the `pipeline-topology` closure gate, allowing the successor shipment to
proceed to its remaining checks.

Observed: `closure_complete("008-S")` returned `None`. The 009-S pre-claim evaluation treated that
as missing evidence and blocked with `PREDECESSOR_CLOSURE_INCOMPLETE`, despite
`docs/closure/2026-09-06-008-s-009-f-apperr-taxonomy-correction-closure.md` existing and containing
correct, complete, human-readable closure evidence.

## Reproduction

Verification against the repaired artifact currently in the repository:

```powershell
python -c "from autoharness.gates.topology import FilesystemTopologyReaders as R; from pathlib import Path; print(R(Path('.')).closure_complete('008-S'))"
```

Current result: `True`.

Isolating the defect requires changing only the filename. Copy the current, valid artifact into a
scratch workspace under the producer-spec name and re-read it:

```powershell
$t = Join-Path $env:TEMP "closure-repro-008s"
New-Item -ItemType Directory -Path "$t/docs/closure" -Force | Out-Null
Copy-Item docs/closure/008-S-009-F-post-merge-closure.md `
  "$t/docs/closure/2026-09-06-008-s-009-f-apperr-taxonomy-correction-closure.md"
python -c "import sys; from autoharness.gates.topology import FilesystemTopologyReaders as R; from pathlib import Path; print(R(Path(sys.argv[1])).closure_complete('008-S'))" $t
```

Result: `None`.

The file content is byte-identical to the artifact that returns `True`, including valid frontmatter
with `closure_status: READY`. Only the name differs. Filename divergence alone is therefore
sufficient to reproduce the block.

Blocking gate token: `PREDECESSOR_CLOSURE_INCOMPLETE`.

## Root cause

The producer contract and the consumer contract for post-merge closure evidence were specified
independently and drifted apart. There is no shared schema, no shared constant, and no shared
writer between them.

The divergence is total on both axes:

* **Naming.** The producer spec begins the filename with a date and ends it with `-closure.md`. The
  consumer glob requires the filename to begin with the shipment ID and end with
  `-post-merge-closure.md`. No string satisfies both patterns, so a conforming producer output is
  guaranteed to be undiscoverable.
* **Metadata.** The producer spec treats releasability and compaction status as fields of the
  document, without requiring YAML frontmatter. The consumer requires a parseable frontmatter
  mapping carrying `compaction_status` and `closure_status` as machine-readable keys.

`_ship.agent.md` compounds the metadata half by propagating only `compaction_status` as
gate-relevant and omitting `closure_status`. An artifact written against that partial guidance
satisfies half the consumer predicate and still fails.

This is a contract-drift defect between two independently specified components. It is not an
authoring error in any individual closure artifact, and renaming individual files does not address
it.

## Why correct human-readable evidence was invisible

Discovery is filename-driven and precedes content inspection. `closure_complete` globs first, and
only files matching the glob are ever opened and parsed. The 008-S artifact never matched, so it
was never read. Its correctness was therefore unable to influence the outcome at all — the gate did
not reject the evidence, it never saw it.

The diagnostic asymmetry makes this worse. The two failure modes are reported very differently:

* A **matching filename with missing or malformed frontmatter** raises `BacklogUnavailableError`
  ("artifact frontmatter is missing or malformed"), which surfaces as a loud, fail-closed
  `BACKLOG_UNAVAILABLE` naming the offending path.
* A **non-matching filename** returns a silent `None`, which is indistinguishable from "no closure
  was ever performed" and collapses into the generic `PREDECESSOR_CLOSURE_INCOMPLETE` token.

The more likely failure — a producer faithfully following its own documented naming spec — is the
one that produces the least actionable signal. The operator is told closure evidence is missing
while a complete closure record sits in the expected directory.

## Recurrence evidence

The same defect class has been repaired three times, each time on the artifact rather than the
contract:

| Shipment | Repair commit | Nature of repair |
|---|---|---|
| 001-S | `6ed75e8` | Rename `R091` from `docs/closure/2026-09-03-intercom-go-foundation-closure.md` to `docs/closure/001-S-001-F-post-merge-closure.md` |
| 005-S | `1baffd4` (after `f97d46c`) | Frontmatter aligned with the machine-readable schema |
| 008-S | `385afd8` | Rename `R094` from `docs/closure/2026-09-06-008-s-009-f-apperr-taxonomy-correction-closure.md` to `docs/closure/008-S-009-F-post-merge-closure.md`, plus frontmatter added |

001-S and 008-S failed identically on the naming axis; 005-S failed on the metadata axis. Both axes
of the divergence have independently caused a block. Because each fix targeted a single file, the
producer contract was never corrected, and the next closure reproduced the defect.

## Immediate remediation already applied

PR #26, merged as `44b1cda5531d34bbe32b9d2b5c277e0a137fece3`, renamed the 008-S artifact to
`docs/closure/008-S-009-F-post-merge-closure.md` and added valid frontmatter including
`compaction_status: done` and `closure_status: READY`. Direct reader verification now returns
`True`, and the 009-S topology gate advances past this check to the separate, expected
`BRANCH_MISMATCH` condition.

This unblocked 009-S. It did not fix the defect: it is the third instance of the same manual
workaround, and the producer contract still directs the next closure to the wrong filename.

## Systemic follow-up scope

The durable fix is contract unification and enforcement between producer and consumer, not another
rename. In scope:

* A single authoritative definition of the closure-evidence contract — filename pattern and
  required frontmatter keys with their permitted values — expressed once and referenced by both
  sides rather than restated in prose in each.
* A canonical writer or shared helper that Ship uses to emit closure evidence, so the path and
  frontmatter are generated from the shared definition instead of hand-authored.
* Write-time validation, so a non-conforming artifact fails at closure time, when the author has
  full context, rather than at a successor shipment's pre-claim gate.
* Reconciliation of `.github/skills/operational-closure/SKILL.md` and `.github/agents/_ship.agent.md`
  with the unified contract, including the currently omitted `closure_status` requirement.
* Diagnostic improvement in the consumer so an unmatched-but-present closure directory is
  distinguishable from genuinely absent evidence.

## Acceptance criteria

A fix is complete when all of the following hold:

1. **Shared contract.** The closure-evidence filename pattern and required frontmatter schema are
   defined in exactly one place, and both the Ship producer path and the `pipeline-topology`
   consumer derive their behavior from that definition. Changing the pattern in one place changes
   both sides.
2. **Canonical writer.** Ship emits closure evidence through a shared helper or canonical writer
   that constructs the path and frontmatter from the shared definition. Hand-authoring a closure
   filename is no longer part of the documented flow.
3. **Write-time validation.** Emitting closure evidence that violates the schema fails at write
   time with a message naming the offending field or path. A closure artifact cannot be committed
   in a state that the consumer would silently ignore.
4. **Deterministic discovery.** Given a shipment ID and a conforming closure artifact, discovery
   resolves to exactly one artifact, with defined behavior for the zero-match and multi-match
   cases.
5. **Actionable diagnostics.** The consumer distinguishes and reports separately: no closure
   artifact present for the shipment; a candidate artifact present but not matching the expected
   name; and a matching artifact with missing, malformed, or schema-invalid metadata. The
   name-mismatch case must name the candidate path it found and the pattern it expected, rather
   than reporting generic incompleteness.
6. **Integration test.** An automated test drives the real Ship closure-production path, then feeds
   its output to the real `pipeline-topology` closure reader and asserts acceptance. The test must
   fail if either the producer naming or the consumer glob changes without the other. A test that
   hand-writes a conforming fixture does not satisfy this criterion, because it would have passed
   throughout the entire history of this defect.
7. **Regression coverage.** The three historical failure shapes — date-prefixed producer-spec
   filename, missing frontmatter, and frontmatter carrying `compaction_status` without
   `closure_status` — are each covered by a test asserting the specific diagnostic.

## Non-goals

* Renaming or editing further individual closure artifacts as the primary remedy.
* Modifying the merged 008-S closure artifact, which is correct and is cited here read-only.
* Relaxing the consumer predicate. Requiring both `compaction_status` and `closure_status` is
  deliberate fail-closed behavior and must be preserved.
* Weakening the fail-closed handling of malformed frontmatter into a silent skip.
* Changing 009-S scope, its manifest, or its branch state.
* Retroactively rewriting the 001-S and 005-S artifacts, which already conform.

## References

* Consumer implementation: `autoharness/gates/topology.py` — `closure_complete` (654-666),
  `_closure_artifact_complete` (294-329), `_frontmatter` (243-269), `_shipment_readiness_check`
  gate token (1611-1618)
* Producer specification: `.github/skills/operational-closure/SKILL.md` (line 23)
* Producer caller: `.github/agents/_ship.agent.md` (line 840)
* Current conforming artifact: `docs/closure/008-S-009-F-post-merge-closure.md`
* Remediation PR: [#26](https://github.com/softwaresalt/intercom/pull/26), merge commit
  `44b1cda5531d34bbe32b9d2b5c277e0a137fece3`, repair commit `385afd8`
* Prior recurrences: commits `6ed75e8` (001-S), `1baffd4` (005-S)
