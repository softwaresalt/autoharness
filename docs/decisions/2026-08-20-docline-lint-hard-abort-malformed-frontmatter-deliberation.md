---
title: "Malformed plan frontmatter aborts workspace-wide docline lint: local fix vs external linter behaviour"
date: 2026-08-20
doc_type: decision
stash_id: 395EBE60
agent: "Stage (planning only - Ship executes)"
classification: "bug / docs-toolchain availability"
blast_radius: "low (single docs file plus a regression guard)"
---

# Deliberation - docline lint hard-abort on malformed frontmatter (`395EBE60`)

Date: 2026-08-20
Agent: Stage (planning only - Ship executes)
Stash source: `395EBE60` (medium, bug, P-021 C2 `DEFERRED SCOPE EXPANSION`)
Source refs: shipment `143-S`, feature `134-F`, task `134.006-T`, discovery HEAD `474a1438`, PR #372 (reconciled)
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Decision (one line)

**Split into two dispositions.** The **local malformed-frontmatter defect is
accepted into the autoharness backlog** and fixed here, together with a
regression guard that prevents recurrence. The **linter's hard-abort-vs-
report-and-continue behaviour is an external backlogit product decision** and is
**explicitly NOT harvested** into this repository's backlog; it is recorded as a
width-isolated external stash entry, matching the existing disposition of
`84D8E6AB` and `3C7AAC71`.

## Problem statement

`docs/archive/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md` line 12 reads:

```yaml
blast_radius: elevated (result-integrity + multi-family: eval code / tests / docs / fixtures)
```

The value is an unquoted YAML scalar containing `": "` (inside
`multi-family: eval code`). YAML therefore parses the line as a nested mapping
in a scalar position, and `mdfront.Decode` fails with
`mapping values are not allowed in this context`.

Because `backlogit docs lint` aborts on the **first** decode error, the entire
repo-wide lint emits **no report at all** and exits 1. One malformed file masks
docline conformance across all of `docs/`.

### Stage verification (read-only)

* Confirmed by direct file inspection at line 12 - the quoted root cause is exact.
* **The lint was deliberately NOT executed.** Stage's Role Boundary forbids
  running linters (Build category). Empirical re-run of `backlogit docs lint`
  before and after the fix is delegated to Ship as the plan's acceptance evidence.
* The prior workaround recorded in the stash entry (per-file `--path` targeting)
  is confirmed available: `backlogit docs lint --path <sub-path>` exists in the
  v1.10.0 CLI surface.

## The two questions, deliberately separated

The stash entry bundles two genuinely different questions. Conflating them would
either (a) block a trivial one-line repo fix behind an external product decision
we do not own, or (b) smuggle an external tool-behaviour change into an
autoharness shipment. Both are unacceptable, so they are separated here.

### Q1 - Is our own document malformed? (LOCAL, in scope)

Yes, unambiguously. Regardless of what the linter does on error, the file is
invalid YAML and must be corrected. This is our artifact, our defect, our fix.

**Decision: accept.** Quote the scalar, sweep `docs/` for the same hazard, and
add a regression guard so a malformed frontmatter block cannot be committed again.

The regression guard matters more than the one-line fix. The one-line fix
restores the lint *today*; the guard is what prevents the next unquoted colon
from silently disabling repo-wide doc validation again. A latent, single-file
denial-of-service on a whole-repo quality gate is the actual severity here, and
it is why this is medium and not low.

### Q2 - Should the linter hard-abort on one bad file? (EXTERNAL, out of scope)

This is a **backlogit product decision**, not an autoharness decision. backlogit
is a separately-owned tool consumed by this workspace. Arguments exist on both
sides:

* **For report-and-continue**: a per-file decode failure is a finding, not a
  reason to suppress every other file's findings. One bad file should degrade
  the report, not delete it.
* **For hard-abort**: a decode failure may mean the lint's own view of the
  corpus is untrustworthy, and failing closed is defensible for a gate.

Stage's position, recorded for the upstream conversation but **not actioned
here**: report-and-continue with a non-zero exit and an explicit per-file
`decode_error` finding is the better behaviour, because it preserves the
gate's fail-closed exit status while removing the whole-corpus masking effect.

**Decision: do not harvest.** Width isolation (P-021 C1) applies - this is a
different product, a different repository, and a different owner. It is captured
as a new `[EXTERNAL / backlogit-owned]` stash entry so the observation is not
lost, following the established precedent of `84D8E6AB` and `3C7AAC71`.

## Options considered for Q1

| # | Option | Verdict |
|---|---|---|
| A | Quote the one scalar only | Rejected - restores the lint but leaves the recurrence path wide open |
| B | Quote the scalar + sweep `docs/` for the same hazard | Necessary but insufficient - a sweep is a point-in-time action |
| C | **B + a regression guard asserting every `docs/**/*.md` frontmatter block parses** | **Chosen** |
| D | C + restructure the `blast_radius` field into a structured mapping | Rejected - gratuitous schema change; scope expansion with no defect behind it |

Option C is the smallest change that fixes the defect *and* closes the class.

## Chosen direction

1. Quote the offending `blast_radius` value in the 2026-08-02 plan. Content is
   preserved verbatim; only quoting changes.
2. Sweep every YAML frontmatter block under `docs/` for values containing `": "`
   that are not quoted, and quote them. Report the count found.
3. Add a regression test that parses the frontmatter of every `docs/**/*.md`
   file and fails with the offending path and line on any decode error.

## Non-goals

* **No change to backlogit.** Not our repository.
* **No docline schema change.** The contract is fine; one document violated it.
* **No reformatting of the 2026-08-02 plan beyond the malformed line.** That plan
  belongs to feature `085-F` and is otherwise untouched.
* **No bulk docline conformance campaign.** Once the lint runs again it may
  surface pre-existing findings across `docs/`. Those are explicitly **out of
  scope** here and must be captured as their own deferred entries under P-021 C1,
  not absorbed into this fix.

## Consequence to plan for

Fixing the abort will, for the first time in a while, let the repo-wide lint
actually produce a report. That report is likely to be non-empty. This is the
expected and correct outcome of restoring a masked gate, and the compound
learning `docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`
applies directly: **do not tune the check, or re-suppress it, to make the newly
surfaced findings go away.** Surface them, capture them, defer them.

## Traceability

* Stash `395EBE60` - reconciled in place (PR #372 recovered; review-thread ID
  confirmed legitimately absent). Duplicate scan: CLEAN.
* Plan: `docs/plans/2026-08-20-docline-lint-restoration-plan.md`
