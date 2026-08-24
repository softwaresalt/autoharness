# Spike — Does `backlogit shipment ship` tolerate pre-archived manifest members?

> **⚠️ SUPERSEDED (155-S / 147-F, 2026-08-24).** This spike's arms were
> constructed with `backlogit move <id> --status done`, which **relocates** a
> record into `archive/` but leaves it declaring `status: done` — never truly
> `status: archived`. Against the engine's own `archiveItems()` guard in
> `internal/core/shipment_lifecycle.go` (`if item.Status == models.StatusArchived
> { continue }`), `done != archived`, so every "pre-archived" artifact in every
> arm below **was archived by the call** and legitimately transited into
> `archived_ids` — it never had the "already archived, nothing to transition"
> case this spike set out to test. **All three arms were, at the guard that
> matters, the control arm.** The spike therefore never once exercised a truly
> `status: archived` input, and its "byte-identical result shape across all
> three arms" finding is valid **only** for relocated-but-`done` records, not
> for genuinely pre-archived ones.
>
> Its **recommendation against adjusting the post-condition** (§ "Consequence
> for the proposed remedy", below) is **RETRACTED**. `docs/plans/2026-08-24-cascade-close-archived-ids-postcondition-plan.md`
> (deliberation `027-DL`, corrected by shipment `155-S`) replaces the
> `archived_ids` exact-match post-condition with a two-set `allowed_ids` /
> `required_ids` gate keyed on DECLARED pre-close `status`, precisely because a
> truly `status: archived` **manifest task item, or a qualifying feature
> member's validated linked deliberation,** has no transition to report and is
> correctly **absent** from `archived_ids` (verified directly against
> `internal/core/shipment_lifecycle.go` source, not a black-box re-run of this
> spike's method). **This never extends to the qualifying feature member
> itself** (155-S, PR #407 review, thread PRRT_kwDORzpWpM6b00dS): this
> spike's own "Full" arm relocated `001-F` with `move --status done` rather
> than truly archiving it, so it never actually exercised a truly
> `status: archived` feature; against the live engine, `ShipShipment`
> unconditionally forces every explicit qualifying feature member through
> `status: done` before archive-candidate collection runs, so it is always
> re-archived and always present in `archived_ids` regardless of its own
> pre-close declared status — a qualifying feature member is an
> unconditional `required_ids` member, never eligible for this tolerance.
>
> The body below is preserved unmodified as the historical record of what was
> actually run and observed; read it as evidence about relocated-but-`done`
> records only.

Date: 2026-08-18
Agent: Stage (spike, read-only against live workspace)
Stash source: `EDE3CC2D`
Primary evidence input: `docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md`
Status: **RESOLVED — decisive, reproducible**

## Question

The 140-S closure session substituted manual safe-close for a clean `CASCADE`
classifier verdict because it could not confirm whether the cascade operation
tolerates manifest members that were already archived before shipment-level
closure ran. The compound doc records this explicitly as unverified:

> "Whether the underlying `backlogit shipment ship` operation is
> idempotent/tolerant of already-archived manifest members was not verified
> before manual safe-close was substituted."

The Cascade Close Sub-Procedure's step 3 post-condition requires `archived_ids`
to match the manifest **exactly**, and is written assuming the cascade
operation performs the archival itself. If the engine omitted pre-archived IDs
from `archived_ids`, that post-condition would fail and force a P-005 halt on
an otherwise-legitimate cascade.

## Method

Three isolated throwaway `backlogit` workspaces were created **outside** the
repository (system temp, `--cwd` pinned so no live backlog state could be
resolved), each with a fully-covered root feature `001-F` and its single child
task `001.001-T`, both listed in shipment `001-S`. Live `.backlogit/` state was
never read for mutation and never written.

The three arms differ only in archival state at the moment `shipment ship` ran:

| Arm | Pre-close state |
|---|---|
| **Control** | Neither member archived (both in `queue/`) |
| **Partial** | Task archived, feature still in `queue/` |
| **Full** | Both members archived (reproduces 140-S exactly) |

Archival was produced the same way 140-S produced it — `backlogit move <id>
--status done`, which auto-relocates the artifact into `archive/`.

Tooling: `backlogit v1.9.0-39-g17530fe3`; classifier run from the source tree
(`src/autoharness/gates/shipment_closure.py`) via `PYTHONPATH=src`.

## Results

### 1. The classifier returns a clean `CASCADE` in every pre-archive state

```text
Full arm:    close_path=ClosePath.CASCADE
             reason="every feature member is a verified fully-covered root; cascade close is permitted"
             qualifying_feature_ids=('001-F',)
Partial arm: close_path=ClosePath.CASCADE  (same reason)
```

No error, no ambiguity, no failed precondition. This confirms the compound
doc's analysis: `_read_artifact_record` already scans **both** `queue/` and
`archive/`, so archived inputs never destabilise the verdict.

### 2. `backlogit shipment ship` is fully idempotent over pre-archived members

All three arms returned **byte-identical result shape**, exit code `0`:

```json
{
  "shipment_id": "001-S",
  "shipment_status": "shipped",
  "archived_ids": ["001.001-T", "001-F", "001-S"],
  "returned_ids": [],
  "commit_sha": "<arm sha>"
}
```

`archived_ids` contains exactly the manifest task item, the qualifying feature
member, and the shipment record — **including members that were already
archived before the call**. `returned_ids` is empty in every arm.

### 3. Invariants that the Cascade Close Sub-Procedure checks all hold

* **Step 3 (exact match)** — passes unchanged in all three arms.
* **Step 4 (`parent_id` preservation)** — `parent_id: 001-F` intact on the
  archived task in every arm, including when it was pre-archived.
* **Step 2 (`returned_ids` empty)** — holds in every arm.
* Merge metadata (`commit: <sha>`) is stamped onto pre-archived records too, so
  the cascade path still adds provenance value over doing nothing.

### 4. Secondary observation — `archived_status` provenance

Pre-archived members carry `archived_status: done` rather than `shipped`. This
is **also true of the control arm**, so it is not a pre-archive-specific
regression, and P-015's sequence-aware exclusion rule already accepts
normalized legacy `done` as verified archived provenance. No action required;
recorded so a future session does not mistake it for a new defect.

## Conclusion

**There is no engine-behaviour gap. The gap is purely documentary.**

The Cascade Close Sub-Procedure as written already executes correctly and
passes all of its own verification steps when manifest members are
pre-archived. What it lacks is any statement *saying so* — leaving a closure
session facing pre-archived members with no contract-legal reassurance, which
is precisely what pushed 140-S into an undocumented judgment call.

## Consequence for the proposed remedy (corrects the compound doc)

The compound doc's follow-up recommends extending the sub-procedure to
"**adjust the `archived_ids` exact-match post-condition** to account for items
that were already archived before the cascade operation ran."

That adjustment is **not required and would be actively harmful.** The engine
already includes pre-archived IDs in `archived_ids`, so the exact-match
post-condition is satisfied as-is. Relaxing it would weaken a live P-005
out-of-scope-mutation safety check to solve a problem that does not exist.

The evidence-supported remedy is narrower: **document the tolerance, change no
invariant.**

Likewise, `src/autoharness/gates/shipment_closure.py` needs **no change** — the
classifier is already correct for pre-archived inputs, as arms 2 and 3 prove.
