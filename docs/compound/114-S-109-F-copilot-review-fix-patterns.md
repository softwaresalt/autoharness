---
title: Fail-closed backlog parsing — eleven-round Copilot review-fix pattern (114-S / 109-F)
tags: [topology-gate, fail-closed, backlog-parsing, path-traversal, review-fix, glob-injection]
related_pr: 297
related_shipment: 114-S
related_feature: 109-F
source: docs/compound/114-S-109-F-copilot-review-fix-patterns.md
doc_type: learning
---

# Compound Learning: The "silent fail-open" defect class in `topology.py`'s backlog parsing

Captured from PR #297's hosted Copilot review — **12 rounds, 27 threads
total, all resolved** — the longest single-PR Copilot review remediation
loop recorded in this repository to date. The operator explicitly removed
the standard 3-cycle review-fix cap for this session ("continue until
clean"), which is what allowed the pattern below to be fully exhausted
rather than capped mid-stream. Recorded here so future work touching
`FilesystemTopologyReaders` (or any similar backlog-frontmatter reader)
reuses this checklist instead of re-discovering each instance one Copilot
round at a time.

## The pattern: every field-read in `topology.py` was audited for silent leniency

Across 11 fix rounds (rounds 1-3 were pre-existing defects unrelated to this
pattern; rounds 4-11 are the pattern), Copilot systematically hunted for
every place the backlog-reading code could **silently swallow a
malformed/missing/unknown value** instead of raising
`BacklogUnavailableError`. The progression, in order found:

1. **Round 4** — `_frontmatter` returned `{}` on missing/malformed
   frontmatter and let YAML errors escape unhandled.
2. **Round 5** — scoped phases (`pre_claim`/`post_claim`/`lifecycle`) only
   required `--shipment` in `agent` mode, letting `ci`/`manual` skip
   ownership/readiness checks with zero active shipments.
3. **Round 6** (3 threads) — missing/blank shipment `id` silently skipped;
   unknown/missing queue `status` collapsed to `None`; archive-presence
   ambiguity keyed off `archived_status` content instead of file presence.
4. **Round 7** (2 threads) — `result.message` (free-text) leaked into
   telemetry `argv_fingerprint`; unknown/missing task `status` silently
   normalized away.
5. **Round 8** — a shipment-shaped id/filename with a missing/misspelled
   `artifact_type` was skipped before its shape was even checked.
6. **Round 9** (2 threads) — an untrusted artifact id was interpolated
   directly into a filesystem glob pattern (path traversal / glob-metachar
   risk); duplicate shipment records in the same folder were silently
   merged via `dict.setdefault(...)`, with the LAST file (by sort order)
   silently winning.
7. **Round 10** — `_tuple_of_str` validated the container shape
   (list/tuple) but not presence — a bare-string `dependencies` or
   `custom_fields.items` value silently collapsed to an empty tuple.
8. **Round 11** (3 threads) — `_tuple_of_str` validated the container shape
   but not each MEMBER (a malformed member like `../../outside` was
   blindly stringified and could later reach `closure_complete()`'s glob);
   `list_shipments` only checked a record's id shape when `artifact_type`
   was wrong, not when it was correctly `shipment`-typed; the live+archive
   ambiguity check applied only to predecessors, never to the TARGET
   shipment itself.
9. **Round 12** — **zero new review threads** (which is what made the
   thread-based P-018 gate return `SATISFIED`) — but **not** a clean
   technical review: the *silent-fail-open* pattern this section tracks
   was fully exhausted, yet the review body at this HEAD still carried two
   unrelated **suppressed comments** (findings Copilot generates but does
   not promote to a new inline thread because they duplicate a position
   raised in an earlier round and never actually fixed): (a)
   `topology.py:680`'s bounded post-claim retry never re-invokes an actual
   claim operation between its two re-reads, so a real delayed/failed claim
   cannot converge in production (only the unit test's fake reader masks
   this); (b) `cli.py:735-739`'s telemetry outcome mapping records an
   invalid (`exit_code == 2`) gate evaluation as `success`. These are a
   *different* defect class from the one below (a design/plumbing gap and a
   telemetry-status mapping gap, not silent-fail-open parsing) and were
   **not** fixed as part of PR #297 — they are documented as required
   follow-ups in `docs/archive/closure/114-S-109-F-post-merge-closure.md`'s "Known
   Residual Findings" section. Lesson: "zero new threads" only proves the
   thread-based gate is satisfied; it does not prove the review's free-text
   body raised nothing outstanding — always read the full review body, not
   just its thread count, before declaring a round "clean."

## Lesson: any reader of untrusted YAML frontmatter needs three layers of validation, not one

For every field read from a `.backlogit/*.md` frontmatter block that flows
into a decision, a lookup key, or a filesystem path component, apply all
three:

1. **Presence** — is the field there at all? (Missing is sometimes
   legitimate — e.g. `dependencies: None` means "no predecessors" — but
   only when explicitly modeled as such, never as a fallback for "didn't
   parse".)
2. **Container shape** — if present, is it the expected type (mapping,
   sequence, scalar)? A field that's present-but-wrong-shaped (a bare
   string where a list was expected) must raise, not silently coerce.
3. **Member/value shape** — for each element (or the scalar itself), does
   it match the expected value-shape (e.g. `_ARTIFACT_ID_PATTERN =
   re.compile(r"^\d+(?:\.\d+)*-[A-Z]+$")`)? Blank, non-string, or
   malformed members must raise — not be silently stringified or
   filtered out.

Skipping any one of these three layers reintroduces exactly one of the 11
rounds above. The three-layer checklist is now the standing review
heuristic for any future PR touching backlog-frontmatter parsing in this
codebase.

## Lesson: any id later used in a filesystem glob must be shape-validated BEFORE the glob call, not after

`_glob_id`/`_artifact_from_paths` (round 9) and `closure_complete()`
(referenced by round 11's fix) both interpolate a caller-supplied
identifier directly into `Path.glob(f"{id}.*")`. An absolute-looking or
`..`-containing pattern can raise an unhandled low-level `ValueError`
instead of the gate's own fail-closed `BacklogUnavailableError`, defeating
the entire fail-closed design. The fix pattern: validate the shape with a
strict allow-list regex **before** any glob resolution is attempted, so a
malformed id is rejected at the boundary rather than reaching pathlib.

## Lesson: `REVIEW_TIMEOUT` with an empty `unresolved_thread_ids` list means "retry", not "pass" or "fail"

Observed twice in this PR (round 9, round 12): `autoharness gate
copilot-review --max-wait 300 --json` returned `REVIEW_TIMEOUT` with zero
unresolved threads. Both times, an immediate identical retry succeeded —
once returning the actual new findings (`UNRESOLVED_THREADS`), once
returning `SATISFIED`. `REVIEW_TIMEOUT` under these conditions means
Copilot's review hadn't finished posting within the bounded window, not
that the review was clean. Treat it as "retry the gate command", never as
an implicit pass.

## Lesson: `_SHIPMENT_ID_PATTERN` / `_ARTIFACT_ID_PATTERN` validation must be applied unconditionally, not only on the "wrong-type" branch

Round 8 fixed shape-validation for records with a missing/misspelled
`artifact_type`. Round 11 found the SAME shape check was still skipped for
records that WERE correctly typed (`artifact_type: shipment`) but had a
non-shipment-shaped `id`. The general lesson: when a validation only
guards one branch of an if/else, check whether the invariant it protects
actually needs to hold on both branches — a correctly-typed-but-wrongly-ID'd
record is just as dangerous as a wrongly-typed one.

## Lesson: a review's "0 new comments"/"0 new threads" count does not mean "clean" — read the full review body

The closure PR for this same shipment (#298) received its own Copilot
review, which caught that our own drafted closure documentation had
mischaracterized PR #297's round 12 as "clean" based solely on the
thread-based P-018 gate returning `SATISFIED` with zero new threads. In
fact the round-12 review body (and the closure PR's own subsequent review)
carried **suppressed comments**: findings Copilot generates but does not
promote to a new resolvable inline thread because they duplicate a position
already raised in an earlier round and never actually fixed
(`topology.py:680`'s no-op bounded retry, `cli.py:735-739`'s telemetry
outcome mapping). Suppressed comments are invisible to any workflow that
only inspects `reviewThreads` — they live only in the review's free-text
`body` field. Lesson: before declaring a round "clean" or finalizing a
closure verdict as unconditional `READY`, read the full review body text
(`reviews(last:N){ nodes{ body } }` via GraphQL), not just the thread
count — and remember that a docs-only PR is not exempt from this scrutiny;
closure documentation itself gets reviewed.

## Lesson: a stated closure "condition" is only real if the code actually enforces it

A second review round on the closure PR (still HEAD `ade757b`) went one
step further: it pointed out that `closure_complete()`
(`topology.py:505-518`) validates only `compaction_status`, never
`closure_status`/releasability — a **third** recurrence of a defect
Copilot's PR #297 review had flagged twice before (also as suppressed
comments, never a resolvable thread). Consequence: writing "115-S must not
proceed until these defects are fixed" in a closure doc's prose has zero
mechanical effect, because the one function that could enforce it doesn't
look at the field that prose depends on. Lesson: when a closure document
declares a condition gating a successor's eligibility, verify whether the
actual gate/tool the successor depends on (here: the topology gate's
`closure_complete()`) can see and enforce that condition — if it can't
(because the gate isn't wired in yet, or checks a different field), say so
explicitly rather than implying a control exists that doesn't. A written
condition without an enforcement point is a process commitment for humans
to honor manually, not a gate.
