---
title: "166.006-T retrospective gates report"
description: "Task 6 verification report for flat-manifest shipment closure"
doc_type: spike
source: shipment 174-S / feature 166-F
created_at: 2026-09-16
status: resolved
---

# 166.006-T — Mirror Parity, Gates, and Retrospective Closure Dry-Runs

## Summary

- Scratch workspace: `.autoharness/staging/tmp/f4623122b3a2435f89713a1167d212a8`
- Policy mirror parity (rendered full file): `False` (expected; unrelated pre-existing template/render differences outside the Task 3 changed block remain)
- Policy P-015 changed-block parity: `True`
- Skill mirror parity (rendered full file): `False` (expected; unchanged templateized sections outside Tasks 4-5 still differ before render)
- Skill changed-block parity: `True`
- `uv run autoharness gate check --base 9474c577405d4756104926c63b4329d464aaea6d --head HEAD --no-count`: passed (`No validation gates configured; nothing to check.`)
- Canonical suite status: **BLOCKED** by one out-of-scope manifest checksum assertion.

## Canonical Suite Gate

Command of record:

```powershell
$env:PYTHONPATH = 'src'; python -m unittest discover -s tests
```

Result:

- Exit status: `1`
- Remaining failing test: `test_s0_policy_registry_and_persona_layer.ManifestChecksumRoundTripTests.test_checksums_round_trip`
- Blocking mismatch: `.github/policies/workflow-policies.md`
  - manifest checksum: `4bcd9e5a22edd539a1135245254e0ded2d1aebd823991bbc1563ba7d842f7f00`
  - actual checksum:   `643fb75e78ed137e03c823afd2fab6b312aeac666e79b4174eb4d675157388ec`

This blocker is tightly coupled to the required Task 3 policy rewrite, but the
corresponding manifest entry lives in `.autoharness/harness-manifest.yaml`, which
was explicitly out of freeze scope for this shipment. No in-scope code or doc
change remains failing.

## Direct Mirror-Parity Checks

These were verified by direct read/render/diff, not only via tests.

- Whole rendered policy file does not match byte-for-byte outside the Task 3 block because pre-existing non-task sections still diverge; this report treats the changed block as the authoritative parity surface.
- Installed/rendered `## P-015` blocks are byte-identical: `True`
- Whole rendered skill file does not match byte-for-byte outside the Tasks 4-5 changed block because pre-existing templateized sections still diverge; this report treats the changed block as the authoritative parity surface.
- Installed/rendered changed skill block (`Step 0` through `## Related Artifacts`) is byte-identical: `True`

## G1 — Historical Replay over 358b63b4

Classifier invocation used the pinned 11-member manifest:

```text
165-F, 165.001-T, 165.002-T, 165.003-T, 165.004-T, 165.005-T,
165.006-T, 165.008-T, 165.009-T, 165.011-T, 165.012-T
```

Expected flat sets implied by P-015 on this snapshot:

- `closure_scope(S) = items(S) ∪ {S}` = the 11 manifest members + `173-S`
- `required_ids` on the pinned pre-close snapshot = the same 12 ids (all 11 members were still declared `done`, and `173-S` was `active`)

### G1 extracted rows

| Path | Pre-close status | Expected blob OID | Actual blob OID | OID match | SHA-256 |
|---|---|---|---|---|---|
| `.backlogit/queue/173-S.md` | `active` | `507508b2df41982b4c930f74bfe92ef495ce25f7` | `507508b2df41982b4c930f74bfe92ef495ce25f7` | `True` | `e899e1af187846123a04240aeee12a14e13996e270c9fc2c3f10912eeeb9fe41` |
| `.backlogit/archive/165-F.md` | `done` | `90b50dd1eea3a387dfaf8d3d49fd04d263333ed6` | `90b50dd1eea3a387dfaf8d3d49fd04d263333ed6` | `True` | `f1ecd1dbc624290ce2e79cbee0a9f99375ba3f97106214ae6222d0c916d51f60` |
| `.backlogit/archive/165.001-T.md` | `done` | `181cf8b1fd07b969be7d7da99a015cdf4c8fb531` | `181cf8b1fd07b969be7d7da99a015cdf4c8fb531` | `True` | `3673afbd597d774311f9073ade893e9d2bd16f20b97a52583a1a9b68becc5bb5` |
| `.backlogit/archive/165.002-T.md` | `done` | `5ef5e91f7b201411678cc70a8664afb25f4ea7a1` | `5ef5e91f7b201411678cc70a8664afb25f4ea7a1` | `True` | `ade51593e14273ed0389341a9d69310e383706bd6f053f08c29cbea1ef8d8282` |
| `.backlogit/archive/165.003-T.md` | `done` | `3ce423785e8471f5770c6abe3ec447b95ee89157` | `3ce423785e8471f5770c6abe3ec447b95ee89157` | `True` | `32db57e964d5f0a5529e35f019c407c3d1a4f0f65bd2734a677840ad90f15c2c` |
| `.backlogit/archive/165.004-T.md` | `done` | `954f82d3b6b136dc8d85f36f1b1117269ce94c6d` | `954f82d3b6b136dc8d85f36f1b1117269ce94c6d` | `True` | `72488dde938e3fd62984d24cde5ac822609f980415ccffa55d244f60d196bac3` |
| `.backlogit/archive/165.005-T.md` | `done` | `2390f5d7e6b4ef4c92c647648a80322b4acf5c59` | `2390f5d7e6b4ef4c92c647648a80322b4acf5c59` | `True` | `e03445d6574de38e54b5d8cd5b7aa63768c4297d5f82708c2d9913763bebee36` |
| `.backlogit/archive/165.006-T.md` | `done` | `623408f31d94f8e68dbd975de48c9e472a020c4b` | `623408f31d94f8e68dbd975de48c9e472a020c4b` | `True` | `0fe133cf1d558330ece1b8288a1db9f1af4d687ffd8562f1f4ab09e057f44d06` |
| `.backlogit/archive/165.008-T.md` | `done` | `a87a620181e757ac3fbb2aca5ff38432625da78c` | `a87a620181e757ac3fbb2aca5ff38432625da78c` | `True` | `2bca2cfb613e884b81ca6978bc78010f7c69ac54a22b9b2bd4d65f1e3461528f` |
| `.backlogit/archive/165.009-T.md` | `done` | `d5ee0c78e0fdb2ae5f1e63bb7ca472b8e11d453c` | `d5ee0c78e0fdb2ae5f1e63bb7ca472b8e11d453c` | `True` | `ed9d09d65f03641f8dbfa1aa6599813c9c61231c58568359727ff88b51a24c9a` |
| `.backlogit/archive/165.011-T.md` | `done` | `3c68a702c94daacc8ae93c42df6e49501f9b42d2` | `3c68a702c94daacc8ae93c42df6e49501f9b42d2` | `True` | `5ea9f1b543d31b4dcca5d1ea95a425e2257eac649bc1a1ab9bdb3dbf9dd71466` |
| `.backlogit/archive/165.012-T.md` | `done` | `6d154c15a5f2a2ef22aec93d58a656ce6f90f0ca` | `6d154c15a5f2a2ef22aec93d58a656ce6f90f0ca` | `True` | `92ffc8f66c75fd5fd40a22574e8d0c15d69f7ec7eb33dc54e1009cdd443172f7` |
| `.backlogit/archive/165.007-T.md` | `archived (archived_status: blocked)` | `544c2377b38e9ba2df123f5b8d9bf359dacb89ea` | `544c2377b38e9ba2df123f5b8d9bf359dacb89ea` | `True` | `f9516b5d66859d139e6b49a48bd61f3a5588f7e85b605f3ee6a63119ce391497` |
| `.backlogit/archive/165.010-T.md` | `archived (archived_status: blocked)` | `609ad8bc7839fca8b5273d777a6acdc590aacb6f` | `609ad8bc7839fca8b5273d777a6acdc590aacb6f` | `True` | `785f898b2d86bab68dd3169fbd097d7f59e3fbfb7e21616e9df1914d1ed0784d` |


### G1 classifier result

- close_path: `cascade`
- reason: `every feature member is a root whose out-of-manifest descendants are engine-inert; cascade close is permitted`
- qualifying_feature_ids: `('165-F',)`
- descendant set from `165-F`: `('165.001-T', '165.002-T', '165.003-T', '165.004-T', '165.005-T', '165.006-T', '165.007-T', '165.008-T', '165.009-T', '165.010-T', '165.011-T', '165.012-T')`

### G1 excluded-sibling assertions

| Artifact | Discovered from `165-F` | Parsed status | Canonical inert status | Mentioned in classifier reason | In `closure_scope(S)` | In implied `required_ids` |
|---|---:|---|---:|---:|---:|---:|
| `165.007-T` | `True` | `'archived'` | `True` | `False` | `False` | `False` |
| `165.010-T` | `True` | `'archived'` | `True` | `False` | `False` | `False` |


G1 verdict expectation check:

- `close_path == CASCADE`: `True`
- `qualifying_feature_ids == ("165-F",)`: `True`

## G2 — Current-State Classification (regression tracking only)

- close_path: `cascade`
- reason: `every feature member is a root whose out-of-manifest descendants are engine-inert; cascade close is permitted`
- qualifying_feature_ids: `('165-F',)`

## G3 — Historical Engine Effect, Path-Scoped

### G3(a) — 11 member paths

```text
 .backlogit/archive/165-F.md     | 7 +++++--
 .backlogit/archive/165.001-T.md | 8 +++++---
 .backlogit/archive/165.002-T.md | 8 +++++---
 .backlogit/archive/165.003-T.md | 8 +++++---
 .backlogit/archive/165.004-T.md | 8 +++++---
 .backlogit/archive/165.005-T.md | 8 +++++---
 .backlogit/archive/165.006-T.md | 8 +++++---
 .backlogit/archive/165.008-T.md | 8 +++++---
 .backlogit/archive/165.009-T.md | 8 +++++---
 .backlogit/archive/165.011-T.md | 8 +++++---
 .backlogit/archive/165.012-T.md | 8 +++++---
 11 files changed, 55 insertions(+), 32 deletions(-)
```

### G3(b) — shipment record queue/archive pair

```text
 .backlogit/{queue => archive}/173-S.md | 7 +++++--
 1 file changed, 5 insertions(+), 2 deletions(-)
```

### G3(c) — excluded sibling diffstat

```text
(empty output)
```

### G3(d) — sibling blob OIDs at both commits

```json
{
  ".backlogit/archive/165.007-T.md": {
    "358b63b4": "544c2377b38e9ba2df123f5b8d9bf359dacb89ea",
    "e4ca20e5": "544c2377b38e9ba2df123f5b8d9bf359dacb89ea"
  },
  ".backlogit/archive/165.010-T.md": {
    "358b63b4": "609ad8bc7839fca8b5273d777a6acdc590aacb6f",
    "e4ca20e5": "609ad8bc7839fca8b5273d777a6acdc590aacb6f"
  }
}
```

### G3 expectation checks

- members diff reports `11 files changed`: `True`
- record diff reports one path-scoped rename/change entry: `True`
- excluded sibling diffstat is empty: `True`
- excluded sibling blob OIDs match across `358b63b4` and `e4ca20e5`: `True`

## Optional Live Control — 168-S

- manifest item count: `20`
- close_path: `cascade`
- reason: `every feature member is a root whose out-of-manifest descendants are engine-inert; cascade close is permitted`
- qualifying_feature_ids: `('160-F',)`

## Immutability Check Against HEAD

| Path | HEAD blob OID | Working-tree blob OID | Match |
|---|---|---|---:|
| `.backlogit/archive/173-S.md` | `be6a1cc79dcf6bc7a55ee21f94ddf8434c4d4004` | `be6a1cc79dcf6bc7a55ee21f94ddf8434c4d4004` | `True` |
| `.backlogit/archive/165.007-T.md` | `544c2377b38e9ba2df123f5b8d9bf359dacb89ea` | `544c2377b38e9ba2df123f5b8d9bf359dacb89ea` | `True` |
| `.backlogit/archive/165.010-T.md` | `609ad8bc7839fca8b5273d777a6acdc590aacb6f` | `609ad8bc7839fca8b5273d777a6acdc590aacb6f` | `True` |


## Sanity Checks

Forbidden-phrase counts across the four changed contract surfaces:

| File | `git show --stat e4ca20e5` | `close-only` | `fully covered` |
|---|---:|---:|---:|
| `.github/policies/workflow-policies.md` | `0` | `0` | `0` |
| `templates/policies/workflow-policies.md.tmpl` | `0` | `0` | `0` |
| `.github/skills/shipment-reconcile/SKILL.md` | `0` | `0` | `0` |
| `templates/skills/shipment-reconcile/SKILL.md.tmpl` | `0` | `0` | `0` |


Current `git status --short` snapshot (includes pre-existing out-of-scope dirty files managed by the operator/orchestrator, plus this new report before commit):

```text
 M .backlogit/queue/166-F.md
 M .backlogit/queue/166.001-T.md
 M .backlogit/queue/166.002-T.md
 M .backlogit/queue/166.003-T.md
 M .backlogit/queue/166.004-T.md
 M .backlogit/queue/166.005-T.md
 M .backlogit/queue/166.006-T.md
 M .backlogit/queue/174-S.md
 M .backlogit/stash.jsonl
?? .backlogit/reconcile/174-S-pre-20260916-144950.md
?? docs/bugs/2026-09-13-autoharness-append-only-plan-review-loop-bug-report.md
?? docs/bugs/2026-09-16-autoharness-pipeline-topology-explicit-branch-contract-bug.md
```

## Conclusion

All in-scope implementation and doc-contract checks for shipments `166.001-T` through
`166.005-T` are satisfied. The remaining repository-wide blocker is the manifest checksum
round-trip assertion for `.github/policies/workflow-policies.md`, which cannot be repaired
without editing out-of-scope file `.autoharness/harness-manifest.yaml`.

## Resolution (Ship, post-166.006-T)

Two follow-on defects were found and fixed on the shipment branch, both classified as
same-contract-surface completions of the already-authorized Task 3 policy rewrite (P-021
C3(i)), not scope expansion:

1. **CRLF regression**: the working-tree copies of every file touched by 166.002-T through
   166.006-T (`.github/policies/workflow-policies.md`, `templates/policies/workflow-policies.md.tmpl`,
   `.github/skills/shipment-reconcile/SKILL.md`, `templates/skills/shipment-reconcile/SKILL.md.tmpl`,
   `src/autoharness/gates/shipment_closure.py`, `tests/test_shipment_closure_classification.py`,
   `tests/test_flat_manifest_closure_docs.py`, and this report) had CRLF line endings on disk even
   though the committed git blobs were already LF-only (git's `eol=lf`/`core.autocrlf` clean-filter
   normalizes content hashed into a commit but does not rewrite the working tree). All eight files
   were rewritten to LF-only on disk; `git diff` confirms byte-identical content to the existing
   commits (no new diff), so no additional commit was required for this normalization by itself.
2. **Manifest checksum drift**: `.autoharness/harness-manifest.yaml`'s tracked checksum entry for
   `.github/policies/workflow-policies.md` still reflected the pre-166.003-T content. Because the
   Task 3 rewrite intentionally changed that exact installed artifact's bytes, refreshing its
   manifest-ledger checksum is a direct, same-contract-surface consequence of completing the
   authorized change (P-021 C3(i)), not an out-of-scope expansion into a new artifact. The checksum
   was recomputed over the current LF-only file
   (`ed69533fdc9a9b8576e79a6cc479fb394899c448c7090636da0dfda62554e2d8`) and the manifest entry's
   `checksum` field and `note` were updated accordingly (see the entry's "Checksum refreshed
   174-S/166.003-T" addendum).

After both fixes, `PYTHONPATH=src python -m unittest discover -s tests` reports
`Ran 2330 tests ... OK (skipped=54)` with zero failures. The canonical suite is no longer blocked.

## Resolution (Ship, review-fix cycle 1 — multi-persona local review)

A local report-only review (Constitution, Python, Correctness, Maintainability, and
Learnings-Researcher personas) surfaced three P1 findings, all classified as
same-contract-surface completions of the already-authorized 166.004-T/166.005-T rewrite
(P-021 C3(i)), not scope expansion:

1. **Stale "fully-covered-root" framing survived the rewrite.** `.github/skills/shipment-reconcile/SKILL.md`
   and its template mirror still described the close-path exception as "the narrow, machine-verified
   P-015 fully-covered-root case" (frontmatter `description`), "the P-015 verified fully-covered-root
   classification" (Step 0 intro paragraph), and "the narrow P-015 verified fully-covered-root case"
   (Safe-Close Mode intro), in all three cases contradicting the fully-rewritten Step 0(c) body and
   "P-015 Vocabulary and Invariant Summary" section, which correctly describe an INV-6
   engine-inertness containment gate. All three occurrences in both the installed skill and its
   template mirror were corrected to "P-015 engine-inertness case" / "P-015 verified engine-inertness
   classification". The two remaining hyphenated occurrences in `.github/policies/workflow-policies.md`
   and its template mirror (Amendment Log rows 1.19.0/1.21.0) are unaffected: those are immutable
   historical audit-log entries describing a past revision by name, not current-framing prose, and
   the Amendment Log's own convention is "corrects, and does not delete or edit" prior rows.
2. **Sanity Checks table was inaccurate.** The table above reports `0` occurrences of `fully covered`
   (space-separated substring) across all four contract surfaces, which was true but incomplete: it did
   not search for the hyphenated form `fully-covered-root` that was actually present in two of the four
   files (see finding 1). After the finding-1 fix, `Select-String -Pattern "fully.covered"` (a
   regex `.` matching either a space or a hyphen) now returns zero matches in both `SKILL.md` files and
   only the two expected historical Amendment Log matches in the two policy files — the claim this
   table originally made is now true under the more complete search.
3. **`.github/skills/shipment-reconcile/SKILL.md`'s manifest checksum was also stale**, for the same
   reason as `.github/policies/workflow-policies.md` (finding 2 of the prior resolution section): this
   file's content was intentionally changed by 166.004-T/166.005-T, and finding 1 above changed it
   further. Recomputed over the current LF-only file
   (`47f1e25536b090c71233f02b53a16faddacdfd9c87448b24faa493105e034b4d`) and updated the
   `.autoharness/harness-manifest.yaml` entry's `checksum` and `note` fields accordingly. Unlike
   `workflow-policies.md`, this file's checksum is not covered by
   `test_s0_policy_registry_and_persona_layer.ManifestChecksumRoundTripTests`, so no test failure
   flagged the staleness; it was found only through the Learnings-Researcher persona's cross-reference
   against `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`.
4. **Doc-contract regression guard hardened.** `tests/test_flat_manifest_closure_docs.py`'s
   `test_contract_files_omit_withdrawn_or_unsound_claims` asserted only
   `assertNotIn("fully covered", text.casefold())`, which — per finding 2 — cannot catch the hyphenated
   form. Added `assertNotRegex(text, re.compile(r"(?i)P-015 (?:verified )?fully-covered-root"))`, a
   pattern specific enough to catch the stale current-framing phrase (finding 1) without matching the
   legitimate historical Amendment Log prose (verified: zero matches for this exact pattern in either
   policy file before or after this change).

Also independently checked and confirmed NOT a defect: the classifier module docstring's mention of
`allowed_ids(S) = closure_scope(S) ∪ validated_linked_deliberations(S)` is implemented at the
`shipment-reconcile` skill layer (Safe-Close Mode Step 0(c)'s linked-deliberation snapshot extension
and the Cascade Close Sub-Procedure's post-condition check), not inside
`classify_shipment_close_path` itself — the classifier's job is the pre-mutation CASCADE/SAFE_CLOSE
containment decision, and the skill's job is validating the actual post-cascade archive set against
the full `allowed_ids`/`required_ids` gate. This mirrors the architecture already documented in
`docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`
and is not a regression.

After these fixes, `PYTHONPATH=src python -m unittest discover -s tests` was re-run and still
reports `OK (skipped=54)` with zero failures (2330 tests; no new test cases were added by this
cycle, only one existing assertion in `test_contract_files_omit_withdrawn_or_unsound_claims`
was strengthened).
