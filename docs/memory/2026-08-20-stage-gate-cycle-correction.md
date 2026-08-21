---
title: "Stage session - bounded correction of three P1 findings across 144-S / 145-S / 146-S"
date: 2026-08-20
agent: stage
route: "claude-opus-5 / anthropic / high (P-013.5)"
branch: chore/stage-144-s
stash_consumed: []
stash_created: []
deliberations_archived: [021-DL]
features: [136-F, 137-F, 138-F]
tasks: [138.001-T, 136.002-T, 136.003-T, 137.001-T, 137.002-T]
superseded: [136.001-T]
shipments: [146-S, 144-S, 145-S]
execution_order: "146-S -> 144-S -> 145-S"
terminal_state: "queued; 146-S is the only claimable shipment; 138.001-T is the only unblocked first task"
---

# Stage session memory - 2026-08-20 (gate-cycle correction)

## Scope

Operator-directed bounded correction of **three confirmed same-contract P1
findings** against already-staged artifacts. No new intake, no new stash entries,
no new features, no new shipments. All three findings pass **P-021 C1** against
the currently authorized staged contracts, so all three were **fixed in place**
and **no deferred entries were created**.

## Degraded-mode declarations

* `TOOL_OK: backlogit` (MCP + CLI)
* `INDEX_SYNC_OK` (908 items at session start and at close)
* `ENGRAM_DEGRADED` - operator-declared unavailable; file-based discovery used
* `INTERCOM_DEGRADED` - operator-declared unavailable; phase broadcasts skipped,
  operator choices carried in the session report
* `GRAPHTOR_UNAVAILABLE` - operator-declared unavailable; file-based `docs/`
  search
* Checkpoint scan (`consumer_id: stage`, unfiltered): 4 total, 2 resolved,
  2 abandoned, **0 active**, 0 quarantined -> ZERO-CANDIDATE NORMAL STARTUP.
  No recovery, no cross-role handling.

## Finding 1 - circular mandatory-gate dependency between 146-S and 144-S

**Problem.** Ship evaluates *all* mandatory gates before completing *every*
task. Two independent blockers were red at baseline, owned by two shipments that
blocked each other in effect:

| Blocker | Gate | Former owner |
| --- | --- | --- |
| `docs/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md` line 12 unquoted YAML scalar | Gate 1 - YAML frontmatter validity | `136.001-T` in `144-S` |
| Stale `.backlogit/queue/019-DL.md` load in two P-021 contract modules | configured pytest suite | `138.001-T` in `146-S` |

`146-S` repaired only the pytest blocker, so its own first task would have
completed with Gate 1 red. `144-S` held the Gate 1 repair but is blocked by
`146-S`, and running it first would still have hit the pytest `setUpClass`
collapse. The recorded `blocks` edges were acyclic throughout - the cycle was in
the **gate** graph. **There was no executable first task anywhere in the chain.**

**Resolution.** `138.001-T` became a **gate-atomic baseline repair** clearing
both blockers in one commit:

* Retitled; original scope preserved intact as **Scope B**; the malformed-scalar
  repair carried in **verbatim** from `136.001-T` as **Scope A** (same file,
  same line 12, same byte-identical quoted replacement, same three acceptance
  criteria, plus A4 binding it to Gate 1).
* Acceptance criterion "no file outside `tests/`" superseded by an enumerated
  **four-file budget**: three `tests/` modules plus one line of the 2026-08-02
  benchmark plan. The repo-wide `docs/` sweep is explicitly excluded.
* New combined criterion C2: all mandatory gates green at this task's completion
  gate, retaining the A1 escape hatch for pre-existing failures on *other*
  surfaces (classified under P-021 C1, captured, escalated - never absorbed).
* `136.001-T` **superseded by `138.001-T`**: stamped
  `[SUPERSEDED by 138.001-T]`, full supersession block plus original text
  preserved, comment logged, **archived not deleted**, removed from `144-S`
  membership.
* Edges `136.002-T -> 136.001-T` and `136.003-T -> 136.001-T` removed.
  `136.002-T` is now the first task of `144-S`; `136.003-T` depends on
  `136.002-T` alone.
* **No cross-shipment task edge added.** Ordering rides the pre-existing
  `144-S depends on 146-S (blocks)` shipment edge, so no reference can dangle
  once `146-S`'s items are archived.

**Both previously authorized scopes are preserved.** Neither the known scalar
fix nor the test-path fix was dropped, weakened, or deferred.

**2-hour granularity preserved.** `138.001-T` stays `S` / `low`: Scope A was
independently sized `XS` / `trivial`, and a mechanical single-line quoting edit
adds no uncertainty on the complexity axis. Neither axis forces a split.

## Finding 2 - 021-DL cleanup field was inert under the installed dogfood Ship

**Problem.** `138-F.custom_fields.source_deliberation_id` pointed at `021-DL`,
but the installed dogfood `.github/agents/_ship.agent.md` carries **no**
`source_deliberation_id` cleanup step. It exists only in
`templates/agents/_ship.agent.md.tmpl` (line 820, verified read-only). `146-S`
executes **before** the `145-S` template/dogfood migration that would install
it, so no later migration could have performed the archival.

**Resolution.** `021-DL` was **archived by Stage** to
`.backlogit/archive/021-DL.md` - the lifecycle-safe Stage-owned mechanism, since
the deliberation is complete and fully harvested into `138-F` / `138.001-T` /
`146-S`. A closure comment recording the reason and the forward refs was logged
first. Verified after archival: 182 lines / 21,845 bytes, `id: 021-DL`,
`created_at` unchanged, `status: archived`, Problem Frame, the chosen Option B
record, the amendment markers and the verification evidence all intact.

`source_deliberation_id` was **retained** under the established idempotent
convention. It points at an already-archived source, so the Ship cleanup step
("if it exists and is not already archived, archive it; otherwise skip and log
it") is a documented **no-op**. Retaining it preserves the provenance link
without scheduling work. **No dogfood Ship implementation scope was added to
`146-S`.**

No test or source file hard-references `021-DL` (verified by repo-wide search
across `tests/`, `src/`, `docs/`, `templates/`, `.github/`, `schemas/`), so the
archival cannot reproduce the 019-DL failure class it was staged to fix.

## Finding 3 - 137.002-T required a successor-owned test reference

**Problem.** `137.002-T`'s acceptance required its new document to be
*referenced from the parity contract test* - an edit to
`tests/test_scope_containment_policy_contract.py` owned by **successor**
`137.001-T`, which depends on `137.002-T`. `137.002-T` could satisfy its own
acceptance only by waiting for its own successor or by duplicating the
successor's edit on the same file and lines. Ship gates every task, so this
blocked `137.002-T` and transitively `145-S`.

**Resolution.** `137.002-T` is now **independently complete** on document
creation, frontmatter validity, and content. The test reference is owned and
verified **exclusively** by `137.001-T`, whose requirement 3 already carried it
and which now also states it as an explicit acceptance criterion, with an
end-state guarantee recorded in new `137-F` covering-feature acceptance.

**Deliberately not done:** no reverse dependency (the edge stays one-way
`137.001-T -> 137.002-T`; the reverse would be a literal cycle), and no
duplication of the test edit - `137.002-T` is explicitly instructed to touch no
test file, width isolation docs-only.

## Final dependency graph - acyclic, no orphans, no dangling references

```text
shipments:   146-S  <-- 144-S  <-- 145-S          (blocks edges; 146-S is the chain source)

146-S: 138.001-T   (no deps)  [FIRST EXECUTABLE TASK - gate-atomic]
144-S: 136.002-T   (no deps)  ->  136.003-T
145-S: 137.002-T   (no deps)  ->  137.001-T
                              ->  137.003-T  [ATOMIC]
       137.004-T   (no deps, order-independent)
```

Every task leaves all mandatory gates green at its own completion gate. No task
depends on a temporarily red predecessor.

## Verification performed by Stage

* `backlogit_sync_index` -> 908 indexed (start and close)
* `backlogit_doctor` (duplicates + orphans + partial mutations + workspace root
  conflict) -> 9 findings, **all pre-existing and unrelated**: orphaned
  `048.001-T` / `048.002-T` / `048.003-T`, and partial commit associations on
  `019-DL`, `040-S`, `041.001-T`, `046-F`, `046.001-T`, `128.002-T`. **Zero
  duplicate IDs. Zero findings against any 136 / 137 / 138 / 144 / 145 / 146
  artifact.**
* `backlogit dep list` forward and reverse for all ten live nodes -> graph
  exactly as above; **no edge references archived `136.001-T`**
* `backlogit dep list 136.001-T --reverse` -> empty
* `backlogit queue view --type shipment` -> `146-S` alone
* `backlogit queue view --type task` -> `138.001-T`, `136.002-T`, `137.002-T`,
  `137.004-T`; `136.001-T` absent
* `backlogit_get_shipment 146-S` -> covering feature `138-F`, items
  `[138-F, 138.001-T]`
* `backlogit_get_shipment 144-S` -> covering feature `136-F`, items
  `[136-F, 136.002-T, 136.003-T]`
* `backlogit_get_shipment 145-S` -> covering feature `137-F`, items
  `[137-F, 137.002-T, 137.001-T, 137.003-T, 137.004-T]`
* `Test-Path` -> `021-DL` and `136.001-T` present only under
  `.backlogit/archive/`, absent from `.backlogit/queue/`
* Frontmatter of every artifact touched this session parsed with
  `yaml.safe_load` -> valid (the review document has no frontmatter block, which
  the `136.003-T` guard skips by design)
* `docs/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md` line 12
  re-read -> still unquoted, confirming Scope A is still needed

### Known cosmetic artifact (pre-existing, not introduced)

`size_composition` on a feature or shipment is a **hierarchy** rollup, not a
manifest rollup, so `144-S` still lists archived `136.001-T` in its
`size_composition.members` while its authoritative `custom_fields.items` is
correct. `145-S` has shown the identical behaviour for archived `137.005-T` /
`137.006-T` since the previous session. Manifest membership - the field Ship
consumes - is correct in both cases.

## Tool-protocol note

backlogit exposes no shipment-member removal operation (`shipment` subcommands
are add / claim / create / get / list / return-blocked / ship, and
`return-blocked` would wrongly flip an archived item to `blocked`). Removal of a
superseded member from a manifest therefore follows the **established repository
precedent** set in commit `8fa8cf67`, which removed `137.005-T` / `137.006-T`
from `.backlogit/queue/145-S.md` the same way: a single-line deletion from the
manifest's `custom_fields.items`, LF endings preserved, nothing else touched.
Archival itself used the official `backlogit_archive_item` operation.

## Boundary statement

Stage made **no** source, test, template, schema, or config edit; ran **no**
build, test suite, or linter; made **no** branch switch, commit, push, or PR;
claimed **no** shipment. Only backlog artifacts and planning documents
(plan / review / memory) were modified. The working tree's pre-existing
operator-managed changes are preserved. Publication remains the Orchestrator's
step.

## Handoff

`146-S` is claimable and its single task `138.001-T` is the first executable
task in the chain - the first one able to leave every mandatory gate green.
Ship must still verify the green transition empirically; Stage ran no tests, and
every claim here rests on file reads, `git cat-file`, `Test-Path`,
`Select-String`, and backlogit read operations.

## Addendum - the manifest-reduction precedent is WITHDRAWN (2026-08-20)

Raised as a Copilot review thread on PR #375 against `.backlogit/queue/145-S.md`.
The record above is left intact; this addendum supersedes the specific
statements it names.

**Withdrawn: the "Tool-protocol note" precedent.** That note is correct that
backlogit exposes no shipment-member **removal** operation, and correct that
`return-blocked` must not be abused for it. Its conclusion - that a superseded
member should therefore be hand-deleted from `custom_fields.items`, following
commit `8fa8cf67` - is **withdrawn**. The absence of a removal operation is not
a gap to be worked around by hand; for a superseded **child of a manifest's
covering feature** it is the contract telling you not to remove the member at
all. Removing one breaks closure:

* the P-015 classifier
  (`autoharness.gates.shipment_closure.classify_shipment_close_path`) enumerates
  a root feature's children across **both** `.backlogit/queue/` and
  `.backlogit/archive/`, so an omitted child means the covering feature is not a
  fully-covered root and **cascade is refused**; and
* safe-close then places that omitted child in the **protected set**, whose
  baseline integrity gate requires every protected member to be present in
  `queue/`. An already-archived protected member is classified as a pre-existing
  cascade and **closure halts**. The `pre-archived` exemption applies to
  manifest items only; the protected set has none.

**Correct disposition instead:** leave the superseded child **in** the manifest
and express supersession through the item's own state - archive it with
`backlogit_archive_item`, stamp the superseded-by pointer, and drop its
dependency edges. P-015 exception item 7 tolerates a pre-archived manifest
member explicitly, and the cascade op is idempotent over it.

**Superseded verification line.** `backlogit_get_shipment 145-S` now returns
items `[137-F, 137.002-T, 137.001-T, 137.003-T, 137.004-T, 137.005-T,
137.006-T]`. `137.005-T` / `137.006-T` were restored with the official
`backlogit_add_to_shipment` operation; the classifier now returns
`cascade: every feature member is a verified fully-covered root`.

**Amends the "Known cosmetic artifact" note.** For `145-S` the divergence is
resolved rather than cosmetic: `size_composition.members` and
`custom_fields.items` now agree on all six children. The note still stands for
`144-S`, whose manifest `[136-F, 136.002-T, 136.003-T]` omits archived
`136.001-T`.

**Observed, not changed - `144-S` carries the same closure defect.** Classifying
`144-S`'s current manifest read-only returns
`safe_close: feature member '136-F' has children outside the manifest
('136.001-T',)`, and `136.001-T` is archived, so safe-close would halt on the
protected-set baseline exactly as `145-S` would have. `144-S` was **not**
modified - it is outside the bounded scope of the `145-S` review thread and is
recorded here for a separate operator decision. (`146-S` was also checked and is
already `cascade`-valid.)

## Addendum 2 — `144-S` manifest restored to full-child membership (2026-08-20)

Same-contract (P-021 C1) continuation of Addendum 1, on the same branch and the
same review cycle. The record above is left intact; this addendum supersedes the
specific statements it names.

**Superseded statements.**

* Finding 1's bullet "`136.001-T` **superseded by `138.001-T`** ... **archived
  not deleted**, removed from `144-S` membership" — correct on supersession
  and archival, **wrong** on the membership reduction, which is now reverted.
* The verification line ``backlogit_get_shipment 144-S`` -> items
  `[136-F, 136.002-T, 136.003-T]`. Current value:
  `[136-F, 136.002-T, 136.003-T, 136.001-T]`.
* Addendum 1's "Observed, not changed — `144-S` carries the same closure
  defect ... recorded here for a separate operator decision" — the operator
  decision was given and the defect is **fixed**, by the same mechanism used for
  `145-S`.
* Addendum 1's "Amends the Known cosmetic artifact note" sentence "The note
  still stands for `144-S`" — it no longer does: `size_composition.members`
  and `custom_fields.items` now agree on all three children of `136-F`, so the
  divergence is resolved for every shipment in the chain.

**Correction applied.** `136.001-T` was added back to `144-S.custom_fields.items`
with the official `backlogit_add_to_shipment` operation (no hand-edit of the
manifest). Classifying read-only, before and after:

```
before: safe_close | feature member '136-F' has children outside the manifest: ('136.001-T',)
after:  cascade    | every feature member is a verified fully-covered root; cascade close is permitted
```

**The withdrawal in Addendum 1 now has no surviving exception.** With `144-S`
corrected, no shipment in the `146-S -> 144-S -> 145-S` chain carries a reduced
manifest, and the `8fa8cf67` hand-removal precedent is withdrawn workspace-wide,
not merely for `145-S`.

**Supersession preserved.** `136.001-T` stays archived, keeps its
`[SUPERSEDED by 138.001-T]` stamp and superseded-by pointer, and declares no
dependency edges in either direction. Executable scope of `144-S` is still
`136.002-T -> 136.003-T`. Full record:
`docs/memory/2026-08-20-stage-144-s-closure-valid-membership.md`.
