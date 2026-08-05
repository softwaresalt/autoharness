---
title: Fail-closed backlog parsing — eleven-round Copilot review-fix pattern (114-S / 109-F)
tags: [topology-gate, fail-closed, backlog-parsing, path-traversal, review-fix, glob-injection]
related_pr: 297
related_shipment: 114-S
related_feature: 109-F
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
9. **Round 12** — clean (`SATISFIED`, 0 new findings). The pattern was
   fully exhausted.

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
